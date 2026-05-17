# Pi Flask Implementation Hints

See [specs/pi-ha-status/spec.md](../specs/pi-ha-status/spec.md) and
[design.md](../design.md).

## Module-level state

```python
import random
import threading

HA_JITTER_MAX_ADD_S = int(os.environ.get("DETECTOR_HA_JITTER_MAX_ADD_S", 2700))
HA_THRESHOLD = int(os.environ.get("DETECTOR_REPORT_THRESHOLD", 1))

_ha_ok = False
_ha_lock = threading.Lock()
_ha_timer: threading.Timer | None = None

def _set_ha_ok(value: bool) -> None:
    global _ha_ok
    with _ha_lock:
        _ha_ok = value
```

## Single-fire timer guard

`threading.Timer` has no built-in `mode: single`. Guard it explicitly:

```python
def _maybe_start_jitter_timer() -> None:
    global _ha_timer
    if _ha_timer is not None and _ha_timer.is_alive():
        return  # timer already pending — ignore subsequent crossings
    delay = 900 + random.random() * HA_JITTER_MAX_ADD_S
    _ha_timer = threading.Timer(delay, lambda: _set_ha_ok(True))
    _ha_timer.daemon = True
    _ha_timer.start()
```

## Background watcher thread

```python
def _watch_ha_state() -> None:
    last_crossed = False
    while True:
        try:
            count, _ = _read_counts()
            crossed = count >= HA_THRESHOLD
            if crossed and not last_crossed:
                _maybe_start_jitter_timer()
            elif not crossed and last_crossed:
                _set_ha_ok(False)  # midnight reset — no jitter
            last_crossed = crossed
        except Exception as exc:
            _log.warning("HA watcher error: %s", exc)
        time.sleep(1)

# Start at module load (before first request):
threading.Thread(target=_watch_ha_state, daemon=True).start()
```

## Endpoint

```python
@app.get("/home-assistant")
def home_assistant():
    with _ha_lock:
        state = "ok" if _ha_ok else "not_ok"
    return {"state": state}
```

## Notes

- `DETECTOR_REPORT_THRESHOLD` default is `"1"` — matches `reporter.py`.
- The watcher detects midnight rollover implicitly: when `_read_counts()` returns
  0 for a new day, `crossed` becomes False and `_set_ha_ok(False)` fires
  immediately (correct — no jitter on reset).
- Mark the watcher thread and timer as `daemon=True` so they don't block process
  shutdown.
