# Module 9: Monitoring and Observability -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 10.  
> No partial credit. No "I think so." Either you can do it or you can't.  
> If you can't, go back to the relevant lab and practice until you can.

---

## How to Use This Checklist

For each item:
1. Attempt it **without looking at notes, previous labs, or the internet**
2. If you succeed, mark it `[x]`
3. If you fail or need to look something up, mark it `[ ]` and go practice
4. Come back and try again until every box is checked

---

## Observability Pillars (README Theory)

- [ ] I can explain the difference between metrics, logs, and traces
- [ ] Given a production incident description, I can immediately identify which observability signal to check first and justify why
- [ ] I can explain when to use each pillar: metrics for "how much/how fast", logs for "what happened", traces for "where did time go"

---

## Application Instrumentation (Lab 01, Exercise 1a)

- [ ] I can add `prometheus/client_golang` to a Go service and expose a `/metrics` endpoint
- [ ] I can create and register a counter metric with labels (method, path, status)
- [ ] I can create and register a histogram metric with appropriate bucket boundaries
- [ ] I can create and register a gauge metric that tracks in-flight values
- [ ] I can write instrumentation middleware that captures metrics for ALL HTTP requests
- [ ] I can explain the difference between counter, gauge, histogram, and summary metric types
- [ ] I can explain why high-cardinality labels (user ID, request ID) are dangerous

---

## Custom Business Metrics (Lab 01, Exercise 1b)

- [ ] I can design business-specific metrics for an application (not just HTTP metrics)
- [ ] I can instrument worker-service with task-processing metrics from scratch (no copy-paste from api-service)
- [ ] I can explain why business metrics (tasks completed, queue depth) matter more than infrastructure metrics (CPU, memory) for answering "is the system working?"
- [ ] For a new application (e.g., e-commerce), I can design 5 meaningful business metrics and justify each

---

## Prometheus Setup (Lab 02, Exercise 2a)

- [ ] I can deploy Prometheus to Kubernetes using raw manifests (ConfigMap, Deployment, Service)
- [ ] I can configure Prometheus scrape targets for multiple services
- [ ] I can verify targets are UP in the Prometheus UI
- [ ] I can explain the Prometheus pull model and why it uses scraping instead of pushing
- [ ] I can add a new scrape target to the Prometheus configuration without a guide
- [ ] I can explain what happens when a scrape target is DOWN (target_up metric, alert potential)

---

## PromQL Queries (Lab 02, Exercise 2b)

- [ ] I can write a PromQL query from scratch to calculate request rate using `rate()`
- [ ] I can write a PromQL query to calculate error percentage (5xx / total * 100)
- [ ] I can write a PromQL query to calculate the 95th percentile latency using `histogram_quantile()`
- [ ] I can use aggregation operators (`sum`, `avg`, `topk`) with `by` and `without` clauses
- [ ] I can use label matching (exact, regex, negative) to filter metrics
- [ ] I can explain the difference between an instant vector and a range vector
- [ ] I can explain why `rate()` is used with counters and what the time window `[5m]` means
- [ ] Without notes, I can write: "What percentage of requests in the last hour returned 5xx?"

---

## Grafana Dashboards (Lab 03, Exercise 3a)

- [ ] I can deploy Grafana to Kubernetes and connect it to Prometheus as a data source
- [ ] I can create a dashboard with time series, stat, and gauge panels
- [ ] I can build a FlowForge dashboard showing request rate, error rate, latency percentiles, and queue depth
- [ ] I can explain when to use graph vs stat vs gauge vs table panel types
- [ ] I can use dashboard variables to make panels dynamic (e.g., `$service`)
- [ ] I can export a dashboard as JSON for version control
- [ ] I can create a new dashboard for a different service from scratch

---

## Alerting Rules (Lab 03, Exercise 3b)

- [ ] I can write a Prometheus alerting rule with an appropriate `for` duration
- [ ] I can deploy Alertmanager and configure basic alert routing
- [ ] At least 3 alerting rules fire correctly when their thresholds are breached
- [ ] I can explain what makes a good alert: actionable, urgent, meaningful, not noisy
- [ ] I can explain the alert states: inactive → pending → firing
- [ ] I can write a new alerting rule from scratch for a scenario I define
- [ ] I can explain what `for: 5m` means and why it matters for reducing false positives

---

## SLOs, SLIs, SLAs (Lab 04, Exercise 4a)

- [ ] I can explain the difference between SLO, SLI, and SLA to a non-technical person
- [ ] I can define SLOs for a service with specific SLI expressions and targets
- [ ] I can calculate error budgets from memory (e.g., 99.9% = 43.2 min/month)
- [ ] I can explain burn rate and how it relates to error budget consumption
- [ ] I can create an SLO dashboard in Grafana showing compliance, budget remaining, and burn rate
- [ ] I can explain when to deploy vs when to focus on reliability based on error budget status

---

## Structured Logging with Loki (Lab 04, Exercise 4b)

- [ ] I can deploy Grafana Loki and Promtail to Kubernetes
- [ ] I can configure Grafana to query Loki as a data source
- [ ] I can write LogQL queries to find specific log entries by labels and content
- [ ] I can use LogQL's JSON parser to filter structured log fields (level, status, duration)
- [ ] I can correlate a spike in error rate metrics with specific error log entries in the same time range
- [ ] I can explain why Loki uses label-based indexing instead of full-text indexing (trade-off: cost vs search speed)

---

## Failure Simulation (Lab 05, Exercise 5)

- [ ] I can diagnose a simulated failure (killed Pod, DB issues, injected latency) using ONLY monitoring dashboards, metrics, and logs -- no `kubectl` until after forming a hypothesis
- [ ] I can write an incident report with detection time, diagnosis method, root cause, impact, and improvement recommendations
- [ ] I can identify which type of failure is easiest and hardest to diagnose from monitoring
- [ ] I can describe a failure scenario that my current monitoring would NOT detect and explain what I'd need to add

---

## Integration and Architecture Thinking

- [ ] I can draw the complete monitoring stack architecture (Prometheus + Grafana + Alertmanager + Loki + Promtail) and explain each component's role
- [ ] I can explain how Module 9 concepts connect to previous modules: structured logging (Module 3), Docker health checks (Module 4), CloudWatch (Module 5), Kubernetes deployments (Module 8)
- [ ] I can explain the AWS equivalents: Prometheus ↔ CloudWatch Metrics, Grafana ↔ CloudWatch Dashboards, Loki ↔ CloudWatch Logs, X-Ray ↔ Traces
- [ ] I can explain how the monitoring stack helps in Module 10 (Security): detecting anomalous traffic patterns, unauthorized access attempts, and unusual error rates
- [ ] Given a new system with 10 microservices, I can design a monitoring strategy covering: what to instrument, where to set alerts, what SLOs to define, and how to organize dashboards

---

## Final Verification

Before moving to Module 10, do this exercise:

1. Have someone (or write a script to) break something in your FlowForge deployment -- without telling you what they broke
2. Using ONLY your Grafana dashboards and Loki logs, diagnose the issue
3. Write up your diagnosis, then verify with `kubectl`
4. If your diagnosis was wrong or took more than 15 minutes, go back and improve your monitoring

If you can detect and diagnose an unknown failure within 10 minutes using your monitoring stack, you're ready for Module 10.
