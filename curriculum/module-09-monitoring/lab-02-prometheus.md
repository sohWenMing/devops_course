# Lab 02: Prometheus Deployment and PromQL

> **Module**: 9 -- Monitoring and Observability  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Lab 01 completed (FlowForge services exposing /metrics endpoints). Kind cluster running with FlowForge deployed (Module 8). Read the [Prometheus Architecture](#) and [PromQL](#) sections of the Module 9 README.

---

## Overview

Your services are emitting metrics, but nobody is collecting them. In this lab you'll deploy Prometheus to your Kubernetes cluster to scrape those metrics, and then learn PromQL to extract meaningful insights from the data.

---

## Exercise 2a: Deploying Prometheus to Kubernetes

### Objectives

- Deploy Prometheus to your Kind cluster using raw Kubernetes manifests (not Helm)
- Configure scrape targets for api-service and worker-service
- Verify targets are UP in the Prometheus UI
- Understand the pull model in practice

### What You'll Do

**Part 1: Create Prometheus Kubernetes Manifests**

1. Create a dedicated namespace for monitoring (e.g., `monitoring`). All monitoring components (Prometheus, Grafana, Loki) will live here, separate from your application namespace.

2. Create a ConfigMap containing the Prometheus configuration (`prometheus.yml`). This config needs:
   - A global scrape interval (15s is a good default)
   - A scrape job for `api-service` -- think about how to target it. In Kubernetes, you can use the Service DNS name (e.g., `api-service.default.svc.cluster.local:8080`)
   - A scrape job for `worker-service` (on its metrics port)
   - A scrape job for Prometheus itself (yes, Prometheus monitors itself at `localhost:9090/metrics`)

3. Think about: why use a ConfigMap for the Prometheus config instead of baking it into the container image? What advantage does this give you?

4. Create a Deployment for Prometheus:
   - Use the official `prom/prometheus` image
   - Mount the ConfigMap as a volume at `/etc/prometheus/`
   - Expose port 9090
   - Think about resource requests/limits -- Prometheus can be memory-hungry with many time series

5. Create a Service (NodePort or ClusterIP) to expose the Prometheus UI. If using Kind, you'll need to be able to access port 9090 from your browser.

6. Optionally, create a PersistentVolumeClaim for Prometheus's data directory (`/prometheus`) so metrics survive Pod restarts.

**Part 2: Deploy and Verify**

7. Apply all manifests: `kubectl apply -f` your Prometheus manifests.

8. Wait for the Prometheus Pod to be Running. Check logs for any configuration errors.

9. Access the Prometheus UI (port-forward if using ClusterIP: `kubectl port-forward -n monitoring svc/prometheus 9090:9090`).

10. Navigate to **Status → Targets** in the Prometheus UI. You should see your scrape jobs listed:
    - `api-service` -- is the target UP or DOWN?
    - `worker-service` -- is the target UP or DOWN?
    - `prometheus` -- should be UP (it scrapes itself)

11. If any targets are DOWN, troubleshoot:
    - Can Prometheus reach the service? (Think: namespaces, DNS, ports)
    - Is the metrics endpoint correct? (Try `kubectl exec` into the Prometheus Pod and `wget` the metrics URL)
    - Are your services actually exposing `/metrics`?

**Part 3: Explore Collected Metrics**

12. In the Prometheus UI, go to the **Graph** tab. Type `http_requests_total` and click **Execute**. You should see the counter values from your api-service.

13. Try `up` -- this built-in metric shows 1 for each target that's UP and 0 for DOWN. Verify all your targets show 1.

14. Generate some traffic to your api-service (create tasks, list tasks, health checks) and watch the metrics update in Prometheus. Remember there's a delay of up to one scrape interval (15s) between the event and when Prometheus sees it.

### Expected Outcome

- Prometheus running in the `monitoring` namespace on your Kind cluster
- All FlowForge service targets showing as UP in the Prometheus UI
- Prometheus scraping itself and showing its own metrics
- Metrics from Lab 01 visible and queryable in the Prometheus Graph tab

### Checkpoint Questions

- [ ] Why did you deploy Prometheus using raw manifests instead of Helm? What would Helm give you? (You'll learn this distinction matters in production)
- [ ] What happens if api-service restarts? Does Prometheus lose the old metrics? Does it notice the restart?
- [ ] Why does Prometheus scrape itself? What metrics does it expose about its own health?
- [ ] If you add a third service to FlowForge, what would you need to change in the Prometheus config? How many files/manifests need to change?
- [ ] What's the trade-off of a shorter scrape interval (e.g., 5s) vs a longer one (e.g., 60s)?

---

## Exercise 2b: Writing PromQL Queries

### Objectives

- Write PromQL queries to answer real operational questions about FlowForge
- Understand `rate()`, `histogram_quantile()`, aggregation operators, and label matching
- Build the muscle memory for writing queries from scratch
- Practice the query patterns you'll use for Grafana dashboards and alerting rules

### What You'll Do

**Part 1: Basic Queries and Rate**

1. Before writing any queries, generate sustained traffic to api-service. Create a script or loop that:
   - Creates tasks (POST /tasks) at a steady rate
   - Reads tasks (GET /tasks) frequently
   - Occasionally requests non-existent resources (to generate 404s)
   - Keep this running in the background while you work on queries

2. Write a PromQL query to find the **total request rate** (requests per second) across all endpoints:
   - Start with `http_requests_total` -- what do you see?
   - Now wrap it with `rate()` and a `[5m]` range -- what changes?
   - What does the `[5m]` window do? Try `[1m]` and `[15m]` -- how do the results differ?

3. Write a query to find the request rate **broken down by HTTP method**. Use the `by` clause.

4. Write a query to find the request rate **for only 5xx errors**. Use label matching with a regex: `status=~"5.."`.

**Part 2: Error Percentage**

5. Write a PromQL query to calculate the **error percentage** -- what fraction of requests are returning 5xx status codes? You'll need:
   - Numerator: rate of 5xx requests
   - Denominator: rate of ALL requests
   - Division to get the fraction
   - Multiply by 100 if you want a percentage

6. Think about edge cases: what happens if the denominator is 0 (no requests at all)? PromQL returns NaN for division by zero. Is that acceptable for a dashboard? For an alert?

**Part 3: Latency Percentiles**

7. Write a PromQL query to find the **95th percentile request latency** using `histogram_quantile()`:
   - Start with `rate(http_request_duration_seconds_bucket[5m])` -- what does this give you?
   - Wrap it with `histogram_quantile(0.95, ...)` -- what's the result?
   - The result is in seconds. What does this number mean in plain English?

8. Write queries for the **50th percentile** (p50, median) and **99th percentile** (p99). How do they compare?

9. Break down the 95th percentile **by endpoint path**. Which endpoints are slowest?

**Part 4: Aggregation and Top-K**

10. Write a query to find the **top 5 endpoints by request rate**:
    - Use `topk(5, ...)` with `sum(rate(...)) by (path)`
    - Which endpoints get the most traffic?

11. Write a query to find the **total number of active connections across all instances** of api-service:
    - Use `sum()` on the gauge metric
    - Why do you use `sum()` without `rate()` for gauges?

**Part 5: FlowForge Business Queries**

12. Write a PromQL query to find the **task creation rate** (tasks created per minute):
    - `rate(flowforge_tasks_created_total[5m]) * 60` -- why multiply by 60?

13. Write a query to show the **current queue depth**:
    - `flowforge_queue_depth` -- is this an instant vector or a range vector?

14. Write a query to find the **95th percentile task processing duration**:
    - Use `histogram_quantile(0.95, rate(flowforge_task_processing_duration_seconds_bucket[5m]))`

15. Write a query that tells you whether tasks are **being processed faster than they're created** (is the queue growing or shrinking?):
    - Compare `rate(flowforge_tasks_created_total[5m])` with `rate(flowforge_tasks_completed_total[5m])`
    - If creation rate > completion rate, the queue is growing

**Part 6: Document Your Queries**

16. Create a document (or comments in a file) listing all your queries with:
    - The question the query answers (in plain English)
    - The PromQL expression
    - What the result means
    - When you'd use this query (dashboard? alert? ad-hoc investigation?)

### Expected Outcome

- A collection of working PromQL queries covering: request rate, error percentage, latency percentiles (p50, p95, p99), top-K endpoints, business metrics
- Understanding of when to use `rate()` vs raw values
- Understanding of `histogram_quantile()` for percentile calculations
- A documented query reference you can use for Grafana dashboards in Lab 03

### Checkpoint Questions

- [ ] Write a PromQL query from scratch: "What percentage of requests in the last hour returned 5xx?" Do it without looking at your notes.
- [ ] Explain in plain English what `rate(http_requests_total[5m])` does. What would happen if you used `[1s]` instead of `[5m]`?
- [ ] Why can't you use `rate()` on a gauge? What function would you use instead if you wanted to see how fast a gauge is changing?
- [ ] What's the difference between `sum(rate(...)) by (path)` and `sum by (path) (rate(...))`? (Trick question!)
- [ ] If you had to add a new PromQL query to answer "Is FlowForge healthy right now?" -- what single query would you write?
