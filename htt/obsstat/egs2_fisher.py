"""NT2-A1 / NT2-A2: genuine multi-multipole Fisher-Cramer-Rao floor on F_shear.

EGS2 extension of the report's NT-A3. The report's NT-A3 is the single-sky
sampling dispersion of *one* estimator (sqrt(2/5) ~ 0.632 at l=2), which is NOT
a Cramer-Rao bound. Here we supply the genuine floor: the multi-multipole Fisher
information of the shear-filling F_shear from the joint low-l Gaussian
likelihood. Because the shear sources l=2 AND (via the EGS gradient/octupole
chain) higher multipoles with response r_l = d ln C_l / d ln F_shear, an
estimator using l=2..L carries more information, so the Cramer-Rao floor is
STRICTLY below 0.632 and decreases with L; sky cuts (f_sky<1) raise it.

  I = sum_{l>=2} (2l+1)/2 * f_sky * r_l^2 ,   sigma(F)/F >= I^{-1/2}.

NT2-A2 (octupole sufficiency): for a decaying r_l the marginal Fisher tail from
l>3 converges, so (a2,a3) is approximately sufficient for F_shear.

These are analytic-check constructs. The toy response r_l is a documented EGS
gradient/octupole proxy; the *shape* (floor < 0.632 for any r_{l>2}>0) is robust,
the exact numeric value needs the covariant l=2/l=3 coefficients and a real
low-l transfer (see the semi-native calculator ticket). No detection is implied.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

KAPPA_ETM = 4.0 / 21.0   # ETM l=2 <-> shear coefficient (figure value)
X_MAX = 9.25e-6          # S2a combined-comparator ceiling (report value)


def response_coeffs(lmax: int, model: str = "egs_gradient") -> dict[int, float]:
    """r_l = d ln C_l / d ln F_shear for l=2..lmax. r_2=1 (F linear in C_2).

    'egs_gradient': higher multipoles inherit a decaying shear-gradient response
    r_l ~ (2/l)^1.5 (documented toy of the EGS octupole/gradient chain).
    'quad_only': r_2=1, r_{>2}=0 (recovers the single-l case).
    """
    if lmax < 2:
        raise ValueError("lmax must be >= 2")
    out = {2: 1.0}
    for ell in range(3, lmax + 1):
        out[ell] = 0.0 if model == "quad_only" else (2.0 / ell) ** 1.5
    return out


def fisher_information(lmax: int, f_sky: float = 1.0, model: str = "egs_gradient") -> float:
    """I = sum_{l=2..lmax} (2l+1)/2 * f_sky * r_l^2."""
    if not (0.0 < f_sky <= 1.0):
        raise ValueError("f_sky must be in (0,1]")
    r = response_coeffs(lmax, model)
    return sum((2 * ell + 1) / 2.0 * f_sky * r[ell] ** 2 for ell in r)


def fisher_floor(lmax: int, f_sky: float = 1.0, model: str = "egs_gradient") -> float:
    """Cramer-Rao fractional floor sigma(F)/F using multipoles l=2..lmax."""
    info = fisher_information(lmax, f_sky, model)
    return 1.0 / math.sqrt(info) if info > 0 else float("inf")


def single_ell_sampling_dispersion(ell: int = 2, f_sky: float = 1.0) -> float:
    """The report's NT-A3 quantity: sqrt(2/((2l+1) f_sky)) -- ONE estimator."""
    if not (0.0 < f_sky <= 1.0):
        raise ValueError("f_sky must be in (0,1]")
    return math.sqrt(2.0 / ((2 * ell + 1) * f_sky))


def octupole_sufficiency_tail(lmax: int, f_sky: float = 1.0, model: str = "egs_gradient") -> dict:
    """NT2-A2: marginal Fisher information beyond the octupole (l>3) and its
    fraction of the total -- bounded/convergent for any decaying r_l."""
    total = fisher_information(lmax, f_sky, model)
    r = response_coeffs(lmax, model)
    tail = sum((2 * ell + 1) / 2.0 * f_sky * r[ell] ** 2 for ell in r if ell > 3)
    return {"info_total": total, "info_tail_l_gt_3": tail,
            "tail_fraction": (tail / total) if total > 0 else 0.0}


@dataclass(frozen=True)
class FloorMCResult:
    lmax: int
    f_sky: float
    fisher_floor: float
    mc_dispersion: float
    ratio: float


def mc_estimator_dispersion(lmax: int, f_sky: float = 1.0, n_real: int = 4000,
                            seed: int = 21, model: str = "egs_gradient") -> FloorMCResult:
    """Monte-Carlo: generate F-dependent C_l power estimates (chi^2 with
    (2l+1)f_sky dof), form the inverse-variance-weighted multi-l MLE of F_shear,
    and measure its fractional dispersion. Verifies the Fisher floor is achieved
    (ratio -> 1), and that the multi-l estimator beats the single-l one."""
    rng = np.random.default_rng(seed)
    r = response_coeffs(lmax, model)
    active = {ell: r[ell] for ell in r if r[ell] != 0.0}
    F_true = 1.0
    ests = np.empty(n_real)
    for i in range(n_real):
        num = 0.0
        den = 0.0
        for ell, r_ell in active.items():
            dof = max(int((2 * ell + 1) * f_sky), 1)
            chi2 = rng.chisquare(dof) / dof
            frac_dC = chi2 - 1.0                       # (C_hat - C_fid)/C_fid
            F_ell = F_true * (1.0 + frac_dC / r_ell)
            var_ell = (2.0 / dof) / r_ell ** 2
            w = 1.0 / var_ell
            num += w * F_ell
            den += w
        ests[i] = num / den if den else F_true
    mean = float(ests.mean())
    disp = float(ests.std() / mean)
    floor = fisher_floor(lmax, f_sky, model)
    return FloorMCResult(lmax, f_sky, floor, disp, disp / floor if floor else float("inf"))
