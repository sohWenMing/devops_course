# Lab 03: Firewalls, Routing & TLS

> **Module**: 2 -- Networking Fundamentals  
> **Time estimate**: 3-4 hours  
> **Prerequisites**: Read the [Firewalls](#), [Routing & Gateways](#), [Load Balancing](#), and [TLS/SSL](#) sections of the Module 2 README. Complete Labs 01-02.

---

## Overview

This is the largest lab in Module 2 and brings together everything you've learned. You'll build firewall rules to control traffic, create isolated network namespaces to simulate multi-subnet routing, set up nginx as a load-balancing reverse proxy, and generate TLS certificates to encrypt traffic. These are the exact same concepts you'll use in AWS security groups, VPC routing, Application Load Balancers, and ACM certificates.

---

## Exercise 3a: Firewall Rules with iptables and ufw

### Objectives

- Configure iptables rules to allow and deny specific traffic patterns
- Understand the default policy concept (default deny)
- Verify that rules work by testing allowed and denied connections
- Use ufw as a higher-level firewall interface

### What You'll Do

**Part 1: iptables fundamentals**

1. List the current iptables rules on your system. What is the default policy for INPUT, OUTPUT, and FORWARD?

2. Before making any changes, save your current iptables rules so you can restore them later. (Hint: `iptables-save` and `iptables-restore` are your friends.)

3. Design and implement a firewall rule set for a FlowForge application server. Your rules should:
   - Set the default INPUT policy to DROP (deny all by default)
   - Allow all traffic on the loopback interface (localhost needs to work)
   - Allow established and related connections (responses to outbound requests)
   - Allow SSH on port 22 from a specific IP range (e.g., `10.0.0.0/24`) only
   - Allow HTTP on port 8080 (the api-service port) from any source
   - Allow ICMP (ping) from your local subnet
   - Log dropped packets (for debugging)

4. Test your rules:
   - Start an HTTP server on port 8080. Can you access it from the allowed network?
   - Try to connect to a port that's NOT in your rules (e.g., port 9999). What happens?
   - Can you ping the machine? Can you SSH?
   - Check the logs for dropped packets

5. Now add rules for the database tier:
   - Allow PostgreSQL (port 5432) ONLY from the app server's IP
   - Deny PostgreSQL from all other sources
   - Verify: try to connect to port 5432 from the allowed IP and from a disallowed IP

**Part 2: ufw**

6. Restore your original iptables rules, then implement the SAME security policy using `ufw` instead.

7. Compare the two approaches:
   - Which is easier to write?
   - Which gives you more control?
   - Run `iptables -L` while ufw is active. What rules did ufw generate behind the scenes?

8. Write your firewall design (rules, reasoning, test results) in a file called `firewall-rules.md`.

### Expected Outcome

- A documented iptables rule set for FlowForge with test results
- The same policy implemented in ufw
- A file `firewall-rules.md` with your firewall design and testing documentation
- You can write firewall rules from scratch for a given scenario

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Why should the default INPUT policy be DROP instead of ACCEPT?
> 2. You have a rule that allows SSH, but you can't SSH in. What could cause this if the default policy is DROP? (Think about rule ordering.)
> 3. What does the `ESTABLISHED,RELATED` state match accomplish? What would break without it?
> 4. Write iptables rules from memory for this scenario: allow HTTPS (443) from anywhere, allow SSH from `10.0.0.5` only, allow PostgreSQL (5432) from `10.0.2.0/24` only, deny everything else.

---

## Exercise 3b: Network Namespaces & Routing

### Objectives

- Create isolated network namespaces to simulate multiple subnets
- Connect namespaces with virtual ethernet pairs (veth)
- Set up routing between namespaces
- Understand routing tables, default gateways, and how traffic finds its path

### What You'll Do

**Part 1: Create network namespaces**

1. Create two network namespaces simulating two different subnets:
   - `ns-app` -- representing the application subnet (10.0.2.0/24)
   - `ns-db` -- representing the database subnet (10.0.3.0/24)

2. Verify your namespaces exist and are empty (no interfaces except loopback).

**Part 2: Connect the namespaces**

3. Create virtual ethernet (veth) pairs to connect the namespaces:
   - A veth pair between the host and `ns-app`
   - A veth pair between the host and `ns-db`
   - Assign IP addresses:
     - Host side to ns-app: `10.0.2.1/24`
     - ns-app side: `10.0.2.10/24`
     - Host side to ns-db: `10.0.3.1/24`
     - ns-db side: `10.0.3.10/24`

4. Bring up all interfaces. Verify connectivity:
   - From ns-app, can you ping `10.0.2.1` (the host side)?
   - From ns-db, can you ping `10.0.3.1` (the host side)?
   - From ns-app, can you ping `10.0.3.10` (ns-db)? If not, why not?

**Part 3: Enable routing**

5. Enable IP forwarding on the host (it acts as a router between the two subnets).

6. Add default routes in each namespace:
   - In ns-app, the default gateway should be `10.0.2.1` (the host)
   - In ns-db, the default gateway should be `10.0.3.1` (the host)

7. Now test again: from ns-app, can you ping `10.0.3.10`? From ns-db, can you ping `10.0.2.10`?

8. Examine the routing table in each namespace. Draw the path a packet takes from ns-app to ns-db (include every hop and routing decision).

**Part 4: Simulate FlowForge communication**

9. In ns-db, start a simple TCP server on port 5432 (simulating PostgreSQL). In ns-app, connect to it (simulating api-service connecting to the database). Verify the connection works across namespaces.

10. Inspect the routing table on the host. Can you trace the complete path?

11. Document your setup, routing tables, and test results in a file called `routing-lab.md`. Include an ASCII diagram of the network topology.

### Expected Outcome

- Two network namespaces communicating through the host as a router
- A file `routing-lab.md` with network topology diagram, routing tables, and test results
- You understand how routing tables determine packet forwarding
- You can set up routing between isolated networks

### Checkpoint Questions

> Answer these without looking at notes:
> 1. What is a network namespace? How does it relate to Docker networking?
> 2. What does "IP forwarding" mean? Why must it be enabled on a machine acting as a router?
> 3. Read and explain this routing table entry: `10.0.3.0/24 via 10.0.2.1 dev veth0`
> 4. Draw the routing path from api-service (10.0.2.10) to PostgreSQL (10.0.3.10) when they're on different subnets. What decision does each router/host make?

---

## Exercise 3c: nginx Reverse Proxy & Load Balancing

### Objectives

- Install and configure nginx as a reverse proxy
- Set up round-robin load balancing across multiple backend instances
- Observe traffic distribution
- Understand the reverse proxy pattern used in every production deployment

### What You'll Do

**Part 1: Set up backend instances**

1. Start two (or three) simple HTTP server instances on different ports (e.g., 8081, 8082, 8083). Each should return a response that identifies which instance handled the request. (Hint: create simple index pages that say "Instance 1", "Instance 2", etc.)

2. Verify each instance is running and responding on its port.

**Part 2: Configure nginx as a reverse proxy**

3. Install nginx.

4. Create an nginx configuration that:
   - Listens on port 80
   - Proxies all requests to one of your backend instances
   - Passes the original client IP via `X-Forwarded-For` header
   - Sets the `Host` header properly

5. Test: make requests to `http://localhost:80`. Does the request reach your backend? Check the nginx access log and your backend's output.

**Part 3: Add load balancing**

6. Update your nginx configuration to use an `upstream` block with all backend instances:
   - Configure round-robin load balancing (the default)
   - Make 10+ requests to `http://localhost:80`
   - Observe: are requests distributed evenly? Which instance handles each request?

7. Experiment with load balancing variations:
   - Mark one server as `down` -- what happens to traffic?
   - Add `weight` to one server -- how does distribution change?
   - What happens if one backend server is stopped? Does nginx detect it? How quickly?

**Part 4: Observe and document**

8. Use `curl -v` to inspect the headers when going through nginx. What headers does nginx add or modify?

9. Check the nginx access log and error log. Where are they located? (Remember Module 1 -- FHS tells you where logs live.)

10. Write your configuration and observations in a file called `nginx-lb.md`. Include:
    - Your nginx configuration file
    - Results of your load balancing tests
    - An explanation of how round-robin distribution works
    - What happens when a backend fails

### Expected Outcome

- nginx running as a reverse proxy in front of multiple backend instances
- Round-robin load balancing distributing traffic evenly
- A file `nginx-lb.md` with configuration, test results, and analysis
- You understand the reverse proxy pattern and can configure basic load balancing

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Explain the difference between L4 and L7 load balancing. nginx operates at which layer?
> 2. Your api-service logs show all requests coming from `127.0.0.1` instead of the real client IP. Why? How do you fix it?
> 3. You have a WebSocket-based feature. What load balancing consideration does this introduce? (Hint: think about connection affinity.)
> 4. Why is TLS termination typically done at the reverse proxy instead of at each backend?

---

## Exercise 3d: TLS/SSL with openssl

### Objectives

- Generate a self-signed TLS certificate
- Configure a service to serve HTTPS
- Inspect the TLS handshake with command-line tools
- Understand certificates, certificate chains, and why trust matters

### What You'll Do

**Part 1: Generate a self-signed certificate**

1. Use `openssl` to generate:
   - A private key (RSA 2048-bit or ECDSA P-256)
   - A Certificate Signing Request (CSR) with the following details:
     - Common Name (CN): `api.flowforge.local`
     - Subject Alternative Names (SANs): `api.flowforge.local`, `localhost`, `127.0.0.1`
   - A self-signed certificate valid for 365 days

2. Examine the certificate you created:
   - Use `openssl x509 -text` to read the certificate details
   - Identify: the subject, issuer, validity dates, public key algorithm, and Subject Alternative Names
   - Is the issuer the same as the subject? What does this mean?

**Part 2: Configure HTTPS**

3. Configure nginx (from Exercise 3c) to serve HTTPS on port 443 using your self-signed certificate:
   - Redirect HTTP (port 80) to HTTPS (port 443) -- or serve both
   - Use your generated certificate and private key

4. Test the HTTPS connection:
   - Use `curl https://localhost:443` -- what error do you get? Why?
   - Use `curl -k https://localhost:443` -- what does `-k` do? Why does it work now?
   - Use `curl --cacert <your-cert-file> https://api.flowforge.local:443` -- does this work? Why?

**Part 3: Inspect the TLS handshake**

5. Use `openssl s_client` to connect to your HTTPS server:
   ```
   openssl s_client -connect localhost:443
   ```
   In the output, identify:
   - The certificate chain
   - The server's certificate details
   - The TLS version and cipher suite negotiated
   - The session parameters

6. Try connecting with different TLS versions:
   - Can you connect with TLS 1.2? TLS 1.3?
   - What happens if you try TLS 1.0 or 1.1? (These should be disabled)

**Part 4: Understand certificate verification**

7. Answer these questions in a file called `tls-analysis.md`:
   - Why does `curl` (without `-k`) refuse your self-signed certificate?
   - How does `curl` know which CAs to trust? Where are trusted CA certificates stored on Linux?
   - What is the difference between a self-signed certificate and one signed by Let's Encrypt?
   - What would happen in production if you used a self-signed certificate for a public API?
   - Explain the TLS handshake step by step, based on what you observed with `openssl s_client`

### Expected Outcome

- A self-signed certificate and private key for `api.flowforge.local`
- nginx serving HTTPS with TLS termination
- A file `tls-analysis.md` with TLS handshake analysis and certificate documentation
- You can generate certificates, configure HTTPS, and verify TLS connections from the command line

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Explain the TLS handshake in 4-5 steps. What is exchanged at each step?
> 2. What is the difference between the private key and the certificate? What happens if the private key leaks?
> 3. Why do certificates have Subject Alternative Names (SANs)? What happens if the hostname you connect to doesn't match any SAN?
> 4. You need to set up HTTPS for FlowForge in production. Would you use a self-signed certificate? If not, what would you use and how does it work?

---

## What's Next?

Proceed to [Lab 04: Broken Network](lab-04-broken-network.md) -- your Module 2 debugging challenge. Everything you've learned in Labs 01-03 will be tested: packet analysis, DNS, HTTP, ports, firewalls, routing, and TLS.

> **Link back to Module 1**: The debugging methodology you learned in Module 1's Broken Server lab applies here too. The difference is that now your investigation spans the network stack instead of just the local system. Same systematic approach: observe symptoms, form hypotheses, gather evidence, identify root causes.
