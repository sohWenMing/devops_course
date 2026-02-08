# Lab 02: Secrets Management & Quality Gates

> **Module**: 7 -- CI/CD with GitHub Actions  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [Secrets Management in CI](#) and [Test Stages & Quality Gates](#) sections of the Module 7 README. Lab 01 completed (working CI workflow with test + build jobs). AWS account with ECR repositories.

---

## Overview

In this lab, you'll properly secure your pipeline credentials (replacing the static AWS keys from Lab 01 with OIDC federation) and add quality gates that prevent bad code from ever reaching a built image. By the end, your pipeline will enforce code quality, security, and test coverage automatically.

---

## Exercise 2a: Secrets Management & OIDC Federation

### Objectives

- Understand how GitHub Secrets work and verify masking in logs
- Store AWS credentials securely as GitHub Secrets
- Configure OIDC federation between GitHub Actions and AWS for keyless authentication
- Replace static credentials with short-lived, role-based access
- Verify that secrets are never exposed in workflow logs

### What You'll Do

**Part 1: Understand GitHub Secrets**

1. Review the secrets you created in Lab 01 (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY):
   - Where are they stored? (GitHub Settings > Secrets)
   - Who can see them? Can collaborators view the secret values?
   - Can workflows in forked repositories access these secrets? Why or why not?

2. Add a test step to your workflow that deliberately tries to print a secret:
   ```yaml
   - name: Test secret masking
     run: echo "My secret is ${{ secrets.AWS_ACCESS_KEY_ID }}"
   ```
   Push and check the logs. What do you see instead of the actual secret value? Why is this important?

3. Try a more subtle leak attempt -- what happens if you:
   - Base64-encode the secret before printing it?
   - Print it character by character?
   - Write it to a file and then `cat` the file?
   
   Understanding how masking works (and its limitations) is important for security.

**Part 2: OIDC Federation Setup (Keyless AWS Auth)**

4. Set up AWS to trust GitHub as an OIDC identity provider:
   - In the AWS IAM console, create an OIDC identity provider
   - The provider URL is `https://token.actions.githubusercontent.com`
   - The audience is `sts.amazonaws.com`
   - What is an OIDC provider in AWS terms? How does it compare to an IAM user?

5. Create an IAM role for GitHub Actions:
   - The trust policy should allow the GitHub OIDC provider to assume the role
   - Condition: restrict to your specific repository (`repo:your-username/your-repo:*`)
   - Permissions: ECR push/pull, any other permissions your pipeline needs
   - What's the advantage of restricting the trust policy to a specific repo?
   - What would happen if you used `repo:*` instead?

6. Update your workflow to use OIDC instead of static secrets:
   - Add `permissions: id-token: write` to the job (this allows the workflow to request an OIDC token)
   - Use the `aws-actions/configure-aws-credentials` action with `role-to-assume`
   - Remove the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from your workflow env
   - What does the workflow do differently now? Where do the credentials come from?

7. Test the OIDC setup:
   - Push a change and verify the workflow still pushes to ECR
   - Check the AWS CloudTrail logs -- can you see the AssumeRoleWithWebIdentity call?
   - What is the session duration of the temporary credentials?

**Part 3: Verify Security**

8. Verify your secrets are properly secured:
   - Delete the static AWS access key and secret key from GitHub Secrets (you don't need them anymore)
   - Delete the IAM user's access keys from AWS (OIDC replaces them)
   - Verify the pipeline still works using only the OIDC role
   - Check the workflow logs -- are there ANY AWS credentials visible?

9. Tighten the OIDC role's trust policy:
   - Can you restrict it to only the `main` branch? (Condition: `repo:user/repo:ref:refs/heads/main`)
   - Why would you want branch-level restrictions?
   - What happens if someone creates a PR from a fork and the workflow runs?

10. Document your security setup:
    - What credentials exist and where?
    - How are they rotated? (Hint: OIDC credentials auto-expire)
    - What's the blast radius if the IAM role is compromised?
    - Compare this to the Lab 01 approach with static keys

### Expected Outcomes

- GitHub OIDC identity provider configured in AWS IAM
- IAM role with trust policy restricted to your repository
- Workflow uses `aws-actions/configure-aws-credentials` with OIDC (no static keys)
- No long-lived AWS credentials stored anywhere
- Secrets are properly masked in all workflow logs

### Checkpoint Questions

- Explain the OIDC federation flow in your own words: what happens between GitHub Actions, AWS STS, and IAM?
- Why is OIDC preferable to static AWS access keys for CI/CD?
- What does `permissions: id-token: write` do in the workflow? What happens without it?
- If you needed to give the CI pipeline access to a DIFFERENT AWS account, how would you do it with OIDC?
- How do you verify that secrets are being masked in logs? What are the limitations of GitHub's masking?

---

## Exercise 2b: Quality Gates -- Linting, Security Scanning & Coverage

### Objectives

- Add `golangci-lint` to the CI pipeline as a code quality gate
- Add `trivy` image scanning as a security gate
- Implement test coverage threshold enforcement (>70%)
- Understand the fail-fast principle in pipeline design
- Configure the pipeline to block merges on quality failures

### What You'll Do

**Part 1: Add Linting**

1. Add a lint job to your workflow that runs `golangci-lint`:
   - Use the `golangci/golangci-lint-action` from the GitHub Marketplace
   - Configure it to run against both api-service and worker-service
   - Should the lint job depend on the test job, or can it run in parallel? Why?

2. Before pushing, predict:
   - Will your current code pass golangci-lint with default settings?
   - What kinds of issues might it find? (unused variables, unchecked errors, etc.)
   - What's the difference between a lint warning and a lint error?

3. Push and observe:
   - Did the lint pass? If not, what issues were found?
   - Fix any lint errors in your Go code
   - Push again and verify the lint passes

4. Optional: Create a `.golangci.yml` configuration file:
   - Enable/disable specific linters
   - Set timeout for slow linters
   - Exclude certain files or patterns
   - What linters would you enable for a production Go project?

**Part 2: Add Security Scanning**

5. Add a trivy scan step that runs after Docker images are built:
   - Use the `aquasecurity/trivy-action` from the GitHub Marketplace
   - Scan the Docker images you build in the pipeline
   - Configure it to fail the pipeline on HIGH or CRITICAL vulnerabilities
   - What's the difference between scanning the image vs scanning the Dockerfile?

6. Consider adding Go-specific security tools:
   - **gosec**: Finds security issues in Go source code (SQL injection, hardcoded credentials, etc.)
   - **govulncheck**: Checks Go module dependencies against the vulnerability database
   - Add at least one of these to your pipeline
   - How do these tools differ from trivy? What does each catch that the others don't?

7. Push and observe the security scan results:
   - Were any vulnerabilities found?
   - If HIGH/CRITICAL vulnerabilities exist, how do you fix them? (Hint: update base images, update dependencies)
   - After fixing, push again and verify the scan passes

**Part 3: Test Coverage Threshold**

8. Modify the test job to enforce a coverage threshold:
   - Run tests with `-coverprofile=coverage.out`
   - Parse the coverage percentage from the output
   - Fail the step if coverage is below 70%
   - Display the current coverage percentage in the log

9. Test the threshold:
   - What's your current coverage percentage?
   - If it's above 70%, temporarily comment out some tests and verify the pipeline fails
   - Restore the tests and verify the pipeline passes

10. Consider adding a coverage report:
    - Can you upload the coverage report as a GitHub Actions artifact?
    - Can you post coverage as a PR comment? (Several GitHub Actions exist for this)
    - What value does a coverage trend provide over just a threshold?

**Part 4: Pipeline Architecture**

11. Review your complete pipeline architecture. It should now look like:
    ```
    push → ┌── lint ──────────────────┐
           ├── test (with coverage) ──┤→ build-push → security-scan
           └──────────────────────────┘
    ```
    - Lint and test run in parallel (independent)
    - Build only runs after both pass
    - Security scan runs on the built images

12. Configure branch protection rules on `main`:
    - Require the lint job to pass before merging
    - Require the test job to pass before merging
    - Require PR review before merging
    - How do you configure which "status checks" are required?

### Expected Outcomes

- `golangci-lint` runs on every push and PR, catching code quality issues
- `trivy` scans Docker images for vulnerabilities, failing on HIGH/CRITICAL
- Test coverage is measured and enforced at a >70% threshold
- Pipeline fails fast: lint and test run in parallel, build only happens if both pass
- Branch protection rules require CI to pass before merging to `main`

### Checkpoint Questions

- What's the difference between linting, testing, and security scanning? What does each catch?
- Why should lint and test run in parallel rather than sequentially?
- What's the fail-fast principle? How does pipeline ordering implement it?
- If trivy finds a HIGH vulnerability in your base image, what are your options to fix it?
- Why set coverage threshold at 70% and not 100%? What's the practical trade-off?
- Add a new quality gate from scratch (e.g., `go vet`, `staticcheck`, or a documentation lint). How would you integrate it?
