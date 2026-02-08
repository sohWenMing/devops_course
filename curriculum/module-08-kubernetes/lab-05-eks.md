# Lab 05: EKS -- FlowForge on AWS Managed Kubernetes

> **Module**: 8 -- Kubernetes  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Lab 04 completed (full FlowForge stack on Kind). Module 5 (AWS) and Module 6 (Terraform) completed. AWS account with permissions. Terraform installed.

---

## Overview

You've deployed FlowForge to a local Kind cluster. Now you'll take the same application and deploy it to AWS EKS -- a production-grade managed Kubernetes service. You'll extend your Terraform modules from Module 6 to provision an EKS cluster and use the AWS Load Balancer Controller for Ingress.

> **Cost Warning**: EKS costs ~$0.10/hour for the control plane alone (~$73/month). Worker nodes add EC2 costs. **Create the cluster, do the lab, and destroy it in the same session.** Use your Python cleanup script from Module 5 if needed.

---

## Exercise 5a: EKS with Terraform -- From Local to Cloud

### Objectives

- Add an EKS cluster to your Terraform modules from Module 6
- Deploy FlowForge to EKS using the same K8s manifests (with minor modifications)
- Use the AWS Load Balancer Controller for Ingress (ALB instead of nginx)
- Understand what's different between Kind and EKS and what's the same
- Clean up ALL resources when done

### What You'll Do

**Part 1: Plan the EKS Infrastructure**

1. Before writing any Terraform, plan what you need:
   - EKS cluster in the VPC from Module 6 (which subnets?)
   - Managed Node Group (what instance type? How many nodes? Min/max for auto-scaling?)
   - IAM roles: cluster role (for the EKS control plane), node role (for EC2 worker nodes)
   - Security groups: what traffic does the cluster need?
   - OIDC provider for IAM Roles for Service Accounts (IRSA) -- why?
   - AWS Load Balancer Controller (requires IRSA)

2. Draw the EKS architecture on paper:
   - VPC with your existing subnets from Module 5/6
   - EKS control plane (managed by AWS -- where does it live?)
   - Worker nodes in private subnets
   - ALB in public subnets (created by the Load Balancer Controller)
   - How does this compare to your Kind architecture?

**Part 2: Write the Terraform**

3. Create an EKS Terraform module (or add to existing modules):
   - `aws_eks_cluster` resource: cluster name, role ARN, VPC config (subnet IDs, endpoint access)
   - `aws_eks_node_group` resource: instance types (t3.medium minimum for K8s), scaling config, node role
   - IAM roles and policies: what permissions does the EKS cluster need? What permissions do the nodes need?
   - Think: should EKS be its own module or part of the compute module?

4. Configure IAM Roles for Service Accounts (IRSA):
   - Create an OIDC provider for the EKS cluster
   - This allows K8s ServiceAccounts to assume IAM roles -- why is this important?
   - What's the alternative to IRSA? (Hint: node instance profiles -- why is that worse?)

5. Add the AWS Load Balancer Controller:
   - This controller watches for Ingress resources and creates ALBs
   - It needs an IAM role (via IRSA) with permissions to create/manage ALBs, target groups, etc.
   - Install it via Helm or manifests (Terraform's `helm_release` resource works)

6. Run Terraform:
   - `terraform plan` -- review what will be created. How many resources?
   - `terraform apply` -- this takes 10-15 minutes (EKS cluster creation is slow)
   - Configure kubectl to use the EKS cluster: `aws eks update-kubeconfig --name <cluster-name> --region <region>`
   - `kubectl get nodes` -- are your worker nodes Ready?

**Part 3: Deploy FlowForge to EKS**

7. Compare your Kind manifests to what you need for EKS:
   - Deployments: same (this is the power of K8s abstraction!)
   - Services: same ClusterIP services
   - ConfigMaps/Secrets: same (but for production, consider External Secrets Operator)
   - PVC: change StorageClass from Kind's default to `gp2` or `gp3` (EBS)
   - Ingress: change from nginx Ingress Controller to AWS ALB Ingress Controller (different annotations)

8. Modify your manifests for EKS:
   - Update the Ingress to use the `alb` Ingress class
   - Add AWS-specific annotations (e.g., `alb.ingress.kubernetes.io/scheme: internet-facing`)
   - Update the PVC StorageClass if needed
   - For the PostgreSQL password, consider whether you'd use K8s Secrets or AWS Secrets Manager in production

9. Apply your manifests:
   - `kubectl apply -f k8s/`
   - Watch Pods start: `kubectl get pods -w`
   - Watch the ALB being created: `kubectl get ingress` -- the ADDRESS field will eventually show an ALB DNS name
   - The ALB can take 2-3 minutes to provision and become healthy

10. Verify the deployment:
    - `kubectl get all` -- everything should be Running
    - `curl http://<ALB-DNS-name>/api/health`
    - Create a task, check the worker processes it, query the result
    - Compare the experience to Kind -- what took longer? What was the same?

**Part 4: Kind vs EKS Comparison**

11. Document the differences:

    | Aspect | Kind | EKS |
    |--------|------|-----|
    | Cluster creation time | ? | ? |
    | Cost | ? | ? |
    | Node type | ? | ? |
    | Storage | ? | ? |
    | Load balancer | ? | ? |
    | Manifest changes needed | ? | ? |
    | Networking model | ? | ? |
    | Security (IAM, RBAC) | ? | ? |

12. Think about the architecture decisions:
    - What does "managed" mean for EKS? What does AWS handle that you handled in Kind?
    - If the EKS control plane goes down, what happens to your running Pods?
    - What's the minimum EKS setup for a production FlowForge deployment? (node count, instance types, AZ distribution)
    - How would you handle EKS upgrades? (K8s version, node AMI updates)

**Part 5: Clean Up (CRITICAL)**

13. Destroy everything:
    - Delete K8s resources first: `kubectl delete -f k8s/` (this deletes the ALB via the controller)
    - Wait for ALB deletion to complete (check AWS Console or CLI)
    - `terraform destroy` -- removes the EKS cluster, node group, IAM roles
    - Verify in AWS Console: no running EC2 instances, no ALBs, no EKS clusters
    - Check your billing dashboard

14. Why is cleanup order important?
    - What happens if you `terraform destroy` before deleting K8s resources?
    - The ALB created by the Load Balancer Controller is not in Terraform state -- Terraform won't delete it
    - This can leave orphaned resources costing money

### Expected Outcome

- EKS cluster provisioned via Terraform
- FlowForge deployed to EKS with the same manifests (minor modifications)
- External access via AWS ALB (created by the Load Balancer Controller)
- End-to-end task flow verified on EKS
- Documented comparison of Kind vs EKS
- All resources cleaned up

### Checkpoint Questions

- Can you explain the IAM roles needed for EKS (cluster role, node role, IRSA)?
- What's the difference between EKS managed node groups and self-managed nodes?
- How many of your K8s manifests changed between Kind and EKS? Which ones and why?
- What does the AWS Load Balancer Controller do that the nginx Ingress Controller doesn't?
- If you `terraform destroy` without deleting K8s resources first, what gets orphaned?
- What does "managed Kubernetes" actually mean? What is and isn't AWS's responsibility?
- How does the EKS networking model (VPC CNI -- Pods get real VPC IPs) differ from Kind's networking?

---

## What's Next?

In [Lab 06](lab-06-broken-k8s.md), you'll debug four intentionally broken K8s deployments -- the Kubernetes equivalent of the "broken server" from Module 1.
