# Unit of Work Dependencies - Profile Update Feature

## Overview

This document analyzes the dependencies, integration points, and relationships for the Profile Update Service unit. Since this is a single-unit feature, this document primarily addresses internal component dependencies and integration with existing infrastructure.

---

## Unit Dependency Matrix

### Single Unit Definition

**Unit Name:** profile-update-service  
**Dependencies Count:** 6 internal components + 5 external infrastructure components  
**Coupling Level:** Low (via interfaces and Spring injection)  
**Circular Dependencies:** None identified

---

## Internal Component Dependencies

### Dependency Graph

```
External: Spring Boot Infrastructure
    │
    ├─ Spring Web (REST)
    ├─ Spring Security (Auth/AuthZ)
    ├─ Spring Data JPA (Persistence)
    ├─ Jakarta Bean Validation (Input Validation)
    └─ Hibernate/H2 (ORM/Database)
            │
            ▼
┌─────────────────────────────────────────────────┐
│ Profile Update Service Unit                      │
│                                                  │
│  ┌────────────────────────────────────┐          │
│  │ Presentation Layer                  │         │
│  │ UserController                      │         │
│  │  ├─ @RestController                │         │
│  │  ├─ @PutMapping("/api/users/...")  │         │
│  │  └─ Coordinates with UserService   │         │
│  └────────────────────────────────────┘         │
│         │                      │                 │
│         ├─────────────────────────────────┐     │
│         │                                 │     │
│         ▼                                 ▼     │
│  ┌──────────────────────┐        ┌───────────────┐
│  │ UpdateUserRequest    │        │ UserResponse  │
│  │ (Request DTO)        │        │ (Response DTO)│
│  │                      │        │               │
│  │ Bean Validation      │        │ Serialization │
│  │ Annotations          │        │               │
│  └──────────────────────┘        └───────────────┘
│         ▲
│         │ Spring deserializes
│         │
│  ┌──────────────────────────────────┐
│  │ Business Logic Layer              │
│  │ UserService                       │
│  │  ├─ @Service                      │
│  │  ├─ @Transactional                │
│  │  ├─ Authorization logic           │
│  │  ├─ Validation logic              │
│  │  └─ Orchestration                 │
│  └──────────────────────────────────┘
│         │
│         ├─────────────────────────────┐
│         │                             │
│         ▼                             ▼
│  ┌────────────────────┐      ┌──────────────┐
│  │ UserRepository     │      │ Spring       │
│  │ (Data Access)      │      │ Security     │
│  │                    │      │              │
│  │ @Repository        │      │ Extract auth │
│  │ JPA Queries        │      │ context      │
│  └────────────────────┘      └──────────────┘
│         │
│         ▼
│  ┌────────────────────┐
│  │ User Entity        │
│  │ (Domain Model)     │
│  │                    │
│  │ @Entity            │
│  │ JPA Annotations    │
│  └────────────────────┘
│         │
│         ▼
│  ┌────────────────────┐
│  │ H2 Database        │
│  │                    │
│  │ users table        │
│  └────────────────────┘
│
└─────────────────────────────────────────────────┘
```

### Component Dependency Details

| Component | Depends On | Type | Purpose | Coupling |
|-----------|-----------|------|---------|----------|
| UserController | UserService | Direct | Business logic | Loose (Spring injection) |
| UserController | Spring Security | Framework | Authentication | Framework (standard) |
| UserController | GlobalExceptionHandler | Framework | Error handling | Framework (via Spring) |
| UpdateUserRequest | Bean Validation | Framework | Input validation | Declarative (annotations) |
| UserService | UserRepository | Direct | Data access | Loose (Spring injection) |
| UserService | User Entity | Direct | Domain model | Direct (parameter) |
| UserService | Spring Security Context | Framework | Authorization | Framework (thread-local) |
| UserService | UpdateUserRequest | Direct | Request data | Parameter (no lifecycle) |
| UserService | UserResponse | Direct | Response data | Factory pattern (no dependency) |
| UserRepository | User Entity | ORM | Persistence mapping | ORM framework (JPA) |
| User Entity | H2 Database | Persistence | Table mapping | ORM framework (JPA) |
| UserResponse | (none) | DTO | Response serialization | None (simple POJO) |

---

## Dependency Flow Analysis

### Request Processing Flow (Dependencies)

```
1. HTTP Request arrives
   └─ Spring DispatcherServlet routes to UserController
   
2. UserController accepts request
   ├─ Depends on: Spring Web, @RequestMapping
   ├─ Uses: UpdateUserRequest (Spring deserializes)
   └─ Depends on: Bean Validation (validates @Valid)
   
3. Spring Security Context injection
   ├─ Depends on: Spring Security
   └─ Provides: Authentication info (userId, role)
   
4. UserController calls UserService
   ├─ Dependency: UserService (injected via @Autowired)
   └─ Passes: userId, request, auth info
   
5. UserService authorization logic
   ├─ Depends on: Spring Security Context (thread-local)
   ├─ Performs: Role-based access control (RBAC)
   └─ Calls: checkUpdateAuthorization() helper
   
6. UserService data validation
   ├─ Depends on: UserRepository for email check
   ├─ Calls: UserRepository.existsByEmailAndIdNot()
   └─ Calls: UserRepository.findById()
   
7. UserService persistence
   ├─ Depends on: UserRepository for save
   ├─ Depends on: User Entity (domain model)
   ├─ Calls: UserRepository.save(user)
   └─ Depends on: @Transactional (Spring)
   
8. Persistence execution
   ├─ Depends on: Hibernate (ORM)
   ├─ Depends on: H2 Database (persistence)
   └─ Executes: SQL UPDATE/INSERT
   
9. Response preparation
   ├─ Depends on: UserResponse DTO
   ├─ Creates: UserResponse from User entity
   └─ Returns to UserController
   
10. Spring serialization
    ├─ Depends on: Jackson (JSON serialization)
    ├─ Serializes: UserResponse to JSON
    └─ Returns to client
```

### Error Handling Dependencies

```
Exception occurs in UserService
    └─ UnauthorizedException
    └─ UserNotFoundException
    └─ EmailAlreadyExistsException
    └─ ValidationException
            ↓
Propagates up through Spring Stack
            ↓
GlobalExceptionHandler catches
    ├─ Depends on: Spring framework @ExceptionHandler
    ├─ Maps: Exception to HTTP status code
    └─ Returns: Error response
            ↓
Spring serializes error to JSON
            ↓
Client receives error response
```

---

## External Infrastructure Dependencies

### Spring Boot Infrastructure Integration

| Infrastructure | Component | Integration Type | Purpose | Impact on Unit |
|---|---|---|---|---|
| Spring Web | UserController | Framework | REST endpoint handling | High (required) |
| Spring Security | UserService | Framework | Authentication/Authorization | High (required) |
| Spring Data JPA | UserRepository | Framework | Data access abstraction | High (required) |
| Jakarta Bean Validation | UpdateUserRequest | Framework | Input validation | Medium (enhanced validation) |
| Hibernate | UserRepository | ORM | Entity persistence | High (required) |
| H2 Database | User Entity | Persistence | Data storage | High (required) |
| Jackson | UserResponse | Serialization | JSON response | Medium (Spring auto-config) |
| Spring Context | All | Framework | Dependency injection | High (required) |

### No New External Dependencies

**Important:** This unit does NOT introduce any new external dependencies. All infrastructure is already present in the existing application:
- Spring Boot 3.2.3 ✅ (existing)
- Spring Security ✅ (existing)
- Spring Data JPA ✅ (existing)
- Jakarta Bean Validation ✅ (existing)
- Hibernate ✅ (existing)
- H2 Database ✅ (existing)
- Jackson ✅ (existing)

---

## Shared Component Ownership

### Shared Components Matrix

| Component | Owner | Location | Sharing Model | Unit Role | Access Pattern |
|-----------|-------|----------|---------------|-----------|----|
| User Entity | Data Model | Existing | Shared | Uses entity | Direct via JPA |
| UserRepository | Data Access | Existing | Shared | Uses interface | Spring injection |
| Spring Security Context | Infrastructure | Framework | Shared | Read-only access | Thread-local getter |
| GlobalExceptionHandler | Infrastructure | Existing | Shared | Delegates exceptions | Framework |
| H2 Database | Persistence | Existing | Shared | Write/read via ORM | Transaction boundary |

### Shared Component Usage Pattern

```
Profile Update Service Unit (Consumer)
    │
    ├─ Uses UserRepository (Spring injection)
    │   └─ Shared interface for data access
    │
    ├─ Uses User Entity (JPA mapping)
    │   └─ Shared domain model
    │
    ├─ Reads Spring Security Context (thread-local)
    │   └─ Shared authentication info
    │
    ├─ Delegates to GlobalExceptionHandler (framework)
    │   └─ Shared error handling
    │
    └─ Accesses H2 Database (via Hibernate)
        └─ Shared persistence layer
```

### Minimal Coupling Design

**Dependency Injection Approach:**
```java
@RestController
public class UserController {
    @Autowired
    private UserService userService;  // Loose coupling via interface
}

@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;  // Loose coupling via interface
    
    public UserResponse updateUser(...) {
        // Read Spring Security Context (framework provided)
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        // Service operates on User entity (passed as parameter)
        // Exceptions caught by GlobalExceptionHandler (framework)
    }
}
```

---

## Data Flow Between Components

### Success Path Data Flow

```
Client JSON Request
    ↓
Spring DispatcherServlet (HTTP routing)
    ↓
UpdateUserRequest DTO
    ├─ Input validation (Bean Validation)
    └─ Deserialization (Jackson)
    ↓
UserController.updateUser()
    ├─ Receives: userId, UpdateUserRequest
    ├─ Extracts: Authentication from SecurityContext
    └─ Calls: UserService.updateUser(userId, request, auth)
    ↓
UserService
    ├─ Authorization check (Spring Security Context)
    ├─ UserRepository.findById(userId) → User entity
    ├─ Email uniqueness check → boolean
    ├─ Apply field updates to User entity
    ├─ UserRepository.save(user) → persisted User
    └─ Convert User → UserResponse DTO
    ↓
UserRepository
    ├─ Hibernate ORM mapping
    ├─ SQL preparation and execution
    ├─ H2 Database transaction
    └─ Return managed User entity
    ↓
UserController
    ├─ Receives: UserResponse DTO
    └─ Returns: ResponseEntity<UserResponse>
    ↓
Spring JSON Serialization (Jackson)
    ├─ UserResponse serialization
    └─ Response body generation
    ↓
HTTP 200 OK Response
    └─ UserResponse JSON
```

### Error Path Data Flow

```
Exception in UserService
    └─ UnauthorizedException, UserNotFoundException, etc.
    ↓
Exception propagates through Spring Stack
    ├─ Spring Transaction rollback (if @Transactional)
    └─ Spring catches exception
    ↓
GlobalExceptionHandler
    ├─ Matches @ExceptionHandler for exception type
    ├─ Builds error response (HTTP status, message)
    └─ Returns ResponseEntity with error
    ↓
Spring JSON Serialization (Jackson)
    ├─ Error response serialization
    └─ Response body generation
    ↓
HTTP Error Response (400, 403, 404, 409)
    └─ Error JSON { "error": "...", "message": "..." }
```

---

## Transaction Boundary Management

### Single @Transactional Boundary

```
UserService.updateUser()
    │
    ├─ @Transactional annotation
    ├─ Spring creates transaction context
    │
    ├─ BEGIN TRANSACTION
    │
    ├─ UserRepository.findById()
    │   └─ SELECT query (within transaction)
    │
    ├─ Email uniqueness check
    │   └─ SELECT query (within transaction)
    │
    ├─ User entity modifications (in memory)
    │   └─ Hibernate tracks changes
    │
    ├─ UserRepository.save()
    │   ├─ Trigger Hibernate flush()
    │   ├─ Execute UPDATE/INSERT (within transaction)
    │   └─ Return managed entity
    │
    ├─ Build UserResponse (return preparation)
    │
    └─ COMMIT TRANSACTION (if no exception)
       OR ROLLBACK TRANSACTION (if exception occurs)
```

**Benefits:**
- Atomicity: All operations succeed or all fail
- Consistency: Email uniqueness guaranteed
- Isolation: Concurrent updates don't interfere
- Durability: Committed changes persist

---

## Dependency Resolution Order

### Component Initialization

```
1. Spring Container Startup
   ├─ Load application context
   └─ Scan for @Service, @Repository, @RestController
   
2. Infrastructure Components
   ├─ DataSource (H2 connection pool)
   ├─ TransactionManager (Spring)
   ├─ SecurityContext (Spring Security)
   └─ ExceptionHandler (GlobalExceptionHandler bean)
   
3. Unit Components (in dependency order)
   ├─ UserRepository
   │   └─ Depends on: DataSource, JPA configuration
   │
   ├─ UserService
   │   ├─ Depends on: UserRepository (injected)
   │   └─ Depends on: Spring context (injected)
   │
   └─ UserController
       └─ Depends on: UserService (injected)
   
4. Ready to accept HTTP requests
```

### Dependency Injection Chain

```
Spring discovers @RestController UserController
    └─ Finds @Autowired UserService dependency
       └─ Spring looks for UserService bean
          └─ Spring discovers @Service UserService
             └─ Finds @Autowired UserRepository dependency
                └─ Spring looks for UserRepository bean
                   └─ Spring discovers @Repository UserRepository
                      └─ Configured by Spring Data JPA
                         └─ Uses DataSource
                            └─ H2 connection pool
    
All dependencies resolved
    └─ ApplicationContext ready
       └─ UserController ready to receive requests
```

---

## Scaling & Future Dependencies

### Single-Unit Constraints

Currently this unit operates within monolithic constraints:
- Single database (H2/production DB)
- Single Spring Context
- Shared transaction boundaries
- All components in same JVM

### Potential Future Dependencies (if unit becomes microservice)

If this unit scales to independent microservice:
- Service-to-service communication (REST/gRPC)
- Distributed transactions (Saga pattern)
- Event messaging (if async)
- Separate database (if data model changes)
- Service discovery (if microservice architecture)

**Current Status:** Not applicable (monolithic deployment)

---

## Dependency Health Checklist

### Verification Checklist

- [x] No circular dependencies detected
- [x] All external dependencies already present
- [x] Loose coupling via Spring injection
- [x] Clear ownership of shared components
- [x] Single transactional boundary for consistency
- [x] Framework integration leverages existing infrastructure
- [x] Error handling via existing GlobalExceptionHandler
- [x] Data flow is unidirectional (no feedback loops)
- [x] Component initialization order valid
- [x] No new external dependencies introduced

### Dependency Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Database coupling | Low | Using standard JPA, can swap databases |
| Spring Security coupling | Low | Standard Spring pattern, can extend |
| UserRepository coupling | Low | Interface-based abstraction |
| User Entity coupling | Low | Stable domain model |
| GlobalExceptionHandler coupling | Low | Framework standard, easy to extend |

---

## Integration Best Practices

### Dependency Injection Pattern (Recommended)

```java
// ✅ Good: Loose coupling via interface
@Service
public class UserService {
    private final UserRepository userRepository;
    
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}

// ❌ Avoid: Direct instantiation (tight coupling)
UserRepository repo = new UserRepositoryImpl();

// ❌ Avoid: Static references
UserRepository repo = UserRepository.getInstance();
```

### Configuration Pattern (Recommended)

```java
// ✅ Good: Spring manages configuration
@Configuration
public class ApplicationConfig {
    // Spring Data JPA handles UserRepository bean
    // Spring Security provides authentication context
}

// ❌ Avoid: Manual configuration
UserService service = new UserService(
    new UserRepositoryImpl(new DataSourceImpl())
);
```

### Testing Pattern (Recommended)

```java
// ✅ Good: Easy to mock dependencies
@Test
public void testUpdateUser() {
    UserRepository mockRepo = mock(UserRepository.class);
    UserService service = new UserService(mockRepo);
    // Test with mocked dependency
}

// ❌ Avoid: Hard to test with tight coupling
UserService service = new UserService();
// Cannot inject test doubles
```

---

## Summary

**Profile Update Service Unit Dependencies:**

- **Internal Structure:** 6 components with clear layering (Presentation → Business → Data)
- **External Integration:** Seamless use of existing Spring Boot infrastructure
- **Coupling:** Minimal coupling via Spring dependency injection and interface abstraction
- **Shared Components:** Clear identification and read-only/controlled access
- **Transactions:** Single @Transactional boundary for consistency
- **Data Flow:** Unidirectional (request → service → repository → database)
- **Error Handling:** Delegated to existing GlobalExceptionHandler
- **No New Dependencies:** All infrastructure already present

This dependency structure supports:
- ✅ Testability (via dependency injection)
- ✅ Maintainability (via clear interfaces)
- ✅ Consistency (via single transaction boundary)
- ✅ Scalability (via loose coupling)
- ✅ Reusability (via component abstraction)

Ready for implementation in CONSTRUCTION phase.
