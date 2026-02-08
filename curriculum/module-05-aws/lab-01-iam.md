# Lab 01: IAM -- Users, Groups, Policies & Roles

> **Module**: 5 -- AWS Fundamentals  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [IAM Fundamentals](#) section of the Module 5 README. Lab 00 completed (AWS account with MFA and billing alarms).

---

## Overview

In this lab, you'll build the identity and access management foundation for FlowForge on AWS. You'll create an IAM user for deployment (so you stop using root), define least-privilege policies, and create IAM roles for your EC2 instances. By the end, every AWS action in this course will use properly scoped credentials, not root.

---

## Exercise 1a: IAM Users, Groups & Policies

### Objectives

- Create an IAM admin user and stop using root for everything
- Create an IAM deployment user with a custom least-privilege policy
- Organize users into groups with attached policies
- Use the IAM Policy Simulator to verify permissions
- Understand how policy evaluation works (explicit deny beats allow)

### What You'll Do

**Part 1: Admin User Setup**

1. Create an IAM user named `flowforge-admin` with both Console access and programmatic access (access keys).
   - What's the difference between Console access and programmatic access?
   - Why might you want both?

2. Create an IAM group called `administrators` and attach the AWS-managed `AdministratorAccess` policy.

3. Add `flowforge-admin` to the `administrators` group.

4. Sign out of root and sign in as `flowforge-admin`. From this point forward, **never use root again** unless you need to change billing settings or close the account.

5. Configure the AWS CLI with the `flowforge-admin` access keys:
   - Run `aws configure` and enter your access key ID, secret access key, default region, and output format
   - Verify it works: `aws sts get-caller-identity`
   - What information does `get-caller-identity` return? Why is this command useful for debugging?

> **Link back**: In Module 1, you created separate users for FlowForge services instead of running everything as root. Same principle here: root is for emergencies only.

**Part 2: Deployment User with Least Privilege**

6. Create an IAM user named `flowforge-deploy` with **programmatic access only** (no Console access).
   - Why doesn't a deployment user need Console access?

7. Write a custom IAM policy called `FlowForgeDeployPolicy` that grants **only** the permissions needed for the FlowForge deployment. Think about what actions the deployment process will need:
   - EC2: describe instances, run instances, terminate instances, manage security groups
   - VPC: describe VPCs, subnets, route tables, internet gateways
   - RDS: describe/create/delete DB instances
   - S3: list/read/write to a specific bucket (not all buckets)
   - ECR: get authorization token, push/pull images
   - IAM: pass roles to EC2 (but NOT create/modify IAM resources)

8. Think carefully about the `Resource` field in your policy:
   - Which actions can be scoped to specific resources (ARNs)?
   - Which actions require `"Resource": "*"` (and why)?
   - Is `"Action": "ec2:*"` appropriate? What about `"Action": "s3:*"`?

9. Create an IAM group called `deployers` and attach your custom policy.

10. Add `flowforge-deploy` to the `deployers` group.

**Part 3: Policy Simulator**

11. Open the IAM Policy Simulator (in the AWS Console under IAM → Policy Simulator).

12. Select the `flowforge-deploy` user and test the following:
    - Can this user launch an EC2 instance? (Should be: Allowed)
    - Can this user create a new IAM user? (Should be: Denied)
    - Can this user delete an S3 bucket that's NOT the FlowForge bucket? (Should be: Denied -- if you scoped the Resource correctly)
    - Can this user read from the FlowForge S3 bucket? (Should be: Allowed)

13. If any of the results surprise you, adjust your policy and test again. The goal is a policy where the deployment user can do everything needed for FlowForge and nothing else.

**Part 4: Understanding Policy Evaluation**

14. Create a second policy called `DenyDeleteProduction` with an explicit deny:
    ```json
    {
      "Effect": "Deny",
      "Action": [
        "ec2:TerminateInstances",
        "rds:DeleteDBInstance"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Environment": "production"
        }
      }
    }
    ```
    Attach this to the `deployers` group alongside the deploy policy.

15. Use the Policy Simulator: can `flowforge-deploy` terminate an instance tagged `Environment: production`? What about one tagged `Environment: dev`? This demonstrates that explicit Deny always wins, even if another policy says Allow.

### Expected Outcome

- You have an admin user (`flowforge-admin`) and never use root again
- You have a deployment user (`flowforge-deploy`) with a custom least-privilege policy
- The deployment user can perform FlowForge operations but cannot create IAM resources or access other S3 buckets
- Policy Simulator confirms the permissions are exactly what you intended
- You understand that explicit Deny overrides Allow

### Checkpoint Questions

1. Given a JSON IAM policy, can you explain exactly what it allows and denies?
2. Write a policy from scratch that allows EC2 describe actions and S3 read-only access for one specific bucket. No looking at your previous policy.
3. What happens when two policies conflict (one says Allow, one says Deny)?
4. Why should you use groups instead of attaching policies directly to users?

---

## Exercise 1b: IAM Roles & Instance Profiles

### Objectives

- Create an IAM role for EC2 instances
- Understand the difference between users (people) and roles (services)
- Create an instance profile and understand how EC2 assumes a role
- Configure the role with S3 read and CloudWatch write permissions
- Explain why roles are preferred over access keys on EC2

### What You'll Do

**Part 1: Understanding Roles**

1. Before creating anything, answer this: why can't you just put the `flowforge-deploy` user's access keys on the EC2 instance? What are the security risks?
   - Think about what happens if the instance is compromised
   - Think about credential rotation
   - Think about the blast radius

2. Read about the IAM role trust policy. A trust policy defines **who** can assume the role. For an EC2 instance profile, the trust policy allows the EC2 service to assume the role.

**Part 2: Create the EC2 Role**

3. Create an IAM role named `flowforge-ec2-role` with a trust policy that allows EC2 to assume it:
   - The trust policy should have `"Service": "ec2.amazonaws.com"` as the Principal
   - Create this role using the AWS CLI (not the Console)

4. Create a custom policy named `FlowForgeEC2Policy` that allows:
   - **S3 read**: `s3:GetObject`, `s3:ListBucket` on the FlowForge artifacts bucket
   - **CloudWatch Logs write**: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
   - **ECR pull**: `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer`

5. Attach the `FlowForgeEC2Policy` to the `flowforge-ec2-role`.

6. Think about why these specific permissions:
   - Why does the EC2 instance need to read from S3 but not write?
   - Why does it need CloudWatch Logs write?
   - Why does it need ECR pull but not push?
   - What's the principle at work here?

**Part 3: Instance Profile**

7. Create an instance profile and add the role to it:
   - Use `aws iam create-instance-profile`
   - Use `aws iam add-role-to-instance-profile`
   - Why is the instance profile a separate resource from the role? (Hint: it's a historical artifact, but understanding it matters)

8. Verify the instance profile exists and has the correct role:
   - Use `aws iam get-instance-profile`
   - Confirm the role is attached

**Part 4: Verify Role Permissions**

9. You can't fully test the instance profile until you launch an EC2 instance in Lab 03, but you can verify the policy is correct:
   - Use the Policy Simulator with the `flowforge-ec2-role`
   - Test: can the role read from the FlowForge S3 bucket? (Should be: Allowed)
   - Test: can the role write to S3? (Should be: Denied)
   - Test: can the role launch EC2 instances? (Should be: Denied)
   - Test: can the role create CloudWatch log groups? (Should be: Allowed)

10. Document the difference between:
    - An IAM user with access keys on the instance
    - An IAM role with an instance profile on the instance
    - When would you ever use access keys instead of a role? (Answer: almost never on EC2)

> **Link forward**: In Module 6 (Terraform), you'll define this role and instance profile as Terraform resources. In Module 7 (CI/CD), your pipeline will assume a role using OIDC federation -- no long-lived credentials at all.

### Expected Outcome

- An IAM role (`flowforge-ec2-role`) exists with S3 read, CloudWatch write, and ECR pull permissions
- An instance profile is created and associated with the role
- Policy Simulator confirms the role can do what FlowForge needs and nothing more
- You can explain why roles are preferred over access keys for EC2 instances
- You understand the trust policy and how EC2 assumes the role

### Checkpoint Questions

1. Explain the difference between an IAM user, group, role, and policy. When would you use each?
2. Why are IAM roles preferred over access keys on EC2 instances?
3. What is a trust policy? Who is the "Principal" in an EC2 instance profile's trust policy?
4. If the EC2 instance needs to write to a different S3 bucket, what would you change? What would you NOT change?
5. Describe the difference between identity-based policies and resource-based policies. Give an example of each.

---

## What's Next

With IAM properly configured, proceed to [Lab 02: VPC & Networking](lab-02-vpc-networking.md) where you'll build the network infrastructure for FlowForge from scratch.
