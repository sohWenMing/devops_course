# Module 10: Security Hardening -- Answer Key

> **INTERNAL USE ONLY**: This file is used by the Socratic mentor skill to validate student work and calibrate hints. NEVER reveal this content directly to the student.

---

## Exercise 1a: Threat Model for FlowForge

### Complete Threat Model

#### System Diagram (ASCII)

```
                    ┌─────────────────── TRUST BOUNDARY: External ───────────────────┐
                    │                                                                  │
  [Users/Clients] ──┼── HTTPS ──► [Ingress/LB] ──── HTTP ──► [api-service]           │
                    │                                            │                     │
                    │                                            │ TCP/5432            │
                    │                                            ▼                     │
                    │              [worker-service] ──────► [PostgreSQL (RDS)]         │
                    │                    ▲                                              │
                    │                    │ polls queue                                  │
                    │                    │                                              │
                    └────────────────────┼──────────────────────────────────────────────┘
                                         │
  ┌── TRUST BOUNDARY: CI/CD ──┐          │
  │ [GitHub Actions] ──► [ECR] ├──────── images ──────────────────┘
  │       │                    │
  │       ▼                    │
  │ [Terraform] ──► [AWS APIs] │
  └────────────────────────────┘

  ┌── TRUST BOUNDARY: Monitoring ──┐
  │ [Prometheus] ──► scrapes metrics│
  │ [Grafana]    ──► dashboards     │
  │ [Loki]       ──► log aggregation│
  │ [Alertmanager]──► alerts        │
  └─────────────────────────────────┘
```

Trust boundaries:
1. External → Ingress (public internet to cluster)
2. Ingress → api-service (Ingress controller to application)
3. api-service → PostgreSQL (application to database)
4. worker-service → PostgreSQL (worker to database)
5. CI/CD → ECR → Kubernetes (build pipeline to deployment target)
6. Developer → AWS Console/CLI (human to cloud infrastructure)
7. Monitoring → Application Pods (scraping internal metrics)

#### Asset Inventory

| Asset Category | Specific Assets | Sensitivity |
|---|---|---|
| Data | Task data (names, descriptions, statuses), API request/response data | Medium |
| Credentials | DB password, AWS access keys, GitHub tokens, TLS certificates, ECR auth tokens | Critical |
| Infrastructure | EC2 instances, RDS database, S3 buckets, EKS cluster, Kind cluster | High |
| Container Images | api-service image, worker-service image in ECR | High |
| Configuration | Terraform state, K8s manifests, CI/CD workflows, environment variables | High |
| Availability | API uptime, worker processing, database connectivity | High |
| Audit Logs | CloudTrail logs, K8s audit logs, application logs | Medium |

#### STRIDE Threat Analysis (15+ Threats)

| # | Component | STRIDE | Threat | Likelihood | Impact | Risk |
|---|---|---|---|---|---|---|
| 1 | api-service | Spoofing | Attacker uses stolen API token to impersonate a legitimate user | Medium | High | High |
| 2 | api-service | Tampering | SQL injection modifies task data in PostgreSQL | Low | Critical | Medium |
| 3 | api-service | Information Disclosure | Error messages leak database schema or internal paths | Medium | Medium | Medium |
| 4 | api-service | Denial of Service | HTTP flood exhausts connections or memory | High | High | Critical |
| 5 | api-service | Elevation of Privilege | Container escape via kernel exploit grants node access | Low | Critical | Medium |
| 6 | PostgreSQL | Spoofing | Unauthorized Pod connects to database (no NetworkPolicy) | High | Critical | Critical |
| 7 | PostgreSQL | Tampering | Direct database modification bypassing application logic | Low | High | Medium |
| 8 | PostgreSQL | Information Disclosure | Unencrypted data at rest exposed via snapshot or disk access | Medium | High | High |
| 9 | worker-service | Tampering | Malicious task payload causes worker to execute arbitrary code | Low | Critical | Medium |
| 10 | worker-service | Denial of Service | Poison pill task crashes worker repeatedly (CrashLoopBackOff) | Medium | Medium | Medium |
| 11 | CI/CD Pipeline | Spoofing | Compromised GitHub token pushes malicious image to ECR | Low | Critical | Medium |
| 12 | CI/CD Pipeline | Tampering | Modified workflow file bypasses security scanning | Medium | High | High |
| 13 | Kubernetes | Information Disclosure | kubectl get secret reveals base64 secrets to anyone with access | High | Critical | Critical |
| 14 | AWS IAM | Elevation of Privilege | Overly permissive IAM role allows lateral movement | High | Critical | Critical |
| 15 | Ingress | Spoofing | TLS certificate not validated, enabling MITM | Medium | High | High |
| 16 | ECR | Tampering | Attacker pushes modified image with backdoor | Low | Critical | Medium |
| 17 | CloudTrail | Repudiation | Attacker disables CloudTrail to hide actions | Low | High | Medium |
| 18 | Terraform State | Information Disclosure | State file in S3 contains plaintext secrets | High | Critical | Critical |

#### Top 5 Priority Threats

1. **Kubernetes Secrets readable as base64** (CRITICAL) → Mitigation: External Secrets Operator + Secrets Manager
2. **Overly permissive IAM policies** (CRITICAL) → Mitigation: Least privilege audit + IAM Access Analyzer
3. **Terraform state contains plaintext secrets** (CRITICAL) → Mitigation: Move secrets to Secrets Manager, encrypt state bucket
4. **No NetworkPolicies allow lateral movement** (CRITICAL) → Mitigation: Default deny + explicit allow rules
5. **No security scanning in CI/CD** (HIGH) → Mitigation: trivy + gosec + govulncheck in pipeline

---

## Exercise 1b: IAM Hardening

### Tightened IAM Policies

#### api-service Instance Profile (Before)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "logs:*",
        "ecr:*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### api-service Instance Profile (After)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReadArtifacts",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::flowforge-artifacts",
        "arn:aws:s3:::flowforge-artifacts/*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:us-east-1:ACCOUNT_ID:log-group:/flowforge/api-service:*"
    },
    {
      "Sid": "ECRPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability"
      ],
      "Resource": "arn:aws:ecr:us-east-1:ACCOUNT_ID:repository/flowforge-api-service"
    },
    {
      "Sid": "ECRAuth",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "SecretsRead",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:flowforge/production/db-*"
    }
  ]
}
```

#### CI/CD OIDC Role (After)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": [
        "arn:aws:ecr:us-east-1:ACCOUNT_ID:repository/flowforge-api-service",
        "arn:aws:ecr:us-east-1:ACCOUNT_ID:repository/flowforge-worker-service"
      ]
    },
    {
      "Sid": "ECRAuth",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "TerraformState",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::flowforge-terraform-state",
        "arn:aws:s3:::flowforge-terraform-state/*"
      ]
    },
    {
      "Sid": "TerraformLocking",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/flowforge-terraform-locks"
    }
  ]
}
```

### CloudTrail Setup

```bash
# Create S3 bucket for CloudTrail logs
aws s3api create-bucket \
  --bucket flowforge-cloudtrail-logs \
  --region us-east-1

# Set bucket policy to allow CloudTrail to write
aws s3api put-bucket-policy \
  --bucket flowforge-cloudtrail-logs \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AWSCloudTrailAclCheck",
        "Effect": "Allow",
        "Principal": {"Service": "cloudtrail.amazonaws.com"},
        "Action": "s3:GetBucketAcl",
        "Resource": "arn:aws:s3:::flowforge-cloudtrail-logs"
      },
      {
        "Sid": "AWSCloudTrailWrite",
        "Effect": "Allow",
        "Principal": {"Service": "cloudtrail.amazonaws.com"},
        "Action": "s3:PutObject",
        "Resource": "arn:aws:s3:::flowforge-cloudtrail-logs/AWSLogs/ACCOUNT_ID/*",
        "Condition": {"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}}
      }
    ]
  }'

# Create CloudTrail trail
aws cloudtrail create-trail \
  --name flowforge-trail \
  --s3-bucket-name flowforge-cloudtrail-logs \
  --is-multi-region-trail \
  --enable-log-file-validation

# Start logging
aws cloudtrail start-logging --name flowforge-trail

# Verify trail status
aws cloudtrail get-trail-status --name flowforge-trail

# Query recent events
aws cloudtrail lookup-events \
  --max-results 10 \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=iam.amazonaws.com
```

### IAM Access Analyzer

```bash
# Create analyzer
aws accessanalyzer create-analyzer \
  --analyzer-name flowforge-analyzer \
  --type ACCOUNT

# List findings
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:ACCOUNT_ID:analyzer/flowforge-analyzer

# Archive a finding (if intentional external access)
aws accessanalyzer update-findings \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:ACCOUNT_ID:analyzer/flowforge-analyzer \
  --ids <finding-id> \
  --status ARCHIVED
```

---

## Exercise 2a: Secrets Management

### Secrets Manager Setup

```bash
# Create database password secret
aws secretsmanager create-secret \
  --name flowforge/production/db-password \
  --description "FlowForge production database password" \
  --secret-string "$(openssl rand -base64 32)" \
  --tags Key=Project,Value=FlowForge Key=Environment,Value=production

# Create database connection string secret
aws secretsmanager create-secret \
  --name flowforge/production/db-connection \
  --description "FlowForge production database connection string" \
  --secret-string '{"host":"flowforge-db.xxxxx.us-east-1.rds.amazonaws.com","port":"5432","dbname":"flowforge","username":"flowforge","password":"REPLACE_WITH_GENERATED"}'

# Retrieve a secret
aws secretsmanager get-secret-value \
  --secret-id flowforge/production/db-password \
  --query SecretString --output text
```

### Terraform Configuration (Secret Container Only)

```hcl
# secrets.tf -- manages the secret container, NOT the value
resource "aws_secretsmanager_secret" "db_password" {
  name        = "flowforge/${var.environment}/db-password"
  description = "FlowForge ${var.environment} database password"

  tags = {
    Project     = "FlowForge"
    Environment = var.environment
  }
}

# Initial secret version -- use ignore_changes so Terraform
# doesn't track the actual value after initial creation
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = "CHANGE_ME_AFTER_CREATION"

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# IAM policy for api-service to read secrets
resource "aws_iam_policy" "api_secrets_read" {
  name        = "flowforge-api-secrets-read"
  description = "Allow api-service to read its Secrets Manager secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadSecrets"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn,
          aws_secretsmanager_secret.db_connection.arn
        ]
      }
    ]
  })
}
```

### External Secrets Operator Manifests

```yaml
# Install ESO (via Helm or manifests -- here using kubectl apply)
# kubectl apply -f https://raw.githubusercontent.com/external-secrets/external-secrets/main/deploy/crds/bundle.yaml
# kubectl apply -f https://raw.githubusercontent.com/external-secrets/external-secrets/main/deploy/manifests/external-secrets.yaml

---
# secret-store.yaml -- configures ESO to read from AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: flowforge
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: flowforge-eso  # ServiceAccount with IRSA annotation

---
# external-secret-db-password.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-password
  namespace: flowforge
spec:
  refreshInterval: 1h  # Re-sync from Secrets Manager every hour
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: flowforge-db-password  # K8s Secret that will be created
    creationPolicy: Owner
  data:
    - secretKey: password  # Key in the K8s Secret
      remoteRef:
        key: flowforge/production/db-password  # Name in Secrets Manager

---
# external-secret-db-connection.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-connection
  namespace: flowforge
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: flowforge-db-connection
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: flowforge/production/db-connection  # JSON secret, each key becomes a K8s Secret key
```

### Updated Deployment (Using ESO-Created Secret)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: flowforge
spec:
  template:
    spec:
      containers:
        - name: api-service
          env:
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: flowforge-db-connection
                  key: host
            - name: DB_PORT
              valueFrom:
                secretKeyRef:
                  name: flowforge-db-connection
                  key: port
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: flowforge-db-password
                  key: password
```

### Rotation Verification

```bash
# Update the secret in Secrets Manager
aws secretsmanager put-secret-value \
  --secret-id flowforge/production/db-password \
  --secret-string "$(openssl rand -base64 32)"

# Wait for ESO to sync (up to refreshInterval)
# Or force immediate sync:
kubectl annotate externalsecret db-password \
  force-sync=$(date +%s) --overwrite -n flowforge

# Verify the K8s Secret was updated
kubectl get secret flowforge-db-password -n flowforge -o jsonpath='{.data.password}' | base64 -d

# Pods may need restart to pick up new env var value:
kubectl rollout restart deployment/api-service -n flowforge
```

---

## Exercise 2b: Container Security

### Trivy Scan Commands

```bash
# Full scan of current image
trivy image flowforge-api-service:latest

# Scan only HIGH and CRITICAL
trivy image --severity HIGH,CRITICAL flowforge-api-service:latest

# Scan with exit code for CI
trivy image --severity HIGH,CRITICAL --exit-code 1 flowforge-api-service:latest

# Table output for readability
trivy image --format table --severity HIGH,CRITICAL flowforge-api-service:latest

# JSON output for programmatic analysis
trivy image --format json --output results.json flowforge-api-service:latest
```

### Hardened Dockerfile (Scratch)

```dockerfile
# Build stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Copy dependency files first (layer caching)
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build static binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -o /api-service ./cmd/api

# Runtime stage -- scratch (empty image)
FROM scratch

# Copy CA certificates for HTTPS calls
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy timezone data
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Copy the binary
COPY --from=builder /api-service /api-service

# Run as non-root (nobody user, UID 65534)
USER 65534:65534

EXPOSE 8080

ENTRYPOINT ["/api-service"]
```

### Hardened Dockerfile (Distroless)

```dockerfile
# Build stage
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s' \
    -o /api-service ./cmd/api

# Runtime stage -- distroless
FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /api-service /api-service

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/api-service"]
```

### Image Size Comparison

| Base Image | Image Size | Vulnerability Count | Has Shell | Has Package Manager |
|---|---|---|---|---|
| ubuntu:22.04 | ~180MB | ~60-100 | Yes | Yes |
| alpine:3.19 | ~15MB | ~5-15 | Yes | Yes |
| distroless/static | ~5MB | ~0-2 | No | No |
| scratch | ~3MB (binary only) | 0 (OS) | No | No |

### Complete Security Context

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: flowforge
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      serviceAccountName: flowforge-api
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        runAsGroup: 65534
        fsGroup: 65534
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: api-service
          image: ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/flowforge-api-service:SHA
          ports:
            - containerPort: 8080
          securityContext:
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: tmp
              mountPath: /tmp
          resources:
            requests:
              cpu: 100m
              memory: 64Mi
            limits:
              cpu: 500m
              memory: 128Mi
      volumes:
        - name: tmp
          emptyDir: {}
```

---

## Exercise 3a: NetworkPolicies

### Default Deny All

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

### PostgreSQL Ingress Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-db-ingress
  namespace: flowforge
spec:
  podSelector:
    matchLabels:
      app: postgresql
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api-service
        - podSelector:
            matchLabels:
              app: worker-service
      ports:
        - protocol: TCP
          port: 5432
```

### api-service Ingress Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-ingress
  namespace: flowforge
spec:
  podSelector:
    matchLabels:
      app: api-service
  policyTypes:
    - Ingress
  ingress:
    # From Ingress controller
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
    # From Prometheus for metrics scraping
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
          podSelector:
            matchLabels:
              app: prometheus
      ports:
        - protocol: TCP
          port: 8080
```

### api-service Egress Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-egress
  namespace: flowforge
spec:
  podSelector:
    matchLabels:
      app: api-service
  policyTypes:
    - Egress
  egress:
    # To PostgreSQL
    - to:
        - podSelector:
            matchLabels:
              app: postgresql
      ports:
        - protocol: TCP
          port: 5432
    # DNS resolution (kube-dns in kube-system)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

### worker-service Egress Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-worker-egress
  namespace: flowforge
spec:
  podSelector:
    matchLabels:
      app: worker-service
  policyTypes:
    - Egress
  egress:
    # To PostgreSQL
    - to:
        - podSelector:
            matchLabels:
              app: postgresql
      ports:
        - protocol: TCP
          port: 5432
    # DNS
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

### worker-service Ingress Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-worker-ingress
  namespace: flowforge
spec:
  podSelector:
    matchLabels:
      app: worker-service
  policyTypes:
    - Ingress
  ingress:
    # From Prometheus for metrics scraping only
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
          podSelector:
            matchLabels:
              app: prometheus
      ports:
        - protocol: TCP
          port: 8080
```

### Verification Commands

```bash
# Install Calico on Kind
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

# Wait for Calico to be ready
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n kube-system --timeout=120s

# Apply default deny
kubectl apply -f default-deny-all.yaml

# Verify FlowForge is broken (expected)
kubectl exec -it deploy/api-service -n flowforge -- curl -s http://postgresql:5432
# Should timeout or fail

# Apply allow policies
kubectl apply -f allow-db-ingress.yaml
kubectl apply -f allow-api-ingress.yaml
kubectl apply -f allow-api-egress.yaml
kubectl apply -f allow-worker-egress.yaml
kubectl apply -f allow-worker-ingress.yaml

# Verify allowed: api-service → PostgreSQL
kubectl exec -it deploy/api-service -n flowforge -- nc -zv postgresql 5432
# Should succeed

# Verify denied: api-service → worker-service
kubectl exec -it deploy/api-service -n flowforge -- nc -zv worker-service 8080
# Should fail (timeout)

# Verify denied: temporary debug Pod → PostgreSQL
kubectl run debug --image=busybox -n flowforge --rm -it -- nc -zv postgresql 5432
# Should fail (blocked by default deny)

# Verify denied: api-service → external internet
kubectl exec -it deploy/api-service -n flowforge -- curl -s https://example.com
# Should fail (no egress to internet)

# Verify end-to-end task flow still works
curl -X POST http://<ingress>/api/tasks -d '{"name":"test"}'
curl http://<ingress>/api/tasks
# Should work end to end
```

---

## Exercise 3b: RBAC

### ServiceAccounts

```yaml
# service-accounts.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flowforge-api
  namespace: flowforge
  labels:
    app: api-service
automountServiceAccountToken: false

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flowforge-worker
  namespace: flowforge
  labels:
    app: worker-service
automountServiceAccountToken: false

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flowforge-postgresql
  namespace: flowforge
  labels:
    app: postgresql
automountServiceAccountToken: false
```

### Roles (Minimal -- Most Services Need Zero K8s API Permissions)

```yaml
# roles.yaml
# api-service: needs to read ConfigMaps for non-secret config
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-service-role
  namespace: flowforge
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "watch", "list"]
    resourceNames: ["flowforge-api-config"]  # Restrict to specific ConfigMap

---
# worker-service: same pattern
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: worker-service-role
  namespace: flowforge
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "watch", "list"]
    resourceNames: ["flowforge-worker-config"]

---
# postgresql: zero K8s API permissions needed
# (No Role created -- just a ServiceAccount for identity)
```

### RoleBindings

```yaml
# role-bindings.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api-service-binding
  namespace: flowforge
subjects:
  - kind: ServiceAccount
    name: flowforge-api
    namespace: flowforge
roleRef:
  kind: Role
  name: api-service-role
  apiGroup: rbac.authorization.k8s.io

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: worker-service-binding
  namespace: flowforge
subjects:
  - kind: ServiceAccount
    name: flowforge-worker
    namespace: flowforge
roleRef:
  kind: Role
  name: worker-service-role
  apiGroup: rbac.authorization.k8s.io
```

### Updated Deployment with ServiceAccount

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: flowforge
spec:
  template:
    spec:
      serviceAccountName: flowforge-api
      automountServiceAccountToken: false  # Redundant if set on SA, but explicit
      containers:
        - name: api-service
          # ... rest of container spec
```

### RBAC Verification

```bash
# Check current ServiceAccount for each Pod
kubectl get pods -n flowforge -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.serviceAccountName}{"\n"}{end}'

# Verify api-service can read its ConfigMap (if automountServiceAccountToken were true)
kubectl auth can-i get configmaps --as=system:serviceaccount:flowforge:flowforge-api -n flowforge
# yes

# Verify api-service CANNOT list secrets
kubectl auth can-i get secrets --as=system:serviceaccount:flowforge:flowforge-api -n flowforge
# no

# Verify api-service CANNOT delete pods
kubectl auth can-i delete pods --as=system:serviceaccount:flowforge:flowforge-api -n flowforge
# no

# Verify postgresql SA has no permissions
kubectl auth can-i get configmaps --as=system:serviceaccount:flowforge:flowforge-postgresql -n flowforge
# no

kubectl auth can-i get secrets --as=system:serviceaccount:flowforge:flowforge-postgresql -n flowforge
# no
```

### Role vs ClusterRole Explanation

**Role**: Grants permissions within a single namespace. Used for namespace-scoped resources.
- Example: api-service reading ConfigMaps in the `flowforge` namespace.

**ClusterRole**: Grants permissions cluster-wide or across namespaces.
- Example: A monitoring agent that needs to list Pods in ALL namespaces.
- Example: Accessing cluster-scoped resources like Nodes or PersistentVolumes.

**FlowForge services use Roles** because:
- They only operate within the `flowforge` namespace
- They don't need to access resources in other namespaces
- Namespace scoping limits blast radius if a ServiceAccount is compromised

---

## Exercise 4a: Encryption

### RDS Encryption Verification

```bash
# Check if existing instance is encrypted
aws rds describe-db-instances \
  --db-instance-identifier flowforge-db \
  --query 'DBInstances[0].StorageEncrypted'
# Expected: true

# If not encrypted, migration process:
# 1. Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier flowforge-db \
  --db-snapshot-identifier flowforge-db-unencrypted-snap

# 2. Copy snapshot with encryption
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier flowforge-db-unencrypted-snap \
  --target-db-snapshot-identifier flowforge-db-encrypted-snap \
  --kms-key-id alias/aws/rds

# 3. Restore from encrypted snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier flowforge-db-encrypted \
  --db-snapshot-identifier flowforge-db-encrypted-snap

# 4. Update connection strings, verify, then delete old instance
```

### S3 Encryption

```bash
# Enable default encryption
aws s3api put-bucket-encryption \
  --bucket flowforge-artifacts \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "aws:kms",
          "KMSMasterKeyID": "alias/aws/s3"
        },
        "BucketKeyEnabled": true
      }
    ]
  }'

# Enforce encryption via bucket policy
aws s3api put-bucket-policy \
  --bucket flowforge-artifacts \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "DenyUnencryptedUploads",
        "Effect": "Deny",
        "Principal": "*",
        "Action": "s3:PutObject",
        "Resource": "arn:aws:s3:::flowforge-artifacts/*",
        "Condition": {
          "StringNotEquals": {
            "s3:x-amz-server-side-encryption": ["aws:kms", "AES256"]
          }
        }
      }
    ]
  }'

# Verify encryption on uploaded object
aws s3api head-object \
  --bucket flowforge-artifacts \
  --key test-file.txt
# Should show "ServerSideEncryption": "aws:kms"
```

### TLS Verification Commands

```bash
# Verify Ingress HTTPS
curl -v https://<ingress-endpoint>/health 2>&1 | grep "SSL connection"
# Expected: SSL connection using TLSv1.3 / ...

# Verify RDS TLS
openssl s_client -connect <rds-endpoint>:5432 -starttls postgres -showcerts
# Should show certificate chain

# Verify from inside api-service Pod
kubectl exec -it deploy/api-service -n flowforge -- \
  openssl s_client -connect postgresql:5432 -starttls postgres

# Check certificate details
openssl s_client -connect <host>:443 -showcerts 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName

# Example output:
# subject=CN = *.us-east-1.rds.amazonaws.com
# issuer=CN = Amazon RDS us-east-1 Root CA RSA2048 G1
# notBefore=Jan 15 00:00:00 2025 GMT
# notAfter=Jan 15 23:59:59 2026 GMT
# X509v3 Subject Alternative Name:
#     DNS:*.us-east-1.rds.amazonaws.com
```

### Terraform Encryption Config

```hcl
resource "aws_db_instance" "flowforge" {
  # ... existing config ...
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn  # or use default: omit this line
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}
```

---

## Exercise 4b: CI/CD Security Scanning

### Complete Pipeline YAML with Security Scanning

```yaml
name: FlowForge CI/CD with Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read
  security-events: write  # For SARIF upload

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - name: Run tests (api-service)
        working-directory: project/api-service
        run: go test -v -race -coverprofile=coverage.out ./...

      - name: Check coverage threshold
        working-directory: project/api-service
        run: |
          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
          echo "Coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 70" | bc -l) )); then
            echo "Coverage ${COVERAGE}% is below 70% threshold"
            exit 1
          fi

      - name: Run tests (worker-service)
        working-directory: project/worker-service
        run: go test -v -race ./...

  security-scan-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      # gosec -- Go security scanner
      - name: Install gosec
        run: go install github.com/securego/gosec/v2/cmd/gosec@latest

      - name: Run gosec (api-service)
        working-directory: project/api-service
        run: gosec -severity medium -confidence medium -fmt json -out gosec-results.json ./... || true

      - name: Check gosec results
        working-directory: project/api-service
        run: |
          HIGH_COUNT=$(cat gosec-results.json | jq '[.Issues[] | select(.severity == "HIGH" or .severity == "CRITICAL")] | length')
          echo "HIGH/CRITICAL issues: ${HIGH_COUNT}"
          if [ "$HIGH_COUNT" -gt 0 ]; then
            cat gosec-results.json | jq '.Issues[] | select(.severity == "HIGH" or .severity == "CRITICAL")'
            exit 1
          fi

      - name: Run gosec (worker-service)
        working-directory: project/worker-service
        run: gosec -severity medium -confidence medium ./...

      # govulncheck -- Go vulnerability checker
      - name: Install govulncheck
        run: go install golang.org/x/vuln/cmd/govulncheck@latest

      - name: Run govulncheck (api-service)
        working-directory: project/api-service
        run: govulncheck ./...

      - name: Run govulncheck (worker-service)
        working-directory: project/worker-service
        run: govulncheck ./...

  build-and-scan-image:
    runs-on: ubuntu-latest
    needs: [test, security-scan-code]
    steps:
      - uses: actions/checkout@v4

      - name: Build api-service image
        run: |
          docker build \
            -t flowforge-api-service:${{ github.sha }} \
            -f project/api-service/Dockerfile \
            project/api-service

      - name: Trivy scan api-service
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'flowforge-api-service:${{ github.sha }}'
          format: 'table'
          exit-code: '1'
          severity: 'HIGH,CRITICAL'

      - name: Build worker-service image
        run: |
          docker build \
            -t flowforge-worker-service:${{ github.sha }} \
            -f project/worker-service/Dockerfile \
            project/worker-service

      - name: Trivy scan worker-service
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'flowforge-worker-service:${{ github.sha }}'
          format: 'table'
          exit-code: '1'
          severity: 'HIGH,CRITICAL'

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [build-and-scan-image]
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - name: Deploy to staging
        run: echo "Deploy to staging..."
        # ... actual deployment steps
```

### gosec Expected Output

```
[gosec] 2025/01/15 10:30:00 analyzer: Loaded analyzers: G101-G601
Results:

[project/api-service/handlers/tasks.go:45] - G201: SQL string concatenation (Confidence: HIGH, Severity: MEDIUM)
  > query := "SELECT * FROM tasks WHERE id = " + id

Fix: Use parameterized queries:
  query := "SELECT * FROM tasks WHERE id = $1"
  row := db.QueryRow(query, id)
```

### govulncheck Expected Output

```
govulncheck is a tool for finding known vulnerabilities.

Scanning your code and 52 packages across 8 modules for known vulnerabilities...

No vulnerabilities found.
```

---

## Exercise 5a: Incident Response Runbooks

### Runbook 1: Compromised API Key

```markdown
# Incident Response Runbook: Compromised AWS API Key

## Trigger
- CloudTrail alert: API calls from unfamiliar IP address using CI/CD credentials
- GuardDuty finding: Credential compromise detected
- Unusual billing spike

## Severity Assessment
- P1 (Critical) if: data accessed, resources modified, or credentials used for privileged operations
- P2 (High) if: reconnaissance only (describe/list calls) with no data access

## Detection (5-10 minutes)

1. Confirm the alert is real:
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIA... \
     --max-results 20

2. Check the source IP:
   - Is it a known IP (office, VPN, AWS service)?
   - whois <source-ip>

3. Check what operations were performed:
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIA... \
     --query 'Events[].{Time:EventTime,Event:EventName,Source:EventSource}'

## Containment (15-30 minutes)

1. IMMEDIATELY deactivate the compromised access key:
   aws iam update-access-key \
     --user-name ci-cd-user \
     --access-key-id AKIA... \
     --status Inactive

2. If using IAM user (not OIDC), delete the key entirely:
   aws iam delete-access-key \
     --user-name ci-cd-user \
     --access-key-id AKIA...

3. Restrict the user's permissions to prevent further damage:
   aws iam put-user-policy \
     --user-name ci-cd-user \
     --policy-name DenyAll \
     --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"*","Resource":"*"}]}'

4. Note: CI/CD pipeline will break. This is expected and acceptable.

## Eradication (1-4 hours)

1. Full CloudTrail audit of compromised key:
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIA... \
     --start-time 2025-01-01T00:00:00Z \
     --end-time 2025-01-15T23:59:59Z

2. Check for backdoors:
   - New IAM users: aws iam list-users
   - New roles: aws iam list-roles
   - New policies: aws iam list-policies --scope Local
   - New access keys on existing users: aws iam list-access-keys --user-name <each-user>

3. Check for resource creation:
   - New EC2 instances: aws ec2 describe-instances
   - New Lambda functions: aws lambda list-functions
   - New S3 buckets: aws s3 ls

4. Check for data exfiltration:
   - S3 access logs (if enabled)
   - RDS slow query logs
   - VPC Flow Logs for large outbound transfers

## Recovery (1-4 hours)

1. Generate new credentials (prefer OIDC over static keys):
   - If not already using OIDC, set up OIDC federation now (see Module 7 Lab 2a)
   - If static keys are needed: aws iam create-access-key --user-name ci-cd-user

2. Update GitHub Secrets with new credentials (or configure OIDC)

3. Run CI/CD pipeline to verify it works

4. Verify no unauthorized resources remain

## Communication
- Immediately: Notify team lead and security team
- Within 1 hour: Notify engineering management
- If data breach confirmed: Legal/compliance team

## Evidence Preservation
- Export CloudTrail events to S3 before any cleanup
- Screenshot any Console findings
- Save GuardDuty finding details

## Post-Mortem
- How was the key compromised? (Git commit, laptop theft, phishing)
- Where was the key stored? (GitHub Secret, local file, env var)
- Action items: Migrate to OIDC, enable key rotation, add IP restrictions
```

### Runbook 2: Unauthorized CloudTrail Access (Root Account)

(Similar structure to above, focused on root account lockdown, MFA verification, full account audit, credential rotation, and organizational controls like AWS Organizations SCPs)

### Runbook 3: Container Escape Attempt

(Similar structure, focused on Pod isolation with kubectl cordon/drain, image digest verification against ECR, node forensics, K8s audit log review, and security context hardening improvements)

---

## Exercise 5b: Security Audit Report Template

```markdown
# FlowForge Security Audit Report

**Date**: 2025-XX-XX
**Auditor**: [Student Name]
**Scope**: Full FlowForge stack (AWS, Kubernetes, CI/CD, Application)

## Executive Summary

Overall security posture: **Moderate → Strong** (after remediations)
Total findings: 12 (0 Critical, 2 High, 5 Medium, 3 Low, 2 Informational)
After remediation: 0 Critical, 0 High, 3 Medium (accepted risk), 3 Low, 2 Informational

## Findings

### F-001: IAM policy allows s3:* on all resources
- **Severity**: HIGH
- **Category**: IAM
- **Description**: CI/CD IAM role has Action: s3:* on Resource: *
- **Evidence**: `aws iam get-policy-version --policy-arn arn:aws:iam::XXXX:policy/cicd-policy --version-id v1`
- **Risk**: Compromised CI/CD credentials could access/delete any S3 bucket
- **Remediation**: Scope to specific bucket ARNs and specific actions (GetObject, PutObject)
- **Status**: REMEDIATED (new policy applied, verified with policy simulator)

### F-002: Kubernetes Secrets contain base64-encoded DB password
- **Severity**: HIGH
- **Category**: Secrets Management
- **Description**: DB password stored as native K8s Secret, readable by anyone with kubectl access
- **Evidence**: `kubectl get secret db-credentials -o yaml` shows base64-encoded password
- **Risk**: Any user/service with K8s Secret read access can decode the password
- **Remediation**: Migrate to External Secrets Operator pulling from AWS Secrets Manager
- **Status**: REMEDIATED (ESO installed, verified Secret is synced from Secrets Manager)

### F-003: Container images use alpine base with 8 MEDIUM vulnerabilities
- **Severity**: MEDIUM
- **Category**: Container Security
- **Description**: api-service and worker-service use alpine:3.19 with known CVEs
- **Evidence**: `trivy image flowforge-api-service:latest` shows 8 MEDIUM findings
- **Risk**: Potential exploitation of OS-level vulnerabilities
- **Remediation**: Switch to distroless/scratch base images
- **Status**: REMEDIATED (switched to scratch, trivy shows 0 vulnerabilities)

(... continue for all findings ...)

## Remediation Summary

| Severity | Found | Remediated | Accepted Risk | Remaining |
|----------|-------|------------|---------------|-----------|
| CRITICAL | 0 | 0 | 0 | 0 |
| HIGH | 2 | 2 | 0 | 0 |
| MEDIUM | 5 | 3 | 2 | 0 |
| LOW | 3 | 1 | 2 | 0 |
| INFO | 2 | 0 | 2 | 0 |

## Accepted Risks

### F-007: etcd not encrypted in Kind cluster
- **Risk**: LOW (Kind is local development, not production)
- **Compensating control**: EKS encrypts etcd by default in production
- **Review date**: Before Capstone production deployment

## Recommendations

1. Consider implementing Falco for runtime container security monitoring
2. Set up automated secret rotation schedule (90-day maximum)
3. Add Pod Security Standards (PSS) admission controller
4. Consider OPA/Gatekeeper for policy enforcement
5. Implement VPC Flow Logs for network traffic analysis
```

---

## Key Explanations

### Role vs ClusterRole
- **Role**: Namespace-scoped. Use for application services that only need access within their namespace.
- **ClusterRole**: Cluster-scoped. Use for cluster-level resources (Nodes, PersistentVolumes) or when a service needs access across multiple namespaces (e.g., a monitoring agent listing all Pods).

### Shift-Left Security
Moving security testing earlier in the development lifecycle (towards the "left" of the timeline: code → build → test → deploy → production). Benefits: cheaper to fix, faster feedback, prevents vulnerable code from reaching production. Challenges: pipeline time increases, potential for false positives blocking development, requires developer security awareness.

### Defense in Depth
Multiple overlapping security layers. If one fails, others still protect the system:
- Linux permissions → Container security contexts → K8s RBAC → K8s NetworkPolicies → AWS Security Groups → AWS IAM → Encryption → Monitoring/Detection → Incident Response

### Secret Lifecycle
1. **Creation**: Generate with high entropy (e.g., `openssl rand -base64 32`), store in Secrets Manager
2. **Distribution**: ESO or CSI driver delivers to Pods, never plaintext in manifests
3. **Rotation**: Change regularly, verify application picks up new value
4. **Revocation**: Immediately invalidate when compromised
5. **Cleanup**: Remove from all caches, restart Pods, verify old value doesn't work
