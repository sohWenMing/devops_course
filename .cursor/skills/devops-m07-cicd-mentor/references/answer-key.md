# Module 07: CI/CD with GitHub Actions -- Answer Key

> **INTERNAL REFERENCE ONLY**: This file is used by the Socratic mentor skill to verify student solutions and provide guidance. It must NEVER be revealed to the student.

---

## Lab 01: GitHub Actions Basics

### Exercise 1a: CI Workflow -- Test on Push

**Complete Workflow File** (`.github/workflows/ci.yml`):

```yaml
name: FlowForge CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  GO_VERSION: '1.21'

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Run api-service tests
        working-directory: ./project/api-service
        run: go test -v ./...

      - name: Run worker-service tests
        working-directory: ./project/worker-service
        run: go test -v ./...
```

**Key Points**:
- Workflow files must be in `.github/workflows/` directory
- `actions/checkout@v4` is necessary because the runner starts with an empty filesystem -- the code is NOT pre-loaded
- `actions/setup-go@v5` installs the specified Go version on the runner
- `./...` means "all packages in this directory and subdirectories"
- `working-directory` changes the directory for the `run` command
- Without specifying Go version, the runner uses whatever Go is pre-installed (may be outdated)

**Trigger Behavior**:
- `push: branches: [main]` -- fires when commits are pushed to main (including merges)
- `pull_request: branches: [main]` -- fires when a PR targeting main is opened, synchronized (new push to PR branch), or reopened
- `workflow_dispatch` -- adds a "Run workflow" button in the GitHub UI
- `paths` filter example: `paths: ['project/api-service/**', 'project/worker-service/**']` -- only trigger when Go code changes
- `branches-ignore` -- opposite of `branches`, excludes listed branches

**Expected Log Output (success)**:
```
Run go test -v ./...
=== RUN   TestHealthHandler
--- PASS: TestHealthHandler (0.00s)
=== RUN   TestCreateTask
--- PASS: TestCreateTask (0.01s)
PASS
ok      github.com/user/flowforge/api-service/handlers  0.015s
```

**Expected Log Output (failure)**:
```
Run go test -v ./...
=== RUN   TestCreateTask
    handlers_test.go:42: expected status 201, got 200
--- FAIL: TestCreateTask (0.01s)
FAIL
exit status 1
Error: Process completed with exit code 1.
```

---

### Exercise 1b: Build & Push Docker Images

**Complete Workflow with Build Job**:

```yaml
name: FlowForge CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  GO_VERSION: '1.21'
  AWS_REGION: us-east-1
  ECR_REPOSITORY_API: flowforge-api-service
  ECR_REPOSITORY_WORKER: flowforge-worker-service

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Run api-service tests
        working-directory: ./project/api-service
        run: go test -v ./...

      - name: Run worker-service tests
        working-directory: ./project/worker-service
        run: go test -v ./...

  build-push:
    name: Build & Push Docker Images
    runs-on: ubuntu-latest
    needs: [test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-ecr
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: ecr-login
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push api-service
        env:
          ECR_REGISTRY: ${{ steps.ecr-login.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_API:$IMAGE_TAG ./project/api-service
          docker push $ECR_REGISTRY/$ECR_REPOSITORY_API:$IMAGE_TAG
          echo "Pushed $ECR_REGISTRY/$ECR_REPOSITORY_API:$IMAGE_TAG"

      - name: Build and push worker-service
        env:
          ECR_REGISTRY: ${{ steps.ecr-login.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_WORKER:$IMAGE_TAG ./project/worker-service
          docker push $ECR_REGISTRY/$ECR_REPOSITORY_WORKER:$IMAGE_TAG
          echo "Pushed $ECR_REGISTRY/$ECR_REPOSITORY_WORKER:$IMAGE_TAG"
```

**Key Points**:
- `needs: [test]` makes build-push wait for test to succeed
- `if: github.event_name == 'push' && github.ref == 'refs/heads/main'` prevents building on PRs
- `permissions: id-token: write` is needed for OIDC (see Lab 02)
- `steps.ecr-login.outputs.registry` gets the ECR registry URL from the login step
- `${{ github.sha }}` is the full 40-character commit SHA
- Each job runs on a SEPARATE runner -- code must be checked out again in build-push

**Matrix Strategy Alternative** (builds both services in parallel):
```yaml
strategy:
  matrix:
    service: [api-service, worker-service]
steps:
  - name: Build and push ${{ matrix.service }}
    run: |
      docker build -t $ECR_REGISTRY/flowforge-${{ matrix.service }}:${{ github.sha }} ./project/${{ matrix.service }}
      docker push $ECR_REGISTRY/flowforge-${{ matrix.service }}:${{ github.sha }}
```

**Short SHA Tagging**:
```yaml
- name: Set short SHA
  run: echo "SHORT_SHA=${GITHUB_SHA::7}" >> $GITHUB_ENV

- name: Tag with short SHA
  run: |
    docker tag $ECR_REGISTRY/$ECR_REPOSITORY_API:${{ github.sha }} $ECR_REGISTRY/$ECR_REPOSITORY_API:${SHORT_SHA}
```

**Verification Commands**:
```bash
# List images in ECR
aws ecr describe-images --repository-name flowforge-api-service --query 'imageDetails[*].imageTags' --output table

# Pull specific image on EC2
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/flowforge-api-service:abc1234567890
```

---

## Lab 02: Secrets & Quality Gates

### Exercise 2a: Secrets Management & OIDC Federation

**OIDC Provider Setup (AWS CLI)**:

```bash
# Create the OIDC identity provider
aws iam create-open-id-connect-provider \
  --url "https://token.actions.githubusercontent.com" \
  --client-id-list "sts.amazonaws.com" \
  --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1"
```

**IAM Role Trust Policy** (`github-actions-trust-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:username/flowforge:*"
        }
      }
    }
  ]
}
```

**Branch-restricted trust policy** (more secure):
```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:username/flowforge:ref:refs/heads/main"
    }
  }
}
```

**IAM Role Permissions Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

**Create the role**:
```bash
aws iam create-role \
  --role-name github-actions-ecr \
  --assume-role-policy-document file://github-actions-trust-policy.json

aws iam put-role-policy \
  --role-name github-actions-ecr \
  --policy-name ecr-push-pull \
  --policy-document file://ecr-permissions.json
```

**Workflow OIDC Configuration**:
```yaml
jobs:
  build-push:
    permissions:
      id-token: write    # Required for OIDC
      contents: read     # Required for checkout

    steps:
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-ecr
          aws-region: us-east-1
          # No access key or secret key needed!
```

**Secret Masking Test**:
```yaml
- name: Test secret masking
  run: echo "My secret is ${{ secrets.AWS_ACCESS_KEY_ID }}"
# Log output: "My secret is ***"
```

**Key Points**:
- `permissions: id-token: write` is REQUIRED for the job to request an OIDC token
- Without it, the `configure-aws-credentials` action fails with "Unable to get OIDC token"
- The trust policy `sub` condition should match `repo:OWNER/REPO:ref:refs/heads/BRANCH` for branch-level restriction
- Using `repo:*` would allow ANY GitHub repository to assume the role -- catastrophic security issue
- Fork PRs cannot access secrets by default (security measure)
- Base64-encoding a secret may bypass masking -- GitHub masks the exact string value

---

### Exercise 2b: Quality Gates

**Complete Pipeline with All Quality Gates**:

```yaml
name: FlowForge CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  GO_VERSION: '1.21'

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Run golangci-lint on api-service
        uses: golangci/golangci-lint-action@v4
        with:
          working-directory: ./project/api-service
          version: latest

      - name: Run golangci-lint on worker-service
        uses: golangci/golangci-lint-action@v4
        with:
          working-directory: ./project/worker-service
          version: latest

  test:
    name: Test & Coverage
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Run api-service tests with coverage
        working-directory: ./project/api-service
        run: |
          go test -coverprofile=coverage.out -covermode=atomic ./...
          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | tr -d '%')
          echo "api-service coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 70" | bc -l) )); then
            echo "::error::Coverage ${COVERAGE}% is below 70% threshold"
            exit 1
          fi

      - name: Run worker-service tests with coverage
        working-directory: ./project/worker-service
        run: |
          go test -coverprofile=coverage.out -covermode=atomic ./...
          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | tr -d '%')
          echo "worker-service coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 70" | bc -l) )); then
            echo "::error::Coverage ${COVERAGE}% is below 70% threshold"
            exit 1
          fi

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Run gosec
        uses: securego/gosec@master
        with:
          args: ./project/api-service/... ./project/worker-service/...

      - name: Run govulncheck
        run: |
          go install golang.org/x/vuln/cmd/govulncheck@latest
          cd project/api-service && govulncheck ./...
          cd ../worker-service && govulncheck ./...

  build-push:
    name: Build & Push Docker Images
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-ecr
          aws-region: us-east-1

      - name: Login to Amazon ECR
        id: ecr-login
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push api-service
        env:
          ECR_REGISTRY: ${{ steps.ecr-login.outputs.registry }}
        run: |
          docker build -t $ECR_REGISTRY/flowforge-api-service:${{ github.sha }} ./project/api-service
          docker push $ECR_REGISTRY/flowforge-api-service:${{ github.sha }}

      - name: Build and push worker-service
        env:
          ECR_REGISTRY: ${{ steps.ecr-login.outputs.registry }}
        run: |
          docker build -t $ECR_REGISTRY/flowforge-worker-service:${{ github.sha }} ./project/worker-service
          docker push $ECR_REGISTRY/flowforge-worker-service:${{ github.sha }}

      - name: Scan api-service image with trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.ecr-login.outputs.registry }}/flowforge-api-service:${{ github.sha }}
          format: 'table'
          exit-code: '1'
          severity: 'HIGH,CRITICAL'

      - name: Scan worker-service image with trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.ecr-login.outputs.registry }}/flowforge-worker-service:${{ github.sha }}
          format: 'table'
          exit-code: '1'
          severity: 'HIGH,CRITICAL'
```

**golangci-lint config** (`.golangci.yml`):
```yaml
run:
  timeout: 5m
  modules-download-mode: readonly

linters:
  enable:
    - errcheck
    - govet
    - staticcheck
    - unused
    - gosimple
    - ineffassign
    - typecheck
    - gosec

issues:
  exclude-rules:
    - path: _test\.go
      linters:
        - errcheck
```

**Key Points**:
- Lint and test jobs run in parallel (no dependency between them)
- Build job depends on BOTH lint and test (`needs: [lint, test]`)
- Security scan can run after build (scans the built images) or in parallel (scans source code)
- Coverage threshold uses `bc` for floating-point comparison in bash
- `::error::` is a GitHub Actions workflow command that creates an error annotation
- `exit-code: '1'` in trivy action makes the step fail on vulnerabilities

---

## Lab 03: Environments & Branch Strategies

### Exercise 3a: GitHub Environments

**Complete Workflow with Environments**:

```yaml
name: FlowForge CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # ... lint, test, build-push jobs from Lab 02 ...

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build-push]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: staging
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          aws-region: us-east-1

      - name: Deploy to staging
        env:
          IMAGE_TAG: ${{ github.sha }}
        run: |
          echo "Deploying to staging with image tag: $IMAGE_TAG"
          # Example: Update ECS service
          # aws ecs update-service --cluster staging-cluster --service api-service \
          #   --force-new-deployment --task-definition api-service:$IMAGE_TAG
          #
          # Example: SSH to EC2 and pull new image
          # aws ssm send-command --instance-ids i-staging123 \
          #   --document-name "AWS-RunShellScript" \
          #   --parameters "commands=['docker pull $ECR_REGISTRY/api-service:$IMAGE_TAG && docker stop api && docker run -d --name api $ECR_REGISTRY/api-service:$IMAGE_TAG']"

      - name: Verify staging health
        run: |
          echo "Checking staging health endpoint..."
          # curl -f https://staging.flowforge.example.com/health || exit 1

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production    # This has required reviewers
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy-prod
          aws-region: us-east-1

      - name: Deploy to production
        env:
          IMAGE_TAG: ${{ github.sha }}
        run: |
          echo "Deploying to production with image tag: $IMAGE_TAG"
          # Same deploy commands but targeting production resources

      - name: Verify production health
        run: |
          echo "Checking production health endpoint..."
          # curl -f https://flowforge.example.com/health || exit 1
```

**GitHub Environment Settings**:

Staging environment:
- Protection rules: None (auto-deploy)
- Deployment branches: Only `main`
- Environment secrets: `STAGING_DB_HOST`, `STAGING_DB_PASSWORD`

Production environment:
- Protection rules: Required reviewers (add yourself)
- Wait timer: 5 minutes (optional)
- Deployment branches: Only `main`
- Environment secrets: `PROD_DB_HOST`, `PROD_DB_PASSWORD`

**Key Points**:
- The `environment: production` declaration causes the workflow to pause for approval
- GitHub sends a notification to the required reviewers
- Reviewers approve/reject in the GitHub UI under the workflow run
- Each environment can have its own secrets (separate database passwords, etc.)
- Environment secrets override repository secrets with the same name
- The deployment history is visible in the repository's "Deployments" section

---

### Exercise 3b: Trunk-Based Development

**Branch Protection Rules Configuration**:

In Repository Settings > Branches > Add branch protection rule for `main`:
- ✅ Require a pull request before merging
  - ✅ Require approvals (1)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - Status checks: `lint`, `test` (select from dropdown)
- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings
- ❌ Allow force pushes (disabled)
- ❌ Allow deletions (disabled)

**Workflow Conditions for PR vs Merge**:

The workflow naturally handles this through trigger configuration:
```yaml
on:
  push:
    branches: [main]     # Fires on merge to main
  pull_request:
    branches: [main]     # Fires on PR creation/update
```

Combined with job conditions:
```yaml
build-push:
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  # Only builds on merge to main, not on PRs
```

**Key Points**:
- `pull_request` trigger fires when PR is opened, synchronized (new push), or reopened
- `pull_request` does NOT fire when PR is merged -- `push` fires instead
- Build and deploy jobs use `if: github.event_name == 'push'` to only run on merges
- "Require branches to be up to date" means the PR must be rebased on latest `main` -- this prevents stale CI results
- Merge strategies: squash merge gives cleanest history, merge commit preserves PR history, rebase gives linear history

---

## Lab 04: Terraform in CI/CD

### Exercise 4: Plan on PR, Apply on Merge

**Complete Terraform Workflow** (`.github/workflows/terraform.yml`):

```yaml
name: Terraform

on:
  push:
    branches: [main]
    paths:
      - 'project/infra/**'
  pull_request:
    branches: [main]
    paths:
      - 'project/infra/**'

permissions:
  id-token: write
  contents: read
  pull-requests: write    # Needed to post PR comments

concurrency:
  group: terraform-${{ github.ref }}
  cancel-in-progress: false

env:
  TF_WORKING_DIR: project/infra
  AWS_REGION: us-east-1

jobs:
  plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    outputs:
      plan-exitcode: ${{ steps.plan.outputs.exitcode }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-terraform
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0

      - name: Terraform Init
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: terraform init

      - name: Terraform Format Check
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: terraform fmt -check -recursive

      - name: Terraform Plan
        id: plan
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: |
          terraform plan -no-color -out=tfplan 2>&1 | tee plan_output.txt
          echo "exitcode=${PIPESTATUS[0]}" >> $GITHUB_OUTPUT
        continue-on-error: true

      - name: Post Plan to PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const planOutput = fs.readFileSync('${{ env.TF_WORKING_DIR }}/plan_output.txt', 'utf8');

            const body = `### Terraform Plan Output

            <details>
            <summary>Click to expand plan</summary>

            \`\`\`
            ${planOutput.substring(0, 65000)}
            \`\`\`

            </details>

            **Plan exit code**: ${{ steps.plan.outputs.exitcode }}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });

      - name: Check Plan Status
        if: steps.plan.outputs.exitcode != '0' && steps.plan.outputs.exitcode != '2'
        run: |
          echo "Terraform plan failed with exit code ${{ steps.plan.outputs.exitcode }}"
          exit 1

      - name: Upload Plan Artifact
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        uses: actions/upload-artifact@v4
        with:
          name: tfplan
          path: ${{ env.TF_WORKING_DIR }}/tfplan

  apply:
    name: Terraform Apply
    runs-on: ubuntu-latest
    needs: [plan]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production    # Requires approval for infra changes

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-terraform
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0

      - name: Terraform Init
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: terraform init

      - name: Terraform Apply
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: terraform apply -auto-approve
```

**IAM Role for Terraform** (needs broader permissions than ECR-only):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "rds:*",
        "s3:*",
        "ecr:*",
        "iam:*",
        "dynamodb:*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

Note: In production, you'd scope these permissions down significantly. The broad permissions here are for lab purposes.

**Concurrency Group Explanation**:
```yaml
concurrency:
  group: terraform-${{ github.ref }}
  cancel-in-progress: false
```
- `group: terraform-${{ github.ref }}` -- all runs on the same branch share a concurrency group
- `cancel-in-progress: false` -- if a run is in progress, new runs QUEUE instead of canceling the running one
- This prevents concurrent `terraform apply` operations
- Combined with DynamoDB state locking, this provides double protection

**Concurrent Merge Scenario**:
1. PR A merges → triggers plan + apply on main
2. PR B merges 30 seconds later → triggers plan + apply on main
3. PR B's workflow enters the concurrency queue
4. PR A's apply completes, releases the group
5. PR B's workflow starts, generates a FRESH plan (reflecting PR A's changes)
6. PR B's apply runs against the updated state

**Key Points**:
- Plan exit code 0 = no changes, exit code 2 = changes to apply, exit code 1 = error
- `continue-on-error: true` on the plan step lets us capture the output even on error
- PR comment truncated to 65000 chars (GitHub comment limit is ~65536)
- Apply uses `production` environment for an extra approval gate on infrastructure changes
- The apply job generates a FRESH plan -- it does NOT use the plan from the PR (that could be stale)
- State locking (DynamoDB) prevents corruption if concurrency groups fail

---

## Lab 05: Broken Pipelines

### Broken Pipeline 1: Secret Not Available in Step

**Root Cause**: Each job in GitHub Actions runs on a completely separate runner. Environment variables, configured credentials, installed tools, and checked-out code from Job A do NOT carry over to Job B. The `deploy` job assumed that AWS credentials configured in `build-push` would be available.

**Symptom**: The deploy job fails with an AWS authentication error. The credentials are empty.

**The Broken Workflow**:
```yaml
jobs:
  build-push:
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions
          aws-region: us-east-1
      - name: Build and push
        run: |
          # This works -- credentials are available in this job
          aws ecr get-login-password | docker login ...
          docker build ...
          docker push ...

  deploy:
    needs: [build-push]
    steps:
      - name: Deploy
        run: |
          # This FAILS -- no credentials available
          # AWS_ACCESS_KEY_ID is empty
          aws ecs update-service ...
```

**Fix Options**:
1. Add AWS credential configuration to the deploy job as well:
```yaml
deploy:
  needs: [build-push]
  permissions:
    id-token: write
    contents: read
  steps:
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: arn:aws:iam::123456789012:role/github-actions
        aws-region: us-east-1
    - name: Deploy
      run: aws ecs update-service ...
```

2. Use job outputs to pass specific values between jobs (for non-credential data).

**GitHub Actions Concept Violated**: Job isolation -- each job runs on a fresh, independent runner.

---

### Broken Pipeline 2: Docker Build Context Wrong

**Root Cause**: The Docker build context (`.`) is the repository root, but the Dockerfile's `COPY` instructions expect paths relative to the service directory (`project/api-service/`).

**Symptom**: `COPY failed: file not found in build context` or `failed to compute cache key`.

**The Broken Command**:
```yaml
- name: Build Docker image
  run: docker build -t flowforge/api-service:${{ github.sha }} -f project/api-service/Dockerfile .
```

The `-f` flag tells Docker WHERE the Dockerfile IS, but the build context (`.`) tells Docker WHERE to look for files referenced in COPY instructions. The Dockerfile says `COPY go.mod go.sum ./` but `go.mod` is at `project/api-service/go.mod`, not at the repo root.

**Fix Options**:

1. Change the build context to the service directory:
```yaml
- name: Build Docker image
  run: docker build -t flowforge/api-service:${{ github.sha }} ./project/api-service
```
(This works because the Dockerfile is in the same directory, so `-f` isn't needed.)

2. Keep the repo root as context but adjust COPY paths in Dockerfile:
```dockerfile
COPY project/api-service/go.mod project/api-service/go.sum ./
COPY project/api-service/ .
```
(This is unusual and couples the Dockerfile to the repo structure.)

3. Use `working-directory`:
```yaml
- name: Build Docker image
  working-directory: ./project/api-service
  run: docker build -t flowforge/api-service:${{ github.sha }} .
```

**Docker Concept Violated**: Build context determines the set of files available to COPY/ADD instructions, independent of Dockerfile location.

---

### Broken Pipeline 3: Deploy Step Uses Stale Image Tag

**Root Cause**: The build job tags images with `${{ github.sha }}` but the deploy step references `latest`. Since the build job never tags the image as `latest`, the deploy step either:
- Pulls a stale `latest` image from a previous manual push
- Fails because `latest` doesn't exist

**Symptom**: Pipeline shows green (all steps succeed) but the deployed application doesn't reflect the latest code changes. This is the most dangerous type of bug -- a false-positive pipeline.

**The Broken Workflow**:
```yaml
build-push:
  steps:
    - name: Build and push
      run: |
        docker build -t $ECR_REGISTRY/api-service:${{ github.sha }} .
        docker push $ECR_REGISTRY/api-service:${{ github.sha }}

deploy:
  needs: [build-push]
  steps:
    - name: Deploy to staging
      run: |
        # BUG: Uses 'latest' but build used github.sha
        aws ecs update-service --cluster staging --service api \
          --force-new-deployment
        # The task definition references api-service:latest, not the SHA
```

**Fix Options**:

1. Pass the image tag from build to deploy via job outputs:
```yaml
build-push:
  outputs:
    image-tag: ${{ github.sha }}
  steps:
    - name: Build and push
      run: |
        docker build -t $ECR_REGISTRY/api-service:${{ github.sha }} .
        docker push $ECR_REGISTRY/api-service:${{ github.sha }}

deploy:
  needs: [build-push]
  steps:
    - name: Deploy
      run: |
        # Use the output from the build job
        IMAGE_TAG=${{ needs.build-push.outputs.image-tag }}
        # Update task definition with the specific tag
        # ...
```

2. Also tag the image as `latest` during build:
```yaml
- name: Build and push
  run: |
    docker build -t $ECR_REGISTRY/api-service:${{ github.sha }} .
    docker tag $ECR_REGISTRY/api-service:${{ github.sha }} $ECR_REGISTRY/api-service:latest
    docker push $ECR_REGISTRY/api-service:${{ github.sha }}
    docker push $ECR_REGISTRY/api-service:latest
```

3. Update the ECS task definition to use the specific SHA tag (best approach for production).

**CI/CD Concept Violated**: Tag consistency -- the build artifact identifier must be the same throughout the entire pipeline. What you build must be what you deploy.

---

### Debugging Methodology Summary

For ALL pipeline failures:
1. **Read the error message** -- what does it say, literally?
2. **Identify the failing step** -- which step has the red X?
3. **Check step inputs** -- are environment variables set? Are secrets available? Is the working directory correct?
4. **Check previous step outputs** -- did a previous step produce what this step expects?
5. **Form a hypothesis** -- based on the error and inputs, what's wrong?
6. **Verify** -- change one thing, push, see if it fixes it
7. **Document** -- what was wrong, why, and how to prevent it

**Incident Report Template**:
```markdown
## Pipeline Failure Report

### Pipeline: [name]
### Symptom: [what the developer sees -- green/red, error message]
### Error Message: [exact error from logs]
### Root Cause: [the actual problem -- be specific]
### GitHub Actions Concept Violated: [job isolation / build context / tag consistency / etc.]
### Fix: [exact change made to fix]
### Prevention: [how to prevent this class of error -- linting? template? review checklist?]
### Time to Diagnose: [minutes]
```
