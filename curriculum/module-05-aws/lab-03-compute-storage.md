# Lab 03: Compute & Storage -- EC2, RDS & S3

> **Module**: 5 -- AWS Fundamentals  
> **Time estimate**: 4-5 hours  
> **Prerequisites**: Read the [EC2 Instances](#), [RDS PostgreSQL](#), and [S3 Basics](#) sections of the Module 5 README. Labs 00-02 completed (VPC with subnets, security groups, and IAM roles configured).

---

## Overview

In this lab, you'll launch the compute and storage resources for FlowForge. You'll run an EC2 instance in the public subnet, set up a managed PostgreSQL database with RDS in the database subnet, and create an S3 bucket for deployment artifacts. By the end, you'll have the infrastructure backbone ready for the full deployment in Lab 04.

---

## Exercise 3a: EC2 Instance in Public Subnet

### Objectives

- Launch an EC2 instance in the public subnet using the AWS CLI
- Connect via SSH using key pairs
- Install Docker on the instance
- Run a FlowForge container to verify the setup
- Attach the IAM instance profile from Lab 01

### What You'll Do

**Part 1: Key Pair**

1. Create an SSH key pair for EC2 access:
   - Use `aws ec2 create-key-pair` to create a key pair named `flowforge-key`
   - Save the private key to a file with proper permissions (remember Module 1: what permissions should a private key have?)
   - Alternatively, import your existing SSH public key with `aws ec2 import-key-pair`

> **Link back**: In Module 1's Lab 04, you generated SSH key pairs and configured sshd to disable password auth. The same principle applies here -- key-based auth only, no passwords.

**Part 2: Find the AMI**

2. Find the latest Ubuntu 22.04 AMI for your region:
   - Use `aws ec2 describe-images` with filters for Ubuntu, 22.04, and amd64
   - Or use AWS Systems Manager Parameter Store: `aws ssm get-parameters --names /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id`
   - Record the AMI ID

3. Why does the AMI ID differ between regions? What would happen if you used an AMI ID from us-east-1 in eu-west-1?

**Part 3: Launch the Instance**

4. Launch a `t3.micro` EC2 instance using the AWS CLI:
   - Place it in one of the public subnets
   - Attach the `api-sg` security group
   - Use the `flowforge-key` key pair
   - Attach the `flowforge-ec2-role` instance profile from Lab 01
   - Tag with `Name: flowforge-api` and `Project: FlowForge`
   - Include user data that installs Docker (write a bash script that runs on first boot)

5. Wait for the instance to reach the "running" state. Find its public IP address:
   - Use `aws ec2 describe-instances` to get the public IP
   - Why does the instance have a public IP? (Hint: what setting did you enable on the public subnet?)

**Part 4: SSH and Verify**

6. SSH into the instance:
   - Use your private key file
   - The default username for Ubuntu AMIs is `ubuntu`
   - If SSH hangs, what should you check? (Security group, NACL, route table, instance state...)

7. Once connected, verify:
   - Is Docker installed and running? (Check if your user data worked)
   - Can the instance reach the internet? (Try `curl https://checkip.amazonaws.com`)
   - What is the instance's private IP? What is its public IP? How do they relate?

8. Verify the instance profile is working:
   - Run `aws sts get-caller-identity` on the instance (no AWS CLI credentials should be configured -- the instance profile provides them)
   - Does the output show the `flowforge-ec2-role`?
   - Try `aws s3 ls` -- does it work? Should it work? (Hint: your role has S3 read on a specific bucket, not `s3:ListAllMyBuckets`)

**Part 5: Run FlowForge Container**

9. Pull and run the FlowForge api-service container:
   - For now, use the image you built locally in Module 4, or a simple test image
   - Run it with the appropriate port mapping
   - Verify you can access the API from your local machine using the EC2 public IP

10. If the container can't be reached from your machine, debug systematically:
    - Is the container running? (`docker ps`)
    - Is the container listening on the right port? (`docker logs`)
    - Is the security group allowing the traffic?
    - Is the route table correct?

> **Architecture Thinking**: You're running Docker directly on EC2. This is the "pets" approach -- you manage the instance, install Docker, run containers manually. In Module 8 (Kubernetes), you'll move to the "cattle" approach where the orchestrator manages containers automatically. But understanding the manual approach first helps you debug when the automation fails.

### Expected Outcome

- An EC2 `t3.micro` instance is running in the public subnet
- You can SSH into it from your machine
- Docker is installed and running (via user data or manual installation)
- The instance profile provides AWS credentials (verified with `aws sts get-caller-identity`)
- A FlowForge container runs and is accessible from the internet
- All resources are tagged with `Project: FlowForge`

### Checkpoint Questions

1. Launch an EC2 instance from the CLI from memory (no copying previous commands). What parameters are required?
2. Explain instance types, AMIs, user data, and key pairs in plain language.
3. What's the difference between the instance's private IP and public IP? When would you use each?
4. If you can't SSH into an instance, list 5 things you'd check in order.
5. How does the instance profile provide AWS credentials to the instance? How are these credentials different from access keys?

---

## Exercise 3b: RDS PostgreSQL in Database Subnet

### Objectives

- Create an RDS DB subnet group using the database subnets
- Launch an RDS PostgreSQL instance (free tier: db.t3.micro)
- Configure the security group to allow connections from EC2 only
- Connect to the database from the EC2 instance
- Understand the managed database model

### What You'll Do

**Part 1: DB Subnet Group**

1. Create a DB subnet group that includes both database subnets:
   - Use `aws rds create-db-subnet-group`
   - Name it `flowforge-db-subnet-group`
   - Include both database subnet IDs
   - Why does RDS require at least two subnets in different AZs?

**Part 2: Launch RDS**

2. Launch an RDS PostgreSQL instance using the AWS CLI:
   - Engine: `postgres` (latest version)
   - Instance class: `db.t3.micro` (free tier)
   - Storage: 20 GB General Purpose SSD (free tier)
   - Master username: `flowforge`
   - Master password: choose a strong password (you'll need this later)
   - DB name: `flowforge`
   - Use the `flowforge-db-subnet-group`
   - Attach the `db-sg` security group
   - Disable Multi-AZ (free tier doesn't cover it)
   - Disable public accessibility (the database should NOT be reachable from the internet)
   - Tag with `Project: FlowForge`

3. Wait for the instance to reach "available" status. This takes 5-10 minutes.
   - Use `aws rds describe-db-instances` to check the status
   - While waiting: why does RDS take longer to launch than EC2? What is AWS doing behind the scenes?

4. Note the RDS endpoint (hostname):
   - This is what your application will use as the PostgreSQL host
   - It looks like `flowforge.xxxxxxxx.us-east-1.rds.amazonaws.com`

**Part 3: Connect from EC2**

5. SSH into your EC2 instance and connect to the RDS database:
   - Install the PostgreSQL client: `sudo apt-get install -y postgresql-client`
   - Connect: `psql -h <rds-endpoint> -U flowforge -d flowforge`
   - Enter the master password when prompted

6. If the connection fails:
   - Check the `db-sg` security group: does it allow port 5432 from `api-sg`?
   - Check the route tables: can the public subnet reach the database subnet? (Hint: the `local` route in the VPC handles this)
   - Check that the RDS instance is NOT publicly accessible
   - Is DNS resolution working? Try `nslookup <rds-endpoint>` from the EC2 instance

7. Once connected, create the FlowForge schema:
   - Create the tasks table (use the schema from Module 3)
   - Insert a test row
   - Query it back
   - This proves end-to-end connectivity: your EC2 instance can reach the database through the security group

> **Link back**: In Module 3's Lab 2a, you set up PostgreSQL locally and connected from your Go service. The SQL is identical -- only the connection string changes. Remember the 12-Factor config from Lab 4a? The `DATABASE_URL` environment variable is how you'll point the FlowForge containers at RDS instead of a local PostgreSQL.

**Part 4: Understand the Managed Model**

8. Explore what RDS manages for you:
   - Check automated backups: `aws rds describe-db-instances` and look at `BackupRetentionPeriod`
   - Check the maintenance window: when will AWS apply patches?
   - Can you SSH into the RDS instance? Why not?

9. Document the pros and cons of RDS vs self-managed PostgreSQL on EC2:
   - What does RDS handle that you'd have to manage yourself?
   - What control do you lose with RDS?
   - When would self-managed PostgreSQL on EC2 be the better choice?

### Expected Outcome

- A DB subnet group exists with both database subnets
- An RDS PostgreSQL `db.t3.micro` instance is running in the database subnet
- The database is NOT publicly accessible
- You can connect to RDS from the EC2 instance (but not from the internet)
- The FlowForge schema is created and test data is inserted
- You understand what RDS manages and what you still control

### Checkpoint Questions

1. Explain Multi-AZ vs Read Replicas. When would you use each?
2. Configure a connection from a new EC2 instance to the existing RDS -- what steps are needed? (Security group changes, subnet placement, connection string)
3. Why is the RDS instance not publicly accessible? What would change if it were?
4. If the EC2 instance can't connect to RDS, list 4 things you'd check in order.
5. What happens to your data if the RDS instance is stopped? What happens if it's deleted?

---

## Exercise 3c: S3 Bucket for Artifacts

### Objectives

- Create an S3 bucket with proper naming and configuration
- Write a bucket policy that grants access to the EC2 role
- Upload and download files via the AWS CLI
- Upload and download files using Python boto3
- Understand storage classes, versioning, and lifecycle policies

### What You'll Do

**Part 1: Create the Bucket**

1. Create an S3 bucket named `flowforge-artifacts-<your-account-id>` (bucket names must be globally unique):
   - Use `aws s3 mb` or `aws s3api create-bucket`
   - If your region is not us-east-1, you'll need to specify a `LocationConstraint`
   - Tag with `Project: FlowForge`

2. Enable versioning on the bucket:
   - Use `aws s3api put-bucket-versioning`
   - Why is versioning useful for deployment artifacts? What happens if you accidentally overwrite a config file?

3. Block all public access (this should be the default, but verify):
   - Use `aws s3api put-public-access-block`
   - Block all 4 public access settings
   - Why should deployment artifact buckets never be public?

**Part 2: Bucket Policy**

4. Write a bucket policy that allows the `flowforge-ec2-role` to read and write objects:
   - The policy should be a resource-based policy on the bucket
   - Allow `s3:GetObject` and `s3:PutObject` for the role
   - Allow `s3:ListBucket` for the role
   - Apply the policy with `aws s3api put-bucket-policy`

5. How does this bucket policy interact with the IAM policy you created in Lab 01? (Hint: both the identity-based and resource-based policy must allow the action -- unless one is in the same account, in which case either one can grant access.)

**Part 3: CLI Upload/Download**

6. Upload a test file using the AWS CLI:
   - Create a simple config file (e.g., `deployment-config.json`)
   - Upload it: `aws s3 cp deployment-config.json s3://flowforge-artifacts-<id>/configs/`
   - List the objects: `aws s3 ls s3://flowforge-artifacts-<id>/configs/`

7. Download the file:
   - Remove the local copy
   - Download it: `aws s3 cp s3://flowforge-artifacts-<id>/configs/deployment-config.json ./`
   - Verify the contents match

8. Test from the EC2 instance:
   - SSH into the instance
   - Use the AWS CLI (which should use the instance profile credentials)
   - Can you download the file? Can you upload a file?
   - How do you know the instance profile credentials are being used?

**Part 4: Python boto3**

9. Write a Python script (or add to the existing scripts) that:
   - Uses boto3 to connect to S3
   - Uploads a file to the FlowForge bucket
   - Lists objects in the bucket
   - Downloads a file from the bucket
   - Handles errors gracefully (bucket doesn't exist, no permissions, file not found)

10. Test the script both locally (with your AWS CLI credentials) and on the EC2 instance (with instance profile credentials). The code should be identical -- boto3 automatically finds credentials from the instance profile.

> **Link back**: In Module 3's Lab 4b, you wrote Python scripts with error handling and meaningful exit codes. Apply those same patterns here. In Module 4, you used Docker to make your code portable. The boto3 script should work identically on your local machine and on EC2 -- only the credential source changes.

**Part 5: Storage Classes and Lifecycle**

11. Explore storage classes:
    - Upload the same file to Standard, Standard-IA, and Glacier storage classes
    - Compare: how does retrieval work for each?
    - When would you use each class for deployment artifacts?

12. Create a lifecycle policy:
    - Move objects to Standard-IA after 30 days
    - Move objects to Glacier after 90 days
    - Delete objects after 365 days
    - Apply to the `logs/` prefix only (not `configs/`)

13. Why would you apply lifecycle policies to logs but not configs? What's the trade-off?

### Expected Outcome

- An S3 bucket exists with versioning enabled and public access blocked
- A bucket policy grants the EC2 role read/write access
- You can upload and download files via CLI and Python boto3
- The EC2 instance can access S3 using instance profile credentials (no access keys)
- A lifecycle policy is configured for the logs prefix
- You understand storage classes and when to use each

### Checkpoint Questions

1. Explain S3 storage classes: Standard, Standard-IA, Glacier. When would you use each?
2. What is S3 versioning? How does it protect against accidental deletion?
3. Write a bucket policy from scratch that allows a specific IAM role to read objects but not delete them.
4. What's the difference between the AWS CLI approach and the boto3 approach for S3 operations? When would you use each?
5. If your EC2 instance can't access S3, what would you check? (IAM role permissions, instance profile, bucket policy, network...)

---

## What's Next

With compute, database, and storage in place, proceed to [Lab 04: ECR & Deploy](lab-04-ecr-deploy.md) where you'll push your Docker images to ECR and deploy the complete FlowForge stack on AWS.
