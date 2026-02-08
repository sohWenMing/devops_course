# FlowForge -- Project Structure

> **This is the application you'll build, containerize, deploy, monitor, and secure throughout the course.**

---

## Overview

FlowForge is a task/workflow orchestration platform consisting of:

- **api-service** (Go): REST API for task management -- accepts HTTP requests, persists tasks to PostgreSQL
- **worker-service** (Go): Background processor that polls PostgreSQL for pending tasks and processes them
- **PostgreSQL**: Persistent storage for tasks and the inter-service communication queue
- **scripts** (Python): Automation tooling for database seeding, health checks, and cleanup

---

## Directory Structure

```
project/
├── api-service/
│   ├── go.mod              # Go module definition
│   ├── main.go             # Application entry point (starter skeleton with TODOs)
│   └── ...                 # You'll add packages here: handlers/, models/, etc.
│
├── worker-service/
│   ├── go.mod              # Go module definition
│   ├── main.go             # Application entry point (starter skeleton with TODOs)
│   └── ...                 # You'll add packages here: worker/, models/, etc.
│
├── scripts/
│   ├── seed-database.py    # Populate database with test data (TODO)
│   ├── healthcheck.py      # Verify all services are running (TODO)
│   └── cleanup.py          # Reset database to clean state (TODO)
│
├── infra/                  # Terraform configs (Module 6)
├── k8s/                    # Kubernetes manifests (Module 8)
└── .github/workflows/      # CI/CD pipelines (Module 7)
```

---

## Getting Started (Module 3)

### Prerequisites

1. **Go 1.21+**: `go version` should show 1.21 or higher
2. **PostgreSQL**: Running locally (installed in Module 1)
3. **Python 3.8+**: `python3 --version` should show 3.8 or higher

### Setup

1. Create a PostgreSQL database for FlowForge:
   ```bash
   sudo -u postgres createdb flowforge
   sudo -u postgres createuser flowforge_user
   ```

2. Set up environment variables (create a `.env` file in the project root):
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. Start with the api-service:
   ```bash
   cd api-service
   go mod tidy        # Download dependencies
   go run main.go     # Start the server
   ```

4. Start the worker-service:
   ```bash
   cd worker-service
   go mod tidy
   go run main.go
   ```

5. Use the Python scripts:
   ```bash
   cd scripts
   pip install -r requirements.txt   # Install Python dependencies
   python seed-database.py --count 20
   python healthcheck.py
   python cleanup.py --confirm
   ```

---

## Environment Variables

See `.env.example` for the complete list. Key variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgres://flowforge_user:pass@localhost:5432/flowforge?sslmode=disable` |
| `API_PORT` | Port for the api-service HTTP server | `8080` |
| `WORKER_POLL_INTERVAL` | How often the worker checks for new tasks | `5s` |
| `LOG_LEVEL` | Minimum log level (debug, info, warn, error) | `info` |

---

## Architecture

```
              HTTP
User ────────────► api-service ────────► PostgreSQL
                   (Go REST API)          (tasks table)
                                              │
                                              │ polling
                                              ▼
                                        worker-service
                                        (Go background)
```

1. User sends HTTP request to api-service (e.g., `POST /tasks`)
2. api-service validates the request and inserts a task with `status=pending`
3. worker-service polls for pending tasks using `SELECT FOR UPDATE SKIP LOCKED`
4. worker-service claims and processes the task, updates status to `completed`
5. User queries api-service to see the task's updated status

---

## Starter Code

The `main.go` files in `api-service/` and `worker-service/` contain minimal skeletons with TODO comments. They compile and run but don't do anything useful. Your job in Module 3 labs is to fill in the implementation:

- **Lab 01**: Design the API and implement HTTP routing
- **Lab 02**: Connect to PostgreSQL and set up migrations
- **Lab 03**: Build the worker polling loop and inter-service queue
- **Lab 04**: Externalize config, write Python scripts, add structured logging
- **Lab 05**: Write unit and integration tests

---

## Future Modules

This project will evolve through the course:
- **Module 4 (Docker)**: Add Dockerfiles, docker-compose.yml
- **Module 5 (AWS)**: Deploy to EC2 + RDS
- **Module 6 (Terraform)**: Codify infrastructure
- **Module 7 (CI/CD)**: Automate build/test/deploy with GitHub Actions
- **Module 8 (Kubernetes)**: Deploy to Kind and EKS with manifests
- **Module 9 (Monitoring)**: Add Prometheus metrics and Grafana dashboards
- **Module 10 (Security)**: Harden everything -- IAM, secrets, network policies, scanning
