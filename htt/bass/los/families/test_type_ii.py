"""Tests for the Type II (nil-Heisenberg) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.special import j0, j1, jn_zeros

from bass.background.bianchi_types import (
    type_i_constants,
    type_ii_constants,
)
from bass.los.families.type_ii import (
    KERNEL,
    TypeIIKernel,
    bessel_first_zero_j0,
    nil_seed_amplitude,
    nil_seed_center_residual,
    nil_seed_norm_residual,
    translate_native_to_storage,
    translate_storage_to_native,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import (
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    register_family_kernel,
)


# ----- Translator --------------------------------------------------------


@pytest.mark.parametrize(
    "native,storage",
    [
        (("mu_nil", "scalar", 0), "m0"),
        (("mu_nil", "tensor", "+"), "m+2"),
        (("mu_nil", "tensor", "-"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


def test_translator_rejects_non_nil_prefix():
    with pytest.raises(ValueError, match="mu_nil"):
        translate_native_to_storage(("mu_hyp", "scalar", 0))


def test_translator_rejects_malformed():
    with pytest.raises(ValueError, match="mu_nil"):
        translate_native_to_storage(("mu_nil", "scalar"))


def test_translator_rejects_outside_pstf():
    with pytest.raises(ValueError, match="PSTF storage window"):
        translate_native_to_storage(("mu_nil", "scalar", 1))


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+3")


# ----- Bessel / seed -----------------------------------------------------


def test_bessel_first_zero_agrees_with_scipy():
    assert bessel_first_zero_j0() == float(jn_zeros(0, 1)[0])


def test_seed_amplitude_matches_closed_form():
    L = 1.5
    j01 = bessel_first_zero_j0()
    expected = 1.0 / (math.sqrt(math.pi) * L * abs(j1(j01)))
    assert nil_seed_amplitude(L) == expected


def test_seed_amplitude_rejects_non_positive_width():
    with pytest.raises(ValueError, match="half_width_L must be > 0"):
        nil_seed_amplitude(0.0)


def test_seed_regularity_passes_quadrature_precision():
    assert nil_seed_norm_residual(half_width_L=1.0, n_samples=64) < 1.0e-10


def test_seed_center_residual_is_zero():
    assert nil_seed_center_residual(half_width_L=1.0) == 0.0


# ----- Transport bundle --------------------------------------------------


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


def test_kernel_rejects_non_type_ii():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_records_nil_specifics():
    bundle = KERNEL.build_transport_bundle(
        structure=type_ii_constants(n1=1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["chart"] == "nil_heisenberg"
    assert md["boundary_edge"] == "dirichlet_at_r_equals_L"
    assert md["bessel_first_zero_j0"] == bessel_first_zero_j0()
    for shortcut in ("no_flrw_seed_reuse", "no_implicit_periodic_boundary", "no_unlabeled_branch_choice"):
        assert shortcut in md["forbidden_shortcut_tracked"]


def test_residuals_are_tight():
    bundle = KERNEL.build_transport_bundle(
        structure=type_ii_constants(n1=1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["label_translator_roundtrip"] == 0.0
    assert r["nil_chart_regularity"] == 0.0
    assert r["seed_regularity"] < 1.0e-10


def test_residual_pack_passes_within_tolerance():
    bundle = KERNEL.build_transport_bundle(
        structure=type_ii_constants(n1=1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "II"


def test_registered_type_ii_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_ii_constants(n1=1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_ii"
