"""Tests for the Type IV (solvable-group) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import type_i_constants, type_iv_constants
from bass.los.families.type_iv import (
    CHART_ORDER,
    KERNEL,
    edge_anisotropy_residual,
    solvable_seed_amplitude,
    solvable_seed_norm_residual,
    translate_native_to_storage,
    translate_storage_to_native,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import (
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    register_family_kernel,
)


def test_chart_order_constant():
    assert CHART_ORDER == "n3_dominated_then_a_twist"


@pytest.mark.parametrize(
    "native,storage",
    [
        (("mu_solv", CHART_ORDER, "scalar"), "m0"),
        (("mu_solv", CHART_ORDER, "tensor_plus"), "m+2"),
        (("mu_solv", CHART_ORDER, "tensor_minus"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


def test_translator_rejects_tampered_chart_order():
    with pytest.raises(ValueError, match="chart_order"):
        translate_native_to_storage(("mu_solv", "a_twist_dominated_then_n3", "scalar"))


def test_translator_rejects_wrong_prefix():
    with pytest.raises(ValueError, match="mu_solv"):
        translate_native_to_storage(("mu_open", CHART_ORDER, "scalar"))


def test_seed_amplitude_positive():
    assert solvable_seed_amplitude(1.0) > 0.0


def test_seed_amplitude_rejects_non_positive():
    with pytest.raises(ValueError, match="L must be > 0"):
        solvable_seed_amplitude(0.0)


def test_seed_norm_residual_under_quadrature_precision():
    assert solvable_seed_norm_residual(1.0, n_samples=256) < 1.0e-8


def test_edge_anisotropy_residual_equals_one_for_peaked_profile():
    # Interior peak of r·e^{-r/L} is at r = L where ψ(L) = ψ_max.
    r = edge_anisotropy_residual(1.0)
    assert math.isclose(r, 1.0, rel_tol=1e-12)


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


def test_kernel_rejects_non_type_iv():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_records_no_flrw_limit():
    bundle = KERNEL.build_transport_bundle(
        structure=type_iv_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["no_flrw_limit"] is True  # Type IV forbids FLRW reduction
    assert md["chart_order"] == CHART_ORDER
    for shortcut in ("no_isotropic_radial_reduction", "no_chart_swap_without_translator_update"):
        assert shortcut in md["forbidden_shortcut_tracked"]


def test_residuals_pass():
    bundle = KERNEL.build_transport_bundle(
        structure=type_iv_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["chart_order"] == 0.0
    assert r["seed_regularity"] < 1.0e-8
    assert r["edge_anisotropy"] < KERNEL.tolerance_edge_anisotropy


def test_residual_pack_passes():
    bundle = KERNEL.build_transport_bundle(
        structure=type_iv_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "IV"


def test_registered_type_iv_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_iv_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_iv"
