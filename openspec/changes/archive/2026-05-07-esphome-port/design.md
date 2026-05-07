<!-- spellchecker: ignore configparser thevenin -->

## Context

The Pi deployment requires a full OS image, Ansible provisioning, three systemd services, and a Python 3.13 runtime — significant overhead for a single GPIO sensor. The ESP32 running ESPHome replaces all of that with a single compiled firmware image, OTA updates, and a built-in web server, while keeping feature parity with the Pi's daemon + reporter + web UI.

Key constraints established during research:
- DFRobot 5V IR sensor must stay on 5V (3.3V alternatives cap at ~25 cm range)
- ESP32 GPIO is NOT 5V tolerant — signal requires level shifting
- ESPHome and MicroPython are mutually exclusive firmware environments
- ESPHome NVS string storage caps at 254 chars with `max_restore_data_length: 254` (Slack webhook ~88 chars — fits comfortably)
- ESPHome 2026.2.0 has an NVS exhaustion bug with many persisted values — keep NVS use minimal

## Goals / Non-Goals

**Goals:**
- Feature-complete ESPHome firmware: beam counting, 14-day in-RAM history, daily Slack webhook (3-tier), runtime-configurable webhook URL and message templates, test mode with 30-min auto-revert, built-in web UI
- Wiring documentation for both ESP32-WROOM DevKit v1 and ESP32-S3 DevKit (color-coded)
- Updated README and DEVELOPMENT docs presenting both routes as equals

**Non-Goals:**
- Replacing or deprecating the Pi route
- Persistent history across reboots (RAM-only is acceptable given rare reboots)
- Custom web UI beyond ESPHome's built-in web server

## Decisions

### 1. NVS-persisted today_count; RAM-only history array
ESPHome's `restore_value` works for scalar globals via NVS. `today_count` (int scalar) uses `restore_value: true` so the daily count survives reboots. Persisting the 14-element history array requires either 14 separate NVS keys (fragile, high exhaustion risk) or a custom binary blob — neither is worth the complexity. `int daily_counts[14]` stays RAM-only and resets to zero on reboot; history rebuilds within 14 days.

**Alternative considered**: Store counts as 14 separate NVS globals. Rejected — 14 extra NVS entries increases exhaustion risk and complicates the YAML.

> C++ array global syntax, FIFO shift lambda, NVS exhaustion gotcha: [`notes/esphome-implementation.md`](notes/esphome-implementation.md)

### 2. Runtime config via `text` entities (NVS-persisted)
Webhook URL and 3 message templates are exposed as ESPHome `text` entities with `max_restore_data_length: 254`. They appear as editable fields in the built-in web UI and survive reboots. Initial values are set via `secrets.yaml` at first flash.

**Alternative considered**: Compile-time `substitutions` only (no runtime editing). Rejected — webhook URL must be changeable without reflashing.

### 3. Resistor divider for 5V→3.3V level shifting
A 10 kΩ + 20 kΩ voltage divider on the sensor signal line drops 5V to ~3.33V (within the ESP32's ≤3.6V input limit). The divider also serves as a pull-up for the NPN open-collector output. Simpler and cheaper than a BSS138 level shifter board.

**Alternative considered**: BSS138 active level shifter (same as Pi BOM). Rejected — adds cost and complexity when a passive divider suffices for a slow digital signal.

> Full voltage math, Pi pull-up interaction, GPIO pin suggestions: [`notes/hardware-wiring.md`](notes/hardware-wiring.md)

### 4. Sensor powered from VBUS/5V pin
ESP32 dev boards expose a 5V pin sourced from USB VBUS. The DFRobot sensor draws ~30 mA — well within USB power budget. No external 5V supply needed.

### 5. ESPHome over MicroPython
MicroPython would allow closer parity with the Pi Python codebase (configparser, custom web framework). However it requires building a web UI from scratch, has no built-in OTA, and the existing Python code is not directly reusable due to RPi.GPIO dependencies. ESPHome provides the web UI, OTA, and NVS persistence for free; custom logic fits in lambdas.

### 6. Target both WROOM DevKit v1 and ESP32-S3 DevKit
Both boards are widely available. GPIO pin numbers differ (e.g., WROOM uses GPIO 4 for a typical input; S3 uses a different numbering on the header). The wiring diagram uses color-coded labels for each board rather than two separate diagrams.

## Risks / Trade-offs

- **NVS exhaustion (ESPHome 2026.2.0 bug)** → Mitigated by limiting NVS-persisted values to 7 entries (4 `text` + 2 `number` + `today_count` scalar). All other globals are RAM-only.
- **History loss on reboot** → Acceptable per design decision 1. Document in README.
- **ESPHome YAML API drift** → Pin the ESPHome version in `esphome/life-check.yaml` and note minimum version in README.
- **Board-specific pin numbers** → Wiring diagram must be clearly labeled; firmware YAML should use a substitution variable for the GPIO pin so users can adapt easily.
- **NPN open-collector + resistor divider pull-up strength** → 10 kΩ + 20 kΩ gives a Thevenin equivalent of ~6.7 kΩ pull-up to 3.33V. Adequate for cable runs typical in a home doorway installation.
