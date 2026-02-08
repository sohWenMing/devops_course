# Module 4: Docker and Containerization

> **Time estimate**: 2 weeks  
> **Prerequisites**: Complete Modules 1-3 (Linux Deep Dive, Networking Fundamentals, Building FlowForge in Go), Docker Engine installed  
> **Link forward**: "These images become your deployment artifacts for AWS and Kubernetes"  
> **Link back**: "You built the OS foundation (Module 1), the network layer (Module 2), and the FlowForge application (Module 3). Now you package everything into portable, reproducible containers."

---

## Why This Module Matters for DevOps

"It works on my machine" is the problem Docker solves. But containerization isn't just about packaging -- it's a fundamental shift in how you think about deploying software.

In Module 1, you set up FlowForge's directory structure, users, and permissions manually on a single machine. In Module 3, you built services that depend on specific Go versions, PostgreSQL, and environment variables. What happens when you need to deploy to a new machine? You'd have to repeat every manual step -- install Go, install PostgreSQL, create users, set permissions, configure environment variables, build binaries... and hope you didn't miss anything.

Containers give you **immutable, reproducible deployments**. You describe your environment in a Dockerfile, build it once, and run it anywhere. The same image that passed your tests is the same image that runs in production. No drift. No "but I installed that library last week."

By the end of this module, you'll have the entire FlowForge stack -- api-service, worker-service, and PostgreSQL -- running with a single `docker compose up` command, ready to be pushed to AWS (Module 5) and orchestrated by Kubernetes (Module 8).

---

## Table of Contents

1. [Containers vs Virtual Machines](#1-containers-vs-virtual-machines)
2. [Dockerfile Fundamentals](#2-dockerfile-fundamentals)
3. [Image Layers and Caching](#3-image-layers-and-caching)
4. [Multi-Stage Builds](#4-multi-stage-builds)
5. [Docker Networking](#5-docker-networking)
6. [Docker Volumes and Persistence](#6-docker-volumes-and-persistence)
7. [Docker Compose](#7-docker-compose)
8. [Docker Compose for Development](#8-docker-compose-for-development)
9. [Container Security Basics](#9-container-security-basics)
10. [Debugging Containers](#10-debugging-containers)

---

## 1. Containers vs Virtual Machines

### The Core Difference: Shared Kernel

Virtual machines and containers both provide isolation, but they achieve it at fundamentally different layers.

A **virtual machine** runs a complete operating system on top of a hypervisor. Each VM has its own kernel, its own init system, its own memory management -- it's a full computer inside a computer. This provides strong isolation but at the cost of resources: each VM needs hundreds of megabytes of RAM just for the OS, and startup takes seconds to minutes.

A **container** shares the host machine's kernel. It uses Linux kernel features -- **namespaces** and **cgroups** -- to create isolation without duplicating the entire OS. This means containers start in milliseconds, use megabytes instead of gigabytes, and you can run dozens on a single machine.

```
┌─────────────────────────────────────────────────────┐
│                 Virtual Machines                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │  App A   │  │  App B   │  │  App C   │             │
│  │ Bins/Libs│  │ Bins/Libs│  │ Bins/Libs│             │
│  │ Guest OS │  │ Guest OS │  │ Guest OS │             │
│  └─────────┘  └─────────┘  └─────────┘             │
│  ┌─────────────────────────────────────┐             │
│  │           Hypervisor                │             │
│  └─────────────────────────────────────┘             │
│  ┌─────────────────────────────────────┐             │
│  │           Host OS                   │             │
│  └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  Containers                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │  App A   │  │  App B   │  │  App C   │             │
│  │ Bins/Libs│  │ Bins/Libs│  │ Bins/Libs│             │
│  └─────────┘  └─────────┘  └─────────┘             │
│  ┌─────────────────────────────────────┐             │
│  │        Container Runtime            │             │
│  └─────────────────────────────────────┘             │
│  ┌─────────────────────────────────────┐             │
│  │     Host OS (shared kernel)         │             │
│  └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────┘
```

### Linux Namespaces: The Isolation Mechanism

Namespaces are a Linux kernel feature that partition system resources so that each set of processes sees its own isolated instance. There are several namespace types:

| Namespace | What It Isolates | FlowForge Example |
|-----------|-----------------|-------------------|
| PID | Process IDs -- a container only sees its own processes | api-service sees only its own PID 1, not the worker's processes |
| NET | Network stack -- interfaces, routes, iptables | Each container gets its own `eth0` interface and IP address |
| MNT | Mount points -- filesystem view | Container sees only its own filesystem, not the host's `/etc/passwd` |
| UTS | Hostname and domain name | Container has its own hostname |
| IPC | Inter-process communication | Shared memory segments are isolated between containers |
| USER | User and group IDs | Root inside a container can map to a non-root user on the host |

> **Link back to Module 1**: Remember when you explored `/proc` and the process tree in Module 1? Each container gets its own PID namespace, so `PID 1` inside the container is *not* the same as `PID 1` on the host. The `unshare` command lets you experiment with namespaces directly.

### Control Groups (cgroups): Resource Limits

While namespaces provide isolation (what a process can *see*), cgroups limit what a process can *use*. They control:

- **CPU**: How much CPU time a container gets
- **Memory**: Maximum RAM a container can use (OOM kill if exceeded)
- **I/O**: Disk read/write bandwidth limits
- **Network**: Bandwidth limits per container

This is critical in production: without cgroups, one runaway container could starve all others of resources.

### Architecture Thinking: When VMs, When Containers?

> **Question to ask yourself**: When would you choose a VM over a container? What about running containers inside VMs?

VMs are appropriate when you need:
- **Strong security isolation** (multi-tenant environments where tenants don't trust each other)
- **Different operating systems** (running Windows alongside Linux)
- **Kernel-level customization** (different kernel versions or modules)

Containers are appropriate when you need:
- **Fast startup** (scaling from 0 to 100 instances in seconds)
- **High density** (running dozens of services on one machine)
- **Consistent environments** (same image in dev, staging, production)
- **Microservice architectures** (each service in its own container)

In practice, cloud deployments often combine both: containers run on VMs. EC2 instances (VMs) run Docker, and EKS worker nodes are EC2 instances running Kubernetes pods (containers). The VM provides the infrastructure isolation; the container provides the application isolation.

> **AWS SAA tie-in**: EC2 instances are VMs. ECS and EKS run containers on EC2 instances (or Fargate, which abstracts the VM away entirely). Understanding the isolation boundary between VMs and containers is essential for choosing between EC2, ECS, EKS, and Fargate on the exam.

---

## 2. Dockerfile Fundamentals

### What Is a Dockerfile?

A Dockerfile is a text file containing instructions to build a Docker image. Think of it as a recipe: each instruction adds a layer to the image, and the final result is an immutable artifact that can be run anywhere Docker is installed.

### Key Instructions

| Instruction | Purpose | Example |
|-------------|---------|---------|
| `FROM` | Base image to build on | `FROM golang:1.21-alpine` |
| `WORKDIR` | Set the working directory | `WORKDIR /app` |
| `COPY` | Copy files from host to image | `COPY . .` |
| `RUN` | Execute a command during build | `RUN go build -o api-service .` |
| `ENV` | Set environment variables | `ENV PORT=8080` |
| `EXPOSE` | Document which port the app listens on | `EXPOSE 8080` |
| `CMD` | Default command when container starts | `CMD ["./api-service"]` |
| `ENTRYPOINT` | Fixed command (CMD becomes arguments) | `ENTRYPOINT ["./api-service"]` |
| `ARG` | Build-time variables | `ARG GO_VERSION=1.21` |
| `LABEL` | Metadata for the image | `LABEL maintainer="you@example.com"` |
| `USER` | Switch to a non-root user | `USER appuser` |
| `HEALTHCHECK` | Define container health check | `HEALTHCHECK CMD curl -f http://localhost:8080/health` |

### COPY vs ADD

`COPY` copies files from the host. `ADD` can also extract tar archives and download from URLs. **Always prefer `COPY`** unless you specifically need tar extraction. `ADD` has hidden magic that makes Dockerfiles harder to understand and can introduce security risks (downloading arbitrary URLs).

### CMD vs ENTRYPOINT

- `CMD` provides a default command that can be overridden: `docker run myimage /bin/sh` replaces the CMD
- `ENTRYPOINT` sets a fixed command; `CMD` becomes its arguments: `docker run myimage --verbose` appends `--verbose` to ENTRYPOINT
- Best practice: use `ENTRYPOINT` for the binary, `CMD` for default flags

```dockerfile
ENTRYPOINT ["./api-service"]
CMD ["--port", "8080"]
# docker run myimage                    → ./api-service --port 8080
# docker run myimage --port 9090        → ./api-service --port 9090
```

### .dockerignore

Just as `.gitignore` tells Git which files to skip, `.dockerignore` tells Docker which files to exclude from the build context. This matters because Docker sends the entire build context to the daemon before building.

Always exclude:
- `.git/` (can be hundreds of MB)
- `vendor/` or `node_modules/` (will be rebuilt inside the container)
- `*.md`, `LICENSE` (not needed at runtime)
- Test files, CI configs, IDE files
- `.env` files (secrets should never be baked into images)

> **Link back to Module 3**: The `.env` file you created with your 12-Factor config should be in `.dockerignore`. Container configuration comes from environment variables passed at runtime, not baked into the image. This is why 12-Factor principle #3 (Store config in the environment) matters so much for containers.

### Architecture Thinking: Dockerfile Design Decisions

> **Question to ask yourself**: Why does instruction order in a Dockerfile matter? What would happen if you `COPY . .` before `RUN go mod download`?

The answer is layer caching, which we cover next. But the key insight is: a Dockerfile isn't just a shell script. Each instruction creates a layer, and Docker caches layers. Your instruction order determines how effectively you use that cache.

> **You'll use this when**: Writing CI/CD pipelines (Module 7) that build Docker images -- slow builds mean slow deployments. Optimizing Kubernetes pod startup times (Module 8) -- large images mean slow pull times.

> **AWS SAA tie-in**: ECR (Elastic Container Registry) stores your Docker images. Understanding image size directly impacts ECR storage costs and EC2 pull times. Multi-stage builds (Section 4) are a best practice for minimizing both.

---

## 3. Image Layers and Caching

### How Layers Work

Every instruction in a Dockerfile creates a new **layer**. A layer is a set of filesystem changes (files added, modified, or deleted). Layers are stacked on top of each other, and the final image is the union of all layers.

```
┌─────────────────────┐
│ Layer 5: CMD         │  (metadata only, no filesystem change)
├─────────────────────┤
│ Layer 4: COPY . .    │  (your application source code)
├─────────────────────┤
│ Layer 3: RUN go build│  (compiled binary)
├─────────────────────┤
│ Layer 2: COPY go.mod │  (dependency files)
├─────────────────────┤
│ Layer 1: FROM golang │  (base OS + Go toolchain)
└─────────────────────┘
```

Key properties of layers:
- Layers are **read-only** once created
- Layers are **shared** between images that use the same base
- Layers are **cached** -- if the instruction and its inputs haven't changed, Docker reuses the cached layer
- When a container runs, a thin **writable layer** is added on top

### Cache Invalidation

Docker's build cache works top-down: if a layer's instruction or its inputs change, that layer and **all subsequent layers** are rebuilt.

This is why instruction order matters enormously:

```dockerfile
# BAD: Any source code change invalidates the dependency cache
FROM golang:1.21-alpine
WORKDIR /app
COPY . .                    # <- changes every time you edit any file
RUN go mod download          # <- re-downloads all deps even if go.mod didn't change
RUN go build -o api-service .

# GOOD: Dependencies are cached separately from source code
FROM golang:1.21-alpine
WORKDIR /app
COPY go.mod go.sum ./        # <- only changes when dependencies change
RUN go mod download           # <- cached unless go.mod/go.sum change
COPY . .                      # <- changes when source code changes
RUN go build -o api-service . # <- rebuild with cached dependencies
```

### The `docker history` Command

`docker history <image>` shows you every layer in an image: what instruction created it, how large it is, and when it was created. This is your tool for understanding image size and finding optimization opportunities.

### Best Practices for Layer Optimization

1. **Put rarely-changing instructions first**: Base image, system packages, dependency install
2. **Put frequently-changing instructions last**: Source code copy, binary build
3. **Combine RUN instructions** to reduce layers: `RUN apt-get update && apt-get install -y pkg1 pkg2 && rm -rf /var/lib/apt/lists/*`
4. **Clean up in the same RUN** instruction: If you download a file, process it, and delete it in the same `RUN`, the deleted file never appears in a layer. If you delete it in a separate `RUN`, the file exists in a previous layer and the image is larger.
5. **Use `.dockerignore`** to prevent unnecessary files from entering the build context

> **Architecture Thinking**: What's the trade-off between fewer layers (combining RUN) and cache granularity? If you combine `apt-get install pkg1 pkg2 pkg3` into one RUN, changing any package forces reinstalling all three. But separate RUN instructions create more layers.

---

## 4. Multi-Stage Builds

### The Problem: Build Tools in Production

A naive Go Dockerfile includes the entire Go toolchain (~300MB) in the final image, even though the compiled binary needs none of it. The same applies to npm/yarn for Node.js, Maven/Gradle for Java, or gcc for C.

Build tools are needed to compile your code, but they shouldn't ship to production. They increase image size, slow down container startup, and expand the attack surface.

### The Solution: Separate Build and Runtime Stages

Multi-stage builds let you use one image for building and a different (smaller) image for running:

```dockerfile
# Stage 1: BUILD
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o api-service .

# Stage 2: RUNTIME
FROM alpine:3.19
RUN apk --no-cache add ca-certificates
WORKDIR /app
COPY --from=builder /app/api-service .
EXPOSE 8080
CMD ["./api-service"]
```

The `COPY --from=builder` instruction copies artifacts from the build stage to the runtime stage. The Go toolchain, source code, and intermediate build files are all left behind.

### Base Image Choices

| Base Image | Size | Includes | When to Use |
|-----------|------|----------|-------------|
| `ubuntu:22.04` | ~77MB | Full Ubuntu userland | Need apt, debugging tools |
| `alpine:3.19` | ~7MB | Minimal Linux with apk | Good balance of small + functional |
| `gcr.io/distroless/static` | ~2MB | Almost nothing (no shell) | Maximum security, CGO_ENABLED=0 |
| `scratch` | 0MB | Literally empty | Statically compiled binaries only |

For Go services compiled with `CGO_ENABLED=0`, `scratch` or `distroless` are ideal -- the binary includes everything it needs.

### Size Comparison

| Approach | Typical Size | Notes |
|----------|-------------|-------|
| `FROM golang` (naive) | ~800MB | Includes entire Go toolchain |
| `FROM golang:alpine` (naive) | ~300MB | Smaller base, still has toolchain |
| Multi-stage with `alpine` | ~15-25MB | Just binary + minimal OS |
| Multi-stage with `scratch` | ~8-15MB | Just the static binary |

> **Architecture Thinking**: Why might you choose `alpine` over `scratch` even though `scratch` is smaller?

With `scratch`, you have no shell, no package manager, no debugging tools. If something goes wrong inside the container, you can't `docker exec` into it and run `ls` or `cat`. Alpine gives you a shell and `apk` for installing debugging tools, at the cost of a few extra megabytes. In development and staging, Alpine is often the pragmatic choice. In production with mature debugging workflows (Module 9 monitoring, Module 10 security), distroless/scratch becomes viable.

> **You'll use this when**: Pushing images to ECR (Module 5) -- smaller images mean faster pushes and pulls. Building in CI/CD (Module 7) -- multi-stage builds simplify the pipeline because the Dockerfile handles the build, not the CI script. Running in Kubernetes (Module 8) -- smaller images mean faster pod startup during scaling events.

> **AWS SAA tie-in**: ECR charges per GB stored. A 15MB image costs ~50x less storage than an 800MB image. Image pull time also affects EC2 Auto Scaling responsiveness -- the faster a new instance can pull and start your container, the faster it can serve traffic.

---

## 5. Docker Networking

### Network Drivers

Docker provides several networking modes, each suited to different use cases:

| Driver | Description | Use Case |
|--------|-------------|----------|
| `bridge` | Default. Containers on an isolated virtual network | Most common -- containers that need to talk to each other |
| `host` | Container uses the host's network stack directly | When you need maximum network performance (no NAT overhead) |
| `none` | No networking at all | Security-sensitive batch jobs that shouldn't have network access |
| `overlay` | Multi-host networking for Docker Swarm/clusters | Distributed deployments (less common with Kubernetes) |

### The Default Bridge Network

When you run `docker run` without specifying a network, the container joins the default `bridge` network. Containers on the default bridge can communicate by IP address but **cannot resolve each other by name**.

### User-Defined Bridge Networks

When you create a custom network with `docker network create`, containers on that network get:

- **Automatic DNS resolution**: Containers can reach each other by container name (e.g., `ping api-service`)
- **Better isolation**: Only containers explicitly connected to the network can communicate
- **Configurable subnets**: You control the IP range

This is why Docker Compose creates a custom network by default -- so services can resolve each other by name.

```
┌──────────────────── Custom Network: flowforge-net ─────────────────────┐
│                                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐            │
│  │ api-service  │    │worker-service│    │    postgres      │            │
│  │  :8080       │    │  (no port)   │    │    :5432         │            │
│  │              │◄──►│              │◄──►│                  │            │
│  └─────────────┘    └──────────────┘    └─────────────────┘            │
│       DNS: api-service   DNS: worker-service   DNS: postgres           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
       │
       │ port mapping -p 8080:8080
       ▼
   Host machine :8080 → api-service :8080
```

### Port Mapping

Containers are isolated by default -- their ports aren't accessible from the host. To expose a container's port:

```bash
docker run -p HOST_PORT:CONTAINER_PORT myimage
# -p 8080:8080    → host:8080 maps to container:8080
# -p 9090:8080    → host:9090 maps to container:8080
# -p 127.0.0.1:8080:8080  → only accessible from localhost
```

### DNS Resolution in Docker

On a user-defined bridge network, Docker runs an embedded DNS server at `127.0.0.11`. When a container looks up another container's name, this DNS server resolves it to the container's IP address on the network.

This means your Go service can connect to PostgreSQL using `postgres` as the hostname (the container name), not an IP address:

```
DB_HOST=postgres    # not 172.19.0.3
DB_PORT=5432
```

> **Link back to Module 2**: Remember DNS resolution from Module 2? Docker's embedded DNS works the same way -- it's just scoped to the Docker network. The same dig/nslookup concepts apply. And the networking model (bridge, routing, NAT) maps directly to what you learned about Linux networking.

> **Link forward to Module 8**: Kubernetes Services provide the same DNS-based service discovery, but across a cluster. `api-service.default.svc.cluster.local` in Kubernetes is the equivalent of `api-service` on a Docker network. The concepts are identical -- the scope expands.

> **AWS SAA tie-in**: VPC networking (Module 5) follows the same pattern: private subnets with DNS resolution (Route 53 private hosted zones), security groups acting as firewalls, and NAT gateways enabling outbound internet access. Docker networking is VPC networking in miniature.

---

## 6. Docker Volumes and Persistence

### The Container Filesystem Problem

Containers are ephemeral by default. When a container is destroyed, all data written to its writable layer is lost. This is a feature -- it ensures containers are disposable and reproducible. But databases, upload directories, and configuration files need to survive container restarts.

### Three Options for Persistent Data

| Type | What It Is | When to Use |
|------|-----------|-------------|
| **Bind mount** | Maps a host directory into the container | Development: mount source code for hot-reload |
| **Named volume** | Docker-managed storage | Production: database data, upload storage |
| **tmpfs mount** | In-memory filesystem | Sensitive data that should never touch disk |

### Bind Mounts

```bash
docker run -v /host/path:/container/path myimage
# or
docker run --mount type=bind,source=/host/path,target=/container/path myimage
```

Bind mounts give the container direct access to a host directory. Changes are immediately visible in both directions. This is essential for development: you mount your source code into the container so changes are reflected without rebuilding.

**Caution**: Bind mounts expose the host filesystem to the container. If the container runs as root, it has root access to that host directory.

### Named Volumes

```bash
docker volume create pgdata
docker run -v pgdata:/var/lib/postgresql/data postgres:16
```

Named volumes are managed by Docker. Docker handles where the data is stored on the host (typically under `/var/lib/docker/volumes/`). They persist even when containers are removed.

**For PostgreSQL**: The PostgreSQL container stores its data in `/var/lib/postgresql/data`. Mounting a named volume there means your database survives container restarts:

```bash
# First run: PostgreSQL initializes the database in the volume
docker run -v pgdata:/var/lib/postgresql/data postgres:16

# Container dies and is removed
docker rm postgres-container

# Second run: PostgreSQL finds existing data in the volume
docker run -v pgdata:/var/lib/postgresql/data postgres:16
# Data is still there!
```

### Volume Permissions

A common gotcha: the user inside the container may not have permission to write to a bind-mounted directory. If the container runs as `appuser` (UID 1000) but the host directory is owned by root, writes will fail with "permission denied."

> **Link back to Module 1**: This is the same permissions model you learned in Module 1 -- UID/GID ownership applies across the host-container boundary. The user inside the container needs write permission on the mounted path, and that maps back to UID/GID on the host.

### Architecture Thinking: Data Persistence Strategy

> **Question to ask yourself**: Why not just use bind mounts for everything in production?

Bind mounts tie your container to a specific host's filesystem layout. In a cluster (Kubernetes, Module 8), pods move between nodes -- bind mounts don't follow them. Named volumes can be backed by network storage (EBS, EFS) that persists independent of any single host.

> **AWS SAA tie-in**: EBS (Elastic Block Store) volumes are the AWS equivalent of Docker named volumes -- persistent block storage that attaches to EC2 instances. EFS (Elastic File System) provides shared file storage across multiple instances. S3 is for object storage. Each maps to different persistence needs.

---

## 7. Docker Compose

### What Is Docker Compose?

Docker Compose lets you define and run multi-container applications with a single YAML file. Instead of running multiple `docker run` commands with long argument lists, you declare your entire stack in `docker-compose.yml` and manage it with `docker compose up` and `docker compose down`.

### The docker-compose.yml Structure

```yaml
version: "3.8"

services:
  api-service:
    build: ./api-service
    ports:
      - "8080:8080"
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - flowforge

  worker-service:
    build: ./worker-service
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - flowforge

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: flowforge
      POSTGRES_USER: flowforge
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flowforge"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - flowforge

volumes:
  pgdata:

networks:
  flowforge:
    driver: bridge
```

### Key Compose Concepts

**services**: Each service is a container definition. The service name (e.g., `api-service`) becomes the DNS hostname on the network.

**depends_on with conditions**: Controls startup order. `condition: service_healthy` means the dependent service waits until the dependency's health check passes, not just until the container starts.

**health checks**: A command that Docker runs periodically to check if the service is ready. This is critical -- `depends_on` without a health check only waits for the container to start, not for the application inside to be ready. PostgreSQL might take several seconds to initialize even after the container is "running."

**environment**: Set environment variables for the container. This is how you pass configuration (12-Factor principle #3).

**volumes**: Mount named volumes or bind mounts. The top-level `volumes:` key declares named volumes; per-service `volumes:` mounts them.

**networks**: By default, Compose creates a network for the project. Declaring it explicitly gives you control over the driver and subnet.

### Compose Commands

| Command | What It Does |
|---------|-------------|
| `docker compose up` | Create and start all services |
| `docker compose up -d` | Same, but detached (background) |
| `docker compose up --build` | Rebuild images before starting |
| `docker compose down` | Stop and remove containers, networks |
| `docker compose down -v` | Same, plus remove named volumes |
| `docker compose logs -f` | Follow logs from all services |
| `docker compose ps` | List running services |
| `docker compose exec api-service sh` | Run a command in a running container |

> **Link back to Module 3**: The environment variables in your `docker-compose.yml` are the same ones you defined in `.env.example` during Module 3. 12-Factor configuration means your Go services don't care whether the env vars come from a `.env` file, `docker-compose.yml`, or Kubernetes ConfigMaps (Module 8).

> **Architecture Thinking**: Docker Compose is a development and single-host tool. It's excellent for local development but doesn't handle multi-host deployments, auto-scaling, or self-healing. That's what Kubernetes (Module 8) is for. Compose defines *what* your stack looks like; Kubernetes adds *how* it should behave in production.

---

## 8. Docker Compose for Development

### Why a Separate Dev Compose?

Production images should be minimal, optimized, and immutable. Development environments need:
- Source code mounted into the container (so changes take effect immediately)
- Hot-reload tools (e.g., `air` for Go) that watch for file changes and restart the binary
- Debug ports exposed
- Verbose logging
- Potentially different base images with debugging tools

### Override Files

Docker Compose supports override files. A `docker-compose.override.yml` file is automatically merged with `docker-compose.yml`:

```bash
docker compose up
# merges docker-compose.yml + docker-compose.override.yml (if exists)

docker compose -f docker-compose.yml -f docker-compose.prod.yml up
# merges docker-compose.yml + docker-compose.prod.yml
```

This lets you keep a base compose file and layer environment-specific changes on top.

### Hot-Reload with Air

[Air](https://github.com/air-verse/air) is a live-reloading tool for Go applications. When you save a Go file, Air detects the change, recompiles, and restarts the binary -- all inside the container.

In a development compose file, you would:
1. Mount the source code as a bind mount
2. Use a Dockerfile that installs `air`
3. Override the CMD to use `air` instead of the compiled binary

This workflow means you edit code on your host machine (in your IDE), and changes are reflected in the running container immediately.

### Dev vs Prod Differences

| Aspect | Development | Production |
|--------|-------------|------------|
| Source code | Bind-mounted from host | Baked into image at build time |
| Binary | Rebuilt by air on file change | Pre-compiled in multi-stage build |
| Base image | golang:alpine (has Go toolchain) | alpine or scratch (minimal) |
| Ports | Debug ports exposed | Only necessary ports |
| Logging | Verbose/debug level | Info or warn level |
| Volumes | Source code mounts | Only data volumes |

> **You'll use this when**: Developing with CI/CD (Module 7) -- the CI pipeline builds the production image, but developers use the dev compose locally. Setting up Kubernetes dev environments (Module 8) -- tools like Skaffold and Tilt provide similar hot-reload for K8s.

---

## 9. Container Security Basics

### Why Container Security Matters

Containers share the host kernel. A container escape -- where a process breaks out of its namespace isolation -- gives the attacker access to the host and all other containers. Security in containers is about reducing the attack surface and limiting the blast radius.

### Running as Non-Root

By default, the process inside a Docker container runs as root. This is dangerous because:
- If the container is compromised, the attacker has root inside the container
- Root inside a container can sometimes escalate to root on the host (container escape)
- Files created by the container on bind mounts are owned by root on the host

Always create a non-root user in your Dockerfile:

```dockerfile
# Create a non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Switch to non-root user
USER appuser

# Now the process runs as appuser, not root
CMD ["./api-service"]
```

### Image Scanning with Trivy

[Trivy](https://github.com/aquasecurity/trivy) is an open-source vulnerability scanner for container images. It checks:
- OS packages (Alpine apk, Debian apt) for known CVEs
- Application dependencies (Go modules, npm packages, Python pip) for known vulnerabilities
- Dockerfile misconfigurations (running as root, using `latest` tag)

```bash
trivy image myimage:latest
```

Trivy reports vulnerabilities by severity: CRITICAL, HIGH, MEDIUM, LOW. In production, you should block deployments with CRITICAL or HIGH vulnerabilities.

### Linux Capabilities

Linux capabilities split root's superpowers into fine-grained permissions. Instead of giving a container full root access, you can grant only the specific capabilities it needs:

- `NET_BIND_SERVICE`: Bind to ports below 1024
- `SYS_TIME`: Set the system clock
- `CHOWN`: Change file ownership

Docker drops most capabilities by default, but some remain. For maximum security, drop ALL capabilities and add back only what you need.

### Additional Security Practices

- **Use specific image tags**, not `latest` -- you need reproducible builds
- **Don't store secrets in images** -- use environment variables or secrets management
- **Use read-only root filesystems** where possible
- **Limit resources** with `--memory` and `--cpus` to prevent denial-of-service
- **Sign images** to verify their provenance

> **Link forward to Module 10**: Module 10 (Security Hardening) goes much deeper into container security: distroless images, read-only root filesystems, Kubernetes SecurityContexts, NetworkPolicies, and image signing with cosign. This section gives you the foundation.

> **AWS SAA tie-in**: ECR supports image scanning (using Clair or Trivy). ECS task definitions and EKS pod specs can enforce non-root execution and drop capabilities. AWS Inspector can scan running containers for vulnerabilities.

---

## 10. Debugging Containers

### The Debugging Toolkit

When a container fails to start, crashes, or behaves unexpectedly, you have several tools:

| Command | What It Shows |
|---------|-------------|
| `docker logs <container>` | stdout/stderr output from the container |
| `docker logs -f <container>` | Follow logs in real-time |
| `docker exec -it <container> sh` | Open a shell inside a running container |
| `docker inspect <container>` | Full JSON metadata: config, network, mounts, state |
| `docker inspect --format '{{.State.ExitCode}}' <container>` | Specific field from inspect output |
| `docker events` | Real-time event stream from the Docker daemon |
| `docker stats` | Live CPU, memory, network, I/O usage per container |
| `docker top <container>` | Running processes inside the container |
| `docker diff <container>` | Files changed in the container's writable layer |

### Common Failure Patterns

**Container exits immediately (exit code 1)**:
- Application error. Check `docker logs`.
- Missing environment variable. Check if all required vars are set.
- Missing file or permission denied. Check volumes and user permissions.

**Container exits with signal (exit code 137 = SIGKILL, 143 = SIGTERM)**:
- 137: Out of memory (OOM killed). Check `docker inspect` for `OOMKilled: true`.
- 143: Graceful shutdown (SIGTERM). Normal during `docker stop`.

**Container starts but doesn't respond**:
- Port mapping incorrect. Check `docker inspect` for port bindings.
- Application listening on wrong interface. Check if it binds to `0.0.0.0` vs `127.0.0.1`.
- Network misconfiguration. Check `docker network inspect`.

**Container can't connect to another container**:
- Not on the same network. Check `docker network inspect`.
- Wrong hostname. Use the container name, not an IP address.
- Target container not ready. Check health checks and startup order.

### The Debugging Methodology

1. **Read the logs**: `docker logs <container>` -- this solves 80% of issues
2. **Check the state**: `docker inspect <container>` -- is it running? What's the exit code?
3. **Get inside**: `docker exec -it <container> sh` -- can you reproduce the issue from inside?
4. **Check the network**: `docker network inspect <network>` -- are containers connected?
5. **Check resources**: `docker stats` -- is the container hitting memory or CPU limits?

> **Link back to Module 1**: The debugging methodology mirrors what you learned in Module 1 (logs → processes → permissions → config). In containers, `docker logs` replaces `journalctl`, `docker exec` replaces SSH, and `docker inspect` replaces examining config files directly.

> **Link forward to Module 9**: In production, you won't SSH into containers. Monitoring (Prometheus metrics, Grafana dashboards, structured logs) becomes your primary debugging tool. The `docker logs` and `docker exec` workflow is for development; observability is for production.

---

## Labs

Work through the labs in order:

1. **[Lab 01: Containers & Dockerfile Fundamentals](lab-01-containers-dockerfile.md)** -- Understand namespaces, write your first Dockerfiles
2. **[Lab 02: Image Layers & Multi-Stage Builds](lab-02-layers-multistage.md)** -- Optimize images for size and build speed
3. **[Lab 03: Docker Networking & Volumes](lab-03-networking-volumes.md)** -- Connect containers and persist data
4. **[Lab 04: Docker Compose](lab-04-compose.md)** -- Orchestrate the full FlowForge stack
5. **[Lab 05: Security & Debugging](lab-05-security-debugging.md)** -- Harden containers and diagnose failures

When you've completed all labs, check yourself against the [Exit Gate Checklist](checklist.md). Every box must be checked before moving to Module 5.
