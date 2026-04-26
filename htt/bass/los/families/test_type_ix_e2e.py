"""Audit P-06: Type IX end-to-end family backend regression.

The audit found that no non-FLRW family had an end-to-end output-level
regression beyond the Type-V→Type-I residual comparator. Type IX is
the cleanest non-FLRW anchor (compact SU(2) discrete spectrum,
analytical Wigner-D seed L²-norm), so this regression pins:

1. Label-translator round-trip = 0 (deterministic lookup).
2. Compact-domain seed L² regularity (Wigner-D quadrature anchor).
3. Compact-anchor limit: ``transfer_T[m=0]`` agrees with Type I in
   the ``n → 0`` isotropic limit, within the kernel's declared
   ``tolerance_anchor_limit = 5e-2``.
4. ``ResidualPack`` assembly does not raise.
5. The shape of the transfer bundle matches ``(n_k, ell_max+1, 3)``
   over the three PSTF storage channels ``m ∈ {0, ±2}``.

Tier of testing: kernel-level. We supply synthetic visibility +
source-builder callables to ``build_lowell_line_of_sight_propagator``
so the regression does not depend on the full Tier-B integrator,
species registry, or recombination tables. The Type IX kernel's
internal logic (label translation, compact-anchor residual) is
exercised end-to-end through ``TypeIXKernel.build_transport_bundle``.
"""
from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pytest


@pytest.fixture(scope="module")
def type_ix_kernel():
    from bass.los.families.type_ix import TypeIXKernel

    return TypeIXKernel()


@pytest.fixture(scope="module")
def isotropic_structure():
    """Type IX with small isotropic structure constants ``n = 1e-3``.

    Approaches Type I in the n→0 limit; the compact-anchor residual
    check is a meaningful regression at this band.
    """
    from bass.background.bianchi_types import StructureConstants

    n = 1.0e-3
    return StructureConstants(label="IX", n1=n, n2=n, n3=n, a_twist=0.0)


def _gaussian_visibility(eta_peak: float, sigma: float):
    """A smooth, normalized visibility window for the LoS quadrature."""
    def _g(eta: float) -> float:
        x = (float(eta) - float(eta_peak)) / float(sigma)
        return float(math.exp(-0.5 * x * x))
    return _g


def _adiabatic_source_builder(amplitude: float = 1.0e-5):
    """Return a (eta, k) → mapping mimicking SW + ISW + Doppler.

    The values are not physically calibrated; the regression is about
    *kernel structure*, not absolute D_ℓ. The builder must yield a
    finite mapping at every (eta, k).
    """
    def _src(eta: float, k: float) -> Mapping[str, object]:
        kr = float(k) * float(eta)
        wave = math.cos(kr) * float(amplitude)
        return {
            "theta_0": wave,
            "psi": 0.5 * wave,
            "pi": 0.1 * wave,
            "phi_dot_plus_psi_dot": 0.05 * wave,
            "v_b": 0.2 * wave,
        }
    return _src


def test_label_translator_roundtrip_is_exact() -> None:
    from bass.los.families.type_ix import (
        translate_native_to_storage,
        translate_storage_to_native,
    )

    for native in ((2, -2, 0), (2, 0, 0), (2, 2, 0)):
        storage = translate_native_to_storage(native)
        assert translate_storage_to_native(storage) == native


def test_compact_seed_norm_under_tolerance() -> None:
    """Wigner-D J=2 unit-L² seed must integrate to 1 within quadrature."""
    from bass.los.families.type_ix import compact_seed_norm_residual

    err = compact_seed_norm_residual(n_samples=48)
    assert err < 1.0e-10, f"seed L² regularity err = {err:.3e}"


def test_su2_amplitude_matches_invariant_volume() -> None:
    from bass.los.families.type_ix import wigner_d_j2_unit_amplitude

    expected = math.sqrt(5.0 / (8.0 * math.pi ** 2))
    assert wigner_d_j2_unit_amplitude() == pytest.approx(expected, rel=1.0e-15)


def test_native_label_outside_pstf_set_raises() -> None:
    from bass.los.families.type_ix import translate_native_to_storage

    with pytest.raises(ValueError, match="outside the PSTF storage set"):
        translate_native_to_storage((2, 1, 0))  # |M|=1 forbidden


def test_storage_label_unknown_raises() -> None:
    from bass.los.families.type_ix import translate_storage_to_native

    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+1")


@pytest.mark.slow
def test_type_ix_transport_bundle_runs_end_to_end(
    type_ix_kernel, isotropic_structure
) -> None:
    """End-to-end Type IX transport bundle via build_transport_bundle.

    Marked slow because ``build_lowell_line_of_sight_propagator`` runs
    a full LoS quadrature for both Type IX and Type I (anchor limit
    comparator). Asserts bundle shape, finite entries, and that the
    residuals sit within the kernel's declared tolerances.
    """
    eta_grid = np.linspace(50.0, 14000.0, 64)
    k_grid = np.logspace(-4.0, -2.5, 8)
    ell_max = 4
    visibility = _gaussian_visibility(eta_peak=280.0, sigma=20.0)
    source = _adiabatic_source_builder()

    bundle = type_ix_kernel.build_transport_bundle(
        structure=isotropic_structure,
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=ell_max,
        visibility_fn=visibility,
        source_builder=source,
    )

    # Shape contract: (n_k, ell_max+1, 3) over m ∈ {0, +2, -2}.
    assert bundle.transfer_T.shape == (k_grid.size, ell_max + 1, 3)
    assert bundle.transfer_E.shape == (k_grid.size, ell_max + 1, 3)
    assert np.all(np.isfinite(bundle.transfer_T))
    assert np.all(np.isfinite(bundle.transfer_E))

    # Residual contract: dictionary entries must satisfy declared tolerances.
    residuals = bundle.metadata["residual_values"]
    assert residuals["label_translator_roundtrip"] == 0.0
    assert residuals["seed_regularity"] < type_ix_kernel.tolerance_seed_regularity
    # Compact-anchor residual: at n=1e-3 and L_max=4, the bound is 5e-2.
    assert residuals["compact_anchor_limit"] < type_ix_kernel.tolerance_anchor_limit, (
        "Type IX m=0 transfer drifted from Type I anchor beyond the "
        f"declared 5e-2 tolerance: {residuals['compact_anchor_limit']:.3e}"
    )

    # The kernel must produce a constructible ResidualPack from the bundle.
    pack = type_ix_kernel.residual_pack_from_bundle(bundle)
    assert pack is not None


@pytest.mark.slow
def test_type_ix_residual_pack_metadata_carries_n_isotropic(
    type_ix_kernel, isotropic_structure
) -> None:
    """The Type IX residual pack must carry the isotropic ``n`` for
    downstream gate bundles to track which band was sampled."""
    eta_grid = np.linspace(50.0, 14000.0, 64)
    k_grid = np.logspace(-4.0, -3.0, 4)
    visibility = _gaussian_visibility(eta_peak=280.0, sigma=20.0)
    source = _adiabatic_source_builder()
    bundle = type_ix_kernel.build_transport_bundle(
        structure=isotropic_structure,
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=4,
        visibility_fn=visibility,
        source_builder=source,
    )
    pack = type_ix_kernel.residual_pack_from_bundle(bundle)
    extra = getattr(pack, "extra_metadata", None) or getattr(pack, "metadata", {})
    # Residual pack interface may carry the band marker under either key.
    assert "n_isotropic" in extra or any(
        "n_isotropic" in str(k) for k in extra
    )
