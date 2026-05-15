# Tech Stack Decisions - Profile Update Service

## Overview

This document formalizes technology stack decisions for the Profile Update Service. Since this is a brownfield enhancement, decisions prioritize leveraging existing infrastructure with minimal new dependencies.

---

## Executive Summary

**Decision:** Use existing tech stack; no new frameworks or libraries required.

| Layer | Technology | Version | Decision |
|-------|-----------|---------|----------|
| **Application Framework** | Spring Boot | 3.2.3 | ✅ Continue (no upgrade) |
| **Language** | Java | 21 | ✅ Continue (no downgrade) |
| **Web Framework** | Spring Web MVC | 6.x | ✅ Continue |
| **Security** | Spring Security | 6.x | ✅ Continue |
| **ORM/JPA** | Spring Data JPA + Hibernate | 6.x / 6.x | ✅ Continue |
| **Database Driver** | H2 (dev) / PostgreSQL (prod) | Latest | ✅ Continue |
| **Validation** | Jakarta Bean Validation | 3.x | ✅ Continue |
| **Logging** | SLF4J + Logback | 2.x / 1.x | ✅ Continue |
| **Testing - Unit** | JUnit 5 | 5.x | ✅ Continue |
| **Testing - Mocking** | Mockito | 5.x | ✅ Continue |
| **Testing - Integration** | Spring Test | 6.x | ✅ Continue |
| **Exception Handling** | Spring's GlobalExceptionHandler | Built-in | ✅ Continue |
| **Metrics** | Spring Actuator | 6.x | ✅ Continue |

**New Dependencies Required:** NONE

---

## 1. Application Framework Layer

### 1.1 Spring Boot 3.2.3

**Decision:** CONTINUE - No upgrade required

**Rationale:**
- ✅ Already in use by application
- ✅ LTS version (Long-Term Support)
- ✅ Stable and well-tested
- ✅ Modern features (records, sealed classes)
- ✅ Excellent ecosystem (Spring Data, Spring Security, Spring Test)
- ✅ Team expertise available

**Alternative Considered:** Spring Boot 3.3.x (latest)
- **Rejected:** No critical features needed; upgrade risk not justified

**Spring Boot Capabilities Used:**
- Auto-configuration for Spring Data JPA
- Embedded server (Tomcat default)
- Actuator for metrics
- Exception handling infrastructure
- Security auto-configuration

**No Changes Needed:** Use existing Spring Boot configuration as-is.

---

## 2. Language and Compiler

### 2.1 Java 21 (LTS)

**Decision:** CONTINUE - No version change

**Rationale:**
- ✅ Already in use (brownfield)
- ✅ LTS version (Long-Term Support until Sep 2031)
- ✅ Modern language features available
- ✅ Performance optimizations
- ✅ Stable and production-ready

**Java 21 Features Used:**
- Records for DTOs (UpdateUserRequest, UserResponse) - optional, can use POJO
- Pattern matching in switch statements - optional
- Virtual threads (if Spring Boot 3.2+ supports) - not needed for profile updates

**Compiler Settings:**
```
source: 21
target: 21
encoding: UTF-8
```

**No Changes Needed:** Continue using Java 21.

---

## 3. Web Framework

### 3.1 Spring Web MVC

**Decision:** CONTINUE - Use existing MVC framework

**Rationale:**
- ✅ Already in use by application
- ✅ Proven framework for REST APIs
- ✅ Built-in request mapping (@GetMapping, @PutMapping, etc.)
- ✅ Built-in exception handling (@ExceptionHandler)
- ✅ Content negotiation and serialization

**Annotations Used:**
```java
@RestController
@RequestMapping("/api/users")
@PutMapping("/{userId}")
@Validated // Enable method-level validation
public class UserController {
    // Implementation
}
```

**Alternative Considered:** Spring WebFlux (reactive)
- **Rejected:** Not needed for stateless REST API; added complexity

**No Changes Needed:** Use existing Spring MVC setup.

---

## 4. Security Framework

### 4.1 Spring Security 6.x

**Decision:** CONTINUE - Use existing security framework

**Rationale:**
- ✅ Already configured in application
- ✅ HTTP Basic Authentication working
- ✅ Role-based access control (RBAC) via authorities
- ✅ SecurityContext provides user identity
- ✅ Filters handle authentication/authorization

**Security Features Used:**
```java
Authentication auth = SecurityContextHolder.getContext().getAuthentication();
boolean isAdmin = auth.getAuthorities().stream()
    .anyMatch(ga -> ga.getAuthority().equals("ROLE_ADMIN"));
```

**RBAC Implementation:**
- Users with ROLE_USER can update own profile only
- Users with ROLE_ADMIN can update any profile
- Admin-only fields (role, active) restricted

**Configuration Leverage:**
- Existing UserDetailsService (loads user from database)
- Existing authentication filters
- Existing authorization patterns

**No Changes Needed:** Use existing Spring Security configuration.

---

## 5. Data Access Layer

### 5.1 Spring Data JPA

**Decision:** CONTINUE - Use existing JPA abstraction

**Rationale:**
- ✅ Already in use
- ✅ Simplifies database access via repository pattern
- ✅ Query method derivation (existsByEmailAndIdNot)
- ✅ Automatic transaction management
- ✅ Integration with Hibernate

**Repository Interface:**
```java
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findById(Long id);
    boolean existsByEmailAndIdNot(String email, Long userId);
}
```

**Query Methods:**
- `findById()` - Load user by primary key (indexed, O(1))
- `save()` - Update user entity
- `existsByEmailAndIdNot()` - Check email uniqueness (custom query via method name)

**No New Queries Required:** Existing methods sufficient.

---

### 5.2 Hibernate ORM

**Decision:** CONTINUE - Use existing Hibernate ORM

**Rationale:**
- ✅ Already configured as Spring Data JPA provider
- ✅ Parameterized queries (SQL injection protection)
- ✅ Transaction management (@Transactional)
- ✅ Entity lifecycle management
- ✅ First-level cache (session cache)

**Hibernate Features Used:**
- Entity mapping via @Entity, @Column annotations
- Unique constraint enforcement on email
- Automatic UPDATE statement generation for save()
- Query statistics for performance monitoring

**Configuration (via Spring Boot properties):**
```properties
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=false
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.H2Dialect
```

**No Changes Needed:** Use existing Hibernate configuration.

---

## 6. Database Layer

### 6.1 Database Engines

**Decision:** CONTINUE with existing setup

| Environment | Database | Rationale |
|-------------|----------|-----------|
| **Development** | H2 (in-memory) | Fast, self-contained, existing setup |
| **Production** | PostgreSQL / MySQL | Existing choice, production-ready |

**Rationale:**
- ✅ H2 for development (fast, no external dependencies)
- ✅ PostgreSQL/MySQL for production (proven, scalable)
- ✅ No schema migrations needed (User entity already has all fields)
- ✅ JDBC drivers already configured

**Schema (Existing - No Changes):**
```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true
);

CREATE INDEX idx_user_email ON user(email);
```

**Connection Pooling:**
- HikariCP (Spring Boot default)
- Pool size: 10 connections (default)
- Tunable if performance testing indicates need

**No Changes Needed:** Continue with existing database setup.

---

## 7. Validation Framework

### 7.1 Jakarta Bean Validation

**Decision:** CONTINUE - Use existing validation framework

**Rationale:**
- ✅ Already in use by application
- ✅ Standard Java EE / Jakarta EE validation
- ✅ Declarative validation via annotations
- ✅ Automatic Spring integration
- ✅ Support for custom validators

**Validation Annotations Used:**
```java
public class UpdateUserRequest {
    @NotEmpty
    @Size(max = 100)
    private String name;
    
    @Email
    private String email;
    
    // Custom validator for role enum
    @ValidRole
    private String role;
    
    private Boolean active;
}
```

**Validation Triggers:**
- `@Validated` on controller enables method-level validation
- `@Valid` on request body parameter triggers DTO validation
- Spring automatically returns 400 with field errors on validation failure

**Custom Validators (if needed):**
```java
@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = RoleValidator.class)
public @interface ValidRole {
    String message() default "Invalid role value";
    // ...
}
```

**No Changes Needed:** Use existing Jakarta validation.

---

## 8. Logging and Observability

### 8.1 SLF4J + Logback

**Decision:** CONTINUE - Use existing logging framework

**Rationale:**
- ✅ Standard Spring Boot logging (SLF4J facade)
- ✅ Logback provides performance and configuration flexibility
- ✅ Structured logging support for JSON output
- ✅ No new dependencies

**Logging Usage:**
```java
private static final Logger log = LoggerFactory.getLogger(UserService.class);

log.info("Profile update successful: userId={}, duration={}ms", userId, duration);
log.warn("Authorization denied: user={}, target={}", userId, targetId);
log.error("Database error during update", exception);
```

**Configuration (Existing):**
```yaml
logging:
  level:
    com.sandbox.userapi: INFO
    org.springframework.security: DEBUG
```

**No Changes Needed:** Use existing logging setup.

---

### 8.2 Spring Actuator

**Decision:** CONTINUE - Use existing metrics collection

**Rationale:**
- ✅ Already in application
- ✅ Provides metrics endpoints (/actuator/metrics)
- ✅ Built-in performance monitoring
- ✅ Health checks and application info

**Metrics to Monitor:**
- HTTP request count (by endpoint)
- HTTP response times (histograms)
- HTTP error rates (by status code)
- JVM metrics (memory, CPU)
- Database connection pool metrics

**Endpoints:**
```
GET /actuator/health - Overall application health
GET /actuator/metrics - Available metrics
GET /actuator/metrics/http.server.requests - HTTP request metrics
```

**No Changes Needed:** Use existing Actuator configuration.

---

## 9. Testing Frameworks

### 9.1 JUnit 5

**Decision:** CONTINUE - Use existing unit testing framework

**Rationale:**
- ✅ Modern testing framework for Java
- ✅ Parameterized tests support
- ✅ Better extension model
- ✅ Already in use

**Test Structure:**
```java
@DisplayName("UserService Profile Update Tests")
class UserServiceTest {
    
    @Nested
    @DisplayName("Authorization Tests")
    class AuthorizationTests {
        @Test void testRegularUserCannotUpdateOtherUser() { }
        @Test void testAdminCanUpdateAnyUser() { }
    }
    
    @ParameterizedTest
    @CsvSource({
        "name, 'Valid Name', true",
        "name, '', false",
        "email, 'invalid', false"
    })
    void testValidation(String field, String value, boolean valid) { }
}
```

**Features Used:**
- @Test for unit tests
- @DisplayName for readable test names
- @Nested for test organization
- @ParameterizedTest for data-driven tests
- Assertions (assertEquals, assertTrue, etc.)

**No Changes Needed:** Use existing JUnit 5 setup.

---

### 9.2 Mockito

**Decision:** CONTINUE - Use existing mocking framework

**Rationale:**
- ✅ Standard mocking library for Java
- ✅ Mock objects for dependencies (UserRepository, Spring Security)
- ✅ Verify method calls and arguments
- ✅ Already integrated

**Mocking Usage:**
```java
@SpringBootTest
class UserControllerTest {
    @MockBean
    private UserService userService;
    
    @Test
    void testUpdateUserEndpoint() {
        User updatedUser = new User(1L, "New Name", "new@ex.com", "ROLE_USER", true);
        when(userService.updateUser(any())).thenReturn(updatedUser);
        
        // Execute endpoint
        // Verify response
    }
}
```

**No Changes Needed:** Use existing Mockito setup.

---

### 9.3 Spring Test Framework

**Decision:** CONTINUE - Use existing integration testing support

**Rationale:**
- ✅ @SpringBootTest for full context loading
- ✅ TestRestTemplate for REST endpoint testing
- ✅ In-memory H2 database for integration tests
- ✅ Mock MVC for request/response testing

**Integration Test Structure:**
```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class UserControllerIntegrationTest {
    @Autowired
    private TestRestTemplate restTemplate;
    
    @Test
    void testProfileUpdateEndpoint() {
        UpdateUserRequest request = new UpdateUserRequest("New Name", null, null, null);
        ResponseEntity<UserResponse> response = restTemplate.exchange(
            "/api/users/1",
            HttpMethod.PUT,
            new HttpEntity<>(request, headers),
            UserResponse.class
        );
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
    }
}
```

**No Changes Needed:** Use existing Spring Test framework.

---

## 10. Exception Handling

### 10.1 Spring's Exception Handler Infrastructure

**Decision:** CONTINUE - Use existing GlobalExceptionHandler

**Rationale:**
- ✅ Centralized exception handling
- ✅ Consistent error response format
- ✅ Already configured in application
- ✅ Maps exceptions to HTTP status codes

**Custom Exceptions to Define:**
```java
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(Long userId) {
        super("User not found: " + userId);
    }
}

public class EmailAlreadyExistsException extends RuntimeException {
    public EmailAlreadyExistsException(String email) {
        super("Email already in use: " + email);
    }
}

public class UnauthorizedException extends RuntimeException {
    public UnauthorizedException(String message) {
        super(message);
    }
}
```

**GlobalExceptionHandler Mappings:**
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(UserNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(UserNotFoundException ex) {
        return ResponseEntity.status(404)
            .body(new ErrorResponse(404, "Not Found", ex.getMessage()));
    }
    
    @ExceptionHandler(EmailAlreadyExistsException.class)
    public ResponseEntity<ErrorResponse> handleConflict(EmailAlreadyExistsException ex) {
        return ResponseEntity.status(409)
            .body(new ErrorResponse(409, "Conflict", ex.getMessage()));
    }
}
```

**No Changes Needed:** Extend existing exception handler patterns.

---

## 11. Performance Optimization Decisions

### 11.1 Database Query Strategy

**Decision:** Use indexed primary key and unique constraint lookups

**Rationale:**
- ✅ O(1) performance via indexes
- ✅ Minimal query count (3 max)
- ✅ Transactional consistency

**Queries:**
1. `SELECT * FROM User WHERE id = ?` (Primary key index)
2. `SELECT COUNT(*) FROM User WHERE email = ? AND id != ?` (Unique email index)
3. `UPDATE User SET ... WHERE id = ?` (Primary key index)

**No N+1 Queries:** Profile update is single-user operation; no related entities loaded.

---

### 11.2 Caching Strategy

**Decision:** No application-level caching initially

**Rationale:**
- ✅ Profile data changes frequently (per-user, not shared)
- ✅ Profile updates are per-user operations (no cache invalidation needed)
- ✅ Simple to add later if performance testing shows bottleneck
- ✅ Avoids cache consistency complexity

**Future Enhancement (if needed):**
- Option 1: Ehcache for in-process caching (single instance)
- Option 2: Redis for distributed cache (multiple instances)
- Decision Point: Performance test results will determine if caching needed

**No Changes Needed:** Start without caching.

---

### 11.3 Connection Pooling

**Decision:** Use HikariCP defaults (10 connections)

**Rationale:**
- ✅ HikariCP is Spring Boot default and fastest
- ✅ 10 connections suitable for typical load
- ✅ Tunable if load testing indicates need

**Tuning Formula (if needed):**
```
pool_size = (number_of_cores * 2) + effective_spindle_count
Example: 4 cores = (4 * 2) + 1 = 9 connections
```

**Configuration (if tuning needed):**
```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
```

**No Changes Needed:** Use HikariCP defaults initially.

---

## 12. Deployment and Infrastructure Decisions

### 12.1 Deployment Model

**Decision:** CONTINUE - Standard Spring Boot JAR deployment

**Rationale:**
- ✅ Existing deployment model
- ✅ Simple, proven approach
- ✅ No new infrastructure needed
- ✅ Supports Docker containerization if needed

**Deployment Process:**
1. Build: `mvn clean package`
2. Run: `java -jar application.jar`
3. Configuration: Environment variables or application.properties
4. Monitoring: Spring Actuator (/actuator endpoints)

**No Changes Needed:** Continue with existing deployment.

---

### 12.2 Container Support (Optional)

**Decision:** Compatible with Docker; no changes required

**Rationale:**
- ✅ Spring Boot applications containerize easily
- ✅ Existing Dockerfile can include profile update feature
- ✅ Environment variables for configuration

**Sample Dockerfile (if containerizing):**
```dockerfile
FROM openjdk:21-slim
COPY target/application.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```

**No Changes Needed:** Existing containerization (if used) continues.

---

### 12.3 Configuration Management

**Decision:** Use Spring Boot application.properties/application.yml

**Rationale:**
- ✅ Built-in Spring Boot configuration management
- ✅ Environment variable overrides
- ✅ Profile-specific configurations (dev, test, prod)

**Configuration File:**
```yaml
spring:
  datasource:
    url: jdbc:h2:mem:testdb
    username: sa
    password: 
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
  security:
    user:
      name: admin
      password: password
```

**No Changes Needed:** Use existing configuration.

---

## Summary: Tech Stack Compliance Checklist

| Component | Technology | Version | Decision | Risk |
|-----------|-----------|---------|----------|------|
| Framework | Spring Boot | 3.2.3 | Continue | ✅ None |
| Language | Java | 21 | Continue | ✅ None |
| Web MVC | Spring Web | 6.x | Continue | ✅ None |
| Security | Spring Security | 6.x | Continue | ✅ None |
| ORM | Spring Data JPA + Hibernate | 6.x / 6.x | Continue | ✅ None |
| Database | H2 / PostgreSQL | Latest | Continue | ✅ None |
| Validation | Jakarta Bean Validation | 3.x | Continue | ✅ None |
| Logging | SLF4J + Logback | 2.x / 1.x | Continue | ✅ None |
| Testing | JUnit 5 + Mockito + Spring Test | 5.x / 5.x / 6.x | Continue | ✅ None |
| Metrics | Spring Actuator | 6.x | Continue | ✅ None |
| Exceptions | GlobalExceptionHandler | Built-in | Continue | ✅ None |

**New Dependencies:** NONE
**Breaking Changes:** NONE
**Migration Needed:** NONE
**Configuration Changes:** Minimal (add profile update endpoint)

---

## Dependencies Summary

### No New Maven Dependencies Required

All required dependencies already in Spring Boot 3.2.3 BOM:

```xml
<!-- Existing - No new additions needed -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
<!-- Existing test dependencies -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

**No new dependencies added.**

---

## Decision Summary

| Decision | Rationale | Risk Level |
|----------|-----------|-----------|
| Continue Spring Boot 3.2.3 | Stable, proven, already in use | ✅ None |
| Continue Java 21 | LTS version, modern features, team expertise | ✅ None |
| Continue Spring Security | Proven, already configured, RBAC supported | ✅ None |
| Continue Spring Data JPA | O(1) lookups with indexes, parameterized queries | ✅ None |
| Continue Jakarta Validation | Standard framework, automatic Spring integration | ✅ None |
| No application caching | Simple design, can add later if needed | ✅ None |
| Standard HikariCP defaults | Suitable for typical load, tunable if needed | ✅ None |
| Standard deployment model | Existing JAR deployment, no infrastructure changes | ✅ None |

**Overall Tech Stack Risk:** ✅ MINIMAL
**No new framework risk, no compatibility issues, no unknown technologies**

---

## Implementation Timeline

**Tech Stack Setup:** No new setup needed
**Framework Configuration:** Use existing configuration
**Development:** Begin immediately with familiar tech stack
**Testing:** Use established testing frameworks
**Deployment:** Use existing deployment process

**Ready to proceed to Code Generation phase.**
