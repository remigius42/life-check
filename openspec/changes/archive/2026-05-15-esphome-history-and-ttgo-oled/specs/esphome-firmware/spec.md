## ADDED Requirements

### Requirement: Daily history text sensor
The firmware SHALL expose the 14-day in-RAM history as a read-only `text_sensor`
entity named "Daily History". The sensor SHALL publish the `daily_counts[14]` array
as a comma-separated string (index 0 = yesterday, index 13 = 14 days ago) and
SHALL update every 60 seconds. The sensor SHALL have no `set_action` and SHALL NOT
be `optimistic`, making it read-only in the web UI.

#### Scenario: History visible in web UI
- **WHEN** a user opens the web UI
- **THEN** a "Daily History" entity is displayed showing 14 comma-separated integers

#### Scenario: History reflects midnight rollover
- **WHEN** the local time transitions to midnight and today's count is shifted into the history array
- **THEN** the Daily History sensor reflects the updated values within the next update interval (≤ 60 seconds)

#### Scenario: History resets on reboot
- **WHEN** the device reboots
- **THEN** the Daily History sensor shows all zeros (arrays cannot be NVS-persisted)

### Requirement: OLED display support (TTGO opt-in)
The firmware YAML SHALL include `i2c`, `font`, and `display` blocks for the TTGO
onboard SSD1306 OLED (SCL=GPIO4, SDA=GPIO5), commented out by default. Users with
a TTGO board SHALL uncomment these blocks to enable the display. When enabled, the
display SHALL show current beam state and today's break count. The blocks MUST
remain commented out by default to avoid continuous I2C errors on boards without
an OLED.

#### Scenario: Non-TTGO board — no OLED errors
- **WHEN** the firmware is flashed to a board without an OLED and the OLED blocks are commented out
- **THEN** no I2C errors appear in the log

#### Scenario: TTGO board — OLED enabled
- **WHEN** a user uncomments the `i2c`, `font`, and `display` blocks and flashes to a TTGO board
- **THEN** the OLED displays beam state and today's break count

### Requirement: Default sensor GPIO
The default `beam_gpio_pin` SHALL be GPIO 13. This pin is free on both the
ESP32-WROOM DevKit v1 and the TTGO all-in-one board (which hard-wires GPIO 4 and
5 to the onboard OLED). The default SHALL be supplied via `secrets.yaml.example`.

#### Scenario: Default GPIO avoids OLED conflict on TTGO
- **WHEN** the firmware is flashed to a TTGO board using the default `beam_gpio_pin`
- **THEN** the sensor input does not conflict with the OLED I2C pins (GPIO 4/5)

## MODIFIED Requirements

### Requirement: Built-in web UI
The firmware SHALL enable the ESPHome `web_server` component so all entities (beam binary sensor, daily count sensor, daily history sensor, test mode switch, configuration text entities) are accessible via a browser on the local network without Home Assistant. The `web_server` component SHALL be configured with username/password authentication.

#### Scenario: Web UI accessible on LAN
- **WHEN** the device is connected to WiFi
- **THEN** the web UI is reachable at the device's IP address on port 80

#### Scenario: All entities visible
- **WHEN** a user opens the web UI
- **THEN** beam state, today's count, daily history, test mode switch, and all configurable text fields are displayed
