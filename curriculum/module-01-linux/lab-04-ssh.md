# Lab 04: SSH

> **Module**: 1 -- Linux Deep Dive  
> **Time estimate**: 1-2 hours  
> **Prerequisites**: Complete Labs 01-03. Read the [SSH (Secure Shell)](#) section of the Module 1 README

---

## Overview

SSH is how you'll access every remote server throughout the rest of this course -- from EC2 instances to Kubernetes nodes. In this lab, you'll set up SSH key-based authentication from scratch, harden the SSH server configuration, and practice connecting securely.

---

## Exercise 4a: SSH Key Pair, Server Configuration & Key-Based Auth

### Objectives

- Generate an SSH key pair using modern cryptography
- Configure the SSH server to enforce security best practices
- Set up key-based authentication and disable password login
- Create an SSH client config for convenient connections
- Verify the entire setup works by connecting with key-based auth

### What You'll Do

**Part 1: Generate SSH Key Pair**

1. Generate an SSH key pair for FlowForge administration:
   - Choose an appropriate key type (think about security vs compatibility)
   - Add a meaningful comment so you can identify the key later
   - Consider whether to set a passphrase and understand the trade-offs
   - Verify both the private and public key files were created
   - Check the permissions on the private key file -- what should they be and why?

2. Examine your key:
   - Look at the public key -- understand its format
   - What's the difference between the key types available (RSA, ECDSA, Ed25519)?
   - Why does the private key's file permissions matter so much?

**Part 2: Configure the SSH Server**

3. Before making changes, examine the current SSH server configuration:
   - Find the sshd configuration file
   - Read through it and identify the default settings
   - Make a backup of the original configuration (always back up before editing!)

4. Harden the SSH server configuration. Think about and implement changes for:
   - Should root be able to log in directly via SSH?
   - Should password-based authentication be allowed?
   - Should the default port be changed? (What are the arguments for and against?)
   - How many authentication attempts should be allowed before disconnecting?
   - Should you limit which users can log in via SSH?

5. After making changes:
   - Validate your configuration file has no syntax errors (there's a command for this)
   - Restart the SSH service to apply changes
   - Verify the service is running with the new configuration

**Part 3: Set Up Key-Based Authentication**

6. Set up your public key for authentication:
   - Place your public key in the correct location for SSH authentication
   - Set the correct permissions on the relevant files and directories (SSH is very strict about this!)
   - Understand WHY SSH cares about permissions on these files

7. Test your setup:
   - Open a NEW terminal (don't close the one where you changed sshd_config!)
   - Connect to localhost using your SSH key
   - Verify that password authentication is denied
   - Verify that key-based authentication succeeds

   **IMPORTANT**: Keep your original terminal open while testing! If you misconfigure SSH and close all your sessions, you could lock yourself out.

**Part 4: SSH Client Configuration**

8. Create an SSH client configuration file to make connections easier:
   - Define a connection profile for FlowForge (connecting to localhost with your settings)
   - Include the correct username, port (if changed), and identity file
   - Verify you can connect using just the profile name

9. Explore additional SSH features:
   - Test port forwarding (forward a local port to a remote port)
   - Understand what an SSH tunnel is and when you'd use one
   - Learn what SSH agent forwarding is (and when it's dangerous)

### Expected Outcome

- An Ed25519 (or equivalent) SSH key pair with proper permissions
- A hardened sshd_config with password auth disabled and key auth required
- Successful SSH connection to localhost using key-based authentication only
- An SSH client config file for convenient connections
- Understanding of SSH security best practices

### Checkpoint Questions

> Without looking at notes:
> 1. Given a fresh machine, set up SSH key-only access in under 5 minutes. List every step you'd take.
> 2. Why is password authentication disabled in production environments?
> 3. You changed the SSH port and restarted sshd, but now you can't connect. What are the possible causes?
> 4. What permissions must `~/.ssh/` and `~/.ssh/authorized_keys` have? Why is SSH strict about this?
> 5. You need to connect to a database server that's only accessible from a bastion host. How would SSH help? (Hint: this is called a "jump host" -- you'll use this in Module 5)
> 6. Why should you NEVER close your existing SSH session before testing that a new SSH configuration works?

---

## What's Next?

With secure remote access configured, you're ready for the final challenge of Module 1: [Lab 05: Broken Server](lab-05-broken-server.md). Everything you've learned in Labs 01-04 comes together as you diagnose and fix a system with multiple deliberate misconfigurations.
