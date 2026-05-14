# Application Design - Profile Update Feature

## Executive Summary

This document presents the complete application design for the "Update Profile" feature in the existing Spring Boot 3.2 Java API. The design builds upon the established 3-tier architecture (Controller → Service → Repository) and integrates seamlessly with existing security, validation, and exception handling infrastructure.

**Design Scope:** Enhance existing UserController, UserService, and UserRepository components to support profile update operations with role-based authorization and comprehensive validation.

**Key Design Principles:**
- Leverage existing Spring Boot patterns and infrastructure
- Maintain backward compatibility
- Enforce strong separation of concerns (3-tier architecture)
- Implement role-based authorization and validation
- Support partial updates with field-level control
- Ensure transactional consistency

---

## Component Overview

The profile update feature involves six primary components:

### 1. UserController (REST Endpoint Layer)
- **Role:** HTTP request handler for profile update operations
- **Key Method:** `updateUser(Long userId, @RequestBody UpdateUserRequest)`
- **Responsibility:** Accept requests, coordinate validation, invoke service, format responses
- **HTTP Mapping:** `PUT /api/users/{userId}`

### 2. UserService (Business Logic Layer)
- **Role:** Orchestrate profile update workflow with authorization and validation
- **Key Method:** `updateUser(Long userId, UpdateUserRequest request, Authentication auth)`
- **Responsibility:** Enforce authorization, validate uniqueness, coordinate persistence
- **Transaction Scope:** Single @Transactional boundary for consistency

### 3. UpdateUserRequest DTO (Request Model)
- **Role:** Data transfer object for client requests
- **Fields:** name, email, role (admin only), active (admin only)
- **Validation:** Bean Validation annotations for format/length checks
- **Pattern:** Supports partial updates (null fields = no change)

### 4. UserRepository (Data Access Layer)
- **Role:** Abstract database operations for User entity
- **Key Methods:** findById(), save(), existsByEmailAndIdNot()
- **Pattern:** Spring Data JPA repository with custom query methods

### 5. User Entity (Domain Model)
- **Role:** JPA entity representing user profile
- **Fields:** id, name, email, role, active
- **Constraints:** Email unique constraint at database level

### 6. UserResponse DTO (Response Model)
- **Role:** Data transfer object for API responses
- **Fields:** id, name, email, role, active
- **Pattern:** Clean API contract excluding internal fields

---

## Component Responsibilities Matrix

| Component | Authorization | Validation | Persistence | Error Handling |
|-----------|---|---|---|---|
| UserController | No | Input validation | No | Delegates to GlobalExceptionHandler |
| UserService | **YES** | Business rule validation | No (delegates) | Throws custom exceptions |
| UpdateUserRequest | No | Bean Validation annotations | No | Declarative validation |
| UserRepository | No | No | **YES** | Transparent exception handling |
| User Entity | No | JPA constraints | Via repository | Database constraint violations |
| UserResponse | No | No | No | Serialization only |

---

## Authorization Design

### Role-Based Access Control (RBAC)

**Two User Roles:**
- **ROLE_USER** - Regular user (can update own profile fields: name, email)
- **ROLE_ADMIN** - Administrator (can update any user, all fields)

### Authorization Rules

| Scenario | Authenticated User | Authenticated Role | Target User | Fields | Result |
|---|---|---|---|---|---|
| Self-update name | User A (ID: 1) | ROLE_USER | User A (ID: 1) | name, email | ✅ Allow |
| Self-update role | User A (ID: 1) | ROLE_USER | User A (ID: 1) | role | ❌ Deny (403) |
| Self-update active | User A (ID: 1) | ROLE_USER | User A (ID: 1) | active | ❌ Deny (403) |
| Other user update | User A (ID: 1) | ROLE_USER | User B (ID: 2) | name, email | ❌ Deny (403) |
| Admin any update | Admin (ID: 3) | ROLE_ADMIN | Any user | Any field | ✅ Allow |
| Admin role change | Admin (ID: 3) | ROLE_ADMIN | Any user | role | ✅ Allow |
| Admin active change | Admin (ID: 3) | ROLE_ADMIN | Any user | active | ✅ Allow |

### Authorization Implementation Pattern

```
UserService.updateUser()
    ├─ Extract authenticated user (userId, role) from Authentication
    ├─ Check: is authenticated user admin?
    │   ├─ YES → Allow all updates
    │   └─ NO → Continue checks
    ├─ Check: is updating own profile?
    │   ├─ NO → Throw UnauthorizedException (403)
    │   └─ YES → Continue checks
    ├─ Check: request includes admin-only fields (role, active)?
    │   ├─ YES → Throw UnauthorizedException (403)
    │   └─ NO → Allow update
    └─ Proceed to validation and persistence
```

---

## Validation Design

### Validation Layers

**Layer 1: Request DTO Validation (declarative)**
- Triggered by Spring's @Valid annotation
- Applied by Bean Validation framework
- Annotations: @Size, @Email on UpdateUserRequest fields
- Violations return 400 Bad Request with field-level errors

**Layer 2: Business Rule Validation (programmatic)**
- Implemented in UserService
- Email uniqueness check before update
- User existence check
- Role value validation

### Validation Rules

| Field | Rules | Error | HTTP Status |
|-------|-------|-------|------------|
| name | Optional, max 100 chars if provided | Validation error | 400 |
| email | Optional, valid email format, unique if provided | Validation error (format) | 400 |
| email | Optional, valid email format, unique if provided | Email exists | 409 |
| role | Optional, valid enum value if provided (admin only) | Invalid role | 400 |
| active | Optional, boolean value (admin only) | Cannot change | 403 |

### Email Uniqueness Strategy

**Pre-Check Pattern:**
```
if (request.email != null) {
    boolean exists = userRepository.existsByEmailAndIdNot(request.email, userId);
    if (exists) {
        throw EmailAlreadyExistsException("Email already in use");
    }
}
```

**Benefits:**
- Returns 409 Conflict (meaningful) vs database constraint violation
- Better user experience with clear error message
- Prevents race conditions (within transaction)
- Reduces database constraint violation errors

---

## Data Flow Design

### Request Flow (Success Path)

```
1. HTTP Request
   └─ PUT /api/users/1
   └─ Authentication: Basic auth
   └─ Body: { "name": "New Name", "email": "newemail@example.com" }

2. Spring DispatcherServlet
   └─ Routes to UserController.updateUser()

3. Spring Binding & Validation
   └─ Deserialize JSON to UpdateUserRequest
   └─ Apply Bean Validation (@Email, @Size)
   └─ Return 400 if validation fails

4. UserController.updateUser()
   ├─ Extract userId from path (userId=1)
   ├─ Get authenticated user from SecurityContext
   └─ Call UserService.updateUser(1, request, authUserId, authRole)

5. UserService.updateUser()
   ├─ checkUpdateAuthorization(1, authUserId, authRole, request)
   │  └─ Return 403 if unauthorized
   ├─ UserRepository.findById(1)
   │  └─ Return 404 if not found
   ├─ validateEmailUniqueness("newemail@example.com", 1)
   │  └─ Return 409 if not unique
   ├─ User.setName("New Name")
   ├─ User.setEmail("newemail@example.com")
   ├─ UserRepository.save(user)
   │  └─ BEGIN TRANSACTION
   │  └─ UPDATE users SET name=?, email=? WHERE id=1
   │  └─ COMMIT TRANSACTION
   └─ Return UserResponse with updated profile

6. UserController
   └─ Return ResponseEntity.ok(userResponse)

7. Spring ResponseBodyHandler
   └─ Serialize UserResponse to JSON
   └─ Set Content-Type: application/json

8. HTTP Response
   └─ 200 OK
   └─ Body: { "id": 1, "name": "New Name", "email": "newemail@example.com", ... }

9. Client
   └─ Receives updated profile
```

### Error Flow (Unauthorized)

```
1. HTTP Request
   └─ PUT /api/users/2 (different user)
   └─ Authenticated as: userId=1, role=ROLE_USER

2. UserController → UserService

3. UserService.checkUpdateAuthorization()
   ├─ Is admin? NO
   ├─ Is self-update? (1 == 2?) NO
   └─ Throw UnauthorizedException("You can only update your own profile")

4. Exception bubbles up

5. GlobalExceptionHandler.handleUnauthorizedException()
   └─ Build error response: 403 Forbidden

6. HTTP Response
   └─ 403 Forbidden
   └─ Body: { "error": "Unauthorized", "message": "You can only update your own profile" }
```

---

## Transaction Design

### Transactional Boundary

```
@Transactional
public UserResponse updateUser(...)
├─ BEGIN TRANSACTION
│
├─ Read operation: UserRepository.findById(userId)
│  └─ User entity loaded in managed state
│
├─ Read operation: UserRepository.existsByEmailAndIdNot(email, userId)
│  └─ Email uniqueness check
│
├─ Memory operation: User.setters()
│  └─ Entity changes tracked by Hibernate
│
├─ Write operation: UserRepository.save(user)
│  └─ Hibernate flush() triggered
│  └─ UPDATE or INSERT executed
│
├─ Return UserResponse
│
└─ COMMIT TRANSACTION (if no exception)
   OR
   ROLLBACK TRANSACTION (if exception occurs)
```

**Benefits:**
- All operations atomic (all succeed or all fail)
- Email uniqueness guaranteed (even with concurrent requests)
- Dirty checking prevents unnecessary database updates
- Automatic rollback on exceptions

---

## Component Dependency Map

```
┌────────────────────────────────────────────────────┐
│ Spring Boot Infrastructure                          │
│ ├─ Spring Web (REST)                              │
│ ├─ Spring Security (Auth/AuthZ)                   │
│ ├─ Spring Data JPA (Persistence)                  │
│ ├─ Jakarta Bean Validation                        │
│ └─ Hibernate (ORM)                                │
└────────────────────────────────────────────────────┘
                        ↑
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ UserController│ │ UserService  │  │ GlobalException  │
│              │  │              │  │ Handler          │
│ @RestController│ │ @Service     │  │ @ControllerAdvice│
│ PUT /api/... │  │ @Transactional│  │                  │
└──────┬───────┘  └──────┬───────┘  └────────┬─────────┘
       │                 │                   │
       ├─────────────────┤                   │
       │                 │                   │
       │          DTOs:  ├→ UpdateUserRequest
       │          ├─────→├→ UserResponse
       │          │      │
       │          └──────┤── Authorization
       │                 ├── Validation
       │                 │
       │                 ▼
       │         ┌──────────────┐
       │         │ UserRepository
       │         │              │
       │         │ @Repository  │
       │         └──────┬───────┘
       │                │
       │       ORM      │
       │                ▼
       │         ┌──────────────┐
       │         │ User Entity  │
       │         │              │
       │         │ @Entity      │
       │         └──────┬───────┘
       │                │
       │       Persist  │
       │                ▼
       │         ┌──────────────┐
       │         │ H2 Database  │
       │         │ users table  │
       │         └──────────────┘
       │
       └─ Exception handling integration
```

---

## Service Layer Design

### UserService Responsibilities

```
UserService (Singleton, @Transactional)
├─ Authorization Enforcement
│  ├─ Check user role (ROLE_USER vs ROLE_ADMIN)
│  ├─ Check self-update vs admin update
│  └─ Restrict admin-only fields for regular users
│
├─ Validation Coordination
│  ├─ Email uniqueness check (pre-check pattern)
│  ├─ Field validation (delegated to Bean Validation)
│  ├─ Business rule validation
│  └─ User existence validation
│
├─ Data Access Coordination
│  ├─ UserRepository.findById() - load user
│  ├─ UserRepository.existsByEmailAndIdNot() - check email
│  ├─ UserRepository.save() - persist changes
│  └─ Manage entity lifecycle
│
├─ Transaction Management
│  ├─ Single @Transactional boundary
│  ├─ Automatic rollback on exception
│  └─ Coordinate read + write operations
│
└─ Exception Translation
   ├─ Throw UnauthorizedException (403)
   ├─ Throw UserNotFoundException (404)
   ├─ Throw EmailAlreadyExistsException (409)
   └─ Throw ValidationException (400)
```

### Service Interaction Pattern

```
Request → UserController → UserService → Repository → Database
                                ↓
                        Authorization Check
                                ↓
                        Validation Layer
                                ↓
                        Data Access Layer
                                ↓
                        Transaction Management
                                ↓
                        Exception Translation
                                ↓
        Response → UserController ← UserService
```

---

## Error Handling Design

### Exception Mapping

| Exception | Scenario | HTTP Status | GlobalExceptionHandler |
|-----------|----------|------------|--------|
| UnauthorizedException | Authorization failure | 403 Forbidden | Maps to 403 response |
| UserNotFoundException | User doesn't exist | 404 Not Found | Maps to 404 response |
| EmailAlreadyExistsException | Email not unique | 409 Conflict | Maps to 409 response |
| ConstraintViolationException | Bean validation fails | 400 Bad Request | Maps to 400 with field errors |
| Other RuntimeExceptions | Unexpected errors | 500 Server Error | Generic error response |

### Exception Flow

```
UserService throws exception
    ↓
Exception propagates through Spring stack
    ↓
GlobalExceptionHandler @ExceptionHandler methods match exception type
    ↓
Handler builds error response:
    ├─ HTTP status code
    ├─ Error message
    ├─ Field-level errors (if validation)
    └─ Request correlation ID (if configured)
    ↓
Spring serializes error response to JSON
    ↓
HTTP response with error details
```

---

## Design Decisions & Rationale

### Decision 1: Single DTO for All Updates
**Choice:** Use UpdateUserRequest DTO with optional fields (null = no change)
**Rationale:**
- Supports partial updates flexibly
- Single endpoint handles all scenarios
- Reduces API surface complexity
- Aligns with REST PATCH semantics while using PUT

### Decision 2: Pre-Check Email Uniqueness
**Choice:** Query before update (vs relying on database constraint)
**Rationale:**
- Returns 409 Conflict (meaningful) vs generic database constraint error
- Better user experience with clear error message
- Prevents confusing constraint violation exceptions
- Within transaction, prevents race conditions

### Decision 3: Authorization at Service Layer
**Choice:** Implement authorization logic in UserService (not controller)
**Rationale:**
- Centralized authorization logic
- Protects against direct repository access
- Easier to test and maintain
- Aligns with Spring Boot best practices

### Decision 4: Single @Transactional Boundary
**Choice:** Entire updateUser() method in single transaction
**Rationale:**
- Ensures atomicity of all operations
- Email uniqueness guaranteed with concurrent requests
- Automatic rollback on exceptions
- Simplifies error handling

### Decision 5: Leverage Existing Infrastructure
**Choice:** Use existing GlobalExceptionHandler, SecurityConfig, etc.
**Rationale:**
- Maintains architectural consistency
- Reduces new code complexity
- Aligns with brownfield development
- Leverages proven patterns

---

## Integration Points

### Spring Security Integration
- Extract authenticated user from SecurityContext
- Access user ID and role for authorization
- Thread-local access (no explicit passing needed)

### Exception Handling Integration
- UserService throws custom exceptions
- GlobalExceptionHandler translates to HTTP responses
- Maintains consistent error response format

### Repository Integration
- UserService calls UserRepository methods
- JPA handles entity lifecycle and persistence
- Hibernate executes SQL queries

### Bean Validation Integration
- @Valid annotation triggers validation
- Validation annotations on UpdateUserRequest
- Spring returns 400 with field errors on validation failure

---

## Testing Strategy

### Unit Testing
- UserService business logic (authorization, validation)
- Mock UserRepository for data access
- Mock SecurityContext for authentication

### Integration Testing
- UserController REST endpoints
- Complete request/response flow
- Real UserService and UserRepository
- In-memory H2 database

### Security Testing
- Authorization enforcement (self-update, admin override)
- Admin-only field restrictions
- Unauthorized access denial

### Validation Testing
- Email uniqueness (duplicate prevention)
- Field validation (format, length)
- Error response formats

---

## Implementation Roadmap

### Phase 1: Enhance DTOs
- [ ] Add name, email, role, active fields to UpdateUserRequest
- [ ] Add Bean Validation annotations
- [ ] Verify UserResponse includes all fields

### Phase 2: Implement UserService
- [ ] Implement updateUser() method with authorization
- [ ] Implement validateEmailUniqueness() helper
- [ ] Implement checkUpdateAuthorization() helper
- [ ] Add appropriate exception throwing

### Phase 3: Implement UserController
- [ ] Add @PutMapping("/api/users/{userId}") endpoint
- [ ] Extract authentication info and pass to UserService
- [ ] Return UserResponse with 200 OK

### Phase 4: Enhance UserRepository
- [ ] Add existsByEmailAndIdNot() custom query method
- [ ] Ensure findById() and save() available

### Phase 5: Add Comprehensive Tests
- [ ] Unit tests for UserService
- [ ] Integration tests for UserController
- [ ] Security tests for authorization
- [ ] Validation tests for all error scenarios

---

## Compliance & Consistency

### Alignment with Requirements

✅ **FR1: Profile Update Endpoint** - PUT /api/users/{userId}  
✅ **FR2: Updatable Fields** - name, email, role (admin), active (admin)  
✅ **FR3: Request Validation** - Bean Validation + business rules  
✅ **FR4: Authorization Rules** - Self-update + admin override  
✅ **FR5: Response Format** - UserResponse DTO with all fields  
✅ **FR6: Error Handling** - 400, 403, 404, 409 status codes  

### Alignment with Existing Architecture

✅ **3-Tier Architecture** - Controller → Service → Repository  
✅ **Spring Boot Patterns** - @RestController, @Service, @Repository  
✅ **Security Model** - Uses existing SecurityConfig and UserDetailsService  
✅ **Exception Handling** - Integrates with GlobalExceptionHandler  
✅ **Database Layer** - Uses existing JPA and H2 setup  
✅ **Validation Framework** - Uses Jakarta Bean Validation  

---

## Summary

The application design for the profile update feature provides a complete blueprint for implementation:

1. **Components:** Six components working together in a 3-tier architecture
2. **Authorization:** Role-based access control with clear rules
3. **Validation:** Multi-layer validation (declarative + programmatic)
4. **Transactions:** Single @Transactional boundary for consistency
5. **Error Handling:** Custom exceptions translated to HTTP responses
6. **Integration:** Seamless integration with existing Spring Boot infrastructure

This design is ready for implementation in the CONSTRUCTION phase, where detailed business logic and unit-of-work specifications will be defined.
