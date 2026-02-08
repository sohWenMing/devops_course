# Module 7: CI/CD with GitHub Actions

> **Time estimate**: 1.5-2 weeks  
> **Prerequisites**: Complete Modules 1-6 (Linux, Networking, Go App, Docker, AWS, Terraform), GitHub account, FlowForge services containerized and infrastructure-as-code ready  
> **Link forward**: "Kubernetes deployment will be the target of this pipeline -- everything you automate here feeds directly into your K8s manifests in Module 8"  
> **Link back**: "In Module 4, you built Docker images manually. In Module 5, you deployed to AWS by hand. In Module 6, you codified infrastructure with Terraform but still ran `terraform apply` from your laptop. Now you automate ALL of it -- every push triggers tests, builds, scans, and deployments without you touching a terminal."

---

## Why This Module Matters for DevOps

Think about what you did in Modules 4-6. You:

1. Wrote Dockerfiles and ran `docker build` on your laptop
2. Tagged images and ran `docker push` to ECR by hand
3. SSHed into EC2 and ran `docker pull` + `docker run` manually
4. Ran `terraform plan` and `terraform apply` from your terminal
5. Had to remember the right order of operations every time

What happens when you go on vacation? What happens when a new team member joins? What happens when you need to deploy at 2am because of a critical bug? The answer with manual processes is: chaos, inconsistency, and human error.

**CI/CD (Continuous Integration / Continuous Delivery / Continuous Deployment)** eliminates this. Your pipeline becomes the single source of truth for how code gets from a developer's laptop to production. Every change follows the same path: test, lint, scan, build, deploy. No shortcuts, no "I'll test it later," no "it works on my machine."

This is the automation layer that ties everything together. Docker images get built automatically. Terraform plans get posted as PR comments for review. Deployments happen automatically to staging and require manual approval for production. And when something breaks, the pipeline tells you exactly where and why.

> **AWS SAA Alignment**: The SAA exam tests CI/CD concepts through questions about CodePipeline, CodeBuild, CodeDeploy, and deployment strategies (blue/green, canary, rolling). While we use GitHub Actions (the industry standard), every concept maps directly: workflows = pipelines, jobs = build projects, environments = deployment groups. Understanding CI/CD deeply makes all the AWS deployment questions straightforward. The exam also tests OIDC federation for cross-account access -- exactly what we configure in Lab 2a.

---

## Table of Contents

1. [CI vs CD: The Automation Spectrum](#1-ci-vs-cd-the-automation-spectrum)
2. [GitHub Actions Fundamentals](#2-github-actions-fundamentals)
3. [Build Pipelines](#3-build-pipelines)
4. [Docker Image Building & Tagging Strategies](#4-docker-image-building--tagging-strategies)
5. [Secrets Management in CI](#5-secrets-management-in-ci)
6. [Test Stages & Quality Gates](#6-test-stages--quality-gates)
7. [Multi-Environment Deployment](#7-multi-environment-deployment)
8. [Branch Strategies](#8-branch-strategies)
9. [Terraform in CI/CD](#9-terraform-in-cicd)
10. [Debugging Pipelines](#10-debugging-pipelines)

---

## 1. CI vs CD: The Automation Spectrum

### Continuous Integration (CI)

**Continuous Integration** means every developer's changes are automatically tested and validated when they push code. The "integration" part is key -- you're continuously integrating your changes with everyone else's changes, catching conflicts and bugs early.

CI typically includes:
- **Compile/build** the application
- **Run unit tests** to catch logic errors
- **Run integration tests** to verify components work together
- **Lint** the code for style and potential bugs
- **Security scan** for known vulnerabilities

> **Link back**: Remember in Module 3 when you wrote Go tests and measured coverage? Those tests are the backbone of CI. In Module 4, you built Docker images. CI automates both -- every push triggers `go test` AND `docker build`.

The golden rule of CI: **the build should always be green**. If tests fail, the team stops and fixes them before adding more code. A broken build is everyone's problem.

### Continuous Delivery vs Continuous Deployment

These two terms sound identical but have a critical difference:

**Continuous Delivery**: Every change that passes CI is *ready* to deploy to production, but a human makes the final decision. The deploy button exists; someone must press it.

**Continuous Deployment**: Every change that passes CI is automatically deployed to production. No human approval needed. If the tests pass, it goes live.

Most organizations start with continuous delivery and graduate to continuous deployment as their test suites mature and confidence grows.

For FlowForge, we'll implement:
- **CI**: Automated tests, linting, security scanning on every push
- **CD (Delivery)**: Auto-deploy to staging, manual approval for production

> **Architecture Thinking**: Why not just do continuous deployment to production from day one? What would need to be true about your test suite, monitoring, and rollback capability for you to trust fully automated production deployments? What's the cost of each model -- both in terms of risk and developer velocity?

### The Pipeline Metaphor

Think of a pipeline like a factory assembly line. Code enters one end (git push), passes through quality stations (test, lint, scan, build), and exits as a deployed application. If any station fails, the line stops -- defective code never reaches production.

```
git push → compile → test → lint → security scan → build image → push to registry → deploy staging → (approval) → deploy production
           \___CI (continuous integration)___/      \___________CD (continuous delivery/deployment)___________/
```

Every stage is automated. Every stage has pass/fail criteria. Every failure produces a clear error message.

> **Link forward**: In Module 9 (Monitoring), you'll add a crucial stage that CI/CD alone can't provide: watching what happens AFTER deployment. Even if all tests pass, production behavior might differ. Monitoring closes the feedback loop.

---

## 2. GitHub Actions Fundamentals

### Why GitHub Actions?

GitHub Actions is the most widely adopted CI/CD platform for open-source and many enterprise projects. It's built into GitHub, which eliminates the need for a separate CI server (Jenkins, CircleCI, Travis). The concepts you learn here transfer directly to any CI/CD system -- they all have triggers, jobs, steps, and environments.

### Core Concepts

**Workflow**: A YAML file in `.github/workflows/` that defines an automated process. You can have multiple workflows per repository. Each workflow is triggered by specific events.

**Trigger (Event)**: What causes the workflow to run. Common triggers:
- `push` -- code pushed to a branch
- `pull_request` -- PR opened, updated, or merged
- `schedule` -- cron-based schedule
- `workflow_dispatch` -- manual trigger via the GitHub UI
- `release` -- a new release is published

**Job**: A set of steps that run on the same runner (machine). Jobs run in parallel by default. You can define dependencies between jobs with `needs`.

**Step**: A single task within a job. Each step either runs a shell command or uses a pre-built Action. Steps within a job run sequentially.

**Runner**: The machine that executes the job. GitHub provides hosted runners (Ubuntu, macOS, Windows), or you can self-host runners on your own infrastructure.

**Action**: A reusable unit of code. The GitHub marketplace has thousands of pre-built Actions (checkout code, set up Go, log into Docker registries). You reference them with `uses: owner/repo@version`.

### YAML Syntax

Workflow files are YAML. Here's the anatomy:

```yaml
name: CI Pipeline              # Display name in GitHub UI

on:                            # Trigger(s)
  push:
    branches: [main]           # Only on pushes to main
  pull_request:
    branches: [main]           # Only on PRs targeting main

env:                           # Workflow-level environment variables
  GO_VERSION: '1.21'

jobs:                          # One or more jobs
  test:                        # Job ID (your choice)
    name: Run Tests            # Display name
    runs-on: ubuntu-latest     # Runner type

    steps:                     # Sequential steps
      - name: Checkout code
        uses: actions/checkout@v4    # Pre-built Action

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Run tests
        run: go test ./...           # Shell command
        working-directory: ./api-service

  build:
    name: Build Images
    runs-on: ubuntu-latest
    needs: [test]              # Only runs after 'test' job succeeds
    steps:
      - name: Build Docker image
        run: docker build -t my-app .
```

### Key YAML Features

**Expression syntax**: `${{ }}` evaluates expressions. You can reference:
- `github.sha` -- the commit SHA that triggered the run
- `github.ref` -- the branch or tag ref
- `secrets.MY_SECRET` -- encrypted secrets
- `env.MY_VAR` -- environment variables
- `needs.job_id.outputs.value` -- outputs from previous jobs

**Conditional execution**: `if` controls whether a step or job runs:
```yaml
- name: Deploy to production
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  run: ./deploy.sh
```

**Matrix strategy**: Run the same job with different configurations:
```yaml
strategy:
  matrix:
    go-version: ['1.20', '1.21', '1.22']
```

> **Link back**: Remember YAML from Module 4's docker-compose.yml and Module 6's Terraform backend config? Same format, same rules: indentation matters, lists use `-`, maps use `key: value`. If you're comfortable with docker-compose YAML, you're 80% there with GitHub Actions.

> **Architecture Thinking**: GitHub Actions runs on GitHub-hosted runners by default. What are the security implications of running your CI on someone else's infrastructure? When would you want self-hosted runners? What about network access -- can a GitHub-hosted runner reach your private VPC?

---

## 3. Build Pipelines

### What a Build Pipeline Does

A build pipeline transforms source code into deployable artifacts. For FlowForge, the pipeline:

1. **Compiles** the Go services to verify the code is syntactically valid
2. **Tests** the code to verify behavior is correct
3. **Lints** the code to catch style issues and potential bugs
4. **Security scans** dependencies and Docker images for vulnerabilities
5. **Builds** Docker images as deployment artifacts
6. **Pushes** images to a registry (ECR) for deployment

### Fail Fast Principle

The pipeline should be ordered so the cheapest, fastest checks run first. If a lint check fails in 10 seconds, there's no point spending 5 minutes building a Docker image. This is the **fail fast** principle.

Typical ordering by speed:
1. **Lint** (seconds) -- catches formatting and style issues
2. **Unit tests** (seconds to minutes) -- catches logic errors
3. **Build** (minutes) -- catches compilation errors
4. **Integration tests** (minutes) -- catches component interaction issues
5. **Security scan** (minutes) -- catches known vulnerabilities
6. **Deploy** (minutes) -- the actual delivery

> **Link back**: In Module 3, you wrote unit tests and integration tests for your Go services. In Module 4, you learned that Docker layer caching dramatically speeds up builds. Both optimizations matter in CI -- fast pipelines mean fast feedback, which means developers stay in flow.

### Parallelization

Jobs in GitHub Actions run in parallel by default. Use `needs` to create dependencies. The key insight: **independent tasks should run in parallel**.

```
  ┌─── lint ─────┐
  │               │
push ──┤               ├── build images → deploy
  │               │
  └─── test ─────┘
```

Lint and test don't depend on each other, so they run simultaneously. Build depends on both passing.

> **Architecture Thinking**: What's the trade-off between parallelizing everything (faster pipeline) and running things sequentially (simpler debugging, fewer runner minutes consumed)? Consider cost: each parallel job uses a separate runner. On a free GitHub plan, you have limited minutes. How would you design the pipeline differently for an open-source project vs an enterprise with unlimited runners?

---

## 4. Docker Image Building & Tagging Strategies

### Why Tagging Matters

> **Link back**: In Module 4 Lab 05a, you learned about the danger of the `latest` tag. In CI/CD, tagging becomes even more critical because images flow automatically through the pipeline. If you can't identify which exact code version an image contains, debugging production issues becomes a nightmare.

Every Docker image you push to a registry needs a tag that uniquely identifies it. The tag strategy determines:
- Can you tell which commit produced this image?
- Can you rollback to a known-good version?
- Can you audit which version is running in each environment?

### Common Tagging Strategies

**Git SHA tagging** (recommended for CI):
```bash
docker build -t flowforge/api-service:abc1234 .
# abc1234 is the short git commit SHA
```

Why it works: every commit produces a unique, traceable image. You can always map a running container back to the exact code that built it.

**Semantic versioning** (recommended for releases):
```bash
docker build -t flowforge/api-service:v1.2.3 .
```

Why it works: semantic versions communicate intent. `v1.2.3` → `v1.2.4` means a patch. `v1.2.3` → `v1.3.0` means a new feature. `v1.2.3` → `v2.0.0` means breaking changes.

**Combined approach** (best practice):
```bash
# On every push to main
docker tag flowforge/api-service:${GIT_SHA} flowforge/api-service:latest
docker tag flowforge/api-service:${GIT_SHA} flowforge/api-service:main

# On release
docker tag flowforge/api-service:${GIT_SHA} flowforge/api-service:v1.2.3
```

### The `latest` Tag Problem

`latest` is not special -- it's just a string. Docker doesn't automatically update it. If you push `v1.0` then `v2.0` without explicitly tagging `latest`, it still points to `v1.0`. In CI, always tag with the commit SHA and *also* update `latest` explicitly if you want a "current" pointer.

> **Architecture Thinking**: You're running `flowforge/api-service:latest` in production and need to rollback. What do you rollback TO? You don't know which commit `latest` pointed to before the broken deploy. Now imagine you're running `flowforge/api-service:abc1234` -- you simply deploy `flowforge/api-service:def5678` (the previous commit). This is why immutable, traceable tags matter.

---

## 5. Secrets Management in CI

### The Problem

Your CI/CD pipeline needs credentials to:
- Push Docker images to ECR (AWS credentials)
- Deploy to EC2/EKS (AWS credentials)
- Run Terraform (AWS credentials)
- Access private APIs or databases (API keys, passwords)

These credentials **must not** be in your workflow YAML, your Git history, or your application code. Ever.

> **Link back**: Remember Module 5's IAM discussion about never using root credentials and Module 6's sensitive variable flag for Terraform? The same principle applies here, but the stakes are higher -- CI/CD logs are often visible to the whole team, and a leaked secret in a workflow run is visible in GitHub's UI.

### GitHub Secrets

GitHub Secrets are encrypted environment variables stored at the repository or organization level. They're:
- **Encrypted at rest** using libsodium sealed boxes
- **Masked in logs** -- if a secret value appears in output, GitHub replaces it with `***`
- **Not available in fork PRs** by default (security feature)
- **Set via Settings > Secrets and variables > Actions**

You reference them in workflows:
```yaml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### OIDC Federation: Keyless AWS Auth (Advanced)

GitHub Secrets with static AWS keys work, but they have problems:
- Keys never expire unless you rotate them manually
- Keys are long-lived credentials -- if leaked, they work until revoked
- Key rotation requires updating secrets in every repository

**OIDC (OpenID Connect) federation** is the modern approach. Instead of storing AWS keys, you:

1. Configure AWS to **trust GitHub** as an identity provider
2. Create an IAM role that GitHub Actions can **assume** during a workflow run
3. Each workflow run gets **short-lived, temporary credentials** (valid for ~1 hour)
4. No permanent keys stored anywhere

The flow:
```
GitHub Actions run starts
  → GitHub issues an OIDC token ("I am repo X, branch Y, workflow Z")
  → Workflow calls AWS STS AssumeRoleWithWebIdentity
  → AWS verifies the token against the GitHub OIDC provider
  → AWS returns temporary credentials (1 hour TTL)
  → Workflow uses temporary credentials for AWS operations
```

This is the same pattern AWS uses for cross-account access, EKS service accounts, and many other federated identity scenarios. The SAA exam asks about this.

> **AWS SAA Alignment**: OIDC federation for CI/CD maps directly to SAA exam topics: IAM roles, federated identity, STS AssumeRoleWithWebIdentity, and least-privilege access. Understanding this pattern helps with questions about cross-account access, third-party integrations, and temporary credential management.

> **Architecture Thinking**: Compare static secrets vs OIDC federation. What's the blast radius of each if compromised? With static keys, an attacker has permanent access until you notice and rotate. With OIDC, the attacker needs to be able to trigger YOUR workflow in YOUR repository to get temporary (1-hour) credentials. Which is easier to audit? Which is easier to revoke?

---

## 6. Test Stages & Quality Gates

### What Is a Quality Gate?

A quality gate is a pass/fail check that prevents bad code from progressing through the pipeline. If any gate fails, the pipeline stops and the developer must fix the issue before proceeding.

Quality gates for FlowForge:

### Linting with golangci-lint

`golangci-lint` is a Go linting aggregator that runs dozens of linters in parallel. It catches:
- Unused variables and imports
- Error return values that aren't checked
- Potential nil pointer dereferences
- Style inconsistencies
- Security issues

> **Link back**: This is the automated version of code review. In Module 3, you wrote Go code and (hopefully) reviewed it yourself. Now the machine reviews it for you on every push.

### Security Scanning

Multiple tools target different vulnerability surfaces:

**trivy** (container image scanning): Scans your Docker images for known vulnerabilities in OS packages and application dependencies. You used this in Module 4 Lab 05a.

**gosec** (Go security linting): Analyzes Go source code for common security issues like SQL injection, hardcoded credentials, weak cryptography.

**govulncheck** (Go vulnerability checking): Checks your Go module dependencies against the Go vulnerability database. Unlike `trivy`, it understands your call graph and only reports vulnerabilities in code paths you actually use.

### Test Coverage Thresholds

A coverage threshold ensures that a minimum percentage of your code is exercised by tests. For FlowForge, we set **>70% coverage** as the gate.

> **Link back**: You targeted 70% coverage in Module 3 Lab 05. Now you enforce it -- if someone adds untested code that drops coverage below 70%, the pipeline fails.

```yaml
- name: Run tests with coverage
  run: go test -coverprofile=coverage.out ./...

- name: Check coverage threshold
  run: |
    COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | tr -d '%')
    echo "Coverage: ${COVERAGE}%"
    if (( $(echo "$COVERAGE < 70" | bc -l) )); then
      echo "Coverage ${COVERAGE}% is below 70% threshold"
      exit 1
    fi
```

### Fail Fast

Order quality gates by speed: lint (fast) → test (medium) → build (medium) → security scan (slow). If lint fails, don't waste time on everything else.

> **Architecture Thinking**: What coverage threshold would you pick and why? 100% coverage means testing trivial code (getters, setters). 50% means large untested surface area. 70-80% is industry consensus for "good enough" -- but what matters more than the number is WHICH code is tested. Would you rather have 90% coverage of utility functions or 60% coverage that includes all error handling paths?

---

## 7. Multi-Environment Deployment

### Why Multiple Environments?

Production is sacred. You never deploy untested changes directly to production. Instead, code flows through progressively more production-like environments:

- **Development (dev)**: For active development. May be broken. Auto-deploys on every push.
- **Staging**: Mirror of production. Used for final validation. Auto-deploys on merge to main.
- **Production**: The real thing. Customer-facing. Manual approval required.

> **Link back**: In Module 6 Lab 04, you used Terraform workspaces to manage dev and staging environments with different configurations (smaller instances for dev). Now you automate the deployment to those environments.

### GitHub Environments

GitHub Environments are a feature that lets you:
- Define **deployment targets** (staging, production)
- Require **manual approval** before deploying to certain environments
- Set **environment-specific secrets** (different AWS accounts, different API keys)
- Configure **wait timers** (deploy to production only after staging has been stable for 30 minutes)
- **Limit which branches** can deploy to an environment (only `main` can deploy to production)

```yaml
jobs:
  deploy-staging:
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: ./deploy.sh staging

  deploy-production:
    environment: production    # This environment has approval rules
    needs: [deploy-staging]
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./deploy.sh production
```

When a job references an `environment` with required reviewers, GitHub pauses the workflow and notifies the reviewers. The workflow resumes only when approved.

### Environment-Specific Configuration

Each environment typically has:
- Different AWS account or region
- Different resource sizes (smaller for staging)
- Different domain names
- Different secrets (database passwords, API keys)
- Different Terraform state files or workspaces

> **Architecture Thinking**: Should staging be identical to production or smaller? Identical means bugs that only appear under production-scale resources get caught. Smaller means lower costs. Most teams compromise: same architecture, but fewer/smaller instances. What would you choose for FlowForge and why?

> **Link forward**: In Module 8, environments become Kubernetes namespaces. In Module 10, each environment has different security policies. The pattern of environment promotion -- dev → staging → production -- is fundamental to everything that follows.

---

## 8. Branch Strategies

### Trunk-Based Development

**Trunk-based development** means all developers commit to `main` (the "trunk") frequently -- at least once per day. Feature branches are short-lived (hours to a few days, never weeks) and merge quickly.

**How it works**:
1. Create a feature branch from `main`
2. Make small, focused changes
3. Open a PR -- CI runs automatically
4. Review and merge quickly (same day if possible)
5. Merge to `main` triggers staging deployment

**Why it works**: Small changes are easy to review, easy to test, and easy to rollback. Long-lived branches accumulate merge conflicts and "big bang" integrations that are painful and risky.

### Gitflow

**Gitflow** uses multiple long-lived branches: `main`, `develop`, `release/*`, `hotfix/*`, `feature/*`. It was designed for software with versioned releases (desktop apps, mobile apps).

**Why you probably don't want it for DevOps**: Gitflow adds ceremony (release branches, develop branch) that makes sense for infrequent releases but slows down continuous deployment. If you're deploying multiple times per day, Gitflow's branch management becomes overhead.

### GitHub Flow

**GitHub Flow** is a simplified model:
1. `main` is always deployable
2. Create feature branches from `main`
3. Open PR for review
4. Merge to `main`
5. Deploy

It's essentially trunk-based development with the addition of PRs for code review. This is what we'll use for FlowForge.

> **Architecture Thinking**: Your team has 3 developers. One wants Gitflow because "it's more organized." Another wants trunk-based because "it's faster." How do you decide? Consider: how often do you deploy? Do you need to maintain multiple release versions? How experienced is the team with Git? What's the cost of a merge conflict? For FlowForge (a single deployable service, deploying to cloud), which model fits better and why?

### Branch Protection Rules

Regardless of strategy, protect `main`:
- Require PR reviews before merge
- Require CI to pass before merge
- Require branches to be up-to-date before merge
- No direct pushes to `main`
- No force pushes to `main`

> **Link back**: This connects to Module 6. Terraform state changes are dangerous. By requiring PRs and CI for `main`, you ensure every infrastructure change is reviewed (terraform plan as PR comment) before being applied.

---

## 9. Terraform in CI/CD

### The Pattern

Terraform in CI/CD follows a specific pattern:

**On Pull Request**:
1. Run `terraform init`
2. Run `terraform plan`
3. Post the plan output as a PR comment
4. Reviewers read the plan to understand what will change
5. **Never** run `terraform apply` on a PR

**On Merge to Main**:
1. Run `terraform init`
2. Run `terraform plan` (generate a fresh plan)
3. Run `terraform apply` with the plan from step 2
4. Only apply if plan succeeds

### Why Plan on PR, Apply on Merge?

The plan output is your change preview. When a PR modifies Terraform configs, the reviewer needs to see:
- What resources will be created?
- What resources will be modified? (in-place update vs destroy-and-recreate?)
- What resources will be destroyed?

This is exactly like `terraform plan` on your laptop (Module 6), but now it's automated and visible to the whole team.

> **Link back**: Remember Module 6's emphasis on reading plan output carefully? In CI/CD, the plan becomes a PR comment that the whole team can review. The declarative model makes this safe -- the plan is a complete, accurate preview of what will change.

### Safeguards for Concurrent Merges

What happens if two PRs are open, both modifying infrastructure, and they merge at roughly the same time?

**Problem**: PR A plans against the current state. PR B also plans against the current state. PR A merges and applies. Now PR B's plan is stale -- it was generated against a state that no longer exists.

**Solutions**:
1. **State locking** (DynamoDB from Module 6): Only one apply can run at a time. The second apply waits.
2. **Always plan before apply**: Even on merge, generate a fresh plan. If the state changed since the PR plan, the fresh plan reflects reality.
3. **Serialized deployments**: Use GitHub's concurrency feature to ensure only one deployment runs at a time.
4. **Require up-to-date branches**: GitHub branch protection can require that PRs are rebased on latest `main` before merging.

```yaml
concurrency:
  group: terraform-deploy
  cancel-in-progress: false  # Don't cancel running deploys!
```

> **Architecture Thinking**: DynamoDB state locking prevents concurrent applies. But what about concurrent plans? Two PRs show their plans simultaneously, but only one can be accurate after the other merges. How do you communicate this to reviewers? Some teams add a warning: "This plan may be outdated if other infrastructure PRs have merged since this was generated."

---

## 10. Debugging Pipelines

### Reading Workflow Logs

When a pipeline fails, the logs are your primary diagnostic tool. GitHub Actions provides:
- **Step-by-step output**: Each step's stdout/stderr is captured
- **Annotations**: Errors and warnings appear as annotations on the workflow run
- **Timing**: You can see how long each step took
- **Expandable groups**: Long output can be grouped for readability

### Common Failure Patterns

**Secret not available in step**:
```
Error: Process completed with exit code 1.
  echo "Pushing to $ECR_REGISTRY"
  Pushing to
```
The variable is empty because the secret wasn't passed to the step. Secrets must be explicitly passed via `env:` at the job or step level. They don't leak into every step automatically.

**Docker build context wrong**:
```
ERROR: failed to solve: failed to read dockerfile
```
The `docker build` command is running in the wrong directory. Remember: the `context` in Docker is relative to where the command runs. In GitHub Actions, you might need `working-directory` or to specify the path explicitly.

> **Link back**: This is the same Docker build context issue from Module 4 -- but now it's happening in CI where you can't just `cd` into the right directory interactively.

**Stale image tag**:
```
Deploying flowforge/api-service:latest...
```
The deploy step is using `latest` instead of the commit SHA. The image was built and pushed with the SHA tag, but the deploy script still references `latest`. This is why tagging strategy matters.

### Debugging Methodology

When a pipeline fails:

1. **Read the error message first** -- don't skip to the code. The error often tells you exactly what's wrong.
2. **Check which step failed** -- the failing step narrows your investigation.
3. **Check the inputs to the failing step** -- are environment variables set? Are secrets available? Is the working directory correct?
4. **Check the outputs of previous steps** -- did a previous step produce the artifact this step expects?
5. **Reproduce locally if possible** -- can you run the same commands on your machine?

> **Link back**: This is the same systematic debugging methodology from Module 1 (broken server), Module 2 (broken network), Module 4 (broken Docker), and Module 6 (broken Terraform). The pattern is always the same: read the error, narrow the scope, check inputs and outputs, reproduce.

> **Architecture Thinking**: Some teams add extensive `echo` statements to their workflows for debugging. Others keep workflows minimal and clean. What's the trade-off? Debug output clutters logs for successful runs but saves hours on failures. A middle ground: use `ACTIONS_STEP_DEBUG` (a GitHub secret) to enable verbose output only when needed.

---

## Summary: What You'll Build in This Module

By the end of Module 7, you'll have a complete CI/CD pipeline for FlowForge:

```
Developer pushes code
    │
    ├── CI: go test, golangci-lint, gosec, govulncheck
    │
    ├── Build: Docker images tagged with git SHA
    │
    ├── Push: Images pushed to ECR
    │
    ├── Terraform: Plan on PR (as comment), apply on merge
    │
    ├── Deploy Staging: Automatic on merge to main
    │
    └── Deploy Production: Manual approval required
```

This pipeline is:
- **Automated**: No manual steps except production approval
- **Traceable**: Every deployment maps to a specific commit
- **Safe**: Quality gates prevent bad code from reaching production
- **Reviewable**: Terraform plans are visible in PRs
- **Auditable**: Every deployment is logged in GitHub Actions

> **Link forward**: In Module 8, the deployment target becomes Kubernetes. The pipeline you build here will be extended to run `kubectl apply` or `helm upgrade` against your K8s cluster. In Module 9, you'll add monitoring checks to the pipeline -- deploy, then verify health metrics before marking the deployment as successful. In Module 10, you'll add security scanning gates that block deployments with known vulnerabilities.

---

## Labs

| Lab | Exercises | What You'll Build |
|-----|-----------|-------------------|
| [Lab 01](lab-01-github-actions-basics.md) | 1a, 1b | Basic CI workflow + Docker image build/push |
| [Lab 02](lab-02-secrets-quality.md) | 2a, 2b | Secrets management + quality gates |
| [Lab 03](lab-03-environments-branches.md) | 3a, 3b | Multi-environment deployment + branch strategy |
| [Lab 04](lab-04-terraform-in-ci.md) | 4 | Terraform plan/apply automation |
| [Lab 05](lab-05-broken-pipelines.md) | 5 | Debugging broken pipelines |

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow syntax reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [OIDC for AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [golangci-lint](https://golangci-lint.run/)
- [trivy](https://aquasecurity.github.io/trivy/)
- [gosec](https://github.com/securego/gosec)
- [govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
