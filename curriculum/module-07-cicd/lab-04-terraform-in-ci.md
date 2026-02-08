# Lab 04: Terraform in CI/CD -- Plan on PR, Apply on Merge

> **Module**: 7 -- CI/CD with GitHub Actions  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Read the [Terraform in CI/CD](#) section of the Module 7 README. Labs 01-03 completed. Module 6 completed (working Terraform configuration with remote state in S3 + DynamoDB locking). OIDC federation configured (from Lab 02).

---

## Overview

In this lab, you'll automate Terraform operations in your CI/CD pipeline. Pull requests will automatically generate a `terraform plan` and post it as a comment for reviewers to inspect. Merging to `main` will trigger `terraform apply` to make the infrastructure changes. This is the standard pattern used by most DevOps teams.

---

## Exercise 4: Terraform Plan on PR, Apply on Merge

### Objectives

- Add Terraform plan to the PR workflow (post plan output as a PR comment)
- Add Terraform apply to the merge-to-main workflow
- Ensure plan output is reviewable before apply
- Configure appropriate IAM permissions for Terraform in CI
- Discuss and implement safeguards for concurrent infrastructure changes

### What You'll Do

**Part 1: Plan the Integration**

1. Before writing any YAML, think about the workflow:
   - When should `terraform plan` run? (On PRs that change Terraform files)
   - When should `terraform apply` run? (On merge to main, after plan)
   - What credentials does Terraform need? (OIDC role from Lab 02, with broader permissions)
   - Where is the Terraform state? (S3 + DynamoDB from Module 6)
   - Should Terraform operations run in the same workflow as Go CI, or a separate workflow? Why?

2. Consider creating a separate workflow file (e.g., `terraform.yml`) specifically for infrastructure changes:
   - Trigger on PRs and pushes that modify files in the `project/infra/` directory (or wherever your Terraform configs live)
   - This keeps infrastructure pipeline separate from application pipeline
   - Use the `paths` filter on triggers

**Part 2: Plan on PR**

3. Create (or extend) a workflow that runs on `pull_request`:
   - Triggers when Terraform files are modified
   - Sets up Terraform CLI on the runner
   - Configures AWS credentials via OIDC (the role needs permissions to read state AND plan all resources)
   - Runs `terraform init` with the S3 backend
   - Runs `terraform plan` and captures the output

4. Post the plan output as a PR comment:
   - Use a GitHub Action (e.g., `actions/github-script`) to create a PR comment with the plan output
   - Format the plan nicely (e.g., wrap in a collapsible `<details>` block)
   - Include a summary at the top: "X to add, Y to change, Z to destroy"
   - Why is posting the plan as a comment valuable? Who reads it?

5. Handle plan failures:
   - What should happen if `terraform plan` fails? (e.g., syntax error, missing variable)
   - The workflow should fail and block the PR from merging
   - The error should be visible in the PR comment or CI status

6. Test it:
   - Create a feature branch
   - Make a Terraform change (e.g., add a tag to a resource, change an instance type)
   - Open a PR
   - Verify: does the plan appear as a PR comment?
   - Can you read the plan and understand what will change?

**Part 3: Apply on Merge**

7. Add a job that runs on `push` to `main` (triggered by merging a PR):
   - Only triggers when Terraform files were modified
   - Runs `terraform init`
   - Runs `terraform plan` (fresh plan, not the one from the PR)
   - Runs `terraform apply` with the plan from the previous step
   - Why run a fresh plan instead of using the PR's plan? (Hint: other merges may have happened)

8. Think about the apply step carefully:
   - Should apply run with auto-approve? Or should it use a saved plan file?
   - If you use a saved plan file (`terraform plan -out=tfplan` then `terraform apply tfplan`), what advantage does this provide?
   - What happens if the plan shows "0 to add, 0 to change, 0 to destroy"? (It's a no-op -- safe)

9. Add safeguards:
   - Use GitHub Actions `concurrency` to prevent multiple Terraform applies from running simultaneously:
     ```yaml
     concurrency:
       group: terraform-apply
       cancel-in-progress: false
     ```
   - Why `cancel-in-progress: false`? (You never want to cancel a running apply!)
   - What happens if two PRs merge in quick succession?

**Part 4: Safeguards & Discussion**

10. Think about these advanced scenarios and document your answers:

    a. **Concurrent merges**: Two PRs both modify Terraform configs. Both show clean plans on their PRs. They merge 5 minutes apart. What happens?
       - Does the DynamoDB lock from Module 6 help?
       - What if the second apply conflicts with the first?
       - How would you prevent this? (Require PRs to be up-to-date, serialize with concurrency groups)

    b. **Plan drift**: A PR shows "1 to add" in the plan comment. Someone manually changes infrastructure in the Console. The PR merges. What does the apply do?
       - Does it apply the original plan? Or does it generate a new plan?
       - What's the correct behavior? (Always fresh plan on apply)

    c. **Destructive changes**: A PR shows "1 to destroy" (e.g., removing an RDS instance). How do you ensure someone actually reads the plan before approving?
       - Could you require the `production` environment approval for Terraform applies?
       - Could you add a step that checks for destroy operations and requires extra confirmation?

    d. **Terraform state locking**: What happens if a CI apply is running and someone tries to run `terraform apply` from their laptop?
       - The DynamoDB lock should prevent this -- verify by checking the lock table

11. Test the full flow end-to-end:
    - Make a Terraform change on a feature branch
    - Open a PR -- verify plan comment appears
    - Review the plan, approve the PR, merge
    - Verify the apply runs and succeeds
    - Verify the infrastructure change was actually made in AWS

### Expected Outcomes

- PRs that modify Terraform files get an automatic plan comment
- Merging to `main` triggers `terraform apply` with a fresh plan
- Concurrent applies are prevented by concurrency groups
- DynamoDB state locking provides additional protection
- Terraform credentials use OIDC (no static keys)

### Checkpoint Questions

- Why run `terraform plan` on PRs and `terraform apply` only on merge to `main`? What would happen if you applied on every PR?
- Why generate a FRESH plan on merge instead of using the plan from the PR? Give a specific scenario where the PR plan would be wrong.
- Explain what happens if two PRs modifying infrastructure merge simultaneously. What safeguards exist?
- What Terraform operations should NEVER run in CI automatically? (Hint: `terraform destroy`, `terraform state rm`)
- How do you handle a situation where `terraform apply` fails mid-way through in CI? What's the recovery process?
- What additional permissions does the OIDC role need for Terraform vs just pushing to ECR? Why is this a concern?
