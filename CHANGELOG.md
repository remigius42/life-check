# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
[unreleased]: https://github.com/remigius42/life-check/compare/v1.0.0...HEAD
