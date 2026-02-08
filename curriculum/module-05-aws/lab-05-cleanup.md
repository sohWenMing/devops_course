# Lab 05: Cleanup & Cost Verification

> **Module**: 5 -- AWS Fundamentals  
> **Time estimate**: 1-2 hours  
> **Prerequisites**: Read the [Cost Awareness & Cleanup](#) section of the Module 5 README. Labs 00-04 completed (full FlowForge deployment on AWS).

---

## Overview

This is the most important lab in Module 5 from a financial perspective. You will tear down every AWS resource you created, verify your cleanup was complete, and understand which resources cost money even when "stopped." The Python cleanup script you started in Lab 00 will be completed and tested.

Leaving resources running is the most expensive mistake in cloud computing. A forgotten NAT Gateway costs $32/month. A forgotten RDS instance costs $12+/month. This lab ensures you have a reliable, automated way to clean up.

---

## Exercise 5: Resource Cleanup & Cost Verification

### Objectives

- Complete and run the Python cleanup script to terminate ALL resources
- Understand resource deletion order (dependencies must be deleted first)
- Verify $0 ongoing charges via the AWS Console and CLI
- Document which resources cost money even when "stopped"
- Understand why automated cleanup is essential for cloud cost management

### What You'll Do

**Part 1: Complete the Cleanup Script**

1. Open `project/scripts/aws-cleanup.py` (the skeleton from Lab 00) and implement all resource cleanup functions. The script must handle:

   **EC2 resources:**
   - Terminate all EC2 instances tagged `Project: FlowForge`
   - Wait for instances to reach "terminated" state
   - Delete associated key pairs

   **RDS resources:**
   - Delete RDS instances (skip final snapshot for course resources)
   - Delete DB subnet groups
   - Wait for RDS deletion (this takes several minutes)

   **NAT Gateway & Elastic IPs:**
   - Delete NAT Gateways
   - Wait for NAT Gateways to reach "deleted" state
   - Release Elastic IP addresses

   **VPC sub-resources (must delete before VPC):**
   - Delete security group rules first (remove dependencies between SGs)
   - Delete security groups (can't delete VPC with SGs attached)
   - Delete route table associations and custom route tables
   - Detach and delete the Internet Gateway
   - Delete subnets
   - Delete NACLs (custom ones only, not the default)

   **VPC:**
   - Delete the VPC itself (only after all sub-resources are gone)

   **S3:**
   - Empty the S3 bucket (delete all objects and versions)
   - Delete the bucket

   **ECR:**
   - Delete all images in each repository
   - Delete the repositories

   **IAM (course-created resources only):**
   - Remove users from groups
   - Delete access keys for course users
   - Detach policies from groups/users/roles
   - Delete custom policies
   - Remove role from instance profile
   - Delete instance profiles
   - Delete roles
   - Delete groups
   - Delete users
   - **Be very careful**: only delete resources tagged/named for FlowForge

2. The script must support:
   - `--dry-run`: list everything that would be deleted, but don't delete anything
   - `--region`: specify the AWS region (default: your chosen region)
   - `--force`: skip confirmation prompts (for CI/CD use later)
   - Confirmation prompt: "You are about to delete X resources. Type 'yes' to proceed."
   - Color-coded output: red for deletions, yellow for warnings, green for success
   - Summary at the end: what was deleted, what failed, what was skipped

3. Handle errors gracefully:
   - If a resource is already deleted, skip it
   - If a deletion fails (dependency error), log the error and continue
   - Retry logic for resources that take time to delete (NAT Gateway, RDS)
   - Final report should list any resources that couldn't be deleted

> **Link back**: In Module 3's Lab 4b, you wrote Python scripts with argparse, error handling, and exit codes. This cleanup script is the largest Python script in the course so far -- apply all those patterns plus retry logic and dependency ordering.

**Part 2: Run the Cleanup**

4. First, run with `--dry-run`:
   - Review every resource listed
   - Verify it found everything you created (EC2, RDS, NAT, VPC, S3, ECR, IAM)
   - If it missed something, check your tags and resource filters

5. Run the cleanup for real:
   - Confirm when prompted
   - Watch the output as resources are deleted
   - Note the order: dependencies are deleted before the resources that depend on them
   - The entire cleanup should take 5-15 minutes (RDS deletion is the slowest)

6. If any resources fail to delete:
   - Read the error message -- it usually tells you what dependency still exists
   - Fix the dependency (delete the blocking resource first)
   - Re-run the script

**Part 3: Verify via Console**

7. Sign into the AWS Console and manually verify:
   - EC2: no running instances (check all regions if you're unsure)
   - RDS: no database instances
   - VPC: no custom VPCs (only the default VPC should remain)
   - S3: no FlowForge buckets
   - ECR: no FlowForge repositories
   - Elastic IPs: none allocated
   - NAT Gateways: none
   - IAM: no FlowForge users/roles (check carefully)

8. Verify via CLI:
   ```
   aws ec2 describe-instances --filters "Name=tag:Project,Values=FlowForge"
   aws rds describe-db-instances
   aws ec2 describe-vpcs --filters "Name=tag:Project,Values=FlowForge"
   aws ec2 describe-nat-gateways --filter "Name=tag:Project,Values=FlowForge"
   aws s3 ls | grep flowforge
   aws ecr describe-repositories
   ```
   All commands should return empty results.

**Part 4: Cost Verification**

9. Check the AWS Billing Dashboard:
   - Navigate to Billing & Cost Management → Bills
   - Check your month-to-date charges
   - If there are charges, identify which service caused them
   - Are they within the free tier, or did you exceed it?

10. Check the Cost Explorer (if available):
    - Look at daily spending over the past week
    - Which days had the highest spend?
    - Which services cost the most?

11. Verify your billing alarm is still in `OK` state (not `ALARM`).

**Part 5: Document Cost Learnings**

12. Create a document (or add to the cleanup script's output) that lists which resources cost money even when "stopped":

    | Resource | Status | Still Costs Money? | Why? |
    |----------|--------|-------------------|------|
    | EC2 instance | Stopped | ? | ? |
    | EC2 instance | Terminated | ? | ? |
    | EBS volume | Detached | ? | ? |
    | RDS instance | Stopped | ? | ? |
    | NAT Gateway | N/A (can't stop) | ? | ? |
    | Elastic IP | Not attached | ? | ? |
    | S3 bucket | With objects | ? | ? |
    | ECR repository | With images | ? | ? |

13. Fill in the table with what you learned. Some resources that surprise people:
    - Stopped EC2: no compute charge, but EBS volume still costs
    - Stopped RDS: still charged (AWS restarts it after 7 days!)
    - Unattached Elastic IPs: charged specifically to discourage waste
    - EBS volumes: charged per GB even when not attached to an instance

> **Architecture Thinking**: Cloud cost management is a real discipline called FinOps. The cleanup script you wrote is primitive compared to production cost management tools, but the principles are the same: tag everything, track spend, automate cleanup, and make it impossible to accidentally leave resources running. In production, you'd use AWS Organizations, Service Control Policies, and automated Lambda functions to enforce cleanup.

> **Link forward**: In Module 6, `terraform destroy` will replace this cleanup script for infrastructure resources. But the cleanup script is still valuable as a safety net -- Terraform can only destroy what it created. Manually created resources need manual (or script-based) cleanup.

### Expected Outcome

- The Python cleanup script successfully deletes ALL FlowForge resources
- The AWS Console and CLI confirm no FlowForge resources remain
- The billing dashboard shows charges within free tier or $0
- You have a documented table of which resources cost money in various states
- The cleanup script handles errors, retries, and dependencies correctly
- You understand why automated cleanup is essential for cloud cost management

### Checkpoint Questions

1. Verify via both the AWS Console and CLI that no FlowForge resources are running.
2. Explain which resources cost money even when "stopped" and why.
3. What's the deletion order for VPC resources? Why can't you delete the VPC first?
4. If the cleanup script fails on a security group deletion, what's the most likely cause? How would you fix it?
5. How would you modify the cleanup script to run automatically on a schedule (e.g., every night at midnight)?

---

## Module 5 Complete

Congratulations! You've deployed a multi-service application to AWS with proper networking, security, and managed services -- all manually. You understand what every resource does because you created each one by hand.

Now proceed to the [Module 5 Exit Gate Checklist](checklist.md) and verify you can pass every checkpoint.

> **What's next**: In [Module 6: Terraform](../module-06-terraform/README.md), you'll define everything you just built as code. Every VPC, subnet, security group, EC2 instance, RDS database, and S3 bucket will be a Terraform resource. `terraform apply` will create it all in minutes, and `terraform destroy` will clean it all up in seconds. The pain of doing it manually in this module becomes the motivation for doing it properly with infrastructure as code.
