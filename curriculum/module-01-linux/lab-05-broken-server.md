# Lab 05: Broken Server -- Debugging Challenge

> **Module**: 1 -- Linux Deep Dive  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Complete Labs 01-04 (you'll need everything you've learned)

---

## Overview

Welcome to your first debugging challenge. This is the most important exercise in Module 1.

A FlowForge "production" server has **5 deliberate misconfigurations**. The system was working perfectly yesterday. Something (or several things) changed overnight. Your job is to find all 5 issues and fix them.

This lab tests your ability to combine everything from Module 1: filesystem knowledge, permissions, processes, systemd, packages, bash scripting, and SSH concepts. There is no step-by-step guide here -- just symptoms and your skills.

> **Why this matters**: In production, nobody tells you what's broken. You get a page at 3 AM that says "the app is down." Your job is to figure out why. This is the skill that separates engineers from copy-pasters.

---

## The Scenario

You are the on-call engineer for FlowForge. You receive the following alert at 2:47 AM:

> **ALERT**: FlowForge health check FAILING. API service unreachable. Multiple subsystems degraded.

You SSH into the server and begin investigating.

---

## Setup Instructions

Before you begin debugging, you need to set up the broken server environment. Run the setup steps below to introduce the 5 misconfigurations. (In a real scenario, you wouldn't know what the setup did -- but since this is a learning exercise, you need to create the broken state yourself.)

**Setup**: Create a script called `break-server.sh` that does the following. **Read these instructions, run the script, then CLOSE the script file and don't look at it again until you've found all 5 issues.**

The script should:
1. Set up a simulated FlowForge environment (if you haven't already from earlier labs):
   - Create service users, directories, config files, a systemd unit, and a simple health check script
2. Introduce exactly 5 misconfigurations across different areas of the system
3. Print "Server is now 'broken'. Good luck!" when done

**IMPORTANT**: Write the script based on your Labs 01-04 work. The misconfigurations should cover different domains:
- One related to file permissions
- One related to systemd/services
- One related to disk/filesystem
- One related to environment variables or configuration
- One related to user/group settings

After running the script, close it and switch to detective mode.

---

## What You'll Observe (Symptoms)

Once the server is "broken," you'll observe these symptoms. Your job is to find the **root cause** of each, not just fix the symptom.

### Symptom 1: The API service won't start

When you try to start the FlowForge API service, it fails. systemd reports an error. The service worked yesterday.

**What to investigate:**
- What does `systemctl status` say?
- What do the journald logs show?
- Is the binary/script present? Can it be executed?
- What user is the service trying to run as?

---

### Symptom 2: The health check script reports all failures

Running the health check script from Lab 03 produces errors or unexpected failures, even for things that should be working.

**What to investigate:**
- Does the script execute at all?
- Are there permission issues?
- Is the environment loaded correctly?
- Are the dependencies (tools/commands) the script needs available?

---

### Symptom 3: A critical configuration file is inaccessible

One of the FlowForge configuration files that the services need cannot be read by the service users, even though it exists on disk.

**What to investigate:**
- What do the file permissions look like?
- What user/group owns the file?
- Did something change about the service user?
- Is SELinux or AppArmor involved? (Probably not on your setup, but in production you'd check)

---

### Symptom 4: Disk space or filesystem issues

Something is consuming an unusual amount of space, or a filesystem/directory is not behaving as expected.

**What to investigate:**
- What does disk usage look like?
- Are there any unexpectedly large files?
- Are all expected directories present and accessible?
- Can the services write to the directories they need?

---

### Symptom 5: A scheduled or automatic process is misconfigured

Something that should be running automatically (or something that shouldn't be running) is in the wrong state.

**What to investigate:**
- Are the right services enabled/disabled?
- Is there a cron job or timer that's wrong?
- Is a process running that shouldn't be, or missing that should be running?
- Check process ownership and state

---

## Your Task

For **each** of the 5 issues:

1. **Describe the symptom**: What did you observe?
2. **Document your investigation**: What commands did you run? What did the output tell you?
3. **Identify the root cause**: What was misconfigured and why does it cause this symptom?
4. **Fix the issue**: What command(s) did you run to fix it?
5. **Verify the fix**: How did you confirm the issue is resolved?

Write your findings in a file called `incident-report.md`. Use this format for each issue:

```markdown
## Issue N: [Brief Title]

**Symptom**: What you observed
**Investigation**: Commands you ran and what you learned
**Root Cause**: What was wrong and why
**Fix**: Commands to resolve it
**Verification**: How you confirmed the fix worked
```

---

## Rules of Engagement

1. **Do NOT look at the break-server.sh script** until you've found all 5 issues
2. **Document everything** as you go -- not after the fact
3. **Use systematic debugging**: Don't just guess. Follow a methodology:
   - Check logs first
   - Check service status
   - Check permissions
   - Check configuration
   - Check resources (disk, memory, processes)
4. **Verify each fix independently** before moving to the next issue
5. **Time yourself**: Note how long it takes. You'll do this again in later modules and should improve.

---

## Completion Criteria

- [ ] All 5 issues identified with correct root causes
- [ ] All 5 issues fixed and verified
- [ ] `incident-report.md` completed with investigation steps for each issue
- [ ] FlowForge API service starts and runs successfully
- [ ] Health check script passes all checks
- [ ] All FlowForge config files are accessible by the correct users
- [ ] No disk/filesystem anomalies remain
- [ ] All services and scheduled tasks are in their correct state

---

## Checkpoint Questions

> After completing the debugging challenge:
> 1. What was your debugging methodology? Did you have a systematic approach or did you jump around?
> 2. Which issue took the longest to find? Why?
> 3. If you could only run 5 commands to assess the overall health of a Linux server, what would they be and why?
> 4. How would you prevent each of these issues from happening in production? (Think: monitoring, automation, code review)

---

## What's Next?

Congratulations -- you've completed all the labs in Module 1! Head to the [Exit Gate Checklist](checklist.md) to verify you've mastered everything before moving to Module 2: Networking Fundamentals.

> **Reflection**: The debugging skills you just practiced are the same ones you'll use in EVERY module's debugging challenge. The domain changes (Docker, AWS, Kubernetes, etc.) but the methodology stays the same: observe symptoms, form hypotheses, gather evidence, identify root causes, fix and verify.
