# Deployment Architecture - Profile Update Service

## Overview

This document describes the complete deployment architecture for the Profile Update Service across different environments (Development, Testing, Production) and deployment targets (local, Docker, Kubernetes, cloud).

---

## 1. Development Environment Deployment

### 1.1 Local Development Setup

**Purpose:** Developer machine with full debug capabilities

**Architecture:**

```
Developer IDE (IntelliJ, VS Code, Eclipse)
    ↓
Spring Boot Application (embedded Tomcat, port 8080)
    ├─ Spring Security: Test credentials
    └─ Profile Update Service components
    ↓
H2 Database (embedded, in-memory or file-based)
    └─ Initialized with test data
    ↓
Spring Actuator (all endpoints exposed)
    ├─ /actuator/health
    ├─ /actuator/metrics
    └─ /actuator/prometheus
    ↓
SLF4J Logback (console output, DEBUG level)
```

**Configuration:**

```yaml
# application-dev.yml
spring:
  application:
    name: user-api
  profiles:
    active: dev
  datasource:
    url: jdbc:h2:mem:testdb
    initialization-mode: always
  jpa:
    show-sql: true
    hibernate:
      ddl-auto: create-drop

server:
  port: 8080

logging:
  level:
    com.sandbox.userapi: DEBUG
    org.springframework.security: DEBUG
    org.hibernate: DEBUG

management:
  endpoints:
    web:
      exposure:
        include: "*"
  metrics:
    enable:
      all: true
```

**Startup Command:**

```bash
mvn spring-boot:run -Dspring-boot.run.arguments="--spring.profiles.active=dev"
```

**Access:**
- Application: http://localhost:8080
- Health: http://localhost:8080/actuator/health
- Metrics: http://localhost:8080/actuator/metrics
- Credentials: HTTP Basic (configured in properties)

---

### 1.2 Docker Container Development

**Purpose:** Containerized local development matching production deployment

**Dockerfile:**

```dockerfile
FROM openjdk:21-slim

WORKDIR /app

# Copy built JAR
COPY target/user-api-*.jar user-api.jar

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/actuator/health || exit 1

# Start application
ENTRYPOINT ["java", "-jar", "user-api.jar"]

# Override with environment
CMD ["--spring.profiles.active=dev"]
```

**Build and Run:**

```bash
# Build
mvn clean package

# Build Docker image
docker build -t user-api:latest .

# Run container
docker run -d \
  --name user-api-dev \
  -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=dev \
  user-api:latest
```

**Docker Compose (with H2):**

```yaml
version: '3.8'
services:
  user-api:
    build: .
    ports:
      - "8080:8080"
    environment:
      SPRING_PROFILES_ACTIVE: dev
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 2. Testing Environment Deployment

### 2.1 Automated Testing Deployment

**Purpose:** Continuous integration testing with fresh database

**Test Environment:**

```
CI/CD Pipeline (GitHub Actions, GitLab CI, Jenkins)
    ↓
Checkout source code
    ↓
Maven: mvn clean test -Dspring.profiles.active=test
    ├─ Unit tests (JUnit 5 + Mockito)
    ├─ Integration tests (@SpringBootTest with embedded H2)
    └─ Security tests (authorization scenarios)
    ↓
Code coverage report (JaCoCo)
    ↓
Results: Pass/Fail
```

**Test Configuration:**

```yaml
# application-test.yml
spring:
  datasource:
    url: jdbc:h2:mem:testdb;MODE=MySQL
    driver-class-name: org.h2.Driver
  jpa:
    hibernate:
      ddl-auto: create-drop
    properties:
      hibernate:
        format_sql: true

logging:
  level:
    com.sandbox.userapi: INFO
    org.springframework.security: WARN
```

**Maven Command:**

```bash
mvn clean test -Dspring.profiles.active=test
```

---

### 2.2 Integration Testing Deployment

**Purpose:** End-to-end testing with realistic data

**Architecture:**

```
Test Docker Network
├─ user-api container (Spring Boot)
├─ postgres container (PostgreSQL test database)
└─ test runner (Maven/JUnit tests)
```

**Docker Compose for Integration Tests:**

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: userapi_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 10s
      timeout: 5s
      retries: 5

  user-api:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      SPRING_PROFILES_ACTIVE: test
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/userapi_test
      SPRING_DATASOURCE_USERNAME: test
      SPRING_DATASOURCE_PASSWORD: test
    ports:
      - "8080:8080"
```

**Integration Test Run:**

```bash
docker-compose up --abort-on-container-exit
```

---

## 3. Production Environment Deployment

### 3.1 Single-Instance Production Deployment

**Purpose:** Production deployment on single server

**Architecture:**

```
Client (HTTPS)
    ↓
Load Balancer / Reverse Proxy (Nginx)
    ├─ SSL/TLS termination
    ├─ HTTP to Spring Boot (localhost:8080)
    └─ Static content serving (optional)
    ↓
Spring Boot Application (Java 21)
    ├─ Heap: 1-2GB
    ├─ Profile: prod
    └─ Port: 8080 (internal only)
    ↓
Database (PostgreSQL 14+)
    ├─ Connection pool: 10 connections
    ├─ Automated backups
    └─ Persistent storage
    ↓
Logging
    └─ JSON structured logs → CloudWatch/ELK/Splunk
    ↓
Monitoring
    └─ Metrics → CloudWatch/Datadog/Prometheus
```

**Configuration for Production:**

```yaml
# application-prod.yml
spring:
  application:
    name: user-api
  profiles:
    active: prod
  datasource:
    url: ${DB_URL}
    username: ${DB_USER}
    password: ${DB_PASSWORD}
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
  jpa:
    show-sql: false
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQL10Dialect

server:
  port: 8080
  servlet:
    context-path: /api

logging:
  level:
    root: WARN
    com.sandbox.userapi: INFO
  pattern:
    console: '{"timestamp":"%d","level":"%p","logger":"%c","message":"%m"}%n'

management:
  endpoints:
    web:
      exposure:
        include: health,metrics,info
  metrics:
    export:
      prometheus:
        enabled: true
```

**Environment Variables:**

```bash
DB_URL=jdbc:postgresql://prod-db.example.com:5432/userapi
DB_USER=userapi_prod
DB_PASSWORD=<secure-password>
SPRING_PROFILES_ACTIVE=prod
```

---

### 3.2 Multi-Instance Production Deployment (AWS Example)

**Purpose:** Highly available production deployment with load balancing

**Architecture:**

```
Internet
    ↓ HTTPS
AWS CloudFront (optional CDN)
    ↓
AWS Application Load Balancer (ALB)
    ├─ SSL/TLS termination
    ├─ Round-robin load balancing
    ├─ Health checks (/actuator/health)
    └─ Auto-scaling group hooks
    ↓
EC2 Auto Scaling Group (2-5 instances)
├─ Instance 1: Spring Boot (t3.large)
├─ Instance 2: Spring Boot (t3.large)
└─ Instance 3: Spring Boot (t3.large)
    ├─ Each instance:
    │  ├─ Java 21 JVM (2GB heap)
    │  ├─ Spring Boot 3.2.3
    │  ├─ Profile: prod
    │  ├─ HikariCP: 10 connections
    │  └─ Tomcat thread pool: default
    ↓
Amazon RDS (PostgreSQL)
    ├─ Instance class: db.t3.medium or larger
    ├─ Multi-AZ deployment (for HA)
    ├─ Automated backups (7 days retention)
    ├─ Read replicas (optional)
    └─ 20-50 connection limit
    ↓
Amazon CloudWatch
    ├─ Logs: Spring Boot logs aggregated
    ├─ Metrics: Response times, error rates
    ├─ Alarms: Trigger on thresholds
    └─ Dashboards: Real-time visibility
```

**CloudFormation Template (Simplified):**

```yaml
Resources:
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Subnets: [subnet1, subnet2]
      SecurityGroups: [sg-alb]

  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      LaunchTemplate: !Ref LaunchTemplate
      MinSize: 2
      MaxSize: 5
      DesiredCapacity: 2
      TargetGroupARNs:
        - !Ref TargetGroup
      VPCZoneIdentifier: [subnet1, subnet2]

  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateData:
        ImageId: ami-0c55b159cbfafe1f0  # Amazon Linux 2
        InstanceType: t3.large
        IamInstanceProfile: 
          Arn: !GetAtt EC2InstanceProfile.Arn
        UserData:
          Fn::Base64: |
            #!/bin/bash
            yum update -y
            yum install java-21-amazon-corretto-devel -y
            aws s3 cp s3://my-bucket/user-api.jar .
            java -jar user-api.jar \
              --spring.profiles.active=prod \
              --server.port=8080 &

  RDSDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      Engine: postgres
      EngineVersion: '14'
      DBInstanceClass: db.t3.medium
      AllocatedStorage: '20'
      DBName: userapi
      MasterUsername: userapi_prod
      MultiAZ: true
      BackupRetentionPeriod: 7
      StorageEncryption: true
      EnableCloudwatchLogsExports:
        - postgresql

  ScalingPolicy:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AdjustmentType: ChangeInCapacity
      AutoScalingGroupName: !Ref AutoScalingGroup
      PolicyType: TargetTrackingScaling
      TargetTrackingConfiguration:
        PredefinedMetricSpecification:
          PredefinedMetricType: ASGAverageCPUUtilization
        TargetValue: 70.0
```

---

### 3.3 Kubernetes Production Deployment

**Purpose:** Container orchestration for production

**Kubernetes Architecture:**

```
Kubernetes Cluster
├─ Ingress (Nginx Ingress Controller)
│  ├─ TLS termination
│  └─ Route /api/* to user-api service
├─ Service (ClusterIP)
│  └─ user-api:8080
├─ Deployment (Replicas: 2-5)
│  ├─ Pod 1: user-api container
│  ├─ Pod 2: user-api container
│  └─ Pod N: user-api container
│     ├─ Resource requests: CPU 500m, Memory 512Mi
│     ├─ Resource limits: CPU 1000m, Memory 2Gi
│     ├─ Health probe: /actuator/health
│     └─ Liveness probe: Restart if unhealthy
└─ ConfigMap
   ├─ application-prod.yml
   └─ Environment variables
```

**Kubernetes Manifest:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-api
  template:
    metadata:
      labels:
        app: user-api
    spec:
      containers:
      - name: user-api
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/user-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "prod"
        - name: SPRING_DATASOURCE_URL
          valueFrom:
            configMapKeyRef:
              name: user-api-config
              key: db.url
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: user-api
spec:
  selector:
    app: user-api
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: user-api
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: user-api-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: user-api
            port:
              number: 8080
```

---

## 4. Deployment Procedures

### 4.1 Deployment Checklist

**Pre-Deployment:**
- [ ] Code reviewed and merged to main branch
- [ ] All tests passing (unit, integration, security)
- [ ] Code coverage >85%
- [ ] Performance validated (<200ms response time)
- [ ] Security scan passed (no vulnerabilities)
- [ ] Database schema validated (no migrations needed)
- [ ] Configuration files prepared
- [ ] Rollback plan documented

**Deployment:**
- [ ] Package application: `mvn clean package`
- [ ] Build Docker image (if containerized)
- [ ] Push image to registry (ECR/Docker Hub/etc.)
- [ ] Deploy to staging for final validation
- [ ] Health checks pass on staging
- [ ] Deploy to production
- [ ] Verify health endpoint responding
- [ ] Smoke test profile update endpoint
- [ ] Monitor metrics for 10 minutes

**Post-Deployment:**
- [ ] Monitor CPU, memory, response times
- [ ] Monitor error rates (<0.1%)
- [ ] Monitor database connections
- [ ] Verify logging working
- [ ] Verify metrics collection working
- [ ] Document deployment in runbook

---

### 4.2 Rollback Procedure

**If Deployment Issues Detected:**

```bash
# Step 1: Identify issue
# - High error rate (>1%)
# - High response time (p95 > 500ms)
# - Health checks failing

# Step 2: Initiate rollback
# For Docker/K8s: Revert to previous image
docker pull user-api:v1.2.3  # Previous stable version
docker run -d --name user-api user-api:v1.2.3

# For AWS Elastic Beanstalk:
eb deploy --version=app-v1.2.3

# For Kubernetes:
kubectl rollout undo deployment/user-api

# Step 3: Verify rollback
curl http://localhost:8080/actuator/health

# Step 4: Analyze root cause
# - Check logs
# - Review metrics
# - Debug in staging environment
```

---

## 5. Monitoring & Observability Setup

### 5.1 Metrics Monitoring

**Key Metrics for Profile Update:**

```
http.server.requests (histogram)
├─ Count: Total requests
├─ Duration: Response time (min, max, mean, p95, p99)
├─ Tags:
│  ├─ uri: /api/users/{userId}
│  ├─ method: PUT
│  └─ status: 200, 400, 403, 404, 409, 500
└─ Alarms:
   ├─ p95 > 300ms: Warning
   ├─ p95 > 500ms: Critical
   └─ Error rate > 1%: Critical

jvm.memory (gauge)
├─ Heap used / max
├─ GC pause time
└─ Alert: Heap > 80%

db.connection.pool (gauge)
├─ Active connections
├─ Idle connections
└─ Alert: Active > 8 (of 10)
```

---

### 5.2 Log Monitoring

**Structured Logging Pattern:**

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "com.sandbox.userapi.service.UserService",
  "message": "Profile update request",
  "userId": 1,
  "fields": ["name", "email"],
  "authenticatedUserId": 1,
  "isAdmin": false,
  "result": "SUCCESS",
  "duration": 45,
  "unit": "ms"
}
```

**Log Search Examples (CloudWatch/ELK):**

```
# Find all profile update errors
fields @timestamp, userId, message
| filter logger = "UserService" and level = "ERROR"
| stats count() by message

# Find slow profile updates
fields @timestamp, userId, duration
| filter logger = "UserService" and duration > 200
| stats avg(duration), max(duration) by userId

# Find authorization failures
fields @timestamp, userId
| filter message = "Authorization denied"
| stats count() by userId
```

---

## 6. Deployment Summary

| Aspect | Development | Testing | Production |
|--------|---|---|---|
| **Database** | H2 embedded | H2 in-memory | PostgreSQL RDS |
| **Instances** | 1 (local) | 1 (test) | 2-5 (auto-scaling) |
| **Load Balancer** | None | None | AWS ALB |
| **TLS/HTTPS** | Optional | Optional | Required |
| **Monitoring** | Local logs | CI/CD | CloudWatch/Datadog |
| **Backup** | None | None | Automated RDS snapshots |
| **High Availability** | N/A | N/A | Multi-AZ, auto-scaling |
| **Disaster Recovery** | N/A | N/A | RTO: 1 hour, RPO: 1 hour |

---

## Next Steps

1. Verify target infrastructure matches design
2. Prepare environment-specific configuration files
3. Set up monitoring dashboards in target platform
4. Validate deployment procedures in staging
5. Document any environment-specific variations
6. Proceed to Code Generation phase
