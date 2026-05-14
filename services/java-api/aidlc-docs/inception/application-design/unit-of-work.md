# Unit of Work - Profile Update Feature

## Executive Summary

This document defines the unit(s) of work for the profile update feature in the existing Spring Boot monolithic application. The decomposition balances story grouping, component organization, and team execution model.

**Unit Strategy:** Single monolithic unit with modular internal structure.

**Rationale:** 
- Existing monolithic architecture (single deployable application)
- Shared data model (User entity) requires unified handling
- Small feature scope (6 stories, 6 components) doesn't justify multiple independent units
- Single team/single deployment model most practical
- Benefits: unified transaction boundaries, simpler coordination, straightforward testing

---

## Unit Definitions

### Unit 1: Profile Update Service

**Unit Name:** `profile-update-service`  
**Unit Type:** Monolithic Feature Module  
**Status:** Development (Inception Phase → Construction Phase)  
**Priority:** Must Have (Core Feature)

#### Purpose

Implement profile update functionality allowing authenticated users to update their profile information (name, email) with administrative capabilities to manage roles and active status. This unit enhances the existing User management system within the Spring Boot application.

#### Scope

- User profile updates (name, email, role, active status)
- Role-based authorization (regular users, administrators)
- Email uniqueness validation
- Partial update support
- Error handling and validation
- Complete REST API integration

#### Unit Responsibilities

1. **REST API Endpoint**
   - Accept HTTP PUT requests on `/api/users/{userId}`
   - Handle UpdateUserRequest DTO deserialization
   - Return UserResponse DTO in responses
   - Delegate error handling to GlobalExceptionHandler

2. **Authorization Enforcement**
   - Validate user permissions (self-update vs admin)
   - Restrict admin-only fields (role, active)
   - Enforce role-based access control (RBAC)
   - Check authentication context

3. **Business Logic Orchestration**
   - Coordinate profile update workflow
   - Manage transactional consistency
   - Validate business rules
   - Orchestrate data access operations

4. **Validation**
   - Email uniqueness validation (pre-check pattern)
   - Field validation (format, length)
   - User existence validation
   - Role value validation

5. **Data Persistence**
   - Load user from database
   - Apply updates to entity
   - Persist changes atomically
   - Maintain referential integrity

6. **Error Handling**
   - Translate exceptions to meaningful types
   - Support proper HTTP status codes (400, 403, 404, 409)
   - Provide clear error messages

#### Components in Unit

| Component | Role | Responsibility |
|-----------|------|-----------------|
| UserController | REST Endpoint Handler | HTTP request/response, Spring Security integration |
| UserService | Business Logic | Authorization, validation, orchestration, transactions |
| UpdateUserRequest DTO | Request Model | Request data binding, field-level validation |
| UserRepository | Data Access | Database queries, entity persistence |
| User Entity | Domain Model | Profile data, JPA persistence |
| UserResponse DTO | Response Model | Response data serialization |

#### Stories in Unit

| Story ID | Title | Size | Status |
|----------|-------|------|--------|
| US-001 | Update Own Profile Name | S | Assigned |
| US-002 | Update Own Profile Email | M | Assigned |
| US-003 | Prevent Unauthorized Updates | S | Assigned |
| US-004 | Admin Update Any User Profile | M | Assigned |
| US-005 | Admin Manage User Roles | M | Assigned |
| US-006 | Admin Manage User Active Status | S | Assigned |

**Total Story Points:** ~10 points (1+2+1+2+2+1)  
**Estimated Team Capacity:** Single team, 1-2 sprints

---

## Unit Architecture

### Component Organization

```
Profile Update Service (Single Unit)
│
├─ Presentation Layer (HTTP)
│  └─ UserController
│     ├─ UpdateUserRequest (inbound DTO)
│     └─ UserResponse (outbound DTO)
│
├─ Business Logic Layer
│  └─ UserService
│     ├─ Authorization logic
│     ├─ Validation logic
│     └─ Orchestration logic
│
├─ Data Access Layer
│  ├─ UserRepository (Spring Data JPA)
│  └─ User Entity (JPA domain model)
│
└─ Infrastructure Integration
   ├─ Spring Security (authentication/authorization)
   ├─ GlobalExceptionHandler (error handling)
   ├─ Bean Validation (input validation)
   └─ JPA/H2 Database (persistence)
```

### Data Flow Within Unit

```
HTTP Request
    ↓
UserController (accepts request)
    ├─ Spring Security Context extraction
    ├─ UpdateUserRequest validation
    └─ UserService.updateUser() invocation
        ↓
    UserService (business logic)
        ├─ Authorization check
        ├─ User lookup (UserRepository)
        ├─ Email uniqueness validation
        ├─ Entity updates
        └─ Persistence (UserRepository.save())
        ↓
    UserRepository (data access)
        ├─ Database transaction
        ├─ SQL execution
        └─ Entity flush
        ↓
    H2 Database (persistence)
    ↓
    UserService returns updated User
        ↓
    UserController returns UserResponse
        ↓
HTTP Response 200 OK
```

### Authorization Model Within Unit

```
Authentication received from Spring Security
    ↓
UserService extracts:
├─ authenticated user ID
├─ authenticated user role
    ↓
Authorization checks:
├─ Is admin?
│   ├─ YES → Allow any update
│   └─ NO → Is self-update?
│           ├─ NO → Reject (403)
│           └─ YES → Check fields
│                   ├─ Role/active update requested?
│                   │   ├─ YES → Reject (403)
│                   │   └─ NO → Allow
```

### Validation Model Within Unit

```
UpdateUserRequest (HTTP request body)
    ├─ Spring deserializes JSON
    ├─ Bean Validation annotations applied
    │  ├─ @Size on name
    │  ├─ @Email on email
    │  └─ Others...
    └─ Returns 400 if validation fails
    ↓
UserService.updateUser() business validation:
    ├─ User existence check
    ├─ Email uniqueness check (pre-check)
    ├─ Role value validation
    └─ Returns 404/409/400 if validation fails
```

---

## Unit Interfaces & Contracts

### REST API Contract

**Endpoint:** `PUT /api/users/{userId}`

**Request:**
```
Headers:
  Authorization: Basic <base64>
  Content-Type: application/json

Path Variables:
  userId: Long (required) - ID of user to update

Body (UpdateUserRequest):
{
  "name": "string (optional)",          // Max 100 chars
  "email": "string (optional)",         // Valid email format
  "role": "string (optional)",          // ROLE_USER or ROLE_ADMIN (admin only)
  "active": "boolean (optional)"        // true/false (admin only)
}
```

**Success Response (200 OK):**
```
Content-Type: application/json

{
  "id": 1,
  "name": "Updated Name",
  "email": "updated@example.com",
  "role": "ROLE_USER",
  "active": true
}
```

**Error Responses:**
- `400 Bad Request` - Validation failure (invalid email format, name too long, etc.)
- `403 Forbidden` - Authorization failure (insufficient permissions)
- `404 Not Found` - User doesn't exist
- `409 Conflict` - Email not unique

### Service Layer Contract (Internal)

```java
UserService.updateUser(
    Long userId,
    UpdateUserRequest request,
    Long authenticatedUserId,
    String authenticatedUserRole
) → UserResponse
    throws UnauthorizedException,
           UserNotFoundException,
           EmailAlreadyExistsException,
           ValidationException
```

### Repository Contract (Internal)

```java
UserRepository.findById(Long id) → Optional<User>
UserRepository.save(User entity) → User
UserRepository.existsByEmailAndIdNot(String email, Long userId) → boolean
```

---

## Story Coverage & Mapping

### Story Implementation Plan

Each story maps directly to unit features:

| Story | Feature | Components | Priority | Size |
|-------|---------|-----------|----------|------|
| US-001 | Update own name | Controller, Service, DTOs, Repo | Must | S |
| US-002 | Update own email | Controller, Service, DTOs, Repo | Must | M |
| US-003 | Prevent unauthorized | Service (authz logic) | Must | S |
| US-004 | Admin update any user | Service (authz), Controller | Must | M |
| US-005 | Admin manage roles | Service, DTOs (role field) | Must | M |
| US-006 | Admin manage active | Service, DTOs (active field) | Must | S |

### Acceptance Criteria Mapping

**US-001 (Update Own Name):**
- ✅ Regular user can update own name
- ✅ Name validation enforced (max 100 chars)
- ✅ Returns 200 OK with updated profile
- ✅ Returns 400 on validation failure

**US-002 (Update Own Email):**
- ✅ Regular user can update own email
- ✅ Email format validation enforced
- ✅ Email uniqueness validation enforced (409 Conflict)
- ✅ Partial update supported (email only)

**US-003 (Prevent Unauthorized):**
- ✅ Regular user cannot update other user's profile (403)
- ✅ Regular user cannot update own role (403)
- ✅ Regular user cannot update own active status (403)

**US-004 (Admin Update Any User):**
- ✅ Admin can update any user's name/email
- ✅ Email uniqueness still enforced (409 Conflict)
- ✅ Returns 404 if user doesn't exist
- ✅ Partial updates supported

**US-005 (Admin Manage Roles):**
- ✅ Admin can update any user's role
- ✅ Role validation enforced (valid enum values)
- ✅ Regular user cannot change roles (403)

**US-006 (Admin Manage Active):**
- ✅ Admin can activate/deactivate users
- ✅ Regular user cannot change active status (403)
- ✅ Returns 200 OK with updated profile

---

## Unit Dependencies & Integration

### External Dependencies

**Required Infrastructure Components:**
1. Spring Security (existing) - Authentication context
2. GlobalExceptionHandler (existing) - Exception translation
3. H2 Database (existing) - Persistence
4. Spring Data JPA (existing) - ORM layer
5. Jakarta Bean Validation (existing) - Input validation

**No New External Dependencies Required**

### Shared Components

| Shared Component | Owner/Location | Unit Usage |
|-----------------|-----------------|-----------|
| User Entity | Data Model (existing) | Used for persistence |
| UserRepository | Data Access (existing) | Used for queries |
| Spring Security Context | Infrastructure | Used for authorization |
| GlobalExceptionHandler | Infrastructure | Used for errors |

### Internal Unit Dependencies

```
UpdateUserRequest
    ↓
UserController
    ├─ calls UserService
    ├─ uses Spring Security
    └─ delegates to GlobalExceptionHandler
    ↓
UserService
    ├─ calls UserRepository
    ├─ manages User Entity
    └─ returns UserResponse
    ↓
UserRepository
    └─ persists User Entity
    ↓
H2 Database
```

**Dependency Flow:** Unidirectional (no circular dependencies)

---

## Unit Development Phases

### Phase 1: DTO Enhancement (Iteration 1)
**Duration:** 1-2 days  
**Stories:** Foundation for US-001, US-002, US-003, US-004, US-005, US-006  
**Tasks:**
- [ ] Enhance UpdateUserRequest with name, email, role, active fields
- [ ] Add Bean Validation annotations
- [ ] Ensure UserResponse includes all fields
- [ ] Test DTO serialization/deserialization

**Definition of Done:**
- DTOs compile and serialize correctly
- Validation annotations work as expected
- Can serialize/deserialize sample JSON

### Phase 2: Core Service Implementation (Iteration 1-2)
**Duration:** 2-3 days  
**Stories:** US-001, US-002, US-003, US-004, US-005, US-006  
**Tasks:**
- [ ] Implement UserService.updateUser() method
- [ ] Implement authorization logic (self-update, admin checks)
- [ ] Implement email uniqueness validation
- [ ] Implement field update logic
- [ ] Add transactional boundaries
- [ ] Implement exception translation

**Definition of Done:**
- All user stories pass acceptance criteria
- Authorization rules enforced
- Email uniqueness validated
- Exceptions translated to correct status codes
- Unit tests cover all scenarios

### Phase 3: Controller Implementation (Iteration 2)
**Duration:** 1-2 days  
**Stories:** US-001, US-002, US-004  
**Tasks:**
- [ ] Add @PutMapping endpoint to UserController
- [ ] Extract authentication context
- [ ] Call UserService.updateUser()
- [ ] Return UserResponse DTO
- [ ] Integration with GlobalExceptionHandler

**Definition of Done:**
- Endpoint receives PUT requests
- Authentication context extracted correctly
- UserResponse returned with 200 OK
- Errors return correct HTTP status codes

### Phase 4: Repository Enhancement (As-Needed)
**Duration:** 0-1 days  
**Dependent:** Phase 2 (if custom queries needed)  
**Tasks:**
- [ ] Add existsByEmailAndIdNot() query method (if not already present)
- [ ] Add findByEmail() query method (if needed)
- [ ] Verify findById() and save() work correctly

**Definition of Done:**
- Custom query methods work correctly
- Email uniqueness checks function as expected
- User lookups work for all scenarios

### Phase 5: Comprehensive Testing (Throughout)
**Duration:** Ongoing (each iteration)  
**Stories:** All stories  
**Tasks:**
- [ ] Unit tests for UserService
- [ ] Integration tests for UserController
- [ ] Security tests for authorization
- [ ] Validation tests for all error scenarios
- [ ] End-to-end tests for complete workflows

**Definition of Done:**
- All stories have passing tests
- Authorization scenarios tested
- Validation scenarios tested
- Error handling verified

---

## Unit Testing Strategy

### Unit Test Scope

**Service Layer Tests:**
- Authorization logic (self-update, admin, field restrictions)
- Email uniqueness validation
- User existence validation
- Field update logic
- Exception throwing for error scenarios

**Controller Layer Tests:**
- Request binding and validation
- Authentication context integration
- Response formatting
- Error delegation to GlobalExceptionHandler

**Integration Tests:**
- Complete request/response flow
- Real UserService and UserRepository
- In-memory H2 database
- All user story scenarios

**Security Tests:**
- Unauthorized user attempts (403)
- Admin override (allowed)
- Field-level restrictions

### Test Coverage Goals

- UserService: >90% code coverage
- UserController: >85% code coverage
- DTOs: >95% coverage (serialization)
- Overall unit: >85% coverage

---

## Deployment & Release

### Unit Deployment Strategy

**Deployment Model:** Monolithic deployment  
- Entire unit deployed as part of application

**Deployment Checklist:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Code review completed
- [ ] Documentation updated
- [ ] API contract verified
- [ ] Performance verified (< 200ms)

**Release Planning:**
- Feature branch for development
- Pull request with test coverage requirement
- Code review by peers
- Merged to main branch
- Deployed with application release

---

## Unit Quality Metrics

### Code Quality Targets

- **Test Coverage:** >85% of unit code
- **Code Complexity:** Max cyclomatic complexity of 10 per method
- **Documentation:** All public methods documented
- **Error Handling:** All code paths handle errors appropriately

### Performance Targets

- **Response Time:** < 200ms for profile update
- **Database Queries:** 2-3 queries max (read, uniqueness check, update)
- **Concurrency:** Support multiple concurrent updates

### Security Targets

- **Authorization:** 100% of restricted operations checked
- **Input Validation:** 100% of inputs validated
- **Error Messages:** No sensitive data in error responses

---

## Implementation Notes

### Technology Stack (All Existing)
- Spring Boot 3.2.3
- Java 21
- Spring Data JPA
- Hibernate ORM
- H2 Database
- Jakarta Bean Validation
- Spring Security

### Design Patterns Used
- MVC Pattern (Controller → Service → Repository)
- DTO Pattern (UpdateUserRequest, UserResponse)
- Service Locator (UserService for business logic)
- Repository Pattern (UserRepository for data access)
- Transactional Pattern (@Transactional for consistency)

### Key Implementation Decisions

1. **Single Unit:** Monolithic approach matches existing architecture
2. **Service Orchestration:** UserService coordinates all operations
3. **Transactional Boundary:** Single @Transactional for consistency
4. **Pre-Check Validation:** Email uniqueness checked before update
5. **Authorization at Service:** Not in controller (better testability)
6. **Existing Infrastructure:** Reuse Spring Security, GlobalExceptionHandler

### Future Considerations

- **Audit Trail:** Log profile changes for compliance
- **Notifications:** Email user on profile changes
- **Validation Enhancement:** More sophisticated business rules
- **Performance:** Caching if needed at scale
- **Scaling:** If monolith splits, this unit could become independent service

---

## Definition of Unit Completion

The unit is complete when:

- [ ] All 6 user stories implemented and passing acceptance criteria
- [ ] Authorization rules fully enforced (self-update + admin)
- [ ] Email uniqueness validated across all scenarios
- [ ] Field-level validation working for all fields
- [ ] Error handling returns correct HTTP status codes
- [ ] Unit tests provide >85% coverage
- [ ] Integration tests verify complete workflows
- [ ] Security tests verify authorization rules
- [ ] Code review completed
- [ ] API documentation updated
- [ ] Performance verified (< 200ms)
- [ ] Ready for production deployment

---

## Summary

**Profile Update Service** is a single-unit feature module implementing all aspects of profile update functionality for the existing Spring Boot application. 

**Key Characteristics:**
- **Scope:** 6 user stories, 6 components
- **Granularity:** Single monolithic unit
- **Integration:** Seamless integration with existing infrastructure
- **Team:** Single-team development
- **Timeline:** 1-2 sprints
- **Deployment:** Monolithic deployment with application release

This unit is ready for transition to CONSTRUCTION phase where per-unit detailed design (Functional Design) and implementation specifications (unit-of-work.md from CONSTRUCTION) will be created.
