"""FIG-MIO-SKIP-GATE — MIO figure-skip auto-activation regression.

INDEPENDENT_TRACKS_PLAN v1.2 §19.7 (Week 6 Day 1).

Purpose: once MIO-BOOT-01 lands, `import mio` must succeed so that any
figure-smoke skip keyed on `No module named 'mio'` is driven by the
figure's *own* downstream dependency (e.g. v2-era `mio.core` /
`mio.reporting` submodules that this v3 skeleton does not carry) —
NOT by the package root itself being unregistered.

This test asserts the root import never fails. If it does, MIO-BOOT-01
has regressed and every figure using `from mio.X` will silently skip
for the wrong reason.
"""
from __future__ import annotations

import importlib


def test_figures_mio_skip_should_activate_after_mio_boot():
    """`import mio` must succeed — gates FIG-MIO-SKIP-GATE (plan §19.7)."""
    mod = importlib.import_module("mio")
    assert hasattr(mod, "__version__"), (
        "mio package root missing __version__ — MIO-BOOT-01 regression."
    )


def test_mio_boot_subpackages_do_not_raise_on_import():
    """Each §12.2 subpackage must import without raising."""
    for name in (
        "mio.coherence",
        "mio.extraction",
        "mio.tension",
        "mio.decomposition",
        "mio.diagnostics",
        "mio.interface",
        "mio.bridges",
    ):
        importlib.import_module(name)
