"""NT2-B1: two-sided quadrupole+octupole shear / F_shear bracket.

EGS2 extension of the report's beyond-MES (which gives only an UPPER shear
bound). Here, conditional on the almost-EGS hypothesis H3 (R_EGS = a3/a2 <= R*),
a NONZERO CMB quadrupole forces a NONZERO LOWER shear:

    a2 * kappa / (1 + R_EGS)  <=  Sigma  <=  C_up * a2 ,

so F_shear is BRACKETED away from zero:
    F_shear in [ (a2 kappa/(1+R_EGS))^2 / x_max , (C_up a2)^2 / x_max ].

The lower bound is the strong new content: an isotropic-looking shear-filling is
EXCLUDED at a fixed nonzero quadrupole. Upper = MES; lower = the l=2 relation
a2 = kappa Sigma + (derivative correction), with H3 bounding the correction.

Analytic-check construct: the MES upper constant C_up and the covariant
derivative-correction coefficient are documented placeholders; the *exclusion of
zero* (F_lo > 0 whenever a2 > 0 under H3) is the robust statement. No detection.
"""
from __future__ import annotations

from dataclasses import dataclass

from .egs2_fisher import KAPPA_ETM, X_MAX

C_UP = 9.0          # MES upper coefficient (documented placeholder)
R_STAR = 1.0        # default H3 threshold a3/a2 <= R*


def shear_upper(a2: float, c_up: float = C_UP) -> float:
    """MES upper bound: Sigma <= C_up * a2."""
    if a2 < 0.0:
        raise ValueError("a2 must be nonnegative")
    return c_up * a2


def shear_lower(a2: float, a3: float, kappa: float = KAPPA_ETM) -> float:
    """H3 lower bound: Sigma >= a2 * kappa / (1 + a3/a2)."""
    if a2 <= 0.0:
        return 0.0
    if a3 < 0.0:
        raise ValueError("a3 must be nonnegative")
    R = a3 / a2
    return a2 * kappa / (1.0 + R)


@dataclass(frozen=True)
class FillingBracket:
    a2: float
    a3: float
    R_EGS: float
    h3_satisfied: bool
    sigma_lo: float
    sigma_hi: float
    F_lo: float
    F_hi: float
    excludes_zero: bool


def filling_bracket(a2: float, a3: float, *, kappa: float = KAPPA_ETM,
                    c_up: float = C_UP, r_star: float = R_STAR,
                    x_max: float = X_MAX) -> FillingBracket:
    """Two-sided bracket on F_shear from the observed quadrupole+octupole."""
    R = a3 / a2 if a2 > 0 else float("inf")
    h3 = R <= r_star
    s_lo = shear_lower(a2, a3, kappa)
    s_hi = shear_upper(a2, c_up)
    f_lo = s_lo ** 2 / x_max
    f_hi = s_hi ** 2 / x_max
    return FillingBracket(a2, a3, R, h3, s_lo, s_hi, f_lo, f_hi,
                          excludes_zero=bool(h3 and a2 > 0 and f_lo > 0.0))
