## Purpose
Install fail2ban and protect the SSH port against brute-force attacks. Optionally post ban events to a Slack webhook.

## Requirements

### Requirement: fail2ban installed and running
The role SHALL install the `fail2ban` package and ensure the service is enabled and started.

#### Scenario: Fresh host
- **WHEN** the `fail2ban` role runs on a host without fail2ban installed
- **THEN** the package is present, the service is enabled, and the service is running

### Requirement: SSH jail deployed with tunables
The role SHALL deploy `/etc/fail2ban/jail.d/sshd.conf` with values derived from `fail2ban_bantime`, `fail2ban_findtime`, and `fail2ban_maxretry`. Defaults: `bantime: 1h`, `findtime: 10m`, `maxretry: 5`.

#### Scenario: Default tunables
- **WHEN** the role runs without overrides
- **THEN** `/etc/fail2ban/jail.d/sshd.conf` exists with `bantime = 1h`, `findtime = 10m`, `maxretry = 5`, and `[sshd]` jail enabled

#### Scenario: Custom tunables
- **WHEN** `fail2ban_bantime: 24h`, `fail2ban_findtime: 1h`, `fail2ban_maxretry: 3` are set
- **THEN** `/etc/fail2ban/jail.d/sshd.conf` reflects the overridden values

### Requirement: Slack notification deployed when webhook URL is set
When `vault_fail2ban_slack_webhook_url` is defined and non-empty, the role SHALL deploy `/etc/fail2ban/action.d/slack-notify.conf` and wire it into the sshd jail. When unset or empty, the action file SHALL be absent.

#### Scenario: Webhook URL provided
- **WHEN** `vault_fail2ban_slack_webhook_url` is set to a non-empty string
- **THEN** `/etc/fail2ban/action.d/slack-notify.conf` is present and the sshd jail's `action` references `slack-notify`

#### Scenario: Webhook URL not provided
- **WHEN** `vault_fail2ban_slack_webhook_url` is empty or undefined
- **THEN** `/etc/fail2ban/action.d/slack-notify.conf` is absent

#### Scenario: Webhook URL removed after prior deploy
- **WHEN** `vault_fail2ban_slack_webhook_url` was previously set but is now empty
- **THEN** `/etc/fail2ban/action.d/slack-notify.conf` is removed and fail2ban is restarted

### Requirement: Config changes trigger fail2ban restart
The role SHALL notify a handler to restart fail2ban whenever a jail drop-in or action file changes.

#### Scenario: Jail config updated
- **WHEN** `/etc/fail2ban/jail.d/sshd.conf` changes
- **THEN** fail2ban service is restarted
