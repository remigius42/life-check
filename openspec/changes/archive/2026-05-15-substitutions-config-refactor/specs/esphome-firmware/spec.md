## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Runtime-configurable webhook URL, threshold, message templates, retry count, and report time
The firmware SHALL expose the webhook URL and three message templates as `text` entities with `max_length: 254` and `restore_value: true`. The break threshold SHALL be a `number` entity with `min_value: 0`, `max_value: 100`, `step: 1`, and `restore_value: true`. The webhook retry count (`webhook_retries`) SHALL be a `number` entity with `min_value: 0`, `max_value: 10`, `step: 1`, `restore_value: true`, and default 3. The report hour (`report_hour`) SHALL be a `number` entity with `min_value: 0`, `max_value: 23`, `step: 1`, and `restore_value: true`. The report minute (`report_minute`) SHALL be a `number` entity with `min_value: 0`, `max_value: 59`, `step: 1`, and `restore_value: true`. All eight entities are NVS-persisted and editable via the web UI without reflashing.

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
- **THEN** webhook URL and templates are pre-populated from the `substitutions:` block in `life-check.yaml`

---

### Requirement: Daily Slack webhook report at configurable time
The daily break count is reset at 00:00 local time by the midnight rollover automation (see "Daily break counting with NVS-persisted today count and in-RAM history" in the main `esphome-firmware` spec). The firmware SHALL send an HTTP POST (timeout configurable via `substitutions:`, default 10 seconds, `Content-Type: application/json`) to the configured webhook URL once per day when local time matches the `report_hour` and `report_minute` entity values. The POST body SHALL be `{"text": "<message>"}`. The message is selected by 3-tier logic based on today's break count and a configured threshold. The count and message SHALL be captured at the time of the trigger and reused unchanged across all retry attempts, even if retries span past midnight.

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

### Requirement: Default sensor GPIO
The default `beam_gpio_pin` SHALL be GPIO 13. This pin is free on both the ESP32-WROOM DevKit v1 and the TTGO all-in-one board (which hard-wires GPIO 4 and 5 to the onboard OLED).

#### Scenario: Default GPIO avoids OLED conflict on TTGO
- **WHEN** the firmware is flashed to a TTGO board using the default `beam_gpio_pin`
- **THEN** the sensor input does not conflict with the OLED I2C pins (GPIO 4/5)

---

### Requirement: SNTP time component
The firmware SHALL configure an ESPHome `time` component (platform: `sntp`) with a timezone set at compile time. This component is required by the midnight rollover automation and the daily webhook trigger. The timezone MUST be set at first flash and survives reboots via the compiled firmware configuration.

#### Scenario: Time synchronized after boot
- **WHEN** the device connects to WiFi after boot
- **THEN** the time component synchronizes with an NTP server and local time becomes available for automations

#### Scenario: Correct local midnight rollover
- **WHEN** the SNTP time component is configured with the user's timezone
- **THEN** the midnight rollover fires at 00:00:00 local time, not UTC

#### Scenario: Correct local report time
- **WHEN** the SNTP time component is configured with the user's timezone
- **THEN** the daily webhook fires at the configured local time (default 17:00), not UTC
