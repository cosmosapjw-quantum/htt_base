"""Tests for bass/hierarchy/pack_unpack.py (LB-5 I-01..I-03).

Pins the combined state vector layout against
``docs/lowell_bianchi/05_integrator_spec.md §2``. Any accidental
layout change must either break these tests or be accompanied by a
spec amendment.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.collision.polarization import (
    PolarizationHierarchyState,
    zero_polarization_hierarchy,
)
from bass.hierarchy.pack_unpack import (
    BACKGROUND_SIZE,
    NEUTRINO_REDUCED_SIZE,
    combined_total_size,
    pack_combined_state,
    slice_a,
    slice_neutrino_reduced,
    slice_photon_E,
    slice_photon_T,
    slice_sigma_pm,
    unpack_combined_state,
)
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
    hierarchy_total_size,
    zero_hierarchy,
)


def _populate_generic_state(L_max: int, seed: int = 42):
    rng = np.random.default_rng(seed=seed)
    tensors = []
    for ell in range(L_max + 1):
        tensors.append(
            PSTFTensor(
                ell=ell,
                components=rng.standard_normal(2 * ell + 1),
            )
        )
    photon_T = PSTFHierarchyState(L=L_max, tensors=tensors)

    E_tensors = []
    for ell in range(L_max + 1):
        if ell < 2:
            E_tensors.append(
                PSTFTensor(
                    ell=ell,
                    components=np.zeros(2 * ell + 1),
                )
            )
        else:
            E_tensors.append(
                PSTFTensor(
                    ell=ell,
                    components=rng.standard_normal(2 * ell + 1) * 0.1,
                )
            )
    photon_E = PolarizationHierarchyState(
        E=PSTFHierarchyState(L=L_max, tensors=E_tensors)
    )
    neutrino_reduced = rng.standard_normal(NEUTRINO_REDUCED_SIZE)
    return photon_T, photon_E, neutrino_reduced


# ════════════════════════════════════════════════════════════════════
# I-01 Round-trip bit-identity
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("L_max", [4, 6, 8])
def test_I01_roundtrip_bit_identical(L_max: int) -> None:
    """``unpack(pack(state))`` reproduces every slot bit-identically.

    Reference: spec §10.1 (I-01), tolerance atol=1e-14.
    """
    photon_T, photon_E, nu = _populate_generic_state(L_max, seed=L_max * 17)
    a = 0.0123
    Sp, Sm = 3.21e-4, -7.77e-5

    y = pack_combined_state(
        a=a, Sigma_plus=Sp, Sigma_minus=Sm,
        photon_T=photon_T, photon_E=photon_E,
        neutrino_reduced=nu, L_max=L_max,
    )
    state = unpack_combined_state(y, L_max=L_max)

    assert state.a == pytest.approx(a, abs=1e-14)
    assert state.Sigma_plus == pytest.approx(Sp, abs=1e-14)
    assert state.Sigma_minus == pytest.approx(Sm, abs=1e-14)
    for ell in range(L_max + 1):
        np.testing.assert_allclose(
            state.photon_T.tensors[ell].components,
            photon_T.tensors[ell].components,
            atol=1e-14, rtol=0,
        )
        np.testing.assert_allclose(
            state.photon_E.E.tensors[ell].components,
            photon_E.E.tensors[ell].components,
            atol=1e-14, rtol=0,
        )
    np.testing.assert_allclose(
        state.neutrino_reduced, nu, atol=1e-14, rtol=0,
    )


# ════════════════════════════════════════════════════════════════════
# I-02 Total size matches spec formula
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("L_max,expected", [
    (4, 3 + 25 + 25 + 4),       # 57
    (6, 3 + 49 + 49 + 4),       # 105  (spec §1.1 baseline; note spec cites
                                 # 3 + 49 + 45 + 4 = 101 using ℓ≥2-only
                                 # E-mode storage — we keep layout parity
                                 # with the temperature tower and store the
                                 # ℓ<2 slots as zero padding per §2)
    (8, 3 + 81 + 81 + 4),       # 169
])
def test_I02_total_size_matches_formula(L_max: int, expected: int) -> None:
    """``combined_total_size(L)`` equals the explicit count for L∈{4,6,8}."""
    assert combined_total_size(L_max) == expected
    photon_T, photon_E, nu = _populate_generic_state(L_max, seed=1)
    y = pack_combined_state(
        a=1.0, Sigma_plus=0.0, Sigma_minus=0.0,
        photon_T=photon_T, photon_E=photon_E,
        neutrino_reduced=nu, L_max=L_max,
    )
    assert y.shape == (expected,)


# ════════════════════════════════════════════════════════════════════
# I-03 Slice helpers are contiguous and non-overlapping
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("L_max", [4, 6, 8])
def test_I03_slices_partition_the_vector(L_max: int) -> None:
    """The four slice helpers partition ``[0, combined_total_size)`` with
    no gaps and no overlap.
    """
    total = combined_total_size(L_max)
    covered = np.zeros(total, dtype=np.int32)

    for sl in (slice_a(L_max), slice_sigma_pm(L_max),
               slice_photon_T(L_max), slice_photon_E(L_max),
               slice_neutrino_reduced(L_max)):
        covered[sl] += 1

    # Every index covered exactly once.
    assert np.all(covered == 1), (
        f"slices do not partition the vector: bincount = "
        f"{np.bincount(covered)}"
    )
    # Spot-check the explicit boundaries from spec §2.1 at L_max=6:
    if L_max == 6:
        assert slice_a(L_max) == slice(0, 1)
        assert slice_sigma_pm(L_max) == slice(1, 3)
        assert slice_photon_T(L_max) == slice(3, 3 + 49)
        assert slice_photon_E(L_max) == slice(3 + 49, 3 + 49 + 49)
        assert slice_neutrino_reduced(L_max) == slice(
            3 + 49 + 49, 3 + 49 + 49 + 4,
        )


def test_I03_constants_are_pinned() -> None:
    """``BACKGROUND_SIZE`` and ``NEUTRINO_REDUCED_SIZE`` are hard-coded
    per spec §2.1; any change must be reflected in this test.
    """
    assert BACKGROUND_SIZE == 3
    assert NEUTRINO_REDUCED_SIZE == 4


# ════════════════════════════════════════════════════════════════════
#   Input validation
# ════════════════════════════════════════════════════════════════════

def test_pack_rejects_mismatched_L() -> None:
    """``pack_combined_state`` flags a photon tower whose ``L`` does
    not match the requested ``L_max``.
    """
    photon_T = zero_hierarchy(L=4)
    photon_E = zero_polarization_hierarchy(L=4)
    nu = np.zeros(NEUTRINO_REDUCED_SIZE)
    with pytest.raises(ValueError, match="photon_T.L"):
        pack_combined_state(
            a=1.0, Sigma_plus=0.0, Sigma_minus=0.0,
            photon_T=photon_T, photon_E=photon_E,
            neutrino_reduced=nu, L_max=6,
        )


def test_unpack_rejects_wrong_length() -> None:
    """``unpack_combined_state`` rejects a vector of the wrong length."""
    with pytest.raises(ValueError, match="y shape"):
        unpack_combined_state(np.zeros(17), L_max=6)


def test_pack_rejects_bad_neutrino_shape() -> None:
    photon_T = zero_hierarchy(L=6)
    photon_E = zero_polarization_hierarchy(L=6)
    with pytest.raises(ValueError, match="neutrino_reduced"):
        pack_combined_state(
            a=1.0, Sigma_plus=0.0, Sigma_minus=0.0,
            photon_T=photon_T, photon_E=photon_E,
            neutrino_reduced=np.zeros(5), L_max=6,
        )


# Silence unused-import warnings on symbols carried for explicit test
# readability.
_ = hierarchy_total_size
