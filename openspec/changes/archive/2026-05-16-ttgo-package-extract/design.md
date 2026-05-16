## Context

`life-check.yaml` contains ~20 lines of TTGO-specific config (i2c, font,
display, battery sensors) as commented-out inline blocks. The opt-in instruction
is "uncomment all four blocks together." ESPHome's `packages:` feature merges a
separate YAML file into the main config at build time, enabling a cleaner
single-line opt-in.

## Goals / Non-Goals

**Goals:**

- Move TTGO blocks to `esphome/packages/ttgo.yaml`
- Replace inline blocks with a commented-out `packages:` entry in `life-check.yaml`
- Update specs to match the new opt-in mechanism

**Non-Goals:**

- No logic, threshold, or lambda changes (battery line in display lambda is
  present but commented out; values and lambdas are identical to the current
  inline blocks when enabled)
- No split of OLED and battery into separate packages (display lambda references
  battery sensor IDs — compile error if separated)
- Web server v3 upgrade (separate change)

## Decisions

**One unified `ttgo.yaml` package (not separate oled/battery packages)** The
display lambda references `battery_voltage` and `battery_level` by ID at compile
time. Splitting into two packages would require `!extend` to modify the display
lambda, which has known edge-case issues in ESPHome. A single package avoids
this entirely.

**Battery blocks commented out by default within `ttgo.yaml` (two-level opt-in)**
Uncommenting the `packages:` line enables OLED only — battery sensors are
commented out with YAML `#` inside the package. Without this, a TTGO board
without battery wiring would show garbage ADC readings in both the web UI and
on the display. The battery line in the display lambda is commented with a C++
`//` (not YAML `#`, which is invalid inside a literal block scalar and would be
interpreted as a preprocessor directive by the C++ compiler). A comment in
`ttgo.yaml` explains the two comment styles.

**Commented-out `packages:` line (not a substitution flag)** Keeps the opt-in
pattern consistent with the existing commented-out block convention. A
substitution-based flag (e.g., `ttgo_enabled: "false"`) would require ESPHome
conditional compilation support that doesn't exist cleanly for component
inclusion.

## Risks / Trade-offs

`packages:` merge behavior is additive — ESPHome merges list components by `id`.
All TTGO components have explicit IDs, so merge is deterministic. No risk of
silent duplication.
