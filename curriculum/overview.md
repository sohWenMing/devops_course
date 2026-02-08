# Curriculum Overview

Full curriculum map for the DevOps and Cloud Engineering course. 10 modules + capstone, approximately 17 weeks at 10-15 hours per week.

---

## Course Progression

```
Linux (Weeks 1-2)
  └─> Networking (Weeks 2-3)
        └─> Go App (Weeks 4-5)
              └─> Docker (Weeks 6-7)
                    └─> AWS (Weeks 8-9)
                          └─> Terraform (Weeks 10-11)
                                └─> CI/CD (Weeks 11-12)
                                      └─> Kubernetes (Weeks 13-14)
                                            └─> Monitoring (Weeks 15-16)
                                                  └─> Security (Weeks 16-17)
                                                        └─> Capstone (Week 17)
```

---

## Module 1: Linux Deep Dive (Weeks 1-2)

**Link forward**: "The OS your containers, VMs, and Kubernetes nodes all run"

**AWS SAA Alignment**: Foundation for all AWS services (EC2, ECS, EKS run Linux)

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 1 | 1a: Filesystem navigation | File system hierarchy | FlowForge project directory structure with correct ownership |
| Lab 1 | 1b: Users, groups, permissions | File permissions & ownership | Isolated dirs for api-service and worker-service with proper chmod/chown/umask |
| Lab 2 | 2a: Processes & signals | Processes & signals | Background processes managed with ps/top/htop, SIGTERM vs SIGKILL demonstrated |
| Lab 2 | 2b: systemd unit files | systemd services | Unit file for api-service, enabled on boot, logs via journalctl |
| Lab 2 | 2c: Package management | Package management | PostgreSQL installed via apt, dependencies inspected |
| Lab 3 | 3a: Health-check script | Bash scripting | Script checking PostgreSQL, api-service port, disk usage with meaningful exit codes |
| Lab 3 | 3b: Env var loading script | Environment variables & config | .env file for FlowForge + validation script |
| Lab 4 | 4a: SSH setup | SSH | SSH keypair, sshd hardened config, key-based auth to localhost |
| Lab 5 | Broken Server | Debugging challenge | 5 misconfigurations found and fixed (permissions, dead service, full disk, bad cron, missing env var) |

### Exit Gate Checkpoints

- [ ] Explain the Linux FHS to someone without notes
- [ ] Write a systemd unit file from memory
- [ ] Write a bash script with argument parsing, error handling, and meaningful exit codes from scratch
- [ ] SSH into a machine with key-based auth you configured yourself
- [ ] Diagnose a broken Linux system by reading logs, checking processes, and inspecting permissions

---

## Module 2: Networking Fundamentals (Weeks 2-3)

**Link forward**: "Every VPC, subnet, security group, and load balancer maps to these concepts"

**AWS SAA Alignment**: Design Resilient Architectures

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 1 | 1a: tcpdump packet capture | OSI model & TCP/IP stack | Captured traffic between api-service and PostgreSQL, layers identified |
| Lab 1 | 1b: Subnet calculation & planning | IP addressing & subnets | Subnet layout for FlowForge (public, private, database subnets) |
| Lab 2 | 2a: Local DNS & dig/nslookup | DNS resolution | Local DNS entries for FlowForge services, DNS trace |
| Lab 2 | 2b: HTTP deep dive with curl | HTTP deep dive | curl -v requests with header inspection, proper status codes |
| Lab 2 | 2c: Ports & socket inspection | Ports & sockets | ss/netstat listing, api-service bound to specific interfaces |
| Lab 3 | 3a: iptables/ufw firewall rules | Firewalls | iptables rules: SSH, api-service, PostgreSQL restricted, deny all else |
| Lab 3 | 3b: Network namespaces & routing | Routing & gateways | Two network namespaces with traffic routed between them |
| Lab 3 | 3c: nginx reverse proxy | Load balancing concepts | nginx round-robin in front of 2 api-service instances |
| Lab 3 | 3d: TLS/SSL setup | TLS/SSL | Self-signed certs, HTTPS on api-service, TLS handshake inspected |
| Lab 4 | Broken Network | Debugging challenge | DNS, firewall, routing, and port binding issues found and fixed |

### Exit Gate Checkpoints

- [ ] Calculate subnet ranges from CIDR notation by hand
- [ ] Capture and explain a packet at every OSI layer using tcpdump
- [ ] Write firewall rules for a 3-tier app from scratch
- [ ] Set up a reverse proxy with TLS termination from memory
- [ ] Systematically diagnose "services can't talk" using a layered approach (physical -> application)

---

## Module 3: Building FlowForge in Go (Weeks 4-5)

**Link forward**: "This is the app you'll containerize, deploy, automate, orchestrate, monitor, and secure"

**AWS SAA Alignment**: Application architecture patterns

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 1 | 1a: REST API design | REST API design | OpenAPI spec for FlowForge task CRUD endpoints |
| Lab 1 | 1b: Go HTTP server | Go HTTP server | api-service with GET/POST/PUT/DELETE /tasks, GET /health |
| Lab 2 | 2a: PostgreSQL setup & schema | PostgreSQL integration | Schema with tasks table, Go connection via database/sql |
| Lab 2 | 2b: Migration files | Database migrations | Up/down migration files, apply/rollback with golang-migrate |
| Lab 3 | 3a: Worker service | Background worker pattern | worker-service polling PostgreSQL, graceful shutdown on SIGTERM |
| Lab 3 | 3b: Inter-service communication | Inter-service communication | api-service enqueues, worker picks up via SELECT FOR UPDATE SKIP LOCKED |
| Lab 4 | 4a: 12-factor config | Configuration & 12-factor | All config externalized to environment variables |
| Lab 4 | 4b: Python automation scripts | Python automation scripts | seed-database.py, healthcheck.py, cleanup.py |
| Lab 4 | 4c: Structured logging | Structured logging | JSON logging with request ID, timestamp, level, caller |
| Lab 5 | Go testing | Go testing | Unit + integration tests, >70% coverage on api-service |

### Exit Gate Checkpoints

- [ ] FlowForge api-service runs, accepts requests, persists to PostgreSQL
- [ ] FlowForge worker-service processes tasks from the queue
- [ ] Both services shut down gracefully on SIGTERM
- [ ] All config comes from env vars, no hardcoded values
- [ ] Tests pass and coverage > 70% for api-service
- [ ] Can explain data flow from "user creates task" to "worker completes task" without looking at code

---

## Module 4: Docker and Containerization (Weeks 6-7)

**Link forward**: "These images become your deployment artifacts for AWS and Kubernetes"

**AWS SAA Alignment**: Container services (ECS, ECR, EKS)

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 1 | 1a: Containers vs VMs | Containers vs VMs | Process isolation with unshare, resource comparison |
| Lab 1 | 1b: Dockerfile fundamentals | Dockerfile fundamentals | Dockerfiles for api-service and worker-service (naive approach) |
| Lab 2 | 2a: Image layer analysis | Image layers & caching | Reordered Dockerfile with maximized cache hits, build time comparison |
| Lab 2 | 2b: Multi-stage builds | Multi-stage builds | Multi-stage Dockerfiles, < 20MB final images |
| Lab 3 | 3a: Docker networking | Docker networking | Custom Docker network with DNS resolution between containers |
| Lab 3 | 3b: Docker volumes | Docker volumes & persistence | PostgreSQL volume with data persistence across container restarts |
| Lab 4 | 4a: Docker Compose | Docker Compose | docker-compose.yml for full FlowForge stack with health checks |
| Lab 4 | 4b: Development workflow | Docker Compose for development | Hot-reload dev setup with source code mounted as volume |
| Lab 5 | 5a: Container security | Container security basics | Non-root containers, trivy scan, vulnerability fixes |
| Lab 5 | 5b: Broken Docker | Debugging challenge | 4 broken setups diagnosed (port mapping, env var, permissions, network) |

### Exit Gate Checkpoints

- [ ] `docker compose up` brings up entire FlowForge stack, all services communicate
- [ ] Images are multi-stage, < 30MB each for Go services
- [ ] Containers run as non-root, trivy scan shows no CRITICAL vulnerabilities
- [ ] Write a Dockerfile from scratch for a new Go service in under 10 minutes
- [ ] Explain image layers, caching, and instruction order without notes
- [ ] Debug a container that fails to start using only docker logs and docker inspect

---

## Module 5: AWS Fundamentals (Weeks 8-9)

**Link forward**: "You just did everything manually. Module 6 will codify ALL of it"

**AWS SAA Alignment**: Design Resilient, High-Performing, and Secure Architectures

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 0 | Account setup & billing | AWS account setup & billing | MFA, billing alarm ($5), budget, Python cleanup script |
| Lab 1 | 1a: IAM users & policies | IAM users, groups, policies | FlowForge IAM user with least-privilege policies |
| Lab 1 | 1b: IAM roles & instance profiles | IAM roles & instance profiles | EC2 instance profile for S3 read + CloudWatch Logs write |
| Lab 2 | 2a: VPC from scratch | VPC from scratch | VPC with public/private/database subnets, IGW, NAT, route tables (all CLI) |
| Lab 2 | 2b: Security groups & NACLs | Security groups & NACLs | api-sg, worker-sg, db-sg with least-privilege rules |
| Lab 3 | 3a: EC2 instances | EC2 instances | t3.micro in public subnet running FlowForge api-service container |
| Lab 3 | 3b: RDS PostgreSQL | RDS PostgreSQL | db.t3.micro in database subnet, connected from EC2 |
| Lab 3 | 3c: S3 basics | S3 basics | S3 bucket for FlowForge artifacts with bucket policy |
| Lab 4 | 4a: ECR | ECR (container registry) | ECR repos for api-service and worker-service, push/pull workflow |
| Lab 5 | Full manual deployment | Manual full deployment | End-to-end FlowForge on AWS: ECR, EC2, RDS, networking, health checks |
| Lab 6 | Cost cleanup | Cost cleanup | Cleanup script run, $0 ongoing charges verified |

### Exit Gate Checkpoints

- [ ] FlowForge runs on AWS (EC2 + RDS) and is accessible from the internet
- [ ] VPC has public, private, and database subnets with correct routing
- [ ] Security groups follow least privilege
- [ ] IAM uses a dedicated user with custom policy, not root
- [ ] Draw the full AWS architecture diagram from memory
- [ ] Create a VPC with subnets, route tables, and security groups from CLI without notes
- [ ] Cleanup script runs and billing dashboard confirms no ongoing charges

---

## Module 6: Terraform (Weeks 10-11)

**Link forward**: "CI/CD will run these Terraform configs automatically"

**AWS SAA Alignment**: Design High-Performing and Cost-Optimized Architectures

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 1 | 1a: HCL basics | IaC philosophy & HCL basics | Minimal Terraform config for S3 bucket; init/plan/apply/destroy |
| Lab 1 | 1b: Resources & data sources | Resources & data sources | VPC, subnet, IGW as resources; latest Ubuntu AMI as data source |
| Lab 2 | 2a: Variables & outputs | Variables & outputs | Parameterized config with typed variables, sensitive values, outputs |
| Lab 2 | 2b: State management | State management | State inspection, drift detection after manual console change, terraform import |
| Lab 3 | 3a: Remote state | Remote state (S3 + DynamoDB) | S3 backend with DynamoDB locking, local-to-remote state migration |
| Lab 3 | 3b: Modules | Modules | Refactored into vpc, compute, database, ecr modules |
| Lab 4 | 4a: Workspaces | Workspaces | dev and staging workspaces with different variable files |
| Lab 5 | Full recreation | Full infrastructure recreation | Entire FlowForge AWS infra recreated with single terraform apply |
| Lab 6 | Broken Terraform | Debugging challenge | 4 bugs fixed (circular dependency, wrong reference, state corruption, provider conflict) |

### Exit Gate Checkpoints

- [ ] `terraform apply` creates entire FlowForge AWS infrastructure from scratch
- [ ] `terraform destroy` cleanly removes everything
- [ ] Infrastructure is modularized (vpc, compute, database, ecr modules)
- [ ] State is stored remotely in S3 with DynamoDB locking
- [ ] Write a new Terraform module from scratch in under 15 minutes
- [ ] Explain plan/apply lifecycle, state purpose, and drift detection without notes
- [ ] Read a terraform plan output and predict exactly what will change

---

## Module 7: CI/CD with GitHub Actions (Weeks 11-12)

**Link forward**: "Kubernetes deployment will be the target of this pipeline"

**AWS SAA Alignment**: Design Cost-Optimized Architectures

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 0 | Pipeline diagram | CI vs CD concepts | Written pipeline diagram from git push to production |
| Lab 1 | 1a: GitHub Actions basics | GitHub Actions basics | Workflow: on push, run go test, report results |
| Lab 1 | 1b: Build & push Docker images | Build & push Docker images | Job: build images, tag with git SHA, push to ECR |
| Lab 2 | 2a: Secrets management | Secrets management in CI | AWS credentials as GitHub secrets, OIDC federation |
| Lab 2 | 2b: Quality gates | Test stages & quality gates | Linting, security scanning, coverage threshold (>70%) |
| Lab 3 | 3a: Multi-environment deploy | Multi-environment deployment | Staging auto-deploy, production manual approval |
| Lab 3 | 3b: Branch strategies | Branch strategies | Trunk-based development with feature branches, PR triggers CI |
| Lab 4 | Terraform in CI/CD | Terraform in CI/CD | terraform plan on PR (as comment), terraform apply on merge |
| Lab 5 | Broken pipelines | Debugging challenge | 3 broken pipelines diagnosed from workflow logs only |

### Exit Gate Checkpoints

- [ ] Push to main triggers: test, lint, build, push to ECR, deploy to staging
- [ ] Production deployment requires manual approval
- [ ] Terraform changes planned on PR and applied on merge
- [ ] Read workflow YAML and predict execution order including parallel jobs
- [ ] Write a new GitHub Actions workflow from scratch for a different project
- [ ] Diagnose a failed pipeline from logs without looking at the workflow file first

---

## Module 8: Kubernetes (Weeks 13-14)

**Link forward**: "Now we need to see what's happening inside -- monitoring"

**AWS SAA Alignment**: Design Cost-Optimized Architectures (EKS)

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 0 | K8s architecture diagram | K8s architecture | Written diagram of control plane and node components |
| Lab 1 | 1a: Kind cluster | Local cluster setup | Kind cluster created and verified |
| Lab 1 | 1b: Pods | Pods | Pod manifest for api-service, exec, logs, delete |
| Lab 2 | 2a: Deployments & ReplicaSets | Deployments & ReplicaSets | Deployments for api-service (2 replicas) and worker-service (1 replica) |
| Lab 2 | 2b: Services | Services (ClusterIP, NodePort, LoadBalancer) | ClusterIP for PostgreSQL, NodePort for api-service, DNS resolution |
| Lab 3 | 3a: ConfigMaps | ConfigMaps | ConfigMaps for non-sensitive config, mounted as env vars |
| Lab 3 | 3b: Secrets | Secrets | Secrets for DB password/API keys, mounted as env vars |
| Lab 3 | 3c: Namespaces | Namespaces | dev and staging namespaces with FlowForge deployed to both |
| Lab 4 | 4a: Ingress | Ingress | nginx ingress controller, /api/* routing, TLS with self-signed cert |
| Lab 4 | 4b: Full local deployment | Full local deployment | Entire FlowForge stack on Kind with PV, end-to-end task flow verified |
| Lab 5 | 5a: EKS deployment | EKS deployment | EKS cluster via Terraform, FlowForge deployed, AWS LB Controller |
| Lab 6 | Broken K8s | Debugging challenge | 4 broken deployments diagnosed (ImagePullBackOff, CrashLoopBackOff, selector mismatch, PVC issue) |

### Exit Gate Checkpoints

- [ ] FlowForge runs on Kind with all services communicating, accessible via Ingress
- [ ] Write Deployment, Service, ConfigMap, Secret, Ingress manifests from scratch
- [ ] Debug CrashLoopBackOff, ImagePullBackOff, and connectivity issues using kubectl
- [ ] Explain the K8s architecture diagram from memory
- [ ] Deploy to EKS and explain what's different from local Kind
- [ ] Scale, update, and rollback a Deployment from the CLI without notes

---

## Module 9: Monitoring and Observability (Weeks 15-16)

**Link forward**: "Monitoring shows you what's happening. Security ensures bad things don't happen"

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 0 | Observability decision exercise | Metrics vs logs vs traces | Written analysis: which signal for each FlowForge failure scenario |
| Lab 1 | 1a: Application instrumentation | Application instrumentation | api-service /metrics endpoint with request count, duration, connections, error rate |
| Lab 1 | 1b: Custom business metrics | Custom business metrics | tasks_created_total, tasks_completed_total, task_processing_duration, queue_depth |
| Lab 2 | 2a: Prometheus setup | Prometheus setup | Prometheus deployed to K8s, scraping api-service and worker-service |
| Lab 2 | 2b: PromQL queries | PromQL queries | Queries for request rate, error percentage, p95 latency, top 5 slowest endpoints |
| Lab 3 | 3a: Grafana dashboards | Grafana dashboards | FlowForge dashboard: request rate, error rate, latency p50/p95/p99, queue depth |
| Lab 3 | 3b: Alerting rules | Alerting rules | Rules for high error rate, high latency, growing queue depth |
| Lab 4 | 4a: SLOs, SLIs, SLAs | SLOs, SLIs, SLAs | SLO definitions, error budget calculation, SLO dashboard |
| Lab 4 | 4b: Structured logging with Loki | Structured logging with Loki | Loki deployed, JSON logs queried alongside metrics |
| Lab 5 | Failure simulation | Failure simulation | Kill Pod, exhaust DB connections, add latency -- observe alerts and dashboards |

### Exit Gate Checkpoints

- [ ] FlowForge services expose Prometheus metrics at /metrics
- [ ] Prometheus scrapes all services and targets show UP
- [ ] Grafana dashboard shows real-time request rate, error rate, latency, and queue depth
- [ ] At least 3 alerting rules fire correctly when thresholds are breached
- [ ] Write PromQL queries from scratch for new metrics
- [ ] Define SLOs and calculate error budgets from memory
- [ ] Diagnose a simulated failure using only monitoring dashboards (no kubectl)

---

## Module 10: Security Hardening (Weeks 16-17)

**Link forward**: "This completes the production-readiness story"

**AWS SAA Alignment**: Design Secure Architectures

### Labs & Exercises

| Lab | Exercise | Concept | Artifact |
|-----|----------|---------|----------|
| Lab 0 | Threat modeling | Threat modeling | FlowForge threat model: assets, threats, mitigations |
| Lab 1 | 1a: IAM hardening | IAM hardening | Tightened IAM policies, CloudTrail enabled, IAM Access Analyzer |
| Lab 1 | 1b: Secrets management | Secrets management | Secrets migrated to AWS Secrets Manager, Terraform + K8s integration |
| Lab 2 | 2a: Container security | Container security | trivy scan, distroless/scratch images, read-only rootfs, dropped capabilities |
| Lab 2 | 2b: K8s network policies | K8s network policies | NetworkPolicies: api->PG, worker->PG allowed; default deny all |
| Lab 3 | 3a: K8s RBAC | K8s RBAC | ServiceAccounts, Roles, RoleBindings with least privilege |
| Lab 3 | 3b: Encryption | Encryption at rest & in transit | RDS encryption, S3 encryption, TLS verification between services |
| Lab 4 | 4a: Security scanning in CI/CD | Security scanning in CI/CD | trivy, gosec, govulncheck in GitHub Actions; fail on HIGH severity |
| Lab 4 | 4b: Incident response runbook | Incident response runbook | Runbooks for compromised key, unauthorized access, container escape |
| Lab 5 | Security audit | Security audit | Full audit: IAM, networking, secrets, containers, CI/CD |

### Exit Gate Checkpoints

- [ ] All IAM policies follow least privilege (verified by IAM Access Analyzer)
- [ ] No secrets in code, environment variables, or Git history
- [ ] Container images have no CRITICAL vulnerabilities
- [ ] K8s NetworkPolicies enforce service-to-service communication rules
- [ ] TLS everywhere (verified by openssl s_client or curl -v)
- [ ] CI/CD pipeline fails on security vulnerabilities
- [ ] Produce a threat model for a new system from scratch
- [ ] Security audit document has zero unaddressed HIGH/CRITICAL findings

---

## Capstone: Production-Grade Deployment (Week 17)

This is not a tutorial -- it is a test. You receive requirements only, no guidance.

### Deliverables

| Deliverable | Acceptance Criteria |
|------------|-------------------|
| **Infrastructure (Terraform)** | All AWS resources as code. `terraform apply` from zero in < 15 min. `terraform destroy` cleans everything |
| **Containerization (Docker)** | Multi-stage builds, < 30MB images, non-root, no CRITICAL vulnerabilities |
| **CI/CD (GitHub Actions)** | Push to main: test, lint, scan, build, push, deploy to staging. Manual production promotion. Terraform plan on PR, apply on merge |
| **Orchestration (Kubernetes)** | Deployments, Services, ConfigMaps, Secrets, Ingress, NetworkPolicies. Rolling updates with zero downtime |
| **Monitoring (Prometheus + Grafana)** | Dashboard with request rate, error rate, latency, queue depth. Alerts. SLO dashboard |
| **Security** | Least-privilege IAM, Secrets Manager, TLS everywhere, container scanning, K8s RBAC + NetworkPolicies, incident response runbook |
| **Documentation** | Architecture diagram, deployment runbook, monitoring guide, security audit, README |

### Exit Gate

- [ ] A stranger can clone the repo, run terraform apply and GitHub Actions, and have FlowForge running in production
- [ ] Break something and demonstrate detection and recovery using only monitoring and runbooks
- [ ] Present architecture decisions and trade-offs as if in a job interview
- [ ] Security audit produces zero unaddressed HIGH/CRITICAL findings
