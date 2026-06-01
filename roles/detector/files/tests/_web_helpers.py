# SPDX-License-Identifier: MIT

"""Shared utilities for web module tests."""

import importlib
import os
import sys
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
