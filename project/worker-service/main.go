package main

import (
	"fmt"
	"log"
	"os"
)

// FlowForge Worker Service
//
// This is the starter skeleton for the FlowForge worker-service.
// It compiles and runs, but doesn't do anything useful yet.
// Your job is to fill in the TODOs through the Module 3 labs.

func main() {
	fmt.Println("FlowForge worker-service starting...")

	// TODO (Lab 03, Exercise 3a): Implement the polling loop
	// 1. Connect to PostgreSQL (read DATABASE_URL from env)
	// 2. Start a loop that:
	//    a. Queries for pending tasks
	//    b. Claims a task (update status to 'processing')
	//    c. Processes the task (simulate work for now)
	//    d. Updates status to 'completed' or 'failed'
	//    e. Sleeps for WORKER_POLL_INTERVAL before next poll

	// TODO (Lab 03, Exercise 3a): Implement graceful shutdown
	// - Listen for SIGTERM and SIGINT using os/signal
	// - Use context.Context to propagate cancellation
	// - When signal received:
	//   1. Stop picking up new tasks
	//   2. Finish processing current task
	//   3. Close database connection
	//   4. Exit cleanly

	// TODO (Lab 03, Exercise 3b): Use SELECT FOR UPDATE SKIP LOCKED
	// - Wrap task claiming in a transaction
	// - SELECT ... WHERE status = 'pending' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED
	// - This prevents multiple workers from claiming the same task

	// TODO (Lab 04, Exercise 4a): Load all config from environment variables
	// - Read DATABASE_URL, WORKER_POLL_INTERVAL, LOG_LEVEL from env
	// - Validate required variables are set
	// - Fail fast with clear error messages

	// TODO (Lab 04, Exercise 4c): Replace fmt.Println with structured JSON logging
	// - Include: timestamp, level, service name, task_id, duration

	pollInterval := os.Getenv("WORKER_POLL_INTERVAL")
	if pollInterval == "" {
		pollInterval = "5s"
	}

	log.Printf("worker-service configured with poll interval: %s", pollInterval)
	log.Println("worker-service has no implementation yet -- fill in the TODOs!")

	// Placeholder: Keep the process running so it can be tested
	// Replace this with the actual polling loop in Lab 03
	select {}
}

// TODO (Lab 03, Exercise 3a): Create the worker package
// Example structure:
//   worker/
//     worker.go     → Worker struct, Start(), Stop(), poll loop
//     processor.go  → Task processing logic
//   repository/
//     task_repo.go  → Database operations (claim task, update status)
//   config/
//     config.go     → Environment variable loading and validation

// TODO (Lab 03, Exercise 3b): Implement the queue pattern
// func (w *Worker) claimNextTask(ctx context.Context) (*Task, error) {
//     tx, err := w.db.BeginTx(ctx, nil)
//     // SELECT id, title, description FROM tasks
//     // WHERE status = 'pending'
//     // ORDER BY created_at
//     // LIMIT 1
//     // FOR UPDATE SKIP LOCKED
//     //
//     // UPDATE tasks SET status = 'processing', assigned_worker = $1 WHERE id = $2
//     // COMMIT or ROLLBACK
// }
