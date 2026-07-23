from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.plugins.registry import PLUGINS, probe_all


def test_plugin_registry_is_optional_and_typed():
    rows = probe_all()
    assert len(rows) == len(PLUGINS)
    assert all(row["track"] in {"I", "II"} for row in rows)
    assert all("available" in row for row in rows)
    assert not any(p.required_for_core for p in PLUGINS)
