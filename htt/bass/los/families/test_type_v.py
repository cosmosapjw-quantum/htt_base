"""Tests for the Type V (open hyperbolic) kernel."""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import type_i_constants, type_v_constants
from bass.los.families.type_v import (
    CHART_METADATA,
    KERNEL,
    translate_native_to_storage,
    translate_storage_to_native,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import (
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    register_family_kernel,
)


def test_chart_metadata_constant():
    assert CHART_METADATA == "open_chart"


@pytest.mark.parametrize(
    "native,storage",
    [
        (("mu_open", CHART_METADATA, "scalar"), "m0"),
        (("mu_open", CHART_METADATA, "tensor_plus"), "m+2"),
        (("mu_open", CHART_METADATA, "tensor_minus"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


def test_translator_rejects_missing_open_chart_metadata():
    with pytest.raises(ValueError, match="chart metadata tag"):
        translate_native_to_storage(("mu_open", "closed_chart", "scalar"))


def test_translator_rejects_wrong_prefix():
    with pytest.raises(ValueError, match="mu_open"):
        translate_native_to_storage(("mu_hyp", CHART_METADATA, "scalar"))


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+3")


ETA = np.linspace(40.0, 420.0, 65)
K = np.array([0.05, 0.08, 0.12])
ELL_MAX = 6


def _vis(eta: float) -> float:
    return float(np.exp(-0.5 * ((eta - 220.0) / 35.0) ** 2))


def _src(eta: float, k: float) -> dict[str, float]:
    env = float(np.exp(-0.5 * ((eta - 210.0) / 40.0) ** 2))
    return {
        "temperature": env * (1.0 + 0.1 * k),
        "temperature_anisotropy": 0.2 * env,
        "polarization": 0.35 * env,
        "b_mode": 0.0,
    }


@pytest.fixture(autouse=True)
def _clean_dispatch():
    snapshot = dict(_TRANSPORT_DISPATCH)
    _TRANSPORT_DISPATCH.clear()
    yield
    _TRANSPORT_DISPATCH.clear()
    _TRANSPORT_DISPATCH.update(snapshot)


def test_kernel_rejects_non_type_v():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_records_open_chart():
    bundle = KERNEL.build_transport_bundle(
        structure=type_v_constants(a_twist=1.0e-3),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["chart_metadata"] == "open_chart"
    assert md["chart"] == "hyperbolic_open_chart"
    assert "no_hidden_flrw_import_without_open_chart_metadata" in md["forbidden_shortcut_tracked"]


def test_residuals_pass_in_small_a_limit():
    bundle = KERNEL.build_transport_bundle(
        structure=type_v_constants(a_twist=1.0e-6),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["label_translator_roundtrip"] == 0.0
    assert r["seed_regularity"] < 1.0e-10
    assert r["open_anchor_limit"] < KERNEL.tolerance_open_anchor_limit


def test_residual_pack_passes():
    bundle = KERNEL.build_transport_bundle(
        structure=type_v_constants(a_twist=1.0e-6),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "V"


def test_registered_type_v_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_v_constants(a_twist=1.0e-3),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_v"
