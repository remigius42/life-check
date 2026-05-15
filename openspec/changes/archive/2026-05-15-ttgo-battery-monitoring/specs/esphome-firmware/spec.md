## MODIFIED Requirements

### Requirement: Beam input debounce
The binary sensor SHALL apply `delayed_on` and `delayed_off` filters to suppress transient signal flips caused by sensor noise or mechanical vibration. The implementation SHALL document the chosen delay values; recommended range is 50–200 ms for stable power supplies. When running on battery (18650), WiFi TX bursts (200–300 mA) cause supply voltage sag that can pull the sensor signal line below the ESP32 HIGH threshold, producing false LOW readings lasting multiple hundred milliseconds. The debounce SHALL be set to at least 250 ms when operating on battery to reject these glitches. The `docs/esp32.md` TTGO section SHALL document this constraint with a warning that reducing below 250 ms may cause false counts on battery power.

#### Scenario: Transient glitch shorter than delayed_on window
- **WHEN** the beam signal briefly drops below HIGH for less than the `delayed_on` duration
- **THEN** no state transition occurs and the counter is not incremented

#### Scenario: Sustained beam break longer than delayed_on window
- **WHEN** the beam signal stays LOW for at least the `delayed_on` duration
- **THEN** the binary sensor transitions to ON and the counter increments (unless test mode is active)

#### Scenario: Transient glitch on beam restoration shorter than delayed_off window
- **WHEN** the beam briefly restores to HIGH for less than the `delayed_off` duration while the sensor is ON
- **THEN** no state transition occurs and the counter remains unchanged

#### Scenario: Sustained beam restoration longer than delayed_off window
- **WHEN** the beam stays HIGH for at least the `delayed_off` duration
- **THEN** the binary sensor transitions to OFF (clear)

#### Scenario: WiFi-induced supply sag on battery — false count rejected
- **WHEN** the device runs on battery and a WiFi TX burst causes a supply sag lasting less than 250 ms
- **THEN** the debounce filter rejects the transient and the counter is not incremented

---

### Requirement: OLED display support (TTGO opt-in)
The firmware YAML SHALL include `i2c`, `font`, and `display` blocks for the TTGO
onboard SSD1306 OLED (SCL=GPIO4, SDA=GPIO5), commented out by default. The
`battery_voltage` and `battery_level` sensor blocks SHALL also be commented out by
default. Users with a TTGO board SHALL uncomment all four blocks together to enable
the display and battery monitoring. When enabled, the display SHALL show three lines:
current beam state, today's break count, and battery voltage with level label. The
blocks MUST remain commented out by default to avoid continuous I2C errors and
permanent `??` sensor readings on boards without OLED or battery wiring.

#### Scenario: Non-TTGO board — no OLED errors
- **WHEN** the firmware is flashed to a board without an OLED and the OLED blocks are commented out
- **THEN** no I2C errors appear in the log

#### Scenario: TTGO board — OLED and battery enabled
- **WHEN** a user uncomments the `i2c`, `font`, `display`, `battery_voltage`, and `battery_level` blocks and flashes to a TTGO board with battery wiring
- **THEN** the OLED displays beam state on line 1, today's break count on line 2, and `Batt: X.XXV Good/OK/Low` on line 3

#### Scenario: Battery divider not wired
- **WHEN** the OLED is enabled but no voltage divider is connected to GPIO34
- **THEN** line 3 displays `Batt: <raw_adc_value>V ??` (voltage shows raw floating ADC reading; level shows `??`) and the rest of the display functions normally
