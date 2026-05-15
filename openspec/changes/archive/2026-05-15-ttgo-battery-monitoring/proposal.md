## Why

The TTGO all-in-one board has no built-in battery monitoring circuit; adding an external voltage divider (100kΩ + 100kΩ) from the battery+ pad to GPIO34 enables voltage measurement with no other hardware changes. This gives the device basic battery health awareness, surfaced on the OLED and web UI.

## What Changes

- New ADC sensor reading GPIO34 at 11dB attenuation, multiplied ×2.0 to correct for the 1:2 voltage divider, reporting battery voltage in volts
- New read-only text sensor mapping voltage to a level label: `Good` (≥4.0V), `OK` (≥3.6V), `Low` (<3.6V), `??` (NaN or <2.5V — floating/disconnected pin guard)
- Third OLED line: `Batt: X.XXV <level>` appended to the existing two-line display when OLED blocks are enabled

## Capabilities

### New Capabilities

- `ttgo-battery-monitoring`: ADC-based battery voltage and level sensors, plus OLED display line, for the TTGO variant

### Modified Capabilities

- `esphome-firmware`: OLED display requirement extended to include battery level as a third display line

## Impact

- `esphome/life-check.yaml`: two new sensors (`battery_voltage`, `battery_level`), updated display lambda
- Wiring: one solder joint to battery+ pad on board underside; two 100kΩ resistors + Dupont wires to GPIO34 and GND headers
- No impact on non-TTGO (WROOM/S3) route — battery sensors are always-on but OLED line is only visible when display blocks are uncommented
