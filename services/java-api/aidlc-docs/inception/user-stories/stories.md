# User Stories - Profile Update Feature

## Story Summary

This document contains user stories for the profile update feature, organized by persona. Stories cover self-update capabilities for regular users and full administrative capabilities for administrators.

### Story Overview

| Story ID | Title | Persona | Priority | Size |
|----------|-------|---------|----------|------|
| US-001 | Update Own Profile Name | Regular User | Must Have | S |
| US-002 | Update Own Profile Email | Regular User | Must Have | M |
| US-003 | Prevent Unauthorized Profile Updates | Regular User | Must Have | S |
| US-004 | Admin Update Any User Profile | Administrator | Must Have | M |
| US-005 | Admin Manage User Roles | Administrator | Must Have | M |
| US-006 | Admin Manage User Active Status | Administrator | Must Have | S |

---

## Regular User Stories

### US-001: Update Own Profile Name

**As a** Regular User  
**I want to** update my own display name  
**So that** my profile reflects my preferred or updated name

#### Acceptance Criteria

##### Scenario 1: Successful Name Update
**Given** I am authenticated as a regular user (Sarah)  
**When** I submit a PUT request to `/api/users/{myUserId}` with a valid new name  
**Then** the system updates my name and returns 200 OK with updated profile  
**And** the response includes my new name

##### Scenario 2: Name Validation Failure
**Given** I am authenticated as a regular user  
**When** I submit a PUT request with an empty or null name  
**Then** the system returns 400 Bad Request  
**And** the response includes validation error details

##### Scenario 3: Name Length Validation
**Given** I am authenticated as a regular user  
**When** I submit a PUT request with a name exceeding 100 characters  
**Then** the system returns 400 Bad Request  
**And** the response indicates the name is too long

#### Priority
Must Have

#### Size Estimate
S (Small)

#### Technical Notes
- Leverages existing UpdateUserRequest DTO (needs enhancement)
- Uses existing UserService and UserRepository
- Validation annotations: `@NotNull`, `@NotEmpty`, `@Size(max=100)`
- Authorization check: authenticated user ID must match target user ID

---

### US-002: Update Own Profile Email

**As a** Regular User  
**I want to** update my email address  
**So that** I receive notifications and communications at my current email

#### Acceptance Criteria

##### Scenario 1: Successful Email Update
**Given** I am authenticated as a regular user (Sarah)  
**When** I submit a PUT request to `/api/users/{myUserId}` with a valid unique email  
**Then** the system updates my email and returns 200 OK with updated profile  
**And** the response includes my new email address

##### Scenario 2: Email Format Validation
**Given** I am authenticated as a regular user  
**When** I submit a PUT request with an invalid email format  
**Then** the system returns 400 Bad Request  
**And** the response indicates the email format is invalid

##### Scenario 3: Email Uniqueness Validation
**Given** I am authenticated as a regular user  
**When** I submit a PUT request with an email that already exists for another user  
**Then** the system returns 409 Conflict  
**And** the response indicates the email is already in use

##### Scenario 4: Partial Update with Email Only
**Given** I am authenticated as a regular user  
**When** I submit a PUT request with only email field (name omitted)  
**Then** the system updates only the email and keeps the name unchanged  
**And** the system returns 200 OK with complete profile

#### Priority
Must Have

#### Size Estimate
M (Medium)

#### Technical Notes
- Requires email uniqueness check: `userRepository.existsByEmailAndIdNot(email, userId)`
- Validation annotations: `@NotNull`, `@Email`
- Must handle partial updates (PATCH-like behavior with PUT)
- Transaction management for uniqueness check + update

---

### US-003: Prevent Unauthorized Profile Updates

**As a** Regular User  
**I want to** be prevented from updating other users' profiles  
**So that** user data integrity and privacy are maintained

#### Acceptance Criteria

##### Scenario 1: Attempt to Update Another User's Profile
**Given** I am authenticated as a regular user (Sarah, userId=1)  
**When** I submit a PUT request to `/api/users/2` (another user)  
**Then** the system returns 403 Forbidden  
**And** no profile changes are made

##### Scenario 2: Attempt to Update Own Role
**Given** I am authenticated as a regular user  
**When** I submit a PUT request to `/api/users/{myUserId}` including a role change  
**Then** the system returns 403 Forbidden  
**And** my role remains unchanged

##### Scenario 3: Attempt to Update Own Active Status
**Given** I am authenticated as a regular user  
**When** I submit a PUT request to `/api/users/{myUserId}` including active status change  
**Then** the system returns 403 Forbidden  
**And** my active status remains unchanged

#### Priority
Must Have

#### Size Estimate
S (Small)

#### Technical Notes
- Authorization logic in UserService
- Check: `authenticatedUserId == targetUserId`
- Check: regular user cannot modify `role` field
- Check: regular user cannot modify `active` field
- Use Spring Security context to get authenticated user

---

## Administrator Stories

### US-004: Admin Update Any User Profile

**As an** Administrator  
**I want to** update any user's name and email  
**So that** I can manage user information and support users who need profile updates

#### Acceptance Criteria

##### Scenario 1: Successful Admin Update of Another User
**Given** I am authenticated as an administrator (Michael)  
**When** I submit a PUT request to `/api/users/{anyUserId}` with updated name and email  
**Then** the system updates the user's profile and returns 200 OK  
**And** the response includes the updated user information

##### Scenario 2: Admin Update with Email Uniqueness Check
**Given** I am authenticated as an administrator  
**When** I submit a PUT request with an email that already exists  
**Then** the system returns 409 Conflict  
**And** the user's profile remains unchanged

##### Scenario 3: Admin Update Non-Existent User
**Given** I am authenticated as an administrator  
**When** I submit a PUT request to `/api/users/99999` (non-existent user)  
**Then** the system returns 404 Not Found  
**And** the response indicates the user was not found

##### Scenario 4: Admin Partial Update
**Given** I am authenticated as an administrator  
**When** I submit a PUT request with only some fields (e.g., email only)  
**Then** the system updates only the provided fields  
**And** other fields remain unchanged

#### Priority
Must Have

#### Size Estimate
M (Medium)

#### Technical Notes
- Authorization check: `hasRole('ROLE_ADMIN')`
- Same validation rules as regular user for name and email
- Must support partial updates
- User lookup: `userRepository.findById(userId).orElseThrow(() -> new UserNotFoundException())`

---

### US-005: Admin Manage User Roles

**As an** Administrator  
**I want to** change any user's role  
**So that** I can grant or revoke administrative privileges as needed

#### Acceptance Criteria

##### Scenario 1: Grant Admin Role to User
**Given** I am authenticated as an administrator (Michael)  
**When** I submit a PUT request to `/api/users/{userId}` with role set to "ROLE_ADMIN"  
**Then** the system updates the user's role to ROLE_ADMIN  
**And** the system returns 200 OK with updated profile showing the new role

##### Scenario 2: Revoke Admin Role from User
**Given** I am authenticated as an administrator  
**When** I submit a PUT request to `/api/users/{userId}` with role set to "ROLE_USER"  
**Then** the system updates the user's role to ROLE_USER  
**And** the system returns 200 OK with updated profile

##### Scenario 3: Invalid Role Value
**Given** I am authenticated as an administrator  
**When** I submit a PUT request with an invalid role value (e.g., "ROLE_INVALID")  
**Then** the system returns 400 Bad Request  
**And** the response indicates the role value is invalid

##### Scenario 4: Regular User Cannot Change Roles
**Given** I am authenticated as a regular user  
**When** I attempt to change any user's role (including my own)  
**Then** the system returns 403 Forbidden  
**And** no role changes are made

#### Priority
Must Have

#### Size Estimate
M (Medium)

#### Technical Notes
- Authorization check: `hasRole('ROLE_ADMIN')`
- Role validation: must be one of the valid role constants
- Consider enum for role values: `enum Role { ROLE_USER, ROLE_ADMIN }`
- Update affects user's authorization immediately on next request

---

### US-006: Admin Manage User Active Status

**As an** Administrator  
**I want to** activate or deactivate user accounts  
**So that** I can control user access without deleting accounts

#### Acceptance Criteria

##### Scenario 1: Deactivate User Account
**Given** I am authenticated as an administrator (Michael)  
**When** I submit a PUT request to `/api/users/{userId}` with active set to false  
**Then** the system updates the user's active status to false  
**And** the system returns 200 OK with updated profile

##### Scenario 2: Reactivate User Account
**Given** I am authenticated as an administrator  
**When** I submit a PUT request to `/api/users/{userId}` with active set to true  
**Then** the system updates the user's active status to true  
**And** the system returns 200 OK with updated profile

##### Scenario 3: Regular User Cannot Change Active Status
**Given** I am authenticated as a regular user  
**When** I attempt to change any user's active status (including my own)  
**Then** the system returns 403 Forbidden  
**And** no active status changes are made

#### Priority
Must Have

#### Size Estimate
S (Small)

#### Technical Notes
- Authorization check: `hasRole('ROLE_ADMIN')`
- Active status is boolean field
- Consider: should deactivated users be able to authenticate? (depends on UserDetailsService implementation)
- Audit trail: log active status changes for compliance

---

## Requirements Traceability

### Functional Requirements Coverage

| Requirement | Stories |
|-------------|---------|
| FR1: Profile Update Endpoint | All stories |
| FR2: Updatable Profile Fields | US-001, US-002, US-005, US-006 |
| FR3: Request Validation | US-001, US-002, US-004, US-005 |
| FR4: Authorization Rules | US-003, US-004, US-005, US-006 |
| FR5: Response Format | All stories |
| FR6: Error Handling | US-002, US-003, US-004, US-005, US-006 |

### Non-Functional Requirements Coverage

| Requirement | Implementation Notes |
|-------------|---------------------|
| NFR1: Security | Covered in US-003, US-005, US-006 (authorization checks) |
| NFR2: Performance | Target: <200ms response time (to be measured in testing) |
| NFR3: Data Integrity | Covered in US-002 (email uniqueness), all updates transactional |
| NFR4: Compatibility | All stories use existing Spring Boot 3.2 / Java 21 patterns |
| NFR5: Testing | Each story has testable acceptance criteria |

---

## Story Dependencies

```
US-001 ─┐
        ├─> US-004 (Admin story extends user story capabilities)
US-002 ─┤
        ├─> US-005 (Adds role management)
US-003 ─┘   └─> US-006 (Adds active status management)
```

**Implementation Order Recommendation**:
1. **Phase 1**: US-001, US-002, US-003 (Core self-update with authorization)
2. **Phase 2**: US-004 (Admin capabilities for name/email)
3. **Phase 3**: US-005, US-006 (Additional admin capabilities for role/active)

---

## Technical Implementation Notes

### API Endpoint Design
```
PUT /api/users/{userId}
Content-Type: application/json

Request Body (UpdateUserRequest):
{
  "name": "string (optional for partial update)",
  "email": "string (optional for partial update)",
  "role": "string (admin only)",
  "active": "boolean (admin only)"
}

Response (UserResponse):
{
  "id": "long",
  "name": "string",
  "email": "string",
  "role": "string",
  "active": "boolean"
}
```

### Authorization Logic Flow
```
1. Extract authenticated user from SecurityContext
2. Check if authenticated user is admin:
   - If YES: Allow all updates to any user
   - If NO: Check if targetUserId == authenticatedUserId
     - If YES: Allow name/email updates only
     - If NO: Return 403 Forbidden
3. Validate request data
4. Execute update
5. Return updated profile
```

### Validation Rules Summary
- **Name**: `@NotNull`, `@NotEmpty`, `@Size(max=100)`
- **Email**: `@NotNull`, `@Email`, unique constraint check
- **Role**: Valid enum value (ROLE_USER, ROLE_ADMIN)
- **Active**: Boolean (true/false)

---

## Definition of Done

Each story is considered complete when:
- [ ] Code implementation matches acceptance criteria
- [ ] Unit tests cover all scenarios (success and failure paths)
- [ ] Integration tests verify API endpoints
- [ ] Authorization rules are tested
- [ ] Validation rules are tested
- [ ] Error handling produces correct HTTP status codes
- [ ] Code review completed
- [ ] Documentation updated (API docs, README)
- [ ] Manual testing confirms expected behavior
