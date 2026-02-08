# Module 8: Kubernetes -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 9.  
> No partial credit. No "I think so." Either you can do it or you can't.  
> If you can't, go back to the relevant lab and practice until you can.

---

## How to Use This Checklist

For each item:
1. Attempt it **without looking at notes, previous labs, or the internet**
2. If you succeed, mark it `[x]`
3. If you fail or need to look something up, mark it `[ ]` and go practice
4. Come back and try again until every box is checked

---

## K8s Architecture (Lab 01, Exercise 1a)

- [ ] I can draw the complete K8s architecture from memory (control plane + node components)
- [ ] I can explain the role of each control plane component: api-server, etcd, scheduler, controller-manager
- [ ] I can explain the role of each node component: kubelet, kube-proxy, container runtime
- [ ] I can trace the full lifecycle of `kubectl apply -f deployment.yaml` through all components (7+ steps)
- [ ] I can explain what happens if etcd goes down vs if the scheduler goes down
- [ ] I can explain the difference between the control plane and the data plane

---

## Local Cluster with Kind (Lab 01, Exercise 1b)

- [ ] I can create and destroy a Kind cluster from memory
- [ ] I can create a multi-node Kind cluster using a configuration file
- [ ] I can verify the cluster with `kubectl cluster-info` and `kubectl get nodes`
- [ ] I can identify all system Pods in `kube-system` and explain each one's role
- [ ] I can explain what Kind does under the hood (Docker containers as K8s nodes)
- [ ] I can load local Docker images into a Kind cluster with `kind load docker-image`

---

## Pods (Lab 02, Exercise 2a)

- [ ] I can write a Pod manifest from scratch (name, labels, container, image, ports, env)
- [ ] I can apply, describe, exec into, view logs, and delete a Pod
- [ ] I can explain Pod lifecycle phases: Pending, Running, Succeeded, Failed, Unknown
- [ ] I can explain why bare Pods are rarely used in production (no self-healing, no scaling)
- [ ] I can use `kubectl logs --previous` to see a crashed container's last output

---

## Deployments & ReplicaSets (Lab 02, Exercise 2b)

- [ ] I can write a Deployment manifest from scratch (name, replicas, selector, Pod template)
- [ ] I can explain the Deployment → ReplicaSet → Pod hierarchy
- [ ] I can scale a Deployment up and down with `kubectl scale`
- [ ] I can trigger a rolling update by changing the image tag
- [ ] I can explain `maxSurge` and `maxUnavailable` and their impact on update behavior
- [ ] I can rollback a Deployment with `kubectl rollout undo`
- [ ] I can view rollout history with `kubectl rollout history`
- [ ] I can demonstrate self-healing by deleting a Pod and watching it get replaced

---

## Services (Lab 03, Exercise 3a)

- [ ] I can write a Service manifest from scratch (ClusterIP and NodePort types)
- [ ] I can explain when to use ClusterIP vs NodePort vs LoadBalancer
- [ ] I can verify Service-to-Pod routing with `kubectl get endpoints`
- [ ] I can resolve Service DNS names from inside a Pod (`nslookup <service>`)
- [ ] I can explain the full DNS format: `<service>.<namespace>.svc.cluster.local`
- [ ] I can diagnose an empty Endpoints list (selector mismatch)
- [ ] I can draw the traffic path from a DNS lookup through kube-proxy to a Pod

---

## ConfigMaps (Lab 03, Exercise 3b)

- [ ] I can create a ConfigMap from scratch (manifest or kubectl command)
- [ ] I can mount ConfigMap values as environment variables in a Deployment
- [ ] I can explain the difference between `envFrom` (all keys) and `valueFrom.configMapKeyRef` (specific keys)
- [ ] I can explain what happens when a ConfigMap is updated (env vars don't change, volume mounts eventually do)
- [ ] I can explain when to restart Pods after ConfigMap changes

---

## Secrets (Lab 03, Exercise 3c)

- [ ] I can create a Secret manifest from scratch with base64-encoded values
- [ ] I can decode a K8s Secret value from the command line
- [ ] I can mount Secrets as environment variables in a Deployment
- [ ] I can explain why base64 is NOT encryption and K8s Secrets are not truly secret by default
- [ ] I can name at least 3 production alternatives for secret management (External Secrets, Sealed Secrets, Vault, CSI driver)

---

## Namespaces (Lab 04, Exercise 4a)

- [ ] I can create a namespace and deploy resources to it
- [ ] I can list resources across all namespaces
- [ ] I can resolve a Service in a different namespace using the full FQDN
- [ ] I can explain when namespaces are appropriate vs separate clusters
- [ ] I can create and apply a ResourceQuota to limit namespace resources

---

## Ingress (Lab 04, Exercise 4b)

- [ ] I can install the nginx Ingress Controller on a Kind cluster
- [ ] I can write an Ingress resource with path-based routing
- [ ] I can configure TLS termination with a self-signed certificate
- [ ] I can explain the difference between an Ingress Controller and an Ingress resource
- [ ] I can add a new path to an existing Ingress from memory
- [ ] I can explain why Ingress is preferred over multiple LoadBalancer Services

---

## Full Local Deployment (Lab 04, Exercise 4c)

- [ ] Starting from a clean Kind cluster, I can deploy the entire FlowForge stack from manifests in under 15 minutes
- [ ] I can create a PersistentVolumeClaim and mount it in a PostgreSQL Deployment
- [ ] I can verify data persists across Pod restarts (PVC persistence)
- [ ] I can verify end-to-end task flow: create task → worker processes → query result
- [ ] My K8s manifests are organized in a directory and can be applied with `kubectl apply -f <dir>`

---

## EKS (Lab 05, Exercise 5a)

- [ ] I can explain what AWS manages in EKS (control plane) vs what I manage (data plane)
- [ ] I can add an EKS cluster to my Terraform modules
- [ ] I can explain IAM Roles for Service Accounts (IRSA) and why it's preferred
- [ ] I can deploy FlowForge to EKS using the same manifests (with minor modifications)
- [ ] I can explain the differences between Kind and EKS (at least 5 aspects)
- [ ] I can explain the AWS Load Balancer Controller's role and how it differs from nginx Ingress
- [ ] I can clean up EKS resources in the correct order (K8s resources before terraform destroy)

---

## Debugging (Lab 06, Exercise 6)

- [ ] Given `ImagePullBackOff`, I can diagnose the issue using `kubectl describe pod`
- [ ] Given `CrashLoopBackOff`, I can find the root cause using `kubectl logs` and `kubectl logs --previous`
- [ ] Given a Service not routing traffic, I can diagnose using `kubectl get endpoints`
- [ ] Given a Pod stuck in Pending due to PVC issues, I can diagnose using `kubectl describe pvc`
- [ ] I can write incident reports with: symptom, diagnosis command, root cause, fix, prevention
- [ ] I can debug a broken K8s deployment using ONLY kubectl (no looking at manifests)

---

## Integration & Architecture Thinking

- [ ] I can explain the complete FlowForge architecture on K8s: Ingress → Service → Deployment → Pod → Container
- [ ] I can explain how K8s connects to every previous module (Linux, Networking, Go, Docker, AWS, Terraform, CI/CD)
- [ ] I can explain when Kubernetes is worth the complexity and when simpler solutions suffice
- [ ] I can write all core K8s manifests from scratch: Pod, Deployment, Service, ConfigMap, Secret, Ingress, PVC, Namespace
- [ ] I can explain the declarative model: desired state vs actual state, and how controllers reconcile them
- [ ] I can discuss rolling update strategies and their trade-offs for different service types

---

## Final Verification

Before moving to Module 9, do this exercise:

1. Delete your Kind cluster
2. Create a new one from scratch
3. Deploy the entire FlowForge stack from your organized manifests
4. Verify end-to-end functionality
5. Time yourself -- can you do it in under 15 minutes?

If yes, you're ready for Module 9: Monitoring and Observability.
