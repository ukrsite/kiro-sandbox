# Unit Test Execution Instructions

## Overview

This document provides instructions for executing unit tests for the Profile Update Service feature (US-001 through US-006). Unit tests validate service layer business logic, authorization, validation, and error handling.

**Test Framework**: JUnit 5  
**Mocking Library**: Mockito  
**Test Location**: `src/test/java/com/sandbox/userapi/`  
**Total Unit Tests**: 18 tests  
**Target Coverage**: >90% of UserService.updateUser()

---

## Story Coverage

| Story | Tests | Purpose |
|-------|-------|---------|
| US-001 | Regular user self-update name | Authorization + validation |
| US-002 | Regular user self-update email | Email uniqueness validation |
| US-003 | Prevent unauthorized updates | Authorization enforcement |
| US-004 | Admin update any user | Admin override capability |
| US-005 | Admin manage user roles | Role validation + restrictions |
| US-006 | Admin manage active status | Admin-only field updates |

---

## Unit Test Execution

### Step 1: Run All Unit Tests

```bash
# Navigate to project directory
cd /home/sk/vscode/aws-sagents-dlc/kiro-sandbox/services/java-api

# Execute all unit tests
mvn test

# Or specifically run unit tests only (skip integration tests)
mvn test -Dtest=*Test -DexcludedGroups=integration
```

### Step 2: Monitor Test Execution

**Expected Output**:
```
[INFO] --- surefire:3.0.0:test (default-test)
[INFO] Running com.sandbox.userapi.service.UserServiceUpdateUserTest
[INFO] Tests run: 18, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 2.123 s
[INFO]
[INFO] BUILD SUCCESS
```

### Step 3: Review Test Results

Tests are categorized into three groups:

#### Authorization Tests (6 tests)
```
✅ testUpdateUser_SelfUpdateNameAsRegularUser_Success
✅ testUpdateUser_SelfUpdateEmailAsRegularUser_Success
✅ testUpdateUser_RegularUserCannotUpdateOtherUser_Throws403
✅ testUpdateUser_RegularUserCannotChangeRole_Throws403
✅ testUpdateUser_RegularUserCannotChangeActive_Throws403
✅ testUpdateUser_AdminCanChangeRole_Success
✅ testUpdateUser_AdminCanChangeActiveStatus_Success
```

#### Validation Tests (4 tests)
```
✅ testUpdateUser_EmailValidation_DuplicateEmail_Throws409
✅ testUpdateUser_RoleValidation_InvalidRole_Throws400
✅ testUpdateUser_UserNotFound_Throws404
✅ testUpdateUser_PartialUpdate_OnlyNameProvided_Success
```

#### Edge Cases & Partial Updates (8 tests)
```
✅ testUpdateUser_PartialUpdate_OnlyEmailProvided_Success
✅ testUpdateUser_AdminPartialUpdate_OnlyEmailProvided_Success
✅ testUpdateUser_UpdateMultipleFields_Success
✅ ... (additional edge case tests)
```

---

## Individual Test Execution

### Run Specific Test Class

```bash
# Run only UserService tests
mvn test -Dtest=UserServiceUpdateUserTest

# Run only Controller tests (integration)
mvn test -Dtest=UserControllerUpdateUserTest
```

### Run Specific Test Method

```bash
# Run single test method
mvn test -Dtest=UserServiceUpdateUserTest#testUpdateUser_SelfUpdateNameAsRegularUser_Success

# Run multiple test methods with pattern
mvn test -Dtest=UserServiceUpdateUserTest#testUpdateUser*Authorization*
```

---

## Test Results Analysis

### Check Test Report

```bash
# View test results summary
cat target/surefire-reports/com.sandbox.userapi.service.UserServiceUpdateUserTest.txt

# Expected Output:
# -------------------------------------------------------
# Test set: com.sandbox.userapi.service.UserServiceUpdateUserTest
# -------------------------------------------------------
# Tests run: 18, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 2.123 s
```

### Generate HTML Test Report

```bash
# Generate HTML report
mvn surefire-report:report

# Open report in browser
open target/site/surefire-report.html
```

---

## Test Coverage Analysis

### Generate Code Coverage Report

```bash
# Add JaCoCo coverage plugin (if not already configured)
mvn clean test jacoco:report

# View coverage report
open target/site/jacoco/index.html
```

### Expected Coverage
- **UserService**: >90% coverage
- **UpdateUserRequest**: >95% coverage
- **Overall**: >85% coverage

### Coverage Breakdown by Component
```
com.sandbox.userapi.service.UserService: 92.3%
├── updateUser(): 95%
├── validateUpdateAuthorization(): 100%
├── validateEmailUniqueness(): 88%
├── validateRoleValue(): 85%
├── applyUpdates(): 100%
├── extractUserId(): 80%
└── isAdmin(): 90%
```

---

## Handling Test Failures

### Test Failure: Authorization Denied

**Error**: `testUpdateUser_RegularUserCannotUpdateOtherUser_Throws403`  
**Message**: `Expected ForbiddenException but was not thrown`

**Diagnosis**:
1. Check authorization logic in UserService.validateUpdateAuthorization()
2. Verify authentication setup in test
3. Check mock configuration

**Fix**:
```bash
# Run with verbose output
mvn test -Dtest=UserServiceUpdateUserTest#testUpdateUser_RegularUserCannotUpdateOtherUser_Throws403 -X

# Review test failure stacktrace
# Identify missing authorization check
# Fix UserService.validateUpdateAuthorization() logic
```

### Test Failure: Email Validation

**Error**: `testUpdateUser_EmailValidation_DuplicateEmail_Throws409`  
**Message**: `Expected BadRequestException with statusCode=409`

**Diagnosis**:
1. Check email uniqueness query in UserRepository mock
2. Verify BadRequestException is thrown with correct status code
3. Check repository mock setup

**Fix**:
```bash
# Run specific test with debugging
mvn test -Dtest=UserServiceUpdateUserTest#testUpdateUser_EmailValidation_DuplicateEmail_Throws409 -e

# Check repository mock configuration
# Ensure existsByEmailAndIdNot() returns true for duplicate emails
# Verify BadRequestException("...", "409") is thrown
```

### Test Failure: User Not Found

**Error**: `testUpdateUser_UserNotFound_Throws404`  
**Message**: `Expected ResourceNotFoundException`

**Diagnosis**:
1. Check user lookup logic in UserService.updateUser()
2. Verify repository.findById() returns Optional.empty()
3. Check exception throwing

**Fix**:
```bash
# Review test setup
# Ensure mock returns Optional.empty() for missing user
# Verify ResourceNotFoundException is thrown with proper message
# Check service logic for user existence validation
```

---

## Retry Failing Tests

### Rerun Failed Tests

```bash
# Rerun only tests that failed
mvn test -Dtest=UserServiceUpdateUserTest -rf :userapi

# Force rerun all tests (skip cache)
mvn clean test
```

### Debug Failing Test

```bash
# Run with debug output and breakpoints
mvn test -Dtest=UserServiceUpdateUserTest -Ddebug

# Or configure IDE debugger and run test in IDE
# Set breakpoints in UserService and test classes
# Execute test in debug mode to step through code
```

---

## Test Scenarios Coverage

### Authorization Scenarios
- [x] Regular user can update own name
- [x] Regular user can update own email
- [x] Regular user cannot update other user's profile → 403
- [x] Regular user cannot change role → 403
- [x] Regular user cannot change active status → 403
- [x] Admin can update any user's profile
- [x] Admin can change role
- [x] Admin can change active status

### Validation Scenarios
- [x] Email uniqueness validation (duplicate email → 409)
- [x] Invalid role value → 400
- [x] User not found → 404
- [x] Partial update (name only)
- [x] Partial update (email only)
- [x] Multiple field updates

### Partial Update Scenarios
- [x] Update only name field
- [x] Update only email field
- [x] Update name and email together
- [x] Admin partial update (name only)
- [x] Admin full update (all fields)

---

## Test Best Practices

### 1. Verify Mock Configuration
Before running tests, ensure mocks are properly configured:
```java
// Verify repository mock behavior
when(userRepository.findById(userId)).thenReturn(Optional.of(user));
when(userRepository.existsByEmailAndIdNot(email, userId)).thenReturn(false);
when(userRepository.save(any(User.class))).thenReturn(user);

// Verify authentication mock behavior
setupAuthenticationForUser(userId, "ROLE_USER");
```

### 2. Isolate Test Dependencies
Each test should be independent:
```java
@BeforeEach
void setUp() {
    // Fresh mocks for each test
    MockitoAnnotations.openMocks(this);
    userService = new UserService(userRepository);
}
```

### 3. Use Meaningful Assertions
```java
// Good: Clear assertion with message
assertEquals("Updated Name", updatedUser.getName(), "User name should be updated");

// Better: AssertJ fluent assertions
assertThat(response).isNotNull().hasFieldOrPropertyWithValue("name", "Updated Name");
```

### 4. Test Both Success and Failure Paths
```java
// Success path
void testUpdateUser_SelfUpdateName_Success()

// Failure paths
void testUpdateUser_UnauthorizedAccess_Throws403()
void testUpdateUser_ValidationFails_Throws400()
void testUpdateUser_UserNotFound_Throws404()
```

---

## Continuous Test Execution

### Watch Mode (Re-run on File Changes)

```bash
# Install Maven Watch plugin
mvn install -f pom.xml

# Run tests in watch mode
mvn watch -Dwatch.pattern=src/

# Or use external tool like fswatch
fswatch -o src/ | xargs -n1 -I {} mvn test
```

### Pre-commit Hook

```bash
# Add pre-commit hook to run tests before commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
mvn test
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

---

## Test Performance Optimization

### Run Tests in Parallel

```bash
# Run tests in parallel for faster execution
mvn test -DthreadCount=4 -Dpercentage=100

# Run with specific thread count
mvn test -DthreadCount=8
```

### Skip Slow Tests During Development

```bash
# Skip integration tests (marked with @Tag("integration"))
mvn test -Dgroups="!integration"

# Or mark tests with categories
mvn test -Dgroups="unit"
```

---

## Test Success Criteria

### All Tests Pass
```
✅ 18 tests run
✅ 0 failures
✅ 0 errors
✅ >90% coverage of UserService
✅ BUILD SUCCESS
```

### Next Steps After Success
1. ✅ Unit tests pass
2. ✅ Proceed to Integration Tests (see integration-test-instructions.md)
3. ✅ Then Performance Tests
4. ✅ Then Build and Test Summary

---

## Test Documentation

### Test File Locations
- **Service Tests**: `src/test/java/com/sandbox/userapi/service/UserServiceUpdateUserTest.java`
- **Controller Tests**: `src/test/java/com/sandbox/userapi/controller/UserControllerUpdateUserTest.java` (integration)
- **Test Reports**: `target/surefire-reports/`

### Story Coverage Mapping
Each test is documented with story coverage in Javadoc:
```java
@DisplayName("US-001: Regular user can update own name successfully")
void testUpdateUser_SelfUpdateNameAsRegularUser_Success() {
    // Test implementation
}
```

---

## Summary

**Test Framework**: JUnit 5 with Mockito  
**Total Tests**: 18 unit tests  
**Coverage Target**: >90%  
**Execution Time**: ~2-3 seconds  
**Success Criteria**: All 18 tests pass  
**Next Step**: Integration test execution
