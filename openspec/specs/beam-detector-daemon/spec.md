## Purpose
Poll a GPIO-connected break-beam sensor, count daily break events, persist history, support test mode via sentinel file, and expose live state to future services via tmpfs IPC.

## Requirements

### Requirement: GPIO polling interval
The daemon SHALL poll the GPIO pin every 50 ms (configurable via `detector_poll_interval_ms`, default 50). This interval governs the maximum latency for all state transitions (beam detection, test-mode activation, signal response) and the `state.json` write frequency.

#### Scenario: State file written at poll rate
- **WHEN** one poll interval elapses
- **THEN** `state.json` is rewritten with current values regardless of whether state changed

### Requirement: Falling-edge beam-break detection
The daemon SHALL detect beam-break events by monitoring GPIO pin 17 (BCM, configurable via `detector_gpio_pin`) for HIGH→LOW transitions. The sensor is NPN open-collector with a pull-up: HIGH = beam intact (transistor off), LOW = beam broken (transistor on). The pin SHALL be configured with a pull-up resistor (`GPIO.PUD_UP`). On daemon startup, the initial `previous_state` SHALL be set to the first sampled GPIO value; no break event SHALL be emitted for this initial sample. Only subsequent HIGH→LOW transitions (edge detection beginning from the second poll onward) constitute break events. Sustained LOW SHALL NOT generate additional events.

#### Scenario: Single break event
- **WHEN** the GPIO pin transitions from HIGH to LOW
- **THEN** exactly one break event is registered

#### Scenario: Sustained beam broken
- **WHEN** the GPIO pin is LOW for multiple consecutive polls
- **THEN** only one break event is registered (the initial transition)

#### Scenario: Beam restored then broken again
- **WHEN** the GPIO pin goes LOW, returns to HIGH, then goes LOW again
- **THEN** two break events are registered in total

#### Scenario: Daemon starts with beam already broken
- **WHEN** the daemon initializes and the GPIO pin is already LOW
- **THEN** no break event is registered until the pin returns to HIGH and then goes LOW again

### Requirement: Daily break counter
The daemon SHALL maintain a per-day break counter that increments on each break event (when not in test mode). The counter SHALL reset to zero when the calendar date changes in the system's configured local timezone (detected by comparing the stored date string `YYYY-MM-DD` against today's date via `datetime.date.today()`, which uses the system local timezone, on each poll tick). Both the stored date and "today" are always interpreted in that same timezone. Date-string comparison is inherently DST-safe: spring-forward and fall-back do not affect the rollover because no wall-clock arithmetic is involved.

#### Scenario: Counter increments on break
- **WHEN** a break event occurs in normal mode
- **THEN** today's counter increases by one

#### Scenario: Counter resets at midnight
- **WHEN** the local date changes (midnight crossed)
- **THEN** the counter resets to zero for the new day and the previous day's total is archived

#### Scenario: System clock adjusted backward
- **WHEN** NTP or a manual adjustment moves the clock backward such that `datetime.date.today()` returns the same or an earlier date than `_current_date`
- **THEN** no rollover is triggered; the daemon continues counting under `_current_date` without archiving or resetting; no log entry is required (small NTP slew is expected and harmless)

#### Scenario: System clock jumps forward multiple days
- **WHEN** the clock jumps forward by more than one day (e.g., manual adjustment or VM resume)
- **THEN** the current day's count is archived under `_current_date` and a fresh counter starts for the new date; intermediate dates are NOT backfilled; a single rollover occurs regardless of the gap size

### Requirement: Persistent history with configurable retention
The daemon SHALL persist daily totals to `/var/lib/beam_detector/counts.json` (configurable). History SHALL be retained for a configurable number of days (default 14). Entries older than the retention window SHALL be purged on the next save.

#### Scenario: History survives restart
- **WHEN** the daemon is restarted and the stored date in counts.json matches today
- **THEN** today's count and all history within the retention window are restored from disk

#### Scenario: Stale date on load
- **WHEN** the stored date in counts.json is earlier than today on daemon startup
- **THEN** the stored today_count (including zero) is archived into history under its stored date (not discarded), today's counter starts at zero, and the previous day's total becomes part of the retained history

#### Scenario: Future date on load
- **WHEN** the stored date in counts.json is later than today on daemon startup (e.g., clock was set back)
- **THEN** the stored today_count is discarded (not archived into history), a warning is logged, and today's counter starts at zero

#### Scenario: Old entries purged
- **WHEN** a save occurs and some history entries are older than the retention window
- **THEN** those entries are removed from the JSON file

### Requirement: Test mode via sentinel file
The daemon SHALL support a test mode in which break events are detected but NOT counted. Test mode is active when the file `/run/beam_detector/test_mode` (configurable) exists. Test mode SHALL activate within one poll interval of the sentinel file appearing.

#### Scenario: Break not counted in test mode
- **WHEN** the sentinel file exists and a break event occurs
- **THEN** the counter is not incremented

#### Scenario: Test mode deactivates when sentinel removed
- **WHEN** the sentinel file is deleted externally
- **THEN** subsequent break events are counted normally within one poll interval

---

### Requirement: Count reset via sentinel file
The daemon SHALL support resetting today's break count to zero. A reset is triggered when a regular file exists at `/run/beam_detector/reset_count` (configurable via `detector_reset_count_sentinel`).

Upon detection of the sentinel, the daemon SHALL:
1. Reset `today_count` to 0.
2. Log the reset event with a timestamp.
3. Attempt to delete the sentinel file.

The daemon SHALL NOT perform another reset until the sentinel file has been successfully deleted. If deletion fails, the daemon SHALL log an error and retry the deletion on every subsequent polling iteration until it succeeds. The daemon SHALL ignore any beam-break events that occur in the same polling iteration that performs the reset.

#### Scenario: Count reset triggered and cleaned up
- **WHEN** a regular file at the reset sentinel path is detected during a polling iteration
- **THEN** today's count is set to 0, a log entry is created, and the sentinel file is deleted within one poll interval

---

### Requirement: Test mode auto-revert after grace period
The daemon SHALL automatically remove the sentinel file and revert to normal mode after a configurable grace period (default 1800 seconds / 30 minutes, `detector_test_mode_grace_period_s`) has elapsed since test mode was entered. Test mode is strictly tied to sentinel-file existence: the daemon only resumes counting after it has successfully deleted the sentinel file.

#### Scenario: Grace period expires — removal succeeds
- **WHEN** the sentinel file has existed for longer than the configured grace period
- **AND** the daemon successfully removes the sentinel file
- **THEN** test mode is deactivated and subsequent break events are counted normally

#### Scenario: Grace period expires — removal fails
- **WHEN** the sentinel file has existed for longer than the configured grace period
- **AND** removal fails with an OS error other than file-not-found
- **THEN** the error is logged, test mode remains active, and the daemon retries removal on the next tick

#### Scenario: Grace period resets on service restart
- **WHEN** the daemon restarts while the sentinel file is present
- **THEN** the in-memory grace-period timer starts fresh from the moment the daemon detects the sentinel (mtime is not consulted)

#### Scenario: Sentinel deleted and recreated
- **WHEN** the sentinel file is deleted (test mode deactivates) and then recreated at any point
- **THEN** the in-memory timer is unconditionally reset to zero at the moment the daemon detects the recreated sentinel file, and the full grace period runs again from that point regardless of how much time had elapsed before deletion

### Requirement: Testability without hardware
The daemon's GPIO interaction SHALL be abstracted behind a `GpioPort` protocol so that a fake implementation can be injected in tests. The `RPi.GPIO` library SHALL be imported lazily (inside `RpiGpioPort.__init__`) so the module can be imported on any machine.

#### Scenario: Unit tests run without GPIO hardware
- **WHEN** unit tests inject a `FakeGpioPort` instance
- **THEN** all detector logic executes correctly without `RPi.GPIO` being installed

### Requirement: Live state written to tmpfs on every tick
The daemon SHALL write `/run/beam_detector/state.json` (configurable) on every poll tick with the following structure:
```json
{"beam_broken": false, "today_count": 7, "test_mode": false}
```
This file is used by the web server (Change 3) as a live IPC channel. It SHALL be written to tmpfs (`/run/`) to avoid SD card wear from the 50 ms write frequency. The file SHALL be written atomically (write to a temp file, then rename).

#### Scenario: State file reflects current beam state
- **WHEN** the beam is broken and the daemon has completed a tick
- **THEN** `state.json` contains `"beam_broken": true`

#### Scenario: State file reflects test mode
- **WHEN** test mode is active
- **THEN** `state.json` contains `"test_mode": true`

### Requirement: Clean shutdown
The daemon SHALL handle SIGTERM and SIGINT by finishing the current poll cycle, flushing the in-memory counter to `counts.json`, calling `gpio.cleanup()`, and exiting. The flush SHALL complete before `gpio.cleanup()` is called so no break events accumulated since the last periodic save are lost. The service SHALL stop within one poll interval of receiving the signal.

#### Scenario: SIGTERM causes clean exit
- **WHEN** SIGTERM is sent to the daemon
- **THEN** the counter is saved to counts.json, GPIO cleanup is called, and the process exits within one poll interval

### Requirement: Error handling
The daemon SHALL handle I/O and hardware errors deterministically:

- **counts.json corrupt on load**: rename the bad file to `counts.json.bak`, log an error, and start fresh with zero counter and empty history.
- **counts.json write failure**: log the error and retain in-memory state; retry on the next save opportunity. The daemon SHALL NOT exit on transient write failures.
- **state.json write failure**: log the error and continue; retry on the next tick. The daemon SHALL NOT exit on transient state.json write or rename failures. Consumers must tolerate possible staleness.
- **Atomic writes** (state.json, counts.json) SHALL fsync the temp file before rename to guarantee durability on power loss.
- **GPIO init failure**: retry up to `detector_gpio_init_retries` times (default 3) with 1 s delay, then exit with non-zero status and a logged error.
- **Directory creation**: the daemon SHALL NOT create `/var/lib/beam_detector/` or `/run/beam_detector/`. These directories are the responsibility of the Ansible role (via `file:` tasks) and systemd (via `StateDirectory=` and `RuntimeDirectory=`). If a required directory is missing, the first write attempt will fail and be handled by the write-failure rules above.

#### Scenario: Corrupt counts.json on startup

- **WHEN** counts.json contains invalid JSON
- **THEN** the file is renamed to counts.json.bak, an error is logged, and the daemon starts with zero state

#### Scenario: GPIO init fails repeatedly

- **WHEN** GPIO initialization fails on every retry attempt
- **THEN** the daemon exits with non-zero status after logging a clear error
