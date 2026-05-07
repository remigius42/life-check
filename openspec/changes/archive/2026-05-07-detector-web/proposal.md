## Why

The beam-break detector currently has no live visibility — checking counts or beam state requires SSH. A minimal web UI on the LAN gives at-a-glance status and lets users toggle test mode without touching a terminal.

## What Changes

- New Flask web server (`web.py`) serving a single-page status UI
- Status page shows: today's break count, current beam state (broken/clear), test mode indicator, and a toggle button to enter/exit test mode
- Test mode toggle writes or deletes the sentinel file `/run/beam_detector/test_mode`
- New systemd service `beam-detector-web.service` running the Flask app
- UFW rule opening the configured port (default 8080) for LAN subnet only
- `detector` Ansible role extended with web server script, systemd service, UFW rule, and new variables

## Capabilities

### New Capabilities

- `web-status-ui`: Flask web server exposing live beam-break status and test mode toggle
- `lan-firewall-rule`: UFW rule allowing LAN access to the web server port

### Modified Capabilities

- `detector-ansible-role`: Extended with web server script deployment, systemd service, UFW rule, and web-related variables

## Impact

- New apt dependency: `python3-flask`
- New systemd service: `beam-detector-web.service`
- New UFW rule: allow TCP port `{{ detector_web_port }}` from `{{ ufw_lan_subnet }}`
- Uses existing `ufw_lan_subnet` variable (already defined in `group_vars/all/vars.yml` by the `ufw` role)
- `community.general.ufw` module already available (used by `ufw` role)
- No changes to `detector.py`, `reporter.py`, or `counts.json` format
- `playbooks/verify.yml` gains web service running assertion
