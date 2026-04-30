"""Tests for the Type VI_h (class-B negative-h twist) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import type_i_constants, type_vih_constants
from bass.los.families.type_vi_h import (
    KERNEL,
    h_twist_scale,
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
        (("mu_VIh", "primary", "scalar"), "m0"),
        (("mu_VIh", "secondary", "tensor_plus"), "m+2"),
        (("mu_VIh", "secondary", "tensor_minus"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


def test_translator_rejects_missing_direction_tag():
    with pytest.raises(ValueError, match="direction_tag"):
        translate_native_to_storage(("mu_VIh", "unknown", "scalar"))


def test_translator_rejects_wrong_prefix():
    with pytest.raises(ValueError, match="mu_VIh"):
        translate_native_to_storage(("mu_hyp", "primary", "scalar"))


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+3")


@pytest.mark.parametrize("h", [0.0, -0.5, -2.0, -10.0])
def test_h_twist_scale_monotonic_decay(h):
    # |h| grows → scale shrinks toward 0.
    assert h_twist_scale(h) == 1.0 / (1.0 + abs(h))
    assert 0.0 < h_twist_scale(h) <= 1.0


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


def test_kernel_rejects_non_type_vi_h():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_records_h_value():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vih_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["h_value"] < 0.0  # VI_h has negative h
    assert md["h_value"] != -1.0  # Type III special case separate
    assert md["h_twist_scale"] == h_twist_scale(md["h_value"])
    assert md["vih_transport_status"] == "type_vih_negative_h_projection"
    assert md["vih_branch_flag"] == "negative_h_branch"
    assert md["vih_h_parameter"] == md["h_value"]
    assert md["vih_h_twist_scale"] == md["h_twist_scale"]
    assert md["vih_mode_mixing_norm"] > 0.0
    assert md["directional_sectors"]["primary"] in {"n1", "n3"}
    for shortcut in (
        "no_using_vi0_seed_at_nonzero_h",
        "no_hiding_h_inside_generic_branch_label",
    ):
        assert shortcut in md["forbidden_shortcut_tracked"]


def test_residuals_pass():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vih_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["h_consistency"] == 0.0
    assert r["branch_label"] == 0.0
    assert r["cutoff_refinement"] < 1.0e-10


def test_residual_pack_passes():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vih_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "VI_h"


def test_registered_type_vi_h_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_vih_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_vi_h"
