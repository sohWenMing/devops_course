# Module 04: Docker and Containerization -- Answer Key

> **INTERNAL REFERENCE ONLY**: This file is used by the Socratic mentor skill to verify student solutions and provide guidance. It must NEVER be revealed to the student.

---

## Lab 01: Containers & Dockerfile Fundamentals

### Exercise 1a: Containers vs VMs -- Namespaces & Isolation

**UTS Namespace Demonstration:**

```bash
# Create a new UTS namespace
sudo unshare --uts /bin/bash

# Inside the namespace:
hostname container-demo
hostname
# Output: container-demo

# In another terminal on the host:
hostname
# Output: original-hostname (unchanged)

exit
```

**PID Namespace Demonstration:**

```bash
# Create a new PID namespace (--fork is required for PID namespace to work)
sudo unshare --pid --fork --mount-proc /bin/bash

# Inside the namespace:
ps aux
# Output: Only 2 processes -- bash (PID 1) and ps itself
# USER  PID %CPU %MEM    VSZ   RSS TTY  STAT START TIME COMMAND
# root    1  0.0  0.0   4636  3564 pts/0 S  12:00 0:00 /bin/bash
# root    2  0.0  0.0   7060  1584 pts/0 R+ 12:00 0:00 ps aux

# On the host: the same bash process has a different, higher PID
# This is how containers see PID 1 as their main process
```

**Mount Namespace Demonstration:**

```bash
# Create mount namespace
sudo unshare --mount /bin/bash

# Create and mount tmpfs
mkdir /tmp/ns-test
mount -t tmpfs tmpfs /tmp/ns-test
echo "inside namespace" > /tmp/ns-test/test.txt
cat /tmp/ns-test/test.txt
# Output: inside namespace

# In another terminal: /tmp/ns-test exists but the tmpfs mount is NOT visible
mount | grep ns-test
# No output -- mount is isolated to the namespace
```

**Resource Comparison Table:**

| Aspect | Virtual Machine | Container |
|--------|----------------|-----------|
| Disk (base image) | 1-10 GB | 5-100 MB |
| RAM (idle OS) | 512 MB - 2 GB | 1-10 MB |
| Boot time | 30s - 5 min | < 1 second |
| Density (4GB host) | 2-4 VMs | 50-100+ containers |
| Isolation | Strong (hypervisor) | Moderate (kernel shared) |
| Kernel | Own kernel | Host kernel shared |

**Non-Technical Explanation:**

"Virtual machines are like separate apartments in a building -- each has its own kitchen, bathroom, plumbing, and electrical system. Containers are like offices in a co-working space -- each has its own locked room and furniture, but they share the building's electricity, plumbing, and HVAC. The co-working offices are cheaper, faster to set up, and you can fit more of them in the same building, but they share more infrastructure."

**Architecture Diagram:**

```
VMs:
┌─────────────────────────────────────────┐
│           Physical Hardware              │
├─────────────────────────────────────────┤
│           Host Operating System          │
├─────────────────────────────────────────┤
│              Hypervisor                  │
├──────────┬──────────┬───────────────────┤
│ Guest OS │ Guest OS │ Guest OS           │
│ Kernel A │ Kernel B │ Kernel C           │
│ App A    │ App B    │ App C              │
└──────────┴──────────┴───────────────────┘
(3 separate kernels)

Containers:
┌─────────────────────────────────────────┐
│           Physical Hardware              │
├─────────────────────────────────────────┤
│     Host Operating System + Kernel       │ ← Shared!
├─────────────────────────────────────────┤
│         Container Runtime (Docker)       │
├──────────┬──────────┬───────────────────┤
│ Libs A   │ Libs B   │ Libs C             │
│ App A    │ App B    │ App C              │
└──────────┴──────────┴───────────────────┘
(1 shared kernel, isolated via namespaces)
```

### Exercise 1b: Dockerfile Fundamentals

**Naive api-service Dockerfile:**

```dockerfile
FROM golang:1.21

WORKDIR /app

COPY . .

RUN go mod download
RUN go build -o api-service .

EXPOSE 8080

CMD ["./api-service"]
```

**Naive worker-service Dockerfile:**

```dockerfile
FROM golang:1.21

WORKDIR /app

COPY . .

RUN go mod download
RUN go build -o worker-service .

CMD ["./worker-service"]
```

**Expected naive image sizes:**
- api-service: ~800-900 MB (golang:1.21 base is ~800MB)
- worker-service: ~800-900 MB

**Expected .dockerignore:**

```
.git
.gitignore
*.md
LICENSE
.env
.env.*
!.env.example
vendor/
tmp/
*.test
coverage.out
.vscode/
.idea/
*.swp
*.swo
docker-compose*.yml
Dockerfile*
```

**3+ Optimization Opportunities the Student Should Identify:**
1. Image is ~800MB but the binary is only ~10-20MB -- too much wasted space (Go toolchain, source code)
2. `COPY . .` before `go mod download` means dependency cache is busted on every source code change
3. Using `golang:1.21` (Debian-based, ~800MB) instead of alpine (~300MB) or a minimal runtime image
4. Two separate `RUN` instructions could be combined
5. No non-root user -- running as root
6. No `.dockerignore` means `.git/`, docs, etc. are in the build context
7. Using the build image as the runtime image (no multi-stage)

**Analysis of the "bad" Dockerfile from checkpoint questions:**

```dockerfile
FROM golang:latest        # Issue 1: :latest is not reproducible
COPY . .                  # Issue 2: No WORKDIR set, copying to /
                          # Issue 3: COPY before go mod download (bad caching)
RUN go mod download
RUN go build -o app .
ENV DB_PASSWORD=supersecret  # Issue 4: SECRET IN IMAGE LAYER! Anyone can inspect this
EXPOSE 8080
CMD go run main.go        # Issue 5: go run recompiles every time, slower than binary
                          # Issue 6: Not exec form (string not array) -- runs under /bin/sh
                          # Issue 7: No non-root user
                          # Issue 8: No multi-stage build, huge final image
                          # Issue 9: No .dockerignore
```

---

## Lab 02: Image Layers & Multi-Stage Builds

### Exercise 2a: Image Layers & Cache Optimization

**docker history output example (naive Dockerfile):**

```
IMAGE          CREATED        CREATED BY                                      SIZE
abc123def      2 min ago      CMD ["./api-service"]                           0B
789xyz456      2 min ago      EXPOSE 8080                                     0B
456def789      2 min ago      RUN go build -o api-service .                   15MB
123abc456      3 min ago      RUN go mod download                             50MB
def456789      3 min ago      COPY . .                                        5MB
xyz789abc      5 min ago      WORKDIR /app                                    0B
base123456     2 weeks ago    (golang:1.21 base layers)                       800MB
```

**Optimized Dockerfile (with caching):**

```dockerfile
FROM golang:1.21-alpine

WORKDIR /app

# Copy dependency files first (change rarely)
COPY go.mod go.sum ./
RUN go mod download

# Copy source code (changes frequently)
COPY . .

# Build
RUN go build -o api-service .

EXPOSE 8080
CMD ["./api-service"]
```

**Cache behavior after source code change:**
- `FROM golang:1.21-alpine` → CACHED
- `WORKDIR /app` → CACHED
- `COPY go.mod go.sum ./` → CACHED (go.mod didn't change)
- `RUN go mod download` → CACHED (previous layer unchanged)
- `COPY . .` → NOT CACHED (source code changed)
- `RUN go build -o api-service .` → NOT CACHED (previous layer invalidated)

**Timing comparison (typical):**
- Naive full rebuild: ~30-60 seconds
- Naive rebuild after code change: ~30-60 seconds (same -- deps redownloaded)
- Optimized rebuild after code change: ~5-10 seconds (deps cached)

### Exercise 2b: Multi-Stage Builds

**Multi-stage api-service Dockerfile:**

```dockerfile
# ============ BUILD STAGE ============
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Cache dependencies
COPY go.mod go.sum ./
RUN go mod download

# Build binary
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o api-service .

# ============ RUNTIME STAGE ============
FROM alpine:3.19

# Install CA certificates for HTTPS calls
RUN apk --no-cache add ca-certificates tzdata

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/api-service .

# Set ownership
RUN chown appuser:appgroup ./api-service

# Switch to non-root
USER appuser

EXPOSE 8080

CMD ["./api-service"]
```

**Multi-stage worker-service Dockerfile:**

```dockerfile
# ============ BUILD STAGE ============
FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o worker-service .

# ============ RUNTIME STAGE ============
FROM alpine:3.19

RUN apk --no-cache add ca-certificates tzdata

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY --from=builder /app/worker-service .

RUN chown appuser:appgroup ./worker-service

USER appuser

CMD ["./worker-service"]
```

**Size Comparison Table:**

| Approach | api-service | worker-service |
|----------|-------------|----------------|
| Naive (golang:1.21) | ~850 MB | ~850 MB |
| Optimized caching (golang:alpine) | ~350 MB | ~350 MB |
| Multi-stage + alpine | ~18-25 MB | ~18-25 MB |
| Multi-stage + distroless | ~10-15 MB | ~10-15 MB |
| Multi-stage + scratch | ~8-12 MB | ~8-12 MB |

**Key build flags explained:**
- `CGO_ENABLED=0`: Disables CGO, producing a statically linked binary. Required for scratch/distroless (no libc).
- `GOOS=linux GOARCH=amd64`: Cross-compile for Linux AMD64 (ensures correct platform).
- `-ldflags="-w -s"`: Strip debug info and symbol table, reducing binary size by ~30%.

**Alpine vs Distroless vs Scratch trade-offs:**
- **Alpine**: Has shell, apk, basic tools. Can `docker exec` into it. ~7MB overhead. Good for development/staging.
- **Distroless**: No shell, no package manager. Includes CA certs and timezone data. ~2-5MB overhead. Good for production.
- **Scratch**: Literally empty. Must provide CA certs manually if needed. 0MB overhead. Maximum security, minimum debuggability.

---

## Lab 03: Docker Networking & Volumes

### Exercise 3a: Docker Networking

**Default bridge -- no DNS resolution:**

```bash
# Start two containers on default bridge
docker run -d --name alpine1 alpine sleep 3600
docker run -d --name alpine2 alpine sleep 3600

# Ping by IP works:
docker exec alpine1 ping -c 2 $(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' alpine2)
# PING 172.17.0.3: 64 bytes, works

# Ping by name FAILS:
docker exec alpine1 ping -c 2 alpine2
# ping: bad address 'alpine2'

docker rm -f alpine1 alpine2
```

**User-defined bridge -- DNS works:**

```bash
# Create custom network
docker network create flowforge-net

# Start containers on custom network
docker run -d --name postgres --network flowforge-net \
  -e POSTGRES_DB=flowforge \
  -e POSTGRES_USER=flowforge \
  -e POSTGRES_PASSWORD=secret \
  postgres:16-alpine

docker run -d --name api-service --network flowforge-net \
  -p 8080:8080 \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=flowforge \
  -e DB_PASSWORD=secret \
  -e DB_NAME=flowforge \
  myapi:latest

docker run -d --name worker-service --network flowforge-net \
  -e DB_HOST=postgres \
  -e DB_PORT=5432 \
  -e DB_USER=flowforge \
  -e DB_PASSWORD=secret \
  -e DB_NAME=flowforge \
  myworker:latest

# DNS resolution works:
docker exec api-service ping -c 2 postgres
# PING postgres (172.19.0.2): 56 data bytes, works!

docker exec api-service ping -c 2 worker-service
# PING worker-service (172.19.0.4): 56 data bytes, works!
```

**Networking modes comparison:**

| Mode | IP Address | Port Mapping Needed | DNS to Others | Performance | Security |
|------|-----------|---------------------|---------------|-------------|----------|
| bridge | Container IP (172.x.x.x) | Yes (-p) | Yes (custom bridge) | Normal (NAT overhead) | Good isolation |
| host | Host IP | No (shares host ports) | N/A | Best (no NAT) | Weak (shares host network) |
| none | None | N/A | No | N/A | Maximum (no network) |

**Why worker doesn't need -p:**
Worker-service initiates outbound connections TO PostgreSQL. It doesn't accept inbound connections. Port mapping (`-p`) is only needed for services that accept connections from outside the Docker network.

### Exercise 3b: Docker Volumes & Persistence

**Data loss without volumes:**

```bash
# Start PostgreSQL WITHOUT volume
docker run -d --name pg-ephemeral \
  -e POSTGRES_DB=flowforge \
  -e POSTGRES_USER=flowforge \
  -e POSTGRES_PASSWORD=secret \
  postgres:16-alpine

# Create data
docker exec -it pg-ephemeral psql -U flowforge -d flowforge -c \
  "CREATE TABLE test (id SERIAL, msg TEXT); INSERT INTO test (msg) VALUES ('hello');"
docker exec -it pg-ephemeral psql -U flowforge -d flowforge -c "SELECT * FROM test;"
# id | msg
#  1 | hello

# Destroy and recreate
docker rm -f pg-ephemeral
docker run -d --name pg-ephemeral \
  -e POSTGRES_DB=flowforge \
  -e POSTGRES_USER=flowforge \
  -e POSTGRES_PASSWORD=secret \
  postgres:16-alpine

# Data is GONE
docker exec -it pg-ephemeral psql -U flowforge -d flowforge -c "SELECT * FROM test;"
# ERROR: relation "test" does not exist
```

**Named volume for persistence:**

```bash
# Create named volume
docker volume create pgdata

# Start PostgreSQL WITH volume
docker run -d --name pg-persistent \
  --network flowforge-net \
  -e POSTGRES_DB=flowforge \
  -e POSTGRES_USER=flowforge \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# Create data
docker exec -it pg-persistent psql -U flowforge -d flowforge -c \
  "CREATE TABLE test (id SERIAL, msg TEXT); INSERT INTO test (msg) VALUES ('persistent!');"

# Destroy container
docker rm -f pg-persistent

# Recreate with SAME volume
docker run -d --name pg-persistent \
  --network flowforge-net \
  -e POSTGRES_DB=flowforge \
  -e POSTGRES_USER=flowforge \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# Data PERSISTS!
docker exec -it pg-persistent psql -U flowforge -d flowforge -c "SELECT * FROM test;"
# id | msg
#  1 | persistent!
```

**Volume inspection:**

```bash
docker volume inspect pgdata
# [
#   {
#     "CreatedAt": "...",
#     "Driver": "local",
#     "Labels": {},
#     "Mountpoint": "/var/lib/docker/volumes/pgdata/_data",
#     "Name": "pgdata",
#     "Options": {},
#     "Scope": "local"
#   }
# ]
```

**Bind mount permission fix:**

```bash
# Problem: container runs as UID 1000, but directory owned by root
# Fix option 1: change host directory ownership
sudo chown -R 1000:1000 /path/to/mount

# Fix option 2: use a named volume (Docker manages permissions)

# Fix option 3: match UID in Dockerfile with host user UID
# In Dockerfile:
# RUN adduser -u 1000 appuser
```

---

## Lab 04: Docker Compose

### Exercise 4a: Docker Compose for FlowForge

**Complete docker-compose.yml:**

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    container_name: flowforge-postgres
    environment:
      POSTGRES_DB: flowforge
      POSTGRES_USER: flowforge
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secret}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flowforge -d flowforge"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    networks:
      - flowforge-net
    restart: unless-stopped

  api-service:
    build:
      context: ./api-service
      dockerfile: Dockerfile
    container_name: flowforge-api
    ports:
      - "8080:8080"
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_USER: flowforge
      DB_PASSWORD: ${DB_PASSWORD:-secret}
      DB_NAME: flowforge
      PORT: "8080"
      LOG_LEVEL: info
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s
    networks:
      - flowforge-net
    restart: unless-stopped

  worker-service:
    build:
      context: ./worker-service
      dockerfile: Dockerfile
    container_name: flowforge-worker
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_USER: flowforge
      DB_PASSWORD: ${DB_PASSWORD:-secret}
      DB_NAME: flowforge
      POLL_INTERVAL: "5s"
      LOG_LEVEL: info
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - flowforge-net
    restart: unless-stopped

volumes:
  pgdata:
    driver: local

networks:
  flowforge-net:
    driver: bridge
```

**Health check for api-service:**
Using `wget` (available in alpine) because `curl` may not be installed in minimal images:
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]
  interval: 10s
  timeout: 5s
  retries: 5
```

Alternative with curl (if available):
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
```

**Worker health check options:**
1. File-based: worker writes a timestamp to a file; health check checks if the file was updated recently
2. Simple process check: `["CMD-SHELL", "pgrep worker-service || exit 1"]`
3. Custom health endpoint: add a simple HTTP health endpoint even to the worker

**Adding a new service (redis example):**

```yaml
  redis:
    image: redis:7-alpine
    container_name: flowforge-redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - flowforge-net
    restart: unless-stopped
```

### Exercise 4b: Development Workflow

**docker-compose.dev.yml (override file):**

```yaml
version: "3.8"

services:
  api-service:
    build:
      context: ./api-service
      dockerfile: Dockerfile.dev
    volumes:
      - ./api-service:/app
    environment:
      LOG_LEVEL: debug
    command: ["air", "-c", ".air.toml"]

  worker-service:
    build:
      context: ./worker-service
      dockerfile: Dockerfile.dev
    volumes:
      - ./worker-service:/app
    environment:
      LOG_LEVEL: debug
    command: ["air", "-c", ".air.toml"]
```

**Dockerfile.dev for api-service:**

```dockerfile
FROM golang:1.21-alpine

# Install air for hot-reload
RUN go install github.com/air-verse/air@latest

WORKDIR /app

# Copy dependency files (these get cached)
COPY go.mod go.sum ./
RUN go mod download

# Source code will be bind-mounted, not copied
# COPY . . is intentionally omitted

EXPOSE 8080

CMD ["air", "-c", ".air.toml"]
```

**.air.toml configuration:**

```toml
root = "."
tmp_dir = "tmp"

[build]
  cmd = "go build -o ./tmp/main ."
  bin = "tmp/main"
  delay = 1000
  exclude_dir = ["assets", "tmp", "vendor"]
  exclude_regex = ["_test\\.go$"]
  include_ext = ["go", "tpl", "tmpl", "html"]
  kill_delay = "1s"
  send_interrupt = true
  stop_on_error = true

[log]
  time = true

[misc]
  clean_on_exit = true
```

**Usage:**

```bash
# Start with dev overrides
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or with override file (auto-detected)
# Rename to docker-compose.override.yml for automatic merge
docker compose up
```

**Dev vs Prod Comparison Table:**

| Aspect | Development | Production |
|--------|-------------|------------|
| Source code | Bind-mounted from host | COPY'd at build time |
| Base image | golang:1.21-alpine (~350MB) | alpine:3.19 (~7MB) |
| Binary | Recompiled by air on change | Pre-compiled, static |
| Build tools | Go compiler, air | None |
| Image size | ~400MB | ~15-25MB |
| Debug tools | Full Go toolchain, shell | Minimal (or none with scratch) |
| Hot-reload | Yes (air watches files) | No (immutable image) |
| Port exposure | Debug ports open | Only required ports |

---

## Lab 05: Container Security & Debugging

### Exercise 5a: Container Security

**Non-root user Dockerfile addition (runtime stage):**

```dockerfile
# In runtime stage:
# Create non-root user and group
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set ownership
WORKDIR /app
COPY --from=builder /app/api-service .
RUN chown appuser:appgroup ./api-service

# Switch to non-root user AFTER setting up files
USER appuser

CMD ["./api-service"]
```

**Verifying non-root:**

```bash
docker exec flowforge-api whoami
# appuser

docker exec flowforge-api id
# uid=100(appuser) gid=101(appgroup) groups=101(appgroup)

# Compare to a root container:
# uid=0(root) gid=0(root) groups=0(root)
```

**Trivy scan example:**

```bash
trivy image flowforge-api:latest

# Output (after multi-stage alpine with non-root):
# flowforge-api:latest (alpine 3.19)
# ============================================
# Total: 2 (UNKNOWN: 0, LOW: 1, MEDIUM: 1, HIGH: 0, CRITICAL: 0)
```

**Common trivy fixes:**
- CRITICAL in base OS: update `FROM alpine:3.19` to latest patch release
- HIGH in Go dependency: update `go.mod` dependency version
- Image using `:latest`: pin to specific version tag
- Root user: add USER instruction (already done)

**Linux capabilities explanation:**
Docker grants these by default: CHOWN, DAC_OVERRIDE, FSETID, FOWNER, MKNOD, NET_RAW, SETGID, SETUID, SETFCAP, SETPCAP, NET_BIND_SERVICE, SYS_CHROOT, KILL, AUDIT_WRITE.

For a Go HTTP service, you likely need NONE of these (binding to port 8080 > 1024).

Drop all in docker-compose.yml:
```yaml
services:
  api-service:
    cap_drop:
      - ALL
```

### Exercise 5b: Debugging Challenge

**Broken Setup 1: Wrong Port Mapping**

The misconfiguration: api-service listens on port 8080 inside the container, but the compose file maps `-p 8080:3000` (wrong container port).

```yaml
# BROKEN:
ports:
  - "8080:3000"  # Container doesn't listen on 3000!
```

**Diagnosis steps:**
```bash
docker compose ps
# Shows: api-service  0.0.0.0:8080->3000/tcp

docker logs flowforge-api
# Shows: "Server listening on :8080" (app is fine)

docker inspect flowforge-api --format '{{json .NetworkSettings.Ports}}'
# Shows: "3000/tcp": [{"HostIp":"0.0.0.0","HostPort":"8080"}]
# Port mismatch! Host 8080 → Container 3000, but app listens on 8080

curl http://localhost:8080
# Connection refused (traffic goes to container port 3000, nothing listens there)
```

**Fix:** Change to `-p 8080:8080` (or change EXPOSE and application to match).

---

**Broken Setup 2: Missing Environment Variable**

The misconfiguration: `DB_HOST` is missing from the api-service environment.

```yaml
# BROKEN:
environment:
  # DB_HOST: postgres    # Missing!
  DB_PORT: "5432"
  DB_USER: flowforge
  DB_PASSWORD: secret
  DB_NAME: flowforge
```

**Diagnosis steps:**
```bash
docker compose ps
# api-service shows: Restarting (1) 5 seconds ago

docker logs flowforge-api
# "FATAL: DB_HOST environment variable is required"
# Exit code: 1

docker inspect flowforge-api --format '{{.State.ExitCode}}'
# 1
```

**Fix:** Add `DB_HOST: postgres` to the environment section.

---

**Broken Setup 3: Permission Denied on Volume**

The misconfiguration: a bind-mounted directory is owned by root, but the container runs as non-root user (UID 100).

```yaml
# BROKEN:
volumes:
  - ./data:/app/data  # ./data is owned by root:root
```

And the container runs as `USER appuser` (UID 100).

**Diagnosis steps:**
```bash
docker logs flowforge-api
# "Error: open /app/data/cache.json: permission denied"

docker exec flowforge-api id
# uid=100(appuser) gid=101(appgroup)

docker exec flowforge-api ls -la /app/data
# drwxr-xr-x  2 root root  4096 ... .
# Container user (100) can't write to root-owned directory
```

**Fix options:**
```bash
# Option 1: Change host directory ownership
sudo chown -R 100:101 ./data

# Option 2: Use a named volume instead (Docker manages permissions)

# Option 3: Run container with matching UID
# In Dockerfile: RUN adduser -u $(id -u) appuser
```

---

**Broken Setup 4: Network Isolation Issue**

The misconfiguration: PostgreSQL is on the default bridge network, while api-service and worker-service are on a custom network.

```yaml
# BROKEN:
services:
  postgres:
    image: postgres:16-alpine
    # No network specified → default bridge

  api-service:
    networks:
      - custom-net  # Different network!
    environment:
      DB_HOST: postgres  # DNS won't resolve!

networks:
  custom-net:
    driver: bridge
```

**Diagnosis steps:**
```bash
docker compose ps
# All containers show as running

docker logs flowforge-api
# "Error: dial tcp: lookup postgres: no such host"

docker network inspect custom-net
# Shows: api-service, worker-service connected
# Does NOT show: postgres

docker inspect flowforge-postgres --format '{{json .NetworkSettings.Networks}}'
# Shows: "bridge": {...}  -- on default bridge, NOT custom-net

# api-service can't resolve "postgres" because they're on different networks
```

**Fix:**
```yaml
# Add postgres to the same network:
services:
  postgres:
    networks:
      - custom-net
```

---

**Debugging Methodology Summary:**

1. `docker compose ps` -- Are containers running? What ports are mapped?
2. `docker logs <container>` -- What does the application say? Error messages?
3. `docker inspect <container>` -- Exit code, network config, mount config, env vars
4. `docker exec -it <container> sh` -- Can you reproduce the issue from inside?
5. `docker network inspect <network>` -- Who is connected? DNS working?
6. Form hypothesis from evidence
7. Test fix
8. Document: symptom → diagnosis → root cause → fix → concept violated
