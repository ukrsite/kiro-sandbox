# Services - Profile Update Feature

## Overview

This document defines the service layer design for the profile update feature, including service definitions, responsibilities, and orchestration patterns.

---

## Service Architecture

The profile update feature is implemented within the existing Spring Boot service layer, leveraging a single primary service with supporting infrastructure services.

---

## 1. UserService - Profile Update Service

### Service Definition

**Name:** UserService  
**Type:** Spring @Service Component  
**Scope:** Singleton  
**Transaction Scope:** @Transactional  
**Stereotype:** Business Logic Service

### Purpose

Core business logic service responsible for orchestrating profile update operations, including authorization enforcement, validation, and data persistence.

### Service Responsibilities

1. **Profile Update Orchestration**
   - Coordinate complete profile update workflow
   - Manage transactional boundaries for data consistency
   - Invoke repository operations in correct sequence
   - Handle partial updates with field-level control

2. **Authorization Enforcement**
   - Validate user permissions before update
   - Enforce role-based access control (RBAC)
   - Restrict field updates based on user role
   - Prevent unauthorized profile modifications

3. **Business Logic Validation**
   - Email uniqueness validation with pre-check
   - Field-level validation (format, length, constraints)
   - Role value validation
   - Authorization check for admin-only fields

4. **Data Persistence Coordination**
   - Load user entity from repository
   - Merge updated fields into entity
   - Persist changes via repository.save()
   - Maintain transaction integrity

5. **Exception Translation**
   - Convert repository exceptions to service exceptions
   - Translate validation failures to appropriate exceptions
   - Provide meaningful error messages for error scenarios
   - Support proper HTTP status code translation

### Service Methods

#### Primary Method: updateUser

```java
@Transactional
public UserResponse updateUser(
    Long userId,
    UpdateUserRequest request,
    Long authenticatedUserId,
    String authenticatedUserRole
)
```

**Workflow:**

```
1. checkUpdateAuthorization()
   ├─ If fails → throw UnauthorizedException (403)
   └─ If passes → continue

2. UserRepository.findById(userId)
   ├─ If not found → throw UserNotFoundException (404)
   └─ If found → load user entity

3. If request.email is provided:
   └─ validateEmailUniqueness(request.email, userId)
      ├─ If not unique → throw EmailAlreadyExistsException (409)
      └─ If unique → continue

4. Build updated User entity:
   ├─ if (request.name != null) → user.setName(request.name)
   ├─ if (request.email != null) → user.setEmail(request.email)
   ├─ if (request.role != null && isAdmin) → user.setRole(request.role)
   └─ if (request.active != null && isAdmin) → user.setActive(request.active)

5. Validate all fields:
   └─ Bean Validation framework validates entity (if configured)

6. UserRepository.save(user)
   └─ Persist updated entity to database

7. Convert user to UserResponse DTO
   └─ return new UserResponse(user)
```

**Exception Handling:**

| Exception | HTTP Status | Scenario |
|-----------|------------|----------|
| UnauthorizedException | 403 | User lacks permission for update |
| UserNotFoundException | 404 | Target user doesn't exist |
| EmailAlreadyExistsException | 409 | Email not unique |
| ValidationException | 400 | Field validation failure |

### Service Integration Points

**Integration with Security Infrastructure:**
- Reads authenticated user information from Security Context
- Validates user role (ROLE_USER, ROLE_ADMIN)
- Enforces role-based authorization decisions

**Integration with Data Access:**
- Calls UserRepository.findById() to load user
- Calls UserRepository.existsByEmailAndIdNot() for email check
- Calls UserRepository.save() to persist updates

**Integration with Exception Handling:**
- Throws custom exceptions
- GlobalExceptionHandler translates to HTTP responses
- Preserves exception context for logging

**Integration with Transaction Management:**
- Single @Transactional block for complete workflow
- Ensures atomicity of profile updates
- Coordinates with email uniqueness check

### Service Interaction Patterns

#### Pattern 1: Orchestration Pattern
UserService orchestrates multiple repository and validation operations in sequence, coordinating data flows between components.

```
Request → Service → Authorization → Repository → Service → Response
                                   ↓
                            Database (Transaction)
```

#### Pattern 2: Authorization Pattern
UserService checks authorization before processing, failing fast on permission violations.

```
Request → Authorization Check → [Pass/Fail]
                                    ↓
                           [Fail: Throw 403]
                                    ↓
                           [Pass: Continue Processing]
```

#### Pattern 3: Validation Pattern
UserService performs validation at multiple levels: authorization, uniqueness, and field validation.

```
Request → Authorization ✓ → Uniqueness ✓ → Field Validation ✓ → Update
                       ✗→ 403      ✗→ 409           ✗→ 400
```

#### Pattern 4: Transaction Pattern
All database operations occur within a single @Transactional boundary for consistency.

```
@Transactional:
    └─ findById()
    └─ email uniqueness check
    └─ save()
    └─ [Commit on success | Rollback on exception]
```

### Helper Methods

#### Authorization Check Helper

```java
private void checkUpdateAuthorization(
    Long targetUserId,
    Long authenticatedUserId,
    String authenticatedUserRole,
    UpdateUserRequest request
) throws UnauthorizedException
```

**Responsibilities:**
- Verify user is admin OR updating their own profile
- Verify regular users can't update admin-only fields (role, active)
- Raise UnauthorizedException on authorization failure

**Logic:**
```
if (authenticatedUserRole.equals("ROLE_ADMIN")) {
    return;  // Admin can do anything
}

if (!targetUserId.equals(authenticatedUserId)) {
    throw UnauthorizedException("Can only update own profile");
}

if (request.getRole() != null || request.getActive() != null) {
    throw UnauthorizedException("Cannot update role or active status");
}
```

#### Email Uniqueness Validation Helper

```java
private void validateEmailUniqueness(
    String newEmail,
    Long userId
) throws EmailAlreadyExistsException
```

**Responsibilities:**
- Check if email exists for another user
- Raise EmailAlreadyExistsException if not unique
- Use pre-check for better error message (409 vs database constraint)

**Logic:**
```
boolean emailExists = userRepository.existsByEmailAndIdNot(newEmail, userId);
if (emailExists) {
    throw EmailAlreadyExistsException("Email already in use");
}
```

---

## 2. Security Service Integration

### Purpose

Integration point with Spring Security framework for authentication context access and role-based authorization.

### Service Type

**Framework Service** (provided by Spring Security)

### Responsibilities

1. **Authentication Context Access**
   - Provide authenticated user identity
   - Expose user role information
   - Support security context extraction

2. **Authorization Information**
   - Supply user's granted authorities
   - Support role-based decisions

### Integration Pattern

```java
// In UserController
Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
Long authenticatedUserId = extractUserId(authentication);
String authenticatedUserRole = extractRole(authentication);

// Pass to UserService
UserResponse response = userService.updateUser(
    userId,
    request,
    authenticatedUserId,
    authenticatedUserRole
);
```

### Security Context Information Extracted

- **User Identity:** Principal (userId, username)
- **User Role:** Authorities (ROLE_USER, ROLE_ADMIN)
- **Authentication Status:** IsAuthenticated

---

## 3. Exception Handling Service Integration

### Purpose

Integration with GlobalExceptionHandler for exception translation and HTTP response generation.

### Exception Translation Mapping

| Service Exception | HTTP Status | Exception Handler |
|------------------|------------|------------------|
| UnauthorizedException | 403 Forbidden | GlobalExceptionHandler |
| UserNotFoundException | 404 Not Found | GlobalExceptionHandler |
| EmailAlreadyExistsException | 409 Conflict | GlobalExceptionHandler |
| ValidationException | 400 Bad Request | GlobalExceptionHandler |
| Constraint Violation | 400 Bad Request | GlobalExceptionHandler |

### Integration Pattern

UserService throws custom exceptions → GlobalExceptionHandler catches → HTTP response generated

```
UserService
    ├─ throws UnauthorizedException
    ├─ throws UserNotFoundException
    ├─ throws EmailAlreadyExistsException
    └─ throws ValidationException
        ↓
GlobalExceptionHandler
    ├─ @ExceptionHandler(UnauthorizedException.class) → 403
    ├─ @ExceptionHandler(UserNotFoundException.class) → 404
    ├─ @ExceptionHandler(EmailAlreadyExistsException.class) → 409
    └─ @ExceptionHandler(ValidationException.class) → 400
        ↓
HTTP Response with error details
```

---

## Service Collaboration Diagram

```
┌─────────────────────┐
│   UserController    │
│  (REST Endpoint)    │
└──────────┬──────────┘
           │
           │ Calls updateUser()
           ↓
┌────────────────────────────────────────┐
│       UserService                      │
│  ┌──────────────────────────────────┐  │
│  │ 1. Authorization Check           │  │
│  │    - checkUpdateAuthorization()  │  │
│  └──────────────────────────────────┘  │
│           ↓ (throws if unauthorized)   │
│  ┌──────────────────────────────────┐  │
│  │ 2. Load User Entity              │  │
│  │    - UserRepository.findById()   │  │
│  └──────────────────────────────────┘  │
│           ↓ (throws if not found)      │
│  ┌──────────────────────────────────┐  │
│  │ 3. Email Uniqueness Validation   │  │
│  │    - validateEmailUniqueness()   │  │
│  │    - Repository.exists...()      │  │
│  └──────────────────────────────────┘  │
│           ↓ (throws if not unique)     │
│  ┌──────────────────────────────────┐  │
│  │ 4. Build Updated Entity          │  │
│  │    - Set updated fields          │  │
│  │    - Validate all fields         │  │
│  └──────────────────────────────────┘  │
│           ↓ (throws if validation fail)│
│  ┌──────────────────────────────────┐  │
│  │ 5. Persist Changes               │  │
│  │    - UserRepository.save()       │  │
│  │    - Transaction commit          │  │
│  └──────────────────────────────────┘  │
│           ↓ (returns updated user)     │
│  ┌──────────────────────────────────┐  │
│  │ 6. Convert to Response DTO       │  │
│  │    - Create UserResponse         │  │
│  └──────────────────────────────────┘  │
└────────────┬─────────────────────────────┘
             │
             │ Returns UserResponse
             ↓
┌─────────────────────┐
│  UserController     │
│  (Returns HTTP 200) │
└─────────────────────┘
```

---

## Service Lifecycle

### Instantiation

```
Spring Container discovers @Service UserService
    ↓
Creates singleton instance
    ↓
Injects UserRepository dependency via @Autowired
    ↓
UserService ready for use
```

### Request Lifecycle

```
1. Request arrives at UserController.updateUser()
   ↓
2. Controller extracts authentication info
   ↓
3. Controller calls UserService.updateUser()
   ↓
4. Service executes within @Transactional boundary
   ↓
5. Service returns UserResponse or throws exception
   ↓
6. Controller returns HTTP response
   ↓
7. Transaction commits or rollbacks automatically
```

---

## Service Dependencies

### Required Dependencies

- **UserRepository** - @Autowired dependency for data access
- **Spring Security Context** - For authentication/authorization info
- **Bean Validator** - For field validation
- **Transaction Manager** - For @Transactional scope management

### Optional Dependencies

- **Logging Framework** - For audit logging
- **Metrics/Monitoring** - For performance tracking

---

## Summary

The service layer for profile updates is built around a single **UserService** that:

1. **Orchestrates** the complete profile update workflow
2. **Enforces** authorization rules before processing
3. **Validates** all business rules (email uniqueness, field constraints)
4. **Coordinates** with repository for data access
5. **Manages** transaction boundaries for consistency
6. **Handles** exceptions with meaningful error translation

The service integrates seamlessly with existing Spring Security for authentication/authorization and GlobalExceptionHandler for error handling, maintaining architectural consistency with the existing system.

