"""EGS3 v8-update U4: statistical closure of the Teff fingerprint lane -- the
T4'/T5' machinery (Hotelling calibration + Imbens-Manski partial
identification) applied to the two-temperature fingerprint ratios.

Completes the unification: U1/U2 (egs3_teff_unification) put the Teff
fingerprints on the comparator tilt coordinate with MES-registry ceilings;
this module runs the EGS3 statistical methodology on them.

Forward model (synthetic, seeded, disclosed). MB energies from the two-
temperature mixture 0.5 Gamma(3, T_+) + 0.5 Gamma(3, T_-), T_+/- = c (1 +/- s)
(the MB energy density x^2 e^{-x/T} IS Gamma(shape 3); the R_p combinatorics
are statistics-independent because every p-moment scales as T^p, so the MB
choice loses no generality for the ratio observables -- disclosed). Estimators
anchor on the retained p=4 moment: T_eff^4 := m_4 Gamma(3)/Gamma(7), then
R_hat_p := (m_p Gamma(3)/Gamma(3+p)) / T_eff^p, whose population values are
EXACTLY the two_temperature_ratio R_p(s) of the Teff lane.

Statistical closures (frozen modules imported read-only):
* T5' pattern -- PARTIAL IDENTIFICATION + IM COVERAGE: with retained-moment
  information only, the mixing is nonidentified on [0, s_max]; the identified
  interval for R_3 is [R_3(s_max), 1]. The Imbens-Manski interval
  (egs3_identified_set.im_interval) is checked by a seeded coverage experiment
  at the interval endpoints and interior (the coverage-critical points).
* T4' pattern -- HOTELLING CALIBRATION: the joint (R_hat_3, R_hat_5) with an
  ESTIMATED covariance over-rejects under the naive chi^2_2 threshold and is
  calibrated by the Hotelling/F threshold
  (egs3_coverage_strengthened.hotelling_scale) -- measured empirically.

SCALE HONESTY: the sampling experiments run at DISPLAY mixings s in
{0.15, 0.3} (disclosed diagnostic scale); at the CF4/MES scale
(s ~ 1.1e-3, fingerprints ~ 2e-6) sampling noise dominates any feasible
event count, so the CF4-scale entry is carried as the DETERMINISTIC
fingerprint row of the K5 v8 card, never as a pretended measurement.

Claim discipline: synthetic seeded experiments + exact anchors at tier
diagnostic_only; no data claim, no signal-discovery claim, no
Bianchi-class-identification-of-the-sky claim, no native-solver-produced
claim, no probabilistic-inference claim about the sky.
"""
from __future__ import annotations

from math import gamma as _gamma

import numpy as np
import sympy as sp

from htt.obsstat.egs3_identified_set import im_interval
from htt.obsstat.egs3_coverage_strengthened import hotelling_scale
from htt.teff.representative import two_temperature_ratio

__all__ = [
    "true_ratio",
    "sample_fingerprints",
    "im_fingerprint_coverage",
    "hotelling_fingerprint_calibration",
    "teff_statistical_seal",
]

_S_MAX_DISPLAY = 0.3     # diagnostic display mixing (disclosed)


def true_ratio(p: int, s: float) -> float:
    """Population R_p(s) from the Teff lane (exact expression, evaluated)."""
    expr, svar = two_temperature_ratio(p)
    return float(expr.subs(svar, sp.Float(s, 30)))


def sample_fingerprints(s: float, n_events: int, rng) -> tuple[float, float]:
    """One replicate: (R_hat_3, R_hat_5) from the two-temperature MB mixture."""
    half = n_events // 2
    x = np.concatenate([rng.gamma(3.0, 1.0 + s, size=half),
                        rng.gamma(3.0, 1.0 - s, size=n_events - half)])
    m3 = float(np.mean(x ** 3))
    m4 = float(np.mean(x ** 4))
    m5 = float(np.mean(x ** 5))
    teff = (m4 * _gamma(3) / _gamma(7)) ** 0.25
    r3 = (m3 * _gamma(3) / _gamma(6)) / teff ** 3
    r5 = (m5 * _gamma(3) / _gamma(8)) / teff ** 5
    return r3, r5


def im_fingerprint_coverage(*, s_max: float = _S_MAX_DISPLAY,
                            n_events: int = 4000, n_rep: int = 800,
                            alpha: float = 0.05,
                            seed: int = 20260710) -> dict:
    """T5' pattern on the fingerprint: identified interval [R_3(s_max), 1]
    for the nonidentified mixing s in [0, s_max]; empirical IM coverage at
    the endpoints and midpoint."""
    rng = np.random.default_rng(seed)
    lo_true = true_ratio(3, s_max)          # R_3 decreasing in s
    hi_true = 1.0                           # s = 0
    rows = {}
    for label, s_true in (("endpoint_s0", 0.0),
                          ("interior_mid", s_max / 2.0),
                          ("endpoint_smax", s_max)):
        target = true_ratio(3, s_true)
        covered = 0
        for _ in range(n_rep):
            r3_hat, _ = sample_fingerprints(s_true, n_events, rng)
            # estimator se at this mixing (plug-in from a calibration block)
            se = rows.get("_se_" + label)
            if se is None:
                block = [sample_fingerprints(s_true, n_events, rng)[0]
                         for _ in range(300)]
                se = float(np.std(block, ddof=1))
                rows["_se_" + label] = se
            # observed identified interval centered on the estimate:
            # [r3_hat - width, r3_hat] with deterministic width (hi - lo)
            width = hi_true - lo_true
            lo_ci, hi_ci, cn = im_interval(r3_hat - width, r3_hat, se, se,
                                           alpha)
            covered += int(lo_ci <= target <= hi_ci)
        rows[label] = {"s_true": s_true, "target_R3": round(target, 8),
                       "coverage": covered / n_rep,
                       "se": round(rows["_se_" + label], 8)}
    for k in [k for k in rows if k.startswith("_se_")]:
        rows.pop(k)
    nominal = 1.0 - alpha
    # binomial 3-sigma band around the nominal level
    tol = 3.0 * (nominal * (1 - nominal) / n_rep) ** 0.5
    all_cover = all(r["coverage"] >= nominal - tol for r in rows.values())
    return {
        "identified_interval_R3": [round(lo_true, 8), 1.0],
        "s_max_display_disclosed": s_max,
        "alpha": alpha,
        "n_events": n_events,
        "n_rep": n_rep,
        "rows": rows,
        "nominal": nominal,
        "binomial_3sigma_tol": round(tol, 6),
        "coverage_holds_everywhere": bool(all_cover),
    }


def hotelling_fingerprint_calibration(*, s_true: float = 0.15,
                                      n_events: int = 4000, n_sim: int = 10,
                                      n_rep: int = 1500, alpha: float = 0.05,
                                      seed: int = 20260710) -> dict:
    """T4' pattern on the joint fingerprint (R_hat_3, R_hat_5): naive chi^2_2
    with an ESTIMATED covariance over-rejects; the Hotelling/F threshold
    calibrates. Empirical sizes measured under the true mixing."""
    from scipy import stats

    rng = np.random.default_rng(seed)
    mu = np.array([true_ratio(3, s_true), true_ratio(5, s_true)])
    df = 2
    scale = hotelling_scale(df, n_sim)
    chi2_thr = stats.chi2.ppf(1 - alpha, df)
    f_thr = scale * stats.f.ppf(1 - alpha, df, n_sim - df)
    rej_naive = rej_hotelling = 0
    for _ in range(n_rep):
        sims = np.array([sample_fingerprints(s_true, n_events, rng)
                         for _ in range(n_sim)])
        cov = np.cov(sims.T)
        obs = np.array(sample_fingerprints(s_true, n_events, rng))
        d = obs - mu
        t2 = float(d @ np.linalg.solve(cov, d))
        rej_naive += int(t2 > chi2_thr)
        rej_hotelling += int(t2 > f_thr)
    size_naive = rej_naive / n_rep
    size_hot = rej_hotelling / n_rep
    tol = 3.0 * (alpha * (1 - alpha) / n_rep) ** 0.5
    return {
        "s_true_display_disclosed": s_true,
        "n_sim_cov": n_sim,
        "n_rep": n_rep,
        "alpha": alpha,
        "empirical_size_naive_chi2": size_naive,
        "empirical_size_hotelling_F": size_hot,
        "naive_over_rejects": bool(size_naive > alpha + tol),
        "hotelling_calibrated": bool(abs(size_hot - alpha) <= tol),
        "binomial_3sigma_tol": round(tol, 6),
    }


def teff_statistical_seal() -> dict:
    """Fail-closed U4 seal."""
    cov = im_fingerprint_coverage()
    hot = hotelling_fingerprint_calibration()
    ok = (cov["coverage_holds_everywhere"] and hot["naive_over_rejects"]
          and hot["hotelling_calibrated"])
    return {
        "seal": "egs3.teff_statistical",
        "status": "PASS" if ok else "FAIL",
        "numpy_version": np.__version__,
        "theorem_U4": "the EGS3 partial-identification + calibration "
                      "machinery closes over the Teff fingerprint lane: IM "
                      "coverage holds on the identified interval "
                      "[R_3(s_max), 1] of the nonidentified mixing, and the "
                      "estimated-covariance joint fingerprint requires the "
                      "Hotelling/F correction exactly as in T4'",
        "im_fingerprint_coverage": cov,
        "hotelling_fingerprint_calibration": hot,
        "scale_honesty": "sampling experiments at display mixings (0.15/0.3, "
                         "disclosed); the CF4/MES-scale fingerprints (~2e-6) "
                         "enter only as the DETERMINISTIC row of the K5 v8 "
                         "card, never as a pretended measurement",
        "claim_boundary": "synthetic seeded experiments over the Teff "
                          "fingerprint observables; diagnostic_only; no data, "
                          "signal-discovery, "
                          "Bianchi-class-identification-of-the-sky, "
                          "native-solver-produced, or probabilistic-inference "
                          "claim about the sky",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(teff_statistical_seal(), indent=2, default=float))
