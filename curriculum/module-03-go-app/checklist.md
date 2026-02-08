# Module 3: Building FlowForge in Go -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 4.  
> No partial credit. No "I think so." Either you can do it or you can't.  
> If you can't, go back to the relevant lab and practice until you can.

---

## How to Use This Checklist

For each item:
1. Attempt it **without looking at notes, previous labs, or the internet**
2. If you succeed, mark it `[x]`
3. If you fail or need to look something up, mark it `[ ]` and go practice
4. Come back and try again until every box is checked

---

## REST API Design (Lab 01, Exercise 1a)

- [ ] I can design a REST API for a new domain (e.g., "inventory system") with proper resource naming, HTTP verbs, and status codes in under 15 minutes
- [ ] I can explain the difference between PUT and PATCH, POST and PUT, and when to use each
- [ ] I can write an OpenAPI specification for a new set of endpoints without referencing examples
- [ ] I know the correct HTTP status codes for: success, created, bad request, not found, internal server error, and can explain when each applies
- [ ] I can explain why API documentation (like OpenAPI) should be written before implementation

---

## Go HTTP Server (Lab 01, Exercise 1b)

- [ ] I can create a new Go HTTP server with routing, middleware, and graceful shutdown from scratch
- [ ] I can add a new resource endpoint (e.g., `/projects`) to the api-service without referencing the `/tasks` implementation
- [ ] I can explain how middleware chains work: execution order, how to pass data between middleware and handlers
- [ ] I can explain what `context.Context` is, how it propagates through handlers, and why it matters for cancellation and timeouts
- [ ] I can implement graceful shutdown: listen for SIGTERM, stop accepting connections, drain in-flight requests, exit cleanly

---

## PostgreSQL Integration (Lab 02, Exercise 2a)

- [ ] I can write a SQL migration from scratch for a new table with appropriate column types, constraints, and indexes
- [ ] I can connect to PostgreSQL from Go, configure connection pooling, and explain why pool settings matter
- [ ] I know the difference between `db.Query()`, `db.QueryRow()`, and `db.Exec()` and when to use each
- [ ] I can explain why parameterized queries (`$1`, `$2`) are used instead of string formatting
- [ ] I can explain connection pooling: what it is, why it matters, what happens when the pool is exhausted
- [ ] I can handle `sql.ErrNoRows` correctly and explain why it's different from other database errors

---

## Database Migrations (Lab 02, Exercise 2b)

- [ ] I can create a migration that adds a column, apply it, verify it, and roll it back
- [ ] I can explain why down migrations are important and when you'd use them
- [ ] I can explain what happens if a migration fails halfway through and how to recover
- [ ] I can describe 3 dangerous operations in migrations and how to make each one safe
- [ ] I can run the complete migration workflow: check version → create migration → apply → verify → rollback → re-apply

---

## Worker Service (Lab 03, Exercise 3a)

- [ ] FlowForge worker-service starts, connects to PostgreSQL, and polls for pending tasks
- [ ] The worker correctly transitions tasks: pending → processing → completed
- [ ] Graceful shutdown works: the worker finishes its current task before exiting on SIGTERM
- [ ] I can explain the polling vs push model trade-offs and when to use each
- [ ] I can add a new task type to the worker without copying existing handler code

---

## Inter-Service Communication (Lab 03, Exercise 3b)

- [ ] The complete flow works: create task via API → worker picks it up → task status updates to completed
- [ ] I can explain `SELECT FOR UPDATE SKIP LOCKED` -- what each keyword does and why
- [ ] I can draw the data flow from "user creates task" to "worker completes task" without looking at code
- [ ] I can explain what happens if the worker crashes mid-task and how to recover
- [ ] I understand when PostgreSQL-as-queue is sufficient vs when to use a dedicated message queue

---

## 12-Factor Configuration (Lab 04, Exercise 4a)

- [ ] ALL configuration in both services comes from environment variables -- zero hardcoded values
- [ ] Both services fail fast with clear error messages if required config is missing
- [ ] I can list all 12 factors from memory and explain how FlowForge adheres to each
- [ ] `.env.example` exists with documentation for every variable, `.env` is in `.gitignore`
- [ ] I can identify which 12 factors will be addressed in future modules (Docker, K8s, CI/CD)

---

## Python Automation Scripts (Lab 04, Exercise 4b)

- [ ] `seed-database.py` populates the database with configurable test data and has `--help`
- [ ] `healthcheck.py` verifies all services are running, reports UP/DOWN, and exits with meaningful codes
- [ ] `cleanup.py` resets the database with a safety `--confirm` flag
- [ ] All scripts use environment variables for configuration (same vars as Go services)
- [ ] I can write a new Python script from scratch (e.g., `load-test.py`) without referencing existing scripts

---

## Structured Logging (Lab 04, Exercise 4c)

- [ ] Both services output structured JSON logs to stdout
- [ ] Every API request has a unique request ID that appears in response headers and all related log entries
- [ ] I can trace a single request from API call through worker processing using the request ID in logs
- [ ] Log level is configurable via environment variable
- [ ] I can explain why structured logging matters for production observability

---

## Go Testing (Lab 05)

- [ ] Unit tests exist for API handlers (at least: create, get, list, update, delete, health, and invalid input cases)
- [ ] Integration tests verify the full HTTP → database → response flow
- [ ] All tests pass: `go test ./...` runs cleanly
- [ ] Test coverage is >70% on the api-service (verified with `go test -cover ./...`)
- [ ] I can write tests for a new feature without referencing existing tests
- [ ] I can run coverage, identify untested paths, and explain why certain code is or isn't covered

---

## Integration & Architecture Thinking

- [ ] FlowForge api-service runs, accepts HTTP requests, and persists data to PostgreSQL
- [ ] FlowForge worker-service processes tasks from the queue automatically
- [ ] Both services shut down gracefully on SIGTERM (verify with `kill -15 <PID>`)
- [ ] I can explain the complete data flow from "user creates task" to "worker completes task"
- [ ] I can explain how 12-Factor principles prepare FlowForge for containerization (Docker, Module 4)
- [ ] I can explain how graceful shutdown relates to Kubernetes rolling updates (Module 8)
- [ ] I can explain how structured logging prepares FlowForge for centralized log aggregation (Module 9)
- [ ] I can explain how the separate api-service and worker-service design enables independent scaling

---

## Final Self-Assessment

> Answer honestly:
>
> **Could I build a similar two-service Go application from scratch on a completely fresh machine with no internet access and no notes?**
>
> - If YES for everything: You're ready for Module 4. Congratulations!
> - If NO for anything: Go back and practice. There are no shortcuts in DevOps.

---

## Ready for Module 4?

If every box above is checked, proceed to [Module 4: Docker and Containerization](../module-04-docker/README.md).

> **What's coming**: In Module 4, you'll take the FlowForge services you just built and containerize them with Docker. You'll write Dockerfiles, optimize image sizes with multi-stage builds, set up Docker Compose for the full stack, and learn container networking and volumes. The 12-Factor principles, graceful shutdown, and stdout logging you implemented here will make containerization smooth -- you'll see why those decisions matter.
