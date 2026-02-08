# Lab 04: Workspaces -- Multi-Environment Deployment

> **Module**: 6 -- Terraform  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Lab 03 completed (remote state with S3/DynamoDB, modularized config). Read the [Workspaces](#) section of the Module 6 README.

---

## Overview

In this lab, you'll use Terraform workspaces to manage multiple environments (dev and staging) with the same configuration but different variable values. You'll see how workspaces provide independent state while sharing the same codebase, and you'll explore the trade-offs of workspaces vs. separate state files.

---

## Exercise 4a: Dev and Staging Workspaces

### Objectives

- Create and manage Terraform workspaces
- Deploy the same configuration to multiple environments with different variable files
- Understand that each workspace has independent state
- Demonstrate environment isolation through workspaces
- Evaluate when workspaces are appropriate vs. alternative approaches

### What You'll Do

**Part 1: Create Workspaces**

1. Start from your modularized configuration (Lab 03). Make sure the backend is configured for remote state.

2. List current workspaces:
   ```
   terraform workspace list
   ```
   - What workspace are you in?
   - What does the `*` indicate?

3. Create a `dev` workspace:
   ```
   terraform workspace new dev
   ```
   - What happened to your state? Check `terraform state list`
   - You should see zero resources -- the new workspace starts with empty state
   - Where does Terraform store the dev workspace state in S3? (Check the bucket)

4. Create a `staging` workspace:
   ```
   terraform workspace new staging
   ```
   - Now you have three workspaces: `default`, `dev`, `staging`
   - Each has completely independent state

5. Examine the S3 bucket structure:
   - Look at how Terraform organizes state files per workspace
   - What's the path pattern? (Hint: `env:/`)

**Part 2: Environment-Specific Variable Files**

6. Create environment-specific variable files if you haven't already:

   `dev.tfvars`:
   - Smaller instance types (t3.micro)
   - Smaller RDS instance (db.t3.micro, no Multi-AZ)
   - Fewer resources where possible
   - Environment = "dev"

   `staging.tfvars`:
   - Medium instance types (t3.small)
   - Slightly larger RDS (db.t3.small or db.t3.micro with different storage)
   - Environment = "staging"

7. Use `terraform.workspace` in your config to make environment-aware decisions:
   ```
   locals {
     name_prefix = "flowforge-${terraform.workspace}"
   }
   ```
   - Where else in your config could `terraform.workspace` be useful?
   - What about resource naming? Tags?

**Part 3: Deploy to Dev**

8. Select the dev workspace:
   ```
   terraform workspace select dev
   ```

9. Plan and apply with the dev variable file:
   ```
   terraform plan -var-file="dev.tfvars"
   terraform apply -var-file="dev.tfvars"
   ```

10. Verify dev infrastructure exists:
    - Check that resources are named with "dev" in them
    - Check instance types are the smaller dev sizes
    - Note the outputs (VPC ID, instance IPs, etc.)

**Part 4: Deploy to Staging**

11. Switch to the staging workspace:
    ```
    terraform workspace select staging
    ```

12. Run `terraform state list`:
    - Should show zero resources (staging has its own empty state)
    - The dev infrastructure still exists -- it's in dev's state

13. Plan and apply with the staging variable file:
    ```
    terraform plan -var-file="staging.tfvars"
    terraform apply -var-file="staging.tfvars"
    ```

14. Verify staging infrastructure exists alongside dev:
    - Check that both sets of resources exist in AWS (dev and staging)
    - Verify they have different names, different instance sizes
    - Do they share a VPC or have separate VPCs? (Depends on your config)

**Part 5: Demonstrate Independent State**

15. Switch between workspaces and verify independence:
    ```
    terraform workspace select dev
    terraform state list    # Shows dev resources
    terraform output        # Shows dev outputs

    terraform workspace select staging
    terraform state list    # Shows staging resources
    terraform output        # Shows staging outputs
    ```

16. Make a change to only the dev environment:
    - Select the dev workspace
    - Change something in `dev.tfvars` (e.g., add a tag)
    - Plan and apply
    - Verify the change only affected dev, not staging

17. Show the current workspace:
    ```
    terraform workspace show
    ```

**Part 6: Evaluate Workspaces vs. Alternatives**

18. Think about the following questions and write down your answers:
    - What happens if dev needs a resource that staging doesn't?
    - Can you have different providers (e.g., different AWS regions) per workspace?
    - What if the dev team should have different Terraform permissions than the staging team?
    - How would you handle a production environment -- same workspace pattern or different approach?

19. Consider the alternative: separate directories with shared modules:
    ```
    environments/
    ├── dev/
    │   ├── main.tf       # Calls shared modules
    │   ├── terraform.tf   # Backend with key="dev/terraform.tfstate"
    │   └── dev.tfvars
    └── staging/
        ├── main.tf       # Calls shared modules
        ├── terraform.tf   # Backend with key="staging/terraform.tfstate"
        └── staging.tfvars
    ```
    - What are the pros and cons of this approach vs. workspaces?
    - When would you choose one over the other?

> **Architecture Thinking**: Workspaces are simple but limited. Many production teams use the "separate directory" pattern because it provides full isolation: different backends, different providers, different IAM permissions, and the ability to evolve environments independently. But it duplicates the root module code. What's the right balance for FlowForge? What would you recommend if the team grew from 1 person to 10?

**Part 7: Cleanup**

20. Destroy staging first:
    ```
    terraform workspace select staging
    terraform destroy -var-file="staging.tfvars"
    ```

21. Destroy dev:
    ```
    terraform workspace select dev
    terraform destroy -var-file="dev.tfvars"
    ```

22. (Optional) Delete the workspaces:
    ```
    terraform workspace select default
    terraform workspace delete dev
    terraform workspace delete staging
    ```

> **Link back**: In Module 5, creating a second environment meant repeating every single CLI command with different names and values. With Terraform workspaces, it's just `terraform workspace new staging && terraform apply -var-file="staging.tfvars"`. This is the power of IaC.

> **Link forward**: In Module 7, your CI/CD pipeline might use workspaces (or separate backend keys) to manage staging vs. production deployments. The staging deploy will be automatic; production will require manual approval.

### Expected Outcomes

- Dev and staging workspaces created and deployed
- Each workspace has independent state and infrastructure
- Different variable files produce different-sized infrastructure
- Understanding of when workspaces are appropriate vs. separate directories
- Both environments cleanly destroyed

### Checkpoint Questions

1. What is a Terraform workspace? How does it relate to state?
2. How does Terraform store different workspace states in S3?
3. Can you deploy to dev without affecting staging? How?
4. What does `terraform.workspace` give you in your config?
5. When would workspaces NOT be appropriate? Name at least 3 scenarios.
6. What's the alternative to workspaces for multi-environment management? What are the trade-offs?

---

## Before You Move On

Before proceeding to Lab 05:
- [ ] You can create, switch between, and delete workspaces
- [ ] You can deploy to multiple environments with different variable files
- [ ] You understand that each workspace has independent state
- [ ] You can articulate when workspaces are appropriate and when they aren't
- [ ] Both environments are destroyed and cleaned up
