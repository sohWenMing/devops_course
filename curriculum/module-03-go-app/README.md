# Module 3: Building FlowForge in Go

> **Time estimate**: 2 weeks  
> **Prerequisites**: Complete Modules 1-2 (Linux Deep Dive, Networking Fundamentals), Go installed (1.21+), PostgreSQL installed (Module 2 exercise)  
> **Link forward**: "This is the app you'll containerize, deploy, automate, orchestrate, monitor, and secure"  
> **Link back**: "You learned the OS layer (Module 1) and the network layer (Module 2). Now you build the application that lives on top of both."

---

## Why This Module Matters for DevOps

DevOps engineers don't just deploy code -- they understand it. When your CI pipeline fails a Go test, you need to know what broke. When the worker-service is consuming too much memory, you need to read the code to understand its polling loop. When a database migration fails mid-deploy, you need to understand what happened and how to recover.

This module isn't about becoming a Go expert. It's about building the application you'll spend the rest of the course deploying, monitoring, and securing. Every decision you make here -- how the API handles errors, how the worker polls for tasks, how config is loaded, how services communicate -- will echo through every future module.

By the end, you'll have two working Go services and a set of Python automation scripts that form the complete FlowForge application. More importantly, you'll understand *why* the application is designed the way it is, because you'll make those design decisions yourself.

---

## Table of Contents

1. [REST API Design Principles](#1-rest-api-design-principles)
2. [Go HTTP Server](#2-go-http-server)
3. [PostgreSQL Integration](#3-postgresql-integration)
4. [Database Migrations](#4-database-migrations)
5. [Background Worker Pattern](#5-background-worker-pattern)
6. [Inter-Service Communication](#6-inter-service-communication)
7. [12-Factor App Configuration](#7-12-factor-app-configuration)
8. [Python Automation Scripts](#8-python-automation-scripts)
9. [Structured Logging](#9-structured-logging)
10. [Go Testing](#10-go-testing)

---

## 1. REST API Design Principles

### What Makes a Good API?

A REST (Representational State Transfer) API uses HTTP verbs and resource-oriented URLs to expose functionality. The key idea is that your API exposes *resources* (nouns like "tasks", "users", "projects") and uses HTTP methods (verbs like GET, POST, PUT, DELETE) to act on them.

| Principle | What It Means | FlowForge Example |
|-----------|--------------|-------------------|
| Resource-oriented URLs | URLs represent nouns, not verbs | `/tasks` not `/getTasks` |
| HTTP verbs as actions | GET reads, POST creates, PUT updates, DELETE removes | `POST /tasks` creates a new task |
| Proper status codes | 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Internal Server Error | `POST /tasks` returns 201, not 200 |
| Consistent response format | All responses follow the same structure | `{"data": {...}, "error": null}` |
| Pagination | Large collections must be pageable | `GET /tasks?page=2&limit=20` |
| Idempotency | PUT and DELETE should produce the same result if called multiple times | `PUT /tasks/123` with the same body always yields the same state |
| Versioning | API versions prevent breaking changes | `/v1/tasks` or `Accept: application/vnd.flowforge.v1+json` |

### The FlowForge API Surface

Your api-service will expose these endpoints:

```
GET    /health          → Health check (is the service up? can it reach the DB?)
GET    /tasks           → List tasks (with pagination)
POST   /tasks           → Create a new task
GET    /tasks/{id}      → Get a specific task
PUT    /tasks/{id}      → Update a task
DELETE /tasks/{id}      → Delete a task
```

Each task has: `id`, `title`, `description`, `status` (pending/processing/completed/failed), `created_at`, `updated_at`.

### OpenAPI / Swagger

Before writing any code, you'll document your API in OpenAPI format. This is a machine-readable specification that describes every endpoint, request body, response shape, and error case. It forces you to think about your API contract *before* implementation.

### Architecture Thinking: API Design Decisions

> **Question to ask yourself**: Why use REST instead of GraphQL or gRPC for FlowForge? What are the trade-offs?

REST is the right choice here because:
- It's the simplest to implement and debug (you can test with curl)
- FlowForge has simple CRUD operations that map naturally to HTTP verbs
- It's universally understood -- any client can consume it

But REST has limitations: multiple round trips for related data, no built-in schema validation, over-fetching. For a complex service mesh with many interdependent calls, gRPC with Protocol Buffers might be better (binary protocol, schema-first, streaming). For a frontend that needs flexible queries, GraphQL could reduce round trips.

> **You'll use this when**: Configuring Kubernetes Services (Module 8) -- they route HTTP traffic to your API endpoints. Writing health checks (Module 9) -- Prometheus scrapes `/health` and `/metrics`. Securing endpoints (Module 10) -- you'll add authentication and rate limiting.

> **AWS SAA tie-in**: API Gateway is AWS's managed REST API service. Understanding REST design helps you configure API Gateway routes, method types, and integration responses.

---

## 2. Go HTTP Server

### net/http: The Standard Library

Go's `net/http` package provides everything you need to build an HTTP server. Unlike many languages, Go's standard library HTTP server is production-grade -- it handles concurrent connections, timeouts, and graceful shutdown out of the box.

```go
// The simplest possible Go HTTP server
package main

import (
    "fmt"
    "net/http"
)

func main() {
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, `{"status":"ok"}`)
    })
    http.ListenAndServe(":8080", nil)
}
```

This is functional but lacks: routing with path parameters, middleware (logging, auth), proper error handling, and graceful shutdown.

### Routers: chi and gin

While `net/http` can do everything, a router library like **chi** or **gin** adds:

| Feature | net/http alone | chi / gin |
|---------|---------------|-----------|
| Path parameters (`/tasks/{id}`) | Manual parsing | Built-in (`chi.URLParam(r, "id")`) |
| Method-based routing | Manual `if r.Method == "GET"` | `r.Get("/tasks", handler)` |
| Middleware chains | Manual wrapping | `r.Use(middleware.Logger)` |
| Route groups | Not available | `r.Route("/v1", func(r chi.Router) {...})` |

**chi** is the recommended choice for FlowForge because it's compatible with `net/http` -- handlers are standard `http.HandlerFunc` signatures. This means your code works with any `net/http`-compatible library.

### Key Concepts

**Handlers**: Functions that receive an `http.ResponseWriter` and `*http.Request` and produce a response.

**Middleware**: Functions that wrap handlers to add cross-cutting behavior (logging, auth, CORS, panic recovery). They form a chain: request → middleware1 → middleware2 → handler → middleware2 → middleware1 → response.

**Graceful shutdown**: When you receive SIGTERM (remember from Module 1?), you want to:
1. Stop accepting new connections
2. Wait for in-flight requests to complete
3. Close database connections
4. Exit cleanly

This is critical for zero-downtime deployments (Module 8 -- Kubernetes rolling updates).

### Architecture Thinking: Framework vs Standard Library

> **Question to ask yourself**: When would you choose `net/http` alone vs a router like chi vs a full framework like gin? What are the trade-offs of each?

- `net/http` alone: Zero dependencies, full control, but more boilerplate
- chi: Thin routing layer, net/http compatible, good balance
- gin: Full framework with validation/binding, slightly more opinionated, slightly heavier

> **You'll use this when**: Writing Dockerfiles (Module 4) -- you'll need to understand the build process. Configuring health checks (Module 8) -- Kubernetes liveness/readiness probes hit your HTTP endpoints. Setting up monitoring (Module 9) -- you'll expose `/metrics` alongside your API.

---

## 3. PostgreSQL Integration

### Why PostgreSQL?

PostgreSQL is the most capable open-source relational database. It supports:
- ACID transactions (data integrity even during crashes)
- JSON/JSONB columns (flexible schema when needed)
- Full-text search
- Robust concurrency control (MVCC)
- `SELECT FOR UPDATE SKIP LOCKED` (we'll use this for our queue!)

### Connecting from Go

Go's `database/sql` package provides a generic interface for SQL databases. You pair it with a driver:

| Driver | Package | Approach |
|--------|---------|----------|
| lib/pq | `github.com/lib/pq` | Mature, widely used, pure Go |
| pgx | `github.com/jackc/pgx` | Newer, more features, better performance |

Both work with `database/sql`. The choice matters less than understanding the interface.

### Connection Pooling

`database/sql` manages a connection pool automatically. This is critical for performance:

```go
db, err := sql.Open("postgres", connStr)
db.SetMaxOpenConns(25)           // Max simultaneous connections
db.SetMaxIdleConns(5)            // Keep 5 connections ready
db.SetConnMaxLifetime(5 * time.Minute)  // Recycle connections
```

Without pooling, every request would open a new TCP connection to PostgreSQL (TCP handshake + TLS negotiation + PostgreSQL authentication = ~50ms overhead). With pooling, requests reuse existing connections (~0ms overhead).

### Architecture Thinking: Connection Pool Sizing

> **Question to ask yourself**: If you set `MaxOpenConns` too high, what happens? Too low? How does this relate to PostgreSQL's `max_connections` setting?

If too high: You exhaust PostgreSQL's connection limit, causing connection refused errors for other services. If too low: Requests queue up waiting for a connection, increasing latency. The pool size should be tuned based on your workload and PostgreSQL's `max_connections` (default 100).

> **Link back**: Remember from Module 2 when you learned about TCP connections and ports? Each database connection is a TCP connection. The `ss` command you learned will show these connections. The connection pool is an application-level optimization on top of TCP.

> **You'll use this when**: Configuring RDS (Module 5) -- you'll set `max_connections` on RDS. Writing Kubernetes manifests (Module 8) -- you'll set connection pool env vars in ConfigMaps. Monitoring (Module 9) -- connection pool exhaustion is a common production issue.

> **AWS SAA tie-in**: RDS PostgreSQL has connection limits based on instance size. RDS Proxy is AWS's managed connection pooler that sits between your application and the database. Understanding why connection pooling matters helps you decide when RDS Proxy is worth the cost.

---

## 4. Database Migrations

### Why Migrations?

Your database schema will evolve. You'll add tables, columns, indexes, and constraints over time. Migrations are versioned, ordered SQL scripts that evolve your database from one state to the next -- like version control for your schema.

Each migration has two parts:
- **Up**: Apply the change (add column, create table)
- **Down**: Reverse the change (drop column, drop table)

```
migrations/
  000001_create_tasks_table.up.sql
  000001_create_tasks_table.down.sql
  000002_add_assigned_worker_column.up.sql
  000002_add_assigned_worker_column.down.sql
```

### golang-migrate

The `golang-migrate` tool manages migrations for you:

```bash
# Create a new migration
migrate create -ext sql -dir migrations -seq add_assigned_worker

# Apply all pending migrations
migrate -database "postgres://..." -path migrations up

# Rollback the last migration
migrate -database "postgres://..." -path migrations down 1
```

### Architecture Thinking: Migration Safety

> **Question to ask yourself**: What happens if a migration fails halfway through? What if the "up" migration succeeds but the "down" migration has a bug?

Dangerous operations in migrations:
- Dropping columns (data loss -- irreversible without backups)
- Renaming tables (breaks running code)
- Adding NOT NULL columns without defaults (fails on existing rows)
- Long-running ALTER TABLE on large tables (locks the table)

Safe migration practices:
- Always test both up AND down migrations
- Never drop columns in the same release that stops using them
- Add columns as nullable first, backfill data, then add constraints
- Use transactions where possible (`BEGIN; ... COMMIT;`)

> **You'll use this when**: CI/CD pipelines (Module 7) -- migrations run automatically before deploying new code. Terraform (Module 6) -- you might manage the database schema lifecycle alongside infrastructure. Kubernetes (Module 8) -- migrations often run as init containers or Jobs before the main deployment.

---

## 5. Background Worker Pattern

### Polling vs Push

The worker-service needs to know when there are tasks to process. Two approaches:

| Approach | How It Works | Pros | Cons |
|----------|-------------|------|------|
| **Polling** | Worker asks "any tasks?" every N seconds | Simple, stateless, fault-tolerant | Wastes resources on empty polls, latency up to N seconds |
| **Push** (message queue) | A queue notifies the worker when a task arrives | Low latency, efficient | More infrastructure (RabbitMQ, SQS), more complexity |

For FlowForge, we use polling with PostgreSQL as the queue. This is simpler and demonstrates the pattern clearly. In production, you might use a dedicated message queue (SQS, RabbitMQ, NATS) -- but the worker pattern is the same.

### The Polling Loop

```go
// Pseudocode for the worker loop
for {
    task := claimNextTask()  // SELECT ... FOR UPDATE SKIP LOCKED
    if task != nil {
        process(task)
        markCompleted(task)
    }
    time.Sleep(pollInterval)  // Wait before polling again
}
```

### Graceful Shutdown

When the worker receives SIGTERM (Kubernetes sends this before killing a Pod), it must:
1. Stop picking up new tasks
2. Finish processing the current task
3. Release any claimed tasks that haven't started processing
4. Close the database connection
5. Exit with code 0

This uses Go's `context.Context` and `os/signal` packages:

```go
ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
defer cancel()
```

The context's `Done()` channel closes when SIGTERM arrives, and your polling loop checks it before claiming the next task.

### Architecture Thinking: Worker Reliability

> **Question to ask yourself**: What happens if the worker crashes after claiming a task but before completing it? How would you prevent a task from being stuck forever?

This is the "at-least-once" delivery problem. Solutions include:
- Timeout: If a task stays in "processing" for more than X minutes, it's considered failed and re-queued
- Heartbeats: The worker periodically updates a `last_heartbeat` column; if it stops, the task is reclaimed
- Idempotent processing: Design the task handler so processing the same task twice is harmless

> **Link back**: Remember SIGTERM vs SIGKILL from Module 1? Graceful shutdown handles SIGTERM. If the process doesn't exit in time, Kubernetes sends SIGKILL (Module 8). The worker must be fast enough in its shutdown to avoid being killed forcefully.

> **AWS SAA tie-in**: SQS (Simple Queue Service) implements this same pattern at cloud scale -- visibility timeout (claim duration), dead letter queues (failed tasks), and at-least-once delivery.

---

## 6. Inter-Service Communication

### The PostgreSQL Queue Pattern

FlowForge uses PostgreSQL as both the data store AND the message queue. When the api-service creates a task, it writes a row to the `tasks` table with `status = 'pending'`. The worker-service queries for pending tasks.

The magic is `SELECT FOR UPDATE SKIP LOCKED`:

```sql
BEGIN;
SELECT id, title, description
FROM tasks
WHERE status = 'pending'
ORDER BY created_at
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- Process the task...

UPDATE tasks SET status = 'completed', updated_at = NOW() WHERE id = $1;
COMMIT;
```

- `FOR UPDATE`: Locks the selected row so no other worker can claim it
- `SKIP LOCKED`: If a row is already locked by another worker, skip it and try the next one
- The combination gives you safe concurrent processing without conflicts

### Why Not a Separate Message Queue?

For FlowForge's scale, PostgreSQL-as-queue is perfect:
- No extra infrastructure
- Transactional consistency (task creation and queuing are one operation)
- Simpler deployment

But it has limits:
- At high throughput (thousands of tasks/second), a dedicated queue (SQS, RabbitMQ) is more efficient
- PostgreSQL locks consume resources
- No built-in retry/dead-letter-queue semantics (you build them yourself)

### Architecture Thinking: Communication Patterns

> **Question to ask yourself**: What if you needed to add a third service (e.g., a notification service)? Would the PostgreSQL queue pattern still work? At what point would you switch to a dedicated message broker?

This is the monolith-to-microservices spectrum. PostgreSQL as queue works for 2-3 services with moderate throughput. Beyond that, you'd introduce something like:
- **SQS** (AWS managed, serverless, durable)
- **RabbitMQ** (feature-rich, routing/exchanges)
- **NATS** (lightweight, fast, good for Kubernetes)

> **You'll use this when**: Docker Compose (Module 4) -- the two services communicate through the shared PostgreSQL container. Kubernetes (Module 8) -- they communicate through a ClusterIP Service exposing PostgreSQL. Monitoring (Module 9) -- you'll track queue depth as a key metric.

---

## 7. 12-Factor App Configuration

### The Twelve Factors

The [Twelve-Factor App](https://12factor.net/) methodology defines best practices for building modern, cloud-native applications. Here are the twelve factors and how they apply to FlowForge:

| # | Factor | Principle | FlowForge Application |
|---|--------|-----------|----------------------|
| I | Codebase | One codebase tracked in version control, many deploys | FlowForge repo deployed to dev, staging, prod |
| II | Dependencies | Explicitly declare and isolate dependencies | `go.mod` lists all Go dependencies |
| III | Config | Store config in the environment | DB host, port, credentials via env vars |
| IV | Backing Services | Treat backing services as attached resources | PostgreSQL is configured via URL, swappable |
| V | Build, Release, Run | Strictly separate build and run stages | `go build` → Docker image → deploy |
| VI | Processes | Execute the app as one or more stateless processes | api-service and worker-service are stateless |
| VII | Port Binding | Export services via port binding | api-service binds to `$PORT` |
| VIII | Concurrency | Scale out via the process model | Run multiple worker-service instances |
| IX | Disposability | Maximize robustness with fast startup and graceful shutdown | Graceful shutdown on SIGTERM |
| X | Dev/Prod Parity | Keep dev, staging, and prod as similar as possible | Same Docker image everywhere |
| XI | Logs | Treat logs as event streams | Write to stdout, not files |
| XII | Admin Processes | Run admin/management tasks as one-off processes | `migrate` runs as a separate process |

### Config in Environment Variables

The critical rule: **no hardcoded configuration values**. Everything that changes between environments (dev/staging/prod) must come from environment variables:

```
DATABASE_URL=postgres://user:pass@localhost:5432/flowforge
API_PORT=8080
WORKER_POLL_INTERVAL=5s
LOG_LEVEL=info
```

Your Go code reads these at startup and fails fast if required variables are missing.

### Architecture Thinking: Config Management

> **Question to ask yourself**: Why not use a config file (like `config.yaml`) instead of environment variables? What are the trade-offs?

Config files are fine for development, but environment variables are the standard for cloud-native apps because:
- Every orchestration system (Docker, Kubernetes, ECS) has first-class env var support
- No file mounting needed
- Easy to change per environment without rebuilding
- Secrets can be injected at runtime from secret stores

The downside: env vars are flat strings. Complex nested config requires naming conventions (like `DB_HOST`, `DB_PORT`, `DB_USER`).

> **You'll use this when**: Docker Compose (Module 4) -- environment variables in docker-compose.yml. Kubernetes ConfigMaps and Secrets (Module 8) -- they inject env vars into Pods. CI/CD (Module 7) -- secrets stored in GitHub Secrets are passed as env vars.

---

## 8. Python Automation Scripts

### Why Python for Automation?

Your FlowForge application is written in Go, but the surrounding tooling -- database seeding, health checks, cleanup scripts, deployment helpers -- is written in Python. Why?

- Python excels at scripting and automation (quick to write, easy to read)
- Libraries like `requests`, `psycopg2`, and `boto3` make common tasks trivial
- Most DevOps tools provide Python SDKs
- It's a separate language from your application, which tests your ability to work across languages

### The FlowForge Scripts

You'll write three scripts:

| Script | Purpose | Key Libraries |
|--------|---------|---------------|
| `seed-database.py` | Populate the database with test data | `psycopg2` (PostgreSQL), `faker` (test data generation) |
| `healthcheck.py` | Verify all FlowForge services are running and healthy | `requests` (HTTP), `psycopg2` (DB check) |
| `cleanup.py` | Reset the database, clean up test data | `psycopg2` (DB operations) |

Each script should:
- Accept configuration via environment variables (same as the Go services)
- Have clear `--help` output explaining what it does
- Return meaningful exit codes (0 = success, 1 = failure)
- Include error handling (don't crash on a connection timeout -- report it clearly)

### Architecture Thinking: Language Boundaries

> **Question to ask yourself**: When should automation be written in the same language as the application (Go) vs a scripting language (Python/Bash)?

Go is better for: performance-critical tooling, compiled binaries that need zero runtime dependencies, tools that are part of the core product.

Python is better for: ad-hoc automation, scripts that glue together multiple services, tasks where development speed matters more than runtime speed, scripts that use cloud SDKs.

Bash is better for: simple file operations, running sequences of commands, environment-specific bootstrapping.

> **Link back**: Remember the bash health-check script from Module 1 (Lab 3a)? These Python scripts serve a similar purpose but are more sophisticated -- they make HTTP requests, query databases, and produce structured output.

> **You'll use this when**: AWS deployment (Module 5) -- you'll write Python scripts using boto3 for AWS resource management. CI/CD (Module 7) -- automation scripts run in pipeline steps.

---

## 9. Structured Logging

### Why Structured Logging?

Traditional logging:
```
2024-01-15 10:30:45 INFO: Received request for task 123
2024-01-15 10:30:45 ERROR: Database connection failed
```

Structured logging (JSON):
```json
{"timestamp":"2024-01-15T10:30:45Z","level":"info","msg":"Received request","task_id":123,"request_id":"abc-123","method":"GET","path":"/tasks/123","duration_ms":12}
{"timestamp":"2024-01-15T10:30:45Z","level":"error","msg":"Database connection failed","error":"connection refused","retry_count":3,"request_id":"abc-123"}
```

The difference: structured logs are **machine-parseable**. You can:
- Filter by any field (`level=error`, `task_id=123`)
- Aggregate metrics from logs (`average duration_ms per endpoint`)
- Trace a request across services using `request_id`
- Feed them into log aggregation systems (Grafana Loki, ELK, CloudWatch)

### Request IDs

A **request ID** is a unique identifier generated when a request enters the system. It's passed through every function call, database query, and inter-service communication so that all log entries for a single user request can be correlated.

```
User → api-service (request_id=abc-123) → PostgreSQL → worker-service (request_id=abc-123)
```

Without request IDs, debugging a production issue means grepping through thousands of unrelated log lines. With them, you filter by one ID and see the entire story.

### Architecture Thinking: Observability

> **Question to ask yourself**: Logs, metrics, and traces are the "three pillars of observability." How does structured logging relate to the other two? When would you use logs vs metrics vs traces?

- **Logs**: Detailed records of individual events (good for debugging specific issues)
- **Metrics**: Aggregated numerical measurements over time (good for dashboards and alerting)
- **Traces**: The path of a request through multiple services (good for understanding latency)

Structured logs can *generate* metrics (count error-level logs per minute) and approximate traces (correlate by request_id). But dedicated metrics and tracing are more efficient for their specific purposes.

> **You'll use this when**: Monitoring (Module 9) -- Grafana Loki queries structured JSON logs. Debugging (every module) -- when something goes wrong, logs are your first investigative tool. Docker (Module 4) -- containers log to stdout, and structured JSON is the expected format.

> **AWS SAA tie-in**: CloudWatch Logs Insights can query structured JSON logs. Understanding structured logging helps you write effective CloudWatch queries.

---

## 10. Go Testing

### Testing in Go

Go has testing built into the language -- no external framework needed. Test files live alongside the code they test and use the naming convention `*_test.go`.

```go
// handlers_test.go
func TestGetTaskHandler(t *testing.T) {
    // Setup
    req := httptest.NewRequest("GET", "/tasks/1", nil)
    w := httptest.NewRecorder()

    // Execute
    handler.GetTask(w, req)

    // Assert
    if w.Code != http.StatusOK {
        t.Errorf("expected 200, got %d", w.Code)
    }
}
```

### Unit Tests vs Integration Tests

| Aspect | Unit Tests | Integration Tests |
|--------|-----------|------------------|
| What they test | A single function/handler in isolation | Multiple components working together |
| Dependencies | Mocked (fake DB, fake HTTP) | Real (actual PostgreSQL, actual HTTP) |
| Speed | Fast (milliseconds) | Slower (seconds, needs DB) |
| Confidence | High for logic correctness | High for system correctness |
| Example | Test that a handler returns 400 for invalid JSON | Test that creating a task via API actually appears in PostgreSQL |

For FlowForge:
- **Unit tests**: Test API handlers with mock database, test request validation, test response formatting
- **Integration tests**: Test the full flow: HTTP request → handler → database → response, with a real PostgreSQL instance

### Test Coverage

Go's built-in coverage tool shows which lines of code are tested:

```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out    # Visual coverage report
```

Your target: **>70% coverage on api-service**. This doesn't mean every line is tested -- it means the critical paths (happy path, error cases, edge cases) are covered.

### Architecture Thinking: What to Test

> **Question to ask yourself**: If you had time to write only 5 tests for the entire api-service, which 5 would give you the most confidence?

Focus on:
1. The happy path (create task, get task, list tasks)
2. Error handling (invalid input, missing task, database down)
3. Edge cases (empty title, very long description, concurrent requests)

Don't waste time testing:
- Go standard library functions (they're already tested)
- Trivial getters/setters
- Code that's just wiring (calling one function from another)

> **You'll use this when**: CI/CD (Module 7) -- tests run automatically on every push. If coverage drops below 70%, the pipeline fails. Docker (Module 4) -- tests run during the Docker build to ensure the image contains working code.

---

## Labs Overview

| Lab | Exercises | What You'll Build |
|-----|-----------|-------------------|
| [Lab 01: REST API](lab-01-rest-api.md) | 1a: API design + OpenAPI, 1b: Go HTTP server | API design document and working HTTP server |
| [Lab 02: Database](lab-02-database.md) | 2a: PostgreSQL setup + Go integration, 2b: Migrations | Database schema, Go-to-PostgreSQL connection, migration files |
| [Lab 03: Worker](lab-03-worker.md) | 3a: Polling worker + graceful shutdown, 3b: Inter-service queue | Working worker-service that processes tasks from the queue |
| [Lab 04: Config, Scripts & Logging](lab-04-config-scripts-logging.md) | 4a: 12-Factor config, 4b: Python scripts, 4c: Structured logging | Externalized config, automation scripts, JSON logging |
| [Lab 05: Testing](lab-05-testing.md) | 5: Unit + integration tests | Test suite with >70% coverage |

---

## Getting Started

Before starting the labs, make sure you have:

1. **Go 1.21+** installed (`go version`)
2. **PostgreSQL** running locally (you installed it in Module 1 Lab 2c)
3. **Python 3.8+** installed (`python3 --version`)
4. The starter code in `project/` -- read the `project/README.md` for the project structure

The starter code provides minimal skeletons with TODOs. Your job is to fill in the implementation following the lab instructions.

> **Remember**: The labs tell you WHAT to build, not HOW to build it. Use the README theory sections, Go documentation, and your own problem-solving skills. If you get stuck, the Socratic mentor skill will guide you with questions, not answers.
