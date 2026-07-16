"""EGS3 Axis D: synthetic joint-information mechanics (pre-solver).

Critical evaluation of the proposed joint likelihood ln L_Total = ln L_PV + ln L_CMB,
ported to what is honestly runnable before the native low-ell solver (BASS):

  * The reusable PV substrate is a correlated-covariance GLS using Woodbury identities.
    PR-120 permits only explicit synthetic inputs in this module while the CF4 P0
    downstream finding is OPEN.
  * A generic information multiplier can be propagated through the coupled Fisher to
    demonstrate covariance sensitivity.  It is not a JWST/CF4 precision forecast and
    carries no observational value.
  * The BipoSH helper may receive explicit synthetic alms as a method witness.  Real-sky
    observational results remain in their separately gated data lane.
  * CMB THEORY sector (BLOCKED): the mode-coupled C_{lm,l'm'}(g) / A^{LM}_{ll'}(g) prediction
    for a proposed Bianchi g needs the native solver and is FAIL-CLOSED here -- it raises
    `OutOfScopeError` (`AWAITING_NATIVE_LOWELL_SOLVER`) and NEVER returns a fabricated
    covariance. `evaluate_joint_loglike` therefore never fabricates a g-conditioned total.

Diagnostic-only synthetic mechanics; no CF4/JWST forecast, Bianchi family, geometry,
frame-violation, native-solver, or MIO-as-odds claim.
"""
from __future__ import annotations

import numpy as np

from bass.los.flrw_bessel_projector import OutOfScopeError
from htt.obsstat.egs3_kinematic_deprojection import coupled_fisher, covariance_inflation
from htt.obsstat import pv_covariance as pv

__all__ = [
    "jwst_anchor_forecast",
    "synthetic_error_shrink_sensitivity",
    "joint_fisher_sensitivity",
    "anisotropic_cmb_covariance",
    "anisotropic_cmb_loglike",
    "evaluate_joint_loglike",
    "AWAITING_NATIVE_LOWELL_SOLVER",
    "CF4_DOWNSTREAM_OPEN",
    "QuarantinedCF4DownstreamError",
]

AWAITING_NATIVE_LOWELL_SOLVER = "AWAITING_NATIVE_LOWELL_SOLVER"
CF4_DOWNSTREAM_OPEN = "N-DATA-CF4-DOWNSTREAM"


class QuarantinedCF4DownstreamError(RuntimeError):
    """Raised when an active caller requests the quarantined CF4/JWST lane."""


def _tilt_precision(n_hat, vpec, diag_sigma2, U, Lambda) -> float:
    fit = pv.pv_tilt_gls(n_hat, vpec, diag_sigma2, U, Lambda)
    return pv.omega_tilt_precision(fit.covariance)


def jwst_anchor_forecast(*args, **kwargs) -> dict:
    """Fail closed: the former observational forecast is quarantined by PR-120."""
    del args, kwargs
    raise QuarantinedCF4DownstreamError(
        "JWST/CF4 downstream forecasting is unavailable while "
        f"{CF4_DOWNSTREAM_OPEN} remains OPEN; catalogue linkage only"
    )


def synthetic_error_shrink_sensitivity(
    n_hat,
    vpec,
    diag_sigma2,
    subset_mask,
    *,
    error_scale: float = 1.0 / 3.0,
    U=None,
    Lambda=None,
) -> dict:
    """Synthetic-only GLS sensitivity to reducing errors on a toy subset."""
    d = np.asarray(diag_sigma2, dtype=float).reshape(-1).copy()
    mask = np.asarray(subset_mask, dtype=bool).reshape(-1)
    prec_base = _tilt_precision(n_hat, vpec, d, U, Lambda)
    d_candidate = d.copy()
    d_candidate[mask] = d[mask] * (float(error_scale) ** 2)
    prec_candidate = _tilt_precision(n_hat, vpec, d_candidate, U, Lambda)
    gain = float(prec_candidate / prec_base) if prec_base > 0 else 1.0
    return {
        "status": "SYNTHETIC_METHOD_WITNESS",
        "input_provenance": "deterministic_synthetic_catalogue",
        "information_multiplier": gain,
        "n_selected": int(mask.sum()),
        "n_total": int(mask.size),
        "error_scale": float(error_scale),
        "observational_interpretation": None,
        "public_use": False,
        "label": "synthetic subset-error sensitivity; not a survey forecast",
    }


def joint_fisher_sensitivity(
    *,
    rho: float,
    f_tilt_base: float = 1.0,
    f_tilt_candidate: float = 1.0,
) -> dict:
    """Generic synthetic sensitivity of covariance inflation to information weight."""
    infl_data = covariance_inflation(rho, kappa_tilt=1.0, alpha=1.0,
                                     f_omega_tilt=float(f_tilt_base))
    infl_candidate = covariance_inflation(rho, kappa_tilt=1.0, alpha=1.0,
                                          f_omega_tilt=float(f_tilt_candidate))
    return {
        "status": "SYNTHETIC_METHOD_WITNESS",
        "rho": float(rho),
        "inflation_base": float(infl_data),
        "inflation_candidate": float(infl_candidate),
        "sensitivity_ratio": (
            float(infl_data / infl_candidate) if infl_candidate > 0 else 1.0
        ),
        "observational_interpretation": None,
        "note": "generic information-weight sensitivity; no CF4/JWST prior",
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


def evaluate_joint_loglike(*, n_hat, vpec, diag_sigma2, input_provenance: str,
                           U=None, Lambda=None, alm=None, lmax: int = 8) -> dict:
    """Synthetic method record plus the fail-closed theory-g CMB sector."""
    if input_provenance != "deterministic_synthetic_catalogue":
        raise QuarantinedCF4DownstreamError(
            "only deterministic_synthetic_catalogue inputs are authorized; "
            f"observational CF4 consumers remain blocked by {CF4_DOWNSTREAM_OPEN}"
        )
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
        cmb_data = {
            "biposh_power_by_L": meas.power_by_L,
            "note": "synthetic-alm BipoSH method witness; no real-sky claim",
        }

    return {
        "schema": "htt.egs3.axis_d.synthetic_joint_method.v2",
        "pv_sector": {"status": "synthetic_method_witness", "tilt": fit.as_dict(), "loglike": float(pv_loglike)},
        "cmb_data_sector": ({"status": "synthetic_method_witness", **cmb_data} if cmb_data
                            else {"status": "not_supplied"}),
        "cmb_theory_sector": {"status": "fail_closed", "blocker": AWAITING_NATIVE_LOWELL_SOLVER,
                              "note": "g-conditioned C_{lm,l'm'}(g) needs the native solver; not fabricated"},
        "joint_total_loglike": None,
        "joint_withheld_reason": ("the g-conditioned CMB theory likelihood is fail-closed, so a "
                                  "single joint scalar would require fabricating the blocked sector; "
                                  "the PV loglike and the CMB-data BipoSH are reported separately"),
        "scope": "synthetic PV/BipoSH mechanics + theory-g CMB fail-closed; no observational interpretation",
    }
