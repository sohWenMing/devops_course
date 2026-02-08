# Lab 01: Application Instrumentation

> **Module**: 9 -- Monitoring and Observability  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [Application Instrumentation](#), [Custom Business Metrics](#), and [Metric Types](#) sections of the Module 9 README. FlowForge api-service and worker-service running (Module 3). Kubernetes cluster with FlowForge deployed (Module 8).

---

## Overview

Before Prometheus can monitor anything, your application needs to speak its language. In this lab you'll add the `prometheus/client_golang` library to your Go services and expose metrics that tell you how the application is performing -- both from an infrastructure perspective (request rate, latency, errors) and a business perspective (tasks created, tasks completed, queue depth).

---

## Exercise 1a: Instrumenting api-service with Prometheus Metrics

### Objectives

- Add the `prometheus/client_golang` library to api-service
- Expose a `/metrics` endpoint that Prometheus can scrape
- Instrument four core HTTP metrics: request count, request duration, active connections, and error rate
- Understand the difference between counters, gauges, and histograms in practice

### What You'll Do

**Part 1: Add the Prometheus Client Library**

1. Add `prometheus/client_golang` as a dependency to api-service. You'll need both the `prometheus` package (for metric types) and the `promhttp` package (for the HTTP handler).

2. Register a `/metrics` endpoint in your HTTP router that serves the Prometheus metrics handler. This endpoint should be separate from your API routes but served by the same HTTP server.

3. Start your api-service and verify you can access the `/metrics` endpoint. You should see Go runtime metrics (garbage collection, goroutines, memory) even before you add any custom metrics. These are provided automatically by the client library's default registry.

**Part 2: Instrument Request Count**

4. Create a **counter** metric called `http_requests_total` that tracks the total number of HTTP requests. It should have labels for:
   - `method` (GET, POST, PUT, DELETE)
   - `path` (the URL path, e.g., `/tasks`, `/health`)
   - `status` (the HTTP status code as a string, e.g., "200", "404", "500")

5. Register this counter with the default Prometheus registry. Increment it in your HTTP middleware so every request is counted, regardless of which handler processes it.

6. Think carefully: should you put this in each handler, or in middleware that wraps all handlers? What are the trade-offs?

**Part 3: Instrument Request Duration**

7. Create a **histogram** metric called `http_request_duration_seconds` that tracks how long each HTTP request takes. Use the same labels as the request counter (method, path, status).

8. Choose appropriate histogram bucket boundaries. Think about what latencies are meaningful for your API:
   - What's "fast" for a FlowForge API request?
   - What's "acceptable"?
   - What's "too slow"?
   - Your buckets should cover the range from fast to too-slow with enough granularity

9. Measure the duration in your middleware by recording the time before and after the handler executes.

**Part 4: Instrument Active Connections**

10. Create a **gauge** metric called `http_active_connections` that tracks the number of currently in-flight HTTP requests. This goes up when a request starts and down when it completes.

11. Increment the gauge at the start of your middleware, and decrement it (using defer) at the end. This gives you a real-time view of concurrency.

12. Think about: why is this a gauge and not a counter? What does this metric tell you that request count doesn't?

**Part 5: Verify Your Instrumentation**

13. Start api-service. Generate some traffic (use curl, your Python healthcheck script, or a simple loop).

14. Visit the `/metrics` endpoint and verify:
    - `http_requests_total` shows counts for each method/path/status combination
    - `http_request_duration_seconds_bucket` shows histogram buckets with counts
    - `http_request_duration_seconds_sum` and `_count` are populated
    - `http_active_connections` shows 0 (or a small number if you're sending concurrent requests)

15. Generate an error (e.g., request a non-existent resource) and verify the counter shows the error status code.

### Expected Outcome

- api-service exposes a `/metrics` endpoint returning valid Prometheus exposition format
- At least three custom metrics are visible: `http_requests_total` (counter), `http_request_duration_seconds` (histogram), `http_active_connections` (gauge)
- Metrics have appropriate labels (method, path, status)
- Middleware captures metrics for ALL routes, not just specific handlers

### Checkpoint Questions

- [ ] Why is `http_requests_total` a counter and not a gauge?
- [ ] Why do you use `rate()` with counters but not with gauges? (You'll use this in Lab 02)
- [ ] What happens to your counter values when api-service restarts? How does Prometheus handle this?
- [ ] Why did you choose the histogram bucket boundaries you chose? What would happen if all your requests are faster than your smallest bucket?
- [ ] What's the cardinality of your metrics? (How many unique time series does each metric create?) What would happen if you added a `user_id` label?

---

## Exercise 1b: Custom FlowForge Business Metrics

### Objectives

- Design and implement business-specific metrics for FlowForge
- Add metrics that measure user outcomes, not just infrastructure health
- Instrument both api-service and worker-service
- Understand the difference between infrastructure metrics and business metrics

### What You'll Do

**Part 1: Design Business Metrics**

1. Before writing any code, think about what FlowForge's stakeholders care about. The question isn't "is the server running?" -- it's "are tasks being created and processed?" Design metrics for:
   - How many tasks are being created (by the API)
   - How many tasks are being completed (by the worker)
   - How long task processing takes (by the worker)
   - How many tasks are waiting in the queue (at any point in time)

2. For each metric, decide:
   - What type should it be? (counter, gauge, or histogram)
   - What labels should it have? (think: task type, status, worker instance)
   - What's a good name following Prometheus naming conventions? (namespace_subsystem_name_unit)

**Part 2: Implement api-service Business Metrics**

3. Add a counter `flowforge_tasks_created_total` to api-service. Increment it whenever a new task is successfully created (POST /tasks returns 201). Add a label for `task_type` if your FlowForge supports different task types.

4. Think about WHERE in the code this counter should be incremented. Should it be in middleware? In the handler? In the database layer? What are the implications of each choice? (Hint: what if the database insert fails after you increment the counter?)

**Part 3: Implement worker-service Business Metrics**

5. Add `prometheus/client_golang` to worker-service. Expose a `/metrics` endpoint on a separate port (e.g., 8081) from the worker's main functionality.

6. Implement the following metrics in worker-service:
   - `flowforge_tasks_completed_total` (counter): Incremented when a task is successfully processed
   - `flowforge_task_processing_duration_seconds` (histogram): Records how long each task takes to process, from pickup to completion
   - `flowforge_queue_depth` (gauge): The current number of tasks in the queue with status "pending"

7. For `flowforge_queue_depth`, think about how to keep this up to date. Options:
   - Query the database periodically and set the gauge value
   - Increment on task creation, decrement on task completion (but what about crashes?)
   - Which approach is more accurate? Which has less overhead?

**Part 4: End-to-End Verification**

8. Run both services (locally or in Kind). Create several tasks through the API. Let the worker process them.

9. Check the `/metrics` endpoint on both services:
   - api-service should show `flowforge_tasks_created_total` increasing
   - worker-service should show `flowforge_tasks_completed_total` increasing
   - worker-service should show `flowforge_task_processing_duration_seconds` with meaningful bucket values
   - worker-service should show `flowforge_queue_depth` reflecting the actual queue state

10. Create a burst of tasks (10-20 quickly) and observe:
    - Does `flowforge_queue_depth` increase and then gradually decrease?
    - Does `flowforge_task_processing_duration_seconds` show a reasonable distribution?
    - Does `flowforge_tasks_completed_total` eventually match `flowforge_tasks_created_total`?

### Expected Outcome

- api-service exposes `flowforge_tasks_created_total` counter
- worker-service exposes `flowforge_tasks_completed_total` counter, `flowforge_task_processing_duration_seconds` histogram, and `flowforge_queue_depth` gauge
- Both services have `/metrics` endpoints serving valid Prometheus format
- Business metrics accurately reflect the actual state of task processing

### Checkpoint Questions

- [ ] If you had to choose ONLY ONE business metric for FlowForge, which would it be and why?
- [ ] What's the difference between `flowforge_tasks_created_total` (counter) and `flowforge_queue_depth` (gauge) in terms of what they tell you?
- [ ] If a worker crashes mid-task, which metrics would change? Which wouldn't? Is that a problem?
- [ ] Why is `flowforge_task_processing_duration_seconds` a histogram rather than a gauge?
- [ ] For a new application (say an e-commerce platform), what business metrics would you design? Name at least 5.
