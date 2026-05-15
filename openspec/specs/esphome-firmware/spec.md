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
The binary sensor SHALL apply `delayed_on` and `delayed_off` filters to suppress transient signal flips caused by sensor noise or mechanical vibration. The implementation SHALL document the chosen delay values; recommended range is 50–200 ms for each filter.

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

### Requirement: Daily Slack webhook report with 3-tier messaging

The firmware SHALL send an HTTP POST (timeout: 10 seconds, `Content-Type: application/json`) to the configured webhook URL once per day at 17:00 local time (as determined by the SNTP time component using the configured timezone). The POST body SHALL be `{"text": "<message>"}`. The message is selected by 3-tier logic based on today's break count and a configured threshold. The count and message SHALL be captured at the time of the 17:00 trigger and reused unchanged across all retry attempts, even if retries span past midnight.

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
- **THEN** the firmware retries up to `webhook_retries` additional times (default 3), with a 30-second delay between attempts; total attempts = 1 initial + `webhook_retries`; each attempt uses the same 10-second timeout

#### Scenario: All retries exhausted
- **WHEN** every attempt (initial + retries) has failed
- **THEN** the firmware logs the failure (HTTP status or error type) and stops; no further retries until the next scheduled report

---

### Requirement: Runtime-configurable webhook URL, threshold, message templates, and retry count
The firmware SHALL expose the webhook URL and three message templates as `text` entities with `max_length: 254` and `restore_value: true`. The break threshold SHALL be a `number` entity with `min_value: 0`, `max_value: 100`, `step: 1`, and `restore_value: true`. The webhook retry count (`webhook_retries`) SHALL be a `number` entity with `min_value: 0`, `max_value: 10`, `step: 1`, `restore_value: true`, and default 3. All six entities are NVS-persisted and editable via the web UI without reflashing. Initial values SHALL be supplied via `secrets.yaml` at first flash.

#### Scenario: User updates webhook URL via web UI
- **WHEN** a user edits the webhook URL field in the web UI and saves
- **THEN** the new URL is used for all subsequent webhook calls and survives reboot

#### Scenario: User updates a message template via web UI
- **WHEN** a user edits a message template in the web UI and saves
- **THEN** the new template is used for all subsequent reports and survives reboot

#### Scenario: Initial values from secrets.yaml
- **WHEN** the device is flashed for the first time
- **THEN** webhook URL and templates are pre-populated from `secrets.yaml` substitutions

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

---

### Requirement: Default sensor GPIO
The default `beam_gpio_pin` SHALL be GPIO 13. This pin is free on both the
ESP32-WROOM DevKit v1 and the TTGO all-in-one board (which hard-wires GPIO 4 and
5 to the onboard OLED). The default SHALL be supplied via `secrets.yaml.example`.

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
The firmware SHALL configure an ESPHome `time` component (platform: `sntp`) with a timezone supplied via `secrets.yaml` substitution. This component is required by the midnight rollover automation and the daily 17:00 webhook trigger. The timezone MUST be set at first flash and survives reboots via the compiled firmware configuration.

#### Scenario: Time synchronized after boot
- **WHEN** the device connects to WiFi after boot
- **THEN** the time component synchronizes with an NTP server and local time becomes available for automations

#### Scenario: Correct local midnight rollover
- **WHEN** the SNTP time component is configured with the user's timezone
- **THEN** the midnight rollover fires at 00:00:00 local time, not UTC

#### Scenario: Correct local 17:00 webhook
- **WHEN** the SNTP time component is configured with the user's timezone
- **THEN** the daily webhook fires at 17:00 local time, not UTC

---

### Requirement: Manual count reset button
The firmware SHALL provide a manual mechanism to reset today's break count to zero. This SHALL be implemented as a `button` component in the ESPHome web interface. When pressed, the `today_count` global variable SHALL be immediately set to 0.

#### Scenario: Count reset triggered
- **WHEN** the "Reset Today's Count" button is pressed in the web UI
- **THEN** today's break count is set to 0

---

### Requirement: Hardware wiring documentation
The project SHALL include a wiring diagram (`wiring_esphome.svg`) covering both the ESP32-WROOM DevKit v1 and the ESP32-S3 DevKit with color-coded pin labels. The diagram SHALL show: sensor 5V power from VBUS, sensor GND to GND, sensor signal through 10 kΩ + 20 kΩ resistor divider to GPIO input.

#### Scenario: User wires WROOM board
- **WHEN** a user follows the wiring diagram using an ESP32-WROOM DevKit v1
- **THEN** the color-coded WROOM labels identify the correct pins unambiguously

#### Scenario: User wires S3 board
- **WHEN** a user follows the wiring diagram using an ESP32-S3 DevKit
- **THEN** the color-coded S3 labels identify the correct pins unambiguously
