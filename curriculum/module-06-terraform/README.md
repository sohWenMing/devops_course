# Module 6: Terraform -- Infrastructure as Code

> **Time estimate**: 2 weeks  
> **Prerequisites**: Complete Modules 1-5 (Linux, Networking, Go App, Docker, AWS), Terraform CLI installed (v1.5+), AWS CLI configured  
> **Link forward**: "CI/CD will run these Terraform configs automatically -- `terraform plan` on PRs, `terraform apply` on merge"  
> **Link back**: "In Module 5, you built every VPC, subnet, security group, EC2 instance, RDS database, S3 bucket, and ECR repository by hand. You typed dozens of `aws` CLI commands, clicked through Console pages, and spent hours debugging typos. Now you codify ALL of it so a single command recreates everything."

---

## Why This Module Matters for DevOps

In Module 5, you experienced the pain of manual infrastructure. You typed `aws ec2 create-vpc`, `aws ec2 create-subnet` (six times), `aws ec2 create-internet-gateway`, configured route tables, security groups, launched EC2 instances, created RDS databases, set up S3 buckets, and pushed images to ECR. If you needed to do it all again -- say for a staging environment -- you'd have to repeat every single step.

That's not just tedious. It's **dangerous**. Manual steps mean drift, inconsistency, and undocumented infrastructure. When the 3am page comes and you need to recreate your entire environment, "I think I remember the CLI commands" is not a recovery plan.

**Infrastructure as Code (IaC)** solves this. Your infrastructure becomes version-controlled text files. You can review changes in pull requests, roll back bad changes with `git revert`, and spin up identical environments in minutes. Terraform is the industry standard for multi-cloud IaC, and it's on virtually every DevOps job posting.

> **AWS SAA Alignment**: While the SAA exam doesn't test Terraform directly, it heavily tests IaC principles, CloudFormation concepts, and the ability to design infrastructure that's repeatable and automated. Understanding Terraform makes CloudFormation trivial, and the exam frequently asks about automation, drift detection, and infrastructure lifecycle management.

---

## Table of Contents

1. [IaC Philosophy: Declarative vs Imperative](#1-iac-philosophy-declarative-vs-imperative)
2. [HCL Basics](#2-hcl-basics)
3. [Providers & Provider Versioning](#3-providers--provider-versioning)
4. [Resources & Data Sources](#4-resources--data-sources)
5. [Variables](#5-variables)
6. [Outputs](#6-outputs)
7. [Locals](#7-locals)
8. [State](#8-state)
9. [Remote State with S3 + DynamoDB](#9-remote-state-with-s3--dynamodb)
10. [Modules](#10-modules)
11. [Workspaces](#11-workspaces)
12. [Terraform CLI Workflow](#12-terraform-cli-workflow)
13. [Debugging Terraform](#13-debugging-terraform)

---

## 1. IaC Philosophy: Declarative vs Imperative

### Two Ways to Describe Infrastructure

There are fundamentally two approaches to automating infrastructure:

**Imperative** (how): You write a sequence of commands that execute in order. "Create a VPC. Then create a subnet. Then attach an internet gateway." If something fails halfway, you have a partially-built environment. If you run it again, you might get duplicate resources or errors because resources already exist. This is what you did in Module 5 with AWS CLI commands.

**Declarative** (what): You describe the desired end state. "I want a VPC with this CIDR, three subnets, an internet gateway attached." The tool figures out how to get from the current state to the desired state. If you run it again and nothing changed, nothing happens. If you add a subnet to the config, only the new subnet gets created.

Terraform is **declarative**. You write configuration files describing what you want, and Terraform calculates the diff between what exists and what you want, then makes only the necessary changes.

> **Link back**: Think about this in terms of Module 5. You ran `aws ec2 create-vpc` -- that's imperative. If you run it again, you get a second VPC. With Terraform, you declare `resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }` and Terraform creates it once, then ignores it on subsequent runs unless you change the CIDR.

### Why Declarative Wins for Infrastructure

1. **Idempotency**: Running the same config twice produces the same result
2. **Drift detection**: Terraform can detect when reality doesn't match your config
3. **Change preview**: `terraform plan` shows exactly what will change before you apply
4. **Version control**: Infrastructure changes go through code review, just like application code
5. **Reproducibility**: Spin up identical environments for dev, staging, and production

> **Architecture Thinking**: When would you choose imperative over declarative? Imperative scripts are simpler for one-off tasks or complex orchestration with conditional logic. Declarative is better for ongoing infrastructure management. Terraform supports some imperative patterns with provisioners, but they're considered a last resort. What does that tell you about the design philosophy?

> **Link forward**: In Module 7, your CI/CD pipeline will run `terraform plan` on every pull request (so reviewers can see infrastructure changes) and `terraform apply` on merge to main. The declarative model makes this safe -- the plan output is a complete preview of what will change.

---

## 2. HCL Basics

### HashiCorp Configuration Language

Terraform uses **HCL** (HashiCorp Configuration Language), a declarative language designed specifically for infrastructure configuration. It's not a general-purpose programming language -- you can't write loops or conditionals like in Go or Python (though HCL has limited versions of both).

### Blocks

Everything in HCL is organized into **blocks**. A block has a type, zero or more labels, and a body:

```hcl
block_type "label1" "label2" {
  argument1 = "value1"
  argument2 = 42

  nested_block {
    argument3 = true
  }
}
```

The most common block types are:

- `terraform {}` -- Terraform settings (required providers, backend config)
- `provider "name" {}` -- Configure a provider (AWS, GCP, Azure)
- `resource "type" "name" {}` -- Define an infrastructure resource
- `data "type" "name" {}` -- Look up existing infrastructure
- `variable "name" {}` -- Input variable definition
- `output "name" {}` -- Output value definition
- `locals {}` -- Local computed values
- `module "name" {}` -- Use a reusable module

### Arguments and Expressions

**Arguments** assign values. They use `=` for assignment:

```hcl
resource "aws_instance" "api" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  tags = {
    Name    = "flowforge-api"
    Project = "FlowForge"
  }
}
```

**Expressions** can be:
- **Literals**: strings (`"hello"`), numbers (`42`), booleans (`true`)
- **References**: `aws_vpc.main.id` references another resource's attribute
- **Functions**: `cidrsubnet("10.0.0.0/16", 8, 1)` computes a subnet CIDR
- **Interpolation**: `"flowforge-${var.environment}"` embeds variables in strings
- **Conditional**: `var.environment == "prod" ? "t3.medium" : "t3.micro"`
- **For expressions**: `[for s in var.subnets : s.cidr_block]`

> **Link back**: Remember structured logging in Module 3 where you used JSON? HCL is similarly structured -- it's a way to represent complex configuration data in a readable format. But unlike JSON, HCL has references, functions, and expressions that make it more powerful for infrastructure definitions.

### File Organization

Terraform loads all `.tf` files in a directory as a single configuration. There's no import statement -- everything in the directory is merged. By convention:

- `main.tf` -- Primary resource definitions
- `variables.tf` -- Variable declarations
- `outputs.tf` -- Output declarations
- `providers.tf` -- Provider configuration
- `terraform.tf` -- Terraform settings (required_providers, backend)
- `locals.tf` -- Local value definitions

This is convention, not requirement. Terraform doesn't care what you name files -- it reads everything ending in `.tf`.

> **Architecture Thinking**: Why split configuration across multiple files instead of one big `main.tf`? Think about readability, code review (smaller diffs), and separation of concerns. When does a single file make sense? When does it become unmanageable? How does this relate to the single-responsibility principle you might know from application code?

---

## 3. Providers & Provider Versioning

### What Providers Do

Terraform itself doesn't know how to create AWS resources. **Providers** are plugins that translate Terraform resource definitions into API calls for specific platforms. The AWS provider knows how to call the EC2 API to create instances, the VPC API to create networks, and so on.

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "FlowForge"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}
```

### Version Constraints

Provider versioning prevents breaking changes from silently breaking your infrastructure:

- `= 5.31.0` -- Exact version (most restrictive)
- `~> 5.0` -- Any 5.x version (allows minor/patch updates)
- `~> 5.31` -- Any 5.31.x version (allows only patch updates)
- `>= 5.0, < 6.0` -- Range constraint

The `~>` operator (tilde-arrow, or "pessimistic constraint") is most common. It allows the rightmost number to increment. `~> 5.0` means `>= 5.0.0, < 6.0.0`.

> **Link back**: Remember Module 3 where you defined Go module dependencies in `go.mod` with version constraints? Same concept. And Module 4 where Dockerfile `FROM` pins a specific image tag? Provider versioning is infrastructure dependency management.

### The Lock File

After `terraform init`, a `.terraform.lock.hcl` file is created. This records the exact provider versions and checksums used. Commit this file -- it ensures everyone on the team uses the same provider version.

> **Architecture Thinking**: Why is provider version pinning critical for infrastructure? What happens if one team member uses AWS provider v5.30 and another uses v5.35 where a resource argument was deprecated? How does this relate to "works on my machine" problems you've seen with application dependencies?

---

## 4. Resources & Data Sources

### Resources

A **resource** tells Terraform to create and manage a piece of infrastructure:

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "flowforge-vpc"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "flowforge-public-a"
  }
}
```

Notice `aws_vpc.main.id` -- this is a **reference**. The subnet references the VPC's ID. Terraform uses these references to build a **dependency graph**: it knows the VPC must be created before the subnet. You don't specify order -- Terraform figures it out.

> **Link back**: In Module 5, you had to create the VPC first, then use its ID in the `create-subnet` command. Terraform does the same thing, but automatically. No more copying VPC IDs from one command to the next.

### Data Sources

A **data source** looks up existing infrastructure that Terraform doesn't manage:

```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "api" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
}
```

The key difference: **resources** are things Terraform creates, updates, and destroys. **Data sources** are things Terraform reads but doesn't manage. A data source for an AMI looks up the latest Ubuntu image but doesn't create or delete it.

> **Architecture Thinking**: When would you use a data source instead of a resource? Consider these scenarios: (1) You need to reference a VPC created by another team. (2) You need the latest AMI from AWS. (3) You need to read a secret from AWS Secrets Manager. In each case, you're consuming something, not creating it. What problems would arise if you tried to use a resource for something that already exists?

> **AWS SAA Tie-in**: Data sources map to the read-only API calls (Describe*, Get*, List*) you used in Module 5. Resources map to the mutating calls (Create*, Delete*, Modify*). Understanding this distinction helps with IAM policy design -- the Terraform IAM role needs both read and write permissions.

---

## 5. Variables

### Input Variables

Variables make your configuration reusable. Instead of hardcoding `"10.0.0.0/16"`, you define a variable:

```hcl
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "db_password" {
  description = "Password for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}
```

### Variable Types

HCL supports several types:

- **Primitive**: `string`, `number`, `bool`
- **Collection**: `list(type)`, `set(type)`, `map(type)`
- **Structural**: `object({...})`, `tuple([...])`

```hcl
variable "subnet_cidrs" {
  description = "CIDR blocks for subnets"
  type = object({
    public_a   = string
    public_b   = string
    private_a  = string
    private_b  = string
    database_a = string
    database_b = string
  })
  default = {
    public_a   = "10.0.1.0/24"
    public_b   = "10.0.2.0/24"
    private_a  = "10.0.3.0/24"
    private_b  = "10.0.4.0/24"
    database_a = "10.0.5.0/24"
    database_b = "10.0.6.0/24"
  }
}
```

### Setting Variable Values

Variables can be set (in precedence order, highest first):

1. `-var` flag on the CLI: `terraform apply -var="environment=prod"`
2. `-var-file` flag: `terraform apply -var-file="prod.tfvars"`
3. `*.auto.tfvars` files (automatically loaded)
4. `terraform.tfvars` (automatically loaded)
5. Environment variables: `TF_VAR_environment=prod`
6. Default value in the variable definition
7. Interactive prompt (if no default and no other source)

### Sensitive Variables

Marking a variable as `sensitive = true` does two things:
1. Terraform won't display its value in plan or apply output
2. It won't appear in `terraform output` unless you specifically ask

This does NOT encrypt the value in state. The state file still contains sensitive values in plaintext. This is a key reason why state file security matters (more on this in the State section).

> **Link back**: Remember the 12-Factor App config from Module 3? Environment variables for database credentials, API keys, service URLs. Terraform variables are the infrastructure equivalent -- you externalize everything that might differ between environments. And just like Module 3, sensitive values need special handling.

> **Architecture Thinking**: What should be a variable and what should be hardcoded? A good rule: anything that differs between environments (dev/staging/prod) should be a variable. Anything that's a fundamental architectural choice (like using VPC, or the number of AZs) can be hardcoded. But where's the line? Does the VPC CIDR need to be a variable if all environments use the same one?

---

## 6. Outputs

### Exporting Values

Outputs expose values from your Terraform configuration. They serve three purposes:

1. **Display information after apply**: Show the EC2 public IP so you can SSH to it
2. **Pass data between modules**: A VPC module outputs its VPC ID for the compute module
3. **Remote state data sharing**: Other Terraform configs can read your outputs via remote state

```hcl
output "api_instance_public_ip" {
  description = "Public IP of the API service EC2 instance"
  value       = aws_instance.api.public_ip
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "db_password" {
  description = "Database password"
  value       = var.db_password
  sensitive   = true
}
```

After `terraform apply`, you'll see:

```
Outputs:

api_instance_public_ip = "54.123.45.67"
rds_endpoint = "flowforge-db.abc123.us-east-1.rds.amazonaws.com:5432"
db_password = <sensitive>
```

> **Architecture Thinking**: What values should you output? Think about what a human operator needs (instance IPs for SSH), what other infrastructure needs (VPC IDs for dependent modules), and what application deployments need (database endpoints for connection strings). Over-outputting is better than under-outputting -- you can always ignore unused outputs.

---

## 7. Locals

### Computed Values

**Locals** are computed values within your configuration. They're like constants or intermediate variables:

```hcl
locals {
  project     = "flowforge"
  name_prefix = "${local.project}-${var.environment}"

  common_tags = {
    Project     = local.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  public_subnet_ids  = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  private_subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}
```

Use locals to:
- Avoid repeating complex expressions
- Build computed values from variables
- Create collections of related resource attributes

The difference between variables and locals: **variables** are inputs (set by the user), **locals** are internal computations (derived from other values).

---

## 8. State

### What State Is and Why It Exists

Terraform **state** is a JSON file (`terraform.tfstate`) that maps your configuration to real-world resources. When you write `resource "aws_vpc" "main" {}` and run apply, the state file records: "the resource `aws_vpc.main` corresponds to VPC `vpc-abc123` in us-east-1."

State exists because there's no reliable way to map configuration to reality without it. If you have `resource "aws_vpc" "main" {}` in your config, how does Terraform know which VPC it corresponds to? There might be dozens of VPCs in your account. The state file is the mapping.

### State Inspection

You can inspect state with:

```bash
# List all resources in state
terraform state list

# Show details of a specific resource
terraform state show aws_vpc.main

# Pull the full state as JSON
terraform state pull
```

### Drift Detection

**Drift** happens when someone changes infrastructure outside of Terraform -- through the Console, CLI, or another tool. Terraform detects drift by comparing state (what Terraform thinks exists) with reality (what actually exists):

```bash
terraform plan
# Shows: ~ aws_instance.api (1 attribute changed: instance_type "t3.micro" -> "t3.small")
```

This is one of Terraform's most powerful features. In Module 5, if someone changed a security group rule through the Console, you'd never know until something broke. Terraform tells you immediately.

> **Link back**: Remember the Python cleanup script from Module 5 that discovered resources by tag? Terraform state is a more reliable version of that -- it knows exactly what it created, not just what has the right tag.

### The State File is Sacred (and Sensitive)

The state file contains:
- Every resource ID and ARN
- Every attribute value (including sensitive ones like database passwords)
- Dependency relationships between resources

This means:
1. **Never edit state manually** -- use `terraform state` commands
2. **Never commit state to Git** -- it contains secrets
3. **Always back up state** -- losing it means Terraform forgets about your infrastructure
4. **Store state remotely** -- local files don't work for teams (covered next)

### terraform import

If you have existing infrastructure that wasn't created by Terraform, you can **import** it:

```bash
terraform import aws_vpc.main vpc-abc123
```

This tells Terraform: "the resource `aws_vpc.main` in my config corresponds to `vpc-abc123` in AWS." Terraform adds it to state. You still need to write the corresponding resource configuration -- import only updates state, not config.

> **Architecture Thinking**: What happens if you lose your state file? Terraform doesn't know about any of your resources. They still exist in AWS, but Terraform can't manage them. You'd need to either import every resource or start fresh. This is why remote state with backups is non-negotiable for any real project. What's the equivalent risk in application development? (Hint: losing your database.)

> **AWS SAA Tie-in**: Drift detection is a key concept in the SAA exam, especially around CloudFormation drift detection. Terraform's approach is the same -- compare desired state with actual state and show the difference. Understanding this concept transfers directly to CloudFormation questions.

---

## 9. Remote State with S3 + DynamoDB

### Why Remote State

Local state (`terraform.tfstate` on your laptop) has three problems:
1. **No collaboration**: Two people can't run Terraform simultaneously without overwriting each other's state
2. **No locking**: Two simultaneous `terraform apply` runs could corrupt state
3. **No backup**: If your laptop dies, so does your state

Remote state solves all three. For AWS, the standard backend is **S3 for storage** and **DynamoDB for locking**.

### S3 + DynamoDB Backend

```hcl
terraform {
  backend "s3" {
    bucket         = "flowforge-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "flowforge-terraform-locks"
    encrypt        = true
  }
}
```

**S3** stores the state file. With versioning enabled, you get automatic backups -- every state change is a new version. If something goes wrong, you can roll back to a previous state version.

**DynamoDB** provides **state locking**. When someone runs `terraform apply`, Terraform creates a lock in DynamoDB. If someone else tries to run apply simultaneously, they get an error: "Error acquiring the state lock." This prevents race conditions.

### The Chicken-and-Egg Problem

You need an S3 bucket and DynamoDB table before you can configure the backend. But you can't create them with Terraform if the backend doesn't exist yet. The standard approach:

1. Create the S3 bucket and DynamoDB table manually (or with a separate, simple Terraform config using local state)
2. Configure the backend in your main Terraform config
3. Run `terraform init` to migrate local state to remote

> **Link forward**: In Module 7, your CI/CD pipeline will use this remote state. Every GitHub Actions run will read state from S3 and acquire a lock from DynamoDB. This is how multiple pipeline runs don't clobber each other.

> **Architecture Thinking**: Why S3 + DynamoDB specifically? S3 provides durable, versioned object storage (remember Module 5 S3 concepts). DynamoDB provides a fast, consistent key-value store for locks. Could you use other AWS services? Sure -- but this combination is battle-tested and recommended by HashiCorp. What would happen if you skipped DynamoDB and just used S3? (Hint: what prevents two people from writing state at the same time?)

---

## 10. Modules

### Why Modules

As your Terraform config grows, a single directory with everything in it becomes unmanageable. **Modules** are reusable, self-contained units of Terraform configuration.

Think of modules like functions in Go: they take inputs (variables), do something (create resources), and return outputs. Each module has its own directory with its own `.tf` files.

### Module Structure

```
project/infra/
├── main.tf               # Root module - calls child modules
├── variables.tf
├── outputs.tf
├── terraform.tf
├── modules/
│   ├── vpc/
│   │   ├── main.tf       # VPC, subnets, IGW, NAT, routes
│   │   ├── variables.tf  # vpc_cidr, subnet_cidrs, environment
│   │   └── outputs.tf    # vpc_id, subnet_ids
│   ├── compute/
│   │   ├── main.tf       # EC2 instances, security groups
│   │   ├── variables.tf  # vpc_id, subnet_ids, instance_type
│   │   └── outputs.tf    # instance_ids, public_ips
│   ├── database/
│   │   ├── main.tf       # RDS, DB subnet group
│   │   ├── variables.tf  # vpc_id, subnet_ids, db_password
│   │   └── outputs.tf    # rds_endpoint
│   └── ecr/
│       ├── main.tf       # ECR repositories
│       ├── variables.tf  # repository_names
│       └── outputs.tf    # repository_urls
```

### Using Modules

In the root module, you call child modules:

```hcl
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr    = var.vpc_cidr
  subnet_cidrs = var.subnet_cidrs
  environment = var.environment
}

module "compute" {
  source = "./modules/compute"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnet_ids
  instance_type = var.instance_type
  environment   = var.environment
}
```

Notice: `module.vpc.vpc_id` references an output from the VPC module. This is how modules communicate -- through their input variables and output values. This creates a clear **contract** between modules.

### Module Best Practices

1. **Minimal interface**: Only expose variables and outputs that consumers need
2. **No hardcoded values**: Everything configurable should be a variable
3. **Sensible defaults**: Common values should have defaults
4. **Documentation**: Every variable and output should have a `description`
5. **Single responsibility**: A VPC module creates VPC resources, not EC2 instances
6. **Version control**: For shared modules, use Git tags and version constraints

> **Link back**: Remember how FlowForge's Go services are separate packages with clear interfaces? Modules are the same principle for infrastructure. The VPC module doesn't need to know what compute resources exist -- it just provides network infrastructure. The compute module doesn't need to know how the VPC was created -- it just needs a VPC ID and subnet IDs.

> **Architecture Thinking**: How do you decide what should be a module? The answer is usually at natural infrastructure boundaries: networking (VPC), compute (EC2/ECS), data (RDS/S3), and common resources (ECR, IAM). If you find yourself copying resource blocks between projects, that's a module waiting to be extracted. But be careful about over-modularizing -- too many tiny modules can be harder to understand than a flat config.

---

## 11. Workspaces

### What Workspaces Are

Terraform **workspaces** allow you to maintain multiple state files for the same configuration. The default workspace is called `default`.

```bash
terraform workspace new dev
terraform workspace new staging
terraform workspace list
terraform workspace select dev
```

Each workspace has its own state file. When you're in the `dev` workspace, `terraform apply` operates on dev's state. Switch to `staging` and the same config operates on staging's state.

### Using Workspaces with Variable Files

```hcl
# In your config
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

# Apply with different variable files per workspace
# terraform workspace select dev && terraform apply -var-file="dev.tfvars"
# terraform workspace select staging && terraform apply -var-file="staging.tfvars"
```

### When Workspaces Are Appropriate

Workspaces work well when:
- Environments share the same configuration structure
- Differences are limited to variable values (instance sizes, counts)
- A single team manages all environments

Workspaces are NOT appropriate when:
- Environments have fundamentally different architectures
- Different teams manage different environments
- You need different provider configurations per environment
- You want independent access controls per environment

For those cases, use **separate state files** with separate directories or separate backend keys.

> **Architecture Thinking**: Many teams start with workspaces and outgrow them. Why? When dev needs a feature that staging doesn't, you can't have different resource definitions per workspace without complex conditionals. Separate directories (with shared modules) give you full flexibility at the cost of some duplication. What would you choose for FlowForge and why?

---

## 12. Terraform CLI Workflow

### The Core Workflow

Every Terraform change follows this cycle:

```
Write → Init → Plan → Apply → (optional: Destroy)
```

### terraform init

Initializes a working directory. Downloads provider plugins, initializes the backend, and downloads modules. Run this once per directory, or after changing providers/backend/modules.

```bash
terraform init
terraform init -upgrade  # Upgrade providers to latest allowed version
```

### terraform plan

Computes the diff between your configuration and the current state. Shows exactly what will be created, modified, or destroyed:

```bash
terraform plan
terraform plan -var-file="prod.tfvars"
terraform plan -out=tfplan  # Save plan to a file for apply
```

**Read the plan output carefully.** It shows:
- `+` create -- a new resource will be created
- `~` update in-place -- an existing resource will be modified
- `-/+` destroy and recreate -- the resource must be replaced (e.g., you changed the AMI)
- `-` destroy -- a resource will be deleted

### terraform apply

Applies the changes. By default, shows the plan and asks for confirmation:

```bash
terraform apply
terraform apply -var-file="prod.tfvars"
terraform apply tfplan           # Apply a saved plan (no confirmation needed)
terraform apply -auto-approve    # Skip confirmation (use in CI/CD only)
```

### terraform destroy

Destroys all resources managed by the configuration:

```bash
terraform destroy
terraform destroy -target=aws_instance.api  # Destroy specific resource only
```

### terraform fmt

Formats your `.tf` files to the canonical HCL style:

```bash
terraform fmt           # Format current directory
terraform fmt -check    # Check if files are formatted (for CI)
terraform fmt -recursive # Format all subdirectories too
```

### terraform validate

Checks that the configuration is syntactically valid and internally consistent:

```bash
terraform validate
```

This catches things like missing required arguments, invalid variable types, and references to resources that don't exist. It does NOT check against the API -- it won't catch invalid AMI IDs or unsupported instance types.

> **Link back**: The init → plan → apply cycle is analogous to Module 4's Docker workflow: write Dockerfile → build → run. And `terraform plan` is like `docker build --dry-run` (if that existed) -- it shows you what would happen without doing it.

> **Link forward**: In Module 7, your CI/CD pipeline will run `terraform fmt -check` and `terraform validate` as quality gates, `terraform plan` on PRs (posting the output as a comment), and `terraform apply` on merge to main. The CLI workflow maps directly to pipeline stages.

---

## 13. Debugging Terraform

### Common Error Categories

1. **Syntax errors**: Invalid HCL. Caught by `terraform validate`
2. **Provider errors**: Wrong credentials, missing permissions, API limits. Returned by the AWS API during plan or apply
3. **State errors**: Corruption, lock conflicts, import mismatches
4. **Dependency errors**: Circular references, wrong interpolation, missing data source results
5. **Plan/apply mismatches**: Plan says one thing, apply does another (rare but possible with eventually consistent APIs)

### Debug Logging

Terraform supports verbose logging via environment variables:

```bash
export TF_LOG=DEBUG     # Maximum verbosity
export TF_LOG=INFO      # Moderate verbosity
export TF_LOG=WARN      # Warnings only
export TF_LOG=ERROR     # Errors only

export TF_LOG_PATH=terraform.log  # Write logs to file
```

### Debugging Strategy

1. **Read the error message** -- Terraform errors are usually specific and helpful
2. **Check the plan** -- Does the plan show what you expect?
3. **Check state** -- Is the resource in state? Does state match reality?
4. **Check credentials** -- Does the provider have the right permissions?
5. **Isolate the resource** -- Use `-target` to plan/apply a single resource
6. **Enable debug logging** -- When nothing else works, `TF_LOG=DEBUG` shows every API call

> **Link back**: In Module 5, when an EC2 instance couldn't reach RDS, you debugged by checking security groups, route tables, NACLs -- layer by layer. Terraform debugging follows the same systematic approach: syntax → config → state → API → provider.

### State Recovery

If state gets corrupted:
1. **Don't panic** -- S3 versioning (if configured) means you can restore a previous state version
2. Use `terraform state pull` to inspect the current state
3. Use `terraform state rm` to remove a resource from state (the resource still exists in AWS)
4. Use `terraform import` to re-import resources into state
5. **Never** edit the state JSON directly

> **Architecture Thinking**: What's your incident response plan for state corruption? In Module 10, you'll write incident response runbooks. Think about this now: how would you detect state corruption? How would you recover? What's the blast radius? (Hint: this is why modules with separate state files can limit blast radius.)

---

## What's Next

You'll work through six labs that take you from writing your first Terraform resource to managing the entire FlowForge infrastructure as code:

| Lab | Topic | Exercises |
|-----|-------|-----------|
| Lab 01 | HCL Basics | 1a: Minimal S3 config + init/plan/apply/destroy; 1b: VPC resources + data sources |
| Lab 02 | Variables & State | 2a: Parameterize everything; 2b: State inspection + drift detection + import |
| Lab 03 | Remote State & Modules | 3a: S3/DynamoDB backend; 3b: Refactor into modules |
| Lab 04 | Workspaces | 4a: Dev/staging workspaces with different variable files |
| Lab 05 | Full Recreation | 5: Destroy manual infra, recreate with terraform apply |
| Lab 06 | Debugging | 6: Four broken Terraform configs |

By the end, you'll be able to type `terraform apply` and watch your entire AWS infrastructure appear in minutes -- the same infrastructure that took hours to build manually in Module 5.

---

## Further Reading

- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://developer.hashicorp.com/terraform/cloud-docs/recommended-practices)
- [HCL Native Syntax Specification](https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md)
