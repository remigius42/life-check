## Why

The Raspberry Pi deployment needs a daemon that counts beam breaks from the break-beam sensor on GPIO pin 17, persists daily totals with history, and supports a non-counting test mode — this is the core sensing layer on which future reporting and web UI increments will build.

## What Changes

- New Ansible role `detector` deploying the daemon, config, and systemd service
- New Python daemon `detector.py` monitoring GPIO for beam-break events (rising edge detection)
- Daily counter with midnight reset, persisted to JSON with configurable retention (default 14 days)
- Test mode toggled via sentinel file `/run/beam_detector/test_mode`; auto-reverts after configurable grace period (default 30 min)
- Systemd service enabling the daemon at boot with `Restart=on-failure`
- Unit tests covering counting, test mode, daily reset, history retention, and persistence
- `playbooks/site.yml` and `playbooks/verify.yml` updated to include the new role

## Capabilities

### New Capabilities

- `beam-detector-daemon`: GPIO polling daemon with rising-edge break detection, daily counter, midnight reset, JSON persistence, and sentinel-file-based test mode
- `detector-ansible-role`: Ansible role deploying the daemon script, INI config, systemd service unit, and all required directories

### Modified Capabilities

<!-- none -->

## Impact

- New Python dependency: `python3-rpi.gpio` (apt)
- New systemd service: `beam-detector.service`
- New directories on target: `/opt/beam_detector/`, `/etc/beam_detector/`, `/var/lib/beam_detector/`, `/run/beam_detector/`
- `playbooks/site.yml` gains `- detector` role entry
- `playbooks/verify.yml` gains six assertion tasks
- No changes to existing roles (ssh, ufw, fail2ban, locales)
