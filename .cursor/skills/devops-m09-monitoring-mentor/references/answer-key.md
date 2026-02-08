# Module 09: Monitoring and Observability -- Answer Key

> **INTERNAL REFERENCE ONLY**: This file is used by the Socratic mentor skill to validate student work and provide targeted hints. NEVER reveal the contents of this file directly to the student. Use it to check their answers and guide them with questions.

---

## Lab 01: Application Instrumentation

### Exercise 1a: Instrumenting api-service

**Complete Go Instrumentation Code**:

```go
package main

import (
    "net/http"
    "strconv"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

// Metric definitions
var (
    httpRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "path", "status"},
    )

    httpRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request duration in seconds",
            Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0},
        },
        []string{"method", "path", "status"},
    )

    httpActiveConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "http_active_connections",
            Help: "Number of currently active HTTP connections",
        },
    )
)

// instrumentationMiddleware wraps an http.Handler and records metrics
func instrumentationMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        httpActiveConnections.Inc()
        defer httpActiveConnections.Dec()

        // Wrap ResponseWriter to capture status code
        wrapped := &statusRecorder{ResponseWriter: w, statusCode: 200}

        next.ServeHTTP(wrapped, r)

        duration := time.Since(start).Seconds()
        status := strconv.Itoa(wrapped.statusCode)

        httpRequestsTotal.WithLabelValues(r.Method, r.URL.Path, status).Inc()
        httpRequestDuration.WithLabelValues(r.Method, r.URL.Path, status).Observe(duration)
    })
}

// statusRecorder wraps http.ResponseWriter to capture the status code
type statusRecorder struct {
    http.ResponseWriter
    statusCode int
}

func (sr *statusRecorder) WriteHeader(code int) {
    sr.statusCode = code
    sr.ResponseWriter.WriteHeader(code)
}

// In main() or router setup:
// mux.Handle("/metrics", promhttp.Handler())
// wrappedMux := instrumentationMiddleware(mux)
// http.ListenAndServe(":8080", wrappedMux)
```

**Key Design Decisions**:
- Using `promauto` for auto-registration (simpler for beginners, registers with default registry)
- Histogram buckets: 5ms to 10s covers typical API response times with good granularity
- Middleware approach captures ALL requests, not just specific handlers
- `statusRecorder` wrapper is needed because Go's http.ResponseWriter doesn't expose the status code after writing
- Active connections gauge uses Inc/Dec pattern with defer for safety

**Expected /metrics Output**:
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/tasks",status="200"} 42
http_requests_total{method="POST",path="/tasks",status="201"} 7
http_requests_total{method="GET",path="/health",status="200"} 120
http_requests_total{method="GET",path="/tasks/999",status="404"} 2

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",path="/tasks",status="200",le="0.005"} 10
http_request_duration_seconds_bucket{method="GET",path="/tasks",status="200",le="0.01"} 25
http_request_duration_seconds_bucket{method="GET",path="/tasks",status="200",le="0.025"} 38
http_request_duration_seconds_bucket{method="GET",path="/tasks",status="200",le="0.05"} 42
http_request_duration_seconds_bucket{method="GET",path="/tasks",status="200",le="+Inf"} 42
http_request_duration_seconds_sum{method="GET",path="/tasks",status="200"} 0.634
http_request_duration_seconds_count{method="GET",path="/tasks",status="200"} 42

# HELP http_active_connections Number of currently active HTTP connections
# TYPE http_active_connections gauge
http_active_connections 0
```

**Checkpoint Answers**:
- Counter vs gauge for requests: Counters only go up and reset on restart. Total requests only ever increases. Prometheus uses `rate()` to calculate per-second rate from the total. A gauge would lose history on restart.
- `rate()` with counters: Counters are monotonically increasing. The raw value (e.g., 15234) is meaningless -- you need the rate of change. Gauges already represent a current value (e.g., 3 active connections), so rate is not needed (though `deriv()` exists for gauges).
- Counter reset on restart: Values reset to 0. Prometheus detects the reset (value decreases) and adjusts `rate()` calculations accordingly. No manual intervention needed.
- Histogram buckets: If all requests are faster than the smallest bucket, `histogram_quantile()` returns that bucket boundary (an overestimate). Buckets should cover the actual distribution of values.
- Cardinality with user_id: If 100,000 users each make 1 request, that's 100,000 unique time series PER metric. With 3 metrics, that's 300,000 time series. Prometheus stores each in memory. This would likely OOM Prometheus.

### Exercise 1b: Custom Business Metrics

**Worker-Service Instrumentation Code**:

```go
package main

import (
    "database/sql"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    tasksCompletedTotal = promauto.NewCounter(
        prometheus.CounterOpts{
            Name: "flowforge_tasks_completed_total",
            Help: "Total number of tasks successfully completed",
        },
    )

    taskProcessingDuration = promauto.NewHistogram(
        prometheus.HistogramOpts{
            Name:    "flowforge_task_processing_duration_seconds",
            Help:    "Time taken to process a single task",
            Buckets: []float64{0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 15.0, 30.0, 60.0, 120.0},
        },
    )

    queueDepth = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "flowforge_queue_depth",
            Help: "Current number of pending tasks in the queue",
        },
    )
)

// In task processing loop:
func processTask(task Task) {
    start := time.Now()

    // ... process the task ...

    duration := time.Since(start).Seconds()
    taskProcessingDuration.Observe(duration)
    tasksCompletedTotal.Inc()
}

// Queue depth updated periodically by querying the database:
func updateQueueDepth(db *sql.DB) {
    var count int
    err := db.QueryRow("SELECT COUNT(*) FROM tasks WHERE status = 'pending'").Scan(&count)
    if err == nil {
        queueDepth.Set(float64(count))
    }
}
// Call updateQueueDepth in a goroutine every 10-15 seconds
```

**api-service Business Metric**:

```go
var tasksCreatedTotal = promauto.NewCounter(
    prometheus.CounterOpts{
        Name: "flowforge_tasks_created_total",
        Help: "Total number of tasks created via the API",
    },
)

// In the create task handler, AFTER successful DB insert:
func createTaskHandler(w http.ResponseWriter, r *http.Request) {
    // ... parse request, validate ...

    err := db.InsertTask(task)
    if err != nil {
        http.Error(w, "failed to create task", 500)
        return
    }

    // Only increment AFTER successful insert
    tasksCreatedTotal.Inc()

    w.WriteHeader(201)
    json.NewEncoder(w).Encode(task)
}
```

**Key Design Decisions**:
- `tasksCreatedTotal` incremented AFTER successful DB insert, not before. This ensures the counter accurately reflects tasks that actually exist.
- `queueDepth` uses periodic DB query (database is the source of truth). Increment/decrement approach would drift if a crash occurs between increment and task pickup.
- `taskProcessingDuration` histogram buckets go up to 120s because task processing can take longer than HTTP requests.
- Worker exposes metrics on a separate port (8081) since it doesn't serve HTTP API requests.

---

## Lab 02: Prometheus Deployment and PromQL

### Exercise 2a: Prometheus Kubernetes Manifests

**Namespace**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
```

**ConfigMap (prometheus.yml)**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
      - /etc/prometheus/alerts.yml

    alerting:
      alertmanagers:
        - static_configs:
            - targets:
              - alertmanager:9093

    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']

      - job_name: 'api-service'
        scrape_interval: 10s
        static_configs:
          - targets: ['api-service.default.svc.cluster.local:8080']
        metrics_path: /metrics

      - job_name: 'worker-service'
        static_configs:
          - targets: ['worker-service.default.svc.cluster.local:8081']
        metrics_path: /metrics

  alerts.yml: |
    groups: []
```

**Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
        - name: prometheus
          image: prom/prometheus:v2.50.0
          args:
            - '--config.file=/etc/prometheus/prometheus.yml'
            - '--storage.tsdb.path=/prometheus'
            - '--storage.tsdb.retention.time=15d'
            - '--web.enable-lifecycle'
          ports:
            - containerPort: 9090
          volumeMounts:
            - name: config
              mountPath: /etc/prometheus
            - name: data
              mountPath: /prometheus
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
      volumes:
        - name: config
          configMap:
            name: prometheus-config
        - name: data
          persistentVolumeClaim:
            claimName: prometheus-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-data
  namespace: monitoring
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

**Service**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
spec:
  type: NodePort
  selector:
    app: prometheus
  ports:
    - port: 9090
      targetPort: 9090
      nodePort: 30090
```

**Verification Commands**:
```bash
kubectl apply -f monitoring-namespace.yaml
kubectl apply -f prometheus-config.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f prometheus-service.yaml

# Check Prometheus is running
kubectl get pods -n monitoring
kubectl logs -n monitoring deployment/prometheus

# Port-forward for access
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Access: http://localhost:9090
# Check targets: http://localhost:9090/targets
```

### Exercise 2b: PromQL Queries with Expected Results

**1. Total request rate**:
```promql
sum(rate(http_requests_total[5m]))
```
Expected: A single number like `2.5` (2.5 requests per second)

**2. Request rate by method**:
```promql
sum(rate(http_requests_total[5m])) by (method)
```
Expected: Multiple results like `{method="GET"} 2.1`, `{method="POST"} 0.4`

**3. 5xx error rate**:
```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
```
Expected: A single number, hopefully near 0

**4. Error percentage**:
```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
* 100
```
Expected: A percentage like `0.5` (meaning 0.5% errors)

**5. 95th percentile latency**:
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```
Expected: A value in seconds like `0.042` (42ms)

**6. p50, p95, p99 latency**:
```promql
# p50 (median)
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# p95
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# p99
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```

**7. p95 by endpoint**:
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, path))
```

**8. Top 5 endpoints by request rate**:
```promql
topk(5, sum(rate(http_requests_total[5m])) by (path))
```

**9. Task creation rate (per minute)**:
```promql
rate(flowforge_tasks_created_total[5m]) * 60
```
Multiply by 60 because `rate()` returns per-second, and "tasks per minute" is more human-readable.

**10. Queue growing check**:
```promql
rate(flowforge_tasks_created_total[5m]) > rate(flowforge_tasks_completed_total[5m])
```
Returns 1 (true) if creation rate exceeds completion rate.

**Checkpoint Answers**:
- "What percentage of requests in the last hour returned 5xx?": `sum(rate(http_requests_total{status=~"5.."}[1h])) / sum(rate(http_requests_total[1h])) * 100`
- Using `[1s]` instead of `[5m]`: Not enough data points. Prometheus scrapes every 15s, so a 1s window has 0 data points. `rate()` needs at least 2 data points. Minimum useful range = 2 * scrape_interval.
- `rate()` on gauges: `rate()` calculates rate of INCREASE of a counter. Gauges go up AND down. Use `deriv()` for gauges if you want rate of change, or just use the raw gauge value.
- `sum(rate(...)) by (path)` vs `sum by (path) (rate(...))`: They're identical! The `by` clause can go either place. This is a common PromQL syntax question.

---

## Lab 03: Grafana Dashboards and Alerting

### Exercise 3a: Grafana Kubernetes Manifests

**Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
        - name: grafana
          image: grafana/grafana:10.3.1
          ports:
            - containerPort: 3000
          env:
            - name: GF_SECURITY_ADMIN_PASSWORD
              value: "admin"  # Change in production!
          volumeMounts:
            - name: data
              mountPath: /var/lib/grafana
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "250m"
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: grafana-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: grafana-data
  namespace: monitoring
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  type: NodePort
  selector:
    app: grafana
  ports:
    - port: 3000
      targetPort: 3000
      nodePort: 30030
```

**Dashboard JSON (FlowForge Overview)** -- abridged:
```json
{
  "dashboard": {
    "title": "FlowForge Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 16, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"api-service\"}[5m])) by (status)",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "gridPos": { "h": 8, "w": 8, "x": 16, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"api-service\",status=~\"5..\"}[5m])) / sum(rate(http_requests_total{job=\"api-service\"}[5m])) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "color": "green", "value": null },
                { "color": "yellow", "value": 1 },
                { "color": "red", "value": 5 }
              ]
            },
            "unit": "percent"
          }
        }
      },
      {
        "title": "Latency p50 / p95 / p99",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 16, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job=\"api-service\"}[5m])) by (le))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job=\"api-service\"}[5m])) by (le))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job=\"api-service\"}[5m])) by (le))",
            "legendFormat": "p99"
          }
        ],
        "fieldConfig": {
          "defaults": { "unit": "s" }
        }
      },
      {
        "title": "Task Queue Depth",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 8, "x": 16, "y": 8 },
        "targets": [
          {
            "expr": "flowforge_queue_depth",
            "legendFormat": "Queue Depth"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "color": "green", "value": null },
                { "color": "red", "value": 100 }
              ]
            }
          }
        }
      }
    ]
  }
}
```

### Exercise 3b: Alerting Rules YAML

**Complete alerts.yml**:
```yaml
groups:
  - name: flowforge_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{job="api-service",status=~"5.."}[5m]))
            /
            sum(rate(http_requests_total{job="api-service"}[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          service: api-service
        annotations:
          summary: "High error rate on api-service"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%). This means more than 1 in 20 requests is failing."
          runbook: "Check api-service logs for error details. Common causes: database connection issues, upstream service failures."

      - alert: HighLatency
        expr: |
          histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="api-service"}[5m])) by (le))
          > 2
        for: 10m
        labels:
          severity: warning
          service: api-service
        annotations:
          summary: "High p99 latency on api-service"
          description: "p99 latency is {{ $value | humanizeDuration }} (threshold: 2s). 1% of requests are taking longer than 2 seconds."
          runbook: "Check for slow database queries, resource contention, or upstream dependency issues."

      - alert: WorkerQueueGrowing
        expr: flowforge_queue_depth > 100
        for: 15m
        labels:
          severity: warning
          service: worker-service
        annotations:
          summary: "Worker task queue is growing"
          description: "Queue depth is {{ $value }} (threshold: 100). Tasks are being created faster than they're being processed."
          runbook: "Check worker-service health. Consider scaling workers. Check for stuck tasks or slow processing."
```

**Alertmanager Configuration**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m

    route:
      group_by: ['alertname', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'default'
      routes:
        - match:
            severity: critical
          receiver: 'critical'
        - match:
            severity: warning
          receiver: 'warning'

    receivers:
      - name: 'default'
        webhook_configs:
          - url: 'http://webhook-receiver:5000/alerts'
      - name: 'critical'
        webhook_configs:
          - url: 'http://webhook-receiver:5000/critical'
      - name: 'warning'
        webhook_configs:
          - url: 'http://webhook-receiver:5000/warning'
```

**Alertmanager Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
        - name: alertmanager
          image: prom/alertmanager:v0.27.0
          args:
            - '--config.file=/etc/alertmanager/alertmanager.yml'
          ports:
            - containerPort: 9093
          volumeMounts:
            - name: config
              mountPath: /etc/alertmanager
      volumes:
        - name: config
          configMap:
            name: alertmanager-config
---
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: monitoring
spec:
  selector:
    app: alertmanager
  ports:
    - port: 9093
      targetPort: 9093
```

---

## Lab 04: SLOs and Logging

### Exercise 4a: SLO Calculations

**Availability SLO (99.9%)**:
- Error budget: 0.1%
- Per month (30 days): 30 × 24 × 60 = 43,200 minutes. 0.1% × 43,200 = **43.2 minutes** of downtime allowed
- Per 1 million requests: 0.1% × 1,000,000 = **1,000 failed requests** allowed

**Latency SLO (99% under 500ms)**:
- Error budget: 1%
- Per 1 million requests: 1% × 1,000,000 = **10,000 requests** can exceed 500ms
- More forgiving than availability SLO (10x the budget)

**Task Processing SLO (99.5% under 30s)**:
- Error budget: 0.5%
- Per 1,000 tasks: 0.5% × 1,000 = **5 tasks** can exceed 30 seconds

**Burn Rate Examples**:
- Error rate 0.1% with 99.9% SLO: burn rate = 0.1% / 0.1% = **1x** (exactly on budget)
- Error rate 1%: burn rate = 1% / 0.1% = **10x** (budget exhausted in 43.2 min / 10 = 4.32 min... wait, that's per-month budget)
  - Actually: monthly budget = 43.2 min. At 10x burn rate, budget exhausted in 43.2 / 10 = **4.32 minutes of error time needed, achieved in ~4.32 days** (because 10x means consuming 10 minutes of budget per day instead of 1.44)
  - More precisely: at 10x burn rate, monthly budget lasts 30 days / 10 = **3 days**
- Error rate 10%: burn rate = 10% / 0.1% = **100x**, budget exhausted in 30/100 = **~7.2 hours**

**SLI PromQL Expressions**:

Availability SLI:
```promql
1 - (
  sum(rate(http_requests_total{job="api-service",status=~"5.."}[30d]))
  /
  sum(rate(http_requests_total{job="api-service"}[30d]))
)
```

Latency SLI:
```promql
# Proportion of requests under 500ms
sum(rate(http_request_duration_seconds_bucket{job="api-service",le="0.5"}[30d]))
/
sum(rate(http_request_duration_seconds_count{job="api-service"}[30d]))
```

Error budget remaining:
```promql
# For 99.9% availability SLO
1 - (
  (1 - (
    sum(rate(http_requests_total{job="api-service",status=~"5.."}[30d]))
    /
    sum(rate(http_requests_total{job="api-service"}[30d]))
  )) - 0.999
) / 0.001
```

Burn rate:
```promql
(
  sum(rate(http_requests_total{job="api-service",status=~"5.."}[1h]))
  /
  sum(rate(http_requests_total{job="api-service"}[1h]))
) / 0.001
```

### Exercise 4b: Loki Deployment

**Loki Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: loki
  template:
    metadata:
      labels:
        app: loki
    spec:
      containers:
        - name: loki
          image: grafana/loki:2.9.4
          args:
            - '-config.file=/etc/loki/loki-config.yml'
          ports:
            - containerPort: 3100
          volumeMounts:
            - name: config
              mountPath: /etc/loki
            - name: data
              mountPath: /loki
      volumes:
        - name: config
          configMap:
            name: loki-config
        - name: data
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: loki
  namespace: monitoring
spec:
  selector:
    app: loki
  ports:
    - port: 3100
      targetPort: 3100
```

**Loki ConfigMap**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: monitoring
data:
  loki-config.yml: |
    auth_enabled: false
    server:
      http_listen_port: 3100
    common:
      path_prefix: /loki
      storage:
        filesystem:
          chunks_directory: /loki/chunks
          rules_directory: /loki/rules
      replication_factor: 1
      ring:
        kvstore:
          store: inmemory
    schema_config:
      configs:
        - from: 2020-10-24
          store: tsdb
          object_store: filesystem
          schema: v13
          index:
            prefix: index_
            period: 24h
    limits_config:
      reject_old_samples: true
      reject_old_samples_max_age: 168h
```

**Promtail DaemonSet**:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: promtail
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: promtail
  template:
    metadata:
      labels:
        app: promtail
    spec:
      containers:
        - name: promtail
          image: grafana/promtail:2.9.4
          args:
            - '-config.file=/etc/promtail/promtail-config.yml'
          volumeMounts:
            - name: config
              mountPath: /etc/promtail
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: varlibdockercontainers
              mountPath: /var/lib/docker/containers
              readOnly: true
      volumes:
        - name: config
          configMap:
            name: promtail-config
        - name: varlog
          hostPath:
            path: /var/log
        - name: varlibdockercontainers
          hostPath:
            path: /var/lib/docker/containers
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: promtail-config
  namespace: monitoring
data:
  promtail-config.yml: |
    server:
      http_listen_port: 9080
    positions:
      filename: /tmp/positions.yaml
    clients:
      - url: http://loki.monitoring.svc.cluster.local:3100/loki/api/v1/push
    scrape_configs:
      - job_name: kubernetes-pods
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            target_label: app
          - source_labels: [__meta_kubernetes_namespace]
            target_label: namespace
          - source_labels: [__meta_kubernetes_pod_name]
            target_label: pod
```

**LogQL Query Examples**:
```logql
# All logs from api-service
{app="api-service"}

# Error logs only
{app="api-service"} | json | level="error"

# 5xx responses
{app="api-service"} | json | status >= 500

# Slow requests (>1s)
{app="api-service"} | json | duration_ms > 1000

# Specific request by ID
{app="api-service"} | json | request_id="abc-123"

# Error count per minute
count_over_time({app="api-service"} | json | level="error" [1m])

# Worker task failures
{app="worker-service"} | json | level="error" |= "task"
```

---

## Lab 05: Failure Simulation

### Scenario 1: Kill a Worker Pod

**Expected Dashboard Behavior**:
- Queue depth: increases steadily (tasks being created but not processed)
- Task completion rate: drops to 0 (or reduced if multiple workers)
- API metrics: unchanged (API still works fine)
- Error rate: unchanged for API (worker failure doesn't affect API)
- Alert: `WorkerQueueGrowing` enters pending after queue exceeds 100, fires after 15 minutes

**Expected Log Entries**:
- Worker Pod termination signal in Loki: `{"level":"info","msg":"received SIGTERM, shutting down"}`
- Possible: `{"level":"warn","msg":"context cancelled during task processing"}`
- K8s events visible: Pod termination, new Pod creation by ReplicaSet

**Correct Diagnosis**:
"Worker-service Pod is down because: queue depth is growing, task completion rate dropped to 0, but API error rate is unchanged. The issue is on the processing side, not the API side. Kubernetes should be recreating the Pod (Deployment has replicas: 1)."

**Recovery**: Kubernetes automatically restarts the Pod via the Deployment's ReplicaSet. Queue should drain once the new worker is ready.

### Scenario 2: Exhaust Database Connections

**Expected Dashboard Behavior**:
- Error rate: spikes on BOTH api-service AND worker-service
- Request rate: may decrease (requests timing out)
- Latency: spikes (requests waiting for connections, then failing)
- Queue depth: may increase (new tasks can't be created, existing tasks can't be processed)

**Expected Log Entries**:
- `{"level":"error","msg":"connection pool exhausted","error":"too many connections"}`
- `{"level":"error","msg":"failed to query database","error":"dial tcp: connection refused"}`
- Both services show similar errors (they share the database)

**Correct Diagnosis**:
"Both api-service and worker-service are showing elevated error rates simultaneously. The errors are database-related (visible in logs: 'connection pool exhausted'). The root cause is database connection exhaustion, which affects both services because they share the PostgreSQL database."

### Scenario 3: Introduce Artificial Latency

**Expected Dashboard Behavior**:
- Latency: all percentiles increase dramatically (p50, p95, p99 all spike)
- Error rate: may stay LOW (requests succeed, just slowly)
- Active connections: increases (slow requests hold connections longer)
- Queue depth: may increase (if API is too slow to enqueue tasks)
- SLO dashboard: latency SLI drops below target, burn rate increases

**Expected Log Entries**:
- `{"level":"info","msg":"request completed","method":"GET","path":"/tasks","status":200,"duration_ms":3450}` (note: high duration but 200 status)
- No error logs! The sneaky part of this scenario is that everything "works" -- just slowly.

**Correct Diagnosis**:
"API requests are succeeding (low error rate) but p99 latency has spiked from ~50ms to ~3.5s. Active connections are elevated because slow requests hold connections longer. The SLO latency burn rate is 7x. The issue is latency, not availability. Logs show successful requests with very high duration_ms values but no errors. Root cause is likely within the request processing path (slow query, artificial delay, or external dependency)."

**Why Scenario 3 is Hardest**:
No errors means no obvious signal. The dashboard's latency panel is the primary indicator. Without an SLO dashboard, you might miss it entirely because "the service is up." This demonstrates why SLOs matter -- they quantify "up but degraded."

### Incident Report Template

```markdown
## Incident Report: [Title]

**Date**: YYYY-MM-DD
**Duration**: Start time - End time (total duration)
**Severity**: Critical / Warning / Info
**Impact**: [User-facing impact description]

### Detection
- How: [Alert / Dashboard observation / User report]
- Time to detect: [minutes from failure to awareness]
- Alert(s) fired: [which alerts, if any]

### Diagnosis
- Method: [Which dashboards, metrics, logs used]
- Key signals: [What metrics/logs pointed to root cause]
- Time to diagnose: [minutes from awareness to hypothesis]

### Root Cause
[Technical description of what broke and why]

### Resolution
- Action taken: [What fixed it]
- Time to resolve: [minutes from diagnosis to fix]
- Recovery verification: [How you confirmed the fix worked]

### Improvements
- Monitoring gaps: [What was hard to diagnose? What would help?]
- New alerts needed: [Should a new alert be created?]
- Dashboard changes: [Should panels be added or modified?]
- Prevention: [What could prevent this from happening again?]
```
