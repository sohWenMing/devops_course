# Lab 04: Encryption & CI/CD Security Scanning

> **Objective**: Enable encryption at rest and in transit for all FlowForge data stores and communication channels. Add comprehensive security scanning to the CI/CD pipeline that fails on HIGH severity.  
> **Prerequisites**: Module 5 (AWS), Module 6 (Terraform), Module 7 (CI/CD), Labs 01-03 done  
> **Time estimate**: 3-4 hours  
> **Produces**: Encrypted RDS, encrypted S3, TLS verification, certificate inspection output, CI/CD pipeline with trivy/gosec/govulncheck

---

## Exercise 4a: Encryption at Rest and in Transit

### Objective

Enable RDS encryption at rest. Enable S3 encryption. Verify TLS between all FlowForge services. Inspect certificates using `openssl s_client` to understand the certificate chain.

### Background

Encryption protects data in two states: at rest (stored on disk) and in transit (moving between services). Without encryption at rest, someone who accesses the storage directly (disk theft, unauthorized S3 access, snapshot cloning) gets plaintext data. Without encryption in transit, someone eavesdropping on the network (man-in-the-middle, packet sniffing) sees everything.

> **Link back to Module 2**: In Lab 3d, you generated self-signed certificates, configured HTTPS, and inspected the TLS handshake with `openssl s_client`. Those same skills apply here -- but now you're verifying TLS across the entire FlowForge stack, not just one service.

> **Link back to Module 5**: When you created RDS in Lab 3b, did you enable encryption? If not, you'll need to migrate to an encrypted instance. When you created S3 in Lab 3c, did you enable default encryption?

### What You'll Do

1. **Enable RDS encryption at rest**:
   - Check if your existing RDS instance has encryption enabled
   - If not: you cannot enable encryption on an existing instance. You must:
     a. Create a snapshot of the existing instance
     b. Copy the snapshot with encryption enabled
     c. Restore a new instance from the encrypted snapshot
     d. Update your connection strings to point to the new instance
     e. Delete the old unencrypted instance
   - If already encrypted: verify the KMS key being used and document it
   - Update Terraform to ensure `storage_encrypted = true` and specify the KMS key
   - Verify encryption: check the RDS console or use `aws rds describe-db-instances` and confirm `StorageEncrypted: true`

2. **Enable S3 encryption**:
   - Check current encryption settings on your FlowForge S3 buckets
   - Enable default encryption with SSE-KMS (or SSE-S3 as a simpler alternative)
   - Update Terraform to include server-side encryption configuration
   - Update the bucket policy to deny any `PutObject` requests without encryption headers (enforce encryption)
   - Upload a test file and verify it's encrypted: `aws s3api head-object` should show `ServerSideEncryption`
   - Verify that existing objects are encrypted (they won't be retroactively -- discuss this)

3. **Verify TLS between all services**:

   For each communication path in FlowForge, verify that TLS is in use:

   - **Client → Ingress**: Verify HTTPS with a valid certificate
     ```
     curl -v https://<ingress-endpoint>/health
     ```
     Check for `SSL connection using TLS...` in the output.

   - **api-service → PostgreSQL**: Verify that the database connection uses TLS
     - Check your Go database connection string for `sslmode=require` or `sslmode=verify-full`
     - From inside the api-service Pod, verify the connection:
       ```
       openssl s_client -connect <postgres-host>:5432 -starttls postgres
       ```
     - For RDS, TLS is available by default -- but your client must request it

   - **worker-service → PostgreSQL**: Same verification as above

   - **kubectl → Kubernetes API**: Already uses TLS (verify with `kubectl cluster-info`)

   - **Prometheus → targets**: Check if scraping uses HTTP or HTTPS

   Document each verification with the command used and relevant output.

4. **Inspect certificates with openssl s_client**:

   Use `openssl s_client` to examine certificates in detail:

   - Connect to the Ingress endpoint and inspect the certificate:
     ```
     openssl s_client -connect <host>:<port> -showcerts
     ```
   - For each certificate in the chain, identify:
     - Subject (who is this certificate for?)
     - Issuer (who signed it?)
     - Validity period (when does it expire?)
     - SANs (Subject Alternative Names -- which domains does it cover?)
     - Key algorithm and size
   - For RDS, inspect the RDS certificate:
     ```
     openssl s_client -connect <rds-endpoint>:5432 -starttls postgres -showcerts
     ```
   - Document the full certificate chain for at least one connection

5. **Create an encryption status report**:
   - For each data store (RDS, S3, Kubernetes Secrets, etcd), document:
     - Is it encrypted at rest? With what mechanism?
     - Is communication encrypted in transit? With what protocol?
     - What key is used? Who manages it?
   - For each service-to-service communication path:
     - Is TLS enabled? What version?
     - Is the certificate valid? When does it expire?
     - Is certificate verification enabled (or is it `sslmode=disable`)?

### Expected Outcome

- RDS instance has encryption at rest enabled (verified via AWS CLI or console)
- S3 buckets have default encryption enabled (SSE-S3 or SSE-KMS)
- S3 bucket policy enforces encryption on all uploads
- TLS verified on all communication paths (client→ingress, service→database)
- Certificate chain inspected and documented for at least one endpoint
- Encryption status report covering all data stores and communication paths
- Terraform updated to enforce encryption settings

### Checkpoint Questions

- [ ] What's the difference between encryption at rest and encryption in transit? Give a scenario where each matters.
- [ ] You have an unencrypted RDS instance in production with data. What's the process to encrypt it? Why can't you just "enable encryption" on it?
- [ ] What are the three S3 encryption types (SSE-S3, SSE-KMS, SSE-C)? When would you choose each?
- [ ] Run `openssl s_client` against an endpoint and explain every line of the certificate output.
- [ ] What happens if a TLS certificate expires and nobody notices? How would you prevent this?
- [ ] If your database connection is using `sslmode=disable`, what specific attack does this enable?

---

## Exercise 4b: Security Scanning in CI/CD

### Objective

Add comprehensive security scanning to your GitHub Actions pipeline: trivy for container image vulnerabilities, gosec for Go security issues, and govulncheck for dependency vulnerabilities. Configure the pipeline to fail on HIGH severity findings.

### Background

Your CI/CD pipeline (Module 7) currently builds, tests, lints, and deploys FlowForge. But it doesn't systematically check for security vulnerabilities. Adding security scanning means that vulnerable code and images can't make it to production -- the pipeline stops them.

This is **shift-left security**: catching security issues early in the development process (left on the timeline) instead of discovering them in production (right on the timeline). Every vulnerability caught in CI is one that never reaches production.

> **Link back to Module 7**: In Lab 2b, you added trivy scanning and quality gates. This lab extends that with Go-specific security tools and stricter failure thresholds. You already have the pipeline structure -- now you're adding more gates.

### What You'll Do

1. **Add trivy image scanning to the pipeline**:
   - In your GitHub Actions workflow, after building the Docker image, add a trivy scan step
   - Configure trivy to:
     - Scan for vulnerabilities with severity HIGH and CRITICAL
     - Exit with code 1 (failure) if any are found
     - Output results in table format for readability
     - Also output SARIF format for GitHub Security tab integration (optional)
   - Test by temporarily using a base image with known vulnerabilities -- verify the pipeline fails
   - Then switch back to your hardened image -- verify the pipeline passes

2. **Add gosec to the pipeline**:
   - Add a step that runs `gosec ./...` on both api-service and worker-service
   - Configure gosec to:
     - Scan all Go source files
     - Report findings by severity
     - Fail the pipeline on HIGH or CRITICAL findings
   - Understand what gosec checks for:
     - SQL injection via string concatenation
     - Hardcoded credentials (passwords, API keys in code)
     - Insecure TLS configurations (TLS 1.0, weak ciphers)
     - Unhandled errors (especially in security-sensitive operations)
     - Use of deprecated or insecure crypto functions
   - Review the output -- you may have existing issues to fix

3. **Add govulncheck to the pipeline**:
   - Add a step that runs `govulncheck ./...` on both services
   - Configure govulncheck to:
     - Check all Go dependencies against the Go Vulnerability Database
     - Report only vulnerabilities in code paths your application actually uses
     - Fail the pipeline if any vulnerabilities are found in used code paths
   - Understand the difference between govulncheck and a generic dependency scanner:
     - Generic scanners flag any vulnerable dependency, even if your code never calls the vulnerable function
     - govulncheck performs call graph analysis to determine if the vulnerability is actually reachable
     - This reduces false positives significantly

4. **Configure pipeline failure on HIGH severity**:
   - Ensure all three tools are configured to fail the pipeline on HIGH severity or above
   - Set up the pipeline stages so that security scanning happens BEFORE the deploy step
   - If any security check fails, the pipeline should stop -- no deployment
   - Design the failure output to be actionable: developers should be able to understand what to fix from the pipeline output alone

5. **Test the complete security pipeline**:
   - Create a test branch
   - Introduce a deliberate security issue (e.g., a SQL injection in a Go file, or use an old base image with CVEs)
   - Push and observe the pipeline fail at the security scanning stage
   - Fix the issue and push again -- observe the pipeline pass
   - Verify that the security checks run in parallel where possible (trivy can run at the same time as gosec)

6. **Explain shift-left security**:
   - Write a brief explanation of what shift-left security means
   - Draw a diagram showing where security checks happen in your pipeline
   - Calculate the cost comparison: finding a vulnerability in CI (automated, minutes) vs. finding it in production (incident response, hours/days, potential data breach)
   - List at least 3 benefits and 2 challenges of shift-left security

### Expected Outcome

- GitHub Actions pipeline includes: trivy image scan, gosec, govulncheck
- All three tools configured to fail the pipeline on HIGH/CRITICAL findings
- Security scanning runs before deployment stage
- Demonstrated pipeline failure on a deliberately introduced vulnerability
- Demonstrated pipeline success after fixing the vulnerability
- Written explanation of shift-left security with diagram and cost analysis
- Complete pipeline YAML committed to the repository

### Checkpoint Questions

- [ ] What does "shift-left security" mean? Why is it cheaper to find vulnerabilities early?
- [ ] What's the difference between trivy, gosec, and govulncheck? What does each tool check for?
- [ ] How does govulncheck differ from a generic dependency vulnerability scanner? Why does this matter?
- [ ] If you were adding security scanning to a Python project's pipeline, what tools would you use instead of gosec and govulncheck?
- [ ] Should your pipeline fail on MEDIUM severity findings? What are the trade-offs?
- [ ] Add a new security scanning tool to the pipeline from scratch (e.g., hadolint for Dockerfile linting). Can you do it without referencing this lab?
