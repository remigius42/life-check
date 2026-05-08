<!-- cspell:ignore wroom -->

# ESP32 Route

## Parts list

| Part                                                                                 | Notes                                                                 |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| ESP32 dev board (WROOM DevKit v1 or S3 DevKit)                                       | Any ESP32 with a free GPIO works                                      |
| [DFRobot 5V IR Photoelectric Switch, 4 m](https://www.dfrobot.com/product-2644.html) | Same sensor as the Pi route                                           |
| 10 kΩ resistor                                                                       | Series resistor on sensor signal line                                 |
| 20 kΩ resistor                                                                       | Pull-down from GPIO to GND; together with 10 kΩ forms voltage divider |

A passive resistor divider (10 kΩ + 20 kΩ) handles level shifting from the sensor's
5 V signal to the ESP32's 3.3 V GPIO — no separate level shifter board is needed. A BSS138 active
level shifter also works if you prefer it.

## Wiring

![ESP32 wiring diagram](../wiring_esphome.svg)

Wire sensor power from the board's **VBUS (5 V)** pin. Connect the receiver signal through the
resistor divider (10 kΩ series + 20 kΩ to GND) to **GPIO 4** — WROOM DevKit v1 physical pin 26,
S3-DevKitC-1 J1 pin 4. Do **not** enable the internal pull-up on the GPIO
(the divider acts as the pull-up; enabling the internal pull-up raises the LOW voltage to ~0.94 V,
above the detection threshold).

## Prerequisites

- Python 3.13+ with a virtual environment
- A webhook URL for daily reports — see [notifications.md](notifications.md) for
  Slack setup and alternatives

## Setup

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/remigius42/life-check
cd life-check
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2. Create your secrets file

```bash
cp esphome/secrets.yaml.example esphome/secrets.yaml
# Edit esphome/secrets.yaml with your WiFi, webhook URL, and timezone
```

`secrets.yaml` is gitignored — never commit it.

### 3. First flash (USB)

Connect the ESP32 via USB, then:

```bash
esphome run esphome/life-check.yaml
```

ESPHome will compile the firmware, flash it over USB, and open the serial log.
After first flash the device is on your WiFi and subsequent updates can be done
over-the-air.

### 4. OTA updates

Once the device is on the network:

```bash
esphome run esphome/life-check.yaml
```

ESPHome discovers the device via mDNS and uploads wirelessly — no USB required.

### 5. Configure webhook and thresholds

Open the device's web UI at its IP address on port 80. All runtime settings
(webhook URL, message templates, threshold, retry count) are editable there and
survive reboots.
