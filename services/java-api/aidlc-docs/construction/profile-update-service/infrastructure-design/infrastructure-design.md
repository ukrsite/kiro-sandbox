# Infrastructure Design - Profile Update Service

## Executive Summary

The Profile Update Service leverages **existing Spring Boot infrastructure** with no new infrastructure services required. This document maps the logical software components from the NFR Design to actual infrastructure choices and documents the complete deployment architecture.

**Key Finding:** This is a brownfield enhancement operating entirely within existing infrastructure. No new cloud services, databases, message queues, or other infrastructure components are required.

---

## 1. Deployment Environment

### 1.1 Deployment Platform: Spring Boot JAR

**Choice:** Standard Spring Boot 3.2.3 JAR application

**Rationale:**
- ✅ Existing deployment model proven in production
- ✅ Single executable JAR includes all dependencies
- ✅ No new deployment platform needed
- ✅ Profile update feature adds to existing JAR

**Deployment Target Options:**
- Local development (IDE, command line)
- Docker container (if containerized)
- Kubernetes (if orchestrated)
- Traditional VM/EC2 instance
- Cloud App Service (AWS Elastic Beanstalk, Azure App Service, GCP App Engine)

**Profile Update Impact:** ZERO - no changes to deployment mechanism

---

### 1.2 Environment Strategy: Multi-Environment Deployment

**Development Environment:**
- Local machine with embedded H2 database
- Spring Boot development profile
- Actuator enabled with all endpoints
- Debug logging enabled

**Testing Environment:**
- Isolated test deployment
- Separate H2 database instance
- Test users and data
- Full Actuator metrics enabled

**Production Environment:**
- Hardened Spring Boot deployment
- PostgreSQL or MySQL (production database)
- Actuator restricted endpoints
- Structured JSON logging
- Performance monitoring enabled

**Profile Update Impact:** Consistent across all environments (same code, same behavior)

---

## 2. Compute Infrastructure

### 2.1 Application Server: Spring Boot Embedded Tomcat

**Choice:** Spring Boot embedded Tomcat servlet container

**Specifications:**
- Embedded in Spring Boot JAR (default)
- Automatic configuration via Spring Boot
- Connection pooling: HikariCP (default 10 connections)
- Thread pool: Default Tomcat settings
- Port: 8080 (configurable)

**Rationale:**
- ✅ Zero configuration complexity
- ✅ Included in Spring Boot BOM (no dependency added)
- ✅ Proven production-ready server
- ✅ Scales horizontally via instance replication

**Profile Update Impact:** 
- Profile update endpoint added to existing server
- Minimal request handler thread overhead (<1ms)
- No compute scaling changes needed

---

### 2.2 Application Scaling: Horizontal Scaling

**Scaling Strategy:** Add Spring Boot instances behind load balancer

```
Load Balancer (AWS ELB, Azure Load Balancer, Nginx, etc.)
├─ Instance 1: Spring Boot (Java 21, <500MB heap)
├─ Instance 2: Spring Boot (Java 21, <500MB heap)
└─ Instance 3: Spring Boot (Java 21, <500MB heap)
    ↓
Single Database (PostgreSQL/H2)
```

**Scaling Trigger:** CPU utilization >70% or response time degradation

**Scaling Characteristics:**
- **Stateless:** Each instance independent (no session replication)
- **Elastic:** Add/remove instances without code changes
- **Load Distribution:** Round-robin or least-connections
- **Session Affinity:** NOT required (stateless design)

**Profile Update Impact:**
- Profile updates are stateless operations
- Enable horizontal scaling without modification
- No session management complexity

---

### 2.3 JVM Configuration

**Java Version:** Java 21 (LTS)

**JVM Heap Configuration (per instance):**

```
Development:    -Xms256m -Xmx512m    (256MB min, 512MB max)
Testing:        -Xms256m -Xmx512m    (256MB min, 512MB max)
Production:     -Xms1g -Xmx2g        (1GB min, 2GB max)
```

**Garbage Collection:**
- Use G1GC (default in Java 21)
- Young generation: ~100-200ms pause time
- Full GC: < 500ms total pause

**Profile Update Impact:** Minimal memory footprint for new components

```
Estimated per-instance memory overhead: <50MB
(UserService, UserController, DTOs, authorization logic)
```

---

## 3. Storage Infrastructure

### 3.1 Database: H2 (Development) / PostgreSQL (Production)

**Development Database:**
- H2 embedded in-memory
- File-based persistence
- Auto-initialization on startup

**Production Database:**
- PostgreSQL 12+ or MySQL 8+
- Separate database server (RDS, Cloud SQL, etc.)
- Automated backups
- Read replicas (optional, not needed for this feature)

**Profile Update Components:**
- User table (existing, no schema changes)
- Indexes: PK (id), Unique (email)
- Constraints: NOT NULL, UNIQUE email

**No New Tables Required:** Profile update operates entirely on existing User entity

---

### 3.2 Connection Pooling: HikariCP

**Configuration:**

```
spring:
  datasource:
    hikari:
      maximum-pool-size: 10
      minimum-idle: 10
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
```

**Connection Pool Characteristics:**

```
Per-Instance: 10 connections
Multi-Instance: 10 connections × number of instances

Example:
- 1 instance:  10 connections (sufficient)
- 2 instances: 20 connections (database supports)
- 3 instances: 30 connections (database must support)
```

**Database Connection Requirements:**
- PostgreSQL: Default max_connections = 100 (sufficient for 5+ instances)
- MySQL: Default max_connections = 150 (sufficient for 10+ instances)
- H2: Unlimited (embedded)

**Profile Update Impact:** Uses standard connection pooling (no changes)

---

### 3.3 Data Persistence Pattern

**Transactional Atomicity:**

```
@Transactional
BEGIN TRANSACTION
├─ SELECT user BY id (1 query, <5ms)
├─ SELECT COUNT(*) FROM user WHERE email != userId (1 query, <5ms)
├─ UPDATE user SET ... WHERE id = userId (1 query, <10ms)
└─ COMMIT (persist to database)
```

**Isolation Level:** READ_COMMITTED (default, sufficient)

**Concurrency:** Optimistic locking via @Version (if needed for simultaneous updates to same user)

---

## 4. Messaging & Event Infrastructure

### 4.1 Messaging: NOT REQUIRED

**Assessment:** Profile update feature does not require messaging infrastructure

**Reasoning:**
- Synchronous request/response pattern
- Single user update operation
- No inter-service communication needed
- No event-driven architecture required

**If Audit Trail Needed (Future):**
- Could add Spring Cloud Stream + Kafka for profile change events
- Currently documented as future enhancement
- No impact on current feature

**Profile Update Impact:** ZERO - messaging not required

---

## 5. Networking Infrastructure

### 5.1 API Gateway / Load Balancer

**Single-Instance Deployment:**
- No load balancer required
- Direct HTTP access to Spring Boot on port 8080
- Optional reverse proxy (Nginx) for SSL termination

**Multi-Instance Deployment:**
- AWS ELB (Elastic Load Balancer)
- Azure Load Balancer
- GCP Load Balancer
- Nginx or HAProxy (on-premise)

**Load Balancing Strategy:**
- Round-robin (default)
- Least connections (recommended for REST APIs)
- No session affinity needed (stateless design)

**Profile Update Impact:**
- `PUT /api/users/{userId}` endpoint routable through any load balancer
- Idempotent operation (safe for retries)
- No session state complexity

---

### 5.2 HTTPS/TLS Configuration

**Requirement:** HTTPS with TLS 1.2+

**Implementation Options:**

**Option 1: Spring Boot Native**
```
server:
  ssl:
    key-store: classpath:keystore.p12
    key-store-password: ${KEYSTORE_PASSWORD}
    key-store-type: PKCS12
```

**Option 2: Reverse Proxy (Recommended)**
- Nginx / HAProxy handles TLS termination
- Spring Boot receives HTTP (internal network)
- Cleaner certificate management

**Option 3: Cloud Provider**
- AWS ACM (Application Load Balancer)
- Azure Application Gateway
- GCP Cloud Load Balancing

**Profile Update Impact:**
- HTTP Basic Auth credentials encrypted in TLS
- No infrastructure changes for this feature

---

### 5.3 CORS Configuration

**Current:** Existing SecurityConfig handles CORS

**If Needed for Cross-Origin Requests:**

```java
@Configuration
public class CorsConfig {
  @Bean
  public WebMvcConfigurer corsConfigurer() {
    return new WebMvcConfigurer() {
      @Override
      public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
          .allowedOrigins("https://app.example.com")
          .allowedMethods("GET", "PUT", "POST", "DELETE")
          .allowCredentials(true);
      }
    };
  }
}
```

**Profile Update Impact:** CORS already configured; PUT method now enabled for profile updates

---

## 6. Monitoring & Observability Infrastructure

### 6.1 Metrics Collection: Spring Actuator

**Built-in Metrics:**

```
/actuator/metrics
├─ http.server.requests (response times, status codes)
├─ process.cpu (CPU utilization)
├─ jvm.memory (heap, GC)
├─ system.load (OS load average)
└─ db.connection.pool (HikariCP metrics)
```

**Profile Update Metrics:**

```
GET /actuator/metrics/http.server.requests
?tag=uri:/api/users/{userId}
?tag=method:PUT
?tag=status:200

Response:
{
  "measurements": [
    {"statistic": "COUNT", "value": 523},
    {"statistic": "TOTAL_TIME", "value": 82_450},
    {"statistic": "MAX", "value": 245},
    {"statistic": "MEAN", "value": 157.6}
  ]
}
```

**Integration with Monitoring Systems:**

```
Spring Boot (Actuator)
    ↓
Prometheus scrapes /actuator/prometheus
    ↓
Time-series database stores metrics
    ↓
Grafana dashboards visualize
    ↓
Alertmanager triggers alerts
```

**Alternative Providers:**
- AWS CloudWatch (via Spring Boot CloudWatch integration)
- Azure Application Insights
- Datadog APM
- New Relic
- Splunk

**Profile Update Impact:** Automatically monitored via existing Actuator

---

### 6.2 Structured Logging: SLF4J + Logback

**Current:** Existing Spring Boot logging configuration

**Profile Update Logs:**

```
[2024-01-15 10:30:00.123] INFO  com.sandbox.userapi.service.UserService
Message: Profile update request
userId: 1
fields: ["name", "email"]
duration: 45ms
result: SUCCESS

[2024-01-15 10:30:00.150] WARN  com.sandbox.userapi.service.UserService
Message: Authorization denied
userId: 2
targetUserId: 1
reason: DIFFERENT_USER
```

**Log Aggregation Integration:**

```
Spring Boot (Logback)
    ↓
Log files / stdout
    ↓
Docker container captures stdout
    ↓
CloudWatch Logs / ELK / Splunk / Datadog
    ↓
Centralized logging dashboard
    ↓
Log search and analysis
```

**JSON Structured Logging (Optional):**

```xml
<!-- logback.xml with JSON appender -->
<appender name="json" class="ch.qos.logback.core.rolling.RollingFileAppender">
  <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
    <!-- Includes all fields in JSON format -->
  </encoder>
</appender>
```

**Profile Update Impact:** Automatically logged via existing Actuator

---

### 6.3 Distributed Tracing: NOT REQUIRED (Currently)

**Assessment:** Profile update feature does not require distributed tracing

**Reasoning:**
- Single service (no inter-service calls)
- Synchronous request/response
- Correlation IDs sufficient for logging

**If Microservices Adopted (Future):**
- Spring Cloud Sleuth for trace generation
- Zipkin or Jaeger for trace collection
- Not needed for monolithic deployment

---

## 7. Infrastructure Mapping: Logical Components to Services

### 7.1 Component-to-Service Mapping

| Logical Component | Infrastructure Service | Deployment Target |
|---|---|---|
| **HTTP Request Interceptor** | Spring Boot Embedded Tomcat | Application Server |
| **DTO Validator** | Spring Boot Bean Validation | Application Runtime |
| **UserController** | Spring Boot Servlet | Application Server |
| **AuthorizationService** | Spring Boot Bean | Application Runtime |
| **EmailValidator** | Spring Boot Bean | Application Runtime |
| **TransactionOrchestrator** | Spring Data JPA + JVM Transaction Manager | Application Runtime |
| **DTOMapper** | Spring Boot Bean | Application Runtime |
| **Indexed Repository** | HikariCP + Hibernate ORM | Database Client |
| **Transaction Manager** | Hibernate / JPA TransactionManager | JVM Runtime |
| **Exception Translator** | Spring Boot DispatcherServlet | Application Runtime |
| **Metrics Collector** | Spring Actuator | Application Runtime |
| **Structured Logger** | SLF4J + Logback | File System / CloudWatch |

---

### 7.2 Infrastructure Stack Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Client (Web Browser / API Client)                       │
│ Sends: HTTP PUT /api/users/{userId}                     │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS (TLS 1.2+)
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Load Balancer (Optional, Multi-Instance Only)           │
│ - AWS ELB / Azure LB / Nginx                            │
│ - Route to Spring Boot instances                        │
│ - SSL termination                                       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP (Internal Network)
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Spring Boot Application Instance (N instances)          │
│ ┌───────────────────────────────────────────────────┐  │
│ │ Java 21 JVM                                       │  │
│ │ - Heap: 512MB-2GB (configurable)                 │  │
│ │ - G1GC Garbage Collector                         │  │
│ │ - Thread pool: Tomcat default                    │  │
│ ├───────────────────────────────────────────────────┤  │
│ │ Spring Boot 3.2.3                                 │  │
│ │ - Embedded Tomcat servlet container               │  │
│ │ - Spring Web MVC                                  │  │
│ │ - Spring Security                                 │  │
│ │ - Spring Data JPA                                 │  │
│ ├───────────────────────────────────────────────────┤  │
│ │ Profile Update Service                            │  │
│ │ - UserController                                  │  │
│ │ - UserService                                     │  │
│ │ - UpdateUserRequest / UserResponse DTOs           │  │
│ ├───────────────────────────────────────────────────┤  │
│ │ Infrastructure                                    │  │
│ │ - Spring Actuator (metrics)                       │  │
│ │ - Logback (structured logging)                    │  │
│ │ - GlobalExceptionHandler                          │  │
│ └───────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ JDBC (Prepared Statements)
                     ▼
┌─────────────────────────────────────────────────────────┐
│ HikariCP Connection Pool (10 connections per instance)  │
│ - Connection pooling                                    │
│ - Connection lifecycle management                       │
│ - Automatic reconnection on failure                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Database (H2 Dev / PostgreSQL Prod)                     │
│ ┌───────────────────────────────────────────────────┐  │
│ │ User Table                                        │  │
│ │ - Columns: id, name, email, role, active         │  │
│ │ - Indexes: PK (id), UQ (email)                    │  │
│ │ - Constraints: NOT NULL, UNIQUE                   │  │
│ └───────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Persistent Storage (File System / Cloud Storage)        │
│ - H2: File-based or in-memory                           │
│ - PostgreSQL/MySQL: Disk-based tables                   │
│ - Automated backups (if cloud database)                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Observability Stack (Optional but Recommended)          │
├─────────────────────────────────────────────────────────┤
│ Spring Actuator → Prometheus/CloudWatch/Datadog        │
│ Logback → CloudWatch Logs/ELK/Splunk/Datadog           │
│ Dashboards and Alerts                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Deployment Configurations

### 8.1 Development Deployment

```yaml
spring:
  application:
    name: user-api
  profiles:
    active: dev
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
    username: sa
    password: 
  jpa:
    hibernate:
      ddl-auto: create-drop
    show-sql: true
    properties:
      hibernate:
        dialect: org.hibernate.dialect.H2Dialect
        
server:
  port: 8080
  
management:
  endpoints:
    web:
      exposure:
        include: "*"  # All endpoints exposed
```

---

### 8.2 Production Deployment

```yaml
spring:
  application:
    name: user-api
  profiles:
    active: prod
  datasource:
    url: jdbc:postgresql://db.prod.example.com:5432/userapi
    username: ${DB_USER}
    password: ${DB_PASSWORD}
    hikari:
      maximum-pool-size: 20
      minimum-idle: 10
  jpa:
    hibernate:
      ddl-auto: validate  # No automatic schema changes
    show-sql: false       # No SQL logging
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQL10Dialect
        jdbc:
          batch_size: 20

server:
  port: 8080
  servlet:
    context-path: /api
  ssl:
    key-store: ${KEYSTORE_PATH}
    key-store-password: ${KEYSTORE_PASSWORD}
    key-store-type: PKCS12
    enabled-protocols: TLSv1.2,TLSv1.3

logging:
  level:
    root: INFO
    com.sandbox.userapi: INFO
  pattern:
    console: "%d{ISO8601} %-5p %c{1} - %msg%n"

management:
  endpoints:
    web:
      exposure:
        include: health,metrics,info
  metrics:
    export:
      cloudwatch:
        enabled: true  # For AWS CloudWatch
```

---

## 9. Infrastructure Requirements & Constraints

### 9.1 Compute Requirements

**Per Instance:**
- **CPU:** 1+ vCPU (2+ recommended)
- **RAM:** 2GB minimum (4GB+ recommended)
- **Disk:** 10GB (for logs, temp files)
- **Network:** 100 Mbps+

**Scaling Parameters:**
- **CPU Trigger:** >70% utilization
- **Memory Trigger:** >80% heap usage
- **Response Time Trigger:** p95 > 300ms

---

### 9.2 Database Requirements

**PostgreSQL:**
- Version: 12+ (recommended 14+)
- Connections: min(10 × instances, 100)
- Storage: 1GB+ (depends on user count)
- Backup: Daily snapshots minimum

**H2 (Development):**
- Embedded in application
- No external setup needed
- File-based persistence

---

### 9.3 Network Requirements

**Ingress:**
- Port 443 (HTTPS, TLS 1.2+)
- Port 8080 (HTTP, internal only)

**Egress:**
- Database connection (port 5432 for PostgreSQL)
- Optional: Monitoring/Logging endpoints

---

### 9.4 Security Infrastructure Requirements

**Network Security:**
- VPC / Private network for database
- Security groups / Network ACLs
- WAF (Web Application Firewall) optional

**Application Security:**
- TLS 1.2+ for HTTPS
- Spring Security for authentication
- No additional security appliances needed

---

## 10. Infrastructure Deployment Checklist

### Pre-Deployment
- [ ] Spring Boot 3.2.3 application built
- [ ] JAR file created and tested
- [ ] Configuration files prepared (application-prod.yml)
- [ ] Database connection tested
- [ ] TLS certificates obtained (if applicable)
- [ ] Load balancer configured (if multi-instance)

### Deployment
- [ ] Deploy Spring Boot JAR to compute instances
- [ ] Start application instances
- [ ] Verify Actuator health endpoint: `GET /actuator/health`
- [ ] Test profile update endpoint: `PUT /api/users/1`
- [ ] Verify metrics available: `GET /actuator/metrics`
- [ ] Verify logs captured

### Post-Deployment
- [ ] Monitor response times (should be <200ms)
- [ ] Monitor error rates (should be <0.1%)
- [ ] Monitor CPU/memory utilization
- [ ] Verify database connections healthy
- [ ] Test failover scenarios

---

## 11. Infrastructure Cost Implications

### Development Environment
- Cost: Minimal (local machine or small VM)
- H2 embedded database (no external service)

### Production Environment (AWS Example)
- **Compute:** EC2 t3.medium (1 instance) = ~$30/month
  - For 3-5 instances: ~$100/month
- **Database:** RDS PostgreSQL db.t3.micro = ~$25/month
  - For production-grade: ~$200+/month
- **Load Balancer:** ALB = ~$15/month
- **Monitoring:** CloudWatch = ~$10/month
- **Total:** ~$50-250/month depending on scale

**Profile Update Impact:** 
- Minimal incremental cost (adds ~5% to compute overhead)
- No new infrastructure services required
- No license costs

---

## Summary: Infrastructure Design Decisions

| Component | Service | Rationale |
|---|---|---|
| Application Runtime | Spring Boot 3.2.3 | Existing, proven |
| Compute | Java 21 JVM + Embedded Tomcat | No changes needed |
| Database | H2 (dev) / PostgreSQL (prod) | Existing setup |
| Connection Pool | HikariCP | Included in Spring Boot |
| Load Balancing | AWS ELB / Nginx / etc. | Optional for scaling |
| Metrics | Spring Actuator | Built-in |
| Logging | SLF4J + Logback | Built-in |
| TLS/HTTPS | Spring Boot / Reverse Proxy | Configurable |
| Messaging | Not Required | Synchronous pattern |
| Caching | Not Required | Simple use case |
| CDN | Not Needed | API, not static content |

**Key Finding:** Profile update feature integrates seamlessly into existing infrastructure with ZERO new infrastructure services required.

---

## Next Steps

1. Verify deployment environment matches this design
2. Prepare configuration files for target environment
3. Set up monitoring dashboards (optional but recommended)
4. Test deployment with existing infrastructure
5. Proceed to Code Generation phase
