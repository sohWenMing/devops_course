# Lab 05: Broken Pipelines -- Debugging Challenge

> **Module**: 7 -- CI/CD with GitHub Actions  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Labs 01-04 completed. Solid understanding of GitHub Actions workflow syntax, secrets, Docker builds, and deployment patterns.

---

## Overview

In this lab, you'll diagnose three broken CI/CD pipelines using only workflow logs. Each pipeline has a single root cause, but the symptoms may be misleading. This exercises your pipeline debugging skills -- a critical real-world ability since CI/CD failures happen frequently and are often the first thing you debug on a Monday morning.

> **Link back**: This follows the same pattern as Module 1 (broken server), Module 2 (broken network), Module 4 (broken Docker), and Module 6 (broken Terraform). The debugging methodology is always the same: read the error, narrow the scope, check inputs and outputs, form a hypothesis, verify.

---

## Exercise 5: Three Broken Pipelines

### Objectives

- Diagnose CI/CD pipeline failures from workflow logs alone
- Practice the systematic debugging methodology for pipelines
- Understand common failure patterns in GitHub Actions
- Fix each issue and verify the pipeline passes
- Document each diagnosis with root cause and fix

### The Rules

1. **Diagnose from logs first**: For each broken pipeline, you'll be given the workflow YAML and the log output. Start by reading the logs -- don't jump to the YAML.
2. **Form a hypothesis**: Before looking at the YAML, form a hypothesis about what's wrong based on the error message.
3. **Verify against the YAML**: Then read the YAML to confirm or refute your hypothesis.
4. **Fix and explain**: Fix the issue and explain WHY it was broken, not just what you changed.

---

### Broken Pipeline 1: "Secret Not Available in Step"

**Scenario**: A developer added a new deploy step to the workflow. The step needs AWS credentials to push to ECR, but the push fails with an authentication error. The workflow was working before the new step was added.

**What You'll See**: Create a workflow (or modify your existing one) that simulates this problem:

1. Create a workflow file with the following structure:
   - A `build-push` job that:
     - Has `permissions: id-token: write, contents: read`
     - Configures AWS credentials using OIDC in Step 1
     - Builds a Docker image in Step 2
     - Logs into ECR in Step 3
     - Pushes the image in Step 4 (this step is in a SEPARATE job that runs after build-push)

2. The SECOND job (`deploy`) that:
   - Runs after `build-push` with `needs: [build-push]`
   - Has a step that tries to use AWS credentials to deploy
   - Does NOT have its own `permissions` block or credential configuration

3. Push this workflow and observe the failure in the `deploy` job.

**Your Task**:
- Read the log output for the `deploy` job
- Why can't the deploy job access AWS credentials?
- What's the fundamental misunderstanding about how jobs share (or don't share) state?
- Fix the issue (there are multiple valid approaches)
- Document: root cause, symptom, fix, and the GitHub Actions concept that was violated

**Hints if stuck** (progressive):
- Hint 1: What happens to environment variables between jobs?
- Hint 2: Each job runs on a fresh runner. What does "fresh" mean?
- Hint 3: Credentials configured in one job don't carry over to another job

---

### Broken Pipeline 2: "Docker Build Context Wrong"

**Scenario**: A developer moved the Dockerfile from the repository root to the service directory (`project/api-service/Dockerfile`) and updated the workflow, but the Docker build fails.

**What You'll See**: Create or modify a workflow to simulate this:

1. Ensure your api-service Dockerfile exists at `project/api-service/Dockerfile`

2. Create a workflow step that runs:
   ```yaml
   - name: Build Docker image
     run: docker build -t flowforge/api-service:${{ github.sha }} -f project/api-service/Dockerfile .
   ```
   The `-f` flag points to the right Dockerfile, but the build context (`.`) is the repository root.

3. The Dockerfile has a `COPY` instruction like:
   ```dockerfile
   COPY go.mod go.sum ./
   COPY . .
   ```
   These paths are relative to the api-service directory, NOT the repository root.

4. Push and observe the Docker build failure.

**Your Task**:
- Read the Docker build error in the workflow logs
- What file is Docker trying to COPY that it can't find?
- What is the "build context" and how does it relate to the `-f` flag?
- What's the difference between the Dockerfile location and the build context directory?
- Fix the issue (there are at least two valid approaches)
- Document: root cause, symptom, fix, and the Docker concept that was violated

**Hints if stuck** (progressive):
- Hint 1: What directory does Docker use as the context when you specify `.`?
- Hint 2: `COPY go.mod go.sum ./` looks for `go.mod` in the build context, not in the directory where the Dockerfile lives
- Hint 3: Either change the build context to `project/api-service/` or adjust the COPY paths in the Dockerfile

---

### Broken Pipeline 3: "Deploy Step Uses Stale Image Tag"

**Scenario**: The pipeline builds and pushes images correctly, but the deploy step always deploys the SAME old image. New code changes don't appear in staging after deployment.

**What You'll See**: Create or modify a workflow to simulate this:

1. The build job correctly:
   - Builds the Docker image
   - Tags it with `${{ github.sha }}`
   - Pushes to ECR

2. The deploy job:
   - Has `needs: [build-push]`
   - Runs a deploy command like:
     ```yaml
     - name: Deploy to staging
       run: |
         echo "Deploying flowforge/api-service:latest to staging..."
         # Simulated deploy command
         aws ecs update-service --cluster staging --service api --force-new-deployment
     ```
   - Notice anything about the image tag in the echo statement? And the ECS command?

3. The ECS task definition (or Docker run command on EC2) references the image as:
   ```
   flowforge/api-service:latest
   ```
   But the build job tagged with the commit SHA, not `latest`.

4. Push and observe: the pipeline "succeeds" but the deployed version doesn't match the latest commit.

**Your Task**:
- Read the workflow logs carefully -- this one "passes" but the deployment is wrong
- What image tag is the build job producing?
- What image tag is the deploy step expecting?
- Why does this work the first time but deploy stale code on subsequent pushes?
- Fix the issue (there are multiple approaches)
- Document: root cause, symptom, fix, and the CI/CD concept that was violated

**Hints if stuck** (progressive):
- Hint 1: Look at the image tags produced by the build job vs consumed by the deploy job
- Hint 2: The build job tags with `github.sha`, but the deploy job references `latest`
- Hint 3: Either pass the SHA tag to the deploy job (via outputs), or also tag the image as `latest` during build, or update the task definition/run command to use the SHA tag

---

### For All Three Broken Pipelines

After fixing each pipeline, fill out this incident report template:

```markdown
## Pipeline Failure Report

### Pipeline: [name]
### Symptom: [what the user/developer sees]
### Error Message: [exact error from logs]
### Root Cause: [the actual problem]
### GitHub Actions Concept Violated: [which fundamental concept was misunderstood]
### Fix: [what you changed]
### Prevention: [how would you prevent this from happening again?]
### Time to Diagnose: [how long it took you]
```

### Expected Outcomes

- All three broken pipelines diagnosed and fixed
- Incident report completed for each failure
- Understanding of job isolation, Docker build context, and image tagging
- Ability to diagnose pipeline failures from logs without seeing the workflow file first

### Checkpoint Questions

- For each broken pipeline: explain the root cause to a colleague (rubber duck) without referencing the YAML
- What's the debugging methodology for CI/CD failures? List the steps in order.
- How do jobs in GitHub Actions share (or not share) data? What mechanisms exist? (`outputs`, artifacts, caches)
- Why is the "stale image tag" bug particularly dangerous? (The pipeline shows green!)
- If you encountered a new pipeline failure you've never seen before, what's the first thing you'd check?
- Given a failed workflow run you've never seen before, can you diagnose the issue from logs alone in under 10 minutes? Practice this.
