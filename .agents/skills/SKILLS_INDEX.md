# DevOps Course -- Socratic Mentor Skills Index

> **11 Socratic mentor skills** installed as part of the DevOps & Cloud Engineering course.
> Each skill provides lab-specific guidance, progressive hints, documentation links, common
> mistakes maps, and architecture thinking prompts for its module. Skills never give direct
> answers -- they guide through questions.

---

| # | Skill Name | Description | Path (relative to workspace root) | Module / Section |
|---|-----------|-------------|-----------------------------------|------------------|
| 1 | devops-m01-linux-mentor | Socratic mentor for Module 01 -- Linux Deep Dive. Guides labs on FHS, permissions, processes, systemd, bash scripting, SSH, and broken-server debugging. | `.cursor/skills/devops-m01-linux-mentor/SKILL.md` | Module 01: Linux Deep Dive |
| 2 | devops-m02-networking-mentor | Socratic mentor for Module 02 -- Networking Fundamentals. Guides labs on OSI/TCP-IP, subnets, DNS, HTTP, ports, firewalls, routing, TLS, and broken-network debugging. | `.cursor/skills/devops-m02-networking-mentor/SKILL.md` | Module 02: Networking Fundamentals |
| 3 | devops-m03-goapp-mentor | Socratic mentor for Module 03 -- Building FlowForge in Go. Guides labs on REST API design, Go HTTP servers, PostgreSQL, migrations, worker pattern, 12-Factor config, Python scripts, logging, and testing. | `.cursor/skills/devops-m03-goapp-mentor/SKILL.md` | Module 03: Building FlowForge in Go |
| 4 | devops-m04-docker-mentor | Socratic mentor for Module 04 -- Docker and Containerization. Guides labs on containers vs VMs, Dockerfiles, layers/caching, multi-stage builds, networking, volumes, Compose, security, and debugging. | `.cursor/skills/devops-m04-docker-mentor/SKILL.md` | Module 04: Docker & Containerization |
| 5 | devops-m05-aws-mentor | Socratic mentor for Module 05 -- AWS Fundamentals. Guides labs on account setup, IAM, VPC networking, security groups/NACLs, EC2, RDS, S3, ECR, manual deployment, and cost cleanup. | `.cursor/skills/devops-m05-aws-mentor/SKILL.md` | Module 05: AWS Fundamentals |
| 6 | devops-m06-terraform-mentor | Socratic mentor for Module 06 -- Terraform. Guides labs on HCL basics, resources/data sources, variables/outputs, state management, remote state, modules, workspaces, full recreation, and debugging. | `.cursor/skills/devops-m06-terraform-mentor/SKILL.md` | Module 06: Terraform |
| 7 | devops-m07-cicd-mentor | Socratic mentor for Module 07 -- CI/CD with GitHub Actions. Guides labs on workflows, Docker build/push, secrets/OIDC, quality gates, multi-environment deployment, branch strategies, Terraform in CI, and broken pipelines. | `.cursor/skills/devops-m07-cicd-mentor/SKILL.md` | Module 07: CI/CD with GitHub Actions |
| 8 | devops-m08-kubernetes-mentor | Socratic mentor for Module 08 -- Kubernetes. Guides labs on K8s architecture, Kind, Pods, Deployments, Services, ConfigMaps, Secrets, Namespaces, Ingress, EKS, and broken-K8s debugging. | `.cursor/skills/devops-m08-kubernetes-mentor/SKILL.md` | Module 08: Kubernetes |
| 9 | devops-m09-monitoring-mentor | Socratic mentor for Module 09 -- Monitoring and Observability. Guides labs on instrumentation, custom metrics, Prometheus, PromQL, Grafana, alerting, SLOs/SLIs, Loki logging, and failure simulation. | `.cursor/skills/devops-m09-monitoring-mentor/SKILL.md` | Module 09: Monitoring & Observability |
| 10 | devops-m10-security-mentor | Socratic mentor for Module 10 -- Security Hardening. Guides labs on threat modeling, IAM hardening, secrets management, container security, NetworkPolicies, RBAC, encryption, CI scanning, incident response, and audits. | `.cursor/skills/devops-m10-security-mentor/SKILL.md` | Module 10: Security Hardening |
| 11 | devops-capstone-mentor | Socratic mentor for the Capstone -- Production-Grade Deployment. Provides even less guidance than module mentors: only clarifies requirements, asks architecture questions, and validates completed work. Never gives implementation hints. | `.cursor/skills/devops-capstone-mentor/SKILL.md` | Capstone: Production-Grade Deployment |

---

## How Skills Work

Each skill directory contains:

```
.cursor/skills/devops-mXX-TOPIC-mentor/
  SKILL.md                    # Socratic mentor rules, lab guidance, hints, docs links
  references/
    answer-key.md             # Complete solutions (used internally, never revealed)
```

**Teaching approach** (enforced by `AGENTS.md` globally):

1. **Level 1 -- Reframe as question**: Guide the student toward the answer with a question.
2. **Level 2 -- Point to documentation**: Direct to a specific doc URL and section.
3. **Level 3 -- Narrow hint**: Give a specific hint without the full answer.
4. **Direct answer**: Only when explicitly requested or after all 3 hint levels exhausted.

## Related Files

- `AGENTS.md` (workspace root) -- Global Socratic teaching rules enforced across all modules
- `curriculum/overview.md` -- Full curriculum map with exercise tables and time estimates
- `README.md` (workspace root) -- Course overview, prerequisites, and getting started guide
