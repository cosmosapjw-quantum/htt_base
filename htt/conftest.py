"""conftest.py — repo root.

Placed at the root so pytest's auto-detection treats this directory as the
project rootdir. The package structure itself (bass/, tsc/ with __init__.py
at every level) takes care of `from bass.X.Y import Z` and `from tsc.X`
imports.

For the `src/common/` layout introduced under COMMON-A (INDEPENDENT_TRACKS_
PLAN.md §2.6), we additionally prepend `src/` to sys.path so that
`from common.sky_geometry import ...` resolves both under pytest and when
htt production modules import the shared utilities.

For the `workspace/contracts/` layout introduced under WS-BOOT-01
(INDEPENDENT_TRACKS_PLAN.md v1.2 §19.1, Week 5 Day 1), we also prepend
the bass_py root itself so that `from workspace.contracts.htt_to_mio
import PosteriorExportBundle` resolves from htt/mio production paths.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

if (_ROOT / "workspace").is_dir() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
