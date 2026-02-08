# Lab 01: Kubernetes Architecture & Local Cluster Setup

> **Module**: 8 -- Kubernetes  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Read the [K8s Architecture](#), [Local Cluster Setup with Kind](#), and [Pods](#) sections of the Module 8 README. Docker installed and running (Module 4). Basic kubectl familiarity (install it if you haven't).

---

## Overview

Before you run a single container on Kubernetes, you need to understand what's happening under the hood. In this lab, you'll first map out the entire K8s architecture from memory, then build a local cluster with Kind and explore it with kubectl.

---

## Exercise 1a: K8s Architecture -- Draw It Out

### Objectives

- Understand every control plane component and its role
- Understand every node component and its role
- Trace the full lifecycle of a `kubectl apply` command
- Connect K8s architecture to concepts from previous modules

### What You'll Do

**Part 1: Draw the Architecture**

1. Get a blank piece of paper (or a whiteboard, or a drawing tool). Without looking at the README or any documentation, draw the Kubernetes architecture from memory:
   - Draw the **control plane** with all its components
   - Draw at least two **worker nodes** with their components
   - Show the communication paths between components
   - Label each component with its name and a one-sentence description of its role

2. If you can't remember all components, that's fine -- draw what you can, then check the README to fill in the gaps. The goal is to build the mental model.

**Part 2: Trace a Request**

3. On your diagram, trace what happens when you run `kubectl apply -f deployment.yaml`:
   - Number each step in order (1, 2, 3, ...)
   - For each step, write which component is involved and what it does
   - Include at least 7 steps (from kubectl to container running)

4. Answer these questions on your diagram or in a separate document:
   - What happens if etcd goes down? What still works? What breaks?
   - What happens if the scheduler goes down? Can existing Pods keep running?
   - What happens if kubelet on a node crashes? What happens to the Pods on that node?
   - What's the difference between the control plane and the data plane?

**Part 3: Connect to Previous Modules**

5. For each K8s component, identify the analogous concept from previous modules:
   - kubelet ↔ ??? from Module 1 (think: what ensures a process keeps running?)
   - kube-proxy ↔ ??? from Module 2 (think: what routes network traffic?)
   - etcd ↔ ??? from Module 3 (think: what stores state?)
   - container runtime ↔ ??? from Module 4 (think: what actually runs containers?)
   - API server ↔ ??? from Module 3 (think: what accepts REST requests?)

### Expected Outcome

- A hand-drawn or digital K8s architecture diagram with all components labeled
- A numbered request flow showing the lifecycle of `kubectl apply`
- Written answers connecting K8s components to Modules 1-4 concepts

### Checkpoint Questions

- Can you redraw this diagram from scratch in under 3 minutes?
- If someone pointed at any component on your diagram, could you explain its role without hesitation?
- Can you explain why the architecture is split into control plane and data plane?

---

## Exercise 1b: Local Cluster with Kind

### Objectives

- Install Kind and kubectl on your machine
- Create a multi-node K8s cluster using Kind
- Verify the cluster is working with kubectl commands
- Understand what Kind is doing under the hood (containers as nodes)
- Explore the cluster's components

### What You'll Do

**Part 1: Install the Tools**

1. Install `kubectl` (the Kubernetes command-line tool):
   - What package manager would you use on Ubuntu? On macOS?
   - Verify the installation with `kubectl version --client`

2. Install `kind` (Kubernetes IN Docker):
   - Kind is a single binary. Find the installation instructions for your OS.
   - Verify with `kind version`

3. Ensure Docker is running:
   - `docker ps` should work without errors
   - If Docker isn't running, start it (remember Module 4?)

**Part 2: Create a Cluster**

4. Create a Kind cluster with the default configuration:
   - Use the `kind create cluster` command
   - What name does Kind give the cluster by default?
   - How long does cluster creation take?

5. Verify the cluster is running:
   - Run `kubectl cluster-info` -- what does it tell you?
   - Run `kubectl get nodes` -- how many nodes do you see? What are their roles?
   - Run `kubectl get pods -A` (all namespaces) -- what's already running?

6. Understand what Kind created. Run `docker ps` and look at the containers:
   - How many Docker containers did Kind create?
   - What are their names?
   - What image are they running?
   - How does this relate to the architecture you drew in Exercise 1a?

**Part 3: Multi-Node Cluster**

7. Delete the default cluster and create a multi-node cluster:
   - Write a Kind configuration file (YAML) that creates 1 control plane node and 2 worker nodes
   - Apply the configuration with `kind create cluster --config <file>`
   - The Kind config file defines the cluster shape. Look at the Kind documentation for the config format.

8. Verify the multi-node cluster:
   - `kubectl get nodes` should show 3 nodes
   - Which node has the `control-plane` role?
   - Run `docker ps` again -- how many containers now?

9. Explore what's running on the cluster:
   - `kubectl get pods -n kube-system` -- identify each system Pod and match it to your architecture diagram
   - Which control plane components do you see? (Hint: they run as static Pods on the control-plane node)
   - Do you see CoreDNS? What namespace is it in?
   - Do you see kube-proxy? Is it a Deployment or a DaemonSet? Why?

**Part 4: Cluster Exploration**

10. Explore the nodes:
    - `kubectl describe node <control-plane-node>` -- look at the "Conditions", "Capacity", and "Allocated resources" sections
    - How much CPU and memory does each node have?
    - What is the container runtime? (Look for "Container Runtime Version")

11. Test cluster DNS:
    - Run a temporary Pod: `kubectl run test --image=busybox --rm -it -- nslookup kubernetes`
    - What IP does `kubernetes` resolve to? This is the API server's ClusterIP.
    - Can you resolve `kubernetes.default.svc.cluster.local`?

12. Load your FlowForge Docker images into the Kind cluster:
    - Kind clusters can't pull from your local Docker daemon by default
    - Use `kind load docker-image <image-name>` to load your api-service and worker-service images
    - Why is this step necessary? What's the difference between Kind's image store and your Docker daemon's image store?

### Expected Outcome

- `kubectl cluster-info` shows a running cluster
- `kubectl get nodes` shows 1 control-plane node + 2 worker nodes (all `Ready`)
- You can identify every system Pod in `kube-system` and explain its role
- FlowForge images are loaded into the Kind cluster

### Checkpoint Questions

- Can you create and destroy a Kind cluster from memory without looking at documentation?
- Can you explain what Kind is doing under the hood (containers pretending to be nodes)?
- Why does Kind need a separate `kind load docker-image` step? What does this tell you about the relationship between Docker on your host and Docker inside Kind nodes?
- If `kubectl get nodes` shows a node as `NotReady`, what would you check first?

---

## What's Next?

In [Lab 02](lab-02-pods-deployments.md), you'll create your first Pod manifest and then graduate to Deployments with rolling updates and scaling.
