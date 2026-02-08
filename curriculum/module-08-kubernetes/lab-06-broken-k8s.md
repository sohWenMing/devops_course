# Lab 06: Broken Kubernetes -- Debug Under Pressure

> **Module**: 8 -- Kubernetes  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Labs 01-04 completed. Familiarity with `kubectl describe`, `kubectl logs`, `kubectl get events`. Read the [Debugging Kubernetes](#) section of the Module 8 README.

---

## Overview

Four FlowForge deployments are broken. Each has a different root cause. Your job: diagnose each one using only `kubectl` commands (describe, logs, events). No looking at the manifest source until you've identified the problem.

This is the Kubernetes equivalent of Module 1's broken server and Module 4's broken Docker setups. The debugging methodology is the same -- read the symptoms, form a hypothesis, verify, fix.

---

## Exercise 6: Four Broken Deployments

### Objectives

- Systematically diagnose K8s deployment failures using kubectl
- Identify root causes for: ImagePullBackOff, CrashLoopBackOff, Service selector mismatch, PVC storage class error
- Document your debugging process (symptoms → hypothesis → verification → fix)
- Build muscle memory for the `kubectl describe → logs → events` debugging loop

### Setup

Apply the four broken deployments to your Kind cluster. You can create these manifests yourself from the descriptions below, then intentionally introduce the specified bug. Alternatively, have a colleague or script create them for you so you don't know the exact issue.

**Important**: The goal is to diagnose from symptoms, not from reading the YAML. Apply the manifests, then close the files. Debug using only kubectl.

---

### Broken Deployment 1: The Image That Doesn't Exist

**Scenario**: The team pushed a new version of api-service, but Pods are stuck and not starting.

Create a Deployment manifest with these characteristics:
- Name: `api-service-broken1`
- Image: `flowforge/api-service:v2.1.0-rc3` (a tag that doesn't exist in your cluster or registry)
- Replicas: 2
- Include standard labels and container ports

Apply the manifest and investigate:

1. What status does `kubectl get pods` show?
2. Run `kubectl describe pod <pod-name>`:
   - Look at the **Events** section at the bottom
   - What event type do you see? (Normal/Warning?)
   - What's the event message?
3. What does the error tell you about the problem?
4. How would you fix this?
5. What would you check in a real production scenario? (Registry access? Image tag? Build pipeline?)

**Write an incident report**:
- **Symptom**: (what you observed)
- **Diagnosis command**: (what kubectl command revealed the issue)
- **Root cause**: (why the Pod can't start)
- **Fix**: (what you'd change)
- **Prevention**: (how to prevent this in CI/CD)

---

### Broken Deployment 2: The Crashing Container

**Scenario**: The worker-service is deployed but keeps restarting. It starts, runs for a few seconds, then crashes.

Create a Deployment manifest with these characteristics:
- Name: `worker-service-broken2`
- Image: your actual worker-service image (one that exists)
- Replicas: 1
- Environment variables: include ALL required variables EXCEPT `DB_HOST` (or whichever env var is critical for database connection)
- The container will start, try to connect to the database, fail, and exit

Apply and investigate:

1. What status does `kubectl get pods` show? What's the RESTARTS count?
2. `kubectl logs <pod-name>` -- what error does the application report?
3. `kubectl logs <pod-name> --previous` -- what was the output before the last crash?
4. `kubectl describe pod <pod-name>` -- look at the "Last State" section. What was the exit code?
5. How do you distinguish between "app is misconfigured" (missing env var) and "app has a bug" (code error)?

**Write an incident report**:
- **Symptom**: (what you observed)
- **Diagnosis command**: (what revealed the issue)
- **Root cause**: (why the container keeps crashing)
- **Fix**: (what environment variable is missing and how to add it)
- **Prevention**: (startup validation, readiness probes, ConfigMap requirements)

---

### Broken Deployment 3: The Service That Routes to Nothing

**Scenario**: api-service Pods are Running and healthy, but the Service isn't routing traffic to them. Internal requests to the Service return connection errors.

Create these resources:
- A Deployment named `api-service-broken3` with labels `app: api-service` and `version: v3` on the Pods
- A Service named `api-service-broken3` with selector `app: api-svc` (note the subtle typo: `api-svc` vs `api-service`)
- Port mapping: Service port 80 → target port 8080

Apply and investigate:

1. `kubectl get pods` -- are the Pods Running?
2. `kubectl get service api-service-broken3` -- does the Service exist?
3. `kubectl get endpoints api-service-broken3` -- what does this show? (This is the key diagnostic command)
4. If endpoints are empty (or the Endpoints resource doesn't list any addresses), what does that mean?
5. Compare the Service's selector with the Pod's labels. Where's the mismatch?
6. Test connectivity from inside a Pod: `kubectl exec <test-pod> -- wget -qO- api-service-broken3:80` -- what error do you get?

**Write an incident report**:
- **Symptom**: (Pods running, Service not routing)
- **Diagnosis command**: (`kubectl get endpoints` is the key)
- **Root cause**: (selector mismatch between Service and Pod labels)
- **Fix**: (correct the selector OR the Pod labels)
- **Prevention**: (label naming conventions, helm templates, automated testing of connectivity)

---

### Broken Deployment 4: The Storage That Won't Bind

**Scenario**: PostgreSQL is deployed with a PersistentVolumeClaim, but the Pod is stuck in Pending because the PVC won't bind.

Create these resources:
- A PVC named `postgres-broken4` requesting 10Gi with StorageClass `premium-ssd` (a class that doesn't exist in Kind)
- A Deployment named `postgres-broken4` mounting the PVC at `/var/lib/postgresql/data`
- Replicas: 1

Apply and investigate:

1. `kubectl get pods` -- what status is the Pod? (Pending)
2. `kubectl describe pod <pod-name>` -- look at the Events. What message appears?
3. `kubectl get pvc postgres-broken4` -- what's the STATUS? (Pending, not Bound)
4. `kubectl describe pvc postgres-broken4` -- what event message appears?
5. `kubectl get storageclasses` -- what classes are actually available?
6. How does the requested StorageClass compare to the available classes?

**Write an incident report**:
- **Symptom**: (Pod stuck in Pending)
- **Diagnosis command**: (PVC describe shows the binding failure)
- **Root cause**: (StorageClass doesn't exist)
- **Fix**: (change to an existing StorageClass or create the requested one)
- **Prevention**: (validate StorageClasses exist before deploying, use default class when possible)

---

### After All Four Bugs

When you've diagnosed and documented all four issues:

1. Fix each broken deployment and verify it becomes healthy
2. Review your incident reports. Do they follow a consistent format?
3. Create a personal debugging checklist:
   - Pod not starting → check: ___
   - Pod crash-looping → check: ___
   - Service not routing → check: ___
   - Pod stuck Pending → check: ___

4. Time yourself: apply all four broken manifests to a fresh namespace and diagnose all four in under 15 minutes

### Expected Outcome

- Four incident reports documenting symptoms, diagnosis, root cause, fix, and prevention
- All four deployments fixed and running
- A personal K8s debugging checklist
- Ability to diagnose common K8s failures systematically

### Checkpoint Questions

- Given `kubectl get pods` showing `ImagePullBackOff`, what are the possible causes? (At least 3)
- Given `CrashLoopBackOff`, what's the first command you run? What information do you look for?
- How do you verify a Service is correctly routing to its target Pods?
- If a Pod is stuck in Pending, what are the three most common reasons?
- Can you debug a broken K8s deployment using ONLY `kubectl describe`, `kubectl logs`, and `kubectl get events`? (No looking at manifests)
- How does K8s debugging compare to the Docker debugging from Module 4? What's similar? What's different?

---

## Module Complete!

Congratulations -- you've completed all Kubernetes labs. Before moving to Module 9, complete the [exit gate checklist](checklist.md) to verify you've internalized every concept.
