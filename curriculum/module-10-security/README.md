# Module 10: Security Hardening -- Making FlowForge Production-Safe

> **Duration**: Weeks 16-17  
> **Prerequisites**: Modules 1-9 completed (Linux, Networking, Go App, Docker, AWS, Terraform, CI/CD, Kubernetes, Monitoring)  
> **Link forward**: "This completes the production-readiness story. The Capstone brings everything together"  
> **Link back**: "Your FlowForge stack is deployed, automated, and monitored. But is it *secure*? Could someone steal your database credentials? Exfiltrate customer data? Pivot from a compromised container to your entire AWS account?"

---

## Why Security Hardening?

You have built an impressive system across Modules 1-9. FlowForge runs on Kubernetes, deploys through CI/CD, stores state in RDS, publishes images to ECR, and has monitoring with Prometheus and Grafana. But none of that matters if an attacker can:

- Read your database credentials from a Kubernetes Secret (base64 is not encryption -- remember Module 8 Lab 3b?)
- Escalate from a compromised container to root on the node (because you didn't drop Linux capabilities)
- Move laterally from api-service to PostgreSQL to worker-service (because there are no NetworkPolicies)
- Push a malicious image through your CI/CD pipeline (because there's no security scanning)
- Access your AWS account with overly permissive IAM policies (because you never tightened them from Module 5)

Security is not a feature you bolt on at the end. It's a mindset that should have been present from Module 1. This module makes that explicit -- you'll systematically harden every layer of FlowForge and build the muscle memory to think about security first in every future system you build.

> **Architecture Thinking**: Security has a fundamental tension with usability and velocity. More restrictions mean fewer attack vectors but also slower development, more complex deployments, and harder debugging. The goal is never "maximum security" -- it's **appropriate security** for your threat model. A personal blog and a banking application have very different security requirements. Every security decision should trace back to a specific threat you're mitigating.

---

## Threat Modeling

Before writing a single security rule, you need to understand **what you're protecting and from whom**. This is threat modeling -- a structured way to think about security.

### Assets, Threats, and Mitigations

Every system has **assets** -- things of value that need protection:

- **Data**: Customer task data in PostgreSQL, API responses, logs
- **Credentials**: Database passwords, AWS access keys, API tokens, TLS certificates
- **Infrastructure**: EC2 instances, RDS databases, S3 buckets, Kubernetes clusters
- **Availability**: The ability of FlowForge to serve requests and process tasks

For each asset, you identify **threats** -- things that could harm it -- and **mitigations** -- controls that reduce the risk.

### The STRIDE Framework

STRIDE is a structured approach to identifying threats, developed by Microsoft. Each letter represents a category:

| Category | Description | FlowForge Example |
|---|---|---|
| **S**poofing | Pretending to be someone/something else | Attacker uses stolen API key to create tasks |
| **T**ampering | Modifying data or code without authorization | Attacker modifies task data in transit between api-service and PostgreSQL |
| **R**epudiation | Denying having performed an action | User claims they didn't delete tasks (no audit trail) |
| **I**nformation Disclosure | Exposing data to unauthorized parties | Database credentials leaked in container environment variables visible via `kubectl describe pod` |
| **D**enial of Service | Making the system unavailable | Attacker floods api-service with requests, exhausting connections |
| **E**levation of Privilege | Gaining higher access than authorized | Attacker escapes compromised container to access the node's filesystem |

> **Architecture Thinking**: When threat modeling, ask these questions for every component:
> 1. "Who has access to this?" (authentication)
> 2. "What can they do with that access?" (authorization)
> 3. "What happens if this is compromised?" (blast radius)
> 4. "How would we know if it was compromised?" (detection)
> 5. "How do we respond?" (incident response)

> **Link back to Module 9**: Your monitoring stack (Prometheus, Grafana, Loki) is your detection layer. Anomalous metrics, unexpected log entries, and alerting rules are how you notice that something security-relevant is happening. Monitoring and security are deeply intertwined.

> **AWS SAA Tie-in**: AWS Well-Architected Framework has a "Security" pillar with five areas: Identity and Access Management, Detection, Infrastructure Protection, Data Protection, and Incident Response. These map directly to what you'll cover in this module. The SAA exam tests all five areas.

---

## IAM Hardening

In Module 5, you created IAM users, groups, policies, and roles. You probably made some of them more permissive than necessary to get things working. Now it's time to apply the **principle of least privilege** rigorously.

### Least Privilege

Least privilege means every identity (user, role, service) gets **only the permissions it needs to do its job, and nothing more**. This minimizes the blast radius when credentials are compromised.

Bad: `"Action": "s3:*", "Resource": "*"` (can do anything to any S3 bucket)

Good: `"Action": ["s3:GetObject", "s3:PutObject"], "Resource": "arn:aws:s3:::flowforge-artifacts/*"` (can only read/write objects in one specific bucket)

### CloudTrail

AWS CloudTrail records every API call made to your AWS account -- who did what, when, from where. It's your audit log for AWS.

Key uses:
- **Security auditing**: Who created this EC2 instance? Who modified this IAM policy?
- **Incident investigation**: What did the compromised credentials do?
- **Compliance**: Prove that only authorized changes were made
- **Anomaly detection**: Alert when unusual API patterns occur (e.g., someone calling `iam:CreateUser` at 3am)

### IAM Access Analyzer

IAM Access Analyzer automatically analyzes your resource policies to identify resources shared with external entities. It answers: "Are any of my resources accessible from outside my account?"

This catches common mistakes like:
- S3 buckets with public access
- IAM roles that can be assumed by any AWS account
- KMS keys with overly permissive policies

### Identity-Based vs Resource-Based Policies

**Identity-based policies** are attached to IAM users, groups, or roles. They say "this identity can do X to resource Y."

**Resource-based policies** are attached to resources (S3 buckets, SQS queues, etc.). They say "identity X can do Y to this resource."

When both exist, AWS evaluates them together. An explicit Deny in either one overrides any Allow.

> **Architecture Thinking**: Ask yourself: "If an attacker got hold of every credential in my system, what's the worst they could do?" The answer reveals your blast radius. Least privilege shrinks that blast radius. If the api-service's IAM role can only read from one S3 bucket and write to CloudWatch Logs, a compromised api-service can't delete your RDS database or spin up Bitcoin miners on EC2.

> **Link back to Module 5**: In Lab 1a, you created IAM policies for FlowForge. Were they truly least privilege? Most people start broad to "get things working" and never tighten them. This module fixes that. In Lab 1b, you created an instance profile with S3 read + CloudWatch write + ECR pull -- review whether those permissions are scoped to specific resources.

> **AWS SAA Tie-in**: IAM is tested heavily on the SAA exam. Know the evaluation logic (explicit Deny > explicit Allow > implicit Deny), the difference between identity-based and resource-based policies, and when to use roles vs users. CloudTrail questions focus on "how to audit API calls" and "how to detect unauthorized access."

---

## Secrets Management

Secrets are the keys to your kingdom -- database passwords, API keys, TLS certificates, OAuth tokens. How you manage them determines whether a single leaked secret leads to a minor incident or a catastrophic breach.

### The Problem with Hardcoded Secrets

In earlier modules, you may have:
- Put the database password in an environment variable in `docker-compose.yml`
- Stored the DB password in a Kubernetes Secret (which is just base64-encoded, not encrypted)
- Put AWS credentials in GitHub Secrets (better, but still static)
- Defined secrets as Terraform variables (which end up in state files)

None of these are truly secure for production.

### AWS Secrets Manager

AWS Secrets Manager provides:
- **Centralized secret storage**: One place for all secrets, encrypted with KMS
- **Automatic rotation**: Secrets Manager can rotate database passwords automatically
- **Audit trail**: CloudTrail logs every access to every secret
- **Fine-grained access control**: IAM policies control who can read which secrets
- **Versioning**: Previous secret values are retained for rollback

### Secret Lifecycle

Every secret goes through a lifecycle:
1. **Creation**: Generate with high entropy, store in Secrets Manager
2. **Distribution**: Deliver to applications securely (never in plaintext environment variables)
3. **Rotation**: Change regularly (automated for databases, manual for API keys)
4. **Revocation**: Immediately invalidate when compromised or no longer needed
5. **Cleanup**: Remove from all caches, restart services, verify the old value no longer works

### External Secrets Operator

The External Secrets Operator (ESO) bridges AWS Secrets Manager and Kubernetes. It:
1. Reads secrets from AWS Secrets Manager (or other providers)
2. Creates Kubernetes Secrets automatically
3. Keeps them in sync when the source changes
4. Supports rotation by re-syncing on a schedule

### CSI Secrets Store Driver

An alternative to ESO is the Secrets Store CSI driver, which:
1. Mounts secrets as files in the Pod (not as environment variables)
2. Fetches from AWS Secrets Manager at Pod startup
3. Can auto-rotate by re-fetching periodically
4. Never creates a Kubernetes Secret object (reducing the attack surface)

> **Architecture Thinking**: There's a spectrum of secret management complexity:
> 1. Hardcoded in source code (terrible -- secrets in Git history forever)
> 2. Environment variables in deployment configs (bad -- visible in `kubectl describe pod`)
> 3. Kubernetes Secrets (better -- but base64 is not encryption, visible to anyone with RBAC access)
> 4. External Secrets Operator (good -- secrets live in Secrets Manager, K8s gets copies)
> 5. CSI driver (best -- secrets never persist as K8s objects, mounted as files only)
>
> The right choice depends on your threat model. For FlowForge, ESO or CSI driver with Secrets Manager is the target.

> **Link back to Module 6**: Your Terraform state file contains every secret you've defined as a variable -- including the database password. If someone accesses your S3 state bucket, they get every secret. This is why state encryption and strict access controls matter. In this module, you'll move secrets out of Terraform variables and into Secrets Manager, with Terraform only managing the *reference*, not the value.

> **Link back to Module 8**: In Lab 3b, you created Kubernetes Secrets and noted that base64 is not encryption. Now you'll replace those with proper secret management that fetches from Secrets Manager.

> **AWS SAA Tie-in**: AWS Secrets Manager vs Systems Manager Parameter Store is a common exam question. Secrets Manager supports automatic rotation and cross-account access; Parameter Store is cheaper for non-rotating configuration. Know when to use each.

---

## Container Security

Docker containers provide process isolation, but they are not security boundaries by default. A misconfigured container can give an attacker root access to the host.

### Image Scanning with Trivy

Trivy scans container images for:
- **OS vulnerabilities**: CVEs in the base image's packages (Debian, Alpine, etc.)
- **Application dependencies**: Vulnerabilities in Go modules, Python packages, etc.
- **Misconfigurations**: Dockerfile issues (running as root, exposing unnecessary ports)
- **Secrets**: Accidentally embedded credentials, API keys, private keys

Severity levels: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN. Your pipeline should fail on CRITICAL and HIGH.

### Distroless and Scratch Base Images

Every package in your base image is a potential vulnerability:
- **Ubuntu/Debian**: Hundreds of packages, many vulnerabilities, large attack surface
- **Alpine**: Fewer packages, musl instead of glibc, much smaller
- **Distroless**: Google's images with only the application runtime -- no shell, no package manager, no utilities
- **Scratch**: Empty base image -- your binary and nothing else

For Go services compiled with `CGO_ENABLED=0`, scratch is ideal. The final image contains only your statically-linked binary. No shell means an attacker who exploits your app can't get a shell in the container.

### Read-Only Root Filesystem

By default, containers can write to their filesystem. This allows attackers to:
- Drop malware, backdoors, or cryptocurrency miners
- Modify application binaries
- Create persistence mechanisms

Setting `readOnlyRootFilesystem: true` in the Kubernetes security context prevents all writes. If your app needs to write (logs, temp files), use `emptyDir` volumes for specific paths.

### Linux Capabilities

Linux capabilities break up root privileges into granular units. By default, Docker containers get a subset of capabilities. For hardened containers:

1. **Drop all capabilities**: `drop: ["ALL"]`
2. **Add back only what's needed**: Most Go HTTP services need zero additional capabilities
3. **Never use privileged mode**: `privileged: false`

### Security Contexts in Kubernetes

A Kubernetes security context defines privilege and access control settings for a Pod or Container:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 65534           # nobody user
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

Each field closes a specific attack vector:
- `runAsNonRoot`: Prevents root in container (container escape → root on node)
- `readOnlyRootFilesystem`: Prevents writing malware to disk
- `allowPrivilegeEscalation`: Prevents gaining higher privileges than the parent process
- `capabilities.drop ALL`: Removes all Linux capabilities (raw sockets, network admin, etc.)

> **Architecture Thinking**: There's a trade-off between security and debuggability. A scratch-based image with no shell and a read-only filesystem is very secure, but you can't `kubectl exec` into it to debug. Some teams use distroless for production and Alpine for staging. What would you choose for FlowForge, and why?

> **Link back to Module 4**: In Lab 5a, you ran `trivy` for the first time and made containers run as non-root. This module goes deeper -- you'll actually fix vulnerabilities, switch to distroless/scratch, implement read-only filesystems, and drop all capabilities. Module 4 was awareness; Module 10 is hardening.

> **Link back to Module 1**: Linux capabilities trace directly back to Module 1's coverage of processes and permissions. The `root` user has all capabilities; dropping them is like applying chmod/chown at the kernel level.

> **AWS SAA Tie-in**: AWS ECS and EKS both support security contexts. ECS uses task definitions with `readonlyRootFilesystem` and `privileged` fields. The SAA exam tests understanding of container security best practices, especially running as non-root and image scanning.

---

## Kubernetes Network Policies

By default, Kubernetes allows every Pod to talk to every other Pod in the cluster. This is convenient for development but catastrophic for security -- if an attacker compromises one Pod, they can reach everything.

### Default Deny

The first step is a **default deny** policy that blocks all traffic. Then you explicitly allow only the traffic that's necessary:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}       # Matches all pods in the namespace
  policyTypes:
    - Ingress
    - Egress
```

This says: "For every Pod in this namespace, deny all incoming and outgoing traffic." After applying this, nothing can talk to anything -- then you add specific allow rules.

### Ingress and Egress Rules

- **Ingress rules**: Control incoming traffic to a set of Pods
- **Egress rules**: Control outgoing traffic from a set of Pods

Rules use **label selectors** to target Pods and **port specifications** to control which ports are allowed.

### Label Selectors and Pod-to-Pod Isolation

NetworkPolicies use labels to identify both the Pods being protected and the Pods allowed to connect:

```yaml
spec:
  podSelector:
    matchLabels:
      app: postgresql     # This policy applies to PostgreSQL pods
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api-service    # Only api-service can connect
      ports:
        - port: 5432
```

For FlowForge, the minimum required communication:
- api-service → PostgreSQL (port 5432)
- worker-service → PostgreSQL (port 5432)
- External → api-service (port 8080 via Ingress)
- api-service → external DNS (for name resolution)
- worker-service → external DNS (for name resolution)

Everything else should be blocked.

> **Architecture Thinking**: NetworkPolicies are like security groups (Module 5) but at the Kubernetes level. In both cases, you start with "deny all" and explicitly open only what's needed. The question is always: "Does this service *need* to talk to that service?" If not, block it. If you can't justify the connection, it shouldn't exist.

> **Link back to Module 2**: In Lab 3a, you wrote iptables rules for FlowForge -- allow SSH, allow api-service port, allow PostgreSQL only from api-service. NetworkPolicies are the same concept, but expressed declaratively in YAML instead of imperatively with iptables commands. Same security thinking, different abstraction layer.

> **Link back to Module 5**: Security groups controlled traffic between EC2 instances and RDS. NetworkPolicies control traffic between Kubernetes Pods. Both implement the same principle: explicit allow, implicit deny.

> **AWS SAA Tie-in**: EKS supports Kubernetes NetworkPolicies when using a CNI plugin like Calico or Cilium. The default Amazon VPC CNI doesn't enforce NetworkPolicies natively -- you need a policy engine. The SAA exam tests understanding of network segmentation at multiple levels (VPC, subnet, security group, NACL, and Kubernetes NetworkPolicies).

---

## Kubernetes RBAC

Kubernetes Role-Based Access Control (RBAC) governs who (or what) can do what within the cluster.

### ServiceAccounts

Every Pod in Kubernetes runs as a **ServiceAccount**. By default, all Pods in a namespace use the `default` ServiceAccount, which may have more permissions than any single service needs.

Best practice: Create a dedicated ServiceAccount for each service:
- `flowforge-api` ServiceAccount for api-service
- `flowforge-worker` ServiceAccount for worker-service
- Each gets only the permissions it actually needs

### Roles and ClusterRoles

- **Role**: Grants permissions within a specific **namespace**. Use for service-specific access.
- **ClusterRole**: Grants permissions **cluster-wide**. Use for cross-namespace access or cluster-level resources.

A Role defines a set of permissions:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: flowforge
  name: api-service-role
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "watch", "list"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get"]
```

### RoleBindings

A RoleBinding connects a ServiceAccount (or user/group) to a Role:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: flowforge
  name: api-service-binding
subjects:
  - kind: ServiceAccount
    name: flowforge-api
    namespace: flowforge
roleRef:
  kind: Role
  name: api-service-role
  apiGroup: rbac.authorization.k8s.io
```

### Least Privilege for RBAC

Apply the same least-privilege thinking as IAM:
1. What Kubernetes API resources does this service actually need?
2. What verbs does it need? (get, list, watch, create, update, delete)
3. Can access be scoped to a namespace? (Role, not ClusterRole)
4. Does this service need to access Secrets directly, or should secrets come from an external source?

Most application Pods need very few Kubernetes API permissions. They don't call the Kubernetes API at all -- they're just HTTP servers. The main reason for dedicated ServiceAccounts is to prevent using the `default` ServiceAccount and to integrate with IAM (IRSA for EKS).

> **Architecture Thinking**: RBAC has the same structure as IAM: identity (ServiceAccount/User), permissions (Role/Policy), and binding (RoleBinding/Policy attachment). If you understand one, you understand the other. The question is always: "What's the minimum set of permissions this identity needs?"

> **Link back to Module 5**: IAM users, roles, and policies map directly to K8s ServiceAccounts, Roles, and RoleBindings. IAM governs AWS API access; RBAC governs Kubernetes API access. Both implement least privilege. In EKS, they integrate via IRSA (IAM Roles for ServiceAccounts).

> **AWS SAA Tie-in**: The SAA exam tests understanding of IRSA -- how a Kubernetes ServiceAccount can assume an IAM role to access AWS resources without static credentials. This is the bridge between K8s RBAC and AWS IAM.

---

## Encryption at Rest and in Transit

Encryption protects data in two states:
- **At rest**: Data stored on disk (RDS databases, S3 objects, EBS volumes)
- **In transit**: Data moving between services (API calls, database queries, inter-service communication)

### RDS Encryption

RDS encryption uses AWS KMS to encrypt the underlying storage, automated backups, read replicas, and snapshots. Once enabled:
- Data is encrypted transparently -- your application doesn't change
- You choose a KMS key (default or custom)
- Performance impact is minimal (encryption happens at the storage layer)
- **Cannot be enabled after creation** -- you must create an encrypted instance and migrate

### S3 Encryption

S3 offers several encryption options:
- **SSE-S3**: Amazon manages the keys. Simplest, good default.
- **SSE-KMS**: You manage the keys via KMS. Supports key rotation, audit trail, and access control.
- **SSE-C**: Customer provides the key with each request. You manage everything.

For FlowForge, SSE-KMS is the best balance of security and manageability.

### TLS Between Services

In production, all communication between services should be encrypted with TLS:
- Client → API (HTTPS via Ingress TLS termination)
- API → PostgreSQL (TLS connection with certificate verification)
- Worker → PostgreSQL (TLS connection with certificate verification)
- Service → AWS APIs (already HTTPS)

You can verify TLS with `openssl s_client`:
```
openssl s_client -connect <host>:<port> -showcerts
```

This shows the certificate chain, cipher suite, and protocol version.

### Certificate Inspection

Understanding certificates is crucial for security:
- **Subject**: Who the certificate is for
- **Issuer**: Who signed it (the Certificate Authority)
- **Validity**: When it expires (expired certs = outages!)
- **SANs**: Subject Alternative Names (which domains the cert covers)
- **Chain**: The trust path from the server cert to a root CA

> **Architecture Thinking**: Encryption at rest protects against physical theft (someone walks off with a hard drive) and logical access (someone accesses the storage directly, bypassing the application). Encryption in transit protects against eavesdropping and man-in-the-middle attacks. Both are necessary -- encrypting at rest but not in transit means someone sniffing network traffic sees plaintext.

> **Link back to Module 2**: In Lab 3d, you generated self-signed certificates and configured HTTPS. You used `openssl s_client` to inspect the TLS handshake. That same skill applies here -- but now you're verifying TLS for every connection in the FlowForge stack, not just one.

> **Link back to Module 5**: RDS encryption should have been enabled when you created the database in Module 5, but if it wasn't, you'll fix that now. S3 bucket encryption should have been configured in Lab 3c.

> **AWS SAA Tie-in**: Encryption is heavily tested on the SAA exam. Know the S3 encryption types (SSE-S3, SSE-KMS, SSE-C), when to use each, KMS key types (AWS-managed vs customer-managed), and the fact that RDS encryption must be specified at creation time (or you migrate to a new encrypted instance).

---

## Security Scanning in CI/CD

The earlier you catch security issues, the cheaper they are to fix. This is called **shift-left security** -- moving security checks left (earlier) in the development pipeline.

### Shift-Left Security

Traditional security: Review and pen-test before release (expensive, slow, late).
Shift-left security: Scan and test continuously as part of the build pipeline (fast, automated, early).

Your CI/CD pipeline (Module 7) already builds, tests, and deploys. Now you add security as a mandatory stage.

### Trivy in CI/CD

Trivy scans Docker images for vulnerabilities. In your GitHub Actions pipeline:
1. Build the Docker image
2. Run `trivy image --severity HIGH,CRITICAL --exit-code 1` on it
3. If trivy finds HIGH or CRITICAL vulnerabilities, the pipeline fails
4. Developers must fix the vulnerabilities before merging

### gosec

`gosec` is a Go security scanner that finds common coding mistakes:
- SQL injection (string concatenation in queries)
- Hardcoded credentials
- Insecure TLS configurations
- Unhandled errors
- Use of weak cryptographic functions

### govulncheck

`govulncheck` checks your Go dependencies against the Go Vulnerability Database:
- Identifies known vulnerabilities in imported packages
- Only reports vulnerabilities in code paths your application actually uses (not just any vulnerable dependency)
- More precise than general dependency scanners

### Pipeline Failure on HIGH Severity

The pipeline should be configured as a quality gate:
- **CRITICAL/HIGH**: Pipeline fails. Must fix before merge.
- **MEDIUM**: Warning. Tracked for future fix.
- **LOW**: Informational. Logged but doesn't block.

> **Architecture Thinking**: Every security scan adds time to the pipeline. A full trivy scan might take 1-2 minutes, gosec another 30 seconds, govulncheck 20 seconds. Is this acceptable? For most teams, yes -- a few minutes of scanning saves hours of incident response. But if your pipeline takes 30 minutes and developers are blocked, you may need to optimize (cache scan results, run only on changed files, parallelize). The key question: "What's the cost of a missed vulnerability vs the cost of pipeline time?"

> **Link back to Module 7**: In Lab 2b, you added trivy scanning and quality gates to the pipeline. This module ensures those gates are strict enough (fail on HIGH, not just CRITICAL) and adds Go-specific security tools (gosec, govulncheck) that you didn't set up before.

> **AWS SAA Tie-in**: AWS provides native security scanning for ECR images (Basic Scanning with Clair, Enhanced Scanning with Amazon Inspector). The SAA exam asks about automated vulnerability management -- ECR scanning is often the answer for container-based architectures.

---

## Incident Response Runbooks

Security incidents will happen. The question is whether your response is chaotic or systematic. A **runbook** is a predefined procedure that tells you exactly what to do when a specific incident occurs.

### The Incident Response Lifecycle

Based on NIST and industry best practices:

1. **Detection**: How do you know an incident is happening?
   - Alerting rules from Module 9 (unusual error rates, unauthorized access patterns)
   - CloudTrail anomaly alerts
   - External reports (bug bounty, customer complaints)

2. **Containment**: Stop the bleeding without destroying evidence
   - Revoke compromised credentials immediately
   - Isolate affected systems (but don't terminate -- you need forensics)
   - Block malicious IPs or traffic patterns

3. **Eradication**: Remove the threat
   - Patch the vulnerability that was exploited
   - Remove any backdoors or malware
   - Rotate all potentially compromised credentials

4. **Recovery**: Restore normal operations
   - Redeploy from known-good images
   - Verify system integrity
   - Gradually restore traffic
   - Monitor closely for recurrence

5. **Post-Mortem (Lessons Learned)**: Learn from the incident
   - What happened? (timeline)
   - How was it detected?
   - What was the impact?
   - What could have prevented it?
   - What will we change? (action items with owners and deadlines)

### Runbook Structure

A good runbook includes:
- **Trigger**: What event or alert initiates this runbook?
- **Severity assessment**: How to determine the severity
- **Step-by-step actions**: Numbered steps with commands, not vague guidance
- **Communication plan**: Who to notify and when
- **Escalation path**: When to involve management, legal, or external parties
- **Evidence preservation**: What logs, screenshots, and artifacts to capture

> **Architecture Thinking**: Runbooks should be tested. An untested runbook is a hypothesis, not a plan. Schedule periodic "fire drills" where someone simulates an incident and the team follows the runbook. You'll find gaps -- unclear steps, missing access, wrong assumptions. Fix them before a real incident.

> **Link back to Module 9**: Your monitoring stack is the first line of detection. The failure simulation in Lab 5 (killed worker Pod, exhausted DB connections, artificial latency) taught you to diagnose from dashboards. Now you'll write formal runbooks that start with "Check the FlowForge Grafana dashboard" and continue through containment and recovery.

> **AWS SAA Tie-in**: The SAA exam covers AWS-specific incident response services: CloudTrail (audit), GuardDuty (threat detection), Security Hub (aggregated findings), and Config (compliance). Understanding the incident response lifecycle helps you choose the right AWS service for each phase.

---

## Security Audit Methodology

A security audit is a systematic review of your entire system's security posture. It's not a one-time activity -- it should happen regularly and after significant changes.

### Systematic Review Approach

A thorough audit covers every layer:

1. **IAM & Access Control**: Are policies least-privilege? Are there unused users/roles? Is MFA enabled?
2. **Network Security**: Are security groups/NACLs/NetworkPolicies restrictive? Is there unnecessary public exposure?
3. **Secrets Management**: Are secrets in a proper vault? Is rotation configured? Are old secrets revoked?
4. **Container Security**: Are images scanned? Are containers non-root? Read-only filesystem? Capabilities dropped?
5. **CI/CD Security**: Is the pipeline scanning for vulnerabilities? Do security gates block deployments?
6. **Data Protection**: Is encryption enabled at rest and in transit? Are backups encrypted?
7. **Monitoring & Detection**: Are security-relevant events logged? Are alerts configured for anomalies?
8. **Incident Response**: Do runbooks exist? Have they been tested?

### Findings Classification

Audit findings are classified by severity:
- **CRITICAL**: Exploitable now, high impact (e.g., publicly accessible database, hardcoded production credentials in Git)
- **HIGH**: Exploitable with moderate effort, significant impact (e.g., overly permissive IAM policy, containers running as root)
- **MEDIUM**: Potential risk, moderate impact (e.g., missing encryption at rest, no secret rotation)
- **LOW**: Best practice violation, minimal immediate impact (e.g., unused IAM user, missing tags)
- **INFORMATIONAL**: Observation, no immediate risk (e.g., documentation gaps, inconsistent naming)

### Remediation

Each finding needs:
- **Description**: What the issue is
- **Evidence**: How you found it (command output, screenshot, log entry)
- **Risk**: What could happen if exploited
- **Remediation**: Specific steps to fix it
- **Timeline**: When it should be fixed (CRITICAL = immediately, HIGH = this sprint, etc.)
- **Owner**: Who is responsible for fixing it

> **Architecture Thinking**: A security audit is like a code review for your infrastructure. The goal isn't to find zero issues -- it's to find all issues, prioritize them, and fix the important ones. A clean audit report doesn't mean the system is secure; it means the known issues are addressed. There are always unknown unknowns.

> **Link forward to Capstone**: In the Capstone, one of the exit gates is "Security audit produces zero unaddressed HIGH/CRITICAL findings." The audit methodology you learn here is exactly what you'll apply there.

> **AWS SAA Tie-in**: AWS Trusted Advisor, Security Hub, Config Rules, and Inspector automate parts of the security audit. The SAA exam asks about using these services to maintain security compliance. Understanding manual audit methodology helps you know what the automated tools are checking.

---

## Summary: Defense in Depth

Security is not a single layer -- it's many layers working together. If one fails, others catch the threat:

```
┌─────────────────────────────────────────────────┐
│  Layer 7: Incident Response (Runbooks, Drills)  │
├─────────────────────────────────────────────────┤
│  Layer 6: CI/CD Security (trivy, gosec, gates)  │
├─────────────────────────────────────────────────┤
│  Layer 5: Monitoring & Detection (Prometheus,   │
│           Grafana, Loki, CloudTrail, Alerts)     │
├─────────────────────────────────────────────────┤
│  Layer 4: K8s Security (NetworkPolicy, RBAC,    │
│           SecurityContext, Secrets)               │
├─────────────────────────────────────────────────┤
│  Layer 3: Container Security (trivy, non-root,  │
│           distroless, read-only, capabilities)   │
├─────────────────────────────────────────────────┤
│  Layer 2: AWS Security (IAM, SGs, NACLs,        │
│           Encryption, Secrets Manager, CloudTrail)│
├─────────────────────────────────────────────────┤
│  Layer 1: Network Security (TLS, firewalls,     │
│           subnets, DNS)                           │
├─────────────────────────────────────────────────┤
│  Layer 0: Linux Security (permissions, users,   │
│           capabilities, SSH)                      │
└─────────────────────────────────────────────────┘
```

Every module you've completed contributed a security layer. Module 10 makes them all explicit, tightens them, and adds the ones that were missing.

> **Architecture Thinking**: When evaluating any system's security, walk through the layers bottom-up. Ask at each layer: "What controls exist? What threats do they mitigate? What gaps remain?" The layers should overlap -- so that a failure at one layer doesn't mean a complete breach. This is defense in depth.

---

## What's Next?

In the labs, you'll systematically harden FlowForge across every layer:

- **Lab 01**: Threat model the entire FlowForge system, then harden IAM
- **Lab 02**: Migrate to proper secrets management and harden containers
- **Lab 03**: Implement Kubernetes NetworkPolicies and RBAC
- **Lab 04**: Enable encryption everywhere and add security scanning to CI/CD
- **Lab 05**: Write incident response runbooks and perform a full security audit

After completing Module 10, you'll be ready for the **Capstone** -- deploying FlowForge as a fully automated, monitored, and secured production system with zero guidance.
