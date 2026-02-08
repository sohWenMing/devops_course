# Lab 02: Variables, Outputs & State Management

> **Module**: 6 -- Terraform  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Lab 01 completed (you can write basic Terraform configs). Read the [Variables](#), [Outputs](#), [Locals](#), and [State](#) sections of the Module 6 README.

---

## Overview

In this lab, you'll transform a hardcoded Terraform configuration into a fully parameterized one using variables, outputs, and locals. Then you'll explore Terraform state -- inspecting it, detecting drift, and importing existing resources. By the end, you'll understand how Terraform tracks and manages infrastructure.

---

## Exercise 2a: Parameterize Everything

### Objectives

- Convert hardcoded values to input variables with types, defaults, and validation
- Use the `sensitive` flag for secrets
- Define meaningful outputs
- Use locals for computed values and DRY patterns
- Work with variable files (`.tfvars`) for different environments

### What You'll Do

**Part 1: Variable Definitions**

1. Create a new directory for this exercise (e.g., `project/infra/lab-02a/`) or extend your Lab 01b config.

2. Take the VPC infrastructure from Lab 01b and parameterize **everything** that might differ between environments:
   - VPC CIDR block
   - Subnet CIDRs (all 6 subnets if you expand to the full Module 5 layout)
   - EC2 instance type
   - AWS region
   - Environment name (dev, staging, prod)
   - Project name

3. For each variable, define:
   - A `description` that explains what it is and why it exists
   - A `type` constraint (use `string`, `map`, `object`, or `list` as appropriate)
   - A `default` value where sensible (what should NOT have a default?)
   - A `validation` block where appropriate (e.g., environment must be dev/staging/prod)

4. Add a variable for the RDS database password:
   - Mark it as `sensitive = true`
   - It should have NO default value (why?)
   - It should have a validation rule for minimum length
   - How would you pass this value without it appearing in your shell history?

5. Think about which variables belong in which file:
   - Which go in `variables.tf`?
   - Which values go in `terraform.tfvars`?
   - Which go in environment-specific files like `dev.tfvars` and `staging.tfvars`?
   - Which should be passed via environment variables (`TF_VAR_*`)? Why?

> **Link back**: In Module 3, you externalized all FlowForge config to environment variables following the 12-Factor App. This is the same principle at the infrastructure level. And just like Module 3's `.env` file, your `.tfvars` files hold the values.

**Part 2: Outputs**

6. Define outputs for values that operators or other systems need:
   - The VPC ID
   - All subnet IDs (grouped by type: public, private, database)
   - The EC2 instance public IP (if you add an instance)
   - The RDS endpoint (if you add an RDS instance)
   - Any other values someone would need to connect to or interact with the infrastructure

7. For each output, add a `description` and mark sensitive values appropriately.

8. After applying, run `terraform output` to see all outputs. Then try:
   - `terraform output api_instance_public_ip` -- get a specific output
   - `terraform output -json` -- get all outputs as JSON (useful for scripts)
   - How could a deployment script use these outputs to configure the application?

**Part 3: Locals**

9. Create a `locals` block that computes:
   - A name prefix: `"${project}-${environment}"` (e.g., `flowforge-dev`)
   - Common tags that should appear on every resource
   - Any repeated expressions you see in your config

10. Refactor your resource tags to use `local.common_tags`:
    ```
    tags = merge(local.common_tags, {
      Name = "${local.name_prefix}-vpc"
    })
    ```

**Part 4: Environment Variable Files**

11. Create two variable files:
    - `dev.tfvars` -- smaller instance types, shorter names, cheaper options
    - `staging.tfvars` -- closer to production sizing

12. Apply with each:
    - `terraform plan -var-file="dev.tfvars"`
    - Switch workspace (or directory) and apply with `staging.tfvars`
    - Observe how the same config produces different infrastructure

13. Destroy when done.

### Expected Outcomes

- A fully parameterized Terraform config with no hardcoded environment-specific values
- Variables with types, descriptions, defaults, and validation
- Meaningful outputs for instance IPs, RDS endpoints, VPC IDs
- Locals for DRY tag management and naming
- Environment-specific `.tfvars` files

### Checkpoint Questions

1. What is the difference between a variable, a local, and an output?
2. What does `sensitive = true` on a variable actually do? What does it NOT do?
3. In what order does Terraform evaluate variable sources (CLI, .tfvars, env vars, defaults)?
4. Why should a database password variable have no default?
5. How would you pass a sensitive variable in CI/CD without it appearing in logs?
6. Given a new Terraform config, how do you decide what should be a variable?

---

## Exercise 2b: State Inspection, Drift Detection & Import

### Objectives

- Inspect and understand Terraform state
- Detect and respond to configuration drift
- Import existing (unmanaged) AWS resources into Terraform state
- Understand why state must never be edited manually

### What You'll Do

**Part 1: State Inspection**

1. Apply a configuration (either from Exercise 2a or create a simple one with a few resources).

2. List all resources in state:
   ```
   terraform state list
   ```
   - How many resources does Terraform know about?
   - Do the resource addresses match your config?

3. Show detailed state for a specific resource:
   ```
   terraform state show aws_vpc.main
   ```
   - What information does Terraform record?
   - Find the VPC ID, CIDR, tags, and any computed attributes
   - Compare this to `aws ec2 describe-vpcs` output -- what's the same?

4. Pull the full state as JSON:
   ```
   terraform state pull | python3 -m json.tool > state.json
   ```
   - Find a resource in the JSON. What fields are recorded?
   - Find the `serial` number -- what does it represent?
   - Find the `lineage` -- what is it for?
   - **Critical**: Is the database password (if you have one) visible in the state file? This is why state security matters!

> **Link back**: In Module 5, you discovered resources by tag using the cleanup script. Terraform state is a complete inventory of everything it manages -- no tag scanning needed. But it also means the state file is your single source of truth.

**Part 2: Drift Detection**

5. With your Terraform infrastructure deployed, go to the **AWS Console** (or use the CLI) and manually change something:
   - Change a tag on the VPC (e.g., add `Environment = "manually-changed"`)
   - OR change a security group rule
   - OR change an instance type (if you have an EC2 instance)
   - **Document what you changed** -- you'll need to verify drift detection caught it

6. Without making any changes to your `.tf` files, run:
   ```
   terraform plan
   ```
   - Does Terraform detect the change?
   - What does the plan output show? Look for `~` (update in-place)
   - The plan shows what Terraform wants to change **back** to match your config
   - This is **drift detection** -- someone changed reality, and Terraform noticed

7. Apply the plan to **restore** the config to its desired state:
   ```
   terraform apply
   ```
   - Verify that the manual change has been reverted

8. Reflect on what just happened:
   - Someone changed infrastructure outside of Terraform
   - Terraform detected the difference
   - Running apply brought reality back in line with the config
   - What if the manual change was intentional? How would you handle that? (Hint: update the config to match)

> **Architecture Thinking**: Drift is a real production problem. People make manual changes during incidents ("just open port 443 real quick"), forget about them, and now reality doesn't match code. What processes or guardrails would you put in place to prevent drift? (Hint: Module 7 CI/CD and Module 10 security audits)

**Part 3: terraform import**

9. Create a resource manually using the AWS CLI (outside of Terraform):
   - Create a small S3 bucket: `aws s3api create-bucket --bucket your-unique-import-test-bucket --region us-east-1`
   - Tag it: `aws s3api put-bucket-tagging --bucket your-unique-import-test-bucket --tagging 'TagSet=[{Key=Project,Value=FlowForge}]'`

10. Write a Terraform resource block in your config that **describes** this bucket:
    - The resource type is `aws_s3_bucket`
    - Give it a local name (e.g., `aws_s3_bucket.imported`)
    - Set the `bucket` argument to the bucket name you created

11. If you run `terraform plan` now, what will happen?
    - Terraform doesn't know this resource already exists
    - It will plan to **create** a new bucket (which will fail because the name is taken)
    - Try it and observe the error

12. Import the existing bucket into Terraform state:
    ```
    terraform import aws_s3_bucket.imported your-unique-import-test-bucket
    ```
    - What does the output say?
    - Run `terraform state show aws_s3_bucket.imported` to see the imported state

13. Run `terraform plan` again:
    - Is the plan empty (no changes)?
    - If Terraform wants to change something, it means your config doesn't perfectly match reality
    - Update your config to match the imported resource's actual configuration
    - Keep running plan → adjust config until the plan shows no changes

14. Now that the bucket is managed by Terraform, you can modify it through config:
    - Add a new tag in your config
    - Run plan to see the change
    - Apply to make the change

15. Clean up: destroy the imported bucket with `terraform destroy`.

> **Link back**: In Module 5, you built everything manually. If you wanted to bring that infrastructure under Terraform management, `terraform import` is how you'd do it -- one resource at a time. It's tedious for many resources but essential when adopting Terraform for existing infrastructure.

### Expected Outcomes

- Ability to inspect state with `terraform state list`, `state show`, `state pull`
- Understanding of what information state contains (including sensitive data)
- Successfully detected drift caused by a manual change
- Successfully imported an existing AWS resource into Terraform state
- Understanding of the import workflow: create resource block → import → adjust config → plan shows no changes

### Checkpoint Questions

1. What commands would you use to find a specific resource in Terraform state?
2. What happens if you lose the state file? Can you recover?
3. What is drift? How does Terraform detect it?
4. What happens if someone makes a manual change and you run `terraform apply`?
5. What does `terraform import` do? Does it create the config file for you?
6. Why should you never edit the `terraform.tfstate` file directly?
7. What sensitive data might be in the state file? Why does this matter for how you store state?

---

## Before You Move On

Before proceeding to Lab 03:
- [ ] Every value that differs between environments is a variable
- [ ] Sensitive values are marked `sensitive = true`
- [ ] You have meaningful outputs for key infrastructure values
- [ ] You can inspect state and find specific resources
- [ ] You can detect drift caused by manual changes
- [ ] You can import an existing resource into Terraform state
- [ ] You understand why state file security is critical
