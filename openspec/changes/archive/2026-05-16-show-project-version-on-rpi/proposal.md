## Why

The Flask web UI on the Raspberry Pi shows no indication of which project
version is deployed, making it hard to confirm whether an Ansible run landed the
expected release. The ESPHome firmware already exposes its version; the RPi side
should too.

## What Changes

- `git describe` (without `--tags`) is captured on the Ansible control host at
  playbook run time and injected as `DETECTOR_VERSION` into the systemd service
  environment
- The Flask web UI renders the version string in the footer next to the GitHub link

## Capabilities

### New Capabilities

_(none — this extends an existing capability)_

### Modified Capabilities

- `web-status-ui`: footer now displays the deployed project version string (e.g.
  `v2.2.1-3-g543b3e5`)
- `detector-ansible-role`: role captures `git describe` on the control host and
  passes it to the service unit

## Impact

- `roles/detector/files/web.py` — reads `DETECTOR_VERSION` env var, renders in
  footer
- `roles/detector/templates/beam-detector-web.service.j2` — adds
  `Environment=DETECTOR_VERSION=…`
- `playbooks/site.yml` or role defaults — sets `detector_version` fact via `git
  describe`
