"""Tests H-09 .. H-12 for ``bass.hierarchy.contractions``.

Covers the STF projection utilities specified in
``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §11.2``:

- H-09: ``sym_trace_free`` kills pure-trace tensors.
- H-10: ``sym_trace_free`` kills purely antisymmetric tensors.
- H-11: ``sym_trace_free`` is idempotent on already-PSTF tensors.
- H-12: ``T8`` at ℓ=2 with explicit hand-worked input matches.

Additional tests cover basis orthonormality and the cached
``stf_basis`` invariants used across the hierarchy package.
"""
from __future__ import annotations

from itertools import permutations

import numpy as np
import pytest

from bass.hierarchy import (
    L_MAX_CACHED,
    pstf_pack,
    pstf_unpack,
    stf_basis,
    sym_trace_free,
    verify_pstf_invariants,
)
from bass.hierarchy.terms import T8_shear_same


# ════════════════════════════════════════════════════════════════════
#   Basis cache sanity
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", list(range(L_MAX_CACHED + 1)))
def test_basis_is_orthonormal(ell: int) -> None:
    """Q_ℓ columns are flat-orthonormal: ``Q^T Q = I_{2ℓ+1}``."""
    Q = stf_basis(ell)
    assert Q.shape == (3 ** ell if ell >= 1 else 1, 2 * ell + 1)
    gram = Q.T @ Q
    assert np.allclose(gram, np.eye(2 * ell + 1), rtol=0, atol=1e-13)


@pytest.mark.parametrize("ell", list(range(2, L_MAX_CACHED + 1)))
def test_basis_columns_are_symmetric_and_trace_free(ell: int) -> None:
    """Every STF basis tensor Q_{:,m} is symmetric and trace-free."""
    Q = stf_basis(ell)
    for m in range(Q.shape[1]):
        T = Q[:, m].reshape((3,) * ell)
        ok, msg = verify_pstf_invariants(T, tol=1e-12)
        assert ok, f"ell={ell}, basis column m={m}: {msg}"


def test_basis_out_of_range_raises() -> None:
    with pytest.raises(NotImplementedError):
        stf_basis(L_MAX_CACHED + 1)
    with pytest.raises(ValueError):
        stf_basis(-1)


# ════════════════════════════════════════════════════════════════════
#   H-09 — sym_trace_free kills pure-trace tensors
# ════════════════════════════════════════════════════════════════════

def test_h09_identity_times_scalar_projects_to_zero() -> None:
    """H-09: ``sym_trace_free(δ_ab)`` = 0 — the identity is pure trace."""
    identity = np.eye(3)
    projected = sym_trace_free(identity)
    assert np.max(np.abs(projected)) < 1e-14


def test_h09_rank_4_double_identity_projects_to_zero() -> None:
    """H-09 variant: δ_ab δ_cd symmetrised is pure trace → STF projection = 0."""
    delta = np.eye(3)
    T = np.einsum("ab,cd->abcd", delta, delta)
    # Symmetrise over all 4 axes
    from itertools import permutations
    S = np.zeros_like(T)
    n = 0
    for perm in permutations(range(4)):
        S += np.transpose(T, perm)
        n += 1
    S /= n
    projected = sym_trace_free(S)
    assert np.max(np.abs(projected)) < 1e-12


# ════════════════════════════════════════════════════════════════════
#   H-10 — sym_trace_free kills antisymmetric tensors
# ════════════════════════════════════════════════════════════════════

def test_h10_antisymmetric_projects_to_zero() -> None:
    """H-10: ``sym_trace_free`` of an antisymmetric rank-2 tensor = 0."""
    A = np.array(
        [
            [0.0, 1.0, -2.0],
            [-1.0, 0.0, 3.0],
            [2.0, -3.0, 0.0],
        ]
    )
    projected = sym_trace_free(A)
    assert np.max(np.abs(projected)) < 1e-14


def test_h10_rank_3_antisymmetric_subspace_partially_projects() -> None:
    """Fully antisymmetric rank-3 (Levi-Civita ε) has zero STF part on 3-space."""
    eps = np.zeros((3, 3, 3))
    for perm in permutations(range(3)):
        sign = 1
        # Count inversions
        arr = list(perm)
        for i in range(3):
            for j in range(i + 1, 3):
                if arr[i] > arr[j]:
                    sign = -sign
        eps[perm] = sign
    projected = sym_trace_free(eps)
    assert np.max(np.abs(projected)) < 1e-13


# ════════════════════════════════════════════════════════════════════
#   H-11 — sym_trace_free is idempotent on already-PSTF input
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", [2, 3, 4, 5])
def test_h11_idempotent_on_pstf(ell: int) -> None:
    """H-11: ``sym_trace_free(sym_trace_free(T)) = sym_trace_free(T)``."""
    rng = np.random.default_rng(400 + ell)
    T = rng.normal(size=(3,) * ell)
    once = sym_trace_free(T)
    twice = sym_trace_free(once)
    assert np.allclose(once, twice, rtol=0, atol=1e-13)


@pytest.mark.parametrize("ell", [2, 3, 4])
def test_h11_unchanged_on_pstf_packed_expansion(ell: int) -> None:
    """An ``Q_ℓ @ c`` tensor already lies in the STF subspace."""
    rng = np.random.default_rng(500 + ell)
    Q = stf_basis(ell)
    c = rng.normal(size=2 * ell + 1)
    T = (Q @ c).reshape((3,) * ell)
    projected = sym_trace_free(T)
    assert np.allclose(projected, T, rtol=0, atol=1e-13)


# ════════════════════════════════════════════════════════════════════
#   H-12 — T8 explicit hand-worked value at ℓ=2
# ════════════════════════════════════════════════════════════════════

def test_h12_T8_ell_2_axisymmetric_hand_value() -> None:
    """H-12: T8 at ℓ=2 with explicit hand-worked axisymmetric setup.

    Choose σ_ab = diag(−2, 1, 1) × (1/√6) (Σ_+ axisymmetric,
    ``axisymmetric_sigma_tensor`` at Σ_+ = 1, Σ_− = 0) and
    Π_ab = σ_ab (same tensor). Compute T8 directly from the formula

        T8_{ab} = (10/7) σ^c_{⟨a} Π_{b⟩ c}

    with the PSTF bracket denoting symmetrise-trace-free over ab.

    σ^c_{a} Π_{b c} = (σ σ)_{ab}  (matrix product) has trace
    σ^c_a σ_c^a = σ_{ab} σ^{ab} = 6 * Σ² = 6 * (1/6 * 6) = 1 (direct computation gives 1).
    Specifically σ σ = diag(4/6, 1/6, 1/6) = diag(2/3, 1/6, 1/6).
    Its trace is 2/3 + 1/6 + 1/6 = 1.0. PSTF projection of
    (σ σ)_{ab} is (σ σ)_{ab} − (1/3) tr(σ σ) δ_{ab}
               = diag(2/3, 1/6, 1/6) − (1/3) × 1 × diag(1,1,1)
               = diag(2/3 − 1/3, 1/6 − 1/3, 1/6 − 1/3)
               = diag(1/3, −1/6, −1/6).

    Therefore T8_{ab} = (10/7) × diag(1/3, −1/6, −1/6)
                      = diag(10/21, −5/21, −5/21).
    """
    from bass.background.tetrad_state import axisymmetric_sigma_tensor
    sigma = axisymmetric_sigma_tensor(sigma_plus=1.0, sigma_minus=0.0)
    Pi = sigma.copy()
    T8 = T8_shear_same(ell=2, Pi_ell_full=Pi, sigma_tensor=sigma)
    expected = np.diag([10.0 / 21.0, -5.0 / 21.0, -5.0 / 21.0])
    assert np.allclose(T8, expected, rtol=0, atol=1e-13), (
        f"T8 hand-worked mismatch: got\n{T8}\nexpected\n{expected}"
    )


# ════════════════════════════════════════════════════════════════════
#   pstf_pack / pstf_unpack utility tests
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", list(range(L_MAX_CACHED + 1)))
def test_pstf_pack_roundtrip(ell: int) -> None:
    """``pstf_pack(pstf_unpack(c)) == c`` for every rank.

    Tolerance scales with the dimension of the flat-tensor space
    (``3**ell``) to absorb the expected ``O(3**ell × ε_mach)``
    accumulated-rounding error in the Q@c @ Q^T re-projection. At
    ℓ=8 the flat space has 6561 entries and the worst-case rounding
    reaches ~1e-13 on random unit data.
    """
    rng = np.random.default_rng(600 + ell)
    c = rng.normal(size=2 * ell + 1)
    T = pstf_unpack(c, ell)
    c_rt = pstf_pack(T)
    atol = 1e-14 * (3 ** ell)  # scales from 1e-14 (ell=0) to ~7e-11 (ell=8)
    assert np.allclose(c_rt, c, rtol=0, atol=max(atol, 1e-14))


def test_pstf_pack_wrong_axis_raises() -> None:
    with pytest.raises(ValueError):
        pstf_pack(np.zeros((3, 4)))  # axis length 4 — not on 3-space


def test_pstf_unpack_wrong_shape_raises() -> None:
    with pytest.raises(ValueError):
        pstf_unpack(np.zeros(4), ell=2)  # need (5,)


def test_sym_trace_free_scalar_and_vector_unchanged() -> None:
    """Rank-0 and rank-1 inputs are returned untouched."""
    s = np.array(3.14)
    v = np.array([1.0, 2.0, 3.0])
    assert np.array_equal(sym_trace_free(s), s)
    assert np.array_equal(sym_trace_free(v), v)


def test_sym_trace_free_shape_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        sym_trace_free(np.zeros((3, 4, 3)))


# ════════════════════════════════════════════════════════════════════
#   verify_pstf_invariants negative tests
# ════════════════════════════════════════════════════════════════════

def test_verify_detects_asymmetry() -> None:
    T = np.zeros((3, 3))
    T[0, 1] = 1.0
    T[1, 0] = 0.0
    ok, msg = verify_pstf_invariants(T)
    assert not ok
    assert "asymmetric" in msg


def test_verify_detects_trace() -> None:
    ok, msg = verify_pstf_invariants(np.eye(3))
    assert not ok
    assert "trace" in msg


def test_verify_accepts_scalar_and_vector() -> None:
    ok1, _ = verify_pstf_invariants(np.array(5.0))
    ok2, _ = verify_pstf_invariants(np.array([1.0, 2.0, 3.0]))
    assert ok1 and ok2
