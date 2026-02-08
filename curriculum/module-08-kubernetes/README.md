# Module 8: Kubernetes -- Orchestrating FlowForge at Scale

> **Duration**: Weeks 13-14  
> **Prerequisites**: Modules 1-7 completed (Linux, Networking, Go App, Docker, AWS, Terraform, CI/CD)  
> **Link forward**: "Now we need to see what's happening inside -- monitoring"  
> **Link back**: "Docker Compose got you far, but what happens when containers crash at 3am with nobody watching?"

---

## Why Kubernetes?

In Module 4 you ran FlowForge with `docker compose up`. It worked great on your laptop. But in production you need:

- **Self-healing**: When a container crashes, something restarts it automatically
- **Scaling**: Run 10 copies of api-service during peak hours, 2 at night
- **Rolling updates**: Deploy a new version without any downtime
- **Service discovery**: Containers find each other by name, not IP address
- **Configuration management**: Change settings without rebuilding images
- **Secret management**: Handle credentials safely across the cluster

Docker Compose handles none of these in production. Kubernetes handles all of them.

> **Architecture Thinking**: Before diving into K8s, ask yourself: "Could I solve my problem with just Docker Compose and a process supervisor?" For many apps, the answer is yes. Kubernetes adds operational complexity. The question isn't "should I use K8s?" -- it's "do I have problems that justify the complexity K8s adds?" FlowForge with 2 services and a database? Probably overkill locally. FlowForge with 50 workers, 10 API replicas, auto-scaling, and zero-downtime deploys? Now you need an orchestrator.

---

## Kubernetes Architecture

Kubernetes is a cluster -- a group of machines (called **nodes**) managed by a **control plane**. Every K8s cluster has two layers:

### Control Plane Components

The control plane makes global decisions about the cluster (e.g., scheduling), detects and responds to cluster events (e.g., starting a new Pod when a Deployment's replicas field is unsatisfied).

| Component | Role | Analogy |
|-----------|------|---------|
| **kube-apiserver** | The front door to the cluster. Every `kubectl` command, every internal component communication goes through the API server. It validates and processes REST requests, then stores the result in etcd. | The reception desk -- everything goes through here first |
| **etcd** | A distributed key-value store that holds ALL cluster state. If etcd dies and you have no backup, your cluster's desired state is gone. | The filing cabinet -- the single source of truth |
| **kube-scheduler** | Watches for newly created Pods with no assigned node, selects a node for them to run on based on resource requirements, affinity rules, and constraints. | The office manager assigning desks to new employees |
| **kube-controller-manager** | Runs controller loops: Deployment controller, ReplicaSet controller, Node controller, Job controller, etc. Each controller watches the current state and works toward the desired state. | The department managers who make sure things get done |

### Node Components

Every node (worker machine) runs these components:

| Component | Role | Analogy |
|-----------|------|---------|
| **kubelet** | An agent that runs on each node. It ensures containers described in PodSpecs are running and healthy. It communicates with the API server. | The local supervisor on each floor |
| **kube-proxy** | Maintains network rules on nodes. Implements the Service concept by routing traffic to the correct Pods. | The mail room -- routes packages to the right desk |
| **Container runtime** | The software that actually runs containers (containerd, CRI-O). Docker was once the default; now containerd is standard. | The actual office space where work happens |

### The Request Flow

When you run `kubectl apply -f deployment.yaml`, here's what happens:

1. `kubectl` sends a REST request to the **API server**
2. The API server validates the request and stores the desired state in **etcd**
3. The **Deployment controller** (inside controller-manager) notices a new Deployment and creates a ReplicaSet
4. The **ReplicaSet controller** notices the ReplicaSet needs Pods and creates Pod objects
5. The **scheduler** notices unassigned Pods and picks nodes for them
6. The **kubelet** on each selected node pulls the container image and starts the container
7. **kube-proxy** updates network rules so the Pod is reachable

Every step is **declarative**: you describe what you want, controllers work to make it happen.

> **Link back to Module 1**: Remember systemd's declarative unit files? "I want this service running." K8s takes the same idea to a cluster level: "I want 3 replicas of this container running, with these environment variables, reachable on this port."

> **Link back to Module 2**: The networking concepts from Module 2 -- DNS resolution, ports, load balancing, routing -- all reappear here. K8s has its own DNS (CoreDNS), its own load balancing (Services), and its own routing (kube-proxy + Ingress).

> **AWS SAA Tie-in**: EKS (Elastic Kubernetes Service) runs the control plane for you. You pay ~$0.10/hour for the control plane, and AWS handles etcd backups, API server availability, and control plane upgrades. You still manage your worker nodes (or use Fargate for serverless nodes). This maps to the SAA "managed services" design principle.

---

## Local Cluster Setup with Kind

**Kind** (Kubernetes IN Docker) runs K8s clusters using Docker containers as nodes. Each "node" is actually a Docker container running kubelet and a container runtime inside it.

### Why Kind?

- **Free**: No cloud costs. EKS control plane costs ~$0.10/hour ($73/month)
- **Fast**: Create a cluster in under 60 seconds
- **Realistic**: Same K8s APIs, same manifests, same kubectl commands
- **Multi-node**: Can simulate multi-node clusters with a single Docker host
- **Disposable**: Delete and recreate in seconds

### How Kind Works

```
Your Laptop
├── Docker
│   ├── kind-control-plane  (container running: kubelet, API server, etcd, scheduler, controller-manager)
│   ├── kind-worker         (container running: kubelet, kube-proxy, container runtime)
│   └── kind-worker2        (container running: kubelet, kube-proxy, container runtime)
```

Each Docker container pretends to be a full K8s node. Inside each container, kubelet manages Pods using a nested container runtime. It's containers all the way down.

> **Link back to Module 4**: Kind is the reason Docker knowledge matters for K8s. The "nodes" are Docker containers. If Docker is broken, Kind is broken. The networking between "nodes" uses Docker networks. The container images your Pods run are pulled into the Kind nodes (Docker containers within Docker containers).

> **Architecture Thinking**: Kind is for development and testing. For production, you'd use EKS, GKE, AKS, or a self-managed cluster (kubeadm). The manifests you write for Kind work identically on EKS -- that's the power of the K8s API abstraction.

---

## Pods

A **Pod** is the smallest deployable unit in Kubernetes. It's a wrapper around one or more containers that:

- Share a network namespace (same IP address, same localhost)
- Share storage volumes
- Have a shared lifecycle (created and destroyed together)

### Why Not Just "Containers"?

K8s doesn't manage containers directly. The Pod abstraction allows:

- **Sidecar patterns**: A main container + a logging agent container sharing a volume
- **Init containers**: Containers that run before the main container starts (e.g., database migration)
- **Shared networking**: Multiple containers in a Pod communicate over localhost

### Pod Lifecycle

Pods are **ephemeral**. They are born, they run, they die. They are never "repaired" -- they are replaced.

| Phase | Meaning |
|-------|---------|
| `Pending` | Pod accepted but containers not yet running (image pull, scheduling) |
| `Running` | At least one container is running |
| `Succeeded` | All containers exited with code 0 (common for Jobs) |
| `Failed` | At least one container exited with non-zero code |
| `Unknown` | Pod state cannot be determined (usually node communication failure) |

### Why You Rarely Create Pods Directly

If you create a Pod directly and it crashes, nothing restarts it. If the node it runs on dies, the Pod is gone forever. Pods are cattle, not pets -- you manage them through higher-level abstractions (Deployments, StatefulSets, Jobs).

> **Link back to Module 1**: Remember processes in Linux? A Pod is like a process group -- related processes that share resources. And just like you used systemd to ensure processes restart on failure, you'll use Deployments to ensure Pods restart on failure.

---

## Deployments & ReplicaSets

A **Deployment** is the primary way you run stateless applications in Kubernetes. It manages a **ReplicaSet**, which in turn manages Pods.

```
Deployment (desired state: 3 replicas, image: api-service:v2)
  └── ReplicaSet (maintains 3 Pods)
       ├── Pod (api-service:v2)
       ├── Pod (api-service:v2)
       └── Pod (api-service:v2)
```

### What Deployments Give You

1. **Declarative updates**: Change the image tag, K8s handles the rest
2. **Rolling updates**: Replace Pods gradually, not all at once
3. **Rollback**: Revert to any previous revision
4. **Scaling**: Change replica count up or down
5. **Self-healing**: Replace crashed/deleted Pods automatically

### Rolling Update Strategy

When you change the image tag in a Deployment, K8s performs a rolling update:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # At most 1 extra Pod during update
      maxUnavailable: 0   # Never have fewer than desired Pods
```

- **maxSurge**: How many Pods above the desired count can exist during the update. `1` means if you want 3 replicas, you can briefly have 4.
- **maxUnavailable**: How many Pods below the desired count are allowed. `0` means all 3 replicas must be running at all times -- the new Pod must be Ready before an old one is killed.

The process:
1. Create a new ReplicaSet with the new image
2. Scale up the new ReplicaSet (respecting maxSurge)
3. Scale down the old ReplicaSet (respecting maxUnavailable)
4. Repeat until all Pods run the new image
5. Old ReplicaSet stays around (with 0 replicas) for rollback

> **Architecture Thinking**: `maxSurge: 1, maxUnavailable: 0` is the safest strategy -- zero downtime, but slower. `maxSurge: 0, maxUnavailable: 1` uses fewer resources but has reduced capacity during the update. What's right for FlowForge api-service? What about worker-service where temporary reduced capacity might cause task processing delays?

> **Link forward to Module 9**: How do you know a rolling update isn't introducing errors? Monitoring. In Module 9, you'll set up dashboards that show error rates spiking during bad deployments, allowing you to rollback before users notice.

---

## Services

Pods get random IP addresses that change every time they restart. **Services** provide a stable network identity for a set of Pods.

### Service Types

| Type | Reachable From | Use Case |
|------|---------------|----------|
| **ClusterIP** | Inside the cluster only | Internal communication: api-service → PostgreSQL |
| **NodePort** | External via `<NodeIP>:<NodePort>` (30000-32767) | Development/testing external access |
| **LoadBalancer** | External via a cloud load balancer | Production external access (creates an AWS ALB/NLB) |

### How Services Work

A Service selects Pods using **label selectors**:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api-service    # Matches Pods with this label
  ports:
    - port: 80          # The Service port
      targetPort: 8080  # The container port
  type: ClusterIP
```

kube-proxy watches for Services and Endpoints, then configures iptables/IPVS rules on each node to route traffic to the correct Pods. The traffic path:

1. A Pod calls `api-service:80` (or `api-service.default.svc.cluster.local:80`)
2. CoreDNS resolves this to the Service's ClusterIP (e.g., `10.96.0.15`)
3. kube-proxy's iptables/IPVS rules load-balance the request to one of the matching Pods' actual IPs

### DNS Resolution

Every Service gets a DNS entry:

```
<service-name>.<namespace>.svc.cluster.local
```

Within the same namespace, you can use just the service name: `api-service`. Across namespaces: `api-service.production.svc.cluster.local`.

> **Link back to Module 2**: This is the same DNS concept from Module 2, but inside the cluster. Remember `dig` and `/etc/hosts`? K8s has CoreDNS doing the same job -- resolving names to IPs. The difference is that these IPs are virtual (ClusterIPs) and the routing is handled by kube-proxy.

> **AWS SAA Tie-in**: A LoadBalancer Service on EKS creates an AWS Elastic Load Balancer (Classic by default, or ALB/NLB with the AWS Load Balancer Controller). This maps directly to the ALB/NLB concepts in the SAA exam. In production, you'd typically use an Ingress with the AWS Load Balancer Controller rather than LoadBalancer Services.

---

## ConfigMaps & Secrets

### ConfigMaps

A **ConfigMap** holds non-sensitive configuration data as key-value pairs. You mount them into Pods as environment variables or files.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flowforge-config
data:
  DB_HOST: "postgresql"
  WORKER_POLL_INTERVAL: "5s"
  LOG_LEVEL: "info"
```

**Two ways to consume ConfigMaps**:

1. **Environment variables**: Each key becomes an env var in the container
2. **Volume mount**: ConfigMap data is mounted as files in a directory

**Important behavior**: If you change a ConfigMap, existing Pods do NOT automatically pick up the change. You need to restart (or roll) the Pods. Volume-mounted ConfigMaps eventually update (kubelet sync period), but env vars never update without a Pod restart.

### Secrets

A **Secret** is like a ConfigMap but intended for sensitive data. The YAML stores values as base64-encoded strings.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: flowforge-secrets
type: Opaque
data:
  DB_PASSWORD: cGFzc3dvcmQxMjM=    # base64 of "password123"
  API_KEY: c2VjcmV0LWtleS0xMjM=     # base64 of "secret-key-123"
```

### Base64 Is NOT Encryption

This is critical to understand: **base64 encoding is not security**. Anyone with `kubectl get secret -o yaml` access can decode the values instantly:

```bash
echo "cGFzc3dvcmQxMjM=" | base64 --decode
# Output: password123
```

K8s Secrets are "secret" in name only, by default. They're stored unencrypted in etcd.

### Production Secret Management

For real security, you need additional measures:

| Approach | How It Works |
|----------|-------------|
| **etcd encryption at rest** | Encrypt Secrets stored in etcd (EKS does this by default with AWS KMS) |
| **External Secrets Operator** | Sync secrets from AWS Secrets Manager, HashiCorp Vault, etc. into K8s Secrets |
| **Sealed Secrets** | Encrypt secrets so they can be safely stored in Git; only the cluster can decrypt |
| **CSI Secrets Store Driver** | Mount external secrets directly as volumes, bypassing K8s Secrets entirely |

> **Link back to Module 3**: Remember the 12-Factor App principle of storing config in the environment? ConfigMaps and Secrets are K8s's implementation of that principle. The same environment variables you defined in `.env` files in Module 3 and `docker-compose.yml` in Module 4 now live in ConfigMaps and Secrets.

> **Link forward to Module 10**: In the Security module, you'll migrate from base64 K8s Secrets to AWS Secrets Manager with the External Secrets Operator. That's where real secret management begins.

---

## Namespaces

A **Namespace** is a virtual cluster within a K8s cluster. It provides:

- **Isolation**: Resources in different namespaces don't see each other by default
- **Access control**: RBAC can restrict users/services to specific namespaces
- **Resource quotas**: Limit CPU/memory usage per namespace
- **Organization**: Separate environments (dev, staging, production) or teams

### Default Namespaces

| Namespace | Purpose |
|-----------|---------|
| `default` | Where resources go if you don't specify a namespace |
| `kube-system` | K8s system components (CoreDNS, kube-proxy, etc.) |
| `kube-public` | Publicly readable resources (rarely used) |
| `kube-node-lease` | Node heartbeat leases |

### Cross-Namespace Communication

Services in different namespaces can still communicate using the full DNS name:

```
api-service.production.svc.cluster.local
```

This means namespaces provide organizational isolation, not network isolation. For true network isolation, you need **NetworkPolicies** (Module 10).

### Resource Quotas

You can limit resources per namespace:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: dev
spec:
  hard:
    pods: "20"
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
```

> **Architecture Thinking**: When should you use namespaces vs separate clusters? Namespaces are lighter but share the same control plane, nodes, and network. Separate clusters are more isolated but more expensive and harder to manage. For FlowForge dev/staging, namespaces are fine. For production vs development, many organizations use separate clusters.

---

## Ingress

A **Service** of type LoadBalancer creates one load balancer per Service. If you have 10 services, you get 10 load balancers -- expensive. **Ingress** solves this by providing a single entry point with routing rules.

### How Ingress Works

Ingress requires two things:

1. **Ingress Controller**: A reverse proxy running in the cluster (nginx, Traefik, HAProxy, AWS ALB). It watches for Ingress resources and configures itself accordingly.
2. **Ingress Resource**: A YAML manifest defining routing rules.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flowforge-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - flowforge.local
      secretName: flowforge-tls
  rules:
    - host: flowforge.local
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
```

### Path-Based Routing

Ingress routes traffic based on the URL path:

- `/api/*` → api-service
- `/health` → api-service (health endpoint)
- `/` → frontend (if you had one)

### TLS Termination

Ingress handles TLS (HTTPS) at the edge. Traffic from the client to the Ingress Controller is encrypted (HTTPS). Traffic from the Ingress Controller to the Pods is typically unencrypted (HTTP) within the cluster network.

The TLS certificate is stored as a K8s Secret and referenced by the Ingress resource.

> **Link back to Module 2**: Remember nginx as a reverse proxy in Module 2's Lab 3c? The nginx Ingress Controller is the same concept, but managed by K8s. Path-based routing, TLS termination, load balancing -- all the same ideas from Module 2, automated by K8s.

> **AWS SAA Tie-in**: On EKS, you'd typically use the **AWS Load Balancer Controller** with the `ALBIngressClass`. This creates an AWS Application Load Balancer for your Ingress, giving you path-based routing, TLS termination with ACM certificates, WAF integration, and more. The SAA exam tests heavily on ALB vs NLB vs CLB, and the Ingress → ALB mapping is a common architecture pattern.

---

## PersistentVolumes & PersistentVolumeClaims

Containers have ephemeral storage. When a Pod dies, its filesystem is gone. For databases like PostgreSQL, you need persistent storage.

### The Storage Abstraction

K8s separates storage provisioning from consumption:

| Resource | Who Creates It | Purpose |
|----------|---------------|---------|
| **PersistentVolume (PV)** | Admin or dynamic provisioner | A piece of storage in the cluster (an AWS EBS volume, local disk, NFS share) |
| **PersistentVolumeClaim (PVC)** | Developer/user | A request for storage ("I need 10Gi of fast storage") |
| **StorageClass** | Admin | Defines HOW storage is provisioned (EBS gp3, io1, local, etc.) |

The flow:
1. Admin creates a StorageClass (or uses the default)
2. Developer creates a PVC requesting storage
3. K8s matches the PVC to an existing PV (or dynamically provisions one)
4. Developer mounts the PVC in their Pod

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

### Access Modes

| Mode | Abbreviation | Meaning |
|------|-------------|---------|
| ReadWriteOnce | RWO | Mounted read-write by a single node |
| ReadOnlyMany | ROX | Mounted read-only by many nodes |
| ReadWriteMany | RWX | Mounted read-write by many nodes (requires NFS or similar) |

> **Link back to Module 4**: Remember Docker volumes? PVCs are the K8s equivalent. In `docker-compose.yml`, you wrote `volumes: - postgres-data:/var/lib/postgresql/data`. In K8s, that named volume becomes a PVC mounted at the same path. The concept is identical; only the abstraction layer changes.

> **AWS SAA Tie-in**: On EKS, PersistentVolumes typically map to **EBS volumes** (gp3, io1, io2). The EBS CSI driver dynamically provisions EBS volumes for PVCs. StorageClasses map to EBS volume types. This is directly testable on the SAA exam: "Which storage type for a database?" → EBS gp3 or io1, provisioned via K8s StorageClass.

---

## EKS -- Elastic Kubernetes Service

EKS is AWS's managed Kubernetes offering. Understanding what's managed and what's not is critical.

### What AWS Manages (Control Plane)

- **API server**: Highly available, multi-AZ
- **etcd**: Replicated, backed up, encrypted
- **Scheduler and controller-manager**: Running and monitored
- **Control plane upgrades**: AWS handles K8s version upgrades
- **etcd backups**: Automatic

### What You Manage (Data Plane)

- **Worker nodes**: EC2 instances or Fargate tasks running your Pods
- **Node upgrades**: You update the AMI and roll nodes
- **Networking**: VPC, subnets, security groups
- **Add-ons**: CoreDNS, kube-proxy, VPC CNI plugin, EBS CSI driver
- **Ingress**: AWS Load Balancer Controller
- **Your applications**: Deployments, Services, etc.

### Node Types

| Type | Pros | Cons |
|------|------|------|
| **Managed Node Groups** | AWS handles EC2 provisioning, AMI updates, draining | Less control over instance configuration |
| **Self-Managed Nodes** | Full control over EC2 instances | You handle everything: AMI, scaling, draining |
| **Fargate** | Serverless -- no nodes to manage | Higher per-Pod cost, some K8s features unavailable (DaemonSets, HostPort) |

### Kind vs EKS

| Aspect | Kind | EKS |
|--------|------|-----|
| Cost | Free | ~$0.10/hr control plane + EC2 nodes |
| Nodes | Docker containers | EC2 instances or Fargate |
| Storage | Local (hostPath) | EBS, EFS, FSx |
| Load Balancer | NodePort/port-forward | AWS ALB/NLB via Load Balancer Controller |
| Networking | Docker bridge network | AWS VPC CNI (Pods get real VPC IPs) |
| Use case | Development, CI testing | Staging, production |

The beautiful thing: **your manifests are almost identical**. A Deployment that runs on Kind runs on EKS. The only differences are infrastructure-specific: StorageClasses, Ingress annotations, and load balancer types.

> **Link back to Module 5**: Your VPC, subnets, and security groups from Module 5 become the network foundation for EKS. The EKS cluster lives in your VPC, worker nodes run in your private subnets, and the API server endpoint can be public or private.

> **Link back to Module 6**: You'll add EKS to your Terraform modules. The `aws_eks_cluster` resource, node groups, IAM roles for service accounts (IRSA), and the VPC CNI all become Terraform-managed.

> **Link back to Module 7**: Your CI/CD pipeline from Module 7 will deploy to EKS. `kubectl apply` from GitHub Actions, using OIDC federation for authentication (no static credentials).

---

## Debugging Kubernetes

K8s has many moving parts. When things go wrong, systematic debugging is essential.

### The Debugging Toolkit

| Command | Purpose |
|---------|---------|
| `kubectl get pods` | See Pod status (Running, CrashLoopBackOff, ImagePullBackOff, Pending) |
| `kubectl describe pod <name>` | Detailed Pod info including events (scheduling, image pull, container start/crash) |
| `kubectl logs <pod>` | Container stdout/stderr (add `-p` for previous crashed container's logs) |
| `kubectl get events --sort-by=.lastTimestamp` | Cluster-wide events sorted by time |
| `kubectl exec -it <pod> -- /bin/sh` | Shell into a running container |
| `kubectl port-forward <pod> 8080:8080` | Tunnel local port to Pod port |

### Common Error Patterns

| Error | Meaning | First Thing to Check |
|-------|---------|---------------------|
| **ImagePullBackOff** | K8s can't pull the container image | Image name/tag typo? Registry auth? Image exists? |
| **CrashLoopBackOff** | Container starts then immediately exits | `kubectl logs` -- what error does the app print? Missing env var? Wrong command? |
| **Pending** | Pod can't be scheduled | `kubectl describe` -- insufficient resources? Node selector mismatch? PVC not bound? |
| **CreateContainerConfigError** | Problem with ConfigMap/Secret mount | Referenced ConfigMap/Secret exists? Key name correct? |
| **Service not reachable** | Network connectivity failure | Label selectors match? Port numbers correct? Pod actually running? |

### The Debugging Flowchart

```
Pod not working?
│
├── kubectl get pods
│   ├── Status: ImagePullBackOff → Check image name, tag, registry auth
│   ├── Status: Pending → kubectl describe pod → check events (scheduling, resources, PVC)
│   ├── Status: CrashLoopBackOff → kubectl logs (and kubectl logs -p for previous)
│   ├── Status: Running but not responding → kubectl exec + curl localhost, check readiness probe
│   └── Status: Unknown → Node problem → kubectl get nodes, kubectl describe node
│
├── Service not routing?
│   ├── kubectl get endpoints <service> → Any endpoints? (empty = selector mismatch)
│   ├── kubectl describe service → Check selector labels match Pod labels
│   └── kubectl exec <other-pod> -- nslookup <service> → DNS working?
│
└── Ingress not routing?
    ├── kubectl describe ingress → Check rules, backend services
    ├── kubectl get pods -n ingress-nginx → Ingress controller running?
    └── kubectl logs <ingress-controller-pod> → Upstream errors?
```

> **Link back to Module 1**: The debugging mindset from Module 1's broken server lab applies directly. Read logs first. Check the obvious things. Work systematically from the bottom up (container → Pod → Service → Ingress).

> **Link back to Module 4**: Remember `docker logs`, `docker exec`, `docker inspect`? The kubectl equivalents are `kubectl logs`, `kubectl exec`, `kubectl describe`. Same debugging approach, different tool.

---

## How It All Fits Together: FlowForge on Kubernetes

Here's the complete picture of FlowForge running on K8s:

```
Internet
  │
  ▼
Ingress (nginx)
  │ /api/* 
  ▼
Service: api-service (ClusterIP)
  │ load balances across
  ▼
Deployment: api-service (2 replicas)
  ├── Pod: api-service-abc123
  │   ├── env: DB_HOST from ConfigMap
  │   └── env: DB_PASSWORD from Secret
  └── Pod: api-service-def456
      ├── env: DB_HOST from ConfigMap
      └── env: DB_PASSWORD from Secret
  │
  │ PostgreSQL connection
  ▼
Service: postgresql (ClusterIP)
  │
  ▼
Deployment: postgresql (1 replica)
  └── Pod: postgresql-xyz789
      ├── env: POSTGRES_PASSWORD from Secret
      └── volume: PVC → PV (persistent data)
  │
  │ Tasks via PostgreSQL queue
  ▼
Service: worker-service (ClusterIP, headless)
  │
  ▼
Deployment: worker-service (1 replica)
  └── Pod: worker-service-uvw321
      ├── env: DB_HOST from ConfigMap
      └── env: DB_PASSWORD from Secret
```

Every component from Modules 1-7 converges here:
- **Module 1**: The Linux kernel running in each container
- **Module 2**: DNS resolution, port mapping, network routing
- **Module 3**: The Go services and PostgreSQL queue pattern
- **Module 4**: The Docker images running in each Pod
- **Module 5**: The AWS infrastructure (EKS, EBS, ALB)
- **Module 6**: The Terraform modules creating the EKS cluster
- **Module 7**: The CI/CD pipeline deploying to the cluster

> **Architecture Thinking**: Look at the diagram above. How many single points of failure can you identify? (Hint: PostgreSQL with 1 replica and a PVC). What would you change for true high availability? What's the minimum number of replicas for each component to survive a node failure?

---

## Labs in This Module

| Lab | Exercises | Focus |
|-----|-----------|-------|
| [Lab 01: Architecture & Kind](lab-01-architecture-kind.md) | 1a, 1b | K8s architecture understanding, local cluster setup |
| [Lab 02: Pods & Deployments](lab-02-pods-deployments.md) | 2a, 2b | Pod lifecycle, Deployments, ReplicaSets, rolling updates |
| [Lab 03: Services & Config](lab-03-services-config.md) | 3a, 3b, 3c | Service types, DNS, ConfigMaps, Secrets |
| [Lab 04: Namespaces & Ingress](lab-04-namespaces-ingress.md) | 4a, 4b, 4c | Namespace isolation, Ingress routing, full local deployment |
| [Lab 05: EKS](lab-05-eks.md) | 5a | Terraform EKS module, AWS Load Balancer Controller |
| [Lab 06: Broken K8s](lab-06-broken-k8s.md) | 6 | Debugging four broken K8s deployments |

---

## Key kubectl Commands Reference

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes

# Pods
kubectl get pods [-n namespace] [-o wide]
kubectl describe pod <name>
kubectl logs <pod> [-c container] [-f] [-p]
kubectl exec -it <pod> -- /bin/sh
kubectl delete pod <name>

# Deployments
kubectl get deployments
kubectl describe deployment <name>
kubectl scale deployment <name> --replicas=5
kubectl rollout status deployment <name>
kubectl rollout undo deployment <name>
kubectl rollout history deployment <name>

# Services
kubectl get services
kubectl describe service <name>
kubectl get endpoints <name>

# ConfigMaps & Secrets
kubectl get configmaps
kubectl describe configmap <name>
kubectl get secrets
kubectl get secret <name> -o jsonpath='{.data.KEY}' | base64 -d

# Namespaces
kubectl get namespaces
kubectl get all -n <namespace>

# Debugging
kubectl get events --sort-by=.lastTimestamp
kubectl top pods    # (requires metrics-server)
kubectl port-forward <pod> <local>:<remote>

# Apply/Delete
kubectl apply -f <file-or-directory>
kubectl delete -f <file-or-directory>
```

---

## Further Reading

- [Kubernetes Official Documentation](https://kubernetes.io/docs/home/)
- [Kubernetes Concepts](https://kubernetes.io/docs/concepts/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kind Quick Start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [EKS User Guide](https://docs.aws.amazon.com/eks/latest/userguide/)
- [Kubernetes The Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way) (advanced -- builds a cluster from scratch)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Kubernetes Networking Deep Dive](https://kubernetes.io/docs/concepts/services-networking/)
