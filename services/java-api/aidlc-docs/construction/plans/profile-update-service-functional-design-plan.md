# Functional Design Plan - Profile Update Service

## Unit Context

**Unit Name**: `profile-update-service`  
**Target Repository**: `/home/sk/vscode/aws-sagents-dlc/kiro-sandbox/services/java-api`  
**Architecture**: Monolithic Spring Boot 3.2 with 3-tier pattern  
**Base Package**: `com.sandbox.userapi`

---

## Step 1: Unit Context Analysis ✓

### Unit Definition Summary
- **Scope**: Profile update functionality for existing User management system
- **Stories**: 6 user stories covering self-update and admin capabilities
- **Components**: UserController, UserService, UpdateUserRequest DTO, UserRepository, User Entity, UserResponse DTO
- **Infrastructure**: Existing Spring Boot, Spring Security, JPA/H2, GlobalExceptionHandler

### Assigned Stories
1. **US-001**: Update Own Profile Name (Small)
2. **US-002**: Update Own Profile Email (Medium)
3. **US-003**: Prevent Unauthorized Profile Updates (Small)
4. **US-004**: Admin Update Any User Profile (Medium)
5. **US-005**: Admin Manage User Roles (Medium)
6. **US-006**: Admin Manage User Active Status (Small)

---

## Step 2: Functional Design Plan

### Functional Design Execution Checklist

- [ ] **Section A**: Clarify authorization business logic and edge cases
- [ ] **Section B**: Clarify email uniqueness validation strategy
- [ ] **Section C**: Clarify partial update semantics and null-handling
- [ ] **Section D**: Clarify business rules for role changes and active status
- [ ] **Section E**: Clarify error handling and recovery scenarios
- [ ] **Section F**: Clarify domain model relationships and constraints
- [ ] **Section G**: Review all answers for completeness
- [ ] **Section H**: Generate business-logic-model.md artifact
- [ ] **Section I**: Generate business-rules.md artifact
- [ ] **Section J**: Generate domain-entities.md artifact
- [ ] **Section K**: Present completion and wait for approval

---

## Step 3: Clarifying Questions

### Section A: Authorization Business Logic

**Question A1**: Role-Based Authorization Inheritance  
When checking authorization, should the system support role hierarchies (e.g., ROLE_SUPER_ADMIN > ROLE_ADMIN > ROLE_USER), or are roles flat and non-hierarchical?

[Answer]: ___________________________________________________________________________

**Question A2**: Self-Update of Admin by Non-Admin  
If a regular user (ROLE_USER) somehow has admin privileges temporarily revoked mid-session, and they attempt to update their own profile, should they be allowed to update their name/email even after their role changes?

[Answer]: ___________________________________________________________________________

**Question A3**: Admin Updating Admin  
When an administrator updates another administrator's profile (name, email, role, active), are there any restrictions? Can an admin deactivate another admin? Can an admin change another admin's role?

[Answer]: ___________________________________________________________________________

**Question A4**: Concurrent Authorization Changes  
If User A (admin) changes User B's role from ROLE_USER to ROLE_ADMIN while User B has an active browser session, should User B's authorization change take effect immediately, or only on next login?

[Answer]: ___________________________________________________________________________

### Section B: Email Uniqueness Validation

**Question B1**: Email Case Sensitivity  
Should email addresses be treated as case-insensitive for uniqueness checks (e.g., "john@example.com" and "JOHN@EXAMPLE.com" are the same)? Or case-sensitive?

[Answer]: ___________________________________________________________________________

**Question B2**: Email Whitespace Handling  
Should email addresses be trimmed of leading/trailing whitespace before uniqueness validation? Should internal whitespace be rejected?

[Answer]: ___________________________________________________________________________

**Question B3**: Concurrent Email Updates  
If User A and User B both attempt to update their email to the same new address simultaneously, what should happen?
- First write wins, second gets 409 Conflict?
- Both requests fail?
- Race condition acceptance?

[Answer]: ___________________________________________________________________________

**Question B4**: Historical Email Uniqueness  
Can a user reclaim their own previous email address if they changed it? For example:
- User has email1@example.com
- User changes to email2@example.com
- User changes back to email1@example.com
Is this allowed?

[Answer]: ___________________________________________________________________________

### Section C: Partial Update Semantics

**Question C1**: Null vs. Omitted Fields  
For optional fields, how should the system differentiate between:
- Field omitted from JSON (should not update)?
- Field present with null value (should clear/set to null)?
- Field present with value (should update)?

Example:
```json
{
  "name": "John",
  "email": null,
  "role": "ROLE_ADMIN"
}
```

Should `email: null` clear the user's email (if allowed) or be treated as "don't update"?

[Answer]: ___________________________________________________________________________

**Question C2**: Empty String Handling  
Should an empty string ("") be treated differently from null?
- For name field: allow empty string or reject as invalid?
- For email field: allow empty string or reject as invalid?

[Answer]: ___________________________________________________________________________

**Question C3**: Field-Level Permissions in Partial Updates  
If a regular user submits a partial update like:
```json
{
  "name": "New Name",
  "role": "ROLE_ADMIN"
}
```

Should the system:
- Reject the entire request (403 Forbidden)?
- Update only the allowed field (name) and ignore role?
- Return 400 Bad Request with message about role field?

[Answer]: ___________________________________________________________________________

**Question C4**: Validation for Partial Updates  
For optional fields that are provided, should all validation rules apply?
- If user provides only email in partial update, should email format validation apply?
- If user provides only name, should name length validation apply?

[Answer]: ___________________________________________________________________________

### Section D: Business Rules for Role and Active Status

**Question D1**: Role Values and Validation  
Are there only two valid roles (ROLE_USER, ROLE_ADMIN), or are there additional roles in the system? Should new roles be added in the future?

[Answer]: ___________________________________________________________________________

**Question D2**: Default Role for New Users  
When a new user is created, what is the default role? Is this relevant to profile updates, or only user creation?

[Answer]: ___________________________________________________________________________

**Question D3**: Active Status and Authentication  
When a user's active status is set to false (deactivated):
- Should they be immediately logged out?
- Should their existing sessions be invalidated?
- Should subsequent login attempts be rejected?

[Answer]: ___________________________________________________________________________

**Question D4**: Active Status Constraints  
Should the system prevent all administrators from being deactivated (at least one admin must remain active), or is any user deactivatable?

[Answer]: ___________________________________________________________________________

**Question D5**: Role Change Audit Requirements  
Should role changes be logged for compliance/audit purposes? If yes, what information should be captured?
- Who made the change (admin user ID)?
- When was it changed (timestamp)?
- Old role and new role?
- Reason for change?

[Answer]: ___________________________________________________________________________

### Section E: Error Handling and Recovery

**Question E1**: Validation Error Detail Level  
When validation fails (e.g., invalid email format), how much detail should error messages include?
- Generic: "Email is invalid"
- Specific: "Email must contain exactly one @ symbol and valid domain"
- Include field name and rejected value?

[Answer]: ___________________________________________________________________________

**Question E2**: Email Conflict Resolution  
When a 409 Conflict is returned (email already exists), should the response include:
- The conflicting email address?
- Which user owns the email?
- Suggestions for alternative emails?

[Answer]: ___________________________________________________________________________

**Question E3**: Partial Update Rollback  
If a partial update fails partway through (e.g., name updates but email update fails), should the system:
- Rollback all changes (atomicity)?
- Keep name update and fail only on email (partial commit)?
- Cascade rollback at which boundary?

[Answer]: ___________________________________________________________________________

**Question E4**: User Not Found Handling  
When a user ID doesn't exist (404 Not Found), should the response message:
- Explicitly state "User ID X not found"?
- Be generic: "Resource not found"?
- Include hints about valid user ranges?

[Answer]: ___________________________________________________________________________

### Section F: Domain Model Relationships

**Question F1**: User Entity Relationships  
Beyond the core User fields (id, name, email, role, active), are there other entities that reference User (e.g., Address, Phone, Preferences)?

[Answer]: ___________________________________________________________________________

**Question F2**: Email as Unique Identifier  
Is email globally unique across the system, or could there be test/demo users with duplicate emails in certain scenarios?

[Answer]: ___________________________________________________________________________

**Question F3**: User Soft Deletes  
Should deactivated users be considered "soft deleted" or are they still queryable? Can admins list deactivated users?

[Answer]: ___________________________________________________________________________

**Question F4**: Cascading Constraints  
If a user is deactivated, should:
- Their profile be partially hidden from other users?
- Their activities/posts be marked as from inactive user?
- Any dependent records be affected?

[Answer]: ___________________________________________________________________________

### Section G: Additional Business Logic

**Question G1**: Name Format Validation  
Beyond length (max 100 chars), are there additional name validation rules?
- Only alphanumeric and spaces allowed?
- Allow special characters (hyphens, apostrophes)?
- Allow numbers in names?
- Allow non-Latin characters?

[Answer]: ___________________________________________________________________________

**Question G2**: Email Domain Restrictions  
Are there allowed/disallowed email domains?
- Any domain allowed?
- Whitelist of domains?
- Blacklist of domains?
- No corporate email addresses?

[Answer]: ___________________________________________________________________________

**Question G3**: Update Frequency Limits  
Should there be rate limiting on profile updates?
- Unlimited updates per user per day?
- Limit updates to X per day?
- Limit role changes more than name changes?

[Answer]: ___________________________________________________________________________

**Question G4**: Notification Triggers  
Should profile updates trigger any business logic?
- Send email notification to user about profile changes?
- Notify admins about certain updates?
- Trigger audit log entries?

[Answer]: ___________________________________________________________________________

---

## Answer Summary Template

Once you provide answers to all questions above, I will:

1. Review answers for clarity and completeness
2. Ask any follow-up questions if ambiguities exist
3. Generate three functional design artifacts:
   - **business-logic-model.md** - Core algorithms and workflows
   - **business-rules.md** - Validation, authorization, and constraints
   - **domain-entities.md** - Data model and relationships

---

## Next Steps

1. **User Action**: Complete all [Answer]: fields above with specific responses
2. **AI Action**: Review answers and clarify any ambiguities
3. **AI Action**: Generate functional design artifacts
4. **User Action**: Review artifacts and approve or request changes
5. **AI Action**: Update workflow state to mark stage complete

---

**Please complete all [Answer]: fields and return this document.**
