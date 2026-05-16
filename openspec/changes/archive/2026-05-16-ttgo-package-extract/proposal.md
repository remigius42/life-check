## Why

TTGO-specific config (i2c, font, display, battery sensors) lives inline in
`life-check.yaml` as commented-out blocks, making the file harder to read and
the opt-in mechanism fragile. Extracting to a package file gives clear
separation and a single line to uncomment.

## What Changes

- New file `esphome/packages/ttgo.yaml` containing i2c, font, display,
  battery_voltage, and battery_level blocks
- `life-check.yaml` gains a commented-out `packages:` entry pointing to
  `ttgo.yaml`
- The inline commented blocks in `life-check.yaml` are removed
- No logic changes — all values, thresholds, and lambdas remain identical

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `esphome-firmware`: opt-in mechanism changes from "uncomment four inline
  blocks" to "uncomment one `packages:` line"
- `ttgo-battery-monitoring`: spec references the inline block pattern; update to
  reflect package-based opt-in

## Impact

- `esphome/life-check.yaml` — remove inline TTGO blocks, add commented
  `packages:` entry
- `esphome/packages/ttgo.yaml` — new file
- `openspec/specs/esphome-firmware/spec.md` — update OLED opt-in requirement
- `openspec/specs/ttgo-battery-monitoring/spec.md` — update any references to
  inline block pattern
