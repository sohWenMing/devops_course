# Lab 03: Bash Scripting

> **Module**: 1 -- Linux Deep Dive  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Labs 01 and 02. Read the [Bash Scripting](#) and [Environment Variables & Configuration](#) sections of the Module 1 README

---

## Overview

In this lab, you'll write real automation scripts for FlowForge. These aren't toy examples -- health check scripts and environment management scripts are things every DevOps engineer writes and maintains. You'll practice argument parsing, exit codes, error handling, and the patterns you'll use throughout the rest of the course.

---

## Exercise 3a: Health Check Script

### Objectives

- Write a bash script that performs multiple health checks on FlowForge services
- Use meaningful exit codes to communicate results
- Handle errors gracefully (don't just crash on the first failure)
- Practice argument parsing and help messages

### What You'll Do

**Part 1: Design the Script**

1. Before writing code, design your health check script on paper (or in a notes file). It should check:
   - Is PostgreSQL running? (hint: you installed it in Lab 02)
   - Is the api-service port listening? (even if nothing is bound yet, practice checking a port)
   - Is disk usage below a threshold? (default 80%, but configurable)

   For each check, decide:
   - What command will you use to check it?
   - What constitutes "passing" vs "failing"?
   - What should the output look like? (Think: what would be useful at 3 AM when you're debugging)

**Part 2: Build the Script**

2. Create the health check script with these requirements:

   **Command-line interface:**
   - Accepts a `-v` flag for verbose output
   - Accepts a `-t <threshold>` option to set the disk usage threshold (default: 80)
   - Shows a usage/help message with `-h`
   - Handles invalid arguments gracefully

   **Safety:**
   - Uses `set -euo pipefail` (but think about when you need to temporarily disable `set -e` to handle expected failures)
   - All variables are quoted properly
   - No unset variable errors

   **Output format:**
   - Each check prints a clear status line: `[OK]` or `[FAIL]` with a description
   - In verbose mode, print additional details (e.g., actual disk usage percentage, PID of service)
   - Summary line at the end: "X of Y checks passed"

   **Exit codes:**
   - Exit 0 if all checks pass
   - Exit 1 if any check fails (but run ALL checks first -- don't stop at the first failure)
   - Exit 2 if the script was called with bad arguments

3. Test your script thoroughly:
   - Run it when PostgreSQL is running -- all checks should pass
   - Stop PostgreSQL and run it again -- the PostgreSQL check should fail, but other checks should still run
   - Test with the `-v` flag
   - Test with a very low disk threshold (e.g., `-t 1`) to trigger a disk failure
   - Test with invalid arguments

**Part 3: Make It Robust**

4. Add resilience to your script:
   - What happens if `ss` or `netstat` isn't installed? Handle that case.
   - What happens if the script is run as a non-root user who can't check certain things?
   - Add a timeout for checks that might hang (e.g., a service that's not responding)

### Expected Outcome

- A working health check script at a location in the FlowForge directory structure
- The script checks PostgreSQL, port listening, and disk usage
- Clear, actionable output that would be useful during incident response
- Meaningful exit codes that automation tools can use
- Proper argument parsing with help text

### Checkpoint Questions

> Without looking at your script or notes:
> 1. Write a new script from scratch that takes a service name as an argument and reports:
>    - Whether the service is running
>    - Its PID
>    - Its memory usage
>    - How long it has been running (uptime)
>    - Must have proper argument parsing, error handling, and exit codes
>    - Must NOT copy from your lab 3a script
> 2. What does `set -euo pipefail` do? Explain each flag.
> 3. Why would you use `exit 1` vs `exit 2` vs `exit 0`? Give a scenario for each.

---

## Exercise 3b: Environment Variable Loading Script

### Objectives

- Create a `.env` file with all the configuration FlowForge needs
- Write a script that loads and validates environment variables
- Practice defensive scripting: check that everything is set before the app starts
- Understand the difference between sourcing and executing

### What You'll Do

**Part 1: Create the .env File**

1. Create a `.env` file for FlowForge with at minimum these categories of config:

   **Database configuration:**
   - Host, port, database name, username, password

   **API service configuration:**
   - Listen port, log level

   **Worker service configuration:**
   - Poll interval, max concurrent jobs

   **General:**
   - Environment name (dev/staging/production)

   Think about:
   - What's a sensible default for development?
   - Which values are secrets that should never be in git?
   - What format should each value be in? (Are all values strings? Should some be numbers?)

**Part 2: Write the Validation Script**

2. Create a script that loads the `.env` file and validates that everything is correct. The script should:

   **Load variables:**
   - Take the path to the `.env` file as an argument (don't hardcode it)
   - Handle the case where the file doesn't exist
   - Export the variables so child processes can see them

   **Validate required variables:**
   - Check that ALL required variables are set (not empty)
   - For each missing variable, print a clear error message
   - Don't stop at the first missing variable -- report ALL missing ones

   **Validate values:**
   - Check that port numbers are actually numbers (and within valid range 1-65535)
   - Check that log level is one of: debug, info, warn, error
   - Check that environment is one of: dev, staging, production
   - Check that the poll interval is a positive number

   **Output:**
   - If validation passes: print a summary of loaded config (mask secrets!)
   - If validation fails: print all errors and exit with a non-zero code

3. Test your script:
   - Run it with a valid `.env` file -- should succeed
   - Remove a required variable -- should fail with a clear message
   - Set a port to "abc" -- should fail validation
   - Set an invalid log level -- should fail validation
   - Remove the `.env` file entirely -- should fail with a file-not-found message

**Part 3: Integration**

4. Integrate your validation script with the health check script from Exercise 3a:
   - Source the validation script at the top of the health check
   - Use the loaded variables to know which port to check
   - Think about: should the health check script fail if env validation fails?

### Expected Outcome

- A `.env` file with all FlowForge configuration
- A validation script that loads, validates, and exports environment variables
- The script catches and reports all configuration errors before the app starts
- Secrets are masked in output (e.g., `DB_PASSWORD=****`)

### Checkpoint Questions

> Without looking at notes or your `.env` file:
> 1. List from memory every environment variable FlowForge needs and explain why each one exists
> 2. What's the difference between `source script.sh` and `./script.sh` in terms of environment variables?
> 3. Your script loads `DB_PASSWORD` from a `.env` file. How would you prevent it from showing up in `ps` output or shell history?
> 4. A developer commits a `.env` file to git with production database credentials. What's the correct response? (Hint: it's more than just deleting the file)

---

## What's Next?

With your scripts in place, move on to [Lab 04: SSH](lab-04-ssh.md), where you'll set up secure remote access -- a foundational skill for managing any server.
