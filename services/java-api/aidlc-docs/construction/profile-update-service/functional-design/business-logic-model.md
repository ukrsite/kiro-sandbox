# Business Logic Model - Profile Update Service

## Overview

This document defines the detailed business logic and workflows for the profile update feature, independent of technology or infrastructure implementation details.

---

## Core Business Process: Profile Update Workflow

### Process Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  User Submits Profile Update                 │
│              (HTTP PUT /api/users/{userId})                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            1. Input Validation (DTO Level)                   │
│  ├─ Name: not null, not empty, max 100 chars               │
│  ├─ Email: valid email format (@Email pattern)             │
│  ├─ Role: valid role enum (ROLE_USER, ROLE_ADMIN)          │
│  └─ Active: boolean (true/false)                           │
│                                                              │
│  Decision: Is input valid?                                  │
│  ├─ NO → Return 400 Bad Request with validation errors     │
│  └─ YES → Proceed to Authentication Check                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          2. Authentication Verification                      │
│  ├─ Extract authenticated user from Spring Security         │
│  ├─ Get authenticated user ID                              │
│  ├─ Get authenticated user role(s)                         │
│                                                              │
│  Decision: Is user authenticated?                           │
│  ├─ NO → Return 401 Unauthorized                           │
│  └─ YES → Proceed to Authorization Check                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          3. Authorization Check (Business Rules)             │
│  ├─ Is authenticated user an ADMIN?                        │
│  │  ├─ YES → Allow full update (any user, any field)       │
│  │  └─ NO → Apply regular user restrictions:               │
│  │      ├─ Is this a self-update (target == authenticated)? │
│  │      │  ├─ NO → Return 403 Forbidden                    │
│  │      │  └─ YES → Check field restrictions:              │
│  │      │      ├─ Attempting to update role? NO ALLOWED    │
│  │      │      ├─ Attempting to update active? NO ALLOWED  │
│  │      │      └─ Only name/email allowed                  │
│                                                              │
│  Decision: Is operation authorized?                         │
│  ├─ NO → Return 403 Forbidden                              │
│  └─ YES → Proceed to User Lookup                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          4. User Lookup (Existence Check)                    │
│  ├─ Query database for User with target userId             │
│  ├─ Check if user record exists                            │
│                                                              │
│  Decision: Does target user exist?                          │
│  ├─ NO → Return 404 Not Found                              │
│  └─ YES → Proceed to Business Rules Validation              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          5. Business Rules Validation                        │
│  ├─ IF email provided AND differs from current:             │
│  │  ├─ Check email uniqueness (email not used by other user) │
│  │  ├─ Query: existsByEmailAndIdNot(newEmail, targetUserId) │
│  │  ├─ Decision: Email unique?                             │
│  │  │  ├─ NO → Return 409 Conflict (email already exists)  │
│  │  │  └─ YES → Email valid, proceed                       │
│  │                                                           │
│  ├─ IF role provided AND differs from current:              │
│  │  ├─ Validate role is valid enum value                   │
│  │  ├─ Decision: Valid role?                               │
│  │  │  ├─ NO → Return 400 Bad Request (invalid role)       │
│  │  │  └─ YES → Role valid, proceed                        │
│  │                                                           │
│  └─ IF active provided AND differs from current:            │
│     ├─ Boolean validation (true/false only)                │
│     └─ Active status valid, proceed                        │
│                                                              │
│  Decision: All business rules satisfied?                    │
│  ├─ NO → Return appropriate error (400/409)                │
│  └─ YES → Proceed to Update Execution                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          6. Update Execution (Transactional)                 │
│  ├─ BEGIN TRANSACTION                                       │
│  ├─ Load current user entity from database                 │
│  ├─ For each field provided in request:                    │
│  │  ├─ IF name is not null: user.setName(request.name)     │
│  │  ├─ IF email is not null: user.setEmail(request.email)  │
│  │  ├─ IF role is not null: user.setRole(request.role)     │
│  │  ├─ IF active is not null: user.setActive(request.active) │
│  │                                                           │
│  ├─ Save updated user entity                               │
│  ├─ COMMIT TRANSACTION                                      │
│                                                              │
│  Decision: Update successful?                               │
│  ├─ NO → Rollback, return 500 Internal Server Error         │
│  └─ YES → Proceed to Response                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          7. Response Generation                              │
│  ├─ Convert updated User entity to UserResponse DTO         │
│  ├─ Include all user fields:                               │
│  │  ├─ id (user ID)                                        │
│  │  ├─ name (display name)                                 │
│  │  ├─ email (email address)                               │
│  │  ├─ role (user role)                                    │
│  │  └─ active (active status)                              │
│  │                                                           │
│  └─ Return 200 OK with UserResponse in response body       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌─────────────────────────────┐
         │   Return 200 OK Response    │
         │   with updated user profile │
         └─────────────────────────────┘
```

---

## Detailed Business Logic Components

### 1. Input Validation Logic

**Purpose:** Ensure incoming data is well-formed before processing

**Rules:**

#### Name Field
- If provided (not null):
  - Must not be empty string
  - Must not exceed 100 characters
  - Whitespace-only values treated as invalid
  - Allowed characters: alphanumeric, spaces, hyphens, apostrophes

**Implementation Notes:**
```
- Use @NotNull annotation for presence check (DTO level)
- Use @NotEmpty annotation for empty check
- Use @Size(max=100) for length validation
- Use @Pattern or custom validator for character set
```

#### Email Field
- If provided (not null):
  - Must conform to valid email format (RFC 5322 simplified)
  - Must be lowercase for database storage
  - Must not exceed reasonable length (255 characters)
  - Must be unique across the system (checked in business rules phase)

**Implementation Notes:**
```
- Use @Email annotation for format validation
- Convert to lowercase before storage
- Use @Size(max=255) for length
- Uniqueness checked in business rules phase
```

#### Role Field
- If provided (not null):
  - Must be one of: "ROLE_USER", "ROLE_ADMIN"
  - Case-sensitive
  - Invalid values rejected

**Implementation Notes:**
```
- Define enum: Role { ROLE_USER, ROLE_ADMIN }
- Validate against enum values
- Custom @ValidRole annotation or enum validation
```

#### Active Field
- If provided (not null):
  - Must be boolean (true/false)
  - No other values accepted

**Implementation Notes:**
```
- Use Boolean type (nullable)
- JPA automatically handles serialization
```

**Error Response for Validation Failure:**
```
HTTP 400 Bad Request
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Validation failed",
  "details": [
    {
      "field": "name",
      "message": "size must be between 1 and 100"
    }
  ]
}
```

---

### 2. Authentication Logic

**Purpose:** Verify user identity and extract security context

**Rules:**

#### Authentication Detection
- Extract authentication from Spring Security SecurityContext
- If no authentication present or not authenticated: treat as unauthorized

#### User Information Extraction
- Extract authenticated user ID (principal)
- Extract authenticated user role(s)
- Extract authenticated user username (optional)

**Decision Points:**
- Is user authenticated? (Yes/No)
  - If No: Return 401 Unauthorized

**Implementation Notes:**
```
- Use SecurityContextHolder.getContext().getAuthentication()
- Check Authentication.isAuthenticated()
- Extract principal as authenticated user ID
- Extract authorities/roles from Authentication
- Handle Spring Security naming conventions
```

---

### 3. Authorization Logic

**Purpose:** Enforce business rules about who can update what

**Rules:**

#### Admin User Authorization
- If authenticated user has role "ROLE_ADMIN":
  - Can update any user's profile
  - Can update any field (name, email, role, active)
  - No field restrictions apply

#### Regular User Authorization
- If authenticated user does NOT have role "ROLE_ADMIN":
  - Can only update own profile (authenticated user ID == target user ID)
  - Can only update certain fields: name, email
  - Cannot update: role, active
  - Cannot view or update other users' profiles

#### Field-Level Authorization
- Name field: Can update if (authenticated user is admin) OR (self-update AND not role change)
- Email field: Can update if (authenticated user is admin) OR (self-update AND not role change)
- Role field: Can ONLY update if authenticated user is admin
- Active field: Can ONLY update if authenticated user is admin

**Decision Tree:**

```
User wants to update User X

├─ Is authenticated user an admin?
│  ├─ YES → Allow all updates to any user
│  └─ NO → Apply regular user restrictions
│      ├─ Is authenticated user ID == target user ID?
│      │  ├─ NO → Reject 403 Forbidden
│      │  └─ YES → Check field restrictions
│      │      ├─ Attempting role update?
│      │      │  ├─ YES → Reject 403 Forbidden
│      │      │  └─ NO → Check next field
│      │      │
│      │      ├─ Attempting active update?
│      │      │  ├─ YES → Reject 403 Forbidden
│      │      │  └─ NO → Allow
│      │      │
│      │      └─ All field checks passed → Allow
```

**Error Response for Authorization Failure:**
```
HTTP 403 Forbidden
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 403,
  "error": "Forbidden",
  "message": "You do not have permission to perform this operation"
}
```

---

### 4. User Lookup Logic

**Purpose:** Retrieve target user and verify existence

**Rules:**

#### User Lookup
- Query database for User with target userId
- Use indexed lookup by primary key
- Return user if found, error if not found

#### Not Found Handling
- If user not found: Return 404 Not Found
- Include message indicating user doesn't exist

**Error Response for Not Found:**
```
HTTP 404 Not Found
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 404,
  "error": "Not Found",
  "message": "User not found"
}
```

---

### 5. Business Rules Validation Logic

**Purpose:** Enforce data consistency and business constraints

#### Rule 1: Email Uniqueness (When Email Updated)

**Condition:** Email field is provided AND differs from current value

**Check:**
- Query database: Is email already used by another user?
- Query: `SELECT COUNT(*) FROM User WHERE email=? AND id != targetUserId`
- Or: `existsByEmailAndIdNot(email, userId)`

**Decision:**
- If duplicate found: Return 409 Conflict
- If unique: Proceed with update

**Business Rationale:** Email is a unique identifier for authentication and notifications

**Error Response:**
```
HTTP 409 Conflict
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 409,
  "error": "Conflict",
  "message": "Email is already in use by another user"
}
```

#### Rule 2: Role Validation (When Role Updated)

**Condition:** Role field is provided AND differs from current value

**Check:**
- Validate role is one of: "ROLE_USER", "ROLE_ADMIN"
- Reject any other role values

**Decision:**
- If invalid role: Return 400 Bad Request
- If valid role: Proceed with update

**Business Rationale:** Roles must be from predefined system roles

**Error Response:**
```
HTTP 400 Bad Request
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Invalid role value. Allowed values: ROLE_USER, ROLE_ADMIN"
}
```

#### Rule 3: Active Status Validation (When Active Updated)

**Condition:** Active field is provided

**Check:**
- Verify active is boolean (true/false)
- Already handled by DTO deserialization

**Decision:**
- If non-boolean value: Return 400 Bad Request (or handled by Spring)
- If valid boolean: Proceed with update

**Business Rationale:** Active status controls user access to system

#### Rule 4: Immutable Fields

**Condition:** Any immutable field update attempted

**Immutable Fields:** User ID (primary key)

**Decision:**
- User ID cannot be changed
- If update attempted: Silently ignore or reject

**Business Rationale:** User ID is primary key and foundation of identity

---

### 6. Update Execution Logic

**Purpose:** Apply approved changes to user entity and persist

**Rules:**

#### Transactional Scope
- All update operations within single database transaction
- Atomicity: All changes succeed or all rollback
- Consistency: No partial updates

#### Partial Update Handling
- Field is only updated if provided in request (not null)
- Fields not provided remain unchanged
- Allows selective field updates

#### Update Operations

```
FOR EACH field in UpdateUserRequest:
  IF field is not null:
    IF field differs from current user value:
      UPDATE user.field = request.field
    ELSE:
      Skip update (no change needed)

PERSIST user entity to database
```

#### Persistence Operations
1. Load current user entity (if not already loaded)
2. Apply field updates
3. Save entity (JPA/Hibernate handles INSERT vs UPDATE)
4. Flush changes to database within transaction
5. Commit transaction

**Error Handling:**
- If update fails during persistence: Rollback transaction
- Return 500 Internal Server Error (with appropriate logging)

---

### 7. Response Generation Logic

**Purpose:** Format update result for client

**Rules:**

#### Response DTO Construction
- Create UserResponse object
- Populate all required fields from updated User entity:
  - id (from user.getId())
  - name (from user.getName())
  - email (from user.getEmail())
  - role (from user.getRole())
  - active (from user.getActive())

#### HTTP Status Code
- Success: 200 OK
- Include full UserResponse in response body
- Content-Type: application/json

#### Response Body Format
```json
{
  "id": 1,
  "name": "Updated Display Name",
  "email": "updated@example.com",
  "role": "ROLE_USER",
  "active": true
}
```

---

## Business Logic State Machine

```
States:
├─ INIT: Request received
├─ INPUT_VALIDATED: DTO validation passed
├─ AUTHENTICATED: User authentication verified
├─ AUTHORIZED: Authorization check passed
├─ USER_FOUND: Target user exists in database
├─ BUSINESS_RULES_VALIDATED: All business constraints satisfied
├─ UPDATED: User entity updated
├─ PERSISTED: Changes saved to database
└─ COMPLETED: Response sent to client

Transitions:
INIT
  │ (DTO deserialization)
  ├─ FAIL → Return 400
  └─ PASS → INPUT_VALIDATED
      │ (Extract authentication)
      ├─ FAIL → Return 401
      └─ PASS → AUTHENTICATED
          │ (Check permissions)
          ├─ FAIL → Return 403
          └─ PASS → AUTHORIZED
              │ (Load user)
              ├─ FAIL → Return 404
              └─ PASS → USER_FOUND
                  │ (Validate email uniqueness, role values, etc.)
                  ├─ FAIL → Return 400/409
                  └─ PASS → BUSINESS_RULES_VALIDATED
                      │ (Apply updates)
                      ├─ FAIL → Rollback, Return 500
                      └─ PASS → UPDATED
                          │ (Persist)
                          ├─ FAIL → Rollback, Return 500
                          └─ PASS → PERSISTED
                              │ (Format response)
                              └─ COMPLETED
                                  └─ Return 200 OK + UserResponse
```

---

## Error Handling Logic

**Purpose:** Translate all error conditions to appropriate HTTP responses

### Error Mapping

| Condition | Exception Type | HTTP Status | Message |
|-----------|---|---|---|
| Invalid DTO format | MethodArgumentNotValidException | 400 Bad Request | Validation failed with field details |
| No authentication | AuthenticationException | 401 Unauthorized | Unauthenticated request |
| Insufficient permissions | AccessDeniedException | 403 Forbidden | Insufficient permissions |
| User not found | UserNotFoundException | 404 Not Found | User not found |
| Email not unique | EmailAlreadyExistsException | 409 Conflict | Email already in use |
| Invalid role | ValidationException | 400 Bad Request | Invalid role value |
| Database error | DataAccessException | 500 Internal Server Error | Database operation failed |

### Error Response Format

**Standard Error Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Human-readable error message",
  "path": "/api/users/1"
}
```

**Validation Error Response (with details):**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Validation failed",
  "details": [
    {
      "field": "email",
      "message": "must be a valid email address"
    },
    {
      "field": "name",
      "message": "size must be between 1 and 100"
    }
  ],
  "path": "/api/users/1"
}
```

---

## Business Rules Summary

| Rule | Condition | Action | Result |
|------|-----------|--------|--------|
| BR1: Self-update for regular users | Regular user attempts cross-user update | Reject with 403 | Access denied |
| BR2: Admin-only fields | Regular user attempts role/active update | Reject with 403 | Access denied |
| BR3: Email uniqueness | Email used by different user | Reject with 409 | Conflict |
| BR4: Role validation | Invalid role value | Reject with 400 | Invalid data |
| BR5: Admin override | Admin updates any user | Allow | Full access |
| BR6: Partial updates | Only some fields provided | Update only provided fields | Selective update |
| BR7: Immutable ID | Attempt to change user ID | Ignore or reject | ID preserved |
| BR8: Transactional consistency | Multiple field updates | All-or-nothing persistence | Atomicity |

---

## Summary

The profile update business logic:

1. **Validates** incoming request data (DTO level)
2. **Authenticates** the user making the request
3. **Authorizes** the operation based on roles and ownership
4. **Looks up** the target user
5. **Validates business rules** (email uniqueness, role values)
6. **Executes the update** within a transaction
7. **Generates the response** with updated profile data

Key design principles:
- **Fail-fast:** Validate early and return appropriate errors
- **Least privilege:** Regular users can only update own profile
- **Data integrity:** Email uniqueness enforced
- **Atomicity:** All updates succeed or all rollback
- **Clear errors:** Each failure has distinct HTTP status code and message
