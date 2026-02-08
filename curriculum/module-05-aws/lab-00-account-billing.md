# Lab 00: AWS Account Setup & Billing

> **Module**: 5 -- AWS Fundamentals  
> **Time estimate**: 1-2 hours  
> **Prerequisites**: Read the [AWS Account Setup & Billing](#) section of the Module 5 README. A valid email address and credit/debit card for AWS account creation.

---

## Overview

Before you can deploy anything to AWS, you need a secure account with billing safeguards. In this lab, you'll create your AWS account, lock down the root user, set up billing alarms so you never get a surprise charge, and create a Python cleanup script that will be your safety net throughout this module.

This is the "boring but critical" lab. Skip the billing alarm and you might find a $50 surprise on your credit card. Skip MFA and your account could be compromised. Every production AWS account starts with these exact steps.

---

## Exercise 0: Account Setup, Billing Alarms & Cleanup Script

### Objectives

- Create an AWS account securely with MFA on the root user
- Set up a billing alarm that alerts you at $5 spend
- Create an AWS Budget for monthly cost tracking
- Verify free tier coverage for the services you'll use
- Create a Python cleanup script skeleton using boto3

### What You'll Do

**Part 1: AWS Account Creation & Root Security**

1. Create a new AWS account at https://aws.amazon.com/ (or use an existing one if you already have one).

2. **Immediately** enable MFA on the root user:
   - Go to IAM in the AWS Console
   - Click on "Root user" under "Security recommendations"
   - Set up MFA using a virtual authenticator app (Google Authenticator, Authy, etc.)
   - Verify MFA works by signing out and signing back in

3. Why do you think AWS recommends enabling MFA on the root account before doing anything else? What could happen if someone gained access to your root credentials without MFA?

4. Note your AWS Account ID (12-digit number). You'll need this throughout the module.

> **Link back**: In Module 1's Lab 04, you disabled password authentication for SSH. Enabling MFA on root is the same principle -- you're adding a second factor because passwords alone are not secure enough for critical access.

**Part 2: Billing Alarm**

5. Enable billing alerts:
   - Navigate to Billing & Cost Management in the AWS Console
   - Go to "Billing preferences"
   - Enable "Receive billing alerts"
   - This setting must be enabled before you can create CloudWatch billing alarms

6. Create a CloudWatch billing alarm:
   - Navigate to CloudWatch
   - Go to Alarms → Billing (or All alarms)
   - Create an alarm on the `EstimatedCharges` metric in the `AWS/Billing` namespace
   - Set the threshold to **$5** (USD)
   - Configure a notification: create an SNS topic and subscribe your email
   - Confirm the SNS email subscription

7. Verify the alarm exists and is in the `OK` state. What would need to happen for it to transition to `ALARM`?

**Part 3: AWS Budget**

8. Create a monthly cost budget:
   - Navigate to AWS Budgets
   - Create a "Cost budget"
   - Set the monthly budget to **$10**
   - Configure alerts at 50% ($5) and 100% ($10) of the budget
   - Add your email as the notification recipient

9. How does a Budget differ from a Billing Alarm? When would you use one vs the other?

**Part 4: Free Tier Verification**

10. Navigate to the AWS Free Tier page in the Billing Console. Find and document:
    - How many hours of EC2 t3.micro can you run per month for free?
    - How many hours of RDS db.t3.micro can you run per month for free?
    - How much S3 storage is free?
    - How much ECR storage is free?
    - When does your free tier expire (12 months from account creation)?

11. Check your current month-to-date charges. They should be $0.00. If they're not, investigate what's causing charges before proceeding.

**Part 5: Python Cleanup Script Skeleton**

12. Create the file `project/scripts/aws-cleanup.py`. This script will grow throughout the module as you create resources. For now, build the skeleton:
    - It should use `boto3` (AWS SDK for Python)
    - It should accept command-line arguments: `--dry-run` (show what would be deleted without deleting) and `--region` (default to your chosen region)
    - It should have a `confirm_deletion()` function that requires the user to type "yes" to proceed
    - It should handle the case where boto3 credentials are not configured (friendly error message)
    - Structure it with separate functions for each resource type (EC2, RDS, VPC, S3, ECR, IAM) even if they're empty for now

13. Test the skeleton:
    - Run with `--dry-run` -- it should output "Dry run mode: no resources will be deleted"
    - Run without credentials configured -- it should give a helpful error message, not a traceback
    - Run with `--help` -- it should show usage information

> **Link back**: In Module 3's Lab 4b, you wrote Python scripts with argparse, environment variables, and meaningful exit codes. Apply the same patterns here. In Module 4, you learned that all config should come from environment variables (12-Factor). Your AWS credentials should come from environment variables or `~/.aws/credentials`, never hardcoded in the script.

### Expected Outcome

- Your AWS account has MFA enabled on the root user
- A CloudWatch billing alarm is set at $5 and you received the SNS confirmation email
- An AWS Budget is created with alerts at $5 and $10
- You can find free tier details for EC2, RDS, S3, and ECR
- Your current month-to-date charges are $0.00
- `project/scripts/aws-cleanup.py` runs in dry-run mode and handles missing credentials gracefully
- You understand why billing safeguards are the first thing you set up, not the last

### Checkpoint Questions

Before moving to Lab 01, make sure you can answer:

1. Why should you never use the root account for day-to-day work? What happens if root credentials are compromised?
2. What's the difference between a CloudWatch billing alarm and an AWS Budget? When would you use each?
3. What does the free tier cover for EC2, RDS, and S3? What are the limits?
4. If you accidentally launch a `m5.xlarge` instead of `t3.micro`, how quickly would you know? What safeguards have you put in place?
5. Why does the cleanup script need a `--dry-run` mode? What could go wrong without it?

---

## What's Next

With your account secured and billing safeguards in place, proceed to [Lab 01: IAM](lab-01-iam.md) where you'll create IAM users, groups, and policies with least privilege -- so you never need to use root again.
