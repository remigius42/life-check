## Why

The Raspberry Pi is a capable but over-engineered platform for a single GPIO sensor — it requires OS setup, Ansible provisioning, systemd services, and a full Python stack. An ESP32 running ESPHome delivers the same core capability (beam detection, daily Slack webhook, live web UI) with far less setup, lower power draw, and cheaper hardware, making the project more accessible as a standalone embedded device.

## What Changes

- Add an ESPHome firmware configuration (`esphome/life-check.yaml`) as a complete alternative deployment path
- Add `esphome/secrets.yaml.example` for first-flash configuration
- Add ESP32 wiring diagram (`wiring_esphome.svg`) covering both DevKit v1 and S3 boards with color-coded pins
- Update `README.md` to present both the Pi route and the ESPHome route as permanent parallel options, with honest trade-off framing
- Update `DEVELOPMENT.md` with ESPHome CLI setup, flash workflow, and OTA update instructions

## Capabilities

### New Capabilities

- `esphome-firmware`: ESP32 firmware delivering beam detection, daily break counting (RAM-only, 14-day history), daily Slack webhook with 3-tier messaging, runtime-configurable webhook URL and message templates (NVS-persisted), test-mode switch with 30-min auto-revert, and built-in web UI — all via ESPHome YAML + C++ lambdas

### Modified Capabilities

_(none — existing Pi-based specs are unchanged)_

## Trade-offs

- **History resets on reboot**: daily break counts are kept in RAM only. A power cycle or firmware update resets today's count and all 14-day history to zero. The Pi route persists history to disk across reboots; users migrating from the Pi should be aware that the ESPHome route does not provide equivalent durability.

## Impact

- `README.md`: new hardware-options section, ESP32 parts list, second wiring diagram
- `DEVELOPMENT.md`: new ESPHome section (CLI install, `esphome run`, OTA)
- New files: `esphome/life-check.yaml`, `esphome/secrets.yaml.example`, `wiring_esphome.svg`
- No changes to any existing Ansible roles, Python code, or Pi-facing specs
