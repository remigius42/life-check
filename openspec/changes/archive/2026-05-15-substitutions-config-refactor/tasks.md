## 1. life-check.yaml — substitutions block

> See `notes/impl-reference.md` for the full value mapping, per-minute trigger lambda, new entity YAML, and docs/esp32.md line numbers.

- [x] 1.1 Add `substitutions:` block at top of `life-check.yaml` with:
  `beam_gpio_pin` (GPIO13), `beam_debounce` (100ms), `timezone`,
  `notification_hour` (17), `notification_minute` (0), `test_mode_timeout`
  (30min), `http_timeout` (10s), `break_threshold` (2), `webhook_retries` (3),
  `msg_ok`, `msg_low`, `msg_zero` (aligned with
  `roles/detector/defaults/main.yml`)
- [x] 1.2 Replace `!secret beam_gpio_pin` with `$beam_gpio_pin` in the `binary_sensor` pin block
- [x] 1.3 Replace `!secret timezone` with `$timezone` in the `time` component
- [x] 1.4 Replace `delayed_on: 100ms` and `delayed_off: 100ms` with `$beam_debounce`
- [x] 1.5 Replace `timeout: 10s` in `http_request` with `$http_timeout`
- [x] 1.6 Replace `delay: 30min` in `test_mode_revert_timer` with `$test_mode_timeout`
- [x] 1.7 Replace `initial_value: 2` for `break_threshold` with `$break_threshold`
- [x] 1.8 Replace `initial_value: 3` for `webhook_retries` with `$webhook_retries`
- [x] 1.9 Replace `initial_value: !secret msg_ok/low/zero` with `$msg_ok`, `$msg_low`, `$msg_zero`

## 2. life-check.yaml — report time entities and trigger

- [x] 2.1 Add `report_hour` number entity (min 0, max 23, step 1, restore_value true, initial_value `$notification_hour`)
- [x] 2.2 Add `report_minute` number entity (min 0, max 59, step 1, restore_value true, initial_value `$notification_minute`)
- [x] 2.3 Replace static `on_time: hours: 17` trigger with a per-minute trigger
  (`minutes: /1`) that checks `id(sntp_time).now().hour ==
  (int)id(report_hour).state && id(sntp_time).now().minute ==
  (int)id(report_minute).state`

## 3. life-check.yaml — ESPHome project block, version sensor, and web UI

- [x] 3.1 Add `project:` block under `esphome:` with `name: "remigius42.life-check"` and `version: "1.0.0"`
- [x] 3.2 Add `friendly_name: "Life Check"` to `esphome:` block
- [x] 3.3 Add `comment:` to `esphome:` block with the project tagline from README.md
- [x] 3.4 Add `Firmware Version` template text_sensor that returns `ESPHOME_PROJECT_VERSION` (update_interval: 1h, icon: mdi:tag)
- [x] 3.5 Add `web_server_version` substitution (default `"2"`); set `web_server: version: $web_server_version` and
  `local: true`; add upgrade comment noting v3 requires uncommenting sorting_groups and per-entity web_server blocks
- [x] 3.6 Add `ota: platform: web_server` to enable firmware upload via browser
- [x] 3.7 Add `sorting_groups:` (Status, Controls, Report, Messages, Webhook, System; weights 1–6) and
  per-entity `sorting_group_id`/`sorting_weight` blocks — both commented out (v3 only; uncomment alongside version bump)
- [x] 3.8 Add `Reset to Defaults (not webhook URL)` button (group: System) that restores all NVS-persisted entities
  except `webhook_url` to substitution defaults
- [x] 3.9 Reorder `text:` entities to match sorting group/weight order (msg_zero, msg_low, msg_ok, webhook_url)

## 4. secrets.yaml.example

- [x] 4.1 Remove keys: `timezone`, `beam_gpio_pin`, `msg_ok`, `msg_low`, `msg_zero`
- [x] 4.2 Add a comment pointing to the `substitutions:` block in
  `life-check.yaml` for non-secret config

## 5. docs/esp32.md, hardware/BOM.md, README.md

- [x] 5.1 Update step 2 to explain the two-file split: credentials in
  `secrets.yaml`, non-secret config (GPIO pin, timezone) in `substitutions:`
  block of `life-check.yaml`
- [x] 5.2 Note that only WiFi credentials, OTA password, web UI credentials, and
  webhook URL must be set before flashing; everything else (threshold, retries,
  report time, messages) has sensible defaults and can be configured via the web
  UI after first flash
- [x] 5.3 Note that `timezone` and `beam_gpio_pin` are compile-time only
  (explain why: opaque POSIX string format and hardware-wired pin respectively)
- [x] 5.4 Add `{count}` token documentation to step 5 "Configure webhook and thresholds"
- [x] 5.5 Add privacy note explaining why default message templates omit `{count}` (in `docs/esp32.md` and `docs/notifications.md`)
- [x] 5.6 Add ESP8266 not-supported warning to `hardware/BOM.md` (ESP32 row) and `README.md` (note below routes table)

## 6. Spec — version sync requirement

- [x] 6.1 Add delta spec requirement in `specs/esphome-firmware/spec.md`:
  `esphome.project.version` must match the git tag before tagging a release

## 7. Spec alignment

- [x] 7.1 Verify `openspec/specs/esphome-firmware/spec.md` is updated with the
  configuration separation rule (archived from delta spec)

## 8. Release

- [x] 8.1 Update `project.version` in `life-check.yaml` to `"2.0.0"`
- [x] 8.2 Add `[2.0.0]` entry to `CHANGELOG.md` (promote [Unreleased], add version link)

## 9. Verification

- [x] 9.1 Run `esphome config esphome/life-check.yaml` — no errors
- [x] 9.2 Grep `life-check.yaml` for `!secret` — only `wifi_ssid`,
  `wifi_password`, `ota_password`, `web_username`, `web_password`, `webhook_url`
  remain
- [x] 9.3 Confirm `secrets.yaml.example` no longer contains removed keys
