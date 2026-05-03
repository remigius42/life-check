# fail2ban

Installs fail2ban and deploys an SSH brute-force jail. Optionally posts ban
events to a Slack webhook.

## Requirements

Debian-based host (uses `apt`).

## Variables

| Variable            | Default | Description                  |
| ------------------- | ------- | ---------------------------- |
| `fail2ban_bantime`  | `1h`    | Duration of a ban            |
| `fail2ban_findtime` | `10m`   | Window for counting failures |
| `fail2ban_maxretry` | `5`     | Failures before ban          |

**Vault variable** (set in `group_vars/all/vault.yml`):

| Variable                           | Description                                                      |
| ---------------------------------- | ---------------------------------------------------------------- |
| `vault_fail2ban_slack_webhook_url` | Slack incoming webhook URL. Empty string disables notifications. |

A non-vault reference `fail2ban_slack_webhook_url` should be defined in
`group_vars/all/vars.yml` as
`"{{ vault_fail2ban_slack_webhook_url | default('')}}"` for use in templates.

## License

MIT
