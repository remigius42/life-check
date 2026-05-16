## 1. Firmware

- [x] 1.1 Create `esphome/packages/ttgo.yaml` with i2c, font, and display
  blocks active; battery_voltage and battery_level blocks commented out with
  YAML `#`; battery line in display lambda commented out with C++ `//`; include
  a comment explaining the two comment styles
- [x] 1.2 Add a comment at the top of `esphome/packages/ttgo.yaml` linking to the
  TTGO section in `docs/esp32.md` for wiring and opt-in instructions
- [x] 1.3 Remove the inline TTGO commented blocks from `life-check.yaml`
- [x] 1.4 Add a commented-out `packages:` entry in `life-check.yaml` pointing to
  `packages/ttgo.yaml`
- [x] 1.5 Bump `project.version` to `2.2.0` in `life-check.yaml`

## 2. Docs

- [x] 2.1 Update the "TTGO all-in-one board" section in `docs/esp32.md` — replace
  the instruction to uncomment four inline blocks with: uncomment the `packages:`
  entry in `life-check.yaml` to enable OLED; separately uncomment the battery
  sensor blocks and battery display line in `ttgo.yaml` to enable battery
  monitoring
- [x] 2.2 Add a note in the general wiring section of `docs/esp32.md` directing
  any battery-powered ESP32 user to `esphome/packages/ttgo.yaml` for the voltage
  divider wiring pattern, ADC sensor config, and the debounce warning

## 3. Specs

- [x] 3.1 Verify `openspec/specs/esphome-firmware/spec.md` OLED requirement
  matches new opt-in wording after archive
- [x] 3.2 Verify `openspec/specs/ttgo-battery-monitoring/spec.md` battery sensor
  requirements reflect package location after archive

## 4. Release

- [x] 4.1 Add `[2.2.0]` entry to `CHANGELOG.md`
