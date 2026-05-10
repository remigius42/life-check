# SPDX-License-Identifier: MIT
import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


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


if __name__ == "__main__":
    unittest.main()
