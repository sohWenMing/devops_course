# Lab 03: Worker Service & Inter-Service Communication

> **Module**: 3 -- Building FlowForge in Go  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Lab 02 (api-service persists tasks to PostgreSQL). Read the [Background Worker Pattern](#) and [Inter-Service Communication](#) sections of the Module 3 README

---

## Overview

In this lab, you'll build the worker-service -- a background process that polls PostgreSQL for pending tasks, claims them, processes them (simulated work), and updates their status. You'll implement graceful shutdown and then wire up the full inter-service communication flow: api-service enqueues tasks, worker-service picks them up.

---

## Exercise 3a: Worker Service -- Polling Pattern & Graceful Shutdown

### Objectives

- Build the worker-service as a standalone Go application
- Implement the polling loop that checks for pending tasks
- Implement task claiming and status updates
- Implement graceful shutdown that finishes the current task before exiting

### What You'll Do

**Part 1: Worker Skeleton**

1. Navigate to `project/worker-service/`. Examine the starter code (`main.go` and `go.mod`).

2. Set up the worker-service project:
   - Add the PostgreSQL driver dependency (same driver as api-service)
   - Create a sensible package structure. Think about:
     - Where does the polling loop logic live?
     - Where do the database queries live?
     - Where does the task processing logic live?
     - How does configuration get loaded?

3. Write the database connection code:
   - Read the connection string from `DATABASE_URL` environment variable
   - Open a connection pool with appropriate settings
   - Verify connectivity at startup

**Part 2: The Polling Loop**

4. Implement the polling loop. The worker should:
   - Query the database for tasks with `status = 'pending'`
   - If a task is found, claim it (update status to `processing`)
   - Process the task (for now, simulate work with a `time.Sleep` of 2-5 seconds)
   - Update the task status to `completed` (or `failed` if processing fails)
   - If no tasks are found, wait for the poll interval before checking again
   - The poll interval should be configurable via environment variable (`WORKER_POLL_INTERVAL`)

5. Think about these questions while implementing:
   - What happens if two worker instances poll at the same time and both find the same pending task?
   - What happens if the worker crashes while processing a task? What status is the task left in?
   - How do you prevent the polling loop from consuming 100% CPU when there are no tasks?

**Part 3: Graceful Shutdown**

6. Implement graceful shutdown:
   - Listen for SIGTERM and SIGINT signals
   - When a signal is received:
     - Stop the polling loop (don't pick up new tasks)
     - If currently processing a task, wait for it to finish
     - Close the database connection
     - Log that shutdown is complete
     - Exit with code 0

7. Test graceful shutdown:
   - Start the worker-service
   - Create several tasks via the api-service
   - While the worker is processing a task, send SIGTERM (`kill -15 <PID>`)
   - Verify the worker finishes the current task before exiting
   - Verify no tasks are left in `processing` status

**Part 4: Worker Logging**

8. Add clear logging to the worker so you can see what's happening:
   - Log when the worker starts (with poll interval)
   - Log when it polls and finds no tasks
   - Log when it claims a task (with task ID and title)
   - Log when it completes a task (with duration)
   - Log when shutdown is initiated and completed

### Expected Outcome

- worker-service starts, connects to PostgreSQL, and polls for tasks
- When tasks are found, it claims and processes them
- Tasks transition: pending → processing → completed
- Graceful shutdown works: current task completes, worker exits cleanly
- Worker logs show clear activity trace

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Explain the polling vs push model trade-offs. When would you use each?
> 2. What Go construct do you use to make the polling loop respond to shutdown signals? (Hint: it involves channels)
> 3. Your worker has been running for 3 hours. How would you verify it's still working correctly using only command-line tools from Modules 1-2?
> 4. Add a new task type to the worker (e.g., "email" tasks that log a different message) without copying existing handler code. Sketch the approach.
> 5. What is `context.Context` and why is it essential for graceful shutdown?

---

## Exercise 3b: Inter-Service Communication via PostgreSQL Queue

### Objectives

- Implement the `SELECT FOR UPDATE SKIP LOCKED` pattern for safe concurrent task claiming
- Wire up the full flow: api-service creates tasks, worker-service processes them
- Handle edge cases: concurrent workers, crashed workers, stuck tasks
- Verify the data flow from API request to task completion

### What You'll Do

**Part 1: Implement the Queue Pattern**

1. Update the worker-service's task claiming query to use `SELECT FOR UPDATE SKIP LOCKED`:
   - The query should select one pending task, ordered by `created_at`
   - `FOR UPDATE` locks the row so no other worker can claim it
   - `SKIP LOCKED` skips rows that are already locked by other workers
   - This must happen within a transaction

2. Think about and implement:
   - What does the transaction boundary look like? (BEGIN → SELECT → process → UPDATE → COMMIT)
   - What happens if processing fails? (The transaction should ROLLBACK and the task should remain `pending` or become `failed`)
   - Should you update the `assigned_worker` column when claiming? (How would you identify which worker instance claimed a task?)

**Part 2: End-to-End Flow**

3. Test the complete flow:
   - Start the api-service
   - Start the worker-service
   - Use `curl` to create several tasks via the api-service
   - Watch the worker-service logs as it picks up and processes tasks
   - Query the database directly to verify task status transitions
   - Use the api-service `GET /tasks` endpoint to see completed tasks

4. Test with multiple tasks:
   - Create 10 tasks rapidly using a bash loop or a quick script
   - Observe the worker processing them one by one
   - Verify all 10 eventually reach `completed` status

**Part 3: Edge Cases**

5. Test crash recovery:
   - Start a task processing, then kill the worker forcefully with `kill -9` (SIGKILL)
   - Check the database: what status is the task in?
   - Think about: How would you detect and recover from stuck tasks?
   - Implement a simple "stuck task" recovery mechanism:
     - If a task has been in `processing` status for more than X minutes, consider it failed and reset to `pending`
     - This could be a SQL query run periodically or a cleanup function

6. Test concurrent workers (stretch goal):
   - Start two instances of worker-service (on different ports or with different worker IDs)
   - Create 10 tasks
   - Verify that both workers pick up tasks without conflicts (no task processed twice)
   - Observe the `SKIP LOCKED` behavior in action

**Part 4: Data Flow Documentation**

7. Draw a diagram (text-based is fine) showing the complete data flow:
   - Client sends POST /tasks
   - api-service validates, creates task in DB with status=pending
   - worker-service polls, finds pending task
   - worker-service claims task (SELECT FOR UPDATE SKIP LOCKED)
   - worker-service processes task
   - worker-service updates status to completed
   - Client sends GET /tasks/{id} and sees completed status

### Expected Outcome

- The complete api-service → PostgreSQL → worker-service flow works end-to-end
- Tasks created via the API are processed by the worker and marked as completed
- `SELECT FOR UPDATE SKIP LOCKED` prevents double-claiming
- You can explain what happens when a worker crashes mid-processing
- You have a data flow diagram documenting the entire flow

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Explain `SELECT FOR UPDATE SKIP LOCKED` -- what does each keyword do?
> 2. Draw the data flow from "user creates task" to "worker completes task" without looking at code.
> 3. What happens if the worker crashes after claiming a task but before completing it? How would you fix this?
> 4. You add a second worker instance. How does `SKIP LOCKED` prevent them from claiming the same task?
> 5. At what scale would you replace PostgreSQL-as-queue with a dedicated message queue? What would you choose and why?

---

## What's Next?

Once both exercises are complete, move on to [Lab 04: Configuration, Scripts & Logging](lab-04-config-scripts-logging.md), where you'll externalize configuration, write Python automation scripts, and add structured JSON logging.
