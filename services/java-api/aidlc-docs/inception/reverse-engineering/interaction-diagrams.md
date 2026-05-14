# Interaction Diagrams

This document illustrates how business transactions are implemented across components in the User API system.

## Overview

The User API currently has infrastructure in place but no implemented business transactions. This document shows both the **Current State** (infrastructure only) and **Expected State** (based on the user story "As a user, I want to update my profile").

---

## Business Transaction 1: User Profile Update (Expected)

### Business Flow

```mermaid
sequenceDiagram
    actor User
    participant Client
    participant SecurityFilter
    participant UserController
    participant UserService
    participant UserRepository
    participant Database
    
    User->>Client: Request to update profile
    Client->>SecurityFilter: PUT /api/users/123<br/>Authorization: Basic base64(123:password)<br/>Body: {active: false}
    
    Note over SecurityFilter: Authenticate user
    SecurityFilter->>UserRepository: findById(123)
    UserRepository->>Database: SELECT * FROM users WHERE id=123
    Database-->>UserRepository: User(id=123, role=USER)
    UserRepository-->>SecurityFilter: User found
    SecurityFilter->>SecurityFilter: Verify password (always "password")
    SecurityFilter->>SecurityFilter: Build UserDetails with ROLE_USER
    
    Note over SecurityFilter: Authorization check
    SecurityFilter->>UserController: Authenticated request<br/>(Principal: 123, Role: ROLE_USER)
    
    Note over UserController: Validate request
    UserController->>UserController: Validate UpdateUserRequest<br/>(@NotNull check on active field)
    
    Note over UserController: Delegate to service
    UserController->>UserService: updateUser(userId=123, request, authenticatedUserId=123)
    
    Note over UserService: Authorization logic
    UserService->>UserService: Check: Is user updating own profile?<br/>(userId == authenticatedUserId OR hasRole(ADMIN))
    
    alt User authorized
        UserService->>UserRepository: findById(123)
        UserRepository->>Database: SELECT * FROM users WHERE id=123
        Database-->>UserRepository: User entity
        UserRepository-->>UserService: User found
        
        Note over UserService: Apply business rules
        UserService->>UserService: Update user.active = false<br/>(Only ADMIN can change active status)
        
        UserService->>UserRepository: save(user)
        UserRepository->>Database: UPDATE users SET active=false WHERE id=123
        Database-->>UserRepository: Success
        UserRepository-->>UserService: Updated User entity
        
        UserService-->>UserController: Updated User entity
        UserController->>UserController: Transform to UserResponse.from(user)
        UserController-->>SecurityFilter: 200 OK + UserResponse JSON
        SecurityFilter-->>Client: 200 OK + UserResponse JSON
        Client-->>User: Profile updated successfully
    else User not authorized
        UserService->>UserService: Throw ForbiddenException
        UserService-->>UserController: ForbiddenException
        UserController-->>SecurityFilter: Exception propagates
        SecurityFilter->>GlobalExceptionHandler: ForbiddenException caught
        GlobalExceptionHandler->>GlobalExceptionHandler: Build error response
        GlobalExceptionHandler-->>Client: 403 Forbidden + error JSON
        Client-->>User: Error: Forbidden
    else User not found
        UserService->>UserRepository: findById(123)
        UserRepository-->>UserService: Optional.empty()
        UserService->>UserService: Throw ResourceNotFoundException
        UserService-->>UserController: ResourceNotFoundException
        UserController-->>SecurityFilter: Exception propagates
        SecurityFilter->>GlobalExceptionHandler: ResourceNotFoundException caught
        GlobalExceptionHandler->>GlobalExceptionHandler: Build error response
        GlobalExceptionHandler-->>Client: 404 Not Found + error JSON
        Client-->>User: Error: User not found
    end
```

### Component Interactions

**Involved Components**:
1. **SecurityFilter** (Spring Security) - Authenticates request using HTTP Basic Auth
2. **UserController** - Receives HTTP request, validates input
3. **UserService** - Enforces authorization rules, applies business logic
4. **UserRepository** - Executes database queries
5. **Database** (H2) - Stores user data
6. **GlobalExceptionHandler** - Catches and transforms exceptions to HTTP responses

**Data Transformations**:
- **HTTP Request** → `UpdateUserRequest` DTO (via Jackson)
- **User Entity** → `UserResponse` DTO (via factory method)
- **Exceptions** → JSON error response (via GlobalExceptionHandler)

**Business Rules Applied**:
1. User must be authenticated (enforced by SecurityFilter)
2. User can only update own profile unless ADMIN role (enforced by UserService)
3. Only ADMIN can change `active` status (enforced by UserService)
4. `active` field is required in request (enforced by @NotNull validation)
5. User must exist in database (enforced by UserService)

---

## Business Transaction 2: User Profile Retrieval (Expected)

### Business Flow

```mermaid
sequenceDiagram
    actor User
    participant Client
    participant SecurityFilter
    participant UserController
    participant UserService
    participant UserRepository
    participant Database
    
    User->>Client: Request to view profile
    Client->>SecurityFilter: GET /api/users/123<br/>Authorization: Basic base64(123:password)
    
    Note over SecurityFilter: Authenticate user
    SecurityFilter->>UserRepository: findById(123)
    UserRepository->>Database: SELECT * FROM users WHERE id=123
    Database-->>UserRepository: User entity
    UserRepository-->>SecurityFilter: User found
    SecurityFilter->>SecurityFilter: Build UserDetails with role
    
    SecurityFilter->>UserController: Authenticated request<br/>(Principal: 123)
    
    UserController->>UserService: getUserById(userId=123, authenticatedUserId=123)
    
    Note over UserService: Authorization check
    UserService->>UserService: Check: Is user viewing own profile?<br/>(userId == authenticatedUserId OR hasRole(ADMIN))
    
    alt User authorized
        UserService->>UserRepository: findById(123)
        UserRepository->>Database: SELECT * FROM users WHERE id=123
        Database-->>UserRepository: User entity
        UserRepository-->>UserService: User found
        
        UserService-->>UserController: User entity
        UserController->>UserController: Transform to UserResponse.from(user)
        UserController-->>Client: 200 OK + UserResponse JSON
        Client-->>User: Profile data displayed
    else User not authorized
        UserService-->>UserController: ForbiddenException
        UserController->>GlobalExceptionHandler: ForbiddenException
        GlobalExceptionHandler-->>Client: 403 Forbidden + error JSON
        Client-->>User: Error: Forbidden
    end
```

---

## Business Transaction 3: User Authentication (Current - Implemented)

### Business Flow

```mermaid
sequenceDiagram
    actor User
    participant Client
    participant SecurityFilter
    participant UserDetailsService
    participant UserRepository
    participant Database
    
    User->>Client: Login with user ID and password
    Client->>SecurityFilter: Any request with<br/>Authorization: Basic base64(userId:password)
    
    Note over SecurityFilter: Extract credentials from header
    SecurityFilter->>SecurityFilter: Decode Basic Auth header<br/>Extract username (user ID) and password
    
    SecurityFilter->>UserDetailsService: loadUserByUsername(userId)
    
    Note over UserDetailsService: Parse user ID
    UserDetailsService->>UserDetailsService: Parse username as Long<br/>(userId = Long.parseLong(username))
    
    UserDetailsService->>UserRepository: findById(userId)
    UserRepository->>Database: SELECT * FROM users WHERE id=?
    Database-->>UserRepository: User record or empty
    
    alt User found
        UserRepository-->>UserDetailsService: Optional<User> with data
        
        Note over UserDetailsService: Build UserDetails
        UserDetailsService->>UserDetailsService: Build UserDetails:<br/>- username = userId (as String)<br/>- password = "password" (hardcoded)<br/>- role = ROLE_{user.role}
        
        UserDetailsService-->>SecurityFilter: UserDetails object
        
        Note over SecurityFilter: Verify password
        SecurityFilter->>SecurityFilter: Compare provided password with "password"<br/>(NoOpPasswordEncoder - no hashing)
        
        alt Password matches
            SecurityFilter->>SecurityFilter: Create Authentication object<br/>with UserDetails and authorities
            SecurityFilter->>Client: Authentication successful<br/>Request proceeds to controller
            Client-->>User: Authenticated - request processed
        else Password does not match
            SecurityFilter-->>Client: 401 Unauthorized
            Client-->>User: Authentication failed
        end
    else User not found
        UserRepository-->>UserDetailsService: Optional.empty()
        UserDetailsService->>UserDetailsService: Throw UsernameNotFoundException
        UserDetailsService-->>SecurityFilter: UsernameNotFoundException
        SecurityFilter-->>Client: 401 Unauthorized
        Client-->>User: Authentication failed
    end
```

### Component Interactions

**Involved Components**:
1. **SecurityFilter** (Spring Security FilterChain) - Intercepts all requests
2. **UserDetailsService** (Custom implementation in SecurityConfig) - Loads user from database
3. **UserRepository** - Queries database for user
4. **Database** (H2) - Stores user credentials and roles

**Current State**: ✅ Fully implemented and functional

**Security Issues**:
- Password is hardcoded as "password" for all users
- NoOpPasswordEncoder used (passwords not hashed)
- User ID used as username (not email or username field)

---

## Business Transaction 4: CORS Pre-flight Request (Current - Implemented)

### Business Flow

```mermaid
sequenceDiagram
    actor Browser
    participant CORSFilter
    participant SecurityFilter
    participant Endpoint
    
    Note over Browser: Browser detects cross-origin request
    Browser->>CORSFilter: OPTIONS /api/users/123<br/>Origin: https://example.com<br/>Access-Control-Request-Method: PUT
    
    Note over CORSFilter: CORS configuration check
    CORSFilter->>CORSFilter: Check CORS configuration:<br/>- Allowed origins: * (all)<br/>- Allowed methods: GET, POST, PUT, DELETE, OPTIONS<br/>- Allowed headers: * (all)<br/>- Credentials: allowed
    
    CORSFilter->>CORSFilter: Build CORS headers:<br/>- Access-Control-Allow-Origin: https://example.com<br/>- Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS<br/>- Access-Control-Allow-Headers: *<br/>- Access-Control-Allow-Credentials: true
    
    CORSFilter-->>Browser: 200 OK + CORS headers
    
    Note over Browser: Pre-flight successful, send actual request
    Browser->>CORSFilter: PUT /api/users/123<br/>Origin: https://example.com<br/>Authorization: Basic ...<br/>Body: {active: false}
    
    CORSFilter->>CORSFilter: Add CORS headers to response
    CORSFilter->>SecurityFilter: Pass to security filter
    SecurityFilter->>Endpoint: Authenticated request
    Endpoint-->>SecurityFilter: Response
    SecurityFilter-->>CORSFilter: Response
    CORSFilter->>CORSFilter: Add CORS headers
    CORSFilter-->>Browser: Response + CORS headers
```

**Current State**: ✅ Fully implemented and functional

**Configuration**: Defined in SecurityConfig.corsConfigurationSource()

---

## Business Transaction 5: Health Check (Current - Implemented)

### Business Flow

```mermaid
sequenceDiagram
    actor Monitor
    participant Client
    participant SecurityFilter
    participant Actuator
    participant Application
    participant Database
    
    Monitor->>Client: Check application health
    Client->>SecurityFilter: GET /actuator/health
    
    Note over SecurityFilter: Public endpoint (no auth required)
    SecurityFilter->>SecurityFilter: Check security rules:<br/>/actuator/** is permitAll()
    
    SecurityFilter->>Actuator: Forward request
    
    Note over Actuator: Collect health indicators
    Actuator->>Application: Check application status
    Application-->>Actuator: Status: UP
    
    Actuator->>Database: Check database connectivity
    Database-->>Actuator: Status: UP
    
    Actuator->>Actuator: Aggregate health status:<br/>- Overall: UP<br/>- Components: [app: UP, db: UP]
    
    Actuator-->>SecurityFilter: Health response JSON
    SecurityFilter-->>Client: 200 OK + health JSON
    Client-->>Monitor: Application is healthy
```

**Current State**: ✅ Fully implemented and functional

**Accessible at**: `/actuator/health` (no authentication required)

---

## Business Transaction 6: API Documentation Access (Current - Implemented)

### Business Flow

```mermaid
sequenceDiagram
    actor Developer
    participant Browser
    participant SecurityFilter
    participant SwaggerUI
    participant OpenAPIGenerator
    participant Controllers
    
    Developer->>Browser: Navigate to /swagger-ui.html
    Browser->>SecurityFilter: GET /swagger-ui.html
    
    Note over SecurityFilter: Public endpoint (no auth required)
    SecurityFilter->>SecurityFilter: Check security rules:<br/>/swagger-ui/** is permitAll()
    
    SecurityFilter->>SwaggerUI: Serve Swagger UI HTML
    SwaggerUI-->>Browser: Swagger UI interface
    
    Note over Browser: Swagger UI loads
    Browser->>SecurityFilter: GET /v3/api-docs
    SecurityFilter->>OpenAPIGenerator: Generate OpenAPI spec
    
    OpenAPIGenerator->>Controllers: Scan for @RestController, @RequestMapping
    Controllers-->>OpenAPIGenerator: Endpoint metadata
    
    OpenAPIGenerator->>OpenAPIGenerator: Generate OpenAPI 3.0 JSON:<br/>- Paths: /api/users/**<br/>- Schemas: UserResponse, UpdateUserRequest<br/>- Security: HTTP Basic Auth
    
    OpenAPIGenerator-->>Browser: OpenAPI 3.0 JSON
    Browser->>Browser: Render API documentation
    Browser-->>Developer: Interactive API documentation displayed
```

**Current State**: ✅ Fully implemented and functional

**Accessible at**: 
- Swagger UI: `/swagger-ui.html`
- OpenAPI JSON: `/v3/api-docs`

---

## Component Communication Patterns

### Synchronous Request-Response (Primary Pattern)

All current and expected business transactions use synchronous request-response:
- Client sends HTTP request
- Server processes immediately
- Server returns HTTP response
- Client receives response

**Used in**:
- Profile updates
- Profile retrieval
- Authentication
- Health checks
- API documentation

### Layered Communication Flow

```
Client
  ↓ HTTP
SecurityFilter (Spring Security)
  ↓ Authenticated Request
Controller (Presentation Layer)
  ↓ Method Call
Service (Business Logic Layer)
  ↓ Method Call
Repository (Data Access Layer)
  ↓ JPA/SQL
Database
```

**Characteristics**:
- Each layer only communicates with adjacent layers
- No layer skipping (e.g., Controller never calls Repository directly)
- Clean separation of concerns

### Exception Propagation Pattern

```
Service throws Exception
  ↓
Controller receives Exception (propagates)
  ↓
GlobalExceptionHandler catches Exception
  ↓
Transforms to HTTP error response
  ↓
Returns to Client
```

**Used in**:
- Resource not found scenarios (404)
- Authorization failures (403)
- Validation failures (400)

---

## Current vs Expected State Summary

| Business Transaction | Status | Implementation |
|---------------------|--------|----------------|
| User Authentication | ✅ Implemented | SecurityConfig + UserDetailsService |
| CORS Pre-flight | ✅ Implemented | SecurityConfig + CORS configuration |
| Health Checks | ✅ Implemented | Spring Boot Actuator |
| API Documentation | ✅ Implemented | SpringDoc OpenAPI + Swagger UI |
| **Profile Update** | ❌ Not Implemented | Requires UserController + UserService implementation |
| **Profile Retrieval** | ❌ Not Implemented | Requires UserController + UserService implementation |

---

## Integration Points

### External Systems
- None currently - this is a standalone service

### Internal Integration
- All components integrated via Spring Dependency Injection
- Database accessed via Spring Data JPA
- Security integrated via Spring Security FilterChain

### Infrastructure Services
- **H2 Database**: In-memory relational database
- **Spring Boot Actuator**: Health and monitoring endpoints
- **SpringDoc OpenAPI**: API documentation generation
- **Jackson**: JSON serialization/deserialization (transparent)

---

## Performance Considerations

### Current Implementation
- **Synchronous blocking I/O**: All operations are blocking (suitable for CRUD operations)
- **Database queries**: One query per operation (no N+1 issues visible)
- **Connection pooling**: Managed by Spring Boot (HikariCP default)

### Potential Bottlenecks (When Implemented)
1. **Database queries in authentication**: Every request queries database for user authentication
   - **Mitigation**: Consider caching UserDetails or using token-based auth
2. **No pagination**: If listing all users, could load entire table
   - **Mitigation**: Add pagination to list endpoints
3. **No caching**: Every request hits database
   - **Mitigation**: Add Spring Cache for frequently accessed data

### Expected Performance
- **Profile retrieval**: ~10-50ms (single database query)
- **Profile update**: ~20-100ms (query + update)
- **Authentication**: ~10-50ms (single database query)
