# Lab 02: PostgreSQL Integration & Database Migrations

> **Module**: 3 -- Building FlowForge in Go  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Lab 01 (working api-service with in-memory storage). Read the [PostgreSQL Integration](#) and [Database Migrations](#) sections of the Module 3 README

---

## Overview

In this lab, you'll connect the api-service to a real PostgreSQL database, replacing the in-memory storage from Lab 01. You'll create the database schema, write Go code to interact with PostgreSQL, and set up a proper migration system. By the end, tasks created via the API will persist across server restarts.

---

## Exercise 2a: PostgreSQL Setup, Schema & Go Integration

### Objectives

- Set up a PostgreSQL database for FlowForge
- Design and create the tasks table with appropriate columns, types, and constraints
- Connect to PostgreSQL from Go using `database/sql` with a driver
- Replace in-memory storage with real database queries
- Configure connection pooling

### What You'll Do

**Part 1: Database Setup**

1. Create a PostgreSQL database for FlowForge:
   - Choose a database name, a dedicated user (not `postgres` superuser), and a password
   - Think about: Why shouldn't your application connect as the PostgreSQL superuser?
   - Grant the dedicated user only the permissions it needs

2. Design the `tasks` table schema. Think about:
   - What columns match your task data model from Lab 01?
   - What data types are appropriate for each column? (e.g., `TEXT` vs `VARCHAR`, `TIMESTAMP` vs `TIMESTAMPTZ`)
   - What constraints should exist? (NOT NULL, DEFAULT values, CHECK constraints)
   - Should `status` be an ENUM or a TEXT with a CHECK constraint?
   - What should `created_at` and `updated_at` default to?
   - Does the table need any indexes? (Think about what queries the worker will run)

3. Write the SQL to create the table and apply it to your database.

**Part 2: Go Database Integration**

4. Add the PostgreSQL driver to your Go module:
   - Choose between `lib/pq` and `pgx`. Read about both and make a decision
   - Think about: What's the difference? Why might you choose one over the other?

5. Write the database connection code:
   - Read the connection string from an environment variable (`DATABASE_URL`)
   - Open a connection pool using `sql.Open()`
   - Configure pool settings: `SetMaxOpenConns`, `SetMaxIdleConns`, `SetConnMaxLifetime`
   - Verify the connection works using `db.Ping()` at startup
   - Handle the case where PostgreSQL is unreachable at startup

6. Create a data access layer (repository pattern or similar):
   - Functions for each database operation: create task, get task by ID, list tasks (with pagination), update task, delete task
   - Use parameterized queries (never string concatenation -- SQL injection!)
   - Handle `sql.ErrNoRows` properly (this means "not found", not "error")
   - Think about: Where should error handling live? In the handler or in the data access layer?

7. Replace the in-memory storage in your handlers with calls to the data access layer.

**Part 3: Connection Pooling**

8. Experiment with connection pool settings:
   - Start the api-service and use `ss` (from Module 2) to see the TCP connections to PostgreSQL
   - Make several API requests and observe new connections being created
   - Check how many idle connections exist after a burst of requests
   - Think about: What happens if you set `MaxOpenConns` to 1 and send 10 concurrent requests?

### Expected Outcome

- PostgreSQL has a `flowforge` database with a `tasks` table
- api-service connects to PostgreSQL on startup and fails fast if the database is unreachable
- All CRUD operations work against the real database
- Tasks persist across server restarts
- You can observe connection pool behavior using `ss`

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Why do you use parameterized queries (`$1`, `$2`) instead of string formatting (`fmt.Sprintf`)?
> 2. What's the difference between `db.Query()`, `db.QueryRow()`, and `db.Exec()`? When do you use each?
> 3. Write a SQL query to create a new table (e.g., `projects` with `id`, `name`, `owner`, `created_at`) from scratch.
> 4. Explain what connection pooling is and why it matters. What would happen without it?
> 5. What does `sql.ErrNoRows` mean and how should you handle it differently from other errors?

---

## Exercise 2b: Database Migrations with golang-migrate

### Objectives

- Set up a migration system using golang-migrate
- Create migration files that can evolve the database schema
- Practice applying and rolling back migrations
- Understand why down migrations are important

### What You'll Do

**Part 1: Set Up Migrations**

1. Install the `golang-migrate` CLI tool (or use the Go library).

2. Create a `migrations/` directory in the api-service project.

3. Create your first migration pair:
   - The "up" migration should create the `tasks` table (the same schema from Exercise 2a)
   - The "down" migration should drop the `tasks` table
   - Think about: Should the down migration use `DROP TABLE` or `DROP TABLE IF EXISTS`? Why?

4. Drop your manually created table and apply the migration instead. Verify the table was created correctly.

**Part 2: Evolve the Schema**

5. Create a second migration that adds new functionality:
   - Add an `assigned_worker` column (nullable TEXT -- the worker that claimed the task)
   - Add a `priority` column (INTEGER with a default value)
   - Think about: Why add these columns as nullable first instead of NOT NULL?

6. Apply the second migration and verify the new columns exist.

7. Rollback the second migration (down by 1) and verify the columns are gone.

8. Re-apply the second migration.

**Part 3: Migration Safety**

9. Create a third migration that does something potentially dangerous:
   - Add a `NOT NULL` constraint to a column that currently allows nulls
   - Think about: What happens if there are existing rows with NULL values? How do you handle this safely?
   - The "up" should: first backfill any NULL values with a default, then add the constraint
   - The "down" should: remove the constraint

10. Practice the full migration workflow:
    - Check the current migration version
    - Apply all pending migrations
    - Rollback one step
    - Apply again
    - Verify the database state at each step

### Expected Outcome

- A `migrations/` directory with at least 3 migration pairs (up + down)
- All migrations can be applied in order from a fresh database
- All migrations can be rolled back in order to return to a clean state
- The api-service uses the migrated schema
- You understand the workflow: create migration → test up → test down → commit

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Create a migration from scratch that adds a `description` column to an existing table. Write both the up and down SQL.
> 2. Why do down migrations matter? When would you use them?
> 3. What happens if an "up" migration fails halfway through (e.g., it runs 2 of 3 SQL statements)? How does golang-migrate handle this?
> 4. You need to rename a column from `task_name` to `title`. Write the migration. What's the risk?
> 5. A migration adds a NOT NULL column to a table with 1 million rows. What could go wrong and how would you make it safe?

---

## What's Next?

Once both exercises are complete, move on to [Lab 03: Worker Service](lab-03-worker.md), where you'll build the worker-service that polls for tasks from the database and processes them.
