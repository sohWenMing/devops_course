# Module 5: AWS Fundamentals

> **Time estimate**: 2 weeks  
> **Prerequisites**: Complete Modules 1-4 (Linux, Networking, Go App, Docker), AWS free-tier account, AWS CLI v2 installed, Python 3 with boto3  
> **Link forward**: "You just did everything manually. Module 6 will codify ALL of it with Terraform"  
> **Link back**: "You built the OS foundation (Module 1), the network layer (Module 2), the FlowForge application (Module 3), and containerized it (Module 4). Now you deploy everything to real cloud infrastructure."

---

## Why This Module Matters for DevOps

Up to now, everything you've built runs on your local machine. That's fine for learning, but nobody ships software by handing out laptops. Production means cloud infrastructure -- real networks, real security boundaries, real cost consequences.

In Module 2, you learned subnets, routing, firewalls, and DNS on your local machine using network namespaces and iptables. Every single one of those concepts maps directly to an AWS service: VPCs, route tables, security groups, and Route 53. In Module 4, you built Docker images and ran them with `docker compose up`. Now you'll push those images to a real container registry (ECR), run them on real compute (EC2), and connect them to a real managed database (RDS).

This module is deliberately **manual**. You will click through the Console. You will type long AWS CLI commands. You will misconfigure things and debug them. This pain is the point -- in Module 6, you'll automate everything with Terraform, and you'll understand *exactly* what Terraform is doing under the hood because you did it by hand first.

> **AWS SAA Alignment**: This module covers the core services tested on the AWS Solutions Architect Associate exam: IAM, VPC, EC2, RDS, S3, and security group design. Every concept here maps directly to SAA exam domains.

---

## Table of Contents

1. [AWS Account Setup & Billing](#1-aws-account-setup--billing)
2. [IAM Fundamentals](#2-iam-fundamentals)
3. [VPC Networking from Scratch](#3-vpc-networking-from-scratch)
4. [Security Groups & NACLs](#4-security-groups--nacls)
5. [EC2 Instances](#5-ec2-instances)
6. [RDS PostgreSQL](#6-rds-postgresql)
7. [S3 Basics](#7-s3-basics)
8. [ECR Container Registry](#8-ecr-container-registry)
9. [Manual Deployment Workflow](#9-manual-deployment-workflow)
10. [Cost Awareness & Cleanup](#10-cost-awareness--cleanup)

---

## 1. AWS Account Setup & Billing

### The Root Account Problem

When you create an AWS account, you get a **root account** -- an all-powerful identity that can do literally anything: delete every resource, close the account, change billing details. This is the most dangerous credential you'll ever own.

The first thing you do with root is **lock it down**: enable MFA (multi-factor authentication), create an admin IAM user, and never use root again. This is the same principle as disabling root SSH login from Module 1's Lab 04 -- you don't operate with maximum privilege.

### Free Tier

AWS offers a 12-month free tier for new accounts that includes:
- **EC2**: 750 hours/month of t2.micro or t3.micro (Linux)
- **RDS**: 750 hours/month of db.t3.micro (single-AZ)
- **S3**: 5 GB standard storage, 20,000 GET requests, 2,000 PUT requests
- **ECR**: 500 MB of storage
- **CloudWatch**: 10 custom metrics, 10 alarms
- **Lambda**: 1 million free requests/month (we won't use this yet, but good to know)

The catch: free tier doesn't protect you from mistakes. Launch a `m5.xlarge` instead of `t3.micro`? Leave a NAT gateway running for a month? That's real money. This is why we set up billing alarms immediately and write cleanup scripts.

### Billing Alarms and Budgets

A **billing alarm** uses CloudWatch to notify you when your estimated charges exceed a threshold. For this course, set a $5 threshold -- any charges above that mean you forgot to clean up resources.

A **budget** in AWS Budgets gives you more granular control: you can set monthly budgets, track actual vs. forecasted spend, and receive alerts at percentage thresholds (e.g., warn at 80%, alarm at 100%).

> **Architecture Thinking**: Why does AWS make it possible to accidentally spend money? It's a trade-off: on-demand provisioning gives you speed and flexibility, but it also means you're responsible for cleanup. This is why Infrastructure as Code (Module 6) and CI/CD automation (Module 7) matter -- they make resource lifecycle management repeatable and auditable.

> **Link forward**: In Module 6, Terraform will track every resource it creates and `terraform destroy` will clean up everything. But until you get there, your Python cleanup script is your safety net.

---

## 2. IAM Fundamentals

### The Identity Model

AWS Identity and Access Management (IAM) controls **who** can do **what** on **which** resources. It's the foundational security layer for everything in AWS.

There are four key building blocks:

**Users** represent individual people or applications that need to interact with AWS. Each user has credentials (password for Console, access keys for CLI/API). In this course, you'll create a deployment user instead of using root.

**Groups** are collections of users. Instead of attaching policies to each user, you attach policies to a group and add users to that group. This scales: when a new team member joins, you add them to the "developers" group instead of copying policies from another user.

**Policies** are JSON documents that define permissions. A policy has three key elements:
- **Effect**: Allow or Deny
- **Action**: What API calls are permitted (e.g., `ec2:DescribeInstances`, `s3:GetObject`)
- **Resource**: Which specific resources the actions apply to (e.g., a specific S3 bucket ARN)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::flowforge-artifacts/*"
    }
  ]
}
```

> **Link back**: Remember the Linux permission model from Module 1? `chmod 640` means owner can read+write, group can read, others can't access. IAM policies are the same concept at cloud scale -- you're defining who can do what, but now "who" spans users, services, and even other AWS accounts.

**Roles** are identities that are *assumed*, not *logged into*. They're for services, not people. When your EC2 instance needs to read from S3, it doesn't get access keys -- it assumes a role that has S3 read permissions. The role provides temporary credentials that rotate automatically.

### Instance Profiles

An **instance profile** is the bridge between IAM roles and EC2 instances. When you launch an EC2 instance, you attach an instance profile, which contains a role. The instance can then make AWS API calls using that role's permissions -- no access keys stored on the instance.

This is critical for security: access keys are long-lived credentials that can be leaked. Instance profile roles provide temporary credentials that rotate automatically.

### The Policy Simulator

Before deploying a policy to production, you can test it with the **IAM Policy Simulator**. It lets you select a user or role and test whether specific actions on specific resources would be allowed or denied. This is how you verify your least-privilege policies actually work.

### Least Privilege

The principle of least privilege means granting **only the permissions needed to perform a specific task** and nothing more. It's the most important security principle in cloud:

- Don't give `s3:*` when `s3:GetObject` on a single bucket is sufficient
- Don't use `Resource: "*"` when you can scope to specific ARNs
- Don't create one "admin" policy when you can create separate policies per function

> **Architecture Thinking**: How do you decide what permissions a service needs? Start with zero permissions. Run the application. It will fail with "Access Denied." Read the error message -- it tells you exactly which action on which resource was denied. Add that specific permission. Repeat. This iterative approach builds a minimal, precise policy.

> **AWS SAA Tie-in**: IAM is tested heavily on the SAA exam. Understand the difference between identity-based policies (attached to users/groups/roles) and resource-based policies (attached to S3 buckets, SQS queues, etc.). Know when to use each.

---

## 3. VPC Networking from Scratch

### What Is a VPC?

A **Virtual Private Cloud (VPC)** is your own logically isolated section of the AWS network. Think of it as your own data center in the cloud -- you control the IP address range, subnets, routing, and network gateways.

Every resource you launch (EC2, RDS, Lambda) lives inside a VPC. If you don't specify one, AWS uses the default VPC in each region. For production, you always create your own.

### CIDR Blocks and IP Planning

When you create a VPC, you assign it a CIDR block -- an IP address range. For FlowForge, we'll use `10.0.0.0/16`, which gives us 65,536 IP addresses. This is the same CIDR notation you practiced in Module 2's Lab 1b.

Within the VPC, you carve out **subnets** -- smaller IP ranges in specific Availability Zones:

```
VPC: 10.0.0.0/16 (65,536 IPs)
│
├── Public Subnet AZ-a:    10.0.1.0/24  (256 IPs) -- Internet-facing resources
├── Public Subnet AZ-b:    10.0.2.0/24  (256 IPs) -- Internet-facing resources (HA)
├── Private Subnet AZ-a:   10.0.10.0/24 (256 IPs) -- Application tier
├── Private Subnet AZ-b:   10.0.20.0/24 (256 IPs) -- Application tier (HA)
├── Database Subnet AZ-a:  10.0.100.0/24 (256 IPs) -- Database tier
└── Database Subnet AZ-b:  10.0.200.0/24 (256 IPs) -- Database tier (HA)
```

> **Link back**: In Module 2's Lab 1b, you calculated subnet ranges by hand and planned a multi-environment network layout. That exact skill applies here -- you're doing the same math, but now the subnets are real AWS infrastructure.

### Public vs Private Subnets

The difference between a public and private subnet is **routing**, not some built-in AWS flag:

- A **public subnet** has a route to an **Internet Gateway (IGW)**, so resources in it can be reached from the internet (if they have a public IP and their security group allows it).
- A **private subnet** has no route to the internet directly. Resources here are isolated. If they need outbound internet access (e.g., to pull Docker images), they go through a **NAT Gateway** in a public subnet.

```
Internet
    │
    ▼
┌─────────────┐
│    IGW      │ (Internet Gateway -- attached to VPC)
└─────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│              Public Subnet                   │
│  ┌───────────┐       ┌──────────────┐       │
│  │    EC2     │       │ NAT Gateway  │       │
│  │ (FlowForge│       │              │       │
│  │  API)      │       └──────┬───────┘       │
│  └───────────┘              │               │
└─────────────────────────────┼───────────────┘
                              │
┌─────────────────────────────┼───────────────┐
│              Private Subnet  │               │
│  ┌───────────┐              │               │
│  │    EC2     │◄─────outbound via NAT       │
│  │ (Worker)   │                              │
│  └───────────┘                              │
└─────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────┐
│              Database Subnet                 │
│  ┌───────────┐                              │
│  │    RDS     │  (no internet access at all) │
│  │ PostgreSQL │                              │
│  └───────────┘                              │
└─────────────────────────────────────────────┘
```

### Route Tables

A **route table** contains rules that determine where network traffic is directed. Each subnet is associated with exactly one route table.

For a public subnet, the route table looks like:

| Destination | Target |
|-------------|--------|
| 10.0.0.0/16 | local |
| 0.0.0.0/0 | igw-xxxxx |

For a private subnet:

| Destination | Target |
|-------------|--------|
| 10.0.0.0/16 | local |
| 0.0.0.0/0 | nat-xxxxx |

The `local` route handles all traffic within the VPC. The `0.0.0.0/0` route is the default gateway -- where traffic goes if no more specific route matches.

> **Link back**: In Module 2's Lab 3b, you set up routing between network namespaces and configured route tables manually. AWS route tables are the exact same concept -- destination-based routing with a default gateway.

### Internet Gateways and NAT Gateways

An **Internet Gateway (IGW)** is a horizontally scaled, redundant, highly available VPC component that allows communication between instances in your VPC and the internet. It performs network address translation for instances that have a public IPv4 address.

A **NAT Gateway** allows instances in a private subnet to initiate outbound connections to the internet (e.g., downloading packages, pulling Docker images) while preventing the internet from initiating connections to those instances. NAT gateways are placed in public subnets and private subnet route tables point to them.

> **Cost warning**: NAT gateways cost ~$0.045/hour ($32/month) plus data processing charges. For this course, create them only when needed and delete them during cleanup. In Module 6, Terraform will manage the lifecycle automatically.

> **Architecture Thinking**: Why have three tiers (public, private, database) instead of just putting everything in a public subnet? It's **defense in depth** -- the same concept from Module 2's firewall labs. The database tier has no internet route at all. Even if an attacker compromises the public-facing EC2 instance, they still can't directly reach the database from the internet. Each tier is an additional barrier.

> **AWS SAA Tie-in**: VPC design is one of the most heavily tested topics on the SAA exam. Know the difference between IGW and NAT Gateway, understand route table configuration, and be able to design multi-AZ VPC architectures with public and private subnets.

---

## 4. Security Groups & NACLs

### Security Groups: Stateful Firewalls

A **security group** acts as a virtual firewall at the instance level. It controls inbound and outbound traffic. Security groups are **stateful** -- if you allow an inbound request, the response is automatically allowed out, regardless of outbound rules.

Key properties:
- **Allow rules only** -- you cannot create deny rules
- **Stateful** -- return traffic is automatically allowed
- **Instance-level** -- attached to ENIs (elastic network interfaces)
- **Default behavior** -- all inbound denied, all outbound allowed
- **Can reference other security groups** -- this is the powerful feature

Referencing other security groups is the key to designing least-privilege network access:

```
api-sg:
  Inbound:
    - Port 80/443 from 0.0.0.0/0       (internet can reach the API)
    - Port 22 from YOUR_IP/32           (only you can SSH)
  Outbound:
    - All traffic allowed (default)

worker-sg:
  Inbound:
    - No inbound from internet           (workers are internal only)
  Outbound:
    - All traffic allowed (default)

db-sg:
  Inbound:
    - Port 5432 from api-sg             (API can connect to database)
    - Port 5432 from worker-sg          (Worker can connect to database)
    - Nothing else                       (database unreachable from internet)
  Outbound:
    - All traffic allowed (default)
```

> **Link back**: In Module 2's Lab 3a, you wrote iptables rules to control traffic. Security groups are the same concept but managed by AWS. The difference: iptables is stateless (you need explicit rules for both directions), security groups are stateful (return traffic is automatic). Also, iptables supports deny rules while security groups only support allow rules.

### NACLs: Stateless Firewalls

**Network Access Control Lists (NACLs)** operate at the subnet level. They are **stateless** -- you must create rules for both inbound AND outbound traffic, including ephemeral port ranges for return traffic. NACLs support both allow and deny rules, and rules are evaluated in order by rule number (lowest first).

| Feature | Security Group | NACL |
|---------|---------------|------|
| Level | Instance (ENI) | Subnet |
| Stateful? | Yes | No |
| Allow/Deny | Allow only | Both |
| Rule evaluation | All rules evaluated | In order by rule number |
| Default | Deny all inbound, allow all outbound | Allow all (default NACL) |
| Return traffic | Automatic | Must create explicit rule |

In practice, you'll use security groups for almost everything. NACLs are a second layer of defense -- useful for blocking specific IP ranges or adding subnet-level deny rules that security groups can't provide.

> **Architecture Thinking**: When debugging connectivity issues, always check security groups first, then NACLs. A common mistake is adding the right security group rule but forgetting the NACL. Since NACLs are stateless, you need inbound AND outbound rules (including ephemeral ports 1024-65535 for return traffic).

> **AWS SAA Tie-in**: The exam loves asking about stateful vs stateless. If a question describes a scenario where return traffic is blocked, the answer is always NACL (because security groups handle return traffic automatically).

---

## 5. EC2 Instances

### What Is EC2?

**Elastic Compute Cloud (EC2)** gives you virtual servers in the cloud. You choose the operating system (via an AMI), the hardware specifications (via an instance type), the network placement (VPC, subnet, security group), and how to connect (key pair for SSH).

### AMIs (Amazon Machine Images)

An **AMI** is a template that contains the OS, pre-installed software, and configuration. Think of it as a Docker image but for entire virtual machines. You can use:
- **AWS-provided AMIs**: Amazon Linux 2023, Ubuntu, Windows Server
- **Marketplace AMIs**: Pre-configured with specific software (e.g., WordPress, Jenkins)
- **Custom AMIs**: Your own images baked with your software and configuration

For this course, we'll use the latest Ubuntu AMI -- it matches the Linux skills you built in Module 1.

### Instance Types

Instance types define the hardware profile: CPU, memory, storage, and networking:

| Family | Purpose | Example | vCPUs | RAM |
|--------|---------|---------|-------|-----|
| t3 | Burstable general purpose | t3.micro | 2 | 1 GB |
| m5 | General purpose | m5.large | 2 | 8 GB |
| c5 | Compute optimized | c5.large | 2 | 4 GB |
| r5 | Memory optimized | r5.large | 2 | 16 GB |

For FlowForge, `t3.micro` is sufficient and is free-tier eligible. The "t" in t3 stands for "burstable" -- you get a baseline of CPU performance with the ability to burst above it using CPU credits.

### User Data

**User data** is a script that runs when the instance first boots. It's how you automate initial setup without SSH-ing in manually:

```bash
#!/bin/bash
apt-get update
apt-get install -y docker.io
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu
```

> **Link back**: This is the same as writing a startup script in Module 1's bash scripting lab, but instead of running it manually, you pass it to EC2 and it executes on first boot. Remember the importance of meaningful exit codes and error handling from Module 3's Python scripts? The same applies here -- if user data fails silently, you'll SSH in and wonder why Docker isn't installed.

### Key Pairs

To SSH into an EC2 instance, you use key pair authentication -- the same SSH key-based auth you set up in Module 1's Lab 04. You create a key pair in AWS (or import your own public key), and AWS injects the public key into the instance. You then SSH in with your private key.

> **Architecture Thinking**: Should you SSH into production instances? Ideally, no. SSH access means manual changes, which means configuration drift. In a mature setup (Module 8+), you'd use Kubernetes to manage containers and never touch the EC2 instance directly. But for learning, SSH is essential for understanding what's happening on the machine.

---

## 6. RDS PostgreSQL

### Why Managed Databases?

In Module 3, you installed PostgreSQL locally and managed it yourself. In Module 4, you ran PostgreSQL in a Docker container. Both approaches work, but in production, managing databases is a full-time job: backups, patching, replication, failover, monitoring, storage management.

**Amazon RDS (Relational Database Service)** handles all of that. You tell it "I want a PostgreSQL instance with 20 GB of storage" and AWS handles:
- Automated backups (with point-in-time recovery)
- Software patching
- Multi-AZ failover (if configured)
- Storage auto-scaling
- CloudWatch monitoring

### Free Tier for RDS

- **db.t3.micro**: 750 hours/month (enough for one instance running 24/7)
- **20 GB** of General Purpose SSD storage
- **20 GB** of backup storage
- Single-AZ only for free tier

### Multi-AZ vs Read Replicas

**Multi-AZ** is about **availability**: RDS maintains a synchronous standby copy in a different Availability Zone. If the primary fails, RDS automatically fails over to the standby. Your application's database endpoint doesn't change -- the DNS record updates automatically.

**Read Replicas** are about **performance**: asynchronous copies of the database that handle read traffic. Your application sends writes to the primary and reads to the replica. This scales read-heavy workloads.

| Feature | Multi-AZ | Read Replica |
|---------|---------|-------------|
| Purpose | High availability | Read scaling |
| Replication | Synchronous | Asynchronous |
| Failover | Automatic | Manual promotion |
| Endpoint | Same endpoint | Different endpoint |
| Cost | ~2x primary | ~1x primary per replica |
| Free tier | No | No |

For this course, we'll use a single-AZ db.t3.micro to stay within free tier. But understanding Multi-AZ and read replicas is essential for the SAA exam and production architectures.

### Subnet Groups

RDS instances are launched into **DB subnet groups** -- a collection of subnets in at least two Availability Zones. This is where your database subnet planning from Section 3 pays off. The database subnets have no internet route, and the security group only allows connections from the application tier.

> **Link back**: In Module 3, you connected to PostgreSQL using `database/sql` with a connection string from environment variables. That exact code works with RDS -- you just change the host from `localhost` to the RDS endpoint. The 12-Factor configuration from Lab 4a makes this switch trivial.

> **AWS SAA Tie-in**: Know when to use Multi-AZ (disaster recovery, high availability) vs read replicas (read scaling). The exam often presents scenarios where you need to choose between them.

---

## 7. S3 Basics

### Object Storage vs Block Storage

**S3 (Simple Storage Service)** is object storage -- you store files (objects) in containers (buckets). Unlike a filesystem (block storage, like EBS), S3 stores each object with metadata and a unique key. There's no directory hierarchy in S3 -- the "folders" you see in the console are just key prefixes.

For FlowForge, S3 is useful for:
- Storing deployment artifacts (Docker build contexts, config files)
- Application logs (long-term storage)
- Static assets
- Backup storage

### Bucket Policies

A **bucket policy** is a resource-based IAM policy attached to an S3 bucket. It defines who can do what with the bucket and its objects:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowEC2RoleAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/flowforge-ec2-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::flowforge-artifacts/*"
    }
  ]
}
```

> **Link back**: This is the same Allow/Deny/Action/Resource structure from IAM policies in Section 2, but attached to the resource instead of the identity. In Module 1, you used file permissions to control who can access what. S3 bucket policies are the cloud equivalent.

### Storage Classes

S3 offers different storage classes with different cost/performance trade-offs:

| Class | Use Case | Retrieval | Cost |
|-------|----------|-----------|------|
| Standard | Frequent access | Immediate | $$ |
| Standard-IA | Infrequent access | Immediate | $ (+ retrieval fee) |
| Glacier Instant | Archive with instant access | Immediate | $ |
| Glacier Flexible | Archive (minutes to hours) | 1-12 hours | ¢ |
| Glacier Deep Archive | Long-term archive | 12-48 hours | ¢¢ |

### Versioning and Lifecycle

**Versioning** keeps multiple variants of an object in the same bucket. When you overwrite an object, S3 keeps the old version. This protects against accidental deletions and overwrites.

**Lifecycle policies** automate transitions between storage classes and deletions. For example: "Move objects to Standard-IA after 30 days, Glacier after 90 days, delete after 365 days."

> **Architecture Thinking**: S3 isn't just a file dump -- it's a building block. In production, you might store Terraform state (Module 6), CI/CD artifacts (Module 7), application logs, and database backups in S3. Each use case might warrant a different bucket with different policies, versioning, and lifecycle rules.

> **AWS SAA Tie-in**: S3 storage classes, versioning, and lifecycle policies are heavily tested. Know the cost trade-offs and when to use each class.

---

## 8. ECR Container Registry

### What Is ECR?

**Elastic Container Registry (ECR)** is a managed Docker container registry. It's where you push Docker images so AWS services (EC2, ECS, EKS) can pull them. Think of it as a private Docker Hub scoped to your AWS account.

> **Link back**: In Module 4, you built Docker images and stored them locally. Now you push them to ECR so they're accessible from any EC2 instance in your account. The `docker push` and `docker pull` commands are the same -- only the registry URL changes.

### ECR Workflow

1. **Create a repository** for each image (e.g., `flowforge/api-service`, `flowforge/worker-service`)
2. **Authenticate** Docker to ECR using `aws ecr get-login-password`
3. **Tag** your local image with the ECR repository URI
4. **Push** the image to ECR
5. **Pull** the image on EC2 (or any compute resource with ECR permissions)

### Image Tagging Strategies

Don't use `latest`. Ever. Instead:
- **Git SHA**: `flowforge/api-service:abc123f` -- ties the image to exact source code
- **Semantic version**: `flowforge/api-service:1.2.3` -- human-readable version
- **Git SHA + timestamp**: `flowforge/api-service:abc123f-20241215` -- unique and sortable

> **Link forward**: In Module 7 (CI/CD), your GitHub Actions pipeline will automatically build, tag with the git SHA, and push images to ECR on every merge to main. But first, you need to understand the manual process.

> **Architecture Thinking**: Why use ECR instead of Docker Hub? ECR integrates with IAM for authentication, lives in your AWS account (lower latency for pulls), supports image scanning for vulnerabilities, and lifecycle policies for cleaning up old images. For production workloads on AWS, ECR is the natural choice.

---

## 9. Manual Deployment Workflow

### The Complete Picture

After completing Labs 0-4, you'll have all the pieces in place. Lab 4b ties them together:

```
┌─────────────────────────────────────────────────────────┐
│                     Your VPC (10.0.0.0/16)               │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Public Subnet (10.0.1.0/24)            │   │
│  │                                                    │   │
│  │   ┌────────────────────┐                          │   │
│  │   │     EC2 (t3.micro) │   ←── SSH from your IP   │   │
│  │   │  ┌──────────────┐  │   ←── HTTP from internet │   │
│  │   │  │ api-service   │  │                          │   │
│  │   │  │ (Docker)      │  │                          │   │
│  │   │  └──────────────┘  │                          │   │
│  │   │  ┌──────────────┐  │                          │   │
│  │   │  │ worker-service│  │                          │   │
│  │   │  │ (Docker)      │  │                          │   │
│  │   │  └──────────────┘  │                          │   │
│  │   └────────────────────┘                          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Database Subnet (10.0.100.0/24)          │   │
│  │                                                    │   │
│  │   ┌────────────────────┐                          │   │
│  │   │  RDS PostgreSQL    │  ←── from EC2 only       │   │
│  │   │  (db.t3.micro)     │                          │   │
│  │   └────────────────────┘                          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ECR: flowforge/api-service:v1                           │
│  ECR: flowforge/worker-service:v1                        │
│  S3: flowforge-artifacts (deployment configs)            │
└─────────────────────────────────────────────────────────┘
```

The deployment flow:
1. Push Docker images to ECR (from your machine)
2. SSH into EC2
3. Pull images from ECR on EC2
4. Run containers with environment variables pointing to RDS
5. Verify the API responds, the worker processes tasks, and data persists in RDS

This is tedious and error-prone. That's intentional. By Module 6, Terraform replaces the infrastructure setup. By Module 7, CI/CD replaces the deployment steps. By Module 8, Kubernetes replaces the container management.

> **Architecture Thinking**: Count the manual steps in the deployment. How many of them could be automated? What happens if you need to deploy to a second environment (staging)? You'd have to repeat every step. This is why infrastructure as code exists -- not because the manual steps are hard, but because they don't scale and they drift.

---

## 10. Cost Awareness & Cleanup

### Resources That Cost Money

Not everything in AWS costs money, but some things are easy to forget:

| Resource | Cost When Running | Cost When Stopped | Cost When Deleted |
|----------|-------------------|-------------------|-------------------|
| EC2 (t3.micro) | Free tier 750 hrs | No compute charge, but **EBS volume still charged** | $0 |
| RDS (db.t3.micro) | Free tier 750 hrs | **Still charged** (stopped RDS restarts after 7 days) | $0 |
| NAT Gateway | ~$0.045/hr ($32/mo) | N/A (can't stop, only delete) | $0 |
| Elastic IP | Free when attached to running instance | **$0.005/hr when unattached** | $0 |
| S3 | Per GB stored | N/A | $0 (after empty) |
| ECR | Per GB stored | N/A | $0 |
| EBS Volumes | Per GB provisioned | Per GB provisioned (same) | $0 |

The most common surprise charges:
- **NAT Gateways left running**: $32/month
- **Elastic IPs not attached**: They're free when attached to a running instance, charged when not
- **RDS "stopped" for too long**: AWS restarts stopped RDS instances after 7 days
- **EBS volumes orphaned**: When you terminate an EC2 instance, the EBS volume might persist

### The Cleanup Script

Your Python cleanup script (`project/scripts/aws-cleanup.py`) is the safety net. It:
1. Lists all resources created for the course (tagged with `Project: FlowForge`)
2. Shows what will be deleted (dry-run mode)
3. Asks for confirmation
4. Deletes everything in the correct order (dependencies first)
5. Verifies the cleanup was complete

> **Link forward**: In Module 6, `terraform destroy` will replace the cleanup script. In Module 7, CI/CD pipelines will manage resource lifecycle. But having a cleanup script is a safety net -- even with Terraform, you might have manually created resources that Terraform doesn't know about.

> **Architecture Thinking**: Why tag everything? Tags are the only way to identify "which resources belong to this project" when you have multiple projects in one AWS account. The `Project: FlowForge` tag makes cleanup reliable and auditable. In production, teams use tags for cost allocation, ownership tracking, and automated cleanup.

---

## Lab Progression

| Lab | Exercises | What You'll Build |
|-----|-----------|-------------------|
| [Lab 00: Account & Billing](lab-00-account-billing.md) | 0 | AWS account, MFA, billing alarm, budget, cleanup script |
| [Lab 01: IAM](lab-01-iam.md) | 1a, 1b | IAM users, groups, policies, roles, instance profiles |
| [Lab 02: VPC & Networking](lab-02-vpc-networking.md) | 2a, 2b | VPC, subnets, gateways, route tables, security groups, NACLs |
| [Lab 03: Compute & Storage](lab-03-compute-storage.md) | 3a, 3b, 3c | EC2 instance, RDS PostgreSQL, S3 bucket |
| [Lab 04: ECR & Deploy](lab-04-ecr-deploy.md) | 4a, 4b | ECR repos, Docker image push/pull, full manual deployment |
| [Lab 05: Cleanup](lab-05-cleanup.md) | 5 | Resource cleanup, cost verification, documentation |

---

## What's Next

After completing this module, you'll understand how cloud infrastructure works by having built it manually. You'll feel the pain of clicking through consoles, typing long CLI commands, and forgetting to clean up resources.

In [Module 6: Terraform](../module-06-terraform/README.md), you'll codify **everything** you did in this module. Every VPC, subnet, security group, EC2 instance, RDS database, and S3 bucket will be defined in code. `terraform apply` will create it all in minutes, and `terraform destroy` will clean it up in seconds. The manual pain of Module 5 becomes the motivation for Module 6.

> **Remember**: The goal of this module isn't just to deploy FlowForge to AWS. It's to understand what's happening at every layer so that when Terraform abstracts it away, you know what's underneath. When a Terraform plan fails, you'll know exactly which AWS resource, security group, or route table is the problem -- because you built them all by hand.
