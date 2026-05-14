# Code Generation Plan - Profile Update Service

## Unit Context

**Unit Name**: `profile-update-service`  
**Project Type**: Brownfield - Spring Boot 3.2 Java API  
**Base Package**: `com.sandbox.userapi`  
**Workspace Root**: `/home/sk/vscode/aws-sagents-dlc/kiro-sandbox/services/java-api`

### Stories Implemented in This Unit
- [ ] US-001: Update Own Profile Name
- [ ] US-002: Update Own Profile Email
- [ ] US-003: Prevent Unauthorized Profile Updates
- [ ] US-004: Admin Update Any User Profile
- [ ] US-005: Admin Manage User Roles
- [ ] US-006: Admin Manage User Active Status

### Unit Dependencies
- Existing User Entity model (`com.sandbox.userapi.model.User`)
- Existing UserRepository interface (`com.sandbox.userapi.repository.UserRepository`)
- Existing GlobalExceptionHandler (`com.sandbox.userapi.exception.GlobalExceptionHandler`)
- Existing SecurityConfig (`com.sandbox.userapi.config.SecurityConfig`)
- Spring Security (authentication/authorization)
- Jakarta Bean Validation (input validation)

### Expected Interfaces & Contracts

#### REST API Endpoint
```
PUT /api/users/{userId}
Content-Type: application/json

Request:
{
  "name": "string (optional)",
  "email": "string (optional)",
  "role": "string (optional, admin only)",
  "active": "boolean (optional, admin only)"
}

Response (200 OK):
{
  "id": "long",
  "name": "string",
  "email": "string",
  "role": "string",
  "active": "boolean"
}

Errors: 400, 403, 404, 409
```

#### Service Layer Contract
```java
UserService.updateUser(
    Long userId,
    UpdateUserRequest request,
    Authentication authentication
) → UserResponse
throws ForbiddenException, ResourceNotFoundException, 
       BadRequestException, DataIntegrityViolationException
```

#### Repository Contract
```java
UserRepository.existsByEmailAndIdNot(String email, Long userId) → boolean
UserRepository.save(User entity) → User
```

---

## Code Generation Plan - Phase 1: Planning

### Overview
This unit requires enhancements to existing components rather than creating new ones. The implementation follows the brownfield pattern:
- **Modify**: UpdateUserRequest DTO (add fields), UserService (add updateUser method), UserController (add endpoint), UserRepository (add query method)
- **Leverage**: Existing User entity, GlobalExceptionHandler, SecurityConfig
- **Test**: Comprehensive unit and integration tests for all new functionality

### Project Structure
```
src/main/java/com/sandbox/userapi/
├── config/
│   └── SecurityConfig.java (existing)
├── controller/
│   └── UserController.java (MODIFY - add PUT endpoint)
├── dto/
│   ├── UpdateUserRequest.java (MODIFY - add fields)
│   └── UserResponse.java (existing - verify all fields)
├── exception/
│   ├── BadRequestException.java (existing)
│   ├── ForbiddenException.java (existing)
│   ├── GlobalExceptionHandler.java (existing)
│   └── ResourceNotFoundException.java (existing)
├── model/
│   └── User.java (existing)
├── repository/
│   └── UserRepository.java (MODIFY - add query method)
├── service/
│   └── UserService.java (MODIFY - add updateUser method)
└── UserApiApplication.java (existing)

src/test/java/com/sandbox/userapi/
├── service/
│   └── UserServiceUpdateUserTest.java (CREATE)
└── controller/
    └── UserControllerUpdateUserTest.java (CREATE)
```

---

## Detailed Code Generation Steps

### Step 1: Analyze Existing Code Structure
**Objective**: Review existing code patterns and conventions  
**Checklist**:
- [ ] Review existing UserController.java for REST endpoint patterns
- [ ] Review existing UserService.java for business logic patterns
- [ ] Review existing UpdateUserRequest.java current state
- [ ] Review existing UserResponse.java structure
- [ ] Review UserRepository.java existing methods
- [ ] Review GlobalExceptionHandler.java exception handling patterns
- [ ] Document naming conventions and code style used

**Story Mapping**: Preparation for all stories (US-001 through US-006)

**Expected Output**: Understanding of codebase patterns to maintain consistency

---

### Step 2: Enhance UpdateUserRequest DTO
**Objective**: Extend UpdateUserRequest to support all updateable fields  
**Target File**: `src/main/java/com/sandbox/userapi/dto/UpdateUserRequest.java`  
**Action**: MODIFY existing file

**Changes**:
- Add `name` field (String, optional, max 100 chars)
- Add `email` field (String, optional, valid email format)
- Add `role` field (String, optional, admin-only validation indicator)
- Add `active` field (Boolean, optional, already exists - verify)
- Add appropriate Jakarta Bean Validation annotations:
  - `@Size(min = 1, max = 100)` on name
  - `@Email` on email
  - Keep `active` field as-is
- Add getters and setters for all fields
- Ensure support for partial updates (all fields nullable)

**Story Mapping**: Foundation for US-001, US-002, US-003, US-004, US-005, US-006

**Acceptance Criteria**:
- DTO compiles successfully
- Supports partial updates (all fields can be null)
- Validation annotations present
- Can serialize/deserialize JSON

---

### Step 3: Enhance UserRepository with Email Uniqueness Query
**Objective**: Add repository method for email uniqueness validation  
**Target File**: `src/main/java/com/sandbox/userapi/repository/UserRepository.java`  
**Action**: MODIFY existing file

**Changes**:
- Add method: `boolean existsByEmailAndIdNot(String email, Long userId)`
- Spring Data JPA will auto-generate implementation
- This allows checking email uniqueness while excluding the current user

**Story Mapping**: Foundation for US-002, US-004

**Acceptance Criteria**:
- Repository compiles successfully
- Method auto-generated by Spring Data JPA
- Can query email uniqueness excluding a specific user ID

---

### Step 4: Enhance UserService with Update Logic
**Objective**: Implement core business logic for profile updates  
**Target File**: `src/main/java/com/sandbox/userapi/service/UserService.java`  
**Action**: MODIFY existing file

**Changes**:
- Add method: `public UserResponse updateUser(Long userId, UpdateUserRequest request, Authentication authentication)`
- Implement authorization checks:
  - Extract authenticated user ID and role from Authentication object
  - Allow admins to update any user
  - Allow regular users to update only themselves
  - Prevent regular users from modifying role and active fields
- Implement business logic:
  - Find user by ID (throw 404 if not found)
  - Validate email uniqueness if email provided and changed
  - Apply field updates only for provided (non-null) fields
  - Save updated user with @Transactional
- Map User entity to UserResponse DTO
- Handle and translate exceptions:
  - ResourceNotFoundException (404) for missing user
  - ForbiddenException (403) for authorization failures
  - BadRequestException (400) for validation failures
  - DataIntegrityViolationException (409) for email conflicts

**Story Mapping**: Core logic for US-001, US-002, US-003, US-004, US-005, US-006

**Key Implementation Details**:
```java
@Transactional
public UserResponse updateUser(Long userId, UpdateUserRequest request, 
                               Authentication authentication) {
  // 1. Extract authenticated user details
  // 2. Authorization checks:
  //    - Is admin? Allow any update
  //    - Is self-update? Check field restrictions
  //    - Else: Throw ForbiddenException
  // 3. Find user or throw 404
  // 4. Validate email uniqueness if provided
  // 5. Apply updates to user entity
  // 6. Save and return as UserResponse
}

Private helper methods:
- validateUpdateAuthorization(authenticatedUserId, targetUserId, 
                             authenticatedRole, updateRequest)
- validateEmailUniqueness(newEmail, userId)
- applyUpdates(user, request)
```

**Acceptance Criteria**:
- Service compiles successfully
- Authorization logic enforced (self-update vs admin)
- Email uniqueness validated
- Partial updates supported
- Returns UserResponse with updated data
- Throws correct exceptions with proper HTTP status codes

---

### Step 5: Enhance UserController with PUT Endpoint
**Objective**: Add REST endpoint for profile updates  
**Target File**: `src/main/java/com/sandbox/userapi/controller/UserController.java`  
**Action**: MODIFY existing file

**Changes**:
- Add method: `public ResponseEntity<UserResponse> updateUser(
    @PathVariable Long userId,
    @RequestBody @Valid UpdateUserRequest request,
    Authentication authentication
  )`
- Annotations: `@PutMapping("/{userId}")` on `/api/users` base path
- Extract Authentication object from Spring Security context
- Call UserService.updateUser()
- Return ResponseEntity with:
  - 200 OK on success with UserResponse body
  - Exceptions handled by GlobalExceptionHandler (400, 403, 404, 409)
- Add Javadoc with API documentation
- Add SpringDoc OpenAPI annotations if present in project

**Story Mapping**: API exposure for US-001, US-002, US-003, US-004, US-005, US-006

**Acceptance Criteria**:
- Endpoint receives PUT requests on `/api/users/{userId}`
- Authentication context injected correctly
- Returns 200 OK with UserResponse on success
- Errors delegate to GlobalExceptionHandler
- API documentation accurate

---

### Step 6: Unit Tests - UserService.updateUser()
**Objective**: Comprehensive unit tests for service layer business logic  
**Target File**: `src/test/java/com/sandbox/userapi/service/UserServiceUpdateUserTest.java`  
**Action**: CREATE new file

**Test Coverage** (minimum 25+ test cases):

**Authorization Tests** (8 tests):
- [ ] testUpdateUser_SelfUpdateNameAsRegularUser_Success
- [ ] testUpdateUser_SelfUpdateEmailAsRegularUser_Success
- [ ] testUpdateUser_RegularUserCannotUpdateOtherUser_Throws403
- [ ] testUpdateUser_RegularUserCannotChangeRole_Throws403
- [ ] testUpdateUser_RegularUserCannotChangeActive_Throws403
- [ ] testUpdateUser_AdminCanUpdateAnyUser_Success
- [ ] testUpdateUser_AdminCanChangeRole_Success
- [ ] testUpdateUser_AdminCanChangeActiveStatus_Success

**Validation Tests** (8 tests):
- [ ] testUpdateUser_NameValidation_MaxLength_Success
- [ ] testUpdateUser_NameValidation_ExceedMaxLength_Throws400
- [ ] testUpdateUser_EmailValidation_ValidFormat_Success
- [ ] testUpdateUser_EmailValidation_InvalidFormat_Throws400
- [ ] testUpdateUser_EmailValidation_DuplicateEmail_Throws409
- [ ] testUpdateUser_RoleValidation_InvalidRole_Throws400
- [ ] testUpdateUser_PartialUpdate_OnlyNameProvided_Success
- [ ] testUpdateUser_PartialUpdate_OnlyEmailProvided_Success

**Data Integrity Tests** (6 tests):
- [ ] testUpdateUser_UserNotFound_Throws404
- [ ] testUpdateUser_EmailUniquenessAcrossSystem_Success
- [ ] testUpdateUser_ExcludingCurrentUserFromEmailCheck_Success
- [ ] testUpdateUser_TransactionalUpdate_AllFieldsOrNone
- [ ] testUpdateUser_UpdateMultipleFields_Success
- [ ] testUpdateUser_NoUpdateForNullFields_Success

**Edge Cases** (3+ tests):
- [ ] testUpdateUser_EmptyRequestBody_PartialUpdate_Success
- [ ] testUpdateUser_UserIdZeroOrNegative_Throws404
- [ ] testUpdateUser_EmailChangeToCurrentEmail_Success

**Test Framework**: JUnit 5, Mockito, AssertJ  
**Mocking**: UserRepository, Authentication  
**Fixtures**: Test users (admin, regular user, various states)

**Acceptance Criteria**:
- All 25+ tests pass
- >90% code coverage of updateUser method
- Tests independent and isolated
- Clear test names and assertions

---

### Step 7: Integration Tests - UserController.updateUser()
**Objective**: End-to-end tests for REST endpoint  
**Target File**: `src/test/java/com/sandbox/userapi/controller/UserControllerUpdateUserTest.java`  
**Action**: CREATE new file

**Test Coverage** (minimum 15+ test cases):

**HTTP Status Tests** (6 tests):
- [ ] testUpdateUser_ValidRequest_Returns200OK
- [ ] testUpdateUser_InvalidData_Returns400BadRequest
- [ ] testUpdateUser_Unauthorized_Returns403Forbidden
- [ ] testUpdateUser_UserNotFound_Returns404NotFound
- [ ] testUpdateUser_EmailDuplicate_Returns409Conflict
- [ ] testUpdateUser_UnauthenticatedRequest_Returns401Unauthorized

**Request/Response Tests** (5 tests):
- [ ] testUpdateUser_ValidRequestBody_DeserializedCorrectly
- [ ] testUpdateUser_ResponseIncludesUpdatedData
- [ ] testUpdateUser_ContentTypeApplicationJson
- [ ] testUpdateUser_ResponseIncludesUserId
- [ ] testUpdateUser_PartialUpdateReturnsCompleteProfile

**Authorization Tests** (4 tests):
- [ ] testUpdateUser_RegularUserCanUpdateOwnProfile
- [ ] testUpdateUser_RegularUserCannotUpdateOtherUser_403
- [ ] testUpdateUser_AdminCanUpdateAnyUser
- [ ] testUpdateUser_AdminCanChangeRoleAndActive

**Test Framework**: Spring Boot Test, MockMvc or RestAssured, JUnit 5  
**Database**: Embedded H2 (in-memory)  
**Auth**: Mock HTTP Basic authentication or TestSecurityContext

**Acceptance Criteria**:
- All 15+ tests pass
- HTTP status codes correct for all scenarios
- Request/response serialization correct
- Authorization rules enforced at endpoint level

---

### Step 8: Verify UserResponse DTO
**Objective**: Ensure UserResponse includes all required fields  
**Target File**: `src/main/java/com/sandbox/userapi/dto/UserResponse.java`  
**Action**: VERIFY existing file

**Required Fields**:
- [ ] id (Long)
- [ ] name (String)
- [ ] email (String)
- [ ] role (String)
- [ ] active (Boolean)

**Required Annotations**:
- [ ] @JsonInclude for null value handling
- [ ] Proper getters/setters
- [ ] Constructors for mapping from User entity

**Story Mapping**: Response format for all stories

**Acceptance Criteria**:
- All 5 required fields present
- Can serialize/deserialize JSON
- Maps correctly from User entity

---

### Step 9: Verify GlobalExceptionHandler
**Objective**: Ensure exception handler covers all profile update error scenarios  
**Target File**: `src/main/java/com/sandbox/userapi/exception/GlobalExceptionHandler.java`  
**Action**: VERIFY/ENHANCE existing file

**Required Handlers**:
- [ ] Handle ForbiddenException → 403
- [ ] Handle ResourceNotFoundException → 404
- [ ] Handle BadRequestException → 400
- [ ] Handle DataIntegrityViolationException → 409 (for email conflicts)
- [ ] Handle MethodArgumentNotValidException → 400 (validation errors)

**Story Mapping**: Error handling for all stories

**If Missing**: Add handlers for any missing exception types

**Acceptance Criteria**:
- All profile update error scenarios handled
- Correct HTTP status codes returned
- Clear error messages in response

---

### Step 10: Verify UserRepository Query Method
**Objective**: Ensure email uniqueness query method works correctly  
**Target File**: `src/main/java/com/sandbox/userapi/repository/UserRepository.java`  
**Action**: VERIFY from Step 3

**Story Mapping**: Email uniqueness for US-002, US-004

**Acceptance Criteria**:
- Method: `existsByEmailAndIdNot(String email, Long userId)`
- Returns true if email exists for another user
- Returns false if email doesn't exist or belongs to same user
- Spring Data JPA auto-generates implementation

---

### Step 11: Create Integration Test Data
**Objective**: Set up test data and fixtures for all test scenarios  
**Target Files**: Test classes from Steps 6-7  
**Action**: Include in test classes

**Test Users**:
- [ ] Regular user 1 (id=1, email=user1@example.com, name=User One, role=ROLE_USER, active=true)
- [ ] Regular user 2 (id=2, email=user2@example.com, name=User Two, role=ROLE_USER, active=true)
- [ ] Admin user (id=99, email=admin@example.com, name=Admin, role=ROLE_ADMIN, active=true)
- [ ] Inactive user (id=3, email=user3@example.com, name=User Three, role=ROLE_USER, active=false)

**Test Scenarios**:
- [ ] UpdateUserRequest with only name
- [ ] UpdateUserRequest with only email
- [ ] UpdateUserRequest with name and email
- [ ] UpdateUserRequest with role (admin only)
- [ ] UpdateUserRequest with active (admin only)
- [ ] UpdateUserRequest with all fields
- [ ] UpdateUserRequest with invalid email format
- [ ] UpdateUserRequest with duplicate email
- [ ] UpdateUserRequest with name exceeding 100 chars

---

### Step 12: Documentation - API Contract
**Objective**: Document REST API endpoint for users  
**Target File**: `aidlc-docs/construction/profile-update-service/code/api-contract.md`  
**Action**: CREATE new documentation

**Content**:
- Endpoint path: PUT /api/users/{userId}
- Request format (JSON schema)
- Response format (JSON schema)
- Error scenarios (400, 403, 404, 409)
- Authentication requirements
- Authorization rules
- Example requests/responses
- Story mapping to endpoint

---

### Step 13: Documentation - Implementation Guide
**Objective**: Document implementation approach for developers  
**Target File**: `aidlc-docs/construction/profile-update-service/code/implementation-guide.md`  
**Action**: CREATE new documentation

**Content**:
- Overview of changes
- Files modified (UpdateUserRequest, UserService, UserController, UserRepository)
- Authorization logic overview
- Validation strategy
- Email uniqueness implementation
- Error handling strategy
- Test execution instructions

---

### Step 14: Build and Dependency Verification
**Objective**: Verify all dependencies and build configuration  
**Target File**: `pom.xml` (if not already present)  
**Action**: VERIFY existing build configuration

**Required Dependencies**:
- [ ] Spring Boot 3.2.3
- [ ] Spring Data JPA
- [ ] Spring Security
- [ ] Jakarta Bean Validation
- [ ] H2 Database (test scope)
- [ ] JUnit 5
- [ ] Mockito
- [ ] AssertJ

**Story Mapping**: Build foundation for all stories

**Acceptance Criteria**:
- All required dependencies present in pom.xml
- Versions compatible with Spring Boot 3.2
- Test dependencies properly scoped

---

### Step 15: Summary Document
**Objective**: Create summary of all changes for review  
**Target File**: `aidlc-docs/construction/profile-update-service/code/GENERATION-SUMMARY.md`  
**Action**: CREATE new documentation

**Content**:
- List of modified files with change summary
- List of new test files created
- Coverage of all 6 user stories
- Verification checklist
- Outstanding items (if any)

---

## Implementation Sequence

The steps should be executed in order:

1. **Analysis** (Step 1): Review existing code
2. **Data Transfer Objects** (Step 2): Enhance UpdateUserRequest
3. **Repository Layer** (Step 3): Add email uniqueness query
4. **Service Layer** (Step 4): Core business logic
5. **Controller Layer** (Step 5): REST endpoint
6. **Service Tests** (Step 6): Unit test business logic
7. **Controller Tests** (Step 7): Integration tests
8. **Verification** (Steps 8-10): Ensure existing components ready
9. **Test Data** (Step 11): Set up test fixtures
10. **Documentation** (Steps 12-13): Document changes
11. **Build Verification** (Step 14): Check dependencies
12. **Summary** (Step 15): Review checklist

## Validation Checklist

- [ ] All code modifications target existing files (no duplicates)
- [ ] All new tests created in appropriate test packages
- [ ] Documentation created in aidlc-docs/construction/profile-update-service/code/
- [ ] No code written to aidlc-docs/ except documentation
- [ ] Base package `com.sandbox.userapi` used consistently
- [ ] All 6 user stories mapped to code changes
- [ ] Authorization rules enforced (self-update vs admin)
- [ ] Email uniqueness validated
- [ ] Error handling for all scenarios (400, 403, 404, 409)
- [ ] Build configuration verified
- [ ] Test coverage >85% for service and controller
- [ ] Code follows existing project conventions

## Total Estimated Steps: 15
## Estimated Scope: 500-700 lines of code + tests
## Stories Covered: All 6 (US-001 through US-006)
