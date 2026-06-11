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

import pytest

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

if (_ROOT / "workspace").is_dir() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.optional_dependencies import (  # noqa: E402
    OPTIONAL_DEPENDENCY_MARKERS as COMMON_OPTIONAL_DEPENDENCY_MARKERS,
    dependency_statuses,
)

_OPTIONAL_DEPENDENCY_MARKERS = COMMON_OPTIONAL_DEPENDENCY_MARKERS


def _dependency_available(module_name: str) -> bool:
    statuses = dependency_statuses()
    by_import_name = {status.import_name: status for status in statuses}
    return by_import_name[module_name].available


def pytest_collection_modifyitems(config, items):
    """Skip marked optional-dependency tests with explicit dependency reasons."""
    for marker_name, module_name in _OPTIONAL_DEPENDENCY_MARKERS.items():
        if _dependency_available(module_name):
            continue
        skip_marker = pytest.mark.skip(
            reason=(
                f"optional dependency '{module_name}' not installed; "
                f"install it to run tests marked {marker_name}"
            )
        )
        for item in items:
            if item.get_closest_marker(marker_name):
                item.add_marker(skip_marker)
