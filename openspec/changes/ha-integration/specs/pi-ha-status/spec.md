## ADDED Requirements

### Requirement: Pi HA status endpoint with privacy window
`web.py` SHALL expose a `GET /home-assistant` endpoint returning JSON
`{"state": "ok"}` or `{"state": "not_ok"}`.

**Privacy window:** The endpoint SHALL return `{"state": "not_ok"}` whenever the
current local time falls within the privacy window, regardless of `today_count` or
jitter state. The privacy window spans from `effective_start` to `DETECTOR_HA_PRIVACY_WINDOW_END`
(crosses midnight). `effective_start` is `DETECTOR_REPORT_TIME` if that time is ≥
`DETECTOR_HA_PRIVACY_WINDOW_END`; otherwise it is `00:00` (midnight cap). The
morning end time SHALL NOT be a HA-configurable entity — it is set via
`DETECTOR_HA_PRIVACY_WINDOW_END` (default `"08:00"`, parsed as `HH:MM`).

Outside the privacy window, the endpoint returns `ok` or `not_ok` based on whether
`today_count` ≥ `DETECTOR_REPORT_THRESHOLD` (default 1), subject to jitter: when
`today_count` first reaches the threshold, the response continues returning `not_ok`
for `900 + random() * DETECTOR_HA_JITTER_MAX_ADD_S` seconds (default [15, 60) min —
upper bound exclusive), after which it returns `ok`. The midnight reset SHALL NOT be
jittered. The watcher thread continues managing `_ha_ok` during the privacy window;
the endpoint applies the window check live at request time.

`DETECTOR_REPORT_TIME` (default `"17:00"`, parsed as `HH:MM`) is the privacy window
start. It is also used by the systemd timer — both MUST be set to the same value
via the Ansible role.

A background daemon thread SHALL watch `state.json` for threshold crossings and
manage jitter via `threading.Timer`. A `threading.Lock` SHALL guard the shared
`_ha_ok` bool.

#### Scenario: Privacy window active
- **WHEN** current local time is within the privacy window
- **THEN** `/home-assistant` returns `{"state": "not_ok"}` regardless of `_ha_ok`

#### Scenario: Count meets or exceeds threshold outside privacy window
- **WHEN** `today_count` reaches `DETECTOR_REPORT_THRESHOLD` and not in privacy window
- **THEN** `/home-assistant` returns `{"state": "not_ok"}` until the jitter delay expires, then `{"state": "ok"}`

#### Scenario: Count meets or exceeds threshold during privacy window
- **WHEN** `today_count` reaches `DETECTOR_REPORT_THRESHOLD` during the privacy window
- **THEN** jitter timer fires and sets `_ha_ok=True`; endpoint still returns `not_ok` (window active); when window ends, endpoint naturally returns `ok`

#### Scenario: Subsequent crossings during jitter window
- **WHEN** additional beam breaks occur while the jitter timer is pending
- **THEN** no new timer is started; the existing timer fires once

#### Scenario: Count below threshold (including zero)
- **WHEN** `today_count` < `DETECTOR_REPORT_THRESHOLD` (including after midnight reset)
- **THEN** `/home-assistant` returns `{"state": "not_ok"}` (no jitter)

#### Scenario: Pi process restarts with count already above threshold
- **WHEN** `web.py` restarts and `today_count` ≥ `DETECTOR_REPORT_THRESHOLD` on the first watcher poll
- **THEN** a new jitter timer fires; outside the window the endpoint self-corrects after the delay

#### Scenario: Pi offline
- **WHEN** the Pi is unreachable by Home Assistant
- **THEN** the HA REST sensor marks the entity `unavailable` without any application change

---

### Requirement: HA integration documentation
`docs/raspberry-pi.md` SHALL include a section explaining:
- How to configure the HA REST sensor pointing at `/home-assistant`
- The `DETECTOR_REPORT_THRESHOLD`, `DETECTOR_REPORT_TIME`, `DETECTOR_HA_JITTER_MAX_ADD_S`, and `DETECTOR_HA_PRIVACY_WINDOW_END` env vars
- The same privacy model, privacy window rationale, jitter rationale, and sensor-failure assumption documented for the ESPHome route

#### Scenario: User reads docs before configuring HA
- **WHEN** a user follows the Pi HA integration docs
- **THEN** they understand the privacy model and can configure the HA REST sensor without additional research
