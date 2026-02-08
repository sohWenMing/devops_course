# Module 01: Linux Deep Dive -- Answer Key

> **INTERNAL REFERENCE ONLY**: This file is used by the Socratic mentor skill to verify student solutions and provide guidance. It must NEVER be revealed to the student.

---

## Lab 01: Filesystem & Permissions

### Exercise 1a: Filesystem Navigation

**FHS Answers:**

- `/bin` vs `/usr/bin`: On modern Ubuntu, `/bin` is typically a symlink to `/usr/bin`. Historically, `/bin` contained essential binaries needed for single-user mode, while `/usr/bin` contained non-essential user programs. The merge happened because the distinction was no longer meaningful.

- `/proc/cpuinfo`: Contains CPU model name, number of cores, clock speed, cache size, CPU flags (capabilities like SSE, AVX, etc.), and more. It's a virtual filesystem -- the kernel generates this information on the fly.

- `/tmp` sticky bit: `/tmp` has permissions `1777` (drwxrwxrwt). The sticky bit (the `t` in the last position) means only the owner of a file can delete it, even though everyone has write access to `/tmp`. Without it, any user could delete anyone else's temp files.

- `$PATH` and binaries: The `$PATH` variable is a colon-separated list of directories that the shell searches (in order) when you type a command. If `/usr/bin` isn't in your PATH, you'd have to type the full path `/usr/bin/ls` instead of just `ls`.

**Expected FlowForge Directory Structure:**

```
/opt/flowforge/                  # Application binaries
  bin/
    api-service
    worker-service
/etc/flowforge/                  # Configuration files
  api.env
  worker.env
  database.env
/var/log/flowforge/              # Log files
  api-service.log
  worker-service.log
/var/lib/flowforge/              # Runtime data
  data/
  tmp/
```

Rationale:
- `/opt` for third-party application binaries (FlowForge isn't a system package)
- `/etc` for configuration (standard location, sysadmins expect config here)
- `/var/log` for logs (standard, logrotate expects logs here)
- `/var/lib` for runtime/state data (standard for application data)

### Exercise 1b: Users, Groups & Permissions

**Expected Users and Groups:**

```bash
# Create service users (no login shell, no home directory)
sudo useradd --system --no-create-home --shell /usr/sbin/nologin flowforge-api
sudo useradd --system --no-create-home --shell /usr/sbin/nologin flowforge-worker

# Create groups
sudo groupadd flowforge           # Shared group for both services
sudo groupadd flowforge-db-config # Group for database config access

# Add users to groups
sudo usermod -aG flowforge flowforge-api
sudo usermod -aG flowforge flowforge-worker
sudo usermod -aG flowforge-db-config flowforge-api
# Note: worker is NOT in flowforge-db-config

# Create a deploy user
sudo useradd --system --no-create-home --shell /bin/bash deploy
sudo usermod -aG flowforge deploy
```

**Expected Directory Permissions:**

```bash
# Application binaries - owned by root, readable by flowforge group
sudo chown -R root:flowforge /opt/flowforge/
sudo chmod 755 /opt/flowforge/
sudo chmod 755 /opt/flowforge/bin/
sudo chmod 750 /opt/flowforge/bin/api-service
sudo chmod 750 /opt/flowforge/bin/worker-service

# Config files
sudo chown root:flowforge /etc/flowforge/
sudo chmod 750 /etc/flowforge/

# API config - readable by api user
sudo chown root:flowforge-api /etc/flowforge/api.env
sudo chmod 640 /etc/flowforge/api.env

# Worker config - readable by worker user
sudo chown root:flowforge-worker /etc/flowforge/worker.env
sudo chmod 640 /etc/flowforge/worker.env

# Database config - ONLY api user (via db-config group)
sudo chown root:flowforge-db-config /etc/flowforge/database.env
sudo chmod 640 /etc/flowforge/database.env

# Log directory - writable by both services
sudo chown root:flowforge /var/log/flowforge/
sudo chmod 775 /var/log/flowforge/

# Data directory
sudo chown root:flowforge /var/lib/flowforge/
sudo chmod 770 /var/lib/flowforge/
```

**Verification Commands:**

```bash
# Test as api user - should succeed
sudo -u flowforge-api cat /etc/flowforge/database.env

# Test as worker user - should FAIL
sudo -u flowforge-worker cat /etc/flowforge/database.env
# Expected: Permission denied

# Test as deploy user - can update binaries
sudo -u deploy cp new-binary /opt/flowforge/bin/
# But cannot read secrets
sudo -u deploy cat /etc/flowforge/database.env
# Expected: Permission denied
```

**umask:**
- Default umask is typically `022` (files: 644, dirs: 755)
- For service users, `027` is better (files: 640, dirs: 750) -- no "others" access
- Set in the service's environment or shell profile

---

## Lab 02: Processes, systemd & Package Management

### Exercise 2a: Processes & Signals

**Creating Placeholder Processes:**

```bash
# Simple long-running processes
bash -c 'while true; do echo "api-service heartbeat" >> /tmp/api.log; sleep 5; done' &
bash -c 'while true; do echo "worker-service heartbeat" >> /tmp/worker.log; sleep 5; done' &
bash -c 'while true; do echo "monitor heartbeat" >> /tmp/monitor.log; sleep 10; done' &
```

**Finding PIDs (multiple methods):**

```bash
# Method 1: ps with grep
ps aux | grep api-service

# Method 2: pgrep
pgrep -f "api-service"

# Method 3: pidof (works best with actual binary names)
pidof bash  # Less useful for scripts

# Method 4: top/htop - interactive
top
# Press 'o' then type COMMAND=api-service

# Method 5: /proc filesystem
ls /proc/*/cmdline | xargs grep -l "api-service" 2>/dev/null
```

**Signal Behavior:**

```bash
# SIGTERM (signal 15) - graceful
kill -15 <PID>
# Process receives signal, can handle it, clean up, exit
# Exit code: 143 (128 + 15)

# SIGKILL (signal 9) - forceful
kill -9 <PID>
# Process is terminated immediately by the kernel
# No cleanup, no signal handler, no choice
# Exit code: 137 (128 + 9)

# SIGSTOP / SIGCONT
kill -STOP <PID>    # Process enters T (stopped) state, CPU usage drops to 0
kill -CONT <PID>    # Process resumes exactly where it left off
```

**Key difference**: SIGTERM can be caught by the process (allowing graceful shutdown). SIGKILL cannot be caught, blocked, or ignored -- the kernel terminates the process directly.

**Creating a Zombie:**

```bash
# Parent that doesn't wait for child
bash -c '(exit 0) & sleep 60'
# The child exits immediately but becomes a zombie because the parent hasn't called wait()
# Use ps aux | grep Z to find it
```

### Exercise 2b: systemd Unit File

**Expected api-service Script:**

```bash
#!/bin/bash
# /opt/flowforge/bin/api-service-placeholder.sh

echo "FlowForge API Service starting..."
echo "PID: $$"

cleanup() {
    echo "Received shutdown signal. Cleaning up..."
    echo "FlowForge API Service stopped gracefully."
    exit 0
}

trap cleanup SIGTERM SIGINT

while true; do
    echo "[$(date)] api-service heartbeat - OK"
    sleep 5
done
```

**Expected Unit File:**

```ini
# /etc/systemd/system/flowforge-api.service
[Unit]
Description=FlowForge API Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=flowforge-api
Group=flowforge-api
WorkingDirectory=/opt/flowforge
ExecStart=/opt/flowforge/bin/api-service-placeholder.sh
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
EnvironmentFile=/etc/flowforge/api.env

[Install]
WantedBy=multi-user.target
```

**Management Commands:**

```bash
sudo systemctl daemon-reload              # Load the new unit file
sudo systemctl start flowforge-api        # Start now
sudo systemctl enable flowforge-api       # Start on boot
sudo systemctl status flowforge-api       # Check status
journalctl -u flowforge-api -f            # Follow logs
journalctl -u flowforge-api --since "10 minutes ago"
journalctl -u flowforge-api -p err        # Errors only
journalctl -u flowforge-api -o json       # JSON format
```

**Crash Recovery Test:**

```bash
# Kill with -9 (simulates crash)
sudo kill -9 $(pgrep -f api-service-placeholder)
# systemd detects the crash within a few seconds
# After RestartSec (5s), it restarts the service
# journalctl shows: "Main process exited, code=killed, status=9/KILL"
# Then: "Service RestartSec=5s expired, scheduling restart"
```

### Exercise 2c: Package Management

**PostgreSQL Installation:**

```bash
sudo apt update
sudo apt install postgresql postgresql-client

# Verify it's running
sudo systemctl status postgresql
# or
pg_isready

# Find binary
which psql        # /usr/bin/psql
which postgres    # /usr/lib/postgresql/*/bin/postgres

# Config file
/etc/postgresql/<version>/main/postgresql.conf
/etc/postgresql/<version>/main/pg_hba.conf

# Data directory
/var/lib/postgresql/<version>/main/

# Logs
journalctl -u postgresql
# or /var/log/postgresql/

# systemd unit
systemctl cat postgresql

# List all files installed by postgresql
dpkg -L postgresql

# Check dependencies
apt depends postgresql
apt rdepends postgresql

# Check version
psql --version
apt show postgresql
```

**Remove vs Purge:**

```bash
# Remove: removes binaries but keeps config files in /etc/
sudo apt remove nginx
ls /etc/nginx/        # Config files still exist!

# Purge: removes binaries AND config files
sudo apt purge nginx
ls /etc/nginx/        # Directory gone

# Cleanup unused dependencies
sudo apt autoremove
```

---

## Lab 03: Bash Scripting

### Exercise 3a: Health Check Script

**Expected Solution:**

```bash
#!/bin/bash
set -uo pipefail
# Note: -e intentionally omitted so script doesn't exit on first check failure

SCRIPT_NAME=$(basename "$0")
VERBOSE=false
DISK_THRESHOLD=80
CHECKS_PASSED=0
CHECKS_TOTAL=0

usage() {
    echo "Usage: ${SCRIPT_NAME} [-v] [-t threshold] [-h]"
    echo ""
    echo "FlowForge Health Check Script"
    echo ""
    echo "Options:"
    echo "  -v            Verbose output"
    echo "  -t threshold  Disk usage threshold percentage (default: 80)"
    echo "  -h            Show this help message"
    exit 2
}

log_verbose() {
    if [[ "${VERBOSE}" == "true" ]]; then
        echo "  DETAIL: $1"
    fi
}

check_pass() {
    echo "[OK]   $1"
    ((CHECKS_PASSED++))
    ((CHECKS_TOTAL++))
}

check_fail() {
    echo "[FAIL] $1"
    ((CHECKS_TOTAL++))
}

# Parse arguments
while getopts "vt:h" opt; do
    case ${opt} in
        v) VERBOSE=true ;;
        t)
            DISK_THRESHOLD="${OPTARG}"
            if ! [[ "${DISK_THRESHOLD}" =~ ^[0-9]+$ ]]; then
                echo "Error: Threshold must be a number"
                exit 2
            fi
            ;;
        h) usage ;;
        *) usage ;;
    esac
done

echo "========================================"
echo "FlowForge Health Check - $(date)"
echo "========================================"
echo ""

# Check 1: PostgreSQL running
if systemctl is-active --quiet postgresql 2>/dev/null; then
    check_pass "PostgreSQL is running"
    if [[ "${VERBOSE}" == "true" ]]; then
        PG_PID=$(pgrep -f "postgres:" | head -1)
        log_verbose "PostgreSQL PID: ${PG_PID:-unknown}"
    fi
else
    check_fail "PostgreSQL is NOT running"
fi

# Check 2: API service port listening
API_PORT="${API_PORT:-8080}"
if ss -tlnp 2>/dev/null | grep -q ":${API_PORT} " || \
   netstat -tlnp 2>/dev/null | grep -q ":${API_PORT} "; then
    check_pass "API service port ${API_PORT} is listening"
    if [[ "${VERBOSE}" == "true" ]]; then
        LISTENER=$(ss -tlnp 2>/dev/null | grep ":${API_PORT} " || true)
        log_verbose "Listener: ${LISTENER}"
    fi
else
    check_fail "API service port ${API_PORT} is NOT listening"
    log_verbose "No process listening on port ${API_PORT}"
fi

# Check 3: Disk usage
DISK_USAGE=$(df / --output=pcent | tail -1 | tr -d '% ')
if [[ ${DISK_USAGE} -lt ${DISK_THRESHOLD} ]]; then
    check_pass "Disk usage is ${DISK_USAGE}% (threshold: ${DISK_THRESHOLD}%)"
else
    check_fail "Disk usage is ${DISK_USAGE}% (threshold: ${DISK_THRESHOLD}%)"
fi
log_verbose "Root partition: $(df -h / --output=size,used,avail | tail -1)"

# Summary
echo ""
echo "========================================"
echo "Results: ${CHECKS_PASSED} of ${CHECKS_TOTAL} checks passed"
echo "========================================"

if [[ ${CHECKS_PASSED} -eq ${CHECKS_TOTAL} ]]; then
    exit 0
else
    exit 1
fi
```

### Exercise 3b: Environment Variable Loading Script

**Expected .env File:**

```bash
# /etc/flowforge/api.env
# FlowForge API Service Configuration

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flowforge
DB_USER=flowforge_api
DB_PASSWORD=changeme_in_production

# API Service
API_PORT=8080
LOG_LEVEL=info

# Worker Service
WORKER_POLL_INTERVAL=5
WORKER_MAX_CONCURRENT=3

# Environment
ENVIRONMENT=dev
```

**Expected Validation Script:**

```bash
#!/bin/bash
set -uo pipefail

SCRIPT_NAME=$(basename "$0")
ERRORS=0

usage() {
    echo "Usage: ${SCRIPT_NAME} <path-to-env-file>"
    echo ""
    echo "Loads and validates FlowForge environment variables."
    exit 2
}

error() {
    echo "[ERROR] $1"
    ((ERRORS++))
}

warn() {
    echo "[WARN]  $1"
}

info() {
    echo "[INFO]  $1"
}

mask_secret() {
    local value="$1"
    if [[ ${#value} -gt 4 ]]; then
        echo "${value:0:2}****${value: -2}"
    else
        echo "****"
    fi
}

validate_number() {
    local name="$1"
    local value="$2"
    if ! [[ "${value}" =~ ^[0-9]+$ ]]; then
        error "${name} must be a number, got: '${value}'"
        return 1
    fi
    return 0
}

validate_port() {
    local name="$1"
    local value="$2"
    if ! validate_number "${name}" "${value}"; then
        return 1
    fi
    if [[ ${value} -lt 1 || ${value} -gt 65535 ]]; then
        error "${name} must be between 1 and 65535, got: ${value}"
        return 1
    fi
    return 0
}

validate_enum() {
    local name="$1"
    local value="$2"
    shift 2
    local valid_values=("$@")
    for v in "${valid_values[@]}"; do
        if [[ "${value}" == "${v}" ]]; then
            return 0
        fi
    done
    error "${name} must be one of: ${valid_values[*]}, got: '${value}'"
    return 1
}

# Check arguments
if [[ $# -ne 1 ]]; then
    usage
fi

ENV_FILE="$1"

# Check file exists
if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Error: Environment file not found: ${ENV_FILE}"
    exit 2
fi

# Load variables
set -a
source "${ENV_FILE}"
set +a

echo "========================================"
echo "FlowForge Environment Validation"
echo "File: ${ENV_FILE}"
echo "========================================"
echo ""

# Required variables
REQUIRED_VARS=(
    "DB_HOST"
    "DB_PORT"
    "DB_NAME"
    "DB_USER"
    "DB_PASSWORD"
    "API_PORT"
    "LOG_LEVEL"
    "WORKER_POLL_INTERVAL"
    "WORKER_MAX_CONCURRENT"
    "ENVIRONMENT"
)

# Check all required variables are set
for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        error "Required variable ${var} is not set or empty"
    fi
done

# If any required vars are missing, exit early
if [[ ${ERRORS} -gt 0 ]]; then
    echo ""
    echo "FAILED: ${ERRORS} error(s) found. Fix required variables first."
    exit 1
fi

# Validate formats
validate_port "DB_PORT" "${DB_PORT}"
validate_port "API_PORT" "${API_PORT}"
validate_number "WORKER_POLL_INTERVAL" "${WORKER_POLL_INTERVAL}"
validate_number "WORKER_MAX_CONCURRENT" "${WORKER_MAX_CONCURRENT}"
validate_enum "LOG_LEVEL" "${LOG_LEVEL}" "debug" "info" "warn" "error"
validate_enum "ENVIRONMENT" "${ENVIRONMENT}" "dev" "staging" "production"

# Results
echo ""
if [[ ${ERRORS} -eq 0 ]]; then
    echo "PASSED: All variables valid"
    echo ""
    echo "Configuration Summary:"
    echo "  DB_HOST:               ${DB_HOST}"
    echo "  DB_PORT:               ${DB_PORT}"
    echo "  DB_NAME:               ${DB_NAME}"
    echo "  DB_USER:               ${DB_USER}"
    echo "  DB_PASSWORD:           $(mask_secret "${DB_PASSWORD}")"
    echo "  API_PORT:              ${API_PORT}"
    echo "  LOG_LEVEL:             ${LOG_LEVEL}"
    echo "  WORKER_POLL_INTERVAL:  ${WORKER_POLL_INTERVAL}"
    echo "  WORKER_MAX_CONCURRENT: ${WORKER_MAX_CONCURRENT}"
    echo "  ENVIRONMENT:           ${ENVIRONMENT}"
    exit 0
else
    echo "FAILED: ${ERRORS} error(s) found"
    exit 1
fi
```

---

## Lab 04: SSH

### Exercise 4a: SSH Setup

**Key Generation:**

```bash
# Generate Ed25519 key (recommended -- faster and more secure than RSA)
ssh-keygen -t ed25519 -C "flowforge-admin" -f ~/.ssh/flowforge_ed25519
# Passphrase: optional but recommended for interactive use; skip for automated access

# Verify files created
ls -la ~/.ssh/flowforge_ed25519*
# -rw------- 1 user user  464 Jan 15 10:30 flowforge_ed25519      (PRIVATE - 600!)
# -rw-r--r-- 1 user user   98 Jan 15 10:30 flowforge_ed25519.pub  (public - 644 is fine)
```

**sshd_config Hardening:**

```bash
# Backup first!
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# Edit sshd_config
sudo nano /etc/ssh/sshd_config
```

Key settings to change:

```
Port 2222                          # Non-standard port
PermitRootLogin no                 # No direct root login
PasswordAuthentication no          # Keys only
PubkeyAuthentication yes           # Explicit enable
MaxAuthTries 3                     # Limit brute force
AllowUsers deploy flowforge-api    # Whitelist users
ChallengeResponseAuthentication no # Disable keyboard-interactive
X11Forwarding no                   # Not needed for servers
```

```bash
# Validate config
sudo sshd -t
# No output = config is valid

# Restart (keep your current session open!)
sudo systemctl restart sshd
```

**Setting Up Key-Based Auth:**

```bash
# Ensure .ssh directory exists with correct permissions
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add public key to authorized_keys
cat ~/.ssh/flowforge_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Critical permissions:
# ~/.ssh/                 -> 700 (drwx------)
# ~/.ssh/authorized_keys  -> 600 (-rw-------)
# ~/.ssh/id_*             -> 600 (-rw-------)
# ~/.ssh/id_*.pub         -> 644 (-rw-r--r--)
```

**Testing:**

```bash
# From a NEW terminal
ssh -i ~/.ssh/flowforge_ed25519 -p 2222 user@localhost

# Or with SSH config:
# ~/.ssh/config
Host flowforge-local
    HostName localhost
    User deploy
    Port 2222
    IdentityFile ~/.ssh/flowforge_ed25519

# Then just:
ssh flowforge-local
```

**Port Forwarding Example:**

```bash
# Local port forwarding: access remote PostgreSQL through SSH tunnel
ssh -L 5433:localhost:5432 flowforge-local
# Now connect to localhost:5433 and traffic is tunneled to remote's localhost:5432
```

---

## Lab 05: Broken Server -- Answer Key

### The 5 Misconfigurations

**break-server.sh Example Implementation:**

```bash
#!/bin/bash
# SETUP: Ensure FlowForge environment exists from earlier labs first

# Issue 1: Wrong permissions on the api-service binary (removes execute permission)
sudo chmod 644 /opt/flowforge/bin/api-service-placeholder.sh
# Symptom: systemd fails to start the service -- "Permission denied" or "Exec format error"
# Fix: sudo chmod 755 /opt/flowforge/bin/api-service-placeholder.sh

# Issue 2: Kill PostgreSQL and disable it
sudo systemctl stop postgresql
sudo systemctl disable postgresql
# Symptom: PostgreSQL isn't running, health check fails, any DB-dependent service fails
# Fix: sudo systemctl enable postgresql && sudo systemctl start postgresql

# Issue 3: Fill up /var/log/flowforge/ with a huge file (simulates disk issue)
sudo dd if=/dev/zero of=/var/log/flowforge/runaway.log bs=1M count=500 2>/dev/null
# Symptom: Disk usage may be high, or if /var is a separate partition it might fill up
# Also: the file shouldn't be there -- it's an anomaly to investigate
# Fix: sudo rm /var/log/flowforge/runaway.log

# Issue 4: Change the .env file to have an invalid DB_PORT
sudo sed -i 's/DB_PORT=5432/DB_PORT=NOTAPORT/' /etc/flowforge/api.env
# Symptom: Env validation fails, services can't connect to database
# Fix: sudo sed -i 's/DB_PORT=NOTAPORT/DB_PORT=5432/' /etc/flowforge/api.env

# Issue 5: Change the owner of the config directory to root:root with restrictive permissions
sudo chown root:root /etc/flowforge/database.env
sudo chmod 600 /etc/flowforge/database.env
# Symptom: api-service user can't read database config (was flowforge-db-config group)
# Fix: sudo chown root:flowforge-db-config /etc/flowforge/database.env && sudo chmod 640 /etc/flowforge/database.env

echo "Server is now 'broken'. Good luck!"
```

### Expected Debugging Approach

**Systematic methodology:**

1. **Start broad**: `systemctl status flowforge-api`, `journalctl -u flowforge-api -n 50`
2. **Check related services**: `systemctl status postgresql`, `pg_isready`
3. **Check resources**: `df -h`, `free -h`, `top`
4. **Check permissions**: `ls -la /opt/flowforge/bin/`, `ls -la /etc/flowforge/`
5. **Check config**: Run the validation script, check .env file contents
6. **Verify fixes one at a time**: Fix one issue, verify, then move to the next

### Expected Incident Report Format

```markdown
## Issue 1: API Service Binary Not Executable

**Symptom**: `systemctl start flowforge-api` fails. Status shows "code=exited, status=203/EXEC"
**Investigation**:
- `systemctl status flowforge-api` → shows 203/EXEC error
- `journalctl -u flowforge-api` → "Permission denied" or "Exec format error"
- `ls -la /opt/flowforge/bin/api-service-placeholder.sh` → permissions are 644 (no execute bit)
**Root Cause**: The execute permission was removed from the service binary
**Fix**: `sudo chmod 755 /opt/flowforge/bin/api-service-placeholder.sh`
**Verification**: `systemctl start flowforge-api && systemctl status flowforge-api` → active (running)
```

---

## Checkpoint Answer Reference

### Filesystem Checkpoint
- PostgreSQL config: `/etc/postgresql/<version>/main/postgresql.conf`
- systemd unit files: `/etc/systemd/system/` (admin-created) or `/lib/systemd/system/` (package-created)
- PID 1234 info: `/proc/1234/status`, `/proc/1234/cmdline`, `/proc/1234/environ`
- `/tmp` vs `/var/tmp`: `/tmp` is cleared on reboot, `/var/tmp` persists across reboots

### Process Checkpoint
- 3 ways to find a PID: `ps aux | grep name`, `pgrep -f name`, `pidof name`
- Zombie: a process that has exited but whose parent hasn't called `wait()` to collect its exit status. It exists so the parent can retrieve the exit code.
- Ctrl+C sends SIGINT (2), Ctrl+Z sends SIGTSTP (20)

### systemd Checkpoint
- After editing unit file: `systemctl daemon-reload`
- `enable` vs `start`: enable sets it to start on boot, start runs it now. They are independent operations.
- Last 50 lines: `journalctl -u service -n 50`

### Bash Checkpoint
- `set -e`: exit on error, `set -u`: error on unset variables, `set -o pipefail`: pipe returns rightmost non-zero exit code
- Exit 0: success. Exit 1: general error (check failed). Exit 2: bad usage (wrong arguments)

### SSH Checkpoint
- `~/.ssh/` must be 700, `~/.ssh/authorized_keys` must be 600, private keys must be 600
- SSH refuses to use keys with wrong permissions because loose permissions mean other users could read or modify them, defeating the purpose of key-based auth
- Never close existing session because if new config has errors, you'd lose access to the machine

### Environment Variable Checkpoint
- FlowForge variables: DB_HOST (where to find database), DB_PORT (which port), DB_NAME (which database), DB_USER (authentication), DB_PASSWORD (authentication), API_PORT (which port to listen on), LOG_LEVEL (verbosity control), WORKER_POLL_INTERVAL (how often to check for work), WORKER_MAX_CONCURRENT (parallelism limit), ENVIRONMENT (behavior differences)
- `source script.sh` runs in the current shell (variables are exported to current session). `./script.sh` runs in a subshell (variables are lost when it exits)
- If `.env` with secrets is committed to git: immediately rotate ALL credentials in the file (they must be considered compromised), remove the file from git history using `git filter-branch` or BFG Repo Cleaner (just deleting the file doesn't remove it from history), add `.env` to `.gitignore`, notify the security team
