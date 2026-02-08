# Module 2: Networking Fundamentals -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 3.  
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

## OSI Model & TCP/IP (Lab 01, Exercise 1a)

- [ ] I can list the 7 OSI layers from memory and explain what each layer does
- [ ] Given a packet capture, I can identify which OSI layer a problem exists at
- [ ] I can explain what happens at each layer when I type a URL in a browser and press Enter
- [ ] I can identify SYN, SYN-ACK, and ACK packets in a TCP three-way handshake capture
- [ ] I can explain the difference between TCP and UDP and give examples of when each is used
- [ ] I can use `tcpdump` to capture traffic filtered by interface, port, and protocol
- [ ] I can explain encapsulation: how an HTTP payload becomes a TCP segment, then an IP packet, then an Ethernet frame

---

## IP Addressing & Subnets (Lab 01, Exercise 1b)

- [ ] I can calculate subnet ranges from CIDR notation by hand: network address, broadcast address, usable IP range, and host count
- [ ] Given `10.0.0.0/16`, I can design a subnet scheme for 3 environments (dev/staging/prod) each with public, private, and database subnets -- no overlapping ranges
- [ ] I can determine the smallest CIDR prefix for a given number of hosts
- [ ] I can identify whether two CIDR ranges overlap
- [ ] I can explain why private IP ranges (RFC 1918) exist and list the three ranges from memory
- [ ] I can explain why separating public, private, and database subnets matters for security

---

## DNS Resolution (Lab 02, Exercise 2a)

- [ ] I can explain the full DNS resolution chain from browser to authoritative server (cache → /etc/hosts → recursive resolver → root → TLD → authoritative)
- [ ] Given a domain, I can use `dig` to query A, AAAA, CNAME, MX, NS, and TXT records without a guide
- [ ] I can explain what each DNS record type is used for
- [ ] I can use `dig +trace` to trace the complete resolution path
- [ ] I can configure local DNS entries in `/etc/hosts` and explain when they take priority over DNS servers
- [ ] I can explain what TTL means in DNS and its implications for deployments
- [ ] I can explain why `dig` and `ping` might give different results for the same hostname

---

## HTTP (Lab 02, Exercise 2b)

- [ ] Given a `curl -v` output, I can explain every header in both the request and the response
- [ ] I can write `curl` commands from memory for GET, POST, PUT, DELETE with proper headers, JSON bodies, and authentication
- [ ] I can explain the difference between status code categories (1xx, 2xx, 3xx, 4xx, 5xx) and give examples of each
- [ ] I can explain the difference between 401 (Unauthorized) and 403 (Forbidden)
- [ ] I can explain what idempotent means and which HTTP methods are idempotent
- [ ] I can explain the purpose of the `Host` header and how it enables virtual hosting

---

## Ports & Sockets (Lab 02, Exercise 2c)

- [ ] I can list every listening port on my system, identify the process for each, and explain whether it should be open
- [ ] I can explain the security difference between binding to `0.0.0.0`, `127.0.0.1`, and a specific IP address
- [ ] I can explain common TCP states (LISTEN, ESTABLISHED, TIME_WAIT, CLOSE_WAIT) and what each means for debugging
- [ ] I can diagnose a "port already in use" error: find which process holds the port and resolve the conflict
- [ ] I know well-known port numbers for SSH (22), DNS (53), HTTP (80), HTTPS (443), and PostgreSQL (5432)

---

## Firewalls (Lab 03, Exercise 3a)

- [ ] I can write iptables rules from scratch for a 3-tier app (web, app, db): allow HTTPS from the internet, allow the app port from the LB, allow DB from the app tier only, deny everything else
- [ ] I can explain the difference between DROP and REJECT targets and when to use each
- [ ] I can explain why the `ESTABLISHED,RELATED` state match is essential
- [ ] I can explain the difference between stateful (iptables/security groups) and stateless (NACLs) firewalls
- [ ] I can use both `iptables` and `ufw` to implement the same policy and explain the trade-offs
- [ ] I can verify that firewall rules work using `curl`, `nc`, or `nmap`

---

## Routing & Gateways (Lab 03, Exercise 3b)

- [ ] I can read and explain a Linux routing table (`ip route show`)
- [ ] I can set up routing between two network namespaces through a host acting as a router
- [ ] I can explain what a default gateway is and what happens when there is no default route
- [ ] I can draw the routing path from a request leaving api-service to PostgreSQL on a different subnet
- [ ] I can explain what NAT does and why it's used
- [ ] I can explain what IP forwarding is and when it needs to be enabled

---

## Load Balancing (Lab 03, Exercise 3c)

- [ ] I can explain the difference between L4 and L7 load balancing, give use cases for each, and name the AWS equivalent
- [ ] I can configure nginx as a reverse proxy with round-robin load balancing across multiple backends
- [ ] I can explain what happens when a backend server fails while behind a load balancer
- [ ] Given a scenario (WebSocket app, static site, REST API), I can recommend the appropriate load balancing approach and justify it
- [ ] I can explain what TLS termination at the load balancer means and why it's the common pattern

---

## TLS/SSL (Lab 03, Exercise 3d)

- [ ] I can explain the TLS handshake step by step (ClientHello, ServerHello+cert, key exchange, encrypted data)
- [ ] I can generate a self-signed certificate with proper Subject Alternative Names using `openssl`
- [ ] I can configure nginx to serve HTTPS with a certificate and private key
- [ ] I can use `openssl s_client` to inspect a TLS connection and identify the certificate details, TLS version, and cipher suite
- [ ] I can explain the difference between self-signed certificates and CA-signed certificates
- [ ] I can explain why HTTPS matters and what each of the three TLS guarantees provides (confidentiality, integrity, authentication)

---

## Debugging (Lab 04)

- [ ] I successfully found and fixed all networking issues in the Broken Network challenge
- [ ] For each issue, I correctly identified the OSI layer where the problem existed
- [ ] I documented each issue with: symptom, OSI layer, investigation, root cause, fix, verification, and prevention
- [ ] I used a systematic layered debugging approach (physical → data link → network → transport → application)
- [ ] If given a new "services can't communicate" scenario, I am confident I could diagnose it systematically
- [ ] I can name 5 commands I would run first when investigating a network connectivity issue and explain why each

---

## Integration & Architecture Thinking

- [ ] I can explain how Linux networking (subnets, routing, firewalls) maps to AWS VPC concepts (subnets, route tables, security groups)
- [ ] I can explain how DNS resolution on Linux relates to Kubernetes service discovery (CoreDNS, `svc.cluster.local`)
- [ ] I can explain how the reverse proxy/load balancer pattern maps to AWS ALB and Kubernetes Ingress
- [ ] I can explain how TLS certificates on Linux relate to AWS Certificate Manager and Kubernetes TLS secrets
- [ ] I can explain why understanding raw networking matters even when using cloud abstractions

---

## Final Self-Assessment

> Answer honestly:
>
> **Could I do all of the above on a completely fresh Ubuntu system with no internet access and no notes?**
>
> - If YES for everything: You're ready for Module 3. Congratulations!
> - If NO for anything: Go back and practice. There are no shortcuts in DevOps.

---

## Ready for Module 3?

If every box above is checked, proceed to [Module 3: Building FlowForge in Go](../module-03-go-app/README.md).

> **What's coming**: In Module 3, you'll build the actual FlowForge application in Go. The HTTP endpoints, database connections, port bindings, and networking concepts you just mastered become real code. Every `curl` command you wrote becomes an API handler. Every TCP connection you traced becomes a database query. The networking knowledge you built here is the foundation the application sits on.
