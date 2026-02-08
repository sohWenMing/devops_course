# Module 9: Monitoring and Observability -- Seeing Inside FlowForge

> **Duration**: Weeks 15-16  
> **Prerequisites**: Modules 1-8 completed (Linux, Networking, Go App, Docker, AWS, Terraform, CI/CD, Kubernetes)  
> **Link forward**: "Monitoring shows you what's happening. Security ensures bad things don't happen"  
> **Link back**: "Your FlowForge stack is running on Kubernetes. But how do you know it's healthy? How do you know *before your users do* that something is wrong?"

---

## Why Monitoring and Observability?

In Module 8 you deployed FlowForge to Kubernetes. Pods are running, Services are routing traffic, Deployments are managing replicas. But right now, if a worker starts taking 10x longer to process tasks, you won't know until users complain. If the database connection pool is slowly leaking, you won't know until the app crashes.

Production systems break. The question isn't *whether* they'll break -- it's **how fast can you detect, diagnose, and recover?**

Monitoring is the difference between:
- "Users reported the site has been down for 2 hours" (reactive)
- "Alert fired 30 seconds after error rate spiked, engineer diagnosed and rolled back in 4 minutes" (proactive)

> **Architecture Thinking**: Before adding monitoring to any system, ask: "What are the most important things I need to know about this system's health?" For FlowForge, you'd want to know: Are API requests being served? Are tasks being processed? How fast? Are there errors? Is the queue growing? These questions drive what you instrument -- not the other way around. Don't monitor everything; monitor what matters.

---

## The Three Pillars of Observability

Observability is the ability to understand a system's internal state from its external outputs. There are three primary signals:

### Metrics

**What**: Numeric measurements collected over time. Think counters, gauges, histograms.

**When to use**: When you need to answer "how much?" or "how fast?" questions. Request rate, error rate, latency, queue depth, CPU usage, memory consumption.

**Example**: "The 95th percentile latency for `/tasks` is 240ms" -- this tells you that 95% of requests complete in 240ms or less.

**Strengths**: Low storage cost, fast to query, great for dashboards and alerting, can aggregate across instances.

**Weaknesses**: Lack detail about individual requests. You know *that* latency spiked, but not *why* a specific request was slow.

### Logs

**What**: Timestamped text records of discrete events. Can be unstructured ("Error connecting to database") or structured (JSON with fields like level, message, request_id, service).

**When to use**: When you need to answer "what happened?" for a specific event. Error messages, stack traces, audit trails, request details.

**Example**: `{"level":"error","msg":"connection refused","host":"postgres:5432","request_id":"abc-123","ts":"2025-01-15T10:30:00Z"}`

**Strengths**: Rich context, human-readable, great for debugging specific issues.

**Weaknesses**: High storage cost at scale, expensive to search, hard to aggregate (you can't average a log message).

### Traces

**What**: Records of the journey of a single request through multiple services. Each service adds a "span" showing what it did and how long it took.

**When to use**: When you need to answer "where did the time go?" for a request that touches multiple services. API → worker → database → external API.

**Example**: A trace shows request abc-123 took 2.1s total: 50ms in api-service, 1.8s in worker-service (of which 1.5s was the database query), 250ms in response serialization.

**Strengths**: Shows causality across services, pinpoints bottlenecks in distributed systems.

**Weaknesses**: Complex to set up, highest overhead, requires correlation IDs propagated between services.

> **Architecture Thinking**: For each FlowForge failure scenario, which pillar would you check first?
> - API returning 500 errors → **Metrics** first (error rate spike on dashboard), then **Logs** (what error?)
> - Worker processing slowly → **Metrics** first (processing duration histogram), then **Traces** (where in the pipeline?)
> - Database connections exhausted → **Metrics** first (active connections gauge), then **Logs** (connection error messages)
> The pattern: metrics tell you *something is wrong*, logs and traces tell you *what and why*.

> **Link back to Module 3**: Remember the structured JSON logging you added with `log/slog` in Lab 4c? That structured logging is the foundation for log aggregation. The request IDs you propagated between api-service and worker-service? Those become trace correlation IDs.

> **AWS SAA Tie-in**: AWS CloudWatch provides metrics (like Prometheus), CloudWatch Logs provides log aggregation (like Loki), and AWS X-Ray provides distributed tracing. The concepts are identical -- different implementation. Understanding Prometheus and Grafana makes you better at CloudWatch, and vice versa.

---

## Application Instrumentation

Before you can monitor anything, your application needs to **emit** metrics. This is called **instrumentation** -- adding code to your application that records measurements.

### prometheus/client_golang

The standard Go library for Prometheus instrumentation is `prometheus/client_golang`. It provides:

- **Registry**: A collection of all metrics your application exposes
- **Collectors**: Objects that produce metrics (counters, gauges, histograms, summaries)
- **HTTP handler**: A handler that exposes all registered metrics at `/metrics` in Prometheus exposition format

### The /metrics Endpoint

Every instrumented application exposes a `/metrics` endpoint that Prometheus scrapes. The format looks like:

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/tasks",status="200"} 1547
http_requests_total{method="POST",path="/tasks",status="201"} 89
http_requests_total{method="GET",path="/tasks",status="500"} 3

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",path="/tasks",le="0.01"} 1200
http_request_duration_seconds_bucket{method="GET",path="/tasks",le="0.05"} 1450
http_request_duration_seconds_bucket{method="GET",path="/tasks",le="0.1"} 1520
http_request_duration_seconds_bucket{method="GET",path="/tasks",le="0.5"} 1547
http_request_duration_seconds_bucket{method="GET",path="/tasks",le="+Inf"} 1547
http_request_duration_seconds_sum{method="GET",path="/tasks"} 45.23
http_request_duration_seconds_count{method="GET",path="/tasks"} 1547
```

This is plain text. Every line is a metric with optional labels in curly braces. Prometheus scrapes this periodically (typically every 15-30 seconds).

### Metric Types

Prometheus has four core metric types:

| Type | What It Measures | Example | Key Rule |
|------|-----------------|---------|----------|
| **Counter** | Things that only go up | Total requests, total errors, total bytes sent | Never decreases (resets to 0 on restart). Use `rate()` to get per-second rate |
| **Gauge** | Things that go up and down | Current queue depth, active connections, temperature | Point-in-time value. Can increase or decrease |
| **Histogram** | Distribution of values in buckets | Request duration, response size | Define bucket boundaries. Calculates count, sum, and per-bucket counts |
| **Summary** | Like histogram but calculates quantiles client-side | Request duration percentiles | Pre-calculated quantiles (p50, p90, p99). Cannot be aggregated across instances |

> **Architecture Thinking**: When should you use a histogram vs a summary?
> - **Histogram**: When you need to aggregate across multiple instances (most common in K8s where you have multiple replicas). You can calculate any percentile server-side with PromQL.
> - **Summary**: When you need exact quantiles from a single instance and don't need to aggregate. Rarely used in modern setups.
> For FlowForge, you'll almost always want **histograms** because you run multiple replicas of api-service.

### Choosing Good Labels

Labels add dimensions to metrics. `http_requests_total{method="GET",path="/tasks",status="200"}` lets you filter and group by method, path, or status.

Rules for labels:
- **Do**: Use labels for dimensions you'll want to filter or group by (HTTP method, status code, endpoint)
- **Don't**: Use labels with high cardinality (user IDs, request IDs, timestamps). Each unique label combination creates a new time series, and Prometheus stores every time series in memory
- **Don't**: Put data in the metric name that belongs in a label. Use `http_requests_total{method="GET"}` not `http_get_requests_total`

> **Link back to Module 3**: In Lab 1b you designed REST API endpoints with proper HTTP verbs and status codes. Those same verbs and status codes become label values on your metrics. Good API design directly supports good instrumentation.

---

## Custom Business Metrics

Beyond standard HTTP metrics, you should instrument **business-specific** metrics that tell you whether your application is fulfilling its purpose.

For FlowForge, standard HTTP metrics tell you "the API is serving requests." But business metrics tell you "tasks are actually being created and processed":

| Metric | Type | What It Tells You |
|--------|------|-------------------|
| `flowforge_tasks_created_total` | Counter | Rate of new tasks entering the system |
| `flowforge_tasks_completed_total` | Counter | Rate of tasks being successfully processed |
| `flowforge_task_processing_duration_seconds` | Histogram | How long workers take to process tasks |
| `flowforge_queue_depth` | Gauge | How many tasks are waiting to be processed |

These metrics answer the question every stakeholder cares about: **Is the system doing its job?**

If `tasks_created_total` is increasing but `tasks_completed_total` is flat and `queue_depth` is growing, you know workers are stuck -- even if all your HTTP metrics look healthy.

> **Architecture Thinking**: For any application, the most important metrics are the ones that measure **user outcomes**, not infrastructure health. CPU and memory matter, but they're symptoms, not root causes. "Are tasks being processed?" is the question your business cares about.

---

## Prometheus Architecture

Prometheus is an open-source monitoring system that collects metrics from targets by **pulling** (scraping) metrics at regular intervals.

### The Pull Model

Unlike systems where applications push metrics to a central server, Prometheus pulls from applications:

```
┌──────────────┐     scrape /metrics      ┌──────────────────┐
│              │ ───────────────────────── │   api-service    │
│              │                           │   :8080/metrics  │
│              │     scrape /metrics      ├──────────────────┤
│  Prometheus  │ ───────────────────────── │  worker-service  │
│   Server     │                           │   :8081/metrics  │
│              │     scrape /metrics      ├──────────────────┤
│              │ ───────────────────────── │    node-exporter │
│              │                           │   :9100/metrics  │
└──────┬───────┘                           └──────────────────┘
       │
       │ store in TSDB
       ▼
┌──────────────┐
│  Time Series │
│   Database   │
│   (local)    │
└──────────────┘
```

**Why pull, not push?**
- Prometheus controls the scrape interval (consistency)
- If a target is down, Prometheus knows immediately (the scrape fails)
- No need for applications to know where Prometheus is (decoupling)
- Easy to add new targets without restarting applications

> **Link back to Module 3**: Remember the polling pattern from Lab 3a? worker-service polls the database for new tasks. Prometheus uses the same pattern -- it polls (scrapes) applications for new metrics. The trade-off is the same: there's a delay between when something happens and when it's observed (up to one scrape interval).

### Scrape Configuration

Prometheus is configured with a YAML file that defines **scrape configs** -- which targets to scrape, how often, and what path:

```yaml
global:
  scrape_interval: 15s      # Default: scrape every 15 seconds
  evaluation_interval: 15s   # Evaluate alerting rules every 15 seconds

scrape_configs:
  - job_name: 'api-service'
    scrape_interval: 10s     # Override global for this job
    static_configs:
      - targets: ['api-service:8080']
    metrics_path: /metrics   # Default path

  - job_name: 'worker-service'
    static_configs:
      - targets: ['worker-service:8081']
```

In Kubernetes, you can also use **service discovery** to automatically find targets based on Pod annotations or Service labels -- no hardcoded IP addresses.

### TSDB (Time Series Database)

Prometheus stores metrics in its own time-series database (TSDB) on local disk. Key characteristics:

- **Time series**: Each unique combination of metric name + labels is a time series
- **Retention**: Default 15 days (configurable). Prometheus is NOT a long-term storage solution
- **Compaction**: Older data is merged into larger blocks for efficient storage
- **Write-ahead log (WAL)**: Protects against data loss on crash

> **AWS SAA Tie-in**: CloudWatch Metrics is AWS's equivalent of Prometheus. CloudWatch uses a push model (applications call PutMetricData), stores metrics for up to 15 months (at decreasing resolution), and uses its own query language. The concepts map directly: CloudWatch metric = Prometheus time series, CloudWatch namespace = Prometheus job, CloudWatch dimension = Prometheus label.

---

## PromQL -- Querying Metrics

PromQL (Prometheus Query Language) is how you extract insights from your metrics. It's a functional query language designed specifically for time-series data.

### Instant Vectors vs Range Vectors

- **Instant vector**: A set of time series, each with a single sample at a point in time. Example: `http_requests_total` returns the current value of all series matching that name.
- **Range vector**: A set of time series, each with a range of samples over time. Example: `http_requests_total[5m]` returns the last 5 minutes of data for each series. You can't graph a range vector directly -- you need a function like `rate()` to convert it to an instant vector.

### Essential Functions

**`rate()`** -- The most important PromQL function. Calculates the per-second rate of increase of a counter over a time window:

```promql
rate(http_requests_total[5m])
```

This says: "Over the last 5 minutes, how many requests per second were being served?" The `[5m]` window smooths out spikes. A wider window = smoother graph, narrower window = more responsive but noisier.

> Why `rate()` and not just the raw counter? Because counters only go up (and reset on restart). The raw value `http_requests_total = 15234` is meaningless -- you need the *rate of change*.

**`histogram_quantile()`** -- Calculates percentiles from histogram buckets:

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

This says: "What is the 95th percentile request duration over the last 5 minutes?" The `0.95` means "the value below which 95% of observations fall."

Common percentiles:
- p50 (median): "typical" experience
- p95: "most users" experience
- p99: "almost all users" experience (including tail latency)

### Aggregation Operators

```promql
# Sum across all instances
sum(rate(http_requests_total[5m]))

# Average error rate by endpoint
sum(rate(http_requests_total{status=~"5.."}[5m])) by (path)
/
sum(rate(http_requests_total[5m])) by (path)

# Top 5 endpoints by request rate
topk(5, sum(rate(http_requests_total[5m])) by (path))
```

Key aggregation operators: `sum`, `avg`, `min`, `max`, `count`, `topk`, `bottomk`, `quantile`.

The `by` clause groups results. `without` excludes labels from grouping. Think of them like SQL's `GROUP BY`.

### Label Matching

```promql
# Exact match
http_requests_total{method="GET"}

# Regex match (all 5xx status codes)
http_requests_total{status=~"5.."}

# Negative match
http_requests_total{path!="/health"}

# Negative regex
http_requests_total{status!~"2.."}
```

### Recording Rules

If you have complex PromQL queries that you use frequently (e.g., in dashboards AND alerts), you can pre-compute them as **recording rules**:

```yaml
groups:
  - name: flowforge_recording_rules
    rules:
      - record: flowforge:api_request_rate:5m
        expr: sum(rate(http_requests_total{job="api-service"}[5m]))
      - record: flowforge:api_error_rate:5m
        expr: |
          sum(rate(http_requests_total{job="api-service",status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="api-service"}[5m]))
```

Recording rules create new time series that are faster to query than computing the expression every time.

> **Architecture Thinking**: PromQL is powerful but can be confusing. The key mental model is: everything starts with a metric name, you apply functions to transform it, and you aggregate across labels. Think of it as a pipeline: `select metric → apply function → aggregate → filter`.

---

## Grafana Dashboards

Grafana is the visualization layer that turns PromQL queries into beautiful, interactive dashboards.

### Panel Types

| Panel | Best For | Example Use |
|-------|----------|-------------|
| **Time series (graph)** | Trends over time | Request rate, latency over the last 6 hours |
| **Stat** | Single important number | Current error rate: 0.3% |
| **Gauge** | Values with known ranges | CPU usage: 67/100% |
| **Table** | Multiple rows of data | Top 10 slowest endpoints with latency values |
| **Bar chart** | Comparing categories | Request count by endpoint |
| **Heatmap** | Distribution over time | Latency distribution showing where most requests fall |

### Dashboard Variables

Variables make dashboards dynamic. Instead of hardcoding `api-service` in every panel, you create a variable `$service` that lets you switch between services in a dropdown:

```promql
rate(http_requests_total{job="$service"}[5m])
```

This single dashboard then works for api-service, worker-service, or any new service you add.

### Annotations

Annotations mark events on dashboards -- deployments, incidents, config changes. When you see a spike in error rate at 14:32, an annotation showing "v2.3.1 deployed at 14:30" immediately points to the cause.

> **Link back to Module 7**: In CI/CD you built deployment pipelines. Each deployment could automatically add a Grafana annotation, creating a visual link between "code changed" and "metrics changed."

> **AWS SAA Tie-in**: CloudWatch Dashboards serve the same purpose as Grafana but with tighter AWS integration. Many teams use both: CloudWatch for AWS resource metrics (EC2, RDS, ALB) and Grafana for application-level metrics. Grafana can actually query CloudWatch as a data source.

---

## Alerting

Dashboards are great for investigation, but you can't stare at dashboards 24/7. Alerting tells you when something needs attention.

### Prometheus Alerting Rules

Alert rules are PromQL expressions with thresholds and durations:

```yaml
groups:
  - name: flowforge_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{job="api-service",status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="api-service"}[5m]))
          > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on api-service"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
```

Key elements:
- **`expr`**: The PromQL expression. When it returns true, the alert is pending
- **`for`**: How long the condition must be true before firing. Prevents alerts from noise/spikes
- **`labels`**: Used for routing (severity, team, service)
- **`annotations`**: Human-readable description with template variables

### Alertmanager

Prometheus evaluates alert rules but doesn't send notifications. That's Alertmanager's job:

```
Prometheus (evaluates rules) → Alertmanager (routes & sends) → Slack/PagerDuty/Email/Webhook
```

Alertmanager handles:
- **Grouping**: Multiple related alerts sent as one notification
- **Inhibition**: If the cluster is down, suppress individual service alerts
- **Silencing**: Temporarily mute alerts during maintenance
- **Routing**: Critical alerts → PagerDuty, warnings → Slack, info → email

### Alert Design -- Actionable, Not Noisy

Bad alerts cause **alert fatigue** -- when alerts fire so often that engineers ignore them. Every alert should be:

1. **Actionable**: Someone needs to DO something. If no action is needed, it's not an alert
2. **Urgent**: It needs attention NOW (or soon). If it can wait until Monday, it's a report
3. **Meaningful**: It represents real user impact or imminent risk
4. **Not noisy**: Alert on symptoms (high error rate), not causes (CPU at 80%). CPU might be high because you're doing useful work

> **Architecture Thinking**: A good rule of thumb: if an alert fires and the on-call engineer says "so what?" or "this always happens," the alert is broken. Every alert should have a clear runbook answer to "what do I do when this fires?"

> **Link back to Module 1**: Remember systemd's restart policies from Lab 2b? Those are the simplest form of "alerting and auto-remediation" -- the system detects a failure (process exited) and takes action (restart). Prometheus alerting is the same concept at a higher level: detect a condition and notify a human (or trigger automation).

---

## SLOs, SLIs, and SLAs

### Definitions

| Term | What It Is | Example |
|------|-----------|---------|
| **SLI** (Service Level Indicator) | A measurable metric that reflects service quality | "Percentage of requests completing in < 500ms" |
| **SLO** (Service Level Objective) | A target value for an SLI | "99.9% of requests complete in < 500ms" |
| **SLA** (Service Level Agreement) | A contract with consequences if the SLO is broken | "If availability drops below 99.9%, customer gets 10% credit" |

The relationship: SLIs measure, SLOs set targets, SLAs set consequences.

### Error Budgets

If your SLO is 99.9% availability, you have a 0.1% **error budget** -- you're allowed to be down for 0.1% of the time:

| Period | 99.9% Error Budget |
|--------|-------------------|
| Per month (30 days) | 43.2 minutes |
| Per quarter (90 days) | 2.16 hours |
| Per year (365 days) | 8.76 hours |

Error budgets give you a framework for making decisions:
- **Budget remaining**: Deploy freely, experiment, take risks
- **Budget almost consumed**: Slow down, focus on reliability
- **Budget exhausted**: Feature freeze, all engineering effort on reliability

### Burn Rate

Burn rate measures how quickly you're consuming your error budget. A burn rate of 1x means you'll exhaust your budget exactly at the end of the period. A burn rate of 10x means you'll burn through your monthly budget in 3 days.

Burn rate alerts are better than threshold alerts for SLOs because they account for the time dimension:
- "Error rate is 1%" is a threshold (might or might not matter)
- "At the current error rate, we'll exhaust our monthly error budget in 2 hours" is a burn rate alert (clearly urgent)

### SLO Dashboard

A good SLO dashboard shows:
1. Current SLI value (e.g., 99.95% availability)
2. SLO target (99.9%)
3. Error budget remaining (63% of budget left)
4. Burn rate (0.8x -- consuming budget slower than allowed)
5. Time remaining in the window (18 days left in the month)

> **Architecture Thinking**: SLOs are a **communication tool** between engineering and business. The business says "we need 99.9% availability," engineering translates that to PromQL expressions and error budgets. When the budget runs low, both sides agree on the response. Without SLOs, reliability discussions become arguments about feelings rather than data.

> **AWS SAA Tie-in**: AWS services publish their own SLAs (e.g., EC2 99.99%, S3 99.9% for standard). Understanding SLOs helps you design systems that meet your targets even when individual AWS services experience their allowed downtime. If EC2 has a 99.99% SLA and your app needs 99.9%, you have margin -- but if you depend on three 99.9% services serially, your combined availability is 99.7%.

---

## Structured Logging with Loki

### Log Aggregation

When FlowForge runs multiple replicas across Kubernetes nodes, logs are scattered. You need a centralized log aggregation system.

**Grafana Loki** is a log aggregation system designed to work with Grafana:

```
┌─────────────────┐     stdout/stderr     ┌──────────────┐
│  api-service    │ ──────────────────── │              │
│  (Pod)          │                       │              │
├─────────────────┤     stdout/stderr     │   Promtail   │    push logs    ┌──────────┐
│  worker-service │ ──────────────────── │   (DaemonSet)│ ──────────────── │  Loki    │
│  (Pod)          │                       │              │                  │  (Server)│
├─────────────────┤     stdout/stderr     │              │                  └────┬─────┘
│  postgres       │ ──────────────────── │              │                       │
│  (Pod)          │                       └──────────────┘                       │ query
└─────────────────┘                                                              ▼
                                                                          ┌──────────┐
                                                                          │ Grafana  │
                                                                          │ (UI)     │
                                                                          └──────────┘
```

Key differences from traditional log systems (ELK/Elasticsearch):
- **Loki does NOT index log content** -- only labels (like Prometheus labels)
- This makes Loki much cheaper to run and faster to ingest
- Trade-off: full-text search is slower, but label-based filtering is fast

### LogQL

LogQL is Loki's query language, inspired by PromQL:

```logql
# All logs from api-service
{app="api-service"}

# Error logs from api-service
{app="api-service"} |= "error"

# Parse JSON logs and filter by status code
{app="api-service"} | json | status >= 500

# Count error logs per minute
count_over_time({app="api-service"} |= "error" [1m])
```

### Labels

Loki uses labels to index and filter logs. Good labels in Kubernetes:
- `namespace`, `pod`, `container`, `app` -- set automatically by Promtail
- `level` (info, warn, error) -- extracted from structured logs

Bad labels (too high cardinality):
- `request_id`, `user_id`, `trace_id` -- use log content filtering instead

### Correlation with Metrics

The real power of Loki + Prometheus + Grafana is **correlation**:

1. You see an error rate spike on your metrics dashboard
2. You click the time range on the dashboard
3. Grafana shows you the corresponding log entries from that same time period
4. The structured log entries contain request IDs, error messages, and stack traces
5. You know exactly what caused the spike

This is why structured JSON logging (from Module 3) matters: it enables machine-readable log queries.

> **Link back to Module 3**: The structured logging with `log/slog` from Lab 4c pays off here. JSON logs with consistent fields (`level`, `msg`, `request_id`, `service`, `ts`) are directly queryable with LogQL. If you had used `fmt.Println("error happened")`, you'd be doing regex parsing instead.

> **Link back to Module 8**: Kubernetes captures stdout/stderr from every container. In Lab 02 you used `kubectl logs` to see individual Pod output. Loki does the same thing but at scale -- aggregating logs from every Pod in the cluster with label-based filtering.

---

## Failure Simulation

### Why Break Things on Purpose?

You've built monitoring, dashboards, alerts, and SLOs. But do they actually work? The only way to know is to **test them** -- by deliberately causing failures and verifying your monitoring detects them.

This is the core principle of **chaos engineering**: controlled experiments to build confidence in your system's ability to withstand turbulent conditions.

### Controlled Experiments

A failure simulation follows the scientific method:

1. **Hypothesis**: "If a worker Pod crashes, the queue depth metric will increase and the alert will fire within 5 minutes"
2. **Experiment**: Kill a worker Pod with `kubectl delete pod`
3. **Observe**: Watch dashboards and alert channels
4. **Verify**: Did the queue depth increase? Did the alert fire? How long did it take?
5. **Learn**: What worked? What didn't? What needs improvement?

### Types of Failures to Simulate

| Failure | What Breaks | What You Should See |
|---------|-------------|-------------------|
| Kill a worker Pod | Task processing stops temporarily | Queue depth increases, processing rate drops, K8s restarts the Pod |
| Exhaust DB connections | Both services can't query the database | Error rate spikes on both services, connection pool metrics saturate |
| Introduce artificial latency | API responses slow down | Latency percentiles increase, SLO burn rate accelerates |
| High CPU load | Everything slows down | Resource metrics spike, latency increases, potential Pod eviction |
| Network partition | Service-to-service communication fails | Connection errors in logs, error rate spikes, partial availability |

> **Architecture Thinking**: Chaos engineering is NOT randomly breaking things in production. It's a disciplined practice: form a hypothesis, design a minimal experiment, have a rollback plan, start in non-production environments, and gradually increase scope. The goal is to find weaknesses before your users do.

> **Link forward to Module 10**: Security incidents are another type of failure. In Module 10 you'll write incident response runbooks. The monitoring and alerting you build here becomes your early warning system for security events too -- unexpected traffic spikes, unusual error patterns, and unauthorized access attempts all show up in metrics and logs.

> **Link back to Module 8**: In Lab 06 you debugged broken Kubernetes deployments using `kubectl describe`, `kubectl logs`, and events. In this module's failure simulation, you'll diagnose the SAME types of issues -- but using your monitoring dashboards FIRST, before reaching for kubectl. That's the real test: can your monitoring tell you what's wrong faster than manual investigation?

---

## Summary: The Monitoring Stack

```
┌─────────────────────────────────────────────────────────────┐
│                        GRAFANA                              │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │  Dashboards  │  │    Alerts     │  │   Log Explorer   │ │
│  │  (PromQL)    │  │  (via Prom)   │  │   (LogQL)        │ │
│  └──────┬───────┘  └───────┬───────┘  └────────┬─────────┘ │
│         │                  │                    │           │
└─────────┼──────────────────┼────────────────────┼───────────┘
          │                  │                    │
          ▼                  ▼                    ▼
    ┌───────────┐     ┌──────────────┐     ┌───────────┐
    │Prometheus │     │Alertmanager  │     │   Loki    │
    │  (TSDB)   │     │ (routing)    │     │  (logs)   │
    └─────┬─────┘     └──────────────┘     └─────┬─────┘
          │ scrape                               │ push
          ▼                                      ▼
    ┌───────────┐                          ┌───────────┐
    │ /metrics  │                          │ Promtail  │
    │ endpoints │                          │ (DaemonSet)│
    └───────────┘                          └───────────┘
```

In this module you'll build this entire stack from scratch:
- **Lab 01**: Instrument FlowForge Go services with prometheus/client_golang
- **Lab 02**: Deploy Prometheus and write PromQL queries
- **Lab 03**: Deploy Grafana and create dashboards and alerting rules
- **Lab 04**: Define SLOs, create SLO dashboards, and deploy Loki for log aggregation
- **Lab 05**: Break things and diagnose from monitoring alone

---

## Further Reading

- [Prometheus documentation](https://prometheus.io/docs/introduction/overview/)
- [PromQL reference](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana documentation](https://grafana.com/docs/grafana/latest/)
- [Grafana Loki documentation](https://grafana.com/docs/loki/latest/)
- [prometheus/client_golang](https://github.com/prometheus/client_golang)
- [Google SRE Book -- Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE Book -- Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Alertmanager documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [AWS CloudWatch documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/)
- [AWS X-Ray documentation](https://docs.aws.amazon.com/xray/latest/devguide/)
