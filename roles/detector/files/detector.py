#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Beam-break detector daemon."""

from __future__ import annotations

import configparser
import datetime
import json
import logging
import os
import signal
import time
import types
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

_log = logging.getLogger(__name__)


@runtime_checkable
class GpioPort(Protocol):
    """Abstraction over a single GPIO input pin. Inject a fake in tests."""

    def read(self) -> bool: ...
    def cleanup(self) -> None: ...


class RpiGpioPort:
    """Production GPIO pin backed by RPi.GPIO (imported lazily so the module
    loads on non-Pi machines for testing)."""

    def __init__(
        self,
        pin: int,
        retries: int = 3,
        _sleep_fn: Callable[[float], None] | None = None,
        _gpio_module: Any = None,
    ) -> None:
        gpio: Any = _gpio_module
        if gpio is None:
            import RPi.GPIO as _rpi_gpio  # lazy — not available on dev machine

            gpio = _rpi_gpio
        self._gpio: Any = gpio
        self._pin = pin
        _sleep: Callable[[float], None] = (
            _sleep_fn if _sleep_fn is not None else time.sleep
        )
        attempts = max(1, retries)
        last_exc: Exception | None = None
        for attempt in range(attempts):
            try:
                gpio.setmode(gpio.BCM)
                gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)
                return
            except Exception as exc:
                last_exc = exc
                _log.error(
                    "GPIO init attempt %d/%d failed: %s", attempt + 1, attempts, exc
                )
                if attempt < attempts - 1:
                    _sleep(1)
        raise RuntimeError(f"GPIO init failed after {attempts} attempts") from last_exc

    def read(self) -> bool:
        return bool(self._gpio.input(self._pin))

    def cleanup(self) -> None:
        self._gpio.cleanup()


@dataclass
class Config:
    """Runtime configuration.

    Defaults must stay in sync with
    roles/detector/defaults/main.yml — the script is deployed verbatim (not as
    a Jinja2 template) so it can be imported and tested without Ansible."""

    gpio_pin: int = 17
    poll_interval_ms: int = 50
    gpio_init_retries: int = 3
    history_retention_days: int = 14
    test_mode_grace_period_s: int = 1800
    counts_path: Path = Path("/var/lib/beam_detector/counts.json")
    state_path: Path = Path("/run/beam_detector/state.json")
    test_mode_sentinel: Path = Path("/run/beam_detector/test_mode")

    @classmethod
    def from_file(cls, path: str = "/etc/beam_detector/config.ini") -> "Config":
        cp = configparser.ConfigParser()
        cp.read(path)  # silently no-ops if missing
        s: Mapping[str, str] = cp["detector"] if "detector" in cp else {}
        d = cls()  # field defaults — single source of truth
        poll_interval_ms = int(s.get("poll_interval_ms", d.poll_interval_ms))
        if poll_interval_ms < 1:
            raise ValueError(f"poll_interval_ms must be >= 1, got {poll_interval_ms}")
        return cls(
            gpio_pin=int(s.get("gpio_pin", d.gpio_pin)),
            poll_interval_ms=poll_interval_ms,
            gpio_init_retries=int(s.get("gpio_init_retries", d.gpio_init_retries)),
            history_retention_days=int(
                s.get("history_retention_days", d.history_retention_days)
            ),
            test_mode_grace_period_s=int(
                s.get("test_mode_grace_period_s", d.test_mode_grace_period_s)
            ),
            counts_path=Path(s.get("counts_path", d.counts_path)),
            state_path=Path(s.get("state_path", d.state_path)),
            test_mode_sentinel=Path(s.get("test_mode_sentinel", d.test_mode_sentinel)),
        )


class BeamDetector:
    """Polling loop that detects rising edges on a GPIO pin, maintains a daily
    break counter, and persists history to counts.json."""

    def __init__(self, config: Config, gpio_port: GpioPort) -> None:
        self._cfg = config
        self._gpio = gpio_port
        self._today_count: int = 0
        self._current_date: datetime.date = datetime.date.today()
        self._pin_state: bool = gpio_port.read()
        self._test_mode_entered_at: float | None = None
        self._history: dict[str, int] = {}
        self._running: bool = False
        self._load()

    def tick(self) -> None:
        self._maybe_roll_day()
        self._maybe_revert_test_mode()
        current_state = self._gpio.read()
        if not current_state and self._pin_state:  # falling edge — beam blocked
            self._on_break()
        self._pin_state = current_state
        self._write_state()

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        self._running = True
        try:
            while self._running:
                self.tick()
                time.sleep(self._cfg.poll_interval_ms / 1000)
        finally:
            self._save()
            self._gpio.cleanup()

    def _handle_signal(
        self, _signum: int, _frame: types.FrameType | None
    ) -> None:  # cspell: ignore signum
        self._running = False

    def _maybe_roll_day(self) -> None:
        today = datetime.date.today()
        if today > self._current_date:
            yesterday_key = self._current_date.isoformat()
            self._history[yesterday_key] = self._today_count
            self._today_count = 0
            self._current_date = today
            self._save()

    def _maybe_revert_test_mode(self) -> None:
        sentinel_exists = self._cfg.test_mode_sentinel.exists()
        if sentinel_exists:
            if self._test_mode_entered_at is None:
                self._test_mode_entered_at = time.monotonic()
            elapsed = time.monotonic() - self._test_mode_entered_at
            if elapsed >= self._cfg.test_mode_grace_period_s:
                try:
                    self._cfg.test_mode_sentinel.unlink()
                    self._test_mode_entered_at = None
                except FileNotFoundError:
                    self._test_mode_entered_at = None
                except OSError as exc:
                    _log.error(
                        "Failed to remove sentinel %s: %s",
                        self._cfg.test_mode_sentinel,
                        exc,
                    )
                    # timer preserved — retry on next tick
        else:
            self._test_mode_entered_at = None

    def _on_break(self) -> None:
        if self._cfg.test_mode_sentinel.exists():
            return
        self._today_count += 1
        self._save()

    def _load(self) -> None:
        try:
            raw = self._cfg.counts_path.read_text()
        except FileNotFoundError:
            return
        except OSError as exc:
            _log.error(
                "Could not read %s: %s — starting fresh", self._cfg.counts_path, exc
            )
            self._rename_bad_counts()
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            _log.error(
                "Corrupt %s: %s — renaming to .bak and starting fresh",
                self._cfg.counts_path,
                exc,
            )
            self._rename_bad_counts()
            return
        today = datetime.date.today().isoformat()
        stored_date = data.get("date")
        try:
            raw_count = int(data.get("today_count", 0))
        except (ValueError, TypeError):
            _log.warning(
                "Non-numeric today_count in %s — using 0", self._cfg.counts_path
            )
            raw_count = 0
        if stored_date == today:
            self._today_count = raw_count
        elif stored_date and stored_date < today:
            self._history[stored_date] = raw_count
        elif stored_date and stored_date > today:
            _log.warning(
                "counts.json has future date %s — discarding today_count", stored_date
            )
        for k, v in data.get("history", {}).items():
            try:
                self._history[k] = int(v)
            except (ValueError, TypeError):
                _log.warning(
                    "Non-numeric history entry %s in %s — skipping",
                    k,
                    self._cfg.counts_path,
                )

    def _rename_bad_counts(self) -> None:
        bak = self._cfg.counts_path.parent / (self._cfg.counts_path.name + ".bak")
        try:
            self._cfg.counts_path.rename(bak)
        except OSError:
            pass

    def _save(self) -> None:
        cutoff = datetime.date.today() - datetime.timedelta(
            days=self._cfg.history_retention_days
        )
        pruned = {k: v for k, v in self._history.items() if k >= cutoff.isoformat()}
        self._history = pruned
        payload = json.dumps(
            {
                "date": self._current_date.isoformat(),
                "today_count": self._today_count,
                "history": self._history,
            },
            indent=2,
        )
        tmp = self._cfg.counts_path.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self._cfg.counts_path)
        except OSError as exc:
            _log.error(
                "Failed to save %s: %s — retaining in-memory state",
                self._cfg.counts_path,
                exc,
            )

    def _write_state(self) -> None:
        payload = json.dumps(
            {
                # NPN open-collector + pull-up: LOW (False) = beam broken,
                # HIGH (True) = beam intact
                "beam_broken": not self._pin_state,
                "today_count": self._today_count,
                "test_mode": self._cfg.test_mode_sentinel.exists(),
            }
        )
        tmp = self._cfg.state_path.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self._cfg.state_path)
        except OSError as exc:
            _log.error("Failed to write %s: %s", self._cfg.state_path, exc)


def main() -> None:
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    parser = argparse.ArgumentParser(description="Beam-break detector daemon")
    parser.add_argument(
        "--config",
        default="/etc/beam_detector/config.ini",
        help="Path to config file (default: /etc/beam_detector/config.ini)",
    )
    args = parser.parse_args()
    cfg = Config.from_file(args.config)
    gpio = RpiGpioPort(cfg.gpio_pin, retries=cfg.gpio_init_retries)
    detector = BeamDetector(cfg, gpio)
    detector.run()


if __name__ == "__main__":
    main()
