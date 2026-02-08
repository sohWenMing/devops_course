# Lab 01: TCP/IP & Subnets

> **Module**: 2 -- Networking Fundamentals  
> **Time estimate**: 2-3 hours  
> **Prerequisites**: Read the [OSI Model & TCP/IP Stack](#) and [IP Addressing & Subnets](#) sections of the Module 2 README

---

## Overview

In this lab, you'll capture real network packets with `tcpdump` and identify what's happening at each OSI layer. Then you'll practice subnet math by hand and design a multi-environment network layout for FlowForge. By the end, you'll be able to read a packet capture like a story and carve up an IP address space with confidence.

---

## Exercise 1a: Packet Capture & OSI Layer Identification

### Objectives

- Capture live network traffic using `tcpdump`
- Identify the Ethernet frame (Layer 2), IP packet (Layer 3), TCP segment (Layer 4), and application payload (Layer 7) in captured packets
- Understand encapsulation by seeing it in real data
- Analyze a TCP three-way handshake

### What You'll Do

**Part 1: Install and explore tcpdump**

1. Install `tcpdump` on your Ubuntu machine if it isn't already installed.
2. List all available network interfaces on your machine. Identify which one carries your main network traffic.
3. Run a basic capture on your main interface and observe the output. What information does each line show you?

**Part 2: Capture HTTP traffic**

4. In one terminal, start a `tcpdump` capture that:
   - Captures traffic on the loopback interface (`lo`)
   - Filters for traffic on port 8080
   - Shows link-layer headers (Ethernet frames)
   - Writes to a file called `flowforge-capture.pcap`

5. In a second terminal, start a simple HTTP server on port 8080. (Hint: Python has a built-in HTTP server module. Think back to Module 1 -- what can you find in the Python standard library?)

6. In a third terminal, make an HTTP request to your server:
   - Use `curl` to make a GET request to `http://localhost:8080`

7. Stop the tcpdump capture and examine the `.pcap` file.

**Part 3: Identify the layers**

8. Read the capture output and identify for each packet:
   - **Layer 2 (Data Link)**: What are the source and destination MAC addresses? On loopback, what do you see instead of real MAC addresses?
   - **Layer 3 (Network)**: What are the source and destination IP addresses? What is the protocol?
   - **Layer 4 (Transport)**: What are the source and destination ports? Can you identify the TCP flags (SYN, ACK, FIN)?
   - **Layer 7 (Application)**: Can you see the HTTP request and response? What method and status code do you see?

9. Identify the TCP three-way handshake in your capture:
   - Which packet is the SYN? (Client initiating the connection)
   - Which packet is the SYN-ACK? (Server acknowledging)
   - Which packet is the ACK? (Client confirming)
   - What happens after the handshake? (HTTP data transfer)
   - How does the connection close? (FIN packets)

10. Write a summary in a file called `packet-analysis.md`. For each OSI layer you can observe, note:
    - Which header fields you can see
    - What information each field provides
    - Why that information is needed at that layer

**Part 4: Capture DNS traffic (Preview for Lab 02)**

11. Start a new capture filtering for DNS traffic (port 53). Then run a `dig` or `nslookup` command for any public domain. Can you see the DNS query and response in the capture? What Layer 4 protocol does DNS use?

### Expected Outcome

- A file `flowforge-capture.pcap` containing captured packets
- A file `packet-analysis.md` with your OSI layer analysis
- You can explain what happens at each layer when you make an HTTP request
- You can identify SYN, SYN-ACK, and ACK packets in a TCP handshake

### Checkpoint Questions

> Answer these without looking at notes:
> 1. You see a packet with the TCP flag "RST". At which OSI layer is this, and what does it mean?
> 2. What is the difference between the IP header's "TTL" field and a DNS record's "TTL"?
> 3. You capture a packet and see source port 54321 and destination port 80. Which is the client and which is the server? How do you know?
> 4. Why does the TCP handshake require three packets instead of two?

---

## Exercise 1b: Subnet Calculation & FlowForge Network Layout

### Objectives

- Calculate subnet ranges, broadcast addresses, and usable IP counts from CIDR notation by hand
- Understand why subnets exist and how they enable network segmentation
- Design a multi-environment subnet layout for FlowForge

### What You'll Do

**Part 1: Subnet math by hand**

1. For each of the following CIDR blocks, calculate **by hand** (no subnet calculator tools):
   - The network address
   - The broadcast address
   - The subnet mask (in dotted-decimal notation)
   - The number of usable host IPs
   - The range of usable host IPs (first usable to last usable)

   CIDRs to calculate:
   - `192.168.1.0/24`
   - `10.0.0.0/16`
   - `172.16.10.0/28`
   - `10.100.0.0/22`
   - `192.168.50.0/26`

2. Write your work (showing the binary math) in a file called `subnet-calculations.md`.

**Part 2: Subnetting decisions**

3. Answer these planning questions in your `subnet-calculations.md` file:
   - You need a subnet for exactly 30 hosts. What is the smallest CIDR prefix you can use? How many IPs are wasted?
   - You have `10.0.0.0/24` and need to split it into 4 equal subnets. What are the 4 CIDR ranges?
   - Two subnets are `10.0.1.0/24` and `10.0.1.128/25`. Do they overlap? Why is this a problem?

**Part 3: Design the FlowForge network layout**

4. You've been given the address space `10.0.0.0/16` for FlowForge. Design a subnet layout that supports:
   - **3 environments**: development, staging, production
   - **3 tiers per environment**: public (load balancers, bastion), private (api-service, worker-service), database (PostgreSQL)
   - **2 availability zones per environment** (for redundancy -- preview of AWS Module 5)
   - No overlapping subnets
   - Room for future growth

   Your design should include:
   - A diagram (ASCII art is fine) showing the overall layout
   - A table listing every subnet with its CIDR, purpose, environment, AZ, and usable IP count
   - Justification for your sizing choices (why /24 instead of /28, etc.)

5. For your design, answer:
   - How many total IPs does your design use? How many are left in the /16 for future expansion?
   - If the development team later needs a fourth environment (QA), can your design accommodate it without re-numbering?
   - Why is it important that the database subnets are separate from the public subnets?

### Expected Outcome

- A file `subnet-calculations.md` with worked-out subnet math (showing binary where appropriate)
- A FlowForge network design document with a subnet table and justification
- You can do CIDR math in your head for common prefix lengths (/24, /28, /16, etc.)

### Checkpoint Questions

> Answer these without looking at notes:
> 1. Given `10.0.0.0/20`, how many usable host IPs are available? What's the broadcast address?
> 2. You need subnets for: 100 hosts, 25 hosts, and 10 hosts. What's the smallest CIDR for each?
> 3. Your colleague proposes using `10.0.0.0/24` for the public subnet and `10.0.0.0/16` for the VPC. Is this valid? Why or why not?
> 4. Why do AWS subnets reserve 5 IP addresses per subnet instead of the usual 2?

---

## What's Next?

Proceed to [Lab 02: DNS, HTTP & Ports](lab-02-dns-http-ports.md) where you'll explore DNS resolution, inspect HTTP conversations in detail, and investigate ports and sockets on your system.

> **Link back to Module 1**: You used `tcpdump` and `curl` as command-line tools, explored files in `/etc/`, and started background processes in multiple terminals -- all skills from Module 1. Networking tools are just Linux tools applied to packets instead of files.
