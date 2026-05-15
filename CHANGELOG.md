<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-05-15

### Added

#### ESP32 / ESPHome route

- Report time (hour + minute) is now runtime-configurable via the web UI without
  reflashing — exposed as `report_hour` and `report_minute` number entities
- Firmware version visible as a read-only sensor in the web UI (`ESPHOME_PROJECT_VERSION`)
- ESPHome project metadata: `friendly_name`, `comment`, and `project:` block
  (`remigius42.life-check`)
- Web UI assets are now served from device flash (`local: true`) — UI works on
  isolated home networks without CDN access
- Browser-based OTA firmware upload via `ota: platform: web_server`
- `Reset to Defaults (not webhook URL)` button restores all NVS-persisted entities
  (thresholds, retries, report time, message templates) to their compile-time defaults;
  webhook URL is intentionally excluded
- Sorting groups and per-entity `sorting_weight` prepared for web server v3 (opt-in;
  both sets of blocks are commented out — default remains v2 for WROOM stability)

### Changed

#### ESP32 / ESPHome route

- All non-secret user-tunable config (`beam_gpio_pin`, `timezone`, `beam_debounce`,
  timing values, message templates, thresholds) moved from `secrets.yaml` to a
  `substitutions:` block at the top of `life-check.yaml`
- Daily report trigger changed from a static `hours: 17` compile-time trigger to a
  per-minute lambda that compares against the `report_hour`/`report_minute` entities
- Message template defaults updated to consistent wording shared across both routes

### Removed

#### ESP32 / ESPHome route

- **BREAKING**: `timezone`, `beam_gpio_pin`, `msg_ok`, `msg_low`, `msg_zero` removed
  from `secrets.yaml` — remove these keys from your local `secrets.yaml` before
  reflashing (ESPHome will warn on unknown keys; leaving them does not break flashing)

## [1.0.0] - 2026-05-15

### Added

#### ESP32 / ESPHome route

- Beam break counting via ESPHome on ESP32 hardware
- 14-day in-RAM beam-break history
- Daily Slack webhook report with 3-tier messaging and configurable count
  threshold
- Runtime-configurable settings via web UI: webhook URL, messages, threshold,
  retry count
- Test mode with 30-minute auto-revert
- TTGO OLED display (opt-in)
- OTA firmware updates

#### Raspberry Pi / Ansible route

- Beam detector daemon with daily Slack webhook report
- Web status UI with Server-Sent Events (SSE)
- Ansible role for deployment with site and verify playbooks
- fail2ban, UFW firewall, SSH hardening roles
- Locales role

#### Tooling / CI

- GitHub Actions workflow running pre-commit checks
- Python 3.13 dev toolchain

[1.0.0]: https://github.com/remigius42/life-check/releases/tag/v1.0.0
[2.0.0]: https://github.com/remigius42/life-check/compare/v1.0.0...v2.0.0
[unreleased]: https://github.com/remigius42/life-check/compare/v2.0.0...HEAD
