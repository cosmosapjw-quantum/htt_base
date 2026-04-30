"""Tests for the Type VII_0 (helical Euclidean, h=0) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import type_i_constants, type_vii0_constants
from bass.los.families.type_vii_0 import (
    KERNEL,
    TypeVII0Kernel,
    spherical_bessel_seed_amplitude,
    spherical_bessel_seed_norm_residual,
    translate_native_to_storage,
    translate_storage_to_native,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import (
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    register_family_kernel,
)


@pytest.mark.parametrize(
    "native,storage",
    [
        (("mu_VII0", "0", "scalar"), "m0"),
        (("mu_VII0", "+", "tensor_plus"), "m+2"),
        (("mu_VII0", "-", "tensor_minus"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


def test_translator_rejects_wrong_prefix():
    with pytest.raises(ValueError, match="mu_VII0"):
        translate_native_to_storage(("mu_nil", "0", "scalar"))


def test_translator_rejects_outside_pstf():
    with pytest.raises(ValueError, match="PSTF storage window"):
        translate_native_to_storage(("mu_VII0", "++", "scalar"))


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+3")


def test_seed_amplitude_positive():
    assert spherical_bessel_seed_amplitude(2, 1.0, 1.0) > 0.0


def test_seed_amplitude_rejects_non_positive():
    with pytest.raises(ValueError, match="R and k must be > 0"):
        spherical_bessel_seed_amplitude(2, 0.0, 1.0)
    with pytest.raises(ValueError, match="R and k must be > 0"):
        spherical_bessel_seed_amplitude(2, 1.0, 0.0)


def test_seed_norm_residual_within_quadrature_precision():
    assert spherical_bessel_seed_norm_residual(2, 1.0, 1.0, n_samples=128) < 1.0e-10


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


def test_kernel_rejects_non_type_vii_0():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_records_helical_specifics():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vii0_constants(n1=1.0e-3, n3=1.0e-3),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["chart"] == "helical_euclidean_chart"
    assert md["helicity_tags"] == ["0", "+", "-"]
    assert md["h_parameter"] == 0.0
    assert md["seed_basis"] == "spherical_jn"
    assert md["helical_transport_status"] == "type_vii0_helical_source_integrated"
    assert md["helical_pitch"] == pytest.approx(1.0e-3)
    assert md["helical_phase_max"] > 0.0
    assert md["polarization_basis_transport"] == "spin2_helical_rotation"
    assert md["helicity_mode_mixing_norm"] > 0.0
    assert np.linalg.norm(bundle.transfer_B[..., 1:]) > 0.0
    for shortcut in ("no_hidden_branch_choice", "no_local_boost_folded_into_backend"):
        assert shortcut in md["forbidden_shortcut_tracked"]


def test_residuals_pass_in_small_n_limit():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vii0_constants(n1=1.0e-6, n3=1.0e-6),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["label_translator_roundtrip"] == 0.0
    assert r["seed_regularity"] < 1.0e-10
    assert r["helical_anchor_limit"] < KERNEL.tolerance_anchor_limit


def test_residual_pack_passes_within_tolerance():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vii0_constants(n1=1.0e-6, n3=1.0e-6),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "VII_0"
    assert pack.metadata["helical_transport_status"] == "type_vii0_helical_source_integrated"


def test_registered_type_vii_0_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_vii0_constants(n1=1.0e-3, n3=1.0e-3),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_vii_0"
