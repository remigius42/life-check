## Why

When multiple devices are deployed (e.g. across rooms in a care setting), Home
Assistant can aggregate their statuses into a single dashboard and drive
automations. Both routes (ESPHome and Pi) can expose a status endpoint, but raw
sensor data must not be exposed due to privacy concerns — a timestamped count
history is a presence/activity log.

## What Changes

- Both routes expose a binary `ok`/`not_ok` status to Home Assistant, with a
  [15, 60] min jitter on threshold-crossing transitions to prevent live
  dashboard inference of crossing timing
- ESPHome: new `binary_sensor` via the native API; raw-data entities marked
  `internal: true`
- Pi: new `GET /home-assistant` JSON endpoint in `web.py`; jitter implemented
  via background watcher thread and `threading.Timer`; reuses
  `DETECTOR_REPORT_THRESHOLD` already present in `reporter.py`
- Docs updated for both routes covering the privacy model, jitter rationale,
  and the sensor-failure assumption

## Capabilities

### New Capabilities

- `esphome-ha-status`: ESPHome exposes a binary status sensor (`ok`/`not_ok`) to
  Home Assistant via the native API, with raw-data entities marked internal and
  jitter on threshold-crossing transitions
- `pi-ha-status`: Pi Flask app exposes a `/home-assistant` JSON endpoint with
  the same binary status and jitter model

### Modified Capabilities

## Impact

- `esphome/life-check.yaml` — new `binary_sensor`, jitter script,
  `ha_jitter_max_add_s` substitution, `internal: true` on three existing entities
- `roles/detector/files/web.py` — new `/home-assistant` endpoint, background
  watcher thread, `threading.Timer` jitter, `DETECTOR_REPORT_THRESHOLD` and
  `DETECTOR_HA_JITTER_MAX_ADD_S` env vars
- `docs/esp32.md` and `docs/raspberry-pi.md` — new HA integration sections
