<!-- spellchecker:words espressif -->

## Context

The TTGO all-in-one board (ESP32-WROOM + 18650 holder + SSD1306 OLED) has no built-in battery monitoring. Battery voltage is accessible only at the large +/− through-hole pads on the board underside where the 18650 holder is soldered. GPIO34 is an input-only ADC1 pin — safe with WiFi active — and is otherwise unused on this board.

Current firmware already has the OLED display showing two lines (beam state, today's count). The display lambda is inside a commented-out block that TTGO users uncomment at setup time.

## Goals / Non-Goals

**Goals:**
- Read 18650 voltage via ADC on GPIO34 with a 1:2 resistor divider
- Expose raw voltage (V) and a human-readable level label as web UI sensors
- Show voltage and level label as a third OLED line when OLED is enabled

**Non-Goals:**
- True State-of-Charge (SoC %) estimation — voltage-only is sufficient for this use case
- Deep-sleep power optimization of the divider — device is always-on WiFi, 21µA divider draw is negligible
- GPIO14 ADC_EN switching — that is specific to the TTGO T-Display, not this board

## Decisions

**GPIO34 for ADC input**
Input-only pin → cannot accidentally be driven HIGH; ADC1 channel → unaffected by WiFi. No other use on this board.

**100kΩ + 100kΩ divider (1:2 ratio)**
4.2V fully charged → 2.1V at ADC; within ESP32 11dB linear range (0.15–2.45V). Power draw ≈21µA — irrelevant vs WiFi. Higher values (470kΩ+) would require a bypass capacitor for ADC accuracy; 100kΩ works without one.

**`multiply: 2.0` filter**
Corrects the 1:2 divider in firmware. If actual resistor values deviate, only this scalar needs adjustment.

**Level thresholds: Good ≥4.0V / OK ≥3.6V / Low <3.6V**
Standard 18650 operating range (3.0–4.2V). Low signals meaningful depletion; Good indicates near-full charge.

**Floating-pin guard: v < 2.5V → `??`**
A running ESP32 cannot have a battery below ~2.5V; any reading below that indicates an unconnected GPIO34.

**OLED shows voltage and label**
`Batt: X.XXV Good/OK/Low/??` — fits within 128px width at Roboto font size 14.

## Risks / Trade-offs

[ESP32 ADC nonlinearity] → Averaged single readings; Espressif calibration API not used (acceptable accuracy for a 3-level display). User can verify against a multimeter.

[Solder joint on battery+ pad] → One-time hardware step; documented in wiring section of esp32.md.

[Battery sensors commented out by default] → Same opt-in pattern as OLED blocks; non-TTGO users leave them commented and see no clutter. TTGO users uncomment all four blocks together (battery_voltage, battery_level, i2c/font/display).
