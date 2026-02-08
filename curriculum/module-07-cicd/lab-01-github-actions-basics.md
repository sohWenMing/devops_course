# Lab 01: GitHub Actions Basics -- Your First CI Pipeline

> **Module**: 7 -- CI/CD with GitHub Actions  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [CI vs CD](#), [GitHub Actions Fundamentals](#), [Build Pipelines](#), and [Docker Image Building & Tagging Strategies](#) sections of the Module 7 README. GitHub account. FlowForge repository with Go services from Module 3 and Dockerfiles from Module 4. AWS ECR repositories from Module 5.

---

## Overview

In this lab, you'll create your first GitHub Actions workflow that automatically tests your Go code on every push, then extend it to build Docker images and push them to ECR. By the end, every push to your repository will trigger a real CI pipeline.

---

## Exercise 1a: CI Workflow -- Test on Push

### Objectives

- Create a GitHub Actions workflow file from scratch
- Understand triggers, jobs, steps, and runners
- Configure a workflow to run `go test` automatically on push
- Read and interpret workflow run output in the GitHub UI
- Understand the relationship between workflow YAML and execution

### What You'll Do

**Part 1: Set Up the Repository**

1. Your FlowForge project should be in a GitHub repository. If it isn't already:
   - Initialize a Git repository in your project root
   - Create a `.gitignore` appropriate for Go projects (binaries, vendor, .env files)
   - Push to a new GitHub repository

2. Before writing any YAML, sketch out (on paper or whiteboard) what you want the pipeline to do:
   - What event should trigger the pipeline?
   - What language/tools need to be available on the runner?
   - What commands need to run?
   - What constitutes "success" vs "failure"?

**Part 2: Write the Workflow**

3. Create the workflow directory structure that GitHub Actions expects.
   - Where do workflow files live in a repository? (Hint: you created a `.github/workflows/` directory in the scaffold)
   - What file extension do workflow files use?

4. Write a workflow file that:
   - Has a descriptive name (e.g., "FlowForge CI")
   - Triggers on push to `main` AND on pull requests targeting `main`
   - Defines a job called `test` that runs on `ubuntu-latest`
   - Checks out the repository code
   - Sets up Go (version 1.21 or later)
   - Runs `go test ./...` for the api-service
   - Runs `go test ./...` for the worker-service

5. Think about these questions before pushing:
   - Why do you need to explicitly check out the code? Isn't it already "there" since the workflow is in the repo?
   - Why specify the Go version? What would happen if you didn't?
   - What does `./...` mean in Go test context?

**Part 3: Trigger and Observe**

6. Commit the workflow file and push to `main`.

7. Go to the GitHub UI and navigate to the "Actions" tab:
   - Can you see the workflow running?
   - Click into the run -- what does the log output look like?
   - Expand each step -- can you see the Go test output?
   - How long did the run take?
   - What's the status (green check or red X)?

8. Make a change to your Go code that breaks a test (e.g., change an expected value). Push.
   - Does the workflow show a failure?
   - Can you identify which test failed from the log output?
   - Fix the test and push again -- does the workflow pass?

**Part 4: Understand Triggers**

9. Experiment with different trigger configurations:
   - What happens if you change the trigger to only `push` (no `pull_request`)?
   - What if you add `paths` filter to only trigger when Go files change?
   - What does `branches-ignore` do?
   - Create a feature branch, push to it, and open a PR -- does the workflow run?

10. Add a second trigger: `workflow_dispatch` (manual trigger). Push the change, then trigger the workflow manually from the GitHub UI. When would manual triggers be useful?

### Expected Outcomes

- A `.github/workflows/ci.yml` (or similar) file in your repository
- The workflow runs automatically on every push to `main`
- The workflow runs on PRs targeting `main`
- Go tests for both services execute and report pass/fail
- You can read the workflow logs and identify test results

### Checkpoint Questions

- Without looking: what are the five core components of a GitHub Actions workflow? (triggers, jobs, steps, runners, actions)
- What's the difference between `push` and `pull_request` triggers? When does each fire?
- Why does the runner need to check out the code explicitly?
- If you wanted this workflow to also run on a schedule (e.g., nightly), what trigger would you add?
- Can two jobs in the same workflow run in parallel? How do you control the order?

---

## Exercise 1b: Build & Push Docker Images

### Objectives

- Add a Docker build job to your CI pipeline
- Tag Docker images with the git commit SHA
- Push images to Amazon ECR from GitHub Actions
- Understand job dependencies with `needs`
- Implement a build pipeline that flows from test → build → push

### What You'll Do

**Part 1: Plan the Build Job**

1. Before writing YAML, plan the build job:
   - What needs to happen before images are built? (Answer: tests must pass)
   - How many images need to be built? (api-service and worker-service)
   - What tag should each image get? (Think about why git SHA is better than `latest`)
   - What credentials are needed to push to ECR?

2. Draw the job dependency graph for your workflow:
   ```
   push → test → build-and-push
   ```
   How do you express "build-and-push depends on test" in GitHub Actions YAML?

**Part 2: Add the Build Job**

3. Add a new job to your existing workflow that:
   - Only runs after the test job succeeds (`needs` keyword)
   - Only runs on pushes to `main` (not on PRs -- why would you skip building images for PRs?)
   - Checks out the code
   - Sets up Docker Buildx (a GitHub Action for multi-platform builds)
   - Logs into Amazon ECR (you'll need AWS credentials -- for now, use GitHub Secrets; Lab 02 will improve this)
   - Builds the Docker image for api-service using the Dockerfile from Module 4
   - Tags the image with `${{ github.sha }}` (the full commit SHA)
   - Pushes the image to your ECR repository
   - Repeats for worker-service

4. Think about these questions:
   - Why build images only on pushes to `main`, not on PRs?
   - What happens if the Docker build fails because of a Dockerfile syntax error? Does the workflow stop?
   - How would you also tag the image with a short SHA (first 7 characters)?

**Part 3: Configure ECR Access**

5. Set up the AWS credentials needed to push to ECR:
   - Go to Settings > Secrets and variables > Actions in your GitHub repository
   - Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as repository secrets
   - These should be for an IAM user with ONLY ECR push permissions (least privilege from Module 5)

6. In your workflow, use the `aws-actions/amazon-ecr-login` action to authenticate with ECR:
   - What does this action output? (Hint: it outputs the registry URL)
   - How do you reference that output in a subsequent step?

**Part 4: Build, Push, Verify**

7. Push the updated workflow to `main` and observe:
   - Do the test job and build job run in the right order?
   - Can you see the Docker build output in the logs?
   - Did the images push to ECR successfully?

8. Verify in AWS:
   - Check your ECR repositories -- are the new images there?
   - What tag do they have? Can you match the tag to the commit SHA in GitHub?
   - How would you pull this specific image on an EC2 instance?

9. Make another push and verify:
   - A new image appears in ECR with a different SHA tag
   - The previous image is still there (immutable tags)
   - You can now map any running container to the exact code that produced it

**Part 5: Optimize**

10. Consider these optimizations (implement at least one):
    - Docker layer caching in CI: the `docker/build-push-action` supports cache-from/cache-to. How much would this speed up subsequent builds?
    - Building both images in parallel: can you use a matrix strategy to build api-service and worker-service simultaneously?
    - Outputting the image URI from the build job so downstream jobs can reference it

### Expected Outcomes

- Your CI workflow now has two jobs: `test` and `build-push`
- The build job only runs after tests pass
- Docker images are tagged with the full git commit SHA
- Images are pushed to ECR automatically on every merge to `main`
- You can verify images in ECR and trace them back to specific commits

### Checkpoint Questions

- Why is tagging with `git SHA` better than tagging with `latest`? Give a specific rollback scenario.
- What's the `needs` keyword doing in the build job? What happens if the test job fails?
- Why did you restrict the build job to only run on `main` and not on PRs?
- How would you add worker-service as a second image to build? (Matrix strategy vs duplicate steps -- trade-offs?)
- If you needed to build images for a new service (e.g., a notification-service), what changes would you make to the workflow?
- Explain the flow from git push to image in ECR. List every step.
