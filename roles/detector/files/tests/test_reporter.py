#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Unit tests for reporter.py — no network or filesystem side-effects."""
from __future__ import annotations

import datetime
import http.client
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from reporter import _post, _read_count, main  # noqa: E402


def _run_main(env: dict) -> int | str | None:
    """Run main() with a clean env, return the exit code."""
    with patch.dict(os.environ, env, clear=True):
        try:
            main()
            return 0
        except SystemExit as exc:
            return exc.code


def _counts_file(tmp: str, *, date: str, count: int) -> str:
    path = Path(tmp) / "counts.json"
    path.write_text(json.dumps({"date": date, "today_count": count, "history": {}}))
    return str(path)


TODAY = datetime.date.today().isoformat()


class TestReadCount(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def test_file_not_found_returns_none(self):
        result = _read_count("/nonexistent/path/counts.json")
        self.assertIsNone(result)

    def test_oserror_returns_none(self):
        path = Path(self._tmp.name) / "counts.json"
        path.write_text(json.dumps({"date": TODAY, "today_count": 5, "history": {}}))
        with patch("builtins.open", side_effect=PermissionError("denied")):
            result = _read_count(str(path))
        self.assertIsNone(result)

    def test_json_decode_error_returns_zero_and_warns(self):
        path = Path(self._tmp.name) / "counts.json"
        path.write_text("not valid json {{{")
        with self.assertLogs("reporter", level="WARNING"):
            result = _read_count(str(path))
        self.assertEqual(result, 0)

    def test_non_dict_returns_zero_and_warns(self):
        path = Path(self._tmp.name) / "counts.json"
        path.write_text("[1, 2, 3]")
        with self.assertLogs("reporter", level="WARNING"):
            result = _read_count(str(path))
        self.assertEqual(result, 0)

    def test_stale_date_returns_zero(self):
        # Stale date is expected daily operation (yesterday's file still present at
        # report time); no warning is intentionally emitted for this case.
        path = Path(self._tmp.name) / "counts.json"
        path.write_text(
            json.dumps({"date": "2000-01-01", "today_count": 99, "history": {}})
        )
        result = _read_count(str(path))
        self.assertEqual(result, 0)

    def test_non_int_today_count_returns_zero_and_warns(self):
        path = Path(self._tmp.name) / "counts.json"
        path.write_text(
            json.dumps({"date": TODAY, "today_count": "lots", "history": {}})
        )
        with self.assertLogs("reporter", level="WARNING"):
            result = _read_count(str(path))
        self.assertEqual(result, 0)

    def test_bool_today_count_returns_zero_and_warns(self):
        path = Path(self._tmp.name) / "counts.json"
        path.write_text(json.dumps({"date": TODAY, "today_count": True, "history": {}}))
        with self.assertLogs("reporter", level="WARNING"):
            result = _read_count(str(path))
        self.assertEqual(result, 0)

    def test_negative_today_count_returns_zero_and_warns(self):
        path = Path(self._tmp.name) / "counts.json"
        path.write_text(json.dumps({"date": TODAY, "today_count": -3, "history": {}}))
        with self.assertLogs("reporter", level="WARNING"):
            result = _read_count(str(path))
        self.assertEqual(result, 0)

    def test_todays_count_returned(self):
        path = _counts_file(self._tmp.name, date=TODAY, count=7)
        result = _read_count(path)
        self.assertEqual(result, 7)


class TestMain(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def _env(self, **overrides) -> dict:
        path = _counts_file(self._tmp.name, date=TODAY, count=overrides.pop("count", 5))
        base = {
            "DETECTOR_REPORT_WEBHOOK_URL": "https://example.com/hook",
            "DETECTOR_COUNTS_PATH": path,
            "DETECTOR_REPORT_THRESHOLD": "3",
            "DETECTOR_REPORT_MSG_OK": "OK",
            "DETECTOR_REPORT_MSG_LOW": "Low",
            "DETECTOR_REPORT_MSG_ZERO": "Zero",
        }
        base.update(overrides)
        return base

    def test_no_webhook_url_exits_0_and_warns(self):
        with self.assertLogs("reporter", level="WARNING"):
            code = _run_main({"DETECTOR_REPORT_WEBHOOK_URL": ""})
        self.assertEqual(code, 0)

    def test_missing_counts_path_env_exits_1(self):
        env = self._env()
        del env["DETECTOR_COUNTS_PATH"]
        code = _run_main(env)
        self.assertEqual(code, 1)

    def test_invalid_threshold_warns_and_continues(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__ = lambda s: s
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            with self.assertLogs("reporter", level="WARNING") as cm:
                code = _run_main(self._env(DETECTOR_REPORT_THRESHOLD="bad", count=5))
        self.assertEqual(code, 0)
        self.assertTrue(any("DETECTOR_REPORT_THRESHOLD" in m for m in cm.output))

    def test_count_zero_sends_msg_zero(self):
        captured = []
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__ = lambda s: s
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            mock_open.side_effect = lambda req, timeout: captured.append(
                req
            ) or io.BytesIO(b"")
            _run_main(self._env(count=0))
        self.assertEqual(len(captured), 1)
        body = json.loads(captured[0].data)
        self.assertEqual(body["text"], "Zero")

    def test_count_below_threshold_sends_msg_low(self):
        captured = []
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = lambda req, timeout: captured.append(
                req
            ) or io.BytesIO(b"")
            _run_main(self._env(count=1, DETECTOR_REPORT_THRESHOLD="3"))
        self.assertEqual(len(captured), 1)
        body = json.loads(captured[0].data)
        self.assertEqual(body["text"], "Low")

    def test_count_at_threshold_sends_msg_ok(self):
        captured = []
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = lambda req, timeout: captured.append(
                req
            ) or io.BytesIO(b"")
            _run_main(self._env(count=3, DETECTOR_REPORT_THRESHOLD="3"))
        self.assertEqual(len(captured), 1)
        body = json.loads(captured[0].data)
        self.assertEqual(body["text"], "OK")

    def test_count_token_interpolated(self):
        captured = []
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = lambda req, timeout: captured.append(
                req
            ) or io.BytesIO(b"")
            _run_main(self._env(count=42, DETECTOR_REPORT_MSG_OK="count={count}"))
        self.assertEqual(len(captured), 1)
        body = json.loads(captured[0].data)
        self.assertEqual(body["text"], "count=42")

    def test_bad_template_exits_1(self):
        with self.assertLogs("reporter", level="ERROR"):
            code = _run_main(self._env(count=5, DETECTOR_REPORT_MSG_OK="{unknown_key}"))
        self.assertEqual(code, 1)

    def test_counts_file_not_found_exits_0_no_post(self):
        env = self._env()
        env["DETECTOR_COUNTS_PATH"] = "/nonexistent/counts.json"
        with patch("urllib.request.urlopen") as mock_open:
            code = _run_main(env)
        mock_open.assert_not_called()
        self.assertEqual(code, 0)


class TestPost(unittest.TestCase):
    URL = "https://example.com/hook"

    def test_success_no_exception(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__ = lambda s: s
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            _post(self.URL, "hello")  # must not raise

    def test_http_error_exits_1(self):
        headers = http.client.HTTPMessage()
        err = urllib.error.HTTPError(
            self.URL, 500, "Server Error", headers, io.BytesIO(b"oops")
        )
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertLogs("reporter", level="ERROR"):
                with self.assertRaises(SystemExit) as ctx:
                    _post(self.URL, "hello")
        self.assertEqual(ctx.exception.code, 1)

    def test_url_error_exits_1(self):
        err = urllib.error.URLError("connection refused")
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertLogs("reporter", level="ERROR"):
                with self.assertRaises(SystemExit) as ctx:
                    _post(self.URL, "hello")
        self.assertEqual(ctx.exception.code, 1)

    def test_generic_exception_exits_1(self):
        with patch("urllib.request.urlopen", side_effect=RuntimeError("boom")):
            with self.assertLogs("reporter", level="ERROR"):
                with self.assertRaises(SystemExit) as ctx:
                    _post(self.URL, "hello")
        self.assertEqual(ctx.exception.code, 1)

    def test_post_sends_json_content_type(self):
        captured = []
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = lambda req, timeout: captured.append(
                req
            ) or io.BytesIO(b"")
            _post(self.URL, "hello")
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].get_header("Content-type"), "application/json")

    def test_post_body_is_json_text(self):
        captured = []
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = lambda req, timeout: captured.append(
                req
            ) or io.BytesIO(b"")
            _post(self.URL, "my message")
        self.assertEqual(len(captured), 1)
        self.assertEqual(json.loads(captured[0].data), {"text": "my message"})


if __name__ == "__main__":
    unittest.main()
