# Component Dependency Analysis - Profile Update Feature

## Overview

This document defines the dependency relationships, communication patterns, and data flow for components involved in the profile update feature.

---

## Dependency Matrix

### Direct Dependencies

| Component | Depends On | Relationship Type | Cardinality |
|-----------|-----------|------------------|------------|
| UserController | UserService | Direct Method Call | 1:1 |
| UserController | Spring Security | Framework Integration | 1:N |
| UserController | GlobalExceptionHandler | Error Handling | 1:1 |
| UserService | UserRepository | Data Access | 1:1 |
| UserService | Spring Security | Authorization | 1:1 |
| UserService | UpdateUserRequest | Data Transfer | 1:1 |
| UserService | User | Domain Model | 1:N |
| UserService | UserResponse | Data Transfer | 1:N |
| UserRepository | User | ORM Mapping | 1:N |
| UpdateUserRequest | (Bean Validation) | Declarative Validation | 1:N |
| User | H2 Database | Persistence | 1:N |

### Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│ External: Spring Boot Framework                             │
│   - Spring Web (REST)                                       │
│   - Spring Security (Authentication/Authorization)          │
│   - Spring Data JPA (Repository Pattern)                    │
│   - Jakarta Bean Validation                                 │
│   - Hibernate (ORM)                                         │
└─────────────────────────────────────────────────────────────┘
                            ↑
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ↓                   ↓                   ↓
    ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐
    │ UserController│  │ UserService  │   │ GlobalException  │
    │              │  │              │   │ Handler          │
    │ @RestController│ │ @Service     │   │                  │
    │ @PutMapping  │  │ @Transactional│  │ @ControllerAdvice│
    └────────┬─────┘  └──────┬───────┘   └────────┬─────────┘
             │                │                   │
             │ HTTP Request   │                   │
             │ Validation     │ Injects           │ Catches
             │                │                   │
             ├────────────────┤ Authorization     │ Exceptions
             │                │ Data Access       │
             │                │ Persistence       │
             │                ↓ Entity Mapping    │
             │         ┌──────────────────┐       │
             │         │ UserRepository   │       │
             │         │                  │       │
             │         │ @Repository      │       │
             │         │ extends JpaRepo  │       │
             │         └────────┬─────────┘       │
             │                  │                 │
             │    Uses ORM      │                 │
             │                  ↓                 │
             │         ┌──────────────────┐       │
             │         │ User Entity      │       │
             │         │                  │       │
             │         │ @Entity          │       │
             │         │ JPA Annotations  │       │
             │         └────────┬─────────┘       │
             │                  │                 │
             │         Persists │                 │
             │                  ↓                 │
             │         ┌──────────────────┐       │
             │         │ H2 Database      │       │
             │         │ users table      │       │
             │         └──────────────────┘       │
             │                                    │
             ├────────────────────────────────────┤
             │                                    │
             │ DTOs                              │
             │ ─────────────────────────          │
             ├──→ UpdateUserRequest              │
             │    (from JSON)                    │
             │    Bean Validation                │
             │    Annotations                    │
             │                                    │
             └──→ UserResponse                   │
                  (to JSON)                      │
                  Serialization                  │
```

---

## Component Communication Patterns

### Pattern 1: REST Request/Response Flow

**Sequence:**
```
1. Client sends HTTP PUT request with UpdateUserRequest JSON
   └─ /api/users/{userId}
   └─ Content-Type: application/json
   └─ Body: { "name": "...", "email": "..." }

2. Spring Dispatcher routes to UserController.updateUser()

3. Spring binds JSON to UpdateUserRequest DTO
   └─ @RequestBody deserialization
   └─ Bean Validation annotations applied

4. UserController calls UserService.updateUser()
   └─ Passes request + authentication info

5. UserService:
   └─ Checks authorization against security context
   └─ Loads user via UserRepository.findById()
   └─ Validates email uniqueness via UserRepository.existsByEmailAndIdNot()
   └─ Saves updated user via UserRepository.save()
   └─ Converts to UserResponse DTO

6. UserController receives UserResponse
   └─ Spring serializes to JSON
   └─ Returns HTTP 200 OK

7. Client receives updated user profile
```

### Pattern 2: Authorization Check Flow

**Decision Tree:**
```
UserService receives update request
    │
    ├─ Is authenticated user an admin?
    │   ├─ YES → Allow all updates to any user
    │   │         Continue to validation
    │   └─ NO → Is updating own profile?
    │           ├─ YES → Check for admin-only fields
    │           │        ├─ Requesting role/active update?
    │           │        │   ├─ YES → Throw UnauthorizedException (403)
    │           │        │   └─ NO → Continue to validation
    │           │        └─ Allow name/email updates only
    │           └─ NO → Throw UnauthorizedException (403)
    │
    ▼
Proceed to validation
```

### Pattern 3: Email Uniqueness Validation

**Flow:**
```
UserService.validateEmailUniqueness() called
    │
    └─ Request email provided?
        ├─ NO → Skip validation
        └─ YES → UserRepository.existsByEmailAndIdNot()
                    │
                    └─ Database query:
                        SELECT COUNT(*) > 0 FROM users
                        WHERE email = ? AND id != ?
                    │
                    ├─ Result: true (email exists for another user)
                    │   └─ Throw EmailAlreadyExistsException (409)
                    │
                    └─ Result: false (email unique)
                        └─ Continue to update
```

### Pattern 4: Transaction & Persistence Flow

**Transactional Boundary:**
```
@Transactional
UserService.updateUser()
    │
    ├─ BEGIN TRANSACTION
    │
    ├─ UserRepository.findById()
    │   └─ Loads user in managed state
    │
    ├─ User entity setters called
    │   └─ Entity marked dirty (changes tracked)
    │
    ├─ UserRepository.save()
    │   └─ Triggers Hibernate flush
    │   └─ INSERT/UPDATE executed in database
    │
    ├─ Return UserResponse
    │
    └─ COMMIT TRANSACTION
        (if exception occurs: ROLLBACK)
```

### Pattern 5: Error Handling Flow

**Exception Translation:**
```
UserService throws exception
    │
    ├─ UnauthorizedException (authorization failed)
    │   └─ GlobalExceptionHandler catches
    │   └─ Returns HTTP 403 Forbidden
    │
    ├─ UserNotFoundException (user not found)
    │   └─ GlobalExceptionHandler catches
    │   └─ Returns HTTP 404 Not Found
    │
    ├─ EmailAlreadyExistsException (not unique)
    │   └─ GlobalExceptionHandler catches
    │   └─ Returns HTTP 409 Conflict
    │
    ├─ ConstraintViolationException (validation)
    │   └─ GlobalExceptionHandler catches
    │   └─ Returns HTTP 400 Bad Request
    │   └─ Includes field-level errors
    │
    └─ Other exceptions
        └─ GlobalExceptionHandler catches
        └─ Returns HTTP 500 Internal Server Error
```

---

## Data Flow Diagram

### Successful Profile Update Flow

```
Request Phase:
    HTTP PUT /api/users/1
    ├─ Header: Authorization: Basic ...
    └─ Body: UpdateUserRequest JSON
        │
        ▼
    Spring DispatcherServlet
    Spring Binding & Validation
    ├─ Deserialize JSON → UpdateUserRequest
    ├─ Apply @Size, @Email annotations
    └─ Inject into UserController
        │
        ▼
    UserController.updateUser()
    ├─ Extract userId = 1 from path
    ├─ Get authenticated user from SecurityContext
    └─ Call UserService.updateUser()

Processing Phase:
        │
        ▼
    UserService.updateUser()
    ├─ checkUpdateAuthorization()
    │   ├─ Is admin? OR is self-update? ✓
    │   └─ Allow only updatable fields? ✓
    ├─ UserRepository.findById(1)
    │   └─ SELECT * FROM users WHERE id=1 ✓
    ├─ validateEmailUniqueness()
    │   ├─ Email provided? ✓
    │   └─ UserRepository.existsByEmailAndIdNot()
    │       └─ SELECT COUNT(*) > 0 FROM users 
    │          WHERE email='newemail@example.com' AND id!=1
    │       └─ Result: false ✓ (unique)
    ├─ Build updated User entity
    │   ├─ user.setName("new name")
    │   ├─ user.setEmail("newemail@example.com")
    │   └─ Entity marked dirty
    └─ UserRepository.save(user)
        ├─ BEGIN TRANSACTION
        ├─ UPDATE users SET name=?, email=? WHERE id=1
        ├─ COMMIT TRANSACTION
        └─ Return managed User entity

Response Phase:
        │
        ▼
    UserService returns UserResponse
    ├─ id: 1
    ├─ name: "new name"
    ├─ email: "newemail@example.com"
    ├─ role: "ROLE_USER"
    └─ active: true
        │
        ▼
    UserController.updateUser()
    ├─ Receives UserResponse
    └─ Returns ResponseEntity<UserResponse>
        │
        ▼
    Spring ResponseBodyHandler
    ├─ Serialize UserResponse to JSON
    └─ Set Content-Type: application/json
        │
        ▼
    HTTP Response 200 OK
    └─ Body: UserResponse JSON
```

### Error Flow - Authorization Failure

```
Request Phase:
    HTTP PUT /api/users/999 (different user)
    ├─ Authenticated as: userId=1, role=ROLE_USER
    └─ Body: UpdateUserRequest {...}
        │
        ▼
    UserController.updateUser()
    ├─ Extract userId = 999
    ├─ Get authenticated userId = 1
    └─ Call UserService.updateUser()

Processing Phase:
        │
        ▼
    UserService.updateUser()
    ├─ checkUpdateAuthorization()
    │   ├─ Is admin? NO
    │   ├─ Is self-update? (1 == 999?) NO
    │   └─ Throw UnauthorizedException ✗
        │
        ▼
    Exception bubbles up

Error Handling Phase:
        │
        ▼
    GlobalExceptionHandler
    ├─ Catches UnauthorizedException
    ├─ Builds error response:
    │   ├─ HTTP Status: 403 Forbidden
    │   ├─ Body: { "error": "Unauthorized" }
    │   └─ Message: "You can only update your own profile"
    └─ Returns ResponseEntity with error
        │
        ▼
    HTTP Response 403 Forbidden
    └─ Body: Error JSON
```

---

## Dependency Management Strategy

### Circular Dependencies
**Prevention:** None identified. Architecture is acyclic:
```
UserController → UserService → UserRepository → Database
              ↓              ↓
        Spring Security
              ↓
        Exception Handler
```

### Loose Coupling
**Techniques Used:**

1. **Dependency Injection**
   - UserService injected into UserController via @Autowired
   - Enables testing with mock UserService
   - Decouples implementations from interfaces

2. **DTO Layer**
   - UpdateUserRequest decouples client API from internal models
   - UserResponse decouples response format from User entity
   - Allows independent evolution of DTOs vs entities

3. **Repository Abstraction**
   - UserRepository interface abstracts database access
   - H2 database can be swapped for production database
   - Query logic isolated from business logic

4. **Exception Abstraction**
   - Custom exceptions (UnauthorizedException, etc.) decouple service from HTTP
   - GlobalExceptionHandler translates to HTTP responses
   - Service layer unaware of HTTP concerns

### Interface Contracts

**UserController Interface:**
```java
PUT /api/users/{userId}
Content-Type: application/json
Request: UpdateUserRequest
Response: UserResponse (200 OK)
Errors: 400, 403, 404, 409
```

**UserService Interface:**
```java
UserResponse updateUser(
    Long userId,
    UpdateUserRequest request,
    Long authenticatedUserId,
    String authenticatedUserRole
)
Exceptions: UnauthorizedException, UserNotFoundException, 
            EmailAlreadyExistsException, ValidationException
```

**UserRepository Interface (JPA):**
```java
Optional<User> findById(Long id)
User save(User entity)
boolean existsByEmailAndIdNot(String email, Long userId)
```

---

## Data Flow Summary

| Flow | Source | Destination | Type | Triggering Event |
|------|--------|------------|------|-----------------|
| HTTP Request | Client | UserController | JSON | HTTP PUT |
| UpdateUserRequest | Spring | UserController | DTO | Request deserialization |
| Authorization Info | SecurityContext | UserService | Authentication | Controller invocation |
| User Entity | UserRepository | UserService | Domain Model | findById() call |
| Email Check Query | UserService | UserRepository | Query | validationEmailUniqueness() |
| Updated User | UserService | UserRepository | Entity | save() call |
| SQL Update | Hibernate | H2 Database | SQL | save() execution |
| UserResponse | UserService | UserController | DTO | Update completion |
| JSON Response | Spring | Client | JSON | Controller response |
| Exceptions | UserService | GlobalExceptionHandler | Exception | Error condition |
| Error Response | GlobalExceptionHandler | Client | JSON | Exception handling |

---

## Deployment & Dependency Injection

### Dependency Injection Tree

```
Spring Container
│
├─ UserController (singleton)
│  └─ @Autowired UserService
│
├─ UserService (singleton)
│  └─ @Autowired UserRepository
│
├─ UserRepository (proxy)
│  └─ Managed by Spring Data JPA
│
├─ DataSource
│  └─ H2 Database Connection Pool
│
└─ SecurityContext
   └─ Thread-local authentication info
```

### Bean Lifecycle

```
1. Spring scans for @Service, @Repository, @RestController
2. UserService bean created, UserRepository injected
3. UserController bean created, UserService injected
4. ApplicationContext ready to handle requests
5. On request: SecurityContext populated with user info
6. UserController method invoked
7. After request: Transaction commits/rolls back
```

---

## Summary

The component dependency architecture for profile updates is:

1. **Layered**: REST → Service → Repository → Database
2. **Loosely Coupled**: Via DTOs, interfaces, and dependency injection
3. **Transactional**: Single @Transactional boundary for consistency
4. **Exception Handling**: Service exceptions translated to HTTP responses
5. **Security Integrated**: Authorization checks at service layer
6. **Data Flow**: Unidirectional from request to response with error branches

This design ensures maintainability, testability, and alignment with existing Spring Boot architectural patterns.
