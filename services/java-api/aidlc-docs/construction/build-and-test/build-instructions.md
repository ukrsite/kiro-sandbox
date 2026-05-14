# Build Instructions - Profile Update Service

## Project Information

**Project Type**: Spring Boot 3.2 Monolithic Java Application  
**Build Tool**: Maven  
**Language**: Java 21  
**Package Manager**: Maven Central Repository

---

## Prerequisites

### System Requirements
- **JDK**: Java 21 (OpenJDK or Oracle JDK)
- **Maven**: 3.8.1 or higher
- **Git**: Version control (if cloning repository)
- **RAM**: Minimum 2GB for build process
- **Disk Space**: At least 2GB for dependencies and build artifacts

### Verify Prerequisites
```bash
# Check Java version
java -version

# Check Maven version
mvn -version

# Expected output:
# Java 21.x.x (or higher)
# Maven 3.8.1 (or higher)
```

---

## Dependencies

### Main Dependencies (Existing in pom.xml)
- **Spring Boot**: 3.2.3
- **Spring Data JPA**: For ORM and repository layer
- **Spring Security**: For authentication and authorization
- **Jakarta Bean Validation**: For input validation
- **H2 Database**: In-memory database for development/testing

### Test Dependencies (Used in Tests)
- **JUnit 5**: Testing framework
- **Mockito**: Mocking library for unit tests
- **Spring Boot Test**: Integration testing framework
- **Spring Security Test**: Security context testing

### No New Dependencies Added
The implementation uses only existing dependencies already configured in the project's `pom.xml` file.

---

## Build Steps

### Step 1: Verify Repository Status

```bash
# Navigate to project directory
cd /home/sk/vscode/aws-sagents-dlc/kiro-sandbox/services/java-api

# Check git status (if using version control)
git status

# Expected: Working directory clean or changes staged
```

### Step 2: Clean Previous Build Artifacts

```bash
# Clean all previous build artifacts
mvn clean

# Expected Output:
# [INFO] Scanning for projects...
# [INFO] --------< com.sandbox:userapi >--------
# [INFO] Building User API 1.0.0
# [INFO] [clean:clean]
# [INFO] Deleting directory: .../target
# [INFO] BUILD SUCCESS
```

### Step 3: Resolve Dependencies

```bash
# Resolve and download all dependencies
mvn dependency:resolve

# Expected Output:
# [INFO] Resolving org.springframework.boot:spring-boot:jar:3.2.3
# [INFO] Resolving org.springframework.security:spring-security-core:jar:6.1.0
# ... (many dependency resolutions)
# [INFO] BUILD SUCCESS
```

### Step 4: Compile Source Code

```bash
# Compile all source code (main + test)
mvn compile

# Expected Output:
# [INFO] --- compiler:3.11.0:compile (default-compile)
# [INFO] Compiling 15 source files to .../target/classes
# [INFO] BUILD SUCCESS
```

### Step 5: Run Unit Tests

```bash
# Execute all unit tests
mvn test

# Expected Output:
# [INFO] --- surefire:3.0.0:test (default-test)
# [INFO] Tests run: 18, Failures: 0, Errors: 0, Skipped: 0
# [INFO] BUILD SUCCESS
```

### Step 6: Build Application Package

```bash
# Create executable JAR file
mvn package

# Expected Output:
# [INFO] --- jar:3.3.0:jar (default-jar)
# [INFO] Building jar: .../target/userapi-1.0.0.jar
# [INFO] BUILD SUCCESS
```

### Step 7: Build Complete

```bash
# Verify build artifacts exist
ls -la target/

# Expected Output:
# userapi-1.0.0.jar (main application JAR)
# userapi-1.0.0.jar.original (original JAR before spring-boot repackaging)
# classes/ (compiled classes directory)
# test-classes/ (compiled test classes directory)
```

---

## Full Build Command (All Steps)

```bash
# Clean build with all steps included
mvn clean compile test package

# Or use the standard Maven build lifecycle
mvn clean install

# This automatically runs:
# 1. Clean
# 2. Compile
# 3. Test (runs unit tests + generates test reports)
# 4. Package (creates JAR file)
# 5. Install (installs to local Maven repository)
```

---

## Build Output Artifacts

### Main Artifacts
- **Target Directory**: `target/`
- **Application JAR**: `target/userapi-1.0.0.jar`
- **Compiled Classes**: `target/classes/`

### Test Reports
- **Test Results**: `target/surefire-reports/`
- **Test HTML Report**: `target/surefire-reports/index.html` (if generated)
- **Code Coverage**: `target/site/jacoco/index.html` (if coverage enabled)

### Dependency Report
- **Resolved Dependencies**: `target/dependency/` (if extracted)

---

## Build Verification

### Verify Build Success
```bash
# Check exit code (0 = success)
echo $?

# List main artifacts
ls -lh target/*.jar

# Expected:
# 0 (exit code)
# -rw-r--r--  userapi-1.0.0.jar (size: ~40-50MB)
```

### Verify JAR Contents
```bash
# Inspect JAR file contents
jar tf target/userapi-1.0.0.jar | grep -E "(UserController|UserService|UpdateUserRequest)" | head -20

# Expected: Compiled classes for modified components
# BOOT-INF/classes/com/sandbox/userapi/controller/UserController.class
# BOOT-INF/classes/com/sandbox/userapi/service/UserService.class
# BOOT-INF/classes/com/sandbox/userapi/dto/UpdateUserRequest.class
```

---

## Run Application

### Option 1: Run from JAR
```bash
# Start Spring Boot application
java -jar target/userapi-1.0.0.jar

# Expected Output:
# 2024-01-15 10:30:45.123  INFO 12345 --- [main] c.s.u.UserApiApplication: Starting UserApiApplication
# ...
# 2024-01-15 10:30:48.456  INFO 12345 --- [main] c.s.u.UserApiApplication: Started UserApiApplication in 3.333 seconds
# Tomcat initialized with port(s): 8080 (http)
```

### Option 2: Run from IDE
In IntelliJ IDEA or Eclipse:
1. Right-click `UserApiApplication.java`
2. Select `Run 'UserApiApplication.main()'`
3. Application starts on `http://localhost:8080`

### Option 3: Run with Maven
```bash
# Run Spring Boot application via Maven
mvn spring-boot:run
```

---

## Troubleshooting

### Build Fails with Compilation Error

**Error**: `[ERROR] ... cannot find symbol`

**Cause**: Missing imports or incorrect class references

**Solution**:
1. Check import statements in the error message
2. Verify class names and packages match existing code
3. Run `mvn clean` and retry
4. Check for typos in generated code

### Build Fails with Dependency Resolution Error

**Error**: `[ERROR] Failed to execute goal on project userapi`  
**Cause**: Maven cannot download dependencies

**Solution**:
```bash
# Clear Maven cache
rm -rf ~/.m2/repository

# Retry build with offline flag disabled
mvn -U clean install

# Or configure Maven settings.xml for correct mirror/proxy
```

### Build Fails with Test Execution Error

**Error**: `[ERROR] Tests run: X, Failures: Y`

**Cause**: Unit tests are failing

**Solution**:
```bash
# Run tests with verbose output
mvn test -X

# Run specific failing test
mvn test -Dtest=UserServiceUpdateUserTest#testUpdateUser_SelfUpdateNameAsRegularUser_Success

# See detailed test output
mvn surefire:test -DfileReports=
```

### Build Fails with OutOfMemoryError

**Error**: `java.lang.OutOfMemoryError: Java heap space`

**Cause**: Build process needs more memory

**Solution**:
```bash
# Increase Maven memory
export MAVEN_OPTS="-Xmx1024m -XX:MaxPermSize=512m"

# Or set permanently in ~/.bashrc or ~/.bash_profile
echo 'export MAVEN_OPTS="-Xmx1024m"' >> ~/.bashrc
source ~/.bashrc

# Retry build
mvn clean install
```

### IDE Shows Build Errors But Maven Build Succeeds

**Cause**: IDE configuration out of sync with Maven

**Solution**:
```bash
# Reimport Maven project in IDE
# IntelliJ: File → Invalidate Caches → Restart
# Eclipse: Project → Clean → Rebuild

# Or manually refresh:
mvn idea:clean idea:idea    # For IntelliJ
mvn eclipse:clean eclipse:eclipse  # For Eclipse
```

---

## Build Configuration

### Maven Build Configuration
**File**: `pom.xml` (existing, no changes needed)

Key sections:
- `<properties>`: Java version (21), Spring Boot version (3.2.3)
- `<dependencies>`: All project dependencies (unchanged)
- `<build>`: Maven plugins configuration
- `<plugins>`: Spring Boot Maven plugin for creating executable JAR

### Java Compiler Configuration
```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-compiler-plugin</artifactId>
    <version>3.11.0</version>
    <configuration>
        <source>21</source>
        <target>21</target>
    </configuration>
</plugin>
```

### Spring Boot Plugin
```xml
<plugin>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-maven-plugin</artifactId>
    <version>3.2.3</version>
</plugin>
```

---

## Build Best Practices

### 1. Always Clean Before Full Rebuild
```bash
mvn clean install
```

### 2. Use Dependency Tree for Troubleshooting
```bash
# Visualize dependency tree
mvn dependency:tree

# Check for conflicts
mvn dependency:tree -Dverbose
```

### 3. Skip Tests During Development (Use Cautiously)
```bash
# Skip tests to speed up build (NOT RECOMMENDED)
mvn clean install -DskipTests

# Only skip integration tests
mvn clean install -DskipITs
```

### 4. Check for Security Vulnerabilities
```bash
# Scan dependencies for known vulnerabilities
mvn org.owasp:dependency-check-maven:check
```

### 5. Update Snapshots
```bash
# Force update of snapshot dependencies
mvn clean install -U
```

---

## Performance Optimization

### Parallel Build
```bash
# Build with parallel threads (faster)
mvn -T 1C clean install

# T 1C = 1 thread per core
```

### Offline Build (If Dependencies Already Downloaded)
```bash
mvn -o clean install
```

### Skip Documentation Generation
```bash
# Skip JavaDoc generation if needed
mvn clean install -Dskip.javadoc=true
```

---

## Next Steps

After successful build:
1. ✅ Build completed successfully (all artifacts in `target/`)
2. ✅ Proceed to Unit Test Execution (see unit-test-instructions.md)
3. ✅ Then Integration Tests (see integration-test-instructions.md)
4. ✅ Then Performance Tests (see performance-test-instructions.md)

---

## Summary

**Build Command**: `mvn clean install`  
**Expected Duration**: 2-5 minutes (depends on first-time dependency download)  
**Success Indicator**: `[INFO] BUILD SUCCESS`  
**Main Artifact**: `target/userapi-1.0.0.jar`  
**Next Step**: Execute unit tests
