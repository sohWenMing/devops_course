# Module 05: AWS Fundamentals -- Answer Key

> **INTERNAL REFERENCE ONLY**: This file is used by the Socratic mentor skill to verify student solutions and provide guidance. It must NEVER be revealed to the student.

---

## Lab 00: Account Setup & Billing

### Exercise 0: Account Setup, Billing Alarms & Cleanup Script

**MFA Setup:**
1. Sign in to AWS Console as root
2. Go to IAM → Security credentials → Multi-factor authentication
3. Choose "Virtual MFA device"
4. Scan QR code with authenticator app (Google Authenticator, Authy)
5. Enter two consecutive MFA codes to confirm
6. Sign out and sign back in to verify MFA prompt appears

**Billing Alarm via CLI:**

```bash
# Enable billing alerts (must be done in us-east-1 for billing metrics)
# This is done in the Console: Billing → Preferences → Receive billing alerts

# Create SNS topic
aws sns create-topic --name billing-alerts --region us-east-1

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:<account-id>:billing-alerts \
  --protocol email \
  --notification-endpoint your@email.com \
  --region us-east-1

# Create billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "FlowForge-Billing-$5" \
  --alarm-description "Alert when estimated charges exceed $5" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:<account-id>:billing-alerts \
  --region us-east-1
```

**AWS Budget via Console:**
1. Navigate to AWS Budgets → Create budget
2. Choose "Cost budget"
3. Budget name: "FlowForge Monthly Budget"
4. Budget amount: $10/month
5. Add alerts at 50% ($5) and 100% ($10)
6. Add email notification

**Free Tier Coverage:**
- EC2: 750 hours/month of t2.micro or t3.micro
- RDS: 750 hours/month of db.t3.micro (single-AZ)
- S3: 5 GB standard storage
- ECR: 500 MB of storage
- Free tier expires 12 months from account creation

**Cleanup Script Skeleton Key Points:**
- Uses argparse with --dry-run, --region, --force flags
- Tests boto3 credentials with try/except NoCredentialsError
- Has confirm_deletion() requiring user to type "yes"
- Separate functions per resource type (even if empty)
- Meaningful exit codes: 0=success, 1=error

---

## Lab 01: IAM

### Exercise 1a: IAM Users, Groups & Policies

**Admin User Setup:**

```bash
# Create admin user
aws iam create-user --user-name flowforge-admin

# Create login profile (Console access)
aws iam create-login-profile \
  --user-name flowforge-admin \
  --password "ChangeMe123!" \
  --password-reset-required

# Create access keys (programmatic access)
aws iam create-access-key --user-name flowforge-admin
# Save the AccessKeyId and SecretAccessKey!

# Create administrators group
aws iam create-group --group-name administrators

# Attach admin policy to group
aws iam attach-group-policy \
  --group-name administrators \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Add user to group
aws iam add-user-to-group \
  --group-name administrators \
  --user-name flowforge-admin

# Configure CLI
aws configure
# Enter: access key, secret key, us-east-1, json

# Verify
aws sts get-caller-identity
# Output: Account, UserId, Arn showing flowforge-admin
```

**Deployment User with Least Privilege:**

```bash
# Create deploy user (programmatic only)
aws iam create-user --user-name flowforge-deploy
aws iam create-access-key --user-name flowforge-deploy
```

**FlowForgeDeployPolicy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2Management",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeRouteTables",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeNatGateways",
        "ec2:DescribeNetworkAcls",
        "ec2:DescribeKeyPairs",
        "ec2:DescribeImages",
        "ec2:DescribeAddresses",
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:CreateInternetGateway",
        "ec2:DeleteInternetGateway",
        "ec2:AttachInternetGateway",
        "ec2:DetachInternetGateway",
        "ec2:CreateNatGateway",
        "ec2:DeleteNatGateway",
        "ec2:AllocateAddress",
        "ec2:ReleaseAddress",
        "ec2:CreateKeyPair",
        "ec2:DeleteKeyPair",
        "ec2:ImportKeyPair",
        "ec2:CreateTags",
        "ec2:ModifyVpcAttribute",
        "ec2:ModifySubnetAttribute",
        "ec2:CreateNetworkAcl",
        "ec2:DeleteNetworkAcl",
        "ec2:CreateNetworkAclEntry",
        "ec2:DeleteNetworkAclEntry",
        "ec2:ReplaceNetworkAclAssociation"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDSManagement",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:CreateDBInstance",
        "rds:DeleteDBInstance",
        "rds:ModifyDBInstance",
        "rds:DescribeDBSubnetGroups",
        "rds:CreateDBSubnetGroup",
        "rds:DeleteDBSubnetGroup",
        "rds:AddTagsToResource",
        "rds:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3FlowForge",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetBucketPolicy",
        "s3:PutBucketPolicy",
        "s3:PutBucketVersioning",
        "s3:GetBucketVersioning",
        "s3:PutLifecycleConfiguration",
        "s3:PutPublicAccessBlock",
        "s3:GetPublicAccessBlock",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::flowforge-*",
        "arn:aws:s3:::flowforge-*/*"
      ]
    },
    {
      "Sid": "S3ListBuckets",
      "Effect": "Allow",
      "Action": "s3:ListAllMyBuckets",
      "Resource": "*"
    },
    {
      "Sid": "ECRManagement",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:CreateRepository",
        "ecr:DeleteRepository",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "ecr:DescribeImages",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchDeleteImage",
        "ecr:PutLifecyclePolicy",
        "ecr:PutImageScanningConfiguration",
        "ecr:TagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMPassRole",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::*:role/flowforge-*"
    },
    {
      "Sid": "CloudWatchAccess",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:PutMetricAlarm",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SSMParameterRead",
      "Effect": "Allow",
      "Action": "ssm:GetParameters",
      "Resource": "arn:aws:ssm:*:*:parameter/aws/service/*"
    }
  ]
}
```

```bash
# Create the policy
aws iam create-policy \
  --policy-name FlowForgeDeployPolicy \
  --policy-document file://flowforge-deploy-policy.json

# Create group and attach
aws iam create-group --group-name deployers
aws iam attach-group-policy \
  --group-name deployers \
  --policy-arn arn:aws:iam::<account-id>:policy/FlowForgeDeployPolicy

aws iam add-user-to-group \
  --group-name deployers \
  --user-name flowforge-deploy
```

**Policy Simulator Tests:**
- flowforge-deploy + ec2:RunInstances → Allowed
- flowforge-deploy + iam:CreateUser → Denied
- flowforge-deploy + s3:DeleteBucket on non-flowforge bucket → Denied
- flowforge-deploy + s3:GetObject on flowforge-artifacts → Allowed

### Exercise 1b: IAM Roles & Instance Profiles

**EC2 Role Trust Policy (trust-policy.json):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**EC2 Role Policy (flowforge-ec2-policy.json):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Read",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::flowforge-*",
        "arn:aws:s3:::flowforge-*/*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECRPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchCheckLayerAvailability"
      ],
      "Resource": "*"
    }
  ]
}
```

```bash
# Create role
aws iam create-role \
  --role-name flowforge-ec2-role \
  --assume-role-policy-document file://trust-policy.json

# Create and attach policy
aws iam create-policy \
  --policy-name FlowForgeEC2Policy \
  --policy-document file://flowforge-ec2-policy.json

aws iam attach-role-policy \
  --role-name flowforge-ec2-role \
  --policy-arn arn:aws:iam::<account-id>:policy/FlowForgeEC2Policy

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name flowforge-ec2-profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name flowforge-ec2-profile \
  --role-name flowforge-ec2-role

# Verify
aws iam get-instance-profile \
  --instance-profile-name flowforge-ec2-profile
```

---

## Lab 02: VPC & Networking

### Exercise 2a: VPC from Scratch

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=flowforge-vpc},{Key=Project,Value=FlowForge}]' \
  --query 'Vpc.VpcId' --output text)

# Enable DNS hostnames
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames '{"Value":true}'
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support '{"Value":true}'

# Create subnets (adjust AZ names for your region)
PUB_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=flowforge-public-a},{Key=Project,Value=FlowForge}]' \
  --query 'Subnet.SubnetId' --output text)

PUB_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=flowforge-public-b},{Key=Project,Value=FlowForge}]' \
  --query 'Subnet.SubnetId' --output text)

PRIV_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=flowforge-private-a},{Key=Project,Value=FlowForge}]' \
  --query 'Subnet.SubnetId' --output text)

PRIV_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID --cidr-block 10.0.20.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=flowforge-private-b},{Key=Project,Value=FlowForge}]' \
  --query 'Subnet.SubnetId' --output text)

DB_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID --cidr-block 10.0.100.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=flowforge-database-a},{Key=Project,Value=FlowForge}]' \
  --query 'Subnet.SubnetId' --output text)

DB_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID --cidr-block 10.0.200.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=flowforge-database-b},{Key=Project,Value=FlowForge}]' \
  --query 'Subnet.SubnetId' --output text)

# Enable auto-assign public IP for public subnets
aws ec2 modify-subnet-attribute --subnet-id $PUB_A --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUB_B --map-public-ip-on-launch

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=flowforge-igw},{Key=Project,Value=FlowForge}]' \
  --query 'InternetGateway.InternetGatewayId' --output text)

aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID

# Allocate Elastic IP for NAT Gateway
EIP_ALLOC=$(aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=flowforge-nat-eip},{Key=Project,Value=FlowForge}]' \
  --query 'AllocationId' --output text)

# Create NAT Gateway in public subnet
NAT_ID=$(aws ec2 create-nat-gateway \
  --subnet-id $PUB_A \
  --allocation-id $EIP_ALLOC \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=flowforge-nat},{Key=Project,Value=FlowForge}]' \
  --query 'NatGateway.NatGatewayId' --output text)

# Wait for NAT Gateway
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_ID

# Create route tables
# Public route table
PUB_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=flowforge-public-rt},{Key=Project,Value=FlowForge}]' \
  --query 'RouteTable.RouteTableId' --output text)

aws ec2 create-route --route-table-id $PUB_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --route-table-id $PUB_RT --subnet-id $PUB_A
aws ec2 associate-route-table --route-table-id $PUB_RT --subnet-id $PUB_B

# Private route table
PRIV_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=flowforge-private-rt},{Key=Project,Value=FlowForge}]' \
  --query 'RouteTable.RouteTableId' --output text)

aws ec2 create-route --route-table-id $PRIV_RT --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_ID
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $PRIV_A
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $PRIV_B

# Database route table (no internet route)
DB_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=flowforge-database-rt},{Key=Project,Value=FlowForge}]' \
  --query 'RouteTable.RouteTableId' --output text)

aws ec2 associate-route-table --route-table-id $DB_RT --subnet-id $DB_A
aws ec2 associate-route-table --route-table-id $DB_RT --subnet-id $DB_B

# Verify
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=FlowForge" --query 'Vpcs[].{Id:VpcId,CIDR:CidrBlock}'
aws ec2 describe-subnets --filters "Name=tag:Project,Values=FlowForge" --query 'Subnets[].{Id:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone,Name:Tags[?Key==`Name`].Value|[0]}'
```

**/24 subnet usable IPs:** 256 total - 5 reserved = **251 usable IPs**. AWS reserves: network address, VPC router, DNS server, future use, broadcast.

### Exercise 2b: Security Groups & NACLs

```bash
# Create security groups
API_SG=$(aws ec2 create-security-group \
  --group-name flowforge-api-sg \
  --description "FlowForge API - public facing" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=flowforge-api-sg},{Key=Project,Value=FlowForge}]' \
  --query 'GroupId' --output text)

WORKER_SG=$(aws ec2 create-security-group \
  --group-name flowforge-worker-sg \
  --description "FlowForge Worker - internal only" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=flowforge-worker-sg},{Key=Project,Value=FlowForge}]' \
  --query 'GroupId' --output text)

DB_SG=$(aws ec2 create-security-group \
  --group-name flowforge-db-sg \
  --description "FlowForge DB - app tier only" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=flowforge-db-sg},{Key=Project,Value=FlowForge}]' \
  --query 'GroupId' --output text)

# API SG rules
MY_IP=$(curl -s https://checkip.amazonaws.com)/32

aws ec2 authorize-security-group-ingress --group-id $API_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $API_SG --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $API_SG --protocol tcp --port 22 --cidr $MY_IP

# DB SG rules (reference SG IDs, not IPs)
aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 5432 --source-group $API_SG
aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 5432 --source-group $WORKER_SG

# NACL for database subnets
DB_NACL=$(aws ec2 create-network-acl \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=network-acl,Tags=[{Key=Name,Value=flowforge-db-nacl},{Key=Project,Value=FlowForge}]' \
  --query 'NetworkAcl.NetworkAclId' --output text)

# Allow inbound PostgreSQL from VPC
aws ec2 create-network-acl-entry --network-acl-id $DB_NACL --rule-number 100 --protocol tcp --port-range From=5432,To=5432 --cidr-block 10.0.0.0/16 --rule-action allow --ingress

# Allow inbound ephemeral ports (return traffic)
aws ec2 create-network-acl-entry --network-acl-id $DB_NACL --rule-number 200 --protocol tcp --port-range From=1024,To=65535 --cidr-block 10.0.0.0/16 --rule-action allow --ingress

# Deny all other inbound
aws ec2 create-network-acl-entry --network-acl-id $DB_NACL --rule-number 32766 --protocol -1 --cidr-block 0.0.0.0/0 --rule-action deny --ingress

# Allow outbound ephemeral ports (return traffic)
aws ec2 create-network-acl-entry --network-acl-id $DB_NACL --rule-number 100 --protocol tcp --port-range From=1024,To=65535 --cidr-block 10.0.0.0/16 --rule-action allow --egress

# Deny all other outbound
aws ec2 create-network-acl-entry --network-acl-id $DB_NACL --rule-number 32766 --protocol -1 --cidr-block 0.0.0.0/0 --rule-action deny --egress

# Associate NACL with database subnets (need to replace default association)
# Find the current NACL associations for the database subnets
# aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" "Name=default,Values=true"
# Then use replace-network-acl-association with each subnet's association ID
```

**Security Group Design Table:**

| SG | Port | Protocol | Source | Purpose |
|----|------|----------|--------|---------|
| api-sg | 80 | TCP | 0.0.0.0/0 | HTTP from internet |
| api-sg | 443 | TCP | 0.0.0.0/0 | HTTPS from internet |
| api-sg | 22 | TCP | YOUR_IP/32 | SSH from your IP only |
| worker-sg | (none) | - | - | No inbound |
| db-sg | 5432 | TCP | api-sg | PostgreSQL from API |
| db-sg | 5432 | TCP | worker-sg | PostgreSQL from Worker |

---

## Lab 03: Compute & Storage

### Exercise 3a: EC2 Instance

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name flowforge-key \
  --query 'KeyMaterial' --output text > flowforge-key.pem

chmod 400 flowforge-key.pem

# Find latest Ubuntu 22.04 AMI
AMI_ID=$(aws ssm get-parameters \
  --names /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id \
  --query 'Parameters[0].Value' --output text)

# User data script
cat > user-data.sh << 'USERDATA'
#!/bin/bash
set -euxo pipefail
apt-get update
apt-get install -y docker.io postgresql-client awscli
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu
USERDATA

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.micro \
  --key-name flowforge-key \
  --subnet-id $PUB_A \
  --security-group-ids $API_SG \
  --iam-instance-profile Name=flowforge-ec2-profile \
  --user-data file://user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=flowforge-api},{Key=Project,Value=FlowForge}]' \
  --query 'Instances[0].InstanceId' --output text)

# Wait for running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "EC2 Public IP: $PUBLIC_IP"

# SSH in (wait a minute for user data to complete)
ssh -i flowforge-key.pem ubuntu@$PUBLIC_IP

# On the instance, verify:
docker --version
aws sts get-caller-identity  # Should show flowforge-ec2-role
```

### Exercise 3b: RDS PostgreSQL

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name flowforge-db-subnet-group \
  --db-subnet-group-description "FlowForge database subnets" \
  --subnet-ids $DB_A $DB_B \
  --tags Key=Project,Value=FlowForge

# Launch RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier flowforge-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15 \
  --master-username flowforge \
  --master-user-password YourStrongPassword123! \
  --db-name flowforge \
  --allocated-storage 20 \
  --storage-type gp2 \
  --db-subnet-group-name flowforge-db-subnet-group \
  --vpc-security-group-ids $DB_SG \
  --no-publicly-accessible \
  --no-multi-az \
  --backup-retention-period 1 \
  --tags Key=Project,Value=FlowForge

# Wait for available (5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier flowforge-db

# Get endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier flowforge-db \
  --query 'DBInstances[0].Endpoint.Address' --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"

# Connect from EC2
# SSH into EC2, then:
psql -h $RDS_ENDPOINT -U flowforge -d flowforge

# Create schema
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    assigned_worker VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO tasks (name) VALUES ('test-task');
SELECT * FROM tasks;
```

### Exercise 3c: S3 Bucket

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create bucket (for non-us-east-1 regions, add --create-bucket-configuration)
aws s3 mb s3://flowforge-artifacts-$ACCOUNT_ID

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket flowforge-artifacts-$ACCOUNT_ID \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket flowforge-artifacts-$ACCOUNT_ID \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Tag the bucket
aws s3api put-bucket-tagging \
  --bucket flowforge-artifacts-$ACCOUNT_ID \
  --tagging 'TagSet=[{Key=Project,Value=FlowForge}]'

# Upload/download test
echo '{"env":"production","version":"1.0"}' > deployment-config.json
aws s3 cp deployment-config.json s3://flowforge-artifacts-$ACCOUNT_ID/configs/
aws s3 ls s3://flowforge-artifacts-$ACCOUNT_ID/configs/
rm deployment-config.json
aws s3 cp s3://flowforge-artifacts-$ACCOUNT_ID/configs/deployment-config.json ./
cat deployment-config.json
```

**Python boto3 script example:**

```python
#!/usr/bin/env python3
"""Upload and download files to/from FlowForge S3 bucket."""

import argparse
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def upload_file(s3_client, bucket, local_path, s3_key):
    try:
        s3_client.upload_file(local_path, bucket, s3_key)
        print(f"Uploaded {local_path} to s3://{bucket}/{s3_key}")
    except ClientError as e:
        print(f"Error uploading: {e}")
        sys.exit(1)

def download_file(s3_client, bucket, s3_key, local_path):
    try:
        s3_client.download_file(bucket, s3_key, local_path)
        print(f"Downloaded s3://{bucket}/{s3_key} to {local_path}")
    except ClientError as e:
        print(f"Error downloading: {e}")
        sys.exit(1)

def list_objects(s3_client, bucket, prefix=""):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for obj in response.get("Contents", []):
            print(f"  {obj['Key']} ({obj['Size']} bytes)")
    except ClientError as e:
        print(f"Error listing: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="FlowForge S3 operations")
    parser.add_argument("action", choices=["upload", "download", "list"])
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--local", help="Local file path")
    parser.add_argument("--key", help="S3 object key")
    parser.add_argument("--prefix", default="", help="S3 prefix for listing")
    args = parser.parse_args()

    try:
        s3 = boto3.client("s3")
    except NoCredentialsError:
        print("ERROR: AWS credentials not configured.")
        sys.exit(1)

    if args.action == "upload":
        upload_file(s3, args.bucket, args.local, args.key)
    elif args.action == "download":
        download_file(s3, args.bucket, args.key, args.local)
    elif args.action == "list":
        list_objects(s3, args.bucket, args.prefix)

if __name__ == "__main__":
    main()
```

**Lifecycle policy:**

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket flowforge-artifacts-$ACCOUNT_ID \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "LogsLifecycle",
        "Filter": {"Prefix": "logs/"},
        "Status": "Enabled",
        "Transitions": [
          {"Days": 30, "StorageClass": "STANDARD_IA"},
          {"Days": 90, "StorageClass": "GLACIER"}
        ],
        "Expiration": {"Days": 365}
      }
    ]
  }'
```

---

## Lab 04: ECR & Deploy

### Exercise 4a: ECR Repository & Push/Pull

```bash
# Create repositories
aws ecr create-repository \
  --repository-name flowforge/api-service \
  --image-scanning-configuration scanOnPush=true \
  --tags Key=Project,Value=FlowForge

aws ecr create-repository \
  --repository-name flowforge/worker-service \
  --image-scanning-configuration scanOnPush=true \
  --tags Key=Project,Value=FlowForge

# Get ECR URI
ECR_URI=$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Authenticate Docker
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI

# Tag images
docker tag flowforge-api:latest $ECR_URI/flowforge/api-service:v1
docker tag flowforge-worker:latest $ECR_URI/flowforge/worker-service:v1

# Push
docker push $ECR_URI/flowforge/api-service:v1
docker push $ECR_URI/flowforge/worker-service:v1

# Verify
aws ecr list-images --repository-name flowforge/api-service
aws ecr describe-images --repository-name flowforge/api-service

# On EC2: authenticate and pull
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
docker pull $ECR_URI/flowforge/api-service:v1
docker pull $ECR_URI/flowforge/worker-service:v1

# Lifecycle policy (keep last 10 images)
aws ecr put-lifecycle-policy \
  --repository-name flowforge/api-service \
  --lifecycle-policy-text '{
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep only 10 images",
        "selection": {
          "tagStatus": "any",
          "countType": "imageCountMoreThan",
          "countNumber": 10
        },
        "action": {"type": "expire"}
      }
    ]
  }'
```

### Exercise 4b: Manual Full Deployment

```bash
# On EC2 instance:

# Run api-service
docker run -d \
  --name flowforge-api \
  -p 8080:8080 \
  -e DATABASE_URL="postgres://flowforge:YourStrongPassword123!@$RDS_ENDPOINT:5432/flowforge?sslmode=require" \
  -e PORT=8080 \
  -e LOG_LEVEL=info \
  $ECR_URI/flowforge/api-service:v1

# Run worker-service
docker run -d \
  --name flowforge-worker \
  -e DATABASE_URL="postgres://flowforge:YourStrongPassword123!@$RDS_ENDPOINT:5432/flowforge?sslmode=require" \
  -e POLL_INTERVAL=5s \
  -e LOG_LEVEL=info \
  $ECR_URI/flowforge/worker-service:v1

# Verify
docker ps
docker logs flowforge-api
docker logs flowforge-worker
```

**From local machine, test:**

```bash
# Health check
curl http://$PUBLIC_IP:8080/health

# Create task
curl -X POST http://$PUBLIC_IP:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"name":"test-task-from-aws"}'

# List tasks
curl http://$PUBLIC_IP:8080/tasks

# Check worker processed it
# (wait a few seconds for worker to pick up)
curl http://$PUBLIC_IP:8080/tasks
```

**Health check script (aws-healthcheck.py):**

```python
#!/usr/bin/env python3
"""Validate FlowForge AWS deployment end-to-end."""

import argparse
import json
import sys
import time
import requests

def check_health(base_url):
    try:
        r = requests.get(f"{base_url}/health", timeout=10)
        return r.status_code == 200
    except requests.RequestException:
        return False

def create_task(base_url, name):
    try:
        r = requests.post(
            f"{base_url}/tasks",
            json={"name": name},
            timeout=10
        )
        if r.status_code in (200, 201):
            return r.json()
        return None
    except requests.RequestException:
        return None

def get_tasks(base_url):
    try:
        r = requests.get(f"{base_url}/tasks", timeout=10)
        return r.json() if r.status_code == 200 else []
    except requests.RequestException:
        return []

def main():
    parser = argparse.ArgumentParser(description="FlowForge deployment health check")
    parser.add_argument("host", help="EC2 public IP or hostname")
    parser.add_argument("--port", default=8080, type=int)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    checks = {"api_health": False, "task_create": False, "worker_process": False}

    print(f"Checking FlowForge at {base_url}...")

    # Check 1: API health
    checks["api_health"] = check_health(base_url)
    print(f"  API Health: {'PASS' if checks['api_health'] else 'FAIL'}")

    if not checks["api_health"]:
        print("API is not healthy. Cannot continue checks.")
        sys.exit(1)

    # Check 2: Create task
    task = create_task(base_url, "healthcheck-test")
    checks["task_create"] = task is not None
    print(f"  Task Create: {'PASS' if checks['task_create'] else 'FAIL'}")

    # Check 3: Worker processes task
    if task:
        print("  Waiting for worker to process task...")
        for i in range(10):
            time.sleep(3)
            tasks = get_tasks(base_url)
            for t in tasks:
                if t.get("name") == "healthcheck-test" and t.get("status") != "pending":
                    checks["worker_process"] = True
                    break
            if checks["worker_process"]:
                break
    print(f"  Worker Process: {'PASS' if checks['worker_process'] else 'FAIL'}")

    # Summary
    passed = all(checks.values())
    print(f"\nOverall: {'ALL CHECKS PASSED' if passed else 'SOME CHECKS FAILED'}")
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
```

---

## Lab 05: Cleanup

### Exercise 5: Resource Cleanup

**Deletion order (dependencies first):**
1. EC2 instances (terminate and wait)
2. RDS instances (delete, skip final snapshot, wait)
3. NAT Gateways (delete and wait)
4. Elastic IPs (release)
5. RDS subnet groups (delete)
6. Security group rules (revoke cross-references)
7. Security groups (delete)
8. Custom NACLs (replace subnet associations, delete)
9. Route table associations (disassociate)
10. Custom route tables (delete)
11. Subnets (delete)
12. Internet Gateways (detach, delete)
13. VPC (delete)
14. S3 buckets (empty all objects/versions, delete)
15. ECR repositories (delete images, delete repos)
16. IAM instance profiles (remove roles, delete)
17. IAM roles (detach policies, delete inline, delete)
18. IAM users (remove from groups, delete keys, detach policies, delete)
19. IAM groups (remove users, detach policies, delete)
20. IAM policies (delete versions, delete)

**Resources that cost money when "stopped":**

| Resource | Stopped | Cost? | Explanation |
|----------|---------|-------|-------------|
| EC2 instance | Stopped | Partial | No compute charge, but EBS volume still charged (~$0.10/GB/month) |
| EC2 instance | Terminated | No | Fully gone, no charges |
| EBS volume | Detached | Yes | Charged per GB provisioned regardless of attachment |
| RDS instance | Stopped | Yes | AWS restarts stopped RDS after 7 days; storage still charged |
| NAT Gateway | Can't stop | Yes | Must delete; ~$0.045/hour |
| Elastic IP | Not attached | Yes | $0.005/hour to discourage waste |
| S3 bucket | With objects | Yes | Per GB stored + requests |
| ECR repository | With images | Yes | Per GB stored |

The full cleanup script is at `project/scripts/aws-cleanup.py`.
