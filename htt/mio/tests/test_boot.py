"""mio.tests.test_boot — MIO package boot smoke.

Landed under INDEPENDENT_TRACKS_PLAN v1.2 §12.2 (MIO-BOOT-01,
Week 6 Day 1).

Purpose: assert that `import mio` and each declared subpackage import
without error, so that `bass_py.mio` is wired into the rest of the
monorepo (conftest prepends bass_py root to sys.path; pyproject
`packages.find` includes `mio*`).
"""
from __future__ import annotations

import importlib


_SUBPACKAGES = (
    "mio",
    "mio.core",
    "mio.core.ceiling_families",
    "mio.coherence",
    "mio.extraction",
    "mio.tension",
    "mio.decomposition",
    "mio.diagnostics",
    "mio.reporting",
    "mio.reporting.identified_vs_reporting",
    "mio.interface",
    "mio.interface.mio_certificate",
    "mio.bridges",
    "mio.formalism",
    "mio.formalism.component_breakdown",
    "mio.formalism.departure_bundle",
)


def test_mio_root_importable():
    mod = importlib.import_module("mio")
    assert hasattr(mod, "__version__")


def test_all_mio_subpackages_importable():
    for name in _SUBPACKAGES:
        importlib.import_module(name)


def test_mio_certificate_contract_reachable():
    """Schema contract lives in workspace.contracts — boot should not mask it."""
    from workspace.contracts.mio_certificate import MioCertificate

    assert MioCertificate.__name__ == "MioCertificate"
