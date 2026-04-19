"""Tests H-01 .. H-08 for ``bass.hierarchy.pstf_tensor``.

Covers the storage-layer behaviour specified in
``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §11.1``:

- Construction of ``zero_pstf`` at every ℓ in the supported range.
- Shape validation of ``PSTFTensor``.
- Invertibility of packed ↔ full-tensor conversion.
- Symmetry and trace-freeness of the full-tensor form.
- Arithmetic identities ``t + (-t) = 0`` and ``2 * t = t + t``.

LB-2a baseline. The hierarchy-level tests (H-18+) live with the LB-2b
driver.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy import (
    L_MAX_CACHED,
    PSTFHierarchyState,
    PSTFTensor,
    hierarchy_total_size,
    pack_hierarchy,
    pstf_from_tensor,
    pstf_to_tensor,
    unpack_hierarchy,
    verify_pstf_invariants,
    zero_hierarchy,
    zero_pstf,
)


# ════════════════════════════════════════════════════════════════════
#   H-01 — zero factory shape
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", list(range(L_MAX_CACHED + 1)))
def test_h01_zero_pstf_shape(ell: int) -> None:
    """H-01: ``zero_pstf(ℓ)`` has packed shape ``(2ℓ+1,)`` for ℓ ∈ 0..8."""
    t = zero_pstf(ell)
    assert t.ell == ell
    assert t.components.shape == (2 * ell + 1,)
    assert t.components.dtype == np.float64
    assert np.all(t.components == 0.0)


def test_h01_zero_pstf_negative_raises() -> None:
    """Negative ``ell`` is rejected by the zero factory."""
    with pytest.raises(ValueError):
        zero_pstf(-1)


# ════════════════════════════════════════════════════════════════════
#   H-02 — construction with valid components
# ════════════════════════════════════════════════════════════════════

def test_h02_pstf_ell_2_valid_components() -> None:
    """H-02: ``PSTFTensor(ℓ=2, components=np.zeros(5))`` is valid."""
    t = PSTFTensor(ell=2, components=np.zeros(5))
    assert t.ell == 2
    assert t.components.shape == (5,)


@pytest.mark.parametrize("ell", list(range(L_MAX_CACHED + 1)))
def test_h02_pstf_accepts_correct_shape(ell: int) -> None:
    """Every supported rank accepts a matching-shape component array."""
    arr = np.arange(2 * ell + 1, dtype=np.float64)
    t = PSTFTensor(ell=ell, components=arr)
    assert np.array_equal(t.components, arr)


# ════════════════════════════════════════════════════════════════════
#   H-03 — construction with wrong-shape components raises
# ════════════════════════════════════════════════════════════════════

def test_h03_pstf_wrong_shape_raises() -> None:
    """H-03: wrong-shape components must raise ``ValueError``."""
    with pytest.raises(ValueError):
        PSTFTensor(ell=2, components=np.zeros(4))
    with pytest.raises(ValueError):
        PSTFTensor(ell=2, components=np.zeros(6))
    with pytest.raises(ValueError):
        PSTFTensor(ell=3, components=np.zeros(5))


def test_h03_pstf_negative_ell_raises() -> None:
    with pytest.raises(ValueError):
        PSTFTensor(ell=-1, components=np.zeros(0))


def test_h03_pstf_non_integer_ell_raises() -> None:
    with pytest.raises(TypeError):
        PSTFTensor(ell=1.5, components=np.zeros(3))  # type: ignore[arg-type]


# ════════════════════════════════════════════════════════════════════
#   H-04 — packed → full → packed round-trip
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", [0, 1, 2, 3, 4])
def test_h04_round_trip(ell: int) -> None:
    """H-04: ``pstf_from_tensor(pstf_to_tensor(t)) == t`` to 1e-14."""
    rng = np.random.default_rng(7 + ell)
    c = rng.normal(size=2 * ell + 1)
    t = PSTFTensor(ell=ell, components=c)
    T_full = pstf_to_tensor(t)
    t_round = pstf_from_tensor(T_full)
    assert t_round.ell == ell
    assert np.allclose(t_round.components, t.components, rtol=0, atol=1e-14)


# ════════════════════════════════════════════════════════════════════
#   H-05 — full tensor is symmetric
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", [2, 3, 4, 5])
def test_h05_full_tensor_symmetric(ell: int) -> None:
    """H-05: ``pstf_to_tensor(t)`` is totally symmetric in its ℓ axes."""
    rng = np.random.default_rng(21 + ell)
    t = PSTFTensor(ell=ell, components=rng.normal(size=2 * ell + 1))
    T = pstf_to_tensor(t)
    # Check invariance under every axis swap.
    from itertools import combinations
    for i, j in combinations(range(ell), 2):
        axes = list(range(ell))
        axes[i], axes[j] = axes[j], axes[i]
        swapped = np.transpose(T, axes)
        assert np.allclose(T, swapped, rtol=0, atol=1e-13), (
            f"asymmetry under swap {i}<->{j} for ell={ell}"
        )


# ════════════════════════════════════════════════════════════════════
#   H-06 — full tensor is trace-free
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", [2, 3, 4, 5, 6])
def test_h06_full_tensor_trace_free(ell: int) -> None:
    """H-06: every pair-trace of ``pstf_to_tensor(t)`` vanishes."""
    rng = np.random.default_rng(55 + ell)
    t = PSTFTensor(ell=ell, components=rng.normal(size=2 * ell + 1))
    T = pstf_to_tensor(t)
    from itertools import combinations
    for i, j in combinations(range(ell), 2):
        perm = [i, j] + [k for k in range(ell) if k not in (i, j)]
        permuted = np.transpose(T, perm)
        tr = np.trace(permuted, axis1=0, axis2=1)
        assert np.max(np.abs(tr)) < 1e-13, (
            f"trace over axes ({i},{j}) non-zero for ell={ell}"
        )


# ════════════════════════════════════════════════════════════════════
#   H-07, H-08 — arithmetic identities
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", [0, 1, 2, 3, 4])
def test_h07_additive_inverse(ell: int) -> None:
    """H-07: ``t + (-t) == zero_pstf(ℓ)``."""
    rng = np.random.default_rng(91 + ell)
    t = PSTFTensor(ell=ell, components=rng.normal(size=2 * ell + 1))
    z = t + (-t)
    assert z.allclose(zero_pstf(ell), rtol=0, atol=1e-14)


@pytest.mark.parametrize("ell", [0, 1, 2, 3, 4])
def test_h08_scalar_multiplication(ell: int) -> None:
    """H-08: ``t * 2 == t + t`` and ``2 * t == t + t`` (rmul)."""
    rng = np.random.default_rng(135 + ell)
    t = PSTFTensor(ell=ell, components=rng.normal(size=2 * ell + 1))
    assert (t * 2).allclose(t + t, rtol=0, atol=1e-14)
    assert (2 * t).allclose(t + t, rtol=0, atol=1e-14)
    assert (t * 0.5 * 2).allclose(t, rtol=0, atol=1e-14)


# ════════════════════════════════════════════════════════════════════
#   Additional: norm, subtraction, equality semantics
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", [0, 1, 2, 3])
def test_norm_matches_component_sum_sq(ell: int) -> None:
    """Norm invariant: ``||Π||² = Σ_m c_m²`` (flat-orthonormal basis)."""
    rng = np.random.default_rng(200 + ell)
    c = rng.normal(size=2 * ell + 1)
    t = PSTFTensor(ell=ell, components=c)
    assert abs(t.norm() - float(np.sum(c ** 2))) < 1e-14


def test_subtraction_yields_zero() -> None:
    rng = np.random.default_rng(42)
    t = PSTFTensor(ell=2, components=rng.normal(size=5))
    z = t - t
    assert z.allclose(zero_pstf(2), atol=1e-14)


def test_mismatched_ell_add_raises() -> None:
    with pytest.raises(ValueError):
        _ = PSTFTensor(ell=1, components=np.zeros(3)) + PSTFTensor(
            ell=2, components=np.zeros(5)
        )


def test_equality_bitwise() -> None:
    a = PSTFTensor(ell=2, components=np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
    b = PSTFTensor(ell=2, components=np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
    c = PSTFTensor(ell=2, components=np.array([1.0, 2.0, 3.0, 4.0, 5.5]))
    assert a == b
    assert not (a == c)


# ════════════════════════════════════════════════════════════════════
#   Verify-invariants helper integration
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", [2, 3, 4, 5])
def test_pstf_full_tensor_passes_invariants(ell: int) -> None:
    """``verify_pstf_invariants`` accepts every ``pstf_to_tensor`` output."""
    rng = np.random.default_rng(315 + ell)
    t = PSTFTensor(ell=ell, components=rng.normal(size=2 * ell + 1))
    T = pstf_to_tensor(t)
    ok, msg = verify_pstf_invariants(T)
    assert ok, msg


# ════════════════════════════════════════════════════════════════════
#   PSTFHierarchyState — tower container
# ════════════════════════════════════════════════════════════════════

def test_hierarchy_total_size_formula() -> None:
    """``total_size(L) = (L+1)²``."""
    for L in range(9):
        assert hierarchy_total_size(L) == (L + 1) ** 2


@pytest.mark.parametrize("L", [0, 1, 2, 4, 6, 8])
def test_zero_hierarchy_shape(L: int) -> None:
    """``zero_hierarchy(L)`` has the right size and ℓ-indexing."""
    state = zero_hierarchy(L)
    assert state.L == L
    assert len(state.tensors) == L + 1
    for ell, t in enumerate(state.tensors):
        assert t.ell == ell
    assert state.total_size == (L + 1) ** 2
    flat = state.as_flat()
    assert flat.shape == ((L + 1) ** 2,)
    assert np.all(flat == 0.0)


@pytest.mark.parametrize("L", [0, 2, 4, 6, 8])
def test_hierarchy_pack_unpack_roundtrip(L: int) -> None:
    """pack ∘ unpack = id and unpack ∘ pack = id."""
    rng = np.random.default_rng(1024 + L)
    flat = rng.normal(size=(L + 1) ** 2)
    state = unpack_hierarchy(flat, L)
    flat_rt = pack_hierarchy(state)
    assert np.allclose(flat, flat_rt, rtol=0, atol=1e-14)
    # Unpack offsets match the expected per-ℓ sizes.
    offset = 0
    for ell in range(L + 1):
        size = 2 * ell + 1
        assert np.allclose(
            state.tensors[ell].components, flat[offset:offset + size],
            rtol=0, atol=1e-14,
        )
        offset += size


def test_hierarchy_from_flat_wrong_shape_raises() -> None:
    with pytest.raises(ValueError):
        PSTFHierarchyState.from_flat(np.zeros(7), L=2)  # need 9


def test_hierarchy_construction_length_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        PSTFHierarchyState(
            L=2,
            tensors=[zero_pstf(0), zero_pstf(1)],  # missing ℓ=2
        )


def test_hierarchy_construction_wrong_ell_raises() -> None:
    with pytest.raises(ValueError):
        PSTFHierarchyState(
            L=2,
            tensors=[zero_pstf(0), zero_pstf(2), zero_pstf(1)],  # misordered
        )


def test_hierarchy_copy_is_deep() -> None:
    state = zero_hierarchy(3)
    state.tensors[2].components[0] = 7.0
    cp = state.copy()
    cp.tensors[2].components[0] = -1.0
    assert state.tensors[2].components[0] == 7.0  # original untouched
