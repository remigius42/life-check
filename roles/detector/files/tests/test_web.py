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
    state = tmp_dir / "state.json"
    counts = tmp_dir / "counts.json"
    static = tmp_dir / "static"
    static.mkdir(exist_ok=True)

    env = {
        "DETECTOR_STATE_PATH": str(state),
        "DETECTOR_SENTINEL": str(sentinel),
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
    return _web_mod, sentinel, state, counts


class TestReadState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, self.sentinel, self.state, self.counts = _load_web(
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


class TestToggleEndpoints(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, self.sentinel, self.state, self.counts = _load_web(
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

    def test_enable_os_error_returns_500(self):
        with patch.object(self.mod, "SENTINEL") as mock_s:
            mock_s.parent.mkdir.return_value = None
            mock_s.touch.side_effect = OSError("permission denied")
            resp = self.client.post("/test-mode/enable")
        self.assertEqual(resp.status_code, 500)

    def test_disable_os_error_returns_500(self):
        with patch.object(self.mod, "SENTINEL") as mock_s:
            mock_s.unlink.side_effect = OSError("permission denied")
            resp = self.client.post("/test-mode/disable")
        self.assertEqual(resp.status_code, 500)


class TestReadTodayCount(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, self.sentinel, self.state, self.counts = _load_web(
            Path(self.tmp.name)
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_counts_returns_zero(self):
        self.assertEqual(self.mod._read_today_count(), 0)

    def test_stale_date_returns_zero(self):
        self.counts.write_text(
            json.dumps({"date": "2000-01-01", "today_count": 42, "history": {}})
        )
        self.assertEqual(self.mod._read_today_count(), 0)

    def test_today_date_returns_count(self):
        today = date.today().isoformat()
        self.counts.write_text(
            json.dumps({"date": today, "today_count": 7, "history": {}})
        )
        self.assertEqual(self.mod._read_today_count(), 7)

    def test_corrupt_counts_returns_zero(self):
        self.counts.write_text("not json")
        self.assertEqual(self.mod._read_today_count(), 0)


class TestIndexAndStream(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mod, self.sentinel, self.state, self.counts = _load_web(
            Path(self.tmp.name)
        )
        self.client = self.mod.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_index_returns_200_with_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"<!DOCTYPE html>", resp.data)

    def test_stream_returns_event_stream_content_type(self):
        resp = self.client.get("/stream")
        self.assertIn("text/event-stream", resp.content_type)


if __name__ == "__main__":
    unittest.main()
