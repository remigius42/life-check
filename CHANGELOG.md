<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### ESP32 / ESPHome route

- Battery monitoring documented as illustrative only — not intended for
  production use, as the boost converter cannot guarantee a stable 5 V supply
  under WiFi TX load at all battery charge levels

## [2.2.0] - 2026-05-15

### Changed

#### ESP32 / ESPHome route

- TTGO-specific config (i2c, font, display, battery sensors) extracted from `life-check.yaml`
  into `esphome/packages/ttgo.yaml`; opt-in changes from "uncomment four inline blocks" to
  "uncomment one `packages:` line" — OLED only by default, battery sensors commented out within
  the package for boards without battery wiring

## [2.1.0] - 2026-05-15

### Added

#### ESP32 / ESPHome route

- Battery voltage ADC sensor on GPIO34 (11 dB attenuation, 1:2 resistor divider via 100 kΩ + 100 kΩ)
  exposed as "Battery Voltage" (V) in the web UI; requires one solder joint to battery+ pad on board underside
- Battery level text sensor ("Battery Level") mapping voltage to `Good` (≥ 4.0 V) / `OK` (≥ 3.6 V) /
  `Low` (< 3.6 V) / `??` (< 2.5 V or floating pin guard)
- OLED third line showing `Batt: X.XXV <level>` when OLED blocks are enabled (TTGO only)
- Both battery sensors include commented-out `web_server` sorting blocks (`group_system`, weights 3 and 4)
  for use when upgrading to web server v3

### Changed

#### ESP32 / ESPHome route

- `beam_debounce` raised from 100 ms to 250 ms — on battery, WiFi TX bursts cause supply sag that
  produces false LOW readings lasting > 100 ms; 250 ms rejects these transients
- OLED display description updated: now shows beam state, today's count, and battery level

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

______________________________________________________________________

[1.0.0]: https://github.com/remigius42/life-check/releases/tag/v1.0.0
[2.0.0]: https://github.com/remigius42/life-check/compare/v1.0.0...v2.0.0
[2.1.0]: https://github.com/remigius42/life-check/compare/v2.0.0...v2.1.0
[2.2.0]: https://github.com/remigius42/life-check/compare/v2.1.0...v2.2.0
[unreleased]: https://github.com/remigius42/life-check/compare/v2.2.0...HEAD
