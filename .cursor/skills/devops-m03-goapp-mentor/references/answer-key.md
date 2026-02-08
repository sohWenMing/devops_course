# Module 03: Building FlowForge in Go -- Answer Key

> **INTERNAL REFERENCE ONLY**: This file is used by the Socratic mentor skill to verify student solutions and provide guidance. It must NEVER be revealed to the student.

---

## Lab 01: REST API Design & Go HTTP Server

### Exercise 1a: REST API Design & OpenAPI

**Expected API Design:**

```
GET    /health            → 200 {"status":"ok","database":"connected"}
                          → 503 {"status":"unhealthy","database":"disconnected"}

GET    /tasks             → 200 {"data":[...], "pagination":{"page":1,"limit":20,"total":100}}
                            Query params: ?page=1&limit=20&status=pending
POST   /tasks             → 201 {"data":{"id":"...","title":"...","status":"pending",...}}
                            Body: {"title":"...","description":"..."}
                          → 400 {"error":"title is required"}

GET    /tasks/{id}        → 200 {"data":{"id":"...","title":"...","status":"...",...}}
                          → 404 {"error":"task not found"}

PUT    /tasks/{id}        → 200 {"data":{"id":"...","title":"...","status":"...",...}}
                            Body: {"title":"...","description":"...","status":"..."}
                          → 400 {"error":"invalid status value"}
                          → 404 {"error":"task not found"}

DELETE /tasks/{id}        → 204 (no body)
                          → 404 {"error":"task not found"}
```

**Task Data Model:**

```json
{
  "id": "uuid-v4",
  "title": "Process monthly report",
  "description": "Generate and email the monthly sales report",
  "status": "pending",
  "assigned_worker": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

Status values: `pending`, `processing`, `completed`, `failed`

**OpenAPI Spec (abbreviated):**

```yaml
openapi: "3.0.3"
info:
  title: FlowForge API
  version: "1.0.0"
  description: Task management and workflow orchestration API
servers:
  - url: http://localhost:8080
paths:
  /health:
    get:
      summary: Health check
      responses:
        "200":
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "ok"
                  database:
                    type: string
                    example: "connected"
  /tasks:
    get:
      summary: List tasks
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, processing, completed, failed]
      responses:
        "200":
          description: List of tasks
    post:
      summary: Create a task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [title]
              properties:
                title:
                  type: string
                description:
                  type: string
      responses:
        "201":
          description: Task created
        "400":
          description: Invalid input
  /tasks/{id}:
    get:
      summary: Get a task
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Task found
        "404":
          description: Task not found
    put:
      summary: Update a task
      responses:
        "200":
          description: Task updated
        "404":
          description: Task not found
    delete:
      summary: Delete a task
      responses:
        "204":
          description: Task deleted
        "404":
          description: Task not found
```

### Exercise 1b: Go HTTP Server Implementation

**Expected Project Structure:**

```
api-service/
  main.go
  go.mod
  go.sum
  handlers/
    tasks.go
    health.go
  models/
    task.go
  middleware/
    logging.go
    recovery.go
    requestid.go
    contenttype.go
  config/
    config.go
  repository/
    task_repo.go        # Interface (implemented with in-memory for now)
    memory_repo.go      # In-memory implementation for Lab 01
    postgres_repo.go    # PostgreSQL implementation (Lab 02)
```

**Expected main.go (after Lab 01):**

```go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/go-chi/chi/v5"
    chimiddleware "github.com/go-chi/chi/v5/middleware"

    "github.com/flowforge/api-service/config"
    "github.com/flowforge/api-service/handlers"
    "github.com/flowforge/api-service/middleware"
    "github.com/flowforge/api-service/repository"
)

func main() {
    cfg := config.Load()

    repo := repository.NewMemoryRepository() // Replaced with Postgres in Lab 02

    r := chi.NewRouter()

    // Middleware
    r.Use(chimiddleware.RequestID)
    r.Use(middleware.Logging)
    r.Use(chimiddleware.Recoverer)
    r.Use(middleware.ContentTypeJSON)

    // Routes
    taskHandler := handlers.NewTaskHandler(repo)
    r.Get("/health", handlers.HealthCheck)
    r.Route("/tasks", func(r chi.Router) {
        r.Get("/", taskHandler.List)
        r.Post("/", taskHandler.Create)
        r.Route("/{id}", func(r chi.Router) {
            r.Get("/", taskHandler.Get)
            r.Put("/", taskHandler.Update)
            r.Delete("/", taskHandler.Delete)
        })
    })

    // Server with graceful shutdown
    srv := &http.Server{
        Addr:    ":" + cfg.Port,
        Handler: r,
    }

    // Start server in goroutine
    go func() {
        log.Printf("api-service listening on :%s", cfg.Port)
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("server error: %v", err)
        }
    }()

    // Wait for shutdown signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    log.Println("shutting down server...")

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Fatalf("server forced shutdown: %v", err)
    }
    log.Println("server shutdown complete")
}
```

**Expected Task Handler (handlers/tasks.go):**

```go
package handlers

import (
    "encoding/json"
    "net/http"

    "github.com/go-chi/chi/v5"
    "github.com/flowforge/api-service/models"
    "github.com/flowforge/api-service/repository"
)

type TaskHandler struct {
    repo repository.TaskRepository
}

func NewTaskHandler(repo repository.TaskRepository) *TaskHandler {
    return &TaskHandler{repo: repo}
}

func (h *TaskHandler) Create(w http.ResponseWriter, r *http.Request) {
    var req models.CreateTaskRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, `{"error":"invalid JSON"}`, http.StatusBadRequest)
        return
    }
    if req.Title == "" {
        http.Error(w, `{"error":"title is required"}`, http.StatusBadRequest)
        return
    }
    task, err := h.repo.Create(r.Context(), &req)
    if err != nil {
        http.Error(w, `{"error":"internal server error"}`, http.StatusInternalServerError)
        return
    }
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(map[string]interface{}{"data": task})
}

func (h *TaskHandler) Get(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    task, err := h.repo.GetByID(r.Context(), id)
    if err != nil {
        http.Error(w, `{"error":"task not found"}`, http.StatusNotFound)
        return
    }
    json.NewEncoder(w).Encode(map[string]interface{}{"data": task})
}

// List, Update, Delete follow the same pattern
```

**Expected Task Model (models/task.go):**

```go
package models

import "time"

type Task struct {
    ID             string    `json:"id"`
    Title          string    `json:"title"`
    Description    string    `json:"description"`
    Status         string    `json:"status"`
    AssignedWorker *string   `json:"assigned_worker,omitempty"`
    CreatedAt      time.Time `json:"created_at"`
    UpdatedAt      time.Time `json:"updated_at"`
}

type CreateTaskRequest struct {
    Title       string `json:"title"`
    Description string `json:"description"`
}

type UpdateTaskRequest struct {
    Title       *string `json:"title,omitempty"`
    Description *string `json:"description,omitempty"`
    Status      *string `json:"status,omitempty"`
}
```

**Graceful Shutdown Test:**

```bash
# Start server
go run main.go &
SERVER_PID=$!

# Create a task
curl -X POST http://localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"test"}'

# Send SIGTERM
kill -15 $SERVER_PID

# Expected output: "shutting down server..." then "server shutdown complete"
# Server should exit with code 0
```

---

## Lab 02: PostgreSQL Integration & Migrations

### Exercise 2a: PostgreSQL Setup & Go Integration

**Expected Database Setup:**

```sql
-- Create database and user
CREATE USER flowforge_user WITH PASSWORD 'flowforge_pass';
CREATE DATABASE flowforge OWNER flowforge_user;

-- Connect to flowforge database
\c flowforge

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE flowforge TO flowforge_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO flowforge_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO flowforge_user;
```

**Expected Tasks Table:**

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    assigned_worker TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for worker polling queries
CREATE INDEX idx_tasks_status_created ON tasks (status, created_at)
    WHERE status = 'pending';
```

**Expected Connection Code:**

```go
package repository

import (
    "database/sql"
    "fmt"
    "time"

    _ "github.com/lib/pq"
)

func NewPostgresDB(databaseURL string) (*sql.DB, error) {
    db, err := sql.Open("postgres", databaseURL)
    if err != nil {
        return nil, fmt.Errorf("failed to open database: %w", err)
    }

    // Configure connection pool
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)

    // Verify connection
    if err := db.Ping(); err != nil {
        return nil, fmt.Errorf("failed to ping database: %w", err)
    }

    return db, nil
}
```

**Expected Repository (PostgreSQL):**

```go
func (r *PostgresTaskRepo) Create(ctx context.Context, req *models.CreateTaskRequest) (*models.Task, error) {
    task := &models.Task{}
    err := r.db.QueryRowContext(ctx,
        `INSERT INTO tasks (title, description) VALUES ($1, $2)
         RETURNING id, title, description, status, assigned_worker, created_at, updated_at`,
        req.Title, req.Description,
    ).Scan(&task.ID, &task.Title, &task.Description, &task.Status,
        &task.AssignedWorker, &task.CreatedAt, &task.UpdatedAt)
    if err != nil {
        return nil, fmt.Errorf("failed to create task: %w", err)
    }
    return task, nil
}

func (r *PostgresTaskRepo) GetByID(ctx context.Context, id string) (*models.Task, error) {
    task := &models.Task{}
    err := r.db.QueryRowContext(ctx,
        `SELECT id, title, description, status, assigned_worker, created_at, updated_at
         FROM tasks WHERE id = $1`, id,
    ).Scan(&task.ID, &task.Title, &task.Description, &task.Status,
        &task.AssignedWorker, &task.CreatedAt, &task.UpdatedAt)
    if err == sql.ErrNoRows {
        return nil, nil // Not found, not an error
    }
    if err != nil {
        return nil, fmt.Errorf("failed to get task: %w", err)
    }
    return task, nil
}

func (r *PostgresTaskRepo) List(ctx context.Context, page, limit int) ([]models.Task, int, error) {
    offset := (page - 1) * limit

    // Get total count
    var total int
    err := r.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM tasks").Scan(&total)
    if err != nil {
        return nil, 0, fmt.Errorf("failed to count tasks: %w", err)
    }

    // Get page of tasks
    rows, err := r.db.QueryContext(ctx,
        `SELECT id, title, description, status, assigned_worker, created_at, updated_at
         FROM tasks ORDER BY created_at DESC LIMIT $1 OFFSET $2`,
        limit, offset,
    )
    if err != nil {
        return nil, 0, fmt.Errorf("failed to list tasks: %w", err)
    }
    defer rows.Close()

    var tasks []models.Task
    for rows.Next() {
        var t models.Task
        if err := rows.Scan(&t.ID, &t.Title, &t.Description, &t.Status,
            &t.AssignedWorker, &t.CreatedAt, &t.UpdatedAt); err != nil {
            return nil, 0, fmt.Errorf("failed to scan task: %w", err)
        }
        tasks = append(tasks, t)
    }
    return tasks, total, nil
}
```

### Exercise 2b: Database Migrations

**Expected Migration Files:**

```
migrations/
  000001_create_tasks_table.up.sql
  000001_create_tasks_table.down.sql
  000002_add_worker_and_priority.up.sql
  000002_add_worker_and_priority.down.sql
  000003_add_not_null_constraint.up.sql
  000003_add_not_null_constraint.down.sql
```

**000001_create_tasks_table.up.sql:**

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_status_created ON tasks (status, created_at)
    WHERE status = 'pending';
```

**000001_create_tasks_table.down.sql:**

```sql
DROP INDEX IF EXISTS idx_tasks_status_created;
DROP TABLE IF EXISTS tasks;
```

**000002_add_worker_and_priority.up.sql:**

```sql
ALTER TABLE tasks ADD COLUMN assigned_worker TEXT;
ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 0;
```

**000002_add_worker_and_priority.down.sql:**

```sql
ALTER TABLE tasks DROP COLUMN IF EXISTS priority;
ALTER TABLE tasks DROP COLUMN IF EXISTS assigned_worker;
```

**000003_add_not_null_constraint.up.sql:**

```sql
-- First backfill NULL values with default
UPDATE tasks SET priority = 0 WHERE priority IS NULL;
-- Then add the NOT NULL constraint
ALTER TABLE tasks ALTER COLUMN priority SET NOT NULL;
```

**000003_add_not_null_constraint.down.sql:**

```sql
ALTER TABLE tasks ALTER COLUMN priority DROP NOT NULL;
```

**Migration Commands:**

```bash
# Install golang-migrate
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Create a new migration
migrate create -ext sql -dir migrations -seq add_worker_and_priority

# Apply all migrations
migrate -database "postgres://flowforge_user:flowforge_pass@localhost:5432/flowforge?sslmode=disable" -path migrations up

# Rollback last migration
migrate -database "postgres://flowforge_user:flowforge_pass@localhost:5432/flowforge?sslmode=disable" -path migrations down 1

# Check version
migrate -database "postgres://..." -path migrations version
```

---

## Lab 03: Worker Service & Inter-Service Communication

### Exercise 3a: Worker Polling & Graceful Shutdown

**Expected Worker Structure:**

```
worker-service/
  main.go
  go.mod
  go.sum
  worker/
    worker.go       # Worker struct, Start, Stop, poll loop
    processor.go    # Task processing logic
  repository/
    task_repo.go    # Database operations
  config/
    config.go       # Environment variable loading
```

**Expected Worker Implementation (worker/worker.go):**

```go
package worker

import (
    "context"
    "log"
    "time"

    "github.com/flowforge/worker-service/repository"
)

type Worker struct {
    repo         repository.TaskRepository
    pollInterval time.Duration
    workerID     string
}

func New(repo repository.TaskRepository, pollInterval time.Duration, workerID string) *Worker {
    return &Worker{
        repo:         repo,
        pollInterval: pollInterval,
        workerID:     workerID,
    }
}

func (w *Worker) Start(ctx context.Context) {
    log.Printf("worker %s starting with poll interval %v", w.workerID, w.pollInterval)

    ticker := time.NewTicker(w.pollInterval)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            log.Printf("worker %s shutting down...", w.workerID)
            return
        case <-ticker.C:
            w.pollAndProcess(ctx)
        }
    }
}

func (w *Worker) pollAndProcess(ctx context.Context) {
    task, err := w.repo.ClaimNextTask(ctx, w.workerID)
    if err != nil {
        log.Printf("error claiming task: %v", err)
        return
    }
    if task == nil {
        // No pending tasks
        return
    }

    log.Printf("worker %s claimed task %s: %s", w.workerID, task.ID, task.Title)
    start := time.Now()

    // Process the task (simulate work)
    err = w.processTask(ctx, task)

    duration := time.Since(start)

    if err != nil {
        log.Printf("task %s failed after %v: %v", task.ID, duration, err)
        w.repo.UpdateTaskStatus(ctx, task.ID, "failed")
    } else {
        log.Printf("task %s completed in %v", task.ID, duration)
        w.repo.UpdateTaskStatus(ctx, task.ID, "completed")
    }
}

func (w *Worker) processTask(ctx context.Context, task *models.Task) error {
    // Simulate work (2-5 seconds)
    select {
    case <-time.After(3 * time.Second):
        return nil // Task processed successfully
    case <-ctx.Done():
        return ctx.Err() // Shutdown requested
    }
}
```

**Expected main.go:**

```go
package main

import (
    "context"
    "log"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/flowforge/worker-service/config"
    "github.com/flowforge/worker-service/repository"
    "github.com/flowforge/worker-service/worker"
)

func main() {
    cfg := config.Load()

    db, err := repository.NewPostgresDB(cfg.DatabaseURL)
    if err != nil {
        log.Fatalf("failed to connect to database: %v", err)
    }
    defer db.Close()

    repo := repository.NewPostgresTaskRepo(db)

    pollInterval, err := time.ParseDuration(cfg.PollInterval)
    if err != nil {
        log.Fatalf("invalid poll interval: %v", err)
    }

    w := worker.New(repo, pollInterval, cfg.WorkerID)

    // Context with signal cancellation
    ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
    defer cancel()

    log.Println("worker-service starting...")
    w.Start(ctx)
    log.Println("worker-service shutdown complete")
}
```

### Exercise 3b: Inter-Service Queue (SELECT FOR UPDATE SKIP LOCKED)

**Expected ClaimNextTask Implementation:**

```go
func (r *PostgresTaskRepo) ClaimNextTask(ctx context.Context, workerID string) (*models.Task, error) {
    tx, err := r.db.BeginTx(ctx, nil)
    if err != nil {
        return nil, fmt.Errorf("failed to begin transaction: %w", err)
    }
    defer tx.Rollback() // Rollback if not committed

    task := &models.Task{}
    err = tx.QueryRowContext(ctx, `
        SELECT id, title, description, status, created_at, updated_at
        FROM tasks
        WHERE status = 'pending'
        ORDER BY created_at
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    `).Scan(&task.ID, &task.Title, &task.Description, &task.Status,
        &task.CreatedAt, &task.UpdatedAt)

    if err == sql.ErrNoRows {
        return nil, nil // No pending tasks
    }
    if err != nil {
        return nil, fmt.Errorf("failed to select task: %w", err)
    }

    // Update status to processing and assign worker
    _, err = tx.ExecContext(ctx, `
        UPDATE tasks
        SET status = 'processing', assigned_worker = $1, updated_at = NOW()
        WHERE id = $2
    `, workerID, task.ID)
    if err != nil {
        return nil, fmt.Errorf("failed to claim task: %w", err)
    }

    if err := tx.Commit(); err != nil {
        return nil, fmt.Errorf("failed to commit: %w", err)
    }

    task.Status = "processing"
    return task, nil
}
```

**Expected Stuck Task Recovery:**

```sql
-- Recovery query: reset tasks stuck in processing for > 10 minutes
UPDATE tasks
SET status = 'pending', assigned_worker = NULL, updated_at = NOW()
WHERE status = 'processing'
  AND updated_at < NOW() - INTERVAL '10 minutes';
```

**End-to-End Test Flow:**

```bash
# Terminal 1: Start api-service
cd project/api-service && go run main.go

# Terminal 2: Start worker-service
cd project/worker-service && go run main.go

# Terminal 3: Create tasks and observe
curl -X POST http://localhost:8080/tasks -H "Content-Type: application/json" \
  -d '{"title":"Send invoice","description":"Send January invoice to client"}'

curl -X POST http://localhost:8080/tasks -H "Content-Type: application/json" \
  -d '{"title":"Generate report","description":"Q4 performance report"}'

# Wait for worker to process...
sleep 10

# Check task status
curl http://localhost:8080/tasks | python3 -m json.tool
# Should show both tasks with status "completed"
```

---

## Lab 04: Configuration, Scripts & Logging

### Exercise 4a: 12-Factor Configuration

**Expected Config Package (config/config.go):**

```go
package config

import (
    "fmt"
    "os"
    "strings"
)

type Config struct {
    DatabaseURL  string
    Port         string
    LogLevel     string
    PollInterval string // worker only
    WorkerID     string // worker only
}

func Load() *Config {
    var errors []string

    databaseURL := os.Getenv("DATABASE_URL")
    if databaseURL == "" {
        errors = append(errors, "DATABASE_URL is required")
    }

    port := os.Getenv("API_PORT")
    if port == "" {
        port = "8080"
    }

    logLevel := os.Getenv("LOG_LEVEL")
    if logLevel == "" {
        logLevel = "info"
    }

    if len(errors) > 0 {
        fmt.Fprintf(os.Stderr, "configuration errors:\n  %s\n", strings.Join(errors, "\n  "))
        os.Exit(1)
    }

    return &Config{
        DatabaseURL: databaseURL,
        Port:        port,
        LogLevel:    logLevel,
    }
}
```

**Expected .env.example:**

```bash
# FlowForge Configuration
# Copy this file to .env and fill in your values
# NEVER commit .env to version control!

# Database
DATABASE_URL=postgres://flowforge_user:your_password@localhost:5432/flowforge?sslmode=disable

# API Service
API_PORT=8080

# Worker Service
WORKER_POLL_INTERVAL=5s
WORKER_ID=worker-1

# Logging
LOG_LEVEL=info  # Options: debug, info, warn, error
```

### Exercise 4b: Python Automation Scripts

**Expected seed-database.py:**

```python
#!/usr/bin/env python3
"""FlowForge Database Seeder - Populates database with test data."""

import argparse
import os
import random
import sys

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

TASK_TITLES = [
    "Process monthly report",
    "Send invoice to client",
    "Generate Q4 analytics",
    "Update user documentation",
    "Run database backup",
    "Deploy staging environment",
    "Review pull requests",
    "Update SSL certificates",
    "Optimize database queries",
    "Clean up temporary files",
]

STATUSES = ["pending", "pending", "pending", "completed", "completed", "failed", "processing"]


def main():
    parser = argparse.ArgumentParser(description="Seed FlowForge database with test data")
    parser.add_argument("--count", type=int, default=20, help="Number of tasks to create (default: 20)")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        sys.exit(1)

    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        if args.clear:
            cur.execute("TRUNCATE TABLE tasks")
            conn.commit()
            print("Cleared existing data")

        status_counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}

        for i in range(args.count):
            title = random.choice(TASK_TITLES)
            description = f"Auto-generated task #{i+1}: {title}"
            status = random.choice(STATUSES)
            status_counts[status] += 1

            cur.execute(
                "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s)",
                (title, description, status),
            )

        conn.commit()
        cur.close()
        conn.close()

        summary = ", ".join(f"{v} {k}" for k, v in status_counts.items())
        print(f"Created {args.count} tasks ({summary})")

    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to database: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Expected healthcheck.py:**

```python
#!/usr/bin/env python3
"""FlowForge Health Check - Verifies all services are running."""

import os
import sys

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

TIMEOUT = 5  # seconds


def check_api():
    api_url = os.environ.get("API_URL", "http://localhost:8080")
    try:
        resp = requests.get(f"{api_url}/health", timeout=TIMEOUT)
        if resp.status_code == 200:
            return True, "UP"
        return False, f"DOWN (status {resp.status_code})"
    except requests.ConnectionError:
        return False, "DOWN (connection refused)"
    except requests.Timeout:
        return False, "DOWN (timeout)"


def check_database():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return False, "DOWN (DATABASE_URL not set)"
    try:
        conn = psycopg2.connect(database_url, connect_timeout=TIMEOUT)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True, "UP"
    except psycopg2.OperationalError as e:
        return False, f"DOWN ({e})"


def main():
    results = {
        "api-service": check_api(),
        "postgresql": check_database(),
    }

    all_healthy = True
    for service, (healthy, status) in results.items():
        print(f"  {service}: {status}")
        if not healthy:
            all_healthy = False

    if all_healthy:
        print("\nAll services healthy")
        sys.exit(0)
    else:
        unhealthy = sum(1 for _, (h, _) in results.items() if not h)
        print(f"\n{unhealthy} of {len(results)} services unhealthy")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Expected cleanup.py:**

```python
#!/usr/bin/env python3
"""FlowForge Database Cleanup - Resets database to clean state."""

import argparse
import os
import sys

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Clean up FlowForge database")
    parser.add_argument("--confirm", action="store_true", help="Confirm deletion (required)")
    args = parser.parse_args()

    if not args.confirm:
        print("WARNING: This will delete ALL tasks from the database.")
        print("Run with --confirm to proceed.")
        sys.exit(0)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable is required")
        sys.exit(1)

    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM tasks")
        count = cur.fetchone()[0]

        cur.execute("TRUNCATE TABLE tasks")
        conn.commit()

        cur.close()
        conn.close()

        print(f"Deleted {count} tasks from database")

    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to database: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Exercise 4c: Structured JSON Logging

**Expected Structured Logging (using log/slog):**

```go
package main

import (
    "log/slog"
    "os"
)

func setupLogging(level string) {
    var logLevel slog.Level
    switch level {
    case "debug":
        logLevel = slog.LevelDebug
    case "warn":
        logLevel = slog.LevelWarn
    case "error":
        logLevel = slog.LevelError
    default:
        logLevel = slog.LevelInfo
    }

    handler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
        Level: logLevel,
    })
    logger := slog.New(handler)
    slog.SetDefault(logger)
}
```

**Expected Request ID Middleware:**

```go
package middleware

import (
    "context"
    "net/http"

    "github.com/google/uuid"
)

type contextKey string

const RequestIDKey contextKey = "request_id"

func RequestID(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = uuid.New().String()
        }

        ctx := context.WithValue(r.Context(), RequestIDKey, requestID)
        w.Header().Set("X-Request-ID", requestID)

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func GetRequestID(ctx context.Context) string {
    if id, ok := ctx.Value(RequestIDKey).(string); ok {
        return id
    }
    return "unknown"
}
```

**Expected Log Output:**

```json
{"time":"2024-01-15T10:30:45Z","level":"INFO","msg":"request received","service":"api-service","request_id":"abc-123","method":"POST","path":"/tasks"}
{"time":"2024-01-15T10:30:45Z","level":"INFO","msg":"task created","service":"api-service","request_id":"abc-123","task_id":"def-456","title":"Process report"}
{"time":"2024-01-15T10:30:50Z","level":"INFO","msg":"task claimed","service":"worker-service","task_id":"def-456","worker_id":"worker-1","request_id":"abc-123"}
{"time":"2024-01-15T10:30:53Z","level":"INFO","msg":"task completed","service":"worker-service","task_id":"def-456","worker_id":"worker-1","duration_ms":3012}
```

---

## Lab 05: Go Testing

### Exercise 5: Unit & Integration Tests

**Expected Test for Create Handler:**

```go
func TestCreateTask_ValidInput(t *testing.T) {
    repo := repository.NewMemoryRepository()
    handler := handlers.NewTaskHandler(repo)

    body := `{"title":"Test Task","description":"A test task"}`
    req := httptest.NewRequest("POST", "/tasks", strings.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    w := httptest.NewRecorder()

    handler.Create(w, req)

    if w.Code != http.StatusCreated {
        t.Errorf("expected status 201, got %d", w.Code)
    }

    var resp map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &resp)

    data := resp["data"].(map[string]interface{})
    if data["title"] != "Test Task" {
        t.Errorf("expected title 'Test Task', got %v", data["title"])
    }
    if data["status"] != "pending" {
        t.Errorf("expected status 'pending', got %v", data["status"])
    }
}

func TestCreateTask_MissingTitle(t *testing.T) {
    repo := repository.NewMemoryRepository()
    handler := handlers.NewTaskHandler(repo)

    body := `{"description":"no title"}`
    req := httptest.NewRequest("POST", "/tasks", strings.NewReader(body))
    w := httptest.NewRecorder()

    handler.Create(w, req)

    if w.Code != http.StatusBadRequest {
        t.Errorf("expected status 400, got %d", w.Code)
    }
}

func TestCreateTask_InvalidJSON(t *testing.T) {
    repo := repository.NewMemoryRepository()
    handler := handlers.NewTaskHandler(repo)

    body := `not json at all`
    req := httptest.NewRequest("POST", "/tasks", strings.NewReader(body))
    w := httptest.NewRecorder()

    handler.Create(w, req)

    if w.Code != http.StatusBadRequest {
        t.Errorf("expected status 400, got %d", w.Code)
    }
}

func TestGetTask_NotFound(t *testing.T) {
    repo := repository.NewMemoryRepository()
    handler := handlers.NewTaskHandler(repo)

    req := httptest.NewRequest("GET", "/tasks/nonexistent", nil)
    // Set chi URL param context
    rctx := chi.NewRouteContext()
    rctx.URLParams.Add("id", "nonexistent")
    req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

    w := httptest.NewRecorder()
    handler.Get(w, req)

    if w.Code != http.StatusNotFound {
        t.Errorf("expected status 404, got %d", w.Code)
    }
}

func TestHealthCheck(t *testing.T) {
    req := httptest.NewRequest("GET", "/health", nil)
    w := httptest.NewRecorder()

    handlers.HealthCheck(w, req)

    if w.Code != http.StatusOK {
        t.Errorf("expected status 200, got %d", w.Code)
    }
}
```

**Expected Integration Test:**

```go
// +build integration

func TestCreateAndGetTask_Integration(t *testing.T) {
    db := setupTestDB(t) // Connects to flowforge_test database
    defer db.Close()

    repo := repository.NewPostgresTaskRepo(db)
    handler := handlers.NewTaskHandler(repo)

    // Create a task
    body := `{"title":"Integration Test Task","description":"Testing DB integration"}`
    createReq := httptest.NewRequest("POST", "/tasks", strings.NewReader(body))
    createReq.Header.Set("Content-Type", "application/json")
    createW := httptest.NewRecorder()
    handler.Create(createW, createReq)

    if createW.Code != http.StatusCreated {
        t.Fatalf("create failed: status %d, body: %s", createW.Code, createW.Body.String())
    }

    // Parse created task to get ID
    var createResp map[string]interface{}
    json.Unmarshal(createW.Body.Bytes(), &createResp)
    data := createResp["data"].(map[string]interface{})
    taskID := data["id"].(string)

    // Get the task
    getReq := httptest.NewRequest("GET", "/tasks/"+taskID, nil)
    rctx := chi.NewRouteContext()
    rctx.URLParams.Add("id", taskID)
    getReq = getReq.WithContext(context.WithValue(getReq.Context(), chi.RouteCtxKey, rctx))

    getW := httptest.NewRecorder()
    handler.Get(getW, getReq)

    if getW.Code != http.StatusOK {
        t.Fatalf("get failed: status %d", getW.Code)
    }

    var getResp map[string]interface{}
    json.Unmarshal(getW.Body.Bytes(), &getResp)
    getData := getResp["data"].(map[string]interface{})

    if getData["title"] != "Integration Test Task" {
        t.Errorf("expected title 'Integration Test Task', got %v", getData["title"])
    }
}

func setupTestDB(t *testing.T) *sql.DB {
    t.Helper()
    dbURL := os.Getenv("TEST_DATABASE_URL")
    if dbURL == "" {
        t.Skip("TEST_DATABASE_URL not set, skipping integration tests")
    }
    db, err := sql.Open("postgres", dbURL)
    if err != nil {
        t.Fatalf("failed to connect to test database: %v", err)
    }
    // Clean up before test
    db.Exec("TRUNCATE TABLE tasks")
    return db
}
```

**Running Tests:**

```bash
# Unit tests only
go test ./...

# With coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out  # Opens coverage in browser
go tool cover -func=coverage.out  # Summary in terminal

# Integration tests (requires TEST_DATABASE_URL)
TEST_DATABASE_URL="postgres://flowforge_user:pass@localhost:5432/flowforge_test?sslmode=disable" \
  go test -tags=integration ./...

# Expected coverage output:
# github.com/flowforge/api-service/handlers    78.5%
# github.com/flowforge/api-service/repository  72.3%
# github.com/flowforge/api-service/config      85.0%
# total:                                        74.1%
```
