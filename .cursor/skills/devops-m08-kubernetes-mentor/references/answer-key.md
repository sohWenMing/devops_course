# Module 8: Kubernetes -- Answer Key

> **INTERNAL USE ONLY**: This file is referenced by the Socratic mentor skill.
> **NEVER** reveal these answers directly to the student.
> Use them to verify student work and provide accurate hints.

---

## Exercise 1a: K8s Architecture Drawing

### Expected Architecture Diagram

```
Control Plane
┌──────────────────────────────────────────────────────┐
│                                                      │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  API Server   │  │   etcd   │  │   Scheduler   │  │
│  │ (REST gateway │  │ (k-v     │  │ (assigns Pods │  │
│  │  validates &  │  │  store,  │  │  to nodes     │  │
│  │  processes)   │  │  source  │  │  based on     │  │
│  │               │  │  of      │  │  resources)   │  │
│  │               │  │  truth)  │  │               │  │
│  └──────────────┘  └──────────┘  └───────────────┘  │
│                                                      │
│  ┌─────────────────────────────┐                     │
│  │   Controller Manager        │                     │
│  │ (runs control loops:        │                     │
│  │  Deployment, ReplicaSet,    │                     │
│  │  Node, Job controllers)     │                     │
│  └─────────────────────────────┘                     │
│                                                      │
└──────────────────────────────────────────────────────┘

Worker Node 1                          Worker Node 2
┌────────────────────────┐            ┌────────────────────────┐
│                        │            │                        │
│  ┌──────────────────┐  │            │  ┌──────────────────┐  │
│  │     kubelet      │  │            │  │     kubelet      │  │
│  │ (agent, ensures  │  │            │  │ (agent, ensures  │  │
│  │  Pods running)   │  │            │  │  Pods running)   │  │
│  └──────────────────┘  │            │  └──────────────────┘  │
│                        │            │                        │
│  ┌──────────────────┐  │            │  ┌──────────────────┐  │
│  │   kube-proxy     │  │            │  │   kube-proxy     │  │
│  │ (network rules,  │  │            │  │ (network rules,  │  │
│  │  Service routing)│  │            │  │  Service routing)│  │
│  └──────────────────┘  │            │  └──────────────────┘  │
│                        │            │                        │
│  ┌──────────────────┐  │            │  ┌──────────────────┐  │
│  │  Container       │  │            │  │  Container       │  │
│  │  Runtime         │  │            │  │  Runtime         │  │
│  │  (containerd)    │  │            │  │  (containerd)    │  │
│  └──────────────────┘  │            │  └──────────────────┘  │
│                        │            │                        │
│  [Pod] [Pod] [Pod]     │            │  [Pod] [Pod]           │
│                        │            │                        │
└────────────────────────┘            └────────────────────────┘
```

### kubectl apply Lifecycle (Expected 7+ Steps)

1. `kubectl` sends HTTP POST to the **API server** with the Deployment YAML
2. **API server** validates the request (auth, admission controllers), then writes the Deployment object to **etcd**
3. **Deployment controller** (in controller-manager) watches etcd, sees new Deployment, creates a **ReplicaSet** object
4. **ReplicaSet controller** watches etcd, sees new ReplicaSet, creates **Pod** objects (desired - actual = Pods to create)
5. **Scheduler** watches etcd for unassigned Pods, evaluates nodes (resources, affinity, taints), assigns Pods to nodes
6. **kubelet** on assigned node watches API server, sees new Pod assignment, tells **container runtime** (containerd) to pull image and start containers
7. **kube-proxy** on all nodes updates iptables/IPVS rules for any Services that match the Pod's labels
8. kubelet reports Pod status back to API server, which updates etcd

### Component Failure Scenarios

- **etcd down**: No new changes can be saved. Existing Pods keep running (kubelet has cached state), but no new deployments, scaling, or scheduling works. This is the worst failure.
- **Scheduler down**: Existing Pods keep running. New Pods stay in Pending (no node assignment). Existing Pods that crash will be recreated by ReplicaSet but stay Pending.
- **kubelet crash on a node**: Pods on that node keep running (container runtime continues). After ~40s, node status becomes NotReady. Controller-manager marks Pods as Unknown. After 5 minutes (default), Pods are rescheduled to other nodes.

### Module Analogies

- kubelet ↔ systemd (Module 1) -- ensures processes/containers are running
- kube-proxy ↔ iptables/nginx (Module 2) -- routes network traffic
- etcd ↔ PostgreSQL (Module 3) -- stores state persistently
- container runtime ↔ Docker daemon (Module 4) -- runs containers
- API server ↔ api-service REST API (Module 3) -- accepts and processes requests

---

## Exercise 1b: Kind Cluster Setup

### Installation Commands

```bash
# Install kubectl (Ubuntu)
sudo apt-get update && sudo apt-get install -y kubectl
# OR
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify
kubectl version --client

# Install Kind
# For Linux AMD64:
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verify
kind version
```

### Create Default Cluster

```bash
kind create cluster
# Output: Creating cluster "kind" ...

kubectl cluster-info
# Kubernetes control plane is running at https://127.0.0.1:xxxxx
# CoreDNS is running at https://127.0.0.1:xxxxx/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

kubectl get nodes
# NAME                 STATUS   ROLES           AGE   VERSION
# kind-control-plane   Ready    control-plane   60s   v1.27.3

docker ps
# Shows: kindest/node container running as kind-control-plane
```

### Multi-Node Kind Config

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
  - role: worker
  - role: worker
```

```bash
# Delete default and create multi-node
kind delete cluster
kind create cluster --config kind-config.yaml

kubectl get nodes
# NAME                 STATUS   ROLES           AGE   VERSION
# kind-control-plane   Ready    control-plane   90s   v1.27.3
# kind-worker          Ready    <none>          60s   v1.27.3
# kind-worker2         Ready    <none>          60s   v1.27.3

docker ps
# Shows 3 containers: kind-control-plane, kind-worker, kind-worker2

# kube-system pods
kubectl get pods -n kube-system
# coredns-xxx-xxx         (Deployment - DNS resolution)
# etcd-kind-control-plane (Static Pod - state store)
# kube-apiserver-kind-control-plane (Static Pod)
# kube-controller-manager-kind-control-plane (Static Pod)
# kube-proxy-xxxxx        (DaemonSet - runs on every node)
# kube-proxy-yyyyy
# kube-proxy-zzzzz
# kube-scheduler-kind-control-plane (Static Pod)
# kindnet-xxxxx           (DaemonSet - Kind's CNI plugin)
```

### Load Images

```bash
# Build images first (from Module 4)
docker build -t flowforge/api-service:latest ./project/api-service/
docker build -t flowforge/worker-service:latest ./project/worker-service/

# Load into Kind
kind load docker-image flowforge/api-service:latest
kind load docker-image flowforge/worker-service:latest
kind load docker-image postgres:15-alpine
```

---

## Exercise 2a: Pod Manifest

### Complete Pod Manifest

```yaml
# pod-api-service.yaml
apiVersion: v1
kind: Pod
metadata:
  name: api-service
  labels:
    app: api-service
    component: api
spec:
  containers:
    - name: api-service
      image: flowforge/api-service:latest
      imagePullPolicy: IfNotPresent   # Important for Kind (local images)
      ports:
        - containerPort: 8080
          name: http
      env:
        - name: DB_HOST
          value: "postgresql"
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: "flowforge"
        - name: DB_USER
          value: "flowforge"
        - name: DB_PASSWORD
          value: "password123"
        - name: SERVER_PORT
          value: "8080"
        - name: LOG_LEVEL
          value: "info"
```

### Expected Commands and Output

```bash
kubectl apply -f pod-api-service.yaml
# pod/api-service created

kubectl get pods -w
# NAME          READY   STATUS              RESTARTS   AGE
# api-service   0/1     ContainerCreating   0          2s
# api-service   0/1     Running             0          5s
# (or CrashLoopBackOff if no database)

kubectl describe pod api-service
# Events:
#   Normal  Scheduled  default-scheduler  Successfully assigned default/api-service to kind-worker
#   Normal  Pulled     kubelet            Container image "flowforge/api-service:latest" already present
#   Normal  Created    kubelet            Created container api-service
#   Normal  Started    kubelet            Started container api-service

kubectl logs api-service
# (Go application output - connection errors if no database)

kubectl exec -it api-service -- /bin/sh
# / # hostname
# api-service
# / # env | grep DB
# DB_HOST=postgresql
# ...
# / # exit

kubectl delete pod api-service
# pod "api-service" deleted

kubectl get pods
# No resources found in default namespace.
# (Nothing recreates the Pod - that's the point)
```

---

## Exercise 2b: Deployment Manifests

### api-service Deployment

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  labels:
    app: api-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-service
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: api-service
        component: api
    spec:
      containers:
        - name: api-service
          image: flowforge/api-service:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
              name: http
          env:
            - name: DB_HOST
              value: "postgresql"
            - name: DB_PORT
              value: "5432"
            - name: DB_NAME
              value: "flowforge"
            - name: DB_USER
              value: "flowforge"
            - name: DB_PASSWORD
              value: "password123"
            - name: SERVER_PORT
              value: "8080"
            - name: LOG_LEVEL
              value: "info"
```

### worker-service Deployment

```yaml
# worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-service
  labels:
    app: worker-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: worker-service
  template:
    metadata:
      labels:
        app: worker-service
        component: worker
    spec:
      containers:
        - name: worker-service
          image: flowforge/worker-service:latest
          imagePullPolicy: IfNotPresent
          env:
            - name: DB_HOST
              value: "postgresql"
            - name: DB_PORT
              value: "5432"
            - name: DB_NAME
              value: "flowforge"
            - name: DB_USER
              value: "flowforge"
            - name: DB_PASSWORD
              value: "password123"
            - name: POLL_INTERVAL
              value: "5s"
            - name: LOG_LEVEL
              value: "info"
```

### Scaling and Rolling Update Commands

```bash
# Apply
kubectl apply -f api-deployment.yaml
kubectl apply -f worker-deployment.yaml

# Observe
kubectl get deployments
# NAME             READY   UP-TO-DATE   AVAILABLE   AGE
# api-service      2/2     2            2           30s
# worker-service   1/1     1            1           25s

kubectl get replicasets
# NAME                        DESIRED   CURRENT   READY   AGE
# api-service-7d9f8b6c5d      2         2         2       30s
# worker-service-5c8d9e7f3a   1         1         1       25s

kubectl get pods
# NAME                              READY   STATUS    RESTARTS   AGE
# api-service-7d9f8b6c5d-abc12      1/1     Running   0          30s
# api-service-7d9f8b6c5d-def34      1/1     Running   0          30s
# worker-service-5c8d9e7f3a-ghi56   1/1     Running   0          25s

# Scale
kubectl scale deployment api-service --replicas=5
kubectl get pods -w   # Watch 3 new Pods appear

kubectl scale deployment api-service --replicas=2
kubectl get pods -w   # Watch 3 Pods terminate

# Rolling update
kubectl set image deployment/api-service api-service=flowforge/api-service:v2
kubectl rollout status deployment api-service
# Waiting for deployment "api-service" rollout to finish: 1 out of 2 new replicas have been updated...
# deployment "api-service" successfully rolled out

kubectl get replicasets
# NAME                        DESIRED   CURRENT   READY   AGE
# api-service-7d9f8b6c5d      0         0         0       5m    (old)
# api-service-8e0g9c7d6e      2         2         2       30s   (new)

# Rollback
kubectl rollout history deployment api-service
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>

kubectl rollout undo deployment api-service
# deployment.apps/api-service rolled back

kubectl rollout undo deployment api-service --to-revision=1
# (rollback to specific revision)
```

---

## Exercise 3a: Services

### PostgreSQL Deployment + Service

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  labels:
    app: postgresql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
        - name: postgresql
          image: postgres:15-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: "flowforge"
            - name: POSTGRES_USER
              value: "flowforge"
            - name: POSTGRES_PASSWORD
              value: "password123"
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
spec:
  selector:
    app: postgresql
  ports:
    - port: 5432
      targetPort: 5432
  type: ClusterIP
```

### api-service ClusterIP + NodePort Services

```yaml
# api-service-svc.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api-service
  ports:
    - port: 80
      targetPort: 8080
      name: http
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: api-service-external
spec:
  selector:
    app: api-service
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080
      name: http
  type: NodePort
```

### DNS Resolution Tests

```bash
# Run debug pod
kubectl run dns-test --image=busybox:1.36 --rm -it -- sh

# Inside the pod:
/ # nslookup postgresql
# Server:    10.96.0.10
# Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local
# Name:      postgresql
# Address 1: 10.96.X.X postgresql.default.svc.cluster.local

/ # nslookup api-service
# Name:      api-service
# Address 1: 10.96.Y.Y api-service.default.svc.cluster.local

/ # nslookup postgresql.default.svc.cluster.local
# (same result, fully qualified)

/ # nslookup kubernetes
# Address 1: 10.96.0.1 kubernetes.default.svc.cluster.local

/ # cat /etc/resolv.conf
# nameserver 10.96.0.10
# search default.svc.cluster.local svc.cluster.local cluster.local
# ndots: 5

/ # wget -qO- api-service:80/health
# {"status":"ok"}

/ # nc -zv postgresql 5432
# postgresql (10.96.X.X:5432) open
```

---

## Exercise 3b: ConfigMaps

### ConfigMap Manifest

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flowforge-config
data:
  DB_HOST: "postgresql"
  DB_PORT: "5432"
  DB_NAME: "flowforge"
  DB_USER: "flowforge"
  WORKER_POLL_INTERVAL: "5s"
  LOG_LEVEL: "info"
  SERVER_PORT: "8080"
```

### Using ConfigMap in Deployment (envFrom)

```yaml
# In the Deployment container spec:
spec:
  containers:
    - name: api-service
      image: flowforge/api-service:latest
      envFrom:
        - configMapRef:
            name: flowforge-config
      # OR individual keys:
      env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: flowforge-config
              key: DB_HOST
```

---

## Exercise 3c: Secrets

### Secret Manifest

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: flowforge-secrets
type: Opaque
data:
  DB_PASSWORD: cGFzc3dvcmQxMjM=        # echo -n "password123" | base64
  POSTGRES_PASSWORD: cGFzc3dvcmQxMjM=   # same for postgres container
stringData:                              # Alternative: plain text (auto-encoded)
  API_KEY: "my-secret-api-key-123"
```

### Decode Secret

```bash
echo -n "password123" | base64
# cGFzc3dvcmQxMjM=

kubectl get secret flowforge-secrets -o yaml
# data:
#   DB_PASSWORD: cGFzc3dvcmQxMjM=

kubectl get secret flowforge-secrets -o jsonpath='{.data.DB_PASSWORD}' | base64 -d
# password123
```

### Using Secret in Deployment

```yaml
spec:
  containers:
    - name: api-service
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: flowforge-secrets
              key: DB_PASSWORD
```

---

## Exercise 4a: Namespaces

### Namespace Manifests

```yaml
# namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: flowforge-dev
---
apiVersion: v1
kind: Namespace
metadata:
  name: flowforge-staging
```

### Resource Quota

```yaml
# resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: flowforge-dev
spec:
  hard:
    pods: "10"
    requests.cpu: "2"
    requests.memory: "4Gi"
    limits.cpu: "4"
    limits.memory: "8Gi"
```

### Cross-Namespace DNS

```bash
# From a Pod in flowforge-dev, resolve staging service:
nslookup api-service.flowforge-staging.svc.cluster.local
# resolves to the ClusterIP of api-service in staging namespace
```

---

## Exercise 4b: Ingress

### NGINX Ingress Controller Installation (Kind)

```bash
# Apply nginx ingress controller for Kind
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for it to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Ingress Resource

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flowforge-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
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
          - path: /api(/|$)(.*)
            pathType: ImplementationSpecific
            backend:
              service:
                name: api-service
                port:
                  number: 80
          - path: /health
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
```

### TLS Setup

```bash
# Generate self-signed cert
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=flowforge.local/O=FlowForge"

# Create K8s TLS secret
kubectl create secret tls flowforge-tls --cert=tls.crt --key=tls.key

# Add to /etc/hosts
echo "127.0.0.1 flowforge.local" | sudo tee -a /etc/hosts

# Test
curl -k https://flowforge.local/api/health
curl -k https://flowforge.local/api/tasks

# Inspect TLS
openssl s_client -connect flowforge.local:443 -servername flowforge.local
```

---

## Exercise 4c: Full Deployment

### Complete Manifest Set (project/k8s/ directory)

Directory structure:
```
project/k8s/
  00-namespace.yaml
  01-configmap.yaml
  02-secret.yaml
  03-postgres-pvc.yaml
  04-postgres.yaml
  05-api-service.yaml
  06-worker-service.yaml
  07-ingress.yaml
```

### PersistentVolumeClaim

```yaml
# 03-postgres-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard   # Kind's default StorageClass
```

### PostgreSQL with PVC

```yaml
# 04-postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  labels:
    app: postgresql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
        - name: postgresql
          image: postgres:15-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: flowforge-config
                  key: DB_NAME
            - name: POSTGRES_USER
              valueFrom:
                configMapKeyRef:
                  name: flowforge-config
                  key: DB_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: flowforge-secrets
                  key: DB_PASSWORD
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
              subPath: pgdata    # Avoids "initdb: directory not empty"
      volumes:
        - name: postgres-storage
          persistentVolumeClaim:
            claimName: postgres-data
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
spec:
  selector:
    app: postgresql
  ports:
    - port: 5432
      targetPort: 5432
  type: ClusterIP
```

### Deploy Everything

```bash
# From clean Kind cluster with ingress port mappings:
kind create cluster --config kind-config.yaml

# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s

# Load images
kind load docker-image flowforge/api-service:latest
kind load docker-image flowforge/worker-service:latest
kind load docker-image postgres:15-alpine

# Apply all manifests
kubectl apply -f project/k8s/

# Verify
kubectl get all
kubectl get pvc
kubectl get ingress

# Test end-to-end
curl -k -X POST https://flowforge.local/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Test K8s","description":"Testing deployment"}'

curl -k https://flowforge.local/api/tasks

# Check worker
kubectl logs -l app=worker-service

# Test persistence
kubectl delete pod -l app=postgresql
# Wait for new Pod
kubectl get pods -w
# Query tasks again - they should still be there
curl -k https://flowforge.local/api/tasks
```

---

## Exercise 5a: EKS Terraform

### EKS Terraform Module

```hcl
# modules/eks/main.tf

# EKS Cluster IAM Role
resource "aws_iam_role" "eks_cluster" {
  name = "${var.project}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster.name
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = "${var.project}-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
  ]
}

# Node Group IAM Role
resource "aws_iam_role" "eks_nodes" {
  name = "${var.project}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# Managed Node Group
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = var.private_subnet_ids

  instance_types = [var.node_instance_type]

  scaling_config {
    desired_size = var.desired_nodes
    max_size     = var.max_nodes
    min_size     = var.min_nodes
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry,
  ]

  tags = var.tags
}

# OIDC Provider for IRSA
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# modules/eks/variables.tf
variable "project" {
  type    = string
  default = "flowforge"
}

variable "kubernetes_version" {
  type    = string
  default = "1.28"
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "node_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "desired_nodes" {
  type    = number
  default = 2
}

variable "min_nodes" {
  type    = number
  default = 1
}

variable "max_nodes" {
  type    = number
  default = 3
}

variable "tags" {
  type    = map(string)
  default = {}
}

# modules/eks/outputs.tf
output "cluster_name" {
  value = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "cluster_ca_certificate" {
  value = aws_eks_cluster.main.certificate_authority[0].data
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.eks.arn
}

output "oidc_provider_url" {
  value = replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")
}
```

### EKS Ingress (ALB)

```yaml
# ingress-eks.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flowforge-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  rules:
    - http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
```

### Configure kubectl for EKS

```bash
aws eks update-kubeconfig --name flowforge-cluster --region us-east-1
kubectl get nodes
# NAME                                       STATUS   ROLES    AGE   VERSION
# ip-10-0-1-xxx.ec2.internal                 Ready    <none>   5m    v1.28.x
# ip-10-0-2-yyy.ec2.internal                 Ready    <none>   5m    v1.28.x
```

### Cleanup Order

```bash
# 1. Delete K8s resources (this deletes the ALB)
kubectl delete -f k8s/

# 2. Wait for ALB to be fully deleted
aws elbv2 describe-load-balancers --query 'LoadBalancers[?contains(LoadBalancerName, `flowforge`)]'
# Should return empty

# 3. Destroy Terraform
terraform destroy
```

---

## Exercise 6: Broken Deployments

### Bug 1: ImagePullBackOff

**Root cause**: Image `flowforge/api-service:v2.1.0-rc3` doesn't exist.

```bash
kubectl get pods
# NAME                                   READY   STATUS             RESTARTS   AGE
# api-service-broken1-xxx                0/1     ImagePullBackOff   0          60s

kubectl describe pod api-service-broken1-xxx
# Events:
#   Warning  Failed     kubelet  Failed to pull image "flowforge/api-service:v2.1.0-rc3": 
#                                rpc error: code = NotFound desc = failed to pull and unpack image
#   Warning  Failed     kubelet  Error: ImagePullBackOff

# Fix: Change image to correct tag
kubectl set image deployment/api-service-broken1 api-service=flowforge/api-service:latest
```

### Bug 2: CrashLoopBackOff (Missing Env Var)

**Root cause**: Missing `DB_HOST` environment variable causes app to fail on startup.

```bash
kubectl get pods
# NAME                                      READY   STATUS             RESTARTS     AGE
# worker-service-broken2-xxx                0/1     CrashLoopBackOff   3 (20s ago)  90s

kubectl logs worker-service-broken2-xxx
# Error: required environment variable DB_HOST is not set
# (or) panic: failed to connect to database: dial tcp: lookup : no such host

kubectl logs worker-service-broken2-xxx --previous
# (same error from previous run)

kubectl describe pod worker-service-broken2-xxx
# State:       Waiting
#   Reason:    CrashLoopBackOff
# Last State:  Terminated
#   Reason:    Error
#   Exit Code: 1

# Fix: Add the missing env var (update Deployment or add ConfigMap)
kubectl edit deployment worker-service-broken2
# Add: env: - name: DB_HOST value: "postgresql"
```

### Bug 3: Service Selector Mismatch

**Root cause**: Service selector `app: api-svc` doesn't match Pod labels `app: api-service`.

```bash
kubectl get pods
# NAME                                   READY   STATUS    RESTARTS   AGE
# api-service-broken3-xxx                1/1     Running   0          60s   # Pod is fine!

kubectl get service api-service-broken3
# NAME                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
# api-service-broken3   ClusterIP   10.96.15.200   <none>        80/TCP    60s

kubectl get endpoints api-service-broken3
# NAME                  ENDPOINTS   AGE
# api-service-broken3   <none>      60s    # <--- EMPTY! No endpoints!

kubectl describe service api-service-broken3
# Selector:          app=api-svc     # <--- Wrong!

kubectl get pods --show-labels
# NAME                                   ...   LABELS
# api-service-broken3-xxx                ...   app=api-service   # <--- Doesn't match!

# Fix: Change Service selector to match Pod labels
kubectl edit service api-service-broken3
# Change selector from: app: api-svc
#                   to: app: api-service

kubectl get endpoints api-service-broken3
# NAME                  ENDPOINTS        AGE
# api-service-broken3   10.244.1.5:8080  5s   # Now has endpoints!
```

### Bug 4: PVC Wrong StorageClass

**Root cause**: PVC requests StorageClass `premium-ssd` which doesn't exist in Kind.

```bash
kubectl get pods
# NAME                               READY   STATUS    RESTARTS   AGE
# postgres-broken4-xxx               0/1     Pending   0          60s

kubectl describe pod postgres-broken4-xxx
# Events:
#   Warning  FailedScheduling  default-scheduler  
#     0/3 nodes are available: pod has unbound immediate PersistentVolumeClaims.

kubectl get pvc postgres-broken4
# NAME               STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# postgres-broken4   Pending                                       premium-ssd    60s

kubectl describe pvc postgres-broken4
# Events:
#   Warning  ProvisioningFailed  persistentvolume-controller  
#     storageclass.storage.k8s.io "premium-ssd" not found

kubectl get storageclasses
# NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
# standard (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  1h

# Fix: Change PVC StorageClass to 'standard' (or remove it to use default)
kubectl delete pvc postgres-broken4
# Edit the PVC YAML: change storageClassName to "standard"
kubectl apply -f fixed-pvc.yaml
```

---

## Kind vs EKS Comparison Table (Expected Answer)

| Aspect | Kind | EKS |
|--------|------|-----|
| Cluster creation time | ~60 seconds | 10-15 minutes |
| Cost | Free | ~$0.10/hr control plane + EC2 |
| Node type | Docker containers | EC2 instances (or Fargate) |
| Storage | Local path provisioner | EBS CSI driver (gp2/gp3) |
| Load balancer | NodePort / port-forward | AWS ALB/NLB |
| Manifest changes | N/A (baseline) | StorageClass, Ingress annotations |
| Networking | kindnet (simple bridge) | VPC CNI (Pods get VPC IPs) |
| Security (IAM) | N/A | IRSA, node roles, cluster roles |
| Upgrades | Delete and recreate | Rolling node group updates |
| Use case | Dev, CI, learning | Staging, production |
