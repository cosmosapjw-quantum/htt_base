"""HTT-P0-ZOA20 regression sweep (INDEPENDENT_TRACKS_PLAN §2.5).

Guards against reappearance of the `FLRW_tilt_zoa20_mean` / `zoa20_mean`
symbols in any htt-production code path, and checks the 3-tier constants
module.
"""
from __future__ import annotations

from pathlib import Path

from htt.core.constants import (
    OPERATIONAL_DEFAULT_ZOA_HALF_ANGLE_DEG,
    PRODUCTION_DEFAULT_AXIS,
    RECOMMENDED_ZOA_HALF_ANGLE_DEG,
)


_HTT_ROOT = Path(__file__).resolve().parent.parent / "htt"
# Scan every .py file under htt/htt/ *except* the constants definition itself
# and historical/test files. Any production appearance of the forbidden symbol
# trips the guard.
_FORBIDDEN_TOKENS = ("zoa20_mean", "FLRW_tilt_zoa20")


def test_recommended_and_operational_defaults_present():
    assert RECOMMENDED_ZOA_HALF_ANGLE_DEG == 20.0
    assert OPERATIONAL_DEFAULT_ZOA_HALF_ANGLE_DEG == 20.0


def test_production_default_axis_must_remain_none():
    """The production path MUST NOT carry a global default axis."""
    assert PRODUCTION_DEFAULT_AXIS is None


def test_no_forbidden_zoa20_tokens_in_htt_production():
    """Sweep the htt package for legacy diagnostic-default symbols.

    Passing this test is the §2.5 gate: ``grep -r zoa20_mean bass_py/htt/
    | grep -v diagnostic|historical|test_`` must yield zero hits.
    """
    # Exempt the constants module itself — it names the forbidden tokens
    # in its own docstring so this guard knows what to watch for.
    _EXEMPT = {"constants.py"}
    hits = []
    for py in _HTT_ROOT.rglob("*.py"):
        if py.name.startswith("test_") or py.name in _EXEMPT:
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(tok in line for tok in _FORBIDDEN_TOKENS):
                if ("# diagnostic" in line) or ("# historical" in line):
                    continue
                hits.append(f"{py.relative_to(_HTT_ROOT.parent)}:{line_no}: {line.strip()}")
    assert hits == [], (
        "Forbidden zoa20/FLRW_tilt_zoa20 tokens found in htt production code:\n"
        + "\n".join(hits)
    )
