#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import datetime
import json
import logging
import os
import sys
import urllib.error
import urllib.request

logging.basicConfig(
    stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s"
)
log = logging.getLogger(__name__)


def main():
    webhook_url = os.environ.get("DETECTOR_REPORT_WEBHOOK_URL", "")
    if not webhook_url:
        log.warning("DETECTOR_REPORT_WEBHOOK_URL not set; skipping report")
        sys.exit(0)

    counts_path = os.environ.get("DETECTOR_COUNTS_PATH", "")
    if not counts_path:
        log.error("DETECTOR_COUNTS_PATH not set")
        sys.exit(1)

    threshold_raw = os.environ.get("DETECTOR_REPORT_THRESHOLD", "1")
    try:
        threshold = int(threshold_raw)
    except ValueError:
        log.warning(
            "Could not parse DETECTOR_REPORT_THRESHOLD=%r; using 1", threshold_raw
        )
        threshold = 1

    msg_ok = os.environ.get(
        "DETECTOR_REPORT_MSG_OK", "Beam breaks today: ✅ OK (equal or above threshold)"
    )
    msg_low = os.environ.get(
        "DETECTOR_REPORT_MSG_LOW", "Beam breaks today: 🚨 under threshold"
    )
    msg_zero = os.environ.get(
        "DETECTOR_REPORT_MSG_ZERO",
        "Beam breaks today: 0 ⚠️ no breaks today, sensor might be down.",
    )

    count = _read_count(counts_path)
    if count is None:
        sys.exit(0)

    if count == 0:
        template = msg_zero
    elif count < threshold:
        template = msg_low
    else:
        template = msg_ok

    try:
        message = template.format(count=count)
    except (KeyError, ValueError) as exc:
        log.error("Failed to interpolate message template %r: %s", template, exc)
        sys.exit(1)

    _post(webhook_url, message)


def _read_count(counts_path):
    today = datetime.date.today().isoformat()
    try:
        with open(counts_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        log.warning("counts.json not found at %s; skipping report", counts_path)
        return None
    except OSError as exc:
        log.warning("Could not read counts.json: %s; skipping report", exc)
        return None
    except json.JSONDecodeError as exc:
        log.warning("counts.json is not valid JSON: %s; using count=0", exc)
        return 0

    if not isinstance(data, dict):
        log.warning("counts.json has unexpected structure; using count=0")
        return 0

    if data.get("date") != today:
        return 0

    raw = data.get("today_count")
    if type(raw) is not int:
        log.warning("today_count is not an integer (%r); using count=0", raw)
        return 0
    if raw < 0:
        log.warning("today_count is negative (%r); using count=0", raw)
        return 0

    return raw


def _post(url, message):
    body = json.dumps({"text": message}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except urllib.error.HTTPError as exc:
        try:
            body_preview = exc.read(500).decode(errors="replace")
        except Exception:
            body_preview = ""
        log.error("HTTP %s posting to webhook: %s", exc.code, body_preview)
        sys.exit(1)
    except urllib.error.URLError as exc:
        log.error("URL error posting to webhook: %s", exc.reason)
        sys.exit(1)
    except Exception as exc:
        log.error("Unexpected error posting to webhook: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
