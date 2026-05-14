# Technology Stack

## Programming Languages

### Java 21
- **Version**: Java 21 (LTS - Long Term Support)
- **Usage**: Primary application language for all business logic, controllers, services, and data access
- **Features Used**:
  - Records (for immutable DTOs: UserResponse, UpdateUserRequest)
  - Pattern matching
  - Text blocks (potential in documentation)
  - Modern Stream API
  - Lambda expressions
- **Justification**: Latest LTS version with modern language features, excellent performance, strong ecosystem

## Frameworks

### Spring Boot 3.2.3
- **Version**: 3.2.3
- **Purpose**: Core application framework providing:
  - Dependency injection and IoC container
  - Auto-configuration for rapid development
  - Embedded web server (Tomcat)
  - Production-ready features (Actuator)
  - Simplified configuration via application.yml
- **Usage**: Foundation for entire application stack

### Spring Web (Spring MVC)
- **Version**: 3.2.3 (via spring-boot-starter-web)
- **Purpose**: REST API development
- **Usage**:
  - @RestController for REST endpoints
  - @RequestMapping for URL routing
  - Automatic JSON serialization/deserialization via Jackson
  - Exception handling via @RestControllerAdvice
  - Input validation via @Valid

### Spring Data JPA
- **Version**: 3.2.3 (via spring-boot-starter-data-jpa)
- **Purpose**: Data persistence and ORM
- **Usage**:
  - JPA repository interfaces (JpaRepository)
  - Automatic CRUD operation implementations
  - Entity management (@Entity, @Table, @Column)
  - Transaction management
  - Query method generation from method names
- **ORM Implementation**: Hibernate (bundled with Spring Data JPA)

### Spring Security
- **Version**: 3.2.3 (via spring-boot-starter-security)
- **Purpose**: Authentication and authorization
- **Usage**:
  - HTTP Basic Authentication
  - Custom UserDetailsService for database-backed authentication
  - Role-based access control (RBAC)
  - SecurityFilterChain configuration
  - CORS configuration
  - Method-level security (@EnableMethodSecurity)

### Jakarta Bean Validation
- **Version**: 3.0.x (via spring-boot-starter-validation)
- **Purpose**: Request and domain object validation
- **Usage**:
  - @NotNull, @Valid annotations for DTO validation
  - Automatic validation in controller methods
  - Custom validation messages

### SpringDoc OpenAPI
- **Version**: 2.3.0
- **Purpose**: API documentation generation
- **Usage**:
  - Automatic OpenAPI 3.0 specification generation
  - Swagger UI for interactive API exploration
  - Annotation-based API documentation
  - Accessible at /swagger-ui.html and /v3/api-docs

## Infrastructure

### H2 Database
- **Version**: Managed by Spring Boot (latest compatible version)
- **Purpose**: In-memory relational database for development and testing
- **Configuration**:
  - JDBC URL: `jdbc:h2:mem:userdb`
  - Driver: `org.h2.Driver`
  - Credentials: username=sa, password=(empty)
- **Features Used**:
  - In-memory storage (data lost on restart)
  - SQL compatibility
  - Web console for database inspection (/h2-console)
- **Note**: Suitable for development/testing only - **NOT for production**

### Apache Tomcat (Embedded)
- **Version**: Managed by Spring Boot 3.2.3
- **Purpose**: Embedded servlet container for serving REST API
- **Configuration**: 
  - Default port: 8080
  - Configured via Spring Boot auto-configuration
- **Usage**: HTTP server for REST endpoints

### Docker
- **Version**: Multi-stage build using official images
- **Purpose**: Application containerization for deployment
- **Images Used**:
  - Build stage: `maven:3.9-eclipse-temurin-21-alpine`
  - Runtime stage: `eclipse-temurin:21-jre-alpine`
- **Configuration**: Dockerfile at repository root
- **Exposed Port**: 8080

### Spring Boot Actuator
- **Version**: 3.2.3 (via spring-boot-starter-actuator)
- **Purpose**: Production-ready monitoring and management
- **Endpoints Available**:
  - `/actuator/health` - Application health status
  - `/actuator/info` - Application information
  - Additional endpoints for metrics, environment, etc.
- **Access**: Public (no authentication required per SecurityConfig)

## Build Tools

### Maven 3.9
- **Version**: 3.9
- **Purpose**: Build automation and dependency management
- **Configuration**: pom.xml
- **Parent POM**: spring-boot-starter-parent:3.2.3
- **Key Plugins**:
  - spring-boot-maven-plugin - Creates executable JAR with embedded Tomcat
- **Build Process**:
  - Dependency resolution
  - Compilation of Java 21 source
  - Test execution (JUnit 5)
  - Packaging as executable JAR

### Spring Boot Maven Plugin
- **Version**: 3.2.3 (managed by Spring Boot parent)
- **Purpose**: Package application as executable JAR
- **Features**:
  - Embed all dependencies
  - Create fully executable JAR
  - Include embedded Tomcat
  - Support for layered JARs

## Testing Tools

### JUnit 5 (Jupiter)
- **Version**: Managed by spring-boot-starter-test
- **Purpose**: Unit and integration test framework
- **Usage**:
  - @Test annotation for test methods
  - @BeforeEach for test setup
  - Lifecycle management
  - Assertions and assumptions

### Mockito
- **Version**: Managed by spring-boot-starter-test
- **Purpose**: Mocking framework for unit tests
- **Usage**:
  - @Mock for creating mock objects
  - @InjectMocks for dependency injection in tests
  - @ExtendWith(MockitoExtension.class) for Mockito integration
- **Current Usage**: UserServiceTest uses Mockito to mock UserRepository

### Spring Boot Test
- **Version**: 3.2.3 (spring-boot-starter-test)
- **Purpose**: Integration testing support
- **Usage**:
  - @SpringBootTest for full application context loading
  - @AutoConfigureMockMvc for MockMvc setup
  - Test slices (@WebMvcTest, @DataJpaTest, etc.)
- **Current Usage**: UserControllerTest uses @SpringBootTest

### MockMvc
- **Version**: Bundled with Spring Test
- **Purpose**: REST controller testing without starting HTTP server
- **Usage**:
  - Simulate HTTP requests
  - Test controller endpoints
  - Verify responses
- **Current Usage**: Autowired in UserControllerTest

### AssertJ
- **Version**: Bundled with spring-boot-starter-test
- **Purpose**: Fluent assertions for tests
- **Usage**: `assertThat(...)` fluent assertion syntax

### Spring Security Test
- **Version**: Managed by Spring Boot
- **Purpose**: Testing security configurations
- **Usage**: Test security filters, authentication, and authorization

## Additional Dependencies

### Jackson (JSON Processing)
- **Version**: Managed by Spring Boot (via spring-boot-starter-web)
- **Purpose**: JSON serialization and deserialization
- **Usage**:
  - Automatic conversion of Java objects to JSON responses
  - Parsing JSON requests to Java objects
  - Configured via Spring Boot auto-configuration

### SLF4J + Logback
- **Version**: Managed by Spring Boot
- **Purpose**: Logging framework
- **Usage**: 
  - Default logging implementation for Spring Boot
  - Configured via application.yml (if needed)
- **Current State**: No explicit logging configuration visible

### Hibernate
- **Version**: Bundled with spring-boot-starter-data-jpa
- **Purpose**: JPA implementation (ORM)
- **Configuration**:
  - DDL strategy: `create-drop` (recreate schema on startup)
  - Show SQL: `false` (SQL logging disabled)
- **Usage**: Entity persistence, query generation, transaction management

## Documentation Tools

### MkDocs
- **Configuration**: mkdocs.yaml present
- **Purpose**: Generate static documentation site
- **Usage**: Documentation generation (likely for GitHub Pages or similar)

### Python (for docs)
- **Configuration**: pyproject.toml, pytest.ini
- **Purpose**: Support documentation build process
- **Usage**: MkDocs is Python-based

## Development Tools Support

### IDE Integration
- **Spring Boot DevTools**: Not included (could be added for hot reloading)
- **Lombok**: Not used (Java records used instead for DTOs)
- **MapStruct**: Not used (manual DTO mapping via factory methods)

## Technology Stack Summary Table

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Java | 21 (LTS) | Application development |
| **Core Framework** | Spring Boot | 3.2.3 | Application framework |
| **Web** | Spring Web (MVC) | 3.2.3 | REST API |
| **Data Access** | Spring Data JPA | 3.2.3 | ORM and repositories |
| **ORM** | Hibernate | (bundled) | JPA implementation |
| **Security** | Spring Security | 3.2.3 | Auth & authz |
| **Validation** | Jakarta Bean Validation | 3.0.x | Input validation |
| **Database** | H2 | (latest) | In-memory database (dev/test) |
| **Web Server** | Apache Tomcat | (embedded) | Servlet container |
| **API Docs** | SpringDoc OpenAPI | 2.3.0 | OpenAPI/Swagger |
| **Monitoring** | Spring Boot Actuator | 3.2.3 | Health checks, metrics |
| **Build** | Maven | 3.9 | Build automation |
| **Container** | Docker | (latest) | Containerization |
| **Testing** | JUnit 5 | (bundled) | Test framework |
| **Mocking** | Mockito | (bundled) | Mocking for tests |
| **Assertions** | AssertJ | (bundled) | Fluent assertions |
| **Test Integration** | Spring Boot Test | 3.2.3 | Integration testing |
| **JSON** | Jackson | (bundled) | JSON processing |
| **Logging** | SLF4J + Logback | (bundled) | Logging |

## Architecture Patterns Supported

- **Layered Architecture**: Clear separation of concerns (controller, service, repository)
- **Repository Pattern**: Spring Data JPA repositories
- **Dependency Injection**: Spring IoC container
- **DTO Pattern**: Java records for data transfer
- **REST API**: Spring Web MVC
- **ORM**: JPA/Hibernate for object-relational mapping
- **Global Exception Handling**: @RestControllerAdvice pattern

## Production Readiness Assessment

### ✅ Production-Ready Components
- Spring Boot 3.2.3 (LTS support until 2025+)
- Java 21 (LTS until 2029)
- Spring Security (enterprise-grade security)
- Docker containerization
- Spring Boot Actuator (monitoring)
- OpenAPI documentation

### ⚠️ Development-Only Components (Require Changes for Production)
- **H2 Database**: In-memory only - replace with PostgreSQL, MySQL, or similar
- **NoOpPasswordEncoder**: Passwords not hashed - replace with BCryptPasswordEncoder
- **Hardcoded Password**: "password" for all users - implement proper password storage
- **CORS Allow All**: Too permissive - restrict to specific origins
- **DDL Auto Create-Drop**: Database recreated on restart - use `validate` or Flyway/Liquibase migrations

### 🔴 Missing for Production
- External relational database (PostgreSQL, MySQL, etc.)
- Password hashing and secure password storage
- Database migration tool (Flyway or Liquibase)
- Distributed logging (ELK stack, CloudWatch, etc.)
- Distributed tracing (Sleuth, Zipkin, etc.)
- Caching layer (Redis, Caffeine)
- API rate limiting
- HTTPS/TLS configuration
- Environment-specific configurations (dev, staging, prod)
- CI/CD pipeline configuration
