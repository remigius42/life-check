# Implementation Notes: Web UI Enhancements

## Daemon Research (`detector.py`)
- The `Config` class needs a new field `reset_count_sentinel`.
- `BeamDetector.tick()` is the main loop. `_maybe_reset_count()` should be called here.
- Deleting the sentinel requires handling `OSError` (similar to `_maybe_revert_test_mode()`).
- Atomic state write is already handled by `_write_state()`.

## Web Server Research (`web.py`)
- `_read_today_count()` currently only returns an `int`. It should be refactored to return the full history dictionary or at least the part needed for rendering.
- `index()` HTML template:
    - Add `<main class="container">` wrapping.
    - Title/H1: "Life Check".
    - History rendering: Iterate over sorted keys (dates) of the history dictionary.
    - CSS:
        ```css
        input[type="submit"] { width: auto; }
        footer { margin-top: 2rem; border-top: 1px solid var(--pico-muted-border-color); padding-top: 1rem; font-size: 0.8rem; }
        ```
- The `onmessage` JS handler only updates specific IDs (`beam`, `count`, `mode`). It does not need to change to support history (history is static per day).

## Service Configuration
- `beam-detector-web.service.j2` needs `Environment=DETECTOR_RESET_SENTINEL={{ detector_reset_sentinel_path }}`.
- `detector_reset_sentinel_path` should be added to `roles/detector/defaults/main.yml`.

## Testing
- Use `unittest.mock.patch` to simulate the sentinel file existence.
- For `web.py`, use `app.test_client()` to verify the redirect and file creation.
