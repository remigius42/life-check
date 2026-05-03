## 1. Create ufw role

- [x] 1.1 Create `roles/ufw/defaults/main.yml` with `ufw_lan_subnet: ""`
- [x] 1.2 Create `roles/ufw/tasks/main.yml`: validate subnet, install ufw, default deny incoming, default allow outgoing, allow SSH from LAN, enable UFW
- [x] 1.3 Create `roles/ufw/meta/main.yml`
- [x] 1.4 Create `roles/ufw/README.md`

## 2. Wire into playbooks and vars

- [x] 2.1 Add `ufw_lan_subnet: "192.168.0.0/24"` to `group_vars/all/vars.yml`
- [x] 2.2 Add `- ufw` after `- ssh` in `playbooks/site.yml`
- [x] 2.3 Add ufw assertions to `playbooks/verify.yml`
