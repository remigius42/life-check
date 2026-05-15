## Why

Three gaps between the implemented ESPHome firmware and its spec: the 14-day
history was stored but never surfaced in the web UI; the OLED/I2C blocks were
always enabled, causing continuous I2C errors on non-TTGO boards; and the
default sensor GPIO wasn't documented as GPIO 13 (chosen to avoid the TTGO's
hard-wired OLED pins on GPIO 4/5).

## What Changes

- Add a read-only `text_sensor` entity ("Daily History") that exposes the 14-day
  history as a comma-separated string (index 0 = yesterday, 13 = 14 days ago),
  updated every 60 seconds
- OLED `i2c`, `font`, and `display` blocks are commented out by default; users
  with a TTGO board uncomment them to enable the onboard display
- Default sensor GPIO is GPIO 13, documented as TTGO-safe (avoids OLED pins 4/5)
- Update the "All entities visible" scenario and Built-in web UI requirement to
  include the Daily History sensor

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `esphome-firmware`: add Daily History text_sensor requirement; add OLED opt-in
  requirement; update "All entities visible" scenario; document GPIO 13 default

## Impact

- `esphome/life-check.yaml` — already updated (text_sensor added, OLED commented out)
- `esphome/secrets.yaml.example` — `beam_gpio_pin` default is GPIO 13
- `docs/esp32.md` — TTGO callout updated to reference uncommenting OLED blocks
- `openspec/specs/esphome-firmware/spec.md` — needs new requirements and updated scenario
