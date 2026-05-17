## ADDED Requirements

### Requirement: HA status binary sensor with privacy window
The firmware SHALL expose a `binary_sensor` (platform: template) named "HA Status"
(id: `ha_status_sensor`) that is ON when `today_count` ≥ `break_threshold` AND the
privacy window is not active. The sensor SHALL be the only entity exposed to Home
Assistant that reflects activity state; all raw-data entities SHALL be marked
`internal: true`.

**Privacy window:** The sensor SHALL return OFF whenever the current local time falls
within the privacy window: from `effective_start` until `ha_privacy_window_end_hour:ha_privacy_window_end_minute` (crosses midnight). `effective_start` is `report_hour:report_minute` if that time is ≥ the window end time; otherwise it is `00:00` (midnight cap). The morning end time SHALL be exposed as substitutions (`ha_privacy_window_end_hour`, default `"8"`; `ha_privacy_window_end_minute`, default `"0"`) and SHALL NOT be a runtime-configurable UI entity — changing it requires a firmware recompile.

At window-start (`report_time`) the sensor is forced OFF. At window-end the sensor
re-evaluates and publishes based on `today_count` without jitter (window-end is
deterministic).

**Daytime jitter:** When the count first reaches `break_threshold` outside the privacy
window, the state change SHALL be delayed by `900 + rand() % ha_jitter_max_add_s`
seconds (default: [15, 60) min — upper bound exclusive). If the jitter delay expires
while the privacy window is active, the sensor publishes OFF; the window-end trigger
then re-evaluates. The midnight reset (sensor→OFF) SHALL NOT be jittered.

The jitter range is exposed as a substitution (`ha_jitter_max_add_s`, default 2700)
and SHALL NOT be a runtime-configurable UI entity.

#### Scenario: Count meets or exceeds threshold outside privacy window
- **WHEN** `today_count` reaches `break_threshold` during the daytime window
- **THEN** `ha_status_sensor` publishes ON after a delay of `900 + rand() % ha_jitter_max_add_s` seconds

#### Scenario: Count meets or exceeds threshold inside privacy window
- **WHEN** `today_count` reaches `break_threshold` during the privacy window
- **THEN** jitter timer fires but sensor publishes OFF (privacy window active); at window-end the sensor re-evaluates and publishes ON (no additional jitter)

#### Scenario: Subsequent crossings during jitter window
- **WHEN** additional beam breaks occur while the jitter script is waiting
- **THEN** the script is not restarted; it publishes once when the original delay expires

#### Scenario: Count below threshold (including zero)
- **WHEN** `today_count` < `break_threshold` (including after midnight reset)
- **THEN** `ha_status_sensor` is OFF immediately (no jitter)

#### Scenario: Privacy window active
- **WHEN** local time is within the privacy window (effective_start to morning_end)
- **THEN** `ha_status_sensor` is OFF regardless of `today_count`

#### Scenario: Window-start (report_time)
- **WHEN** local time reaches `report_hour:report_minute`
- **THEN** `ha_status_sensor` is forced OFF (privacy window begins); the daily report is sent concurrently

#### Scenario: Window-end (morning_end)
- **WHEN** local time reaches `ha_privacy_window_end_hour:ha_privacy_window_end_minute`
- **THEN** `ha_status_sensor` publishes `today_count >= break_threshold` without jitter

#### Scenario: Device reboots with count already above threshold, outside privacy window
- **WHEN** the device boots with SNTP synced, `today_count` ≥ `break_threshold`, and not in privacy window
- **THEN** `ha_status_sensor` publishes ON immediately (no jitter)

#### Scenario: Device reboots during privacy window
- **WHEN** the device boots with SNTP synced and current time is in the privacy window
- **THEN** `ha_status_sensor` publishes OFF regardless of `today_count`

#### Scenario: Device reboots before SNTP sync
- **WHEN** the device boots and SNTP time is not yet valid
- **THEN** `ha_status_sensor` publishes based on `today_count` only (privacy window check skipped); self-corrects on next crossing or window-end trigger

#### Scenario: Device reboots after midnight rollover while powered off
- **WHEN** the device boots and `today_count` is 0 (reset by NVS midnight rollover)
- **THEN** `ha_status_sensor` publishes OFF — correctly reflects no crossings today

#### Scenario: Device offline
- **WHEN** the ESP32 is unreachable by Home Assistant
- **THEN** HA marks the entity `unavailable` via the native API without any firmware change

---

### Requirement: Raw-data entities hidden from HA
The firmware SHALL mark the following entities `internal: true` so they are not
exposed via the native API:
- `today_count_sensor` (daily break count)
- `daily_history_sensor` (14-day history string)
- `webhook_url` (contains a secret)

#### Scenario: Raw count not ingested by HA
- **WHEN** the device is connected to Home Assistant via the native API
- **THEN** HA does not receive `today_count_sensor`, `daily_history_sensor`, or `webhook_url` as entities
