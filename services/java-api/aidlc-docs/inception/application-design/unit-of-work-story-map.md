# Unit of Work Story Map - Profile Update Feature

## Overview

This document maps user stories to the Profile Update Service unit, defining story assignment, implementation sequencing, dependencies between stories, and acceptance criteria validation.

---

## Story-to-Unit Assignment

### Unit: profile-update-service

**Unit Type:** Monolithic Feature Module  
**Stories Assigned:** 6 (100% of feature scope)  
**Total Story Points:** ~10 points  
**Team Capacity:** 1-2 sprints (single team)  
**Status:** Ready for CONSTRUCTION phase

---

## Story Assignment Summary

| Story ID | Title | Persona | Size | Points | Priority | Unit | Phase |
|----------|-------|---------|------|--------|----------|------|-------|
| US-001 | Update Own Profile Name | Regular User | S | 1 | Must Have | profile-update-service | 1 |
| US-002 | Update Own Profile Email | Regular User | M | 2 | Must Have | profile-update-service | 1 |
| US-003 | Prevent Unauthorized Updates | Regular User | S | 1 | Must Have | profile-update-service | 1 |
| US-004 | Admin Update Any User Profile | Administrator | M | 2 | Must Have | profile-update-service | 2 |
| US-005 | Admin Manage User Roles | Administrator | M | 2 | Must Have | profile-update-service | 2 |
| US-006 | Admin Manage User Active Status | Administrator | S | 1 | Must Have | profile-update-service | 2 |

**Total:** 6 stories, ~10 story points, 2 development phases

---

## Story Dependencies & Sequencing

### Dependency Graph

```
US-001 ────────┐
(Name update)  │
               ├─→ Core infrastructure
               │   (DTOs, Controller,
US-002 ────────┤    Service setup)
(Email update) │
               │
US-003 ────────┤─→ Authorization enforcement
(Prevent unauth)
               │
               └──→ Phase 1 (Regular User Features)
                       │
                       ▼ Builds on Phase 1 foundation
                       │
                US-004 (Admin any user) ────┐
                                            ├─→ Admin capabilities
                US-005 (Admin roles) ───────┤   (Building on Phase 1)
                                            │
                IS-006 (Admin active) ──────┘
                
                       Phase 2 (Admin Features)
```

### Implementation Sequencing

**Phase 1: Regular User Features (Sprint 1)**
1. US-001: Update Own Profile Name
2. US-002: Update Own Profile Email
3. US-003: Prevent Unauthorized Updates

**Phase 2: Admin Features (Sprint 2)**
4. US-004: Admin Update Any User Profile
5. US-005: Admin Manage User Roles
6. US-006: Admin Manage User Active Status

### Story Dependencies Details

| Story | Depends On | Reason | Constraint |
|-------|-----------|--------|-----------|
| US-001 | None | First story, sets up core | None |
| US-002 | US-001 | Uses same endpoint/service | Email validation, uniqueness |
| US-003 | US-001, US-002 | Tests authorization logic | Can't test until US-001 exists |
| US-004 | US-001, US-002, US-003 | Builds on core features | Extends existing endpoint |
| US-005 | US-004 | Adds role field to DTO | Role validation rules |
| US-006 | US-004 | Adds active field to DTO | Active status handling |

**Critical Path:** US-001 → US-002 → US-003 → US-004 → (US-005 and US-006 can be parallel)

---

## Story Details & Implementation Plan

### US-001: Update Own Profile Name

**Story Card:**
```
Title: Update Own Profile Name
Persona: Regular User (Sarah)
Priority: Must Have
Size: S (1 story point)
Phase: 1 (Foundation)
```

**User Story:**
```
As a Regular User,
I want to update my own display name,
So that my profile reflects my preferred or updated name
```

**Acceptance Criteria:**

| Scenario | Given | When | Then | Components |
|----------|-------|------|------|-----------|
| AC1: Success | Authenticated as regular user | PUT /api/users/1 with valid name | 200 OK with updated profile | Controller, Service, DTO, Repo |
| AC2: Validation | Authenticated as regular user | PUT with empty/null name | 400 Bad Request with error | DTO validation, Service |
| AC3: Length limit | Authenticated as regular user | PUT with name > 100 chars | 400 Bad Request | Bean Validation @Size |

**Implementation Tasks:**

- [ ] Task 1.1: Enhance UpdateUserRequest DTO with name field
  - Add `private String name;` field
  - Add `@Size(max = 100)` annotation
  - Implement getter/setter
  
- [ ] Task 1.2: Implement UserService.updateUser() for name updates
  - Add method signature
  - Implement authorization check (must be self-update)
  - Implement field update logic
  - Add @Transactional annotation
  
- [ ] Task 1.3: Implement UserController.updateUser() endpoint
  - Add @PutMapping("/api/users/{userId}")
  - Extract authentication context
  - Call UserService.updateUser()
  - Return UserResponse with 200 OK
  
- [ ] Task 1.4: Verify UserRepository has required methods
  - findById() for user lookup
  - save() for persistence
  
- [ ] Task 1.5: Add unit tests
  - Test successful name update
  - Test name validation (max 100 chars)
  - Test authorization (self-update only)

**Component Involvement:**
- UserController: HTTP endpoint
- UserService: Authorization + update logic
- UpdateUserRequest: DTO with name field
- UserRepository: Load/save user
- User Entity: Domain model
- UserResponse: Response DTO

**Definition of Done:**
- [x] Name field added to UpdateUserRequest
- [x] UserService handles name updates
- [x] UserController endpoint accepts PUT requests
- [x] Validation enforces max 100 characters
- [x] Authorization checks self-update
- [x] Unit tests pass (success + validation)
- [x] Integration tests pass
- [x] Code review completed

---

### US-002: Update Own Profile Email

**Story Card:**
```
Title: Update Own Profile Email
Persona: Regular User (Sarah)
Priority: Must Have
Size: M (2 story points)
Phase: 1 (Foundation)
Depends On: US-001
```

**User Story:**
```
As a Regular User,
I want to update my email address,
So that I receive notifications and communications at my current email
```

**Acceptance Criteria:**

| Scenario | Given | When | Then | Components |
|----------|-------|------|------|-----------|
| AC1: Success | Authenticated as regular user | PUT with valid unique email | 200 OK with updated profile | Controller, Service, DTO, Repo |
| AC2: Format validation | Authenticated as regular user | PUT with invalid email | 400 Bad Request | DTO validation |
| AC3: Uniqueness check | Authenticated as regular user | PUT with email already in use | 409 Conflict | Service validation |
| AC4: Partial update | Authenticated as regular user | PUT with email only (no name) | Updates email, keeps name | Service logic |

**Implementation Tasks:**

- [ ] Task 2.1: Enhance UpdateUserRequest DTO with email field
  - Add `private String email;` field
  - Add `@Email` annotation
  - Implement getter/setter
  
- [ ] Task 2.2: Implement email uniqueness validation in UserService
  - Add validateEmailUniqueness() helper method
  - Call UserRepository.existsByEmailAndIdNot()
  - Throw EmailAlreadyExistsException if not unique
  
- [ ] Task 2.3: Add custom repository query method (if needed)
  - Add existsByEmailAndIdNot(String email, Long userId)
  - Uses Spring Data JPA query derivation or @Query
  
- [ ] Task 2.4: Update UserService.updateUser() for email updates
  - Add email update logic (if provided in request)
  - Call validateEmailUniqueness() before update
  - Handle partial updates (email only)
  
- [ ] Task 2.5: Add unit tests
  - Test successful email update
  - Test email format validation
  - Test email uniqueness validation (409 Conflict)
  - Test partial update (email only)

**Component Involvement:**
- UserService: Email validation + update logic
- UpdateUserRequest: DTO with email field
- UserRepository: Email uniqueness check, save
- User Entity: Email field
- UserResponse: Email in response

**Definition of Done:**
- [x] Email field added to UpdateUserRequest
- [x] @Email validation annotation applied
- [x] UserRepository has existsByEmailAndIdNot() method
- [x] Email uniqueness checked before update
- [x] Returns 409 Conflict if email not unique
- [x] Partial updates supported (email only)
- [x] Unit tests pass (success + validations)
- [x] Integration tests pass

---

### US-003: Prevent Unauthorized Profile Updates

**Story Card:**
```
Title: Prevent Unauthorized Profile Updates
Persona: Regular User (Sarah)
Priority: Must Have
Size: S (1 story point)
Phase: 1 (Foundation)
Depends On: US-001, US-002
```

**User Story:**
```
As a Regular User,
I want to be prevented from updating other users' profiles,
So that user data integrity and privacy are maintained
```

**Acceptance Criteria:**

| Scenario | Given | When | Then | Components |
|----------|-------|------|------|-----------|
| AC1: Other user block | Regular user (ID: 1) | PUT to /api/users/2 | 403 Forbidden | Authorization |
| AC2: Role update block | Regular user | PUT with role field | 403 Forbidden | Authorization |
| AC3: Active update block | Regular user | PUT with active field | 403 Forbidden | Authorization |

**Implementation Tasks:**

- [ ] Task 3.1: Implement authorization logic in UserService
  - Add checkUpdateAuthorization() helper method
  - Check if authenticated user is admin
  - Check if updating own profile (if not admin)
  - Check for admin-only fields (role, active)
  - Throw UnauthorizedException if not allowed
  
- [ ] Task 3.2: Extract authentication info in UserController
  - Get Authentication from SecurityContext
  - Extract user ID and role
  - Pass to UserService.updateUser()
  
- [ ] Task 3.3: Add GlobalExceptionHandler mapping
  - Map UnauthorizedException to 403 Forbidden
  - Create appropriate error response
  
- [ ] Task 3.4: Add unit tests
  - Test unauthorized: different user (403)
  - Test unauthorized: role update by regular user (403)
  - Test unauthorized: active update by regular user (403)
  - Test authorized: self-update allowed (200)

**Component Involvement:**
- UserService: Authorization logic (core)
- UserController: Extract authentication context
- GlobalExceptionHandler: Map exception to 403
- Spring Security: Provide authentication info

**Definition of Done:**
- [x] Authorization logic implemented
- [x] checkUpdateAuthorization() method added
- [x] Regular users cannot update other users (403)
- [x] Regular users cannot update role/active (403)
- [x] UnauthorizedException thrown appropriately
- [x] GlobalExceptionHandler returns 403 Forbidden
- [x] Unit tests pass (all unauthorized scenarios)
- [x] Integration tests pass

---

### US-004: Admin Update Any User Profile

**Story Card:**
```
Title: Admin Update Any User Profile
Persona: Administrator (Michael)
Priority: Must Have
Size: M (2 story points)
Phase: 2 (Admin)
Depends On: US-001, US-002, US-003
```

**User Story:**
```
As an Administrator,
I want to update any user's name and email,
So that I can manage user information and support users who need profile updates
```

**Acceptance Criteria:**

| Scenario | Given | When | Then | Components |
|----------|-------|------|------|-----------|
| AC1: Admin any user | Admin authenticated | PUT to any user with name/email | 200 OK | Authorization override |
| AC2: Email uniqueness | Admin authenticated | PUT with duplicate email | 409 Conflict | Email validation still applies |
| AC3: Not found | Admin authenticated | PUT to non-existent user | 404 Not Found | Repository lookup |
| AC4: Partial update | Admin authenticated | PUT with only email | Updates only email | Partial update logic |

**Implementation Tasks:**

- [ ] Task 4.1: Update authorization logic for admin override
  - Modify checkUpdateAuthorization() to allow admin any update
  - Admin can update any user (not just self)
  - Admin can update any field (name, email, and more)
  
- [ ] Task 4.2: Ensure UserRepository returns 404 for missing users
  - UserRepository.findById() returns Optional
  - Service throws UserNotFoundException if empty
  - GlobalExceptionHandler maps to 404
  
- [ ] Task 4.3: Add unit tests
  - Test admin can update any user (200)
  - Test admin respects email uniqueness (409)
  - Test admin gets 404 for missing user
  - Test admin can do partial updates

**Component Involvement:**
- UserService: Admin authorization override
- Authorization logic: Enhanced
- UserRepository: User lookup for any user
- GlobalExceptionHandler: Map UserNotFoundException to 404

**Definition of Done:**
- [x] Admin can update any user's profile
- [x] Authorization logic allows admin override
- [x] Email uniqueness still enforced for admin
- [x] Returns 404 for non-existent user
- [x] Returns 409 for duplicate email
- [x] Partial updates work for admin
- [x] Unit tests pass
- [x] Integration tests pass

---

### US-005: Admin Manage User Roles

**Story Card:**
```
Title: Admin Manage User Roles
Persona: Administrator (Michael)
Priority: Must Have
Size: M (2 story points)
Phase: 2 (Admin)
Depends On: US-004
```

**User Story:**
```
As an Administrator,
I want to change any user's role,
So that I can grant or revoke administrative privileges as needed
```

**Acceptance Criteria:**

| Scenario | Given | When | Then | Components |
|----------|-------|------|------|-----------|
| AC1: Grant admin | Admin authenticated | PUT with role="ROLE_ADMIN" | 200 OK with new role | Role update |
| AC2: Revoke admin | Admin authenticated | PUT with role="ROLE_USER" | 200 OK with new role | Role update |
| AC3: Invalid role | Admin authenticated | PUT with role="ROLE_INVALID" | 400 Bad Request | Role validation |
| AC4: Regular user blocked | Regular user | PUT with role field | 403 Forbidden | Authorization |

**Implementation Tasks:**

- [ ] Task 5.1: Add role field to UpdateUserRequest DTO
  - Add `private String role;` field
  - Add validation annotations for role enum
  - Implement getter/setter
  
- [ ] Task 5.2: Update UserResponse DTO
  - Ensure role field included in response
  
- [ ] Task 5.3: Implement role validation in UserService
  - Validate role is one of: ROLE_USER, ROLE_ADMIN
  - Throw ValidationException if invalid
  - Only allow role updates by admin (authorization check)
  
- [ ] Task 5.4: Add unit tests
  - Test admin can change role to ROLE_ADMIN (200)
  - Test admin can change role to ROLE_USER (200)
  - Test invalid role rejected (400)
  - Test regular user cannot change role (403)

**Component Involvement:**
- UpdateUserRequest: Add role field
- UserResponse: Include role in response
- UserService: Role validation and update logic
- Authorization: Enforce admin-only restriction

**Definition of Done:**
- [x] Role field added to UpdateUserRequest
- [x] Role field included in UserResponse
- [x] Admin can update user roles
- [x] Invalid roles rejected (400)
- [x] Regular users cannot change roles (403)
- [x] Role values validated (ROLE_USER, ROLE_ADMIN)
- [x] Unit tests pass
- [x] Integration tests pass

---

### US-006: Admin Manage User Active Status

**Story Card:**
```
Title: Admin Manage User Active Status
Persona: Administrator (Michael)
Priority: Must Have
Size: S (1 story point)
Phase: 2 (Admin)
Depends On: US-004
```

**User Story:**
```
As an Administrator,
I want to activate or deactivate user accounts,
So that I can control user access without deleting accounts
```

**Acceptance Criteria:**

| Scenario | Given | When | Then | Components |
|----------|-------|------|------|-----------|
| AC1: Deactivate | Admin authenticated | PUT with active=false | 200 OK with active=false | Active field update |
| AC2: Reactivate | Admin authenticated | PUT with active=true | 200 OK with active=true | Active field update |
| AC3: Regular user blocked | Regular user | PUT with active field | 403 Forbidden | Authorization |

**Implementation Tasks:**

- [ ] Task 6.1: Add active field to UpdateUserRequest DTO
  - Add `private Boolean active;` field (nullable)
  - Implement getter/setter
  
- [ ] Task 6.2: Update UserResponse DTO
  - Ensure active field included in response
  
- [ ] Task 6.3: Implement active status update in UserService
  - Handle Boolean active field update (if provided)
  - Enforce admin-only restriction (authorization check)
  - Regular users cannot change active status
  
- [ ] Task 6.4: Add unit tests
  - Test admin can deactivate user (200, active=false)
  - Test admin can reactivate user (200, active=true)
  - Test regular user cannot change active status (403)

**Component Involvement:**
- UpdateUserRequest: Add active field
- UserResponse: Include active in response
- UserService: Active status update + authorization
- User Entity: Active field (already exists)

**Definition of Done:**
- [x] Active field added to UpdateUserRequest
- [x] Active field included in UserResponse
- [x] Admin can update active status
- [x] Regular users cannot change active (403)
- [x] Boolean values handled correctly (true/false)
- [x] Unit tests pass
- [x] Integration tests pass

---

## Development Phases

### Phase 1: Regular User Features (Sprint 1)

**Duration:** 3-4 days  
**Stories:** US-001, US-002, US-003  
**Story Points:** ~4  
**Team:** 1-2 engineers  

**Deliverables:**
- Updateable profile endpoint (PUT /api/users/{userId})
- Self-update capability (name, email)
- Authorization enforcement (prevent cross-user updates, admin-only fields)
- Email uniqueness validation

**Milestone:** Regular user features complete, ready for admin feature integration

**Definition of Phase Done:**
- All 3 stories pass acceptance criteria
- Unit tests pass (>85% coverage)
- Integration tests verify complete workflows
- Security tests verify authorization rules
- Code review completed
- API contract verified

---

### Phase 2: Admin Features (Sprint 2)

**Duration:** 3-4 days  
**Stories:** US-004, US-005, US-006  
**Story Points:** ~5  
**Team:** 1-2 engineers (can be same or different from Phase 1)  

**Deliverables:**
- Admin override capability (update any user)
- Role management (ROLE_USER ↔ ROLE_ADMIN)
- Active status management (activate/deactivate)

**Milestone:** Feature complete, ready for production

**Definition of Phase Done:**
- All 3 stories pass acceptance criteria
- Unit tests pass (>85% coverage)
- Integration tests verify complete workflows
- Security tests verify authorization rules
- Code review completed
- Full acceptance testing completed

---

## Definition of Done (Per Story)

Each story is complete when:

### Story-Level DoD

- [ ] Code implemented per acceptance criteria
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Security tests (authorization, validation) passing
- [ ] Code review completed and approved
- [ ] No new technical debt introduced
- [ ] Documentation updated (API docs, code comments)
- [ ] Acceptance criteria verified against running code
- [ ] Performance verified (< 200ms response)
- [ ] Error handling verified (correct HTTP status codes)

### Unit-Level DoD

- [ ] All 6 stories implemented
- [ ] All acceptance criteria validated
- [ ] >85% code coverage for unit
- [ ] Authorization rules enforced 100%
- [ ] Validation rules enforced 100%
- [ ] Error handling returns correct status codes
- [ ] API contract matches specification
- [ ] Performance meets targets (< 200ms)
- [ ] Ready for production deployment

---

## Testing Strategy by Story

### US-001 Testing

**Unit Tests:**
- Name update success with valid input
- Name validation: max 100 characters
- Name validation: empty/null rejection
- Authorization: self-update allowed

**Integration Tests:**
- PUT /api/users/1 with valid name returns 200
- PUT /api/users/1 with invalid name returns 400
- Response includes updated name

### US-002 Testing

**Unit Tests:**
- Email update success with valid input
- Email format validation
- Email uniqueness validation (duplicate rejected)
- Partial update (email only, name unchanged)

**Integration Tests:**
- PUT /api/users/1 with valid email returns 200
- PUT /api/users/1 with invalid email returns 400
- PUT /api/users/1 with duplicate email returns 409
- Partial update verification

### US-003 Testing

**Unit Tests:**
- Other user update blocked (403)
- Role update by regular user blocked (403)
- Active update by regular user blocked (403)
- Self-update of allowed fields permitted

**Integration Tests:**
- Regular user cannot access other user endpoint
- Regular user gets 403 Forbidden
- Error response includes clear message

### US-004 Testing

**Unit Tests:**
- Admin can update any user (200)
- Email uniqueness still enforced (409)
- 404 returned for non-existent user
- Partial updates by admin

**Integration Tests:**
- Admin PUT to any user endpoint succeeds
- Non-existent user returns 404
- Duplicate email returns 409

### US-005 Testing

**Unit Tests:**
- Admin can change role to ROLE_ADMIN
- Admin can change role to ROLE_USER
- Invalid role rejected (400)
- Regular user cannot change role (403)

**Integration Tests:**
- Admin role change returns 200
- Invalid role returns 400 with error details
- Regular user role change attempt returns 403

### US-006 Testing

**Unit Tests:**
- Admin can set active=true
- Admin can set active=false
- Regular user cannot change active (403)

**Integration Tests:**
- Admin active status change returns 200
- Response includes updated active value
- Regular user active change attempt returns 403

---

## Story Priority & Risk

### Priority Assessment

All 6 stories are **Must Have** priority:
- Represent core profile update functionality
- Blocking feature for production release
- Required by business requirements

### Risk Assessment

| Story | Risk Level | Mitigation |
|-------|-----------|-----------|
| US-001 | Low | Simple name field update |
| US-002 | Medium | Email uniqueness complexity |
| US-003 | Medium | Authorization logic validation |
| US-004 | Low | Extends Phase 1 work |
| US-005 | Low | Adds field to existing logic |
| US-006 | Low | Simple boolean field update |

### Success Criteria

- All user stories implemented
- All acceptance criteria verified
- All tests passing
- Authorization rules enforced
- Error handling correct
- Performance targets met
- Production ready

---

## Summary

**Profile Update Feature Story Map:**

- **Total Stories:** 6 (all assigned to single unit)
- **Phases:** 2 (Regular User → Admin)
- **Team:** 1-2 engineers
- **Duration:** 1-2 sprints (~6-8 days)
- **Story Points:** ~10 points

**Phase 1 (Sprint 1):** Regular user self-update features (US-001, US-002, US-003)  
**Phase 2 (Sprint 2):** Admin capabilities (US-004, US-005, US-006)

Ready for CONSTRUCTION phase per-unit design and implementation.
