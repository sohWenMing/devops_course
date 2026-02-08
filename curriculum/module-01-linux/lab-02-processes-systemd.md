# Lab 02: Processes, systemd & Package Management

> **Module**: 1 -- Linux Deep Dive  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Lab 01. Read the [Processes & Signals](#), [systemd Services](#), and [Package Management](#) sections of the Module 1 README

---

## Overview

In this lab, you'll learn to manage processes, write systemd unit files for FlowForge services, and use the package manager to install and manage software. These are everyday skills for any DevOps engineer.

---

## Exercise 2a: Processes & Signals

### Objectives

- Run processes in the foreground and background
- Find and inspect running processes using multiple tools
- Send signals to processes and observe different behaviors
- Understand the difference between graceful and forceful termination

### What You'll Do

**Part 1: Background Processes**

1. Create 3 simple "placeholder" processes that simulate FlowForge services. These can be simple bash loops or `sleep` commands with meaningful names. Run them in the background.

2. Using only process inspection tools (NOT the terminal that started them), find:
   - The PID of each process
   - Which user each process is running as
   - How much CPU and memory each is using
   - The parent process of each

3. Try at least 2 different tools/commands to find this information. Compare their output.

**Part 2: Signals**

4. Send `SIGTERM` (signal 15) to one of your placeholder processes:
   - What happens?
   - How quickly does it stop?
   - What exit code do you get?

5. Send `SIGKILL` (signal 9) to another placeholder process:
   - What happens differently compared to SIGTERM?
   - Can you explain WHY it behaves differently?
   - What exit code do you get?

6. Send `SIGSTOP` to the remaining process, then `SIGCONT`:
   - What state does the process go into when stopped?
   - What happens to its CPU usage?
   - Does it resume exactly where it left off?

**Part 3: Process States**

7. Find a process in each of these states on your system and explain what the state means:
   - Running/Runnable (`R`)
   - Sleeping (`S`)
   - Zombie (`Z`) -- you may need to create one deliberately

### Expected Outcome

- You can start background processes and find them using multiple tools
- You understand the behavioral difference between SIGTERM and SIGKILL
- You can explain process states and what they mean
- You can identify orphaned and zombie processes

### Checkpoint Questions

> Without looking at notes:
> 1. What's the difference between `SIGTERM` and `SIGKILL`? Which should you try first and why?
> 2. How would you find the PID of a process called "api-service" using 3 different methods?
> 3. What is a zombie process and why does it exist?
> 4. What signal does Ctrl+C send? What about Ctrl+Z?

---

## Exercise 2b: systemd Unit Files

### Objectives

- Write a systemd unit file from scratch for a FlowForge service
- Manage the service lifecycle (start, stop, restart, enable)
- View and filter service logs with journalctl
- Understand service dependencies and restart behavior

### What You'll Do

**Part 1: Create a Service**

1. Write a simple script that acts as the FlowForge `api-service`:
   - It should print a startup message
   - Run in a loop (printing periodic "heartbeat" messages)
   - Handle SIGTERM gracefully (print a shutdown message and exit cleanly)

2. Write a systemd unit file for this script. Your unit file should:
   - Run the service as the correct FlowForge user (from Lab 01)
   - Start after the network is available
   - Restart automatically if the service crashes
   - Load environment variables from the config file you created in Lab 01
   - Have a proper description

3. Install and manage your service:
   - Load the unit file so systemd sees it
   - Start the service and verify it's running
   - Enable it so it starts on boot
   - View the service logs
   - Stop and restart the service

**Part 2: Observe Behaviors**

4. Test crash recovery:
   - While the service is running, kill it with `kill -9` (simulating a crash)
   - Observe how systemd responds
   - Check the logs to see what happened
   - How quickly does systemd restart the service?

5. Test dependency ordering:
   - Modify your unit file to depend on a service that doesn't exist
   - What happens when you try to start it?
   - What's the difference between `Wants=` and `Requires=` in this scenario?

**Part 3: Logs**

6. Use journalctl to:
   - View only your service's logs
   - View logs from the last 10 minutes
   - Follow the log output in real-time
   - Filter to show only error-level messages
   - Output logs in JSON format

### Expected Outcome

- A working systemd unit file for a FlowForge placeholder service
- The service starts on boot, restarts on crash, and logs to journald
- You can manage the service lifecycle and read its logs

### Checkpoint Questions

> Without looking at notes or your existing unit file:
> 1. Write a complete systemd unit file for `worker-service` from scratch (different from the one you just created for api-service)
> 2. What command do you run after editing a unit file so systemd picks up the changes?
> 3. What's the difference between `systemctl enable` and `systemctl start`?
> 4. How would you see only the last 50 lines of logs for a service?
> 5. What happens if your service's `ExecStart` binary doesn't exist?

---

## Exercise 2c: Package Management

### Objectives

- Install software using apt
- Understand package dependencies and what gets installed
- Find where a package puts its files (binaries, config, logs)
- Cleanly remove packages and understand the difference between remove and purge

### What You'll Do

**Part 1: Install PostgreSQL**

1. Install PostgreSQL using apt:
   - Update the package list first
   - Install PostgreSQL
   - Observe the output -- what dependencies are being installed?

2. After installation, investigate:
   - Is PostgreSQL running? How can you tell?
   - Where is the PostgreSQL binary installed?
   - Where is the PostgreSQL configuration file?
   - Where does PostgreSQL store its data?
   - Where are the PostgreSQL logs?
   - Which systemd unit file manages PostgreSQL?

3. Verify PostgreSQL is functional:
   - Check that it's listening on the expected port
   - Connect to it using the PostgreSQL client tool

**Part 2: Package Exploration**

4. Investigate the PostgreSQL package:
   - List all files that the PostgreSQL package installed
   - Find which packages depend on PostgreSQL
   - Find which packages PostgreSQL depends on
   - Check the installed version

5. Practice package operations:
   - Install a small utility package of your choice
   - Find its config files
   - Remove it using `apt remove` -- are the config files still there?
   - Install it again, then remove it using `apt purge` -- what's different?
   - Clean up any leftover dependencies

**Part 3: Repository Management**

6. Examine your system's package repositories:
   - Look at the sources list to see where packages come from
   - Understand the format of a repository entry
   - What's the difference between `main`, `universe`, and `restricted`?

### Expected Outcome

- PostgreSQL is installed and running on your system
- You can find the config files, data directory, and logs for any installed package
- You understand the difference between `remove` and `purge`
- You know how to explore package dependencies

### Checkpoint Questions

> Without looking at notes:
> 1. What's the first command you should run before installing any package? Why?
> 2. You installed `nginx` but now you want to completely remove it with no traces left. What command(s) do you use?
> 3. How do you find out which package owns the file `/usr/bin/curl`?
> 4. What's the difference between `apt remove` and `apt purge`?
> 5. PostgreSQL is installed but won't start. What are the first 3 things you'd check?

---

## What's Next?

With processes, services, and packages under your belt, move on to [Lab 03: Bash Scripting](lab-03-bash-scripting.md), where you'll write automation scripts for FlowForge.
