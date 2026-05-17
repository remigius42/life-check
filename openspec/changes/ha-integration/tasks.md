## 0. Artifacts

- [x] 0.1 Update `design.md`: reframe privacy model; add privacy window decision;
  update jitter framing to "secondary, daytime-only"
- [x] 0.2 Update `specs/esphome-ha-status/spec.md`: add privacy window requirement
  and scenarios; add `ha_privacy_window_end_hour`/`ha_privacy_window_end_minute`
  substitutions; revise on_boot scenarios
- [x] 0.3 Update `specs/pi-ha-status/spec.md`: add privacy window requirement and
  scenarios; add `DETECTOR_REPORT_TIME` and `DETECTOR_HA_PRIVACY_WINDOW_END` env vars

## 1. ESPHome YAML

- [x] 1.1 Read [notes/esphome-impl-hints.md](notes/esphome-impl-hints.md) before
  starting, but keep in mind that the codebase might have changed since the
  document was written.
- [x] 1.2 Add `ha_status_sensor` binary_sensor (ON when `today_count` ≥
  `break_threshold`)
- [x] 1.3 Add jitter script (`mode: single`, delay `900 + rand() %
  ha_jitter_max_add_s` seconds) triggered on threshold crossing; add
  `ha_jitter_max_add_s` substitution (default `"2700"`) with comment that it
  must not become a UI entity
- [x] 1.4 Add `internal: true` to `today_count_sensor`
- [x] 1.5 Add `internal: true` to `daily_history_sensor`
- [x] 1.6 Add `internal: true` to `webhook_url` text entity

- [x] 1.7 Add substitutions `ha_privacy_window_end_hour: "8"` and
  `ha_privacy_window_end_minute: "0"` with comment that they must not become UI
  entities
- [x] 1.8 Add inline privacy window lambda (midnight cap logic using
  `id(sntp_time).now()`, `id(report_hour).state`/`id(report_minute).state`, and
  substitutions); apply in `publish_ha_status` final step (publish false if in
  window) and `on_boot` (with SNTP validity guard)
- [x] 1.9 Add `on_time` at `ha_privacy_window_end_hour:ha_privacy_window_end_minute`
  seconds:0 that publishes `today_count >= break_threshold` without jitter
- [x] 1.10 Extend existing per-minute `on_time` at `report_time`: add
  `publish_state(false)` alongside `send_daily_report` (window-start force-off)

## 2. Pi Flask (`web.py`)

- [x] 2.1 Read [notes/pi-impl-hints.md](notes/pi-impl-hints.md) before starting,
  but keep in mind that the codebase might have changed since the document was
  written.
- [x] 2.2 Add module-level `_ha_ok: bool`, `_ha_lock: threading.Lock`,
  `_ha_timer: threading.Timer | None`
- [x] 2.3 Add `_set_ha_ok(value)` helper (acquires lock, sets `_ha_ok`)
- [x] 2.4 Add background watcher thread: polls `state.json` at 1 s, fires
  `threading.Timer(900 + random() * DETECTOR_HA_JITTER_MAX_ADD_S, ...)` on
  `not_ok→ok` crossing; resets immediately on midnight rollover
- [x] 2.5 Add `GET /home-assistant` endpoint returning `{"state": "ok" | "not_ok"}`
- [x] 2.6 Read `DETECTOR_REPORT_THRESHOLD` (reuse from `reporter.py`, default
  `"1"`) and `DETECTOR_HA_JITTER_MAX_ADD_S` (default `"2700"`) in `web.py`

- [x] 2.7 Add `_HA_REPORT_TIME` and `_HA_PRIVACY_WINDOW_END` module-level constants
  (parse `DETECTOR_REPORT_TIME` default `"17:00"` and `DETECTOR_HA_PRIVACY_WINDOW_END`
  default `"08:00"` as `datetime.time`)
- [x] 2.8 Add `_in_privacy_window() -> bool` with midnight cap logic
- [x] 2.9 Modify `GET /home-assistant` endpoint: return `not_ok` immediately if
  `_in_privacy_window()`; otherwise return based on `_ha_ok`

## 3. Documentation

- [x] 3.1 Add HA integration section to `docs/esp32.md`: how to add device via
  native API, what entity is exposed
- [x] 3.2 Add HA integration section to `docs/raspberry-pi.md`: REST sensor
  config, `DETECTOR_REPORT_THRESHOLD` and `DETECTOR_HA_JITTER_MAX_ADD_S` env
  vars
- [x] 3.3 Document (both routes): why binary sensor instead of message templates
  (`{count}` leak risk)
- [x] 3.4 Document (both routes): jitter — [15, 60) min floor prevents live
  dashboard inference; floor intentionally not a UI/runtime setting; midnight
  reset not jittered
- [x] 3.5 Document (both routes): sensor-failure assumption — device online +
  `not_ok` means no threshold crossings, not broken sensor; device offline = HA
  `unavailable`
- [x] 3.6 Update `README.md` "What it does": add HA integration bullet (both
  routes expose a privacy-bounded binary status sensor); link "Home Assistant"
  to `https://www.home-assistant.io`
- [x] 3.7 Add `home-assistant` to the repository topics on GitHub (manual — done by user)
- [x] 3.13 Add `TestPrivacyWindow` test class in `test_web.py`: test
  `_in_privacy_window()` for in-window, out-of-window, midnight cap, and boundary
  edge cases; extend `TestHomeAssistantEndpoint` with privacy window suppression tests
- [x] 3.8 Add assert to `playbooks/verify.yml`: `/home-assistant` endpoint
  returns 200 and `{"state": "ok"}` or `{"state": "not_ok"}`
- [x] 3.9 Update `docs/esp32.md` HA section: replace jitter-centric privacy model
  text with privacy window explanation; document `ha_privacy_window_end_hour`/
  `ha_privacy_window_end_minute` and why they're substitutions not UI entities
- [x] 3.10 Update `docs/raspberry-pi.md` HA section: add `DETECTOR_REPORT_TIME` and
  `DETECTOR_HA_PRIVACY_WINDOW_END` to env var table; update privacy model text
- [x] 3.11 Add `DETECTOR_REPORT_TIME` and `DETECTOR_HA_PRIVACY_WINDOW_END` to
  `beam-detector-web.service.j2`; fix existing `DETECTOR_REPORT_THRESHOLD` omission
- [x] 3.12 Add `detector_ha_privacy_window_end: "08:00"` to
  `roles/detector/defaults/main.yml` and corresponding row to `roles/detector/README.md`

## 4. Release

- [x] 4.1 Add entry to `CHANGELOG.md` under a new minor version (2.x.0 — check
  current version at implementation time and bump the minor component)
- [x] 4.2 Update `esphome.project.version` in `esphome/life-check.yaml` to match
  new CHANGELOG version
