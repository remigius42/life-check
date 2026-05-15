# Commit history for 1.0.0 summary

Full git log from first commit to HEAD (e4d52c8), grouped by theme for writing the CHANGELOG entry.

## ESP32 / ESPHome route
- `f9dd23d` feat: add ESPHome/ESP32 deployment route
- `76e075e` fix: correct GPIO signal polarity for NPN sensor
- `0e0cbbd` feat: add branding, manual reset, and history
- `3405b70` feat: expose history in web UI; TTGO OLED opt-in
- `e4d52c8` docs: add TTGO OLED hardware photo to ESP32 guide

## Raspberry Pi / Ansible route
- `37bea86` feat: add beam-detector daemon and Ansible role
- `5f2b1c6` feat: add daily beam-break reporter
- `1aba205` feat: add beam-detector web UI with SSE
- `9c1873d` feat: add fail2ban role
- `838f617` feat: add ufw firewall role
- `b95adf5` feat: add ssh role with optional key management
- `8512d4b` feat: add locales role with site & verify playbook
- `870e3d4` fix: add become and fix verify timer assertion
- `07d921b` fix: load vault in both playbooks

## CI / tooling
- `85138bf` ci: add GitHub Actions workflow running pre-commit
- `ea338ea` chore: standardize dev toolchain on Python 3.13
- `a53d592` chore: refactor pre-commit config

## Docs
- `4517af7` docs: add README, DEVELOPMENT, and wiring diagram
- `b8ec0dd` docs: add NOTIFICATIONS.md with webhook setup
- `44ca919` docs: add comprehensive hardware BOM & route links
- `097e688` docs: add hardware examples and 3D housing docs
- `7b4e4f7` docs: restructure docs and split HW routes
