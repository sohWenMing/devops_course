# Lab 04: Configuration, Python Scripts & Structured Logging

> **Module**: 3 -- Building FlowForge in Go  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Lab 03 (both services working end-to-end). Read the [12-Factor App Configuration](#), [Python Automation Scripts](#), and [Structured Logging](#) sections of the Module 3 README

---

## Overview

In this lab, you'll harden FlowForge for production-readiness. You'll externalize all configuration to environment variables (no hardcoded values), write Python automation scripts for seeding data and checking health, and add structured JSON logging with request IDs that let you trace a request across both services.

---

## Exercise 4a: 12-Factor Configuration

### Objectives

- Audit both services for hardcoded configuration values
- Externalize all configuration to environment variables
- Implement startup validation that fails fast if required config is missing
- Create a `.env.example` file documenting every variable

### What You'll Do

**Part 1: Config Audit**

1. Review all code in api-service and worker-service. Find every hardcoded value that could differ between environments:
   - Database connection details (host, port, user, password, database name)
   - Server port
   - Worker poll interval
   - Log level
   - Any timeouts, retry counts, or thresholds
   - Think about: What else might change between development and production?

2. Make a list of every configuration value with:
   - Variable name (e.g., `DATABASE_URL`, `API_PORT`)
   - Description of what it controls
   - Whether it's required or optional
   - Default value (if optional)
   - Example value

**Part 2: Implement Config Loading**

3. Create a configuration package/module in each service that:
   - Reads all configuration from environment variables at startup
   - Validates that all required variables are set
   - Validates formats where appropriate (e.g., port is a number, poll interval is a valid duration)
   - Fails immediately with a clear error message if validation fails
   - Think about: Is it better to fail on the first missing variable, or collect all errors and report them at once?

4. Replace every hardcoded value in both services with config references.

5. Verify: search the entire codebase for any remaining hardcoded values. There should be zero.

**Part 3: Documentation**

6. Create a `.env.example` file at the project root that documents every environment variable:
   - Include comments explaining each variable
   - Include example values (not real passwords!)
   - This file should be committed to git (it contains no secrets, just the template)

7. Create a `.env` file (which should NOT be committed -- add it to `.gitignore`):
   - Copy from `.env.example`
   - Fill in your actual development values
   - Think about: Why should `.env` never be committed to version control?

**Part 4: Verify 12-Factor Compliance**

8. Walk through all 12 factors from the README and check how FlowForge complies:
   - For each factor, write a one-sentence explanation of how FlowForge follows it
   - Identify any factors where FlowForge doesn't fully comply yet (that's okay -- some will be addressed in later modules)

### Expected Outcome

- Both services read ALL configuration from environment variables
- Startup fails fast with clear messages if required config is missing
- `.env.example` documents every variable
- `.env` is in `.gitignore`
- Zero hardcoded configuration values in the codebase

### Checkpoint Questions

> Answer these without looking at notes:
> 1. List all 12 factors from memory. For each one, give a one-line explanation.
> 2. Your colleague hardcoded `"localhost:5432"` in the database connection. Explain to them why this is a problem and what they should do instead.
> 3. What's the difference between `.env`, `.env.example`, and `.env.production`?
> 4. How does the 12-Factor principle of "config in the environment" relate to Docker (Module 4) and Kubernetes ConfigMaps (Module 8)?
> 5. A new developer clones the repo. What do they need to do to run FlowForge? How does `.env.example` help?

---

## Exercise 4b: Python Automation Scripts

### Objectives

- Write a database seeding script that populates FlowForge with test data
- Write a health check script that verifies all services are running
- Write a cleanup script that resets the system to a clean state
- Practice Python scripting with environment variable configuration

### What You'll Do

**Part 1: seed-database.py**

1. Navigate to `project/scripts/`. Examine the starter files.

2. Implement `seed-database.py`:
   - Connect to PostgreSQL using the same `DATABASE_URL` environment variable as the Go services
   - Insert a configurable number of test tasks with realistic data
     - Vary the titles, descriptions, and statuses
     - Include tasks in each status: pending, processing, completed, failed
   - Accept command-line arguments:
     - `--count N`: Number of tasks to create (default: 20)
     - `--clear`: Clear existing data before seeding
   - Print a summary of what was created
   - Think about: What Python library connects to PostgreSQL? How do you install it?

3. Test: Run the script, then verify via `curl` to the api-service that the tasks appear.

**Part 2: healthcheck.py**

4. Implement `healthcheck.py`:
   - Check that the api-service is reachable (HTTP GET to `/health`)
   - Check that the worker-service is running (optional: you could add a `/health` endpoint to the worker, or check via the process list)
   - Check that PostgreSQL is reachable (direct connection test)
   - Report the status of each component: UP or DOWN with details
   - Exit with code 0 if all healthy, code 1 if any unhealthy
   - Think about: What timeout should you use for health checks? Too short gives false negatives, too long makes the check slow.

5. Test: Run the script with all services up (should report all UP), then stop one service and run again (should report it as DOWN and exit with code 1).

**Part 3: cleanup.py**

6. Implement `cleanup.py`:
   - Connect to PostgreSQL
   - Delete all data from the tasks table (or truncate)
   - Accept a `--confirm` flag (don't delete without it -- safety!)
   - Print what was deleted
   - Exit cleanly
   - Think about: Why require a `--confirm` flag? What happens if this runs in production by accident?

7. Test: Seed data, verify it exists, run cleanup, verify it's gone.

**Part 4: Script Quality**

8. Ensure all three scripts:
   - Have a clear `--help` message (use `argparse`)
   - Read configuration from environment variables
   - Handle errors gracefully (don't crash with a stack trace if PostgreSQL is down)
   - Return meaningful exit codes (0 = success, 1 = failure)
   - Include a module docstring explaining what the script does

### Expected Outcome

- `seed-database.py` populates the database with configurable test data
- `healthcheck.py` verifies all services are running and reports status
- `cleanup.py` resets the database (with safety confirmation)
- All scripts use environment variables for configuration
- All scripts have `--help`, error handling, and meaningful exit codes

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What Python library connects to PostgreSQL? How do you install it?
> 2. Your `healthcheck.py` reports the api-service as DOWN. What's the first thing you'd check? (Think back to Modules 1-2: is the process running? Is the port listening? Is there a firewall issue?)
> 3. Write a new Python script from scratch: `load-test.py` that sends N concurrent POST requests to the api-service and reports the success rate and average response time. Don't reference the existing scripts.
> 4. Why do the Python scripts use the same `DATABASE_URL` variable as the Go services?
> 5. What's the difference between `sys.exit(0)` and `sys.exit(1)` and why does it matter for automation?

---

## Exercise 4c: Structured JSON Logging with Request IDs

### Objectives

- Replace plain-text logging with structured JSON logging in both Go services
- Add request IDs that are generated at the API entry point and propagated through the system
- Add contextual fields to every log entry (timestamp, level, service name, caller)
- Demonstrate request tracing across services

### What You'll Do

**Part 1: Structured Logging Setup**

1. Choose a structured logging library for Go:
   - Options: `log/slog` (Go 1.21+ standard library), `zerolog`, `zap`
   - `log/slog` is recommended (no external dependency, standard library)
   - Think about: What are the trade-offs between standard library logging and third-party loggers?

2. Replace all existing `log.Println`/`fmt.Println` calls in api-service with structured log calls:
   - Every log entry should include: `timestamp`, `level`, `msg`, `service` (e.g., "api-service")
   - Request-related logs should also include: `method`, `path`, `status`, `duration_ms`
   - Error logs should include: `error` (the error message)

3. Do the same for worker-service:
   - Include: `timestamp`, `level`, `msg`, `service` (e.g., "worker-service")
   - Task-related logs should include: `task_id`, `task_title`, `duration_ms`

**Part 2: Request IDs**

4. Implement request ID generation in the api-service:
   - Generate a unique ID (UUID) for every incoming HTTP request
   - Store it in the request context
   - Include it in every log entry for that request
   - Return it in the response headers (`X-Request-ID`)
   - Think about: What Go mechanism lets you pass values through the request lifecycle?

5. Create middleware that:
   - Generates the request ID (or uses one from the `X-Request-ID` header if the client provides it)
   - Injects it into the request context
   - Adds it to the response headers

**Part 3: Cross-Service Tracing**

6. When the api-service creates a task, store the request ID in the task record (add a column or use an existing metadata field).

7. When the worker-service picks up a task, include the original request ID in its log entries.

8. Test the full tracing flow:
   - Create a task via the api-service (note the request ID from the response header)
   - Watch the worker process the task
   - Search both services' logs for that request ID
   - You should see the complete lifecycle: request received → task created → task claimed → task processed → task completed

**Part 4: Log Output Configuration**

9. Make the log output configurable:
   - `LOG_LEVEL` environment variable controls the minimum log level (debug, info, warn, error)
   - In development, you might want pretty-printed output
   - In production, JSON is essential for log aggregation

### Expected Outcome

- Both services output structured JSON logs to stdout
- Every API request has a unique request ID
- Request IDs appear in both api-service and worker-service logs for the same task
- You can trace a request's journey from API call to task completion using the request ID
- Log level is configurable via environment variable

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Given a log file with 10,000 entries, how would you find all log entries related to a single user request?
> 2. Why is JSON logging better than plain text for production systems?
> 3. Explain the difference between logs, metrics, and traces. When would you use each?
> 4. Your worker-service processed a task but the result seems wrong. Using only the logs (no debugger), trace the issue. What fields would you search for?
> 5. Why do both services log to stdout instead of to a file? (Hint: think about containers and the 12-Factor methodology)

---

## What's Next?

Once all three exercises are complete, move on to [Lab 05: Testing](lab-05-testing.md), where you'll write unit and integration tests for the api-service and aim for >70% code coverage.
