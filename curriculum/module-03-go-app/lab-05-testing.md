# Lab 05: Go Testing -- Unit & Integration Tests

> **Module**: 3 -- Building FlowForge in Go  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Labs 01-04 (fully working FlowForge with both services, structured logging, and config externalization). Read the [Go Testing](#) section of the Module 3 README

---

## Overview

In this lab, you'll write tests for the api-service to verify that handlers, database operations, and the full request flow work correctly. You'll write unit tests (with mocked dependencies) and integration tests (with a real PostgreSQL instance), and aim for >70% code coverage.

---

## Exercise 5: Unit Tests & Integration Tests

### Objectives

- Write unit tests for API handler functions using Go's `testing` package and `httptest`
- Write integration tests that verify the full flow with a real PostgreSQL database
- Achieve >70% code coverage on the api-service
- Understand the difference between unit and integration tests and when to use each

### What You'll Do

**Part 1: Test Setup**

1. Create test files alongside the code they test (Go convention: `foo_test.go` next to `foo.go`).

2. Think about your test strategy:
   - Which functions are best tested as unit tests (isolated, mocked dependencies)?
   - Which functions require integration tests (real database)?
   - What test cases should you write for each handler? Think about:
     - Happy path (valid input → correct response)
     - Invalid input (bad JSON, missing fields → 400 error)
     - Not found (valid request for non-existent resource → 404)
     - Server error (database unreachable → 500)

3. For integration tests, set up a test database:
   - Create a separate PostgreSQL database for testing (e.g., `flowforge_test`)
   - Run migrations before tests start
   - Clean up data between tests so they don't affect each other
   - Think about: Should tests share a database? What are the risks of test isolation?

**Part 2: Unit Tests for Handlers**

4. Write unit tests for the API handlers using `httptest`:
   - `TestCreateTask_ValidInput`: POST with a valid JSON body returns 201 and the created task
   - `TestCreateTask_InvalidJSON`: POST with invalid JSON returns 400
   - `TestCreateTask_MissingTitle`: POST with empty title returns 400
   - `TestGetTask_Found`: GET for an existing task returns 200 and the task
   - `TestGetTask_NotFound`: GET for a non-existent task returns 404
   - `TestListTasks_Empty`: GET /tasks with no tasks returns 200 and an empty list
   - `TestListTasks_WithPagination`: GET /tasks with pagination params returns the correct page
   - `TestUpdateTask_ValidInput`: PUT with valid input returns 200
   - `TestUpdateTask_NotFound`: PUT for a non-existent task returns 404
   - `TestDeleteTask_Found`: DELETE for an existing task returns 200 (or 204)
   - `TestDeleteTask_NotFound`: DELETE for a non-existent task returns 404
   - `TestHealthCheck`: GET /health returns 200

   For unit tests, you need to mock or abstract the database layer. Think about:
   - How do you test a handler without a real database?
   - What interface should the data access layer implement so you can swap in a mock?

5. For each test:
   - Create the request using `httptest.NewRequest`
   - Create a response recorder using `httptest.NewRecorder`
   - Call the handler directly
   - Assert the status code
   - Assert the response body (parse JSON and check fields)

**Part 3: Integration Tests**

6. Write integration tests that test the full flow with a real database:
   - `TestCreateAndGetTask`: Create a task via POST, retrieve it via GET, verify they match
   - `TestCreateAndListTasks`: Create multiple tasks, list them, verify count and contents
   - `TestCreateUpdateGetTask`: Create, update, retrieve -- verify the update was persisted
   - `TestCreateDeleteGetTask`: Create, delete, try to retrieve -- verify 404
   - `TestDatabaseConnectionFailure`: Test behavior when the database is unreachable (optional, stretch goal)

7. Think about test isolation:
   - How do you clean up between tests? (Truncate tables? Use transactions that rollback?)
   - How do you ensure tests can run in any order?
   - How do you prevent integration tests from requiring a running database in CI? (Hint: build tags or environment variables to skip them)

**Part 4: Code Coverage**

8. Run the test suite with coverage:
   ```
   go test -coverprofile=coverage.out ./...
   ```

9. Generate a coverage report and examine it:
   ```
   go tool cover -html=coverage.out
   ```

10. Identify untested code paths:
    - Which functions have no tests?
    - Which branches (if/else) are not covered?
    - Focus on testing the most critical untested paths first

11. Write additional tests until you reach >70% coverage on the api-service.

**Part 5: Test Quality Check**

12. Review your tests against these quality criteria:
    - Does each test test one thing? (Not a giant test that checks everything)
    - Are test names descriptive? (Can you tell what failed from the test name alone?)
    - Do tests have clear arrange/act/assert sections?
    - Are there edge cases you're missing? (empty strings, zero values, very long inputs)
    - Could someone new to the codebase understand what each test verifies?

### Expected Outcome

- Unit test files exist alongside the handler code
- Integration test files test the full HTTP → DB → response flow
- All tests pass: `go test ./...` shows green
- Coverage is >70% on the api-service (verify with `go test -cover ./...`)
- You can explain which code is tested and which isn't, and why

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What's the difference between `httptest.NewRequest` and `http.NewRequest`? When do you use each?
> 2. Your test creates a task and then immediately reads it. Is this a unit test or an integration test? Why?
> 3. Write a test from scratch for a new handler (e.g., `TestGetProject_NotFound`) without referencing existing tests. Time yourself.
> 4. Your coverage report shows that error handling code is untested. How would you test the "database connection failed" code path?
> 5. A test passes locally but fails in CI. What are the most common causes? How would you debug this?

---

## What's Next?

Congratulations! Once this lab is complete, you've built the entire FlowForge application. Head to the [Exit Gate Checklist](checklist.md) to verify you're ready for Module 4.

> **What's coming in Module 4**: You'll take these two Go services and containerize them with Docker. Everything you built here -- the services, the database integration, the config externalization, the graceful shutdown -- will be tested by the containerization process. The 12-Factor principles you followed will make containerization straightforward.
