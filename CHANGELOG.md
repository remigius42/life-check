<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.4.0] - 2026-05-17

### Added

#### Both routes

- Home Assistant integration: both routes now expose a privacy-bounded binary
  status sensor (`ok`/`not_ok`) indicating whether today's crossing count has
  reached the configured threshold
- A **privacy window** keeps the sensor at `not_ok` from the daily report time
  (or midnight, whichever is earlier) until a configurable morning end time
  (default 08:00), making nighttime activity structurally invisible in HA history
- Within the daytime window, `not_ok`→`ok` transitions are delayed by a
  randomized jitter of 15–60 minutes to prevent live dashboard inference of exact
  crossing timing; the midnight reset and window-end re-evaluation are published
  immediately (deterministic events)
- Raw crossing count, 14-day history, and webhook URL are not exposed to HA

#### ESP32 / ESPHome route

- `ha_status_sensor` binary sensor exposed via the native API (auto-discovered
  by Home Assistant)
- `today_count_sensor`, `daily_history_sensor`, and `webhook_url` marked
  `internal: true` to prevent raw data exposure
- New `ha_jitter_max_add_s` substitution (default `2700`) controls the jitter
  ceiling; intentionally compile-time only
- New `ha_privacy_window_end_hour` / `ha_privacy_window_end_minute` substitutions
  (default `8` / `0`) set the morning end of the privacy window; intentionally
  compile-time only

#### Raspberry Pi route

- New `GET /home-assistant` endpoint in the web server returning
  `{"state": "ok"}` or `{"state": "not_ok"}`
- New `DETECTOR_HA_JITTER_MAX_ADD_S` env var (default `2700`) controls the
  jitter ceiling
- New `DETECTOR_HA_PRIVACY_WINDOW_END` env var (default `08:00`) sets the
  morning end of the privacy window; set at deploy time via Ansible
- New `DETECTOR_REPORT_TIME` env var (default `17:00`) sets the privacy window
  start; must match the systemd timer schedule (`detector_report_time`)
- `DETECTOR_REPORT_THRESHOLD` (already used by the daily reporter) now also
  controls the HA status threshold

## [2.3.0] - 2026-05-16

### Added

#### Raspberry Pi route

- Project version now shown in the web UI footer (e.g. `v2.3.0` or
  `v2.3.0-3-g543b3e5`), captured at Ansible deploy time via `git describe --tags`
  and injected as `DETECTOR_VERSION` into the systemd service environment

## [2.2.1] - 2026-05-16

### Changed

#### ESP32 / ESPHome route

- Binary sensor renamed from `Beam` to `Beam interruption sensor` — `Beam: OFF`
  was misleading to non-technical users who may interpret "OFF" as an outage
  rather than a clear beam
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
[2.2.1]: https://github.com/remigius42/life-check/compare/v2.2.0...v2.2.1
[2.3.0]: https://github.com/remigius42/life-check/compare/v2.2.1...v2.3.0
[2.4.0]: https://github.com/remigius42/life-check/compare/v2.3.0...v2.4.0
[unreleased]: https://github.com/remigius42/life-check/compare/v2.4.0...HEAD
