# Lab 04: Docker Compose

> **Module**: 4 -- Docker and Containerization  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Lab 03 (networking and volumes working). Read the [Docker Compose](#) and [Docker Compose for Development](#) sections of the Module 4 README.

---

## Overview

In Lab 03, you manually started and connected containers with individual `docker run` commands. In this lab, you'll define the entire FlowForge stack in a single `docker-compose.yml` file and add a development workflow with hot-reload so you can edit code and see changes immediately.

---

## Exercise 4a: Docker Compose for FlowForge

### Objectives

- Write a `docker-compose.yml` that defines the complete FlowForge stack
- Configure health checks so services start in the correct order
- Use `depends_on` with conditions to prevent premature startup
- Manage configuration through environment variables
- Bring the entire stack up and down with a single command

### What You'll Do

**Part 1: Define the Compose File**

1. Create a `docker-compose.yml` at the project root (`project/docker-compose.yml`) that defines three services:
   - **postgres**: The database
     - Use the official PostgreSQL Alpine image
     - Set up database name, user, and password through environment variables
     - Mount a named volume for data persistence
     - Add a health check that verifies PostgreSQL is ready to accept connections (not just that the container is running)
     - Think about: what command checks if PostgreSQL is accepting connections?

   - **api-service**: The REST API
     - Build from the api-service Dockerfile (your multi-stage build from Lab 02)
     - Map the API port to the host
     - Set environment variables for database connection (host, port, user, password, database name)
     - Configure `depends_on` so it waits for PostgreSQL to be healthy
     - Think about: what should DB_HOST be? (Remember DNS from Lab 03)

   - **worker-service**: The background processor
     - Build from the worker-service Dockerfile
     - Set the same database connection environment variables
     - Configure `depends_on` to wait for PostgreSQL to be healthy
     - Think about: does the worker need port mapping? Why or why not?

2. Define shared resources:
   - A named volume for PostgreSQL data
   - A custom bridge network for all services
   - Think about: should all services be on the same network? Are there reasons to separate them?

**Part 2: Configure Health Checks**

3. Add a health check for the api-service:
   - What endpoint should the health check hit?
   - What does a passing health check look like?
   - Configure appropriate interval, timeout, and retry settings
   - Why is a health check on the api-service important? (Think about load balancers, Kubernetes readiness probes in Module 8)

4. Consider a health check for the worker-service:
   - The worker doesn't expose an HTTP endpoint. How would you check if it's healthy?
   - Options: a file-based health check? A custom health endpoint? A process check?
   - Implement whichever approach you choose and explain your reasoning

**Part 3: Bring Up the Stack**

5. Start the entire FlowForge stack:
   - Run `docker compose up` and watch the startup sequence
   - Observe: in what order do services start?
   - Verify PostgreSQL is healthy before api-service tries to connect
   - Check that all services are running with `docker compose ps`

6. Test the complete flow:
   - Create a task through the api-service HTTP endpoint
   - Check that the worker-service picks it up and processes it (check its logs)
   - Verify the task status changes in the database
   - This is the first time the entire FlowForge stack runs together in containers!

7. Explore Compose commands:
   - View logs from all services together (`docker compose logs`)
   - View logs from just one service
   - Stop a single service and observe what happens to the others
   - Scale the worker-service to 2 instances. Does it work? What challenges arise?

**Part 4: Teardown and Persistence**

8. Test the data persistence:
   - Create some tasks through the API
   - Run `docker compose down` (WITHOUT `-v`)
   - Run `docker compose up` again
   - Are the tasks still there? Why?

9. Test complete cleanup:
   - Run `docker compose down -v`
   - Run `docker compose up` again
   - Are the tasks still there? Why not?
   - When would you want each behavior?

### Expected Outcome

- A complete `docker-compose.yml` that defines the entire FlowForge stack
- `docker compose up` brings up all services with correct startup ordering
- Health checks ensure PostgreSQL is ready before application services start
- The complete task flow works: create via API → worker processes → status updates
- You understand the difference between `down` and `down -v`
- You can manage individual services within the Compose stack

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Start the entire FlowForge stack with one command and verify all services communicate.
> 2. Add a new service (e.g., `redis`) to the compose file from scratch. It should be on the same network, have a health check, and be accessible by name from other services.
> 3. What's the difference between `depends_on` without a condition and `depends_on` with `condition: service_healthy`? Why does the difference matter?
> 4. Your api-service starts before PostgreSQL is ready and crashes. What's the likely cause and how do you fix it in docker-compose.yml?
> 5. Explain what `docker compose down -v` does that `docker compose down` doesn't. When is each appropriate?

---

## Exercise 4b: Development Workflow with Hot-Reload

### Objectives

- Create a development-specific compose setup with source code mounting and hot-reload
- Use `air` (or a similar tool) for automatic Go binary rebuilding on file changes
- Understand the differences between dev and prod compose configurations
- Edit Go code on your host and see changes reflected in running containers immediately

### What You'll Do

**Part 1: Development Compose Configuration**

1. Create a development-oriented compose configuration:
   - You have several options: a separate `docker-compose.dev.yml`, a `docker-compose.override.yml`, or using Compose profiles
   - Choose an approach and explain why
   - The dev config should override/extend the production compose file

2. For the api-service development setup:
   - Override the build to use a development Dockerfile (or modify the existing one with a build target)
   - Mount the api-service source code directory from the host into the container as a bind mount
   - Install a hot-reload tool (e.g., `air` for Go) in the development image
   - Override the CMD to use the hot-reload tool instead of the compiled binary
   - Think about: the dev image needs the Go toolchain (to recompile). The prod image shouldn't have it. How do you handle this?

3. Apply the same approach for worker-service:
   - Mount the worker-service source code
   - Set up hot-reload for the worker too
   - Consider: does the worker need any special handling for hot-reload?

**Part 2: Configure Air (or Similar)**

4. Set up the hot-reload tool:
   - Install `air` or a similar Go live-reload tool
   - Create a configuration file (e.g., `.air.toml`) that watches `.go` files
   - Configure it to rebuild and restart the binary when files change
   - Consider: what files should trigger a rebuild? What about `go.mod` changes?

5. Create a development Dockerfile (or build target):
   - Based on a Go image (needs the compiler)
   - Installs the hot-reload tool
   - Does NOT compile the binary at build time (air will do it)
   - Sets air as the entrypoint/command

**Part 3: Test the Development Workflow**

6. Start the development stack:
   - Use your dev compose configuration to bring up the stack
   - Verify all services start correctly
   - Make a request to the api-service to confirm it works

7. Test hot-reload:
   - Make a visible change to the api-service code (e.g., add a new endpoint, change a response message, modify the health check response)
   - Save the file on your host
   - Watch the container logs -- air should detect the change, recompile, and restart
   - Make a request to verify the change is live
   - How long does the reload cycle take? (From save to new response)

8. Test with the worker-service:
   - Make a change to the worker-service code
   - Verify the change takes effect without manually rebuilding the container

**Part 4: Dev vs Prod Comparison**

9. Document the differences between your dev and prod setups:
   - Create a comparison covering:
     - How source code gets into the container (bind mount vs baked in)
     - Base image used (golang vs alpine/scratch)
     - How the binary is started (air vs compiled binary)
     - Image size (dev vs prod)
     - What tools are available inside the container
     - When would you use each?

10. Verify the production compose still works:
    - Run the production compose (without dev overrides)
    - Confirm it uses pre-built images, not bind mounts
    - Confirm the images are the small multi-stage versions from Lab 02
    - Can you change code and see it reflected? (No -- that's the point. Production images are immutable.)

### Expected Outcome

- A development compose setup that mounts source code and uses hot-reload
- Changes to Go files on the host are automatically detected, compiled, and served by the running containers
- You have separate dev and prod compose configurations with clear differences
- The production compose still builds and runs the optimized multi-stage images
- You can articulate why immutable production images and hot-reload dev environments are both important

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Modify a Go source file while containers are running and see the change reflected immediately without rebuilding. Demonstrate this.
> 2. Explain the difference between the dev and prod Dockerfiles/compose files. Why do you need both?
> 3. Why is mounting source code as a bind mount acceptable in development but not in production?
> 4. Your hot-reload isn't detecting file changes. List 3 things you'd check.
> 5. How does this dev-mode compose setup relate to Kubernetes development tools like Skaffold or Tilt? (Think ahead to Module 8)
