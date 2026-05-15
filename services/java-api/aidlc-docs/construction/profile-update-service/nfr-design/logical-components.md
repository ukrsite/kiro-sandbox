# Logical Components - Profile Update Service

## Overview

This document defines the logical infrastructure components and architectural elements that support the Non-Functional Requirements for the Profile Update Service. Each component is designed for specific NFR concerns and integrates with existing Spring Boot infrastructure.

---

## 1. Presentation Layer Components

### Component 1.1: HTTP Request Interceptor (Spring Security Filter Chain)

**Purpose:** Intercept incoming HTTP requests and extract authentication

**Responsibility:**
- Extract HTTP Basic Auth credentials from Authorization header
- Validate credentials against UserDetailsService
- Populate Spring Security context (SecurityContextHolder)
- Pass authenticated context to controller

**Design:**

```
HTTP Request
    ↓
Spring Security Filter Chain
    ├─ BasicAuthenticationFilter intercepts
    ├─ Extracts "Authorization: Basic base64(user:pass)"
    ├─ Decodes credentials
    ├─ UserDetailsService.loadUserByUsername(username)
    ├─ Validates password
    ├─ Creates Authentication object with authorities
    ├─ Sets SecurityContextHolder.getContext().setAuthentication(auth)
    └─ Continues to controller
    ↓
Controller receives with populated SecurityContext
```

**Integration:**

```java
// Existing configuration leveraged
@Configuration
@EnableWebSecurity
public class SecurityConfig {
  // Spring Security auto-configures HTTP Basic auth
  // BasicAuthenticationEntryPoint returns 401 if unauthenticated
}
```

**Monitoring:**
- Log authentication attempts (success and failure)
- Alert on repeated authentication failures (potential attack)

---

### Component 1.2: DTO Validation Filter (Spring Validation)

**Purpose:** Validate incoming request DTOs before service layer

**Responsibility:**
- Deserialize JSON to UpdateUserRequest DTO
- Apply Jakarta Bean Validation annotations
- Return 400 Bad Request if validation fails

**Design:**

```
HTTP Request body JSON
    ↓
Spring MVC deserializer converts to UpdateUserRequest
    ↓
@Validated triggered on method parameter
    ├─ @NotEmpty on name (if provided)
    ├─ @Size(max=100) on name
    ├─ @Email on email
    ├─ @ValidRole on role (custom validator)
    └─ @Valid triggers nested validation
    ↓
Validation success:
    └─ Proceed to service layer
    
Validation failure:
    ├─ MethodArgumentNotValidException thrown
    ├─ GlobalExceptionHandler catches
    ├─ Creates ErrorResponse with field details
    └─ Return 400 Bad Request with details
```

**Implementation:**

```java
@RestController
@RequestMapping("/api/users")
public class UserController {
  
  @PutMapping("/{userId}")
  public ResponseEntity<UserResponse> updateUser(
      @PathVariable Long userId,
      @Valid @RequestBody UpdateUserRequest request,  // Triggers validation
      HttpServletRequest httpRequest) {
    // At this point, request is guaranteed valid
    // ...
  }
}
```

**DTO Validation Annotations:**

```java
public class UpdateUserRequest {
  
  @NotEmpty(message = "Name cannot be empty")
  @Size(max = 100, message = "Name cannot exceed 100 characters")
  private String name;
  
  @Email(message = "Invalid email format")
  private String email;
  
  @ValidRole(message = "Role must be ROLE_USER or ROLE_ADMIN")
  private String role;
  
  private Boolean active;
}
```

---

### Component 1.3: Security Context Extractor

**Purpose:** Extract authenticated user information for authorization checks

**Responsibility:**
- Get authenticated user ID from principal
- Get authenticated user roles from authorities
- Pass to service layer for authorization decisions

**Design:**

```java
@Component
public class SecurityContextExtractor {
  
  public Long getAuthenticatedUserId() {
    Authentication auth = SecurityContextHolder.getContext().getAuthentication();
    if (auth == null || !auth.isAuthenticated()) {
      throw new IllegalStateException("No authentication in context");
    }
    return (Long) auth.getPrincipal();  // User ID from UserDetails
  }
  
  public boolean isAdmin() {
    Authentication auth = SecurityContextHolder.getContext().getAuthentication();
    return auth.getAuthorities().stream()
      .anyMatch(ga -> ga.getAuthority().equals("ROLE_ADMIN"));
  }
  
  public Collection<String> getUserRoles() {
    Authentication auth = SecurityContextHolder.getContext().getAuthentication();
    return auth.getAuthorities().stream()
      .map(GrantedAuthority::getAuthority)
      .collect(Collectors.toList());
  }
}
```

**Usage in Controller:**

```java
@PutMapping("/{userId}")
public ResponseEntity<UserResponse> updateUser(
    @PathVariable Long userId,
    @Valid @RequestBody UpdateUserRequest request) {
  
  Authentication auth = SecurityContextHolder.getContext().getAuthentication();
  UserResponse response = userService.updateUser(userId, request, auth);
  
  return ResponseEntity.ok(response);
}
```

---

## 2. Service Layer Components

### Component 2.1: Authorization Service

**Purpose:** Enforce role-based and field-level authorization

**Responsibility:**
- Check if user is authenticated
- Check if user is admin
- Check if performing self-update only (for non-admin)
- Check if attempting restricted field updates (for non-admin)
- Throw ForbiddenException if unauthorized

**Design:**

```java
@Component
public class AuthorizationService {
  
  public void checkUpdateAuthorization(Long targetUserId, 
                                       UpdateUserRequest request,
                                       Authentication auth) {
    // Step 1: Extract authenticated info
    Long authenticatedUserId = (Long) auth.getPrincipal();
    boolean isAdmin = auth.getAuthorities().stream()
      .anyMatch(ga -> ga.getAuthority().equals("ROLE_ADMIN"));
    
    // Step 2: Check admin status or self-update
    if (!isAdmin && !targetUserId.equals(authenticatedUserId)) {
      throw new ForbiddenException("Cannot update other users' profiles");
    }
    
    // Step 3: Field-level restrictions for non-admin
    if (!isAdmin) {
      if (request.getRole() != null) {
        throw new ForbiddenException("Non-admin cannot change role");
      }
      if (request.getActive() != null) {
        throw new ForbiddenException("Non-admin cannot change active status");
      }
    }
  }
}
```

**Authorization Matrix Implementation:**

```
User Type | Can Update Self | Can Update Others | Can Change Role | Can Change Active
----------|---|---|---|---
ROLE_USER | ✅ name, email | ❌ | ❌ | ❌
ROLE_ADMIN | ✅ all | ✅ all | ✅ | ✅
```

---

### Component 2.2: Email Validation Service

**Purpose:** Validate email uniqueness and format

**Responsibility:**
- Check if email format is valid (RFC 5322)
- Check if email is unique (no other user has it)
- Handle optional email updates (skip validation if not provided)

**Design:**

```java
@Component
public class EmailValidationService {
  
  private final UserRepository userRepository;
  
  public void validateEmail(String newEmail, Long userId) {
    // Skip if not provided (partial update)
    if (newEmail == null) {
      return;
    }
    
    // Check uniqueness (excluding current user)
    if (userRepository.existsByEmailAndIdNot(newEmail, userId)) {
      throw new EmailAlreadyExistsException(newEmail);
    }
  }
}
```

**Performance Optimization:**

- **Pre-check Pattern:** Query database BEFORE attempting update
- **Indexed Query:** `existsByEmailAndIdNot` uses unique email index
- **O(1) Performance:** Index lookup guaranteed fast
- **Prevents DB Constraints:** Catch conflict before hitting database constraint

**Query Implementation:**

```java
public interface UserRepository extends JpaRepository<User, Long> {
  
  // Returns true if email exists for user ID other than provided
  // Translates to: SELECT COUNT(*) FROM User WHERE email = ? AND id != ?
  // Uses index on email column for O(1) performance
  boolean existsByEmailAndIdNot(String email, Long userId);
}
```

---

### Component 2.3: Transactional Update Orchestrator

**Purpose:** Coordinate all update operations in single transaction

**Responsibility:**
- Load user entity
- Validate authorization
- Validate business rules
- Apply field updates
- Persist changes
- Rollback on any error

**Design:**

```java
@Service
public class UserService {
  
  private final UserRepository userRepository;
  private final AuthorizationService authService;
  private final EmailValidationService emailService;
  
  @Transactional  // Single transaction encompasses entire operation
  public UserResponse updateUser(Long userId, 
                                 UpdateUserRequest request,
                                 Authentication auth) {
    
    // Step 1: Load user
    User user = userRepository.findById(userId)
      .orElseThrow(() -> new UserNotFoundException(userId));
    
    // Step 2: Check authorization
    authService.checkUpdateAuthorization(userId, request, auth);
    
    // Step 3: Validate business rules
    emailService.validateEmail(request.getEmail(), userId);
    
    // Step 4: Apply updates (conditional)
    if (request.getName() != null) {
      user.setName(request.getName());
    }
    if (request.getEmail() != null) {
      user.setEmail(request.getEmail());
    }
    
    // Only admin can update these
    boolean isAdmin = auth.getAuthorities().stream()
      .anyMatch(ga -> ga.getAuthority().equals("ROLE_ADMIN"));
    if (isAdmin) {
      if (request.getRole() != null) {
        user.setRole(request.getRole());
      }
      if (request.getActive() != null) {
        user.setActive(request.getActive());
      }
    }
    
    // Step 5: Persist (within transaction)
    User updated = userRepository.save(user);
    
    // Step 6: Convert to response DTO
    return UserResponse.from(updated);
  }
  // Transaction commits here (if no exception)
  // Transaction rolls back if ANY exception thrown above
}
```

**Transactional Semantics:**

```
Method Entry: BEGIN TRANSACTION
    ↓
All database operations execute within transaction context
    ├─ findById: SELECT within transaction
    ├─ existsByEmailAndIdNot: SELECT within transaction
    └─ save: UPDATE within transaction
    ↓
Method Exit (normal): COMMIT TRANSACTION
    └─ All changes persisted atomically
    
Method Exit (exception): ROLLBACK TRANSACTION
    └─ All changes discarded, database unchanged
```

---

### Component 2.4: DTO Mapper

**Purpose:** Convert between entity and DTO representations

**Responsibility:**
- Convert User entity to UserResponse DTO
- Handle null values safely
- Ensure all fields populated

**Design:**

```java
@Component
public class UserMapper {
  
  public UserResponse toResponse(User user) {
    if (user == null) {
      return null;
    }
    
    return UserResponse.builder()
      .id(user.getId())
      .name(user.getName())
      .email(user.getEmail())
      .role(user.getRole())
      .active(user.getActive())
      .build();
  }
  
  public User toEntity(UpdateUserRequest request, User existingUser) {
    // Partial update: only update provided fields
    if (request.getName() != null) {
      existingUser.setName(request.getName());
    }
    if (request.getEmail() != null) {
      existingUser.setEmail(request.getEmail());
    }
    if (request.getRole() != null) {
      existingUser.setRole(request.getRole());
    }
    if (request.getActive() != null) {
      existingUser.setActive(request.getActive());
    }
    return existingUser;
  }
}
```

---

## 3. Data Access Layer Components

### Component 3.1: Indexed Query Repository

**Purpose:** Provide efficient database access via Spring Data JPA

**Responsibility:**
- Load user by ID (primary key index)
- Check email uniqueness (unique index)
- Persist updates
- Manage database connections via HikariCP

**Design:**

```java
public interface UserRepository extends JpaRepository<User, Long> {
  
  // Inherited methods with automatic indexing:
  // - findById(Long id): Uses PK index, O(1)
  // - save(User user): INSERT or UPDATE
  
  // Custom methods for profile update:
  
  /**
   * Check if email exists for user ID other than specified.
   * Pre-checks before update to avoid duplicate constraint violations.
   * 
   * @param email Email to check
   * @param userId User ID to exclude from check
   * @return true if email exists for different user
   * 
   * Translates to SQL:
   *   SELECT COUNT(*) FROM user WHERE email = ? AND id != ?
   * Uses index on email column for O(1) performance
   */
  boolean existsByEmailAndIdNot(String email, Long userId);
  
  /**
   * Find user by email address.
   * Optional helper method for lookups (not used in main flow).
   */
  Optional<User> findByEmail(String email);
}
```

**Database Indexes (DDL):**

```sql
-- Primary key index (automatic)
CREATE UNIQUE INDEX idx_user_id ON user(id);

-- Email unique index (enforces uniqueness)
CREATE UNIQUE INDEX idx_user_email ON user(email);

-- Enables existsByEmailAndIdNot query to run in O(1) time
```

**Connection Pooling:**

```yaml
# Default HikariCP configuration
spring:
  datasource:
    hikari:
      maximum-pool-size: 10
      minimum-idle: 10
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
```

---

### Component 3.2: Database Transaction Manager

**Purpose:** Manage transactional boundaries for consistency

**Responsibility:**
- Begin transaction at service method entry
- Commit if method completes normally
- Rollback if exception thrown
- Manage isolation level (default: READ_COMMITTED)

**Design:**

```
Spring Transaction Management (Auto-configured)
    ↓
@Transactional annotation marks transaction boundary
    ├─ Aspect intercepts method call
    ├─ Gets database connection from pool
    ├─ Begins transaction
    ├─ Executes method
    ├─ If success: Commit transaction
    └─ If exception: Rollback transaction
    ↓
Isolation Level: READ_COMMITTED (default)
    ├─ Prevents dirty reads (don't read uncommitted data)
    ├─ Allows non-repeatable reads (acceptable for profile updates)
    └─ Sufficient for low-concurrency single-user updates
```

**Configuration:**

```java
@Configuration
@EnableTransactionManagement
public class TransactionConfig {
  // Spring auto-configures PlatformTransactionManager
  // No explicit configuration needed for H2/JPA/Hibernate stack
}

// Spring Boot auto-configures:
// - HibernateJpaVendorAdapter
// - JpaTransactionManager
// - Read COMMITTED isolation level
```

---

## 4. Infrastructure Components

### Component 4.1: Exception Translator

**Purpose:** Convert exceptions to appropriate HTTP responses

**Responsibility:**
- Catch application exceptions
- Map to correct HTTP status code
- Generate structured error response
- Log exception for debugging

**Design:**

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
  
  private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);
  
  @ExceptionHandler(UserNotFoundException.class)
  public ResponseEntity<ErrorResponse> handleUserNotFound(
      UserNotFoundException ex, HttpServletRequest request) {
    log.warn("User not found: {}", ex.getMessage());
    
    ErrorResponse error = ErrorResponse.builder()
      .timestamp(Instant.now())
      .status(HttpStatus.NOT_FOUND.value())
      .error("Not Found")
      .message(ex.getMessage())
      .path(request.getRequestURI())
      .build();
    
    return ResponseEntity
      .status(HttpStatus.NOT_FOUND)
      .body(error);
  }
  
  @ExceptionHandler(EmailAlreadyExistsException.class)
  public ResponseEntity<ErrorResponse> handleEmailConflict(
      EmailAlreadyExistsException ex, HttpServletRequest request) {
    log.warn("Email conflict: {}", ex.getMessage());
    
    ErrorResponse error = ErrorResponse.builder()
      .timestamp(Instant.now())
      .status(HttpStatus.CONFLICT.value())
      .error("Conflict")
      .message(ex.getMessage())
      .path(request.getRequestURI())
      .build();
    
    return ResponseEntity
      .status(HttpStatus.CONFLICT)
      .body(error);
  }
  
  @ExceptionHandler(ForbiddenException.class)
  public ResponseEntity<ErrorResponse> handleForbidden(
      ForbiddenException ex, HttpServletRequest request) {
    log.warn("Authorization denied: {}", ex.getMessage());
    
    ErrorResponse error = ErrorResponse.builder()
      .timestamp(Instant.now())
      .status(HttpStatus.FORBIDDEN.value())
      .error("Forbidden")
      .message(ex.getMessage())
      .path(request.getRequestURI())
      .build();
    
    return ResponseEntity
      .status(HttpStatus.FORBIDDEN)
      .body(error);
  }
  
  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<ErrorResponse> handleValidationException(
      MethodArgumentNotValidException ex, HttpServletRequest request) {
    log.debug("Validation error: {}", ex.getMessage());
    
    List<FieldError> errors = ex.getBindingResult().getFieldErrors();
    List<Map<String, String>> details = errors.stream()
      .map(err -> Map.of(
        "field", err.getField(),
        "message", err.getDefaultMessage(),
        "rejectedValue", String.valueOf(err.getRejectedValue())
      ))
      .collect(Collectors.toList());
    
    ErrorResponse error = ErrorResponse.builder()
      .timestamp(Instant.now())
      .status(HttpStatus.BAD_REQUEST.value())
      .error("Bad Request")
      .message("Validation failed")
      .path(request.getRequestURI())
      .details(details)
      .build();
    
    return ResponseEntity
      .status(HttpStatus.BAD_REQUEST)
      .body(error);
  }
}
```

**Exception Mapping:**

| Exception | HTTP Status | Reason |
|-----------|---|---|
| UserNotFoundException | 404 | Requested resource doesn't exist |
| EmailAlreadyExistsException | 409 | Conflict with existing data |
| ForbiddenException | 403 | User lacks permission |
| MethodArgumentNotValidException | 400 | Invalid request format/data |
| DataAccessException | 500 | Unexpected database error |

---

### Component 4.2: Metrics Collector (Spring Actuator)

**Purpose:** Collect system metrics for monitoring

**Responsibility:**
- Record HTTP request/response metrics
- Track response times and error rates
- Monitor database connection pool
- Expose metrics via HTTP endpoint

**Design:**

```
Spring Actuator auto-configures MeterRegistry
    ├─ Collects HTTP request metrics automatically
    ├─ Tracks response times (histogram)
    ├─ Counts requests by status code
    ├─ Monitors JVM metrics
    └─ Provides /actuator/metrics endpoint
    ↓
Available metrics:
    ├─ http.server.requests
    │  ├─ Total count
    │  ├─ Response time (p50, p95, p99)
    │  ├─ Max/Min/Mean times
    │  └─ Count by status (200, 400, 403, 404, 409, 500)
    ├─ db.connection.pool
    │  ├─ Active connections
    │  ├─ Idle connections
    │  └─ Pending requests
    └─ jvm.memory
       ├─ Heap memory usage
       ├─ Non-heap memory
       └─ Garbage collection stats
    ↓
Monitoring system scrapes /actuator/metrics
    ├─ Prometheus
    ├─ Datadog
    ├─ New Relic
    └─ Other APM tools
```

**Configuration:**

```yaml
# Enable Actuator endpoints
management:
  endpoints:
    web:
      exposure:
        include: health,metrics,info
  metrics:
    enable:
      jvm: true
      logback: true
      process: true
    distribution:
      percentiles-histogram:
        http.server.requests: true  # Enable histogram for response times
      percentiles:
        http.server.requests: 0.5,0.95,0.99  # p50, p95, p99
```

---

### Component 4.3: Structured Logger (SLF4J + Logback)

**Purpose:** Generate structured, aggregatable logs

**Responsibility:**
- Format logs as JSON for aggregation
- Include context fields (userId, email, result)
- Use appropriate log levels
- Write to stdout for container capture

**Design:**

```java
@Service
public class UserService {
  
  private static final Logger log = LoggerFactory.getLogger(UserService.class);
  
  public UserResponse updateUser(Long userId, 
                                 UpdateUserRequest request,
                                 Authentication auth) {
    
    log.info("Profile update request", userId, request.getFields());
    
    try {
      // Validation
      authService.checkUpdateAuthorization(userId, request, auth);
      log.debug("Authorization check passed", userId, isAdmin);
      
      emailService.validateEmail(request.getEmail(), userId);
      log.debug("Email validation passed", userId, request.getEmail());
      
      // Update
      User updated = loadAndUpdate(userId, request, auth);
      
      log.info("Profile update successful", userId, 
               request.getFields().size(), duration);
      
      return UserResponse.from(updated);
      
    } catch (ForbiddenException ex) {
      log.warn("Authorization failed", userId, ex.getMessage());
      throw ex;
    } catch (Exception ex) {
      log.error("Profile update failed", userId, ex);
      throw ex;
    }
  }
}
```

**Log Output (JSON):**

```json
{"timestamp":"2024-01-15T10:30:00Z","level":"INFO","logger":"UserService",
 "message":"Profile update request","userId":1,"fields":["name","email"]}

{"timestamp":"2024-01-15T10:30:00Z","level":"DEBUG","logger":"UserService",
 "message":"Authorization check passed","userId":1,"isAdmin":false}

{"timestamp":"2024-01-15T10:30:01Z","level":"DEBUG","logger":"UserService",
 "message":"Email validation passed","userId":1,"email":"new@example.com"}

{"timestamp":"2024-01-15T10:30:02Z","level":"INFO","logger":"UserService",
 "message":"Profile update successful","userId":1,"fieldsUpdated":2,"durationMs":45}
```

---

## 5. Logical Component Diagram

```
HTTP Request (JSON)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Presentation Layer                                          │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ Spring Security Filter Chain                         │  │
│ │ - HTTP Basic Auth extraction                         │  │
│ │ - Credential validation                              │  │
│ │ - SecurityContext population                         │  │
│ └──────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ DTO Validation Filter                                │  │
│ │ - JSON deserialization                               │  │
│ │ - Jakarta Bean Validation                            │  │
│ │ - 400 Bad Request on failure                         │  │
│ └──────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ UserController                                       │  │
│ │ - Extract security context                           │  │
│ │ - Call UserService                                   │  │
│ │ - Return UserResponse                                │  │
│ └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Service Layer (Transactional Boundary)                      │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ UserService.updateUser()                             │  │
│ │ @Transactional                                       │  │
│ │ ┌──────────────────────────────────────────────┐    │  │
│ │ │ 1. AuthorizationService                      │    │  │
│ │ │    - Check admin or self-update              │    │  │
│ │ │    - Check field restrictions                │    │  │
│ │ └──────────────────────────────────────────────┘    │  │
│ │ ┌──────────────────────────────────────────────┐    │  │
│ │ │ 2. EmailValidationService                    │    │  │
│ │ │    - Check email uniqueness                  │    │  │
│ │ │    - Query existsByEmailAndIdNot             │    │  │
│ │ └──────────────────────────────────────────────┘    │  │
│ │ ┌──────────────────────────────────────────────┐    │  │
│ │ │ 3. UserRepository.save()                     │    │  │
│ │ │    - Persist updated entity                  │    │  │
│ │ │    - Generate UPDATE statement               │    │  │
│ │ └──────────────────────────────────────────────┘    │  │
│ │ ┌──────────────────────────────────────────────┐    │  │
│ │ │ 4. DTOMapper                                 │    │  │
│ │ │    - Convert entity to UserResponse          │    │  │
│ │ └──────────────────────────────────────────────┘    │  │
│ └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Data Access Layer                                           │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ UserRepository (Spring Data JPA)                     │  │
│ │ - findById(userId) - PK index                        │  │
│ │ - existsByEmailAndIdNot(email, userId) - Email idx  │  │
│ │ - save(user) - INSERT/UPDATE                         │  │
│ │ - Connection pool (HikariCP, 10 connections)        │  │
│ │ - Transaction manager                               │  │
│ └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Database Layer                                              │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ User Table                                           │  │
│ │ - Columns: id, name, email, role, active            │  │
│ │ - Indexes: PK (id), UQ (email)                       │  │
│ │ - Constraints: NOT NULL, UNIQUE on email            │  │
│ └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Infrastructure Components                                   │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ Exception Translator (GlobalExceptionHandler)        │  │
│ │ - Maps exceptions to HTTP status codes               │  │
│ │ - Generates ErrorResponse DTO                        │  │
│ └──────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ Metrics Collector (Spring Actuator)                  │  │
│ │ - Records response times                             │  │
│ │ - Tracks error rates                                 │  │
│ │ - Exposes /actuator/metrics endpoint                 │  │
│ └──────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ Structured Logger (SLF4J + Logback)                  │  │
│ │ - JSON-formatted logs                                │  │
│ │ - Context fields (userId, result)                    │  │
│ │ - Stdout for container aggregation                   │  │
│ └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
    ↓
HTTP Response (JSON) + Metrics + Logs
```

---

## Summary: Logical Components

| Component | Purpose | Implements NFR |
|-----------|---------|---|
| Security Filter Chain | Extract authentication | Security/AUTH |
| DTO Validator | Validate request format | Security/INPUT |
| Controller | Handle HTTP | Performance/RESP |
| AuthorizationService | Check permissions | Security/RBAC |
| EmailValidator | Check email uniqueness | Reliability/DATA |
| Transactional Orchestrator | Atomic updates | Reliability/CONS |
| DTOMapper | Entity ↔ DTO conversion | Maintainability |
| Indexed Repository | Efficient queries | Performance/DB |
| Transaction Manager | Transaction boundaries | Reliability/TXNS |
| Exception Translator | Error responses | Reliability/ERROR |
| Metrics Collector | Monitor performance | Observability/METRICS |
| Structured Logger | Aggregatable logs | Observability/LOGS |

---

## Next Steps

These logical components will be implemented using Spring Boot patterns and integrated into the Code Generation phase for actual implementation.
