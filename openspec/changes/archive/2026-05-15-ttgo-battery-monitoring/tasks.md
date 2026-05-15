## 1. Firmware

- [x] 1.1 Verify `battery_voltage` ADC sensor (GPIO34, 11dB, multiply 2.0) is in `life-check.yaml`
- [x] 1.2 Verify `battery_level` text sensor (Good/OK/Low/?? thresholds) is in `life-check.yaml`
- [x] 1.3 Verify OLED display lambda includes third line `Batt: <level>`
- [x] 1.4 Bump `project.version` to `2.1.0` in `life-check.yaml`

## 2. Hardware

- [x] 2.1 Solder wire to battery+ through-hole pad on board underside
- [x] 2.2 Wire 100kΩ+100kΩ divider: battery+ → R1 → GPIO34 header, midpoint → R2 → GND header

## 3. Verification

- [x] 3.1 Flash firmware and confirm "Battery Voltage" sensor reads plausible value (3.5–4.2V)
- [x] 3.2 Confirm "Battery Level" shows `Good`, `OK`, or `Low` (not `??`)
- [x] 3.3 Confirm OLED line 3 shows `Batt: X.XXV <level>` when display blocks are enabled

## 4. Documentation

- [x] 4.1 Add warning to `docs/esp32.md` TTGO section: do not reduce
  `beam_debounce` below 250 ms on battery — WiFi TX supply sag causes false
  counts

## 5. Release

- [x] 5.1 Add battery wiring step to `docs/esp32.md` under TTGO section
- [x] 5.2 Add `[2.1.0]` entry to `CHANGELOG.md`
