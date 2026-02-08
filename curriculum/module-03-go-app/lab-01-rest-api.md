# Lab 01: REST API Design & Go HTTP Server

> **Module**: 3 -- Building FlowForge in Go  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [REST API Design Principles](#) and [Go HTTP Server](#) sections of the Module 3 README

---

## Overview

In this lab, you'll design the FlowForge REST API from scratch, document it in OpenAPI format, and then implement it as a Go HTTP server using a router. By the end, you'll have a running api-service that handles HTTP requests -- though it won't persist data to a database yet (that comes in Lab 02).

---

## Exercise 1a: REST API Design & OpenAPI Documentation

### Objectives

- Design a RESTful API for the FlowForge task management system
- Choose appropriate HTTP verbs, URL patterns, status codes, and response formats
- Document the API in OpenAPI (Swagger) format before writing any code

### What You'll Do

**Part 1: Design the API**

1. Design endpoints for the FlowForge task management API. Think about:
   - What resources does FlowForge manage? (Hint: tasks, and later workers/projects)
   - For each resource, what CRUD operations make sense?
   - What HTTP method maps to each operation?
   - What should the URL pattern be for each endpoint?
   - What status codes should each endpoint return for success and error cases?

2. Define the data model for a **task**:
   - What fields does a task have?
   - Which fields are set by the client vs the server?
   - What are the possible status values and what do they mean?
   - What format should timestamps be in?

3. Design the response format:
   - How will successful responses look?
   - How will error responses look? (Think: what information does a client need to handle an error?)
   - How will list endpoints handle pagination?

4. Design a health check endpoint:
   - What should `/health` return?
   - What constitutes "healthy"? (Hint: think about database connectivity)
   - What status code should an unhealthy service return?

**Part 2: Document in OpenAPI**

5. Create an OpenAPI specification file (YAML format) that documents:
   - All endpoints with their HTTP methods
   - Request body schemas (for POST and PUT)
   - Response schemas for each status code
   - The task data model
   - Query parameters for pagination on list endpoints

   Place this file at `project/api-service/openapi.yaml`.

   If you haven't used OpenAPI before, start with the [Swagger Editor](https://editor.swagger.io/) to get familiar with the format. The [OpenAPI 3.0 specification](https://spec.openapis.org/oas/v3.0.3) is the reference.

### Expected Outcome

- A document or notes file describing your API design decisions and rationale
- An `openapi.yaml` file that fully describes the FlowForge API
- You can explain why you chose each endpoint, method, status code, and response format

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What's the difference between PUT and PATCH? Which one did you choose for updating tasks and why?
> 2. Why should `POST /tasks` return 201 instead of 200?
> 3. A client sends `GET /tasks/999` and task 999 doesn't exist. What status code do you return and why?
> 4. Given a new domain (e.g., "inventory system" with products and warehouses), sketch the REST endpoints in under 5 minutes.
> 5. Why do you document the API *before* writing code?

---

## Exercise 1b: Go HTTP Server Implementation

### Objectives

- Implement the api-service HTTP server in Go using chi (or gin)
- Set up routing for all FlowForge API endpoints
- Add middleware for logging and panic recovery
- Implement graceful shutdown on SIGTERM/SIGINT
- Return hardcoded/in-memory responses (database integration comes in Lab 02)

### What You'll Do

**Part 1: Project Setup**

1. Navigate to `project/api-service/`. Examine the starter code (`main.go` and `go.mod`).

2. Initialize the project:
   - Add a router dependency (chi or gin) to your Go module
   - Create a sensible package structure. Think about:
     - Where should your handler functions live?
     - Where should your data models (structs) live?
     - Where should your middleware live?
     - Where should your server configuration live?

**Part 2: Implement the Router**

3. Set up the HTTP router with:
   - Route definitions matching your OpenAPI spec from Exercise 1a
   - Method-based routing (GET, POST, PUT, DELETE)
   - Path parameters for task ID (`/tasks/{id}`)

4. Add middleware:
   - Request logging (log method, path, status code, duration)
   - Panic recovery (catch panics, return 500 instead of crashing)
   - Content-Type header (`application/json`)

**Part 3: Implement Handlers**

5. Implement handler functions for each endpoint. For now, use an in-memory slice or map to store tasks (database comes in Lab 02):
   - `GET /health` -- Return health status
   - `GET /tasks` -- List all tasks (support pagination query params)
   - `POST /tasks` -- Create a task (validate input, generate ID and timestamps)
   - `GET /tasks/{id}` -- Get a specific task (return 404 if not found)
   - `PUT /tasks/{id}` -- Update a task (return 404 if not found, validate input)
   - `DELETE /tasks/{id}` -- Delete a task (return 404 if not found)

6. Implement proper input validation:
   - POST and PUT must have a JSON body with at least a title
   - Task ID in the URL must be valid
   - Return 400 with a clear error message for invalid input

**Part 4: Graceful Shutdown**

7. Implement graceful shutdown:
   - Listen for SIGTERM and SIGINT signals
   - When received, stop accepting new connections
   - Wait for in-flight requests to complete (with a timeout)
   - Exit cleanly

   Think about: What Go packages do you need for signal handling? How does `http.Server.Shutdown()` work?

**Part 5: Test Manually**

8. Start your server and test every endpoint using `curl`:
   - Create a task
   - List tasks
   - Get the task you created by ID
   - Update the task
   - Delete the task
   - Verify 404 for non-existent tasks
   - Verify 400 for invalid input
   - Test graceful shutdown by sending SIGTERM while making a request

### Expected Outcome

- api-service starts, listens on a configurable port, and responds to HTTP requests
- All endpoints return proper JSON responses with correct status codes
- Graceful shutdown works (verify by sending `kill -15 <PID>` from Module 1 knowledge)
- Request logging middleware shows every request in the terminal

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What's the difference between `http.ListenAndServe()` and creating an `http.Server{}` struct? Why does graceful shutdown require the latter?
> 2. How does middleware work in chi/gin? What's the execution order when you have 3 middleware and a handler?
> 3. Add a new resource endpoint (e.g., `GET /projects`, `POST /projects`) to your API from scratch without referencing the `/tasks` implementation side by side. Time yourself.
> 4. Your handler panics with a nil pointer dereference. Without the recovery middleware, what does the client see? With it?
> 5. Explain what `context.WithTimeout` does and why it's useful for graceful shutdown.

---

## What's Next?

Once both exercises are complete, move on to [Lab 02: Database Integration](lab-02-database.md), where you'll connect your api-service to PostgreSQL and persist tasks to a real database.
