<!-- Implementation notes: notes/hardware-wiring.md (resistor math, GPIO pins) | notes/esphome-implementation.md (YAML patterns, NVS gotchas) -->

## 1. ESPHome Firmware

- [x] 1.1 Create `esphome/` directory and `esphome/life-check.yaml` with WiFi, OTA (with password from `secrets.yaml`), web_server (with username/password auth from `secrets.yaml`), and SNTP time components
- [x] 1.2 Add GPIO binary sensor for beam input (substitution variable for pin number) with `delayed_on` and `delayed_off` filters (document chosen values, 50–200 ms range)
- [x] 1.3 Add C++ globals: `today_count` (int, RAM), `daily_counts[14]` array (int, RAM), `test_mode_active` (bool, RAM)
- [x] 1.4 Add beam-break automation: increment `today_count` on rising edge, skip when test mode active
- [x] 1.5 Add midnight rollover automation: shift history array, reset `today_count`
- [x] 1.6 Add 4 `text` entities with `max_restore_data_length: 254` and `restore_value: true`: `webhook_url`, `msg_ok`, `msg_low`, `msg_zero`
- [x] 1.7 Add `number` entity for break threshold (`min_value: 0`, `max_value: 100`, `step: 1`, `restore_value: true`, default 2)
- [x] 1.8 Add `number` entity for webhook retry count (`min_value: 0`, `max_value: 10`, `step: 1`, `restore_value: true`, default 3)
- [x] 1.9 Add `switch` entity for test mode with `on_turn_on` script that triggers 30-min auto-revert via `delay`
- [x] 1.10 Add daily 17:00 webhook automation: 3-tier message selection lambda, `{count}` substitution, HTTP POST with 10s timeout; implement retry loop in a script (up to `webhook_retries` attempts, 30s delay between attempts via `delay` action)
- [x] 1.11 Add `sensor` entity exposing `today_count` for display in web UI
- [x] 1.12 Create `esphome/secrets.yaml.example` with placeholder values for all substitutions (wifi SSID/password, OTA password, web UI username/password, initial webhook URL, message templates, GPIO pin, timezone)

## 2. Wiring Diagram

- [x] 2.1 Rename `wiring.svg` → `wiring_rpi.svg`
- [x] 2.2 Create `wiring_esphome.svg` following the same style as `wiring_rpi.svg`; show: sensor 5V→VBUS, sensor GND→GND, sensor signal→10kΩ→GPIO, 20kΩ from GPIO to GND; add a caption: divider replaces the BSS138 used on the Pi because the ESP32 internal pull-up is NOT enabled — enabling it would cause ~0.94V LOW (ambiguous against 0.8V threshold); note that a BSS138 level shifter also works on the ESP32 if preferred (see `notes/hardware-wiring.md`)
- [x] 2.3 Color-code WROOM DevKit v1 pin labels (header pin numbers + GPIO numbers)
- [x] 2.4 Color-code ESP32-S3 DevKit pin labels (different color from WROOM, same diagram)

## 3. Documentation

- [x] 3.1 Update `README.md`: fix `wiring.svg` reference → `wiring_rpi.svg`
- [x] 3.2 Update `README.md`: add "Hardware options" section before parts list explaining Pi vs ESPHome trade-offs (Pi: familiar hardware, future automations, data vault; ESPHome: simpler, lower power, cheaper); note that a BSS138 level shifter also works for the ESP32 route (divider is simpler but both are valid)
- [x] 3.3 Update `README.md`: add ESP32 parts list (ESP32 dev board, 10kΩ + 20kΩ resistors, same DFRobot sensor)
- [x] 3.4 Update `README.md`: add ESPHome setup section (flash workflow, reference to `esphome/secrets.yaml.example`)
- [x] 3.5 Update `README.md`: add `wiring_esphome.svg` diagram reference alongside Pi wiring diagram
- [x] 3.6 Update `DEVELOPMENT.md`: add ESPHome section covering CLI install (`pip install esphome`), first flash (`esphome run`), OTA update workflow, and `secrets.yaml` setup

## 4. YAML Validation (pre-commit + CI)

- [x] 4.1 Add `esphome` to `requirements-dev.txt` so it is installed in dev venv and CI
- [x] 4.2 Add `esphome-config-validate` local pre-commit hook: copy `esphome/secrets.yaml.example` → `esphome/secrets.yaml` if absent, then run `esphome config esphome/life-check.yaml`; scope to `^esphome/` file changes
- [x] 4.3 Update `DEVELOPMENT.md`: note that `esphome` is now in `requirements-dev.txt` (no separate install needed) and document the new hook and its CI setup
- [x] 4.4 Create `.vscode/settings.json` with `yaml.customTags` for ESPHome-specific YAML tags (`!secret`, `!lambda`, `!extend`, `!remove`, `!include`) to suppress "Unresolved tag" IDE warnings
- [x] 4.5 Create `.ansible-lint` config excluding `esphome/` from ansible-lint's project-wide file discovery (pre-commit `exclude` is insufficient — ansible-lint discovers files independently)
- [x] 4.6 Create `.gitleaks.toml` allowlisting `esphome/secrets.yaml.example` and `openspec/changes/archive/` to suppress false-positive secret detection on placeholder values
