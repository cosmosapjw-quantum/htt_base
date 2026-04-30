"""Tests for the Type VII_h (helical open, h>0) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import type_i_constants, type_viih_constants
from bass.los.families.type_vii_h import (
    H_BRANCH_TAG,
    KERNEL,
    h_dependent_cutoff,
    translate_native_to_storage,
    translate_storage_to_native,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import (
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    register_family_kernel,
)


def test_h_branch_tag_constant():
    assert H_BRANCH_TAG == "positive_h_branch"


@pytest.mark.parametrize(
    "native,storage",
    [
        (("mu_VIIh", H_BRANCH_TAG, "scalar"), "m0"),
        (("mu_VIIh", H_BRANCH_TAG, "tensor_plus"), "m+2"),
        (("mu_VIIh", H_BRANCH_TAG, "tensor_minus"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


def test_translator_rejects_missing_h_branch():
    with pytest.raises(ValueError, match="h_branch tag"):
        translate_native_to_storage(("mu_VIIh", "other_branch", "scalar"))


def test_translator_rejects_wrong_prefix():
    with pytest.raises(ValueError, match="mu_VIIh"):
        translate_native_to_storage(("mu_open", H_BRANCH_TAG, "scalar"))


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+3")


@pytest.mark.parametrize("h", [0.0, 0.25, 1.0, 4.0])
def test_h_dependent_cutoff_monotonic(h):
    assert h_dependent_cutoff(h) == 1.0 + math.sqrt(h)


def test_h_dependent_cutoff_rejects_negative():
    with pytest.raises(ValueError, match="h >= 0"):
        h_dependent_cutoff(-0.1)


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


def test_kernel_rejects_non_type_vii_h():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_encodes_h_branch():
    bundle = KERNEL.build_transport_bundle(
        structure=type_viih_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["h_branch_tag"] == H_BRANCH_TAG
    assert md["h_parameter"] > 0.0
    assert md["radial_cutoff_R"] == 1.0 + math.sqrt(md["h_parameter"])
    assert md["operator_kernel"] == "type_viih_open_helical_projection"
    assert md["viih_transport_status"] == "type_viih_open_helical_source_integrated"
    assert md["viih_helical_pitch"] > 0.0
    assert md["viih_twist_scale"] > 0.0
    assert 0.0 < md["viih_open_attenuation_min"] < 1.0
    assert md["viih_mode_mixing_norm"] > 0.0
    assert md["polarization_basis_transport"] == "spin2_open_helical_rotation"
    assert np.linalg.norm(bundle.transfer_B[..., 1:]) > 0.0
    assert "no_hidden_h_branch_choice" in md["forbidden_shortcut_tracked"]


def test_residuals_pass_in_small_twist_limit():
    # Small a_twist keeps h near zero → FLRW-like limit.
    bundle = KERNEL.build_transport_bundle(
        structure=type_viih_constants(n1=1.0e-2, n3=1.0e-2, a_twist=1.0e-6),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["label_translator_roundtrip"] == 0.0
    assert r["seed_regularity"] < 1.0e-10
    assert r["positive_h_anchor_limit"] < KERNEL.tolerance_anchor_limit


def test_residual_pack_passes():
    bundle = KERNEL.build_transport_bundle(
        structure=type_viih_constants(n1=1.0e-2, n3=1.0e-2, a_twist=1.0e-6),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "VII_h"
    assert pack.metadata["viih_transport_status"] == "type_viih_open_helical_source_integrated"


def test_registered_type_vii_h_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_viih_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_vii_h"
