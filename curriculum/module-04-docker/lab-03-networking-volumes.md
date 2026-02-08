# Lab 03: Docker Networking & Volumes

> **Module**: 4 -- Docker and Containerization  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Complete Lab 02 (multi-stage Dockerfiles ready). Read the [Docker Networking](#) and [Docker Volumes & Persistence](#) sections of the Module 4 README.

---

## Overview

So far, your containers run in isolation. In this lab, you'll connect them: api-service, worker-service, and PostgreSQL will communicate over a Docker network. You'll also set up persistent storage so database data survives container restarts.

---

## Exercise 3a: Docker Networking

### Objectives

- Understand the difference between the default bridge and user-defined bridge networks
- Create a custom network and connect FlowForge containers to it
- Verify DNS resolution between containers (using container names as hostnames)
- Compare bridge, host, and none networking modes

### What You'll Do

**Part 1: Explore the Default Bridge Network**

1. Start two containers on the default bridge network:
   - Run two `alpine` containers (e.g., `alpine1` and `alpine2`) in the background
   - Use `docker network inspect bridge` to find their IP addresses
   - Exec into `alpine1` and try to ping `alpine2` by IP address. Does it work?
   - Now try to ping `alpine2` by container name. Does it work? Why not?

2. Explore the default bridge network:
   - What subnet does the default bridge use?
   - What gateway address is assigned?
   - Use `docker inspect` on a container to find its network settings
   - How does this compare to the networking concepts from Module 2 (subnets, gateways, DNS)?

**Part 2: Create a User-Defined Bridge Network**

3. Create a custom network for FlowForge:
   - Create a bridge network named `flowforge-net`
   - Start a PostgreSQL container on this network (use the official `postgres:16-alpine` image with appropriate environment variables)
   - Start your api-service container on the same network
   - Start your worker-service container on the same network

4. Test DNS resolution:
   - Exec into the api-service container
   - Try to resolve the PostgreSQL container's hostname. What command would you use? (Hint: think about Module 2 DNS tools)
   - Can you ping the PostgreSQL container by name?
   - Can you connect to PostgreSQL using its container name as the hostname?

5. Verify service communication:
   - Configure your api-service to connect to PostgreSQL using the container name as DB_HOST
   - Verify the api-service can reach its database
   - Can the worker-service also reach PostgreSQL?
   - Can the api-service and worker-service reach each other? (Should they need to for FlowForge's architecture?)

**Part 3: Compare Networking Modes**

6. Experiment with different networking drivers:
   - Run a container with `--network host`. What IP address does it have? Can you access its port without `-p` port mapping? What are the security implications?
   - Run a container with `--network none`. Can it reach the internet? Can it reach other containers? When would you use this?
   - Compare: what can a bridge container do that a host container can't, and vice versa?

7. Understand port mapping:
   - With bridge networking, expose the api-service on port 8080 using `-p 8080:8080`
   - Try exposing it on a different host port: `-p 9090:8080`. What changes?
   - Try binding to localhost only: `-p 127.0.0.1:8080:8080`. Who can access it now?
   - Why doesn't the worker-service need port mapping? (Think about which direction the connections flow)

**Part 4: Network Isolation**

8. Create a second network and test isolation:
   - Create a second bridge network (e.g., `other-net`)
   - Start a container on `other-net`
   - Can it reach the containers on `flowforge-net`? Why not?
   - Connect a container to both networks. Can it reach containers on both?
   - How does this relate to subnet isolation from Module 2?

### Expected Outcome

- You understand why user-defined bridge networks are preferred over the default bridge
- FlowForge containers can communicate by name on a custom network
- You can explain bridge vs host vs none networking and when to use each
- You understand port mapping and why some services need it and others don't
- You can relate Docker networking to the Linux networking concepts from Module 2

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Why can containers on the default bridge network communicate by IP but not by name?
> 2. Explain bridge vs host vs none networking. Give a use case for each.
> 3. Your api-service container can't connect to PostgreSQL. List 3 things you'd check, in order.
> 4. Given a docker-compose file with 3 services, predict which services can talk to which. How does Docker Compose handle networking?
> 5. How does Docker's container DNS resolution compare to the DNS resolution you set up in Module 2?

---

## Exercise 3b: Docker Volumes & Persistence

### Objectives

- Set up a named volume for PostgreSQL data persistence
- Demonstrate that data survives container destruction and recreation
- Understand the difference between bind mounts and named volumes
- Handle volume permissions correctly

### What You'll Do

**Part 1: The Ephemeral Container Problem**

1. Demonstrate data loss without volumes:
   - Start a PostgreSQL container WITHOUT a volume
   - Connect to it and create a test table with some data (use `docker exec` and `psql`)
   - Verify the data exists
   - Stop and remove the container (`docker rm -f`)
   - Start a new PostgreSQL container (same image, same name, same config)
   - Is your data still there? Why or why not?

**Part 2: Named Volumes for Persistence**

2. Set up persistent PostgreSQL storage:
   - Create a named volume for PostgreSQL data
   - Start a PostgreSQL container with the volume mounted at `/var/lib/postgresql/data`
   - Connect and create a test table with data
   - Verify the data exists

3. Test persistence across container lifecycle:
   - Stop the PostgreSQL container. Is the data accessible? (Hint: the volume still exists)
   - Remove the container entirely (`docker rm`)
   - Start a brand new PostgreSQL container using the SAME named volume
   - Is your data still there? Connect and verify

4. Explore volume management:
   - List all Docker volumes on your system
   - Inspect your PostgreSQL volume -- where does Docker actually store the data on the host?
   - How much space does the volume consume?
   - What happens if you run `docker volume rm` while a container is using it?

**Part 3: Bind Mounts for Development**

5. Set up a bind mount:
   - Create a directory on your host with a test file
   - Start a container with the directory bind-mounted
   - From inside the container, can you see the test file?
   - Modify the file from the host. Is the change visible inside the container?
   - Create a new file from inside the container. Is it visible on the host?
   - What user owns the file created from inside the container?

6. Explore permission issues:
   - Start a container that runs as a non-root user (e.g., UID 1000)
   - Bind-mount a directory owned by root
   - Try to write a file from inside the container. What happens?
   - How would you fix this permission issue?
   - Why is this relevant when mounting source code for development?

**Part 4: Data Persistence for FlowForge**

7. Put it all together for FlowForge:
   - Start PostgreSQL with a named volume on your custom network
   - Start the api-service connected to PostgreSQL
   - Create a task via the API
   - Verify the task exists in PostgreSQL (use `docker exec` + `psql`)
   - Stop and remove ALL containers (but keep the volume)
   - Restart everything
   - Is the task still there? The volume preserved it through the restart

8. Understand volume cleanup:
   - What does `docker compose down` do to volumes?
   - What does `docker compose down -v` do?
   - Why is the `-v` flag dangerous in production?
   - When would you intentionally want to destroy volumes?

### Expected Outcome

- PostgreSQL data persists across container stops, removals, and recreations
- You understand the difference between named volumes and bind mounts and when to use each
- You can handle permission issues between host and container
- You can set up the full FlowForge stack with persistent PostgreSQL storage
- You understand volume lifecycle (create, use, inspect, remove)

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What's the difference between a named volume and a bind mount? When do you use each?
> 2. You destroy your PostgreSQL container and create a new one. Your data is gone. What did you forget?
> 3. A container running as UID 1000 can't write to a bind-mounted directory. What's the likely cause and how do you fix it?
> 4. Explain what `docker compose down -v` does and why it's dangerous in production.
> 5. How do Docker volumes relate to EBS volumes in AWS? (Think about Module 5)
