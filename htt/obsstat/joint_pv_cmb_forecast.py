"""EGS3 Axis D: BASS-Extended joint PV+CMB information forecast (pre-solver).

Critical evaluation of the proposed joint likelihood ln L_Total = ln L_PV + ln L_CMB,
ported to what is honestly runnable before the native low-ell solver (BASS):

  * PV sector (REAL, now): a feasible correlated-covariance bulk-flow / tilt GLS on
    the real CF4 catalogue (`pv_covariance`, Woodbury; never a dense N x N inversion).
    A JWST-anchored distance prior tightens the Omega_tilt precision (FORECAST until the
    anchors are materially matched; the actual gain is reported, not inflated).
  * The joint benefit -- "PV pins Omega_tilt so the CMB inversion cannot leak power into a
    false Sigma^2" -- is realized solver-free at the Fisher level: the PV Omega_tilt prior
    precision enters the rev-r141 coupled Fisher `f_omega_tilt` diagonal, which strictly
    reduces the Sigma^2 covariance inflation 1/(1-r^2) and breaks the Sigma^2-Omega_tilt
    degeneracy.
  * CMB DATA sector (REAL, now): the off-diagonal BipoSH statistic from the real SMICA map
    (`biposh_smica`), null-calibrated -- a measurement, not a theory fit.
  * CMB THEORY sector (BLOCKED): the mode-coupled C_{lm,l'm'}(g) / A^{LM}_{ll'}(g) prediction
    for a proposed Bianchi g needs the native solver and is FAIL-CLOSED here -- it raises
    `OutOfScopeError` (`AWAITING_NATIVE_LOWELL_SOLVER`) and NEVER returns a fabricated
    covariance. `evaluate_joint_loglike` therefore never fabricates a g-conditioned total.

Diagnostic-only: model-independent kinematics + a real SI descriptor + a labelled forecast;
no Bianchi family, geometry, frame-violation, native-solver, or MIO-as-odds claim; Sigma^2 on
the real sky stays partial.
"""
from __future__ import annotations

import numpy as np

from htt.bass.los.flrw_bessel_projector import OutOfScopeError
from htt.obsstat.egs3_kinematic_deprojection import coupled_fisher, covariance_inflation
from htt.obsstat import pv_covariance as pv

__all__ = [
    "jwst_anchor_forecast",
    "joint_fisher_forecast",
    "anisotropic_cmb_covariance",
    "anisotropic_cmb_loglike",
    "evaluate_joint_loglike",
    "AWAITING_NATIVE_LOWELL_SOLVER",
]

AWAITING_NATIVE_LOWELL_SOLVER = "AWAITING_NATIVE_LOWELL_SOLVER"


def _tilt_precision(n_hat, vpec, diag_sigma2, U, Lambda) -> float:
    fit = pv.pv_tilt_gls(n_hat, vpec, diag_sigma2, U, Lambda)
    return pv.omega_tilt_precision(fit.covariance)


def jwst_anchor_forecast(n_hat, vpec, diag_sigma2, anchor_mask, *,
                         jwst_shrink: float = 1.0 / 3.0,
                         U=None, Lambda=None) -> dict:
    """Forecast the Omega_tilt precision gain from shrinking the JWST-anchored groups'
    distance errors by `jwst_shrink` (a hypothetical prior until the anchors are matched).

    f_omega_tilt_data is normalised to 1; f_omega_tilt_jwst = gain = precision_jwst /
    precision_data (>= 1). Uses the feasible correlated-covariance GLS (`pv_covariance`)."""
    d = np.asarray(diag_sigma2, dtype=float).reshape(-1).copy()
    mask = np.asarray(anchor_mask, dtype=bool).reshape(-1)
    prec_data = _tilt_precision(n_hat, vpec, d, U, Lambda)
    d_jwst = d.copy()
    d_jwst[mask] = d[mask] * (float(jwst_shrink) ** 2)     # sigma_v -> shrink * sigma_v
    prec_jwst = _tilt_precision(n_hat, vpec, d_jwst, U, Lambda)
    gain = float(prec_jwst / prec_data) if prec_data > 0 else 1.0
    return {
        "f_omega_tilt_data": 1.0,
        "f_omega_tilt_jwst": gain,
        "precision_gain": gain,
        "n_anchor": int(mask.sum()),
        "n_total": int(mask.size),
        "jwst_shrink": float(jwst_shrink),
        "label": "forecast (hypothetical JWST prior until anchors materially matched)",
    }


def joint_fisher_forecast(*, rho: float, f_omega_tilt_data: float = 1.0,
                          f_omega_tilt_jwst: float = 1.0) -> dict:
    """The PV Omega_tilt prior reduces the Sigma^2 covariance inflation at fixed boost-tilt
    coupling rho. Uses the rev-r141 coupled Fisher with beta=rho, kappa_tilt=alpha=1 so the
    off-diagonal is rho^2; the prior enters the `f_omega_tilt` diagonal."""
    infl_data = covariance_inflation(rho, kappa_tilt=1.0, alpha=1.0,
                                     f_omega_tilt=float(f_omega_tilt_data))
    infl_jwst = covariance_inflation(rho, kappa_tilt=1.0, alpha=1.0,
                                     f_omega_tilt=float(f_omega_tilt_jwst))
    return {
        "rho": float(rho),
        "inflation_data": float(infl_data),
        "inflation_jwst": float(infl_jwst),
        "degeneracy_break_factor": float(infl_data / infl_jwst) if infl_jwst > 0 else 1.0,
        "note": "higher PV/JWST Omega_tilt precision -> lower Sigma^2 covariance inflation",
    }


def anisotropic_cmb_covariance(g, l_max: int = 30):
    """Theory mode-coupled C_{lm,l'm'}(g) -- FAIL-CLOSED (native low-ell solver required).

    For l_max this is a dense ((l_max+1)^2 - 4) x ((l_max+1)^2 - 4) matrix whose off-diagonal
    A^{LM}_{ll'}(g) entries require the covariant Bianchi transfer (Wigner-3j mode-coupling
    from g). Never fabricated here."""
    raise OutOfScopeError(
        f"Theory C_{{lm,l'm'}}(g) for l_max={l_max} requires the native low-ell Bianchi "
        f"solver ({AWAITING_NATIVE_LOWELL_SOLVER}); the drop-in point is "
        "bass.spectrum.cl_assembly.off_diagonal_biposh. Fabricating it is forbidden.")


def anisotropic_cmb_loglike(g, alm, l_max: int = 30):
    """Theory-g CMB log-likelihood -- FAIL-CLOSED: needs `anisotropic_cmb_covariance`."""
    raise OutOfScopeError(
        f"g-conditioned CMB log-likelihood requires the theory C_{{lm,l'm'}}(g) "
        f"({AWAITING_NATIVE_LOWELL_SOLVER}); use the data-side BipoSH statistic "
        "(biposh_smica) for a solver-free SI measurement instead.")


def evaluate_joint_loglike(*, n_hat, vpec, diag_sigma2, U=None, Lambda=None,
                           alm=None, lmax: int = 8) -> dict:
    """The honest joint record: a REAL PV GLS fit + (optionally) the REAL SMICA BipoSH data
    statistic + the FAIL-CLOSED theory-g CMB sector. NEVER returns a fabricated g-conditioned
    total log-likelihood (that needs BASS)."""
    d = np.asarray(diag_sigma2, dtype=float).reshape(-1)
    fit = pv.pv_tilt_gls(n_hat, vpec, d, U, Lambda)
    # PV Gaussian log-likelihood at the ML tilt (real number characterising the PV fit)
    resid = np.asarray(vpec, dtype=float) - np.asarray(n_hat, dtype=float) @ fit.vector
    if U is None or Lambda is None:
        quad = float(np.sum(resid * resid / d))
        logdet = float(np.sum(np.log(d)))
    else:
        quad = float(resid @ pv.woodbury_solve(d, U, Lambda, resid))
        logdet = pv.woodbury_logdet(d, U, Lambda)
    pv_loglike = -0.5 * (quad + logdet + resid.size * np.log(2.0 * np.pi))

    cmb_data = None
    if alm is not None:
        from htt.obsstat.biposh_smica import compute_biposh_from_alm
        meas = compute_biposh_from_alm(alm, lmax, L_values=(1, 2))
        cmb_data = {"biposh_power_by_L": meas.power_by_L,
                    "note": "real single-sky SI descriptor (null calibration in k1_biposh_smica)"}

    return {
        "schema": "htt.egs3.axis_d.joint_loglike.v1",
        "pv_sector": {"status": "measured", "tilt": fit.as_dict(), "loglike": float(pv_loglike)},
        "cmb_data_sector": ({"status": "measured_partial", **cmb_data} if cmb_data
                            else {"status": "not_supplied"}),
        "cmb_theory_sector": {"status": "fail_closed", "blocker": AWAITING_NATIVE_LOWELL_SOLVER,
                              "note": "g-conditioned C_{lm,l'm'}(g) needs the native solver; not fabricated"},
        "joint_total_loglike": None,
        "joint_withheld_reason": ("the g-conditioned CMB theory likelihood is fail-closed, so a "
                                  "single joint scalar would require fabricating the blocked sector; "
                                  "the PV loglike and the CMB-data BipoSH are reported separately"),
        "scope": "PV real + SMICA BipoSH real + theory-g CMB fail-closed; Sigma^2 stays partial",
    }
