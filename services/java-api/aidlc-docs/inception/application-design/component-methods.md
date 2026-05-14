# Component Methods - Profile Update Feature

## Overview

This document defines the method signatures and high-level purposes for components involved in the profile update feature. Detailed business logic and implementation rules are specified in the Functional Design phase.

---

## 1. UserController Methods

### Method: updateUser

**Signature:**
```java
@PutMapping("/api/users/{userId}")
@ResponseStatus(HttpStatus.OK)
public ResponseEntity<UserResponse> updateUser(
    @PathVariable("userId") Long userId,
    @RequestBody @Valid UpdateUserRequest request,
    HttpServletRequest httpRequest
)
```

**Purpose:**
Handle HTTP PUT requests to update user profile information. Acts as the HTTP endpoint handler that coordinates request reception, validation, and response formatting.

**Input Parameters:**
- `userId` (Long): Path variable identifying the target user for update
- `request` (UpdateUserRequest): Request body containing profile fields to update (validated by Bean Validation)
- `httpRequest` (HttpServletRequest): HTTP request context for security information extraction

**Output:**
- `ResponseEntity<UserResponse>`: HTTP 200 OK response containing updated UserResponse DTO

**High-level Responsibilities:**
1. Extract userId from path variable
2. Validate request body via @Valid annotation
3. Retrieve authenticated user from security context
4. Invoke UserService.updateUser() to process profile update
5. Convert returned User entity to UserResponse DTO
6. Return HTTP 200 OK with updated profile
7. Delegate error handling to GlobalExceptionHandler

**Integration Points:**
- Calls UserService.updateUser() for business logic
- Accesses Spring Security context for authentication
- Returns UserResponse DTO serialized to JSON
- Exceptions handled by GlobalExceptionHandler

**Notes:**
- GlobalExceptionHandler manages 400, 403, 404, 409 error responses
- Request body validation (@Valid) triggers Bean Validation annotations
- Returns complete updated User profile in response body

---

## 2. UserService Methods

### Method: updateUser

**Signature:**
```java
@Transactional
public UserResponse updateUser(
    Long userId,
    UpdateUserRequest request,
    Long authenticatedUserId,
    String authenticatedUserRole
)
```

**Purpose:**
Orchestrate the complete profile update workflow including authorization checks, validation, and database updates. Acts as the service layer coordinator for all business logic.

**Input Parameters:**
- `userId` (Long): ID of the user whose profile is being updated
- `request` (UpdateUserRequest): Update request containing desired field changes (null fields = no change)
- `authenticatedUserId` (Long): ID of the authenticated user making the request
- `authenticatedUserRole` (String): Role of the authenticated user (e.g., "ROLE_USER", "ROLE_ADMIN")

**Output:**
- `UserResponse`: DTO containing the updated user profile information

**High-level Responsibilities:**
1. Check update authorization (self-update or admin)
2. Load existing user from UserRepository
3. Validate email uniqueness if email is being updated
4. Build updated User entity with provided fields
5. Validate all business rules
6. Persist updated user via UserRepository.save()
7. Convert updated User to UserResponse DTO
8. Return UserResponse

**Authorization Rules:**
- Regular users (ROLE_USER) can update only themselves
- Regular users can update only name and email
- Regular users cannot update role or active fields
- Admins (ROLE_ADMIN) can update any user's profile
- Admins can update all fields (name, email, role, active)

**Validation Rules:**
- Name: not null, not empty, max 100 characters (if provided)
- Email: valid email format, unique across system (if provided)
- Role: valid role value (ROLE_USER or ROLE_ADMIN) (if provided)
- Active: boolean value (if provided)

**Transaction Scope:**
- Single @Transactional block ensures all operations complete atomically
- Rolled back on any exception

**Integration Points:**
- Calls UserRepository.findById() to load user
- Calls UserRepository.existsByEmailAndIdNot() for email uniqueness check
- Calls UserRepository.save() to persist updates
- Returns UserResponse converted from updated User entity

**Exceptions Raised:**
- UserNotFoundException (404) - if user doesn't exist
- UnauthorizedException (403) - if authorization fails
- ValidationException (400) - if validation fails
- EmailAlreadyExistsException (409) - if email is not unique

**Notes:**
- Pre-check email uniqueness before update to provide better error response (409 vs database constraint error)
- Supports partial updates (null fields skipped)
- Transactional ensures data consistency with email uniqueness check

---

### Method: checkUpdateAuthorization (Helper)

**Signature:**
```java
private void checkUpdateAuthorization(
    Long targetUserId,
    Long authenticatedUserId,
    String authenticatedUserRole,
    UpdateUserRequest request
) throws UnauthorizedException
```

**Purpose:**
Validate that the authenticated user has permission to perform the requested profile update.

**Input Parameters:**
- `targetUserId` (Long): ID of user being updated
- `authenticatedUserId` (Long): ID of authenticated user
- `authenticatedUserRole` (String): Role of authenticated user
- `request` (UpdateUserRequest): Fields being updated (to check for admin-only fields)

**Output:**
- void (throws exception on authorization failure)

**High-level Responsibilities:**
1. Check if authenticated user is admin
2. If admin: allow all updates to any user
3. If not admin: check if targetUserId == authenticatedUserId
4. If not self-update: throw UnauthorizedException
5. If self-update: check for admin-only fields (role, active)
6. If regular user tries to update admin-only fields: throw UnauthorizedException

**Notes:**
- Regular users cannot update role or active fields even on their own profile
- Admins have no restrictions

---

### Method: validateEmailUniqueness (Helper)

**Signature:**
```java
private void validateEmailUniqueness(
    String newEmail,
    Long userId
) throws EmailAlreadyExistsException
```

**Purpose:**
Verify that an email address is unique in the system (excluding the current user).

**Input Parameters:**
- `newEmail` (String): Email address to validate
- `userId` (Long): ID of user being updated (to exclude from uniqueness check)

**Output:**
- void (throws exception if email is not unique)

**High-level Responsibilities:**
1. Call UserRepository.existsByEmailAndIdNot(newEmail, userId)
2. If email exists for another user: throw EmailAlreadyExistsException
3. Otherwise: return successfully

**Notes:**
- Pre-check prevents confusing database constraint violation errors
- Allows users to keep their existing email without conflict

---

## 3. UpdateUserRequest DTO Methods

### Method: Getters (Implicit)

**Signatures:**
```java
public String getName()
public String getEmail()
public String getRole()
public Boolean getActive()
```

**Purpose:**
Provide access to update request fields for validation and service processing.

**Input Parameters:**
- None (getters operate on instance state)

**Output:**
- Field value (String for name/email/role, Boolean for active)
- May return null for optional fields not provided in request

**High-level Responsibilities:**
- Return field value as-is (null for unprovided optional fields)
- Support null-checks for partial update handling

**Notes:**
- Optional fields support partial updates (null = don't update)
- No complex logic; simple field accessors

---

### Validation Annotations (Declarative)

**Applied to DTO Fields:**

```java
public class UpdateUserRequest {
    
    @Size(max = 100, message = "Name must not exceed 100 characters")
    private String name;
    
    @Email(message = "Email must be valid")
    private String email;
    
    private String role;  // Validated in service layer
    
    private Boolean active;  // No validation annotations (boolean is always valid)
}
```

**Validation Responsibility:**
- Bean Validation framework automatically validates before service invocation
- Name: max 100 characters (null allowed for partial updates)
- Email: valid email format (null allowed for partial updates)
- Role/Active: no declarative validation (service layer validates)

**Validation Trigger:**
- Spring validates @Valid UpdateUserRequest in UserController.updateUser()
- Returns 400 Bad Request with validation error details if validation fails

---

## 4. UserRepository Methods

### Method: findById

**Signature:**
```java
Optional<User> findById(Long id)
```

**Purpose:**
Retrieve a user by their unique identifier.

**Input Parameters:**
- `id` (Long): User ID to retrieve

**Output:**
- `Optional<User>`: Contains User entity if found, empty if not found

**High-level Responsibilities:**
1. Query database for user with given ID
2. Return Optional containing user or empty Optional

**Notes:**
- Inherited from JpaRepository
- Returns Optional to safely handle "not found" scenarios

---

### Method: save

**Signature:**
```java
User save(User entity)
```

**Purpose:**
Persist a user entity to the database (insert or update).

**Input Parameters:**
- `entity` (User): User entity to save

**Output:**
- `User`: Saved entity (may include generated ID or timestamp)

**High-level Responsibilities:**
1. Save or update user entity in database
2. Return entity with any database-generated values

**Notes:**
- Inherited from JpaRepository
- Managed within @Transactional scope

---

### Method: existsByEmailAndIdNot

**Signature:**
```java
boolean existsByEmailAndIdNot(String email, Long userId)
```

**Purpose:**
Check if an email address exists in the system for any user except the specified user ID.

**Input Parameters:**
- `email` (String): Email address to check
- `userId` (Long): User ID to exclude from check

**Output:**
- `boolean`: true if email exists for another user, false otherwise

**High-level Responsibilities:**
1. Query database for email matching criteria (excluding specified user)
2. Return true if found, false if not found

**High-level Query Logic:**
```sql
SELECT COUNT(*) > 0 FROM users 
WHERE email = ? AND id != ?
```

**Notes:**
- Custom query method (Spring Data derives from method name)
- Used for pre-check before email uniqueness database constraint
- Excludes current user to allow retaining existing email

---

### Method: findByEmail

**Signature:**
```java
Optional<User> findByEmail(String email)
```

**Purpose:**
Retrieve a user by their email address.

**Input Parameters:**
- `email` (String): Email address to search for

**Output:**
- `Optional<User>`: Contains User entity if found, empty if not found

**High-level Responsibilities:**
1. Query database for user with given email
2. Return Optional containing user or empty Optional

**Notes:**
- May exist in current codebase or added for profile update feature
- Returns Optional to safely handle "not found" scenarios

---

## 5. User Entity Methods

### Method: Getters (Implicit)

**Signatures:**
```java
public Long getId()
public String getName()
public String getEmail()
public String getRole()
public Boolean getActive()
```

**Purpose:**
Provide access to entity field values for service layer processing.

**Output:**
- Field value as stored in entity

**Notes:**
- Simple field accessors managed by entity framework

---

### Method: Setters (Implicit)

**Signatures:**
```java
public void setName(String name)
public void setEmail(String email)
public void setRole(String role)
public void setActive(Boolean active)
```

**Purpose:**
Modify entity field values during profile update operations.

**Input Parameters:**
- Field value to set

**High-level Responsibilities:**
1. Update entity field value
2. Track entity as dirty for persistence

**Notes:**
- Used by service layer to build updated entity
- JPA tracks changes and persists via save()

---

## 6. UserResponse DTO Methods

### Method: Constructor (Implicit)

**Signature:**
```java
public UserResponse(Long id, String name, String email, String role, Boolean active)
```

**Purpose:**
Create a response DTO from updated user entity.

**Input Parameters:**
- User entity fields (id, name, email, role, active)

**Output:**
- UserResponse instance ready for serialization

**Notes:**
- Typically created by service layer after successful update

---

### Method: Getters (Implicit)

**Signatures:**
```java
public Long getId()
public String getName()
public String getEmail()
public String getRole()
public Boolean getActive()
```

**Purpose:**
Provide access to response fields for JSON serialization.

**Output:**
- Field value for inclusion in JSON response

**Notes:**
- Spring's Jackson framework calls these for JSON serialization

---

## Method Call Flow Summary

```
HTTP Request with UpdateUserRequest JSON
    ↓
UserController.updateUser()
    ↓ (validates request)
UserService.updateUser()
    ├→ checkUpdateAuthorization() [throws if not allowed]
    ├→ UserRepository.findById() [throws UserNotFoundException if not found]
    ├→ validateEmailUniqueness() [if email is provided; throws if not unique]
    ├→ User.setters [build updated entity]
    └→ UserRepository.save() [persist changes]
    ↓
UserResponse creation
    ↓
HTTP 200 OK with UserResponse JSON
```

---

## Notes on Business Logic

**Important:** Detailed business logic implementation rules are defined in the **Functional Design** phase (CONSTRUCTION). This document provides method signatures and high-level purposes only. The Functional Design will specify:

- Exact validation rule implementations
- Email uniqueness check query patterns
- Authorization decision logic
- Error handling and exception translation
- Data transformation patterns
- Transaction boundary management
- Null-handling for partial updates

