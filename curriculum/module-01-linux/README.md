# Module 1: Linux Deep Dive

> **Time estimate**: 2 weeks  
> **Prerequisites**: Basic terminal usage, a computer running Ubuntu (or WSL2 on Windows)  
> **Link forward**: "The OS your containers, VMs, and Kubernetes nodes all run"

---

## Why This Module Matters for DevOps

Every production server you will ever manage runs Linux. Every Docker container is a Linux process. Every Kubernetes node is a Linux machine. Every EC2 instance boots a Linux AMI. If you don't understand the operating system, you're building on a foundation you can't debug.

This module gives you the deep Linux knowledge that separates a developer who *uses* servers from an engineer who *understands* them. When something breaks at 3 AM, you won't be guessing -- you'll know exactly where to look.

---

## Table of Contents

1. [File System Hierarchy](#1-file-system-hierarchy)
2. [File Permissions & Ownership](#2-file-permissions--ownership)
3. [Processes & Signals](#3-processes--signals)
4. [systemd Services](#4-systemd-services)
5. [Package Management](#5-package-management)
6. [Bash Scripting](#6-bash-scripting)
7. [Environment Variables & Configuration](#7-environment-variables--configuration)
8. [SSH (Secure Shell)](#8-ssh-secure-shell)

---

## 1. File System Hierarchy

### The Linux FHS (Filesystem Hierarchy Standard)

Linux organizes everything into a single tree rooted at `/`. There is no `C:\` drive, no `D:\` drive -- just one tree. Every file, device, process, and even kernel parameter lives somewhere in this tree.

Here are the directories you must know:

| Directory | Purpose | FlowForge Example |
|-----------|---------|-------------------|
| `/` | Root of the entire filesystem | Everything starts here |
| `/bin`, `/usr/bin` | Essential user binaries | `bash`, `ls`, `ps`, `curl` |
| `/sbin`, `/usr/sbin` | System administration binaries | `systemctl`, `iptables`, `useradd` |
| `/etc` | System-wide configuration files | `/etc/systemd/system/flowforge-api.service` |
| `/var` | Variable data (logs, databases, mail) | `/var/log/flowforge/`, PostgreSQL data |
| `/var/log` | Log files | `/var/log/syslog`, journalctl output |
| `/tmp` | Temporary files (cleared on reboot) | Build artifacts, temporary uploads |
| `/home` | User home directories | `/home/flowforge/` |
| `/opt` | Optional/third-party software | `/opt/flowforge/` for application binaries |
| `/proc` | Virtual filesystem -- running process info | `/proc/<PID>/status`, `/proc/cpuinfo` |
| `/sys` | Virtual filesystem -- kernel/hardware info | `/sys/class/net/` for network interfaces |
| `/dev` | Device files | `/dev/sda` (disk), `/dev/null` (black hole) |
| `/root` | Root user's home directory | Not `/home/root` -- it gets its own directory |

### Architecture Thinking: Why Does FHS Matter?

> **Question to ask yourself**: If every application just put files wherever it wanted, what would go wrong?

The FHS is a contract. When you know the contract, you can:
- Find any application's config files instantly (`/etc/`)
- Find any application's logs instantly (`/var/log/`)
- Know where binaries live (`/usr/bin/`, `/usr/local/bin/`)
- Understand what's safe to delete (`/tmp/`) and what's critical (`/etc/`)

This matters enormously in DevOps because you'll be writing Dockerfiles, Ansible playbooks, and Terraform user data scripts that assume this structure.

> **You'll use this when**: Writing Dockerfiles (Module 4) -- you'll need to know where to `COPY` config files. Building AMIs (Module 5) -- user data scripts write to these paths. Writing systemd unit files (this module) -- they reference binary paths and config locations.

> **AWS SAA tie-in**: When you launch an EC2 instance, it boots a Linux AMI. Understanding FHS helps you write user data scripts, debug instances via SSH, and configure services correctly.

---

## 2. File Permissions & Ownership

### The Permission Model

Every file and directory in Linux has three sets of permissions for three categories of users:

```
-rwxr-xr-- 1 flowforge api-team 4096 Jan 15 10:30 config.yaml
│├─┤├─┤├─┤   │         │
│ │  │  │    owner     group
│ │  │  │
│ │  │  └── others: r-- (read only)
│ │  └───── group:  r-x (read + execute)
│ └──────── owner:  rwx (read + write + execute)
└────────── file type: - (regular file), d (directory), l (symlink)
```

### Permission Bits

| Symbol | Octal | Meaning for Files | Meaning for Directories |
|--------|-------|-------------------|------------------------|
| `r` | 4 | Read contents | List contents |
| `w` | 2 | Modify contents | Create/delete files inside |
| `x` | 1 | Execute as program | Enter (cd into) the directory |

Common permission patterns:
- `755` (`rwxr-xr-x`): Binaries, scripts -- everyone can read/execute, only owner can modify
- `644` (`rw-r--r--`): Config files -- everyone can read, only owner can modify
- `600` (`rw-------`): Secrets, private keys -- only owner can read/write
- `700` (`rwx------`): Private directories -- only owner can enter

### Users, Groups, and Ownership

Linux uses a user/group model for access control:

- Every process runs as a **user**
- Every user belongs to one or more **groups**
- Every file has an **owner** (user) and a **group**
- Permissions are checked in order: owner -> group -> others (first match wins)

Key commands: `useradd`, `groupadd`, `usermod`, `chown`, `chmod`, `chgrp`, `umask`

### Special Permissions

- **SUID** (`4xxx`): File executes as the file's owner, not the person running it. Example: `/usr/bin/passwd` runs as root so users can change their own passwords.
- **SGID** (`2xxx`): On directories, new files inherit the directory's group. Useful for shared project directories.
- **Sticky bit** (`1xxx`): On directories, only the file's owner can delete the file. Applied to `/tmp` so users can't delete each other's temp files.

### Architecture Thinking: Why Permissions Matter for DevOps

> **Question**: What happens if your API service config file containing database credentials is readable by every user on the system?

In production, the principle of **least privilege** starts at the filesystem level:
- Each service runs as its own user
- Config files are readable only by the service that needs them
- Log directories are writable by the service but readable by the ops team
- Private keys are `600` -- readable only by the owner

> **You'll use this when**: Running Docker containers as non-root (Module 4). Setting up IAM with least privilege (Module 5). Writing Kubernetes SecurityContexts (Module 8). All of these are the same principle at different scales.

---

## 3. Processes & Signals

### What Is a Process?

A process is a running instance of a program. When you type `./api-service`, the kernel:
1. Creates a new process (with a unique PID)
2. Loads the program into memory
3. Starts executing it

Every process has:
- **PID**: Process ID (unique identifier)
- **PPID**: Parent Process ID (who started this process)
- **UID**: User ID (who the process runs as)
- **State**: Running, sleeping, stopped, zombie
- **File descriptors**: stdin (0), stdout (1), stderr (2), plus any files/sockets it opened

### Viewing Processes

| Command | What it shows |
|---------|--------------|
| `ps aux` | Snapshot of all processes (BSD style) |
| `ps -ef` | Snapshot of all processes (POSIX style) |
| `top` | Real-time process monitor (CPU/memory) |
| `htop` | Better real-time monitor (if installed) |
| `pgrep <name>` | Find PIDs by name |
| `pidof <name>` | Find PID of a running program |

### Signals

Signals are how processes communicate. The kernel delivers a signal to a process, and the process handles it (or doesn't).

| Signal | Number | Default Action | Use Case |
|--------|--------|---------------|----------|
| `SIGTERM` | 15 | Terminate gracefully | Polite "please stop" -- process can clean up |
| `SIGKILL` | 9 | Terminate immediately | Force kill -- process cannot catch or ignore this |
| `SIGHUP` | 1 | Terminate / reload config | Many daemons reload config on SIGHUP |
| `SIGINT` | 2 | Terminate | Ctrl+C in a terminal |
| `SIGSTOP` | 19 | Stop (pause) | Freeze the process -- cannot be caught |
| `SIGCONT` | 18 | Continue | Resume a stopped process |
| `SIGUSR1/2` | 10/12 | User-defined | Application-specific (log rotation, etc.) |

Sending signals: `kill <PID>` (sends SIGTERM), `kill -9 <PID>` (sends SIGKILL), `kill -HUP <PID>` (sends SIGHUP)

### Architecture Thinking: Graceful Shutdown

> **Question**: Your api-service is processing a request when you deploy a new version. What should happen?

This is the graceful shutdown pattern:
1. Receive `SIGTERM`
2. Stop accepting new connections
3. Finish processing in-flight requests
4. Close database connections cleanly
5. Exit with code 0

If a process doesn't respond to `SIGTERM` within a timeout, `SIGKILL` is sent as a last resort.

> **You'll use this when**: Writing Go services with graceful shutdown (Module 3). Configuring Kubernetes pod termination (Module 8) -- K8s sends SIGTERM, waits `terminationGracePeriodSeconds`, then sends SIGKILL. Understanding Docker stop (Module 4) -- same SIGTERM/SIGKILL pattern.

---

## 4. systemd Services

### What Is systemd?

systemd is the init system and service manager for most modern Linux distributions. It:
- Starts services at boot
- Manages service lifecycle (start, stop, restart, reload)
- Handles dependencies between services
- Collects logs (via journald)
- Manages sockets, timers, mounts, and more

### Unit Files

A systemd **unit file** describes a service. Unit files live in:
- `/etc/systemd/system/` -- custom/admin-created units (highest priority)
- `/lib/systemd/system/` -- package-installed units

Example structure of a unit file:

```ini
[Unit]
Description=What this service does
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=flowforge
Group=flowforge
WorkingDirectory=/opt/flowforge
ExecStart=/opt/flowforge/api-service
ExecStop=/bin/kill -SIGTERM $MAINPID
Restart=on-failure
RestartSec=5
EnvironmentFile=/etc/flowforge/api.env

[Install]
WantedBy=multi-user.target
```

### Key Sections

**[Unit]**: Metadata and dependencies
- `After=`: Start this service *after* the listed units
- `Wants=`: Weak dependency -- start the listed units, but don't fail if they don't start
- `Requires=`: Strong dependency -- fail if the listed units don't start

**[Service]**: How to run the service
- `Type=`: `simple` (default), `forking`, `oneshot`, `notify`
- `User=/Group=`: Run as this user/group (NOT root!)
- `ExecStart=`: The command to run
- `Restart=`: When to restart: `no`, `on-failure`, `always`, `on-abnormal`
- `EnvironmentFile=`: Load environment variables from a file

**[Install]**: When to start at boot
- `WantedBy=multi-user.target`: Start when the system reaches multi-user mode (normal boot)

### Managing Services

```bash
systemctl start <service>       # Start now
systemctl stop <service>        # Stop now
systemctl restart <service>     # Stop and start
systemctl reload <service>      # Reload config without stopping (if supported)
systemctl enable <service>      # Start on boot
systemctl disable <service>     # Don't start on boot
systemctl status <service>      # Show current state
systemctl daemon-reload         # Reload unit file changes (after editing .service files)
```

### Viewing Logs with journalctl

```bash
journalctl -u <service>              # All logs for a service
journalctl -u <service> -f           # Follow (tail) logs
journalctl -u <service> --since "1 hour ago"
journalctl -u <service> -p err       # Only errors
journalctl -u <service> --no-pager   # Don't paginate
```

### Architecture Thinking: Why systemd Matters

> **Question**: What happens to your api-service if the server reboots and you didn't configure systemd?

systemd ensures:
- Services start automatically on boot
- Crashed services restart automatically
- Services start in the correct order (database before app)
- Logs are captured centrally

> **You'll use this when**: Understanding Docker's restart policies (Module 4) -- same concept. Kubernetes liveness/readiness probes (Module 8) -- same "is this thing running?" problem. AWS EC2 user data scripts (Module 5) -- systemd starts your app after EC2 boots.

---

## 5. Package Management

### APT (Advanced Package Tool)

Ubuntu/Debian uses `apt` for package management. The package manager handles:
- Downloading software from repositories
- Resolving dependencies (package A needs package B to work)
- Installing, upgrading, and removing software
- Tracking which files belong to which package

### Key Commands

```bash
sudo apt update                    # Refresh package list (always do this first!)
sudo apt install <package>         # Install a package
sudo apt remove <package>          # Remove a package (keep config files)
sudo apt purge <package>           # Remove package AND config files
sudo apt autoremove                # Remove unused dependencies
apt list --installed               # List all installed packages
apt show <package>                 # Show package details
apt search <keyword>               # Search for packages
dpkg -L <package>                  # List all files installed by a package
dpkg -S /path/to/file              # Find which package owns a file
```

### Understanding the Difference

- `apt remove`: Removes the package binary but keeps config files in `/etc/`. Useful when you want to reinstall later with the same config.
- `apt purge`: Removes everything -- binary AND config files. Clean slate.
- `apt autoremove`: Removes packages that were installed as dependencies but are no longer needed.

### Repositories

Packages come from **repositories** configured in `/etc/apt/sources.list` and `/etc/apt/sources.list.d/`. Third-party software (like Docker, Node.js, PostgreSQL) often requires adding their repository first.

### Architecture Thinking: Package Management in Production

> **Question**: Why don't we just download and compile everything from source?

Package management gives you:
- Reproducible installs (same version every time)
- Security updates (one command to patch all packages)
- Dependency management (no "DLL hell")
- Clean removal (nothing left behind)

> **You'll use this when**: Writing Dockerfiles (Module 4) -- `RUN apt-get install` is in every Dockerfile. Configuring EC2 instances (Module 5) -- user data scripts install packages. Understanding why immutable infrastructure matters (Module 6) -- instead of apt-upgrading servers, you replace them.

> **AWS SAA tie-in**: Amazon Linux uses `yum`/`dnf` instead of `apt`, but the concepts are identical. AMIs are pre-packaged OS images -- the "package" at the OS level.

---

## 6. Bash Scripting

### Why Bash?

Bash is the default shell on virtually every Linux system. Every DevOps engineer writes bash scripts for:
- Automation (health checks, deployment scripts, cleanup)
- Glue (connecting tools together)
- One-off tasks that are too complex for a single command

### Script Fundamentals

```bash
#!/bin/bash
# ^ Shebang line: tells the kernel which interpreter to use

set -euo pipefail
# ^ Safety net:
#   -e: Exit immediately if any command fails
#   -u: Treat unset variables as errors
#   -o pipefail: Pipe fails if ANY command in the pipeline fails
```

### Variables

```bash
# Assignment (no spaces around =!)
SERVICE_NAME="api-service"
PORT=8080

# Usage
echo "Starting ${SERVICE_NAME} on port ${PORT}"

# Command substitution
CURRENT_DATE=$(date +%Y-%m-%d)
PID=$(pgrep -f api-service)

# Default values
DB_HOST="${DB_HOST:-localhost}"    # Use localhost if DB_HOST is not set
```

### Conditionals

```bash
# File tests
if [[ -f /etc/flowforge/api.env ]]; then
    echo "Config file exists"
fi

# String comparison
if [[ "${ENV}" == "production" ]]; then
    echo "Running in production"
fi

# Numeric comparison
if [[ ${DISK_USAGE} -gt 80 ]]; then
    echo "WARNING: Disk usage above 80%"
fi

# Command success/failure
if systemctl is-active --quiet postgresql; then
    echo "PostgreSQL is running"
else
    echo "PostgreSQL is NOT running"
fi
```

### Loops

```bash
# Iterate over a list
for service in api-service worker-service postgresql; do
    echo "Checking ${service}..."
done

# Iterate over files
for config_file in /etc/flowforge/*.env; do
    echo "Found config: ${config_file}"
done

# While loop
while ! pg_isready -q; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
```

### Functions

```bash
check_service() {
    local service_name="$1"   # local scope

    if systemctl is-active --quiet "${service_name}"; then
        echo "[OK] ${service_name} is running"
        return 0
    else
        echo "[FAIL] ${service_name} is not running"
        return 1
    fi
}

# Call it
check_service "postgresql"
```

### Argument Parsing

```bash
#!/bin/bash
set -euo pipefail

usage() {
    echo "Usage: $0 [-s service_name] [-v]"
    echo "  -s  Service name to check"
    echo "  -v  Verbose output"
    exit 1
}

VERBOSE=false
SERVICE=""

while getopts "s:vh" opt; do
    case ${opt} in
        s) SERVICE="${OPTARG}" ;;
        v) VERBOSE=true ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [[ -z "${SERVICE}" ]]; then
    echo "Error: Service name is required"
    usage
fi
```

### Exit Codes

Exit codes are how scripts communicate success or failure to the calling process:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Misuse of command/bad arguments |
| 126 | Command found but not executable |
| 127 | Command not found |
| 128+N | Killed by signal N (e.g., 137 = 128+9 = SIGKILL) |

```bash
# Set meaningful exit codes
if ! check_database; then
    echo "CRITICAL: Database is unreachable"
    exit 2
fi

if ! check_disk_space; then
    echo "WARNING: Disk space low"
    exit 1
fi

echo "All checks passed"
exit 0
```

### Architecture Thinking: When Bash vs. When Python?

> **Question**: When should you write a bash script vs. a Python script?

**Use Bash when**:
- Gluing together CLI tools (`grep`, `awk`, `curl`, `jq`)
- Simple automation (start/stop/check services)
- Quick one-off tasks
- Scripts under ~100 lines

**Use Python when**:
- Complex logic, data structures, or error handling
- API interactions (HTTP clients, JSON parsing)
- Anything that needs testing
- Scripts that might grow over time

> **You'll use this when**: Writing health check scripts (this module). Writing Docker entrypoint scripts (Module 4). Writing CI/CD pipeline steps (Module 7). Writing Python automation scripts (Module 3).

---

## 7. Environment Variables & Configuration

### What Are Environment Variables?

Environment variables are key-value pairs that configure how processes behave. They're inherited by child processes (so if you set a variable in your shell, every command you run from that shell sees it).

```bash
# Set for current shell session
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_PASSWORD="secret123"

# View all environment variables
env

# View a specific variable
echo $DB_HOST

# Unset a variable
unset DB_PASSWORD
```

### The .env File Pattern

Rather than setting variables manually, applications use `.env` files:

```bash
# /etc/flowforge/api.env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flowforge
DB_USER=flowforge_api
DB_PASSWORD=changeme_in_production
API_PORT=8080
LOG_LEVEL=info
WORKER_POLL_INTERVAL=5s
```

Loading a .env file in bash:

```bash
# Simple approach (careful: this executes the file!)
source /etc/flowforge/api.env

# Safer approach (export each line)
set -a  # automatically export all variables
source /etc/flowforge/api.env
set +a
```

### The 12-Factor App: Configuration

The [12-Factor App](https://12factor.net/config) methodology says:

> **Store config in the environment**

This means:
- No hardcoded database URLs, API keys, or ports in your code
- Every environment (dev, staging, production) uses the same code with different env vars
- Secrets never live in version control

### Architecture Thinking: Config Management

> **Question**: Why not just put the config in a JSON file that ships with the application?

Environment variables give you:
- **Separation of config from code**: The same binary runs everywhere
- **Secret safety**: Env vars aren't committed to git
- **Platform compatibility**: Every platform (Docker, K8s, EC2, systemd) supports env vars
- **Easy overrides**: Change one variable without redeploying

> **You'll use this when**: Configuring Go services (Module 3) -- `os.Getenv()`. Docker `--env` and `docker-compose.yml` environment sections (Module 4). Kubernetes ConfigMaps and Secrets (Module 8). GitHub Actions secrets (Module 7). AWS Parameter Store and Secrets Manager (Module 10).

> **AWS SAA tie-in**: AWS Systems Manager Parameter Store and Secrets Manager are the cloud-native equivalent of `.env` files. You'll use them to store database credentials, API keys, and other secrets.

---

## 8. SSH (Secure Shell)

### What Is SSH?

SSH is a protocol for secure remote access to systems. It provides:
- **Encrypted communication**: Everything between client and server is encrypted
- **Authentication**: Prove who you are (password or key)
- **Tunneling**: Forward ports through the encrypted connection

### How SSH Key-Based Auth Works

1. You generate a **key pair**: a private key (stays on your machine, NEVER shared) and a public key (goes on every server you need to access)
2. When you connect, the server challenges you to prove you have the private key
3. Your SSH client uses the private key to answer the challenge
4. No password is ever sent over the network

```bash
# Generate a key pair
ssh-keygen -t ed25519 -C "your_email@example.com"
# Creates: ~/.ssh/id_ed25519 (private) and ~/.ssh/id_ed25519.pub (public)

# Copy public key to a server
ssh-copy-id user@server

# Or manually: append the public key to ~/.ssh/authorized_keys on the server
```

### SSH Server Configuration

The SSH server configuration file is `/etc/ssh/sshd_config`. Key settings:

```
Port 2222                          # Change from default 22 (security through obscurity + reduces noise)
PermitRootLogin no                 # Never allow direct root SSH login
PasswordAuthentication no          # Disable password auth -- keys only!
PubkeyAuthentication yes           # Enable key-based auth
MaxAuthTries 3                     # Lock out after 3 failed attempts
AllowUsers flowforge deploy        # Only these users can SSH in
```

After changing sshd_config: `sudo systemctl restart sshd`

### SSH Config File

Your client-side config (`~/.ssh/config`) makes SSH much easier:

```
Host flowforge-dev
    HostName 10.0.1.50
    User deploy
    Port 2222
    IdentityFile ~/.ssh/flowforge_ed25519

Host flowforge-prod
    HostName 10.0.2.50
    User deploy
    Port 2222
    IdentityFile ~/.ssh/flowforge_ed25519
```

Now `ssh flowforge-dev` connects with all the right settings.

### Architecture Thinking: SSH in Production

> **Question**: Why is password authentication disabled on production servers?

- Passwords can be brute-forced; SSH keys are 256+ bits of entropy
- Passwords can be phished; keys never leave your machine
- Passwords require human typing; keys enable automation
- Keys can be revoked per-machine by removing the public key

> **You'll use this when**: Connecting to EC2 instances (Module 5) -- AWS uses key pairs for EC2 SSH access. Setting up GitHub deploy keys (Module 7). Understanding bastion hosts / jump boxes (Module 5) -- SSH through an intermediary to reach private-subnet instances.

> **AWS SAA tie-in**: EC2 key pairs use the same SSH key mechanism. AWS Session Manager is a modern alternative that eliminates the need for SSH ports entirely -- but understanding SSH is still essential for debugging.

---

## Labs for This Module

| Lab | Exercises | What You'll Build |
|-----|-----------|-------------------|
| [Lab 01: Filesystem & Permissions](lab-01-filesystem-permissions.md) | 1a, 1b | FlowForge directory structure with proper ownership and permissions |
| [Lab 02: Processes & systemd](lab-02-processes-systemd.md) | 2a, 2b, 2c | systemd unit files for FlowForge services |
| [Lab 03: Bash Scripting](lab-03-bash-scripting.md) | 3a, 3b | Health check script and environment variable loader |
| [Lab 04: SSH](lab-04-ssh.md) | 4a | SSH key-based authentication setup |
| [Lab 05: Broken Server](lab-05-broken-server.md) | Challenge | Debug 5 deliberate misconfigurations |

---

## Recommended Reading

- [Linux Filesystem Hierarchy Standard](https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)
- [Bash Reference Manual (GNU)](https://www.gnu.org/software/bash/manual/bash.html)
- [systemd documentation](https://www.freedesktop.org/software/systemd/man/)
- [SSH man page](https://man.openbsd.org/ssh)
- [The Twelve-Factor App](https://12factor.net/)
- [Linux man pages online](https://man7.org/linux/man-pages/)

---

## What's Next?

After completing all labs and the [exit gate checklist](checklist.md), you move to **Module 2: Networking Fundamentals** -- where you'll learn the networking concepts that underpin every VPC, subnet, security group, and load balancer you'll build in AWS.

> **Connection**: In this module you learned how a single Linux machine works. In Module 2, you'll learn how machines talk to each other. Together, these two modules form the foundation everything else builds on.
