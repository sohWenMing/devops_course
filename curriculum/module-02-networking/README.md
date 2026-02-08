# Module 2: Networking Fundamentals

> **Time estimate**: 1.5-2 weeks  
> **Prerequisites**: Complete Module 1 (Linux Deep Dive), Ubuntu machine (or WSL2)  
> **Link forward**: "Every VPC, subnet, security group, and load balancer maps to these concepts"  
> **Link back**: "You learned Linux as the OS layer. Now we add the communication layer that lets machines talk to each other."

---

## Why This Module Matters for DevOps

Every distributed system is a network conversation. When your api-service talks to PostgreSQL, that's a TCP connection traversing IP routing, DNS resolution, and firewall rules. When a user hits your load balancer, that's HTTP over TLS negotiated through a certificate handshake. When your Kubernetes Pod can't reach another Pod, that's a networking problem hiding behind an orchestration abstraction.

Cloud services like AWS VPCs, security groups, and Application Load Balancers are just user-friendly wrappers around the exact concepts in this module. If you understand networking fundamentals, cloud networking is just vocabulary. If you don't, every "security group not working" bug will feel like magic.

This module gives you the mental model to debug connectivity issues at any layer -- from the physical wire to the application payload. That's the difference between an engineer who says "it's a network problem" and an engineer who says "the TCP handshake completes but the server sends a RST after the TLS ClientHello because the certificate's SAN doesn't match the hostname."

---

## Table of Contents

1. [OSI Model & TCP/IP Stack](#1-osi-model--tcpip-stack)
2. [IP Addressing & Subnets](#2-ip-addressing--subnets)
3. [DNS Resolution](#3-dns-resolution)
4. [HTTP Deep Dive](#4-http-deep-dive)
5. [Ports & Sockets](#5-ports--sockets)
6. [Firewalls (iptables/ufw)](#6-firewalls-iptablesufw)
7. [Routing & Gateways](#7-routing--gateways)
8. [Load Balancing Concepts](#8-load-balancing-concepts)
9. [TLS/SSL](#9-tlsssl)

---

## 1. OSI Model & TCP/IP Stack

### The Seven-Layer Model

The OSI (Open Systems Interconnection) model is a conceptual framework that describes how data moves from an application on one machine to an application on another. Think of it as a mental debugging tool -- when something goes wrong, you ask: "Which layer is the problem at?"

| Layer | OSI Name      | TCP/IP Name  | What It Does                         | Protocols/Examples        | DevOps Relevance                    |
|-------|---------------|-------------|--------------------------------------|---------------------------|-------------------------------------|
| 7     | Application   | Application | User-facing protocols                | HTTP, DNS, SSH, SMTP      | Your API endpoints, health checks   |
| 6     | Presentation  | Application | Data formatting, encryption          | TLS/SSL, JSON, gzip       | TLS termination, content encoding   |
| 5     | Session       | Application | Session management, connections      | Sockets, sessions         | WebSocket connections, keep-alives  |
| 4     | Transport     | Transport   | Reliable delivery, port numbers      | TCP, UDP                  | Port mappings, connection issues    |
| 3     | Network       | Internet    | IP addressing, routing               | IP, ICMP                  | Subnets, routing tables, VPCs      |
| 2     | Data Link     | Link        | MAC addresses, local network         | Ethernet, ARP, Wi-Fi      | Switch-level issues, ARP tables    |
| 1     | Physical      | Link        | Bits on a wire/radio wave            | Cables, fiber, wireless   | "Is it plugged in?"                |

In practice, most DevOps work happens at Layers 3-7. But knowing all seven helps you ask the right questions when debugging.

### How Data Flows: Encapsulation

When your api-service sends an HTTP response to a client, here's what happens:

```
Application (Layer 7):  HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"status":"ok"}
        ↓ encapsulate
Transport (Layer 4):    [TCP Header: src_port=8080, dst_port=54321, seq=1, ack=1] + HTTP data
        ↓ encapsulate
Network (Layer 3):      [IP Header: src=10.0.1.10, dst=203.0.113.5] + TCP segment
        ↓ encapsulate
Data Link (Layer 2):    [Ethernet Header: src_mac, dst_mac] + IP packet + [Ethernet Trailer]
        ↓ transmit
Physical (Layer 1):     Electrical signals / light pulses on the wire
```

Each layer wraps (encapsulates) the layer above it with its own header. On the receiving end, each layer strips its header and passes the payload up. This is why `tcpdump` can show you every layer -- it captures the complete frame.

### Architecture Thinking: Why Layers Matter

> **Question to ask yourself**: If networking were one monolithic protocol instead of layers, what would go wrong when you needed to change just one thing (like switching from Wi-Fi to Ethernet)?

Layering gives you:
- **Modularity**: Change one layer without affecting others (swap Ethernet for Wi-Fi, TCP still works)
- **Debugging isolation**: "The IP routing works (Layer 3 is fine) but the TCP connection resets (Layer 4 problem)"
- **Abstraction**: Your Go application uses HTTP (Layer 7) without knowing whether the network underneath is fiber, copper, or wireless

> **You'll use this when**: Debugging Kubernetes networking (Module 8) -- "the Pod can ping the Service IP (Layer 3 works) but can't connect on port 8080 (Layer 4 issue -- is the Service selector correct?)". Configuring AWS security groups (Module 5) -- security groups operate at Layer 4 (ports/protocols), NACLs operate at Layer 3-4.

> **AWS SAA tie-in**: The AWS networking model maps directly to these layers. VPCs and subnets = Layer 3. Security groups = Layer 4. Application Load Balancers = Layer 7. Network Load Balancers = Layer 4. Understanding these layers tells you which AWS service to use for each problem.

---

## 2. IP Addressing & Subnets

### IPv4 Addressing

An IPv4 address is a 32-bit number, written as four octets in decimal: `192.168.1.100`. Each octet is 8 bits (0-255).

```
192      .  168      .  1        .  100
11000000    10101000    00000001    01100100
```

### CIDR Notation & Subnet Masks

CIDR (Classless Inter-Domain Routing) notation specifies how many bits of the address are the **network portion** vs the **host portion**:

- `10.0.0.0/8` → First 8 bits are network, 24 bits for hosts → 16,777,214 usable IPs
- `10.0.0.0/16` → First 16 bits are network, 16 bits for hosts → 65,534 usable IPs
- `10.0.0.0/24` → First 24 bits are network, 8 bits for hosts → 254 usable IPs
- `10.0.0.0/28` → First 28 bits are network, 4 bits for hosts → 14 usable IPs

**How to calculate**:
1. Number of host bits = 32 - prefix length
2. Total addresses in the range = 2^(host bits)
3. Usable IPs = total addresses - 2 (one for network address, one for broadcast)

For `10.0.1.0/24`:
- Network address: `10.0.1.0` (all host bits = 0)
- First usable: `10.0.1.1`
- Last usable: `10.0.1.254`
- Broadcast: `10.0.1.255` (all host bits = 1)
- Subnet mask: `255.255.255.0`

### Private IP Ranges (RFC 1918)

These ranges are reserved for private networks -- they are not routable on the public internet:

| Range | CIDR | Common Use |
|-------|------|------------|
| `10.0.0.0` - `10.255.255.255` | `10.0.0.0/8` | Large organizations, AWS VPCs |
| `172.16.0.0` - `172.31.255.255` | `172.16.0.0/12` | Medium networks, Docker default |
| `192.168.0.0` - `192.168.255.255` | `192.168.0.0/16` | Home networks, small offices |

### Subnet Design for Multi-Tier Applications

A well-designed network separates concerns into subnets:

```
VPC: 10.0.0.0/16 (65,534 IPs)
├── Public Subnet:    10.0.1.0/24 (254 IPs) -- Load balancers, bastion hosts
├── Private Subnet:   10.0.2.0/24 (254 IPs) -- api-service, worker-service
└── Database Subnet:  10.0.3.0/24 (254 IPs) -- PostgreSQL, Redis
```

Why separate subnets?
- **Security isolation**: Database subnet has no internet gateway route → databases are unreachable from the internet
- **Network policies**: Different firewall rules per subnet (public allows HTTP/HTTPS, private allows only internal traffic)
- **Cost management**: NAT gateways only needed for private subnets that need outbound internet access

### Architecture Thinking: Subnet Design Decisions

> **Question to ask yourself**: Why not just put everything in one big subnet? What do you gain by splitting?

The answer is **blast radius reduction**. If an attacker compromises a host in the public subnet, they still can't reach the database because network-level controls prevent it. This is defense in depth -- multiple layers of protection.

> **You'll use this when**: Creating VPCs in AWS (Module 5) -- you'll design subnets across availability zones. Writing Terraform (Module 6) -- you'll codify this subnet scheme. Kubernetes networking (Module 8) -- Pod CIDR ranges use the same concepts.

> **AWS SAA tie-in**: AWS VPCs use exactly this CIDR/subnet model. Each subnet lives in one Availability Zone. You'll create public, private, and database subnets -- the math you learn here is the math you use there. The SAA exam loves to test subnet sizing and non-overlapping CIDR ranges.

---

## 3. DNS Resolution

### What DNS Does

DNS (Domain Name System) translates human-readable names (`api.flowforge.local`) to IP addresses (`10.0.2.10`). Without DNS, you'd need to memorize IP addresses for every service.

### The Resolution Chain

When you type `https://api.flowforge.example.com` in a browser:

```
1. Browser cache       → "Do I already know this?" → No
2. OS resolver cache   → "Has the OS seen this recently?" → No
3. /etc/hosts file     → "Is there a local override?" → No
4. /etc/resolv.conf    → "Which DNS server should I ask?"
5. Recursive resolver  → ISP or configured DNS (e.g., 8.8.8.8)
   ├── Root server (.)     → "Who handles .com?"
   ├── TLD server (.com)   → "Who handles example.com?"
   └── Authoritative NS    → "api.flowforge.example.com = 203.0.113.10"
6. Answer cached at each level with TTL (Time To Live)
```

### DNS Record Types

| Type  | Purpose | Example |
|-------|---------|---------|
| A     | Maps name to IPv4 address | `api.flowforge.com → 203.0.113.10` |
| AAAA  | Maps name to IPv6 address | `api.flowforge.com → 2001:db8::1` |
| CNAME | Alias to another name | `www.flowforge.com → api.flowforge.com` |
| MX    | Mail exchange servers | `flowforge.com → mail.flowforge.com (priority 10)` |
| NS    | Authoritative name servers | `flowforge.com → ns1.dnshost.com` |
| TXT   | Arbitrary text (SPF, verification) | `flowforge.com → "v=spf1 include:..."` |
| SOA   | Start of Authority (zone metadata) | Zone serial, refresh timers |
| SRV   | Service location (host + port) | `_http._tcp.flowforge.com → 10 0 8080 api.flowforge.com` |
| PTR   | Reverse DNS (IP to name) | `10.113.0.203.in-addr.arpa → api.flowforge.com` |

### /etc/hosts and /etc/resolv.conf

Two critical files (remember Module 1's FHS!):

- **`/etc/hosts`**: Local name resolution override. Checked before DNS servers. Useful for development:
  ```
  127.0.0.1   localhost
  10.0.2.10   api.flowforge.local
  10.0.3.10   db.flowforge.local
  ```

- **`/etc/resolv.conf`**: Configures which DNS servers to use:
  ```
  nameserver 8.8.8.8
  nameserver 8.8.4.4
  search flowforge.local
  ```
  The `search` directive means you can type `api` and the resolver will try `api.flowforge.local` automatically.

### Architecture Thinking: DNS in Distributed Systems

> **Question to ask yourself**: What happens when a DNS record changes but clients have the old IP cached? How does TTL affect deployments?

DNS caching is both a performance optimization and a deployment hazard. A long TTL means fewer DNS lookups (faster) but slower propagation of changes. A short TTL means quick updates but more DNS traffic. Blue-green deployments often use DNS switching, which is why TTL matters.

> **You'll use this when**: Configuring Route 53 (AWS's DNS service) in Module 5. Service discovery in Kubernetes (Module 8) -- K8s has its own DNS (CoreDNS) where services get names like `api-service.default.svc.cluster.local`. Docker Compose (Module 4) -- container names become DNS entries on a Docker network.

> **AWS SAA tie-in**: Route 53 is AWS's DNS service. Understanding A records, CNAME records, alias records, and TTLs is essential. The SAA exam tests routing policies (simple, weighted, latency-based, failover) -- all built on DNS concepts.

---

## 4. HTTP Deep Dive

### The Request/Response Cycle

HTTP (Hypertext Transfer Protocol) is the application-layer protocol your API speaks. Every request follows this pattern:

```
Client → Server: Request
  Method  URL             Version
  GET /api/v1/tasks HTTP/1.1
  Host: api.flowforge.com
  Accept: application/json
  Authorization: Bearer eyJ...

Server → Client: Response
  Version  Status
  HTTP/1.1 200 OK
  Content-Type: application/json
  Content-Length: 142
  X-Request-Id: abc-123

  {"tasks":[{"id":1,"name":"Deploy v2","status":"pending"}]}
```

### HTTP Methods (Verbs)

| Method | Purpose | Idempotent | Safe | FlowForge Example |
|--------|---------|------------|------|--------------------|
| GET    | Retrieve a resource | Yes | Yes | `GET /tasks` -- list all tasks |
| POST   | Create a new resource | No | No | `POST /tasks` -- create a task |
| PUT    | Replace a resource entirely | Yes | No | `PUT /tasks/1` -- replace task 1 |
| PATCH  | Partially update a resource | No | No | `PATCH /tasks/1` -- update one field |
| DELETE | Remove a resource | Yes | No | `DELETE /tasks/1` -- delete task 1 |
| HEAD   | Like GET but no body (headers only) | Yes | Yes | Check if resource exists |
| OPTIONS| List allowed methods (CORS preflight) | Yes | Yes | Browser CORS check |

### Status Codes

| Range | Category | Common Codes |
|-------|----------|-------------|
| 1xx | Informational | 101 Switching Protocols (WebSocket upgrade) |
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirection | 301 Moved Permanently, 302 Found, 304 Not Modified |
| 4xx | Client Error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests |
| 5xx | Server Error | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout |

### Headers That Matter

| Header | Direction | Purpose |
|--------|-----------|---------|
| `Host` | Request | Which virtual host to route to |
| `Content-Type` | Both | MIME type of the body (`application/json`, `text/html`) |
| `Authorization` | Request | Authentication credentials (`Bearer token`, `Basic base64`) |
| `Accept` | Request | What content types the client wants |
| `Content-Length` | Both | Size of the body in bytes |
| `Cache-Control` | Both | Caching directives (`no-cache`, `max-age=3600`) |
| `X-Request-Id` | Both | Unique request identifier for tracing |
| `Connection` | Both | `keep-alive` (reuse TCP connection) or `close` |

### HTTP/1.1 vs HTTP/2 vs HTTP/3

| Feature | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---------|----------|--------|--------|
| Multiplexing | No (one request per connection, or pipelining) | Yes (multiple streams per connection) | Yes |
| Header compression | No | HPACK | QPACK |
| Transport | TCP | TCP | QUIC (UDP-based) |
| Server push | No | Yes | Yes |

### Architecture Thinking: Designing HTTP APIs

> **Question to ask yourself**: Why do we use specific status codes instead of always returning 200 with an error message in the body?

Proper status codes enable:
- Load balancers to route based on response status (retry on 503, not on 400)
- Monitoring systems to track error rates (5xx rate is a key SLI)
- Clients to handle errors programmatically without parsing the body
- Caches to know what's cacheable (200) and what's not (POST responses)

> **You'll use this when**: Building FlowForge's REST API (Module 3) -- you'll implement these methods and status codes. Configuring health checks (Module 5, 8) -- health endpoints return 200 when healthy. Setting up monitoring (Module 9) -- you'll track request rates by status code.

> **AWS SAA tie-in**: Application Load Balancers operate at Layer 7 (HTTP). They can route based on URL path, host header, and HTTP method. Understanding HTTP is essential for configuring ALB rules, health checks, and sticky sessions.

---

## 5. Ports & Sockets

### What Ports Do

IP addresses identify machines. Ports identify **services** on a machine. Together, an IP:port pair is a **socket address** -- the unique endpoint for a network connection.

```
10.0.2.10:8080  →  api-service on the app server
10.0.3.10:5432  →  PostgreSQL on the database server
```

Port numbers range from 0-65535:
- **Well-known ports (0-1023)**: Require root/sudo to bind. Reserved for standard services.
- **Registered ports (1024-49151)**: Assigned by IANA but don't require root.
- **Dynamic/ephemeral ports (49152-65535)**: Used by clients for outbound connections.

### Common Ports

| Port | Protocol | Service | FlowForge Context |
|------|----------|---------|-------------------|
| 22   | TCP | SSH | Remote server access |
| 53   | TCP/UDP | DNS | Name resolution |
| 80   | TCP | HTTP | Unencrypted web traffic |
| 443  | TCP | HTTPS | Encrypted web traffic |
| 5432 | TCP | PostgreSQL | FlowForge database |
| 8080 | TCP | HTTP (alt) | FlowForge api-service |
| 6379 | TCP | Redis | Caching (future) |
| 9090 | TCP | Prometheus | Metrics collection (Module 9) |

### Binding: 0.0.0.0 vs 127.0.0.1 vs Specific IP

When a service starts, it **binds** to an address and port. The bind address determines who can connect:

| Bind Address | Who Can Connect | When to Use |
|-------------|----------------|-------------|
| `127.0.0.1:8080` | Only processes on the same machine | Development, services that should ONLY be accessed locally |
| `0.0.0.0:8080` | Any IP address that can reach the machine | Services that need to accept external connections |
| `10.0.2.10:8080` | Only connections arriving on that specific network interface | Multi-homed servers (multiple NICs) |

### Architecture Thinking: Binding and Security

> **Question to ask yourself**: Your database server has PostgreSQL listening on `0.0.0.0:5432`. Even if firewall rules block external access, why is this still a concern?

Defense in depth: if the firewall is misconfigured (or temporarily disabled), a service bound to `0.0.0.0` is immediately exposed. Binding to a private IP (`10.0.3.10:5432`) means even a firewall misconfiguration doesn't expose the service to the public internet.

> **You'll use this when**: Configuring Docker port mappings (Module 4) -- `-p 8080:8080` maps host ports to container ports. Kubernetes Services (Module 8) -- ClusterIP vs NodePort vs LoadBalancer controls who can reach the Service. Security group rules (Module 5) -- you specify which ports to allow.

> **AWS SAA tie-in**: Security groups are port-based access controls. You'll write rules like "allow TCP port 5432 from the app subnet only." Understanding binding and ports is essential for designing these rules correctly.

---

## 6. Firewalls (iptables/ufw)

### What Firewalls Do

A firewall inspects network packets and decides whether to **accept**, **drop**, or **reject** each one based on rules. Think of it as a security guard checking IDs at a door.

### iptables: The Low-Level Tool

`iptables` is the traditional Linux firewall. It organizes rules into **chains**:

| Chain | When It Applies |
|-------|----------------|
| INPUT | Packets arriving at the machine (destined for local processes) |
| OUTPUT | Packets leaving the machine (sent by local processes) |
| FORWARD | Packets passing through the machine (routing/NAT) |

Each rule in a chain has:
- **Match criteria**: Source IP, destination IP, protocol, port, interface
- **Target/action**: ACCEPT, DROP, REJECT, LOG

Rules are evaluated **in order** -- the first matching rule wins. If no rule matches, the chain's **default policy** applies.

**Example rule set for FlowForge**:
```
# Default policy: drop everything
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow established/related connections (responses to our outbound requests)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow loopback (localhost traffic)
iptables -A INPUT -i lo -j ACCEPT

# Allow SSH from admin network only
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/24 -j ACCEPT

# Allow HTTP/HTTPS from anywhere (public API)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow PostgreSQL from app subnet only
iptables -A INPUT -p tcp --dport 5432 -s 10.0.2.0/24 -j ACCEPT
```

### ufw: The Friendly Frontend

`ufw` (Uncomplicated Firewall) is a user-friendly wrapper around iptables:

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow from 10.0.0.0/24 to any port 22       # SSH from admin network
ufw allow 80/tcp                                   # HTTP from anywhere
ufw allow 443/tcp                                  # HTTPS from anywhere
ufw allow from 10.0.2.0/24 to any port 5432      # PostgreSQL from app subnet
ufw enable
```

Same rules, friendlier syntax. Under the hood, ufw generates iptables rules.

### Stateful vs Stateless

**iptables is stateful by default** (when using `conntrack`/`state` modules):
- You allow an inbound connection on port 80
- The response packets going back to the client are automatically allowed (ESTABLISHED state)
- You don't need separate outbound rules for response traffic

**This is exactly how AWS Security Groups work** -- they're stateful. NACLs, by contrast, are stateless (you need explicit inbound AND outbound rules).

### Architecture Thinking: Firewall Design Philosophy

> **Question to ask yourself**: Should you default to allowing everything and blocking specific threats, or default to blocking everything and allowing specific services?

The answer is always **default deny**. Start with "block everything" and explicitly allow only what's needed. This is the principle of least privilege applied to networking.

> **You'll use this when**: Creating AWS security groups (Module 5) -- they're the cloud equivalent of iptables rules. Writing Kubernetes NetworkPolicies (Module 10) -- default deny ingress/egress, then allow specific flows. Hardening Docker (Module 4) -- Docker modifies iptables rules for port mappings.

> **AWS SAA tie-in**: Security groups = stateful (like iptables with conntrack). NACLs = stateless (like iptables without state tracking). The SAA exam loves to test the difference.

---

## 7. Routing & Gateways

### How Routing Works

When a packet needs to go from point A to point B, the **routing table** determines the next hop:

```bash
$ ip route show
default via 10.0.1.1 dev eth0                # Default gateway -- "if nothing else matches, send here"
10.0.1.0/24 dev eth0 proto kernel scope link  # Local subnet -- deliver directly
10.0.2.0/24 via 10.0.1.1 dev eth0            # App subnet -- through the gateway
10.0.3.0/24 via 10.0.1.1 dev eth0            # DB subnet -- through the gateway
```

**Routing decisions**:
1. Kernel checks: "Is the destination in my local subnet?" → Deliver directly (Layer 2, ARP)
2. If not: "Which route matches the destination?" → Send to the next-hop gateway
3. If no route matches: "Is there a default route?" → Send to the default gateway
4. If no default route: → "Destination unreachable" error

### Default Gateway

The default gateway is the router that connects your local network to the rest of the world. For a machine in a private subnet, it's typically the NAT gateway or a router that knows how to reach other subnets.

```
api-service (10.0.2.10)
    → default gateway (10.0.2.1)
        → router
            → db-server (10.0.3.10)
```

### Network Address Translation (NAT)

NAT allows machines with private IPs to communicate with the public internet by rewriting packet headers:

```
Internal: 10.0.2.10:54321 → 203.0.113.50:443
NAT rewrites source:
External: 198.51.100.1:12345 → 203.0.113.50:443
```

The NAT device keeps a translation table so return traffic gets routed back to the correct internal machine. This is how your entire home network shares one public IP.

### Architecture Thinking: Routing in Multi-Tier Architectures

> **Question to ask yourself**: Why would you put your database on a subnet with NO route to the internet (no internet gateway, no NAT gateway)?

Because the database should never initiate outbound connections to the internet, and the internet should never be able to reach it. If the database needs updates (e.g., apt packages), you use a private endpoint or a bastion host -- never direct internet access.

> **You'll use this when**: Designing VPC route tables (Module 5) -- public subnets route through an Internet Gateway, private subnets route through a NAT Gateway. Understanding Kubernetes networking (Module 8) -- kube-proxy manages routing between Services and Pods. Setting up Docker networks (Module 4) -- Docker creates bridge networks with their own routing.

> **AWS SAA tie-in**: VPC routing is a core SAA topic. You need to understand route tables, Internet Gateways, NAT Gateways, and VPC peering. The exam tests whether you can design a network where public, private, and database tiers have exactly the right connectivity.

---

## 8. Load Balancing Concepts

### Why Load Balance?

A single server has limits: CPU, memory, network bandwidth, concurrent connections. Load balancing distributes traffic across multiple servers to:
- **Increase capacity**: Handle more requests than one server can
- **Improve reliability**: If one server dies, others keep serving
- **Enable deployments**: Rolling updates without downtime

### Layer 4 vs Layer 7 Load Balancing

| Feature | L4 (Transport) | L7 (Application) |
|---------|----------------|-------------------|
| Operates at | TCP/UDP level | HTTP/HTTPS level |
| Sees | IP addresses, ports | URLs, headers, cookies |
| Routing decisions | Based on IP:port | Based on URL path, host header, headers |
| Speed | Faster (less processing) | Slower (must parse HTTP) |
| TLS | Passes through or terminates | Always terminates |
| Use case | TCP services, databases, high throughput | Web apps, APIs, path-based routing |
| AWS equivalent | Network Load Balancer (NLB) | Application Load Balancer (ALB) |

### Load Balancing Algorithms

| Algorithm | How It Works | When to Use |
|-----------|-------------|-------------|
| Round-robin | Rotate through servers sequentially | Servers are identical, requests are similar |
| Weighted round-robin | Round-robin but some servers get more traffic | Servers have different capacities |
| Least connections | Send to the server with fewest active connections | Long-lived connections (WebSockets) |
| IP hash | Hash the client IP to select a server | Stateful apps needing session affinity |
| Random | Pick a random server | Simple, surprisingly effective at scale |

### Health Checks

A load balancer needs to know which servers are healthy:
- **Active health checks**: LB periodically sends requests (e.g., `GET /health`) and checks responses
- **Passive health checks**: LB monitors real traffic for errors
- **Unhealthy threshold**: How many failures before marking a server as down
- **Healthy threshold**: How many successes before marking a server as up again

### Reverse Proxy Pattern

A reverse proxy (like nginx) sits in front of your application and forwards requests:

```
Client → nginx (reverse proxy) → api-service-1
                                → api-service-2
                                → api-service-3
```

This is the foundation of every production deployment. The reverse proxy handles:
- Load balancing across multiple instances
- TLS termination (handle HTTPS, forward plain HTTP internally)
- Static file serving
- Rate limiting
- Request logging

### Architecture Thinking: Choosing a Load Balancer

> **Question to ask yourself**: FlowForge has an HTTP REST API and a WebSocket endpoint for real-time task updates. Which type of load balancer do you need?

The answer depends on the features you need. L7 for path-based routing and HTTP-aware health checks. But if you have WebSocket connections, you also need to consider connection affinity (sticky sessions) and connection draining during deployments.

> **You'll use this when**: Setting up nginx as a reverse proxy (this module, Lab 3c). Configuring AWS Application Load Balancers (Module 5). Kubernetes Ingress controllers (Module 8) -- they ARE L7 load balancers. Docker Compose (Module 4) -- running multiple instances behind a proxy.

> **AWS SAA tie-in**: ALB vs NLB is a common SAA question. ALB for HTTP/HTTPS, NLB for TCP/UDP/high-performance. The exam also tests health check configuration, cross-zone load balancing, and connection draining.

---

## 9. TLS/SSL

### What TLS Does

TLS (Transport Layer Security) provides three guarantees:
1. **Confidentiality**: Data is encrypted -- eavesdroppers can't read it
2. **Integrity**: Data hasn't been tampered with in transit
3. **Authentication**: You're talking to the real server, not an impostor

SSL (Secure Sockets Layer) is the predecessor to TLS. The terms are often used interchangeably, but "TLS" is the correct modern term.

### The TLS Handshake (Simplified)

```
Client                                Server
  |                                      |
  |--- ClientHello ------------------>   |  "I support TLS 1.3, these ciphers..."
  |                                      |
  |<-- ServerHello + Certificate ----    |  "Let's use TLS 1.3 with this cipher. Here's my cert."
  |                                      |
  |   [Client verifies certificate]      |
  |   - Is it signed by a trusted CA?    |
  |   - Is the hostname in the SAN?      |
  |   - Is it expired?                   |
  |                                      |
  |--- Key Exchange ----------------->   |  "Here's my part of the key exchange"
  |<-- Key Exchange ------------------   |  "Here's mine"
  |                                      |
  |   [Both derive session keys]         |
  |                                      |
  |=== Encrypted Application Data ===    |  All HTTP traffic is now encrypted
```

### Certificates

A TLS certificate contains:
- **Subject**: Who the certificate belongs to (e.g., `api.flowforge.com`)
- **Subject Alternative Names (SANs)**: Additional valid hostnames/IPs
- **Issuer**: The Certificate Authority (CA) that signed it
- **Validity period**: Not Before / Not After dates
- **Public key**: Used for key exchange
- **Signature**: The CA's cryptographic signature proving authenticity

**Certificate chain**:
```
Root CA (trusted, built into browser/OS)
  └── Intermediate CA (signed by Root)
        └── Server Certificate (signed by Intermediate)
```

### Self-Signed vs CA-Signed

| | Self-Signed | CA-Signed |
|-|-------------|-----------|
| Signed by | The server itself | A trusted Certificate Authority |
| Browsers trust it? | No (security warning) | Yes |
| Cost | Free | Free (Let's Encrypt) to expensive |
| Use case | Development, internal services | Production, public-facing |

### Architecture Thinking: TLS Termination

> **Question to ask yourself**: Where should TLS be terminated -- at the load balancer or at each application server? What are the trade-offs?

**TLS termination at the load balancer** (most common):
- Pro: One place to manage certificates, reduces CPU load on app servers
- Pro: Load balancer can inspect HTTP headers for routing
- Con: Traffic between LB and app servers is unencrypted (but usually on a private network)

**End-to-end TLS** (app servers handle TLS):
- Pro: Traffic encrypted everywhere, even on the private network
- Con: Every server needs certificates, more CPU usage, LB can't inspect HTTP

> **You'll use this when**: Configuring HTTPS for FlowForge (this module, Lab 3d). Setting up ALB with ACM certificates (Module 5). Kubernetes Ingress with TLS (Module 8). CI/CD pipeline to renew certificates (Module 7). Security hardening (Module 10) -- encryption in transit.

> **AWS SAA tie-in**: AWS Certificate Manager (ACM) provides free TLS certificates. You'll attach them to ALBs and CloudFront distributions. The SAA exam tests end-to-end encryption, TLS termination points, and certificate management.

---

## Labs

| Lab | Exercises | Topic |
|-----|-----------|-------|
| [Lab 01: TCP/IP & Subnets](lab-01-tcp-ip-subnets.md) | 1a, 1b | Packet capture with tcpdump, subnet calculation and network design |
| [Lab 02: DNS, HTTP & Ports](lab-02-dns-http-ports.md) | 2a, 2b, 2c | DNS resolution, HTTP inspection, ports and sockets |
| [Lab 03: Firewalls, Routing & TLS](lab-03-firewalls-routing-tls.md) | 3a, 3b, 3c, 3d | iptables/ufw, network namespaces, nginx reverse proxy, TLS certificates |
| [Lab 04: Broken Network](lab-04-broken-network.md) | Debugging challenge | Multi-layered network troubleshooting |

---

## What's Next?

After completing all labs and the [Exit Gate Checklist](checklist.md), you're ready for [Module 3: Building FlowForge in Go](../module-03-go-app/README.md). You'll take everything you learned about networking and build the actual applications that communicate over these protocols. The TCP connections, HTTP requests, database ports, and DNS names you explored here become real Go code.

> **Connection to Module 1**: In Module 1, you learned how a single Linux machine works -- processes, files, permissions, services. In this module, you learned how machines talk to each other -- packets, protocols, ports, routing. In Module 3, you'll build the application that uses both layers. Every concept stacks.
