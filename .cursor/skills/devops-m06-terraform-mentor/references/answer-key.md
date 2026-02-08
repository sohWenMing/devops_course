# Module 06: Terraform -- Answer Key

> **INTERNAL REFERENCE ONLY**: This file is used by the Socratic mentor skill to verify student solutions and provide guidance. It must NEVER be revealed to the student.

---

## Lab 01: HCL Basics

### Exercise 1a: Minimal Terraform Config (S3 Bucket)

**Complete Configuration:**

`main.tf`:
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
  region = "us-east-1"
}

resource "aws_s3_bucket" "lab01" {
  bucket = "flowforge-lab01-<unique-suffix>"

  tags = {
    Project   = "FlowForge"
    ManagedBy = "Terraform"
  }
}
```

**Key Commands and Expected Output:**

```bash
# Initialize
$ terraform init
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.xx.x...
Terraform has been successfully initialized!

# Plan
$ terraform plan
Terraform will perform the following actions:

  # aws_s3_bucket.lab01 will be created
  + resource "aws_s3_bucket" "lab01" {
      + arn                         = (known after apply)
      + bucket                      = "flowforge-lab01-<suffix>"
      + id                          = (known after apply)
      + region                      = (known after apply)
      + tags                        = {
          + "ManagedBy" = "Terraform"
          + "Project"   = "FlowForge"
        }
      + tags_all                    = {
          + "ManagedBy" = "Terraform"
          + "Project"   = "FlowForge"
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.

# Apply
$ terraform apply
aws_s3_bucket.lab01: Creating...
aws_s3_bucket.lab01: Creation complete after 2s [id=flowforge-lab01-<suffix>]
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

# Verify
$ aws s3api list-buckets --query "Buckets[?contains(Name, 'flowforge-lab01')]"

# Second plan (idempotency)
$ terraform plan
No changes. Your infrastructure matches the configuration.

# Destroy
$ terraform destroy
aws_s3_bucket.lab01: Destroying... [id=flowforge-lab01-<suffix>]
aws_s3_bucket.lab01: Destruction complete after 1s
Destroy complete! Resources: 1 destroyed.
```

**What `.terraform/` contains:**
- `providers/registry.terraform.io/hashicorp/aws/<version>/<os_arch>/terraform-provider-aws_v<version>` -- the provider binary
- This is a local cache; Terraform downloads providers here

**What `.terraform.lock.hcl` contains:**
- Exact provider version and hash checksums
- Should be committed to Git to ensure consistent versions across the team

**What `terraform.tfstate` contains after apply:**
- JSON with `version`, `serial`, `lineage`, and a `resources` array
- The resource entry includes the bucket name, ARN, ID, region, tags
- After destroy, the `resources` array is empty but the file still exists

**Changing bucket name behavior:**
- S3 bucket names are immutable. Terraform shows `-/+` (destroy and recreate)
- The plan will show: `# aws_s3_bucket.lab01 must be replaced`

---

### Exercise 1b: VPC + Subnet + IGW + Data Sources

**Complete Configuration:**

`main.tf`:
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
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name    = "flowforge-vpc"
    Project = "FlowForge"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name    = "flowforge-public-a"
    Project = "FlowForge"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name    = "flowforge-igw"
    Project = "FlowForge"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name    = "flowforge-public-rt"
    Project = "FlowForge"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public_a.id
}

output "latest_ubuntu_ami" {
  description = "Latest Ubuntu 22.04 AMI ID"
  value       = data.aws_ami.ubuntu.id
}
```

**Dependency Graph:**
```
aws_vpc.main
├── aws_subnet.public_a (depends on VPC)
│   └── aws_route_table_association.public_a (depends on subnet + route table)
├── aws_internet_gateway.main (depends on VPC)
│   └── aws_route_table.public (depends on VPC + IGW)
│       └── aws_route_table_association.public_a
```

**Creation order**: VPC → (subnet, IGW in parallel) → route table → association
**Destroy order**: association → route table → (subnet, IGW in parallel) → VPC

**Plan output shows**: 5 resources to create + 1 data source to read
Data sources show as: `# data.aws_ami.ubuntu will be read during apply`

---

## Lab 02: Variables & State

### Exercise 2a: Parameterize Everything

**variables.tf:**
```hcl
variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project" {
  description = "Project name for tagging and naming"
  type        = string
  default     = "flowforge"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid CIDR block."
  }
}

variable "subnet_cidrs" {
  description = "CIDR blocks for all subnets"
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

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "db_password" {
  description = "Password for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 12
    error_message = "Database password must be at least 12 characters."
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}
```

**locals.tf:**
```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]
}
```

**outputs.tf:**
```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

output "database_subnet_ids" {
  description = "IDs of database subnets"
  value       = [aws_subnet.database_a.id, aws_subnet.database_b.id]
}
```

**dev.tfvars:**
```hcl
environment       = "dev"
instance_type     = "t3.micro"
db_instance_class = "db.t3.micro"
```

**staging.tfvars:**
```hcl
environment       = "staging"
instance_type     = "t3.small"
db_instance_class = "db.t3.small"
```

**Variable precedence (highest to lowest):**
1. `-var` flag: `terraform apply -var="environment=prod"`
2. `-var-file` flag: `terraform apply -var-file="prod.tfvars"`
3. `*.auto.tfvars` files (alphabetical)
4. `terraform.tfvars` (auto-loaded)
5. `TF_VAR_*` environment variables
6. Default in variable definition
7. Interactive prompt

**Passing sensitive variables:**
- Environment variable: `export TF_VAR_db_password="securepassword123"` (appears in shell history unless using `read -s`)
- Via file: `echo 'db_password = "securepassword123"' > secrets.tfvars` then `terraform apply -var-file=secrets.tfvars` (file must be in .gitignore)
- Via CI/CD secret: GitHub Actions secret → env var → `TF_VAR_db_password`

---

### Exercise 2b: State Inspection, Drift Detection & Import

**State Inspection Commands:**

```bash
# List all resources
$ terraform state list
aws_vpc.main
aws_subnet.public_a
aws_subnet.public_b
aws_internet_gateway.main
aws_route_table.public
aws_route_table_association.public_a

# Show specific resource
$ terraform state show aws_vpc.main
# aws_vpc.main:
resource "aws_vpc" "main" {
    arn                              = "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-abc123"
    cidr_block                       = "10.0.0.0/16"
    enable_dns_hostnames             = true
    enable_dns_support               = true
    id                               = "vpc-abc123"
    instance_tenancy                 = "default"
    main_route_table_id              = "rtb-xyz789"
    owner_id                         = "123456789012"
    tags                             = {
        "Environment" = "dev"
        "Name"        = "flowforge-dev-vpc"
        "Project"     = "flowforge"
    }
}

# Pull full state as JSON
$ terraform state pull | python3 -m json.tool > state.json
```

**Drift Detection:**

```bash
# After manually adding a tag "Environment = manually-changed" via Console:
$ terraform plan

Terraform will perform the following actions:

  # aws_vpc.main will be updated in-place
  ~ resource "aws_vpc" "main" {
        id                               = "vpc-abc123"
      ~ tags                             = {
          ~ "Environment" = "manually-changed" -> "dev"
            # (2 unchanged elements hidden)
        }
      ~ tags_all                         = {
          ~ "Environment" = "manually-changed" -> "dev"
            # (2 unchanged elements hidden)
        }
    }

Plan: 0 to add, 1 to change, 0 to destroy.

# Apply to revert the manual change
$ terraform apply
# Confirms: 0 to add, 1 to change, 0 to destroy
```

**Import Workflow:**

```bash
# 1. Create bucket manually
$ aws s3api create-bucket --bucket flowforge-import-test-abc123 --region us-east-1

# 2. Tag it
$ aws s3api put-bucket-tagging --bucket flowforge-import-test-abc123 \
  --tagging 'TagSet=[{Key=Project,Value=FlowForge}]'

# 3. Write the resource block in Terraform config:
# resource "aws_s3_bucket" "imported" {
#   bucket = "flowforge-import-test-abc123"
#   tags = {
#     Project = "FlowForge"
#   }
# }

# 4. Plan shows: 1 to add (wants to CREATE, will fail because name taken)

# 5. Import
$ terraform import aws_s3_bucket.imported flowforge-import-test-abc123
aws_s3_bucket.imported: Importing from ID "flowforge-import-test-abc123"...
aws_s3_bucket.imported: Import prepared!
aws_s3_bucket.imported: Refreshing state...
Import successful!

# 6. Plan again - may show minor diffs, adjust config to match
$ terraform plan
# Adjust config until: No changes. Your infrastructure matches the configuration.
```

---

## Lab 03: Remote State & Modules

### Exercise 3a: S3 + DynamoDB Backend

**State Backend Configuration:**

`state-backend/main.tf`:
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

resource "aws_s3_bucket" "terraform_state" {
  bucket = "flowforge-terraform-state-<unique-id>"

  tags = {
    Name      = "Terraform State"
    Project   = "FlowForge"
    ManagedBy = "Terraform"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "flowforge-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "Terraform Lock Table"
    Project   = "FlowForge"
    ManagedBy = "Terraform"
  }
}

output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}

output "lock_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}
```

**Backend Configuration in Main Project:**

```hcl
terraform {
  backend "s3" {
    bucket         = "flowforge-terraform-state-<unique-id>"
    key            = "flowforge/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "flowforge-terraform-locks"
    encrypt        = true
  }
}
```

**Migration:**
```bash
$ terraform init
Initializing the backend...
Do you want to migrate all workspaces to "s3"?
  Enter a value: yes

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
```

**After migration**, the local `terraform.tfstate` file becomes nearly empty (just the backend info). All state is now in S3.

**Verify:**
```bash
# Check S3
$ aws s3 ls s3://flowforge-terraform-state-<unique-id>/flowforge/
# Should show terraform.tfstate

# Check lock during plan
$ aws dynamodb scan --table-name flowforge-terraform-locks
# During plan/apply: shows a lock entry with LockID
# After completion: table is empty (lock released)
```

---

### Exercise 3b: Refactor into Modules

**Module Structure:**

```
project/infra/
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tf
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

**Root main.tf:**
```hcl
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr           = var.vpc_cidr
  subnet_cidrs       = var.subnet_cidrs
  environment        = var.environment
  project            = var.project
  availability_zones = local.availability_zones
}

module "compute" {
  source = "./modules/compute"

  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  instance_type     = var.instance_type
  environment       = var.environment
  project           = var.project
}

module "database" {
  source = "./modules/database"

  vpc_id              = module.vpc.vpc_id
  database_subnet_ids = module.vpc.database_subnet_ids
  db_password         = var.db_password
  db_instance_class   = var.db_instance_class
  allowed_security_groups = [module.compute.api_security_group_id]
  environment         = var.environment
  project             = var.project
}

module "ecr" {
  source = "./modules/ecr"

  repository_names = ["flowforge-api", "flowforge-worker"]
  environment      = var.environment
  project          = var.project
}
```

**modules/vpc/variables.tf:**
```hcl
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

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
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}
```

**modules/vpc/outputs.tf:**
```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

output "database_subnet_ids" {
  description = "IDs of database subnets"
  value       = [aws_subnet.database_a.id, aws_subnet.database_b.id]
}
```

**modules/vpc/main.tf (key resources):**
```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.subnet_cidrs.public_a
  availability_zone       = var.availability_zones[0]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-a"
    Tier = "public"
  })
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.subnet_cidrs.public_b
  availability_zone       = var.availability_zones[1]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-b"
    Tier = "public"
  })
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidrs.private_a
  availability_zone = var.availability_zones[0]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-a"
    Tier = "private"
  })
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidrs.private_b
  availability_zone = var.availability_zones[1]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-b"
    Tier = "private"
  })
}

resource "aws_subnet" "database_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidrs.database_a
  availability_zone = var.availability_zones[0]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database-a"
    Tier = "database"
  })
}

resource "aws_subnet" "database_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidrs.database_b
  availability_zone = var.availability_zones[1]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database-b"
    Tier = "database"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw"
  })
}

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-eip"
  })
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-gw"
  })

  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt"
  })
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-rt"
  })
}

resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database-rt"
  })
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_b" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "database_a" {
  subnet_id      = aws_subnet.database_a.id
  route_table_id = aws_route_table.database.id
}

resource "aws_route_table_association" "database_b" {
  subnet_id      = aws_subnet.database_b.id
  route_table_id = aws_route_table.database.id
}
```

**modules/compute/main.tf (key resources):**
```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "api" {
  name        = "${local.name_prefix}-api-sg"
  description = "Security group for FlowForge API service"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from admin"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-api-sg"
  })
}

resource "aws_instance" "api" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.api.id]
  iam_instance_profile   = var.instance_profile_name

  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu
  EOF

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-api"
  })
}
```

**modules/database/main.tf (key resources):**
```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

resource "aws_security_group" "database" {
  name        = "${local.name_prefix}-db-sg"
  description = "Security group for FlowForge RDS"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from allowed security groups"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_groups
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-db-sg"
  })
}

resource "aws_db_instance" "postgres" {
  identifier     = "${local.name_prefix}-postgres"
  engine         = "postgres"
  engine_version = "15"
  instance_class = var.db_instance_class

  allocated_storage = 20
  storage_type      = "gp3"

  db_name  = "flowforge"
  username = "flowforge"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  multi_az            = var.environment == "prod" ? true : false
  publicly_accessible = false
  skip_final_snapshot = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-postgres"
  })
}
```

**modules/ecr/main.tf:**
```hcl
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecr_repository" "repos" {
  for_each = toset(var.repository_names)

  name                 = each.value
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(local.common_tags, {
    Name = each.value
  })
}

resource "aws_ecr_lifecycle_policy" "repos" {
  for_each   = aws_ecr_repository.repos
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
```

---

## Lab 04: Workspaces

### Exercise 4a: Dev and Staging Workspaces

**Commands and Expected Output:**

```bash
# List workspaces
$ terraform workspace list
* default

# Create dev workspace
$ terraform workspace new dev
Created and switched to workspace "dev"!

# Create staging workspace
$ terraform workspace new staging
Created and switched to workspace "staging"!

# List all workspaces
$ terraform workspace list
  default
  dev
* staging

# Check state in new workspace (empty)
$ terraform state list
# (no output -- new workspace has empty state)

# Deploy to dev
$ terraform workspace select dev
Switched to workspace "dev".

$ terraform apply -var-file="dev.tfvars"
# Creates all resources with "dev" naming

# Deploy to staging
$ terraform workspace select staging
Switched to workspace "staging".

$ terraform apply -var-file="staging.tfvars"
# Creates separate set of resources with "staging" naming

# Show workspace in config
# terraform.workspace returns "dev" or "staging"
```

**S3 state paths per workspace:**
- default: `flowforge/terraform.tfstate`
- dev: `env:/dev/flowforge/terraform.tfstate`
- staging: `env:/staging/flowforge/terraform.tfstate`

**When workspaces are NOT appropriate:**
1. Different teams manage different environments (need separate access controls)
2. Environments have fundamentally different architectures (dev has no NAT, prod has Multi-AZ RDS)
3. Need different provider configurations (different regions per environment)
4. Want independent backend access controls per environment
5. Environments should be able to evolve independently (add resources to staging that don't exist in dev)

---

## Lab 05: Full Recreation

### Exercise 5: Destroy and Recreate

**Expected resource count**: ~25-35 resources depending on configuration (VPC, 6 subnets, IGW, NAT, 3 route tables, 6 route table associations, 3+ security groups, EC2 instance, RDS instance, DB subnet group, 2 ECR repos, S3 bucket, IAM role, instance profile)

**Expected terraform apply time**: 8-15 minutes (RDS is the slowest: 5-10 min)

**Verification commands:**
```bash
# After apply, use outputs
$ terraform output
api_instance_public_ip = "54.x.x.x"
rds_endpoint = "flowforge-dev-postgres.xxx.us-east-1.rds.amazonaws.com:5432"

# SSH into EC2
$ ssh -i ~/.ssh/flowforge-key.pem ubuntu@$(terraform output -raw api_instance_public_ip)

# On EC2, verify Docker
$ docker --version
$ aws sts get-caller-identity  # Should show instance profile role

# Test RDS connectivity from EC2
$ psql -h $(terraform output -raw rds_endpoint | cut -d: -f1) -U flowforge -d flowforge

# Test ECR
$ aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
```

---

## Lab 06: Debugging

### Bug 1: Circular Dependency

**Error message:**
```
Error: Cycle: aws_security_group.api, aws_security_group.worker
```

**Root cause**: `aws_security_group.api` has an inline ingress rule referencing `aws_security_group.worker.id`, and `aws_security_group.worker` has an inline ingress rule referencing `aws_security_group.api.id`. Neither can be created first because each needs the other's ID.

**Fix**: Use separate `aws_vpc_security_group_ingress_rule` (or the older `aws_security_group_rule`) resources instead of inline rules:

```hcl
resource "aws_security_group" "api" {
  name        = "api-sg"
  description = "Security group for API service"
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "api-sg" }
}

resource "aws_security_group" "worker" {
  name        = "worker-sg"
  description = "Security group for Worker service"
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "worker-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "api_from_worker" {
  security_group_id            = aws_security_group.api.id
  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.worker.id
}

resource "aws_vpc_security_group_ingress_rule" "worker_from_api" {
  security_group_id            = aws_security_group.worker.id
  from_port                    = 9090
  to_port                      = 9090
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.api.id
}
```

**Why this works**: The SGs are created first (no dependency on each other), then the rules are added as separate resources that reference the existing SGs. No cycle.

---

### Bug 2: Wrong Resource Reference

**Error messages:**
```
Error: Unsupported attribute
  on main.tf line XX:
  aws_subnet.public.subnet_id is not an attribute of aws_subnet

Error: Reference to undeclared resource
  on main.tf line XX:
  A managed resource "aws_subnet" "private_subnet" has not been declared
```

**Two bugs:**

1. `aws_subnet.public.subnet_id` should be `aws_subnet.public.id` -- the `aws_subnet` resource exports `id`, not `subnet_id`

2. `aws_subnet.private_subnet.id` should be `aws_subnet.private.id` -- the resource is named `"private"` not `"private_subnet"`

**Fixed lines:**
```hcl
resource "aws_instance" "api" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public.id          # Fixed: .id not .subnet_id

  tags = { Name = "debug-api-instance" }
}

resource "aws_instance" "worker" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.private.id          # Fixed: private not private_subnet

  tags = { Name = "debug-worker-instance" }
}
```

---

### Bug 3: State Corruption Simulation

**After `terraform state rm aws_s3_bucket.main`:**
- State no longer tracks the bucket
- `terraform plan` shows: `+ aws_s3_bucket.main will be created`
- Applying would fail: `BucketAlreadyOwnedByYou` or `BucketAlreadyExists`

**Fix -- import the bucket back:**
```bash
$ terraform import aws_s3_bucket.main <bucket-name>
aws_s3_bucket.main: Importing from ID "<bucket-name>"...
aws_s3_bucket.main: Import prepared!
Import successful!

$ terraform plan
No changes. Your infrastructure matches the configuration.
```

---

### Bug 4: Provider Version Conflict

**Error after changing `= 4.67.0` to `~> 5.0`:**
```
Error: Failed to query available provider packages

Could not retrieve the list of available versions for provider
hashicorp/aws: locked provider registry.terraform.io/hashicorp/aws
4.67.0 does not match configured version constraint ~> 5.0;
must use terraform init -upgrade to allow selection of new versions
```

**Fix:**
```bash
# Upgrade the provider
$ terraform init -upgrade
Upgrading provider hashicorp/aws from 4.67.0 to 5.x.x...

# Also need to add the random provider if not declared
# Add to required_providers:
#   random = {
#     source  = "hashicorp/random"
#     version = "~> 3.0"
#   }

$ terraform init -upgrade
# Both providers now at correct versions

$ terraform validate
Success! The configuration is valid.
```

**Note on v4 → v5 changes**: The AWS provider v4 deprecated several combined resources (e.g., `aws_s3_bucket` had inline `versioning {}`, `server_side_encryption_configuration {}` blocks). In v5, these must be separate resources (`aws_s3_bucket_versioning`, `aws_s3_bucket_server_side_encryption_configuration`). If upgrading an existing config, you'd need to refactor these.

**Team handling of provider upgrades:**
1. One person updates the version constraint in `terraform.tf`
2. Runs `terraform init -upgrade` to update `.terraform.lock.hcl`
3. Commits both files together in a PR
4. All team members run `terraform init` to get the new version
5. The lock file ensures everyone uses the exact same version
