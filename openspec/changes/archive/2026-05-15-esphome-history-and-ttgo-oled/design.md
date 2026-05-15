## Context

Three implementation details were missing from the spec: (1) `daily_counts[14]`
was used internally but never surfaced in the web UI; (2) the OLED `i2c`/`font`/
`display` blocks were unconditionally enabled, causing I2C errors on any board
without an SSD1306; (3) the default `beam_gpio_pin` (GPIO 13) was chosen to avoid
the TTGO's hard-wired OLED pins (GPIO 4/5) but was not documented in the spec.

## Goals / Non-Goals

**Goals:**
- Expose the 14-day history in the ESPHome web UI as a read-only entity
- Make OLED support opt-in so the firmware works cleanly on non-TTGO boards
- Document GPIO 13 as the default sensor pin and its TTGO rationale
- Keep the spec in sync with the already-shipped implementation

**Non-Goals:**
- Persistent history across reboots (arrays cannot be NVS-persisted in ESPHome)
- Structured or dated output for the history string

## Decisions

- **text_sensor over 14 individual sensors**: One entity is cleaner in the UI and
  avoids polluting the entity list. The string requires manual parsing if consumed
  programmatically, but there are no such consumers today.
- **update_interval: 60s**: Matches `today_count_sensor` for consistency; history
  only changes at midnight so any interval is fine.
- **OLED blocks commented out by default**: Safest default — non-TTGO boards get
  no log noise; TTGO users uncomment three blocks. An alternative (separate YAML
  file per board) would fragment maintenance.

## Risks / Trade-offs

- History resets to all-zeros on reboot — documented in spec and README comparison
  table. No mitigation; NVS arrays are not supported by ESPHome.
- OLED opt-in requires a manual step for TTGO users — mitigated by clear
  instructions in `docs/esp32.md` and comments in the YAML.
