# Module 5: AWS Fundamentals -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 6.  
> No partial credit. No "I think so." Either you can do it or you can't.  
> If you can't, go back to the relevant lab and practice until you can.

---

## How to Use This Checklist

For each item:
1. Attempt it **without looking at notes, previous labs, or the internet**
2. If you succeed, mark it `[x]`
3. If you fail or need to look something up, mark it `[ ]` and go practice
4. Come back and try again until every box is checked

---

## AWS Account & Billing (Lab 00, Exercise 0)

- [ ] MFA is enabled on my root account
- [ ] I have a CloudWatch billing alarm set at $5
- [ ] I have an AWS Budget with alerts at 50% and 100%
- [ ] I can find my current month-to-date charges in the Billing Console
- [ ] I can explain what the free tier covers for EC2, RDS, S3, and ECR
- [ ] I can explain why billing safeguards are the first thing you set up, not the last

---

## IAM Users, Groups & Policies (Lab 01, Exercise 1a)

- [ ] I have an admin IAM user and never use root for day-to-day work
- [ ] I have a deployment user with a custom least-privilege policy
- [ ] Given a JSON IAM policy, I can explain exactly what it allows and denies
- [ ] I can write an IAM policy from scratch that allows EC2 describe + S3 read-only for one bucket
- [ ] I can use the Policy Simulator to verify permissions
- [ ] I can explain how policy evaluation works (explicit Deny always wins)
- [ ] I can explain why groups are preferred over attaching policies directly to users

---

## IAM Roles & Instance Profiles (Lab 01, Exercise 1b)

- [ ] I can explain why IAM roles are preferred over access keys on EC2
- [ ] I can describe the difference between a user, group, role, and policy
- [ ] I have an EC2 instance profile with S3 read, CloudWatch write, and ECR pull permissions
- [ ] I can explain what a trust policy is and who the Principal is for an EC2 role
- [ ] I can explain the difference between identity-based and resource-based policies

---

## VPC Architecture (Lab 02, Exercise 2a)

- [ ] I can draw the VPC architecture from memory (VPC, subnets, IGW, NAT, route tables)
- [ ] I can create a VPC with subnets, route tables, and gateways from the CLI without notes
- [ ] I can explain the traffic flow from the internet to an EC2 in a public subnet
- [ ] I can explain the traffic flow from a private subnet instance to the internet (via NAT)
- [ ] I can explain why database subnets have no internet route
- [ ] I can explain the difference between an Internet Gateway and a NAT Gateway
- [ ] I can calculate usable IPs in an AWS subnet (total minus 5 reserved)
- [ ] I can explain why you need subnets in at least two Availability Zones

---

## Security Groups & NACLs (Lab 02, Exercise 2b)

- [ ] I can explain the difference between security groups and NACLs (stateful vs stateless, allow vs deny)
- [ ] I have security groups that follow least privilege: api-sg, worker-sg, db-sg
- [ ] The database security group only allows connections from the api and worker security groups
- [ ] SSH is only allowed from my IP (not 0.0.0.0/0)
- [ ] I can explain why referencing a security group ID is better than an IP address
- [ ] Given a connectivity problem, I can determine whether it's a security group or NACL issue
- [ ] I can write security group rules from scratch for a new 3-tier architecture

---

## EC2 Instances (Lab 03, Exercise 3a)

- [ ] I can launch an EC2 instance from the CLI from memory
- [ ] I can explain instance types, AMIs, user data, and key pairs
- [ ] I can SSH into an EC2 instance using key-based authentication
- [ ] Docker is installed on my EC2 instance (via user data or manual installation)
- [ ] The instance profile provides AWS credentials (verified with aws sts get-caller-identity)
- [ ] I can run a FlowForge container on EC2 and access it from the internet
- [ ] If I can't SSH into an instance, I can list at least 5 things to check

---

## RDS PostgreSQL (Lab 03, Exercise 3b)

- [ ] An RDS PostgreSQL instance is running in the database subnet (not publicly accessible)
- [ ] I can connect to RDS from EC2 using psql
- [ ] I can explain Multi-AZ vs Read Replicas and when to use each
- [ ] I can configure a connection from a new EC2 to the existing RDS without a guide
- [ ] I can explain what RDS manages for you and what you still control
- [ ] I can explain what happens if an RDS instance is stopped vs deleted

---

## S3 (Lab 03, Exercise 3c)

- [ ] An S3 bucket exists with versioning enabled and public access blocked
- [ ] I can upload and download files via CLI and Python boto3
- [ ] I can explain S3 storage classes (Standard, IA, Glacier) and when to use each
- [ ] I can write a bucket policy from scratch for a specific IAM role
- [ ] I can explain S3 versioning and lifecycle policies
- [ ] The EC2 instance accesses S3 using instance profile credentials (no access keys)

---

## ECR (Lab 04, Exercise 4a)

- [ ] ECR repositories exist for api-service and worker-service
- [ ] I can push images from my local machine and pull them on EC2
- [ ] I can push a new image version and pull it on EC2 without referencing previous commands
- [ ] I can explain image tagging strategies and why not to use `latest`
- [ ] I can authenticate Docker with ECR using the get-login-password flow

---

## Manual Deployment (Lab 04, Exercise 4b)

- [ ] FlowForge runs on AWS: api-service and worker-service in Docker on EC2, connected to RDS
- [ ] The end-to-end flow works: create task via API → worker processes → data in RDS
- [ ] The API is accessible from the internet via the EC2 public IP
- [ ] A Python health check script validates the deployment
- [ ] I documented every manual step and know which parts Terraform/CI/CD/K8s would automate

---

## Cleanup & Cost (Lab 05, Exercise 5)

- [ ] The Python cleanup script terminates all FlowForge resources
- [ ] I verified via both Console and CLI that no resources remain
- [ ] The billing dashboard confirms charges are within free tier or $0
- [ ] I can explain which resources cost money when "stopped" (EC2/EBS, RDS, Elastic IPs)
- [ ] I can explain the resource deletion order for VPC cleanup
- [ ] The cleanup script has dry-run mode, confirmation prompts, and error handling

---

## Integration & Architecture Thinking

- [ ] FlowForge runs on AWS (EC2 + RDS) and is accessible from the internet
- [ ] VPC has public, private, and database subnets with correct routing
- [ ] Security groups follow least privilege (no 0.0.0.0/0 on SSH, DB only from app tier)
- [ ] IAM uses a dedicated user with a custom policy, not root
- [ ] I can draw the full AWS architecture diagram from memory
- [ ] I can create a VPC with subnets, route tables, and security groups from CLI without notes
- [ ] The cleanup script runs and billing dashboard confirms no ongoing charges
- [ ] I can explain how every AWS concept maps to what I learned in previous modules:
  - VPC/subnets → Module 2 network namespaces and subnets
  - Security groups → Module 2 iptables/ufw
  - EC2 user data → Module 1 bash scripting
  - SSH key pairs → Module 1 SSH lab
  - IAM permissions → Module 1 file permissions
  - RDS connection → Module 3 PostgreSQL integration
  - ECR → Module 4 Docker images
  - Container env vars → Module 3 12-Factor config

---

## Final Self-Assessment

> Answer honestly:
>
> **Could I build a VPC with subnets, security groups, EC2, RDS, S3, and ECR from scratch -- all via the AWS CLI -- on a fresh AWS account with no notes and no internet access?**
>
> - If YES for everything: You're ready for Module 6. Congratulations!
> - If NO for anything: Go back and practice. The manual understanding is essential before automating with Terraform.

---

## Ready for Module 6?

If every box above is checked, proceed to [Module 6: Terraform](../module-06-terraform/README.md).

> **What's coming**: In Module 6, you'll define everything you built manually in this module as Terraform code. Every VPC, subnet, security group, EC2 instance, RDS database, S3 bucket, and ECR repository becomes a `.tf` file. `terraform apply` will create it all in minutes. `terraform destroy` will clean it up in seconds. And when something changes, `terraform plan` will show you exactly what will be modified before you apply it. The manual pain of Module 5 becomes your greatest asset -- you'll know exactly what Terraform is doing under the hood.
