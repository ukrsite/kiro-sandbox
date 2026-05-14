# Application Components - Profile Update Feature

## Overview

This document defines the main functional components and their responsibilities for the profile update feature. The design leverages and enhances existing Spring Boot components within the 3-tier architecture.

---

## 1. UserController Component

### Purpose
REST API endpoint handler for user-related operations, including profile updates.

### Responsibilities
- Accept incoming HTTP PUT requests for profile updates on `/api/users/{userId}`
- Extract and parse the `UpdateUserRequest` DTO from request body
- Invoke the UserService to process the profile update
- Translate service responses to appropriate HTTP responses
- Handle security context injection (authenticated user information)
- Delegate to GlobalExceptionHandler for error handling

### Component Interfaces
```java
// Primary Interface
public ResponseEntity<UserResponse> updateUser(
    @PathVariable Long userId,
    @RequestBody UpdateUserRequest request,
    HttpServletRequest httpRequest
)
```

### Key Methods
- `updateUser()` - Main endpoint handler for profile updates

### Integration Points
- Integrates with Spring Security for authentication context
- Calls UserService for business logic
- Returns UserResponse DTO for successful updates
- Delegates error handling to GlobalExceptionHandler

### Interaction Patterns
- Request → Response: Synchronous HTTP request/response pattern
- Uses Spring REST conventions with `@RestController`, `@PutMapping`, `@PathVariable`, `@RequestBody`

---

## 2. UserService Component

### Purpose
Core business logic service for user profile operations and validation.

### Responsibilities
- Implement profile update business logic
- Perform authorization checks (self-update vs admin capabilities)
- Validate all business rules for profile updates
- Coordinate with UserRepository for data access
- Handle email uniqueness validation with pre-check strategy
- Manage transactional integrity for update operations
- Translate exceptions to meaningful service layer exceptions

### Component Interfaces
```java
// Primary Interface
public UserResponse updateUser(
    Long userId,
    UpdateUserRequest request,
    Authentication authentication
)
```

### Key Methods
- `updateUser()` - Orchestrate complete profile update workflow
- `validateEmailUniqueness()` - Check email uniqueness before update (helper)
- `checkUpdateAuthorization()` - Enforce authorization rules (helper)

### Integration Points
- Uses UserRepository for database operations
- Integrates with Spring Security Authentication object
- Calls User entity mapping utilities for DTO conversion
- Works with existing exception handling framework

### Interaction Patterns
- Service orchestration: coordinates multiple repository and security operations
- Transaction management: all updates in single @Transactional block
- Authorization delegation: checks permissions against authentication context

---

## 3. UpdateUserRequest DTO Component

### Purpose
Data Transfer Object for profile update requests from clients.

### Responsibilities
- Encapsulate profile update request data (name, email, role, active status)
- Support partial updates (optional fields for flexibility)
- Provide declarative validation annotations for input validation
- Facilitate null-handling for partial update scenarios
- Transform client data into service layer format

### Component Interfaces
```java
// Primary Interface - DTO Record/Class
public class UpdateUserRequest {
    private String name;           // Optional: null = don't update
    private String email;          // Optional: null = don't update
    private String role;           // Optional: null = don't update (admin only)
    private Boolean active;        // Optional: null = don't update (admin only)
}
```

### Key Attributes
- **name**: Optional string for user display name
- **email**: Optional string for user email address
- **role**: Optional string for user role (admin only field)
- **active**: Optional boolean for user active status (admin only field)

### Validation Annotations
- `@NotNull` and `@Size(max=100)` on name (when provided)
- `@Email` on email (when provided)
- Valid enum values for role (when provided)
- Boolean validation for active (when provided)

### Integration Points
- Accepts client JSON data via Spring's JSON deserialization
- Passes to UserService for processing
- Includes Jakarta Bean Validation annotations

### Interaction Patterns
- Request payload binding: Spring automatically deserializes JSON to DTO
- Bean validation: automatic validation before service invocation
- Null-handling: optional fields support partial updates

---

## 4. UserRepository Component

### Purpose
Data access layer abstraction for User persistence operations.

### Responsibilities
- Provide database query methods for User entity operations
- Execute email uniqueness checks with custom repository methods
- Support finding users by ID for profile retrieval
- Manage JPA/Hibernate interactions for database persistence
- Coordinate with H2 database for entity storage

### Component Interfaces
```java
// Primary Interface (existing + enhancements)
public interface UserRepository extends JpaRepository<User, Long> {
    // Existing methods
    Optional<User> findById(Long id);
    
    // New methods for profile updates
    boolean existsByEmailAndIdNot(String email, Long userId);
    Optional<User> findByEmail(String email);
}
```

### Key Methods
- `findById()` - Retrieve user by ID
- `save()` - Persist updated user entity
- `existsByEmailAndIdNot()` - Check email uniqueness excluding current user
- `findByEmail()` - Find user by email address

### Integration Points
- Uses Spring Data JPA for automatic query generation
- Integrates with JPA/Hibernate for ORM operations
- Connected to H2 database persistence layer
- Works with existing User entity model

### Interaction Patterns
- Database query abstraction: Repository pattern isolates persistence logic
- Optional return types: supports "user not found" scenarios
- Transaction management: spring manages database transactions

---

## 5. User Entity Component

### Purpose
Domain model representing user profile data.

### Responsibilities
- Encapsulate user profile information (id, name, email, role, active)
- Provide entity-level constraints and validation
- Support JPA persistence annotations
- Maintain data integrity at entity level

### Component Interfaces
```java
// Primary Interface - JPA Entity
@Entity
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, length = 100)
    private String name;
    
    @Column(nullable = false, unique = true)
    private String email;
    
    @Column(nullable = false)
    private String role;
    
    @Column(nullable = false)
    private Boolean active;
}
```

### Key Attributes
- **id**: Unique identifier for user
- **name**: User's display name (required)
- **email**: User's email (required, unique)
- **role**: User's role (required)
- **active**: User's active status (required)

### Integration Points
- Persisted in H2 database via JPA
- Mapped by UserRepository for queries
- Converted to/from DTOs by service layer
- Subject to database constraints

### Interaction Patterns
- Entity mapping: JPA annotations define database schema
- Transactional scope: entities managed within transaction boundaries
- Conversion: service layer converts entities to/from DTOs

---

## 6. UserResponse DTO Component

### Purpose
Data Transfer Object for profile update responses to clients.

### Responsibilities
- Encapsulate updated user profile information for response
- Provide clean API contract for client consumption
- Exclude internal system fields from response
- Support Jackson serialization to JSON

### Component Interfaces
```java
// Primary Interface - DTO Record/Class
public class UserResponse {
    private Long id;
    private String name;
    private String email;
    private String role;
    private Boolean active;
}
```

### Key Attributes
- **id**: User ID
- **name**: User's display name
- **email**: User's email address
- **role**: User's role
- **active**: User's active status

### Integration Points
- Receives User entity from service layer
- Serialized to JSON by Spring for HTTP response
- Used by UserController for response body

### Interaction Patterns
- Response payload generation: Controller creates UserResponse from updated User entity
- JSON serialization: Spring automatically serializes to JSON
- Clean API contract: only exposes relevant user profile fields

---

## Component Dependency Map

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (HTTP Request)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────┐
│        UserController                  │
│ - @PutMapping("/api/users/{userId}")  │
│ - Accepts UpdateUserRequest DTO       │
│ - Returns UserResponse DTO            │
└────────┬─────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│        UserService                     │
│ - Authorization checks                │
│ - Email uniqueness validation          │
│ - Profile update orchestration         │
│ - Transaction management               │
└────────┬──────────────────┬───────────┘
         │                  │
         ▼                  ▼
┌──────────────────┐  ┌──────────────────────┐
│  UserRepository  │  │ Spring Security      │
│ - findById()     │  │ - Authentication     │
│ - save()         │  │ - Role checks        │
│ - Custom queries │  │                      │
└────────┬─────────┘  └──────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  User Entity                           │
│ - id, name, email, role, active        │
│ - JPA annotations                      │
│ - Database constraints                 │
└────────┬─────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│        H2 Database                     │
│ - User table persistence               │
│ - Unique constraint on email           │
└────────────────────────────────────────┘
```

---

## Summary

The application design comprises six main components working together to implement the profile update feature:

1. **UserController** - HTTP request handling and response formatting
2. **UserService** - Business logic orchestration and authorization
3. **UpdateUserRequest DTO** - Request payload validation and binding
4. **UserRepository** - Data access layer abstraction
5. **User Entity** - Domain model with persistence annotations
6. **UserResponse DTO** - Response payload formatting

These components leverage the existing Spring Boot 3-tier architecture and integrate seamlessly with the current security, exception handling, and database infrastructure. The design supports both self-updates by regular users and comprehensive profile management by administrators, with appropriate authorization and validation enforcement at each layer.
