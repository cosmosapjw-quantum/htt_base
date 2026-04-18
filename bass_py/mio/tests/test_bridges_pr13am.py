"""MIO-BRIDGES-01 (W6D6) — PR13AM re-export integration tests.

Plan §12.5 (option A): preserve the `htt.PR13AM_te_sign_d1d3_bridge`
import path and expose an identical handle via `mio.bridges`.

These tests assert both paths resolve to the same module object and
that the `__mio_owned__` / `__mio_rationale__` ownership tags survive
the re-export.
"""
from __future__ import annotations

import importlib


def test_pr13am_reachable_via_mio_bridges():
    import mio.bridges as bridges

    assert hasattr(bridges, "PR13AM_te_sign_d1d3_bridge")


def test_both_import_paths_point_to_same_module():
    """`htt.PR13AM_*` and `mio.bridges.PR13AM_*` must alias the same module."""
    from htt import PR13AM_te_sign_d1d3_bridge as htt_module
    from mio.bridges import PR13AM_te_sign_d1d3_bridge as bridge_module

    assert htt_module is bridge_module, (
        "mio.bridges re-export produced a divergent module — MIO-BRIDGES-01 "
        "option A requires semantic re-export, not a copy."
    )


def test_mio_ownership_flags_visible_through_bridge():
    """The `__mio_owned__` / `__mio_rationale__` tags must survive re-export."""
    from mio.bridges import PR13AM_te_sign_d1d3_bridge as bridge_module

    assert getattr(bridge_module, "__mio_owned__", False) is True
    assert isinstance(getattr(bridge_module, "__mio_rationale__", None), str)
    assert "model-independent" in bridge_module.__mio_rationale__.lower()


def test_bridge_exports_existing_pr13am_api():
    """The re-exported module must still carry PR13AM's public helpers."""
    from mio.bridges import PR13AM_te_sign_d1d3_bridge as bridge_module

    assert hasattr(bridge_module, "_mio_artifact_name")
    assert callable(bridge_module._mio_artifact_name)
    name = bridge_module._mio_artifact_name("pr13am_te_sign", version=2)
    assert name.startswith("mio_"), f"_mio_artifact_name regression: {name!r}"


def test_mio_bridges_all_attribute_advertises_pr13am():
    module = importlib.import_module("mio.bridges")
    assert "PR13AM_te_sign_d1d3_bridge" in module.__all__
