# Lab 02: DNS, HTTP & Ports

> **Module**: 2 -- Networking Fundamentals  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Read the [DNS Resolution](#), [HTTP Deep Dive](#), and [Ports & Sockets](#) sections of the Module 2 README. Complete Lab 01.

---

## Overview

In this lab, you'll trace the full DNS resolution chain, dissect HTTP conversations with `curl -v`, and investigate every listening port on your system. These three skills form the foundation of application-layer troubleshooting -- when "the app won't connect," you'll know exactly how to figure out why.

---

## Exercise 2a: DNS Resolution with dig and nslookup

### Objectives

- Understand the DNS resolution chain from local cache to authoritative server
- Use `dig` and `nslookup` to query specific record types
- Configure local DNS entries in `/etc/hosts`
- Understand DNS caching and TTL implications

### What You'll Do

**Part 1: Explore local DNS configuration**

1. Examine your system's DNS configuration:
   - Look at `/etc/resolv.conf` -- what DNS servers are configured? Is there a `search` directive?
   - Look at `/etc/hosts` -- what entries exist by default?
   - Check `/etc/nsswitch.conf` -- what is the order of name resolution? (Hint: look for the `hosts:` line). What does `files dns` mean?

2. Add local DNS entries for FlowForge services in `/etc/hosts`:
   - `api.flowforge.local` → `127.0.0.1`
   - `db.flowforge.local` → `127.0.0.1`
   - `worker.flowforge.local` → `127.0.0.1`

3. Verify your entries work:
   - Use `ping` to confirm each name resolves to the correct IP
   - Use `getent hosts api.flowforge.local` to check resolution
   - What happens if you try to `dig api.flowforge.local`? Does it return the same result as `ping`? Why or why not?

**Part 2: DNS querying with dig**

4. Install `dig` if not present (it's part of a common DNS utility package -- which one?).

5. Use `dig` to query a well-known public domain (e.g., `example.com`, `github.com`):
   - Perform a basic A record lookup. What IP address(es) does it return?
   - Note the TTL value. What does it mean? How long will this answer be cached?
   - Look at the `ANSWER SECTION`, `AUTHORITY SECTION`, and `ADDITIONAL SECTION`. What does each contain?
   - Note the `Query time` and `SERVER` fields. Which DNS server answered?

6. Explore different record types for a domain:
   - Query for A records (`dig example.com A`)
   - Query for AAAA records (IPv6)
   - Query for MX records (mail servers)
   - Query for NS records (name servers)
   - Query for TXT records
   - Query for the SOA record

   For each, write down what the record contains and when you'd need to look it up.

7. Trace the full DNS resolution path:
   - Use `dig +trace` to see the complete resolution chain from root servers to the authoritative answer
   - Identify: the root servers, the TLD servers, and the authoritative name servers
   - How many hops does it take to resolve the name?

**Part 3: Compare dig and nslookup**

8. Perform the same queries using `nslookup`. Compare the output format with `dig`. Which tool gives you more information? When might you prefer one over the other?

9. Write your findings in a file called `dns-exploration.md`, including:
   - The DNS resolution chain you traced
   - A table of record types with examples and use cases
   - The difference between what `/etc/hosts` does and what DNS servers do
   - Why `dig` and `/etc/hosts` might give different answers for the same name

### Expected Outcome

- FlowForge service names resolve locally via `/etc/hosts`
- A file `dns-exploration.md` with DNS resolution chain analysis and record type documentation
- You can query any DNS record type for any domain using `dig`
- You understand the difference between local resolution (`/etc/hosts`) and DNS server resolution

### Checkpoint Questions

> Answer these without looking at notes:
> 1. You change an A record's IP in DNS, but clients still connect to the old IP. What's happening? How long might this last?
> 2. What is the purpose of a CNAME record? Can a CNAME point to another CNAME?
> 3. You run `dig api.flowforge.local` and get NXDOMAIN, but `ping api.flowforge.local` works. Why?
> 4. Explain the full resolution chain from your browser to an authoritative DNS server, step by step.

---

## Exercise 2b: HTTP Deep Dive with curl -v

### Objectives

- Inspect complete HTTP request/response cycles including headers
- Understand HTTP methods, status codes, and their semantics
- Make requests with different methods, headers, and body content
- Use `curl` as a diagnostic tool for HTTP services

### What You'll Do

**Part 1: Inspect HTTP traffic**

1. Start a simple HTTP server on port 8080 (same approach as Lab 01, or use a different method if you know one).

2. Use `curl -v` to make a request and examine the verbose output carefully:
   ```
   curl -v http://localhost:8080/
   ```
   In the output, identify:
   - Lines starting with `>` (what the client SENT)
   - Lines starting with `<` (what the server RESPONDED)
   - Lines starting with `*` (curl's internal connection info)
   - The TCP connection establishment
   - The HTTP request line (method, path, version)
   - The request headers
   - The response status line
   - The response headers
   - The response body

3. Document every header you see in both the request and response. For each header, explain what it does. Write this in a file called `http-analysis.md`.

**Part 2: HTTP methods in practice**

4. Using `curl`, craft requests with different methods. For each, observe what the server does (you may need to use a different server that handles POST/PUT, or note the behavior):

   - `GET` request with custom `Accept` header
   - `POST` request with a JSON body (use `-d` and `-H "Content-Type: application/json"`)
   - `PUT` request with a JSON body
   - `DELETE` request
   - `HEAD` request (what's different about the response compared to GET?)

5. Explore status codes by requesting different paths:
   - A path that exists → What status code?
   - A path that doesn't exist → What status code?
   - What other status codes can you provoke?

**Part 3: HTTP headers deep dive**

6. Experiment with these request headers and observe the effect:
   - `Host`: Make a request with a different `Host` header. What happens with virtual hosting?
   - `User-Agent`: Change your user agent string. Does the server respond differently?
   - `Accept-Encoding`: Request gzip compression. Does the response come back compressed?
   - `Connection: close` vs `Connection: keep-alive`: What changes?

7. Use `curl` to follow redirects (`-L`), save response headers to a file (`-D`), and time the request (`-w "%{time_total}\n"`).

**Part 4: Simulating FlowForge API requests**

8. Think ahead to Module 3. Write `curl` commands (in a file called `flowforge-api-tests.sh`) for what the FlowForge API would look like:
   - Create a task: `POST /api/v1/tasks` with a JSON body `{"name": "Deploy v2", "priority": "high"}`
   - List all tasks: `GET /api/v1/tasks`
   - Get one task: `GET /api/v1/tasks/1`
   - Update a task: `PUT /api/v1/tasks/1` with updated JSON
   - Delete a task: `DELETE /api/v1/tasks/1`
   - Health check: `GET /health`

   Include the appropriate headers (`Content-Type`, `Accept`) and note which status code you'd expect for each.

### Expected Outcome

- A file `http-analysis.md` documenting headers, methods, and status codes
- A file `flowforge-api-tests.sh` with curl commands for the FlowForge API
- You can craft any HTTP request with `curl` and interpret the verbose output
- You understand the purpose of every common HTTP header

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What is the difference between a 401 and a 403 status code?
> 2. Write a `curl` command from memory that sends a POST request with a JSON body and an Authorization header.
> 3. Given `curl -v` output, how can you tell whether the connection used HTTP/1.1 or HTTP/2?
> 4. Why does a POST request to create a resource return 201 instead of 200?

---

## Exercise 2c: Ports & Sockets with ss and netstat

### Objectives

- List all listening ports on your system and identify which service owns each one
- Understand the difference between `0.0.0.0`, `127.0.0.1`, and specific IP binding
- Use `ss` and `netstat` to diagnose port conflicts and connection states
- Understand TCP connection states (LISTEN, ESTABLISHED, TIME_WAIT, CLOSE_WAIT)

### What You'll Do

**Part 1: Discover listening ports**

1. Use `ss` to list all TCP listening sockets on your system:
   - Show listening sockets with process information (you'll need appropriate flags)
   - For each listening port, identify: the port number, the bind address, and the process name/PID

2. Do the same with `netstat` (you may need to install it -- it's part of a legacy networking package). Compare the output with `ss`. Which is more informative?

3. Create a file called `port-audit.md`. For every listening port on your system, document:
   - Port number
   - Protocol (TCP/UDP)
   - Bind address
   - Process name and PID
   - Whether you know what the service does
   - Whether it SHOULD be listening (from a security perspective)

**Part 2: Understand bind addresses**

4. Start your HTTP server on different bind addresses and test connectivity:
   - Start on `127.0.0.1:8080` -- can you connect from the same machine? From another machine on your network?
   - Start on `0.0.0.0:8080` -- can you connect from both? Why the difference?
   - If you have a specific non-loopback IP (e.g., `192.168.x.x`), try binding to that and test from loopback

5. For each scenario, verify with `ss` that the bind address is what you expect. Document your findings in `port-audit.md`.

**Part 3: TCP connection states**

6. While your HTTP server is running, establish a connection and use `ss` to observe the connection state:
   - Before any connection: What state is the server socket in?
   - During a connection: What states do you see? (Hint: use `curl` with a `keep-alive` connection)
   - After the connection closes: Do you see `TIME_WAIT`? What is it for? How long does it last?

7. Research and document the meaning of these TCP states:
   - LISTEN
   - SYN_SENT
   - SYN_RECV
   - ESTABLISHED
   - FIN_WAIT_1, FIN_WAIT_2
   - TIME_WAIT
   - CLOSE_WAIT
   - LAST_ACK

   When debugging, which states indicate a problem? Which are normal?

**Part 4: Port conflicts**

8. Try to start two servers on the same port. What error do you get? What does it tell you about how the OS manages ports?

9. Find out: can a TCP service and a UDP service both listen on the same port number simultaneously? Why?

### Expected Outcome

- A file `port-audit.md` with a complete audit of listening ports and connection state documentation
- You can list every listening port, identify the process, and assess whether it should be open
- You understand the security implications of different bind addresses
- You know what TCP connection states mean and which indicate problems

### Checkpoint Questions

> Answer these without looking at notes:
> 1. You run `ss -tlnp` and see a service listening on `0.0.0.0:5432`. What is the security concern?
> 2. You see many connections in `CLOSE_WAIT` state to your api-service. What does this mean? Which side has the problem?
> 3. Your api-service crashes and you can't restart it because "address already in use." What's likely happening? How do you investigate?
> 4. Explain why binding to `127.0.0.1` vs `0.0.0.0` matters for security, using the FlowForge database as an example.

---

## What's Next?

Proceed to [Lab 03: Firewalls, Routing & TLS](lab-03-firewalls-routing-tls.md) where you'll build firewall rules, route traffic between network namespaces, set up a reverse proxy with load balancing, and configure TLS certificates.

> **Link back to Module 1**: The tools you used here (`ss`, `curl`, `dig`) follow the same patterns as Module 1 tools -- they read from `/etc/` config files, run as processes you can find with `ps`, and some require root privileges you learned about with `sudo`. It's all Linux under the hood.
