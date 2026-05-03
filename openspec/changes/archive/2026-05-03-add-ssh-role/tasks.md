## 1. Create ssh role skeleton

> Reference: `notes/source-role.md` — contains base task/defaults/handler files and project conventions.

- [x] 1.1 Create `roles/ssh/defaults/main.yml` with `ssh_manage_keys`, `ssh_public_key_file`, `ssh_service_name`, `ssh_remote_user_home`
- [x] 1.2 Create `roles/ssh/tasks/main.yml`: unconditional lineinfile loop (PermitRootLogin/PubkeyAuthentication) runs **first**; then block (when ssh_manage_keys) containing pre-check, key deploy, and PasswordAuthentication lineinfile; become: true on system-touching tasks
- [x] 1.3 Create `roles/ssh/handlers/main.yml`: Restart sshd handler
- [x] 1.4 Create `roles/ssh/meta/main.yml` (same structure as locales meta)
- [x] 1.5 Create `roles/ssh/README.md` documenting ssh_manage_keys and both usage modes
- [x] 1.6 Verify `collections/requirements.yml` includes `ansible.posix`; add if missing

## 2. Wire into playbooks and vars

- [x] 2.1 Add `ssh_manage_keys: false` to `group_vars/all/vars.yml`
- [x] 2.2 Append `- ssh` to roles list in `playbooks/site.yml`
- [x] 2.3 Add SSH assertions to `playbooks/verify.yml`: slurp sshd_config, assert PermitRootLogin no, assert PubkeyAuthentication yes, conditional PasswordAuthentication assertions, service_facts + assert sshd running
