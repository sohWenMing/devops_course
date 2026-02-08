# Lab 05: Container Security & Debugging

> **Module**: 4 -- Docker and Containerization  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Labs 01-04 (FlowForge stack running with Docker Compose). Read the [Container Security Basics](#) and [Debugging Containers](#) sections of the Module 4 README. Install [trivy](https://github.com/aquasecurity/trivy).

---

## Overview

Your FlowForge stack runs in Docker Compose -- but is it secure? And when things break, can you diagnose the issue? In this lab, you'll harden your containers against common security mistakes and practice debugging deliberately broken setups.

---

## Exercise 5a: Container Security

### Objectives

- Configure containers to run as non-root users
- Scan Docker images for known vulnerabilities using trivy
- Fix or mitigate discovered vulnerabilities
- Understand Linux capabilities and why dropping them matters
- Apply security best practices to the FlowForge Dockerfiles

### What You'll Do

**Part 1: Audit Current Security Posture**

1. Check which user your containers currently run as:
   - Exec into each FlowForge container and run `whoami` and `id`
   - Which containers run as root? Why is this a problem?
   - What could an attacker do if they compromised a container running as root?

2. Scan your images with trivy:
   - Install trivy if you haven't already
   - Scan your api-service image: `trivy image <your-api-image>`
   - Scan your worker-service image
   - Scan the PostgreSQL image you're using
   - How many vulnerabilities are reported? What severity levels?
   - Separate the vulnerabilities into: ones in the base OS, ones in your application dependencies, ones in your Dockerfile choices

**Part 2: Run as Non-Root**

3. Modify the api-service Dockerfile to run as a non-root user:
   - In the runtime stage, create a dedicated user and group
   - Set the file ownership of the binary appropriately
   - Switch to the non-root user with the `USER` instruction
   - Think about: does the non-root user need to read any specific files? Write to any directories?

4. Apply the same change to the worker-service Dockerfile:
   - Create a non-root user
   - Ensure the worker can still function (it needs to connect to PostgreSQL -- does the user affect outbound network connections?)

5. Verify non-root execution:
   - Rebuild and restart the stack
   - Exec into each container and verify it runs as the non-root user
   - Verify all functionality still works (API requests, worker processing)
   - What happens if the non-root container tries to bind to port 80? (Ports < 1024 require special privileges)

**Part 3: Fix Vulnerabilities**

6. Address the trivy findings:
   - Start with CRITICAL and HIGH severity vulnerabilities
   - For each vulnerability:
     - Is it in the base image or your application code?
     - If it's in the base image: can you use a newer base image version? A different base image?
     - If it's in application dependencies: can you update the dependency?
     - If you can't fix it: document why and what mitigates the risk
   - Rescan after fixes and compare the results

7. Consider additional hardening:
   - Use specific image tags instead of `latest` -- why?
   - Drop unnecessary Linux capabilities (research which capabilities Docker grants by default)
   - Consider read-only root filesystems (does your Go binary need to write to the filesystem?)
   - Review your `.dockerignore` -- are there any sensitive files that might leak into the image?

**Part 4: Document Your Security Posture**

8. Create a brief security summary:
   - Which containers run as non-root? (Should be all)
   - What vulnerability scan results look like after fixes (trivy output summary)
   - What capabilities are dropped?
   - What security practices you've applied and why
   - What security improvements remain for Module 10 (Security Hardening)?

### Expected Outcome

- All FlowForge containers run as non-root users
- trivy scan shows no CRITICAL vulnerabilities (HIGH should be minimized)
- You can explain why running as root in a container is dangerous
- You can show the Dockerfile changes needed for non-root execution
- You have a documented security posture for the FlowForge Docker stack

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Why is running as root inside a container dangerous, even though the container has namespace isolation?
> 2. Show the Dockerfile changes needed to run a Go service as a non-root user.
> 3. You run `trivy image myapp:latest` and get 15 HIGH vulnerabilities, all in the base OS packages. What are your options?
> 4. What is a Linux capability? Name 3 capabilities and explain what each allows.
> 5. Your non-root container can't start because of "permission denied." What's the likely cause?

---

## Exercise 5b: Debugging Challenge -- Broken Docker Setups

### Objectives

- Diagnose container failures using `docker logs`, `docker exec`, and `docker inspect`
- Identify four different categories of Docker misconfiguration
- Practice a systematic debugging methodology for containers
- Document each issue, its root cause, and the fix

### What You'll Do

You will create (or be given) **four broken Docker setups**. Each one has a different type of misconfiguration. Your job is to diagnose each issue using ONLY Docker debugging tools -- no peeking at the configuration that created the break.

### Setup

Create a directory `project/broken-docker/` with four subdirectories, each containing a broken Docker setup. Each setup should be a simple single-service or multi-service configuration that fails in a specific, diagnosable way.

You can either:
- **Create the broken setups yourself** (recommended -- this reinforces your understanding of what can go wrong)
- **Have a study partner create them** (more realistic)
- **Use the descriptions below** and set them up

### Broken Setup 1: Wrong Port Mapping

**Symptom**: `docker compose up` succeeds, all containers show as running, but you can't reach the api-service from your host machine at `http://localhost:8080`.

**Your task**:
1. Start the broken setup
2. Use `docker compose ps` to check the state of each service
3. Use `docker inspect` to examine the port configuration
4. Use `docker logs` to check if the service started successfully inside the container
5. Find the misconfiguration and fix it
6. Document: what was wrong, how you found it, how you fixed it

**Think about**: There are several ways a port mapping can be "wrong." The container port might not match what the app listens on. The host port might be bound to the wrong interface. The `-p` flag might be missing entirely.

### Broken Setup 2: Missing Environment Variable

**Symptom**: The api-service container starts and then immediately exits with a non-zero exit code. It restarts repeatedly (restart policy is set).

**Your task**:
1. Check container status with `docker compose ps`
2. Read the exit code -- what does it tell you?
3. Check the logs for error messages
4. Compare the required environment variables (from Module 3's `.env.example`) to what's actually set
5. Fix the issue and verify the service starts
6. Document: what was missing, what error message it produced, how you found it

**Think about**: Your Go services should fail fast with clear error messages when required config is missing (Module 3, 12-Factor). The error message in the logs should point you to the problem.

### Broken Setup 3: Permission Denied on Volume

**Symptom**: A service starts but crashes when trying to write to a mounted volume. The logs show "permission denied" errors.

**Your task**:
1. Read the container logs to identify the exact error
2. Exec into the container and check the permissions on the mount point
3. Check what user the container process runs as
4. Check the ownership and permissions of the volume/bind mount
5. Fix the permission mismatch
6. Document: what user the container ran as, what the mount permissions were, how you resolved it

**Think about**: This is the intersection of Module 1 (Linux permissions, UID/GID) and Docker volumes. The user inside the container and the owner of the mounted path must be compatible.

### Broken Setup 4: Network Isolation Issue

**Symptom**: The api-service starts, passes its own health check, but can't connect to PostgreSQL. The worker-service has the same problem. PostgreSQL itself is running fine.

**Your task**:
1. Check that all containers are running
2. Check the network configuration of each container (`docker inspect`)
3. Check if the services can resolve each other's hostnames
4. Check if the services are on the same network
5. Identify the network isolation issue
6. Fix it and verify inter-service communication
7. Document: what the network configuration looked like, why it prevented communication, how you fixed it

**Think about**: Services need to be on the same Docker network to communicate by name. If they're on different networks, or if one is using the default bridge while others are on a custom network, DNS resolution will fail.

### Debugging Methodology

For each broken setup, follow this systematic approach:

1. **Observe symptoms**: What's happening? What's not happening?
2. **Read logs**: `docker logs <container>` -- this solves most issues
3. **Check state**: `docker inspect <container>` -- exit code, network, mounts, env vars
4. **Get inside**: `docker exec -it <container> sh` -- test from within the container
5. **Check network**: `docker network inspect <network>` -- who's connected to what?
6. **Form hypothesis**: Based on evidence, what's the most likely cause?
7. **Test fix**: Apply the fix and verify
8. **Document**: What broke, how you found it, how you fixed it, what Docker concept was involved

### Expected Outcome

- You've diagnosed and fixed all four broken Docker setups
- For each issue, you have:
  - The symptom (what you observed)
  - The diagnostic commands you used
  - The root cause
  - The fix
  - The Docker concept that was violated
- You can diagnose container failures without looking at the configuration source
- You have a systematic debugging methodology you can apply to any Docker issue

### Checkpoint Questions

> Answer these without looking at notes:
> 1. A container exits immediately after starting. What's the first command you run? What are the three most common causes?
> 2. Your container is running but you can't reach it from the host. Walk through your debugging steps.
> 3. `docker inspect` shows `"OOMKilled": true`. What happened and how do you fix it?
> 4. Two containers on different Docker networks can't communicate. Explain why and give two ways to fix it.
> 5. Given a new broken container setup you've never seen before, describe your systematic debugging approach.
