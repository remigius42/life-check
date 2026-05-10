<!-- spellchecker: ignore sigusr -->

## Context

The system consists of a polling daemon (`detector.py`) and a Flask-based web status UI (`web.py`). Communication happens via state files and sentinels in `/run/beam_detector/`. The UI currently lacks padding, branding, and history, and there is no way to reset the daily count without manually deleting the `counts.json` file or waiting for midnight.

## Goals / Non-Goals

**Goals:**
- Provide a branded ("Life Check") and responsive UI.
- Display 14 days of break history.
- Allow the user to reset today's count via a button.
- Maintain consistency with the existing sentinel-based IPC pattern.

**Non-Goals:**
- Real-time SSE updates for the history table (initial render is sufficient).
- Graphical charts (simple list/table is preferred for now).
- Persistent storage of "who" or "when" a reset occurred.

## Decisions

### Decision 1: IPC for Count Reset
- **Choice**: Use a sentinel file `/run/beam_detector/reset_count`.
- **Rationale**: The daemon already polls for a `test_mode` sentinel. Adding one more check to the `tick()` loop is trivial and keeps the communication decoupled. It avoids adding a network port or complex signal handling to the daemon.
- **Alternatives**: Sending SIGUSR1 (requires PID management), adding a dedicated API port to the daemon (overkill).

### Decision 2: Layout Management
- **Choice**: Wrap content in `<main class="container">`.
- **Rationale**: This is the Pico CSS idiomatic way to handle horizontal margins, responsive max-width, and padding. It replaces the need for a manual 8px margin.
- **Alternatives**: Custom CSS margins on `body`.

### Decision 3: History Data Flow
- **Choice**: `web.py` reads `counts.json` and renders history on `GET /`.
- **Rationale**: `counts.json` is updated by the daemon. Since history only changes at the daily rollover, there is no need to stream it over SSE.
- **Alternatives**: Including history in every SSE message (wasteful).

### Decision 4: Button Styling
- **Choice**: Apply `width: auto` to submit inputs in the CSS.
- **Rationale**: Form buttons in Pico CSS stretch to 100% width by default. Setting them to `auto` makes the UI feel less "blocky".

### Decision 5: ESP32 Reset Implementation
- **Choice**: Use an ESPHome `button` component.
- **Rationale**: A `button` component in ESPHome is the standard way to trigger a one-shot action (resetting a global variable) and it automatically appears in the built-in web server UI.
- **Alternatives**: Using a `switch` (requires manual "turn off" after reset), custom web server handler (more complex).

## Risks / Trade-offs

- **[Risk]** Daemon fails to delete the reset sentinel.
- **[Mitigation]** The daemon will log an error and retry the deletion on every tick (50ms interval) until it succeeds.
- **[Risk]** Reset occurs exactly at midnight.
- **[Mitigation]** The daemon handles the daily rollover before checking for the reset sentinel, ensuring no data loss for the previous day.
