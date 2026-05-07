<!-- spellchecker: ignore classmethod configparser dataclasses pathlib -->

<!-- spellchecker: ignore setdefault setmode signum -->

# Implementation Notes — detector-core

## Python module layout

```text
detector.py
  GpioPort          Protocol (runtime_checkable)
  RpiGpioPort       production adapter, lazy RPi.GPIO import in __init__
  Config            dataclass, Config.from_file(path) reads INI, falls back to defaults
  BeamDetector      main class
  main()            entry point
```

## GpioPort Protocol

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class GpioPort(Protocol):
    def read(self) -> bool: ...    # True = beam broken (HIGH)
    def cleanup(self) -> None: ...
```

## RpiGpioPort

Lazy import avoids ImportError on non-Pi machines:

```python
class RpiGpioPort:
    def __init__(self, pin: int) -> None:
        import RPi.GPIO as GPIO        # lazy — not available on dev machine
        self._gpio = GPIO
        self._pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self) -> bool:
        return bool(self._gpio.input(self._pin))

    def cleanup(self) -> None:
        self._gpio.cleanup()
```

## Config dataclass

```python
from dataclasses import dataclass, field
from pathlib import Path
import configparser

@dataclass
class Config:
    gpio_pin: int = 17
    poll_interval_s: float = 0.05
    history_retention_days: int = 14
    test_mode_grace_period_s: int = 1800
    counts_path: Path = Path("/var/lib/beam_detector/counts.json")
    state_path: Path = Path("/run/beam_detector/state.json")
    test_mode_sentinel: Path = Path("/run/beam_detector/test_mode")

    @classmethod
    def from_file(cls, path: str = "/etc/beam_detector/config.ini") -> "Config":
        cp = configparser.ConfigParser()
        cp.read(path)   # silently no-ops if missing — tests need no filesystem setup
        s = cp["detector"] if "detector" in cp else {}
        return cls(
            gpio_pin=int(s.get("gpio_pin", 17)),
            poll_interval_s=float(s.get("poll_interval_s", 0.05)),
            history_retention_days=int(s.get("history_retention_days", 14)),
            test_mode_grace_period_s=int(s.get("test_mode_grace_period_s", 1800)),
            counts_path=Path(s.get("counts_path", "/var/lib/beam_detector/counts.json")),
            state_path=Path(s.get("state_path", "/run/beam_detector/state.json")),
            test_mode_sentinel=Path(s.get("test_mode_sentinel", "/run/beam_detector/test_mode")),
        )
```

## BeamDetector skeleton

```python
class BeamDetector:
    def __init__(self, config: Config, gpio_port: GpioPort) -> None:
        self._cfg = config
        self._gpio = gpio_port
        self._today_count: int = 0
        self._current_date: datetime.date = datetime.date.today()
        self._last_pin_state: bool = False
        self._test_mode_entered_at: float | None = None
        self._history: dict[str, int] = {}
        self._running: bool = False
        self._load()

    def tick(self) -> None:
        self._maybe_roll_day()
        self._maybe_revert_test_mode()
        current_state = self._gpio.read()
        if current_state and not self._last_pin_state:   # rising edge only
            self._on_break()
        self._last_pin_state = current_state
        self._write_state()

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        self._running = True
        while self._running:
            self.tick()
            time.sleep(self._cfg.poll_interval_s)
        self._gpio.cleanup()

    def _handle_signal(self, signum, frame) -> None:
        self._running = False
```

## counts.json structure

Written to `/var/lib/beam_detector/counts.json` on break events and midnight resets only.

```json
{
  "date": "2026-05-03",
  "today_count": 7,
  "history": {
    "2026-05-02": 12,
    "2026-05-01": 9
  }
}
```

On load: if `"date"` ≠ today, `today_count` is NOT restored (counter starts at 0).

## state.json structure

Written to `/run/beam_detector/state.json` (tmpfs) on **every tick** (~20/s). Atomic write: write to `state.json.tmp`, then `os.replace()`.

```json
{"beam_broken": false, "today_count": 7, "test_mode": false}
```

Atomic write pattern:

```python
def _write_state(self) -> None:
    payload = json.dumps({
        "beam_broken": self._last_pin_state,
        "today_count": self._today_count,
        "test_mode": self._cfg.test_mode_sentinel.exists(),
    })
    tmp = self._cfg.state_path.with_suffix(".tmp")
    tmp.write_text(payload)
    os.replace(tmp, self._cfg.state_path)
```

## Test setup — mocking RPi.GPIO

Inject stub modules before importing detector, so `RpiGpioPort.__init__` never fires:

```python
import sys
sys.modules.setdefault("RPi", type(sys)("RPi"))
sys.modules.setdefault("RPi.GPIO", type(sys)("RPi.GPIO"))

sys.path.insert(0, str(Path(__file__).parent.parent))
from detector import BeamDetector, Config, GpioPort


class FakeGpioPort:
    def __init__(self, state: bool = False) -> None:
        self.state = state
        self.cleaned_up = False

    def read(self) -> bool:
        return self.state

    def cleanup(self) -> None:
        self.cleaned_up = True
```

## Test helper pattern

All tests use a `tempfile.TemporaryDirectory` for `counts_path` and `state_path` so no filesystem cleanup is needed:

```python
class TestBreakCounting(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        cfg = Config(
            counts_path=Path(self._tmp.name) / "counts.json",
            state_path=Path(self._tmp.name) / "state.json",
            test_mode_sentinel=Path(self._tmp.name) / "test_mode",
        )
        self._gpio = FakeGpioPort()
        self._det = BeamDetector(cfg, self._gpio)

    def tearDown(self):
        self._tmp.cleanup()
```
