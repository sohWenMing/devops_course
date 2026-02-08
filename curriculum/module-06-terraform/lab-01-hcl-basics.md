# Lab 01: HCL Basics -- Your First Terraform Resources

> **Module**: 6 -- Terraform  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [IaC Philosophy](#), [HCL Basics](#), [Providers](#), and [Resources & Data Sources](#) sections of the Module 6 README. Terraform CLI installed (v1.5+). AWS CLI configured with credentials.

---

## Overview

In this lab, you'll write your first Terraform configurations, experience the init/plan/apply/destroy lifecycle, and learn the difference between resources and data sources. By the end, you'll have created and destroyed real AWS resources using nothing but `.tf` files.

---

## Exercise 1a: Minimal Terraform Config -- S3 Bucket

### Objectives

- Write a minimal Terraform configuration from scratch
- Understand the `terraform init` → `plan` → `apply` → `destroy` lifecycle
- Read and interpret `terraform plan` output
- Understand what `.terraform/` and `.terraform.lock.hcl` contain
- Observe how Terraform tracks resources in state

### What You'll Do

**Part 1: Write the Config**

1. Create a new directory for this exercise (e.g., `project/infra/lab-01a/`).

2. Create a Terraform configuration file that:
   - Declares the AWS provider with a region
   - Pins the provider version (use the `~>` constraint for the latest 5.x)
   - Creates a single S3 bucket with a unique name
   - Tags the bucket with `Project = "FlowForge"` and `ManagedBy = "Terraform"`
   - What is the minimum number of `.tf` files you need? How many would you use following conventions?

3. Before running anything, predict:
   - What will `terraform init` do?
   - What files/directories will it create?
   - What will `terraform plan` output show?

**Part 2: Init**

4. Run `terraform init` and observe the output carefully.
   - What provider was downloaded?
   - What version was selected?
   - Where was it downloaded to?
   - Look at the `.terraform/` directory -- what's inside?
   - Look at `.terraform.lock.hcl` -- what does it contain and why?

5. What would happen if you deleted the `.terraform/` directory and ran `terraform plan`? Try it and see.

**Part 3: Plan**

6. Run `terraform plan` and read every line of the output.
   - How many resources will be created?
   - What does the `+` symbol mean?
   - What does `(known after apply)` mean? Why can't Terraform know the bucket ARN before creating it?
   - Are there any values that Terraform does know in advance?

7. Save the plan to a file: `terraform plan -out=tfplan`. What advantage does saving a plan give you?

**Part 4: Apply**

8. Run `terraform apply` (either with the saved plan or interactively).
   - Did you get a confirmation prompt? When would you not get one?
   - What output did Terraform show after creating the bucket?
   - How long did it take?

9. Verify the bucket exists using the AWS CLI (not the Console):
   - Can you list your buckets and find the new one?
   - Can you describe the bucket's tags?

10. Look at the `terraform.tfstate` file that was created.
    - Find the S3 bucket in the state. What information does Terraform record?
    - Is the state file human-readable? Would you ever edit it manually?

**Part 5: Plan Again (Idempotency)**

11. Run `terraform plan` again without changing anything.
    - What does the output say?
    - This is **idempotency** -- the config matches reality, so nothing needs to change
    - Why is this property valuable?

12. Now change the bucket name in your config and run `terraform plan` again.
    - Does Terraform plan to update the existing bucket or destroy-and-recreate?
    - Why? (Hint: S3 bucket names are immutable -- look for `-/+` in the plan)
    - What's the difference between an update-in-place (`~`) and a destroy-and-recreate (`-/+`)?

**Part 6: Destroy**

13. Run `terraform destroy`.
    - Read the plan it shows -- it mirrors the create plan but with `-` instead of `+`
    - Confirm and watch it delete the bucket
    - Verify the bucket is gone using AWS CLI

14. What does `terraform.tfstate` contain after destroy? (It should still exist but be nearly empty.)

> **Link back**: In Module 5, you created an S3 bucket with `aws s3api create-bucket` and deleted it with `aws s3api delete-bucket` (after emptying it). Compare that experience to this: one file, one command to create, one command to destroy. Which approach would you rather use at 3am?

### Expected Outcomes

- A working `.tf` file that creates an S3 bucket
- Understanding of the init → plan → apply → destroy lifecycle
- Ability to read and predict plan output
- Understanding of state file purpose and contents

### Checkpoint Questions

1. What is the difference between `terraform plan` and `terraform apply`?
2. Why does Terraform need to `init` before `plan`?
3. What does `(known after apply)` mean in plan output?
4. What happens if you run `terraform apply` twice with no config changes?
5. Where does Terraform store the mapping between your config and real resources?
6. What happens if you change a bucket name -- is it an in-place update or a replacement? Why?

---

## Exercise 1b: VPC + Subnet + IGW Resources and Data Sources

### Objectives

- Create multiple related resources with dependencies
- Understand how Terraform builds a dependency graph from references
- Use data sources to look up existing AWS information
- Understand the difference between resources and data sources
- Practice reading plan output for multi-resource configurations

### What You'll Do

**Part 1: VPC Infrastructure Resources**

1. Create a new directory for this exercise (e.g., `project/infra/lab-01b/`).

2. Write Terraform configuration that creates:
   - A VPC with CIDR `10.0.0.0/16`, DNS support and DNS hostnames enabled
   - A public subnet in one AZ with CIDR `10.0.1.0/24`, with `map_public_ip_on_launch = true`
   - An internet gateway attached to the VPC
   - A route table with a default route (`0.0.0.0/0`) pointing to the internet gateway
   - A route table association linking the subnet to the route table
   - Proper tags on every resource with `Name` and `Project` tags

3. Before running `terraform plan`, draw the dependency graph on paper:
   - Which resource depends on which?
   - In what order will Terraform create them?
   - In what order will Terraform destroy them? (Hint: reverse)

4. Run `terraform plan` and check:
   - How many resources will be created?
   - Does the order match your prediction?
   - Find the references between resources in the plan output (e.g., `vpc_id = (known after apply)` on the subnet)

5. Apply and verify:
   - Can you see the VPC in the Console or with `aws ec2 describe-vpcs`?
   - Can you see the subnet, IGW, route table?
   - Does the route table have the correct default route?

> **Link back**: In Module 5 Lab 02, you created this exact infrastructure with a dozen `aws ec2` CLI commands. You had to copy VPC IDs, IGW IDs, and route table IDs between commands. Count how many times you had to manually pass an ID from one command to the next. Terraform does this automatically through references.

**Part 2: Data Sources**

6. Add a **data source** that looks up the latest Ubuntu 22.04 AMI:
   - The owner is Canonical (AWS account `099720109477`)
   - Filter by name pattern `ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*`
   - Use `most_recent = true`

7. Add an output that displays the AMI ID:
   ```
   output "latest_ubuntu_ami" {
     value = <reference to the data source>
   }
   ```

8. Run `terraform plan` and observe:
   - Does the data source appear as a `+` (create) or something different?
   - What does `# data.aws_ami.ubuntu will be read during apply` mean?
   - How is this different from a resource?

9. Apply and note the AMI ID that's output. Verify it with `aws ec2 describe-images`.

10. (Optional) Add an EC2 instance resource that uses the data source AMI:
    - Place it in the public subnet
    - Use instance type `t3.micro`
    - What additional resource might you need for SSH access? (Think security groups)
    - **Do NOT actually apply this** yet -- just write the config and plan to see what would happen. You'll create the full infrastructure in later labs.

**Part 3: Understanding the Graph**

11. Run `terraform graph` and pipe the output to examine the dependency graph:
    - Can you identify the edges (dependencies) between resources?
    - What would happen if you introduced a circular dependency? (e.g., resource A depends on B, and B depends on A)
    - (Optional) If you have Graphviz installed, render the graph as a PNG: `terraform graph | dot -Tpng > graph.png`

12. Destroy everything: `terraform destroy`
    - Watch the destroy order -- is it the reverse of creation?

### Expected Outcomes

- A Terraform config that creates a basic VPC with subnet, IGW, and routing
- A data source that looks up the latest Ubuntu AMI
- Understanding of resource dependency graphs
- Understanding of the difference between resources (create/manage) and data sources (read-only)

### Checkpoint Questions

1. What is the difference between a resource and a data source?
2. How does Terraform know to create the VPC before the subnet?
3. What happens if you reference `aws_vpc.main.id` in a subnet resource -- does Terraform understand this as a dependency?
4. When would you use a data source instead of a resource?
5. What does `terraform graph` show and why is it useful?
6. If you added 3 independent subnets (no dependencies between them), could Terraform create them in parallel? Why or why not?

---

## Before You Move On

Before proceeding to Lab 02:
- [ ] You can write a Terraform config from scratch without referencing Lab 01a
- [ ] You can predict what `terraform plan` will output before running it
- [ ] You can explain the init → plan → apply → destroy lifecycle
- [ ] You understand the difference between resources and data sources
- [ ] You can draw a dependency graph for a multi-resource config
- [ ] You can find a resource in the state file and explain what Terraform records about it
