# DevOps and Cloud Engineering: Project-Based Course

A hands-on, project-based DevOps course that takes you from bare Linux fundamentals through to a fully automated, monitored, and secured Kubernetes deployment on AWS.

---

## What This Course Is

This is a **10-module + capstone** course designed to build real DevOps engineering skills through a single evolving project. Every concept is taught through hands-on labs that produce tangible artifacts, and every module includes debugging challenges with intentionally broken configurations.

The course emphasizes four AI-proof pillars that make you irreplaceable:

- **Architecture thinking** -- knowing *why* you choose one design over another
- **Debugging under pressure** -- diagnosing failures across distributed systems
- **Security instinct** -- threat modeling before writing a single line of code
- **Decision frameworks** -- when to use ECS vs EKS, Fargate vs EC2, monolith vs microservices

This is not a copy-paste tutorial. You will fail, debug, and understand.

---

## Who This Course Is For

A **junior developer transitioning to DevOps/Cloud engineering** with:

- OutSystems background and moderate Go experience
- Basic Linux familiarity (command line, file editing)
- Zero cloud/AWS experience
- An Ubuntu machine ready for hands-on work

---

## Prerequisites

- **Ubuntu machine** (bare metal, VM, or WSL2) -- this is your primary working environment
- **Basic programming knowledge** (you can read and write code, understand functions, loops, data structures)
- **GitHub account** (free tier is fine)
- **AWS account** (free tier -- the course is designed to stay within free-tier limits, estimated $5-20/month if careful)
- **Willingness to be stuck** -- the Socratic teaching method means you'll work through problems, not be handed solutions

---

## The Golden Thread: FlowForge

One application -- **FlowForge** -- evolves through every module, so each concept builds on the last:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **api-service** | Go | REST API for task management |
| **worker-service** | Go | Background processor polling a PostgreSQL queue |
| **PostgreSQL** | Database | Persistent storage |
| **Python scripts** | Python | Automation tooling, health checks, deployment helpers |

By the end of the course, FlowForge will be a fully containerized, infrastructure-as-code deployed, CI/CD automated, Kubernetes orchestrated, monitored, and security-hardened production application.

---

## Module Progression (~17 weeks at 10-15 hrs/week)

| # | Module | Topics | Time Estimate |
|---|--------|--------|---------------|
| 1 | **Linux Deep Dive** | File system, permissions, processes, systemd, bash scripting, SSH | Weeks 1-2 |
| 2 | **Networking Fundamentals** | OSI model, TCP/IP, DNS, HTTP, firewalls, routing, TLS | Weeks 2-3 |
| 3 | **Building FlowForge in Go** | REST APIs, PostgreSQL, worker pattern, 12-factor, testing | Weeks 4-5 |
| 4 | **Docker & Containerization** | Dockerfiles, multi-stage builds, Compose, networking, security | Weeks 6-7 |
| 5 | **AWS Fundamentals** | IAM, VPC, EC2, RDS, S3, ECR, manual deployment | Weeks 8-9 |
| 6 | **Terraform** | HCL, resources, state, modules, workspaces, full IaC | Weeks 10-11 |
| 7 | **CI/CD with GitHub Actions** | Pipelines, secrets, multi-env, Terraform in CI | Weeks 11-12 |
| 8 | **Kubernetes** | Architecture, Pods, Deployments, Services, Ingress, EKS | Weeks 13-14 |
| 9 | **Monitoring & Observability** | Prometheus, Grafana, PromQL, alerting, SLOs, Loki | Weeks 15-16 |
| 10 | **Security Hardening** | Threat modeling, IAM, secrets management, NetworkPolicies, RBAC | Weeks 16-17 |
| C | **Capstone** | Full production deployment -- requirements only, no guidance | Week 17 |

Each module has an **exit gate** -- a set of checkpoints you must pass before moving on. No skipping.

---

## AWS SAA Certification Alignment

This course aligns with the AWS Solutions Architect Associate (SAA) exam domains:

- **Design Resilient Architectures**: Modules 2, 5
- **Design High-Performing Architectures**: Modules 5, 6
- **Design Secure Architectures**: Modules 5, 10
- **Design Cost-Optimized Architectures**: Modules 6, 7, 8
- **Specify Secure Applications and Architectures**: Modules 5, 6

---

## Getting Started

1. **Read the curriculum overview**: Start with `curriculum/overview.md` for the full map of modules, labs, and exercises.

2. **Understand the teaching method**: This course uses **Socratic teaching**. The AI mentor will guide you with questions and hints, not hand you answers. See `AGENTS.md` for the rules.

3. **Start Module 1**: Open `curriculum/module-01-linux/README.md` to begin with Linux fundamentals. Work through each lab sequentially.

4. **Complete exit gates**: Each module ends with a checklist (`checklist.md`). You must honestly pass every checkpoint before moving to the next module.

5. **Use the mentor**: When you're stuck on a lab, ask for help. The AI mentor will guide you through a progressive hint system -- but you'll do the work.

---

## Course Structure

```
devops_course/
  AGENTS.md                          # Global Socratic teaching rules
  README.md                          # This file -- course overview
  PROGRESS.md                        # Agent relay progress tracker
  curriculum/
    overview.md                      # Full curriculum map with time estimates
    module-01-linux/                 # Module 1: Linux Deep Dive
    module-02-networking/            # Module 2: Networking Fundamentals
    module-03-go-app/                # Module 3: Building FlowForge in Go
    module-04-docker/                # Module 4: Docker & Containerization
    module-05-aws/                   # Module 5: AWS Fundamentals
    module-06-terraform/             # Module 6: Terraform
    module-07-cicd/                  # Module 7: CI/CD with GitHub Actions
    module-08-kubernetes/            # Module 8: Kubernetes
    module-09-monitoring/            # Module 9: Monitoring & Observability
    module-10-security/              # Module 10: Security Hardening
    capstone/                        # Capstone: Full Production Deployment
  project/                           # The evolving FlowForge app (starts empty)
    api-service/                     # Go REST API
    worker-service/                  # Go background worker
    scripts/                         # Python automation scripts
    infra/                           # Terraform infrastructure code
    k8s/                             # Kubernetes manifests
    .github/workflows/               # GitHub Actions CI/CD pipelines
```

---

## Cost Estimate

This course is designed to be **AWS free-tier friendly**:

- EC2: t2.micro/t3.micro (free tier: 750 hrs/month)
- RDS: db.t3.micro (free tier: 750 hrs/month)
- S3: 5GB free
- ECR: 500MB free
- EKS: Control plane ~$0.10/hr (use sparingly; Kind locally for most work)
- **Estimated total**: $5-20/month if careful with EKS usage and cleanup

Python cleanup scripts are provided to tear down resources after each session.
