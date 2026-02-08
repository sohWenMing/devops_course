# Lab 04: ECR & Manual Deployment

> **Module**: 5 -- AWS Fundamentals  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [ECR Container Registry](#) and [Manual Deployment Workflow](#) sections of the Module 5 README. Labs 00-03 completed (VPC, EC2, RDS, S3 all running).

---

## Overview

In this lab, you'll push your Docker images to ECR and perform a complete manual deployment of FlowForge on AWS. This is the culmination of the entire module: your containerized application running on real cloud infrastructure with proper networking, a managed database, and container images stored in a private registry.

---

## Exercise 4a: ECR Repository & Image Push/Pull

### Objectives

- Create ECR repositories for FlowForge services
- Authenticate Docker with ECR
- Tag and push Docker images from your local machine
- Pull images on the EC2 instance
- Understand image tagging strategies and lifecycle policies

### What You'll Do

**Part 1: Create Repositories**

1. Create ECR repositories for both FlowForge services:
   - `flowforge/api-service`
   - `flowforge/worker-service`
   - Use `aws ecr create-repository` for each
   - Tag with `Project: FlowForge`

2. Note the repository URIs. They look like:
   `<account-id>.dkr.ecr.<region>.amazonaws.com/flowforge/api-service`

3. Enable image scanning on push for both repositories:
   - This automatically scans images for known vulnerabilities when pushed
   - How does this relate to the trivy scanning from Module 4?

**Part 2: Authenticate & Push**

4. Authenticate Docker with ECR:
   - Use `aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com`
   - What does this command do? How long does the authentication token last?

5. Tag your local Docker images with the ECR repository URI:
   - `docker tag flowforge-api:latest <ecr-repo-uri>/flowforge/api-service:v1`
   - `docker tag flowforge-worker:latest <ecr-repo-uri>/flowforge/worker-service:v1`
   - Why use `v1` instead of `latest`? What happens in production when everyone pushes to `latest`?

6. Push both images to ECR:
   - `docker push <ecr-repo-uri>/flowforge/api-service:v1`
   - `docker push <ecr-repo-uri>/flowforge/worker-service:v1`
   - Observe the layer upload -- which layers are shared between images? How does this relate to the layer sharing you learned about in Module 4?

7. Verify the images are in ECR:
   - Use `aws ecr list-images` to see the tags
   - Use `aws ecr describe-images` to see the image details and scan results

> **Link back**: In Module 4's Lab 02, you built multi-stage Docker images that are < 20MB. Those optimized images are what you're pushing to ECR now. Smaller images mean faster pushes and faster pulls.

**Part 3: Pull on EC2**

8. SSH into your EC2 instance and authenticate Docker with ECR:
   - The instance profile should have ECR pull permissions (from Lab 01's role)
   - Use the same `get-login-password` command but this time credentials come from the instance profile

9. Pull both images:
   - `docker pull <ecr-repo-uri>/flowforge/api-service:v1`
   - `docker pull <ecr-repo-uri>/flowforge/worker-service:v1`

10. Verify the images are available on the instance:
    - `docker images`
    - Compare the image sizes to what you see in ECR

11. If the pull fails:
    - Check the instance profile: does the role have ECR pull permissions?
    - Check the security group: can the instance reach ECR (it's an AWS API endpoint, needs outbound HTTPS)
    - Check the authentication: did `get-login-password` succeed?

**Part 4: Image Tagging Strategy**

12. Push a second version with a different tag strategy:
    - Tag with the git SHA: `docker tag flowforge-api:latest <ecr-repo-uri>/flowforge/api-service:<git-sha>`
    - Push it
    - Now you have `v1` and `<git-sha>` pointing to the same image
    - Why is the git SHA a better tag than `v1` for production?

13. Create an ECR lifecycle policy that keeps only the last 10 images:
    - Use `aws ecr put-lifecycle-policy`
    - Why is cleanup important for ECR? (Hint: storage costs)

### Expected Outcome

- Two ECR repositories exist: `flowforge/api-service` and `flowforge/worker-service`
- Docker images are pushed from your local machine and pullable on EC2
- The EC2 instance authenticates with ECR using instance profile credentials (no access keys)
- You understand image tagging strategies (why not `latest`)
- A lifecycle policy limits stored images

### Checkpoint Questions

1. Push a new image version to ECR and pull it on EC2 without referencing your previous commands.
2. Explain your image tagging strategy. Why is git SHA better than `latest`?
3. What happens if the ECR authentication token expires while you're in the middle of a push?
4. How does ECR image scanning compare to the trivy scanning from Module 4?
5. Why does the EC2 instance use an instance profile for ECR authentication instead of access keys?

---

## Exercise 4b: Manual Full Deployment

### Objectives

- Deploy the complete FlowForge stack to AWS manually
- Connect ECR images on EC2 to RDS PostgreSQL with proper networking
- Verify end-to-end functionality: create a task via the API, verify the worker processes it, verify data persists in RDS
- Write a Python health check script that validates the deployment
- Document every manual step (to appreciate Terraform in Module 6)

### What You'll Do

**Part 1: Prepare the Environment**

1. Document your infrastructure:
   - EC2 public IP: __________
   - RDS endpoint: __________
   - RDS port: 5432
   - RDS database name: flowforge
   - RDS master username: flowforge
   - ECR API image URI: __________
   - ECR Worker image URI: __________

2. Ensure the RDS database has the FlowForge schema (from Lab 03). If not, connect from EC2 and create it.

**Part 2: Deploy FlowForge Containers**

3. SSH into the EC2 instance and run the api-service container:
   - Pull the image from ECR (if not already pulled)
   - Run with the correct environment variables:
     - `DATABASE_URL` pointing to the RDS endpoint
     - `PORT` for the API listening port
     - Any other environment variables your FlowForge API needs
   - Map the container port to the host port
   - Run in detached mode

4. Run the worker-service container on the same instance:
   - Pull the image from ECR
   - Set the same `DATABASE_URL` (both services connect to the same database)
   - Set worker-specific environment variables (poll interval, etc.)
   - Run in detached mode

5. Verify both containers are running:
   - `docker ps` -- both should show as running
   - `docker logs <api-container>` -- check for startup messages and database connection
   - `docker logs <worker-container>` -- check for polling messages

> **Link back**: This is exactly what `docker compose up` did in Module 4, but manually on a cloud instance. The environment variables are the same ones from Module 3's 12-Factor config. The only change is `DATABASE_URL` now points to RDS instead of a local PostgreSQL.

**Part 3: End-to-End Verification**

6. From your local machine, test the API:
   - `curl http://<ec2-public-ip>:<port>/health` -- should return a healthy status
   - `curl -X POST http://<ec2-public-ip>:<port>/tasks -d '{"name":"test-task"}'` -- should create a task
   - `curl http://<ec2-public-ip>:<port>/tasks` -- should list the task

7. Verify the worker processes the task:
   - Check worker logs: `docker logs <worker-container>`
   - The worker should pick up the task and change its status
   - Query the API again to see the updated status

8. Verify data persists in RDS:
   - Connect to RDS from the EC2 instance using `psql`
   - Query the tasks table directly
   - Verify the data matches what the API returned

**Part 4: Health Check Script**

9. Write a Python health check script (`project/scripts/aws-healthcheck.py`) that validates the entire deployment:
   - Check API health endpoint responds with 200
   - Create a test task via the API
   - Wait for the worker to process it (poll with timeout)
   - Verify the task status changed
   - Clean up the test task
   - Report overall health: all checks passed or list of failures
   - Accept the EC2 public IP as a command-line argument

10. Run the health check script from your local machine:
    - It should report all green if everything is working
    - Break something (stop the worker container) and run it again -- it should report the specific failure

**Part 5: Document the Process**

11. Write down every step you performed to deploy FlowForge to AWS, from the very first `aws` command to the final health check. Count the steps.
    - How many AWS CLI commands did you run across all labs?
    - How many manual SSH sessions?
    - How long did the entire process take?
    - What would happen if you needed to deploy to a second environment (staging)?

12. Identify which steps are:
    - **Infrastructure** (VPC, subnets, security groups, etc.) -- these will become Terraform in Module 6
    - **Deployment** (push images, pull images, run containers) -- these will become CI/CD in Module 7
    - **Orchestration** (managing containers, health checks, restarts) -- this will become Kubernetes in Module 8

> **Architecture Thinking**: You just experienced the pain of manual deployment. Every step you documented is a step that could be forgotten, done wrong, or done differently by a different person. This is why we automate. Terraform automates the infrastructure. CI/CD automates the deployment. Kubernetes automates the orchestration. But you needed to do it manually first to understand what the automation is doing.

### Expected Outcome

- FlowForge api-service and worker-service are running as Docker containers on EC2
- Both services connect to RDS PostgreSQL
- The end-to-end flow works: create task via API → worker processes → data persists in RDS
- The API is accessible from the internet via the EC2 public IP
- A Python health check script validates the entire deployment
- You have a documented list of every manual step performed

### Checkpoint Questions

1. End-to-end: create a task via the API on the EC2 public IP, verify the worker processes it, verify the data is in RDS.
2. If the API can reach the internet but can't connect to RDS, list everything you'd check.
3. How many manual steps did the entire deployment take? What would happen if you needed to do this weekly?
4. Which parts of the deployment would Terraform automate? Which parts would CI/CD automate? Which parts would Kubernetes automate?
5. What happens if the EC2 instance terminates? What data is lost? What persists? (Hint: Docker containers vs RDS data)

---

## What's Next

With FlowForge running on AWS, proceed to [Lab 05: Cleanup](lab-05-cleanup.md) where you'll tear down all resources and verify you have no ongoing charges.
