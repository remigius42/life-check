## 1. Create CHANGELOG.md

> See `notes/commit-history.md` for commits grouped by theme.

- [x] 1.1 Create `CHANGELOG.md` at repo root with keepachangelog 1.1.0 header and an `[Unreleased]` section
- [x] 1.2 Write `[1.0.0]` entry summarizing current state across both routes:
  - **ESP32/ESPHome route**: beam break counting, 14-day in-RAM history, daily Slack webhook with 3-tier messaging and configurable threshold, runtime-configurable settings via web UI (webhook URL, messages, threshold, retry count), test mode with 30-minute auto-revert, TTGO OLED opt-in, OTA updates
  - **Raspberry Pi/Ansible route**: beam detector daemon, daily Slack webhook report, web status UI, Ansible role for deployment, fail2ban, UFW firewall, SSH hardening, CI via GitHub Actions

## 2. Tag baseline

- [x] 2.1 Tag HEAD as `v1.0.0` with an annotated tag: `git tag -a v1.0.0 -m "Initial stable release"`
- [x] 2.2 Push the tag: `git push origin v1.0.0`

## 2b. Link changelog from README

- [x] 2b.1 Add `## Changelog` section to `README.md` linking to `CHANGELOG.md`

## 3. Verification

- [x] 3.1 Confirm `CHANGELOG.md` exists at repo root and renders correctly
- [x] 3.2 Confirm `git tag` lists `v1.0.0` pointing to HEAD
