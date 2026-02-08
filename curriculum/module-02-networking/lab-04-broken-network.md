# Lab 04: Broken Network -- Debugging Challenge

> **Module**: 2 -- Networking Fundamentals  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Complete Labs 01-03 (you'll need everything you've learned)

---

## Overview

Welcome to your second debugging challenge. This time, the problem isn't a single machine -- it's the network between machines (simulated using network namespaces and local services).

A FlowForge deployment has **multiple networking issues** spanning different layers of the stack. Services that were communicating yesterday are now failing in various ways. Your job is to diagnose every issue and fix it, using the layered debugging approach you've been building throughout this module.

> **Why this matters**: In production, networking problems are the most common -- and the most frustrating -- class of failures. "It works on my machine" usually means "there's a networking difference between here and there." Engineers who can systematically debug network issues are worth their weight in gold.

---

## The Scenario

You are the on-call engineer for FlowForge. At 3:12 AM, you receive a cascade of alerts:

> **ALERT**: FlowForge health check FAILING  
> **ALERT**: api-service cannot reach database  
> **ALERT**: DNS resolution failures detected  
> **ALERT**: External clients report "connection refused" for the API  
> **ALERT**: TLS certificate warnings in client logs

The system was working perfectly at midnight. Something changed -- but the change log is empty (sound familiar?).

---

## Setup Instructions

Before you debug, you need to create the broken network environment. Build a setup script called `break-network.sh` that creates the FlowForge networking environment and then introduces the failures.

**Your script should set up:**

1. **Network namespaces** (from Lab 03 Exercise 3b):
   - `ns-public` -- simulating the public-facing subnet (for the load balancer/proxy)
   - `ns-app` -- simulating the application subnet (for api-service)
   - `ns-db` -- simulating the database subnet (for PostgreSQL)
   - Connected via veth pairs through the host (acting as a router)
   - Proper IP addressing on different subnets

2. **Services**:
   - A simple HTTP server in `ns-app` acting as api-service (port 8080)
   - A simple TCP listener in `ns-db` acting as PostgreSQL (port 5432)
   - nginx on the host or in `ns-public` acting as a reverse proxy

3. **DNS**: Local entries in `/etc/hosts` or a local configuration for FlowForge service names

4. **Firewall**: iptables rules to control traffic between subnets

5. **TLS**: A certificate and HTTPS configuration for the reverse proxy

**Then your script should introduce networking issues across multiple layers.** The issues should cover at least these categories:
- A **DNS resolution** problem
- A **firewall rule** problem
- A **routing** problem
- A **port binding or port conflict** issue
- A **TLS/certificate** problem

**IMPORTANT**: Write the script, run it, then close the script file and don't look at it again until you've found and fixed all issues.

---

## What You'll Observe (Symptoms)

Once the network is "broken," you'll encounter these symptoms. Each symptom may have one or more underlying causes. Your job is to find the **root cause** of each, identify which **OSI layer** the problem exists at, and fix it.

### Symptom 1: api-service cannot resolve the database hostname

When api-service (in ns-app) tries to connect to the database using its hostname, the name resolution fails. The IP address of the database server hasn't changed.

**What to investigate:**
- How does name resolution work in this environment?
- What files control local name resolution?
- Is the DNS configuration correct in the namespace?
- Can you resolve other hostnames? Just this one fails?

---

### Symptom 2: Even with the correct IP, api-service cannot reach the database port

After bypassing the DNS issue and using the direct IP address, api-service still cannot establish a TCP connection to the database on port 5432.

**What to investigate:**
- Can you ping the database IP from the app namespace?
- If ping works but TCP doesn't, what layer is the problem at?
- Are there firewall rules blocking the traffic?
- Is the database service actually listening? On which address?
- Check rules in both directions -- inbound AND outbound

---

### Symptom 3: External clients cannot reach the reverse proxy

Clients trying to connect to the FlowForge API from outside the network receive "connection refused" errors.

**What to investigate:**
- Is the reverse proxy (nginx) running?
- What port is it listening on? What address is it bound to?
- Are there firewall rules affecting inbound traffic to the proxy?
- Is there a port conflict preventing the proxy from starting?
- Check nginx error logs for startup failures

---

### Symptom 4: Traffic between subnets is not being routed

Even when individual services are running and firewalls are open, packets from one subnet don't reach the other subnet.

**What to investigate:**
- Is IP forwarding enabled on the host (the router)?
- Are the routing tables in each namespace correct?
- Is there a default route? Does it point to the right gateway?
- Can you trace the path a packet would take? Where does it get stuck?

---

### Symptom 5: HTTPS connections fail with certificate errors

Clients that connect via HTTPS receive TLS errors and the handshake fails.

**What to investigate:**
- Is the certificate valid (not expired)?
- Does the certificate's Subject or SANs match the hostname being used?
- Is the certificate file readable by the service?
- Is the private key file present and matching the certificate?
- Use `openssl s_client` to inspect what the server presents

---

## Your Task

For **each** issue you find:

1. **Describe the symptom**: What did you observe? What error messages did you see?
2. **Identify the OSI layer**: At which layer does this problem exist? (This is new compared to Module 1's debugging challenge)
3. **Document your investigation**: What commands did you run? What did each output tell you?
4. **Identify the root cause**: What was misconfigured and why does it cause this symptom?
5. **Fix the issue**: What command(s) did you run to fix it?
6. **Verify the fix**: How did you confirm the issue is resolved?

Write your findings in a file called `network-incident-report.md`. Use this format for each issue:

```markdown
## Issue N: [Brief Title]

**Symptom**: What you observed
**OSI Layer**: Which layer the problem exists at and why
**Investigation**: Commands you ran and what you learned at each step
**Root Cause**: What was wrong and why
**Fix**: Commands to resolve it
**Verification**: How you confirmed the fix worked
**Prevention**: How would you prevent this in production?
```

---

## Debugging Methodology: Layered Approach

Use this systematic approach for network debugging (bottom-up through the stack):

```
Layer 1 (Physical):  Is the link up? (ip link show)
Layer 2 (Data Link): Can we reach the local network? (arping, arp table)
Layer 3 (Network):   Can we ping the destination? (ping, ip route)
Layer 4 (Transport): Can we connect to the port? (ss, nc, telnet)
Layer 7 (Application): Does the application respond correctly? (curl, dig)
```

At each layer, if the check passes, move up. If it fails, you've found the layer where the problem lives. Then dig deeper at that layer to find the root cause.

---

## Rules of Engagement

1. **Do NOT look at break-network.sh** until you've found all issues
2. **For each issue, identify the OSI layer** -- this is a key skill
3. **Use the layered debugging methodology** -- don't jump straight to Layer 7
4. **Document as you go** -- your incident report is part of the deliverable
5. **Verify each fix independently** before moving on
6. **Time yourself** -- compare to your Module 1 debugging time

---

## Completion Criteria

- [ ] All networking issues identified with correct root causes
- [ ] Each issue mapped to the correct OSI layer
- [ ] All issues fixed and verified
- [ ] `network-incident-report.md` completed with layered investigation for each issue
- [ ] api-service can resolve and connect to the database
- [ ] External clients can reach the reverse proxy
- [ ] Traffic routes correctly between all subnets
- [ ] HTTPS connections succeed without certificate errors
- [ ] End-to-end test: external request → proxy → api-service → database all works

---

## Checkpoint Questions

> After completing the debugging challenge:
> 1. For each issue you found, at which OSI layer did the problem exist? Could you have determined the layer faster?
> 2. What is your network debugging methodology now? Is it different from your Module 1 system debugging methodology?
> 3. If you could only run 5 commands to assess network health, what would they be and why?
> 4. How would you monitor for these types of issues in production before they cause alerts? (Preview for Module 9)
> 5. Compare this experience to Module 1's Broken Server. How is network debugging different from single-system debugging?

---

## What's Next?

Congratulations -- you've completed all the labs in Module 2! Head to the [Exit Gate Checklist](checklist.md) to verify you've mastered everything before moving to Module 3: Building FlowForge in Go.

> **Reflection**: You now have two debugging experiences under your belt -- system-level (Module 1) and network-level (Module 2). Every future module adds a new debugging dimension: application-level (Module 3), container-level (Module 4), cloud-level (Module 5), infrastructure-as-code (Module 6), pipeline (Module 7), orchestration (Module 8), observability (Module 9), and security (Module 10). The methodology is always the same: observe, hypothesize, test, fix, verify. The domain changes, but the skill doesn't.
