## Context

Both routes expose sensor data that could be privacy-sensitive if raw. The
ESPHome native API exposes all non-internal entities to Home Assistant
automatically; currently this includes `today_count_sensor` (raw daily count),
`daily_history_sensor` (14-day history), and `webhook_url` (contains a secret).
The Pi Flask app has no HA integration today. In both cases, exposing raw counts
with HA's built-in time-series logging would produce a presence/activity
timeline. The `msg_*` text entities store user-configurable templates that may
contain `{count}` — exposing them directly would leak raw readings whenever the
template is customized.

## Goals / Non-Goals

**Goals:**

- Both routes expose a binary `ok`/`not_ok` status within a daytime window only;
  outside that window (privacy window) the sensor always returns `not_ok`
- Privacy window: from `report_time` (capped at midnight if misconfigured) until a
  configurable morning end time (default `08:00`); the morning end time is a
  compile-time/deploy-time constant, not a HA-configurable entity
- Within the daytime window, threshold-crossing transitions are delayed by [15, 60)
  min jitter to prevent live inference of crossing timing
- ESPHome: raw-data entities marked `internal: true`
- Pi: `/home-assistant` endpoint with background watcher thread, `threading.Timer`
  jitter, and live privacy window check
- Docs cover the privacy model, privacy window rationale, jitter rationale, and
  sensor-failure assumption for both routes

**Non-Goals:**

- Changing the webhook or message template behavior on either route
- Modifying HA configuration (ESPHome: auto-discovery via native API; Pi: user
  configures a REST sensor)

## Decisions

**Binary `ok`/`not_ok` rather than tristate or message templates**
The `msg_*` templates may contain `{count}`; substitution happens only at
webhook-send time so the raw template would leak counts. A tristate
(`ok`/`low`/`none`) was considered but rejected: `low→ok` transitions still
reveal intra-day crossing timing, and the `none` state (zero crossings, possible
sensor fault) is redundant — device offline is natively modelled as `unavailable`
by HA, and distinguishing "zero crossings" from "below threshold" adds no value
to a report-time automation. Binary is the minimum necessary signal.

**Sensor hardware failure is not a monitored failure mode**
A device that is online and reporting `not_ok` is assumed to mean the person has
not crossed the threshold, not that the sensor is broken. If sensor fault
monitoring is added in future it should be a separate diagnostic entity.
This assumption is documented explicitly in the docs for both routes.

**Privacy window: sensor forced `not_ok` from `effective_start` to `morning_end`**
Jitter is a timing smear — it delays a signal but does not destroy it. Over a
long enough history, habitual patterns (e.g. regularly getting up at night) remain
statistically visible regardless of jitter range. The privacy window eliminates
the signal structurally: during the window the sensor always returns `not_ok`,
regardless of the beam count, so HA history accumulates no nighttime activity at all.

The window spans `effective_start` → `morning_end` (crosses midnight):
- `effective_start`: `report_time` if `report_time ≥ morning_end`; otherwise `00:00`
  (midnight cap — prevents a misconfigured or malicious `report_time` in the morning
  hours from leaving midnight–report_time uncovered)
- `morning_end`: default `08:00` — intentionally NOT a HA-configurable entity. If it
  were, a HA-level actor could eliminate the window. It is a substitution
  (`ha_privacy_window_end_hour`/`ha_privacy_window_end_minute`) on ESPHome and an env
  var (`DETECTOR_HA_PRIVACY_WINDOW_END`) on Pi; both require device-level access to
  change.

At window-start (`report_time`) the sensor is forced to `not_ok`. At window-end
(`morning_end`) the sensor re-evaluates without jitter — the window-end transition is
deterministic and reveals no behavioral timing information. The midnight count reset
is NOT jittered for the same reason.

**Jitter: `15min + rand() % 45min` on daytime threshold-crossing transitions only**
Within the daytime window (`morning_end` to `report_time`), when the count first
reaches the threshold the HA status update is delayed by `900 + rand() % 2700`
seconds ([15, 60) min — upper bound exclusive). This prevents a live observer from
inferring "this just happened" — the event is always at least 15 min in the past.

Jitter config is intentionally not a runtime UI setting: reducing it without
understanding the privacy model can silently erode protection. ESPHome exposes it
as a substitution (`ha_jitter_max_add_s`); Pi exposes it as an env var
(`DETECTOR_HA_JITTER_MAX_ADD_S`), both defaulting to 2700.

**ESPHome: privacy window via inline lambda; jitter via `script` with `mode: single`**
The privacy window check is an inline C++ lambda defined in two places via a YAML
anchor: `on_boot` (where the anchor is declared) and `publish_ha_status` final step
(where it is referenced). It reads `id(sntp_time).now()`,
`id(report_hour).state`/`id(report_minute).state` (runtime number entities), and
`ha_privacy_window_end_hour`/`ha_privacy_window_end_minute` substitutions
(compile-time). The midnight cap is applied inline.

The window-end `on_time` uses a simplified inline expression
(`today_count >= break_threshold`) rather than the anchored lambda — no privacy window
check is needed there because the window-end trigger fires exactly when the window
closes, so the sensor is by definition outside the window.

The `publish_ha_status` script delays `900 + rand() % ha_jitter_max_add_s` seconds,
then publishes `false` if in the privacy window (threshold may have been crossed
during window), otherwise publishes based on count. `mode: single` ensures subsequent
crossings during the jitter window don't restart the timer.

A dedicated `on_time` at `ha_privacy_window_end_hour:ha_privacy_window_end_minute`
re-evaluates and publishes without jitter (window-end is deterministic). The
existing per-minute `on_time` handler that already checks for `report_time` is
extended to also publish `false` at window-start.

**Pi: privacy window via live endpoint check; jitter via background watcher thread + `threading.Timer`**
The privacy window check is applied directly in the `/home-assistant` endpoint at
request time: if `_in_privacy_window()` returns True, `not_ok` is returned
immediately without consulting `_ha_ok`. This means the watcher thread continues
tracking logical state (including firing jitter timers) during the window — when
the window ends, the endpoint naturally reflects `_ha_ok` without any watcher
change.

`_in_privacy_window()` reads `DETECTOR_REPORT_TIME` (default `"17:00"`) and
`DETECTOR_HA_PRIVACY_WINDOW_END` (default `"08:00"`) parsed as `datetime.time`
objects at module load. Midnight cap: if `report_time < window_end` (misconfigured),
`effective_start` is set to `time(0, 0)`.

The background watcher thread polls `state.json` at 1 s intervals, tracks the last
threshold-crossed state, and on a `not_ok→ok` transition fires a `threading.Timer`.
A `threading.Lock` guards the shared `_ha_ok` bool. `DETECTOR_REPORT_THRESHOLD` is
reused from `reporter.py`. `DETECTOR_HA_JITTER_MAX_ADD_S` is a new env var (default
2700).

**ESPHome: `internal: true` rather than removing entities**
Entities are useful in the ESPHome web UI and for debugging; `internal: true`
hides them only from HA while keeping them locally accessible.

## Risks / Trade-offs

- [ESPHome privacy window lambda duplicated across two call sites] → Duplication
  is ~8 lines; a YAML anchor (`&ha_status_publish_lambda`) shared between `on_boot`
  and `publish_ha_status` keeps it DRY within ESPHome's constraints. Acceptable given
  the sites are cohesive (all HA status related).
- [ESPHome SNTP not synced at boot] → `on_boot` priority -100 fires after WiFi/SNTP
  initialization in practice. Guard with `id(sntp_time).now().is_valid()`: if not
  valid (no sync yet), publish based on count only (falls back to pre-window behavior
  briefly; self-corrects on next crossing or window-end trigger).
- [HA entity name/ID changes if ESPHome sensor is renamed] → Use a stable `id:`;
  keep the name stable across releases.
- [ESPHome jitter script publishing during privacy window] → Final lambda in
  `publish_ha_status` checks window and publishes false; window-end `on_time`
  re-evaluates when window lifts.
- [Pi watcher thread adds background load] → 1 s polling of a local file is
  negligible.

## Migration Plan

No existing HA installations expected. ESPHome users will lose
`today_count_sensor` and `daily_history_sensor` on firmware update — acceptable
given this is a new integration being introduced for the first time.
