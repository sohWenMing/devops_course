# Lab 03: Environments & Branch Strategies

> **Module**: 7 -- CI/CD with GitHub Actions  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [Multi-Environment Deployment](#) and [Branch Strategies](#) sections of the Module 7 README. Lab 02 completed (CI pipeline with quality gates). GitHub repository with branch protection on `main`. AWS infrastructure (from Module 6 Terraform) or ability to deploy.

---

## Overview

In this lab, you'll configure GitHub Environments to manage staging and production deployments with different approval requirements, then implement a trunk-based development workflow with feature branches, PRs, and environment promotion. By the end, your pipeline automatically deploys to staging on merge and requires manual approval for production.

---

## Exercise 3a: GitHub Environments -- Staging & Production

### Objectives

- Configure GitHub Environments for staging and production
- Implement auto-deploy to staging on merge to `main`
- Require manual approval for production deployments
- Use environment-specific secrets and variables
- Deploy to different AWS resources per environment

### What You'll Do

**Part 1: Create GitHub Environments**

1. In your GitHub repository, go to Settings > Environments:
   - Create a `staging` environment
   - Create a `production` environment
   - What configuration options are available for each environment?

2. Configure the `staging` environment:
   - No required reviewers (auto-deploy)
   - Add environment-specific secrets if needed (e.g., `STAGING_DB_HOST`)
   - Restrict to the `main` branch only (deployment branches)
   - Why restrict deployment branches? What would happen if any branch could deploy to staging?

3. Configure the `production` environment:
   - Add at least one required reviewer (yourself, for this exercise)
   - Add a wait timer (optional -- e.g., 5 minutes after staging deploy before production is eligible)
   - Restrict to the `main` branch only
   - Add environment-specific secrets (e.g., `PROD_DB_HOST`)
   - Why require reviewers for production? What does the approval workflow look like?

**Part 2: Add Deployment Jobs**

4. Add deployment jobs to your workflow:
   - `deploy-staging` job that:
     - References the `staging` environment
     - Depends on the build-push job
     - Only runs on pushes to `main` (not on PRs)
     - Deploys the Docker images built in the pipeline to your staging AWS resources
   - `deploy-production` job that:
     - References the `production` environment
     - Depends on `deploy-staging`
     - Only runs on pushes to `main`
     - Deploys to production AWS resources

5. For the actual deployment step, think about what "deploy" means for FlowForge:
   - SSH into EC2 and pull the new image? (Simple but fragile)
   - Use AWS Systems Manager Run Command? (Better -- no SSH needed)
   - Update an ECS service? (Best for container deployments, if you set up ECS)
   - For this exercise, even a simulated deploy (echo commands) is fine -- the WORKFLOW is what matters, not the deploy mechanism

6. How does the workflow handle the `production` environment's approval requirement?
   - Push a change to `main`
   - Watch the workflow -- it should deploy to staging automatically
   - The production job should pause and show "Waiting for review"
   - Go to the workflow run in GitHub UI and approve the deployment
   - Watch production deployment execute

**Part 3: Environment-Specific Configuration**

7. Configure your deployment to use different settings per environment:
   - Staging: smaller instances, different database endpoint, debug logging
   - Production: full-size instances, production database, info logging
   - How do you pass environment-specific values to the deploy step?
   - Can you use GitHub environment variables (not secrets) for non-sensitive config?

8. Verify environment isolation:
   - Staging deployment should not affect production resources
   - Production deployment should not happen without approval
   - Each environment should use its own secrets
   - Check the "Deployments" tab in your repository -- does it show the deployment history?

**Part 4: Deployment History & Rollback**

9. Make multiple deployments to staging and observe:
   - Can you see the deployment history in the GitHub UI?
   - Each deployment should reference a specific commit SHA
   - If you needed to rollback staging to a previous version, how would you do it?
   - (Hint: you could re-run a previous workflow, or deploy a specific image tag)

10. Think about rollback strategies:
    - Revert the code change and push (triggers a new deploy)
    - Re-deploy a previous image tag (faster, doesn't need code change)
    - Blue/green deployment (advanced -- Module 8 with Kubernetes)
    - Which strategy works best for different failure scenarios?

### Expected Outcomes

- `staging` and `production` environments configured in GitHub
- Workflow deploys automatically to staging on merge to `main`
- Production deployment pauses for manual approval
- Environment-specific secrets and configuration are used
- Deployment history is visible in the GitHub UI

### Checkpoint Questions

- What's the difference between a GitHub Environment and a GitHub Secret? Can you have secrets at both levels?
- Why does staging auto-deploy but production requires approval? When might you change this?
- What happens if you reject a production deployment? Can you re-trigger it?
- How would you add a third environment (e.g., QA) between staging and production?
- If a deployment to staging fails, does the production deployment job even start? Why or why not?
- Explain the environment promotion flow: code commit → staging → production. What gates exist at each transition?

---

## Exercise 3b: Branch Strategy -- Trunk-Based Development

### Objectives

- Implement trunk-based development with short-lived feature branches
- Configure PRs to trigger CI (but not deployment)
- Configure merges to `main` to trigger the full pipeline (CI + CD)
- Understand why branch strategy affects pipeline design
- Practice the full developer workflow: branch → develop → PR → review → merge → deploy

### What You'll Do

**Part 1: Configure Branch Protection**

1. Review and enhance branch protection rules for `main`:
   - Require pull request reviews before merging (at least 1 reviewer)
   - Require status checks to pass (select your lint, test, and build jobs)
   - Require branches to be up to date before merging
   - Do not allow bypassing the above settings
   - Prevent force pushes to `main`
   - What does each rule prevent? What workflow does each enforce?

2. Verify direct pushes are blocked:
   - Try pushing directly to `main` -- what happens?
   - The only way code reaches `main` should be through a PR

**Part 2: Feature Branch Workflow**

3. Practice the full workflow:
   - Create a feature branch from `main`: `git checkout -b feature/add-health-endpoint`
   - Make a small change (e.g., add or modify a health check endpoint in api-service)
   - Commit and push the feature branch
   - Open a PR from the feature branch to `main`

4. Observe what happens when you open the PR:
   - Which workflow jobs run? (Should be CI jobs: lint, test)
   - Which jobs DON'T run? (Should NOT build images or deploy)
   - Can you see the CI status on the PR page?
   - Does the PR show "All checks passed" or "Some checks failed"?

5. Review the PR:
   - Look at the code diff
   - Look at the CI results
   - If CI passes, approve and merge the PR
   - What merge strategy do you use? (Merge commit, squash, or rebase? What are the trade-offs?)

6. After merging, observe the deployment:
   - Does a new workflow run trigger on `main`?
   - Does it run the full pipeline (CI + build + deploy to staging)?
   - Is the staging deployment successful?
   - Is the production deployment waiting for approval?

**Part 3: Multiple Feature Branches**

7. Simulate parallel development:
   - Create two feature branches from `main`: `feature/api-improvement` and `feature/worker-optimization`
   - Make different changes on each branch
   - Open PRs for both
   - What happens if both PRs are passing CI?
   - Merge one PR first -- does the second PR now need to be rebased?

8. Handle merge conflicts:
   - Modify the same file on both branches (different sections)
   - Try to merge both -- what happens?
   - Resolve the conflict, push, verify CI passes again
   - This is why short-lived branches matter -- the longer branches live, the more conflicts accumulate

**Part 4: Workflow Conditions**

9. Ensure your workflow correctly differentiates between PR events and merge events:
   - On PR: run lint, test (CI only)
   - On merge to main: run lint, test, build, push, deploy (CI + CD)
   - How do you use `if` conditions or trigger configuration to achieve this?
   - What happens with the `pull_request` trigger when a PR is merged? (It doesn't fire -- `push` fires instead)

10. Document your branch strategy:
    - Draw a diagram showing the flow: feature branch → PR → CI → review → merge → CD → staging → approval → production
    - List the rules: no direct pushes to main, PRs required, CI must pass, at least one review
    - Compare your strategy to Gitflow -- what's simpler? What's the trade-off?
    - When would you change your strategy? (e.g., for a mobile app with versioned releases)

### Expected Outcomes

- Branch protection rules enforce PR-based workflow on `main`
- Feature branches trigger CI only (lint, test)
- Merges to `main` trigger the full pipeline (CI + build + deploy)
- Developers practice: branch → develop → PR → review → merge → deploy
- Multiple feature branches can coexist without issues

### Checkpoint Questions

- Explain trunk-based development in one sentence. Why is it preferred for continuous deployment?
- What's the difference between trunk-based, Gitflow, and GitHub Flow? When would you choose each?
- Why should PRs trigger only CI (not deployment)? What's the risk of deploying from a PR?
- What happens if two PRs modify Terraform configs and both merge? (Connect to Lab 04)
- How do you handle a hotfix that needs to go to production immediately? Does your branch strategy support this?
- Explain why "require branches to be up to date before merging" prevents stale CI results.
