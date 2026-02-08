# Lab 02: VPC & Networking

> **Module**: 5 -- AWS Fundamentals  
> **Time estimate**: 4-5 hours  
> **Prerequisites**: Read the [VPC Networking from Scratch](#) and [Security Groups & NACLs](#) sections of the Module 5 README. Labs 00-01 completed (AWS account with IAM users configured).

---

## Overview

In this lab, you'll build the entire network infrastructure for FlowForge from scratch using the AWS CLI. No clicking through the Console -- every resource is created via CLI commands so you understand exactly what each component does. This is the same subnet planning and firewall design you did in Module 2, but now on real cloud infrastructure.

---

## Exercise 2a: VPC from Scratch via CLI

### Objectives

- Create a VPC with a carefully planned CIDR block
- Create public, private, and database subnets across two Availability Zones
- Set up an Internet Gateway for public internet access
- Create a NAT Gateway for private subnet outbound access
- Configure route tables for each subnet tier
- Perform all operations via AWS CLI (not the Console)

### What You'll Do

**Part 1: VPC Creation**

1. Create a VPC with CIDR block `10.0.0.0/16` using the AWS CLI.
   - Tag it with `Name: flowforge-vpc` and `Project: FlowForge`
   - How many IP addresses does a /16 give you?
   - Why is 10.0.0.0/16 a good choice? Could you use 172.16.0.0/16 or 192.168.0.0/16 instead?

2. Enable DNS hostnames and DNS resolution on the VPC.
   - Why do instances need DNS hostnames? What feature depends on this?

> **Link back**: In Module 2's Lab 1b, you calculated subnet ranges by hand. You're now applying that exact math to real infrastructure. In Module 2's Lab 3b, you used network namespaces to simulate separate subnets. AWS VPCs are the production version of that concept.

**Part 2: Subnet Design**

3. Before creating subnets, plan your CIDR allocation. You need:
   - 2 public subnets (one per AZ) for internet-facing resources
   - 2 private subnets (one per AZ) for application tier
   - 2 database subnets (one per AZ, required by RDS for subnet groups)

4. Create all 6 subnets using the AWS CLI:
   - Public subnets: `10.0.1.0/24` (AZ-a) and `10.0.2.0/24` (AZ-b)
   - Private subnets: `10.0.10.0/24` (AZ-a) and `10.0.20.0/24` (AZ-b)
   - Database subnets: `10.0.100.0/24` (AZ-a) and `10.0.200.0/24` (AZ-b)
   - Tag each subnet with its purpose (`Name: flowforge-public-a`, etc.) and `Project: FlowForge`

5. For the public subnets, enable "auto-assign public IPv4 address."
   - Why is this only on public subnets?
   - What would happen if private subnet instances got public IPs?

6. Calculate: how many usable IPs does each /24 subnet provide? (Hint: AWS reserves 5 IPs per subnet -- the first 4 and the last 1.)

**Part 3: Internet Gateway**

7. Create an Internet Gateway and attach it to your VPC.
   - Tag it with `Name: flowforge-igw` and `Project: FlowForge`
   - A VPC can have at most one IGW. What happens to internet traffic if the IGW is detached?

**Part 4: NAT Gateway**

8. Allocate an Elastic IP address for the NAT Gateway.

9. Create a NAT Gateway in one of the public subnets (AZ-a), using the Elastic IP.
   - Tag it with `Name: flowforge-nat` and `Project: FlowForge`
   - Wait for the NAT Gateway to reach the "available" state before proceeding
   - Why must the NAT Gateway be in a PUBLIC subnet? What would happen if you put it in a private subnet?

> **Cost warning**: NAT Gateways cost ~$0.045/hour. Remember to delete this when you're done for the day if you want to minimize costs. The cleanup script should handle this.

**Part 5: Route Tables**

10. Create a route table for public subnets:
    - Add a route: `0.0.0.0/0` → Internet Gateway
    - Associate this route table with both public subnets
    - Tag it: `Name: flowforge-public-rt`

11. Create a route table for private subnets:
    - Add a route: `0.0.0.0/0` → NAT Gateway
    - Associate this route table with both private subnets
    - Tag it: `Name: flowforge-private-rt`

12. Create a route table for database subnets:
    - Do NOT add a `0.0.0.0/0` route -- database subnets have no internet access at all
    - Associate this route table with both database subnets
    - Tag it: `Name: flowforge-database-rt`

13. Verify your route tables:
    - Use `aws ec2 describe-route-tables` to list all route tables
    - For each one, verify the routes and subnet associations
    - Draw a diagram (on paper or a tool) showing the traffic flow from the internet to an instance in each subnet tier

**Part 6: Verification**

14. Verify your entire VPC setup:
    - List the VPC: `aws ec2 describe-vpcs --filters "Name=tag:Project,Values=FlowForge"`
    - List subnets and confirm their CIDR blocks and AZ placement
    - List route tables and confirm the routes
    - Confirm the IGW is attached and the NAT Gateway is available

15. Answer: if a user sends an HTTP request to your API running in the public subnet, trace the path of that request through every component (IGW → subnet → route table → instance → security group). What about the response path?

### Expected Outcome

- A VPC (`10.0.0.0/16`) exists with DNS hostnames enabled
- 6 subnets across 2 AZs: 2 public, 2 private, 2 database
- An Internet Gateway is attached to the VPC
- A NAT Gateway with an Elastic IP is in the public subnet
- Route tables are configured: public → IGW, private → NAT, database → local only
- All resources are tagged with `Project: FlowForge`
- You can trace a request path through every network component

### Checkpoint Questions

1. Draw the VPC architecture from memory, including all subnets, gateways, and route tables.
2. Explain the traffic flow from the internet to an EC2 instance in the private subnet (through IGW, public subnet, NAT). Why can't the internet initiate a connection to a private subnet instance?
3. What's the difference between an Internet Gateway and a NAT Gateway?
4. Why do you need subnets in at least two Availability Zones? What does this protect against?
5. How many usable IPs are in a /24 subnet in AWS? Why does AWS reserve 5?

---

## Exercise 2b: Security Groups & NACLs

### Objectives

- Design security groups for a 3-tier architecture (API, worker, database)
- Implement least-privilege rules using security group references
- Create and configure NACLs as a second layer of defense
- Understand the difference between stateful (SG) and stateless (NACL) firewalls
- Debug connectivity issues by determining whether the problem is SG or NACL

### What You'll Do

**Part 1: Security Group Design**

1. Before creating any security groups, plan the rules on paper. You need three security groups:

   **api-sg** (for the API service EC2 instance in the public subnet):
   - What inbound traffic does the API need to accept? (HTTP/HTTPS from the internet, SSH from your IP only)
   - What outbound traffic does it need? (Default: all)

   **worker-sg** (for the worker service -- if you later move it to a separate instance):
   - Should the worker accept ANY inbound traffic from the internet?
   - What outbound traffic does it need?

   **db-sg** (for the RDS PostgreSQL instance in the database subnet):
   - Who should be able to connect to PostgreSQL (port 5432)?
   - Should the database be reachable from the internet? (Answer: absolutely not)

2. Create the three security groups using the AWS CLI, all in the FlowForge VPC. Tag each with `Project: FlowForge`.

**Part 2: Security Group Rules**

3. Add inbound rules to `api-sg`:
   - Allow TCP port 80 from `0.0.0.0/0` (HTTP from the internet)
   - Allow TCP port 443 from `0.0.0.0/0` (HTTPS from the internet)
   - Allow TCP port 22 from YOUR public IP address only (use `/32` CIDR)
   - Find your public IP: what command or website would you use?

4. Add inbound rules to `worker-sg`:
   - No inbound rules from the internet
   - If workers are on the same instance as the API for now, you may not need this SG yet, but create it for the architecture

5. Add inbound rules to `db-sg`:
   - Allow TCP port 5432 from `api-sg` (reference the security group ID, not an IP range)
   - Allow TCP port 5432 from `worker-sg`
   - No other inbound rules

6. Why is referencing a security group (e.g., "allow port 5432 from api-sg") better than referencing an IP address (e.g., "allow port 5432 from 10.0.1.50")? What happens when the EC2 instance IP changes?

> **Link back**: In Module 2's Lab 3a, you wrote iptables rules for a 3-tier application. The design is identical here -- allow specific ports from specific sources, deny everything else. The difference is that security groups are stateful (return traffic is automatic) while iptables is stateless (you needed explicit rules for return traffic).

**Part 3: NACL Configuration**

7. Examine the default NACL for your VPC:
   - Use `aws ec2 describe-network-acls` to see the rules
   - What does the default NACL allow? Is it permissive or restrictive?

8. Create a custom NACL for the database subnets:
   - Allow inbound TCP port 5432 from the VPC CIDR (`10.0.0.0/16`)
   - Allow inbound ephemeral ports (1024-65535) from the VPC CIDR (for return traffic)
   - Deny all other inbound traffic
   - Allow outbound TCP ephemeral ports (1024-65535) to the VPC CIDR (for return traffic)
   - Deny all other outbound traffic
   - Associate this NACL with both database subnets

9. Why do you need ephemeral port rules for NACLs but not for security groups? (Hint: stateful vs stateless.)

10. Answer this: if a connection from the API to the database is being blocked, how would you determine whether the problem is the security group or the NACL?
    - What tools or logs would you check?
    - What's the systematic approach to debugging this?

**Part 4: Verification**

11. Verify all security groups:
    - List them: `aws ec2 describe-security-groups --filters "Name=tag:Project,Values=FlowForge"`
    - For each SG, verify the inbound and outbound rules
    - Confirm `db-sg` references `api-sg` and `worker-sg` (not IP addresses)

12. Verify the NACL:
    - Confirm it's associated with the database subnets
    - Confirm the rules allow only the intended traffic

13. Document your security group design as a table:

    | SG | Port | Source | Purpose |
    |----|------|--------|---------|
    | api-sg | 80 | 0.0.0.0/0 | HTTP |
    | ... | ... | ... | ... |

### Expected Outcome

- Three security groups exist: `api-sg`, `worker-sg`, `db-sg`
- `db-sg` only allows PostgreSQL from `api-sg` and `worker-sg` (security group references)
- `api-sg` allows HTTP/HTTPS from internet and SSH from your IP only
- A custom NACL protects database subnets with explicit allow/deny rules
- You understand stateful vs stateless firewalls and can debug connectivity issues
- All resources are tagged with `Project: FlowForge`

### Checkpoint Questions

1. Explain the difference between security groups and NACLs (stateful vs stateless, allow vs deny, instance vs subnet level).
2. Given a connectivity problem between two instances, describe how you would determine if the issue is a security group or a NACL.
3. Why is referencing a security group ID better than an IP address in security group rules?
4. Write security group rules from scratch for a new scenario: a web server that needs HTTPS from the internet, SSH from a bastion host's security group, and a database that only the web server can reach.
5. Why do NACL rules need explicit ephemeral port ranges for return traffic? What are ephemeral ports?

---

## What's Next

With the network infrastructure and security boundaries in place, proceed to [Lab 03: Compute & Storage](lab-03-compute-storage.md) where you'll launch EC2 instances, set up RDS PostgreSQL, and create S3 buckets.
