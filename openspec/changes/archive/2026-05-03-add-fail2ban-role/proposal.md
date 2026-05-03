## Why

The `ssh` role (when `ssh_manage_keys: false`) leaves password auth enabled, exposing the host to brute-force attacks until fail2ban is active. Fail2ban closes this window and optionally posts ban events to a Slack webhook for operator visibility.

## What Changes

- New `roles/fail2ban/` Ansible role
- SSH jail with tunables: `fail2ban_bantime`, `fail2ban_findtime`, `fail2ban_maxretry`
- Optional Slack ban notification: deploy `action.d/slack-notify.conf` when `vault_fail2ban_slack_webhook_url` is set; remove it when unset
- `group_vars/all/vars.yml`: add fail2ban tunables + `fail2ban_slack_webhook_url` reference
- `group_vars/all/vault.yml`: add `vault_fail2ban_slack_webhook_url: ""`
- `playbooks/site.yml`: add `fail2ban` role after `ufw`
- `playbooks/verify.yml`: add fail2ban service and jail assertions

## Capabilities

### New Capabilities

- `fail2ban`: SSH brute-force protection with optional Slack ban notifications

### Modified Capabilities

- `site`: fail2ban role added after ufw in execution order
- `verify`: fail2ban service, sshd jail, and conditional slack-notify.conf assertions added

## Impact

- `roles/fail2ban/` (new): defaults, tasks, handlers, meta, templates, README
- `group_vars/all/vars.yml`: three new variables
- `group_vars/all/vault.yml`: one new vault variable
- `playbooks/site.yml`: one new role entry
- `playbooks/verify.yml`: new assertion block
