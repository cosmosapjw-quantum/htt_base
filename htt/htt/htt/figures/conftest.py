"""HTT-STAB conftest — ensure htt figures collect under pytest.

INDEPENDENT_TRACKS_PLAN.md §3.4 — the figure scripts historically used
sys.path.insert tricks (pointing at absolute paths like `/mnt/project` or
`workspace/` that only exist in the original author's environment). Under
pytest's collection, those inserts are evaluated at import time and silently
mutate sys.path in ways that interfere with subsequent imports.

This conftest provides three stability guarantees:

  1. **HTT-FIG-SHIM** (INDEPENDENT_TRACKS_PLAN v1.2 §19.2). The figure
     scripts top-level-import `plot_style` and `bounds`, which physically
     live at `htt/core/plot_style.py` and `htt/core/bounds.py`. We prepend
     `htt/core/` to sys.path so those imports resolve under pytest
     without the legacy `/mnt/project` hack.
  2. A skip-marker fixture `figures_skip_if_no_mio` lets individual figure
     scripts (if they are ever promoted to tests) declare their dependency
     on the external `mio/`, `workspace/`, or `/mnt/project` roots cleanly.
  3. Setting `htt.egg-info`-based import resolution takes precedence: htt
     is already installed editable, so figures can simply ``from htt.core
     import ...`` without any sys.path poking. This conftest documents that
     intent and gives a single place to add future shims if needed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

# HTT-FIG-SHIM: top-level `plot_style` / `bounds` → `htt/core/*` resolution.
_CORE = Path(__file__).resolve().parent.parent / "core"
if _CORE.is_dir() and str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

# HTT-STAB W8D6: wire HTT_PIPELINE_OUTDIR to the repo-local synthetic
# fixture directory so figure scripts that load pipeline JSONs from the
# legacy '/mnt/user-data/outputs' path can find stubs under pytest.
# The stubs at bass_py/htt/tests/fixtures/pipeline_outputs/ provide
# schema-matching payloads for:
#   FLRW_tilt_results.json (fig_evidence_decomposition),
#   robustness_sweeps_integrated.json (fig_channel_ablation_heatmap).
# The env var is only set if not already defined, so production runs
# with an explicit HTT_PIPELINE_OUTDIR override are untouched.
_PIPELINE_FIXTURES = (
    Path(__file__).resolve().parent.parent.parent
    / "tests" / "fixtures" / "pipeline_outputs"
)
if _PIPELINE_FIXTURES.is_dir() and not os.environ.get("HTT_PIPELINE_OUTDIR"):
    os.environ["HTT_PIPELINE_OUTDIR"] = str(_PIPELINE_FIXTURES)


_EXTERNAL_ROOTS = {
    "mnt_project": Path("/mnt/project"),
    "workspace": Path(__file__).resolve().parent.parent.parent.parent / "workspace",
    "mio": Path(__file__).resolve().parent.parent.parent.parent / "mio",
}


@pytest.fixture(scope="session")
def figures_external_roots() -> dict[str, Path]:
    """Expose the external-root lookup table for figure-level skip logic."""
    return dict(_EXTERNAL_ROOTS)


@pytest.fixture(scope="session")
def figures_skip_if_no_mio(figures_external_roots):
    """Skip if the `mio/` sibling dir is absent (many figures depend on it)."""
    if not figures_external_roots["mio"].exists():
        pytest.skip("mio/ sibling directory not available in this environment")
