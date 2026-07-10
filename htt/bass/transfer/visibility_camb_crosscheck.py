"""EGS2/EGS3 B1 closure: semi-native shear transfer vs the REAL CAMB visibility.

Closes the ``semi_native_shear_to_quadrupole`` exit gate ("exact-FLRW-anchored
single-mode shear transfer cross-checked vs CAMB/CLASS visibility"). The
v7-frozen module ``htt.bass.transfer.shear_quadrupole_seminative`` uses an
analytic Gaussian last-scattering visibility as a stand-in; this successor
recomputes the SAME line-of-sight Bessel projection through the actual CAMB
recombination visibility g(eta) (camb.get_background_time_evolution) and
cross-checks the three load-bearing conclusions of the frozen lane:

1. super-horizon saturation: for k*chi_star << 1 the single-mode Fisher floor
   saturates at sqrt(2/5) ~ 0.632 with BOTH visibilities;
2. finite-k improvement: once the mode sources a band of multipoles the floor
   drops strictly below 0.632 with BOTH visibilities;
3. band structure: the response peaks in an l-band around l ~ k*chi_star.

The projected r_l profile and floors are compared quantitatively; the measured
relative floor differences are recorded (the CAMB visibility is much NARROWER
than the registered stand-in -- FWHM ~ 38 Mpc in conformal time vs the 250 Mpc
Gaussian width -- so exact profile agreement is neither expected nor claimed).
The frozen module is imported read-only for the Gaussian branch and the floor
functional; nothing frozen is modified.

Pinned background: H0 = 67.5, ombh2 = 0.022, omch2 = 0.122, YHe = 0.24
(explicit YHe: the camb 1.6.x BBN interpolator is numpy-2 incompatible in this
environment; the pinned value is recorded in the seal). The visibility is
normalised over the last-scattering window (the reionisation tail is outside
the window and outside this lane's scope).

Claim discipline. Single-mode, exact-FLRW-anchored diagnostic cross-check; the
AWAITING_NATIVE_LOWELL_SOLVER blocker stays partially discharged only (the full
transfer needs the shear-power mode integral / the native line-of-sight); no
data claim, no signal-discovery claim, no Bianchi-class/geometry claim, no
probabilistic-inference claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.special import spherical_jn

from htt.bass.transfer.shear_quadrupole_seminative import (
    TransferResponse, shear_multipole_response, fisher_floor_from_transfer,
)

__all__ = [
    "CAMB_PINNED_PARAMS",
    "camb_visibility_window",
    "camb_multipole_response",
    "visibility_crosscheck",
    "seminative_camb_crosscheck_seal",
]

CAMB_PINNED_PARAMS = {"H0": 67.5, "ombh2": 0.022, "omch2": 0.122, "YHe": 0.24}
SINGLE_L_FLOOR = float(np.sqrt(2.0 / 5.0))          # sqrt(2/5) ~ 0.6325
_ETA_WINDOW = (150.0, 500.0)                        # last-scattering window (Mpc)
_N_ETA = 3000


@lru_cache(maxsize=1)
def camb_visibility_window() -> dict:
    """Real CAMB recombination visibility on the last-scattering window.

    Returns chi grid (ascending), normalised g(chi), the peak chi_star, the
    FWHM-equivalent Gaussian sigma, and the camb version."""
    import camb

    pars = camb.CAMBparams()
    pars.set_cosmology(**CAMB_PINNED_PARAMS)
    data = camb.get_background(pars)
    eta0 = float(data.conformal_time(0.0))
    eta = np.linspace(_ETA_WINDOW[0], _ETA_WINDOW[1], _N_ETA)
    ev = data.get_background_time_evolution(eta, ["visibility"])
    g_eta = np.asarray(ev["visibility"], dtype=float)
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    g_eta = g_eta / float(trap(g_eta, eta))
    chi = eta0 - eta                       # descending in eta -> ascending flip
    order = np.argsort(chi)
    chi, g_chi = chi[order], g_eta[order]  # g(chi) dchi = g(eta) deta (|dchi/deta|=1)
    i_pk = int(np.argmax(g_chi))
    half = g_chi > 0.5 * g_chi[i_pk]
    fwhm = float(chi[half][-1] - chi[half][0])
    return {
        "chi": chi,
        "g": g_chi,
        "chi_star": float(chi[i_pk]),
        "sigma_fwhm_equiv": fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0))),
        "eta0": eta0,
        "camb_version": camb.__version__,
    }


def camb_multipole_response(k: float, lmax: int = 20) -> TransferResponse:
    """Line-of-sight Bessel projection of a single shear-sourced mode through
    the REAL CAMB visibility (same projection as the frozen Gaussian lane)."""
    if k <= 0 or lmax < 2:
        raise ValueError("k>0 and lmax>=2 required")
    vis = camb_visibility_window()
    chi, g = vis["chi"], vis["g"]
    x = k * chi
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    proj = {ell: float(trap(g * spherical_jn(ell, x), chi))
            for ell in range(2, lmax + 1)}
    base = proj[2]
    if base == 0.0:
        raise ValueError("degenerate projection at l=2")
    r = {ell: float((proj[ell] / base) ** 2) for ell in range(2, lmax + 1)}
    vals = [r[ell] for ell in range(2, lmax + 1)]
    bounded = all(np.isfinite(v) and v >= 0.0 for v in vals)
    return TransferResponse(tuple(range(2, lmax + 1)), r, float(k), bool(bounded),
                            bool(r[2] >= max(r[ell] for ell in range(3, lmax + 1))))


@dataclass(frozen=True)
class CrosscheckRow:
    k: float
    k_chi_star: float
    floor_camb: float
    floor_gaussian_matched: float
    floor_gaussian_registered: float
    rel_diff_matched: float


def _floor_gauss(k: float, lmax: int, chi_star: float, width: float) -> float:
    resp = shear_multipole_response(k=k, lmax=lmax, chi_star=chi_star, width=width)
    return fisher_floor_from_transfer(resp)


def visibility_crosscheck(lmax: int = 30) -> dict:
    """The B1 cross-check: super-horizon saturation, finite-k improvement and
    band structure hold with the REAL visibility; measured floor differences
    vs the Gaussian stand-in are recorded (matched = Gaussian at the CAMB
    chi_star/width; registered = the frozen lane's 14000/250 stand-in)."""
    vis = camb_visibility_window()
    chi_star, sig = vis["chi_star"], vis["sigma_fwhm_equiv"]
    rows = []
    for k in (1.0e-6, 7.0e-5, 1.0e-3):
        resp_c = camb_multipole_response(k, lmax=lmax)
        f_c = fisher_floor_from_transfer(resp_c)
        f_gm = _floor_gauss(k, lmax, chi_star, sig)
        f_gr = _floor_gauss(k, lmax, 14000.0, 250.0)
        rows.append(CrosscheckRow(
            k=float(k), k_chi_star=float(k * chi_star), floor_camb=f_c,
            floor_gaussian_matched=f_gm, floor_gaussian_registered=f_gr,
            rel_diff_matched=float(abs(f_c - f_gm) / f_c)))

    superhorizon, finite_k = rows[0], rows[2]
    resp_band = camb_multipole_response(finite_k.k, lmax=lmax)
    band_peak_ell = max(resp_band.r_ell, key=resp_band.r_ell.get)
    checks = {
        "superhorizon_saturates_at_single_l_floor_camb":
            bool(abs(superhorizon.floor_camb - SINGLE_L_FLOOR) < 5e-3),
        "superhorizon_saturates_at_single_l_floor_gaussian":
            bool(abs(superhorizon.floor_gaussian_matched - SINGLE_L_FLOOR) < 5e-3),
        "finite_k_floor_below_single_l_camb":
            bool(finite_k.floor_camb < SINGLE_L_FLOOR - 1e-3),
        "finite_k_floor_below_single_l_gaussian":
            bool(finite_k.floor_gaussian_matched < SINGLE_L_FLOOR - 1e-3),
        "band_peak_tracks_k_chi_star":
            bool(abs(band_peak_ell - finite_k.k_chi_star)
                 <= max(4.0, 0.5 * finite_k.k_chi_star)),
        "r2_is_unity_by_construction":
            bool(resp_band.r_ell[2] == 1.0),
        "matched_gaussian_floor_within_20pct_everywhere":
            bool(all(r.rel_diff_matched < 0.20 for r in rows)),
    }
    return {
        "camb_version": vis["camb_version"],
        "pinned_params": CAMB_PINNED_PARAMS,
        "chi_star_camb": round(chi_star, 2),
        "sigma_fwhm_equiv_camb": round(sig, 3),
        "registered_standin": {"chi_star": 14000.0, "width": 250.0},
        "rows": [{
            "k": r.k,
            "k_chi_star": round(r.k_chi_star, 4),
            "floor_camb": round(r.floor_camb, 6),
            "floor_gaussian_matched": round(r.floor_gaussian_matched, 6),
            "floor_gaussian_registered": round(r.floor_gaussian_registered, 6),
            "rel_diff_matched": round(r.rel_diff_matched, 6),
        } for r in rows],
        "band_peak_ell": int(band_peak_ell),
        "single_l_floor": round(SINGLE_L_FLOOR, 6),
        "checks": checks,
    }


def seminative_camb_crosscheck_seal() -> dict:
    """Fail-closed seal for the CAMB-visibility cross-check (B1 exit gate)."""
    try:
        cc = visibility_crosscheck()
    except Exception as exc:  # camb unavailable -> registered blocker, not silence
        return {
            "seal": "egs2.seminative_camb_crosscheck",
            "status": "BLOCKED_CAMB_UNAVAILABLE",
            "error": f"{type(exc).__name__}: {exc}",
            "claim_boundary": "cross-check unavailable in this environment; "
                              "no conclusion recorded",
        }
    ok = all(cc["checks"].values())
    return {
        "seal": "egs2.seminative_camb_crosscheck",
        "status": "PASS" if ok else "FAIL",
        "closes_exit_gate": "semi_native_shear_to_quadrupole: exact-FLRW-anchored "
                            "single-mode shear transfer cross-checked vs CAMB/CLASS "
                            "visibility",
        "crosscheck": cc,
        "residual_blocker": "AWAITING_NATIVE_LOWELL_SOLVER stays partially "
                            "discharged (full transfer = shear-power mode "
                            "integral / native line of sight)",
        "claim_boundary": "single-mode exact-FLRW-anchored diagnostic cross-check; "
                          "no data, signal-discovery, Bianchi-class/geometry, or "
                          "probabilistic-inference claim",
    }
