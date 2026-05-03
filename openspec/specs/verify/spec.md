## Purpose
Assert post-state of all applied roles via `playbooks/verify.yml`.

## Requirements

### Requirement: verify.yml asserts SSH post-state
`playbooks/verify.yml` SHALL assert the SSH role's post-state after a successful `site.yml` run.

#### Scenario: Run verify after successful site.yml (ssh_manage_keys false)
- **WHEN** `playbooks/verify.yml` runs with `ssh_manage_keys: false`
- **THEN** assertions pass: `PermitRootLogin no` present, `PubkeyAuthentication yes` present, `PasswordAuthentication no` absent, sshd service running

#### Scenario: Run verify after successful site.yml (ssh_manage_keys true)
- **WHEN** `playbooks/verify.yml` runs with `ssh_manage_keys: true`
- **THEN** assertions pass: `PermitRootLogin no` present, `PubkeyAuthentication yes` present, `PasswordAuthentication no` present, sshd service running

### Requirement: verify.yml asserts ufw post-state
`playbooks/verify.yml` SHALL assert that UFW is active after a successful `site.yml` run.

#### Scenario: Run verify after successful site.yml
- **WHEN** `playbooks/verify.yml` runs
- **THEN** `ufw status` reports `Status: active`

### Requirement: verify.yml asserts fail2ban post-state
`playbooks/verify.yml` SHALL assert the fail2ban role's post-state after a successful `site.yml` run.

#### Scenario: Run verify after successful site.yml
- **WHEN** `playbooks/verify.yml` runs
- **THEN** assertions pass: fail2ban service running and enabled, `/etc/fail2ban/jail.d/sshd.conf` present

#### Scenario: Slack action file present when webhook URL set
- **WHEN** `playbooks/verify.yml` runs and `vault_fail2ban_slack_webhook_url` is non-empty
- **THEN** `/etc/fail2ban/action.d/slack-notify.conf` exists

#### Scenario: Slack action file absent when webhook URL unset
- **WHEN** `playbooks/verify.yml` runs and `vault_fail2ban_slack_webhook_url` is empty or undefined
- **THEN** `/etc/fail2ban/action.d/slack-notify.conf` does not exist
