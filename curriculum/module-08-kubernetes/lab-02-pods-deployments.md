# Lab 02: Pods & Deployments -- Running FlowForge on Kubernetes

> **Module**: 8 -- Kubernetes  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Lab 01 completed (Kind cluster running with FlowForge images loaded). Read the [Pods](#), [Deployments & ReplicaSets](#) sections of the Module 8 README.

---

## Overview

In this lab, you'll go from running a bare Pod to managing Deployments with multiple replicas. You'll experience firsthand why Pods alone are fragile and why Deployments are the standard for running workloads in K8s.

---

## Exercise 2a: Pod Manifests -- The Fragile Foundation

### Objectives

- Write a Pod manifest from scratch for FlowForge api-service
- Apply the manifest and observe Pod lifecycle
- Execute commands inside a running Pod
- Inspect Pod logs
- Understand why bare Pods are almost never used in production

### What You'll Do

**Part 1: Write a Pod Manifest**

1. Create a YAML file for a Pod running your FlowForge api-service:
   - The Pod needs a name, labels (why?), and a container specification
   - The container needs the image name, a container port declaration, and at minimum the environment variables required to start (think back to Module 3 -- what env vars does api-service need?)
   - For now, use placeholder values for database connection (the Pod won't connect to a real database yet -- that's OK, we're focusing on Pod mechanics)

2. Before applying, predict:
   - What status will the Pod show?
   - Will the container keep running or crash? Why?

**Part 2: Apply and Explore**

3. Apply the Pod manifest:
   - Use `kubectl apply -f <your-pod-file.yaml>`
   - Watch the Pod status change: `kubectl get pods -w` (the `-w` flag watches for changes)
   - What phases does the Pod go through?

4. If the Pod is running, inspect it:
   - `kubectl describe pod <pod-name>` -- read the Events section. What happened?
   - `kubectl logs <pod-name>` -- what output does the api-service produce?
   - What IP address was assigned to the Pod? (Look in `describe` output or `kubectl get pod -o wide`)

5. Execute a command inside the Pod:
   - `kubectl exec -it <pod-name> -- /bin/sh` (or `/bin/bash` if available)
   - Inside the Pod, check: `hostname`, `env`, `ls /`, `wget -qO- localhost:<port>/health` (or curl if available)
   - Can you see the environment variables you set in the manifest?
   - Exit the shell

6. If the Pod is CrashLoopBackOff (because there's no database), that's expected:
   - Check `kubectl logs <pod-name>` -- what error does it report?
   - Check `kubectl logs <pod-name> --previous` (or `-p`) -- what was the last output before crash?
   - This is a preview of debugging skills you'll need in Lab 06

**Part 3: Pod Fragility**

7. Delete the Pod:
   - `kubectl delete pod <pod-name>`
   - Run `kubectl get pods` -- what do you see?
   - Did anything recreate the Pod? Why not?

8. Think about these scenarios:
   - What happens if the node running the Pod crashes?
   - What if you need 3 copies of the Pod for load balancing?
   - What if you want to update the image to a new version?
   - None of these are handled by bare Pods. This is why we need Deployments.

### Expected Outcome

- A valid Pod manifest YAML file
- Experience applying, inspecting, exec-ing into, and deleting a Pod
- Understanding of why bare Pods are fragile and insufficient for production

### Checkpoint Questions

- Can you write a Pod manifest from memory (name, labels, container, image, ports, env)?
- Can you explain the Pod lifecycle phases (Pending, Running, Succeeded, Failed)?
- What happens to a bare Pod when it crashes? When its node dies?
- Why do Pods get random IP addresses and why is this a problem?

---

## Exercise 2b: Deployments -- Self-Healing and Rolling Updates

### Objectives

- Write Deployment manifests for api-service (2 replicas) and worker-service (1 replica)
- Observe ReplicaSet creation and Pod management
- Scale Deployments up and down
- Trigger a rolling update by changing the image tag
- Understand rollback mechanics

### What You'll Do

**Part 1: Write Deployment Manifests**

1. Create a Deployment manifest for `api-service`:
   - The Deployment should have a descriptive name and labels
   - Set `replicas: 2`
   - The Pod template should have labels that match the Deployment's selector (why must these match?)
   - Container spec: your api-service image, container port, environment variables
   - For now, use placeholder/mock values for DB connection (we'll fix this in Lab 03 with Services and ConfigMaps)

2. Create a Deployment manifest for `worker-service`:
   - Set `replicas: 1` (why might you start with fewer worker replicas than API replicas?)
   - Same approach: name, labels, selector, Pod template
   - What environment variables does the worker need? (Think back to Module 3)

3. Before applying, look at your manifests and answer:
   - How does the Deployment know which Pods belong to it? (Hint: label selectors)
   - What's the relationship between the Deployment, the ReplicaSet, and the Pods?
   - What's the default update strategy if you don't specify one?

**Part 2: Apply and Observe**

4. Apply both Deployment manifests:
   - `kubectl apply -f <api-deployment.yaml>`
   - `kubectl apply -f <worker-deployment.yaml>`

5. Observe what was created:
   - `kubectl get deployments` -- what do the READY, UP-TO-DATE, and AVAILABLE columns mean?
   - `kubectl get replicasets` -- who created this ReplicaSet? What's its name pattern?
   - `kubectl get pods` -- how many Pods are running? Who created them?
   - The naming chain: `api-service` (Deployment) → `api-service-7d9f8b` (ReplicaSet) → `api-service-7d9f8b-abc12` (Pod)

6. Inspect the Deployment:
   - `kubectl describe deployment api-service` -- read the Events section
   - Look at the "OldReplicaSets" and "NewReplicaSet" fields -- what do they show?

**Part 3: Self-Healing**

7. Test self-healing by deleting a Pod:
   - `kubectl delete pod <one-of-the-api-pods>`
   - Immediately run `kubectl get pods -w` -- what happens?
   - How fast was the replacement Pod created?
   - Compare this to what happened in Exercise 2a when you deleted a bare Pod

8. Test self-healing by simulating a crash:
   - If your Pod has a shell, exec in and kill the main process: `kubectl exec <pod> -- kill 1`
   - Watch `kubectl get pods -w` -- what does the RESTARTS column show?
   - How does this compare to systemd restarting a crashed service? (Module 1)

**Part 4: Scaling**

9. Scale the api-service Deployment:
   - `kubectl scale deployment api-service --replicas=5`
   - Watch the Pods appear: `kubectl get pods -w`
   - Where did the new Pods get scheduled? (Check with `kubectl get pods -o wide` -- look at the NODE column)
   - Did the scheduler spread them across nodes or put them all on one?

10. Scale back down:
    - `kubectl scale deployment api-service --replicas=2`
    - Watch Pods get terminated. Which Pods were removed? (Newest? Oldest? Random?)
    - How does K8s decide which Pods to kill when scaling down?

**Part 5: Rolling Updates**

11. Trigger a rolling update by changing the image:
    - First, check the current state: `kubectl rollout status deployment api-service`
    - Update the image (you can use a different tag or even a different image for testing):
      `kubectl set image deployment/api-service api-service=<new-image-tag>`
    - OR edit the manifest and `kubectl apply` again

12. Watch the rolling update in real-time:
    - `kubectl rollout status deployment api-service` (blocks until complete)
    - In another terminal: `kubectl get pods -w` -- watch old Pods terminate and new Pods start
    - `kubectl get replicasets` -- how many ReplicaSets exist now? How many Pods does each manage?

13. Inspect the update strategy:
    - `kubectl describe deployment api-service` -- look at the `StrategyType` and `RollingUpdateStrategy` fields
    - What are `maxSurge` and `maxUnavailable` set to by default?
    - During the update, was there ever a moment with zero running Pods? (There shouldn't be)

14. Rollback the update:
    - `kubectl rollout history deployment api-service` -- see the revision history
    - `kubectl rollout undo deployment api-service` -- roll back to the previous version
    - Watch the Pods change again: `kubectl get pods -w`
    - Can you rollback to a specific revision? (Hint: `--to-revision=N`)

### Expected Outcome

- Two Deployment manifests (api-service with 2 replicas, worker-service with 1 replica)
- Observed self-healing: deleted Pod replaced automatically
- Scaled up to 5 and back to 2 replicas
- Triggered a rolling update and verified zero-downtime transition
- Successfully rolled back a Deployment

### Checkpoint Questions

- Can you write a Deployment manifest from scratch without referencing your previous one?
- Can you explain the Deployment → ReplicaSet → Pod hierarchy and why each layer exists?
- What happens to the old ReplicaSet after a rolling update? Why is it kept around?
- What is `maxSurge` and `maxUnavailable`? What's the safest configuration for zero downtime?
- If you scale to 5 replicas and then change the image, how does the rolling update work with 5 Pods?
- How does K8s rolling updates compare to what you'd have to do manually with Docker Compose?

---

## What's Next?

In [Lab 03](lab-03-services-config.md), you'll connect your Deployments with Services for network access, and inject configuration through ConfigMaps and Secrets -- making your Pods actually functional.
