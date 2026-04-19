"""HTT figures subpackage -- 22+ figure generation scripts.

Each fig_*.py is a standalone script that generates one publication figure.
They are not imported as library modules — run them directly.

HTT-FIG-SHIM (INDEPENDENT_TRACKS_PLAN v1.2 §19.2). The figure scripts
top-level-import `plot_style` and `bounds`, which physically live at
`htt/core/plot_style.py` and `htt/core/bounds.py`. Prepending `core/`
to sys.path on package import makes those names resolve under both
direct-script execution and pytest parametric collection.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parent.parent / "core"
if _CORE.is_dir() and str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

# HTT-STAB W8D6: wire HTT_PIPELINE_OUTDIR to the repo-local synthetic
# fixture directory so figure scripts that load pipeline JSONs from
# the legacy '/mnt/user-data/outputs' path can find stubs under
# pytest collection.  The env var is only set if not already defined,
# so production runs with an explicit HTT_PIPELINE_OUTDIR override or
# an actual /mnt/user-data/outputs mount point are untouched.
_PIPELINE_FIXTURES = (
    Path(__file__).resolve().parent.parent.parent
    / "tests" / "fixtures" / "pipeline_outputs"
)
if _PIPELINE_FIXTURES.is_dir() and not os.environ.get("HTT_PIPELINE_OUTDIR"):
    os.environ["HTT_PIPELINE_OUTDIR"] = str(_PIPELINE_FIXTURES)
