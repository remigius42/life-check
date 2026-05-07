## ADDED Requirements

### Requirement: Status page shows today's break count
The web server SHALL expose a status page at `GET /` that displays today's beam-break count read from `/var/lib/beam_detector/counts.json` (configurable via `DETECTOR_COUNTS_PATH` env var). The file has the structure `{"date": "YYYY-MM-DD", "today_count": <integer>, "history": {...}}`. If the file is missing, unreadable, or the stored `"date"` differs from today's local date, the displayed count SHALL be 0.

#### Scenario: Count displayed correctly
- **WHEN** a browser requests `GET /`
- **THEN** the page shows today's break count as read from `counts.json`

#### Scenario: Missing counts.json
- **WHEN** `counts.json` does not exist
- **THEN** the page shows a count of 0 without raising an error

#### Scenario: Stale date in counts.json
- **WHEN** the stored date in `counts.json` differs from today
- **THEN** the page displays 0 as today's count

### Requirement: Status page shows test mode state
The status page SHALL display whether test mode is currently active (sentinel file `/run/beam_detector/test_mode` exists) or inactive.

#### Scenario: Test mode active
- **WHEN** the sentinel file exists and `GET /` is requested
- **THEN** the page indicates test mode is ON

#### Scenario: Test mode inactive
- **WHEN** the sentinel file does not exist and `GET /` is requested
- **THEN** the page indicates test mode is OFF

### Requirement: Test mode toggle via HTML form
The status page SHALL include a form with a single button. When test mode is OFF, the button SHALL submit `POST /test-mode/enable`. When test mode is ON, the button SHALL submit `POST /test-mode/disable`. After the POST, the server SHALL respond with HTTP 303 See Other redirecting to `GET /`.

#### Scenario: Enable test mode
- **WHEN** the user clicks the enable button (test mode is OFF)
- **THEN** `POST /test-mode/enable` is called, the sentinel file is created, and the page reloads showing test mode ON

#### Scenario: Disable test mode
- **WHEN** the user clicks the disable button (test mode is ON)
- **THEN** `POST /test-mode/disable` is called, the sentinel file is deleted, and the page reloads showing test mode OFF

### Requirement: Live beam state display via SSE
The status page SHALL display the current beam state (broken/clear) and today's break count, updated in real time via Server-Sent Events. The page SHALL connect to `GET /stream` (SSE endpoint) using the browser `EventSource` API. The server SHALL push a JSON event whenever beam state or count changes, read from `/run/beam_detector/state.json` (configurable via `DETECTOR_STATE_PATH` env var) on tmpfs. Each pushed event SHALL be a JSON object with exactly the fields written by the daemon:

```json
{"beam_broken": false, "today_count": 7, "test_mode": false}
```

- `beam_broken`: boolean — `true` when the beam is currently broken
- `today_count`: non-negative integer — breaks counted today
- `test_mode`: boolean — `true` when the sentinel file is present

The DOM SHALL update within one daemon poll interval (50 ms) plus one network RTT of the daemon writing the state change. All timing scenarios below use this same bound.

#### Scenario: Beam broken reflected immediately
- **WHEN** the beam is interrupted and the daemon writes `state.json`
- **THEN** the browser updates the beam state indicator to "broken" within ~50 ms (one daemon poll interval + network RTT)

#### Scenario: Beam restored reflected immediately
- **WHEN** the beam is restored and the daemon writes `state.json`
- **THEN** the browser updates the beam state indicator to "clear" within ~50 ms

#### Scenario: Count increments in real time
- **WHEN** a break event occurs in normal mode and the daemon increments the count
- **THEN** the displayed count updates in the browser without a page reload

#### Scenario: SSE reconnects after interruption
- **WHEN** the SSE connection is dropped (e.g. web service restart)
- **THEN** the browser `EventSource` reconnects automatically and resumes receiving events

### Requirement: Web server binds to configurable port
The Flask server SHALL listen on `0.0.0.0:{{ detector_web_port }}` (default 8080). The port SHALL be configurable via the Ansible variable `detector_web_port`.

#### Scenario: Server accessible on configured port
- **WHEN** the service is running and `detector_web_port` is set to 8080
- **THEN** `http://<host>:8080/` returns the status page
