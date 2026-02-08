# Capstone Self-Grading Rubric

Use this rubric to honestly assess your capstone submission. For each deliverable, select the level that best describes your work. Be honest -- this rubric is for your growth, not a grade.

---

## Scoring Levels

| Level | Points | Description |
|---|---|---|
| **Exceeds Expectations** | 4 | Goes beyond requirements. Production-ready with thoughtful extras. Demonstrates deep understanding |
| **Meets Expectations** | 3 | All acceptance criteria met. Solid implementation. Could be handed off to a team |
| **Needs Improvement** | 2 | Partially complete. Core functionality works but gaps exist. Would need fixes before production |
| **Not Attempted** | 0 | Deliverable missing or fundamentally broken |

---

## Deliverable 1: Infrastructure (Terraform)

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | All acceptance criteria met. Multiple environment support (dev/staging/prod) with workspace or directory separation. Terraform validates with zero warnings. Modules are reusable and well-documented with README files. State versioning enabled. Plan output is clean and predictable. Includes cost estimation with `infracost` or similar. Resources have meaningful names and comprehensive tags. Destroy and recreate is fully idempotent |
| **Meets Expectations (3)** | All AWS resources defined as Terraform. `terraform apply` creates working infrastructure from zero. `terraform destroy` cleanly removes everything. Infrastructure modularized into logical modules. Remote state in S3 with DynamoDB locking. Variables parameterize environment-specific values. Sensitive values marked appropriately |
| **Needs Improvement (2)** | Terraform code exists but has issues: some resources created manually, modules are incomplete, state is local, hardcoded values remain, or destroy leaves orphaned resources. Infrastructure works but wouldn't survive a fresh `terraform apply` from zero |
| **Not Attempted (0)** | No Terraform code, or code doesn't apply successfully |

**Your score**: ___/4

---

## Deliverable 2: Containerization (Docker)

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | All acceptance criteria met. Images are extremely optimized (under 15MB using scratch or distroless). Build times are fast due to excellent layer caching strategy. Docker Compose includes production-like health checks with proper intervals and retries. Development compose includes debugging tools. Dockerfile comments explain non-obvious decisions. Images are signed or have SBOM |
| **Meets Expectations (3)** | Multi-stage Dockerfiles for both services. Final images under 30MB. Non-root user. No CRITICAL vulnerabilities from trivy. `.dockerignore` present. Health check endpoints work. Docker Compose available for local development |
| **Needs Improvement (2)** | Dockerfiles exist but are not optimized: single-stage builds, large images (>100MB), running as root, trivy shows CRITICAL vulnerabilities, or missing `.dockerignore`. Containers run but don't follow best practices |
| **Not Attempted (0)** | No Dockerfiles, or images don't build successfully |

**Your score**: ___/4

---

## Deliverable 3: CI/CD (GitHub Actions)

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | All acceptance criteria met. Pipeline includes matrix builds for multiple Go versions or architectures. Cache steps reduce build time significantly. Status badges in README. Deployment includes rollback strategy. Terraform plan diff is posted as a collapsible PR comment with summary. Notifications configured (Slack, email). Pipeline runs in under 10 minutes end-to-end. Reusable workflow components |
| **Meets Expectations (3)** | Push to main triggers full pipeline: test, lint, scan, build, push, deploy to staging. Production requires manual approval. Terraform plan on PR, apply on merge. OIDC for AWS auth. Quality gates: tests >70% coverage, linting, trivy, gosec/govulncheck. Fails on HIGH/CRITICAL. Git SHA image tags. Concurrency groups for Terraform |
| **Needs Improvement (2)** | Pipeline exists but incomplete: missing security scanning, no environment separation, static AWS credentials instead of OIDC, no Terraform integration, or quality gates that don't actually fail the pipeline. Deployment works but isn't fully automated |
| **Not Attempted (0)** | No GitHub Actions workflows, or workflows don't run successfully |

**Your score**: ___/4

---

## Deliverable 4: Orchestration (Kubernetes)

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | All acceptance criteria met. Horizontal Pod Autoscaler configured for api-service based on CPU/custom metrics. Pod Disruption Budgets ensure availability during node maintenance. Anti-affinity rules spread Pods across nodes. Readiness and liveness probes are tuned (not just defaults). Helm charts or Kustomize for environment-specific overlays. Resource quotas per namespace |
| **Meets Expectations (3)** | Deployments for api-service and worker-service with appropriate replica counts. Services for internal and external access. ConfigMaps for non-sensitive config. Secrets via External Secrets Operator. Ingress with TLS. NetworkPolicies enforced. Rolling updates configured (maxSurge, maxUnavailable). Resource requests and limits set. Dedicated ServiceAccounts with RBAC |
| **Needs Improvement (2)** | K8s manifests exist but incomplete: missing NetworkPolicies, using default ServiceAccount, no resource limits, Secrets stored as plain K8s Secrets (not ESO), no TLS on Ingress, or rolling update strategy not configured. Services run but aren't production-ready |
| **Not Attempted (0)** | No Kubernetes manifests, or manifests don't deploy successfully |

**Your score**: ___/4

---

## Deliverable 5: Monitoring (Prometheus + Grafana)

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | All acceptance criteria met. Custom recording rules for frequently used PromQL expressions. Dashboard uses template variables for filtering by namespace/service. Grafana dashboard is exported as JSON and version-controlled. Alerting includes escalation paths (warning → critical → page). SLO dashboard includes burn rate alerts. Runbook links in alert annotations. Traces integrated (OpenTelemetry) alongside metrics and logs |
| **Meets Expectations (3)** | Both services instrumented with custom metrics. Prometheus deployed and scraping all targets (all UP). Grafana dashboard with request rate, error rate, latency percentiles, queue depth panels. Three alerting rules configured and functional. Alertmanager with at least one notification route. SLO dashboard with availability SLI and error budget. Structured logging queryable in Grafana |
| **Needs Improvement (2)** | Monitoring partially implemented: Prometheus deployed but not all targets UP, dashboard exists but missing key panels, alerting rules defined but not tested/firing, no SLO dashboard, or no log aggregation. Monitoring exists but wouldn't catch a real production incident |
| **Not Attempted (0)** | No monitoring stack deployed, or Prometheus/Grafana not functional |

**Your score**: ___/4

---

## Deliverable 6: Security

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | All acceptance criteria met. Automated secret rotation with zero-downtime application restart. Pod Security Standards (Restricted) enforced. OPA/Gatekeeper or Kyverno policies for admission control. CIS Kubernetes Benchmark audit performed. SIEM integration for centralized security monitoring. Penetration test performed and documented. Supply chain security (image signing, SBOM) |
| **Meets Expectations (3)** | IAM follows least privilege (Access Analyzer clean). All secrets in Secrets Manager (none in code/env/Git). No CRITICAL trivy findings. NetworkPolicies with default deny. RBAC with dedicated ServiceAccounts. TLS everywhere. CI/CD fails on HIGH/CRITICAL findings. Three incident response runbooks. Threat model document |
| **Needs Improvement (2)** | Security controls partially implemented: some IAM policies are too broad, some secrets not yet migrated, NetworkPolicies exist but don't cover all paths, TLS missing on some connections, or CI scanning doesn't actually block deployment. Security exists but has notable gaps |
| **Not Attempted (0)** | No security controls beyond defaults, or security audit reveals multiple CRITICAL findings |

**Your score**: ___/4

---

## Deliverable 7: Documentation

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | All acceptance criteria met. Architecture diagram is detailed and professionally formatted (generated from code, e.g., Mermaid). ADRs (Architecture Decision Records) document key decisions with context and consequences. Monitoring guide includes alert playbooks with specific commands. Documentation is tested -- someone else followed it successfully. Changelog maintained. Contributing guide with PR template |
| **Meets Expectations (3)** | Architecture diagram shows all components and interactions. Deployment runbook allows a stranger to deploy. Monitoring guide explains dashboards and alert responses. Security audit report documents findings and remediation. README covers overview, prerequisites, quick start, architecture. All documentation matches the actual deployed system |
| **Needs Improvement (2)** | Documentation exists but has gaps: architecture diagram is outdated or incomplete, deployment runbook has missing steps, monitoring guide doesn't explain how to respond to alerts, or README doesn't cover enough to get started. A stranger would need to ask questions |
| **Not Attempted (0)** | No documentation beyond default boilerplate, or documentation is fundamentally inaccurate |

**Your score**: ___/4

---

## Exit Gate Assessment

### Stranger Test

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | Stranger deploys successfully on first attempt with zero questions. Documentation is so clear that setup takes under 30 minutes. Includes troubleshooting section for common issues |
| **Meets Expectations (3)** | Stranger can deploy by following README. May need minor clarification but all steps are documented. System is fully functional after deployment |
| **Needs Improvement (2)** | Stranger can partially deploy but gets stuck at one or more steps. Some commands fail or are missing from documentation |
| **Not Attempted (0)** | Stranger cannot deploy the system from the documentation alone |

**Your score**: ___/4

### Break-and-Recover

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | All three scenarios completed with detailed incident reports. Detection time under 2 minutes for each. Recovery is automated or semi-automated. Improvements implemented, not just documented. Post-mortem includes timeline, impact assessment, and prevention plan |
| **Meets Expectations (3)** | All three scenarios completed (pod failure, traffic spike, secret rotation). Monitoring detects each issue. Recovery demonstrated. Incident reports written with detection, diagnosis, root cause, recovery |
| **Needs Improvement (2)** | One or two scenarios completed but incident reports are shallow. Detection relies on kubectl rather than monitoring. Recovery steps not documented |
| **Not Attempted (0)** | No break-and-recover scenarios attempted |

**Your score**: ___/4

### Interview Presentation

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | Can articulate every architectural decision with clear reasoning. Discusses trade-offs with specific alternatives considered. Includes cost breakdown with optimization suggestions. Demonstrates knowledge of scaling strategies. Could confidently present in a real interview |
| **Meets Expectations (3)** | Can explain architecture decisions and trade-offs. Has a cost estimate. Knows what they'd change at scale. Can answer "why" for major choices |
| **Needs Improvement (2)** | Can describe what was built but struggles to explain why. Trade-off analysis is shallow. No cost estimate |
| **Not Attempted (0)** | No presentation prepared |

**Your score**: ___/4

### Security Audit

| Level | Criteria |
|---|---|
| **Exceeds Expectations (4)** | Zero findings of any severity. Automated compliance checks in CI. CIS benchmarks for K8s evaluated. Evidence of regular rotation and access review |
| **Meets Expectations (3)** | Zero unaddressed HIGH/CRITICAL findings. All tools run (IAM Analyzer, trivy, NetworkPolicy tests, TLS verification, CloudTrail review, Git history scan). Accepted risks documented with justification |
| **Needs Improvement (2)** | Audit performed but HIGH findings remain unaddressed. Not all audit areas covered. Documentation incomplete |
| **Not Attempted (0)** | No security audit performed |

**Your score**: ___/4

---

## Score Summary

| Category | Max Points | Your Score |
|---|---|---|
| **Deliverable 1**: Infrastructure (Terraform) | 4 | ___  |
| **Deliverable 2**: Containerization (Docker) | 4 | ___  |
| **Deliverable 3**: CI/CD (GitHub Actions) | 4 | ___  |
| **Deliverable 4**: Orchestration (Kubernetes) | 4 | ___  |
| **Deliverable 5**: Monitoring (Prometheus + Grafana) | 4 | ___  |
| **Deliverable 6**: Security | 4 | ___  |
| **Deliverable 7**: Documentation | 4 | ___  |
| **Exit Gate**: Stranger Test | 4 | ___  |
| **Exit Gate**: Break-and-Recover | 4 | ___  |
| **Exit Gate**: Interview Presentation | 4 | ___  |
| **Exit Gate**: Security Audit | 4 | ___  |
| **TOTAL** | **44** | **___** |

---

## Score Interpretation

| Total Score | Level | What It Means |
|---|---|---|
| **40-44** | **Production Engineer** | You've built a system that would pass a real production readiness review. You could confidently discuss every decision in an interview. You're ready for a DevOps/Cloud engineering role |
| **33-39** | **Capstone Complete** | You meet all core requirements. Your system works, is automated, monitored, and secured. Minor polish would make it exceptional. You have strong fundamentals |
| **22-32** | **Almost There** | Core components work but gaps exist. Review the areas where you scored "Needs Improvement" and address them. Revisit the corresponding module labs if needed |
| **11-21** | **Needs More Work** | Significant gaps remain. Return to the modules for areas scoring below 2 and redo the labs. The capstone requires all 10 modules' knowledge working together |
| **0-10** | **Start Over** | Major deliverables are missing. Go back through the modules systematically before attempting the capstone again |

---

## After Scoring

1. **Be honest with yourself.** Inflating scores only hurts your learning.
2. **Focus on "Needs Improvement" areas.** These are your growth opportunities.
3. **Revisit specific modules.** The [cross-reference table in the requirements](./README.md#module-cross-reference) tells you exactly which module to review.
4. **Iterate.** The capstone isn't meant to be perfect on the first try. Improve, re-score, repeat.
5. **Celebrate what works.** Every "Meets Expectations" represents real, applicable knowledge.
