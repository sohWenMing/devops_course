# Lab 05: Full Infrastructure Recreation

> **Module**: 6 -- Terraform  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Labs 01-04 completed (modularized, parameterized config with remote state). Module 5 understanding of the full FlowForge AWS architecture.

---

## Overview

This is the payoff lab. In Module 5, you spent hours manually creating VPCs, subnets, security groups, EC2 instances, RDS databases, S3 buckets, and ECR repositories. Now you'll destroy everything and recreate the **entire** FlowForge infrastructure with a single `terraform apply` command. Then you'll verify that everything works identically.

---

## Exercise 5: Destroy and Recreate FlowForge Infrastructure

### Objectives

- Verify that your Terraform config can recreate the complete FlowForge infrastructure from scratch
- Prove that Infrastructure as Code makes your environment reproducible
- Experience the confidence of `terraform apply` after the pain of manual provisioning
- Validate end-to-end functionality after recreation
- Understand what "infrastructure as code" truly means in practice

### What You'll Do

**Part 1: Ensure Your Config is Complete**

1. Before destroying anything, verify your Terraform configuration covers the **entire** FlowForge infrastructure from Module 5:
   - [ ] VPC with `10.0.0.0/16` CIDR
   - [ ] 6 subnets across 2 AZs (2 public, 2 private, 2 database)
   - [ ] Internet gateway
   - [ ] NAT gateway (or NAT instance for cost savings)
   - [ ] Route tables (public, private, database) with correct routes
   - [ ] Security groups (api-sg, worker-sg, db-sg) with least-privilege rules
   - [ ] EC2 instance in public subnet with Docker installed (user data)
   - [ ] RDS PostgreSQL in database subnet
   - [ ] S3 bucket for artifacts
   - [ ] ECR repositories for api-service and worker-service
   - [ ] IAM instance profile for EC2
   - [ ] Proper tags on every resource

2. Run `terraform plan` against your complete config:
   - If you've already applied, it should show "No changes"
   - If not, review the plan to ensure it creates everything needed
   - Count the total number of resources. How does this compare to the number of CLI commands you typed in Module 5?

3. Make sure you have outputs for everything a deployment needs:
   - EC2 instance public IP (for SSH and API access)
   - RDS endpoint (for database connection strings)
   - ECR repository URLs (for Docker push/pull)
   - VPC ID and subnet IDs (for verification)

> **Link back**: Look at your Module 5 notes or lab work. Count the manual steps you took. Count the AWS CLI commands. Count the times you copied an ID from one command to paste into another. All of that is now ~200 lines of HCL.

**Part 2: Destroy Everything**

4. If you have any manually-created Module 5 resources still running, clean them up first:
   - Run the Python cleanup script from Module 5: `python3 project/scripts/aws-cleanup.py --dry-run`
   - If it finds anything, run without `--dry-run` to clean up
   - Verify nothing remains from Module 5

5. Destroy the Terraform-managed infrastructure:
   ```
   terraform destroy
   ```
   - Read the destroy plan carefully -- how many resources will be destroyed?
   - Watch the order -- Terraform reverses the dependency graph
   - Note how long the destroy takes (especially RDS -- it can take several minutes)

6. Verify everything is gone:
   - `aws ec2 describe-vpcs --filters "Name=tag:Project,Values=FlowForge"` -- should return nothing
   - `aws rds describe-db-instances` -- no FlowForge instances
   - `aws s3 ls` -- no FlowForge buckets (other than the state bucket)
   - `aws ecr describe-repositories` -- no FlowForge repos
   - Check the billing dashboard -- no running resources

7. This is **zero state**. No FlowForge infrastructure exists. Take a moment to appreciate (or dread) this.

**Part 3: Recreate Everything**

8. Run the magic command:
   ```
   terraform apply -var-file="dev.tfvars"
   ```
   (Or whichever variable file you want to use)

9. Watch the output:
   - How many resources are being created?
   - What order does Terraform create them in?
   - How long does the entire apply take? Note the time.
   - Compare this to how long Module 5 took you manually

10. When complete, note all the outputs:
    - EC2 public IP
    - RDS endpoint
    - ECR repository URLs
    - VPC ID

**Part 4: Verify Everything Works**

11. SSH into the EC2 instance:
    - Use the public IP from the output
    - Verify Docker is installed (from user data)
    - Verify the instance profile provides AWS credentials: `aws sts get-caller-identity`

12. Verify the RDS database is accessible from EC2:
    - Use the RDS endpoint from the output
    - Connect with psql from the EC2 instance
    - Can you create the FlowForge schema?

13. Verify ECR works:
    - Authenticate Docker with ECR from EC2
    - Can you push and pull images?

14. (If you have the full FlowForge stack ready) Deploy and test the application:
    - Push FlowForge Docker images to ECR
    - Pull and run them on EC2
    - Connect to RDS
    - Create a task via the API
    - Verify the worker processes it
    - Verify data in RDS

15. Compare this infrastructure to what you built manually in Module 5:
    - Is the VPC CIDR the same?
    - Are the security group rules identical?
    - Is the RDS configuration the same?
    - Are there any differences? (There probably will be small ones -- document them)

> **Architecture Thinking**: You just went from zero infrastructure to a fully running environment with a single command. Think about what this enables: disaster recovery, environment cloning, infrastructure auditing, and repeatable deployments. If your production environment went down, how long would it take to recreate it with Terraform vs. manually? What's the business value of reducing recovery time from hours to minutes?

**Part 5: The Confidence Test**

16. Destroy everything again:
    ```
    terraform destroy
    ```

17. And recreate again:
    ```
    terraform apply -var-file="dev.tfvars"
    ```

18. Does it work identically the second time? It should. This is the **reproducibility guarantee** of Infrastructure as Code.

**Part 6: Document the Comparison**

19. Write a brief comparison document (for your own reference):
    - How many manual steps did Module 5 require?
    - How many Terraform commands does the same result require?
    - How long did manual setup take vs. Terraform apply?
    - What can go wrong with manual steps that can't go wrong with Terraform?
    - What can go wrong with Terraform that can't go wrong manually?

20. Clean up (destroy) when done -- unless you want to keep it running for future labs.

> **Link forward**: In Module 7, you'll wire `terraform apply` into a CI/CD pipeline. Push to main, and your infrastructure automatically updates. But that requires trust in your Terraform config -- trust you just built by proving it can recreate everything from scratch.

### Expected Outcomes

- Complete FlowForge infrastructure destroyed and recreated from scratch
- Single `terraform apply` creates all AWS resources
- End-to-end functionality verified (SSH, RDS, ECR, optionally full app deployment)
- Understanding of the value proposition of Infrastructure as Code
- Written comparison of manual vs. Terraform deployment

### Checkpoint Questions

1. How many resources does your Terraform config create in total?
2. How long does `terraform apply` take from zero to fully running? How does this compare to Module 5 manual setup?
3. If you ran `terraform apply` a third time, what would happen?
4. What would you do if `terraform apply` failed halfway through?
5. What's the business case for Infrastructure as Code? How would you explain it to a manager?
6. Starting from zero, could you have FlowForge running on AWS within 15 minutes? What would you need?

---

## Before You Move On

Before proceeding to Lab 06:
- [ ] You can destroy and recreate the entire FlowForge infrastructure with Terraform
- [ ] `terraform apply` creates everything from scratch with no manual steps
- [ ] You've verified that the recreated infrastructure functions correctly
- [ ] You can articulate the value of Infrastructure as Code to a non-technical stakeholder
- [ ] Infrastructure is cleaned up (destroyed) to avoid ongoing charges
