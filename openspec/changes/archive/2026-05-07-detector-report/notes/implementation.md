<!-- spellchecker: ignore isinstance isoformat -->

# Implementation Notes — detector-report

## HTTP POST via stdlib only

No pip packages. `urllib.request` handles a JSON POST in ~6 lines:

```python
import json
import logging
import sys
import urllib.error
import urllib.request

def post_webhook(url: str, message: str) -> None:
    body = json.dumps({"text": message}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read(500).decode("utf-8", errors="replace")
        except Exception:
            detail = "<unreadable>"
        logging.error("Webhook HTTP %s for %s: %s", exc.code, url, detail)
        sys.exit(1)
    except urllib.error.URLError as exc:
        logging.error("Webhook request failed for %s: %s", url, exc.reason)
        sys.exit(1)
```

## Message selection logic

Zero check MUST come before threshold check (zero is a special health-alert case):

```python
if count == 0:
    template = msg_zero
elif count < threshold:
    template = msg_low
else:
    template = msg_ok

message = template.format(count=count)
```

## Default message templates

The Ansible defaults (in `roles/detector/defaults/main.yml`) intentionally omit `{count}` for privacy. The examples below show `{count}` to illustrate the interpolation mechanism; they are NOT the actual defaults:

```python
# usage examples — not the actual Ansible defaults
MSG_OK   = "Beam breaks today: {count}\n✅ OK"
MSG_LOW  = "Beam breaks today: {count}\n🚨 breaks under threshold!"
MSG_ZERO = "Beam breaks today: {count}\n⚠️ no breaks today, sensor might be down."
```

`{count}` is the only interpolation token. Use `str.format(count=N)` — not f-strings, so the template can be stored as a plain string in an Ansible variable override.

## counts.json read

Path comes from the `DETECTOR_COUNTS_PATH` environment variable. If the stored `"date"` differs from today, treat count as 0:

```python
import datetime
import json
import logging

def _read_count(counts_path):
    """Return today's count, or None to skip the report."""
    today = datetime.date.today().isoformat()
    try:
        with open(counts_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        logging.warning("counts.json not found at %s; skipping report", counts_path)
        return None
    except OSError as exc:
        logging.warning("Could not read counts.json: %s; skipping report", exc)
        return None
    except json.JSONDecodeError as exc:
        logging.warning("counts.json is not valid JSON: %s; using count=0", exc)
        return 0
    if not isinstance(data, dict):
        logging.warning("counts.json has unexpected structure; using count=0")
        return 0
    if data.get("date") != today:
        return 0
    raw = data.get("today_count")
    if type(raw) is not int:
        logging.warning("today_count is not an integer (%r); using count=0", raw)
        return 0
    if raw < 0:
        logging.warning("today_count is negative (%r); using count=0", raw)
        return 0
    return raw
```

Callers check for `None` to skip the POST entirely (missing file is not the same as a zero-count day):

```python
count = _read_count(counts_path)
if count is None:
    sys.exit(0)
```

## Guard: empty webhook URL

Log a warning and exit 0 if URL is not configured — avoids systemd failed-unit noise, but the skip is still visible in the journal:

```python
if not webhook_url:
    logging.warning("detector_report_webhook_url is not set — skipping")
    sys.exit(0)
```

## Passing config to the reporter

All config is passed via environment variables set in `beam-detector-report.service.j2` (`Environment=` lines). The reporter reads only `os.environ` — it does NOT read `/etc/beam_detector/config.ini` directly. This keeps secrets out of the shared INI file and makes the reporter self-contained.

| env var | Ansible source |
|---|---|
| `DETECTOR_COUNTS_PATH` | `detector_counts_path` |
| `DETECTOR_REPORT_WEBHOOK_URL` | `detector_report_webhook_url` |
| `DETECTOR_REPORT_THRESHOLD` | `detector_report_threshold` |
| `DETECTOR_REPORT_MSG_OK` | `detector_report_msg_ok` |
| `DETECTOR_REPORT_MSG_LOW` | `detector_report_msg_low` |
| `DETECTOR_REPORT_MSG_ZERO` | `detector_report_msg_zero` |
