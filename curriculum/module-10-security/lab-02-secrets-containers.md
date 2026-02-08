# Lab 02: Secrets Management & Container Security

> **Objective**: Migrate all hardcoded secrets to AWS Secrets Manager with Kubernetes integration, then harden container images and runtime security.  
> **Prerequisites**: Module 5 (AWS), Module 6 (Terraform), Module 8 (Kubernetes) completed, Lab 01 done  
> **Time estimate**: 3-4 hours  
> **Produces**: Secrets Manager secrets, Terraform configs for secrets, External Secrets Operator manifests, hardened container images, security context configs

---

## Exercise 2a: Secrets Management with AWS Secrets Manager

### Objective

Migrate all hardcoded secrets to AWS Secrets Manager. Update Terraform to manage the secrets. Update Kubernetes to pull secrets from Secrets Manager using the External Secrets Operator (ESO) or the CSI Secrets Store driver. Verify that secret rotation works.

### Background

Throughout this course, you've handled secrets in various ways -- environment variables in docker-compose, Kubernetes Secrets (base64-encoded), Terraform variables (stored in state). None of these are production-grade. AWS Secrets Manager provides centralized, encrypted, auditable, rotatable secret storage.

> **Link back to Module 6**: Your Terraform state file in S3 contains every secret you've passed as a variable. This is a major security risk -- anyone who can read the state bucket can read your database password. The fix: store secrets in Secrets Manager and have Terraform only reference them, not contain them.

> **Link back to Module 8**: In Lab 3b, you created Kubernetes Secrets and acknowledged that base64 is not encryption. Anyone with `kubectl get secret -o yaml` access can read them. The fix: never store the actual secret value in Kubernetes -- pull it from Secrets Manager at runtime.

### What You'll Do

1. **Inventory all secrets in FlowForge**:
   - Database password (PostgreSQL)
   - Database connection string
   - API authentication tokens (if any)
   - AWS credentials (should already be using OIDC/IRSA, not static keys)
   - Any other credentials or sensitive configuration
   - Document where each secret currently lives (env var, K8s Secret, Terraform variable, etc.)

2. **Create secrets in AWS Secrets Manager**:
   - For each secret identified, create a Secrets Manager secret
   - Use meaningful naming convention (e.g., `flowforge/production/db-password`, `flowforge/staging/db-password`)
   - Set appropriate descriptions and tags
   - Generate strong values (don't reuse the old ones -- this is a rotation event)

3. **Update Terraform to manage secrets**:
   - Create Terraform resources for each Secrets Manager secret
   - **Important**: Terraform should create the *secret* (the container), but the *secret value* should be set outside Terraform (via CLI or console) so it doesn't end up in state
   - Alternatively, use `aws_secretsmanager_secret_version` with `lifecycle { ignore_changes = [secret_string] }` to manage initial creation but not track the value
   - Create IAM policies that allow your services to read their specific secrets (and no others)

4. **Install and configure the External Secrets Operator (ESO)** in your Kind cluster:
   - Install ESO using its manifests or Helm chart
   - Create a `SecretStore` resource that configures ESO to read from AWS Secrets Manager
   - For each secret, create an `ExternalSecret` resource that:
     - References the Secrets Manager secret by name
     - Creates a corresponding Kubernetes Secret
     - Sets a sync interval (how often to check for updates)
   - Verify that the Kubernetes Secrets are created automatically

   **Alternative: CSI Secrets Store Driver**:
   - If you prefer, install the Secrets Store CSI driver instead of ESO
   - Create `SecretProviderClass` resources for each secret
   - Mount secrets as files in your Pod volumes
   - This approach avoids creating Kubernetes Secret objects entirely

5. **Update FlowForge deployments** to use the new secrets:
   - Remove hardcoded environment variables with secret values
   - Reference the Kubernetes Secrets created by ESO (or use volume mounts from CSI driver)
   - Verify that api-service and worker-service start correctly with secrets from Secrets Manager
   - Verify the full task flow still works (create task → worker processes → verify in DB)

6. **Test secret rotation**:
   - Change a secret value in Secrets Manager (e.g., the database password)
   - Observe how ESO syncs the new value to Kubernetes
   - Verify that the application picks up the new value (may require Pod restart depending on your configuration)
   - Document the rotation process: how long does it take from secret change to application using the new value?

7. **Clean up old secrets**:
   - Remove base64-encoded secrets from any Kubernetes manifest files
   - Remove secret values from Terraform variable files
   - Verify that no secrets remain in Git history (discuss: how would you handle this if they were already committed?)

### Expected Outcome

- All FlowForge secrets stored in AWS Secrets Manager (not in K8s manifests, Terraform state, or env files)
- External Secrets Operator (or CSI driver) installed and syncing secrets to Kubernetes
- FlowForge services start and function correctly using secrets from Secrets Manager
- Secret rotation tested and documented (change value in SM → verify app uses new value)
- IAM policies scoped so each service can only read its own secrets
- No secret values in Git, Terraform state, or Kubernetes manifest files

### Checkpoint Questions

- [ ] Can you explain the secret lifecycle (creation, distribution, rotation, revocation, cleanup)?
- [ ] What's the difference between External Secrets Operator and the CSI Secrets Store driver? When would you choose each?
- [ ] If you rotate the database password in Secrets Manager, what happens to running Pods? How do they get the new value?
- [ ] Why is it important that Terraform doesn't store the secret value in state? What would an attacker gain if they accessed your state file?
- [ ] If someone asks you to set up secrets management for a new project from scratch, could you do it without referencing this lab?

---

## Exercise 2b: Container Security Hardening

### Objective

Scan container images with trivy and fix all HIGH/CRITICAL vulnerabilities. Switch to distroless or scratch base images. Implement read-only root filesystems, drop all Linux capabilities, and configure security contexts in Kubernetes.

### Background

In Module 4, you learned about container security basics -- running as non-root and basic trivy scanning. Now you'll go much deeper: fix actual vulnerabilities, minimize your attack surface with scratch/distroless images, and lock down the container runtime with Kubernetes security contexts.

> **Link back to Module 4**: In Lab 2b, you built multi-stage images and achieved small image sizes. In Lab 5a, you ran trivy and made containers non-root. This lab takes those foundations and hardens them to production standards.

> **Link back to Module 1**: Linux capabilities are a direct extension of the permissions and processes concepts from Module 1. The `root` user has all capabilities; your containers should have none.

### What You'll Do

1. **Scan current images with trivy**:
   - Run `trivy image` on your current api-service and worker-service images
   - Document all findings: CRITICAL, HIGH, MEDIUM, LOW
   - For each CRITICAL and HIGH vulnerability, identify:
     - Which package is vulnerable?
     - What's the CVE?
     - Is a fix available?
     - What's the attack vector?

2. **Fix vulnerabilities**:
   - Update base images to the latest patched versions
   - Update vulnerable application dependencies (Go modules)
   - For vulnerabilities without fixes, assess the risk and document your decision
   - Re-scan after fixes and verify that CRITICAL and HIGH counts are zero (or justified)

3. **Switch to distroless or scratch base images**:
   - Modify your multi-stage Dockerfiles:
     - Build stage: Use `golang:1.xx` as before
     - Runtime stage: Switch from `alpine` to `gcr.io/distroless/static-debian12` or `scratch`
   - For scratch images, ensure your Go binaries are statically compiled (`CGO_ENABLED=0`)
   - For distroless images, understand what's included (CA certificates, timezone data) and what's not (shell, package manager)
   - Re-scan with trivy -- observe the dramatic reduction in vulnerabilities
   - Compare image sizes: alpine vs distroless vs scratch
   - Document the trade-offs: What do you lose by not having a shell in the container?

4. **Implement read-only root filesystem in Kubernetes**:
   - Add `readOnlyRootFilesystem: true` to the security context of each container
   - Identify any directories your application needs to write to (temp files, caches)
   - Create `emptyDir` volume mounts for those specific directories
   - Verify that the application starts and functions correctly
   - Test: Try to write to the root filesystem from inside the container -- it should fail

5. **Drop all Linux capabilities**:
   - Add to the security context:
     ```yaml
     capabilities:
       drop: ["ALL"]
     ```
   - Verify that your Go services don't need any capabilities (most HTTP services don't)
   - If a service fails, determine which specific capability it needs and add only that one back
   - Document which capabilities each service runs with and why

6. **Configure complete security contexts**:
   - For every FlowForge container, configure:
     - `runAsNonRoot: true`
     - `runAsUser: 65534` (nobody) or a specific UID
     - `readOnlyRootFilesystem: true`
     - `allowPrivilegeEscalation: false`
     - `capabilities.drop: ["ALL"]`
   - Apply the same to any init containers or sidecar containers
   - Apply `seccompProfile.type: RuntimeDefault` (restricts system calls)

7. **Create a before/after security comparison**:
   - trivy scan results: before vs after
   - Image sizes: before vs after
   - Security context: before vs after
   - Attack surface analysis: what an attacker can do in the old container vs the new one
   - Document this as a security improvement report

### Expected Outcome

- trivy scan shows zero CRITICAL and zero HIGH vulnerabilities on all images
- Images use distroless or scratch base (not ubuntu, debian, or full alpine)
- All containers run with read-only root filesystem (with emptyDir for necessary writes)
- All containers have all Linux capabilities dropped
- All containers run as non-root with no privilege escalation
- Complete security context applied to every Pod in FlowForge
- Before/after comparison document showing the security improvement

### Checkpoint Questions

- [ ] Given a trivy scan output with 3 HIGH and 12 MEDIUM vulnerabilities, how would you prioritize which to fix first?
- [ ] What's the difference between distroless and scratch? When would you choose each?
- [ ] What Linux capabilities does a typical Go HTTP server need? (Think carefully -- the answer might surprise you)
- [ ] If a container has `readOnlyRootFilesystem: true`, how does it write log files? (Hint: it doesn't write to the filesystem -- where do logs go in a containerized environment?)
- [ ] Explain each field in the security context and what specific attack it prevents.
- [ ] If someone gave you a Dockerfile and a K8s deployment manifest for a service you've never seen, could you harden both to production standards?
