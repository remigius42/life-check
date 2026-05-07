## Why

The beam-break detector (detector-core) accumulates daily counts silently — a daily push notification via webhook gives visibility without requiring anyone to SSH in or check a UI. The threshold-based message also provides passive sensor health monitoring: zero or suspiciously few breaks triggers an alert.

## What Changes

- New Python reporter script that reads `counts.json`, selects a message template based on count vs threshold, and POSTs to a webhook URL
- New systemd timer unit firing daily at a configurable time (default 17:00)
- New systemd service unit executing the reporter script (one-shot)
- Vault-backed webhook URL variable (`vault_detector_report_webhook_url`)
- Three configurable message templates with `{count}` interpolation token
- Configurable daily threshold variable (default 2)
- Ansible role `detector` extended with reporter script, timer, service, and new variables

## Capabilities

### New Capabilities

- `daily-report`: One-shot reporter script + systemd timer that POSTs a daily summary to a webhook with threshold-based message selection

### Modified Capabilities

- `detector-ansible-role`: Extended with reporter script deployment, systemd timer+service, and new report-related variables

## Impact

- New dependency: `python3-urllib3` or stdlib `urllib.request` (prefer stdlib — no extra apt package needed)
- New systemd units: `beam-detector-report.service` (oneshot), `beam-detector-report.timer`
- `group_vars/all/vault.yml` gains `vault_detector_report_webhook_url`
- `group_vars/all/vars.yml` gains `detector_report_webhook_url` reference
- `playbooks/verify.yml` gains timer-enabled assertion
- No changes to `detector.py` or `counts.json` format
