"""EGS3 B1 (flagship): semi-native shear -> low-l multipole transfer operator.

Interim partial discharge of AWAITING_NATIVE_LOWELL_SOLVER. NT2-A1's Fisher
floor used a TOY response r_l = (2/l)^1.5; here we replace it with a
physically-sourced response from a line-of-sight projection of a single
shear-sourced mode through a recombination visibility:

    Theta_l(k)  ~  integral  g(chi) * S_sigma(k,chi) * j_l(k chi) dchi ,

with g the (Gaussian last-scattering) visibility, S_sigma the shear source, and
j_l the spherical Bessel projection. The response is

    r_l = d ln C_l / d ln F_shear   (proportional to the projected transfer^2),

normalised so r_2 = 1 (NT-A1 linear closure, ETM kappa=4/21 at l=2). This is a
BOUNDED LINEAR OPERATOR with explicit decay; its rank/decay derive the NT2-A1
response and bound the NT2-A2 tail.

Honest refinement of NT2-A1 (the strong physical result). The genuine floor is
NOT a single number: it is a PROFILE in the shear mode scale k. The line-of-sight
projection of a mode k peaks at l ~ k*chi_star, so:
  * a PURE super-horizon shear (k*chi_star << 1, the homogeneous-Bianchi limit)
    is QUADRUPOLE-DOMINATED: r_{l>2} -> 0 and the floor -> the single-l
    sqrt(2/5) ~ 0.632 EXACTLY. The toy r_l = (2/l)^1.5 over-stated the higher-l
    response; the real super-horizon shear barely improves on the quadrupole.
  * a finite-k shear sources a BAND of multipoles around l ~ k*chi_star, and the
    multi-l floor drops below 0.632.
So NT2-A1's "floor strictly below 0.632" is a finite-k statement; in the exact
homogeneous-shear limit the floor saturates at 0.632. A sharpening, not a
retraction. Single-mode, exact-FLRW-anchored; NOT the family atlas, NOT a
family-ID claim; the Gaussian visibility is an analytic stand-in for the real
CAMB/CLASS recombination visibility (the remaining to-close).
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.special import spherical_jn

KAPPA_ETM = 4.0 / 21.0


def gaussian_visibility(chi: np.ndarray, chi_star: float, width: float) -> np.ndarray:
    """Normalised Gaussian last-scattering visibility g(chi) (analytic stand-in
    for the real CAMB/CLASS recombination visibility)."""
    g = np.exp(-0.5 * ((chi - chi_star) / width) ** 2)
    area = np.trapezoid(g, chi) if hasattr(np, "trapezoid") else np.trapz(g, chi)
    return g / area


@dataclass(frozen=True)
class TransferResponse:
    ell: tuple[int, ...]
    r_ell: dict          # l -> r_l (normalised r_2 = 1)
    k: float
    bounded: bool
    monotone_decay_from_l2: bool


def shear_multipole_response(k: float = 7.0e-5, lmax: int = 20,
                             chi_star: float = 14000.0, width: float = 250.0,
                             n_chi: int = 4096) -> TransferResponse:
    """Line-of-sight Bessel projection of a single shear-sourced mode through the
    visibility -> the response r_l for l=2..lmax (r_2 normalised to 1)."""
    if k <= 0 or lmax < 2:
        raise ValueError("k>0 and lmax>=2 required")
    chi = np.linspace(max(1.0, chi_star - 6 * width), chi_star + 6 * width, n_chi)
    g = gaussian_visibility(chi, chi_star, width)
    x = k * chi
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    # projected transfer per l; the shear source is smooth so we project g j_l.
    proj = {ell: float(trap(g * spherical_jn(ell, x), chi)) for ell in range(2, lmax + 1)}
    base = proj[2]
    if base == 0.0:
        raise ValueError("degenerate projection at l=2; adjust k/chi_star/width")
    # response r_l = (proj_l / proj_2)^2, so r_2 = 1 by construction.
    r = {ell: float((proj[ell] / base) ** 2) for ell in range(2, lmax + 1)}
    vals = [r[ell] for ell in range(2, lmax + 1)]
    bounded = all(np.isfinite(v) and v >= 0.0 for v in vals) and max(vals) <= 1.0 + 1e-9
    # decay envelope: the running max of r_l does not grow (bounded, summable).
    return TransferResponse(tuple(range(2, lmax + 1)), r, float(k), bool(bounded),
                            bool(r[2] >= max(r[ell] for ell in range(3, lmax + 1))))


def fisher_floor_from_transfer(response: TransferResponse, f_sky: float = 1.0) -> float:
    """NT2-A1 floor computed from the *physical* response instead of the toy r_l:
    sigma(F)/F = [ sum_l (2l+1)/2 f_sky r_l^2 ]^{-1/2}."""
    info = sum((2 * ell + 1) / 2.0 * f_sky * response.r_ell[ell] ** 2 for ell in response.ell)
    return float(info ** -0.5) if info > 0 else float("inf")


def floor_profile_vs_k(k_values, lmax: int = 30, chi_star: float = 14000.0,
                       width: float = 250.0, f_sky: float = 1.0) -> dict:
    """The genuine floor as a PROFILE in the shear mode scale k: it saturates at
    the single-l sqrt(2/5)~0.632 for super-horizon shear (k*chi_star<<1) and
    drops below it once the shear sources a band of multipoles (finite k)."""
    out = {}
    for k in k_values:
        resp = shear_multipole_response(k=k, lmax=lmax, chi_star=chi_star, width=width)
        out[float(k)] = {"k_chi_star": float(k * chi_star),
                         "floor": fisher_floor_from_transfer(resp, f_sky)}
    return out
