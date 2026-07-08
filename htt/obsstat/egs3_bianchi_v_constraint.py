"""EGS3 Axis F: constraint-algebra seal of the conditional Bianchi V formula (P5).

P5 (conditional) states that for a tilted LRS Bianchi type V model at small tilt
beta, the shear comparator obeys

    Sigma_+^2 = [(1+w) Omega_m]^2 beta^2 / (4 Omega_K),    Omega_K = A^2 > 0,

at leading order in beta. The load-bearing input is the MOMENTUM CONSTRAINT of the
expansion-normalized LRS-V system (Wainwright-Ellis form),

    2 A Sigma_+ = (1+w) Omega_m beta          (leading order in beta),

whose exact-rapidity form carries the flux factor sinh(beta) cosh(beta). This
module seals, fail-closed:

(1) ``symbolic_p5_formula`` -- solving the constraint for Sigma_+ and substituting
    Omega_K = A^2 reproduces the P5 formula exactly (sympy simplify == 0).
(2) ``exact_tilt_correction_series`` -- the exact-rapidity flux gives
    Sigma_+^2 = leading * (1 + (4/3) beta^2 + O(beta^4)): the first correction
    coefficient is 4/3 (sympy series).
(3) ``numeric_scaling_witness`` -- the relative error of the leading-order formula
    against the exact-rapidity constraint scales as beta^2 (log-log slope 2).
(4) The formula is UNDEFINED for Omega_K <= 0 (raises), matching P5's stated
    domain (the Omega_K -> 0 collapse of the conditional recovery).

Honest scope: this is the CONSTRAINT-ALGEBRA content of P5 -- the statement P5
actually makes -- NOT an integration of the Hewitt-Wainwright dynamical system. A
full expansion-normalized tilted-LRS-V ODE evolution (checking that trajectories
respect the constraint en route) is registered as an explicit stretch item in the
research plan, not silently claimed here.

Claim discipline. Conditional symbolic/numeric seal only; no data claim, no
detection, no family identification (the Bianchi V label is the CONDITION of the
legacy-recovery statement, not a claim about the sky), no native-solver claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import sympy as sp

__all__ = [
    "p5_leading_sigma_plus_sq",
    "exact_rapidity_sigma_plus_sq",
    "symbolic_p5_formula",
    "exact_tilt_correction_series",
    "BianchiVWitness",
    "numeric_scaling_witness",
    "bianchi_v_seal",
]


def p5_leading_sigma_plus_sq(beta: float, *, A: float, w: float,
                             Omega_m: float) -> float:
    """Leading-order P5 formula Sigma_+^2 = [(1+w) Omega_m]^2 beta^2 / (4 Omega_K),
    Omega_K = A^2. Raises for Omega_K <= 0 (P5 domain condition)."""
    Omega_K = float(A) * float(A)
    if Omega_K <= 0.0:
        raise ValueError("P5 is conditional on Omega_K > 0; the formula is "
                         "undefined (no-result) for Omega_K <= 0")
    num = ((1.0 + float(w)) * float(Omega_m)) ** 2 * float(beta) ** 2
    return num / (4.0 * Omega_K)


def exact_rapidity_sigma_plus_sq(beta: float, *, A: float, w: float,
                                 Omega_m: float) -> float:
    """Exact-rapidity momentum-constraint solution: the tilt flux carries
    sinh(beta) cosh(beta) instead of beta."""
    Omega_K = float(A) * float(A)
    if Omega_K <= 0.0:
        raise ValueError("Omega_K <= 0: undefined")
    flux = (1.0 + float(w)) * float(Omega_m) * math.sinh(beta) * math.cosh(beta)
    sigma_plus = flux / (2.0 * float(A))
    return sigma_plus * sigma_plus


def symbolic_p5_formula() -> dict:
    """Solve 2 A Sigma_+ = (1+w) Omega beta, substitute Omega_K = A^2, compare."""
    A, Sp_sym, w, Om, b, Ok = sp.symbols("A Sigma_plus w Omega beta Omega_K",
                                         positive=True)
    constraint = sp.Eq(2 * A * Sp_sym, (1 + w) * Om * b)
    sigma_plus = sp.solve(constraint, Sp_sym)[0]
    sigma_plus_sq = sp.simplify(sigma_plus ** 2)
    p5 = ((1 + w) * Om) ** 2 * b ** 2 / (4 * Ok)
    residual = sp.simplify(sigma_plus_sq.subs(A ** 2, Ok) - p5)
    return {
        "constraint": "2 A Sigma_+ = (1+w) Omega beta",
        "solved_sigma_plus": str(sigma_plus),
        "p5_formula": "((1+w) Omega)^2 beta^2 / (4 Omega_K)",
        "residual": str(residual),
        "identity_ok": bool(residual == 0),
    }


def exact_tilt_correction_series() -> dict:
    """Series of the exact-rapidity flux: Sigma_+^2/leading = 1 + (4/3) beta^2 + ..."""
    b = sp.symbols("beta", positive=True)
    ratio = (sp.sinh(b) * sp.cosh(b)) ** 2 / b ** 2
    series = sp.series(ratio, b, 0, 6).removeO()
    coeff_b2 = sp.simplify(series.coeff(b, 2))
    return {
        "ratio": "sinh(beta)^2 cosh(beta)^2 / beta^2",
        "series": str(sp.expand(series)),
        "beta2_coefficient": str(coeff_b2),
        "coefficient_is_four_thirds": bool(coeff_b2 == sp.Rational(4, 3)),
    }


@dataclass(frozen=True)
class BianchiVWitness:
    betas: tuple
    rel_errors: tuple
    loglog_slope: float
    slope_target: float
    omega_k_breakdown_raises: bool


def numeric_scaling_witness(betas=(1e-3, 3e-3, 1e-2, 3e-2), *, A: float = 0.5,
                            w: float = 0.0, Omega_m: float = 0.6
                            ) -> BianchiVWitness:
    """Relative error of the leading formula vs the exact-rapidity constraint
    scales as beta^2 (log-log slope 2); Omega_K <= 0 raises."""
    rel = []
    for b in betas:
        exact = exact_rapidity_sigma_plus_sq(b, A=A, w=w, Omega_m=Omega_m)
        lead = p5_leading_sigma_plus_sq(b, A=A, w=w, Omega_m=Omega_m)
        rel.append(abs(exact / lead - 1.0))
    logb = np.log(np.asarray(betas, dtype=float))
    logr = np.log(np.asarray(rel, dtype=float))
    slope = float(np.polyfit(logb, logr, 1)[0])
    try:
        p5_leading_sigma_plus_sq(1e-3, A=0.0, w=w, Omega_m=Omega_m)
        raises = False
    except ValueError:
        raises = True
    return BianchiVWitness(
        betas=tuple(float(b) for b in betas),
        rel_errors=tuple(float(r) for r in rel),
        loglog_slope=slope, slope_target=2.0,
        omega_k_breakdown_raises=bool(raises),
    )


def bianchi_v_seal() -> dict:
    """Aggregate seal; status FAIL if any check fails (fail-closed)."""
    symbolic = symbolic_p5_formula()
    series = exact_tilt_correction_series()
    witness = numeric_scaling_witness()
    ok = (symbolic["identity_ok"] and series["coefficient_is_four_thirds"]
          and abs(witness.loglog_slope - 2.0) < 0.05
          and witness.omega_k_breakdown_raises)
    return {
        "seal": "egs3.bianchi_v_constraint",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "symbolic": symbolic,
        "series": series,
        "numeric_witness": {
            "betas": list(witness.betas),
            "rel_errors": list(witness.rel_errors),
            "loglog_slope": witness.loglog_slope,
            "slope_target": witness.slope_target,
            "omega_k_breakdown_raises": witness.omega_k_breakdown_raises,
        },
        "scope": "constraint-algebra seal of the conditional P5 statement; NOT a "
                 "Hewitt-Wainwright dynamical-system integration (registered "
                 "stretch item)",
        "claim_boundary": "conditional legacy-recovery seal; no data, detection, "
                          "family/geometry, or native-solver claim",
    }
