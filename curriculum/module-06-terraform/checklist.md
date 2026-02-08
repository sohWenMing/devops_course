# Module 6: Terraform -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 7.  
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

## IaC Philosophy & HCL Basics (Lab 01, Exercise 1a)

- [ ] I can explain declarative vs imperative infrastructure management
- [ ] I can predict what `terraform plan` will show when I change a resource
- [ ] I can write a minimal Terraform config (provider + resource) from scratch
- [ ] I understand the init → plan → apply → destroy lifecycle
- [ ] I can explain what `.terraform/`, `.terraform.lock.hcl`, and `terraform.tfstate` contain
- [ ] I can explain what `(known after apply)` means in plan output
- [ ] I understand idempotency -- running apply twice with no changes produces no changes

---

## Resources & Data Sources (Lab 01, Exercise 1b)

- [ ] I can explain the difference between a resource and a data source
- [ ] I can create multiple related resources with correct dependency references
- [ ] I can use a data source to look up the latest Ubuntu AMI
- [ ] I understand how Terraform builds a dependency graph from resource references
- [ ] I can predict the creation order of resources based on their dependencies
- [ ] I can read plan output for a multi-resource configuration and understand every line

---

## Variables, Outputs & Locals (Lab 02, Exercise 2a)

- [ ] Given a new Terraform config, I can identify every value that should be a variable
- [ ] I can write variable definitions with types, defaults, descriptions, and validation
- [ ] I can mark sensitive variables and explain what `sensitive = true` does (and doesn't do)
- [ ] I can define meaningful outputs for instance IPs, RDS endpoints, and VPC IDs
- [ ] I can use locals to avoid repeating expressions and build computed values
- [ ] I can create environment-specific `.tfvars` files for dev/staging/prod
- [ ] I can explain the variable precedence order (CLI > var-file > auto.tfvars > default)

---

## State Management (Lab 02, Exercise 2b)

- [ ] I can inspect state with `terraform state list`, `state show`, and `state pull`
- [ ] I can find a specific resource in state and explain what Terraform records about it
- [ ] I can detect drift by making a manual change and running `terraform plan`
- [ ] I can explain what happens when Terraform detects drift and you run `terraform apply`
- [ ] I can import an existing AWS resource into Terraform state with `terraform import`
- [ ] I understand the import workflow: write resource block → import → adjust config → plan shows no changes
- [ ] I can explain what happens if the state file is lost
- [ ] I can explain why the state file is sensitive (contains passwords, keys, etc.)
- [ ] I never edit the state file manually

---

## Remote State (Lab 03, Exercise 3a)

- [ ] I can create an S3 bucket + DynamoDB table for Terraform state storage and locking
- [ ] I can configure a Terraform backend for S3 remote state
- [ ] I can migrate local state to remote state with `terraform init`
- [ ] I can explain why remote state matters for teams (collaboration, locking, backup)
- [ ] I can explain what DynamoDB locking prevents (concurrent state modifications)
- [ ] I understand the chicken-and-egg problem with state backend resources
- [ ] I can demonstrate that state is stored in S3 and locks appear in DynamoDB during operations

---

## Modules (Lab 03, Exercise 3b)

- [ ] My infrastructure is organized into modules: vpc, compute, database, ecr
- [ ] Each module has its own variables.tf and outputs.tf with descriptions
- [ ] I can explain how modules communicate (outputs from one → variables of another)
- [ ] I can create a new Terraform module from scratch in under 15 minutes
- [ ] I can explain the difference between a root module and a child module
- [ ] I can explain why `terraform init` needs to re-run after adding modules
- [ ] I follow module best practices: single responsibility, minimal interface, sensible defaults

---

## Workspaces (Lab 04, Exercise 4a)

- [ ] I can create, switch between, list, and delete Terraform workspaces
- [ ] I can deploy to multiple environments (dev/staging) with different variable files
- [ ] I understand that each workspace has independent state
- [ ] I can use `terraform.workspace` in my config for environment-aware naming
- [ ] I can explain when workspaces are appropriate vs. separate state files
- [ ] I can articulate at least 3 scenarios where workspaces are NOT appropriate

---

## Full Infrastructure Recreation (Lab 05, Exercise 5)

- [ ] `terraform apply` creates the entire FlowForge AWS infrastructure from scratch
- [ ] `terraform destroy` cleanly removes everything
- [ ] I can go from zero infrastructure to fully running FlowForge in under 15 minutes
- [ ] The recreated infrastructure passes all Module 5 verification checks
- [ ] I can articulate the business value of Infrastructure as Code (disaster recovery, reproducibility)
- [ ] No manual steps are required -- everything is in `.tf` files

---

## Debugging (Lab 06, Exercise 6)

- [ ] I can diagnose and fix a circular dependency error
- [ ] I can identify and correct wrong resource references
- [ ] I can recover from state corruption using `terraform import`
- [ ] I can resolve provider version conflicts with `terraform init -upgrade`
- [ ] I have a written Terraform debugging methodology
- [ ] Given a `terraform plan` error, I can diagnose the root cause without searching the error message
- [ ] I can enable debug logging with `TF_LOG=DEBUG` when needed

---

## Integration & Architecture Thinking

- [ ] `terraform apply` creates the entire FlowForge AWS infrastructure from scratch
- [ ] `terraform destroy` cleanly removes everything
- [ ] Infrastructure is modularized (vpc, compute, database, ecr modules)
- [ ] State is stored remotely in S3 with DynamoDB locking
- [ ] I can write a new Terraform module from scratch in under 15 minutes
- [ ] I can explain the plan/apply lifecycle, state purpose, and drift detection without notes
- [ ] I can read a `terraform plan` output and predict exactly what will change
- [ ] I can explain how every Terraform concept maps to what I learned in previous modules:
  - Resources → Module 5 manual AWS CLI commands
  - Variables → Module 3 12-Factor configuration
  - State → Module 5 Python cleanup script's tag-based discovery
  - Modules → Module 3 Go service separation
  - Provider → Module 4 Docker registry (external dependency)
  - Remote state → Module 2 shared network state (everyone needs to agree on IPs/subnets)
  - Drift detection → Module 5 manual changes that were undocumented
  - Dependency graph → Module 4 Docker Compose depends_on

---

## Final Self-Assessment

> Answer honestly:
>
> **Could I write a complete Terraform configuration for a new AWS project -- with VPC, compute, database, and ECR -- organized into modules with remote state, from scratch on a blank editor with no notes and no internet access?**
>
> - If YES for everything: You're ready for Module 7. Congratulations!
> - If NO for anything: Go back and practice. The Terraform skills are foundational for everything that follows.

---

## Ready for Module 7?

If every box above is checked, proceed to [Module 7: CI/CD with GitHub Actions](../module-07-cicd/README.md).

> **What's coming**: In Module 7, you'll automate everything. `terraform plan` will run automatically on pull requests (posted as a comment for code review). `terraform apply` will run on merge to main. Docker images will be built, tested, scanned, and pushed to ECR automatically. The entire pipeline from `git push` to running infrastructure will be hands-free. The manual Terraform workflow you mastered in this module becomes a CI/CD pipeline stage.
