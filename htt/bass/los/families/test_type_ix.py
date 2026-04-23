"""Tests for the Type IX (compact SU(2), Wigner-D) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import (
    type_i_constants,
    type_ix_constants,
    type_iv_constants,
)
from bass.los.families.type_ix import (
    KERNEL,
    TypeIXKernel,
    compact_seed_norm_residual,
    translate_native_to_storage,
    translate_storage_to_native,
    wigner_d_j2_unit_amplitude,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import (
    ExactTransportBundle,
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    register_family_kernel,
)


# ----- Label translator --------------------------------------------------


@pytest.mark.parametrize(
    "native,storage",
    [((2, -2, 0), "m-2"), ((2, 0, 0), "m0"), ((2, 2, 0), "m+2")],
)
def test_label_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


@pytest.mark.parametrize(
    "bad_label",
    [(1, 0, 0), (2, 1, 0), (2, -1, 0), (2, 0, 1), (3, 0, 0)],
)
def test_translator_rejects_non_pstf_native(bad_label):
    with pytest.raises(ValueError, match="PSTF"):
        translate_native_to_storage(bad_label)


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+1")


# ----- Compact seed ------------------------------------------------------


def test_wigner_d_j2_unit_amplitude_closed_form():
    assert wigner_d_j2_unit_amplitude() == math.sqrt(5.0 / (8.0 * math.pi ** 2))


def test_compact_seed_norm_residual_is_zero_to_quadrature_precision():
    # J=2, M=N=0 reduces to P_2(cos β). Gauss-Legendre with 48 nodes
    # integrates P_2² exactly up to degree 94; the residual should be
    # machine precision.
    assert compact_seed_norm_residual(n_samples=48) < 1.0e-12


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


def test_kernel_rejects_non_type_ix_structure():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_iv_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_contains_type_ix_specifics():
    bundle = KERNEL.build_transport_bundle(
        structure=type_ix_constants(n=5.0e-3),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert isinstance(bundle, ExactTransportBundle)
    assert bundle.family == "IX"
    md = bundle.metadata
    assert md["chart"] == "wigner_d_compact_chart"
    assert md["storage_order"] == ["m-2", "m0", "m+2"]
    assert md["n_isotropic"] == 5.0e-3
    assert math.isclose(md["su2_amplitude_unit_l2"], wigner_d_j2_unit_amplitude())
    assert math.isclose(md["su2_invariant_volume"], 8.0 * math.pi ** 2)
    assert "residual_values" in md
    assert "no_untracked_compact_basis_reordering" in md["forbidden_shortcut_tracked"]


def test_residuals_pass_in_small_n_limit():
    # n → 0 → isotropic Type IX ≈ Type I.
    bundle = KERNEL.build_transport_bundle(
        structure=type_ix_constants(n=1.0e-6),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["label_translator_roundtrip"] == 0.0
    assert r["seed_regularity"] < 1.0e-12
    assert r["compact_anchor_limit"] < KERNEL.tolerance_anchor_limit


def test_residual_pack_passes_when_residuals_within_tolerance():
    bundle = KERNEL.build_transport_bundle(
        structure=type_ix_constants(n=1.0e-6),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "IX"
    # Required residuals from _FAMILY_RESIDUALS["IX"] must all be covered.
    for label in pack.required_residuals:
        assert label in pack.residual_values


def test_residual_pack_fails_when_anchor_limit_misaligned():
    """Synthesize a failure by shrinking the tolerance below the residual."""
    bundle = KERNEL.build_transport_bundle(
        structure=type_ix_constants(n=5.0e-2),  # larger n → larger anchor drift
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )

    class _TighterIX(TypeIXKernel):
        tolerance_anchor_limit = 0.0  # force any drift to fail

    pack = _TighterIX().residual_pack_from_bundle(bundle)
    assert pack.passed is False
    assert "compact_anchor_limit" in pack.violated_tolerances


def test_registered_type_ix_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_ix_constants(n=5.0e-3),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_ix"
    assert bundle.family == "IX"


def test_bundle_as_payload_preserves_legacy_keys():
    """Raw payload passthrough must keep legacy consumers working."""
    bundle = KERNEL.build_transport_bundle(
        structure=type_ix_constants(n=5.0e-3),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    payload = bundle.as_payload()
    for key in ("transfer_T", "transfer_E", "transfer_B", "propagator_matrix"):
        assert key in payload
