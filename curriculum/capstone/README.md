# Capstone: Production-Grade FlowForge Deployment

## Overview

**This is a test, not a tutorial. You receive requirements and acceptance criteria only. No step-by-step guidance is provided.**

Deploy FlowForge as a fully automated, monitored, and secured production system. Everything you have learned across all 10 modules culminates here. You must synthesize knowledge from Linux fundamentals through security hardening into a single, cohesive production deployment.

Your goal: a stranger should be able to clone your repository, run `terraform apply`, trigger a GitHub Actions pipeline, and have a fully running, monitored, and secured FlowForge system in production -- without asking you a single question.

---

## What You Are Building

A production-grade deployment of FlowForge that includes:

- **api-service** (Go): REST API for task management
- **worker-service** (Go): Background processor polling a PostgreSQL queue
- **PostgreSQL**: Persistent storage (RDS on AWS)
- **Python scripts**: Automation tooling, health checks, cleanup
- **Complete infrastructure**: VPC, subnets, security groups, EKS, ECR, S3, IAM
- **Full CI/CD pipeline**: Automated testing, building, scanning, and deployment
- **Monitoring stack**: Prometheus, Grafana, Alertmanager, Loki
- **Security controls**: Least-privilege IAM, secrets management, NetworkPolicies, RBAC, TLS, scanning

---

## Deliverables

You must produce all 7 deliverables below. Each has specific acceptance criteria that must be met.

### Deliverable 1: Infrastructure (Terraform)

**Module reference**: [Module 5 -- AWS Fundamentals](../module-05-aws/README.md), [Module 6 -- Terraform](../module-06-terraform/README.md)

| Acceptance Criteria |
|---|
| All AWS resources defined as Terraform code -- no manual Console steps |
| `terraform apply` from zero to running infrastructure in under 15 minutes |
| `terraform destroy` cleanly removes everything with no orphaned resources |
| Infrastructure is modularized (vpc, compute, database, ecr, eks, etc.) |
| Remote state stored in S3 with DynamoDB locking |
| Variables parameterize all environment-specific values (dev, staging, production) |
| Resources tagged consistently for cost tracking and cleanup |
| Sensitive values marked as `sensitive` and never in plain text |

### Deliverable 2: Containerization (Docker)

**Module reference**: [Module 4 -- Docker and Containerization](../module-04-docker/README.md)

| Acceptance Criteria |
|---|
| Multi-stage Dockerfiles for api-service and worker-service |
| Final images under 30MB each |
| Containers run as non-root user |
| No CRITICAL vulnerabilities when scanned with trivy |
| `.dockerignore` excludes unnecessary files |
| Health check endpoints work correctly in containers |
| Docker Compose available for local development with hot-reload |

### Deliverable 3: CI/CD (GitHub Actions)

**Module reference**: [Module 7 -- CI/CD with GitHub Actions](../module-07-cicd/README.md)

| Acceptance Criteria |
|---|
| Push to main triggers the full pipeline: test, lint, security scan, build, push to ECR, deploy to staging |
| Production deployment requires manual approval via GitHub Environments |
| Terraform changes: `plan` posted as PR comment, `apply` on merge to main |
| OIDC federation for keyless AWS authentication (no static access keys) |
| Quality gates: `go test` with >70% coverage, `golangci-lint`, `trivy` image scan, `gosec`/`govulncheck` |
| Pipeline fails fast on any security finding rated HIGH or CRITICAL |
| Docker images tagged with git SHA (not `latest`) |
| Concurrency groups prevent parallel Terraform applies |

### Deliverable 4: Orchestration (Kubernetes)

**Module reference**: [Module 8 -- Kubernetes](../module-08-kubernetes/README.md)

| Acceptance Criteria |
|---|
| Deployment manifests for api-service and worker-service with appropriate replica counts |
| Services: ClusterIP for internal communication, Ingress for external access |
| ConfigMaps for non-sensitive configuration |
| Secrets managed via External Secrets Operator pulling from AWS Secrets Manager |
| Ingress with TLS termination |
| NetworkPolicies enforcing service-to-service communication rules |
| Rolling updates with zero downtime (maxSurge, maxUnavailable configured) |
| Resource requests and limits set for all containers |
| Dedicated ServiceAccounts with RBAC (no default ServiceAccount) |

### Deliverable 5: Monitoring (Prometheus + Grafana)

**Module reference**: [Module 9 -- Monitoring and Observability](../module-09-monitoring/README.md)

| Acceptance Criteria |
|---|
| Both Go services instrumented with prometheus/client_golang exposing `/metrics` |
| Custom business metrics: tasks_created_total, tasks_completed_total, task_processing_duration_seconds, queue_depth |
| Prometheus deployed to K8s, scraping all service targets (all show UP) |
| Grafana dashboard with panels: request rate, error rate, latency p50/p95/p99, queue depth |
| Alerting rules: high error rate (>5% for 5 min), high latency (p99 >2s for 10 min), growing queue (>100 for 15 min) |
| Alertmanager configured with at least one notification route |
| SLO dashboard: availability SLI, error budget remaining, burn rate |
| Structured JSON logging queryable in Grafana (via Loki or alternative) |

### Deliverable 6: Security

**Module reference**: [Module 10 -- Security Hardening](../module-10-security/README.md)

| Acceptance Criteria |
|---|
| All IAM policies follow least privilege (verified by IAM Access Analyzer) |
| No secrets in code, environment variables, or Git history -- all in AWS Secrets Manager |
| Container images have no CRITICAL vulnerabilities (trivy scan passes in CI) |
| Kubernetes NetworkPolicies: default deny all, explicit allow for required paths only |
| RBAC: dedicated ServiceAccounts, Roles, RoleBindings -- no wildcards |
| TLS everywhere: service-to-service, client-to-ingress, RDS connections |
| CI/CD pipeline includes security scanning that fails on HIGH/CRITICAL |
| Incident response runbooks for at least 3 scenarios (compromised key, unauthorized access, container escape) |
| Threat model document covering all FlowForge components |

### Deliverable 7: Documentation

**Module reference**: All modules

| Acceptance Criteria |
|---|
| Architecture diagram showing all components and their interactions |
| Deployment runbook: step-by-step instructions a stranger can follow |
| Monitoring guide: what dashboards exist, what alerts mean, how to respond |
| Security audit report: findings, risk levels, remediation status |
| README.md: project overview, prerequisites, quick start, architecture, contributing |
| All documentation is accurate and matches the actual deployed system |

---

## Exit Gate

You must pass all four exit gate challenges to complete the capstone.

### 1. The Stranger Test

A person who has never seen your project should be able to:

1. Clone the repository
2. Run `terraform apply` (with their own AWS credentials)
3. Push a commit to trigger GitHub Actions
4. Have FlowForge running in production -- API accessible, tasks processing, monitoring active

**How to verify**: Give your repo URL to a friend, colleague, or rubber duck. Walk through the README as if you have no context. Every step must be documented. Every command must work. If you have to explain anything verbally, your documentation is incomplete.

### 2. Break-and-Recover

Demonstrate that your system is resilient and observable by performing three failure scenarios:

| Scenario | What to Break | What to Demonstrate |
|---|---|---|
| Pod failure | Kill a worker Pod (`kubectl delete pod`) | Monitoring detects the failure (alert fires or dashboard shows). Kubernetes self-heals. Queue backlog clears. Document the timeline |
| Traffic spike | Generate a burst of requests (use your Python scripts or a load testing tool) | Latency and error rate dashboards reflect the spike. Alerts fire if SLOs are breached. System recovers after spike ends. Document your SLO budget impact |
| Secret compromise | Rotate a secret in AWS Secrets Manager | Application detects the new secret (or you follow your runbook to restart). No downtime. Document the rotation procedure and recovery time |

For each scenario, write an incident report including: detection time, diagnosis steps, root cause, recovery actions, prevention improvements.

### 3. Interview Presentation

Present your architecture as if in a technical interview. Cover:

- **Architecture decisions**: Why EKS over ECS? Why this VPC layout? Why this branching strategy?
- **Trade-offs**: What did you sacrifice for simplicity? What would you change at 10x scale?
- **Cost analysis**: What does this cost per month? Where are the biggest cost drivers?
- **What you'd do differently**: With unlimited time and budget, what would you add?

Record yourself explaining (video, audio, or written script). You should be able to answer "why" for every technical choice.

### 4. Security Audit

Perform a complete security audit of your deployed system:

- Run IAM Access Analyzer and address all findings
- Run trivy on all container images
- Verify NetworkPolicies block unauthorized traffic (test with curl from unauthorized Pods)
- Verify TLS on all communication paths (openssl s_client)
- Review CloudTrail logs for any unexpected API calls
- Check that no secrets appear in Git history (`git log -p | grep -i password`)

**Result**: Zero unaddressed HIGH or CRITICAL findings. Any accepted risks must be documented with justification.

---

## Module Cross-Reference

Every deliverable builds on knowledge from specific modules. Use this table to review concepts you need:

| Deliverable | Primary Modules | Key Concepts to Review |
|---|---|---|
| Infrastructure (Terraform) | [Module 5](../module-05-aws/README.md), [Module 6](../module-06-terraform/README.md) | VPC/subnets/SGs, IAM, RDS, ECR, S3; HCL, modules, state, workspaces |
| Containerization (Docker) | [Module 4](../module-04-docker/README.md) | Multi-stage builds, layer caching, non-root, .dockerignore, trivy |
| CI/CD (GitHub Actions) | [Module 7](../module-07-cicd/README.md) | Workflows, OIDC, quality gates, environments, Terraform in CI |
| Orchestration (Kubernetes) | [Module 8](../module-08-kubernetes/README.md) | Deployments, Services, ConfigMaps, Secrets, Ingress, NetworkPolicies |
| Monitoring (Prometheus + Grafana) | [Module 9](../module-09-monitoring/README.md) | Instrumentation, PromQL, dashboards, alerting, SLOs, Loki |
| Security | [Module 10](../module-10-security/README.md) | Threat modeling, IAM, Secrets Manager, RBAC, encryption, scanning, runbooks |
| Documentation | All modules | Architecture diagrams, runbooks, audit reports |

Additionally, foundational knowledge from earlier modules underpins everything:

| Foundation Module | What It Contributes to the Capstone |
|---|---|
| [Module 1 -- Linux](../module-01-linux/README.md) | File permissions for containers, process management (SIGTERM/graceful shutdown), systemd concepts for understanding K8s service management, bash scripting for automation |
| [Module 2 -- Networking](../module-02-networking/README.md) | TCP/IP for understanding service communication, DNS for K8s service discovery, firewall rules informing SecurityGroups and NetworkPolicies, TLS/SSL, subnetting for VPC design |
| [Module 3 -- Go App](../module-03-go-app/README.md) | The application itself: REST API, worker pattern, PostgreSQL queue, 12-Factor config, structured logging, Python scripts, testing |

---

## Suggested Timeline

This capstone is designed to take approximately 1 week of focused effort. Here is a suggested breakdown:

| Day | Focus | Deliverables |
|---|---|---|
| Day 1 | Infrastructure setup | Terraform modules: VPC, subnets, SGs, RDS, ECR, EKS. Remote state. Verify `terraform apply` works end-to-end |
| Day 2 | Containerization + CI/CD | Dockerfiles finalized, GitHub Actions pipeline: test → lint → scan → build → push → deploy. OIDC configured |
| Day 3 | Kubernetes deployment | All K8s manifests: Deployments, Services, ConfigMaps, Secrets (ESO), Ingress, NetworkPolicies. Verify end-to-end task flow |
| Day 4 | Monitoring + Security | Prometheus, Grafana, Alertmanager deployed. Alerts configured. Security controls applied: RBAC, TLS, scanning, Secrets Manager |
| Day 5 | Documentation + Exit Gate | Architecture diagram, deployment runbook, monitoring guide, security audit. Stranger test. Break-and-recover. Interview prep |

This timeline assumes you have completed all 10 modules and have working implementations from each. If you need to revisit module material, plan for additional time.

---

## Important Reminders

1. **No guidance is provided.** You have the knowledge from Modules 1-10. Apply it.
2. **If you're stuck**, revisit the specific module README and your lab work. The answers are in what you've already built.
3. **The goal is synthesis**, not repetition. You're not just redoing each module -- you're combining everything into a coherent whole.
4. **Production means production.** Would you be comfortable handing this system to a team and walking away? That's the bar.
5. **Document everything.** If it's not documented, it doesn't exist. Your future self (and the stranger test) depend on it.
6. **Security is not optional.** Every deliverable has security implications. A beautifully automated but insecure system fails the capstone.

---

## Self-Assessment

Before declaring the capstone complete, use the [Rubric](./rubric.md) to score yourself honestly. Your target: "Meets Expectations" or higher on every deliverable.

Good luck. You've been preparing for this since Module 1.
