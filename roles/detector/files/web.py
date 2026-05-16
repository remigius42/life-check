# SPDX-License-Identifier: MIT

# spellchecker: ignore noopener noreferrer

import json
import logging
import os
import time
from datetime import date
from pathlib import Path

from flask import Flask, Response, redirect, url_for  # type: ignore[import-untyped]
from waitress import serve  # type: ignore[import-untyped]

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

STATIC_DIR = os.environ.get("DETECTOR_STATIC_DIR", "/opt/beam_detector/static")
STATE_PATH = Path(
    os.environ.get("DETECTOR_STATE_PATH", "/run/beam_detector/state.json")
)
SENTINEL = Path(os.environ.get("DETECTOR_SENTINEL", "/run/beam_detector/test_mode"))
SENTINEL_RESET = Path(
    os.environ.get("DETECTOR_RESET_SENTINEL", "/run/beam_detector/reset_count")
)
COUNTS_PATH = Path(
    os.environ.get("DETECTOR_COUNTS_PATH", "/var/lib/beam_detector/counts.json")
)
PICO_CSS = os.environ.get("DETECTOR_PICO_CSS", "pico-2.1.1.min.css")
PROJECT_VERSION = os.environ.get("DETECTOR_VERSION", "unknown")

app = Flask(__name__, static_folder=STATIC_DIR)


def _read_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except OSError as exc:
        _log.debug("Could not read %s: %s", STATE_PATH, exc)
        return {"beam_broken": False, "today_count": 0, "test_mode": False}
    except json.JSONDecodeError as exc:
        _log.warning("Corrupt state.json: %s", exc)
        return {"beam_broken": False, "today_count": 0, "test_mode": False}


def _read_counts() -> tuple[int, list[tuple[str, int]]]:
    """Read counts.json and return (today_count, sorted_history_list)."""
    try:
        data = json.loads(COUNTS_PATH.read_text())
        history_dict = data.get("history", {})
        # Sort history descending by date (ISO 8601 strings sort correctly)
        history = sorted(history_dict.items(), key=lambda x: x[0], reverse=True)

        if data.get("date") == date.today().isoformat():
            return int(data.get("today_count", 0)), history
        return 0, history
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        _log.warning("Could not read history from %s: %s", COUNTS_PATH, exc)
        return 0, []


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
        time.sleep(0.05)


@app.get("/")
def index():
    state = _read_state()
    today_count, history = _read_counts()
    beam_text = "🔴 BROKEN" if state["beam_broken"] else "🟢 clear"
    mode_text = "TEST" if state["test_mode"] else "NORMAL"
    toggle_action = "/test-mode/disable" if state["test_mode"] else "/test-mode/enable"
    toggle_label = "Disable test mode" if state["test_mode"] else "Enable test mode"

    # Generate history table rows
    history_html = ""
    if history:
        rows = "".join(f"<tr><td>{d}</td><td>{c}</td></tr>" for d, c in history)
        history_html = f"""
        <article id="history">
          <header><h2>History</h2></header>
          <table class="striped">
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Count</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
        </article>"""
    else:
        history_html = """
        <article id="history">
          <header><h2>History</h2></header>
          <p>History unavailable</p>
        </article>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Life Check</title>
  <link rel="stylesheet" href="/static/{PICO_CSS}">
  <style>
    input[type="submit"] {{ width: auto; }}
    footer {{
      margin-top: 2rem;
      border-top: 1px solid var(--pico-muted-border-color);
      padding-top: 1rem;
      font-size: 0.8rem;
      text-align: center;
    }}
    .status-indicator {{ font-size: 1.2rem; }}
  </style>
</head>
<body>
  <main class="container">
    <h1>Life Check</h1>
    <article>
      <header><h2>Current Status</h2></header>
      <p>Beam state: <strong id="beam" class="status-indicator">{beam_text}</strong></p>
      <p>Breaks today: <strong id="count">{today_count}</strong></p>
      <p>Mode: <small id="mode">{mode_text}</small></p>

      <div class="grid">
        <form id="toggle-form" method="post" action="{toggle_action}">
          <input id="toggle" type="submit"
                 value="{toggle_label}" aria-label="Toggle test mode">
        </form>

        <form method="post" action="/reset-count">
          <input id="reset-count" type="submit" class="secondary"
                 value="Reset Today's Count" aria-label="Reset daily count to zero">
        </form>
      </div>

      <p id="status" aria-live="polite"></p>
    </article>

    {history_html}

    <footer>
      <p>
        <a id="github-link" href="https://www.github.com/remigius42/life-check"
           target="_blank" rel="noopener noreferrer">
          View on GitHub
        </a>
        &nbsp;·&nbsp;
        <span id="version">{PROJECT_VERSION}</span>
      </p>
    </footer>
  </main>
  <script>
    const src = new EventSource("/stream");
    src.onmessage = (e) => {{
      try {{
        const s = JSON.parse(e.data);
        const tm = s.test_mode;
        document.getElementById("beam").textContent =
          s.beam_broken ? "🔴 BROKEN" : "🟢 clear";
        document.getElementById("count").textContent = s.today_count;
        document.getElementById("mode").textContent =
          tm ? "TEST" : "NORMAL";
        document.getElementById("toggle").value =
          tm ? "Disable test mode" : "Enable test mode";
        document.getElementById("toggle-form").action =
          tm ? "/test-mode/disable" : "/test-mode/enable";
        document.getElementById("status").textContent = "";
      }} catch (err) {{
        console.error("Failed to parse SSE message:", err);
        document.getElementById("status").textContent =
          "⚠️ Invalid data received";
      }}
    }};
    src.onerror = () => {{
      document.getElementById("status").textContent =
        "⚠️ Connection lost — reconnecting…";
    }};
  </script>
</body>
</html>"""
    return html


@app.get("/stream")
def stream():
    return Response(
        _sse_stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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


@app.post("/reset-count")
def reset_count():
    try:
        SENTINEL_RESET.parent.mkdir(parents=True, exist_ok=True)
        SENTINEL_RESET.touch()
        _log.info("Reset sentinel created")
    except OSError as exc:
        _log.error("Failed to create reset sentinel %s: %s", SENTINEL_RESET, exc)
        return "Internal server error while resetting count", 500
    return redirect(url_for("index"), 303)


if __name__ == "__main__":
    port = int(os.environ.get("DETECTOR_WEB_PORT", 8080))
    serve(app, host="0.0.0.0", port=port, threads=4)
