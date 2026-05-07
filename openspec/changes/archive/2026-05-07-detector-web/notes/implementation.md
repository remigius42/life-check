<!-- spellchecker: ignore pathlib wsgi -->

# Implementation Notes — detector-web

## Flask SSE generator

One route, one generator, no extensions. Note: `static_folder` is configured via env var — see the
[Flask binding](#flask-binding) and [Pico CSS](#pico-css) sections below for the full `Flask(__name__,
static_folder=static_dir)` initialization.

```python
import json
import logging
import os
import time
from pathlib import Path
from flask import Flask, Response, redirect, request

static_dir = os.environ.get("DETECTOR_STATIC_DIR", "/opt/beam_detector/static")
app = Flask(__name__, static_folder=static_dir)
STATE_PATH = Path(os.environ.get("DETECTOR_STATE_PATH", "/run/beam_detector/state.json"))
SENTINEL   = Path(os.environ.get("DETECTOR_SENTINEL",   "/run/beam_detector/test_mode"))

_log = logging.getLogger(__name__)

def _read_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except OSError as exc:
        _log.debug("Could not read %s: %s", STATE_PATH, exc)
        return {"beam_broken": False, "today_count": 0, "test_mode": False}
    except json.JSONDecodeError as exc:
        _log.warning("Corrupt state.json: %s", exc)
        return {"beam_broken": False, "today_count": 0, "test_mode": False}

def _sse_stream():
    last = None
    while True:
        state = _read_state()
        if state != last:
            try:
                yield f"data: {json.dumps(state)}\n\n"
            except GeneratorExit:
                return
            last = state
        time.sleep(0.05)   # match daemon poll interval

@app.get("/stream")
def stream():
    return Response(_sse_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

`X-Accel-Buffering: no` prevents nginx/proxy buffering if one is ever added in front.

## Test mode toggle endpoints

Return 303 redirect to `GET /` — works with or without JS. When JS is enabled the EventSource stream also updates the DOM; the full page reload from the redirect is redundant but harmless. When JS is disabled the redirect is the only mechanism that reloads the page.

`url_for("index")` resolves because `GET /` is mapped to `def index()` in the same file. Explicit 303 is required — Flask's `redirect()` defaults to 302, which is semantically incorrect for POST-Redirect-GET:

```python
from flask import redirect, url_for

@app.post("/test-mode/enable")
def enable_test_mode():
    try:
        SENTINEL.parent.mkdir(parents=True, exist_ok=True)
        SENTINEL.touch()
        _log.info("Test mode enabled")
    except OSError as exc:
        _log.error("Failed to create sentinel %s: %s", SENTINEL, exc)
        return "Internal server error while enabling test mode", 500
    return redirect(url_for("index"), 303)

@app.post("/test-mode/disable")
def disable_test_mode():
    try:
        SENTINEL.unlink(missing_ok=True)
        _log.info("Test mode disabled")
    except OSError as exc:
        _log.error("Failed to remove sentinel %s: %s", SENTINEL, exc)
        return "Internal server error while disabling test mode", 500
    return redirect(url_for("index"), 303)
```

## Vanilla JS EventSource (~10 lines)

No framework. Inline in the HTML page:

```html
<script>
  const src = new EventSource("/stream");
  src.onmessage = (e) => {
    try {
      const s = JSON.parse(e.data);
      document.getElementById("beam").textContent  = s.beam_broken ? "🔴 BROKEN" : "🟢 clear";
      document.getElementById("count").textContent = s.today_count;
      document.getElementById("mode").textContent  = s.test_mode   ? "TEST"      : "NORMAL";
      document.getElementById("toggle").value      = s.test_mode   ? "Disable test mode" : "Enable test mode";
      document.getElementById("toggle-form").action = s.test_mode  ? "/test-mode/disable" : "/test-mode/enable";
      document.getElementById("status").textContent = "";
    } catch (err) {
      console.error("Failed to parse SSE message:", err);
      document.getElementById("status").textContent = "⚠️ Invalid data received";
    }
  };
  src.onerror = () => {
    document.getElementById("status").textContent = "⚠️ Connection lost — reconnecting…";
  };
</script>
```

## Toggle button — plain HTML form, no JS dependency

The toggle still works if JS is disabled (falls back to POST + page reload):

```html
<form id="toggle-form" method="post" action="/test-mode/enable">
  <input id="toggle" type="submit" value="Enable test mode">
</form>
```

JS updates `action` and `value` live via the SSE handler above.

## Passing config to web.py

Read from environment variables set in the systemd unit (`Environment=` lines in `beam-detector-web.service.j2`). `web.py` reads all paths directly from env vars — it does not read the shared INI config. `DETECTOR_COUNTS_PATH` is read for the initial page render (`GET /`); the SSE stream reads `DETECTOR_STATE_PATH`:

```ini
[Service]
User=beam-detector-web
Group=detector
Environment=DETECTOR_STATE_PATH=/run/beam_detector/state.json
Environment=DETECTOR_SENTINEL=/run/beam_detector/test_mode
Environment=DETECTOR_WEB_PORT=8080
Environment=DETECTOR_COUNTS_PATH=/var/lib/beam_detector/counts.json
Environment=DETECTOR_STATIC_DIR=/opt/beam_detector/static
Environment=DETECTOR_PICO_CSS=pico-2.1.1.min.css
```

## Pico CSS

Vendored at `roles/detector/files/static/pico-2.1.1.min.css` (version in filename for cache busting and auditability). Copied to `{{ detector_install_dir }}/static/pico-2.1.1.min.css` by Ansible. Filename passed to `web.py` via `DETECTOR_PICO_CSS` env var in the systemd unit. The fallback in the `os.environ.get` call matches the vendored filename — in production the systemd unit always overrides it via `DETECTOR_PICO_CSS`.

```python
pico_css = os.environ.get("DETECTOR_PICO_CSS", "pico-2.1.1.min.css")
```

Link in the page `<head>` constructed dynamically:

```python
# inside the HTML f-string or format call:
f'<link rel="stylesheet" href="/static/{pico_css}">'
```

Semantic elements that get automatic styling relevant to this UI:
- `<main>` — centered, max-width container with padding
- `<article>` — card with border, padding, border-radius
- `<button type="submit">` — styled primary button
- `<small>` — muted text, useful for the mode badge

Flask static folder must point to `{{ detector_install_dir }}/static/` via env var:

```python
static_dir = os.environ.get("DETECTOR_STATIC_DIR", "/opt/beam_detector/static")
app = Flask(__name__, static_folder=static_dir)
```

Systemd unit env vars (in `beam-detector-web.service.j2`):

```ini
Environment=DETECTOR_STATIC_DIR={{ detector_install_dir }}/static
Environment=DETECTOR_PICO_CSS=pico-{{ detector_pico_version }}.min.css
```

## Flask binding / WSGI server

Deployment uses **Waitress** (`python3-waitress` apt package — no pip required, consistent with the apt-only constraint):

```python
from waitress import serve

if __name__ == "__main__":
    port = int(os.environ.get("DETECTOR_WEB_PORT", 8080))
    serve(app, host="0.0.0.0", port=port, threads=4)
```

Waitress is multi-threaded out of the box — the SSE stream and the toggle POST are served concurrently without any extra flag. The systemd unit invokes `python3 web.py` directly.

`threads=4` is sufficient for a single-user LAN deployment: one thread holds the SSE stream, the others serve page loads and toggle POSTs.

For local development `app.run(host="0.0.0.0", port=port, threaded=True)` can be used instead, but Waitress works fine locally too.
