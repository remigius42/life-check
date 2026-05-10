## 1. Update Daemon (detector.py)

- [x] 1.1 Add `reset_count_sentinel: Path = Path("/run/beam_detector/reset_count")` to `Config` class and `Config.from_file` parser.
- [x] 1.2 Implement `_maybe_reset_count(self)` in `BeamDetector`: check sentinel, reset `self._today_count`, delete sentinel, call `self._save()` and `self._write_state()`.
- [x] 1.3 Call `_maybe_reset_count()` in `tick()` before edge detection.
- [x] 1.4 Add unit tests for reset functionality (verify count goes to 0 and sentinel is deleted).

## 2. Update Web Server (web.py)

- [x] 2.1 Update `_read_today_count()` to return `(today_count, history_dict)`.
- [x] 2.2 Add `POST /reset-count` endpoint: `SENTINEL_RESET.touch()` and redirect to `/`.
- [x] 2.3 Update `index()` template: use `<main class="container">`, rename to "Life Check", add History section, add Reset form, and GitHub link in footer.
- [x] 2.4 Add CSS for `input[type="submit"] { width: auto; }` and footer styling.
- [x] 2.5 Add unit tests for `POST /reset-count` and history display in HTML.

## 3. Configuration & Verification

- [x] 3.1 Update `roles/detector/templates/beam-detector-web.service.j2` to include `DETECTOR_RESET_SENTINEL` environment variable.
- [x] 3.2 Run `python3 -m unittest discover -s roles/detector/files/tests` and ensure all pass.
- [x] 3.3 Update `playbooks/verify.yml` with checks for "Life Check" branding, reset button IDs, history section, and GitHub link.
- [x] 3.4 Verify UI layout in a browser (check centered content and button widths).

## 4. Documentation

- [x] 4.1 Update `README.md` to reflect the "Life Check" branding and new web UI features.
- [x] 4.2 Update `roles/detector/README.md` to document the new `DETECTOR_RESET_SENTINEL` environment variable and Ansible defaults.
- [x] 4.3 Update `docs/raspberry-pi.md` with instructions on using the new Reset button and the manual sentinel override.
- [x] 4.4 Check and update `TODO.md` if any related items are now completed.

## 5. ESP32 Implementation

- [x] 5.1 Add `button` component to `esphome/life-check.yaml` to reset `today_count`.
- [x] 5.2 Update `docs/esp32.md` to document the new Reset button.
