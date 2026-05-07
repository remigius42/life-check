<!-- spellchecker: ignore pinout -->

# Hardware Wiring Notes

## Resistor divider: why 10 kΩ + 20 kΩ

The DFRobot sensor has an internal pull-up to 5V on its NPN open-collector output.

Voltage at GPIO when beam is **clear** (NPN OFF, output pulled to 5V by sensor):

```
V_GPIO = 5V × 20kΩ / (10kΩ + 20kΩ) = 3.33V
```

ESP32 absolute maximum input voltage: **3.6V** → 3.33V is within spec (270 mV margin).
At USB 5.25V (high end of tolerance): 5.25V × 0.667 = 3.50V — still under 3.6V.

Voltage when beam is **broken** (NPN ON, output pulled to GND):

```
V_GPIO ≈ 0V  (NPN sinks current through both resistors)
```

ESP32 HIGH threshold: ~2.48V (0.75 × 3.3V). 3.33V is well above it. ✓
ESP32 LOW threshold: ~0.825V (0.25 × 3.3V). ~0V is well below it. ✓

**Do NOT enable the ESP32 internal pull-up** (`pullup: false` on the GPIO). The divider itself provides the pull-up via the sensor's internal resistor. Enabling the internal pull-up (~45 kΩ to 3.3V) in parallel with the 20 kΩ to GND would raise the LOW voltage and risk a missed detection.

## Why the Pi needs a BSS138 instead

The Pi daemon explicitly enables the internal GPIO pull-up (~50 kΩ to 3.3V) as a fallback. With a divider in place, when the NPN activates (beam broken), the LOW voltage at GPIO becomes:

```
V = 3.3V × 20kΩ / (50kΩ + 20kΩ) ≈ 0.94V
```

Pi GPIO LOW threshold is ~0.8V. **0.94V is above the threshold** → unreliable LOW detection. The BSS138 active level shifter properly isolates the two voltage domains and avoids this problem.

**Why CodeRabbit's suggested swap (22 kΩ upper / 10 kΩ lower) is wrong:**

```
V_GPIO = 5V × 10kΩ / (22kΩ + 10kΩ) = 1.56V
```

1.56V < ESP32 HIGH threshold of 2.48V → the HIGH state would never be detected. Beam would always appear broken. Do not use this configuration.

## GPIO pin selection

The YAML uses a substitution variable (`${beam_gpio_pin}`) so users set it in `secrets.yaml`. Suggested defaults to document in `secrets.yaml.example`:

| Board | Suggested GPIO | Header pin | Notes |
|---|---|---|---|
| ESP32-WROOM DevKit v1 | GPIO 4 | Pin 26 | Free general-purpose I/O |
| ESP32-S3 DevKit | GPIO 4 | Pin varies by board variant | Check your specific board's pinout |

Any free GPIO works; avoid strapping pins (0, 2, 5, 12, 15 on WROOM) and USB-connected pins on S3.

## Sensor power

Power the sensor from the board's **5V / VBUS** pin (sourced from USB). The DFRobot sensor draws ~30 mA — well within USB 500 mA budget. Do **not** use the ESP32's 3.3V rail for the sensor.
