# Lab 03: Kubernetes Network Policies & RBAC

> **Objective**: Implement Kubernetes NetworkPolicies to control service-to-service communication with default deny, then create dedicated ServiceAccounts with least-privilege Roles and RoleBindings.  
> **Prerequisites**: Module 8 (Kubernetes), Labs 01-02 done  
> **Time estimate**: 3-4 hours  
> **Produces**: NetworkPolicy manifests, verification of denied connections, ServiceAccount manifests, Role/RoleBinding manifests, RBAC verification

---

## Exercise 3a: Kubernetes Network Policies

### Objective

Write Kubernetes NetworkPolicies that enforce a default-deny posture, then explicitly allow only the communication paths that FlowForge requires. Verify that denied connections actually fail.

### Background

Right now, every Pod in your Kind cluster can talk to every other Pod. If an attacker compromises the api-service, they can reach PostgreSQL directly, reach the worker-service, reach Prometheus, reach Grafana -- anything. NetworkPolicies fix this by defining explicit allow rules.

> **Link back to Module 2**: In Lab 3a, you wrote iptables rules: allow SSH, allow api-service port, allow PostgreSQL only from api-service IP, deny everything else. NetworkPolicies are the same concept applied to Kubernetes. Instead of IP addresses, you use Pod labels. Instead of iptables commands, you write YAML manifests.

> **Link back to Module 5**: Security groups controlled which EC2 instances could communicate on which ports. `db-sg` only allowed 5432 from `api-sg` and `worker-sg`. NetworkPolicies do the same thing but at the Pod level inside Kubernetes.

### Important: NetworkPolicy CNI Requirement

NetworkPolicies require a CNI (Container Network Interface) plugin that enforces them. The default Kind networking does **not** enforce NetworkPolicies. You need to install a policy-capable CNI:

- **Calico**: Full-featured, widely used. Install with `kubectl apply -f` from Calico's quickstart manifests.
- **Cilium**: eBPF-based, high performance. More complex to install but very powerful.

Choose one and install it before writing NetworkPolicies, or your policies will be accepted by the API server but silently ignored.

### What You'll Do

1. **Install a NetworkPolicy-capable CNI** in your Kind cluster:
   - Research which CNI to install (Calico is recommended for learning)
   - Install it and verify it's running
   - Confirm that existing Pod connectivity still works after installation

2. **Map required communication paths** for FlowForge:

   Before writing any policies, document every legitimate communication path:

   | Source | Destination | Port | Protocol | Purpose |
   |--------|-------------|------|----------|---------|
   | api-service | PostgreSQL | 5432 | TCP | Database queries |
   | worker-service | PostgreSQL | 5432 | TCP | Task polling and updates |
   | Ingress controller | api-service | 8080 | TCP | Route external traffic |
   | api-service | DNS (kube-dns) | 53 | TCP/UDP | Name resolution |
   | worker-service | DNS (kube-dns) | 53 | TCP/UDP | Name resolution |
   | Prometheus | api-service | 8080 | TCP | Metrics scraping |
   | Prometheus | worker-service | 8080 | TCP | Metrics scraping |

   Everything not in this table should be blocked.

3. **Create a default-deny policy**:
   - Write a NetworkPolicy that denies ALL ingress and ALL egress for every Pod in the FlowForge namespace
   - Apply it
   - Verify that FlowForge is now completely broken (nothing can talk to anything)
   - This is intentional -- you'll add allow rules next

4. **Write allow policies for each service**:

   Create individual NetworkPolicies for each required communication path:

   - **PostgreSQL ingress**: Allow incoming connections on port 5432 from Pods labeled as api-service OR worker-service. Deny everything else.

   - **api-service ingress**: Allow incoming connections on port 8080 from the Ingress controller and from Prometheus. Deny everything else.

   - **api-service egress**: Allow outgoing connections to PostgreSQL on port 5432. Allow DNS (port 53 to kube-dns). Block everything else.

   - **worker-service ingress**: Allow incoming connections on port 8080 from Prometheus only (for metrics scraping). Deny everything else.

   - **worker-service egress**: Allow outgoing connections to PostgreSQL on port 5432. Allow DNS. Block everything else.

   - **DNS egress**: Ensure all services can reach kube-dns for name resolution (this is easy to forget and breaks everything).

5. **Apply policies incrementally**:
   - Apply one policy at a time
   - Test after each policy to verify expected behavior
   - If something breaks, debug by checking which policy is blocking the traffic
   - Order matters less for NetworkPolicies (they're additive), but applying incrementally helps debugging

6. **Verify denied connections**:

   This is the most important step -- prove that your policies actually block unauthorized traffic:

   - **Test 1**: From api-service, try to connect to worker-service directly (should fail)
   - **Test 2**: From worker-service, try to reach the Ingress controller (should fail)
   - **Test 3**: From a temporary debug Pod (with curl/netcat), try to connect to PostgreSQL (should fail -- only api-service and worker-service should be allowed)
   - **Test 4**: From api-service, try to reach an external URL (should fail -- no egress to internet allowed)
   - **Test 5**: Verify that legitimate traffic still works: create a task via the API, verify the worker processes it, verify data is in the database

   For each test, document the command you used and the result (connection refused, timeout, success).

7. **Document your NetworkPolicy architecture**:
   - Draw a diagram showing which Pods can communicate with which
   - For each policy, explain what it allows and why
   - List what is explicitly denied (by omission from allow rules)

### Expected Outcome

- Default deny policy applied to the FlowForge namespace
- Individual allow policies for each legitimate communication path
- api-service can reach PostgreSQL and DNS (nothing else)
- worker-service can reach PostgreSQL and DNS (nothing else)
- PostgreSQL accepts connections only from api-service and worker-service
- Prometheus can scrape metrics from both services
- At least 5 denied connection tests documented with commands and results
- FlowForge end-to-end task flow still works correctly
- Architecture diagram showing allowed vs blocked communication

### Checkpoint Questions

- [ ] What's the difference between a default-deny policy and individual deny rules? Why start with default deny?
- [ ] If you deploy a new service (e.g., a Redis cache) to the FlowForge namespace, can it communicate with anything? Why or why not?
- [ ] How do you debug a NetworkPolicy that's blocking traffic you think should be allowed? What tools or commands would you use?
- [ ] Could you write a NetworkPolicy from scratch for a completely different set of services (e.g., a frontend, backend, and cache)?
- [ ] What happens if you forget to allow DNS egress? What symptoms would you see?
- [ ] How do NetworkPolicies compare to AWS security groups? What's similar and what's different?

---

## Exercise 3b: Kubernetes RBAC

### Objective

Create dedicated ServiceAccounts for each FlowForge service. Create Roles and RoleBindings that grant only the minimum Kubernetes API permissions needed. Ensure no service uses the default ServiceAccount.

### Background

Every Pod in Kubernetes runs as a ServiceAccount. By default, all Pods use the `default` ServiceAccount in their namespace. This is a security risk because:
- The default ServiceAccount may have more permissions than any single service needs
- All services share the same identity, making audit trails useless
- If one service is compromised, the attacker has the permissions of all services

> **Link back to Module 5**: This is exactly the same principle as IAM. In Module 5, you created a dedicated IAM user instead of using root. Here, you create dedicated ServiceAccounts instead of using `default`. The principle is identical: least privilege per identity.

### What You'll Do

1. **Audit current ServiceAccount usage**:
   - Check which ServiceAccount each FlowForge Pod is currently using
   - Check what permissions the `default` ServiceAccount has
   - Check if there's an auto-mounted service account token in each Pod (and whether it's needed)

2. **Create dedicated ServiceAccounts**:
   - Create a `flowforge-api` ServiceAccount for api-service
   - Create a `flowforge-worker` ServiceAccount for worker-service
   - Create a `flowforge-postgresql` ServiceAccount for PostgreSQL
   - Set `automountServiceAccountToken: false` on each unless the Pod actually needs Kubernetes API access

3. **Determine required Kubernetes API permissions for each service**:

   Think carefully about what each service actually does with the Kubernetes API:

   - **api-service**: Does it call the Kubernetes API at all? (Most application Pods don't -- they just serve HTTP.) If not, it needs zero permissions.
   - **worker-service**: Same question. Does it interact with Kubernetes at all?
   - **PostgreSQL**: Does the database need Kubernetes API access? (Almost certainly not.)

   For services that don't need Kubernetes API access, the ServiceAccount exists for identity purposes and IRSA integration (EKS), not for K8s API permissions.

   If any service does need K8s API access (e.g., a controller that watches resources), define the minimum set:
   - Which API groups? (`""` for core, `"apps"` for deployments, etc.)
   - Which resources? (pods, services, configmaps, secrets, etc.)
   - Which verbs? (get, list, watch, create, update, delete)

4. **Create Roles with least privilege**:
   - For each service that needs K8s API access, create a Role with only the necessary permissions
   - Use namespace-scoped Roles (not ClusterRoles) unless cross-namespace access is genuinely needed
   - Be specific about verbs: `get` and `list` are different from `create` and `delete`

5. **Create RoleBindings**:
   - Bind each ServiceAccount to its corresponding Role
   - Double-check that the namespace in the RoleBinding matches the namespace of the ServiceAccount and Role

6. **Update FlowForge Deployments**:
   - Add `serviceAccountName: flowforge-api` to the api-service Deployment
   - Add `serviceAccountName: flowforge-worker` to the worker-service Deployment
   - Add `serviceAccountName: flowforge-postgresql` to the PostgreSQL Deployment
   - Set `automountServiceAccountToken: false` where appropriate
   - Apply the updated Deployments and verify all services start correctly

7. **Verify RBAC enforcement**:
   - From inside each Pod, attempt Kubernetes API operations:
     - `kubectl get pods` (should it work or be denied?)
     - `kubectl get secrets` (should definitely be denied for most services)
     - `kubectl delete pod <some-pod>` (should be denied for all application services)
   - Document which operations succeed and which are denied for each ServiceAccount
   - Confirm that the permissions match your Role definitions

8. **Explain Role vs ClusterRole**:
   - Write a brief explanation of when to use Role vs ClusterRole
   - Give an example scenario where a ClusterRole would be necessary (e.g., a monitoring agent that needs to list Pods across all namespaces)
   - Explain why FlowForge services should use Roles, not ClusterRoles

### Expected Outcome

- Three dedicated ServiceAccounts created (flowforge-api, flowforge-worker, flowforge-postgresql)
- No FlowForge Pod uses the `default` ServiceAccount
- Roles created with minimum necessary permissions (many services may need zero K8s API permissions)
- RoleBindings connecting ServiceAccounts to Roles
- RBAC enforcement verified (denied operations documented)
- Written explanation of Role vs ClusterRole with examples
- All FlowForge services still function correctly

### Checkpoint Questions

- [ ] What's the difference between a Role and a ClusterRole? When would you use each?
- [ ] Why should you set `automountServiceAccountToken: false` for most application Pods?
- [ ] If someone compromises the api-service Pod and tries to `kubectl get secrets`, what happens? Why?
- [ ] How does Kubernetes RBAC relate to AWS IAM? (Think ServiceAccount ↔ IAM Role, Role ↔ Policy, RoleBinding ↔ Policy attachment)
- [ ] For a new namespace with three services, create RBAC from scratch in under 10 minutes. Can you do it?
- [ ] How does IRSA (IAM Roles for ServiceAccounts) bridge Kubernetes RBAC and AWS IAM? Why does this matter for EKS?
