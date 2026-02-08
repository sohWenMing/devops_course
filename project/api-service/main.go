package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

// FlowForge API Service
//
// This is the starter skeleton for the FlowForge api-service.
// It compiles and runs, but doesn't do anything useful yet.
// Your job is to fill in the TODOs through the Module 3 labs.

func main() {
	fmt.Println("FlowForge api-service starting...")

	// TODO (Lab 01, Exercise 1b): Replace this basic setup with a proper router (chi or gin)
	// - Set up route definitions matching your OpenAPI spec
	// - Add middleware: logging, panic recovery, content-type
	// - Implement graceful shutdown with signal handling

	// TODO (Lab 02, Exercise 2a): Add database connection
	// - Read DATABASE_URL from environment variable
	// - Open connection pool with sql.Open()
	// - Configure pool settings (MaxOpenConns, MaxIdleConns, ConnMaxLifetime)
	// - Verify connection with db.Ping()

	// TODO (Lab 04, Exercise 4a): Load all config from environment variables
	// - Read API_PORT, DATABASE_URL, LOG_LEVEL from env
	// - Validate required variables are set
	// - Fail fast with clear error messages if config is invalid

	// TODO (Lab 04, Exercise 4c): Replace fmt.Println with structured JSON logging
	// - Use log/slog, zerolog, or zap
	// - Include: timestamp, level, service name, request ID

	port := os.Getenv("API_PORT")
	if port == "" {
		port = "8080"
	}

	// Basic health check endpoint -- replace with router-based routing in Lab 01
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		// TODO (Lab 02): Add database health check
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status":"ok","service":"api-service"}`)
	})

	// TODO (Lab 01, Exercise 1b): Add these route handlers:
	// GET    /tasks        → List all tasks (with pagination)
	// POST   /tasks        → Create a new task
	// GET    /tasks/{id}   → Get a specific task
	// PUT    /tasks/{id}   → Update a task
	// DELETE /tasks/{id}   → Delete a task

	log.Printf("api-service listening on :%s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}

// TODO (Lab 01, Exercise 1b): Create handler functions in a separate package
// Example structure:
//   handlers/
//     tasks.go      → CreateTask, GetTask, ListTasks, UpdateTask, DeleteTask
//     health.go     → HealthCheck
//   models/
//     task.go       → Task struct, CreateTaskRequest, TaskResponse
//   middleware/
//     logging.go    → Request logging middleware
//     requestid.go  → Request ID generation middleware
//   repository/
//     task_repo.go  → Database operations for tasks

// TODO (Lab 02, Exercise 2a): Create repository layer
// type TaskRepository interface {
//     Create(ctx context.Context, task *Task) error
//     GetByID(ctx context.Context, id string) (*Task, error)
//     List(ctx context.Context, page, limit int) ([]Task, int, error)
//     Update(ctx context.Context, id string, task *Task) error
//     Delete(ctx context.Context, id string) error
// }

// TODO (Lab 05): Write tests
// handlers/tasks_test.go  → Unit tests for each handler
// repository/task_repo_test.go → Integration tests with real DB
