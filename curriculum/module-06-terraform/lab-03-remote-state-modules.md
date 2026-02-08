# Lab 03: Remote State & Modules

> **Module**: 6 -- Terraform  
> **Time estimate**: 4-5 hours  
> **Prerequisites**: Lab 02 completed (you understand variables, outputs, and state). Read the [Remote State with S3 + DynamoDB](#) and [Modules](#) sections of the Module 6 README.

---

## Overview

In this lab, you'll solve two critical production problems: (1) local state files don't work for teams or CI/CD, and (2) a flat Terraform config becomes unmanageable as it grows. You'll set up remote state with S3 and DynamoDB locking, then refactor your configuration into reusable modules.

---

## Exercise 3a: Remote State with S3 + DynamoDB Locking

### Objectives

- Create the S3 bucket and DynamoDB table for state storage and locking
- Configure a Terraform backend to use remote state
- Migrate existing local state to remote state
- Understand state locking and why DynamoDB is needed
- Verify that state is stored remotely and versioned

### What You'll Do

**Part 1: Create the State Infrastructure**

This is the chicken-and-egg problem: you need AWS resources (S3 bucket, DynamoDB table) before you can store state remotely. So you'll create them first.

1. Create a separate directory for the state infrastructure (e.g., `project/infra/state-backend/`). This will use **local** state (it's the one thing that doesn't use remote state).

2. Write a Terraform config that creates:
   - An S3 bucket for state storage:
     - A unique bucket name (e.g., `flowforge-terraform-state-<your-id>`)
     - Versioning enabled (why is versioning important for state?)
     - Server-side encryption enabled (AES256)
     - Block all public access
     - Lifecycle rule to prevent accidental deletion (optional but recommended)
   - A DynamoDB table for state locking:
     - Table name: something like `flowforge-terraform-locks`
     - Partition key: `LockID` (type: String) -- this is what Terraform uses for locking
     - Billing mode: PAY_PER_REQUEST (to stay in free tier)

3. Apply this config. Note the bucket name and DynamoDB table name -- you'll need them for the backend configuration.

4. Verify:
   - Can you see the S3 bucket in the Console or CLI?
   - Can you see the DynamoDB table?
   - Is versioning enabled on the bucket?

> **Link back**: In Module 5 Lab 03, you created an S3 bucket with versioning. Here you're doing the same thing, but the bucket stores your Terraform state instead of application artifacts. And the DynamoDB table is a new concept -- it provides distributed locking that prevents concurrent state modifications.

**Part 2: Configure the Backend**

5. Go to your main infrastructure config (from Lab 02) and add a backend configuration:
   ```
   terraform {
     backend "s3" {
       bucket         = "<your-state-bucket-name>"
       key            = "flowforge/terraform.tfstate"
       region         = "us-east-1"
       dynamodb_table = "<your-lock-table-name>"
       encrypt        = true
     }
   }
   ```
   - What does the `key` argument specify?
   - What does `encrypt = true` do?

6. Run `terraform init`. Terraform will detect the new backend configuration:
   - It should ask: "Do you want to migrate all workspaces to 's3'?"
   - Confirm yes
   - What happened to the local `terraform.tfstate` file? (Check its contents)
   - Where is the state now?

**Part 3: Verify Remote State**

7. Verify state is in S3:
   - Use `aws s3 ls` to find your state file in the bucket
   - Download it and compare with what `terraform state pull` shows
   - Are they the same?

8. Verify locking works:
   - Run `terraform plan` and while it's running, check the DynamoDB table:
     - `aws dynamodb scan --table-name <your-lock-table-name>`
     - Can you see the lock entry?
   - After plan completes, check again -- the lock should be released

9. (Optional) Test lock contention:
   - Open two terminals
   - Run `terraform plan` in both simultaneously
   - One should succeed, the other should show a lock error
   - What does the lock error message say?
   - How would you manually release a stuck lock? (Research `terraform force-unlock`)

**Part 4: State Versioning**

10. Make a change to your infrastructure config (e.g., add a tag) and apply it.

11. Check S3 bucket versions:
    - `aws s3api list-object-versions --bucket <your-state-bucket-name>`
    - You should see multiple versions of the state file
    - Each version corresponds to a state change

12. Think about recovery:
    - If a `terraform apply` goes wrong, how would you restore a previous state version?
    - Why is S3 versioning more reliable than your own backups?

> **Link forward**: In Module 7, your CI/CD pipeline will use this remote backend. Every GitHub Actions run will read state from S3 and acquire a DynamoDB lock before modifying state. This is how concurrent pipeline runs don't corrupt state.

> **Architecture Thinking**: Why S3 + DynamoDB specifically? What properties does each service provide? (S3: durable storage, versioning, encryption. DynamoDB: consistent reads, conditional writes for locking.) Could you use a different combination? What trade-offs would that involve?

### Expected Outcomes

- An S3 bucket with versioning for state storage
- A DynamoDB table for state locking
- Local state migrated to remote state
- Understanding of why remote state matters for teams and CI/CD
- Understanding of state locking and how DynamoDB prevents concurrent modifications

### Checkpoint Questions

1. Why can't you use remote state for the state-backend resources themselves?
2. What happens if two people run `terraform apply` at the same time with remote state + DynamoDB locking?
3. What happens if two people run `terraform apply` at the same time with remote state but WITHOUT DynamoDB locking?
4. Why does the S3 bucket need versioning enabled?
5. What does `terraform force-unlock` do and when would you use it?
6. After migrating to remote state, what happens to the local `terraform.tfstate` file?

---

## Exercise 3b: Refactor into Modules

### Objectives

- Refactor a flat Terraform configuration into logical modules
- Define module input variables and output values
- Understand module composition and inter-module communication
- Follow module best practices (single responsibility, minimal interface, documentation)

### What You'll Do

**Part 1: Plan the Module Structure**

1. Before writing code, plan your module boundaries. You'll create four modules:
   - **vpc**: VPC, subnets, internet gateway, NAT gateway, route tables
   - **compute**: EC2 instances, security groups, key pairs
   - **database**: RDS instance, DB subnet group, database security group
   - **ecr**: ECR repositories, lifecycle policies

2. For each module, define:
   - What resources does it create?
   - What input variables does it need?
   - What output values does it expose?
   - What does it depend on? (e.g., compute needs VPC ID and subnet IDs from the vpc module)

3. Draw the dependency diagram:
   ```
   vpc → compute (needs vpc_id, subnet_ids)
   vpc → database (needs vpc_id, database_subnet_ids)
   ecr → (independent, no dependencies on vpc)
   ```

> **Link back**: Remember how FlowForge has separate services (api-service, worker-service) with clear interfaces? Modules follow the same principle. The VPC module doesn't care about compute details -- it just provides network infrastructure. This is separation of concerns applied to infrastructure.

**Part 2: Create the Module Directories**

4. Create the directory structure:
   ```
   project/infra/
   ├── main.tf          # Root module - calls child modules
   ├── variables.tf     # Root-level variables
   ├── outputs.tf       # Root-level outputs
   ├── terraform.tf     # Provider and backend config
   ├── dev.tfvars
   ├── staging.tfvars
   └── modules/
       ├── vpc/
       │   ├── main.tf
       │   ├── variables.tf
       │   └── outputs.tf
       ├── compute/
       │   ├── main.tf
       │   ├── variables.tf
       │   └── outputs.tf
       ├── database/
       │   ├── main.tf
       │   ├── variables.tf
       │   └── outputs.tf
       └── ecr/
           ├── main.tf
           ├── variables.tf
           └── outputs.tf
   ```

**Part 3: Build the VPC Module**

5. Start with the VPC module:
   - Move all VPC-related resources (VPC, subnets, IGW, NAT, route tables) into `modules/vpc/main.tf`
   - Define input variables in `modules/vpc/variables.tf` for everything the module needs:
     - VPC CIDR
     - Subnet CIDRs
     - Environment name
     - Availability zones
   - Define outputs in `modules/vpc/outputs.tf` for everything other modules need:
     - VPC ID
     - Public subnet IDs
     - Private subnet IDs
     - Database subnet IDs

6. In the root `main.tf`, call the VPC module:
   ```
   module "vpc" {
     source = "./modules/vpc"

     vpc_cidr     = var.vpc_cidr
     subnet_cidrs = var.subnet_cidrs
     environment  = var.environment
   }
   ```

7. Run `terraform init` (required after adding modules) and `terraform plan`:
   - Resources now have addresses like `module.vpc.aws_vpc.main`
   - Does the plan look correct?

**Part 4: Build the Remaining Modules**

8. Create the **compute** module:
   - EC2 instances and security groups
   - Input: VPC ID, subnet IDs, instance type, key pair name, AMI data
   - Output: instance IDs, public IPs

9. Create the **database** module:
   - RDS instance and DB subnet group
   - Input: VPC ID, database subnet IDs, database password, instance class
   - Output: RDS endpoint, RDS port, database name

10. Create the **ecr** module:
    - ECR repositories for api-service and worker-service
    - Input: repository names, image tag mutability, scan on push
    - Output: repository URLs, repository ARNs

11. Wire everything together in the root `main.tf`:
    ```
    module "compute" {
      source = "./modules/compute"

      vpc_id        = module.vpc.vpc_id
      subnet_ids    = module.vpc.public_subnet_ids
      instance_type = var.instance_type
      environment   = var.environment
    }
    ```
    - Notice: `module.vpc.vpc_id` -- this is how modules communicate
    - The VPC module outputs its VPC ID, and the compute module accepts it as input

**Part 5: Apply and Verify**

12. Run `terraform init` and `terraform plan`:
    - How many total resources will be created?
    - Are the module dependencies resolved correctly?
    - Do the resource addresses make sense (e.g., `module.vpc.aws_subnet.public_a`)?

13. Apply the configuration. Verify:
    - VPC and subnets exist with correct CIDRs
    - Security groups have the correct rules
    - ECR repositories exist
    - (If you included compute/database) EC2 and RDS are running

14. Check that outputs work:
    - Root-level outputs should expose values from child modules
    - `terraform output` should show VPC ID, subnet IDs, etc.

**Part 6: Test Module Independence**

15. Try changing a value in just one module (e.g., add a tag in the VPC module):
    - Does `terraform plan` show changes only in the VPC module?
    - This is the benefit of modules: changes are isolated

16. (Optional) Create a new module from scratch:
    - A `security-groups` module that separates SG definitions from compute
    - What inputs and outputs does it need?
    - How does it integrate with the existing modules?

17. Destroy when done: `terraform destroy`

> **Architecture Thinking**: You now have the same infrastructure as Module 5, but as code organized into logical modules. Think about what happens when a new team member joins: instead of reading 500 lines of flat config, they can understand the VPC module in isolation, then the compute module, then the database module. Each module is a bounded context. How does this map to microservices architecture?

### Expected Outcomes

- Four Terraform modules: vpc, compute, database, ecr
- Each module with own variables.tf and outputs.tf
- Root module that composes the child modules
- Inter-module communication via outputs and variables
- Understanding of module best practices and composition patterns

### Checkpoint Questions

1. What is the difference between a root module and a child module?
2. How do modules communicate with each other?
3. Why does `terraform init` need to be re-run after adding a module?
4. What happens if a module output is referenced by another module but the output doesn't exist?
5. When would you create a module vs keeping resources in the root module?
6. Could you create a new module from scratch (e.g., a `monitoring` module) without referencing the existing modules?

---

## Before You Move On

Before proceeding to Lab 04:
- [ ] State is stored remotely in S3 with DynamoDB locking
- [ ] You can explain why remote state matters for teams and CI/CD
- [ ] Infrastructure is organized into modules (vpc, compute, database, ecr)
- [ ] Each module has clear inputs (variables) and outputs
- [ ] You can add a new module from scratch
- [ ] You can explain how modules communicate through outputs/variables
