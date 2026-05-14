# Integration Test Execution Instructions

## Overview

This document provides instructions for executing integration tests for the Profile Update Service feature. Integration tests validate the complete REST API endpoint including request/response handling, authentication, authorization, and error handling through the full Spring context.

**Test Framework**: Spring Boot Test with MockMvc  
**Mock Database**: In-Memory H2  
**Test Location**: `src/test/java/com/sandbox/userapi/controller/`  
**Total Integration Tests**: 15 tests  
**Target Coverage**: >85% of UserController.updateUser()

---

## Integration Test Scenarios

### Success Scenarios (5 tests)
- Regular user updates own name → 200 OK
- Regular user updates own email → 200 OK
- Admin updates any user profile → 200 OK
- Admin updates user role → 200 OK
- Admin updates user active status → 200 OK

### Error Scenarios (5 tests)
- Duplicate email conflict → 409 Conflict
- Regular user updates other user → 403 Forbidden
- Regular user changes role → 403 Forbidden
- User not found → 404 Not Found
- Invalid request data → 400 Bad Request
- Unauthenticated request → 401 Unauthorized

### Response Format Scenarios (5 tests)
- Response includes all required fields
- Partial update returns complete profile
- HTTP status codes correct
- JSON content type correct
- Error response format valid

---

## Prerequisites for Integration Tests

### Environment Setup

```bash
# Ensure project is built
mvn clean compile

# Verify H2 database dependency (in-memory, no setup needed)
mvn dependency:tree | grep h2

# Expected: com.h2database:h2:jar:2.1.x (scope: test)
```

### Test Data Setup

Integration tests use `@Transactional` to isolate each test:
```java
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class UserControllerUpdateUserTest {
    @BeforeEach
    void setUp() {
        // Create fresh test data for each test
        regularUser = userRepository.save(new User(...));
        adminUser = userRepository.save(new User(...));
    }
}
```

---

## Step 1: Run All Integration Tests

```bash
# Navigate to project directory
cd /home/sk/vscode/aws-sagents-dlc/kiro-sandbox/services/java-api

# Run only integration tests (Controller tests)
mvn test -Dtest=UserControllerUpdateUserTest

# Or run all tests including integration
mvn test
```

### Expected Output

```
[INFO] --- surefire:3.0.0:test (default-test)
[INFO] Running com.sandbox.userapi.controller.UserControllerUpdateUserTest
[INFO]  Tests run: 15, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 5.234 s
[INFO]
[INFO] BUILD SUCCESS
```

---

## Step 2: Monitor Integration Test Execution

### Success Scenario Test

**Test**: `testUpdateUser_ValidRequest_Returns200OK`

```bash
# Run with verbose output
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_ValidRequest_Returns200OK -X

# Expected Flow:
# 1. MockMvc creates PUT request to /api/users/1
# 2. Spring Security context created with @WithMockUser
# 3. UpdateUserRequest deserialized and validated
# 4. UserService.updateUser() called
# 5. UserController returns ResponseEntity<UserResponse>
# 6. MockMvc asserts status().isOk()
# 7. MockMvc asserts response JSON fields
```

### Authorization Test

**Test**: `testUpdateUser_UnauthorizedUser_Returns403Forbidden`

```bash
# Run authorization test
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_UnauthorizedUser_Returns403Forbidden -X

# Expected Flow:
# 1. Regular user (userId=1) attempts to update other user (userId=2)
# 2. Spring Security context: userId=1, role=ROLE_USER
# 3. UserService checks authorization
# 4. ForbiddenException thrown
# 5. GlobalExceptionHandler catches exception
# 6. MockMvc asserts status().isForbidden()
# 7. MockMvc asserts error response contains "do not have permission"
```

### Email Conflict Test

**Test**: `testUpdateUser_DuplicateEmail_Returns409Conflict`

```bash
# Run email conflict test
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_DuplicateEmail_Returns409Conflict -X

# Expected Flow:
# 1. Regular user attempts to update email to one that exists
# 2. UpdateUserRequest validated (email format OK)
# 3. UserService checks email uniqueness
# 4. Repository query returns: email already exists
# 5. BadRequestException("...", "409") thrown
# 6. GlobalExceptionHandler returns 409 CONFLICT
# 7. MockMvc asserts status().isConflict()
```

---

## Step 3: Run Specific Test Scenarios

### Run Success Scenarios Only

```bash
# Test successful profile updates
mvn test -Dtest=UserControllerUpdateUserTest -k "Returns200OK"

# Or run specific test
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_AdminUpdateOtherUser_Returns200OK
```

### Run Error Scenarios Only

```bash
# Test error conditions
mvn test -Dtest=UserControllerUpdateUserTest -k "Returns.*Forbidden|Conflict|NotFound|BadRequest"

# Or run each error test individually
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_DuplicateEmail_Returns409Conflict
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_UnauthorizedUser_Returns403Forbidden
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_UserNotFound_Returns404NotFound
```

### Run Authorization Scenarios

```bash
# Test authorization enforcement
mvn test -Dtest=UserControllerUpdateUserTest -k "Forbidden|Admin"
```

---

## Step 4: Analyze Test Results

### HTTP Status Code Verification

```bash
# Extract status code assertions from test results
cat target/surefire-reports/com.sandbox.userapi.controller.UserControllerUpdateUserTest.txt

# Expected Output:
# ✅ 200 OK: Successful updates
# ✅ 400 Bad Request: Invalid data
# ✅ 403 Forbidden: Authorization failures
# ✅ 404 Not Found: User not found
# ✅ 409 Conflict: Email duplicates
```

### Response Content Verification

Each integration test verifies:
- HTTP status code
- JSON content type
- Response body contains all required fields
- Error messages are descriptive but don't expose sensitive data

```
✅ status().isOk()
✅ jsonPath("$.id").exists()
✅ jsonPath("$.name").exists()
✅ jsonPath("$.email").exists()
✅ jsonPath("$.role").exists()
✅ jsonPath("$.active").exists()
```

---

## Step 5: Test Request/Response Validation

### Valid Request Example

```bash
# Trace a successful request through the full stack
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_ValidRequest_Returns200OK -X

# Test validates:
# 1. Request parsing: JSON to UpdateUserRequest DTO
# 2. Request validation: @Valid annotation checks
# 3. Authentication: Spring Security context
# 4. Response serialization: User to UserResponse
# 5. JSON output: Correct field names and types
```

### Invalid Request Handling

```bash
# Test invalid email format validation
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_InvalidData_Returns400BadRequest

# Test validates:
# 1. Request deserializes
# 2. @Email validation catches invalid format
# 3. MethodArgumentNotValidException thrown
# 4. GlobalExceptionHandler returns 400
# 5. Error response includes validation details
```

---

## Handling Integration Test Failures

### Test Failure: Status Code Mismatch

**Error**: `Expected 403 Forbidden but got 200 OK`

**Cause**: Authorization check not enforced in UserService or GlobalExceptionHandler

**Fix**:
```bash
# Debug authorization flow
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_UnauthorizedUser_Returns403Forbidden -X

# Check:
# 1. Spring Security context created correctly (@WithMockUser)
# 2. UserService.validateUpdateAuthorization() logic
# 3. ForbiddenException thrown and caught
# 4. GlobalExceptionHandler handles ForbiddenException
```

### Test Failure: Response Format Incorrect

**Error**: `Expected jsonPath $.name to exist but was null`

**Cause**: UserResponse DTO missing fields or mapping incorrect

**Fix**:
```bash
# Verify UserResponse DTO has all fields
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_ResponseIncludesAllFields

# Check UserResponse record:
# - Has all 5 fields (id, name, email, role, active)
# - Correct Java type for each field
# - from() mapper method correctly creates response
```

### Test Failure: Email Conflict Not Caught

**Error**: `Expected 409 Conflict but got 200 OK`

**Cause**: Email uniqueness validation not working in UserService

**Fix**:
```bash
# Run email conflict test with verbose output
mvn test -Dtest=UserControllerUpdateUserTest#testUpdateUser_DuplicateEmail_Returns409Conflict -X

# Verify:
# 1. UserRepository.existsByEmailAndIdNot() returns true
# 2. BadRequestException thrown with statusCode="409"
# 3. GlobalExceptionHandler checks statusCode and returns 409
```

---

## Test Coverage for Each Story

### US-001: Update Own Profile Name
```
✅ testUpdateUser_ValidRequest_Returns200OK
✅ testUpdateUser_PartialUpdateReturnsCompleteProfile (name only)
```

### US-002: Update Own Profile Email
```
✅ testUpdateUser_UpdateEmailOnly_Returns200OK
✅ testUpdateUser_DuplicateEmail_Returns409Conflict
✅ testUpdateUser_InvalidData_Returns400BadRequest
```

### US-003: Prevent Unauthorized Updates
```
✅ testUpdateUser_UnauthorizedUser_Returns403Forbidden
✅ testUpdateUser_RegularUserChangeRole_Returns403Forbidden
```

### US-004: Admin Update Any User Profile
```
✅ testUpdateUser_AdminUpdateOtherUser_Returns200OK
✅ testUpdateUser_AdminUpdateRole_Returns200OK
```

### US-005: Admin Manage User Roles
```
✅ testUpdateUser_AdminUpdateRole_Returns200OK (included above)
```

### US-006: Admin Manage User Active Status
```
✅ testUpdateUser_AdminUpdateActiveStatus_Returns200OK
```

---

## Performance Baseline

Integration tests performance expectations:
```
Total Tests: 15
Total Time: 5-7 seconds (including Spring context startup)
Per Test: 300-500ms average
Database Operations: 2-3 per test (find, save, query)
```

### Monitor Test Performance

```bash
# Run with timing output
mvn test -Dtest=UserControllerUpdateUserTest -Dsurefire.reportFormat=plain

# Check timing in test output
# com.sandbox.userapi.controller.UserControllerUpdateUserTest:
#   - testUpdateUser_ValidRequest_Returns200OK: 0.421 s
#   - testUpdateUser_DuplicateEmail_Returns409Conflict: 0.312 s
#   - ... (all tests)
# Total: 5.234 s
```

---

## Test Isolation and Transactions

### Transaction Management

Each test runs in a transaction that's rolled back after completion:
```java
@SpringBootTest
@Transactional  // Rollback after each test
class UserControllerUpdateUserTest {
    @Test
    void testUpdateUser_ValidRequest() {
        // Test data created in setUp()
        // Any DB changes are isolated
        // Transaction rolled back after test
    }
}
```

### Test Data Isolation

```bash
# Verify test data isolation
mvn test -Dtest=UserControllerUpdateUserTest -Dsurefire.reportFormat=plain

# Each test should:
# 1. Create fresh test users in setUp()
# 2. Run in isolated transaction
# 3. Clean up via transaction rollback
# 4. Not affect other tests
```

---

## Continuous Integration (CI) Setup

### CI Pipeline Integration

```yaml
# Example CI configuration (GitHub Actions, GitLab CI, etc.)
test:
  script:
    - mvn clean compile test
  coverage: '/Coverage: \d+\.\d+%/'
  artifacts:
    reports:
      junit: target/surefire-reports/*.xml
```

### Pre-deployment Testing

```bash
# Full build and test before deployment
mvn clean install -Pintegration

# This runs:
# 1. Unit tests (UserService)
# 2. Integration tests (UserController)
# 3. Code coverage analysis
# 4. Report generation
```

---

## Test Success Criteria

### All Integration Tests Pass
```
✅ 15 tests run
✅ 0 failures
✅ 0 errors
✅ >85% coverage of UserController
✅ All HTTP status codes correct (200, 400, 403, 404, 409)
✅ All error scenarios handled
✅ BUILD SUCCESS
```

### Next Steps After Success
1. ✅ Integration tests pass
2. ✅ Proceed to Build and Test Summary
3. ✅ Then Performance Tests (if required)
4. ✅ Ready for Operations phase

---

## Test Documentation

### Test File Locations
- **Integration Tests**: `src/test/java/com/sandbox/userapi/controller/UserControllerUpdateUserTest.java`
- **Test Reports**: `target/surefire-reports/`
- **HTML Report**: `target/site/surefire-report.html`

### Story Coverage Mapping
Each test is labeled with story coverage:
```java
@DisplayName("US-002: Email uniqueness validation - 409 Conflict")
void testUpdateUser_DuplicateEmail_Returns409Conflict() { ... }
```

---

## Debugging Tips

### Enable Request/Response Logging

```bash
# Add logging to see full request/response
mvn test -Dtest=UserControllerUpdateUserTest \
  -Dspring.jpa.show-sql=true \
  -Dlogging.level.org.springframework.web=DEBUG
```

### Use IDE Debugger

```java
// Set breakpoint in UserController.updateUser()
// Run test in IDE debugger
// Step through request handling
// Inspect Spring Security context, DTOs, responses
```

### Print Test Details

```java
// Add logging to test
@Test
void testUpdateUser_ValidRequest_Returns200OK() {
    // ...
    log.debug("Request: {}", request);
    log.debug("Response: {}", response);
    // ...
}
```

---

## Summary

**Test Framework**: Spring Boot Test with MockMvc  
**Total Tests**: 15 integration tests  
**Coverage Target**: >85%  
**Execution Time**: 5-7 seconds (includes Spring context startup)  
**Success Criteria**: All 15 tests pass with correct HTTP status codes  
**Next Step**: Build and Test Summary review
