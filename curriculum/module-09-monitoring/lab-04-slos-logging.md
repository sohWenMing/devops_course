# Lab 04: SLOs and Structured Logging with Loki

> **Module**: 9 -- Monitoring and Observability  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Lab 03 completed (Grafana deployed with FlowForge dashboard, alerting rules in place). Read the [SLOs, SLIs, and SLAs](#) and [Structured Logging with Loki](#) sections of the Module 9 README.

---

## Overview

Your dashboards show you what's happening, and your alerts tell you when things go wrong. But how do you answer the question "Is FlowForge reliable enough?" -- not just right now, but over time? In this lab you'll define Service Level Objectives (SLOs) that set reliability targets, and deploy Grafana Loki for centralized log aggregation so you can correlate metrics with log entries.

---

## Exercise 4a: Define SLOs and Create an SLO Dashboard

### Objectives

- Define meaningful SLOs for FlowForge with specific SLIs
- Calculate error budgets and understand burn rate
- Create an SLO dashboard in Grafana that shows compliance status
- Understand the relationship between SLOs, error budgets, and engineering decisions

### What You'll Do

**Part 1: Define FlowForge SLOs**

1. Define three SLOs for FlowForge. For each, identify the SLI (what you measure) and the SLO (what target you set):

**SLO 1: Availability**
- SLI: The proportion of successful HTTP requests (non-5xx) to total requests
- SLO target: 99.9% over a 30-day rolling window
- Think about: what counts as "unavailable"? Just 5xx errors? What about timeouts? What about 4xx errors (those are usually the client's fault, not yours)?

**SLO 2: Latency**
- SLI: The proportion of HTTP requests completing within 500ms (p99)
- SLO target: 99% of requests complete in < 500ms over a 30-day rolling window
- Think about: why 500ms? Is that the right threshold for FlowForge? What do your current p99 numbers look like?

**SLO 3: Task Processing Time**
- SLI: The proportion of tasks processed within 30 seconds
- SLO target: 99.5% of tasks complete processing in < 30 seconds over a 30-day rolling window
- Think about: this is a business-level SLO, not an infrastructure SLO. Why is this different from API latency?

2. For each SLO, write the PromQL expression that calculates the SLI value. For example, the availability SLI would be something like:
   ```
   1 - (rate of 5xx requests / rate of total requests)
   ```
   Express this as a proper PromQL query.

**Part 2: Calculate Error Budgets**

3. For your 99.9% availability SLO, calculate the error budget:
   - In a 30-day month, how many minutes of downtime are allowed?
   - In a 30-day month, if you serve 1 million requests, how many can be errors?
   - Show your math

4. Calculate the error budget for the latency SLO (99% under 500ms):
   - How many requests per million can exceed 500ms?
   - Is this more or less forgiving than the availability SLO?

5. Calculate the error budget for the task processing SLO (99.5% under 30s):
   - How many tasks per 1000 can exceed 30 seconds?

6. Think about: if you've consumed 80% of your monthly error budget with 10 days remaining, what should you do? What if you've consumed 20% with 1 day remaining?

**Part 3: Understand Burn Rate**

7. Calculate burn rates for different scenarios:
   - If your error rate is 0.1% (matching your SLO), what's the burn rate? (Answer: 1x)
   - If your error rate is 1% (10x your budget rate), what's the burn rate? How quickly would you exhaust your 30-day budget?
   - If your error rate is 10%, what's the burn rate? How long until your budget is gone?

8. Think about alerting on burn rate:
   - A "fast burn" alert: burn rate > 14.4x for 1 hour (you'll exhaust your budget in ~2 days)
   - A "slow burn" alert: burn rate > 6x for 6 hours (you'll exhaust your budget in ~5 days)
   - Why have two burn rate alerts instead of one? What does each catch that the other misses?

**Part 4: Create SLO Dashboard in Grafana**

9. Create a new Grafana dashboard called "FlowForge SLOs". Add the following panels:

**Panel 1: Availability SLI (Current)**
- Stat panel showing the current availability percentage (e.g., 99.95%)
- Color thresholds: green if above SLO (99.9%), yellow if within 0.1% of SLO, red if below SLO

**Panel 2: Error Budget Remaining**
- Gauge panel showing what percentage of the monthly error budget remains
- Think about: how do you calculate "budget consumed"? You need to track cumulative errors over the rolling window and compare to the total allowed

**Panel 3: Burn Rate**
- Stat panel showing the current burn rate (should hover around 1x when healthy)
- Thresholds: green (< 1x), yellow (1-6x), red (> 6x)

**Panel 4: SLI Over Time**
- Time series panel showing the rolling availability SLI over the last 7 days
- Add a horizontal line at the SLO target (99.9%)
- This shows whether you're trending above or below your target

**Panel 5: Latency SLI**
- Stat panel for the latency SLO compliance (% of requests under 500ms)

**Panel 6: Task Processing SLI**
- Stat panel for the task processing SLO compliance (% of tasks under 30s)

10. Save and export the dashboard JSON.

### Expected Outcome

- Three defined SLOs with specific SLI expressions, targets, and error budget calculations
- An SLO dashboard in Grafana with panels for: current availability, error budget remaining, burn rate, SLI over time, latency SLI, task processing SLI
- Written error budget calculations showing minutes of downtime allowed
- Understanding of how burn rate relates to error budget consumption

### Checkpoint Questions

- [ ] Explain the difference between SLO, SLI, and SLA to a product manager in plain English. No jargon.
- [ ] Calculate from memory: how many minutes of downtime does a 99.9% SLO allow per month? What about 99.99%?
- [ ] If your error rate is 0.5% and your SLO is 99.9%, what's your burn rate? How long until your monthly error budget is exhausted?
- [ ] Why is it important to have error budgets? What decisions do they enable that raw uptime percentages don't?
- [ ] For a new service (say a payment processing API), define an SLO. Justify why you chose that target and not higher or lower.

---

## Exercise 4b: Deploy Grafana Loki for Structured Log Aggregation

### Objectives

- Deploy Grafana Loki and Promtail to your Kind cluster
- Configure FlowForge to send structured JSON logs that Loki can query
- Query logs in Grafana using LogQL alongside metrics
- Correlate an error rate spike in metrics with specific error log entries

### What You'll Do

**Part 1: Deploy Loki**

1. Create Kubernetes manifests for Loki in the `monitoring` namespace:
   - A Deployment for Loki using the official `grafana/loki` image
   - A Service to expose Loki internally (Promtail pushes to Loki, Grafana queries it)
   - A ConfigMap with basic Loki configuration (auth disabled, local storage)
   - Think about: Loki stores log indexes and chunks. For a Kind cluster, local storage is fine. In production, you'd use S3 or GCS.

2. Deploy Promtail as a DaemonSet:
   - Promtail runs on every node and tails container logs
   - It needs access to the node's `/var/log/pods` directory (host path volume mount)
   - Configure it to push logs to the Loki Service URL
   - It automatically adds Kubernetes labels (namespace, pod, container) to log entries

3. Apply all manifests. Verify Loki and Promtail are running:
   - `kubectl get pods -n monitoring` should show Loki and Promtail pods
   - Check Promtail logs to confirm it's tailing container logs and pushing to Loki

**Part 2: Configure Grafana to Query Loki**

4. In Grafana, add Loki as a data source:
   - Navigate to Configuration → Data Sources → Add data source → Loki
   - Set the URL to the Loki Service DNS name (e.g., `http://loki.monitoring.svc.cluster.local:3100`)
   - Click "Save & Test"

5. Go to the Explore page in Grafana. Select the Loki data source. Run a basic query:
   - `{namespace="default"}` -- shows all logs from the default namespace
   - `{app="api-service"}` -- shows all logs from api-service (if your Pods have an `app` label)
   - You should see log entries streaming from your FlowForge services

**Part 3: Structured JSON Logging**

6. Verify that your FlowForge services are outputting structured JSON logs (you set this up in Module 3, Lab 4c). If not, update them now.
   
   Good structured log output looks like:
   ```json
   {"level":"info","msg":"request completed","method":"GET","path":"/tasks","status":200,"duration_ms":12,"request_id":"abc-123","ts":"2025-01-15T10:30:00Z"}
   ```
   
   Bad unstructured log output looks like:
   ```
   2025-01-15 10:30:00 INFO request completed GET /tasks 200 12ms
   ```

7. With structured JSON logs, you can use LogQL's JSON parser to filter on specific fields:
   - `{app="api-service"} | json | level="error"` -- only error-level logs
   - `{app="api-service"} | json | status >= 500` -- only 5xx responses
   - `{app="api-service"} | json | duration_ms > 1000` -- only slow requests (>1s)

8. Try these queries in Grafana's Explore page. Do they return the expected results?

**Part 4: Correlate Metrics and Logs**

9. Now for the real test: **correlate a metrics spike with log entries**.

10. Generate a scenario that causes an error spike:
    - Temporarily break the database connection (e.g., scale down PostgreSQL, or change the DB_HOST env var)
    - This should cause 5xx errors in api-service

11. In Grafana, open your FlowForge Overview dashboard (from Lab 03). You should see:
    - Request rate might stay steady (requests are still coming in)
    - Error rate spikes to near 100%
    - Latency might change (depending on how the error manifests)

12. From the dashboard, select the time range of the spike. Then switch to the Explore page with the Loki data source and query:
    - `{app="api-service"} | json | level="error"` for the same time range
    - You should see the specific error messages: "connection refused", "database unreachable", etc.
    - The log entries tell you WHAT went wrong; the metrics told you WHEN and HOW MUCH

13. If your logs include request IDs, try finding a specific request:
    - `{app="api-service"} | json | request_id="<specific-id>"` -- trace one request's journey

14. Fix the database connection and observe the error rate return to normal.

**Part 5: Add Log Panel to Dashboard**

15. Add a "Recent Errors" panel to your FlowForge Overview dashboard:
    - Use a Logs panel type with the Loki data source
    - Query: `{app="api-service"} | json | level="error"`
    - This gives you metrics AND recent error logs on the same dashboard

16. Think about: having logs next to metrics on the same dashboard -- what investigation workflows does this enable? What would you lose if you only had metrics or only had logs?

### Expected Outcome

- Loki and Promtail running in the `monitoring` namespace
- Grafana connected to both Prometheus and Loki as data sources
- Structured JSON logs from FlowForge queryable with LogQL in Grafana
- Successful correlation of a metrics spike with corresponding log entries
- FlowForge Overview dashboard updated with a logs panel

### Checkpoint Questions

- [ ] Explain how Loki differs from Elasticsearch/ELK. What's the key trade-off in Loki's design (hint: indexing)?
- [ ] Correlate a spike in error rate metrics with specific error log entries. Walk through the investigation process step by step.
- [ ] Why does structured (JSON) logging matter for Loki? What queries become possible with structured logs that aren't possible with unstructured logs?
- [ ] If you had to choose between Prometheus (metrics) and Loki (logs) for FlowForge, which would you keep? Justify your answer.
- [ ] In production with 100 services each generating 10GB of logs per day, what would you need to think about for Loki? (Hint: storage, retention, cost)
