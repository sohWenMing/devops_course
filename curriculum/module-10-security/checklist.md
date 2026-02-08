# Module 10: Security Hardening -- Exit Gate Checklist

> **Instructions**: Complete every item below before moving to the Capstone. Each checkpoint is binary -- YES (you can do it confidently) or NO (you need more practice). You must answer YES to ALL items.
>
> **How to use**: After completing all labs, go through each item WITHOUT looking at your notes or previous work. If you can't do it from memory, go back and practice until you can. The Capstone gives you zero guidance -- these checkpoints verify you're ready.

---

## Threat Modeling

- [ ] Can you explain what STRIDE stands for and apply each category to a system you've never seen before?
- [ ] Given a new system architecture diagram, can you identify all assets, trust boundaries, and at least 10 threats in under 20 minutes?
- [ ] Can you create a risk matrix and prioritize threats by likelihood and impact?
- [ ] Can you map each identified threat to a specific mitigation?
- [ ] Can you draw FlowForge's trust boundaries from memory?

## IAM Hardening

- [ ] Can you explain the difference between identity-based and resource-based policies and give examples of each?
- [ ] Given a JSON IAM policy, can you explain exactly what it allows and denies?
- [ ] Can you write an IAM policy from scratch with least privilege for a specific use case (e.g., "read objects from one S3 bucket and write logs to one CloudWatch log group")?
- [ ] Can you find and fix an overly permissive IAM policy (one with `*` actions or resources)?
- [ ] Can you explain the IAM evaluation logic (explicit Deny > explicit Allow > implicit Deny)?
- [ ] Can you query CloudTrail to find who made a specific API call?
- [ ] Can you explain what IAM Access Analyzer does and interpret its findings?

## Secrets Management

- [ ] Can you explain the secret lifecycle (creation, distribution, rotation, revocation, cleanup)?
- [ ] Can you create a secret in AWS Secrets Manager and retrieve it programmatically?
- [ ] Can you explain the difference between External Secrets Operator and CSI Secrets Store driver?
- [ ] Can you set up ESO or CSI driver to pull secrets from Secrets Manager into Kubernetes?
- [ ] Can you rotate a secret and verify the application picks up the new value?
- [ ] Can you identify where secrets are stored in a system and migrate them to a proper secret manager?

## Container Security

- [ ] Given a trivy scan output with multiple vulnerabilities, can you prioritize and fix them?
- [ ] Can you switch a Dockerfile from Alpine to distroless or scratch and explain the trade-offs?
- [ ] Can you build a Go service as a static binary with `CGO_ENABLED=0` and explain why this is needed for scratch images?
- [ ] Can you explain what Linux capabilities are and why you drop them all?
- [ ] Can you write a complete Kubernetes security context from memory (runAsNonRoot, readOnlyRootFilesystem, allowPrivilegeEscalation, capabilities.drop)?
- [ ] Can you explain what `readOnlyRootFilesystem: true` prevents and how to handle applications that need to write files?

## Kubernetes Network Policies

- [ ] Can you write a default-deny NetworkPolicy from memory?
- [ ] Can you write a NetworkPolicy that allows specific ingress and egress traffic based on Pod labels?
- [ ] Can you verify that a NetworkPolicy is actually blocking traffic (not just silently being ignored)?
- [ ] Can you explain why you need a NetworkPolicy-capable CNI and name at least two options?
- [ ] Given a new set of services, can you design and implement NetworkPolicies from scratch?
- [ ] Can you debug a situation where a NetworkPolicy is blocking legitimate traffic?
- [ ] Can you compare NetworkPolicies to AWS security groups and explain similarities and differences?

## Kubernetes RBAC

- [ ] Can you explain the difference between a Role and a ClusterRole?
- [ ] Can you create a ServiceAccount, Role, and RoleBinding from scratch?
- [ ] Can you explain why application Pods should not use the `default` ServiceAccount?
- [ ] Can you explain what `automountServiceAccountToken: false` does and when to use it?
- [ ] Can you verify RBAC enforcement by testing allowed and denied operations from inside a Pod?
- [ ] Can you explain how IRSA bridges Kubernetes RBAC and AWS IAM?

## Encryption at Rest and in Transit

- [ ] Can you explain the difference between encryption at rest and encryption in transit?
- [ ] Can you verify that RDS has encryption enabled using the AWS CLI?
- [ ] Can you explain the three S3 encryption types (SSE-S3, SSE-KMS, SSE-C) and when to use each?
- [ ] Can you verify TLS between two services using `openssl s_client`?
- [ ] Can you read and interpret a TLS certificate chain (subject, issuer, validity, SANs)?
- [ ] Can you explain what happens if you try to enable encryption on an existing unencrypted RDS instance?

## Security Scanning in CI/CD

- [ ] Can you explain what shift-left security means and why it's valuable?
- [ ] Can you add trivy image scanning to a GitHub Actions pipeline from memory?
- [ ] Can you add gosec and govulncheck to a pipeline?
- [ ] Can you configure the pipeline to fail on HIGH severity findings?
- [ ] Can you explain the difference between trivy, gosec, and govulncheck?
- [ ] Can you explain how govulncheck differs from a generic dependency scanner?
- [ ] Can you add a new security scanning tool to the pipeline from scratch?

## Incident Response

- [ ] Can you explain the five phases of incident response (Detection, Containment, Eradication, Recovery, Post-Mortem)?
- [ ] Given a new incident scenario, can you write a response runbook from scratch in under 15 minutes?
- [ ] Can you explain why evidence preservation matters and what you'd lose by immediately terminating a compromised instance?
- [ ] Can you determine the severity of an incident and decide on escalation?
- [ ] Can you conduct a blameless post-mortem and produce actionable improvement items?

## Security Audit

- [ ] Can you perform a systematic security audit across IAM, networking, secrets, containers, CI/CD, encryption, monitoring, and incident response?
- [ ] Can you classify findings by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)?
- [ ] Can you write a finding with description, evidence, risk, and remediation?
- [ ] Does your FlowForge security audit have zero unaddressed CRITICAL or HIGH findings?
- [ ] Could another person follow your audit report and independently verify each finding?

## Integration & Architecture Thinking

- [ ] Can you draw the defense-in-depth layers for FlowForge from memory (Linux → Network → AWS → Container → K8s → CI/CD → Monitoring → Incident Response)?
- [ ] Can you explain how security controls from Modules 1-9 contribute to the overall security posture?
- [ ] For any new system, can you identify which security controls are needed and in what order to implement them?
- [ ] Can you explain the trade-off between security and usability/velocity? How do you make that decision?
- [ ] Can you threat model a completely new system (different from FlowForge) and produce a prioritized mitigation plan?

---

## Final Verification

Before moving to the Capstone, verify these end-to-end scenarios:

1. **Attack simulation**: Attempt to bypass each security control you've implemented. Try to access the database from a Pod that shouldn't have access. Try to deploy an image with known vulnerabilities. Try to read Kubernetes Secrets. Each attempt should be blocked.

2. **Recovery drill**: Pick one of your incident response runbooks. Walk through it (tabletop exercise -- you don't need to actually cause an incident). Can you follow every step? Are any steps unclear?

3. **Stranger test**: Could someone unfamiliar with FlowForge read your security audit report and understand the security posture of the system? Would they agree with your severity classifications?

---

> **Ready for the Capstone?** If every checkbox above is YES and you've passed the final verification scenarios, you're ready. The Capstone will test all of these skills together -- with zero guidance. Good luck.
