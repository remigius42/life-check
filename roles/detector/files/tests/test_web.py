# SPDX-License-Identifier: MIT

# spellchecker:ignore dtime

import importlib
import json
import os
import sys
import tempfile
import threading
import unittest
from datetime import date, datetime
from datetime import time as dtime
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_web(tmp_dir: Path):
    """Load web module with env vars pointing at tmp_dir."""
    sentinel = tmp_dir / "test_mode"
    sentinel_reset = tmp_dir / "reset_count"
    state = tmp_dir / "state.json"
    counts = tmp_dir / "counts.json"
    static = tmp_dir / "static"
    static.mkdir(exist_ok=True)

    env = {
        "DETECTOR_STATE_PATH": str(state),
        "DETECTOR_SENTINEL": str(sentinel),
        "DETECTOR_RESET_SENTINEL": str(sentinel_reset),
        "DETECTOR_COUNTS_PATH": str(counts),
        "DETECTOR_STATIC_DIR": str(static),
        "DETECTOR_PICO_CSS": "pico-2.1.1.min.css",
        "DETECTOR_WEB_PORT": "18080",
    }
    with patch.dict(os.environ, env):
        # Re-import so module-level constants pick up the patched env.
        files_dir = Path(__file__).parent.parent
        if str(files_dir) not in sys.path:
            sys.path.insert(0, str(files_dir))
        import web as _web_mod

        importlib.reload(_web_mod)
    return _web_mod, sentinel, sentinel_reset, state, counts


class TestReadState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, self.sentinel, self.reset, self.state, self.counts = _load_web(
            Path(self.tmp.name)
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_file_not_found_returns_default(self):
        result = self.mod._read_state()
        self.assertEqual(
            result, {"beam_broken": False, "today_count": 0, "test_mode": False}
        )

    def test_os_error_returns_default(self):
        self.state.mkdir()  # IsADirectoryError is a subclass of OSError
        result = self.mod._read_state()
        self.assertEqual(
            result, {"beam_broken": False, "today_count": 0, "test_mode": False}
        )

    def test_json_decode_error_returns_default_and_warns(self):
        self.state.write_text("not json")
        with self.assertLogs(self.mod._log, level="WARNING"):
            result = self.mod._read_state()
        self.assertEqual(
            result, {"beam_broken": False, "today_count": 0, "test_mode": False}
        )

    def test_valid_json_returns_parsed(self):
        payload = {"beam_broken": True, "today_count": 5, "test_mode": False}
        self.state.write_text(json.dumps(payload))
        result = self.mod._read_state()
        self.assertEqual(result, payload)


class TestEndpoints(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, self.sentinel, self.reset, self.state, self.counts = _load_web(
            Path(self.tmp.name)
        )
        self.client = self.mod.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_enable_creates_sentinel_and_redirects(self):
        resp = self.client.post("/test-mode/enable")
        self.assertEqual(resp.status_code, 303)
        self.assertTrue(self.sentinel.exists())

    def test_disable_removes_sentinel_and_redirects(self):
        self.sentinel.touch()
        resp = self.client.post("/test-mode/disable")
        self.assertEqual(resp.status_code, 303)
        self.assertFalse(self.sentinel.exists())

    def test_reset_count_creates_sentinel_and_redirects(self):
        resp = self.client.post("/reset-count")
        self.assertEqual(resp.status_code, 303)
        self.assertTrue(self.reset.exists())

    def test_enable_os_error_returns_500(self):
        with patch.object(self.mod, "SENTINEL") as mock_s:
            mock_s.parent.mkdir.return_value = None
            mock_s.touch.side_effect = OSError("permission denied")
            resp = self.client.post("/test-mode/enable")
        self.assertEqual(resp.status_code, 500)

    def test_reset_os_error_returns_500(self):
        with patch.object(self.mod, "SENTINEL_RESET") as mock_s:
            mock_s.parent.mkdir.return_value = None
            mock_s.touch.side_effect = OSError("permission denied")
            resp = self.client.post("/reset-count")
        self.assertEqual(resp.status_code, 500)


class TestReadCounts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, self.sentinel, self.reset, self.state, self.counts = _load_web(
            Path(self.tmp.name)
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_counts_returns_zero_and_empty_history(self):
        c, h = self.mod._read_counts()
        self.assertEqual(c, 0)
        self.assertEqual(h, [])

    def test_stale_date_returns_zero_with_history(self):
        h_data = {"2000-01-01": 42}
        self.counts.write_text(
            json.dumps({"date": "2000-01-01", "today_count": 42, "history": h_data})
        )
        c, h = self.mod._read_counts()
        self.assertEqual(c, 0)
        self.assertEqual(h, [("2000-01-01", 42)])

    def test_today_date_returns_count_with_history(self):
        today = date.today().isoformat()
        h_data = {"2024-05-09": 10}
        self.counts.write_text(
            json.dumps({"date": today, "today_count": 7, "history": h_data})
        )
        c, h = self.mod._read_counts()
        self.assertEqual(c, 7)
        self.assertEqual(h, [("2024-05-09", 10)])


class TestIndexAndStream(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, self.sentinel, self.reset, self.state, self.counts = _load_web(
            Path(self.tmp.name)
        )
        self.client = self.mod.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_index_returns_200_with_life_check_branding(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Life Check", resp.data)
        self.assertIn(b'id="github-link"', resp.data)
        self.assertIn(b'id="reset-count"', resp.data)
        self.assertIn(b'id="history"', resp.data)
        self.assertIn(b'class="container"', resp.data)

    def test_index_shows_version_from_env(self):
        with patch.dict(os.environ, {"DETECTOR_VERSION": "v9.9.9-test"}):
            importlib.reload(self.mod)
            client = self.mod.app.test_client()
            resp = client.get("/")
        self.assertIn(b"v9.9.9-test", resp.data)
        self.assertIn(b'id="version"', resp.data)

    def test_index_shows_unknown_when_version_unset(self):
        env = {k: v for k, v in os.environ.items() if k != "DETECTOR_VERSION"}
        with patch.dict(os.environ, env, clear=True):
            importlib.reload(self.mod)
            client = self.mod.app.test_client()
            resp = client.get("/")
        self.assertIn(b"unknown", resp.data)

    def test_index_shows_history_table(self):
        h_data = {"2026-05-09": 123}
        self.counts.write_text(
            json.dumps(
                {"date": date.today().isoformat(), "today_count": 7, "history": h_data}
            )
        )
        resp = self.client.get("/")
        self.assertIn(b"2026-05-09", resp.data)
        self.assertIn(b"123", resp.data)

    def test_index_shows_history_unavailable_when_missing(self):
        resp = self.client.get("/")
        self.assertIn(b"History unavailable", resp.data)

    def test_stream_returns_event_stream_content_type(self):
        resp = self.client.get("/stream")
        self.assertIn("text/event-stream", resp.content_type)


class TestHaTimerCancellation(unittest.TestCase):
    """Jitter timer cancelled when count drops below threshold (midnight reset)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, *_ = _load_web(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_cancel_ha_timer_cancels_and_clears(self):
        mock_timer = MagicMock()
        setattr(self.mod, "_ha_timer", mock_timer)
        self.mod._cancel_ha_timer()
        mock_timer.cancel.assert_called_once()
        self.assertIsNone(self.mod._ha_timer)

    def test_cancel_ha_timer_noop_when_no_timer(self):
        setattr(self.mod, "_ha_timer", None)
        self.mod._cancel_ha_timer()  # must not raise
        self.assertIsNone(self.mod._ha_timer)

    def test_pending_timer_cancelled_on_threshold_drop(self):
        """On threshold drop, pending timer is cancelled before state is cleared."""
        mock_timer = MagicMock()
        mock_timer.is_alive.return_value = True
        setattr(self.mod, "_ha_timer", mock_timer)
        setattr(self.mod, "_ha_ok", True)

        self.mod._cancel_ha_timer()
        self.mod._set_ha_ok(False)

        mock_timer.cancel.assert_called_once()
        self.assertIsNone(self.mod._ha_timer)
        self.assertFalse(self.mod._ha_ok)


class TestHomeAssistantEndpoint(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, *_ = _load_web(Path(self.tmp.name))
        self.client = self.mod.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_returns_200(self):
        resp = self.client.get("/home-assistant")
        self.assertEqual(resp.status_code, 200)

    def test_returns_not_ok_by_default(self):
        setattr(self.mod, "_ha_ok", False)
        resp = self.client.get("/home-assistant")
        self.assertEqual(resp.get_json(), {"state": "not_ok"})

    def test_returns_ok_when_ha_ok_true(self):
        setattr(self.mod, "_ha_ok", True)
        with patch.object(self.mod, "_in_privacy_window", return_value=False):
            resp = self.client.get("/home-assistant")
        self.assertEqual(resp.get_json(), {"state": "ok"})


class TestMaybeStartJitterTimer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, *_ = _load_web(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_starts_timer_when_none_exists(self):
        setattr(self.mod, "_ha_timer", None)
        with patch("threading.Timer") as mock_timer_cls:
            mock_instance = MagicMock()
            mock_timer_cls.return_value = mock_instance
            self.mod._maybe_start_jitter_timer()
        mock_timer_cls.assert_called_once()
        mock_instance.start.assert_called_once()

    def test_does_not_start_new_timer_when_one_is_alive(self):
        mock_timer = MagicMock()
        mock_timer.is_alive.return_value = True
        setattr(self.mod, "_ha_timer", mock_timer)
        with patch("threading.Timer") as mock_timer_cls:
            self.mod._maybe_start_jitter_timer()
        mock_timer_cls.assert_not_called()

    def test_starts_new_timer_when_existing_timer_dead(self):
        mock_timer = MagicMock()
        mock_timer.is_alive.return_value = False
        setattr(self.mod, "_ha_timer", mock_timer)
        with patch("threading.Timer") as mock_timer_cls:
            mock_instance = MagicMock()
            mock_timer_cls.return_value = mock_instance
            self.mod._maybe_start_jitter_timer()
        mock_timer_cls.assert_called_once()
        mock_instance.start.assert_called_once()


class TestPrivacyWindow(unittest.TestCase):
    """Unit tests for _in_privacy_window() with controlled clock and env vars."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _load_with_times(self, report_time: str, window_end: str):
        env = {
            "DETECTOR_REPORT_TIME": report_time,
            "DETECTOR_HA_PRIVACY_WINDOW_END": window_end,
        }
        with patch.dict(os.environ, env):
            mod, *_ = _load_web(Path(self.tmp.name))
        return mod

    def _check(self, mod, now: dtime) -> bool:
        with patch("web.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(
                2026, 1, 1, now.hour, now.minute, now.second
            )
            return mod._in_privacy_window()

    def test_in_window_evening(self):
        mod = self._load_with_times("17:00", "08:00")
        self.assertTrue(self._check(mod, dtime(20, 0)))

    def test_in_window_after_midnight(self):
        mod = self._load_with_times("17:00", "08:00")
        self.assertTrue(self._check(mod, dtime(3, 30)))

    def test_in_window_at_start_boundary(self):
        mod = self._load_with_times("17:00", "08:00")
        self.assertTrue(self._check(mod, dtime(17, 0)))

    def test_out_of_window_daytime(self):
        mod = self._load_with_times("17:00", "08:00")
        self.assertFalse(self._check(mod, dtime(12, 0)))

    def test_out_of_window_at_end_boundary(self):
        # 08:00 is the first minute outside the window
        mod = self._load_with_times("17:00", "08:00")
        self.assertFalse(self._check(mod, dtime(8, 0)))

    def test_out_of_window_just_before_start(self):
        mod = self._load_with_times("17:00", "08:00")
        self.assertFalse(self._check(mod, dtime(16, 59)))

    def test_midnight_cap_report_time_in_morning(self):
        # report_time=02:00 < window_end=08:00 → effective_start capped to 00:00
        mod = self._load_with_times("02:00", "08:00")
        self.assertTrue(self._check(mod, dtime(1, 0)))  # in window (before end)
        self.assertFalse(self._check(mod, dtime(10, 0)))  # out of window (after end)

    def test_midnight_cap_boundary_at_window_end(self):
        mod = self._load_with_times("01:00", "08:00")
        self.assertFalse(self._check(mod, dtime(8, 0)))  # end boundary is exclusive

    def test_report_time_equals_window_end_daytime_not_in_window(self):
        # report_time == window_end (degenerate config) must not make sensor always off
        mod = self._load_with_times("08:00", "08:00")
        self.assertFalse(self._check(mod, dtime(12, 0)))

    def test_in_window_at_start_boundary_with_nonzero_seconds(self):
        # now=17:00:30 strips to 17:00:00 which equals start — still in window
        mod = self._load_with_times("17:00", "08:00")
        with patch("web.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 1, 17, 0, 30)
            self.assertTrue(mod._in_privacy_window())


class TestWatchHaStateRestart(unittest.TestCase):
    """
    _watch_ha_state must reflect real count at startup,
    not assume last_crossed=False.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, *_ = _load_web(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_ha_ok_set_immediately_when_already_above_threshold(self):
        """
        Restart while count >= threshold: _ha_ok True immediately,
        no jitter timer.
        """
        setattr(self.mod, "_ha_ok", False)
        setattr(self.mod, "_ha_timer", None)

        above_threshold = self.mod._HA_THRESHOLD + 1

        with patch.object(self.mod, "_read_counts", return_value=(above_threshold, [])):
            with patch.object(self.mod, "time") as mock_time:
                mock_time.sleep.side_effect = SystemExit
                try:
                    self.mod._watch_ha_state()
                except SystemExit:
                    pass

        self.assertTrue(self.mod._ha_ok)
        self.assertIsNone(self.mod._ha_timer)


class TestWatcherThread(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_only_one_watcher_thread_after_multiple_reloads(self):
        _load_web(Path(self.tmp.name))
        _load_web(Path(self.tmp.name))
        ha_watchers = [t for t in threading.enumerate() if t.name == "ha-watcher"]
        self.assertEqual(len(ha_watchers), 1)


class TestJitterConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_negative_jitter_env_var_clamped_to_zero(self):
        env = {"DETECTOR_HA_JITTER_MAX_ADD_S": "-1800"}
        with patch.dict(os.environ, env):
            mod, *_ = _load_web(Path(self.tmp.name))
        self.assertGreaterEqual(mod._HA_JITTER_MAX_ADD_S, 0)


class TestHomeAssistantEndpointPrivacyWindow(unittest.TestCase):
    """Privacy window suppresses 'ok' state at the endpoint level."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _load_with_times(self, report_time: str, window_end: str):
        env = {
            "DETECTOR_REPORT_TIME": report_time,
            "DETECTOR_HA_PRIVACY_WINDOW_END": window_end,
        }
        with patch.dict(os.environ, env):
            mod, *_ = _load_web(Path(self.tmp.name))
        return mod

    def test_returns_not_ok_in_window_even_when_ha_ok_true(self):
        mod = self._load_with_times("17:00", "08:00")
        setattr(mod, "_ha_ok", True)
        client = mod.app.test_client()
        with patch("web.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 1, 20, 0, 0)
            resp = client.get("/home-assistant")
        self.assertEqual(resp.get_json(), {"state": "not_ok"})

    def test_returns_ok_outside_window_when_ha_ok_true(self):
        mod = self._load_with_times("17:00", "08:00")
        setattr(mod, "_ha_ok", True)
        client = mod.app.test_client()
        with patch("web.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 1, 12, 0, 0)
            resp = client.get("/home-assistant")
        self.assertEqual(resp.get_json(), {"state": "ok"})

    def test_returns_not_ok_outside_window_when_ha_ok_false(self):
        mod = self._load_with_times("17:00", "08:00")
        setattr(mod, "_ha_ok", False)
        client = mod.app.test_client()
        with patch("web.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 1, 12, 0, 0)
            resp = client.get("/home-assistant")
        self.assertEqual(resp.get_json(), {"state": "not_ok"})


if __name__ == "__main__":
    unittest.main()
