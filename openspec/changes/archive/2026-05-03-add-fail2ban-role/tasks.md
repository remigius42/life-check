## 1. Create role skeleton

- [x] 1.1 Create `roles/fail2ban/defaults/main.yml` with `fail2ban_bantime`, `fail2ban_findtime`, `fail2ban_maxretry` defaults
- [x] 1.2 Create `roles/fail2ban/tasks/main.yml`: install package, deploy jail drop-in, deploy/remove slack action file, enable service
- [x] 1.3 Create `roles/fail2ban/handlers/main.yml`: restart fail2ban handler
- [x] 1.4 Create `roles/fail2ban/templates/jail.d/sshd.conf.j2` with tunable variables
- [x] 1.5 Create `roles/fail2ban/templates/action.d/slack-notify.conf.j2` (curl webhook, fire-and-forget)
- [x] 1.6 Create `roles/fail2ban/meta/main.yml` and `roles/fail2ban/README.md`

## 2. Wire into playbooks and group_vars

- [x] 2.1 Add `fail2ban_bantime`, `fail2ban_findtime`, `fail2ban_maxretry`, `fail2ban_slack_webhook_url` to `group_vars/all/vars.yml`
- [x] 2.2 Add `vault_fail2ban_slack_webhook_url: ""` to `group_vars/all/vault.yml`
- [x] 2.3 Add `fail2ban` role after `ufw` in `playbooks/site.yml`

## 3. Add verify.yml assertions

- [x] 3.1 Add fail2ban service running/enabled assertion to `playbooks/verify.yml`
- [x] 3.2 Add `/etc/fail2ban/jail.d/sshd.conf` existence assertion
- [x] 3.3 Add conditional `slack-notify.conf` present/absent assertions (gated on `vault_fail2ban_slack_webhook_url`)
