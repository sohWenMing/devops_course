# Module 1: Linux Deep Dive -- Exit Gate Checklist

> **Instructions**: You must be able to answer YES to **every** item below before moving to Module 2.  
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

## Filesystem & Permissions (Lab 01)

- [ ] I can draw the Linux FHS from memory and explain where config files (`/etc`), logs (`/var/log`), temporary files (`/tmp`), user data (`/home`), binaries (`/usr/bin`), and process info (`/proc`) live
- [ ] Given an `ls -la` output, I can explain every column: file type, permissions (owner/group/others), link count, owner, group, size, timestamp, name
- [ ] I can set file permissions using both symbolic (`chmod u+x`) and octal (`chmod 750`) notation
- [ ] I can create a user, create a group, add the user to the group, and set file ownership so that only specific users/groups can access a file
- [ ] I can set permissions so the api-service user can read a config file but the worker-service user cannot
- [ ] I can explain what SUID, SGID, and the sticky bit do and give a real-world example of each
- [ ] I can explain what `umask` does and set it appropriately for a service user

---

## Processes & Signals (Lab 02, Exercise 2a)

- [ ] I can start 3 background processes, find their PIDs without looking at the terminal that started them, and prove I found the right ones
- [ ] I can kill one process gracefully (SIGTERM) and one forcefully (SIGKILL) and explain the behavioral difference
- [ ] I can explain what happens when a process receives SIGTERM vs SIGKILL (hint: one can be caught, one cannot)
- [ ] I can explain what a zombie process is and why it exists
- [ ] I can use at least 3 different commands/tools to find information about running processes

---

## systemd Services (Lab 02, Exercise 2b)

- [ ] I can write a complete systemd unit file from scratch for a new service (not by copying an existing one) that includes: description, dependencies, user, restart policy, and environment file
- [ ] I can start, stop, restart, enable, and disable a service using systemctl
- [ ] I know to run `systemctl daemon-reload` after editing a unit file and can explain why
- [ ] I can view service logs using journalctl with time filters, severity filters, and follow mode
- [ ] I can explain the difference between `Wants=` and `Requires=` in a unit file
- [ ] I can explain the difference between `systemctl start` and `systemctl enable`

---

## Package Management (Lab 02, Exercise 2c)

- [ ] I can install a package, find its config files, find its logs, and remove it cleanly
- [ ] I can explain the difference between `apt remove` and `apt purge`
- [ ] I know to run `apt update` before installing and can explain why
- [ ] Given an installed package, I can list all the files it installed on the system
- [ ] Given a file path, I can find which package owns it

---

## Bash Scripting (Lab 03)

- [ ] I can write a bash script from scratch with argument parsing (`getopts`), error handling (`set -euo pipefail`), and meaningful exit codes
- [ ] I can explain what each flag in `set -euo pipefail` does
- [ ] I can write conditional checks: file existence, string comparison, numeric comparison, and command success/failure
- [ ] I can write a function that takes arguments, uses local variables, and returns meaningful exit codes
- [ ] Given a new requirement (e.g., "check if a service is running and report its memory usage"), I can write a complete script without referencing previous scripts

---

## Environment Variables & Configuration (Lab 03)

- [ ] I can list from memory every environment variable FlowForge needs and explain why each one exists
- [ ] I can write a script that loads a `.env` file, validates all required variables are set, validates their formats, and exits with a clear error if anything is wrong
- [ ] I can explain the difference between `source script.sh` and `./script.sh` in terms of variable scope
- [ ] I can explain why secrets should never be committed to git and what to do if it happens accidentally
- [ ] I understand the 12-Factor App principle of storing config in the environment

---

## SSH (Lab 04)

- [ ] Given a fresh machine, I can set up SSH key-only access in under 5 minutes: generate key pair, place public key, configure sshd, disable password auth, test
- [ ] I can explain why password authentication is disabled in production
- [ ] I can explain the difference between the private key and the public key, and what would happen if the private key were compromised
- [ ] I know the correct file permissions for `~/.ssh/`, `~/.ssh/authorized_keys`, and private key files, and why SSH enforces them
- [ ] I can create an SSH client config file with host aliases for convenient connections
- [ ] I can explain what a bastion/jump host is and why it's used (preview for Module 5)

---

## Debugging (Lab 05)

- [ ] I successfully found and fixed all 5 misconfigurations in the Broken Server challenge
- [ ] I documented each issue with: symptom, investigation commands, root cause, fix, and verification
- [ ] I have a systematic debugging methodology: check logs -> check service status -> check permissions -> check config -> check resources
- [ ] If given a new broken Linux system with different issues, I am confident I could diagnose and fix them without hints
- [ ] I can name 5 commands I would run first when investigating a server issue and explain why each one

---

## Integration & Architecture Thinking

- [ ] I can explain how Linux filesystem structure relates to Docker container images (preview)
- [ ] I can explain how Linux processes and signals relate to container lifecycle management (preview)
- [ ] I can explain how systemd is similar to Kubernetes pod management (preview)
- [ ] I can explain why least-privilege file permissions and dedicated service users matter for security (preview for Module 10)

---

## Final Self-Assessment

> Answer honestly:
>
> **Could I do all of the above on a completely fresh Ubuntu system with no internet access and no notes?**
>
> - If YES for everything: You're ready for Module 2. Congratulations!
> - If NO for anything: Go back and practice. There are no shortcuts in DevOps.

---

## Ready for Module 2?

If every box above is checked, proceed to [Module 2: Networking Fundamentals](../module-02-networking/README.md).

> **What's coming**: In Module 2, you'll learn how machines communicate. You'll use tools like `tcpdump`, `dig`, `curl`, `ss`, `iptables`, and `nginx` to understand the networking stack that underpins every cloud service. The Linux skills you just learned are the foundation everything else builds on.
