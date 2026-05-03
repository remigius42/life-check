## Context

`life_man_switch` builds up security layers incrementally via OpenSpec. SSH (`ssh_manage_keys: false`) leaves password auth enabled — fail2ban closes the brute-force window. This change implements SSH jail and optional Slack notification. There is no IRC role in this project.

## Goals / Non-Goals

**Goals:**
- Protect the SSH port against brute-force with sshd jail and configurable tunables
- Optional Slack ban notifications with zero mandatory config (empty string = disabled)
- Follow established project conventions (per-task `become`, `vault_` prefix for secrets, removal tasks for idempotent cleanup)

**Non-Goals:**
- Custom jails for other services (Ergo, Caddy) — those roles don't exist here yet
- IRC notification — no Ergo role
- Unban notifications — actionunban not wired (keep it simple; ban events are the high-value signal)

## Decisions

**`vault_fail2ban_slack_webhook_url` checked directly in task conditionals** rather than a derived `fail2ban_slack_notify_enabled` boolean. The vault variable is already the natural gate — a second boolean would just duplicate it. Separately, define `fail2ban_slack_webhook_url: "{{ vault_fail2ban_slack_webhook_url | default('') }}"` in `vars.yml` so templates can reference a non-vault variable.

**Removal task for `action.d/slack-notify.conf`** when webhook unset — makes the role idempotent across re-runs where the webhook is later removed.

**Single `jail.d/sshd.conf` drop-in** (not editing `jail.conf` or `jail.local`) — drop-ins are composable, won't conflict with package upgrades, and match Debian's recommended approach.

**`become: true` per-task** — project convention from `locales` and `ssh` roles. Keeps privilege scope minimal.

**Handler restarts fail2ban on any config change** — jail drop-in and action file both notify the same handler. Single restart at end of play if either changed.

## Risks / Trade-offs

`vault_fail2ban_slack_webhook_url` undefined (not just empty) will not deploy the action file — this is correct behavior, but operators must add `vault_fail2ban_slack_webhook_url: ""` to `vault.yml` explicitly so the variable is always defined. Add it as part of this change.

Slack curl fires `&>/dev/null &` (background, fire-and-forget) — a webhook failure silently skips the notification. Acceptable: ban action still applies; alerting is best-effort.

## Migration Plan

No prior fail2ban config on target. Run `playbooks/site.yml`, then `playbooks/verify.yml`. Rollback: `apt remove fail2ban`, remove `/etc/fail2ban/jail.d/sshd.conf` and `/etc/fail2ban/action.d/slack-notify.conf`.
