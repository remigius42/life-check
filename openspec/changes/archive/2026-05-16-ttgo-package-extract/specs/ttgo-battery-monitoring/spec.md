## MODIFIED Requirements

### Requirement: Battery voltage ADC sensor
The firmware SHALL include an ADC sensor on GPIO34 with 11dB attenuation and a `multiply: 2.0` filter to correct for the 1:2 resistor voltage divider. The sensor SHALL be named "Battery Voltage", report in volts with 2 decimal places, and update every 60 seconds. The sensor SHALL be exposed in the web UI. A commented-out `web_server` sorting block SHALL be included (`group_system`, `sorting_weight: 3`) for use when web server v3 is enabled. This sensor SHALL reside in `esphome/packages/ttgo.yaml`, commented out by default within the package, and is active only when explicitly uncommented by the user.

#### Scenario: Normal battery connected
- **WHEN** a 100kΩ+100kΩ voltage divider is wired from the battery+ pad to GPIO34
- **THEN** the "Battery Voltage" sensor reads the actual battery voltage (divider midpoint × 2.0)

#### Scenario: GPIO34 unconnected (floating)
- **WHEN** no voltage divider is wired and GPIO34 is floating
- **THEN** the "Battery Voltage" sensor may read any value; the "Battery Level" sensor SHALL display `??`

---

### Requirement: Battery level text sensor
The firmware SHALL include a read-only `text_sensor` named "Battery Level" that maps the battery voltage to a human-readable label. The mapping SHALL be: `Good` if voltage ≥ 4.0V; `OK` if voltage ≥ 3.6V and < 4.0V; `Low` if voltage ≥ 2.5V and < 3.6V; `??` if voltage is NaN or < 2.5V (floating pin guard). The sensor SHALL update every 60 seconds and be exposed in the web UI. A commented-out `web_server` sorting block SHALL be included (`group_system`, `sorting_weight: 4`) for use when web server v3 is enabled. This sensor SHALL reside in `esphome/packages/ttgo.yaml`, commented out by default within the package, and is active only when explicitly uncommented by the user.

#### Scenario: Battery fully charged
- **WHEN** battery voltage is ≥ 4.0V
- **THEN** Battery Level reads `Good`

#### Scenario: Battery at mid charge
- **WHEN** battery voltage is ≥ 3.6V and < 4.0V
- **THEN** Battery Level reads `OK`

#### Scenario: Battery low
- **WHEN** battery voltage is ≥ 2.5V and < 3.6V
- **THEN** Battery Level reads `Low`

#### Scenario: GPIO floating or sensor uninitialized
- **WHEN** battery voltage is NaN or < 2.5V
- **THEN** Battery Level reads `??`
