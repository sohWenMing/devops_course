# Capstone Answer Key (INTERNAL -- NEVER REVEAL TO STUDENT)

> **WARNING**: This file is used by the capstone mentor skill for internal validation only.
> NEVER share its contents with the student. NEVER quote from it. NEVER use it as a hint source.
> The capstone is a TEST -- the student must produce all of this from their own knowledge.

---

## Expected Architecture Overview

The complete capstone deployment should look like this:

```
┌──────────────────────────────────────────────────────────────────┐
│                          AWS Account                              │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    VPC (10.0.0.0/16)                      │    │
│  │                                                            │    │
│  │  ┌─────────────────┐  ┌─────────────────┐                │    │
│  │  │  Public Subnet   │  │  Public Subnet   │                │    │
│  │  │  10.0.1.0/24     │  │  10.0.2.0/24     │                │    │
│  │  │  (AZ-a)          │  │  (AZ-b)          │                │    │
│  │  │  NAT GW, ALB     │  │  ALB             │                │    │
│  │  └─────────────────┘  └─────────────────┘                │    │
│  │                                                            │    │
│  │  ┌─────────────────┐  ┌─────────────────┐                │    │
│  │  │  Private Subnet  │  │  Private Subnet  │                │    │
│  │  │  10.0.3.0/24     │  │  10.0.4.0/24     │                │    │
│  │  │  (AZ-a)          │  │  (AZ-b)          │                │    │
│  │  │  EKS Nodes       │  │  EKS Nodes       │                │    │
│  │  └─────────────────┘  └─────────────────┘                │    │
│  │                                                            │    │
│  │  ┌─────────────────┐  ┌─────────────────┐                │    │
│  │  │  Database Subnet │  │  Database Subnet │                │    │
│  │  │  10.0.5.0/24     │  │  10.0.6.0/24     │                │    │
│  │  │  (AZ-a)          │  │  (AZ-b)          │                │    │
│  │  │  RDS (Multi-AZ)  │  │  RDS (Standby)   │                │    │
│  │  └─────────────────┘  └─────────────────┘                │    │
│  │                                                            │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐     │
│  │  ECR        │  │  S3 (state)│  │  Secrets Manager       │     │
│  │  api-svc    │  │  + DynamoDB│  │  db-password            │     │
│  │  worker-svc │  │  (locking) │  │  api-key                │     │
│  └────────────┘  └────────────┘  └────────────────────────┘     │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                     EKS Cluster                              │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │ api-service  │  │worker-service│  │  PostgreSQL(RDS) │   │  │
│  │  │ 2+ replicas  │  │ 1+ replica   │  │  (external)      │   │  │
│  │  │ /metrics     │  │ /metrics     │  │                   │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │ Prometheus   │  │ Grafana      │  │ Alertmanager     │   │  │
│  │  │              │  │ dashboards   │  │ webhook/email    │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │ Loki         │  │ Promtail     │  │ ESO              │   │  │
│  │  │ (logs)       │  │ (DaemonSet)  │  │ (secrets sync)   │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │  │
│  │                                                              │  │
│  │  ┌──────────────────────────────────────────────────┐      │  │
│  │  │ Ingress (AWS ALB via ALB Controller)              │      │  │
│  │  │ /api/* → api-service                              │      │  │
│  │  │ TLS termination                                    │      │  │
│  │  └──────────────────────────────────────────────────┘      │  │
│  │                                                              │  │
│  │  NetworkPolicies: default-deny-all + explicit allow          │  │
│  │  RBAC: per-service ServiceAccount + least-privilege Roles    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘

GitHub Actions:
  push → test → lint → scan → build → push ECR → deploy staging → (approval) → deploy prod
  PR   → terraform plan (comment) → merge → terraform apply
```

---

## Deliverable 1: Terraform Module Structure

### Expected Directory Layout

```
project/infra/
├── main.tf                    # Root module -- composes all child modules
├── variables.tf               # Root variables: region, environment, project name, etc.
├── outputs.tf                 # Root outputs: cluster endpoint, ALB DNS, RDS endpoint, ECR URLs
├── terraform.tfvars           # Default values (NOT committed if contains secrets)
├── backend.tf                 # S3 + DynamoDB backend configuration
├── providers.tf               # AWS provider with version constraint + lock file
├── versions.tf                # Terraform version constraint
│
├── modules/
│   ├── vpc/
│   │   ├── main.tf            # VPC, 6 subnets (2 public, 2 private, 2 database), IGW, NAT GW, route tables
│   │   ├── variables.tf       # vpc_cidr, public/private/database subnet CIDRs, AZs, tags
│   │   └── outputs.tf         # vpc_id, subnet_ids (public, private, database), nat_gw_id
│   │
│   ├── security-groups/
│   │   ├── main.tf            # api-sg, worker-sg, db-sg, alb-sg with SG-to-SG references
│   │   ├── variables.tf       # vpc_id, allowed_cidr_blocks
│   │   └── outputs.tf         # sg_ids for each group
│   │
│   ├── eks/
│   │   ├── main.tf            # EKS cluster, managed node group, OIDC provider for IRSA
│   │   ├── variables.tf       # cluster_name, k8s_version, node_instance_type, node_count, subnet_ids
│   │   ├── outputs.tf         # cluster_endpoint, cluster_ca, oidc_provider_arn, node_group_role
│   │   └── iam.tf             # Cluster role, node role, IRSA roles for ESO and ALB controller
│   │
│   ├── database/
│   │   ├── main.tf            # RDS PostgreSQL instance, DB subnet group, parameter group
│   │   ├── variables.tf       # instance_class, db_name, username, engine_version, subnet_ids, sg_id
│   │   └── outputs.tf         # rds_endpoint, rds_port, db_name
│   │
│   ├── ecr/
│   │   ├── main.tf            # ECR repositories for api-service and worker-service, lifecycle policies
│   │   ├── variables.tf       # repository_names, image_tag_mutability, scan_on_push
│   │   └── outputs.tf         # repository_urls, repository_arns
│   │
│   ├── secrets/
│   │   ├── main.tf            # Secrets Manager secrets (containers only, values set outside Terraform)
│   │   ├── variables.tf       # secret_names, recovery_window_in_days
│   │   └── outputs.tf         # secret_arns
│   │
│   └── s3/
│       ├── main.tf            # S3 buckets for artifacts, encrypted with SSE-KMS
│       ├── variables.tf       # bucket_name, versioning, lifecycle_rules
│       └── outputs.tf         # bucket_arn, bucket_name
│
└── environments/
    ├── dev.tfvars              # Smaller instances, single AZ, lower costs
    ├── staging.tfvars          # Production-like but smaller scale
    └── prod.tfvars             # Full production values
```

### Key Terraform Configuration Details

**Backend configuration (backend.tf)**:
```hcl
terraform {
  backend "s3" {
    bucket         = "flowforge-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "flowforge-terraform-locks"
    encrypt        = true
  }
}
```

**EKS module key resources**:
- `aws_eks_cluster` with private endpoint enabled
- `aws_eks_node_group` with desired/min/max capacity
- `aws_iam_openid_connect_provider` for IRSA
- IAM roles for: cluster, node group, ALB controller, ESO, application pods

**VPC module key decisions**:
- 6 subnets across 2 AZs for high availability
- NAT Gateway in public subnet for private subnet internet access
- Database subnets have no internet access (no NAT route)
- Proper tagging for EKS subnet discovery (`kubernetes.io/cluster/<name>` tags)

**Expected `terraform apply` time**: 10-15 minutes (EKS cluster creation is the bottleneck at ~10 min)

---

## Deliverable 2: Complete Docker Configuration

### api-service Dockerfile

```dockerfile
# Build stage
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o api-service .

# Runtime stage
FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /build/api-service /api-service
USER 65534:65534
EXPOSE 8080
ENTRYPOINT ["/api-service"]
```

### worker-service Dockerfile

```dockerfile
# Build stage
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o worker-service .

# Runtime stage
FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /build/worker-service /worker-service
USER 65534:65534
ENTRYPOINT ["/worker-service"]
```

### .dockerignore

```
.git
.gitignore
README.md
docs/
*.md
.env
.env.*
Dockerfile*
docker-compose*
.air.toml
tmp/
vendor/
```

### docker-compose.yml (local development)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: flowforge
      POSTGRES_USER: flowforge
      POSTGRES_PASSWORD: localdev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flowforge"]
      interval: 5s
      timeout: 3s
      retries: 5

  api-service:
    build:
      context: ./api-service
      dockerfile: Dockerfile.dev
    ports:
      - "8080:8080"
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_USER: flowforge
      DB_PASSWORD: localdev
      DB_NAME: flowforge
      LOG_LEVEL: debug
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./api-service:/app

  worker-service:
    build:
      context: ./worker-service
      dockerfile: Dockerfile.dev
    environment:
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_USER: flowforge
      DB_PASSWORD: localdev
      DB_NAME: flowforge
      POLL_INTERVAL: "5s"
      LOG_LEVEL: debug
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./worker-service:/app

volumes:
  pgdata:
```

### Expected image sizes

| Image | Expected Size |
|---|---|
| api-service (scratch) | 8-15 MB |
| api-service (alpine) | 15-25 MB |
| worker-service (scratch) | 8-15 MB |
| worker-service (alpine) | 15-25 MB |

---

## Deliverable 3: Complete CI/CD Pipeline YAML

### .github/workflows/ci-cd.yml

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read
  pull-requests: write

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: flowforge_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Test api-service
        working-directory: project/api-service
        run: go test -v -race -coverprofile=coverage.out ./...
        env:
          DB_HOST: localhost
          DB_PORT: "5432"
          DB_USER: test
          DB_PASSWORD: test
          DB_NAME: flowforge_test
      - name: Check coverage
        working-directory: project/api-service
        run: |
          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
          echo "Coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 70" | bc -l) )); then
            echo "Coverage ${COVERAGE}% is below 70% threshold"
            exit 1
          fi
      - name: Test worker-service
        working-directory: project/worker-service
        run: go test -v -race ./...
        env:
          DB_HOST: localhost
          DB_PORT: "5432"
          DB_USER: test
          DB_PASSWORD: test
          DB_NAME: flowforge_test

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: golangci-lint api-service
        uses: golangci/golangci-lint-action@v6
        with:
          working-directory: project/api-service
      - name: golangci-lint worker-service
        uses: golangci/golangci-lint-action@v6
        with:
          working-directory: project/worker-service

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: gosec api-service
        uses: securego/gosec@master
        with:
          args: ./...
        working-directory: project/api-service
      - name: govulncheck
        run: |
          go install golang.org/x/vuln/cmd/govulncheck@latest
          cd project/api-service && govulncheck ./...
          cd ../worker-service && govulncheck ./...

  build-push:
    needs: [test, lint, security-scan]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-service, worker-service]
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::role/github-actions-role
          aws-region: ap-southeast-1
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      - name: Build and push
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          cd project/${{ matrix.service }}
          docker build -t $ECR_REGISTRY/${{ matrix.service }}:$IMAGE_TAG .
          docker push $ECR_REGISTRY/${{ matrix.service }}:$IMAGE_TAG
      - name: Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.ECR_REGISTRY }}/${{ matrix.service }}:${{ github.sha }}
          format: table
          exit-code: 1
          severity: HIGH,CRITICAL

  deploy-staging:
    needs: [build-push]
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::role/github-actions-role
          aws-region: ap-southeast-1
      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name flowforge-staging --region ap-southeast-1
      - name: Deploy to staging
        run: |
          kubectl set image deployment/api-service api-service=$ECR_REGISTRY/api-service:${{ github.sha }} -n flowforge
          kubectl set image deployment/worker-service worker-service=$ECR_REGISTRY/worker-service:${{ github.sha }} -n flowforge
          kubectl rollout status deployment/api-service -n flowforge --timeout=300s
          kubectl rollout status deployment/worker-service -n flowforge --timeout=300s

  deploy-production:
    needs: [deploy-staging]
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::role/github-actions-role
          aws-region: ap-southeast-1
      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name flowforge-production --region ap-southeast-1
      - name: Deploy to production
        run: |
          kubectl set image deployment/api-service api-service=$ECR_REGISTRY/api-service:${{ github.sha }} -n flowforge
          kubectl set image deployment/worker-service worker-service=$ECR_REGISTRY/worker-service:${{ github.sha }} -n flowforge
          kubectl rollout status deployment/api-service -n flowforge --timeout=300s
          kubectl rollout status deployment/worker-service -n flowforge --timeout=300s
```

### .github/workflows/terraform.yml

```yaml
name: Terraform

on:
  push:
    branches: [main]
    paths: ['project/infra/**']
  pull_request:
    branches: [main]
    paths: ['project/infra/**']

permissions:
  id-token: write
  contents: read
  pull-requests: write

concurrency:
  group: terraform-${{ github.ref }}

jobs:
  plan:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::role/github-actions-terraform-role
          aws-region: ap-southeast-1
      - name: Terraform Init
        working-directory: project/infra
        run: terraform init
      - name: Terraform Plan
        id: plan
        working-directory: project/infra
        run: terraform plan -no-color -out=tfplan 2>&1 | tee plan-output.txt
        continue-on-error: true
      - name: Post plan to PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('project/infra/plan-output.txt', 'utf8');
            const truncated = plan.length > 60000 ? plan.substring(0, 60000) + '\n\n... (truncated)' : plan;
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `### Terraform Plan\n\n<details>\n<summary>Click to expand</summary>\n\n\`\`\`\n${truncated}\n\`\`\`\n\n</details>`
            });
      - name: Check plan status
        if: steps.plan.outcome == 'failure'
        run: exit 1

  apply:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::role/github-actions-terraform-role
          aws-region: ap-southeast-1
      - name: Terraform Init
        working-directory: project/infra
        run: terraform init
      - name: Terraform Apply
        working-directory: project/infra
        run: terraform apply -auto-approve
```

---

## Deliverable 4: Complete Kubernetes Manifest Set

### Expected directory layout

```
project/k8s/
├── namespace.yaml
├── configmap.yaml
├── external-secret.yaml       # or secretstore.yaml + externalsecret.yaml
├── api-deployment.yaml
├── api-service.yaml
├── worker-deployment.yaml
├── worker-service.yaml
├── ingress.yaml
├── network-policies/
│   ├── default-deny.yaml
│   ├── api-service.yaml
│   ├── worker-service.yaml
│   └── dns-egress.yaml
├── rbac/
│   ├── api-serviceaccount.yaml
│   ├── worker-serviceaccount.yaml
│   ├── api-role.yaml
│   ├── api-rolebinding.yaml
│   ├── worker-role.yaml
│   └── worker-rolebinding.yaml
└── monitoring/
    ├── prometheus-config.yaml
    ├── prometheus-deployment.yaml
    ├── prometheus-service.yaml
    ├── grafana-deployment.yaml
    ├── grafana-service.yaml
    ├── alertmanager-config.yaml
    ├── alertmanager-deployment.yaml
    ├── alertmanager-service.yaml
    ├── alerting-rules.yaml
    ├── loki-deployment.yaml
    ├── loki-service.yaml
    ├── promtail-daemonset.yaml
    └── promtail-config.yaml
```

### Key Manifests

**namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: flowforge
  labels:
    app.kubernetes.io/part-of: flowforge
```

**api-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: flowforge
  labels:
    app: api-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-service
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: api-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: api-service
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        fsGroup: 65534
      containers:
        - name: api-service
          image: <ECR_URL>/api-service:<SHA>
          ports:
            - containerPort: 8080
              protocol: TCP
          envFrom:
            - configMapRef:
                name: flowforge-config
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: flowforge-db-credentials
                  key: password
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
```

**worker-deployment.yaml** (similar structure, 1 replica, no ports exposed)

**configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flowforge-config
  namespace: flowforge
data:
  DB_HOST: "flowforge-db.xxxxx.rds.amazonaws.com"
  DB_PORT: "5432"
  DB_USER: "flowforge"
  DB_NAME: "flowforge"
  LOG_LEVEL: "info"
  POLL_INTERVAL: "5s"
```

**external-secret.yaml** (External Secrets Operator):
```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: flowforge
spec:
  provider:
    aws:
      service: SecretsManager
      region: ap-southeast-1
      auth:
        jwt:
          serviceAccountRef:
            name: eso-service-account
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: flowforge-db-credentials
  namespace: flowforge
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: flowforge-db-credentials
  data:
    - secretKey: password
      remoteRef:
        key: flowforge/db-password
```

**default-deny NetworkPolicy**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: flowforge
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

**api-service NetworkPolicy**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-service
  namespace: flowforge
spec:
  podSelector:
    matchLabels:
      app: api-service
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - port: 8080
    - from:
        - podSelector:
            matchLabels:
              app: prometheus
      ports:
        - port: 8080
  egress:
    - to:
        - ipBlock:
            cidr: 10.0.5.0/24  # Database subnet
        - ipBlock:
            cidr: 10.0.6.0/24  # Database subnet AZ-b
      ports:
        - port: 5432
    - to:  # DNS
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
        - port: 53
          protocol: TCP
```

**Ingress**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flowforge-ingress
  namespace: flowforge
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...:certificate/...
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  rules:
    - host: flowforge.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8080
          - path: /health
            pathType: Exact
            backend:
              service:
                name: api-service
                port:
                  number: 8080
```

---

## Deliverable 5: Prometheus/Grafana Configuration

### Go Instrumentation (api-service)

```go
package main

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    httpRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "endpoint", "status"},
    )

    httpRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "Duration of HTTP requests in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "endpoint"},
    )

    activeConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "http_active_connections",
            Help: "Number of active HTTP connections",
        },
    )

    tasksCreatedTotal = promauto.NewCounter(
        prometheus.CounterOpts{
            Name: "tasks_created_total",
            Help: "Total number of tasks created",
        },
    )

    tasksCompletedTotal = promauto.NewCounter(
        prometheus.CounterOpts{
            Name: "tasks_completed_total",
            Help: "Total number of tasks completed",
        },
    )
)
```

### Go Instrumentation (worker-service)

```go
var (
    taskProcessingDuration = promauto.NewHistogram(
        prometheus.HistogramOpts{
            Name:    "task_processing_duration_seconds",
            Help:    "Duration of task processing in seconds",
            Buckets: []float64{0.1, 0.5, 1, 2, 5, 10, 30},
        },
    )

    queueDepth = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "queue_depth",
            Help: "Current number of tasks waiting in the queue",
        },
    )
)
```

### Prometheus ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: flowforge
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
      - /etc/prometheus/rules/*.yml

    scrape_configs:
      - job_name: 'api-service'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names: ['flowforge']
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            regex: api-service
            action: keep
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
            target_label: __address__
            regex: (.+)
            replacement: ${1}:${2}

      - job_name: 'worker-service'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names: ['flowforge']
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            regex: worker-service
            action: keep
```

### Alerting Rules

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alerting-rules
  namespace: flowforge
data:
  alerts.yml: |
    groups:
      - name: flowforge-alerts
        rules:
          - alert: HighErrorRate
            expr: |
              sum(rate(http_requests_total{status=~"5.."}[5m]))
              /
              sum(rate(http_requests_total[5m]))
              > 0.05
            for: 5m
            labels:
              severity: critical
            annotations:
              summary: "High error rate detected"
              description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
              runbook_url: "https://wiki.example.com/runbooks/high-error-rate"

          - alert: HighLatency
            expr: |
              histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
              > 2
            for: 10m
            labels:
              severity: warning
            annotations:
              summary: "High latency detected"
              description: "p99 latency is {{ $value }}s (threshold: 2s)"

          - alert: WorkerQueueGrowing
            expr: queue_depth > 100
            for: 15m
            labels:
              severity: warning
            annotations:
              summary: "Worker queue is growing"
              description: "Queue depth is {{ $value }} (threshold: 100)"
```

### SLO PromQL Expressions

| SLI | PromQL |
|---|---|
| Availability (success rate) | `sum(rate(http_requests_total{status!~"5.."}[30d])) / sum(rate(http_requests_total[30d]))` |
| Error budget remaining | `1 - ((1 - (sum(rate(http_requests_total{status!~"5.."}[30d])) / sum(rate(http_requests_total[30d])))) / (1 - 0.999))` |
| Latency SLI (p99 < 500ms) | `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[30d])) by (le)) < 0.5` |
| Burn rate (1h window) | `(1 - (sum(rate(http_requests_total{status!~"5.."}[1h])) / sum(rate(http_requests_total[1h])))) / (1 - 0.999)` |
| Task processing SLI (<30s) | `histogram_quantile(0.99, sum(rate(task_processing_duration_seconds_bucket[30d])) by (le)) < 30` |

### SLO Targets

| SLO | Target | Error Budget (30 days) |
|---|---|---|
| Availability | 99.9% | 43.2 minutes downtime |
| Latency (p99) | < 500ms | 0.1% of requests may exceed |
| Task processing | < 30s (p99) | 0.1% of tasks may exceed |

---

## Deliverable 6: Security Controls Checklist

### IAM
- [ ] No root account usage (MFA enabled, no access keys)
- [ ] Dedicated IAM user for admin with MFA
- [ ] GitHub Actions uses OIDC role (no static credentials)
- [ ] OIDC trust policy restricted to specific repository and branch
- [ ] EKS node role has minimal permissions
- [ ] IRSA roles for ESO and ALB controller
- [ ] IAM Access Analyzer enabled, all findings addressed
- [ ] CloudTrail enabled for all API calls

### Secrets
- [ ] DB password in AWS Secrets Manager
- [ ] API keys in AWS Secrets Manager
- [ ] External Secrets Operator syncing to K8s
- [ ] No secrets in Git history (verified with `git log -p`)
- [ ] No secrets in Terraform state (using secret containers, not values)
- [ ] Rotation procedure documented and tested

### Containers
- [ ] Multi-stage builds (no build tools in runtime)
- [ ] scratch or distroless base images
- [ ] Non-root user (USER 65534)
- [ ] No CRITICAL vulnerabilities (trivy)
- [ ] Read-only root filesystem
- [ ] All capabilities dropped
- [ ] No privileged containers

### Kubernetes
- [ ] Default deny NetworkPolicies (ingress and egress)
- [ ] Explicit allow policies for each service path
- [ ] DNS egress allowed
- [ ] Dedicated ServiceAccounts (no default)
- [ ] Roles with least privilege (no wildcards)
- [ ] RoleBindings properly scoped
- [ ] Resource requests and limits set
- [ ] Security contexts on all Pods

### Encryption
- [ ] RDS encryption at rest enabled
- [ ] S3 encryption (SSE-KMS) with enforcing bucket policy
- [ ] TLS on Ingress (ALB with ACM certificate)
- [ ] TLS to RDS (require SSL parameter)
- [ ] EKS secrets encryption at rest (KMS)

### CI/CD Security
- [ ] trivy image scan fails on HIGH/CRITICAL
- [ ] gosec Go security linting
- [ ] govulncheck dependency vulnerability check
- [ ] No secrets in workflow logs (masked)
- [ ] OIDC for all AWS access (no static keys)
- [ ] Branch protection: required reviews, status checks

### Incident Response
- [ ] Runbook: Compromised API key (rotate in Secrets Manager, invalidate old, check CloudTrail, update ESO)
- [ ] Runbook: Unauthorized CloudTrail access (identify source, revoke credentials, check for persistence, audit changes)
- [ ] Runbook: Container escape attempt (isolate node, check NetworkPolicies, review Pod security, audit container runtime)
- [ ] Communication plan for each scenario
- [ ] Evidence preservation procedures

---

## Deliverable 7: Documentation Templates

### Architecture Diagram (Expected Content)

The architecture diagram should show:
1. VPC with all 6 subnets across 2 AZs
2. EKS cluster with node groups in private subnets
3. RDS in database subnets with Multi-AZ
4. ALB in public subnets
5. ECR, S3, Secrets Manager as external services
6. Ingress → api-service → PostgreSQL data flow
7. worker-service → PostgreSQL polling flow
8. Prometheus → api-service + worker-service scraping
9. NetworkPolicy boundaries
10. GitHub Actions → ECR → EKS deployment flow

### Deployment Runbook (Expected Sections)

1. **Prerequisites**: AWS account, Terraform installed, kubectl, GitHub repo, AWS CLI
2. **Initial Setup**: Create S3 bucket and DynamoDB for Terraform state (bootstrap)
3. **Infrastructure**: `terraform init && terraform apply` with expected time and output
4. **Kubernetes Setup**: Configure kubeconfig, install ALB controller, install ESO, install Calico
5. **Application Deployment**: Apply K8s manifests in order (namespace → RBAC → config → secrets → deployments → services → ingress → monitoring)
6. **Verification**: curl endpoints, check Prometheus targets, verify Grafana dashboards
7. **CI/CD Setup**: GitHub repository secrets (none -- OIDC), environment configuration
8. **Troubleshooting**: Common issues and their solutions

### Monitoring Guide (Expected Sections)

1. **Dashboard Overview**: What each panel shows and what "normal" looks like
2. **Alert Response**: For each alert, what it means, likely causes, and investigation steps
3. **SLO Monitoring**: How to read the SLO dashboard, when to raise concerns
4. **Log Queries**: Common LogQL queries for debugging
5. **Escalation Path**: When to escalate and to whom

### Security Audit Report (Expected Format)

| Finding ID | Area | Severity | Description | Evidence | Remediation | Status |
|---|---|---|---|---|---|---|
| SEC-001 | IAM | HIGH | Overly permissive S3 policy | Policy JSON | Restrict to specific bucket | Remediated |
| SEC-002 | Containers | MEDIUM | Alpine base image CVE | trivy output | Update to latest alpine | Accepted (low risk) |
| ... | ... | ... | ... | ... | ... | ... |

---

## Exit Gate: Expected Evaluation

### Stranger Test Verification

The student should be able to demonstrate:
1. README has prerequisites, setup steps, and verification commands
2. `terraform apply` runs without errors from a clean state
3. GitHub Actions pipeline triggers and completes successfully
4. API is accessible at the Ingress endpoint
5. Creating a task via API and seeing it processed by worker
6. Prometheus targets all show UP
7. Grafana dashboard displays live data

### Break-and-Recover Expected Behavior

**Pod failure** (kill worker Pod):
- Queue depth increases within 1-2 minutes (visible in Grafana)
- WorkerQueueGrowing alert may fire if queue exceeds threshold
- K8s restarts the Pod (ReplicaSet controller)
- Queue depth returns to normal within minutes
- Detection time: < 2 minutes via monitoring

**Traffic spike** (burst of requests):
- Request rate panel shows dramatic increase
- Latency increases (visible in p95/p99 panels)
- Error rate may increase if capacity is exceeded
- HighLatency or HighErrorRate alerts fire
- System recovers after traffic normalizes
- SLO dashboard shows error budget consumption

**Secret rotation** (rotate DB password):
- Update secret in Secrets Manager
- ESO syncs new value (within refresh interval)
- Restart Pods to pick up new secret (or wait for ESO to trigger)
- Verify DB connectivity restored
- No downtime if done correctly (rolling restart)

### Interview Presentation Key Points

The student should articulate:
- **EKS vs ECS**: K8s portability, ecosystem, community. Trade-off: complexity
- **VPC layout**: 3-tier (public/private/database), 2 AZs for HA. Trade-off: NAT Gateway cost
- **Trunk-based development**: Simpler, faster feedback. Trade-off: requires good CI
- **Prometheus pull model**: Service mesh friendly, target discovery. Trade-off: NAT/firewall complexity
- **External Secrets Operator**: Single source of truth for secrets. Trade-off: additional operator to manage
- **Cost drivers**: EKS control plane ($73/mo), NAT Gateway ($32/mo + data), RDS ($15/mo), node instances
- **At 10x scale**: HPA, cluster autoscaler, multi-region, CDN, read replicas, caching layer

### Security Audit Expected Results

- IAM Access Analyzer: 0 public or cross-account findings
- trivy: 0 CRITICAL, low/no HIGH (with justification for any accepted)
- NetworkPolicy: unauthorized curl connections are blocked
- TLS: all openssl s_client connections succeed with valid certificates
- CloudTrail: only expected API calls from known roles
- Git history: no passwords, API keys, or tokens in any commit
