<!-- spellchecker: ignore enoent fsyncs inspectable -->

## Context

The Raspberry Pi runs Raspberry Pi OS (Debian). A break-beam sensor is wired to GPIO pin 17 (BCM), open-collector receiver, pull-up required. `HIGH` = beam broken, `LOW` = beam clear. The project uses Ansible roles for all system configuration. Existing roles (ssh, ufw, fail2ban) set the convention: Python scripts are not used; this is the first role introducing a persistent Python daemon. The daemon is the foundation for two planned future increments: a daily report webhook and a web UI.

## Goals / Non-Goals

**Goals:**
- Detect beam-break events via rising-edge (LOW→HIGH) polling
- Count breaks per day; reset at midnight
- Persist history as JSON with configurable retention (default 14 days)
- Support test mode (breaks not counted) via sentinel file, auto-reverting after configurable grace period (default 30 minutes; Ansible var `detector_test_mode_grace_period_s` renders into INI key `test_mode_grace_period_s`)
- Be unit-testable without GPIO hardware
- Deploy and start automatically via Ansible + systemd

**Non-Goals:**
- Daily report delivery (Change 2)
- Web UI or remote toggle (Change 3)
- Hardware-level interrupt triggering (polling at 50 ms is sufficient; latency requirement is not sub-millisecond)
- Multi-sensor support

## Decisions

### 1. Polling vs. interrupt-driven detection

**Decision:** Poll at 50 ms intervals.

GPIO edge interrupts (`GPIO.add_event_detect`) require callback threading and are harder to test without hardware. Polling at 50 ms gives ≤50 ms latency — well within any human-scale beam-break duration. The daemon is not safety-critical.

Alternatives: `GPIO.add_event_detect` with threading; hardware debounce IC. Both add complexity without meaningful benefit here.

### 2. GPIO abstraction for testability

**Decision:** `GpioPort` Protocol with constructor injection into `BeamDetector`.

The daemon never imports `RPi.GPIO` at module level — `RpiGpioPort` does a lazy import inside `__init__`. Tests inject `FakeGpioPort` directly. No mocking framework required; `python3 -m unittest` works on any machine.

Alternatives: `unittest.mock.patch`; a module-level GPIO stub variable. Both couple tests to internal import paths.

### 3. Configuration: INI file + plain Python script (not Jinja2 template)

**Decision:** Config lives in `/etc/beam_detector/config.ini` (Jinja2 template). The Python script is deployed verbatim via `ansible.builtin.copy`.

Keeping the script out of the template layer means it can be run and tested locally without Ansible rendering. The future web server can read the same INI file to discover the sentinel path and counts path.

Ansible variables and their INI key mappings (all in the `[detector]` section):
| Ansible var | INI key | Default |
|---|---|---|
| `detector_gpio_pin` | `gpio_pin` | `17` |
| `detector_poll_interval_ms` | `poll_interval_ms` | `50` |
| `detector_gpio_init_retries` | `gpio_init_retries` | `3` |
| `detector_history_retention_days` | `history_retention_days` | `14` |
| `detector_test_mode_grace_period_s` | `test_mode_grace_period_s` | `1800` |

### 4. Test mode IPC via sentinel file

**Decision:** Presence of `/run/beam_detector/test_mode` activates test mode.

Simple, inspectable (`ls /run/beam_detector/`), no inter-process socket needed. The web server (Change 3) can write/delete this file. The daemon auto-removes it after the grace period.

Grace-period tracking uses an in-memory timestamp recorded when the daemon first detects the sentinel on a given run. If the daemon restarts while the sentinel is present, the timer starts fresh from the moment the daemon detects the file — mtime is not consulted. This means a restart resets the grace period, which is acceptable: `/run/` is tmpfs and cleared on reboot anyway, so an unintended restart already implies the sentinel was cleared.

Test mode is strictly tied to sentinel-file existence. The daemon only exits test mode after it has successfully deleted the sentinel file. If removal fails (OS error other than ENOENT), test mode remains active and removal is retried on the next tick.

`/run/` is appropriate: it's tmpfs, cleared on reboot. systemd `RuntimeDirectory=beam_detector` recreates the directory on every service start but does not pre-create the sentinel — the web server (Change 3) is responsible for recreating it after a reboot if test mode should persist.

### 5. Midnight reset via date comparison in main loop

**Decision:** `_maybe_roll_day()` runs on every `tick()`, comparing `datetime.date.today()` (system local timezone,
which is authoritative) to stored `_current_date`. NTP slew and manual clock adjustments are not handled — small NTP
corrections are harmless; a large backward jump could delay a rollover by up to the jump size, which is acceptable
for a non-safety-critical counter.

No timer thread. On a missed midnight (service was down), the JSON is keyed by ISO date strings. On startup the
daemon checks the stored date against today. If they differ, the stored `today_count` is written into the
`history` dict under its date key inside `counts.json` (same file, no separate archive), then today's counter
starts at zero. Old entries beyond the retention window are purged on the next save.

### 6. Live state IPC via tmpfs `state.json`

**Decision:** The daemon writes `/run/beam_detector/state.json` on every poll tick, containing `{"beam_broken": true/false, "today_count": N, "test_mode": true/false}`. The web server (Change 3) reads this file for its SSE stream.

Writing to `/run/` (tmpfs) avoids SD card wear — this file is written every 50 ms (~20 writes/second), which would be destructive on `/var/lib/`. tmpfs is RAM-backed, cleared on reboot, and already managed by systemd `RuntimeDirectory=beam_detector`.

`counts.json` on `/var/lib/` continues to be written only on break events and midnight resets (as before). `state.json` on tmpfs is the live-state IPC channel between daemon and web server, requiring no sockets or shared memory.

**Concurrency policy for `/run/beam_detector/` shared files:**

- `state.json` is written atomically: the daemon writes a `.tmp` sibling, fsyncs it, then renames it into place. `rename(2)` is atomic on Linux, so readers never observe a partial file. Readers (web server) must tolerate `FileNotFoundError` (file absent between ticks or on first startup) by retrying once or serving the last-known state.
- The test-mode sentinel (`/run/beam_detector/test_mode`) is treated as an idempotent presence flag. The web server creates or unlinks it; the daemon polls its existence each tick. TOCTOU between a `Path.exists()` check and the subsequent `unlink()` is benign: worst case the daemon misses one tick and removes the sentinel on the next. No locking is required.
- `/run/beam_detector/` has mode `2775` (setgid, group `detector`) so files created inside inherit the `detector` group. The daemon, reporter (Change 2), and web server (Change 3) all run in the `detector` group and have read/write access; no process needs root for IPC.
- `counts.json` on `/var/lib/beam_detector/` is written infrequently (on break events and midnight rollover) using the same atomic temp-file pattern, so no reader coordination is needed there either.

Alternatives considered: a Unix socket (more complex, requires both sides to be socket-aware); shared memory (overkill); polling `counts.json` from the web server (misses beam state and causes SD wear if polled fast enough to be useful).

## Risks / Trade-offs

- **Single-threaded polling blocks on `time.sleep`** → SIGTERM response latency ≤50 ms (acceptable; systemd default kill timeout is 90 s)
- **Root service user** → GPIO access on stock RPi OS requires root; the daemon runs as root permanently. Attack surface is reduced by the `detector` group: the daemon's service unit sets `Group=detector` and `/run/beam_detector/` is created with setgid mode `2775`, so the reporter and web server run as unprivileged users in that group with no need for root
- **JSON write on every break** → wear on SD card if break rate is very high; mitigation: writes are atomic (full file rewrite, short); acceptable for expected use (≤hundreds of breaks/day)
- **`state.json` written every 50 ms** → tmpfs write, no SD card involved; negligible risk
- **`state.json` lost on reboot** → correct behavior: web server SSE stream reconnects and reads fresh state within one poll interval
- **Sentinel file lost on reboot** → correct behavior: reboot clears test mode, which is safe. Service restart also clears it (RuntimeDirectory).

## Migration Plan

1. Run `ansible-playbook playbooks/site.yml` — role installs package, deploys files, enables service
2. Run `ansible-playbook playbooks/verify.yml` — assertions confirm service running, files present
3. Rollback: `systemctl disable --now beam-detector && rm -rf /opt/beam_detector /etc/beam_detector` (data in `/var/lib/beam_detector` is preserved)

## Open Questions

None for this change.

## See Also

- `notes/implementation.md` — Python class skeletons, counts.json / state.json structures, atomic write pattern, test setup with FakeGpioPort
