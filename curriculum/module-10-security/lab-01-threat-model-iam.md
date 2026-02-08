# Lab 01: Threat Modeling & IAM Hardening

> **Objective**: Build a complete threat model for FlowForge using the STRIDE framework, then systematically harden all IAM policies from Module 5 to follow least privilege.  
> **Prerequisites**: Module 5 (AWS/IAM), Module 6 (Terraform), Module 8 (Kubernetes), Module 9 (Monitoring) completed  
> **Time estimate**: 3-4 hours  
> **Produces**: Threat model document, tightened IAM policies, CloudTrail enabled, IAM Access Analyzer findings

---

## Exercise 1a: Threat Model for FlowForge

### Objective

Create a comprehensive threat model for the FlowForge system that identifies assets, threats (using STRIDE), and mitigations for each threat. Prioritize threats by likelihood and impact.

### Background

Threat modeling is the practice of systematically identifying what can go wrong in your system's security. You do this BEFORE writing security controls -- so the controls you implement are driven by real threats, not guesswork.

Think of it like the architecture diagrams you've been drawing throughout the course, but from an attacker's perspective. Instead of asking "How does data flow?" you ask "How could an attacker exploit this data flow?"

> **Link back to Module 3**: Remember the data flow diagram you drew for FlowForge (user → api-service → PostgreSQL → worker-service → PostgreSQL → api-service → user)? That same diagram is the starting point for your threat model. Every arrow is a potential attack vector.

### What You'll Do

1. **Draw the FlowForge system diagram** from a security perspective:
   - Include all components: api-service, worker-service, PostgreSQL, Ingress/load balancer, ECR, S3, CI/CD pipeline
   - Mark all trust boundaries (where data crosses from one security domain to another)
   - Label all data flows with what data travels on each path
   - Include external actors: users, developers, CI/CD system, AWS APIs

2. **Identify all assets** in the system:
   - What data exists? (task data, user credentials, API responses, logs)
   - What credentials exist? (database passwords, AWS access keys, TLS certificates, API tokens, GitHub tokens)
   - What infrastructure exists? (EC2, RDS, S3, EKS/Kind cluster, container images)
   - What processes/services exist? (api-service, worker-service, PostgreSQL, Prometheus, Grafana)

3. **Apply STRIDE to every component and data flow**:

   For each major component (api-service, worker-service, PostgreSQL, Ingress, CI/CD pipeline, container registry, monitoring stack), analyze all six STRIDE categories:

   | Category | Question to Ask |
   |---|---|
   | Spoofing | Can someone pretend to be this component or a legitimate user of it? |
   | Tampering | Can someone modify data in this component or in transit to/from it? |
   | Repudiation | Can someone perform actions that can't be traced back to them? |
   | Information Disclosure | Can someone read data they shouldn't from this component? |
   | Denial of Service | Can someone make this component unavailable? |
   | Elevation of Privilege | Can someone gain higher access through this component? |

4. **For each identified threat, document**:
   - Threat description (what the attack looks like)
   - Affected asset(s)
   - STRIDE category
   - Likelihood (Low / Medium / High)
   - Impact (Low / Medium / High)
   - Existing mitigations (what you've already done in Modules 1-9)
   - Recommended mitigations (what you'll implement in Module 10)

5. **Prioritize threats** using a risk matrix:

   ```
            │ Low Impact │ Med Impact │ High Impact
   ─────────┼────────────┼────────────┼────────────
   High     │  Medium    │  High      │  Critical
   Likelihood│            │            │
   ─────────┼────────────┼────────────┼────────────
   Medium   │  Low       │  Medium    │  High
   Likelihood│            │            │
   ─────────┼────────────┼────────────┼────────────
   Low      │  Info      │  Low       │  Medium
   Likelihood│            │            │
   ```

6. **Create the final threat model document** with:
   - System diagram (with trust boundaries)
   - Asset inventory
   - Threat table (at least 15 threats across all STRIDE categories)
   - Risk matrix visualization
   - Top 5 highest-priority threats with detailed mitigation plans
   - Summary of existing vs. missing mitigations

### Expected Outcome

A markdown document (or diagram + tables) containing:
- FlowForge architecture diagram with trust boundaries marked
- Complete asset inventory (data, credentials, infrastructure)
- At least 15 identified threats using STRIDE, covering all components
- Each threat rated by likelihood and impact
- Clear mapping of threats to mitigations (existing from Modules 1-9, new for Module 10)
- Top 5 priority list that will drive the rest of the module's labs

### Checkpoint Questions

- [ ] Can you explain what STRIDE stands for and give an example of each category for FlowForge?
- [ ] What are the trust boundaries in the FlowForge system? Where does data cross from one security domain to another?
- [ ] Which three threats in your model have the highest combined risk (likelihood × impact)? Why?
- [ ] For each of those top three threats, what specific mitigation will you implement?
- [ ] If someone asked you to threat model a completely different system (e.g., an e-commerce platform), could you apply the same methodology in under 20 minutes?

---

## Exercise 1b: IAM Hardening

### Objective

Review and tighten all IAM policies created in Module 5. Apply least privilege rigorously. Enable CloudTrail for auditing. Set up IAM Access Analyzer to find overly permissive policies.

### Background

In Module 5, you created IAM users, groups, policies, and roles to get FlowForge running on AWS. Those policies likely grant more permissions than necessary -- a common pattern when learning. Now it's time to review every policy and tighten it.

> **Link back to Module 5**: Pull up the IAM policies you created in Labs 1a and 1b. Look at every `Action` and `Resource` field. Ask yourself: "Does this service actually need this permission? Does it need it on all resources, or just specific ones?"

### What You'll Do

1. **Audit existing IAM policies**:
   - List all IAM users, groups, roles, and policies in your account
   - For each policy, document what it allows and on which resources
   - Identify overly permissive policies (wildcards in actions or resources)
   - Identify unused policies, users, or roles
   - Check for any inline policies (these should be managed policies instead)

2. **Apply least privilege to each identity**:

   For each IAM identity used by FlowForge, tighten the policies:

   - **EC2 instance profile (api-service)**: What AWS APIs does api-service actually call? Scope to exactly those actions and resources. Think about:
     - Does it need S3 access? To which bucket(s)? Read-only or read-write?
     - Does it need CloudWatch Logs? To which log group?
     - Does it need ECR access? Just pull, or push too?

   - **EC2 instance profile (worker-service)**: Same analysis for worker-service.

   - **CI/CD IAM role (GitHub Actions OIDC)**: What does the pipeline need?
     - ECR push (but only to specific repositories)
     - Terraform apply (but scoped to specific resource types)
     - S3 access for Terraform state (but only the state bucket)

   - **Terraform execution role**: What resources does Terraform manage? Scope accordingly.

   - **Developer IAM user/group**: What do developers need day-to-day? Read access to most things, write access to few.

3. **Enable CloudTrail**:
   - Create a CloudTrail trail that logs all management events
   - Configure the trail to deliver logs to an S3 bucket
   - Enable log file validation (integrity checking)
   - Verify you can see recent API calls in the CloudTrail console
   - Explore: What API calls did your account make in the last hour?

4. **Set up IAM Access Analyzer**:
   - Create an IAM Access Analyzer for your account
   - Review all findings -- these are resources accessible from outside your account
   - For each finding, determine if external access is intentional or a mistake
   - Fix any unintentional external access
   - Document which findings were intentional and why

5. **Fix overly permissive policies**:
   - Replace `"Resource": "*"` with specific ARNs wherever possible
   - Replace broad action wildcards (`s3:*`) with specific actions (`s3:GetObject`, `s3:PutObject`)
   - Add conditions where appropriate (e.g., restrict S3 access to specific prefixes, restrict by source IP)
   - Verify that FlowForge still works after tightening each policy (test after each change, not all at once!)

6. **Create a before/after comparison**:
   - Document the original policy alongside the tightened version for each identity
   - Explain what was removed and why it was unnecessary
   - Verify that all FlowForge functionality still works with the tightened policies

### Expected Outcome

- All IAM policies reviewed and tightened (before/after comparison for each)
- No IAM policy uses `"Resource": "*"` unless absolutely justified
- No IAM policy uses broad action wildcards (`s3:*`, `ec2:*`) -- only specific actions
- CloudTrail is enabled and logging API calls
- IAM Access Analyzer is running with all findings reviewed
- All unintentional external access findings are resolved
- FlowForge still functions correctly with tightened policies

### Checkpoint Questions

- [ ] Can you explain the difference between identity-based and resource-based policies? Give an example of each from your FlowForge setup.
- [ ] What is the evaluation logic for IAM policies? (What happens when multiple policies apply?)
- [ ] Pick one IAM policy you tightened. Explain what the original allowed that was unnecessary and what specific threat it mitigated.
- [ ] What did IAM Access Analyzer find? Were any findings surprising?
- [ ] If you found a CloudTrail entry showing `iam:CreateUser` at 3am from an IP you don't recognize, what would you do? (Think detection → containment → eradication → recovery)
- [ ] Can you find and fix an overly permissive policy if given a new AWS account you've never seen before?
