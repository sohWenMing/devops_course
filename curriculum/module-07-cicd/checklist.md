# Module 7: CI/CD with GitHub Actions -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 8.  
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

## CI vs CD Concepts

- [ ] I can explain the difference between continuous integration, continuous delivery, and continuous deployment
- [ ] I can draw a pipeline diagram showing every stage from git push to production deployment
- [ ] I can identify which stages are CI and which are CD in a given pipeline
- [ ] I can explain the fail-fast principle and why pipeline stages are ordered by speed

---

## GitHub Actions Basics (Lab 01, Exercise 1a)

- [ ] I can write a GitHub Actions workflow from scratch for a Go project (triggers, jobs, steps)
- [ ] I can explain the five core components: triggers, jobs, steps, runners, and actions
- [ ] I can configure triggers for push, pull_request, workflow_dispatch, and schedule
- [ ] I can use `paths` filters to trigger workflows only when specific files change
- [ ] I can read workflow run logs in the GitHub UI and identify which step failed
- [ ] I can write a workflow from scratch for a DIFFERENT project (e.g., Python, Node) without referencing my Go workflow

---

## Docker Image Build & Push (Lab 01, Exercise 1b)

- [ ] I can add a Docker build job that depends on tests passing (`needs` keyword)
- [ ] I can tag Docker images with the git commit SHA (`${{ github.sha }}`)
- [ ] I can push Docker images to ECR from a GitHub Actions workflow
- [ ] I can explain why git SHA tagging is better than `latest` for CI/CD
- [ ] I can add a new service to the build pipeline from memory

---

## Secrets Management (Lab 02, Exercise 2a)

- [ ] I can store secrets in GitHub and reference them in workflows
- [ ] I can verify that secrets are masked in workflow logs
- [ ] I can configure OIDC federation between GitHub Actions and AWS
- [ ] I can explain the OIDC flow: GitHub token → AWS STS → temporary credentials
- [ ] I can explain why OIDC is preferable to static access keys
- [ ] I can restrict the OIDC role trust policy to a specific repository and branch

---

## Quality Gates (Lab 02, Exercise 2b)

- [ ] I can add `golangci-lint` to a CI pipeline and fix lint issues it finds
- [ ] I can add `trivy` image scanning that fails on HIGH/CRITICAL vulnerabilities
- [ ] I can add Go security scanning (gosec or govulncheck) to the pipeline
- [ ] I can enforce a test coverage threshold (>70%) in the pipeline
- [ ] I can add a NEW quality gate from scratch (e.g., go vet, staticcheck) without referencing existing gates
- [ ] I can configure branch protection rules that require CI to pass before merging

---

## Multi-Environment Deployment (Lab 03, Exercise 3a)

- [ ] I can configure GitHub Environments for staging and production
- [ ] I can set up auto-deploy to staging on merge to `main`
- [ ] I can require manual approval for production deployments
- [ ] I can use environment-specific secrets and variables
- [ ] I can add a new environment (e.g., QA) to the pipeline from scratch
- [ ] I can explain environment promotion: code → staging → approval → production

---

## Branch Strategies (Lab 03, Exercise 3b)

- [ ] I can implement trunk-based development with short-lived feature branches
- [ ] I can configure PRs to trigger CI only (not deployment)
- [ ] I can configure merges to `main` to trigger the full CI/CD pipeline
- [ ] I can explain trunk-based vs Gitflow vs GitHub Flow and when to use each
- [ ] I can set up branch protection rules (required reviews, required CI, no direct push)
- [ ] I can handle merge conflicts between feature branches

---

## Terraform in CI/CD (Lab 04, Exercise 4)

- [ ] I can add `terraform plan` on PR that posts plan output as a PR comment
- [ ] I can add `terraform apply` on merge to `main` with proper safeguards
- [ ] I can explain why a fresh plan is generated on merge (not reusing the PR plan)
- [ ] I can explain what happens if two infrastructure PRs merge simultaneously
- [ ] I can use concurrency groups to prevent concurrent Terraform applies
- [ ] I can explain why `terraform apply` in CI requires careful safeguards

---

## Debugging Pipelines (Lab 05, Exercise 5)

- [ ] I can diagnose a "secret not available" error from workflow logs
- [ ] I can diagnose a Docker build context error from workflow logs
- [ ] I can diagnose a stale image tag deployment issue from workflow logs
- [ ] I can explain my debugging methodology: read error → check step → check inputs → check outputs
- [ ] Given a NEW failed workflow I've never seen, I can diagnose the issue from logs alone in under 10 minutes
- [ ] I can write an incident report for a pipeline failure (symptom, root cause, fix, prevention)

---

## Integration & Architecture Thinking

- [ ] Push to `main` automatically: tests, lints, builds images, pushes to ECR, deploys to staging
- [ ] Production deployment requires manual approval via GitHub Environments
- [ ] Terraform changes are planned on PR (posted as comment) and applied on merge
- [ ] I can read workflow YAML and predict execution order, including parallel jobs and conditional steps
- [ ] I can write a complete GitHub Actions workflow from scratch for a different project in under 30 minutes
- [ ] I can explain how CI/CD connects to: Docker (Module 4), AWS (Module 5), and Terraform (Module 6)
- [ ] I can explain what Module 8 (Kubernetes) will add to this pipeline

---

## Final Verification

Before moving to Module 8, verify your complete pipeline:

1. **Push a Go code change** → tests run → lint runs → images build → push to ECR → staging deploys
2. **Open a PR with Terraform changes** → plan appears as comment → merge → apply runs
3. **Approve production deployment** → production receives the update
4. **Break something deliberately** → diagnose from logs → fix → pipeline goes green

If ALL four scenarios work end-to-end, you're ready for Module 8: Kubernetes.
