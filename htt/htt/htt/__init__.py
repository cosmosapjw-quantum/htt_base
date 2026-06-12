"""HTT -- Hubble Tilt Tracker.

Low-z survey ingestion, structured-null families, shared-latent models,
tilt histories, exploratory bridge metadata.
Owner: HTT repo.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if _SRC.is_dir():
    _src_str = str(_SRC)
    if _src_str not in sys.path:
        sys.path.insert(0, _src_str)

__version__ = "0.1.0"
__all__ = [
    "core",
    "nulls",
    "infer",
    "bridge",
    "figures",
    "integration",
    "zoa",
    "direction",
]
