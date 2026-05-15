## Purpose

ESPHome firmware for the life-check ESP32 device: beam counting, 14-day in-RAM history, daily Slack webhook with 3-tier messaging, runtime-configurable settings via built-in web UI, and test mode with auto-revert.

## Requirements

### Requirement: Beam break detection

The firmware SHALL monitor a GPIO input connected to the DFRobot 5V IR break-beam sensor via a resistor divider (10 kΩ series + 20 kΩ to GND). The signal SHALL be treated as a `binary_sensor`: LOW = beam broken, HIGH = beam clear (NPN open-collector, active-low logic).

#### Scenario: Beam broken
- **WHEN** the beam is interrupted
- **THEN** the binary sensor state transitions to ON (broken) and the daily break counter increments by 1

#### Scenario: Beam restored
- **WHEN** the beam is restored
- **THEN** the binary sensor state transitions to OFF (clear) with no counter change

#### Scenario: Test mode active during beam break
- **WHEN** the beam is interrupted and test mode is enabled
- **THEN** the binary sensor state transitions to ON but the daily break counter does NOT increment

---

### Requirement: Beam input debounce
The binary sensor SHALL apply `delayed_on` and `delayed_off` filters to suppress transient signal flips caused by sensor noise or mechanical vibration. The implementation SHALL document the chosen delay values; recommended range is 50–200 ms for stable power supplies. When running on battery (18650), WiFi TX bursts (200–300 mA) cause supply voltage sag that can pull the sensor signal line below the ESP32 HIGH threshold, producing false LOW readings lasting multiple hundred milliseconds. The debounce SHALL be set to at least 250 ms when operating on battery to reject these glitches. The `docs/esp32.md` TTGO section SHALL document this constraint with a warning that reducing below 250 ms may cause false counts on battery power.

#### Scenario: Transient glitch shorter than delayed_on window
- **WHEN** the beam signal briefly drops below HIGH for less than the `delayed_on` duration
- **THEN** no state transition occurs and the counter is not incremented

#### Scenario: Sustained beam break longer than delayed_on window
- **WHEN** the beam signal stays LOW for at least the `delayed_on` duration
- **THEN** the binary sensor transitions to ON and the counter increments (unless test mode is active)

#### Scenario: Transient glitch on beam restoration shorter than delayed_off window
- **WHEN** the beam briefly restores to HIGH for less than the `delayed_off` duration while the sensor is ON
- **THEN** no state transition occurs and the counter remains unchanged

#### Scenario: Sustained beam restoration longer than delayed_off window
- **WHEN** the beam stays HIGH for at least the `delayed_off` duration
- **THEN** the binary sensor transitions to OFF (clear)

#### Scenario: WiFi-induced supply sag on battery — false count rejected
- **WHEN** the device runs on battery and a WiFi TX burst causes a supply sag lasting less than 250 ms
- **THEN** the debounce filter rejects the transient and the counter is not incremented

---

### Requirement: Daily break counting with NVS-persisted today count and in-RAM history

The firmware SHALL maintain a daily break count (`today_count`, `restore_value: true`, NVS-persisted) and a 14-day rolling history (`daily_counts[14]`, `restore_value: false`, RAM-only). The history is a FIFO array of length 14: on each day rollover, today's count is written to index 0 and older entries shift up, dropping the oldest (index 13). On first boot all entries are zero. The history resets on reboot; today's count survives reboot via NVS.

#### Scenario: Day rollover
- **WHEN** the local time (as determined by the SNTP time component using the configured timezone) transitions to midnight (00:00:00)
- **THEN** today's count is shifted into the history array, and today's counter resets to 0

#### Scenario: Count visible in web UI
- **WHEN** a user opens the web UI
- **THEN** today's break count is displayed as a sensor entity

#### Scenario: Reboot preserves today's count
- **WHEN** the device reboots
- **THEN** today's count is restored from NVS; the 14-day history array resets to zero (arrays cannot be NVS-persisted)

---

### Requirement: Daily Slack webhook report at configurable time

The firmware SHALL send an HTTP POST (timeout configurable via `substitutions:`, default 10 seconds, `Content-Type: application/json`) to the configured webhook URL once per day when local time matches the `report_hour` and `report_minute` entity values (as determined by the SNTP time component using the configured timezone). The POST body SHALL be `{"text": "<message>"}`. The message is selected by 3-tier logic based on today's break count and a configured threshold. The count and message SHALL be captured at the time of the trigger and reused unchanged across all retry attempts, even if retries span past midnight.

#### Scenario: Count meets or exceeds threshold
- **WHEN** today's break count ≥ threshold at report time
- **THEN** the webhook POST uses the `msg_ok` template

#### Scenario: Count is positive but below threshold
- **WHEN** 0 < today's break count < threshold at report time
- **THEN** the webhook POST uses the `msg_low` template

#### Scenario: Count is zero
- **WHEN** today's break count = 0 at report time
- **THEN** the webhook POST uses the `msg_zero` template

#### Scenario: Message template contains `{count}` placeholder
- **WHEN** the selected template contains the literal string `{count}`
- **THEN** it is replaced with today's numeric break count before sending

#### Scenario: Webhook URL not configured
- **WHEN** the webhook URL text entity is empty at report time
- **THEN** no HTTP request is made and no error is logged

#### Scenario: POST fails — retry up to configured limit
- **WHEN** the HTTP POST returns a non-2xx status code or times out
- **THEN** the firmware retries up to `webhook_retries` additional times (default 3), with a 30-second delay between attempts; total attempts = 1 initial + `webhook_retries`; each attempt uses the configured timeout

#### Scenario: All retries exhausted
- **WHEN** every attempt (initial + retries) has failed
- **THEN** the firmware logs the failure (HTTP status or error type) and stops; no further retries until the next scheduled report

---

### Requirement: Runtime-configurable webhook URL, threshold, message templates, retry count, and report time
The firmware SHALL expose the webhook URL and three message templates as `text` entities with `max_length: 254` and `restore_value: true`. The break threshold SHALL be a `number` entity with `min_value: 0`, `max_value: 100`, `step: 1`, and `restore_value: true`. The webhook retry count (`webhook_retries`) SHALL be a `number` entity with `min_value: 0`, `max_value: 10`, `step: 1`, `restore_value: true`, and default 3. The report hour (`report_hour`) SHALL be a `number` entity with `min_value: 0`, `max_value: 23`, `step: 1`, and `restore_value: true`. The report minute (`report_minute`) SHALL be a `number` entity with `min_value: 0`, `max_value: 59`, `step: 1`, and `restore_value: true`. All eight entities are NVS-persisted and editable via the web UI without reflashing. Initial values (except webhook URL) are defined in the `substitutions:` block of `life-check.yaml`; webhook URL is supplied via `secrets.yaml` at first flash.

#### Scenario: User updates webhook URL via web UI
- **WHEN** a user edits the webhook URL field in the web UI and saves
- **THEN** the new URL is used for all subsequent webhook calls and survives reboot

#### Scenario: User updates a message template via web UI
- **WHEN** a user edits a message template in the web UI and saves
- **THEN** the new template is used for all subsequent reports and survives reboot

#### Scenario: User updates report time via web UI
- **WHEN** a user changes the Report Hour or Report Minute number entity in the web UI
- **THEN** subsequent daily reports fire at the new time and the setting survives reboot

#### Scenario: Initial values from substitutions block
- **WHEN** the device is flashed for the first time
- **THEN** message templates and numeric defaults are pre-populated from the `substitutions:` block in `life-check.yaml`; the webhook URL is pre-populated from `secrets.yaml` (`!secret webhook_url`)

---

### Requirement: Test mode with 30-minute auto-revert

The firmware SHALL expose a `switch` entity for test mode with `restore_mode: ALWAYS_OFF`. When test mode is ON, beam break events SHALL NOT increment the daily counter. Test mode SHALL automatically turn OFF 30 minutes after being enabled. On device boot, test mode MUST be OFF and any pending auto-revert timer MUST be cancelled.

#### Scenario: Test mode enabled
- **WHEN** a user toggles the test mode switch ON via the web UI
- **THEN** subsequent beam breaks do not increment the counter

#### Scenario: Auto-revert after 30 minutes
- **WHEN** test mode has been ON for 30 minutes
- **THEN** test mode automatically turns OFF

#### Scenario: Manual disable before timeout
- **WHEN** a user toggles the test mode switch OFF before the 30-minute timeout
- **THEN** test mode turns OFF immediately and the auto-revert timer is cancelled

---

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

---

### Requirement: OLED display support (TTGO opt-in)
The firmware YAML SHALL include `i2c`, `font`, and `display` blocks for the TTGO
onboard SSD1306 OLED (SCL=GPIO4, SDA=GPIO5), commented out by default. The
`battery_voltage` and `battery_level` sensor blocks SHALL also be commented out by
default. Users with a TTGO board SHALL uncomment all four blocks together to enable
the display and battery monitoring. When enabled, the display SHALL show three lines:
current beam state, today's break count, and battery voltage with level label. The
blocks MUST remain commented out by default to avoid continuous I2C errors and
permanent `??` sensor readings on boards without OLED or battery wiring.

#### Scenario: Non-TTGO board — no OLED errors
- **WHEN** the firmware is flashed to a board without an OLED and the OLED blocks are commented out
- **THEN** no I2C errors appear in the log

#### Scenario: TTGO board — OLED and battery enabled
- **WHEN** a user uncomments the `i2c`, `font`, `display`, `battery_voltage`, and `battery_level` blocks and flashes to a TTGO board with battery wiring
- **THEN** the OLED displays beam state on line 1, today's break count on line 2, and `Batt: X.XXV Good/OK/Low` on line 3

#### Scenario: Battery divider not wired
- **WHEN** the OLED is enabled but no voltage divider is connected to GPIO34
- **THEN** line 3 displays `Batt: <raw_adc_value>V ??` (voltage shows raw floating ADC reading; level shows `??`) and the rest of the display functions normally

---

### Requirement: Default sensor GPIO
The default `beam_gpio_pin` SHALL be GPIO 13. This pin is free on both the
ESP32-WROOM DevKit v1 and the TTGO all-in-one board (which hard-wires GPIO 4 and
5 to the onboard OLED). The default is defined in the `substitutions:` block of `life-check.yaml`.

#### Scenario: Default GPIO avoids OLED conflict on TTGO
- **WHEN** the firmware is flashed to a TTGO board using the default `beam_gpio_pin`
- **THEN** the sensor input does not conflict with the OLED I2C pins (GPIO 4/5)

---

### Requirement: Built-in web UI
The firmware SHALL enable the ESPHome `web_server` component so all entities (beam binary sensor, daily count sensor, daily history sensor, test mode switch, configuration text entities) are accessible via a browser on the local network without Home Assistant. The `web_server` component SHALL be configured with username/password authentication.

#### Scenario: Web UI accessible on LAN
- **WHEN** the device is connected to WiFi
- **THEN** the web UI is reachable at the device's IP address on port 80

#### Scenario: All entities visible
- **WHEN** a user opens the web UI
- **THEN** beam state, today's count, daily history, test mode switch, and all configurable text fields are displayed

---

### Requirement: OTA firmware updates
The firmware SHALL include the ESPHome `ota` component so firmware updates can be pushed wirelessly via `esphome run` without physical USB access after initial flash. The `ota` component SHALL be configured with a password, supplied via `secrets.yaml`.

#### Scenario: OTA update
- **WHEN** a developer runs `esphome run esphome/life-check.yaml` with the device on the network
- **THEN** the firmware is updated over-the-air without requiring USB connection

---

### Requirement: SNTP time component
The firmware SHALL configure an ESPHome `time` component (platform: `sntp`) with a timezone set at compile time in the `substitutions:` block of `life-check.yaml`. This component is required by the midnight rollover automation and the daily webhook trigger. The timezone MUST be set at first flash and survives reboots via the compiled firmware configuration.

#### Scenario: Time synchronized after boot
- **WHEN** the device connects to WiFi after boot
- **THEN** the time component synchronizes with an NTP server and local time becomes available for automations

#### Scenario: Correct local midnight rollover
- **WHEN** the SNTP time component is configured with the user's timezone
- **THEN** the midnight rollover fires at 00:00:00 local time, not UTC

#### Scenario: Correct local report time
- **WHEN** the SNTP time component is configured with the user's timezone
- **THEN** the daily webhook fires at the configured local time (default 17:00), not UTC

---

### Requirement: Manual count reset button
The firmware SHALL provide a manual mechanism to reset today's break count to zero. This SHALL be implemented as a `button` component in the ESPHome web interface. When pressed, the `today_count` global variable SHALL be immediately set to 0.

#### Scenario: Count reset triggered
- **WHEN** the "Reset Today's Count" button is pressed in the web UI
- **THEN** today's break count is set to 0

---

### Requirement: ESPHome project identity and firmware version
The `esphome:` block SHALL include: `friendly_name: "Life Check"` (used in web UI and mDNS); `comment:` set to the project tagline from README.md; and a `project:` sub-block with `name: "remigius42.life-check"` and a `version:` field set to the current semver release (e.g. `"1.0.0"`). The firmware SHALL expose the project version as a read-only `text_sensor` (platform: template, `lambda: 'return {ESPHOME_PROJECT_VERSION};'`, `update_interval: 1h`) visible in the web UI.

The `project.version` field SHALL be updated to match the git release tag immediately before tagging (i.e. tag `v1.2.3` → `version: "1.2.3"`). The CHANGELOG.md entry and the `project.version` field SHALL always refer to the same version number at release time.

The `web_server` component SHALL use `local: true` (assets served from device flash; UI works on isolated home networks) and expose firmware upload via `ota: platform: web_server`. The web server version SHALL be controlled by a `web_server_version` substitution (default `"2"` for WROOM stability; set to `"3"` on ESP32-S3 or when group/graph/browser-OTA UI features are needed). Version 3 on original ESP32-WROOM causes significant UI latency and HTTP server task contention with sensor logic.

When `web_server_version` is `"3"`, the web UI SHALL define six `sorting_groups`: **Status** (Beam, Today's Break Count, Daily History), **Controls** (Test Mode, Reset Today's Count), **Report** (Break Threshold, Report Hour, Report Minute), **Messages** (Message: Zero, Message: Low, Message: OK), **Webhook** (Webhook URL, Webhook Retries), **System** (Reset to Defaults, Firmware Version). Every entity SHALL declare a `sorting_group_id` and sequential `sorting_weight` (1, 2, 3…) within its group. These blocks SHALL be commented out when running version 2 (they hard-error under v2).

The firmware SHALL include a `Reset to Defaults (not webhook URL)` button that restores all NVS-persisted entities (thresholds, retries, report time, message templates) to their substitution-block defaults. The webhook URL SHALL be explicitly excluded from this reset.

#### Scenario: Device web UI shows firmware version
- **WHEN** a user opens the device web UI
- **THEN** a read-only "Firmware Version" sensor displays the current semver version string

#### Scenario: Release tag created
- **WHEN** a new git release tag (e.g. `v1.2.3`) is created
- **THEN** `esphome.project.version` in `life-check.yaml` is already set to `"1.2.3"` and the commit being tagged includes that update

---

### Requirement: Configuration separation — substitutions vs secrets
All user-tunable, non-sensitive configuration values SHALL be defined in the `substitutions:` block at the top of `life-check.yaml`. Sensitive values (credentials, authentication tokens, URLs containing embedded secrets) SHALL be stored in `secrets.yaml` and referenced via `!secret`. No sensitive value SHALL appear in `substitutions:`, and no non-sensitive value SHALL appear in `secrets.yaml`. This rule applies to all current and future configuration added to the firmware.

This rule governs the **compile-time config source** (where the value is declared in firmware configuration files), not runtime storage. A sensitive value whose initial value is supplied via `secrets.yaml`/`!secret` MAY also be exposed as an NVS-persisted, web-UI-editable entity; the `!secret` reference covers the initial value at flash time, and runtime NVS storage is a separate concern.

A value is considered sensitive if its exposure would grant unauthorized access to a system or service (e.g., WiFi password, OTA password, web UI credentials, webhook URLs containing auth tokens). A value is non-sensitive if it is a behavioral parameter or hardware setting with no security implication (e.g., GPIO pin, timezone, timing values, message templates, numeric thresholds).

#### Scenario: New sensitive config added
- **WHEN** a new configuration value that grants access to a system or service is added to the firmware
- **THEN** it SHALL be stored in `secrets.yaml` and referenced via `!secret`, not placed in `substitutions:`

#### Scenario: New non-sensitive config added
- **WHEN** a new behavioral or hardware configuration value with no security implication is added to the firmware
- **THEN** it SHALL be defined in the `substitutions:` block of `life-check.yaml`, not in `secrets.yaml`

---

### Requirement: Hardware wiring documentation
The project SHALL include a wiring diagram (`wiring_esphome.svg`) covering both the ESP32-WROOM DevKit v1 and the ESP32-S3 DevKit with color-coded pin labels. The diagram SHALL show: sensor 5V power from VBUS, sensor GND to GND, sensor signal through 10 kΩ + 20 kΩ resistor divider to GPIO input.

#### Scenario: User wires WROOM board
- **WHEN** a user follows the wiring diagram using an ESP32-WROOM DevKit v1
- **THEN** the color-coded WROOM labels identify the correct pins unambiguously

#### Scenario: User wires S3 board
- **WHEN** a user follows the wiring diagram using an ESP32-S3 DevKit
- **THEN** the color-coded S3 labels identify the correct pins unambiguously
