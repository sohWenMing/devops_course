# Lab 06: Debugging Terraform -- Broken Configurations

> **Module**: 6 -- Terraform  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Labs 01-05 completed. Solid understanding of Terraform resources, state, providers, and the plan/apply lifecycle.

---

## Overview

In production, Terraform configurations break. Dependencies get tangled, references go wrong, state gets corrupted, and provider updates introduce incompatibilities. This lab presents four deliberately broken Terraform configurations. Your job is to diagnose the root cause and fix each one -- using only the error messages, Terraform commands, and your understanding of Terraform internals.

This is the Terraform equivalent of the broken server (Module 1) and broken network (Module 2) labs.

---

## Exercise 6: Four Terraform Bugs

### Objectives

- Diagnose Terraform errors from error messages and plan output
- Fix circular dependencies
- Fix incorrect resource references
- Recover from simulated state corruption
- Resolve provider version conflicts
- Develop a systematic Terraform debugging methodology

### General Instructions

For each bug:
1. **Read the error message carefully** -- Terraform errors are usually specific
2. **Identify the root cause** -- Don't just fix the symptom
3. **Fix the issue** -- Make the minimum change needed
4. **Verify** -- Run `terraform validate`, `terraform plan`, and/or `terraform apply` to confirm
5. **Document** -- Write down the error, root cause, fix, and what you learned

Do NOT look at the answer key or search for the exact error message. Use your understanding of Terraform concepts to reason through each problem.

---

### Bug 1: Circular Dependency

**Scenario**: You're setting up security groups for FlowForge. The API service needs to allow traffic from the worker service, and the worker service needs to allow traffic from the API service.

Create a directory (e.g., `project/infra/lab-06-bug1/`) with this configuration:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags       = { Name = "debug-vpc" }
}

resource "aws_security_group" "api" {
  name        = "api-sg"
  description = "Security group for API service"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.worker.id]
  }

  tags = { Name = "api-sg" }
}

resource "aws_security_group" "worker" {
  name        = "worker-sg"
  description = "Security group for Worker service"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 9090
    to_port         = 9090
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
  }

  tags = { Name = "worker-sg" }
}
```

**Your task**:
1. Run `terraform validate` or `terraform plan`
2. Read the error message -- what does it tell you?
3. Draw the dependency graph -- where is the cycle?
4. Fix the circular dependency without removing the security rules
5. Verify the fix with `terraform validate` and `terraform plan`

**Hint**: Think about whether the ingress rules need to be part of the security group resource definition, or if there's another way to define them...

---

### Bug 2: Wrong Resource Reference

**Scenario**: You're creating an EC2 instance that should be placed in a specific subnet, but the configuration has a reference error.

Create a directory (e.g., `project/infra/lab-06-bug2/`) with this configuration:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags       = { Name = "debug-vpc" }
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  tags              = { Name = "debug-public-subnet" }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1a"
  tags              = { Name = "debug-private-subnet" }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "api" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public.subnet_id

  tags = { Name = "debug-api-instance" }
}

resource "aws_instance" "worker" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.private_subnet.id

  tags = { Name = "debug-worker-instance" }
}
```

**Your task**:
1. Run `terraform validate`
2. There are **two** reference errors. Find and fix both
3. Understand why each reference was wrong
4. Verify with `terraform validate` and `terraform plan`

**Hint**: Look carefully at the attribute names and resource addresses. What attributes does `aws_subnet` actually export? What's the correct way to reference a resource?

---

### Bug 3: State Corruption Simulation

**Scenario**: You have a working configuration with an S3 bucket. Something went wrong and the state is now out of sync with reality.

Create a directory (e.g., `project/infra/lab-06-bug3/`) and follow these steps:

1. Write a simple config that creates an S3 bucket with a unique name and some tags.

2. Apply the config successfully. Verify the bucket exists.

3. Now **simulate state corruption** by removing the bucket from state:
   ```
   terraform state rm aws_s3_bucket.main
   ```
   This simulates what happens when state gets corrupted or out of sync.

4. Run `terraform plan`. What does Terraform think needs to happen?
   - It wants to **create** the bucket because it's not in state
   - But the bucket already exists in AWS!

5. If you apply, what would happen?
   - Think about it before trying. The bucket name already exists in S3...

**Your task**:
1. Without destroying the actual bucket, get Terraform back in sync
2. The bucket should exist in both AWS and Terraform state
3. Running `terraform plan` should show "No changes"
4. You should NOT need to create any new AWS resources

**Hint**: There's a Terraform command specifically designed for this situation. You used it in Lab 02.

---

### Bug 4: Provider Version Conflict

**Scenario**: You're working on a shared Terraform config and someone updated the provider version constraint, but the lock file still references the old version.

Create a directory (e.g., `project/infra/lab-06-bug4/`) with this configuration:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 4.67.0"
    }
  }
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project   = "FlowForge"
      ManagedBy = "Terraform"
    }
  }
}

resource "aws_s3_bucket" "test" {
  bucket = "debug-provider-test-${random_string.suffix.result}"
  tags   = { Name = "debug-bucket" }
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}
```

**Your task**:
1. Run `terraform init` -- it should succeed (or may need the random provider added)
2. Now change the AWS provider version constraint to `"~> 5.0"` (simulating a team update)
3. Run `terraform init` again
4. You should get an error about version constraints vs. the lock file
5. Diagnose the error and resolve it properly
6. After fixing, add a resource that uses an AWS provider v5 feature that doesn't exist in v4 (e.g., `aws_s3_bucket` with separate `aws_s3_bucket_versioning` resource -- the split happened between v3→v4)
7. Verify everything works with `terraform validate` and `terraform plan`

**Bonus challenge**: What would happen if one team member has the v4 lock file and another has v5? How should a team handle provider upgrades?

**Hint**: There's an `init` flag that resolves lock file conflicts...

---

### Debugging Methodology (Write This Down)

After fixing all four bugs, write down your personal Terraform debugging methodology. Include:

1. **Read the error message** -- What does Terraform tell you?
2. **Classify the error** -- Is it syntax? Reference? State? Provider? Permissions?
3. **Check the basics** -- `terraform validate`, `terraform fmt`, are credentials configured?
4. **Inspect state** -- `terraform state list`, `terraform state show`
5. **Enable debug logging** -- `TF_LOG=DEBUG terraform plan`
6. **Isolate** -- Use `-target` to focus on one resource
7. **Check the graph** -- `terraform graph` to see dependencies

> **Link back**: In Module 1 (broken server) you developed a Linux debugging methodology. In Module 2 (broken network) you added OSI layer analysis. Now you have a Terraform debugging methodology. Notice how each builds on the last -- Terraform errors about security groups might require Module 2 networking knowledge. State permission errors might require Module 5 IAM knowledge.

### Expected Outcomes

- All four bugs diagnosed and fixed
- Understanding of circular dependencies and how to break them
- Understanding of resource reference syntax and common mistakes
- Ability to recover from state corruption using `terraform import`
- Ability to resolve provider version conflicts
- A written debugging methodology for Terraform

### Checkpoint Questions

1. What causes a circular dependency in Terraform? How do you fix it without removing functionality?
2. What's the difference between `aws_subnet.public.id` and `aws_subnet.public.subnet_id`?
3. If Terraform state says a resource doesn't exist but it does in AWS, what command fixes this?
4. What does `terraform init -upgrade` do and when would you use it?
5. How would you diagnose a Terraform error you've never seen before? Walk through your methodology.
6. What is the most dangerous Terraform state operation? Why?

---

## Before You Move On

Before completing Module 6:
- [ ] You can diagnose and fix circular dependency errors
- [ ] You can identify and correct wrong resource references
- [ ] You can recover from state corruption using import
- [ ] You can resolve provider version conflicts
- [ ] You have a written Terraform debugging methodology
- [ ] You can approach a new Terraform error systematically without immediately searching the internet
