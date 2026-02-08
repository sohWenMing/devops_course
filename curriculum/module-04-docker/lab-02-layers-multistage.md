# Lab 02: Image Layers & Multi-Stage Builds

> **Module**: 4 -- Docker and Containerization  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Lab 01 (you need the naive Dockerfiles). Read the [Image Layers and Caching](#) and [Multi-Stage Builds](#) sections of the Module 4 README.

---

## Overview

In this lab, you'll take the naive Dockerfiles from Lab 01 and transform them into optimized, production-ready images. You'll analyze layer structure, understand caching behavior, and implement multi-stage builds to achieve dramatically smaller images.

---

## Exercise 2a: Image Layers & Cache Optimization

### Objectives

- Use `docker history` to understand the layer structure of your images
- Reorder Dockerfile instructions to maximize cache hits
- Measure build time improvement from better caching
- Understand exactly which layers rebuild when source code changes

### What You'll Do

**Part 1: Analyze Your Current Layers**

1. Run `docker history` on your api-service image from Lab 01:
   - Identify each layer and which Dockerfile instruction created it
   - Note the size of each layer
   - Which layer is the largest? Why?
   - Which layers are shared with the worker-service image?

2. Experiment with cache behavior:
   - Make a small change to a Go source file (e.g., change a log message)
   - Rebuild the api-service image
   - Watch the build output: which steps say "CACHED" and which re-execute?
   - How long did the rebuild take compared to a fresh build?
   - Now change only `go.mod` (add a comment). Rebuild. What happens?

**Part 2: Optimize Instruction Order**

3. Rewrite the api-service Dockerfile with optimized instruction ordering:
   - Think about what changes most frequently (source code) vs what changes rarely (dependencies)
   - Copy dependency files (`go.mod`, `go.sum`) first and download dependencies
   - Then copy source code and build
   - What other instructions can be reordered for better caching?

4. Test the optimized caching:
   - Build the optimized image from scratch (note the time)
   - Make a small source code change and rebuild
   - Compare rebuild time to the naive Dockerfile rebuild time from step 2
   - Which layers were cached this time?
   - The dependency download step should now be cached. Is it?

5. Document the difference:
   - Record: naive rebuild time vs optimized rebuild time
   - Record: number of layers cached in each case
   - Why does this matter for CI/CD pipelines? (Think about Module 7)

**Part 3: Layer Size Optimization**

6. Examine RUN instruction patterns:
   - If you have multiple `RUN` instructions that install packages, what happens to intermediate files?
   - Combine related `RUN` instructions and clean up in the same step
   - Compare image size before and after combining

7. Check for unnecessary files in the image:
   - Use `docker exec` to explore the filesystem inside your container
   - Are there files that shouldn't be in a production image? (test files, docs, build cache, etc.)
   - How would you remove them?

### Expected Outcome

- You can read `docker history` output and explain every layer
- Your Dockerfile has optimized instruction ordering (dependencies before source code)
- Rebuilds after source code changes are measurably faster
- You understand exactly which file changes trigger which layer rebuilds
- You have documented timing comparisons between naive and optimized builds

### Checkpoint Questions

> Answer these without looking at notes:
> 1. You change one line in `main.go`. Which layers rebuild? Which are cached? Explain why.
> 2. Why does `COPY go.mod go.sum ./` come before `COPY . .` in an optimized Dockerfile?
> 3. You run `RUN apt-get update` in one layer and `RUN rm -rf /var/lib/apt/lists/*` in the next layer. Is the image smaller than if you didn't delete? Why or why not?
> 4. Your CI pipeline builds Docker images on every commit. Why does cache optimization directly affect deployment speed?
> 5. Predict the cache behavior: you change `go.sum` but not `go.mod`. Does the dependency download step re-run?

---

## Exercise 2b: Multi-Stage Builds

### Objectives

- Convert your Dockerfiles to multi-stage builds
- Understand the build stage vs runtime stage pattern
- Achieve final image sizes under 20MB for each Go service
- Compare image sizes between naive, optimized, and multi-stage approaches

### What You'll Do

**Part 1: Implement Multi-Stage Builds**

1. Rewrite the api-service Dockerfile as a multi-stage build:
   - **Stage 1 (builder)**: Use a golang base image to compile the binary
     - Copy dependency files, download dependencies
     - Copy source code, build the binary
     - Use appropriate Go build flags for a static binary (think about CGO and target OS)
   - **Stage 2 (runtime)**: Use a minimal base image
     - Choose an appropriate minimal base image (alpine, distroless, or scratch)
     - Copy ONLY the compiled binary from the builder stage
     - Set up the user, expose port, define the CMD
   - Think about: does the runtime stage need any files besides the binary? (CA certificates for HTTPS? timezone data?)

2. Build the multi-stage image and compare:
   - What's the final image size?
   - Compare to your Lab 01 naive image size
   - What's the size reduction percentage?
   - Run `docker history` -- how many layers does the final image have?

3. Verify the multi-stage image works:
   - Run the container and test the `/health` endpoint
   - Check that all functionality still works
   - Can you `docker exec` into the container? (Depends on your base image choice)

**Part 2: Worker Service Multi-Stage**

4. Apply the same multi-stage pattern to worker-service:
   - Create the builder and runtime stages
   - Build and note the image size
   - Think about whether the worker-service has any different requirements from api-service

**Part 3: Explore Base Image Choices**

5. Build your api-service with different runtime base images and compare:
   - `alpine:3.19`
   - `gcr.io/distroless/static-debian12`
   - `scratch`
   - For each, note: final image size, can you exec into it, what tools are available

6. For each base image, consider:
   - Can you debug issues inside the container?
   - Does the image include a shell?
   - Does the image include CA certificates (needed for HTTPS)?
   - What are the security implications? (fewer packages = fewer vulnerabilities)

**Part 4: Size Comparison Summary**

7. Create a comparison table documenting all your image sizes:

   | Approach | api-service | worker-service |
   |----------|-------------|----------------|
   | Naive (Lab 01) | ??? MB | ??? MB |
   | Optimized caching (2a) | ??? MB | ??? MB |
   | Multi-stage + alpine | ??? MB | ??? MB |
   | Multi-stage + distroless | ??? MB | ??? MB |
   | Multi-stage + scratch | ??? MB | ??? MB |

   - Which approach would you use for development? Why?
   - Which approach would you use for production? Why?
   - What's the trade-off between smallest possible image and debuggability?

### Expected Outcome

- Both services use multi-stage Dockerfiles with build and runtime stages
- Final images are under 20MB (ideally under 15MB with scratch/distroless)
- You can articulate the trade-offs between different base images
- You have a documented size comparison across all approaches
- The containers work correctly despite being dramatically smaller

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What does `COPY --from=builder` do? Why is this the key mechanism of multi-stage builds?
> 2. Why do you set `CGO_ENABLED=0` when building Go binaries for scratch/distroless images?
> 3. Write a multi-stage Dockerfile for a new Go binary from scratch (don't reference your existing one). Target under 20MB.
> 4. Your scratch-based container is crashing. You can't `docker exec` into it because there's no shell. How do you debug it?
> 5. Why does image size matter beyond just disk space? Think about network pull times, CI/CD speed, and security.
