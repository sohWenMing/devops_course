# Module 4: Docker and Containerization -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 5.  
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

## Containers vs VMs (Lab 01, Exercise 1a)

- [ ] I can explain the difference between containers and VMs to a non-technical person
- [ ] I can draw the architecture of both from memory, showing where the kernel is shared
- [ ] I can name at least 3 Linux namespace types and explain what each isolates
- [ ] I can explain what cgroups are and what they limit (CPU, memory, I/O)
- [ ] I can give 2 scenarios where a VM is more appropriate than a container

---

## Dockerfile Fundamentals (Lab 01, Exercise 1b)

- [ ] I can write a Dockerfile for a Go service from scratch without referencing an existing one
- [ ] I can explain the difference between CMD and ENTRYPOINT and when to use each
- [ ] I can explain the difference between COPY and ADD and why COPY is preferred
- [ ] Given a bad Dockerfile, I can identify every issue and explain why each matters
- [ ] I know what belongs in `.dockerignore` and why

---

## Image Layers & Caching (Lab 02, Exercise 2a)

- [ ] I can read `docker history` output and explain every layer
- [ ] I can predict which layers will be cached and which will rebuild when I change one Go file
- [ ] I can explain why `COPY go.mod go.sum ./` should come before `COPY . .`
- [ ] I can explain why files deleted in a later `RUN` instruction still contribute to image size
- [ ] I can optimize a Dockerfile's instruction order for maximum cache utilization

---

## Multi-Stage Builds (Lab 02, Exercise 2b)

- [ ] I can write a multi-stage Dockerfile from scratch for a new Go service in under 10 minutes
- [ ] My FlowForge Go service images are under 30MB each (ideally under 20MB)
- [ ] I can explain what `COPY --from=builder` does and why it's the key to multi-stage builds
- [ ] I can explain why `CGO_ENABLED=0` matters when targeting scratch or distroless base images
- [ ] I can articulate the trade-offs between alpine, distroless, and scratch as runtime base images

---

## Docker Networking (Lab 03, Exercise 3a)

- [ ] I can create a custom Docker network and connect containers to it
- [ ] I can explain why user-defined bridge networks enable DNS resolution but the default bridge doesn't
- [ ] I can explain bridge vs host vs none networking and give a use case for each
- [ ] I can diagnose a container networking issue using `docker network inspect` and `docker exec`
- [ ] I can explain how Docker container DNS relates to the DNS concepts from Module 2

---

## Docker Volumes & Persistence (Lab 03, Exercise 3b)

- [ ] I can set up a named volume for PostgreSQL and demonstrate data persistence across container restarts
- [ ] I can explain the difference between bind mounts and named volumes and when to use each
- [ ] I can fix a permission denied error on a bind-mounted volume
- [ ] I can explain what `docker compose down -v` does and why it's dangerous in production
- [ ] I can explain how Docker volumes relate to AWS EBS volumes (thinking ahead to Module 5)

---

## Docker Compose (Lab 04, Exercise 4a)

- [ ] `docker compose up` brings up the entire FlowForge stack and all services communicate
- [ ] Health checks are configured and `depends_on` uses `condition: service_healthy`
- [ ] I can add a new service (e.g., redis) to the compose file from scratch
- [ ] I can start, stop, and manage individual services within the compose stack
- [ ] The complete task flow works: create via API → worker picks up → status updates

---

## Development Workflow (Lab 04, Exercise 4b)

- [ ] I have separate dev and prod compose configurations with clear differences
- [ ] In dev mode, Go code changes are automatically detected and reloaded without rebuilding
- [ ] I can explain why bind-mounting source code is appropriate for dev but not for prod
- [ ] Production compose uses pre-built, optimized multi-stage images (not bind mounts)
- [ ] I can articulate how dev-mode hot-reload relates to K8s dev tools like Skaffold (Module 8)

---

## Container Security (Lab 05, Exercise 5a)

- [ ] All FlowForge containers run as non-root users
- [ ] trivy scan shows no CRITICAL vulnerabilities on FlowForge images
- [ ] I can explain why running as root in a container is dangerous
- [ ] I can show the Dockerfile changes needed to run as non-root from memory
- [ ] I understand what Linux capabilities are and why dropping unnecessary ones matters

---

## Debugging Containers (Lab 05, Exercise 5b)

- [ ] I can diagnose a container that fails to start using `docker logs` and `docker inspect`
- [ ] I can identify and fix a wrong port mapping issue
- [ ] I can identify and fix a missing environment variable issue
- [ ] I can identify and fix a permission denied on volume issue
- [ ] I can identify and fix a network isolation issue
- [ ] I have a systematic debugging methodology for container issues

---

## Integration & Architecture Thinking

- [ ] `docker compose up` brings up the complete FlowForge stack (api, worker, postgres) and they all communicate
- [ ] Images are multi-stage builds, under 30MB each for Go services
- [ ] I can write a Dockerfile from scratch for a new Go service in under 10 minutes
- [ ] I can explain image layers, caching, and why instruction order matters without notes
- [ ] I can explain how Docker networking concepts map to AWS VPC networking (Module 5)
- [ ] I can explain how Docker Compose relates to Kubernetes (Module 8) -- what Compose does well and where K8s takes over
- [ ] I can explain how the 12-Factor config from Module 3 makes containerization smooth (env vars, stdout logging, graceful shutdown)
- [ ] I can debug a container that fails to start using only `docker logs` and `docker inspect`

---

## Final Self-Assessment

> Answer honestly:
>
> **Could I containerize a new multi-service Go application from scratch -- writing Dockerfiles, a compose file, configuring networking, volumes, health checks, and security -- on a fresh machine with no internet access and no notes?**
>
> - If YES for everything: You're ready for Module 5. Congratulations!
> - If NO for anything: Go back and practice. There are no shortcuts in DevOps.

---

## Ready for Module 5?

If every box above is checked, proceed to [Module 5: AWS Fundamentals](../module-05-aws/README.md).

> **What's coming**: In Module 5, you'll take the containerized FlowForge stack and deploy it to AWS. You'll create a VPC with public and private subnets, launch EC2 instances, set up RDS PostgreSQL, push your Docker images to ECR, and run everything in the cloud. The Docker skills you just learned -- writing Dockerfiles, building images, configuring networks, managing volumes -- will directly apply to your AWS deployment.
