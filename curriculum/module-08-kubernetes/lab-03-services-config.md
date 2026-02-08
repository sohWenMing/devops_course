# Lab 03: Services & Configuration -- Connecting FlowForge

> **Module**: 8 -- Kubernetes  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Lab 02 completed (Deployments for api-service and worker-service). Read the [Services](#), [ConfigMaps & Secrets](#) sections of the Module 8 README.

---

## Overview

Your Deployments exist, but the Pods can't find each other and have no real configuration. In this lab, you'll create Services for network connectivity, ConfigMaps for non-sensitive config, and Secrets for credentials -- turning isolated Pods into a connected system.

---

## Exercise 3a: Services -- Network Identity for Pods

### Objectives

- Create a ClusterIP Service for PostgreSQL (internal database access)
- Create a ClusterIP Service for api-service (internal inter-service access)
- Create a NodePort Service to expose api-service externally
- Test DNS resolution from inside Pods
- Understand the Service → Endpoints → Pod routing chain

### What You'll Do

**Part 1: PostgreSQL Service**

1. Before creating Services, you need a PostgreSQL Deployment. Create a Deployment for PostgreSQL:
   - Image: `postgres:15-alpine` (or the version you used in Module 4)
   - Replicas: 1
   - Environment variables: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (use literal values for now -- we'll move these to ConfigMaps/Secrets in exercises 3b and 3c)
   - Container port: 5432

2. Create a **ClusterIP** Service for PostgreSQL:
   - Service name: `postgresql` (this becomes the DNS name other Pods use to connect)
   - The Service's `selector` must match the labels on your PostgreSQL Pods
   - Port: 5432 (maps to container port 5432)
   - Type: ClusterIP (the default -- only accessible from within the cluster)

3. Verify the Service:
   - `kubectl get services` -- what ClusterIP was assigned?
   - `kubectl get endpoints postgresql` -- does it show the PostgreSQL Pod's IP? If not, why not? (Hint: check label selectors)
   - `kubectl describe service postgresql` -- read the Endpoints field

**Part 2: Internal API Service**

4. Create a **ClusterIP** Service for api-service:
   - Service name: `api-service`
   - Selector: must match your api-service Deployment's Pod labels
   - Port: 80 (external), targetPort: 8080 (or whatever port your api-service listens on)
   - Why use port 80 on the Service even though the container uses 8080?

5. Verify:
   - `kubectl get endpoints api-service` -- should show 2 IPs (since you have 2 replicas)
   - If you scale the Deployment to 3 replicas, what happens to the endpoints?

**Part 3: External Access via NodePort**

6. Create a **NodePort** Service to expose api-service externally:
   - You can create a second Service or modify the existing one
   - Type: NodePort
   - The NodePort range is 30000-32767. You can let K8s pick one or specify one.
   - Think: why would you have BOTH a ClusterIP and a NodePort Service for the same application?

7. Test external access:
   - For Kind, you need to map the NodePort to your host. Kind's default config doesn't expose NodePorts.
   - Alternative: use `kubectl port-forward service/api-service 8080:80` to tunnel traffic
   - Can you reach the api-service from your host machine?

**Part 4: DNS Resolution**

8. Test DNS resolution from inside a Pod:
   - Run a temporary debug Pod: `kubectl run dns-test --image=busybox:1.36 --rm -it -- sh`
   - Inside the Pod, run:
     - `nslookup postgresql` -- what IP does it resolve to?
     - `nslookup api-service` -- matches the ClusterIP?
     - `nslookup postgresql.default.svc.cluster.local` -- the fully qualified name
     - `nslookup kubernetes` -- what's this?
   - Look at `/etc/resolv.conf` inside the Pod. What DNS server is configured? What search domains?

9. Test actual connectivity:
   - From the debug Pod: `wget -qO- api-service:80/health` (or the appropriate endpoint)
   - From the debug Pod: try connecting to PostgreSQL: `nc -zv postgresql 5432` (or `telnet postgresql 5432`)
   - If it works, your Services are routing correctly

**Part 5: Understanding the Routing Chain**

10. Trace the full routing path:
    - When a Pod calls `api-service:80`, what happens step by step?
    - DNS resolution: CoreDNS → ClusterIP
    - kube-proxy: ClusterIP → Pod IP (via iptables/IPVS rules)
    - Draw this path and compare it to the nginx reverse proxy from Module 2

### Expected Outcome

- PostgreSQL Deployment + ClusterIP Service running and reachable
- api-service has both ClusterIP (internal) and NodePort (external) Services
- DNS resolution works inside Pods (`nslookup postgresql` resolves)
- Connectivity verified from inside the cluster

### Checkpoint Questions

- Can you explain the difference between ClusterIP, NodePort, and LoadBalancer Services?
- What happens if your Service selector doesn't match any Pod labels?
- Why does `kubectl get endpoints` show Pod IPs? What creates these Endpoints?
- Can you resolve a Service DNS name from inside a Pod? What's the full FQDN format?
- How does K8s DNS compare to the /etc/hosts and dig/nslookup work from Module 2?

---

## Exercise 3b: ConfigMaps -- Non-Sensitive Configuration

### Objectives

- Create ConfigMaps for FlowForge non-sensitive configuration
- Mount ConfigMap values as environment variables in Deployments
- Understand what happens when you change a ConfigMap (spoiler: Pods need restart)
- Compare ConfigMaps to the .env files from Module 3

### What You'll Do

**Part 1: Create ConfigMaps**

1. Identify which FlowForge configuration values are non-sensitive:
   - Database host (the Service name: `postgresql`)
   - Database port (`5432`)
   - Database name (`flowforge`)
   - Worker poll interval (e.g., `5s`)
   - Log level (e.g., `info`)
   - API service port (e.g., `8080`)
   
   Why are these NOT sensitive? What makes them different from passwords and API keys?

2. Create a ConfigMap manifest:
   - Use `kind: ConfigMap` with a `data` section containing key-value pairs
   - Give it a descriptive name like `flowforge-config`
   - Think: should you have one ConfigMap for all services or separate ones per service?

3. Apply the ConfigMap:
   - `kubectl apply -f <configmap.yaml>`
   - `kubectl get configmaps` -- is it there?
   - `kubectl describe configmap flowforge-config` -- can you see the values?

**Part 2: Mount as Environment Variables**

4. Update your Deployment manifests to reference the ConfigMap:
   - In the container spec, use `envFrom` to load all keys from the ConfigMap as env vars
   - OR use individual `env` entries with `valueFrom.configMapKeyRef` for specific keys
   - What's the difference between these two approaches? When would you use each?

5. Apply the updated Deployments:
   - `kubectl apply -f <api-deployment.yaml>`
   - Watch the Pods restart (why do they restart?)
   - Exec into a Pod and verify the environment variables are set: `kubectl exec <pod> -- env | grep DB`

**Part 3: ConfigMap Update Behavior**

6. Change a value in the ConfigMap (e.g., change `LOG_LEVEL` from `info` to `debug`):
   - `kubectl apply -f <updated-configmap.yaml>` (or `kubectl edit configmap flowforge-config`)
   - Check the running Pod's env vars: `kubectl exec <pod> -- env | grep LOG_LEVEL`
   - Did the value change? Why or why not?
   - How would you force the Pods to pick up the new value?

7. Understand the two ConfigMap consumption modes:
   - Environment variables: set at Pod creation, NEVER update without Pod restart
   - Volume mounts: files update eventually (kubelet sync period, typically ~1 minute)
   - Which mode did you use? What are the trade-offs of each?

### Expected Outcome

- A ConfigMap with FlowForge non-sensitive configuration
- Deployments updated to read config from ConfigMaps instead of hardcoded values
- Understanding that ConfigMap changes require Pod restarts for env var consumption

### Checkpoint Questions

- Can you create a ConfigMap from scratch without referencing your previous one?
- What happens if the ConfigMap referenced by a Pod doesn't exist? Will the Pod start?
- How is a K8s ConfigMap different from the `.env` file in Module 3 or `environment:` in docker-compose.yml?
- Can you change a ConfigMap value and have running Pods pick it up automatically? Under what conditions?

---

## Exercise 3c: Secrets -- Sensitive Configuration

### Objectives

- Create Kubernetes Secrets for database passwords and API keys
- Mount Secrets as environment variables in Deployments
- Understand that base64 is NOT encryption
- Discuss production alternatives for secret management

### What You'll Do

**Part 1: Create Secrets**

1. Identify sensitive values for FlowForge:
   - Database password
   - Database user (arguably sensitive)
   - Any API keys your services use
   - Why are these different from ConfigMap values?

2. Create a Secret manifest:
   - Values in the `data` field must be base64-encoded
   - Encode a value: `echo -n "mypassword" | base64`
   - Why `-n` with echo? What happens if you forget it?
   - Alternatively, use `stringData` for plain-text values (K8s encodes them for you)

3. Apply the Secret:
   - `kubectl apply -f <secret.yaml>`
   - `kubectl get secrets` -- what type is it?
   - `kubectl describe secret flowforge-secrets` -- notice the values are hidden in describe output

**Part 2: The base64 Illusion**

4. Prove that base64 is not encryption:
   - `kubectl get secret flowforge-secrets -o yaml` -- can you see the base64 values?
   - Decode one: `kubectl get secret flowforge-secrets -o jsonpath='{.data.DB_PASSWORD}' | base64 -d`
   - Anyone with `kubectl get secret` access can read your "secrets"
   - This is important: K8s Secrets provide a slightly better mechanism than ConfigMaps (separate RBAC, not shown in describe), but they are NOT encrypted by default

5. Think about the implications:
   - If you commit the Secret YAML to Git, anyone with repo access can decode the passwords
   - If etcd is compromised, all Secrets are readable
   - What would you need to make Secrets truly secret?

**Part 3: Mount Secrets in Deployments**

6. Update your Deployment manifests to read from the Secret:
   - Use `env` entries with `valueFrom.secretKeyRef`
   - Replace the hardcoded `POSTGRES_PASSWORD` in both the PostgreSQL Deployment and the api/worker Deployments
   - Apply the updated manifests

7. Verify the Secrets are mounted:
   - `kubectl exec <pod> -- env | grep DB_PASSWORD` -- the value should be the decoded plain text (not base64)
   - Compare this to how Docker Compose handled secrets in Module 4

**Part 4: Production Secret Management Discussion**

8. Research and document the production alternatives (you don't need to implement these yet -- that's Module 10):
   - **etcd encryption at rest**: What does this protect against? What doesn't it protect against?
   - **External Secrets Operator**: How would it work with AWS Secrets Manager?
   - **Sealed Secrets (Bitnami)**: How does asymmetric encryption make Git-stored secrets safe?
   - **HashiCorp Vault**: When would you use this over AWS Secrets Manager?

9. Write a brief document (or add to your notes) answering:
   - "If I were deploying FlowForge to production today, how would I handle secrets?"
   - What's the minimum acceptable approach? What's the gold standard?

### Expected Outcome

- A Secret manifest with base64-encoded values
- Deployments reading sensitive config from Secrets (not hardcoded)
- Understanding that base64 is encoding, NOT encryption
- A written assessment of production secret management approaches

### Checkpoint Questions

- Can you create a Secret manifest from scratch?
- Can you decode a K8s Secret value from the command line?
- Why are K8s Secrets not truly secret by default? What additional steps are needed?
- What's the difference between `data` (base64) and `stringData` (plain text) in a Secret manifest?
- If you need to rotate a database password, what steps would you take in K8s?
- How does the K8s Secret approach compare to the environment variables in Module 3's `.env` files?

---

## What's Next?

In [Lab 04](lab-04-namespaces-ingress.md), you'll organize your deployments with Namespaces, expose them through an Ingress controller with TLS, and do a full end-to-end deployment of FlowForge on Kind.
