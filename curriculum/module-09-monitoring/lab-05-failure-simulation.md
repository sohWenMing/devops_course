# Lab 05: Failure Simulation

> **Module**: 9 -- Monitoring and Observability  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Labs 01-04 completed (FlowForge instrumented, Prometheus scraping, Grafana dashboard and alerts, SLOs defined, Loki deployed). All monitoring components running on Kind.

---

## Overview

You've built a complete monitoring stack: metrics, dashboards, alerts, SLOs, and log aggregation. But does it actually work when things go wrong? In this lab you'll deliberately break FlowForge in three different ways and diagnose each failure **using only your monitoring tools** -- no `kubectl` allowed until you've formed a hypothesis.

This is the real test: in production, you won't have a lab document telling you what broke. You'll have a pager alert and a dashboard. Can you figure it out?

---

## Exercise 5: Break Things and Diagnose from Monitoring

### Objectives

- Deliberately cause three different types of failures in FlowForge
- Observe alerts firing and dashboards reflecting the issues
- Diagnose each failure from monitoring data alone (metrics + logs + dashboards)
- Verify your diagnosis with kubectl only AFTER forming a hypothesis
- Practice the investigation workflow you'd use in a real incident

### What You'll Do

**Important Rule**: For each failure scenario, you MUST:
1. Cause the failure
2. Switch to your Grafana dashboard (or wait for an alert)
3. Diagnose the issue using ONLY metrics, logs, and dashboards
4. Write down your hypothesis ("I think X is broken because Y")
5. THEN (and only then) use `kubectl` to verify your hypothesis

This simulates real incident response: your monitoring should tell you what's wrong before you need to dig into the infrastructure.

---

**Scenario 1: Kill a Worker Pod**

### Setup

1. Ensure FlowForge is running normally with tasks being created and processed. Your dashboards should show steady request rates, low error rates, and a stable queue depth.

2. Generate a steady stream of new tasks (use a script or curl loop creating a new task every few seconds).

### Break It

3. Kill one of the worker-service Pods:
   ```
   kubectl delete pod <worker-pod-name>
   ```
   Do this in a separate terminal and then STOP looking at kubectl. Switch entirely to Grafana.

### Observe and Diagnose (Monitoring Only)

4. Watch your FlowForge Overview dashboard:
   - What happens to the queue depth panel?
   - What happens to the task processing rate?
   - Do any metrics from api-service change?
   - How long before you notice something is wrong?

5. Check the alerts page: does `WorkerQueueGrowing` enter pending state? If so, how long before it fires?

6. Check the logs in Grafana (Loki): are there any error messages from the worker? Any Pod termination signals?

7. Write your hypothesis:
   - "I believe [X] is broken because I see [Y] in metrics and [Z] in logs"
   - "The impact is [describe user impact]"
   - "Expected recovery: [how will K8s handle this?]"

### Verify

8. NOW use kubectl to verify:
   ```
   kubectl get pods
   kubectl describe pod <new-worker-pod>
   kubectl get events
   ```
   Was your hypothesis correct? Did Kubernetes restart the worker?

9. Watch the dashboard as the new worker Pod starts and begins processing the backlog. How long does it take for the queue to drain?

---

**Scenario 2: Exhaust Database Connections**

### Setup

10. Ensure everything is recovered from Scenario 1. Dashboards should be back to normal.

### Break It

11. Exhaust the database connection pool. There are several ways to do this:
    - Set the max connections to a very low number (e.g., 2) in your PostgreSQL config or Go connection pool settings and redeploy
    - Or create many concurrent requests that all hold database connections
    - Or scale up api-service replicas significantly so the total connections exceed the pool limit
    
    The exact method depends on your implementation. The goal: make the database refuse new connections.

12. Once the break is in place, STOP looking at kubectl/terminal and switch to Grafana.

### Observe and Diagnose (Monitoring Only)

13. Watch your dashboards:
    - What happens to the error rate on api-service?
    - What happens to the error rate on worker-service?
    - What happens to request latency? (Do errors respond faster or slower?)
    - What happens to queue depth? (Tasks can't be created or can't be processed?)

14. Check the logs:
    - What error messages appear in api-service logs?
    - What error messages appear in worker-service logs?
    - Can you identify the ROOT CAUSE from the logs? (Look for "connection refused", "too many connections", "pool exhausted", etc.)

15. Check alerts: which alerts fire? Do the right ones fire?

16. Write your hypothesis:
    - "The root cause is [X]"
    - "It affects [which services] because [reason]"
    - "Both api-service and worker-service are impacted because [they both depend on...]"

### Verify

17. Use kubectl and database tools to verify:
    - Check active database connections
    - Check api-service and worker-service Pod logs with kubectl
    - Was your monitoring-based diagnosis correct?

18. Fix the issue (restore connection limits). Watch the recovery on dashboards.

---

**Scenario 3: Introduce Artificial Latency**

### Setup

19. Ensure everything is recovered from Scenario 2. Dashboards should be back to normal.

### Break It

20. Introduce artificial latency into api-service. Options:
    - Add a `time.Sleep()` to a handler (e.g., 3-5 seconds per request) and redeploy
    - Use a network tool to add latency to traffic (e.g., `tc` if you have access to the Pod's network namespace)
    - Introduce a slow database query (e.g., `SELECT pg_sleep(3)` before each real query)

    The key: API requests should still succeed (200 OK) but take much longer than normal.

21. Once the latency is injected, switch to Grafana.

### Observe and Diagnose (Monitoring Only)

22. Watch your dashboards:
    - What happens to the latency panel? Which percentiles are affected most?
    - What happens to the error rate? (Trick question: if requests are slow but still succeeding, the error rate might stay low)
    - What happens to active connections? (Slow requests = connections held longer)
    - What happens to queue depth? (If the API is slow to enqueue tasks, what cascading effects occur?)

23. Check the SLO dashboard:
    - Is the latency SLO being violated?
    - What's the burn rate?
    - How long until the error budget is exhausted at this rate?

24. Check the logs:
    - Are there any errors? (Maybe not -- requests are slow but succeeding)
    - Can you find evidence of the latency in log entries? (If your structured logs include `duration_ms`, they'll show it)

25. Write your hypothesis:
    - "The issue is [X]"
    - "The error rate is [high/low] but latency is [high/low], which means [interpretation]"
    - "The SLO impact is [describe in terms of error budget]"

### Verify

26. Use kubectl to verify your diagnosis. Was the latency source what you expected?

27. Remove the artificial latency. Watch the dashboards recover.

---

**Part 4: Incident Report**

28. Write a brief incident report for each scenario. Include:
    - **Detection**: How was the issue detected? (Alert? Dashboard? User report?)
    - **Time to detect**: How long between the failure and your awareness?
    - **Diagnosis method**: What metrics/logs pointed you to the root cause?
    - **Root cause**: What actually broke?
    - **Impact**: What was the user-facing impact?
    - **Recovery**: How was the issue resolved? How long did recovery take?
    - **Improvement**: What could be improved in your monitoring to detect this faster or provide better signal?

29. Reflect on the three scenarios:
    - Which was easiest to diagnose from monitoring alone? Why?
    - Which was hardest? What additional instrumentation would have helped?
    - Did any alerts fire that shouldn't have? Did any alerts NOT fire that should have?

### Expected Outcome

- Three failure scenarios executed with monitoring-first diagnosis
- Written hypotheses formed BEFORE using kubectl, verified after
- Incident reports for each scenario documenting detection, diagnosis, root cause, impact, and improvement
- Understanding of how different types of failures manifest differently in metrics, logs, and alerts
- Identification of monitoring gaps (things that were hard to diagnose)

### Checkpoint Questions

- [ ] Watch your dashboards while someone (or a script) breaks something new. Can you diagnose the issue from monitoring alone, without knowing what was broken?
- [ ] Which is more useful for diagnosing Scenario 1 (killed Pod): metrics or logs? What about Scenario 2 (DB connections)? Scenario 3 (latency)?
- [ ] If you could add ONE more metric or dashboard panel to improve your diagnosis speed, what would it be?
- [ ] Describe a real production failure scenario that your current monitoring would NOT detect. What would you need to add?
- [ ] What's the difference between a failure your monitoring can detect in 30 seconds vs one that takes 15 minutes? What determines the detection speed?
