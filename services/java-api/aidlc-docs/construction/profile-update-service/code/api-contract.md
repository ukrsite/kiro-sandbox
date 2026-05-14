# Profile Update API Contract

## Overview

The Profile Update API provides REST endpoints for authenticated users to update their profile information. The feature supports self-update capabilities for regular users and comprehensive profile management by administrators.

**Base URL**: `/api/users`

---

## Endpoint: Update User Profile

### REST Contract

```
PUT /api/users/{userId}
Content-Type: application/json
Authorization: Basic <base64-encoded-credentials>
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `userId` | Long | Yes | The ID of the user to update |

### Request Headers

| Header | Required | Value |
|--------|----------|-------|
| `Content-Type` | Yes | `application/json` |
| `Authorization` | Yes | `Basic <base64>` for HTTP Basic auth |

### Request Body (UpdateUserRequest)

```json
{
  "name": "string (optional, 1-100 chars)",
  "email": "string (optional, valid email format)",
  "role": "string (optional, admin-only: ROLE_USER or ROLE_ADMIN)",
  "active": "boolean (optional, admin-only: true/false)"
}
```

**Field Details:**
- **name**: Optional. User's display name. If provided, must be 1-100 characters.
- **email**: Optional. User's email address. If provided, must be valid email format and unique across system.
- **role**: Optional. User's role. Admin-only field. Must be `ROLE_USER` or `ROLE_ADMIN`.
- **active**: Optional. User's active status. Admin-only field. Boolean value (true/false).

**Partial Updates**: All fields are optional. Null or omitted fields will not be updated. Clients can update any subset of fields.

### Success Response

**HTTP Status**: `200 OK`

```json
{
  "id": 1,
  "name": "Updated Name",
  "email": "updated@example.com",
  "role": "ROLE_USER",
  "active": true
}
```

**Response Type**: `UserResponse` (application/json)

### Error Responses

#### 400 Bad Request
**Reason**: Validation failure (invalid email format, name too long, invalid role, etc.)

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Name must be between 1 and 100 characters",
  "path": "/api/users/1"
}
```

#### 403 Forbidden
**Reason**: Insufficient permissions for requested update

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "status": 403,
  "error": "Forbidden",
  "message": "You do not have permission to update this user's profile",
  "path": "/api/users/2"
}
```

#### 404 Not Found
**Reason**: User ID does not exist

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "status": 404,
  "error": "Not Found",
  "message": "User not found with ID: 99999",
  "path": "/api/users/99999"
}
```

#### 409 Conflict
**Reason**: Email already exists for another user

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "status": 409,
  "error": "Conflict",
  "message": "Email already exists in the system: existing@example.com",
  "path": "/api/users/1"
}
```

---

## Authorization Rules

### Regular Users (ROLE_USER)
- Can update their **own profile only** (authenticated userId == path userId)
- Can update: **name**, **email**
- Cannot update: **role**, **active** (will receive 403 Forbidden)
- Cannot update other users' profiles (will receive 403 Forbidden)

### Administrators (ROLE_ADMIN)
- Can update **any user's profile**
- Can update all fields: **name**, **email**, **role**, **active**

### Authentication
- HTTP Basic authentication required (existing system)
- User ID must be extractable from Authentication principal

---

## Validation Rules

### Name Field
- Optional for updates (if provided, validated)
- Must be 1-100 characters if provided
- Required if updating user profile initially
- No special character restrictions

### Email Field
- Optional for updates (if provided, validated)
- Must be valid email format (RFC 5322)
- Must be unique across system (checked against all other users)
- Self-updates to same email allowed (validation excludes current user)
- Case-insensitive uniqueness check (recommended)

### Role Field
- Optional for updates (if provided, validated)
- Only accessible to admins (regular users get 403 if provided)
- Must be one of: `ROLE_USER`, `ROLE_ADMIN`
- Enum validation enforced

### Active Field
- Optional for updates (if provided, validated)
- Only accessible to admins (regular users get 403 if provided)
- Boolean value: `true` or `false`

---

## Story Coverage & Mapping

| Story ID | Title | Covered By | Endpoint | HTTP Status |
|----------|-------|-----------|----------|-------------|
| US-001 | Update Own Profile Name | PUT /api/users/{userId} + name field | 200 OK |
| US-002 | Update Own Profile Email | PUT /api/users/{userId} + email field + uniqueness | 200 OK / 409 Conflict |
| US-003 | Prevent Unauthorized Updates | Authorization check + field restrictions | 403 Forbidden |
| US-004 | Admin Update Any User | Admin authorization + any user | 200 OK / 404 / 409 |
| US-005 | Admin Manage User Roles | Admin + role field | 200 OK / 400 / 403 |
| US-006 | Admin Manage User Active Status | Admin + active field | 200 OK / 403 |

---

## Usage Examples

### Example 1: Regular User Updates Own Name

**Request:**
```bash
curl -X PUT http://localhost:8080/api/users/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic dXNlcjE6cGFzc3dvcmQ=" \
  -d '{
    "name": "John Updated"
  }'
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "John Updated",
  "email": "john@example.com",
  "role": "ROLE_USER",
  "active": true
}
```

### Example 2: Regular User Attempts Role Change

**Request:**
```bash
curl -X PUT http://localhost:8080/api/users/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic dXNlcjE6cGFzc3dvcmQ=" \
  -d '{
    "role": "ROLE_ADMIN"
  }'
```

**Response (403 Forbidden):**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "status": 403,
  "error": "Forbidden",
  "message": "You do not have permission to update user roles",
  "path": "/api/users/1"
}
```

### Example 3: Admin Updates Another User's Email

**Request:**
```bash
curl -X PUT http://localhost:8080/api/users/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" \
  -d '{
    "email": "newemail@example.com"
  }'
```

**Response (200 OK):**
```json
{
  "id": 2,
  "name": "Original Name",
  "email": "newemail@example.com",
  "role": "ROLE_USER",
  "active": true
}
```

### Example 4: Admin Updates User Role

**Request:**
```bash
curl -X PUT http://localhost:8080/api/users/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" \
  -d '{
    "role": "ROLE_ADMIN"
  }'
```

**Response (200 OK):**
```json
{
  "id": 2,
  "name": "Original Name",
  "email": "user@example.com",
  "role": "ROLE_ADMIN",
  "active": true
}
```

### Example 5: Email Uniqueness Conflict

**Request:**
```bash
curl -X PUT http://localhost:8080/api/users/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic dXNlcjE6cGFzc3dvcmQ=" \
  -d '{
    "email": "existing@example.com"
  }'
```

**Response (409 Conflict):**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "status": 409,
  "error": "Conflict",
  "message": "Email already exists in the system: existing@example.com",
  "path": "/api/users/1"
}
```

---

## Implementation Details

### Transactional Behavior
- All profile updates are transactional (@Transactional)
- If any part of update fails, entire transaction rolls back
- Email uniqueness check and update are atomic

### Database Queries
- Find user by ID (1 query)
- Email uniqueness check if email provided (1 query - repository method)
- Update and save user (1 query)
- Total: 2-3 queries

### Performance
- Target response time: < 200ms
- Minimal database queries
- No N+1 query issues
- Supports concurrent updates with database-level locking

### Security
- Authenticated users only (HTTP Basic auth)
- Authorization enforced at service layer
- Field-level restrictions for regular users
- Input validation (length, format, enum)
- No sensitive data in error messages

---

## HTTP Status Code Reference

| Status | Meaning | When Thrown |
|--------|---------|------------|
| 200 | OK | Successful update |
| 400 | Bad Request | Validation failure (format, length, invalid enum) |
| 403 | Forbidden | Authorization failure (not own profile, role field as regular user, etc.) |
| 404 | Not Found | User ID does not exist |
| 409 | Conflict | Email already exists |
| 500 | Server Error | Unexpected server error |

---

## Related Files

- **Source Code**: `src/main/java/com/sandbox/userapi/`
  - `controller/UserController.java` - REST endpoint implementation
  - `service/UserService.java` - Business logic and authorization
  - `dto/UpdateUserRequest.java` - Request DTO with validation
  - `dto/UserResponse.java` - Response DTO
  - `repository/UserRepository.java` - Data access layer

- **Tests**:
  - `src/test/java/com/sandbox/userapi/service/UserServiceUpdateUserTest.java` - Unit tests
  - `src/test/java/com/sandbox/userapi/controller/UserControllerUpdateUserTest.java` - Integration tests

- **Documentation**: This file
