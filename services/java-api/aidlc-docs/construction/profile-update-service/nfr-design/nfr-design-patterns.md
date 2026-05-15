# NFR Design Patterns - Profile Update Service

## Overview

This document defines the design patterns and architectural approaches used to implement the Non-Functional Requirements for the Profile Update Service. Each pattern is mapped to specific NFR requirements and provides implementation guidance.

---

## 1. Performance Design Patterns

### Pattern 1: Query Optimization Pattern

**Pattern Name:** Indexed Single-Pass Query

**Applied to:** PR1 (Response Time), PR2 (Database Query Optimization)

**Intent:** Minimize database round trips and execution time by using indexed lookups

**Structure:**

```
Profile Update Request
    ↓
Spring validates DTO (< 50ms)
    ↓
Controller extracts security context (< 10ms)
    ↓
Service layer begins transaction
    ├─ Query 1: findById(userId) → O(1) via PK index (< 20ms)
    ├─ Query 2: existsByEmailAndIdNot(email, userId) → O(1) via email index (< 20ms) [optional]
    ├─ Update: save(user) → Single UPDATE statement (< 30ms)
    └─ Transaction commits
    ↓
Service → Controller → HTTP Response (< 100ms total)
```

**Design Decisions:**

1. **Primary Key Indexing:** User ID lookups use database primary key index
   - O(1) performance guaranteed
   - Database optimizer recognizes PK index

2. **Unique Email Index:** Email uniqueness check uses unique constraint index
   - `CREATE UNIQUE INDEX idx_user_email ON user(email)`
   - `existsByEmailAndIdNot` translates to indexed query
   - Prevents N+1 queries

3. **Lazy Loading:** Don't load related entities
   - Profile update operates on User entity only
   - No JPA eager loading of relationships
   - Reduces memory and database load

4. **Single Update Statement:** Update all fields in one SQL UPDATE
   - JPA/Hibernate generates single UPDATE with multiple SET clauses
   - Atomic at database level
   - No intermediate states

**Performance Targets:**

| Operation | Target | Rationale |
|-----------|--------|-----------|
| findById(userId) | < 20ms | Indexed PK lookup |
| existsByEmailAndIdNot | < 20ms | Indexed unique email |
| save(user) | < 30ms | Single UPDATE statement |
| Total Service Logic | < 100ms | Sum of all DB operations |
| HTTP Response | < 200ms | Includes JSON serialization |

**Monitoring:**

```java
// Enable Hibernate statistics
spring.jpa.properties.hibernate.generate_statistics=true

// Monitor in tests/metrics:
Statistics stats = sessionFactory.getStatistics();
long queryCount = stats.getQueryExecutionCount();  // Should be 2-3 max
```

---

### Pattern 2: Partial Update Pattern

**Pattern Name:** Conditional Field Update with Null Handling

**Applied to:** PR1 (Response Time), NFR design efficiency

**Intent:** Support partial updates (update only provided fields) while maintaining performance

**Structure:**

```java
// Request
UpdateUserRequest {
  name: "New Name",
  email: null,
  role: null,
  active: null
}

// Service logic
if (request.getName() != null) {
  user.setName(request.getName());  // One field updated
}
if (request.getEmail() != null) {
  // Email uniqueness check
  user.setEmail(request.getEmail());
}
// Unchanged fields not touched

// Single UPDATE statement:
// UPDATE User SET name = 'New Name' WHERE id = 1
// (email, role, active remain unchanged)
```

**Benefits:**

1. **Efficient Bandwidth:** Client sends only changed fields
2. **Efficient Database:** Only changed columns in UPDATE
3. **Efficient Validation:** Skip validation for null fields
4. **Performance:** Fewer comparisons, smaller UPDATE statement

**Constraints:**

1. **Null = Don't Update:** Must distinguish between null and unchanged
2. **No Explicit Nullification:** Cannot set field to NULL via this endpoint
3. **Optional Fields Required:** All fields must be nullable in DTO

---

### Pattern 3: Transaction Boundary Pattern

**Pattern Name:** Single Transaction for Atomic Operations

**Applied to:** REL1 (Data Consistency), PR1 (Performance)

**Intent:** Ensure all operations succeed or all fail together; prevent partial updates

**Structure:**

```java
@Service
public class UserService {
  
  @Transactional  // Single transaction boundary
  public UserResponse updateUser(Long userId, UpdateUserRequest request, 
                                  Authentication auth) {
    // All operations in this method are in single transaction
    
    // Step 1: Load
    User user = userRepository.findById(userId)
      .orElseThrow(() -> new UserNotFoundException(userId));
    // If not found: ROLLBACK, throw exception
    
    // Step 2: Validate authorization
    checkUpdateAuthorization(user, request, auth);
    // If unauthorized: ROLLBACK, throw exception
    
    // Step 3: Validate business rules
    if (request.getEmail() != null && !request.getEmail().equals(user.getEmail())) {
      if (userRepository.existsByEmailAndIdNot(request.getEmail(), userId)) {
        // If email exists: ROLLBACK, throw exception
        throw new EmailAlreadyExistsException(request.getEmail());
      }
    }
    
    // Step 4: Update
    if (request.getName() != null) user.setName(request.getName());
    if (request.getEmail() != null) user.setEmail(request.getEmail());
    if (isAdmin(auth) && request.getRole() != null) user.setRole(request.getRole());
    if (isAdmin(auth) && request.getActive() != null) user.setActive(request.getActive());
    
    // Step 5: Persist (within transaction)
    User updated = userRepository.save(user);
    // If persistence fails: ROLLBACK
    
    // Step 6: Return
    return UserResponse.from(updated);
  }
  // At method end: COMMIT transaction (if all succeeded)
}
```

**Consistency Guarantees:**

1. **All-or-Nothing:** Either entire update succeeds or entire update fails
2. **No Partial Updates:** Database never left in partially-updated state
3. **No Reading Dirty Data:** Other transactions see consistent state
4. **Rollback on Error:** Any exception rolls back entire transaction

**Isolation Level:** Spring Boot default (READ_COMMITTED)
- Prevents dirty reads
- Prevents lost updates
- Sufficient for profile updates (low concurrency on same user)

---

## 2. Scalability Design Patterns

### Pattern 4: Stateless Request Handling Pattern

**Pattern Name:** No Session State Per Request

**Applied to:** SR1 (Horizontal Scaling)

**Intent:** Enable horizontal scaling via stateless design (each instance handles request independently)

**Structure:**

```
Load Balancer
    ├─ Instance 1: Profile Update Service
    ├─ Instance 2: Profile Update Service
    └─ Instance 3: Profile Update Service
    
All instances share:
    └─ Single Database

Each request:
1. Client sends request with credentials (no session)
2. Load balancer routes to any available instance (no affinity needed)
3. Instance extracts authentication from request headers
4. Instance checks authorization from current request context
5. Instance executes update
6. Instance returns response
7. Client receives response

Next request:
1. Can go to different instance (no state dependency)
2. Fresh authentication extraction
3. Same result guaranteed (stateless operation)
```

**Design Decisions:**

1. **No Session Storage:** Spring Security uses header-based auth (HTTP Basic)
   - Credentials in Authorization header each request
   - No session cookies
   - No session replication needed

2. **No Request State:** Each request is independent
   - No thread-local state maintained across requests
   - No cache invalidation between instances
   - User data fetched fresh from database

3. **Load Balancing:** Any load balancer strategy works
   - Round-robin: ✅ Works
   - Least connections: ✅ Works
   - Random: ✅ Works
   - Sticky sessions: ❌ Not needed (but harmless)

**Scalability Implications:**

| Scaling Dimension | Approach | Benefit |
|------------------|----------|---------|
| Horizontal | Add instances | Linear throughput increase |
| Vertical | Increase JVM heap/CPU | More concurrent requests per instance |
| Database | Indexes, connection pool | Shared across instances |

**Performance Scaling:**

```
1 instance, 2 cores:  ~2,000 req/sec
2 instances, 2 cores: ~4,000 req/sec
4 instances, 2 cores: ~8,000 req/sec
(Linear scaling with stateless design)
```

---

### Pattern 5: Database Connection Pooling Pattern

**Pattern Name:** HikariCP Connection Pool Sharing

**Applied to:** SR1, SR2, SR3 (Scalability)

**Intent:** Efficiently manage database connections across multiple concurrent requests

**Structure:**

```
HikariCP Connection Pool (10 connections)
├─ Connection 1: Active request handling
├─ Connection 2: Active request handling
├─ Connection 3: Idle (ready)
├─ Connection 4: Idle (ready)
└─ ... (up to 10 total)

Request Handling Lifecycle:
1. Request received
2. Service layer requests database connection
3. HikariCP provides connection from pool (existing or new, up to max)
4. Service executes query/update
5. Connection returned to pool
6. Next request can reuse connection
```

**Configuration (Default Spring Boot):**

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10  # Default
      minimum-idle: 10       # Default
      connection-timeout: 30000  # 30 seconds
      idle-timeout: 600000       # 10 minutes
      max-lifetime: 1800000      # 30 minutes
```

**Scaling Implications:**

- **Per Instance:** 10 connections each
- **2 Instances:** 20 connections total to database
- **4 Instances:** 40 connections total to database
- **Database Must Support:** Connection limit >= instances × pool size

**Tuning Formula:**

```
optimal_pool_size = (number_of_cores × 2) + effective_spindle_count

Example:
- 4 CPU cores, 1 disk spindle
- optimal = (4 × 2) + 1 = 9 connections
- Spring Boot default of 10 is reasonable
```

---

## 3. Availability & Reliability Design Patterns

### Pattern 6: Transactional Rollback Pattern

**Pattern Name:** Automatic Transaction Rollback on Error

**Applied to:** AR2 (Fault Tolerance), AR3 (Error Recovery), REL1 (Data Consistency)

**Intent:** Ensure database consistency by rolling back transactions when errors occur

**Structure:**

```
Transaction Begins
    ↓
Load User (success)
    ↓
Authorization Check (FAIL) ← Error detected
    ├─ Set rollback flag
    ├─ Throw exception
    └─ Transaction rolls back
         ├─ Undo Load operation
         └─ Database state unchanged
    ↓
Exception caught by controller/handler
    ↓
Return 403 Forbidden error response


Transaction Begins
    ↓
Load User (success)
    ↓
Authorization Check (success)
    ↓
Email Uniqueness Check (FAIL) ← Error detected
    ├─ Set rollback flag
    ├─ Throw exception
    └─ Transaction rolls back
         ├─ Undo Load operation
         └─ Database state unchanged
    ↓
Exception caught by controller/handler
    ↓
Return 409 Conflict error response


Transaction Begins
    ↓
Load User (success)
    ↓
Authorization Check (success)
    ↓
Email Uniqueness Check (success)
    ↓
Update Entity (success)
    ↓
Persist (success)
    ↓
Transaction commits (all changes persisted)
    ↓
Return 200 OK with updated user
```

**Error Conditions Handled:**

| Error | Cause | Action | Result |
|-------|-------|--------|--------|
| User not found | findById returns empty | Throw UserNotFoundException | Rollback (nothing persisted) |
| Unauthorized | Authorization check fails | Throw ForbiddenException | Rollback (nothing persisted) |
| Email duplicate | existsByEmailAndIdNot returns true | Throw EmailAlreadyExistsException | Rollback (nothing persisted) |
| Database error | SQLException during save | Caught by Spring, rolled back | Rollback (nothing persisted) |

**Consistency Guarantee:** Database always left in consistent state (either pre-update or post-update, never in-between)

---

### Pattern 7: Graceful Degradation Pattern

**Pattern Name:** Error Response with Meaningful Feedback

**Applied to:** AR3 (Error Recovery), REL2 (Error Handling)

**Intent:** Return clear, actionable error information so clients can recover

**Structure:**

```
Error Occurs in Service Layer
    ↓
Spring catches exception
    ↓
GlobalExceptionHandler translates to appropriate HTTP status
    ├─ ValidationException → 400 Bad Request
    ├─ ForbiddenException → 403 Forbidden
    ├─ UserNotFoundException → 404 Not Found
    ├─ EmailAlreadyExistsException → 409 Conflict
    └─ Unexpected exception → 500 Internal Server Error
    ↓
Generate ErrorResponse DTO
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
    ↓
Return JSON response with appropriate HTTP status
    ↓
Client receives clear, structured error information
    ↓
Client can determine cause and retry appropriately
```

**Error Response Design:**

1. **HTTP Status Code:** Indicates error category (client error 4xx vs server error 5xx)
2. **Error Message:** Human-readable explanation
3. **Error Details:** Field-level details for validation errors
4. **Timestamp:** When error occurred (for debugging)
5. **No Stack Traces:** Security: never expose internal details
6. **No Sensitive Data:** Never expose user IDs of other users or passwords

---

## 4. Security Design Patterns

### Pattern 8: Authorization Check Pattern

**Pattern Name:** Multi-Layer Authorization Enforcement

**Applied to:** SEC2 (Authorization)

**Intent:** Enforce RBAC with field-level restrictions

**Structure:**

```
Request received with user data
    ↓
Extract authentication from HTTP Basic header
    ↓
Get authenticated user ID and role from Spring Security
    ↓
Layer 1: Is user authenticated?
    ├─ NO → Return 401 Unauthorized
    └─ YES → Continue
    ↓
Layer 2: Role-based authorization
    ├─ Is user admin?
    │  ├─ YES → Allow all operations, skip to Layer 4
    │  └─ NO → Check self-update
    │          ├─ Is targetUserId == authenticatedUserId?
    │          │  ├─ NO → Return 403 Forbidden
    │          │  └─ YES → Continue to Layer 3
    ↓
Layer 3: Field-level authorization (for non-admin)
    ├─ Requesting role update?
    │  ├─ YES → Return 403 Forbidden (only admin can)
    │  └─ NO → Continue
    ├─ Requesting active update?
    │  ├─ YES → Return 403 Forbidden (only admin can)
    │  └─ NO → Continue
    ↓
Layer 4: Update execution authorized
    ├─ Execute update with authorized fields
    └─ Return 200 OK
```

**Implementation:**

```java
private void checkUpdateAuthorization(Long targetUserId, UpdateUserRequest request, 
                                      Authentication auth) {
  // Layer 1: Extract authenticated info
  Long authenticatedUserId = (Long) auth.getPrincipal();
  boolean isAdmin = auth.getAuthorities().stream()
    .anyMatch(ga -> ga.getAuthority().equals("ROLE_ADMIN"));
  
  // Layer 2: Role-based check
  if (!isAdmin && !targetUserId.equals(authenticatedUserId)) {
    throw new ForbiddenException("Cannot update other users' profiles");
  }
  
  // Layer 3: Field-level check (non-admin only)
  if (!isAdmin) {
    if (request.getRole() != null) {
      throw new ForbiddenException("Cannot update role");
    }
    if (request.getActive() != null) {
      throw new ForbiddenException("Cannot update active status");
    }
  }
}
```

**Authorization Matrix:**

| User Type | Update Self | Update Other | Change Role | Change Active |
|-----------|---|---|---|---|
| Regular User | ✅ Name, Email | ❌ | ❌ | ❌ |
| Admin | ✅ All fields | ✅ All fields | ✅ | ✅ |

---

### Pattern 9: Input Validation Pattern

**Pattern Name:** Multi-Layer Defense-in-Depth Validation

**Applied to:** SEC3 (Input Validation)

**Intent:** Validate data at multiple layers to catch errors early

**Structure:**

```
HTTP Request received
    ↓
Layer 1: Spring deserializes JSON to UpdateUserRequest DTO
    ├─ Check valid JSON structure
    ├─ Check property types (String/Boolean)
    └─ If invalid JSON: 400 Bad Request (before DTO validation)
    ↓
Layer 2: Bean Validation annotations applied
    ├─ @NotEmpty on name
    ├─ @Size(max=100) on name
    ├─ @Email on email
    ├─ Custom @ValidRole on role
    └─ If validation fails: 400 Bad Request with field details
    ↓
Layer 3: Service-level business rule validation
    ├─ Check user exists
    │  └─ If not found: 404 Not Found
    ├─ Check email uniqueness (if email provided)
    │  └─ If duplicate: 409 Conflict
    ├─ Check role validity (if role provided)
    │  └─ If invalid: 400 Bad Request
    └─ If validation fails: Return appropriate error
    ↓
Layer 4: Database constraints (final guard)
    ├─ Unique constraint on email
    ├─ NOT NULL constraints
    └─ If constraint violated: 500 Internal Server Error (should never happen)
    ↓
Update succeeds (all validation layers passed)
```

**Validation Layers:**

| Layer | Location | What's Checked | Error Response |
|-------|----------|---|---|
| 1 | Spring Deserialization | JSON structure, types | 400 Bad Request |
| 2 | DTO Annotations | Format, length, format | 400 Bad Request |
| 3 | Service Business Logic | Email uniqueness, user exists | 404/409 Conflict |
| 4 | Database Constraints | Unique constraints, NOT NULL | 500 (shouldn't happen) |

**Validation Annotations:**

```java
public class UpdateUserRequest {
  @NotEmpty
  @Size(max = 100)
  private String name;
  
  @Email
  private String email;
  
  @ValidRole  // Custom validator
  private String role;
  
  private Boolean active;
}
```

---

## 5. Observability Design Patterns

### Pattern 10: Structured Logging Pattern

**Pattern Name:** JSON-Structured Logging for Aggregation

**Applied to:** REL3 (Monitoring and Observability)

**Intent:** Enable log aggregation and analysis across distributed instances

**Structure:**

```
Application generates log event
    ↓
SLF4J formats as structured JSON
    ├─ timestamp: ISO 8601
    ├─ level: INFO/DEBUG/ERROR
    ├─ logger: class name
    ├─ message: human-readable message
    └─ fields: contextual data
    ↓
Logback writes to stdout
    ↓
Docker/Kubernetes captures stdout
    ↓
Log aggregation system (ELK, Splunk, etc.) consumes
    ├─ Parses JSON
    ├─ Indexes fields
    └─ Enables searching/filtering
    ↓
Dashboards and alerts created from logs
```

**Log Examples:**

```
{"timestamp":"2024-01-15T10:30:00Z","level":"INFO","logger":"UserService",
 "message":"Profile update request received","userId":1,"fields":["name","email"]}

{"timestamp":"2024-01-15T10:30:01Z","level":"DEBUG","logger":"UserService",
 "message":"Authorization check","authenticatedUserId":1,"targetUserId":1,
 "isAdmin":false,"result":"AUTHORIZED"}

{"timestamp":"2024-01-15T10:30:01Z","level":"DEBUG","logger":"UserService",
 "message":"Email uniqueness check","email":"new@example.com","userId":1,"exists":false}

{"timestamp":"2024-01-15T10:30:02Z","level":"INFO","logger":"UserService",
 "message":"Profile update successful","userId":1,"fieldsUpdated":2,"duration":45,"unit":"ms"}
```

---

### Pattern 11: Metrics Collection Pattern

**Pattern Name:** Spring Actuator Metrics

**Applied to:** REL3 (Monitoring and Observability)

**Intent:** Collect and expose system metrics for monitoring

**Structure:**

```
Spring Actuator autoconfigures metrics collection
    ↓
MeterRegistry collects:
    ├─ HTTP request metrics
    │  ├─ http.server.requests (histogram of response times)
    │  ├─ Count by status code (200, 400, 403, 404, 409, 500)
    │  └─ Count by endpoint (/api/users/{userId})
    ├─ Database metrics
    │  ├─ Database connection pool size/utilization
    │  ├─ Query execution time
    │  └─ Active transactions
    ├─ JVM metrics
    │  ├─ Memory usage
    │  ├─ CPU usage
    │  └─ Thread count
    └─ Custom metrics
       ├─ Profile updates by result type
       └─ Authorization decisions
    ↓
Exposed via /actuator/metrics endpoint
    ↓
Monitoring system scrapes (Prometheus, Datadog, etc.)
    ↓
Dashboards and alerts created
```

**Monitoring Example:**

```
GET /actuator/metrics/http.server.requests

{
  "name": "http.server.requests",
  "measurements": [
    {"statistic": "COUNT", "value": 1523},
    {"statistic": "TOTAL_TIME", "value": 245632.5},
    {"statistic": "MAX", "value": 523.2},
    {"statistic": "MEAN", "value": 161.3}
  ],
  "baseUnit": "milliseconds"
}

// Also available by status:
GET /actuator/metrics/http.server.requests?tag=status:200
GET /actuator/metrics/http.server.requests?tag=status:403
GET /actuator/metrics/http.server.requests?tag=status:409
```

---

## 6. Resilience Design Patterns

### Pattern 12: Retry Strategy Pattern

**Pattern Name:** Automatic Retry with Backoff

**Applied to:** AR2 (Fault Tolerance)

**Intent:** Handle transient failures by retrying

**Structure:**

```
Request execution
    ↓
Try to execute (attempt 1)
    ├─ Success → Return result
    └─ Transient error (e.g., connection timeout):
        ├─ Wait 100ms (initial backoff)
        └─ Try again (attempt 2)
    ├─ Success → Return result
    └─ Transient error:
        ├─ Wait 200ms (exponential backoff)
        └─ Try again (attempt 3)
    ├─ Success → Return result
    └─ Transient error:
        ├─ Wait 400ms (exponential backoff)
        └─ Try again (attempt 4)
    ├─ Success → Return result
    └─ Failure after max retries:
        └─ Give up, return error
```

**Implementation (Spring Retry):**

```java
@Service
public class UserService {
  
  @Retryable(
    value = {DataAccessException.class},
    maxAttempts = 3,
    backoff = @Backoff(delay = 100, multiplier = 2.0)
  )
  public User loadUser(Long userId) {
    return userRepository.findById(userId)
      .orElseThrow(() -> new UserNotFoundException(userId));
  }
  
  @Recover
  public User recover(DataAccessException ex, Long userId) {
    // Called if all retries fail
    log.error("Failed to load user {} after retries", userId, ex);
    throw new RuntimeException("Service unavailable", ex);
  }
}
```

**Transient vs Permanent Errors:**

| Error | Type | Retry? | Reason |
|-------|------|--------|--------|
| Connection timeout | Transient | ✅ | Might succeed on retry |
| Database unavailable | Transient | ✅ | Database may recover |
| SQL syntax error | Permanent | ❌ | Will always fail |
| Validation error | Permanent | ❌ | User must fix input |
| Authorization failure | Permanent | ❌ | Permissions won't change |

---

## Summary: NFR Design Patterns

| NFR Category | Pattern | Purpose | Key Benefit |
|---|---|---|---|
| **Performance** | Indexed Single-Pass Query | Minimize DB queries | O(1) lookups, <200ms response |
| | Partial Update | Conditional field updates | Efficient network/database |
| | Transaction Boundary | Atomic operations | Consistency guaranteed |
| **Scalability** | Stateless Handling | Enable horizontal scaling | Add instances for throughput |
| | Connection Pooling | Efficient resource use | Shared pool across requests |
| **Availability** | Transactional Rollback | Consistency on error | No partial updates |
| | Graceful Degradation | Clear error responses | Clients can recover |
| **Security** | Authorization Check | RBAC enforcement | Field-level restrictions |
| | Input Validation | Multi-layer defense | SQL injection prevention |
| **Observability** | Structured Logging | Centralized analysis | Dashboards and alerts |
| | Metrics Collection | System monitoring | Performance visibility |
| **Resilience** | Retry Strategy | Handle transient failures | Automatic recovery |

---

## Next Steps

These patterns will be implemented using specific technologies confirmed in NFR Requirements:

- **Spring Boot 3.2.3** for framework and patterns
- **Spring Data JPA** for query optimization
- **Spring Security** for authentication/authorization
- **Spring Actuator** for metrics
- **SLF4J + Logback** for structured logging
- **Jakarta Bean Validation** for input validation

The Logical Components document will detail how these patterns are composed into specific design components.
