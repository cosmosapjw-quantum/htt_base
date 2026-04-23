"""Tests for the Type VI_0 (class-A solvable, directional) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import (
    StructureConstants,
    type_i_constants,
    type_vi0_constants,
)
from bass.los.families.type_vi_0 import (
    KERNEL,
    TypeVI0Kernel,
    directional_sector_for,
    seed_piecewise_constant_unit_l2,
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
        (("mu_VI0", "primary", "scalar"), "m0"),
        (("mu_VI0", "secondary", "tensor_plus"), "m+2"),
        (("mu_VI0", "secondary", "tensor_minus"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


def test_translator_rejects_malformed_native():
    with pytest.raises(ValueError, match="direction_tag"):
        translate_native_to_storage(("mu_VI0", "scalar"))  # too short
    with pytest.raises(ValueError, match="direction_tag"):
        translate_native_to_storage(("mu_VI0", "tertiary", "scalar"))  # bad direction


def test_translator_rejects_outside_pstf():
    with pytest.raises(ValueError, match="PSTF storage window"):
        translate_native_to_storage(("mu_VI0", "primary", "tensor_plus"))


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+1")


# ----- Directional sector selection --------------------------------------


def test_principal_direction_n1_when_larger():
    s = StructureConstants(n1=2.0e-2, n2=0.0, n3=-1.0e-2, label="VI_0")
    sectors = directional_sector_for(s)
    assert sectors == {"primary": "n1", "secondary": "n3"}


def test_principal_direction_n3_when_larger():
    s = StructureConstants(n1=1.0e-2, n2=0.0, n3=-3.0e-2, label="VI_0")
    sectors = directional_sector_for(s)
    assert sectors == {"primary": "n3", "secondary": "n1"}


def test_principal_direction_ties_favor_n1():
    s = StructureConstants(n1=1.0e-2, n2=0.0, n3=-1.0e-2, label="VI_0")
    sectors = directional_sector_for(s)
    assert sectors["primary"] == "n1"


# ----- Seed regularity ---------------------------------------------------


def test_seed_unit_l2_passes_quadrature_precision():
    err = seed_piecewise_constant_unit_l2(half_width_L=1.0, n_samples=64)
    assert err < 1.0e-12


def test_seed_rejects_non_positive_width():
    with pytest.raises(ValueError, match="half_width_L must be > 0"):
        seed_piecewise_constant_unit_l2(half_width_L=0.0)


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


def test_kernel_rejects_non_vi_0_structure():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_records_directional_sectors():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vi0_constants(n1=2.0e-2, n3=-1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["chart"] == "class_a_solvable_intrinsic"
    assert md["directional_sectors"] == {"primary": "n1", "secondary": "n3"}
    assert md["principal_direction_axis"] == "n1"
    assert md["truncation_half_width"] == 1.0
    for shortcut in ("no_borrowing_type_i_or_vii_seeds", "no_isotropic_direction_compression"):
        assert shortcut in md["forbidden_shortcut_tracked"]


def test_residuals_are_tight():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vi0_constants(n1=1.0e-2, n3=-1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["translator_directional_tag"] == 0.0
    assert r["seed_regularity"] < 1.0e-12
    assert r["directional_truncation"] < 1.0e-11


def test_residual_pack_passes_within_tolerance():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vi0_constants(n1=1.0e-2, n3=-1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "VI_0"


def test_residual_pack_fails_when_translator_tolerance_zeroed():
    bundle = KERNEL.build_transport_bundle(
        structure=type_vi0_constants(n1=1.0e-2, n3=-1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    # Inject a non-zero residual by overriding the bundle payload.
    bad_bundle = bundle
    bad_meta = dict(bundle.metadata)
    bad_meta["residual_values"] = {
        **bundle.metadata["residual_values"],
        "translator_directional_tag": math.inf,
    }
    # Just rebuild residual_pack with infinite residual.

    class _InfFailureKernel(TypeVI0Kernel):
        pass

    kernel = _InfFailureKernel()

    # The kernel's pack builder reads residual_values from bundle metadata;
    # we construct a shim bundle-like object with mutated metadata.
    class _Shim:
        def __init__(self, metadata): self.metadata = metadata
    shim = _Shim(bad_meta)
    pack = kernel.residual_pack_from_bundle(shim)  # type: ignore[arg-type]
    assert pack.passed is False
    assert "translator_directional_tag" in pack.violated_tolerances


def test_registered_type_vi_0_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_vi0_constants(n1=1.0e-2, n3=-1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_vi_0"
