## MODIFIED Requirements

### Requirement: OLED display support (TTGO opt-in)
The firmware SHALL ship a separate package file `esphome/packages/ttgo.yaml` containing the `i2c`, `font`, and `display` blocks for the TTGO all-in-one board, with the `battery_voltage` and `battery_level` blocks commented out by default within the package. `life-check.yaml` SHALL include a commented-out `packages:` entry pointing to this file. Uncommenting the `packages:` entry enables OLED display only; the battery line in the display lambda SHALL also be commented out by default. Users who have wired the battery voltage divider SHALL additionally uncomment the battery sensor blocks and the battery line in the display lambda within `ttgo.yaml`. The package file MUST NOT be active by default to avoid continuous I2C errors on boards without OLED wiring. When fully enabled, the display SHALL show three lines: current beam state, today's break count, and battery voltage with level label.

#### Scenario: Non-TTGO board — no OLED errors
- **WHEN** the firmware is flashed to a board without an OLED and the `packages:` entry is commented out
- **THEN** no I2C errors appear in the log

#### Scenario: TTGO board — OLED only (battery not wired)
- **WHEN** a user uncomments the `packages:` entry in `life-check.yaml` and flashes to a TTGO board without battery wiring
- **THEN** the OLED displays beam state on line 1 and today's break count on line 2; no battery sensors appear in the web UI

#### Scenario: TTGO board — OLED and battery enabled
- **WHEN** a user uncomments the `packages:` entry and additionally uncomments the battery blocks and battery display line within `ttgo.yaml`, then flashes to a TTGO board with battery wiring
- **THEN** the OLED displays beam state on line 1, today's break count on line 2, and `Batt: X.XXV Good/OK/Low` on line 3
