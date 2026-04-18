"""bass/hierarchy/terms.py (LB-2a/b) — PSTF multipole RHS term functions.

Implements the PSTF-projected contributions corresponding to the
nine-term 1+3 covariant hierarchy (``02_multipole_hierarchy_spec.md
§1``, lowell reference §6):

    Π̇_{⟨A_ℓ⟩} + T1 + T2 + T3 + T4 + T5 + T6 + T7 + T8 + T9 = K_{A_ℓ}

Each term is a pure function returning a full-tensor ``(3,)*ell``
contribution. The driver (``hierarchy_rhs``) sums them.

LB-2a (storage + orthogonal-same-rank subset)
---------------------------------------------
- **T1** — expansion ``(4/3) Θ Π_{A_ℓ}``
- **T2** — gradient ``∇̃_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}``
- **T3** — divergence ``((ℓ+1)/(2ℓ+3)) ∇̃^b Π_{A_ℓ b}``
- **T8** — shear-stays-at-ℓ ``(5ℓ/(2ℓ+3)) σ^b_{⟨a_ℓ} Π_{A_{ℓ−1}⟩ b}``
- **T9** — shear-to-ℓ-minus-2 ``−(ℓ+2) σ_{⟨a_ℓ a_{ℓ−1}} Π_{A_{ℓ−2}⟩}``

LB-2b (this file — added couplings)
-----------------------------------
- **T4** — accel × divergence ``−((ℓ+1)(ℓ−2)/(2ℓ+3)) A^b Π_{A_ℓ b}``
- **T5** — accel × gradient ``(ℓ+3) A_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}``
- **T6** — vorticity × same-ℓ ``ℓ ω^b η_{bc⟨a_ℓ} Π^c_{A_{ℓ−1}⟩}``
- **T7** — shear-to-ℓ-plus-2
  ``−((ℓ−1)(ℓ+1)(ℓ+2)/((2ℓ+3)(2ℓ+5))) σ^{bc} Π_{A_ℓ bc}``

All four LB-2b terms are pure algebraic contractions followed by PSTF
projection; they are well-defined for arbitrary ``A_a``, ``ω_a`` and
``σ_ab``. At orthogonal Bianchi (``A = ω = 0``) they trivially vanish
via zero inputs, but the functions themselves are not hard-wired to
zero — LB-2c / LB-2d (tilted + vorticity-bearing types) reuse the
identical contraction code with non-zero ``A``, ``ω``.

References
----------
- lowell reference §6 (source equation; the canonical form).
- Ellis, Maartens, MacCallum §4.6 (derivation of the hierarchy).
- Baumann *Lecture Notes in Cosmology* §4.6 (linearised hierarchy,
  cross-check).
- Pontzen-Challinor 2007 eq (C4) (shear-quadrupole coupling, T9 at
  ℓ = 2).
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from bass.hierarchy.contractions import sym_trace_free


__all__ = [
    "T1_expansion",
    "T2_gradient",
    "T3_divergence",
    "T4_accel_divergence",
    "T5_accel_gradient",
    "T6_vorticity",
    "T7_shear_up",
    "T8_shear_same",
    "T9_shear_down",
    "zero_nabla_operator",
]


# ════════════════════════════════════════════════════════════════════
#   Background-level ∇̃ operator (LB-2a default)
# ════════════════════════════════════════════════════════════════════

def zero_nabla_operator(tensor: np.ndarray, kind: str = "gradient") -> np.ndarray:
    """Background-level spatial covariant derivative: identically zero.

    At homogeneous background (Bianchi I / V / VII₀ with ``k = 0``) all
    physical fields depend only on ``η``, so ``∇̃_a (·) = 0`` regardless
    of the structure constants.

    Parameters
    ----------
    tensor : ndarray
        The rank-``ℓ'`` tensor whose gradient (``kind='gradient'``) or
        divergence (``kind='divergence'``) would be taken.
    kind : {'gradient', 'divergence'}
        Selects the output rank: ``'gradient'`` raises rank by one
        (output shape ``(3,) × (ell' + 1)``); ``'divergence'`` lowers
        rank by one (output shape ``(3,) × (ell' − 1)``).

    Returns
    -------
    ndarray
        All-zero array of the appropriate shape.

    Reference: 02_multipole_hierarchy_spec.md §4.2 — background-level
    shortcut for orthogonal Bianchi I/V/VII₀.
    """
    arr = np.asarray(tensor, dtype=np.float64)
    if kind == "gradient":
        return np.zeros((3,) * (arr.ndim + 1), dtype=np.float64)
    if kind == "divergence":
        if arr.ndim == 0:
            raise ValueError(
                "divergence of a rank-0 tensor is not defined"
            )
        target_rank = arr.ndim - 1
        if target_rank == 0:
            return np.array(0.0, dtype=np.float64)
        return np.zeros((3,) * target_rank, dtype=np.float64)
    raise ValueError(f"kind must be 'gradient' or 'divergence', got {kind!r}")


# ════════════════════════════════════════════════════════════════════
#   T1 — expansion
# ════════════════════════════════════════════════════════════════════

def T1_expansion(
    ell: int, Pi_ell_full: np.ndarray, Theta: float
) -> np.ndarray:
    """T1: ``(4/3) Θ Π_{A_ℓ}`` — isotropic dilution by expansion.

    At every rank ℓ the photon brightness suffers the ``(4/3) Θ``
    redshift damping (Ellis §4.6 eq, lowell §6). The result is
    trivially PSTF because the input already is.

    Parameters
    ----------
    ell : non-negative int
        Rank of ``Pi_ell_full``. Used for shape validation only.
    Pi_ell_full : ndarray of shape ``(3,) * ell``
        Full-tensor PSTF brightness at rank ``ell``.
    Theta : float
        **Proper-time** expansion scalar Θ = ∇_a u^a [1/Mpc].
        Equal to ``3 H_mpc = 3 calH_mpc / a`` at FLRW. Note this is
        NOT the conformal-time expansion. Drivers reading from
        ``FLRWBackgroundTable`` should use the ``Theta`` column
        directly — the LB-1 table already stores proper-time Θ.

    Reference: Ellis §4.6 (expansion term); lowell §6;
    ``00_conventions.md §3`` (kinematic variables).
    """
    if Pi_ell_full.ndim != ell:
        raise ValueError(
            f"T1_expansion: Pi_ell_full.ndim={Pi_ell_full.ndim} != ell={ell}"
        )
    return (4.0 / 3.0) * float(Theta) * Pi_ell_full


# ════════════════════════════════════════════════════════════════════
#   T2 — gradient
# ════════════════════════════════════════════════════════════════════

def T2_gradient(
    ell: int,
    Pi_ell_minus_1_full: np.ndarray,
    nabla_operator: Optional[Callable[..., np.ndarray]] = None,
) -> np.ndarray:
    """T2: ``∇̃_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}`` — gradient of the lower multipole.

    ``nabla_operator(tensor, kind='gradient')`` must return a tensor of
    rank one higher than ``tensor``; for a homogeneous background this
    is identically zero (``zero_nabla_operator``). The result is PSTF-
    projected on its ℓ indices.

    For ``ell = 0`` the term is identically zero (no ``ℓ − 1 = −1``
    tensor exists).

    Reference: Ellis §4.6 eq; lowell §6; 02_multipole_hierarchy_spec.md
    §4.2 (background-level simplification).
    """
    if ell == 0:
        return np.array(0.0, dtype=np.float64)
    if Pi_ell_minus_1_full.ndim != ell - 1:
        raise ValueError(
            f"T2_gradient: Pi_ell_minus_1_full.ndim="
            f"{Pi_ell_minus_1_full.ndim} != ell-1 = {ell - 1}"
        )
    if nabla_operator is None:
        nabla_operator = zero_nabla_operator
    raw = nabla_operator(Pi_ell_minus_1_full, kind="gradient")
    expected_rank = ell
    if raw.ndim != expected_rank:
        raise ValueError(
            f"T2_gradient: nabla_operator returned rank {raw.ndim}, "
            f"expected {expected_rank}"
        )
    return sym_trace_free(raw)


# ════════════════════════════════════════════════════════════════════
#   T3 — divergence
# ════════════════════════════════════════════════════════════════════

def T3_divergence(
    ell: int,
    Pi_ell_plus_1_full: np.ndarray,
    nabla_operator: Optional[Callable[..., np.ndarray]] = None,
) -> np.ndarray:
    """T3: ``((ℓ+1)/(2ℓ+3)) ∇̃^b Π_{A_ℓ b}`` — divergence of next multipole.

    Reference: Ellis §4.6 eq; lowell §6; 02_multipole_hierarchy_spec.md
    §4.2.
    """
    if Pi_ell_plus_1_full.ndim != ell + 1:
        raise ValueError(
            f"T3_divergence: Pi_ell_plus_1_full.ndim="
            f"{Pi_ell_plus_1_full.ndim} != ell+1 = {ell + 1}"
        )
    if nabla_operator is None:
        nabla_operator = zero_nabla_operator
    raw = nabla_operator(Pi_ell_plus_1_full, kind="divergence")
    if raw.ndim != ell:
        raise ValueError(
            f"T3_divergence: nabla_operator returned rank {raw.ndim}, "
            f"expected {ell}"
        )
    prefactor = (ell + 1.0) / (2.0 * ell + 3.0)
    return prefactor * sym_trace_free(raw)


# ════════════════════════════════════════════════════════════════════
#   Spatial 3-Levi-Civita (used by T6)
# ════════════════════════════════════════════════════════════════════

def _levi_civita_3() -> np.ndarray:
    """Rank-3 Levi-Civita symbol ε_{ijk} on an orthonormal 3-basis.

    Reference: Arfken Ch 3; Ellis §4.4 (kinematic identities).
    """
    eps = np.zeros((3, 3, 3), dtype=np.float64)
    eps[0, 1, 2] = eps[1, 2, 0] = eps[2, 0, 1] = 1.0
    eps[0, 2, 1] = eps[2, 1, 0] = eps[1, 0, 2] = -1.0
    return eps


# ════════════════════════════════════════════════════════════════════
#   T4 — acceleration × divergence
# ════════════════════════════════════════════════════════════════════

def T4_accel_divergence(
    ell: int, Pi_ell_plus_1_full: np.ndarray, accel_vector: np.ndarray
) -> np.ndarray:
    """T4: ``−((ℓ+1)(ℓ−2)/(2ℓ+3)) A^b Π_{A_ℓ b}`` — accel × divergence.

    Contracts the acceleration vector ``A^b`` with the last index of
    ``Π_{ℓ+1}``, leaving ℓ outer indices (PSTF-projected). Non-zero
    only when ``A_a ≠ 0`` (tilted or curvature-driven backgrounds); at
    orthogonal Bianchi ``A = 0`` makes this trivially vanish.

    At ``ℓ = 2`` the prefactor ``−(ℓ+1)(ℓ−2)/(2ℓ+3)`` vanishes by the
    explicit ``(ℓ − 2)`` factor, so T4 decouples Π_3 from Π_2 even if
    acceleration is non-zero.

    Parameters
    ----------
    ell : non-negative int
        Output rank.
    Pi_ell_plus_1_full : ndarray of shape ``(3,) * (ell + 1)``
        Full-tensor PSTF brightness at rank ``ell + 1``.
    accel_vector : ndarray of shape ``(3,)``
        4-acceleration ``A_a`` in the orthonormal tetrad basis [1/Mpc].

    Reference: Ellis §4.6; lowell §6; Pontzen-Challinor 2007 (C4).
    """
    if Pi_ell_plus_1_full.ndim != ell + 1:
        raise ValueError(
            f"T4_accel_divergence: Pi_ell_plus_1_full.ndim="
            f"{Pi_ell_plus_1_full.ndim} != ell+1 = {ell + 1}"
        )
    if accel_vector.shape != (3,):
        raise ValueError(
            f"accel_vector must have shape (3,), got {accel_vector.shape}"
        )
    prefactor = -(ell + 1.0) * (ell - 2.0) / (2.0 * ell + 3.0)
    # Contract A^b with the last axis of Π_{ℓ+1}.
    raw = np.tensordot(Pi_ell_plus_1_full, accel_vector, axes=([-1], [0]))
    if ell == 0:
        return np.asarray(prefactor * raw, dtype=np.float64)
    return prefactor * sym_trace_free(raw)


# ════════════════════════════════════════════════════════════════════
#   T5 — acceleration × gradient
# ════════════════════════════════════════════════════════════════════

def T5_accel_gradient(
    ell: int, Pi_ell_minus_1_full: np.ndarray, accel_vector: np.ndarray
) -> np.ndarray:
    """T5: ``(ℓ+3) A_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}`` — accel × gradient.

    Outer product of the acceleration vector ``A_{a_ℓ}`` with
    ``Π_{ℓ−1}``, PSTF-projected on the ℓ output indices. At
    ``ℓ = 0`` the term is identically zero (no ``A_{ℓ − 1}`` tensor).
    Active only for ``A_a ≠ 0``.

    Reference: Ellis §4.6; lowell §6.
    """
    if ell == 0:
        return np.array(0.0, dtype=np.float64)
    if Pi_ell_minus_1_full.ndim != ell - 1:
        raise ValueError(
            f"T5_accel_gradient: Pi_ell_minus_1_full.ndim="
            f"{Pi_ell_minus_1_full.ndim} != ell-1 = {ell - 1}"
        )
    if accel_vector.shape != (3,):
        raise ValueError(
            f"accel_vector must have shape (3,), got {accel_vector.shape}"
        )
    prefactor = ell + 3.0
    # Outer product A ⊗ Π_{ℓ-1} → rank ell.
    raw = np.tensordot(accel_vector, Pi_ell_minus_1_full, axes=0)
    return prefactor * sym_trace_free(raw)


# ════════════════════════════════════════════════════════════════════
#   T6 — vorticity (stays at ℓ)
# ════════════════════════════════════════════════════════════════════

def T6_vorticity(
    ell: int, Pi_ell_full: np.ndarray, omega_vector: np.ndarray
) -> np.ndarray:
    """T6: ``ℓ ω^b ε_{bc⟨a_ℓ} Π^c_{A_{ℓ−1}⟩}`` — vorticity coupling.

    Builds the antisymmetric rank-2 dual ``(ε · ω)_{ca} = ε_{bca} ω^b``
    and contracts its ``c`` index with one index of ``Π_ℓ``, producing
    a rank-ℓ output that is PSTF-projected. The term stays at rank ℓ
    (input and output both rank ℓ). The prefactor ``ℓ`` makes T6
    vanish at ``ℓ = 0``. Active only for ``ω_a ≠ 0`` (Bianchi types
    VII_h, VIII, IX; zero for I, V, VII₀ in the LB-2b target set).

    Parameters
    ----------
    ell : non-negative int
        Output rank (equal to input Π rank).
    Pi_ell_full : ndarray of shape ``(3,) * ell``
        Full-tensor PSTF brightness at rank ``ell``.
    omega_vector : ndarray of shape ``(3,)``
        Vorticity axial vector ``ω^a = (1/2) ε^{abc} ω_{bc}`` [1/Mpc].

    Reference: Ellis §4.6; lowell §6; Ellis §4.4 (ω-vector definition).
    """
    if ell == 0:
        return np.array(0.0, dtype=np.float64)
    if Pi_ell_full.ndim != ell:
        raise ValueError(
            f"T6_vorticity: Pi_ell_full.ndim={Pi_ell_full.ndim} != ell={ell}"
        )
    if omega_vector.shape != (3,):
        raise ValueError(
            f"omega_vector must have shape (3,), got {omega_vector.shape}"
        )
    eps = _levi_civita_3()
    # (ε · ω)_{ca} = ε_{bca} ω^b — antisymmetric rank-2.
    eps_om = np.einsum("bca,b->ca", eps, omega_vector)
    # Contract (ε·ω)_{ca} with Π^c_{A_{ℓ−1}} (axis 0 of Π represents c).
    raw = np.tensordot(eps_om, Pi_ell_full, axes=([0], [0]))
    return float(ell) * sym_trace_free(raw)


# ════════════════════════════════════════════════════════════════════
#   T7 — shear-to-ℓ-plus-2
# ════════════════════════════════════════════════════════════════════

def T7_shear_up(
    ell: int, Pi_ell_plus_2_full: np.ndarray, sigma_tensor: np.ndarray
) -> np.ndarray:
    """T7: ``−((ℓ−1)(ℓ+1)(ℓ+2)/((2ℓ+3)(2ℓ+5))) σ^{bc} Π_{A_ℓ bc}``.

    Couples ℓ to Π_{ℓ+2} via a two-index contraction with the shear.
    The prefactor ``(ℓ − 1)`` makes T7 vanish at ``ℓ = 1`` even when
    ``σ ≠ 0``; at the top of a truncated tower (``ℓ = L_max``)
    ``Π_{ℓ+2}`` is supplied by the closure strategy.

    Parameters
    ----------
    ell : non-negative int
        Output rank.
    Pi_ell_plus_2_full : ndarray of shape ``(3,) * (ell + 2)``
        Full-tensor PSTF brightness at rank ``ell + 2``. The contraction
        consumes the last two indices.
    sigma_tensor : ndarray of shape ``(3, 3)``
        **Proper-time** symmetric trace-free shear ``σ_ab`` [1/Mpc] —
        same convention as ``T8_shear_same`` / ``T9_shear_down``; not
        the conformal ``Σ_ab`` stored on ``TetradBackgroundState``.

    Reference: Ellis §4.6; lowell §6; 02_multipole_hierarchy_spec.md §1.
    """
    if Pi_ell_plus_2_full.ndim != ell + 2:
        raise ValueError(
            f"T7_shear_up: Pi_ell_plus_2_full.ndim="
            f"{Pi_ell_plus_2_full.ndim} != ell+2 = {ell + 2}"
        )
    if sigma_tensor.shape != (3, 3):
        raise ValueError(
            f"sigma_tensor must have shape (3, 3), got {sigma_tensor.shape}"
        )
    prefactor = -(
        (ell - 1.0) * (ell + 1.0) * (ell + 2.0)
        / ((2.0 * ell + 3.0) * (2.0 * ell + 5.0))
    )
    # Contract σ_{bc} with the last two axes of Π_{ℓ+2}.
    raw = np.tensordot(
        Pi_ell_plus_2_full, sigma_tensor, axes=([-2, -1], [0, 1])
    )
    if ell == 0:
        return np.asarray(prefactor * raw, dtype=np.float64)
    return prefactor * sym_trace_free(raw)


# ════════════════════════════════════════════════════════════════════
#   T8 — shear stays at ℓ
# ════════════════════════════════════════════════════════════════════

def _sigma_contract_last_axis(
    sigma_tensor: np.ndarray, Pi_with_b: np.ndarray
) -> np.ndarray:
    """Contract ``σ^b_c`` with a tensor whose **last axis** carries ``b``.

    ``σ^b_c`` is a rank-2 mixed tensor; raising / lowering in an
    orthonormal tetrad basis (``h_ab = δ_ab``) reduces to the ordinary
    matrix action. The product is

        out_{c, other...} = σ_{c, b} · Pi_{other..., b}

    Reshapes input axes so ``np.tensordot`` contracts the right one.
    """
    return np.tensordot(Pi_with_b, sigma_tensor, axes=([-1], [1]))


def T8_shear_same(
    ell: int, Pi_ell_full: np.ndarray, sigma_tensor: np.ndarray
) -> np.ndarray:
    """T8: ``(5ℓ/(2ℓ+3)) σ^b_{⟨a_ℓ} Π_{A_{ℓ−1}⟩ b}`` — shear stays at ℓ.

    Contracts one ``Π_ℓ`` index with σ and PSTF-projects on the ℓ
    output indices. At ``ℓ = 0`` the term is identically zero (no
    index to contract). At ``ℓ = 1`` the ``A_{ℓ − 1}`` index set is
    empty, so only σ supplies the output ℓ = 1 index:

        T8_a = 5 σ_{ab} Π^b

    which is already PSTF (rank-1 tensor is PSTF on 3-space).

    Parameters
    ----------
    ell : non-negative int
        Output rank.
    Pi_ell_full : ndarray of shape ``(3,) * ell``
        Full-tensor PSTF brightness at rank ``ell``.
    sigma_tensor : ndarray of shape ``(3, 3)``
        **Proper-time** symmetric trace-free shear ``σ_ab`` [1/Mpc].
        In an orthonormal tetrad basis ``σ^b_c = σ_{bc}`` numerically
        (raising / lowering with ``h_ab = δ_ab``). **NOT** the
        conformal-shear ``Σ_ab = e^α σ_ab`` stored on
        ``TetradBackgroundState.sigma_tensor``; the driver (LB-2b) is
        responsible for that conversion.

    Reference: lowell §6; Ellis §4.6; 02_multipole_hierarchy_spec.md §3.1;
    ``00_conventions.md §3`` (σ_ab convention).
    """
    if ell == 0:
        return np.array(0.0, dtype=np.float64)
    if Pi_ell_full.ndim != ell:
        raise ValueError(
            f"T8_shear_same: Pi_ell_full.ndim={Pi_ell_full.ndim} != ell={ell}"
        )
    if sigma_tensor.shape != (3, 3):
        raise ValueError(
            f"sigma_tensor must have shape (3, 3), got {sigma_tensor.shape}"
        )
    prefactor = 5.0 * ell / (2.0 * ell + 3.0)
    # Contract last axis of Π_ℓ with σ: out[other..., c] = σ_{cb} Π_{other..., b}.
    raw = _sigma_contract_last_axis(sigma_tensor, Pi_ell_full)
    return prefactor * sym_trace_free(raw)


# ════════════════════════════════════════════════════════════════════
#   T9 — shear to ℓ − 2
# ════════════════════════════════════════════════════════════════════

def T9_shear_down(
    ell: int, Pi_ell_minus_2_full: np.ndarray, sigma_tensor: np.ndarray
) -> np.ndarray:
    """T9: ``−(ℓ+2) σ_{⟨a_ℓ a_{ℓ−1}} Π_{A_{ℓ−2}⟩}`` — shear couples ℓ → ℓ−2.

    At ``ℓ = 2`` this gives the canonical shear-quadrupole source
    ``T9_{ab} = −4 σ_{ab} × Π_monopole`` which is the mechanism by
    which Bianchi shear injects a CMB quadrupole (Pontzen-Challinor
    2007 eq C4).

    For ``ℓ < 2`` the term is identically zero (no ``A_{ℓ − 2}`` tensor).

    Parameters
    ----------
    ell : non-negative int
        Output rank.
    Pi_ell_minus_2_full : ndarray of shape ``(3,) * (ell − 2)``
        Full-tensor PSTF brightness at rank ``ell − 2``. For
        ``ell = 2`` this is a 0-d ndarray holding the monopole.
    sigma_tensor : ndarray of shape ``(3, 3)``
        **Proper-time** symmetric trace-free shear ``σ_ab`` [1/Mpc].
        Same units convention as ``T8_shear_same`` — NOT the
        conformal ``Σ_ab`` stored on ``TetradBackgroundState``.

    Reference: lowell §6 (ℓ=2 worked example); Ellis §4.6;
    Pontzen-Challinor 2007 eq C4; 02_multipole_hierarchy_spec.md §3.
    """
    if ell < 2:
        return np.array(0.0, dtype=np.float64) if ell == 0 else np.zeros((3,), dtype=np.float64)
    if Pi_ell_minus_2_full.ndim != ell - 2:
        raise ValueError(
            f"T9_shear_down: Pi_ell_minus_2_full.ndim="
            f"{Pi_ell_minus_2_full.ndim} != ell-2 = {ell - 2}"
        )
    if sigma_tensor.shape != (3, 3):
        raise ValueError(
            f"sigma_tensor must have shape (3, 3), got {sigma_tensor.shape}"
        )
    prefactor = -(ell + 2.0)
    # Outer product σ ⊗ Π_{ℓ-2}: rank-ℓ tensor. Then PSTF-project.
    raw = np.tensordot(sigma_tensor, Pi_ell_minus_2_full, axes=0)
    # raw shape: (3, 3) + (3,)*(ell-2) = (3,)*ell.
    return prefactor * sym_trace_free(raw)
