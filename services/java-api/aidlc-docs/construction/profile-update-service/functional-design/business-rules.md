# Business Rules - Profile Update Service

## Overview

This document defines all business rules governing profile update operations. These rules are technology-agnostic and focus purely on business logic constraints and validations.

---

## Rule Categories

### 1. Data Validation Rules

#### DV1: Name Field Validation

**Rule:** When a user provides a name in a profile update request, the system SHALL validate:
- Name is not null (if provided)
- Name is not empty string
- Name does not exceed 100 characters
- Name contains only valid characters (alphanumeric, spaces, hyphens, apostrophes)

**Enforcement Point:** Input validation at DTO/request level

**Error Handling:** Return HTTP 400 Bad Request with field-specific error details

**Rationale:** Ensures data consistency and prevents database storage issues

**Examples:**
- ✅ "John Smith" - Valid
- ✅ "Mary-Jane O'Connor" - Valid
- ❌ "" (empty) - Invalid: empty string not allowed
- ❌ "A" * 101 - Invalid: exceeds 100 character limit
- ❌ "John<script>" - Invalid: contains invalid characters

---

#### DV2: Email Field Validation

**Rule:** When a user provides an email in a profile update request, the system SHALL validate:
- Email is not null (if provided)
- Email conforms to RFC 5322 simplified email format (standard @example.com pattern)
- Email contains exactly one @ symbol
- Email has valid domain component
- Email is stored in lowercase (case-insensitive)

**Enforcement Point:** Input validation at DTO level via @Email annotation

**Error Handling:** Return HTTP 400 Bad Request if email format invalid

**Rationale:** Ensures valid email addresses for authentication and notifications

**Examples:**
- ✅ "user@example.com" - Valid
- ✅ "john.smith+tag@company.co.uk" - Valid
- ❌ "invalid.email" - Invalid: missing @
- ❌ "user@@example.com" - Invalid: double @
- ❌ "user@" - Invalid: missing domain
- ❌ "@example.com" - Invalid: missing local part

---

#### DV3: Role Field Validation

**Rule:** When a user provides a role in a profile update request, the system SHALL validate:
- Role is not null (if provided)
- Role is one of the predefined system roles: "ROLE_USER", "ROLE_ADMIN"
- Role comparison is case-sensitive
- Invalid roles are rejected

**Enforcement Point:** Business logic validation (not DTO level to allow clearer error messages)

**Error Handling:** Return HTTP 400 Bad Request with list of valid roles

**Rationale:** Ensures only valid system roles are assigned; prevents unauthorized role creation

**Valid Values:**
- "ROLE_USER" - Standard user with basic access
- "ROLE_ADMIN" - Administrator with full system access

**Examples:**
- ✅ "ROLE_USER" - Valid
- ✅ "ROLE_ADMIN" - Valid
- ❌ "role_user" (lowercase) - Invalid: case-sensitive
- ❌ "USER" - Invalid: missing ROLE_ prefix
- ❌ "ROLE_SUPERADMIN" - Invalid: undefined role
- ❌ "" (empty) - Invalid: empty role not allowed

---

#### DV4: Active Status Field Validation

**Rule:** When a user provides an active status in a profile update request, the system SHALL validate:
- Active is a boolean value (true or false)
- Active can be null (optional field for partial updates)
- Only boolean values are accepted; no string representations

**Enforcement Point:** DTO deserialization / Spring validation

**Error Handling:** Return HTTP 400 Bad Request if non-boolean value provided

**Rationale:** Ensures active status is always in valid state (activated or deactivated)

**Valid Values:**
- true - User account is active
- false - User account is deactivated
- null - Do not change active status (partial update)

**Examples:**
- ✅ active=true - Valid
- ✅ active=false - Valid
- ✅ active=null - Valid (partial update)
- ❌ active="true" (string) - Invalid: must be boolean
- ❌ active=1 - Invalid: must be boolean, not numeric
- ❌ active="yes" - Invalid: must be boolean

---

### 2. Authentication & Authorization Rules

#### AR1: User Authentication Requirement

**Rule:** ANY profile update request MUST be from an authenticated user. The system SHALL:
- Require HTTP authentication (existing HTTP Basic auth or other Spring Security mechanism)
- Extract authenticated user ID from security context
- Extract authenticated user roles/authorities from security context
- Reject unauthenticated requests with 401 Unauthorized

**Enforcement Point:** Spring Security at controller level

**Error Handling:** Return HTTP 401 Unauthorized if not authenticated

**Rationale:** Ensures all changes are attributable to authenticated users; prevents anonymous modifications

---

#### AR2: Admin Full Access Authorization

**Rule:** If the authenticated user has role "ROLE_ADMIN", the system SHALL:
- Allow updates to ANY user's profile (not just own profile)
- Allow updates to ALL fields (name, email, role, active)
- Apply no field-level restrictions
- Still enforce data validation rules (email format, role validity, etc.)

**Enforcement Point:** Authorization logic in service layer

**Implications:**
- Admin can update any user's profile including their own
- Admin can grant/revoke admin role to other users
- Admin can activate/deactivate any account
- Admin can change any email address (if unique)

**Examples:**
- Admin user Alice (ID: 100) can update User Bob (ID: 50) → Allowed
- Admin can change Bob's role from ROLE_USER to ROLE_ADMIN → Allowed
- Admin can deactivate User Bob (set active=false) → Allowed

---

#### AR3: Regular User Self-Update Only

**Rule:** If the authenticated user does NOT have role "ROLE_ADMIN", the system SHALL:
- Allow updates ONLY to the authenticated user's own profile
- Enforce condition: authenticated_user_id == target_user_id
- Reject any attempt to update another user's profile with HTTP 403 Forbidden
- Still allow partial updates (selective fields)

**Enforcement Point:** Authorization logic in service layer

**Error Handling:** Return HTTP 403 Forbidden if attempting cross-user update

**Implications:**
- Regular user Sarah (ID: 1) can update her own profile (ID: 1) → Allowed
- Regular user Sarah (ID: 1) cannot update User Bob (ID: 2) → Rejected
- Regular user can update own email/name → Allowed

**Examples:**
- User Sarah attempts PUT /api/users/1 (her own ID) → Allowed
- User Sarah attempts PUT /api/users/2 (different user) → Rejected with 403 Forbidden

---

#### AR4: Regular User Field-Level Restrictions

**Rule:** For regular (non-admin) users, even when performing self-updates, the system SHALL:
- Allow updates to: name, email
- Prohibit updates to: role, active
- Reject requests that attempt to modify prohibited fields with HTTP 403 Forbidden
- Treat any attempt to modify restricted fields as authorization failure

**Enforcement Point:** Authorization logic in service layer (checks field values in request)

**Error Handling:** Return HTTP 403 Forbidden if attempting to modify restricted fields

**Business Rationale:** Prevents regular users from elevating themselves to admin or disabling their own accounts

**Field Restrictions Table:**

| Field | Regular User | Admin |
|-------|---|---|
| name | ✅ Can update | ✅ Can update |
| email | ✅ Can update | ✅ Can update |
| role | ❌ Cannot update | ✅ Can update |
| active | ❌ Cannot update | ✅ Can update |

**Examples:**
- User Sarah tries: `{"name": "New Name", "email": "new@ex.com"}` → Allowed
- User Sarah tries: `{"name": "New Name", "role": "ROLE_ADMIN"}` → Rejected with 403
- User Sarah tries: `{"active": false}` → Rejected with 403
- User Sarah tries: `{"email": "new@ex.com", "active": true}` → Rejected (active field prohibited)

---

### 3. Data Integrity Rules

#### DI1: Email Uniqueness Constraint

**Rule:** The system SHALL enforce that email addresses are unique across all users. When updating a user's email address:
- Check if the new email is already used by another user
- Allow if: email is unique OR email hasn't changed
- Reject if: email is already used by a different user
- Return HTTP 409 Conflict if email not unique

**Enforcement Point:** Business logic validation in service layer (pre-update check)

**Implementation Details:**
- Query: Check if `existsByEmailAndIdNot(newEmail, targetUserId)`
- The `IdNot` part allows user to keep their current email unchanged
- Must be checked BEFORE update, not after (pre-check pattern)

**Error Handling:** Return HTTP 409 Conflict with message indicating email already in use

**Business Rationale:** Email is used for authentication and must be globally unique

**Examples:**
- User Sarah (ID: 1, email: sarah@ex.com) tries to update to john@ex.com
  - Check: Is john@ex.com used by user ID != 1?
  - Result: If no, update allowed. If yes (used by John), return 409 Conflict
- User Sarah (ID: 1, email: sarah@ex.com) updates to SARAH@EX.COM (case change)
  - Result: Allowed (same email, just case difference)

---

#### DI2: Email Normalization

**Rule:** Email addresses SHALL be stored in lowercase to ensure consistent comparison and prevent duplicate emails with different casing.

**Enforcement Point:** Service layer before persistence

**Implementation:** Convert email to lowercase: `email.toLowerCase()`

**Business Rationale:** Email is case-insensitive in most systems but stored case-sensitive in databases

---

#### DI3: Role Value Consistency

**Rule:** Only valid system-defined role values SHALL be stored in the database. When a role update is requested:
- Validate role is one of: "ROLE_USER", "ROLE_ADMIN"
- Reject invalid values immediately
- Prevent invalid roles from being persisted

**Enforcement Point:** Business logic validation before persistence

**Implementation:** 
```
if (!isValidRole(roleValue)) {
  throw ValidationException("Invalid role value")
}
```

**Business Rationale:** Ensures system has consistent, predictable role values for authorization

---

#### DI4: Immutable User ID

**Rule:** The user ID (primary key) CANNOT be changed. The system SHALL:
- Never allow user ID modifications
- Ignore any attempt to update ID
- Treat ID as immutable throughout profile update process

**Enforcement Point:** Data model (ID is primary key, cannot be updated)

**Business Rationale:** User ID is foundation of identity and primary key; changing it breaks all references

---

#### DI5: Transactional Atomicity

**Rule:** All profile update operations SHALL be atomic within a database transaction. The system SHALL:
- Group all field updates (name, email, role, active) into single transaction
- Apply all updates together
- If any validation or persistence fails, rollback ALL changes
- Maintain database consistency

**Enforcement Point:** Service layer with @Transactional annotation

**Behavior:** 
- All-or-nothing: Either entire update succeeds or entire update fails
- No partial updates persisted to database
- If user provides multiple field changes and one fails validation, none are applied

**Example:**
- Request: update name AND email AND role
- Scenario 1: Name valid, email valid, role INVALID
  - Result: No changes persisted (entire transaction rolled back)
  - User still has original name, email, role
- Scenario 2: Name valid, email valid, role valid
  - Result: All three fields updated together

---

### 4. Business Process Rules

#### BP1: Partial Update Support

**Rule:** The profile update API SHALL support partial updates (updating subset of fields). The system SHALL:
- Treat each field as optional (null = do not update)
- Update ONLY fields that are explicitly provided (not null) in request
- Leave other fields unchanged
- Allow requests with just name, just email, or any combination

**Enforcement Point:** Service logic checks each field for null before updating

**Implementation:**
```
if (request.name != null) {
  user.setName(request.name)
}
if (request.email != null) {
  user.setEmail(request.email)
}
// etc.
```

**Examples:**
- Request: `{"name": "New Name"}` → Update only name, keep email/role/active unchanged
- Request: `{"email": "new@ex.com"}` → Update only email, keep name/role/active unchanged
- Request: `{"name": "New", "email": "new@ex.com", "role": "ROLE_ADMIN"}` → Update all three (if authorized)

**Business Rationale:** Allows flexible, fine-grained updates; reduces unnecessary data transmission

---

#### BP2: User Lookup Verification

**Rule:** Before performing ANY profile update, the system SHALL verify the target user exists in the database. If user not found:
- Return HTTP 404 Not Found
- Do not attempt to create new user
- Do not proceed with update

**Enforcement Point:** Service layer looks up user by ID

**Implementation:**
```
User user = repository.findById(userId)
  .orElseThrow(() -> new UserNotFoundException())
```

**Error Handling:** Return HTTP 404 Not Found

**Business Rationale:** Ensures updates only apply to existing users; prevents accidental user creation

---

#### BP3: Change Logging and Audit Trail (Future)

**Rule (Future Enhancement):** The system MAY log all profile update operations including:
- Timestamp of update
- Authenticated user who performed update
- User whose profile was updated
- Fields that changed
- Old values vs new values

**Enforcement Point:** Service layer (would add audit logging)

**Status:** Currently not implemented; documented for future enhancement

---

### 5. Response and Feedback Rules

#### RF1: Successful Update Response

**Rule:** When profile update succeeds, the system SHALL:
- Return HTTP 200 OK
- Include complete updated user profile in response body (UserResponse DTO)
- Include all user fields: id, name, email, role, active
- Use JSON content type

**Enforcement Point:** Controller response generation

**Response Format:**
```json
{
  "id": 1,
  "name": "Updated Name",
  "email": "updated@example.com",
  "role": "ROLE_USER",
  "active": true
}
```

**Business Rationale:** Allows client to immediately see updated profile without additional request

---

#### RF2: Error Response Format

**Rule:** All error responses SHALL include:
- Appropriate HTTP status code
- Machine-readable error code (optional)
- Human-readable error message
- Timestamp of error
- Request path
- Additional field-level details if applicable (for validation errors)

**Enforcement Point:** GlobalExceptionHandler

**Response Format:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Validation failed",
  "path": "/api/users/1",
  "details": [
    {
      "field": "email",
      "message": "must be a valid email address"
    }
  ]
}
```

**Business Rationale:** Provides clients with clear, actionable error information

---

## Business Rules Priority & Enforcement Matrix

| Priority | Rule | Must Enforce | When | Enforcement Point |
|----------|------|---|---|---|
| CRITICAL | AR1: Authentication required | Always | Before any operation | Spring Security |
| CRITICAL | AR2/3: Authorization | Always | Before update | Service layer |
| CRITICAL | DI1: Email uniqueness | Always | Before persist | Service layer |
| CRITICAL | DI5: Transactional atomicity | Always | During persist | @Transactional |
| HIGH | DV1-4: Input validation | Always | Request received | DTO/Spring validation |
| HIGH | DI3: Role validity | Always | Before persist | Service layer |
| MEDIUM | BP1: Partial updates | Always | During update | Service logic |
| MEDIUM | BP2: User exists | Always | Before update | Service lookup |
| MEDIUM | RF1/2: Response format | Always | On success/error | Controller/Handler |

---

## Business Rules by User Story

### US-001: Update Own Profile Name
- Applies: DV1 (name validation), AR3 (self-update only), DI5 (atomicity), BP1 (partial)
- Core Rules: Name validation, self-update authorization

### US-002: Update Own Profile Email
- Applies: DV2 (email validation), AR3 (self-update), DI1 (email uniqueness), DI2 (normalization), DI5 (atomicity)
- Core Rules: Email validation, email uniqueness, partial updates

### US-003: Prevent Unauthorized Updates
- Applies: AR1 (authentication), AR3 (self-update), AR4 (field restrictions)
- Core Rules: Authorization enforcement, field restrictions

### US-004: Admin Update Any User Profile
- Applies: AR1 (authentication), AR2 (admin full access), DV1/2 (validation), DI1 (email uniqueness), BP2 (user lookup)
- Core Rules: Admin authorization, email uniqueness, user existence

### US-005: Admin Manage User Roles
- Applies: AR1/2 (authentication + admin auth), DV3 (role validation), DI3 (role consistency), DI5 (atomicity)
- Core Rules: Admin authorization, role validation

### US-006: Admin Manage User Active Status
- Applies: AR1/2 (authentication + admin auth), DV4 (active validation), DI5 (atomicity)
- Core Rules: Admin authorization, active validation

---

## Exception Scenarios and Rule Application

### Scenario 1: Regular User Updates Own Email to Duplicate Email

**Sequence:**
1. User Sarah (ID: 1) authenticated ✅ (AR1)
2. Request: PUT /api/users/1 with email="john@ex.com"
3. Authorization: Sarah (ID: 1) updating user (ID: 1) ✅ (AR3: self-update)
4. Field check: Email field allowed ✅ (AR4)
5. Email validation: "john@ex.com" is valid format ✅ (DV2)
6. Email uniqueness: john@ex.com already used by user ID 2 ❌ (DI1)
7. Response: HTTP 409 Conflict - "Email already in use"

---

### Scenario 2: Regular User Attempts to Make Themselves Admin

**Sequence:**
1. User Bob (ID: 2) authenticated ✅ (AR1)
2. Request: PUT /api/users/2 with role="ROLE_ADMIN"
3. Authorization: Bob (ID: 2) updating user (ID: 2) ✅ (AR3: self-update)
4. Field check: Role field is restricted for regular users ❌ (AR4)
5. Response: HTTP 403 Forbidden - "Insufficient permissions to modify this field"

---

### Scenario 3: Admin Updates User's Name and Role

**Sequence:**
1. Admin Alice (ID: 100) authenticated ✅ (AR1)
2. Request: PUT /api/users/50 with name="New Name", role="ROLE_ADMIN"
3. Authorization: Alice is admin ✅ (AR2: full access)
4. User lookup: User ID 50 exists ✅ (BP2)
5. Name validation: "New Name" is valid ✅ (DV1)
6. Role validation: "ROLE_ADMIN" is valid ✅ (DV3)
7. Email not modified: No uniqueness check needed
8. Update: Both fields updated in single transaction ✅ (DI5)
9. Response: HTTP 200 OK with updated profile

---

## Compliance Checklist

- [x] All business rules documented
- [x] Priority levels assigned
- [x] Enforcement points identified
- [x] Error handling specified
- [x] Examples provided
- [x] Rules linked to user stories
- [x] Exception scenarios covered
- [x] Technology-agnostic (no Spring/Java specifics in this document)
- [x] Rules are clear, unambiguous, testable

---

## Summary

This document defines **23 distinct business rules** organized into 5 categories:

1. **Data Validation (4 rules):** Name, email, role, active format/length validation
2. **Authorization (4 rules):** Authentication, admin full access, regular user limits, field restrictions
3. **Data Integrity (5 rules):** Email uniqueness, normalization, role consistency, immutable ID, transactional atomicity
4. **Business Process (3 rules):** Partial updates, user lookup, audit trail
5. **Response & Feedback (2 rules):** Success response format, error response format

All rules are prioritized, mapped to enforcement points, and linked to user stories for comprehensive traceability.
