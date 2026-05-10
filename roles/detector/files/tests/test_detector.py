#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Unit tests for detector.py — run without GPIO hardware."""

import datetime
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Stub out RPi.GPIO before importing detector
sys.modules.setdefault("RPi", type(sys)("RPi"))
sys.modules.setdefault("RPi.GPIO", type(sys)("RPi.GPIO"))

sys.path.insert(0, str(Path(__file__).parent.parent))
from detector import BeamDetector, Config, RpiGpioPort  # noqa: E402


class FakeGpioPort:
    def __init__(self, state: bool = False) -> None:
        self.state = state
        self.cleaned_up = False

    def read(self) -> bool:
        return self.state

    def cleanup(self) -> None:
        self.cleaned_up = True


def _make_detector(tmp_dir: str, gpio: FakeGpioPort, **cfg_overrides) -> BeamDetector:
    cfg = Config(
        counts_path=Path(tmp_dir) / "counts.json",
        state_path=Path(tmp_dir) / "state.json",
        test_mode_sentinel=Path(tmp_dir) / "test_mode",
        reset_count_sentinel=Path(tmp_dir) / "reset_count",
        **cfg_overrides,
    )
    return BeamDetector(cfg, gpio)


class TestBreakCounting(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._gpio = FakeGpioPort(state=True)  # HIGH = intact
        self._det = _make_detector(self._tmp.name, self._gpio)

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_phantom_break_when_beam_already_broken_at_startup(self):
        gpio = FakeGpioPort(state=False)  # LOW = broken
        det = _make_detector(self._tmp.name, gpio)
        det.tick()
        self.assertEqual(det._today_count, 0)

    def test_single_falling_edge_registers_one_break(self):
        self._gpio.state = False  # beam broken (LOW)
        self._det.tick()
        self.assertEqual(self._det._today_count, 1)

    def test_sustained_low_does_not_re_register(self):
        self._gpio.state = False
        self._det.tick()
        self._det.tick()
        self._det.tick()
        self.assertEqual(self._det._today_count, 1)

    def test_two_breaks_separated_by_high(self):
        self._gpio.state = False  # first break
        self._det.tick()
        self._gpio.state = True  # restore
        self._det.tick()
        self._gpio.state = False  # second break
        self._det.tick()
        self.assertEqual(self._det._today_count, 2)

    def test_state_json_written_on_tick(self):
        state_path = Path(self._tmp.name) / "state.json"
        self._gpio.state = False  # beam broken (LOW)
        self._det.tick()
        data = json.loads(state_path.read_text())
        self.assertTrue(data["beam_broken"])
        self.assertEqual(data["today_count"], 1)
        self.assertFalse(data["test_mode"])


class TestTestMode(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._gpio = FakeGpioPort(state=True)  # HIGH = intact
        self._det = _make_detector(self._tmp.name, self._gpio)
        self._sentinel = Path(self._tmp.name) / "test_mode"

    def tearDown(self):
        self._tmp.cleanup()

    def test_break_not_counted_in_test_mode(self):
        self._sentinel.touch()
        self._gpio.state = False  # beam broken (LOW)
        self._det.tick()
        self.assertEqual(self._det._today_count, 0)

    def test_break_counted_after_sentinel_removed(self):
        self._sentinel.touch()
        self._gpio.state = False  # broken in test mode — not counted
        self._det.tick()
        self._sentinel.unlink()
        self._gpio.state = True  # restore
        self._det.tick()
        self._gpio.state = False  # broken again, sentinel gone
        self._det.tick()
        self.assertEqual(self._det._today_count, 1)

    def test_state_json_reflects_test_mode(self):
        self._sentinel.touch()
        self._det.tick()
        state = json.loads((Path(self._tmp.name) / "state.json").read_text())
        self.assertTrue(state["test_mode"])

    def test_grace_period_timer_starts_fresh_on_restart(self):
        self._sentinel.touch()
        # Simulate restart: new detector instance while sentinel already present
        det = _make_detector(self._tmp.name, self._gpio, test_mode_grace_period_s=9999)
        self.assertIsNone(det._test_mode_entered_at)
        det.tick()
        self.assertIsNotNone(det._test_mode_entered_at)
        self.assertTrue(self._sentinel.exists())

    def test_sentinel_removal_oserror_is_logged(self):
        import unittest.mock

        self._sentinel.touch()
        det = _make_detector(self._tmp.name, self._gpio, test_mode_grace_period_s=0)
        with unittest.mock.patch(
            "pathlib.Path.unlink", side_effect=PermissionError("read-only fs")
        ):
            with self.assertLogs("detector", level="ERROR") as cm:
                det.tick()
            self.assertTrue(
                any(str(det._cfg.test_mode_sentinel) in msg for msg in cm.output)
            )
            # sentinel still present and timer preserved — test mode remains active
            self.assertTrue(self._sentinel.exists())
            self.assertIsNotNone(det._test_mode_entered_at)
            # next break must not be counted (mock active; sentinel still exists)
            self._gpio.state = False
            det.tick()
            self.assertEqual(det._today_count, 0)

    def test_sentinel_recreation_resets_grace_timer(self):
        # Enter test mode; let timer start
        self._sentinel.touch()
        det = _make_detector(self._tmp.name, self._gpio, test_mode_grace_period_s=9999)
        det.tick()
        original_entered_at = det._test_mode_entered_at
        self.assertIsNotNone(original_entered_at)
        # External agent removes sentinel — timer clears
        self._sentinel.unlink()
        det.tick()
        self.assertIsNone(det._test_mode_entered_at)
        # Sentinel recreated — timer starts fresh from zero
        self._sentinel.touch()
        det.tick()
        self.assertIsNotNone(det._test_mode_entered_at)
        assert det._test_mode_entered_at is not None
        assert original_entered_at is not None
        self.assertGreaterEqual(det._test_mode_entered_at, original_entered_at)

    def test_auto_revert_after_grace_period(self):
        self._sentinel.touch()
        self._det = _make_detector(
            self._tmp.name, self._gpio, test_mode_grace_period_s=0
        )
        self._det.tick()
        self.assertFalse(self._sentinel.exists())

    def test_grace_period_not_yet_elapsed(self):
        self._sentinel.touch()
        self._det = _make_detector(
            self._tmp.name, self._gpio, test_mode_grace_period_s=9999
        )
        self._det.tick()
        self.assertTrue(self._sentinel.exists())


class TestResetCount(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._gpio = FakeGpioPort(state=True)  # HIGH = intact
        self._det = _make_detector(self._tmp.name, self._gpio)
        self._sentinel = Path(self._tmp.name) / "reset_count"

    def tearDown(self):
        self._tmp.cleanup()

    def test_count_reset_via_sentinel(self):
        self._gpio.state = False  # break
        self._det.tick()
        self.assertEqual(self._det._today_count, 1)

        self._gpio.state = True
        self._det.tick()

        self._sentinel.touch()
        self._det.tick()

        self.assertEqual(self._det._today_count, 0)
        self.assertFalse(self._sentinel.exists())
        # Verify it was saved
        counts = json.loads((Path(self._tmp.name) / "counts.json").read_text())
        self.assertEqual(counts["today_count"], 0)

    def test_breaks_ignored_during_reset_tick(self):
        self._det._today_count = 5
        self._sentinel.touch()
        self._gpio.state = False  # break during the same tick as reset
        # tick() calls _maybe_reset_count before edge detection
        self._det.tick()

        self.assertEqual(self._det._today_count, 0)
        self.assertFalse(self._sentinel.exists())

    def test_reset_sentinel_deletion_failure_retries(self):
        import unittest.mock

        self._det._today_count = 5
        self._sentinel.touch()

        with unittest.mock.patch("pathlib.Path.unlink", side_effect=OSError("busy")):
            with self.assertLogs("detector", level="ERROR") as cm:
                self._det.tick()
            self.assertTrue(any("will retry" in msg for msg in cm.output))

        self.assertEqual(self._det._today_count, 0)
        self.assertTrue(self._sentinel.exists())

        # Second tick should retry and succeed (if no patch)
        self._det.tick()
        self.assertFalse(self._sentinel.exists())


class TestDailyReset(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._gpio = FakeGpioPort(state=True)  # HIGH = intact
        self._det = _make_detector(self._tmp.name, self._gpio)

    def tearDown(self):
        self._tmp.cleanup()

    def test_roll_day_archives_and_resets_count(self):
        self._gpio.state = False  # beam broken
        self._det.tick()
        self.assertEqual(self._det._today_count, 1)

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        self._det._current_date = yesterday

        self._gpio.state = True  # restore
        self._det.tick()

        self.assertEqual(self._det._today_count, 0)
        self.assertIn(yesterday.isoformat(), self._det._history)
        self.assertEqual(self._det._history[yesterday.isoformat()], 1)

    def test_no_rollover_on_backward_clock_jump(self):
        self._gpio.state = False  # beam broken
        self._det.tick()
        self.assertEqual(self._det._today_count, 1)
        # Simulate clock jumping forward then being corrected back (NTP slew)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        self._det._current_date = tomorrow
        self._gpio.state = True  # restore
        self._det.tick()
        # today < _current_date — must NOT roll back, counter preserved
        self.assertEqual(self._det._today_count, 1)
        self.assertEqual(self._det._current_date, tomorrow)

    def test_forward_clock_jump_single_rollover_no_backfill(self):
        self._gpio.state = False  # beam broken
        self._det.tick()
        self.assertEqual(self._det._today_count, 1)
        # Jump _current_date back three days to simulate clock jumping forward 3 days
        three_days_ago = datetime.date.today() - datetime.timedelta(days=3)
        self._det._current_date = three_days_ago
        self._gpio.state = True  # restore
        self._det.tick()
        # One rollover: three_days_ago archived, counter reset; no intermediate backfill
        self.assertEqual(self._det._today_count, 0)
        self.assertIn(three_days_ago.isoformat(), self._det._history)
        self.assertEqual(self._det._current_date, datetime.date.today())
        # Intermediate dates must NOT be present
        for gap in (1, 2):
            mid = (datetime.date.today() - datetime.timedelta(days=gap)).isoformat()
            self.assertNotIn(mid, self._det._history)


class TestHistoryRetention(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._gpio = FakeGpioPort(state=True)  # HIGH = intact
        self._det = _make_detector(self._tmp.name, self._gpio, history_retention_days=3)

    def tearDown(self):
        self._tmp.cleanup()

    def test_old_entries_purged_on_save(self):
        today = datetime.date.today()
        old_date = (today - datetime.timedelta(days=10)).isoformat()
        recent_date = (today - datetime.timedelta(days=2)).isoformat()
        self._det._history[old_date] = 5
        self._det._history[recent_date] = 3

        self._gpio.state = False  # beam broken (LOW)
        self._det.tick()

        counts = json.loads((Path(self._tmp.name) / "counts.json").read_text())
        self.assertNotIn(old_date, counts["history"])
        self.assertIn(recent_date, counts["history"])


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def test_today_count_survives_restart(self):
        gpio = FakeGpioPort(state=True)  # start intact
        det = _make_detector(self._tmp.name, gpio)
        gpio.state = False  # break 1
        det.tick()
        gpio.state = True  # restore
        det.tick()
        gpio.state = False  # break 2
        det.tick()
        self.assertEqual(det._today_count, 2)

        gpio2 = FakeGpioPort(state=True)
        det2 = _make_detector(self._tmp.name, gpio2)
        self.assertEqual(det2._today_count, 2)

    def test_stale_date_not_restored_as_today(self):
        counts_path = Path(self._tmp.name) / "counts.json"
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        counts_path.write_text(
            json.dumps(
                {
                    "date": yesterday,
                    "today_count": 42,
                    "history": {},
                }
            )
        )
        gpio = FakeGpioPort()
        det = _make_detector(self._tmp.name, gpio)
        self.assertEqual(det._today_count, 0)
        self.assertEqual(det._history.get(yesterday), 42)

    def test_stale_date_zero_count_archived(self):
        counts_path = Path(self._tmp.name) / "counts.json"
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        counts_path.write_text(
            json.dumps(
                {
                    "date": yesterday,
                    "today_count": 0,
                    "history": {},
                }
            )
        )
        gpio = FakeGpioPort()
        det = _make_detector(self._tmp.name, gpio)
        self.assertEqual(det._today_count, 0)
        self.assertIn(yesterday, det._history)
        self.assertEqual(det._history[yesterday], 0)

    def test_future_date_discarded_not_archived(self):
        counts_path = Path(self._tmp.name) / "counts.json"
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        counts_path.write_text(
            json.dumps(
                {
                    "date": tomorrow,
                    "today_count": 99,
                    "history": {},
                }
            )
        )
        gpio = FakeGpioPort()
        with self.assertLogs("detector", level="WARNING") as cm:
            det = _make_detector(self._tmp.name, gpio)
        self.assertEqual(det._today_count, 0)
        self.assertNotIn(tomorrow, det._history)
        self.assertTrue(any(tomorrow in msg for msg in cm.output))

    def test_missing_file_starts_fresh(self):
        gpio = FakeGpioPort()
        det = _make_detector(self._tmp.name, gpio)
        self.assertEqual(det._today_count, 0)
        self.assertEqual(det._history, {})

    def test_counts_saved_on_shutdown(self):
        import threading
        import unittest.mock

        gpio = FakeGpioPort()
        det = _make_detector(self._tmp.name, gpio, poll_interval_ms=0)
        # Register a break so today_count > 0
        gpio.state = True
        det.tick()
        gpio.state = False
        det.tick()
        self.assertEqual(det._today_count, 1)
        # Remove counts.json so we can verify run()'s finally-block re-saves it
        counts_path = Path(self._tmp.name) / "counts.json"
        counts_path.unlink()
        with unittest.mock.patch("signal.signal"):
            t = threading.Thread(target=det.run)
            t.start()
            time.sleep(0.02)
            det._running = False
            t.join(timeout=1)
            self.assertFalse(t.is_alive(), "detector thread did not terminate")
        data = json.loads(counts_path.read_text())
        self.assertEqual(data["today_count"], 1)

    def test_cleanup_called_on_run_exit(self):
        import threading
        import unittest.mock

        gpio = FakeGpioPort()
        det = _make_detector(self._tmp.name, gpio, poll_interval_ms=0)
        with unittest.mock.patch("signal.signal"):
            t = threading.Thread(target=det.run)
            t.start()
            time.sleep(0.02)
            det._running = False
            t.join(timeout=1)
            self.assertFalse(t.is_alive(), "detector thread did not terminate")
        self.assertTrue(gpio.cleaned_up)

    def test_cleanup_called_when_tick_raises(self):
        import threading
        import unittest.mock

        class BrokenGpioPort(FakeGpioPort):
            def __init__(self):
                super().__init__()
                self._first = True

            def read(self) -> bool:
                if self._first:
                    self._first = False
                    return False
                raise RuntimeError("hardware fault")

        gpio = BrokenGpioPort()
        det = _make_detector(self._tmp.name, gpio, poll_interval_ms=0)
        with unittest.mock.patch("signal.signal"):
            t = threading.Thread(target=det.run)
            t.start()
            t.join(timeout=1)
            self.assertFalse(t.is_alive(), "detector thread did not terminate")
        self.assertTrue(gpio.cleaned_up)

    def test_corrupt_counts_json_starts_fresh(self):
        counts_path = Path(self._tmp.name) / "counts.json"
        counts_path.write_text("not valid json {{{")
        gpio = FakeGpioPort()
        det = _make_detector(self._tmp.name, gpio)
        self.assertEqual(det._today_count, 0)
        self.assertEqual(det._history, {})
        self.assertTrue((Path(self._tmp.name) / "counts.json.bak").exists())

    def test_save_failure_does_not_crash(self):
        import unittest.mock

        gpio = FakeGpioPort(state=True)  # start intact
        det = _make_detector(self._tmp.name, gpio)
        gpio.state = False  # beam broken
        with unittest.mock.patch("os.replace", side_effect=OSError("disk full")):
            det.tick()  # must not raise
        self.assertEqual(det._today_count, 1)  # in-memory state preserved


class TestGpioInitRetry(unittest.TestCase):
    def _make_gpio(self, fail_times: int):
        calls = {"n": 0}

        class FakeGPIO:
            BCM = 11
            IN = 1
            PUD_UP = 22

            def setmode(self, mode):
                calls["n"] += 1
                if calls["n"] <= fail_times:
                    raise RuntimeError("hardware not ready")

            def setup(self, pin, mode, pull_up_down=None):
                pass

            def input(self, pin):
                return False

            def cleanup(self):
                pass

        return FakeGPIO(), calls

    def test_succeeds_after_transient_failures(self):
        sleep_calls = []
        gpio_mod, calls = self._make_gpio(fail_times=2)
        port = RpiGpioPort(
            17,
            retries=3,
            _sleep_fn=lambda s: sleep_calls.append(s),
            _gpio_module=gpio_mod,
        )
        self.assertIsNotNone(port)
        self.assertEqual(len(sleep_calls), 2)  # slept between each failed attempt

    def test_raises_after_all_retries_exhausted(self):
        sleep_calls = []
        gpio_mod, _ = self._make_gpio(fail_times=99)
        with self.assertRaises(RuntimeError):
            RpiGpioPort(
                17,
                retries=3,
                _sleep_fn=lambda s: sleep_calls.append(s),
                _gpio_module=gpio_mod,
            )
        self.assertEqual(len(sleep_calls), 2)  # retries-1 sleeps before final failure


if __name__ == "__main__":
    unittest.main()
