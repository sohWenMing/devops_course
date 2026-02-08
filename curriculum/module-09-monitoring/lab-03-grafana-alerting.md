# Lab 03: Grafana Dashboards and Alerting

> **Module**: 9 -- Monitoring and Observability  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Lab 02 completed (Prometheus deployed and scraping FlowForge, PromQL queries working). Read the [Grafana Dashboards](#) and [Alerting](#) sections of the Module 9 README.

---

## Overview

You can query metrics in the Prometheus UI, but that's a developer tool, not an operations dashboard. In this lab you'll deploy Grafana to create a visual dashboard for FlowForge, then set up Prometheus alerting rules so you're notified when things go wrong.

---

## Exercise 3a: Deploy Grafana and Create a FlowForge Dashboard

### Objectives

- Deploy Grafana to your Kind cluster using Kubernetes manifests
- Connect Grafana to Prometheus as a data source
- Build a FlowForge dashboard with 4 panels: request rate, error rate, latency percentiles, and queue depth
- Choose appropriate visualization types for each metric

### What You'll Do

**Part 1: Deploy Grafana to Kubernetes**

1. Create Kubernetes manifests for Grafana in the `monitoring` namespace:
   - A Deployment using the official `grafana/grafana` image
   - A Service to expose Grafana (NodePort or port-forward to access the UI)
   - A PersistentVolumeClaim for Grafana's data (so dashboards survive Pod restarts)
   - Think about: what's the default admin password? How would you change it?

2. Apply the manifests and wait for Grafana to be Running.

3. Access the Grafana UI (default port 3000). Log in with the default credentials.

**Part 2: Configure Data Source**

4. Add Prometheus as a data source in Grafana:
   - Navigate to Configuration → Data Sources → Add data source → Prometheus
   - Set the URL to the Prometheus Service DNS name (e.g., `http://prometheus.monitoring.svc.cluster.local:9090`)
   - Click "Save & Test" to verify the connection

5. Think about: why use the Kubernetes DNS name instead of an IP address? What would happen if the Prometheus Pod restarted and got a new IP?

**Part 3: Create the FlowForge Dashboard**

6. Create a new dashboard called "FlowForge Overview". You'll build 4 panels:

**Panel 1: Request Rate**
7. Create a time series (graph) panel showing the request rate over time.
   - Write a PromQL query that shows total requests per second
   - Add a second query that shows the rate broken down by status code (group 2xx, 4xx, 5xx)
   - Choose appropriate colors (green for 2xx, yellow for 4xx, red for 5xx)
   - Set a meaningful title and Y-axis label (requests/second)
   - Think about the time range -- what window gives a useful view?

**Panel 2: Error Rate**
8. Create a stat panel showing the current error rate as a percentage.
   - Use your error percentage PromQL query from Lab 02
   - Configure thresholds: green (< 1%), yellow (1-5%), red (> 5%)
   - Think about: why a stat panel instead of a graph for error rate? When would you want to see the trend vs the current value?

**Panel 3: Latency p50 / p95 / p99**
9. Create a time series (graph) panel showing latency percentiles.
   - Add three queries: p50, p95, and p99
   - Use different line styles or colors for each percentile
   - Set the Y-axis unit to "seconds" (Grafana will auto-format to ms if values are small)
   - Think about: why show three percentiles instead of just one? What does the gap between p50 and p99 tell you?

**Panel 4: Active Tasks in Queue**
10. Create a time series (graph) panel showing the task queue depth.
    - Use the `flowforge_queue_depth` gauge metric
    - Add a threshold line at 100 (the level where you'd want to investigate)
    - Think about: what does a steadily increasing line mean? What about a sawtooth pattern?

**Part 4: Dashboard Polish**

11. Arrange the panels in a logical layout:
    - Top row: request rate (wide) and error rate (narrow stat)
    - Bottom row: latency percentiles (wide) and queue depth (medium)

12. Add a dashboard variable for time range refresh and auto-refresh interval (e.g., every 30s).

13. Consider adding a dashboard variable for `$service` so you can switch between api-service and worker-service metrics.

14. Save the dashboard. Export it as JSON (Dashboard Settings → JSON Model → Copy). This JSON export is your dashboard-as-code -- you can version control it and restore it later.

### Expected Outcome

- Grafana running in the `monitoring` namespace, connected to Prometheus
- A "FlowForge Overview" dashboard with 4 panels showing real-time metrics
- Appropriate visualization types: time series for trends, stat for current values
- Dashboard exported as JSON for version control
- All panels showing live data from your running FlowForge services

### Checkpoint Questions

- [ ] Why did you choose a time series panel for request rate but a stat panel for error rate? Could you justify the opposite choices?
- [ ] What's the difference between Grafana's auto-refresh and the Prometheus scrape interval? Which determines how "real-time" your dashboard is?
- [ ] If you had to create a dashboard for worker-service specifically, what panels would you include? How would they differ from the API dashboard?
- [ ] What does it mean when p99 latency is 10x the p50 latency? Is that a problem?
- [ ] How would you share this dashboard with a team? What's the role of the JSON export?

---

## Exercise 3b: Prometheus Alerting Rules

### Objectives

- Create Prometheus alerting rules for FlowForge
- Understand alert evaluation, pending state, and firing state
- Configure alert routing to a webhook
- Design alerts that are actionable, not noisy

### What You'll Do

**Part 1: Create Alerting Rules**

1. Create a Prometheus alerting rules file. This will be mounted via ConfigMap alongside your `prometheus.yml`. You need to:
   - Define the rules file in a YAML format
   - Reference it from your `prometheus.yml` under `rule_files`
   - Update the Prometheus ConfigMap and restart Prometheus

2. Create the following alerting rules:

**Alert 1: High Error Rate**
3. Write an alerting rule called `HighErrorRate`:
   - Condition: error rate exceeds 5% of total requests
   - Duration (`for`): 5 minutes (the condition must be true for 5 minutes before firing)
   - Severity label: `critical`
   - Annotations: include a human-readable summary and description with the current error rate value
   - Think about: why 5 minutes and not immediately? What would happen with a 0-second `for` duration?

**Alert 2: High Latency**
4. Write an alerting rule called `HighLatency`:
   - Condition: p99 latency exceeds 2 seconds
   - Duration: 10 minutes
   - Severity label: `warning`
   - Annotations: include the current p99 value
   - Think about: why p99 and not p50? Why is this a warning and not critical?

**Alert 3: Worker Queue Growing**
5. Write an alerting rule called `WorkerQueueGrowing`:
   - Condition: queue depth exceeds 100 tasks
   - Duration: 15 minutes
   - Severity label: `warning`
   - Annotations: include the current queue depth
   - Think about: why 15 minutes? A brief spike to 101 and back to 0 isn't concerning. Sustained growth is.

**Part 2: Deploy and Verify Rules**

6. Update the Prometheus ConfigMap with both the rules file and the reference in `prometheus.yml`:
   ```yaml
   rule_files:
     - /etc/prometheus/alerts.yml
   ```

7. Restart Prometheus (delete the Pod and let the Deployment recreate it, or use Prometheus's reload endpoint if configured).

8. In the Prometheus UI, navigate to **Status → Rules**. Verify all three alerting rules appear and are in the "inactive" state (meaning the condition is not currently true).

9. Navigate to **Alerts** in the Prometheus UI. You should see your three rules listed.

**Part 3: Test Alert Firing**

10. Trigger the `HighErrorRate` alert. You need to generate enough 5xx errors to exceed 5% of total requests for 5+ minutes:
    - Introduce a bug in api-service that returns 500 for some requests (or use a test endpoint)
    - Alternatively, if you've deployed to Kind, you could break the database connection to cause real errors

11. Watch the alert transition through states in the Prometheus UI:
    - **Inactive** → **Pending** (condition is true but `for` duration hasn't elapsed) → **Firing** (condition has been true for the full `for` duration)

12. How long does the transition take? Does it match your expectations based on the `for` duration?

**Part 4: Alertmanager Setup (Basic)**

13. Deploy Alertmanager to your Kind cluster:
    - Create a ConfigMap with an Alertmanager configuration
    - Create a Deployment using the `prom/alertmanager` image
    - Create a Service to expose it
    - Configure Prometheus to send alerts to Alertmanager (add `alerting` section to `prometheus.yml`)

14. Configure a basic webhook receiver in Alertmanager. For testing, you can:
    - Use a simple HTTP server that prints received alerts (e.g., a Python one-liner)
    - Use an online webhook testing service
    - Or simply watch the Alertmanager UI to see alerts arriving

15. Configure routing in Alertmanager:
    - All `critical` alerts go to one receiver
    - All `warning` alerts go to another receiver (or the same one for now)
    - Think about: in a real production environment, how would routing differ? (PagerDuty for critical, Slack for warning?)

16. Verify end-to-end: trigger an alert → see it in Prometheus Alerts → see it arrive in Alertmanager → see the webhook receive the notification.

### Expected Outcome

- Three alerting rules configured in Prometheus: HighErrorRate, HighLatency, WorkerQueueGrowing
- Rules visible in Prometheus UI under Status → Rules and Alerts
- At least one alert successfully triggered and transitioned through inactive → pending → firing
- Alertmanager deployed and receiving alerts from Prometheus
- Basic webhook receiver showing alert notifications

### Checkpoint Questions

- [ ] Write a new alerting rule from scratch: "Alert when API availability drops below 99.9% over 30 minutes." What PromQL expression would you use?
- [ ] Explain what makes a good alert. What's the difference between alerting on symptoms vs causes?
- [ ] What happens if Prometheus itself goes down? Who alerts on the alerter? (This is a real production concern)
- [ ] Why does the `for` duration matter? Give an example of an alert that should fire immediately vs one that should wait 15 minutes.
- [ ] In a real production setup with 20 microservices, how would you organize your alerting rules? One file per service? One big file?
