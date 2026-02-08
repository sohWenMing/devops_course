# Module 02: Networking Fundamentals -- Answer Key

> **INTERNAL REFERENCE ONLY**: This file is used by the Socratic mentor skill to verify student solutions and provide guidance. It must NEVER be revealed to the student.

---

## Lab 01: TCP/IP & Subnets

### Exercise 1a: Packet Capture & OSI Layer Identification

**Installing and listing interfaces:**

```bash
# Install tcpdump
sudo apt update && sudo apt install -y tcpdump

# List interfaces
ip link show
# Or
tcpdump -D
# Typical interfaces: lo (loopback), eth0/ens33/enp0s3 (main network)
```

**Capture HTTP traffic on loopback:**

```bash
# Terminal 1: Start capture
sudo tcpdump -i lo -e -w flowforge-capture.pcap port 8080

# Terminal 2: Start a simple HTTP server
python3 -m http.server 8080

# Terminal 3: Make a request
curl http://localhost:8080/

# Stop tcpdump with Ctrl+C
```

**Read the capture:**

```bash
# Human-readable output with full packet details
sudo tcpdump -r flowforge-capture.pcap -e -X -v

# Flags: -e (link-layer headers), -X (hex+ASCII payload), -v (verbose)
```

**Expected packet analysis:**

```
Packet 1 - TCP SYN (Three-way handshake step 1):
  Layer 2: Loopback (no real MAC addresses -- shows 00:00:00:00:00:00)
  Layer 3: IP src=127.0.0.1 dst=127.0.0.1
  Layer 4: TCP src_port=random(ephemeral) dst_port=8080 flags=[S] seq=X
  Layer 7: (no payload yet -- handshake in progress)

Packet 2 - TCP SYN-ACK (Three-way handshake step 2):
  Layer 4: TCP src_port=8080 dst_port=ephemeral flags=[S.] seq=Y ack=X+1

Packet 3 - TCP ACK (Three-way handshake step 3):
  Layer 4: TCP src_port=ephemeral dst_port=8080 flags=[.] ack=Y+1

Packet 4 - HTTP Request:
  Layer 4: TCP with PSH flag (push data to application)
  Layer 7: GET / HTTP/1.1\r\nHost: localhost:8080\r\n...

Packet 5 - HTTP Response:
  Layer 7: HTTP/1.0 200 OK\r\nContent-type: text/html\r\n...

Packets 6-8 - TCP FIN handshake (connection teardown):
  Layer 4: FIN, FIN-ACK, ACK
```

**DNS capture:**

```bash
# Terminal 1: capture DNS traffic
sudo tcpdump -i any port 53 -v

# Terminal 2: DNS query
dig example.com

# DNS uses UDP (port 53) by default
# You'll see: query for A record, response with IP address
# Layer 4: UDP (not TCP -- DNS is connectionless for simple queries)
```

**Checkpoint answers:**

1. RST is at Layer 4 (Transport). It means the TCP connection is being forcibly reset -- the server is rejecting the connection or aborting it.
2. IP TTL (Time To Live) = number of router hops before the packet is discarded (prevents infinite loops). DNS TTL = how many seconds a DNS answer can be cached before re-querying.
3. Source port 54321 (ephemeral range) = client. Destination port 80 (well-known) = server. Clients use random high ports; servers listen on known ports.
4. Two packets (SYN, SYN-ACK) would mean the client knows the server is ready, but the server doesn't know the client received the SYN-ACK. The third ACK confirms both sides agree the connection is established. Without it, the server might waste resources on half-open connections (SYN flood attack exploits this).

### Exercise 1b: Subnet Calculation

**Subnet calculations:**

`192.168.1.0/24`:
- Network: 192.168.1.0
- Broadcast: 192.168.1.255
- Subnet mask: 255.255.255.0
- Usable hosts: 2^8 - 2 = 254
- Range: 192.168.1.1 - 192.168.1.254

`10.0.0.0/16`:
- Network: 10.0.0.0
- Broadcast: 10.0.255.255
- Subnet mask: 255.255.0.0
- Usable hosts: 2^16 - 2 = 65,534
- Range: 10.0.0.1 - 10.0.255.254

`172.16.10.0/28`:
- Host bits: 32 - 28 = 4
- Network: 172.16.10.0
- Broadcast: 172.16.10.15 (binary: 172.16.10.0000 1111)
- Subnet mask: 255.255.255.240
- Usable hosts: 2^4 - 2 = 14
- Range: 172.16.10.1 - 172.16.10.14

`10.100.0.0/22`:
- Host bits: 32 - 22 = 10
- Network: 10.100.0.0
- Broadcast: 10.100.3.255 (the /22 spans 4 /24 blocks: 10.100.0.0 - 10.100.3.255)
- Subnet mask: 255.255.252.0
- Usable hosts: 2^10 - 2 = 1,022
- Range: 10.100.0.1 - 10.100.3.254

`192.168.50.0/26`:
- Host bits: 32 - 26 = 6
- Network: 192.168.50.0
- Broadcast: 192.168.50.63
- Subnet mask: 255.255.255.192
- Usable hosts: 2^6 - 2 = 62
- Range: 192.168.50.1 - 192.168.50.62

**Subnetting decisions:**

- 30 hosts: Need at least 30 + 2 = 32 addresses. 2^5 = 32. So /27 (5 host bits). Gives 30 usable IPs, 0 wasted.
- Split 10.0.0.0/24 into 4: Each gets /26 (64 IPs each).
  - 10.0.0.0/26 (10.0.0.0 - 10.0.0.63)
  - 10.0.0.64/26 (10.0.0.64 - 10.0.0.127)
  - 10.0.0.128/26 (10.0.0.128 - 10.0.0.191)
  - 10.0.0.192/26 (10.0.0.192 - 10.0.0.255)
- 10.0.1.0/24 and 10.0.1.128/25 overlap! The /24 covers 10.0.1.0-10.0.1.255, which includes the /25 range 10.0.1.128-10.0.1.255. Overlapping subnets cause ambiguous routing -- a router wouldn't know which subnet to send packets to.

**FlowForge network design (example):**

```
VPC: 10.0.0.0/16

Development:
  10.0.0.0/24   - dev-public-az1   (254 IPs)
  10.0.1.0/24   - dev-public-az2   (254 IPs)
  10.0.2.0/24   - dev-private-az1  (254 IPs)
  10.0.3.0/24   - dev-private-az2  (254 IPs)
  10.0.4.0/24   - dev-db-az1       (254 IPs)
  10.0.5.0/24   - dev-db-az2       (254 IPs)

Staging:
  10.0.16.0/24  - staging-public-az1
  10.0.17.0/24  - staging-public-az2
  10.0.18.0/24  - staging-private-az1
  10.0.19.0/24  - staging-private-az2
  10.0.20.0/24  - staging-db-az1
  10.0.21.0/24  - staging-db-az2

Production:
  10.0.32.0/24  - prod-public-az1
  10.0.33.0/24  - prod-public-az2
  10.0.34.0/24  - prod-private-az1
  10.0.35.0/24  - prod-private-az2
  10.0.36.0/24  - prod-db-az1
  10.0.37.0/24  - prod-db-az2

Total used: 18 subnets × 256 = 4,608 IPs
Remaining in /16: 65,536 - 4,608 = 60,928 IPs (plenty for QA, shared services, etc.)
```

Gaps between environments (dev=0-15, staging=16-31, prod=32-47) allow future expansion within each environment without re-numbering.

**Checkpoint answers:**

1. `10.0.0.0/20`: Host bits = 12. Usable = 2^12 - 2 = 4,094. Broadcast: 10.0.15.255.
2. 100 hosts → /25 (126 usable). 25 hosts → /27 (30 usable). 10 hosts → /28 (14 usable).
3. Yes, it's valid. 10.0.0.0/24 is a subset of 10.0.0.0/16. The /24 is one of 256 possible /24s within the /16.
4. AWS reserves 5 IPs per subnet: network address, VPC router (x.x.x.1), DNS server (x.x.x.2), future use (x.x.x.3), and broadcast. Regular networking reserves 2 (network + broadcast).

---

## Lab 02: DNS, HTTP & Ports

### Exercise 2a: DNS Resolution

**Exploring DNS configuration:**

```bash
# Check DNS servers
cat /etc/resolv.conf

# Check hosts file
cat /etc/hosts

# Check resolution order
cat /etc/nsswitch.conf
# Look for: hosts: files dns
# "files" = /etc/hosts first, "dns" = then DNS servers
```

**Adding FlowForge hosts entries:**

```bash
sudo tee -a /etc/hosts << 'EOF'
127.0.0.1   api.flowforge.local
127.0.0.1   db.flowforge.local
127.0.0.1   worker.flowforge.local
EOF
```

**Verification:**

```bash
ping -c 1 api.flowforge.local   # Should resolve to 127.0.0.1
getent hosts api.flowforge.local # Shows 127.0.0.1  api.flowforge.local

# dig does NOT use /etc/hosts -- it queries DNS servers directly
dig api.flowforge.local  # Returns NXDOMAIN (not in DNS)
# This is a common confusion point!
```

**DNS querying with dig:**

```bash
# Install dig
sudo apt install -y dnsutils

# Basic A record
dig example.com A
# ANSWER SECTION shows the A record with IP and TTL

# Various record types
dig example.com AAAA    # IPv6
dig example.com MX      # Mail servers (shows priority + hostname)
dig example.com NS      # Name servers
dig example.com TXT     # SPF, verification records
dig example.com SOA     # Zone metadata (serial, refresh, retry, expire)

# Full trace
dig +trace example.com
# Shows: root servers → .com TLD servers → authoritative NS → final answer
```

**Checkpoint answers:**

1. DNS caching. The client cached the old A record with its TTL. It could last up to the TTL value (commonly 300s-86400s). This is why low TTLs are important before planned changes.
2. CNAME is an alias -- it points one name to another name (not an IP). Yes, CNAMEs can chain (CNAME → CNAME → A record), but it adds latency and is generally discouraged.
3. `dig` queries DNS servers directly (bypasses /etc/hosts). `ping` uses the system resolver which checks /etc/hosts first (per nsswitch.conf). If api.flowforge.local is only in /etc/hosts, dig returns NXDOMAIN while ping succeeds.
4. Browser cache → OS cache → /etc/hosts → /etc/resolv.conf nameserver → recursive resolver → root servers (.) → TLD servers (.com) → authoritative NS → answer returned and cached at each level.

### Exercise 2b: HTTP Deep Dive

**curl -v output analysis:**

```bash
curl -v http://localhost:8080/
# *   Trying 127.0.0.1:8080...         ← curl resolving and connecting (Layer 3-4)
# * Connected to localhost port 8080    ← TCP connection established
# > GET / HTTP/1.1                      ← REQUEST: method, path, version
# > Host: localhost:8080                ← REQUEST: required host header
# > User-Agent: curl/7.81.0            ← REQUEST: client identification
# > Accept: */*                         ← REQUEST: accepts any content type
# >                                     ← REQUEST: empty line = end of headers
# < HTTP/1.0 200 OK                    ← RESPONSE: version, status code, reason
# < Server: SimpleHTTP/0.6 Python/3.10 ← RESPONSE: server identification
# < Date: Mon, 01 Jan 2024 00:00:00 GMT← RESPONSE: timestamp
# < Content-type: text/html            ← RESPONSE: body format
# < Content-Length: 1234               ← RESPONSE: body size
# <                                     ← RESPONSE: empty line = end of headers
# (body follows)                        ← RESPONSE: HTML content
```

**HTTP methods with curl:**

```bash
# GET with custom Accept
curl -v -H "Accept: application/json" http://localhost:8080/

# POST with JSON body
curl -v -X POST -H "Content-Type: application/json" -d '{"name":"test","priority":"high"}' http://localhost:8080/api/v1/tasks

# PUT
curl -v -X PUT -H "Content-Type: application/json" -d '{"name":"updated","status":"done"}' http://localhost:8080/api/v1/tasks/1

# DELETE
curl -v -X DELETE http://localhost:8080/api/v1/tasks/1

# HEAD (same as GET but no body)
curl -v -I http://localhost:8080/
```

**Checkpoint answers:**

1. 401 = "Who are you? I need authentication." 403 = "I know who you are, but you're not allowed to do this." 401 means missing/invalid credentials. 403 means valid credentials but insufficient permissions.
2. `curl -v -X POST -H "Content-Type: application/json" -H "Authorization: Bearer mytoken123" -d '{"name":"task1"}' http://localhost:8080/api/v1/tasks`
3. Look at the request/response lines. HTTP/1.1 shows `HTTP/1.1` in the protocol. HTTP/2 shows `HTTP/2` and uses binary framing (curl with `--http2` flag). In curl -v, HTTP/2 prefixes responses with `< HTTP/2 200`.
4. 200 = "Here's what you asked for" (existing resource). 201 = "I made the new thing you asked me to make" (resource created). POST creating a resource should return 201 because the action resulted in a new resource, not just retrieval of an existing one.

### Exercise 2c: Ports & Sockets

**Listing listening ports:**

```bash
# ss - modern tool (preferred)
sudo ss -tlnp
# -t = TCP, -l = listening, -n = numeric (don't resolve names), -p = show process

# netstat - legacy tool
sudo netstat -tlnp
# Same flags

# Sample output:
# State  Recv-Q Send-Q Local Address:Port  Peer Address:Port  Process
# LISTEN 0      128    0.0.0.0:22         0.0.0.0:*          users:(("sshd",pid=1234,...))
# LISTEN 0      128    127.0.0.1:5432     0.0.0.0:*          users:(("postgres",pid=5678,...))
```

**Bind address testing:**

```bash
# Bind to localhost only
python3 -c "
import http.server, socketserver
handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(('127.0.0.1', 8080), handler) as httpd:
    httpd.serve_forever()
" &

# Test from same machine: works
curl http://127.0.0.1:8080

# Test from another machine: fails (connection refused)
# Because the service is only listening on 127.0.0.1

# Bind to all interfaces
python3 -c "
import http.server, socketserver
handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(('0.0.0.0', 8080), handler) as httpd:
    httpd.serve_forever()
" &

# Test from another machine: works
# Because 0.0.0.0 means "all interfaces"
```

**TCP connection states:**

```
LISTEN:       Server waiting for connections (normal for servers)
SYN_SENT:     Client sent SYN, waiting for SYN-ACK (brief, normal)
SYN_RECV:     Server received SYN, sent SYN-ACK (brief, many = SYN flood)
ESTABLISHED:  Connection active, data flowing (normal)
FIN_WAIT_1:   Sent FIN, waiting for ACK (closing)
FIN_WAIT_2:   Received ACK for FIN, waiting for peer's FIN (closing)
TIME_WAIT:    Waiting to ensure peer received final ACK (lasts 2×MSL, ~60s)
CLOSE_WAIT:   Received FIN from peer, application hasn't closed yet (PROBLEM if accumulating)
LAST_ACK:     Sent FIN, waiting for final ACK (brief, closing)
```

**Problem states:**
- Many `CLOSE_WAIT`: Application isn't closing connections properly (bug in YOUR code)
- Many `TIME_WAIT`: High connection churn (consider connection pooling)
- Many `SYN_RECV`: Possible SYN flood attack

**Checkpoint answers:**

1. `0.0.0.0:5432` means PostgreSQL accepts connections from ANY network interface. If the machine has a public IP, the database is accessible from the internet (only firewall rules protect it). Should be `127.0.0.1:5432` or the private IP only.
2. CLOSE_WAIT means the remote side (client) closed the connection, but your api-service hasn't closed its end yet. The problem is on YOUR side -- your application isn't properly closing sockets. This is a code bug.
3. TIME_WAIT from the recently crashed process. TCP keeps the socket in TIME_WAIT for ~60 seconds to ensure all packets from the old connection are flushed. Options: wait 60s, or use `SO_REUSEADDR` socket option in your application.
4. `127.0.0.1` = only local access (even if firewall fails, remote users can't connect). `0.0.0.0` = accessible from any interface. For FlowForge DB: bind to `10.0.3.10` (private IP) so even a firewall misconfiguration doesn't expose it to the internet.

---

## Lab 03: Firewalls, Routing & TLS

### Exercise 3a: Firewalls

**Save/restore iptables:**

```bash
# Save current rules
sudo iptables-save > ~/iptables-backup.rules

# Restore if needed
sudo iptables-restore < ~/iptables-backup.rules
```

**FlowForge firewall rules:**

```bash
# Flush existing rules
sudo iptables -F
sudo iptables -X

# Default policies
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established/related (CRITICAL -- without this, response packets are dropped)
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH from admin network
sudo iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/24 -j ACCEPT

# Allow api-service (HTTP)
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# Allow ICMP (ping) from local subnet
sudo iptables -A INPUT -p icmp -s 10.0.0.0/16 -j ACCEPT

# Allow PostgreSQL ONLY from app server
sudo iptables -A INPUT -p tcp --dport 5432 -s 10.0.2.10 -j ACCEPT

# Log dropped packets (useful for debugging)
sudo iptables -A INPUT -j LOG --log-prefix "IPTABLES-DROP: " --log-level 4
```

**Testing:**

```bash
# Start a test server on 8080
python3 -m http.server 8080 &

# Test allowed port
curl http://localhost:8080  # Should work (loopback allowed)

# Test blocked port
curl http://localhost:9999  # Should fail (no rule for 9999)

# Check logs for drops
sudo journalctl -k | grep IPTABLES-DROP
```

**ufw equivalent:**

```bash
sudo ufw reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 22 proto tcp
sudo ufw allow 8080/tcp
sudo ufw allow from 10.0.0.0/16 proto icmp
sudo ufw allow from 10.0.2.10 to any port 5432 proto tcp
sudo ufw enable

# See generated rules
sudo iptables -L -n -v
```

**Checkpoint answers:**

1. Default DROP means anything not explicitly allowed is blocked. This is "default deny" / principle of least privilege. If you forget a rule, traffic is blocked (safe). With default ACCEPT, if you forget a deny rule, traffic gets through (dangerous).
2. Possible causes: (a) the SSH allow rule is placed AFTER a broader DROP rule that matches first, (b) the source IP doesn't match the allowed range, (c) SSH is on a non-standard port but the rule uses port 22, (d) the loopback rule isn't present and you're testing from localhost.
3. Without ESTABLISHED,RELATED: You can receive an inbound SYN on port 80, but the SYN-ACK response going BACK to the client hits the INPUT chain as a new packet on the ephemeral port -- which gets DROPped because there's no rule for it. The ESTABLISHED match allows packets that are part of an already-accepted connection.
4. `iptables -P INPUT DROP && iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT && iptables -A INPUT -i lo -j ACCEPT && iptables -A INPUT -p tcp --dport 443 -j ACCEPT && iptables -A INPUT -p tcp --dport 22 -s 10.0.0.5 -j ACCEPT && iptables -A INPUT -p tcp --dport 5432 -s 10.0.2.0/24 -j ACCEPT`

### Exercise 3b: Network Namespaces & Routing

**Create namespaces and connect them:**

```bash
# Create namespaces
sudo ip netns add ns-app
sudo ip netns add ns-db

# Create veth pairs
sudo ip link add veth-app type veth peer name veth-app-br
sudo ip link add veth-db type veth peer name veth-db-br

# Move one end into each namespace
sudo ip link set veth-app netns ns-app
sudo ip link set veth-db netns ns-db

# Assign IPs on the host side (bridge endpoints)
sudo ip addr add 10.0.2.1/24 dev veth-app-br
sudo ip addr add 10.0.3.1/24 dev veth-db-br

# Assign IPs inside namespaces
sudo ip netns exec ns-app ip addr add 10.0.2.10/24 dev veth-app
sudo ip netns exec ns-db ip addr add 10.0.3.10/24 dev veth-db

# Bring up all interfaces
sudo ip link set veth-app-br up
sudo ip link set veth-db-br up
sudo ip netns exec ns-app ip link set veth-app up
sudo ip netns exec ns-app ip link set lo up
sudo ip netns exec ns-db ip link set veth-db up
sudo ip netns exec ns-db ip link set lo up

# Add default routes in namespaces
sudo ip netns exec ns-app ip route add default via 10.0.2.1
sudo ip netns exec ns-db ip route add default via 10.0.3.1

# Enable IP forwarding on the host (THE KEY STEP)
sudo sysctl -w net.ipv4.ip_forward=1

# Test connectivity
sudo ip netns exec ns-app ping -c 3 10.0.3.10  # Should work!
sudo ip netns exec ns-db ping -c 3 10.0.2.10    # Should work!
```

**Simulate FlowForge communication:**

```bash
# Start a "PostgreSQL" listener in ns-db
sudo ip netns exec ns-db python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('10.0.3.10', 5432))
s.listen(1)
print('PostgreSQL simulator listening on 10.0.3.10:5432')
conn, addr = s.accept()
print(f'Connection from {addr}')
conn.sendall(b'Connected to PostgreSQL\n')
conn.close()
s.close()
" &

# Connect from ns-app
sudo ip netns exec ns-app python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('10.0.3.10', 5432))
data = s.recv(1024)
print(f'Received: {data.decode()}')
s.close()
"
```

**Routing tables:**

```bash
# Host routing table
ip route show
# 10.0.2.0/24 dev veth-app-br proto kernel scope link
# 10.0.3.0/24 dev veth-db-br proto kernel scope link

# ns-app routing table
sudo ip netns exec ns-app ip route show
# 10.0.2.0/24 dev veth-app proto kernel scope link
# default via 10.0.2.1 dev veth-app

# Packet path: ns-app (10.0.2.10) → veth-app → host (10.0.2.1) → IP forwarding →
#              host (10.0.3.1) → veth-db-br → veth-db → ns-db (10.0.3.10)
```

**Checkpoint answers:**

1. A network namespace is an isolated network stack (interfaces, routing table, iptables rules, sockets) within the same kernel. Docker uses network namespaces to isolate each container's network. When you run `docker run`, Docker creates a network namespace just like `ip netns add`.
2. IP forwarding means the host will accept packets not addressed to itself and forward them based on its routing table. It's disabled by default because a regular computer shouldn't act as a router -- enabling it is an explicit choice.
3. "Packets destined for 10.0.3.0/24 should be sent via 10.0.2.1 (the gateway) using the veth0 interface." The host at 10.0.2.1 then uses its own routing table to deliver to 10.0.3.0/24.
4. api-service (10.0.2.10) → "destination 10.0.3.10 not in my subnet, check routing table → default via 10.0.2.1" → host receives packet → "destination 10.0.3.10 matches route for 10.0.3.0/24 via veth-db-br" → forwards out veth-db-br → arrives at ns-db veth-db → reaches PostgreSQL on 10.0.3.10:5432.

### Exercise 3c: nginx Reverse Proxy & Load Balancing

**Backend instances:**

```bash
# Create distinct responses
mkdir -p /tmp/instance1 /tmp/instance2 /tmp/instance3
echo "<h1>Instance 1</h1>" > /tmp/instance1/index.html
echo "<h1>Instance 2</h1>" > /tmp/instance2/index.html
echo "<h1>Instance 3</h1>" > /tmp/instance3/index.html

# Start servers
cd /tmp/instance1 && python3 -m http.server 8081 &
cd /tmp/instance2 && python3 -m http.server 8082 &
cd /tmp/instance3 && python3 -m http.server 8083 &
```

**nginx configuration (reverse proxy + load balancing):**

```nginx
# /etc/nginx/sites-available/flowforge-lb
upstream flowforge_api {
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
    server 127.0.0.1:8083;
}

server {
    listen 80;
    server_name api.flowforge.local;

    location / {
        proxy_pass http://flowforge_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Install and configure nginx
sudo apt install -y nginx
sudo ln -s /etc/nginx/sites-available/flowforge-lb /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test config
sudo systemctl reload nginx

# Test load balancing (run multiple times)
for i in {1..10}; do curl -s http://localhost/ | grep Instance; done
# Should see Instance 1, 2, 3 rotating
```

**Checkpoint answers:**

1. L4 = TCP/UDP level, sees only IP:port (faster, less flexible). L7 = HTTP level, sees URLs, headers, cookies (slower, more features). nginx operates at L7 (it parses HTTP to make routing decisions).
2. Because nginx terminates the client connection and creates a new connection to the backend. The backend sees nginx's IP as the source. Fix: add `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;` to nginx config, and read this header in the backend.
3. WebSockets are long-lived connections. If you use round-robin, a reconnection might go to a different server, losing session state. You'd need sticky sessions (ip_hash or cookie-based) or make the app stateless.
4. TLS at the proxy: one place to manage certs, less CPU on backends, LB can inspect HTTP headers. Downside: internal traffic is unencrypted (usually acceptable on a private network).

### Exercise 3d: TLS/SSL

**Generate self-signed certificate:**

```bash
# Generate private key and certificate with SANs
openssl req -x509 -newkey rsa:2048 -keyout flowforge-key.pem -out flowforge-cert.pem \
  -days 365 -nodes \
  -subj "/CN=api.flowforge.local" \
  -addext "subjectAltName=DNS:api.flowforge.local,DNS:localhost,IP:127.0.0.1"

# Examine the certificate
openssl x509 -in flowforge-cert.pem -text -noout
# Check: Subject, Issuer (same = self-signed), Validity, SANs, Public Key
```

**Configure nginx with TLS:**

```nginx
server {
    listen 443 ssl;
    server_name api.flowforge.local;

    ssl_certificate /path/to/flowforge-cert.pem;
    ssl_certificate_key /path/to/flowforge-key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://flowforge_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.flowforge.local;
    return 301 https://$host$request_uri;
}
```

**Testing:**

```bash
# This fails -- curl doesn't trust self-signed certs
curl https://localhost:443
# Error: SSL certificate problem: self-signed certificate

# Skip verification (development only!)
curl -k https://localhost:443

# Trust our specific cert
curl --cacert flowforge-cert.pem https://api.flowforge.local:443

# Inspect TLS handshake
openssl s_client -connect localhost:443
# Shows: certificate chain, server cert details, TLS version, cipher suite
# Note: "Verify return code: 18 (self-signed certificate)"
```

**Checkpoint answers:**

1. (a) ClientHello: client sends supported TLS versions and cipher suites. (b) ServerHello + Certificate: server chooses TLS version and cipher, sends its certificate. (c) Client verifies certificate (CA signed? hostname match? expired?). (d) Key exchange: both sides derive a shared session key. (e) Encrypted data: all HTTP traffic encrypted with the session key.
2. Private key = secret, stays on the server, used to prove identity and decrypt. Certificate = public, sent to clients, contains the public key and identity info. If the private key leaks, an attacker can impersonate the server and decrypt traffic. You must revoke the certificate immediately and generate a new key pair.
3. SANs specify all hostnames and IPs the certificate is valid for. Modern TLS implementations check SANs (not CN). If you connect to `localhost` but the cert only has SAN for `api.flowforge.local`, the handshake fails with a hostname mismatch error.
4. No self-signed cert in production. Use Let's Encrypt (free, automated CA) or AWS Certificate Manager (free for ALB/CloudFront). These are signed by CAs that browsers already trust, so users don't see security warnings.

---

## Lab 04: Broken Network

### Example break-network.sh and Solutions

**Example break-network.sh:**

```bash
#!/bin/bash
set -euo pipefail

echo "=== Setting up FlowForge networking environment ==="

# Create namespaces
sudo ip netns add ns-public 2>/dev/null || true
sudo ip netns add ns-app 2>/dev/null || true
sudo ip netns add ns-db 2>/dev/null || true

# Create veth pairs
sudo ip link add veth-pub type veth peer name veth-pub-br
sudo ip link add veth-app type veth peer name veth-app-br
sudo ip link add veth-db type veth peer name veth-db-br

# Move into namespaces
sudo ip link set veth-pub netns ns-public
sudo ip link set veth-app netns ns-app
sudo ip link set veth-db netns ns-db

# Host side IPs
sudo ip addr add 10.0.1.1/24 dev veth-pub-br
sudo ip addr add 10.0.2.1/24 dev veth-app-br
sudo ip addr add 10.0.3.1/24 dev veth-db-br

# Namespace side IPs
sudo ip netns exec ns-public ip addr add 10.0.1.10/24 dev veth-pub
sudo ip netns exec ns-app ip addr add 10.0.2.10/24 dev veth-app
sudo ip netns exec ns-db ip addr add 10.0.3.10/24 dev veth-db

# Bring up interfaces
sudo ip link set veth-pub-br up
sudo ip link set veth-app-br up
sudo ip link set veth-db-br up
sudo ip netns exec ns-public ip link set veth-pub up
sudo ip netns exec ns-public ip link set lo up
sudo ip netns exec ns-app ip link set veth-app up
sudo ip netns exec ns-app ip link set lo up
sudo ip netns exec ns-db ip link set veth-db up
sudo ip netns exec ns-db ip link set lo up

# Default routes in namespaces
sudo ip netns exec ns-public ip route add default via 10.0.1.1
sudo ip netns exec ns-app ip route add default via 10.0.2.1
sudo ip netns exec ns-db ip route add default via 10.0.3.1

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Add /etc/hosts entries
echo "10.0.3.10  db.flowforge.local" | sudo tee -a /etc/hosts
echo "10.0.2.10  api.flowforge.local" | sudo tee -a /etc/hosts

# Generate TLS cert
openssl req -x509 -newkey rsa:2048 -keyout /tmp/ff-key.pem -out /tmp/ff-cert.pem \
  -days 365 -nodes -subj "/CN=api.flowforge.local" \
  -addext "subjectAltName=DNS:api.flowforge.local,DNS:localhost,IP:127.0.0.1"

# Start services
sudo ip netns exec ns-db python3 -c "
import socket, threading
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('10.0.3.10', 5432))
s.listen(5)
print('DB listening on 10.0.3.10:5432')
while True:
    conn, addr = s.accept()
    conn.sendall(b'PostgreSQL OK\n')
    conn.close()
" &

sudo ip netns exec ns-app python3 -m http.server 8080 --bind 10.0.2.10 &

echo "=== Environment working. Now breaking things... ==="

# BREAK 1: DNS -- corrupt the hosts file entry for the database
sudo sed -i 's/10.0.3.10  db.flowforge.local/10.0.3.99  db.flowforge.local/' /etc/hosts

# BREAK 2: Firewall -- block port 5432 from the app subnet
sudo iptables -I FORWARD -s 10.0.2.0/24 -d 10.0.3.0/24 -p tcp --dport 5432 -j DROP

# BREAK 3: Routing -- remove default route in ns-public so it can't reach app subnet
sudo ip netns exec ns-public ip route del default

# BREAK 4: Port binding -- start a process on port 80 on the host to conflict with nginx
python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 80))
s.listen(1)
import time
while True: time.sleep(60)
" &

# BREAK 5: TLS -- replace the cert with one that has wrong SANs
openssl req -x509 -newkey rsa:2048 -keyout /tmp/ff-key.pem -out /tmp/ff-cert.pem \
  -days 365 -nodes -subj "/CN=wrong.example.com" 2>/dev/null

echo "Server is now 'broken'. Good luck!"
```

**Solutions:**

**Issue 1: DNS resolution broken (Layer 7 / Application)**
- Symptom: `ping db.flowforge.local` from ns-app goes to wrong IP (10.0.3.99 instead of 10.0.3.10)
- Investigation: `cat /etc/hosts | grep flowforge` shows wrong IP
- Root cause: /etc/hosts has 10.0.3.99 instead of 10.0.3.10
- Fix: `sudo sed -i 's/10.0.3.99  db.flowforge.local/10.0.3.10  db.flowforge.local/' /etc/hosts`
- Verification: `ping -c 1 db.flowforge.local` shows 10.0.3.10

**Issue 2: Firewall blocking database traffic (Layer 3-4 / Network-Transport)**
- Symptom: Can ping 10.0.3.10 from ns-app but TCP connection to port 5432 times out
- Investigation: `sudo iptables -L FORWARD -n -v` shows DROP rule for port 5432
- Root cause: iptables FORWARD chain has a DROP rule for TCP 5432 from 10.0.2.0/24 to 10.0.3.0/24
- Fix: `sudo iptables -D FORWARD -s 10.0.2.0/24 -d 10.0.3.0/24 -p tcp --dport 5432 -j DROP`
- Verification: `sudo ip netns exec ns-app nc -zv 10.0.3.10 5432` succeeds

**Issue 3: Missing route in ns-public (Layer 3 / Network)**
- Symptom: ns-public can't reach any other namespace (ping fails with "Network is unreachable")
- Investigation: `sudo ip netns exec ns-public ip route show` shows no default route
- Root cause: Default route was removed from ns-public
- Fix: `sudo ip netns exec ns-public ip route add default via 10.0.1.1`
- Verification: `sudo ip netns exec ns-public ping -c 1 10.0.2.10` succeeds

**Issue 4: Port conflict on port 80 (Layer 4 / Transport)**
- Symptom: nginx fails to start with "bind() to 0.0.0.0:80 failed: Address already in use"
- Investigation: `sudo ss -tlnp | grep :80` shows another process on port 80
- Root cause: A rogue process is occupying port 80
- Fix: `sudo kill <PID_of_rogue_process>`
- Verification: `sudo systemctl start nginx` succeeds, `sudo ss -tlnp | grep :80` shows nginx

**Issue 5: TLS certificate hostname mismatch (Layer 6-7 / Presentation-Application)**
- Symptom: `curl https://api.flowforge.local:443` gives "SSL: certificate subject name does not match"
- Investigation: `openssl x509 -in /tmp/ff-cert.pem -text -noout` shows CN=wrong.example.com, no SANs
- Root cause: Certificate was replaced with one issued for wrong.example.com
- Fix: Regenerate cert with correct CN and SANs:
  ```bash
  openssl req -x509 -newkey rsa:2048 -keyout /tmp/ff-key.pem -out /tmp/ff-cert.pem \
    -days 365 -nodes -subj "/CN=api.flowforge.local" \
    -addext "subjectAltName=DNS:api.flowforge.local,DNS:localhost,IP:127.0.0.1"
  sudo systemctl reload nginx
  ```
- Verification: `curl --cacert /tmp/ff-cert.pem https://api.flowforge.local:443` succeeds

**Checkpoint answers:**

1. Issue 1: Layer 7 (DNS/Application). Issue 2: Layer 3-4 (firewall between network/transport). Issue 3: Layer 3 (routing). Issue 4: Layer 4 (port binding at transport). Issue 5: Layer 6-7 (TLS/certificate at presentation/application).
2. Network debugging methodology: Start bottom-up. Layer 1: Is the link up? Layer 2: Can we reach the local gateway? Layer 3: Can we ping the destination? Layer 4: Can we connect to the port? Layer 7: Does the application respond correctly? Different from Module 1 which was single-system (check logs, processes, permissions, config, resources).
3. Five essential commands: (a) `ip link show` - are interfaces up? (b) `ping <gateway>` - can I reach the local network? (c) `ip route show` - where does traffic go? (d) `ss -tlnp` - what's listening? (e) `curl -v <service>` - does the application work end-to-end?
4. Monitoring: DNS resolution checks (Module 9 synthetic monitoring), firewall rule auditing (Module 10), route table monitoring, port monitoring (check that expected services are listening on expected ports), TLS certificate expiry alerting.
5. Network debugging vs system debugging: Network adds the dimension of "between systems." You need to check from BOTH ends. A service can be healthy on one machine but unreachable from another. The layered approach (OSI) gives structure. Module 1 was "find the broken thing on this machine." Module 2 is "find where in the path between machines the problem lives."

---

## Cleanup

After the student completes all labs, clean up:

```bash
# Remove namespaces
sudo ip netns del ns-public 2>/dev/null || true
sudo ip netns del ns-app 2>/dev/null || true
sudo ip netns del ns-db 2>/dev/null || true

# Remove /etc/hosts entries
sudo sed -i '/flowforge.local/d' /etc/hosts

# Restore iptables
sudo iptables -F
sudo iptables -X
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT
# Or restore from backup: sudo iptables-restore < ~/iptables-backup.rules

# Stop nginx
sudo systemctl stop nginx

# Kill background processes
pkill -f "python3 -m http.server" 2>/dev/null || true
pkill -f "python3 -c" 2>/dev/null || true

# Reset IP forwarding
sudo sysctl -w net.ipv4.ip_forward=0

# Remove temp files
rm -f /tmp/ff-key.pem /tmp/ff-cert.pem
rm -f flowforge-capture.pcap
```
