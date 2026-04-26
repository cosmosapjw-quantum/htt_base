"""bass/integration/ark4_tableau.py — Kennedy-Carpenter ARK4(3)6L[2]SA tableau.

Implements V5_ROUND16_04 §1.1: the verbatim Butcher tableau for the
4th-order, 6-stage, L-stable, stiffly-accurate additive Runge-Kutta pair
of Kennedy & Carpenter, NASA/TM-2001-211038 (also published as
*Appl. Numer. Math.* 44 (2003) 139-181, eq. 5.16-5.18 + Tables in §5).

The coefficients are fetched verbatim from the SUNDIALS ARKode reference
implementation (LLNL/sundials, ``src/arkode/arkode_butcher_dirk.def``
and ``arkode_butcher_erk.def``, identifiers ``ARK436L2SA_DIRK_6_3_4``
and ``ARK436L2SA_ERK_6_3_4``), which has been validated against the
original paper. They are stored here as Python ``Fraction`` constants
so the tableau is bit-exact across platforms.

Per V5_ROUND16_04 §1.6 audit A2, these coefficients must match
Kennedy-Carpenter 2001 *bit-for-bit*; this is enforced by
``test_ark4_tableau.py::test_coefficients_match_sundials_reference``.

Properties (Kennedy-Carpenter 2003, §5.4):
- Implicit method: 4th order, 3rd-order embedded estimator, ESDIRK
  (Explicit first stage, Singly Diagonally Implicit RK), L-stable,
  stiffly accurate (last row of A^I equals b^I).
- Explicit method: 4th order, 3rd-order embedded estimator, ERK
  (Explicit RK), strict lower-triangular A^E.
- Both share c-vector and b-vector; only A and bhat differ between
  implicit and explicit pairs.
- ESDIRK diagonal γ = a^I_{ii} = 1/4 for stages i ∈ {1..5} (constant),
  enabling factorisation reuse across stages.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np

__all__ = [
    "ARK4Tableau",
    "ARK4_TABLEAU",
    "NUM_STAGES",
    "ESDIRK_DIAGONAL",
]


#: Number of stages (Kennedy-Carpenter 2003, §5.4).
NUM_STAGES: int = 6

#: ESDIRK diagonal γ = a^I_{ii} for i ≥ 1. Used by the implicit Newton
#: linear-solve factorisation (single LU per step instead of one per
#: stage).
ESDIRK_DIAGONAL: Fraction = Fraction(1, 4)


def _f(num: int, den: int) -> Fraction:
    return Fraction(num, den)


# ──────────────────────────────────────────────────────────────────────
# Stage abscissae c_i (shared between ERK and DIRK pairs).
# Kennedy-Carpenter 2003 §5.4 / SUNDIALS ARK436L2SA def files.
# ──────────────────────────────────────────────────────────────────────
_C: tuple[Fraction, ...] = (
    Fraction(0),
    _f(1, 2),
    _f(83, 250),
    _f(31, 50),
    _f(17, 20),
    Fraction(1),
)

# ──────────────────────────────────────────────────────────────────────
# Implicit (DIRK) A matrix — lower triangular, diagonal = 1/4.
# Verbatim from arkode_butcher_dirk.def::ARK436L2SA_DIRK_6_3_4.
# ──────────────────────────────────────────────────────────────────────
_A_I: tuple[tuple[Fraction, ...], ...] = (
    # Stage 0 (ESDIRK first stage, all zero)
    (Fraction(0),) * 6,
    # Stage 1
    (_f(1, 4), _f(1, 4)) + (Fraction(0),) * 4,
    # Stage 2
    (_f(8611, 62500), _f(-1743, 31250), _f(1, 4)) + (Fraction(0),) * 3,
    # Stage 3
    (
        _f(5012029, 34652500),
        _f(-654441, 2922500),
        _f(174375, 388108),
        _f(1, 4),
    ) + (Fraction(0),) * 2,
    # Stage 4
    (
        _f(15267082809, 155376265600),
        _f(-71443401, 120774400),
        _f(730878875, 902184768),
        _f(2285395, 8070912),
        _f(1, 4),
    ) + (Fraction(0),),
    # Stage 5 — stiffly accurate (== b row)
    (
        _f(82889, 524892),
        Fraction(0),
        _f(15625, 83664),
        _f(69875, 102672),
        _f(-2260, 8211),
        _f(1, 4),
    ),
)

# ──────────────────────────────────────────────────────────────────────
# Explicit (ERK) A matrix — strictly lower triangular.
# Verbatim from arkode_butcher_erk.def::ARK436L2SA_ERK_6_3_4.
# ──────────────────────────────────────────────────────────────────────
_A_E: tuple[tuple[Fraction, ...], ...] = (
    (Fraction(0),) * 6,
    # Stage 1
    (_f(1, 2),) + (Fraction(0),) * 5,
    # Stage 2
    (_f(13861, 62500), _f(6889, 62500)) + (Fraction(0),) * 4,
    # Stage 3
    (
        _f(-116923316275, 2393684061468),
        _f(-2731218467317, 15368042101831),
        _f(9408046702089, 11113171139209),
    ) + (Fraction(0),) * 3,
    # Stage 4
    (
        _f(-451086348788, 2902428689909),
        _f(-2682348792572, 7519795681897),
        _f(12662868775082, 11960479115383),
        _f(3355817975965, 11060851509271),
    ) + (Fraction(0),) * 2,
    # Stage 5
    (
        _f(647845179188, 3216320057751),
        _f(73281519250, 8382639484533),
        _f(552539513391, 3454668386233),
        _f(3354512671639, 8306763924573),
        _f(4040, 17871),
    ) + (Fraction(0),),
)

# ──────────────────────────────────────────────────────────────────────
# Quadrature weights b_i (shared between implicit and explicit pair).
# Same as the last row of A^I (stiffly-accurate property).
# ──────────────────────────────────────────────────────────────────────
_B: tuple[Fraction, ...] = (
    _f(82889, 524892),
    Fraction(0),
    _f(15625, 83664),
    _f(69875, 102672),
    _f(-2260, 8211),
    _f(1, 4),
)

# ──────────────────────────────────────────────────────────────────────
# Embedded 3rd-order weights bhat_i (== d_i in SUNDIALS naming).
# Shared between implicit and explicit pair.
# ──────────────────────────────────────────────────────────────────────
_BHAT: tuple[Fraction, ...] = (
    _f(4586570599, 29645900160),
    Fraction(0),
    _f(178811875, 945068544),
    _f(814220225, 1159782912),
    _f(-3700637, 11593932),
    _f(61727, 225920),
)


def _as_array(rows: tuple[tuple[Fraction, ...], ...]) -> np.ndarray:
    """Convert a fraction matrix to float64 once for the runtime path.

    The Fraction-typed source-of-truth above ensures bit-exact equality
    across platforms in tests; the runtime stepper consumes the float64
    cast for performance.
    """
    return np.array(
        [[float(v) for v in row] for row in rows],
        dtype=np.float64,
    )


def _as_vec(values: tuple[Fraction, ...]) -> np.ndarray:
    return np.array([float(v) for v in values], dtype=np.float64)


@dataclass(frozen=True)
class ARK4Tableau:
    """Frozen Kennedy-Carpenter ARK4(3)6L[2]SA tableau.

    Attributes
    ----------
    num_stages : int
        Number of stages s = 6.
    gamma : float
        ESDIRK diagonal γ = 1/4 (constant for stages 1..5).
    c : ndarray, shape (s,)
        Stage abscissae c_i ∈ [0, 1].
    a_I : ndarray, shape (s, s)
        Implicit DIRK matrix (lower triangular).
    a_E : ndarray, shape (s, s)
        Explicit ERK matrix (strictly lower triangular).
    b : ndarray, shape (s,)
        Main 4th-order quadrature weights (shared).
    bhat : ndarray, shape (s,)
        Embedded 3rd-order weights (shared).
    c_fractions, a_I_fractions, a_E_fractions, b_fractions, bhat_fractions
        Source-of-truth Fraction tuples for the bit-identity audit.
    """

    num_stages: int = field(default=NUM_STAGES, init=False)
    gamma: float = field(default=float(ESDIRK_DIAGONAL), init=False)
    c: np.ndarray = field(default_factory=lambda: _as_vec(_C), init=False)
    a_I: np.ndarray = field(default_factory=lambda: _as_array(_A_I), init=False)
    a_E: np.ndarray = field(default_factory=lambda: _as_array(_A_E), init=False)
    b: np.ndarray = field(default_factory=lambda: _as_vec(_B), init=False)
    bhat: np.ndarray = field(default_factory=lambda: _as_vec(_BHAT), init=False)

    c_fractions: tuple[Fraction, ...] = field(default=_C, init=False)
    a_I_fractions: tuple[tuple[Fraction, ...], ...] = field(
        default=_A_I, init=False
    )
    a_E_fractions: tuple[tuple[Fraction, ...], ...] = field(
        default=_A_E, init=False
    )
    b_fractions: tuple[Fraction, ...] = field(default=_B, init=False)
    bhat_fractions: tuple[Fraction, ...] = field(default=_BHAT, init=False)

    # Order conditions follow from Kennedy-Carpenter 2003 Theorem 5.1;
    # checked in tests (sum of b == 1, c_i = sum_j a_ij, etc.).


#: Singleton runtime tableau. Frozen.
ARK4_TABLEAU: ARK4Tableau = ARK4Tableau()
