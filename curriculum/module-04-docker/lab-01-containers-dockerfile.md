# Lab 01: Containers & Dockerfile Fundamentals

> **Module**: 4 -- Docker and Containerization  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [Containers vs VMs](#) and [Dockerfile Fundamentals](#) sections of the Module 4 README. Docker Engine installed and running.

---

## Overview

In this lab, you'll explore what makes containers work under the hood by experimenting with Linux namespaces directly, then apply that understanding by writing Dockerfiles for the FlowForge services you built in Module 3.

---

## Exercise 1a: Containers vs VMs -- Namespaces & Isolation

### Objectives

- Understand that containers are just Linux processes with namespace isolation
- Use `unshare` to create an isolated process and observe what changes
- Compare the resource footprint of containers vs VMs
- Explain the container architecture to a non-technical person

### What You'll Do

**Part 1: Explore Namespaces with unshare**

1. On your Linux machine, run `unshare --help` to see the available namespace types. Identify the flags for PID, network, mount, and UTS namespaces.

2. Create a new process in a separate UTS namespace:
   - Use `unshare` with the UTS namespace flag to start a new shell
   - Inside the new shell, change the hostname to something different
   - Verify the hostname changed inside the namespace
   - Open another terminal and verify the host's real hostname is unaffected
   - What does this tell you about how containers get their own hostnames?

3. Create a new process in a separate PID namespace:
   - Use `unshare` with the PID namespace flag and `--fork` to start a new shell
   - Inside the new namespace, run `ps aux` or `ps -ef`
   - How many processes do you see? Compare this to running `ps aux` on the host
   - What PID is your shell process inside the namespace? What PID is it on the host?
   - Why does Docker show PID 1 as the main process inside every container?

4. Observe mount namespace isolation:
   - Use `unshare` with the mount namespace flag
   - Create a temporary directory, mount a tmpfs filesystem on it
   - Verify the mount exists inside the namespace
   - From another terminal, check if the mount is visible on the host
   - This is how containers have their own filesystem view

**Part 2: Container vs VM Resource Comparison**

5. Research and document the resource differences:
   - How much disk space does a typical Ubuntu VM image take? How about an Alpine Docker image?
   - How much RAM does a VM need just for its OS? How about a container running a single Go binary?
   - How long does a VM typically take to boot? How about a container?

6. Run a practical comparison:
   - Start a Docker container: `docker run -d alpine sleep 3600`
   - Use `docker stats` to observe its resource usage
   - Compare this to what a VM would use for the same workload (sleeping)
   - How many containers could you fit on a machine with 4GB RAM? How many VMs?

**Part 3: Explain It**

7. Write a brief explanation (3-5 sentences) of why containers exist and how they differ from VMs. Target audience: a non-technical project manager who asks "why can't we just use VMs?"

8. Draw (on paper or in a diagram tool) the architecture of:
   - Three applications running in VMs on a single physical host
   - Three applications running in containers on a single physical host
   - Clearly label where the kernel is shared and where it's duplicated

### Expected Outcome

- You've used `unshare` to create processes in isolated namespaces
- You understand that containers are NOT lightweight VMs -- they're isolated processes
- You can explain the UTS, PID, and mount namespaces and what each isolates
- You have a written explanation and architecture diagram comparing containers vs VMs
- You understand why containers start faster and use fewer resources than VMs

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What Linux kernel feature provides process isolation for containers? What about resource limits?
> 2. If a container's PID 1 process dies, what happens to the container? Why?
> 3. Explain to a non-technical person why containers exist. Use an analogy.
> 4. Draw the architecture of containers vs VMs from memory, showing where the kernel is shared.
> 5. When would you choose a VM over a container? Give two specific scenarios.

---

## Exercise 1b: Dockerfile Fundamentals

### Objectives

- Write Dockerfiles for the FlowForge api-service and worker-service
- Start with a "naive" approach intentionally (large image, inefficient caching)
- Understand what each Dockerfile instruction does and why it matters
- Create a `.dockerignore` file to optimize the build context

### What You'll Do

**Part 1: Write a Naive Dockerfile for api-service**

1. Create a Dockerfile at `project/api-service/Dockerfile` that:
   - Uses `golang:1.21` (not alpine) as the base image
   - Sets an appropriate working directory
   - Copies ALL files into the container in a single step
   - Downloads Go module dependencies
   - Builds the api-service binary
   - Exposes the appropriate port
   - Sets the command to run the binary

   Don't worry about optimization yet. Write the simplest Dockerfile that works.

2. Build the image and tag it:
   - Choose an appropriate image name and tag
   - Note the build time and final image size
   - Record these numbers -- you'll compare them after optimization in Lab 02

3. Run the container:
   - Start the container with the appropriate port mapping
   - Verify the api-service is accessible from your host machine (try hitting `/health`)
   - Check the container's logs

**Part 2: Write a Naive Dockerfile for worker-service**

4. Create a Dockerfile at `project/worker-service/Dockerfile` following the same approach:
   - Same base image as api-service
   - Copy, build, and run the worker-service binary
   - The worker-service doesn't need port exposure (it connects outbound to PostgreSQL)

5. Build and run the worker-service container:
   - Note the image size
   - Think about whether the worker-service can actually connect to PostgreSQL yet (spoiler: it can't without networking setup -- that's Lab 03)

**Part 3: Create .dockerignore**

6. Create a `.dockerignore` file in each service directory (or the project root, depending on your build context):
   - What files should NOT be included in the Docker build context?
   - Think about: version control files, documentation, test files, IDE configurations, environment files, compiled binaries on the host
   - Compare the build context size with and without `.dockerignore` (Docker prints this at the start of a build)

**Part 4: Analyze Your Dockerfiles**

7. Look critically at the Dockerfiles you just wrote:
   - How large is the final image? (use `docker images`)
   - How many layers does it have? (use `docker history`)
   - What happens if you change one line of Go code and rebuild? Which layers are cached and which rebuild?
   - What's in the image that doesn't need to be there at runtime?

   Write down at least 3 things you would improve. You'll make these improvements in Lab 02.

### Expected Outcome

- Two working Dockerfiles (api-service and worker-service) that build and produce runnable images
- A `.dockerignore` file that excludes unnecessary files from the build context
- A list of at least 3 optimization opportunities you've identified
- Notes on image sizes and build times for comparison in Lab 02
- You understand every instruction in your Dockerfiles and can explain why each line is there

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What's the difference between `CMD` and `ENTRYPOINT`? When would you use each?
> 2. Why does `COPY . .` before `RUN go mod download` hurt build performance?
> 3. What's in your Docker image that doesn't need to be there at runtime? How much space does it waste?
> 4. Given this bad Dockerfile, identify every issue:
>    ```dockerfile
>    FROM golang:latest
>    COPY . .
>    RUN go mod download
>    RUN go build -o app .
>    ENV DB_PASSWORD=supersecret
>    EXPOSE 8080
>    CMD go run main.go
>    ```
> 5. Why should `.env` files be in `.dockerignore`?
