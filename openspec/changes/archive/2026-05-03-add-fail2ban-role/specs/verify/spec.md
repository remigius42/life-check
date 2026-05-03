## ADDED Requirements

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
