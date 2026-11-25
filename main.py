"""Backward-compatible entry point for `python3 main.py`."""

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_ROOT, "src")
_PKG = os.path.join(_SRC, "friday")

for _path in (_PKG, _SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from friday.app import run_friday  # noqa: E402

if __name__ == "__main__":
    run_friday()
