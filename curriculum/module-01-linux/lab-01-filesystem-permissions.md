# Lab 01: Filesystem & Permissions

> **Module**: 1 -- Linux Deep Dive  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Read the [File System Hierarchy](#) and [File Permissions & Ownership](#) sections of the Module 1 README

---

## Overview

In this lab, you'll explore the Linux filesystem hierarchy hands-on and set up the FlowForge project directory structure with proper users, groups, and permissions. By the end, you'll understand where things live on a Linux system and how to control who can access what.

---

## Exercise 1a: Filesystem Navigation & FlowForge Directory Structure

### Objectives

- Navigate the Linux filesystem and understand what lives in each key directory
- Examine real system files to build intuition about the FHS
- Create a production-like directory structure for the FlowForge application

### What You'll Do

**Part 1: Explore the FHS**

1. Visit each of these directories and examine their contents:
   - `/etc` -- Find at least 3 configuration files and explain what they configure
   - `/var/log` -- Find at least 3 log files and identify which service produces each
   - `/proc` -- Find information about your system's CPU, memory, and a running process
   - `/home` -- Examine what's in your home directory and understand hidden files (dotfiles)
   - `/tmp` -- Understand who can write here and what happens on reboot
   - `/usr/bin` -- Find 5 commands you use regularly and verify they live here

2. Answer these questions (write your answers in a file called `fhs-notes.md`):
   - What is the difference between `/bin` and `/usr/bin` on your system?
   - What kind of information can you find in `/proc/cpuinfo`?
   - Why does `/tmp` have the sticky bit set? What would happen without it?
   - What does the `$PATH` variable have to do with where binaries live?

**Part 2: Create the FlowForge Directory Structure**

3. Create a production-like directory layout for FlowForge. Your structure should have:
   - A directory for the application binaries
   - A directory for configuration files
   - A directory for log files
   - A directory for data/runtime files

   Think about which standard FHS locations are appropriate for each. Don't just make everything under `/home` -- think about where a real production application would put these things.

4. Verify your structure makes sense:
   - Can you explain why you chose each location?
   - Does it follow FHS conventions?
   - Would another sysadmin know where to find FlowForge files without you telling them?

### Expected Outcome

- A file `fhs-notes.md` with your answers about the filesystem
- A FlowForge directory structure created on your system that follows FHS conventions
- You can navigate to any standard directory and explain what belongs there

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Where would you look for PostgreSQL's configuration file?
> 2. Where are systemd service files stored?
> 3. A process with PID 1234 is running -- where can you find information about it in the filesystem?
> 4. What's the difference between `/tmp` and `/var/tmp`?

---

## Exercise 1b: Users, Groups, and Permissions for FlowForge Services

### Objectives

- Create dedicated users and groups for FlowForge services
- Set file ownership and permissions following the principle of least privilege
- Understand how permissions affect service isolation

### What You'll Do

**Part 1: Create Service Users and Groups**

1. Create the following users and groups for FlowForge:
   - A user for the API service
   - A user for the worker service
   - A group that both services belong to (for shared resources)
   - A dedicated group for accessing the database config

   Think about:
   - Should these users have login shells? Why or why not?
   - Should they have home directories? Why or why not?
   - What's the principle behind giving each service its own user?

**Part 2: Set Directory Permissions**

2. Set permissions on the FlowForge directories you created in Exercise 1a so that:
   - Each service can read its own config files but NOT the other service's config
   - Both services can write to a shared log directory
   - Only the API service user can read the database credentials file
   - The worker service cannot access the API service's working directory
   - A separate "deploy" user can update the application binaries but cannot read secrets

3. Create a test config file with a fake database password. Verify your permissions work:
   - Switch to the API service user and confirm you can read the database config
   - Switch to the worker service user and confirm you CANNOT read the database config
   - Attempt to write to a directory you shouldn't have write access to

**Part 3: Understand umask**

4. Experiment with `umask`:
   - Check the current umask value
   - Create a file and observe its default permissions
   - Change the umask and create another file -- observe how permissions differ
   - Explain what umask value you'd set for a service user and why

### Expected Outcome

- FlowForge service users and groups exist on the system
- Directory permissions enforce isolation between services
- You can demonstrate that the worker user cannot read the API's secrets
- You understand how umask affects default file permissions

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Given this `ls -la` output, explain every column:
>    ```
>    -rw-r----- 1 flowforge-api db-config 256 Jan 15 10:30 database.env
>    ```
> 2. What command would you use to make a file readable ONLY by its owner?
> 3. Why should service users have `/usr/sbin/nologin` as their shell?
> 4. If a file has permissions `750` and you're in the file's group, what can you do with it?
> 5. How would you set up a directory where multiple users can create files, but each user can only delete their own files?

---

## What's Next?

Once you've completed both exercises, move on to [Lab 02: Processes & systemd](lab-02-processes-systemd.md), where you'll learn to manage running processes and create systemd service files for FlowForge.
