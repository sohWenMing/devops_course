# Lab 05: Incident Response & Security Audit

> **Objective**: Write incident response runbooks for three security scenarios, then perform a comprehensive security audit of the entire FlowForge system. No HIGH or CRITICAL findings should remain.  
> **Prerequisites**: All previous modules and Labs 01-04 done  
> **Time estimate**: 4-5 hours  
> **Produces**: Three incident response runbooks, complete security audit report with findings and remediation

---

## Exercise 5a: Incident Response Runbooks

### Objective

Write detailed incident response runbooks for three specific security scenarios: (1) compromised API key, (2) unauthorized CloudTrail access, (3) container escape attempt. Each runbook must include detection, containment, eradication, recovery, and post-mortem steps.

### Background

When a security incident happens, you don't have time to figure out what to do. Every minute counts -- especially during the containment phase, where delay means more data exposed, more systems compromised, more damage done.

Incident response runbooks are pre-written procedures that tell you exactly what to do for specific scenarios. They turn a panicked "what do we do?" into a calm, systematic response.

> **Link back to Module 9**: Your monitoring stack is the detection layer. The failure simulation in Lab 5 taught you to diagnose from dashboards first, form a hypothesis, then verify with kubectl. Incident response runbooks formalize this process and extend it through containment, eradication, and recovery.

### What You'll Do

Write a complete runbook for each of the following three scenarios. Each runbook must follow the incident response lifecycle: Detection → Containment → Eradication → Recovery → Post-Mortem.

#### Scenario 1: Compromised API Key

**Situation**: You receive an alert that an AWS access key associated with the CI/CD pipeline is being used from an unfamiliar IP address to list S3 buckets and describe EC2 instances. The API calls are coming from a region you don't use.

Write a runbook that covers:

1. **Detection**:
   - How would you detect this? (CloudTrail alerts, GuardDuty findings, unusual billing)
   - What specific CloudTrail events would you look for?
   - How do you confirm it's a real incident and not a false positive?

2. **Containment**:
   - What's the very first action to take? (Hint: stop the bleeding before investigating)
   - How do you revoke the compromised key without breaking the CI/CD pipeline?
   - How do you block the attacker's IP?
   - How do you preserve evidence for investigation?

3. **Eradication**:
   - How do you determine what the attacker accessed or modified?
   - What CloudTrail queries would you run?
   - How do you verify no backdoors were created (new IAM users, roles, or policies)?
   - How do you check for persistence mechanisms (scheduled actions, Lambda functions)?

4. **Recovery**:
   - How do you generate new credentials?
   - How do you update the CI/CD pipeline with the new credentials?
   - How do you verify that the pipeline works with the new credentials?
   - How do you confirm that the attacker no longer has access?

5. **Post-Mortem**:
   - What questions do you ask? (How was the key compromised? Where was it stored? Who had access?)
   - What preventive measures would you implement? (OIDC federation, key rotation, IP restrictions)
   - What monitoring improvements would you make?

#### Scenario 2: Unauthorized Access in CloudTrail

**Situation**: Your CloudTrail monitoring alerts fire: someone has made `iam:CreateUser` and `iam:AttachUserPolicy` API calls at 3am from a root account that should have MFA enabled. The new user has `AdministratorAccess` attached.

Write a runbook that covers:

1. **Detection**:
   - What CloudTrail fields indicate this is suspicious? (source IP, time, user identity, event name)
   - How do you determine if MFA was used for the root login?
   - Is this an automated system or a human actor?

2. **Containment**:
   - How do you disable the newly created user immediately?
   - How do you lock down the root account?
   - Should you disable all IAM users? What are the trade-offs?
   - How do you alert the rest of the team?

3. **Eradication**:
   - How do you find everything the attacker did? (CloudTrail query for the suspicious user and root account)
   - How do you check for other persistence: additional users, roles, policies, access keys?
   - How do you check for resource-level changes: new EC2 instances, modified security groups, new Lambda functions?

4. **Recovery**:
   - How do you change the root password and re-enable MFA?
   - How do you review and restore any modified IAM policies?
   - How do you verify the account is clean?

5. **Post-Mortem**:
   - How was the root password compromised?
   - Was MFA enabled? If so, how was it bypassed?
   - What organizational controls failed?
   - What technical controls will prevent recurrence?

#### Scenario 3: Container Escape Attempt

**Situation**: Your Kubernetes monitoring shows unusual activity: a Pod running api-service is making unexpected system calls -- attempting to mount the host filesystem, reading `/proc/1/environ` on the node, and trying to access the Kubernetes API server with elevated privileges.

Write a runbook that covers:

1. **Detection**:
   - What monitoring signals indicate a container escape attempt? (unusual syscalls, unexpected API calls, Falco alerts if installed)
   - How do you determine if the escape was successful or just attempted?
   - What logs would you check? (container logs, node audit logs, Kubernetes audit logs)

2. **Containment**:
   - How do you isolate the compromised Pod without losing forensic evidence?
   - Should you delete the Pod? What do you lose if you do?
   - How do you cordon the node to prevent new Pods from scheduling on it?
   - How do you check if other Pods on the same node are compromised?

3. **Eradication**:
   - How do you determine the initial attack vector? (compromised application code, vulnerable dependency, supply chain attack)
   - How do you check if the attacker pivoted to other services via the Kubernetes network?
   - How do you verify the container image hasn't been tampered with? (compare to the image in ECR by digest)
   - How do you check the node for signs of compromise?

4. **Recovery**:
   - How do you rebuild the compromised container from a known-good image?
   - How do you verify the node is clean (or replace it)?
   - How do you verify that the vulnerability that allowed the attempt is patched?
   - How do you restore normal traffic to the service?

5. **Post-Mortem**:
   - What security controls should have prevented this? (security contexts, NetworkPolicies, read-only filesystem, dropped capabilities)
   - Were those controls in place? If so, did they work?
   - What additional controls would you add? (Falco for runtime detection, Pod Security Standards, OPA/Gatekeeper)
   - How do you update your container security posture based on this incident?

### Runbook Format

Each runbook should follow this template:

```markdown
# Incident Response Runbook: [Scenario Name]

## Trigger
What event or alert initiates this runbook?

## Severity Assessment
How to determine severity: P1 (Critical) / P2 (High) / P3 (Medium) / P4 (Low)

## Detection (5-10 minutes)
Step-by-step commands and checks to confirm the incident.

## Containment (15-30 minutes)
Immediate actions to stop the bleeding. Include specific commands.

## Eradication (1-4 hours)
Steps to remove the threat and verify clean state.

## Recovery (1-4 hours)
Steps to restore normal operations.

## Communication Plan
Who to notify, when, and how (Slack, email, phone tree).

## Evidence Preservation
What logs, screenshots, and artifacts to capture before making changes.

## Post-Mortem Template
Timeline, root cause, impact, what worked, what didn't, action items.
```

### Expected Outcome

- Three complete incident response runbooks (one per scenario)
- Each runbook follows the Detection → Containment → Eradication → Recovery → Post-Mortem lifecycle
- Each runbook includes specific commands (AWS CLI, kubectl, etc.) not just vague guidance
- Communication plans and evidence preservation steps included
- Post-mortem templates with action items

### Checkpoint Questions

- [ ] Given a completely new incident scenario (e.g., ransomware on an EC2 instance), could you write a response runbook from scratch in under 15 minutes?
- [ ] What's the most important phase of incident response? (Hint: it's not the one most people focus on)
- [ ] Why is evidence preservation important? What would you lose if you immediately terminated a compromised instance?
- [ ] How do you determine severity for an incident? What factors influence whether it's P1 vs P3?
- [ ] What's the purpose of a post-mortem? Why is it "blameless"?
- [ ] When should you involve legal, compliance, or management in an incident? What triggers escalation?

---

## Exercise 5b: Full Security Audit

### Objective

Perform a comprehensive security audit of the entire FlowForge system. Review IAM, networking, secrets, containers, CI/CD, encryption, monitoring, and incident response. Document all findings with severity, evidence, and remediation. No HIGH or CRITICAL findings should remain after remediation.

### Background

A security audit is a systematic review of your entire system's security posture. It's different from the individual labs you've done -- those focused on implementing specific controls. The audit takes a step back and asks: "Is the system as a whole secure? Did we miss anything? Do all the pieces work together?"

Think of it as a final exam for security: you're the auditor reviewing your own work, trying to find every weakness before an attacker does.

> **Link forward to Capstone**: In the Capstone, one of the exit gates is "Security audit produces zero unaddressed HIGH/CRITICAL findings." The methodology and report format you develop here is exactly what you'll use there.

### What You'll Do

1. **IAM & Access Control Audit**:
   - List all IAM users, roles, groups, and policies
   - For each, verify least privilege (no `*` actions or resources without justification)
   - Check for unused users, roles, or access keys (should be deleted)
   - Verify MFA is enabled on the root account and all human users
   - Verify CloudTrail is enabled and logging
   - Verify IAM Access Analyzer has no unresolved findings
   - Check: Are there any access keys older than 90 days?

2. **Network Security Audit**:
   - Review all VPC security groups -- are any too permissive?
   - Review NACLs -- are they adding value beyond security groups?
   - Review Kubernetes NetworkPolicies -- is default deny in place?
   - Verify no unnecessary ports are open to 0.0.0.0/0
   - Verify SSH access is restricted to specific IPs (not 0.0.0.0/0)
   - Check: Can api-service reach worker-service directly? (Should it be blocked by NetworkPolicy?)

3. **Secrets Management Audit**:
   - Search for hardcoded secrets in all code, configs, and manifests
   - Verify all secrets are in AWS Secrets Manager (not in env files, K8s Secrets, or Terraform state)
   - Check Terraform state file for any remaining secret values
   - Verify secret rotation is configured or at least possible
   - Search Git history for previously committed secrets (even if now removed)
   - Check: Are Kubernetes Secret objects created by ESO, or are there still manual Secret manifests?

4. **Container Security Audit**:
   - Run trivy on all current container images
   - Verify zero CRITICAL and HIGH vulnerabilities
   - Verify all containers use distroless or scratch base images
   - Verify all containers run as non-root
   - Verify read-only root filesystem is enabled
   - Verify all Linux capabilities are dropped
   - Verify `allowPrivilegeEscalation: false` is set
   - Check: Is the Docker socket mounted in any Pod? (Critical security risk)

5. **CI/CD Security Audit**:
   - Review GitHub Actions workflows for security gates
   - Verify trivy, gosec, and govulncheck run on every build
   - Verify the pipeline fails on HIGH severity findings
   - Verify secrets are not exposed in pipeline logs
   - Verify OIDC is used for AWS authentication (no static access keys)
   - Check: Can a developer bypass security checks by pushing directly to main?

6. **Data Protection Audit**:
   - Verify RDS encryption at rest is enabled
   - Verify S3 encryption is enabled with appropriate key management
   - Verify TLS is used for all service-to-service communication
   - Verify TLS certificates are valid and not expiring soon
   - Check: Is Kubernetes etcd encrypted? (In EKS, AWS manages this; in Kind, likely not)

7. **Monitoring & Detection Audit**:
   - Verify security-relevant metrics are being collected
   - Verify alerting rules exist for security anomalies
   - Verify CloudTrail is being monitored for suspicious activity
   - Verify log aggregation captures security events
   - Check: Would you detect a brute-force attack against the API? A slow data exfiltration?

8. **Incident Response Audit**:
   - Verify runbooks exist for key scenarios
   - Verify runbooks include specific commands (not just vague guidance)
   - Verify communication plans exist
   - Verify evidence preservation procedures exist
   - Check: Have the runbooks been tested (tabletop exercise)?

### Audit Report Format

Create a formal audit report with these sections:

```markdown
# FlowForge Security Audit Report

## Executive Summary
Overall security posture: [Strong / Moderate / Weak]
Total findings: X (Y Critical, Z High, A Medium, B Low, C Informational)

## Scope
What was audited, when, by whom, and using what tools.

## Methodology
How the audit was conducted (manual review, automated scanning, both).

## Findings

### Finding 1: [Title]
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW / INFO
- **Category**: IAM / Network / Secrets / Container / CI/CD / Encryption / Monitoring / Incident Response
- **Description**: What the issue is
- **Evidence**: How you found it (command output, screenshot)
- **Risk**: What could happen if exploited
- **Remediation**: Specific steps to fix
- **Status**: Open / Remediated / Accepted Risk

(Repeat for each finding)

## Remediation Summary
What was fixed during the audit and what remains.

## Recommendations
Strategic improvements beyond the immediate findings.
```

### What To Do After the Audit

9. **Remediate all CRITICAL and HIGH findings**:
   - Fix each finding immediately
   - Re-verify after fixing
   - Update the finding status to "Remediated" with evidence

10. **Document accepted risks for MEDIUM and below**:
    - For findings you choose not to fix, document the justification
    - Include the compensating controls that reduce the risk
    - Set a review date to reassess

11. **Create a final status summary**:
    - Total findings by severity
    - Remediated vs accepted risk vs informational
    - Verify: zero remaining CRITICAL or HIGH findings

### Expected Outcome

- Complete security audit report covering all 8 audit areas
- Every finding has severity, evidence, risk assessment, and remediation plan
- All CRITICAL and HIGH findings remediated (with evidence of fix)
- MEDIUM findings documented with accepted risk justification (if not fixed)
- FlowForge passes a clean audit: zero unaddressed CRITICAL or HIGH findings
- Audit report can be shared with a peer for independent review

### Checkpoint Questions

- [ ] Can you perform a security audit on a system you've never seen before? What would your methodology be?
- [ ] Which audit area typically has the most findings in a real-world system? Why?
- [ ] What's the difference between a finding that's "Remediated" and one that's "Accepted Risk"? When is accepting risk appropriate?
- [ ] If you found a CRITICAL vulnerability during the audit (e.g., public RDS with default password), what would you do before continuing the audit?
- [ ] How often should security audits be performed? What events should trigger an out-of-cycle audit?
- [ ] Could another person follow your audit report and independently verify each finding and remediation?
