<!-- spellchecker: ignore fsyncs oserror -->

## 1. Ansible Role Scaffold

- [x] 1.1 Run `ansible-galaxy init roles/detector` and delete unused dirs (files/ kept, vars/ tests/ removed)
- [x] 1.2 Write `roles/detector/defaults/main.yml` with all `detector_*` variables and defaults
- [x] 1.3 Write `roles/detector/meta/main.yml` (author, license, min_ansible_version: 2.14)

## 2. Python Daemon

- [x] 2.1 Write `roles/detector/files/detector.py`: `GpioPort` Protocol, `RpiGpioPort`, `Config` dataclass with `from_file()`, `BeamDetector` class with `tick()`, `run()`, `_maybe_roll_day()`, `_maybe_revert_test_mode()`, `_on_break()`, `_load()`, `_save()`, `_write_state()` (atomic write of `state.json` to tmpfs on every tick), signal handlers, and `main()` entry point
- [x] 2.2 Verify script runs locally with `python3 roles/detector/files/detector.py --help` or at minimum imports cleanly: `python3 -c "import sys; sys.modules['RPi']=''; sys.modules['RPi.GPIO']=''; exec(open('roles/detector/files/detector.py').read())"` (no ImportError)

## 3. Unit Tests

- [x] 3.1 Write `roles/detector/files/tests/test_detector.py`: `FakeGpioPort`, `TestBreakCounting`, `TestTestMode`, `TestDailyReset`, `TestHistoryRetention`, `TestPersistence`
- [x] 3.2 Run `python3 -m unittest discover roles/detector/files/tests` locally and confirm all tests pass

## 4. Ansible Templates and Tasks

- [x] 4.1 Write `roles/detector/templates/config.ini.j2` with all tunable parameters referencing `detector_*` vars
- [x] 4.2 Write `roles/detector/templates/beam-detector.service.j2` with `RuntimeDirectory=beam_detector`
- [x] 4.3 Write `roles/detector/tasks/main.yml`: apt install, directory creation, copy script+tests, template config+service, service enable+start
- [x] 4.4 Write `roles/detector/handlers/main.yml`: `Reload systemd` and `Restart beam-detector`

## 5. Playbook Integration

- [x] 5.1 Add `- detector` to `playbooks/site.yml` after `fail2ban`
- [x] 5.2 Add six detector verify tasks to `playbooks/verify.yml`: package installed, script present, config present, data dir present, service running and enabled (service_facts already gathered earlier in the file)

## 6. Cleanup

- [x] 6.1 Delete `example_detector.py` from the repo root (superseded by `detector.py`)

## 7. Spec-driven fixes (post-CodeRabbit review)

- [x] 7.1 **defaults + config template** — add `detector_poll_interval_ms` (default 50) and `detector_gpio_init_retries` (default 3) to `roles/detector/defaults/main.yml` and `roles/detector/templates/config.ini.j2` (touches 1.2, 4.1)
- [x] 7.2 **Stale-date load behavior** — already implemented and tested: `test_stale_date_not_restored_as_today` (test_detector.py:209) asserts `_history.get(yesterday) == 42`; spec updated to match
- [x] 7.3 **Flush on shutdown** — update signal handler in `detector.py` to call `_save()` before `gpio.cleanup()`; extend `test_cleanup_called_on_run_exit` (test_detector.py:229) to assert counts.json is written with current count before cleanup
- [x] 7.4 **Error handling — corrupt counts.json** — in `_load()`: catch `json.JSONDecodeError`/`OSError`, rename bad file to `counts.json.bak`, log error, start with zero state; add `TestPersistence.test_corrupt_counts_json_starts_fresh`
- [x] 7.5 **Error handling — write failures** — in `_save()` and `_write_state()`: catch `OSError`, log, retain in-memory state, do not exit; fsync temp file before rename in atomic writes; add `TestPersistence.test_save_failure_does_not_crash`
- [x] 7.6 **Error handling — GPIO init retry** — in `RpiGpioPort.__init__`: retry up to `gpio_init_retries` times (injectable sleep for testability) with 1 s delay on exception, then raise; add `TestGpioInitRetry` class with injectable failing init
- [x] 7.7 **Zero-count day archival bug** — `_load()` used `if stale_date and stale_count:` which silently dropped zero-count days; fixed to `if stale_date:`; spec scenario updated to say "including zero"; added `test_stale_date_zero_count_archived`
- [x] 7.8 **daemon_reload on service enable** — `tasks/main.yml` Enable task had `daemon_reload: false`; fixed to `true` so the freshly deployed unit file is visible to systemd before start
- [x] 7.9 **Sentinel removal OSError** — `_maybe_revert_test_mode()` silently swallowed non-FileNotFoundError; now logs the error; spec grace-period scenario updated to describe this behavior
- [x] 7.10 **Timer consistency on sentinel OSError** — `_maybe_revert_test_mode()` was resetting `_test_mode_entered_at = None` unconditionally after the try/except, meaning an OSError re-delayed the retry by a full grace period; fixed to only clear the timer on successful `unlink()` or `FileNotFoundError` (preserving it on any other OSError so the grace-period countdown is not restarted); updated `test_sentinel_removal_oserror_is_logged` to assert sentinel still exists, timer preserved, and next break suppressed
- [x] 7.11 **Atomic write durability** — `_save()` and `_write_state()` used `write_text()` (closes fd) then reopened `"r+"` to fsync — the fsync was a no-op since the original fd was closed; replaced both with a single `open("w")` context that writes, flushes, and fsyncs before `os.replace()`
- [x] 7.12 **Grace-period restart scenario test** — added `test_grace_period_timer_starts_fresh_on_restart`: asserts `_test_mode_entered_at` is None before first tick and set after, confirming timer starts fresh on daemon restart
- [x] 7.13 **Sentinel OSError logging test** — added `test_sentinel_removal_oserror_is_logged`: patches `Path.unlink` to raise `PermissionError`, asserts error message containing the sentinel path is emitted
- [x] 7.14 **Rename `_last_pin_state` → `_pin_state`** — `_write_state()` reads this field after the tick update, so "last" was misleading; renamed to `_pin_state` throughout `detector.py`

## 8. Post-spec-review fixes (consistency audit)

- [x] 8.1 **Future date on load** — `_load()` archived future-dated `today_count` into history where it could never be pruned by the retention window; fixed to log a warning and discard instead; added `test_future_date_discarded_not_archived`
- [x] 8.2 **Backward clock jump rollover bug** — `_maybe_roll_day()` used `today != _current_date`, triggering a spurious rollover and counter reset when the clock moved backward; fixed to `today > _current_date` (roll forward only); added `test_no_rollover_on_backward_clock_jump`
- [x] 8.3 **Forward multi-day jump test** — added `test_forward_clock_jump_single_rollover_no_backfill`: asserts that a large forward jump produces exactly one rollover and no intermediate dates are backfilled (spec scenario)
- [x] 8.4 **Sentinel recreation timer test** — added `test_sentinel_recreation_resets_grace_timer`: asserts that deleting and recreating the sentinel file causes `_test_mode_entered_at` to be cleared and restarted fresh (spec scenario)

## 9. Non-root group infrastructure (consistency with detector-web)

- [x] 9.1 Add `detector_group: "detector"` to `roles/detector/defaults/main.yml`
- [x] 9.2 Add `ansible.builtin.group` task to `roles/detector/tasks/main.yml` to create the `detector` system group (before directory creation tasks)
- [x] 9.3 Update directory ownership in `roles/detector/tasks/main.yml`: set `/var/lib/beam_detector/` to `root:{{ detector_group }}` mode `0750`; removed manual `/run/beam_detector/` creation (systemd owns it via RuntimeDirectory)
- [x] 9.4 Update `roles/detector/templates/beam-detector.service.j2`: add `Group={{ detector_group }}` and `RuntimeDirectoryMode=2775` to the `[Service]` section so systemd recreates `/run/beam_detector/` with the correct group and setgid bit on every service start

## 10. Python formatting tooling (Black)

- [x] 10.1 Add `pyproject.toml` at repo root with `[tool.black]` so editors auto-discover Black as the project formatter
- [x] 10.2 Add `psf/black` hook to `.pre-commit-config.yaml` (files: `\.py$`, stages: `[pre-commit]`) for enforced formatting on commit
- [x] 10.3 Add `[tool.ruff]` and `[tool.pyright]` sections to `pyproject.toml`; suppress `reportMissingModuleSource` for `RPi.GPIO`
- [x] 10.4 Add `astral-sh/ruff-pre-commit` and `RobertCraigie/pyright-python` hooks to `.pre-commit-config.yaml`
- [x] 10.5 Fix pyright findings: narrow `float | None` before `assertGreaterEqual`; rename `self_` → `self` in `FakeGPIO`; shorten two over-length comments flagged by ruff E501
