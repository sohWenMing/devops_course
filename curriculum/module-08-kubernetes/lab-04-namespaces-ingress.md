# Lab 04: Namespaces & Ingress -- Organizing and Exposing FlowForge

> **Module**: 8 -- Kubernetes  
> **Time estimate**: 4-5 hours  
> **Prerequisites**: Lab 03 completed (Services, ConfigMaps, Secrets configured). Read the [Namespaces](#), [Ingress](#), and [PersistentVolumes & PersistentVolumeClaims](#) sections of the Module 8 README.

---

## Overview

Your FlowForge stack is running in the `default` namespace with NodePort access. In this lab, you'll organize resources with Namespaces, set up a proper Ingress controller for HTTP routing with TLS, and deploy the entire stack end-to-end with persistent storage.

---

## Exercise 4a: Namespaces -- Isolation and Organization

### Objectives

- Create namespaces for different environments (dev, staging)
- Deploy FlowForge to multiple namespaces
- Demonstrate cross-namespace DNS resolution
- Understand resource quotas and when to use namespaces vs separate clusters

### What You'll Do

**Part 1: Create Namespaces**

1. Create two namespaces: `flowforge-dev` and `flowforge-staging`:
   - You can use `kubectl create namespace` or a YAML manifest
   - Which approach is better for reproducibility? Why?

2. Verify your namespaces:
   - `kubectl get namespaces` -- you should see your two new ones plus the defaults
   - What namespaces already existed? What's in `kube-system`?

**Part 2: Deploy to Multiple Namespaces**

3. Deploy FlowForge to the `flowforge-dev` namespace:
   - You can add `namespace: flowforge-dev` to each manifest's `metadata` section
   - OR use `kubectl apply -f <file> -n flowforge-dev`
   - Deploy at minimum: PostgreSQL Deployment + Service, api-service Deployment + Service, ConfigMap, Secret
   - What's the trade-off between putting the namespace in the manifest vs using `-n` on the command line?

4. Deploy the same stack to `flowforge-staging` (with different ConfigMap values if you want -- e.g., different log level)

5. Verify isolation:
   - `kubectl get all -n flowforge-dev` -- see the dev resources
   - `kubectl get all -n flowforge-staging` -- see the staging resources
   - `kubectl get all` (no namespace flag) -- what do you see in `default`?

**Part 3: Cross-Namespace Communication**

6. Test that services in different namespaces can communicate (if needed):
   - From a Pod in `flowforge-dev`, try to reach the api-service in `flowforge-staging`:
     `kubectl exec -n flowforge-dev <pod> -- nslookup api-service.flowforge-staging.svc.cluster.local`
   - Does it resolve? Can you actually connect?
   - What does this tell you about namespace isolation? (Hint: namespaces provide naming isolation, not network isolation)

7. Think about when you'd want true network isolation:
   - How would you prevent dev from accidentally calling staging? (Preview: NetworkPolicies in Module 10)
   - When would separate clusters be better than namespaces?

**Part 4: Resource Quotas**

8. Create a ResourceQuota for the dev namespace:
   - Limit to 10 Pods, 2 CPU, 4Gi memory
   - Apply it to `flowforge-dev`
   - Try to scale a Deployment beyond the quota -- what happens?

9. Why would you use resource quotas?
   - Prevent dev environments from consuming production resources
   - Cost control in shared clusters
   - What happens if a namespace exceeds its quota?

### Expected Outcome

- Two namespaces (`flowforge-dev`, `flowforge-staging`) with FlowForge deployed to each
- Demonstrated cross-namespace DNS resolution
- Resource quota applied and enforced
- Understanding of namespace isolation boundaries

### Checkpoint Questions

- Can you create a namespace and deploy resources to it from memory?
- Can you list resources across all namespaces with a single command?
- What's the full DNS name to reach a Service in another namespace?
- When should you use namespaces vs separate clusters? What are the trade-offs?
- What do resource quotas protect against?

---

## Exercise 4b: Ingress -- HTTP Routing with TLS

### Objectives

- Install the nginx Ingress Controller on Kind
- Write an Ingress resource routing paths to FlowForge services
- Configure TLS termination with a self-signed certificate
- Understand Ingress vs LoadBalancer Services

### What You'll Do

**Part 1: Install the Ingress Controller**

1. Install the nginx Ingress Controller:
   - For Kind, there's a specific installation method. Check the Kind documentation for Ingress setup.
   - You may need to recreate your Kind cluster with specific port mappings (ports 80 and 443 mapped from host to the control-plane node)
   - Apply the nginx Ingress Controller manifests

2. Verify the Ingress Controller is running:
   - `kubectl get pods -n ingress-nginx` -- the controller Pod should be Running
   - `kubectl get services -n ingress-nginx` -- what type of Service is it?
   - This is itself a K8s Deployment with a Service -- it's turtles all the way down

3. Understand what happened:
   - What resources did the Ingress Controller installation create? (Deployments, Services, ConfigMaps, ServiceAccounts, RBAC...)
   - Why does the Ingress Controller need RBAC permissions? What does it watch for?

**Part 2: Create an Ingress Resource**

4. Make sure you have FlowForge deployed to the `default` namespace (or whichever namespace you choose) with working ClusterIP Services for api-service.

5. Write an Ingress manifest that:
   - Uses the `nginx` ingress class
   - Routes requests with path `/api` (Prefix) to the api-service Service on port 80
   - Add a route for `/health` if your api-service has a health endpoint
   - Sets the host to `flowforge.local` (you'll add this to /etc/hosts)

6. Apply and verify:
   - `kubectl apply -f <ingress.yaml>`
   - `kubectl get ingress` -- what ADDRESS is shown?
   - `kubectl describe ingress <name>` -- check the Rules and Backends
   - Add `127.0.0.1 flowforge.local` to your `/etc/hosts` file (remember Module 2?)

7. Test the routing:
   - `curl http://flowforge.local/api/health` (or appropriate endpoint)
   - `curl http://flowforge.local/api/tasks`
   - If it doesn't work, check the Ingress Controller logs: `kubectl logs -n ingress-nginx <controller-pod>`

**Part 3: TLS Termination**

8. Generate a self-signed TLS certificate:
   - Use `openssl` to create a certificate for `flowforge.local` (remember Module 2's TLS lab?)
   - `openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=flowforge.local"`

9. Create a K8s Secret of type `tls`:
   - `kubectl create secret tls flowforge-tls --cert=tls.crt --key=tls.key`
   - OR write a manifest. What `type` does a TLS Secret use?

10. Update your Ingress to use TLS:
    - Add a `tls` section referencing the `flowforge-tls` Secret and the `flowforge.local` host
    - Apply the updated Ingress

11. Test HTTPS:
    - `curl -k https://flowforge.local/api/health` (the `-k` flag ignores certificate validation for self-signed certs)
    - Inspect the certificate: `openssl s_client -connect flowforge.local:443 -servername flowforge.local`
    - Is HTTP still accessible? Should it be? (Hint: look at Ingress annotations for SSL redirect)

**Part 4: Ingress vs LoadBalancer**

12. Think about why you'd use Ingress instead of LoadBalancer Services:
    - How many AWS ALBs would you need with LoadBalancer Services for 5 microservices?
    - How many with Ingress?
    - What does Ingress give you that LoadBalancer Services don't? (Path-based routing, TLS termination, rewriting...)
    - When would you still use a LoadBalancer Service directly?

### Expected Outcome

- nginx Ingress Controller running on the Kind cluster
- Ingress resource routing `/api/*` to api-service
- TLS termination with self-signed certificate
- HTTPS access to FlowForge via `https://flowforge.local`

### Checkpoint Questions

- Can you install an Ingress Controller and create an Ingress resource from memory?
- Can you add a new path to an existing Ingress? (e.g., `/health` → api-service)
- Can you explain the difference between an Ingress Controller and an Ingress resource?
- How does the nginx Ingress Controller compare to the nginx reverse proxy from Module 2?
- What happens if no Ingress Controller is running but you create an Ingress resource?
- How would TLS work differently on EKS with ACM certificates vs self-signed certs?

---

## Exercise 4c: Full Local Deployment -- FlowForge End-to-End

### Objectives

- Deploy the entire FlowForge stack on Kind from manifests
- Use a PersistentVolumeClaim for PostgreSQL data
- Verify end-to-end task flow: create task → worker processes it → query result
- Practice deploying everything from a clean slate

### What You'll Do

**Part 1: Clean Slate**

1. Delete your existing resources (or create a fresh Kind cluster):
   - If starting fresh, create a new Kind cluster with Ingress port mappings
   - Install the nginx Ingress Controller
   - Load your FlowForge Docker images into the cluster

2. Organize your manifests:
   - Create a directory structure for your K8s manifests (e.g., `project/k8s/`)
   - Group related manifests logically (e.g., `namespace.yaml`, `postgres.yaml`, `api-service.yaml`, `worker-service.yaml`, `config.yaml`, `ingress.yaml`)
   - Why is manifest organization important? How does it relate to `kubectl apply -f <directory>`?

**Part 2: PostgreSQL with Persistent Storage**

3. Create a PersistentVolumeClaim for PostgreSQL:
   - Request 1Gi of storage (enough for development)
   - Access mode: ReadWriteOnce
   - Use the default StorageClass (Kind provisions local volumes automatically)

4. Update the PostgreSQL Deployment to mount the PVC:
   - Mount the PVC at `/var/lib/postgresql/data`
   - You may need a `subPath` to avoid PostgreSQL's "initdb: directory not empty" error
   - What happens to your data if the PostgreSQL Pod restarts? If the Pod is deleted? If the cluster is deleted?

5. Deploy PostgreSQL and verify:
   - Apply the PVC, then the Deployment and Service
   - `kubectl get pvc` -- is the PVC Bound? To what PV?
   - `kubectl get pv` -- was a PV dynamically provisioned?

**Part 3: Deploy Everything**

6. Deploy the complete stack in order:
   - Namespace (if using one)
   - ConfigMap and Secret
   - PVC for PostgreSQL
   - PostgreSQL Deployment + Service
   - Wait for PostgreSQL to be Ready (why is order important here?)
   - api-service Deployment + Service
   - worker-service Deployment + Service
   - Ingress

7. Alternatively, put all manifests in a directory and:
   - `kubectl apply -f k8s/` (applies everything in the directory)
   - Does order matter when using `kubectl apply -f <directory>`? What happens if a Pod starts before its ConfigMap exists?

8. Verify everything is running:
   - `kubectl get all` -- all Deployments should show the correct READY count
   - `kubectl get pods` -- all Pods should be Running (no CrashLoopBackOff)
   - `kubectl get services` -- ClusterIP services for all components
   - `kubectl get ingress` -- Ingress configured with correct rules

**Part 4: End-to-End Verification**

9. Run the database migration (if your app requires one):
   - How would you run a one-time migration in K8s? (Hint: `kubectl exec` into the api-service Pod, or use a K8s Job)
   - Alternatively, if your api-service runs migrations on startup, check the logs

10. Test the full task flow:
    - Create a task: `curl -X POST https://flowforge.local/api/tasks -H "Content-Type: application/json" -d '{"title": "Test task", "description": "Testing K8s deployment"}' -k`
    - List tasks: `curl https://flowforge.local/api/tasks -k`
    - Wait a moment for the worker to process
    - Check the task status: `curl https://flowforge.local/api/tasks/<id> -k`
    - Check worker logs: `kubectl logs <worker-pod>` -- did it pick up and process the task?

11. Test data persistence:
    - Create some tasks
    - Delete the PostgreSQL Pod: `kubectl delete pod <postgres-pod>`
    - Wait for the Deployment to recreate it
    - Query tasks again -- are they still there? (They should be, thanks to the PVC)

**Part 5: Document Your Deployment**

12. Create a deployment document (or mental checklist) answering:
    - What's the correct order to deploy FlowForge on K8s?
    - What are all the manifests needed?
    - What's the verification step for each component?
    - How long does it take from clean cluster to working system?
    - What are the most common issues you encountered?

### Expected Outcome

- Complete FlowForge stack running on Kind: PostgreSQL (with PVC), api-service (2 replicas), worker-service (1 replica), Ingress
- End-to-end task flow verified: create → process → query
- Data persists across PostgreSQL Pod restarts
- All manifests organized in a `k8s/` directory

### Checkpoint Questions

- Starting from a clean Kind cluster, can you deploy everything from manifests in under 15 minutes?
- Can you explain the PVC → PV → StorageClass relationship?
- What happens to data in a PVC when the Pod using it is deleted? When the PVC is deleted?
- If a Pod is stuck in Pending, what's the first thing you check? (Hint: `kubectl describe pod` events)
- Can you draw the network path from an external curl request to the worker processing a task?
- How does this K8s deployment compare to `docker compose up` from Module 4? What's gained? What's more complex?

---

## What's Next?

In [Lab 05](lab-05-eks.md), you'll take these same manifests and deploy FlowForge to AWS EKS -- a production-grade managed Kubernetes cluster.
