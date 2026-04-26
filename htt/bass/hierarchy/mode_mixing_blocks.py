"""bass/hierarchy/mode_mixing_blocks.py — Round-16 PR-S3 RHS k-mixing.

Implements V5_ROUND16_02_SOLVER_LAYER.md §2.3-§2.4: the off-diagonal
shear-coupling block A_mix(η) that closes Round-16 gap **G2** (the
hierarchy RHS having no off-diagonal ℓ-ℓ' or m-m' coupling).

The physics: the shear σ_ab (background, time-dependent) couples PSTF
multipoles via the three terms T7, T8, T9 of the photon Boltzmann RHS
(Pereira-Pitrou-Uzan 2007 + Pontzen-Challinor 2007 + Challinor-Lasenby
2000-I §3):

    T7 ⊃ σ^{2M} C_7(ℓ, m, M) Π_{ℓ+2, m-M}     [shear-quadrupole-up]
    T8 ⊃ σ^{2M} C_8(ℓ, m, M) Π_{ℓ,   m-M}     [shear-recoupling]
    T9 ⊃ σ^{2M} C_9(ℓ, m, M) Π_{ℓ-2, m-M}     [shear-quadrupole-down]

with M ∈ {-2..+2} indexing the five PSTF quadrupole components of
σ_ab and the C-coefficients given by Wigner-3j Clebsch-Gordan
combinations. The quadrupole ``σ_2M`` evaluated against the background
five-vector ``(σ_+, σ_-, σ_×1, σ_×2, σ_×3)`` from
:mod:`bass.background.codazzi_tilt_rhs` (PR-S1) drives the time
dependence.

This module provides the **standalone** building blocks:
- :func:`build_shear_coupling_table` — pre-compute C_7, C_8, C_9 for
  all (ℓ, m, M).
- :func:`assemble_A_mix_block` — assemble the sparse off-diagonal matrix
  given a background ``σ_2M(η)``.

The wiring of A_mix into the production hierarchy RHS (PR-S13 scope)
will consume these primitives. For Round-15 backward compatibility the
existing single-m photon tower is unchanged; PR-S3 only adds the
mode-mixing primitives + their tests.

References
----------
- Pereira, Pitrou & Uzan 2007, *JCAP* 09, 006 — scalar-vector-tensor
  seesaw and mode mixing in Bianchi I.
- Pontzen & Challinor 2007, *Class. Quantum Grav.* 24, 3185 — Bianchi
  B-mode tower, m-recoupling. Eq. 23-25 give the C^{(7,8,9)} coupling
  coefficients in PSTF normalisation.
- Challinor & Lasenby 2000, *Ann. Phys.* 282, 285 — 1+3 covariant
  CMB hierarchy I+II.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np
import scipy.sparse as sp
from sympy.physics.wigner import wigner_3j as _wigner_3j_exact

__all__ = [
    "ShearCouplingTable",
    "wigner_3j",
    "build_shear_coupling_table",
    "shear_5vec_to_quadrupole_components",
    "assemble_A_mix_block",
    "ell_m_to_index",
    "index_to_ell_m",
    "PHOTON_M_VALUES",
    "PHOTON_M_COUNT",
]

#: Five m-channels {-2, -1, 0, +1, +2} carried by the PSTF photon tower.
PHOTON_M_VALUES: tuple[int, ...] = (-2, -1, 0, 1, 2)
PHOTON_M_COUNT: int = 5


@lru_cache(maxsize=8192)
def wigner_3j(j1: int, j2: int, j3: int, m1: int, m2: int, m3: int) -> float:
    """Cached float Wigner-3j ``( j1 j2 j3 ; m1 m2 m3 )``.

    Wraps :func:`sympy.physics.wigner.wigner_3j` and casts to float.
    """
    return float(_wigner_3j_exact(j1, j2, j3, m1, m2, m3))


def ell_m_to_index(ell: int, m: int, *, ell_min: int = 2) -> int:
    """Map (ℓ, m) ∈ ([ell_min..L], [-2..2]) to a flat slot index.

    Layout: m-major within each ℓ-block, ℓ ascending. So slot index =
    ``5 * (ℓ − ℓ_min) + (m + 2)``.
    """
    if m < -2 or m > 2:
        raise ValueError(f"m={m!r} outside the PSTF five-channel range [-2, 2]")
    if ell < ell_min:
        raise ValueError(f"ell={ell!r} below ell_min={ell_min!r}")
    return PHOTON_M_COUNT * (ell - ell_min) + (m + 2)


def index_to_ell_m(idx: int, *, ell_min: int = 2) -> tuple[int, int]:
    """Inverse of :func:`ell_m_to_index`."""
    if idx < 0:
        raise ValueError(f"idx={idx!r} must be non-negative")
    return ell_min + idx // PHOTON_M_COUNT, (idx % PHOTON_M_COUNT) - 2


# ──────────────────────────────────────────────────────────────────────
# Wigner-3j coupling coefficients (PSTF normalisation)
# ──────────────────────────────────────────────────────────────────────


def _C7(ell: int, m: int, M: int) -> float:
    """⟨ℓ+2, m | ℓ, m−M; 2, M⟩ — the shear-quadrupole-up coupling.

    PSTF normalisation per Pontzen-Challinor 2007 eq. 23-25; selection
    rule |m − M| ≤ ℓ enforced by Wigner-3j.
    """
    return _coupling_coefficient(ell_lower=ell, ell_upper=ell + 2, m=m, M=M)


def _C8(ell: int, m: int, M: int) -> float:
    """⟨ℓ, m | ℓ, m−M; 2, M⟩ — the same-ℓ recoupling."""
    return _coupling_coefficient(ell_lower=ell, ell_upper=ell, m=m, M=M)


def _C9(ell: int, m: int, M: int) -> float:
    """⟨ℓ−2, m | ℓ, m−M; 2, M⟩ — the shear-quadrupole-down coupling.

    Returns 0 for ell < 2 (no source).
    """
    if ell < 2:
        return 0.0
    return _coupling_coefficient(ell_lower=ell, ell_upper=ell - 2, m=m, M=M)


def _coupling_coefficient(*, ell_lower: int, ell_upper: int, m: int, M: int) -> float:
    """Generic coupling ``⟨ell_upper, m | ell_lower, m−M; 2, M⟩``.

    Built from the Wigner-3j with the ``(2 ell_upper + 1)`` normalisation
    convention used throughout this module. Selection rule (m − M ≤
    min(ℓ_lower, ℓ_upper)) enforced.
    """
    m_lower = m - M
    if abs(m_lower) > ell_lower:
        return 0.0
    if abs(m) > ell_upper:
        return 0.0
    if abs(M) > 2:
        return 0.0
    # Phase + normalisation convention: ⟨J3 m3 | J1 m1; J2 m2⟩ =
    # (-1)^{J1-J2+m3} sqrt(2 J3 + 1) (J1 J2 J3; m1 m2 -m3).
    cg = wigner_3j(int(ell_lower), 2, int(ell_upper), int(m_lower), int(M), int(-m))
    norm = float(np.sqrt(2 * ell_upper + 1))
    sign = (-1) ** (ell_lower - 2 + m)
    return float(sign * norm * cg)


@dataclass(frozen=True)
class ShearCouplingTable:
    """Cached C_7, C_8, C_9 table over (kind, ℓ, m, M) for ℓ ≤ L_max.

    Layout: ``values[kind, ℓ, m+2, M+2]`` with ``kind ∈ {0:C7, 1:C8,
    2:C9}``, ℓ ∈ [0..L_max], m ∈ [-2..2], M ∈ [-2..2].

    This is a *family-agnostic* table — the C-coefficients depend only
    on (ℓ, m, M) and the PSTF normalisation, not on the Bianchi family.
    Per family, ``A_mix`` is then assembled by contracting the table
    with the time-dependent ``σ_2M(η)`` quadrupole.
    """

    values: np.ndarray
    L_max: int

    def __post_init__(self) -> None:
        arr = np.asarray(self.values, dtype=np.float64)
        expected = (3, self.L_max + 1, PHOTON_M_COUNT, PHOTON_M_COUNT)
        if arr.shape != expected:
            raise ValueError(
                f"ShearCouplingTable.values must have shape {expected!r}; "
                f"got {arr.shape!r}"
            )
        object.__setattr__(self, "values", arr)


def build_shear_coupling_table(L_max: int) -> ShearCouplingTable:
    """Pre-compute C_7, C_8, C_9 for all ``(ℓ ≤ L_max, m ∈ [-2..2], M ∈ [-2..2])``.

    The table is built once at backend init and reused across η-steps.
    For ``L_max = 40`` (production) the table holds 3·41·5·5 = 3075
    floats — trivial memory footprint.

    Parameters
    ----------
    L_max : int
        Maximum ℓ in the photon tower. Must be ≥ 2.

    Returns
    -------
    ShearCouplingTable
    """
    if L_max < 2:
        raise ValueError(f"L_max must be >= 2; got {L_max!r}")
    table = np.zeros(
        (3, L_max + 1, PHOTON_M_COUNT, PHOTON_M_COUNT),
        dtype=np.float64,
    )
    for ell in range(0, L_max + 1):
        for m_idx, m in enumerate(PHOTON_M_VALUES):
            for M_idx, M in enumerate(PHOTON_M_VALUES):
                table[0, ell, m_idx, M_idx] = _C7(ell, m, M)
                table[1, ell, m_idx, M_idx] = _C8(ell, m, M)
                table[2, ell, m_idx, M_idx] = _C9(ell, m, M)
    return ShearCouplingTable(values=table, L_max=L_max)


# ──────────────────────────────────────────────────────────────────────
# Shear five-vector → quadrupole spherical components
# ──────────────────────────────────────────────────────────────────────


def shear_5vec_to_quadrupole_components(sigma_5vec: np.ndarray) -> np.ndarray:
    """Convert tetrad-frame shear 5-vector to PSTF quadrupole {σ_2M}.

    Input five-vector indexing per PR-S1 / V5_ROUND16_01 §3.2:
    ``(σ_+, σ_-, σ_×1, σ_×2, σ_×3)`` where σ_+ = (σ_11 − σ_22)/2 and
    σ_- = (σ_11 + σ_22 − 2σ_33)/(2√3) parameterise the diagonal PSTF
    components, and σ_×i = σ_(off-diagonal,i) parameterise the three
    off-diagonal components.

    Output array shape (5,) indexed by M ∈ {-2, -1, 0, +1, +2} with
    real spherical-harmonic conventions:

        σ_{2,−2} = σ_×1               (xy)
        σ_{2,−1} = σ_×3               (yz)
        σ_{2, 0} = σ_-                (zz-projection)
        σ_{2,+1} = σ_×2               (xz)
        σ_{2,+2} = σ_+                (xx-yy)

    This is the convention used throughout V5_ROUND16_02 §2.2; the
    real-spherical-harmonic basis matches the existing
    :mod:`bass.background.initial_conditions._ORTHONORMAL_PSTF_BASIS`.

    Parameters
    ----------
    sigma_5vec : ndarray, shape (5,)
        Tetrad-frame shear 5-vector ``(σ_+, σ_-, σ_×1, σ_×2, σ_×3)``.

    Returns
    -------
    ndarray, shape (5,)
        Quadrupole components ``σ_2M`` for M ∈ {-2, -1, 0, +1, +2}.
    """
    s = np.asarray(sigma_5vec, dtype=np.float64)
    if s.shape != (5,):
        raise ValueError(
            f"sigma_5vec must have shape (5,); got {s.shape!r}"
        )
    sigma_plus, sigma_minus, x1, x2, x3 = (float(v) for v in s)
    return np.array([x1, x3, sigma_minus, x2, sigma_plus], dtype=np.float64)


# ──────────────────────────────────────────────────────────────────────
# A_mix assembly
# ──────────────────────────────────────────────────────────────────────


def assemble_A_mix_block(
    *,
    sigma_2M: np.ndarray,
    L_max: int,
    coupling_table: ShearCouplingTable | None = None,
    ell_min: int = 2,
) -> sp.csr_matrix:
    """Assemble the sparse off-diagonal shear-mixing block ``A_mix(η)``.

    For ℓ ∈ [ell_min..L_max] and m ∈ {-2..+2}, this populates the
    sparse matrix whose action on the (ℓ, m)-indexed PSTF tower gives
    the T7+T8+T9 contributions to the photon Boltzmann RHS:

        (A_mix Π)_{ℓ, m} = T7 + T8 + T9

    with the prefactors of V5_ROUND16_02 §2.3:

        T7: −((ℓ−1)(ℓ+1)(ℓ+2))/((2ℓ+3)(2ℓ+5)) Σ_M σ_2M C_7 Π_{ℓ+2, m−M}
        T8: +(5ℓ)/(2ℓ+3) Σ_M σ_2M C_8 Π_{ℓ, m−M}
        T9: −(ℓ+2) Σ_M σ_2M C_9 Π_{ℓ−2, m−M}

    Parameters
    ----------
    sigma_2M : ndarray, shape (5,)
        PSTF quadrupole components of the shear at the current η.
    L_max : int
        Maximum ℓ in the photon tower.
    coupling_table : ShearCouplingTable, optional
        Pre-computed C-coefficient table (from
        :func:`build_shear_coupling_table`). Built on the fly if omitted
        — but for production the caller should pass a cached table.
    ell_min : int, default 2
        Lowest ℓ in the photon tower (default 2 — the polarisation
        E/B towers; for the temperature tower pass ``ell_min=0``).

    Returns
    -------
    scipy.sparse.csr_matrix
        Square matrix of shape ``(N, N)`` where
        ``N = 5 * (L_max − ell_min + 1)``.

    Notes
    -----
    For axisymmetric backgrounds (only ``σ_{2,0}`` non-zero), the
    matrix is *block-diagonal* in m. For a parity-odd shear
    (``σ_{2,±1} ≠ 0``) the matrix couples (m, m−M) channels — this is
    the structural ingredient that drives B-mode generation from
    pre-recombination shear (see PR-S4 / PR-S11).
    """
    s = np.asarray(sigma_2M, dtype=np.float64)
    if s.shape != (5,):
        raise ValueError(
            f"sigma_2M must have shape (5,); got {s.shape!r}"
        )
    if L_max < ell_min:
        raise ValueError(
            f"L_max={L_max!r} must be >= ell_min={ell_min!r}"
        )
    if coupling_table is None:
        coupling_table = build_shear_coupling_table(L_max)
    elif coupling_table.L_max < L_max:
        raise ValueError(
            f"coupling_table.L_max={coupling_table.L_max!r} < "
            f"L_max={L_max!r}; rebuild the table with the larger ceiling"
        )

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    table = coupling_table.values

    for ell in range(ell_min, L_max + 1):
        # T7 prefactor: -((ℓ-1)(ℓ+1)(ℓ+2))/((2ℓ+3)(2ℓ+5))
        if ell + 2 <= L_max:
            pre7 = -(
                (ell - 1) * (ell + 1) * (ell + 2)
            ) / ((2 * ell + 3) * (2 * ell + 5))
        else:
            pre7 = 0.0
        # T8 prefactor: +(5ℓ)/(2ℓ+3)
        pre8 = (5 * ell) / (2 * ell + 3)
        # T9 prefactor: -(ℓ+2); only when ℓ-2 ≥ ell_min
        if ell - 2 >= ell_min:
            pre9 = -(ell + 2)
        else:
            pre9 = 0.0

        for m_idx, m in enumerate(PHOTON_M_VALUES):
            row = ell_m_to_index(ell, m, ell_min=ell_min)
            for M_idx, M in enumerate(PHOTON_M_VALUES):
                m_target = m - M
                if abs(m_target) > 2:
                    continue
                sigma_M = float(s[M_idx])
                if sigma_M == 0.0:
                    continue
                # T7: ℓ → ℓ+2
                if pre7 != 0.0:
                    coeff = pre7 * sigma_M * float(table[0, ell, m_idx, M_idx])
                    if coeff != 0.0:
                        col = ell_m_to_index(ell + 2, m_target, ell_min=ell_min)
                        rows.append(row); cols.append(col); data.append(coeff)
                # T8: ℓ → ℓ
                coeff = pre8 * sigma_M * float(table[1, ell, m_idx, M_idx])
                if coeff != 0.0:
                    col = ell_m_to_index(ell, m_target, ell_min=ell_min)
                    rows.append(row); cols.append(col); data.append(coeff)
                # T9: ℓ → ℓ-2
                if pre9 != 0.0:
                    coeff = pre9 * sigma_M * float(table[2, ell, m_idx, M_idx])
                    if coeff != 0.0:
                        col = ell_m_to_index(ell - 2, m_target, ell_min=ell_min)
                        rows.append(row); cols.append(col); data.append(coeff)

    n = PHOTON_M_COUNT * (L_max - ell_min + 1)
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n))
