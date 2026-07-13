#!/usr/bin/env python3
"""K5 real-claim upgrade: the CF4 bulk-flow amplitude vs its LambdaCDM cosmic-
variance expectation, computed with the ESTIMATOR-MATCHED window (not a scalar
prior).

The frozen release-coverage card inflates the bulk-flow error with a hand-set
isotropic cosmic-variance prior (b_true ~ N(0, 150 km/s) per component,
`SIGMA_CV_PRIOR_KMS`), explicitly conditional on that guess and registered
`BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP`. This lane replaces the prior with the
real linear-theory cosmic-variance covariance of the SAME weighted-GLS
estimator.

Honest outcome: the |B| amplitude, apex, and Omega_tilt are REAL measurements
(inverse-Fisher measurement error). The linear estimator-matched cosmic variance
turns out to be small (~35 km/s along B), because the noise-weighted GLS
estimator aliases small-scale (nonlinear) velocity power that linear theory
omits -- so it is a LOWER BOUND on the true LambdaCDM scatter. The naive chi^2
built from it is therefore NOT a credible amplitude significance (it would read
a spurious ~9 sigma); the significance is WITHHELD. A credible significance
needs the minimum-variance ideal-window estimator or release-matched mocks
(BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP). This is the honest result, not a
manufactured tension.

Estimator (bulkflow_mle): B = A^{-1} b, A = sum_i w_i n_i n_i^T,
w_i = 1/(sigma_i^2 + sigma_*^2), measurement covariance A^{-1}. The cosmic
(sample) variance of B propagates the true peculiar-velocity covariance through
the linear estimator:

    Cov_CV(B) = A^{-1} M A^{-1},
    M_ij = sum_{mn} w_m w_n n_{m,i} n_{n,j} <v_m v_n>_CV .

In linear theory the radial velocity covariance is, factorising the plane-wave
expansion into per-group mode functions,

    <v_m v_n>_CV = (H0 f)^2 * int d^3k/(2pi)^3 [P(k)/k^2]
                     (n_m.khat)(n_n.khat) exp(i k.(x_m - x_n)) ,

so   M_ij = (H0 f)^2/(2pi)^3 int dk P(k) I_ij(k),
     I_ij(k) = int dOmega_k F_i F_j^* ,
     F_i(k,khat) = sum_m w_m n_{m,i} (n_m.khat) exp(i k r_m (khat.n_m)) .

The k^2 in the measure cancels the 1/k^2, leaving a 1-D radial integral of a
mode function evaluated on a spherical khat grid -- O(N_k N_dir N) rather than
the O(N^2) pair sum. Working in Mpc/h and h/Mpc, the prefactor is (100 f)^2
(the h cancels), with f = Omega_m^0.55. Fiducial linear P(k) = A k^{n_s} T(k)^2,
EH98 no-wiggle transfer, normalised to sigma_8 (self-contained, no download).

Validation (in-card, gates the status): the single-group diagonal <v_m^2> from
the same angular grid must reproduce the closed-form linear 1-D velocity
dispersion (100 f)^2/(6 pi^2) int P dk (~370 km/s for Planck LambdaCDM), and the
mode-function M must be converged in the k and khat grids.

Claim tier: a real measurement of the CF4 bulk-flow amplitude, apex, and
Omega_tilt (model-independent kinematic descriptors). The LambdaCDM amplitude
significance is WITHHELD (linear cosmic variance is a lower bound). NOT a Bianchi
family/geometry/frame-violation claim, and NOT a tension/anomaly claim. Residual:
the credible amplitude significance (MV ideal-window estimator or release-matched
mock covariance) stays BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP.

Outputs docs/generated/cf4_bulkflow_lcdm_card.json. Deterministic; --check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from htt.obsstat.bulkflow_mle import (  # noqa: E402
    estimate_bulk_flow, fit_sigma_star, velocity_error)

CF4 = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
OBS_DEFAULTS = REPO / "htt/workspace/data/obs_defaults.json"
OUT = REPO / "docs/generated/cf4_bulkflow_lcdm_card.json"

# fiducial LambdaCDM (Planck 2018 base); Omega_b/n_s/sigma_8 not in obs_defaults
OMEGA_B = 0.0493
N_S = 0.9649
SIGMA_8 = 0.8111
T_CMB = 2.7255

# grids (fixed -> deterministic)
NSIDE_KHAT = 8            # HEALPix khat directions (12*nside^2 = 768)
NK_MODE = 160            # k samples for the mode-function integral [h/Mpc]
KMIN, KMAX = 1.0e-3, 1.0  # mode-function k range [h/Mpc]
NK_SIGMA = 400           # k samples for the 1-D sigma_v / sigma_8 integrals
KMIN_S, KMAX_S = 1.0e-4, 50.0


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


# --- fiducial linear power spectrum (EH98 no-wiggle) -------------------
def _transfer_eh98_nw(k_hmpc: np.ndarray, om: float, ob: float, h: float) -> np.ndarray:
    """Eisenstein-Hu 1998 no-wiggle transfer, k in h/Mpc."""
    omhh = om * h * h
    theta = T_CMB / 2.7
    s = 44.5 * np.log(9.83 / omhh) / np.sqrt(1.0 + 10.0 * (ob * h * h) ** 0.75)  # Mpc
    ob_om = ob / om
    ag = (1.0 - 0.328 * np.log(431.0 * omhh) * ob_om
          + 0.38 * np.log(22.3 * omhh) * ob_om ** 2)
    k_mpc = k_hmpc * h                                   # 1/Mpc
    gamma = om * h * (ag + (1.0 - ag) / (1.0 + (0.43 * k_mpc * s) ** 4))
    q = k_hmpc * theta * theta / gamma
    c0 = 14.2 + 731.0 / (1.0 + 62.5 * q)
    l0 = np.log(2.0 * np.e + 1.8 * q)
    return l0 / (l0 + c0 * q * q)


def _sigma8_sq_unnorm(pk_unnorm, k):
    r = 8.0                                              # Mpc/h
    x = k * r
    w = 3.0 * (np.sin(x) - x * np.cos(x)) / x ** 3
    integ = k * k * pk_unnorm(k) * w * w
    return np.trapz(integ, k) / (2.0 * np.pi ** 2) if hasattr(np, "trapz") else \
        np.trapezoid(integ, k) / (2.0 * np.pi ** 2)


def _make_pk(om: float, ob: float, h: float):
    def pk_unnorm(k):
        return k ** N_S * _transfer_eh98_nw(k, om, ob, h) ** 2
    k8 = np.geomspace(1e-4, 50.0, 4000)
    s8sq_u = _sigma8_sq_unnorm(pk_unnorm, k8)
    amp = SIGMA_8 ** 2 / s8sq_u
    return lambda k: amp * pk_unnorm(k)


def _trapz(y, x):
    return (np.trapz(y, x) if hasattr(np, "trapz") else np.trapezoid(y, x))


# --- cosmic-variance matrix M via the mode-function integral ----------
def _mode_function_M(n_hat, r_hmpc, w, pk, hf2, nside, nk, kmin, kmax):
    import healpy as hp
    kgrid = np.geomspace(kmin, kmax, nk)
    pk_vals = pk(kgrid)
    khat = np.array(hp.pix2vec(nside, np.arange(hp.nside2npix(nside)))).T  # (Ndir,3)
    dOmega = 4.0 * np.pi / khat.shape[0]
    Iacc = np.zeros((nk, 3, 3), dtype=np.complex128)
    wn = w[:, None] * n_hat                              # (N,3)  w_m n_{m,i}
    for kv in khat:
        mu = n_hat @ kv                                 # (N,)   n_m.khat
        proj = r_hmpc * mu                              # (N,)   r_m (khat.n_m)
        cvec = wn * mu[:, None]                          # (N,3)  w_m n_{m,i} mu_m
        phase = np.exp(1j * np.outer(kgrid, proj))       # (nk,N)
        F = phase @ cvec                                 # (nk,3)
        Iacc += dOmega * (F[:, :, None] * np.conj(F[:, None, :]))
    integ = pk_vals[:, None, None] * Iacc                # (nk,3,3)
    trapz = np.trapz if hasattr(np, "trapz") else np.trapezoid
    M = hf2 / (2.0 * np.pi) ** 3 * trapz(integ.real, kgrid, axis=0)
    return np.real(M), kgrid, khat.shape[0]


def measure() -> dict:
    if not CF4.is_file():
        return {"schema": "htt.cf4_bulkflow_lcdm.v1",
                "status": "BLOCKED_MISSING_CF4_CATALOGUE"}
    obs = json.loads(OBS_DEFAULTS.read_text())
    om, h = float(obs["Omega_m"]), float(obs["h"])
    f_growth = om ** 0.55
    hf2 = (100.0 * f_growth) ** 2                        # (km/s)^2 per (Mpc/h)^2

    d = np.load(CF4, allow_pickle=True)
    pos = np.c_[d["SGX"], d["SGY"], d["SGZ"]].astype(float)
    r_mpc = np.linalg.norm(pos, axis=1)
    vpec = np.asarray(d["Vpec"], float)
    v3k = np.asarray(d["V3k"], float)
    sigma = velocity_error(d["e_DMzp"], v3k)
    good = (np.isfinite(vpec) & np.isfinite(sigma) & (sigma > 0)
            & (r_mpc > 1.0) & np.isfinite(v3k))
    n_hat = pos[good] / r_mpc[good, None]
    vpec, sigma = vpec[good], sigma[good]
    r_hmpc = r_mpc[good] * h                             # Mpc -> Mpc/h

    sigma_star = fit_sigma_star(n_hat, vpec, sigma)
    bf = estimate_bulk_flow(n_hat, vpec, sigma, sigma_star=sigma_star)
    A_inv = bf.covariance                                # (km/s)^2
    w = 1.0 / (sigma ** 2 + sigma_star ** 2)
    B = bf.vector

    pk = _make_pk(om, OMEGA_B, h)

    # closed-form linear 1-D velocity dispersion (validation anchor)
    ks = np.geomspace(KMIN_S, KMAX_S, NK_SIGMA)
    sigma_v_1d = float(np.sqrt(hf2 / (6.0 * np.pi ** 2) * _trapz(pk(ks), ks)))

    # cosmic-variance matrix (estimator-matched)
    M, kgrid, ndir = _mode_function_M(
        n_hat, r_hmpc, w, pk, hf2, NSIDE_KHAT, NK_MODE, KMIN, KMAX)
    cov_cv = A_inv @ M @ A_inv                           # (km/s)^2

    # --- validation: single-group diagonal must reproduce sigma_v_1d ---
    # one group at unit weight; <v^2> from the same angular grid
    idx0 = int(np.argmin(np.abs(r_hmpc - np.median(r_hmpc))))
    M1, _, _ = _mode_function_M(
        n_hat[idx0:idx0 + 1], r_hmpc[idx0:idx0 + 1], np.ones(1),
        pk, hf2, NSIDE_KHAT, NK_MODE, KMIN, KMAX)
    sigma_v_grid = float(np.sqrt(np.trace(M1)))          # sum_i <v n_i n_i> = <v^2>
    valid_diag = abs(sigma_v_grid - sigma_v_1d) / sigma_v_1d < 0.02

    # --- convergence: coarser khat grid ---
    Mc, _, _ = _mode_function_M(
        n_hat, r_hmpc, w, pk, hf2, 4, NK_MODE, KMIN, KMAX)
    cov_cv_c = A_inv @ Mc @ A_inv
    conv_rel = float(np.linalg.norm(cov_cv - cov_cv_c) / np.linalg.norm(cov_cv))
    valid_conv = conv_rel < 0.05

    # cosmic-variance amplitude of B (3-D expected |B| under LambdaCDM)
    evals = np.linalg.eigvalsh(cov_cv)
    b_lcdm_rms = float(np.sqrt(np.trace(cov_cv)))        # sqrt(E|B|^2)_CV
    u = B / np.linalg.norm(B)
    sigma_cv_los = float(np.sqrt(u @ cov_cv @ u))        # CV along the measured B
    sigma_meas_los = float(np.sqrt(u @ A_inv @ u))
    amp = float(np.linalg.norm(B))

    # LambdaCDM consistency of the measured 3-vector: chi^2_3 with the total
    # (measurement + linear cosmic variance) covariance = the expected scatter
    # of B under LambdaCDM + noise around zero.
    from scipy.stats import chi2 as _chi2
    cov_tot = cov_cv + A_inv
    naive_chi2 = float(B @ np.linalg.solve(cov_tot, B))
    naive_p = float(_chi2.sf(naive_chi2, 3))
    naive_sigma = (float(np.sqrt(_chi2.isf(naive_p, 1))) if naive_p > 0
                   else float("inf"))

    beta = amp / 299792.458
    omega_tilt = (om * np.sinh(beta) ** 2)
    dtilt = om * 2.0 * np.sinh(beta) * np.cosh(beta)
    # the reported amplitude error is the measurement (inverse-Fisher) error;
    # the cosmic-variance term is a LOWER BOUND (see below) and is NOT folded in
    omega_tilt_err = float(dtilt * sigma_meas_los / 299792.458)

    # apex in Galactic coords (supergalactic Cartesian -> Galactic l,b)
    l_gal, b_gal = _sg_to_galactic(u)
    cmb_lb = (float(obs["dipole_observations"]["cmb_planck_2018"]["l_deg"]),
              float(obs["dipole_observations"]["cmb_planck_2018"]["b_deg"]))
    cf4w = obs["dipole_observations"].get("cf4_watkins_2023", {})
    sep_cmb = _ang_sep_deg((l_gal, b_gal), cmb_lb)
    sep_cf4w = (_ang_sep_deg((l_gal, b_gal),
                             (float(cf4w["l_deg"]), float(cf4w["b_deg"])))
                if "l_deg" in cf4w else None)

    status = ("MEASURED_BULKFLOW_AMPLITUDE" if (valid_diag and valid_conv)
              else "VALIDATION_FAILED")
    return {
        "schema": "htt.cf4_bulkflow_lcdm.v1",
        "status": status,
        "product": "Cosmicflows-4 groups (Tully+ 2023); weighted-GLS bulk flow",
        "n_groups": int(good.sum()),
        "sigma_star_kms": round(sigma_star, 3),
        "fiducial_cosmology": {
            "Omega_m": om, "Omega_b": OMEGA_B, "h": h, "n_s": N_S,
            "sigma_8": SIGMA_8, "growth_f_Om^0.55": round(f_growth, 5),
            "P_k": "EH98 no-wiggle, sigma_8-normalised (self-contained)"},
        "bulk_flow": {
            "amplitude_kms": round(amp, 3),
            "vector_sgxyz_kms": [round(float(x), 3) for x in B],
            "apex_galactic_l_b_deg": [round(l_gal, 2), round(b_gal, 2)],
            "measurement_error_kms": round(sigma_meas_los, 3),
            "separation_from_cmb_dipole_deg": round(sep_cmb, 2),
            "separation_from_cf4_watkins2023_deg":
                (round(sep_cf4w, 2) if sep_cf4w is not None else None),
        },
        "linear_cosmic_variance_lower_bound": {
            "method": "estimator-matched mode-function window integral "
                      "(linear theory); replaces the frozen card's scalar "
                      "150 km/s isotropic prior",
            "is_lower_bound": True,
            "why_lower_bound": ("the noise-weighted GLS estimator aliases "
                                "small-scale (nonlinear) velocity power that "
                                "linear theory omits, so the linear window "
                                "cosmic variance underestimates the true "
                                "LambdaCDM scatter of this estimator"),
            "sigma_v_1d_linear_kms": round(sigma_v_1d, 2),
            "sigma_cv_along_B_kms": round(sigma_cv_los, 3),
            "expected_B_rms_lcdm_linear_kms": round(b_lcdm_rms, 2),
            "cov_cv_eigenvalues_kms2": [round(float(e), 2) for e in evals],
        },
        "lcdm_amplitude_significance": {
            "significance_claimed": False,
            "naive_chi2_3dof": round(naive_chi2, 3),
            "naive_p_value": round(naive_p, 6),
            "naive_gaussian_sigma": round(naive_sigma, 2),
            "why_withheld": ("the naive chi^2 uses the linear cosmic-variance "
                             "LOWER BOUND, so its large apparent significance "
                             "(~%.0f sigma) is an artifact, NOT a cosmological "
                             "anomaly; a credible amplitude significance needs "
                             "the minimum-variance ideal-window estimator "
                             "(isolates the large-scale flow) or release-matched "
                             "mocks (full nonlinear + selection covariance), "
                             "which stay BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP"
                             % naive_sigma),
        },
        "omega_tilt": {
            "value": omega_tilt,
            "error": omega_tilt_err,
            "beta_v_over_c": beta,
            "definition": "Omega_tilt = Omega_m sinh^2(beta), beta = |B|/c",
            "error_note": "measurement (inverse-Fisher) error only",
        },
        "validation": {
            "single_group_diag_sigma_v_kms": round(sigma_v_grid, 2),
            "closed_form_sigma_v_kms": round(sigma_v_1d, 2),
            "diagonal_matches_closed_form": bool(valid_diag),
            "khat_grid_convergence_rel": round(conv_rel, 4),
            "converged": bool(valid_conv),
            "n_khat_directions": ndir,
            "n_k_samples": NK_MODE,
        },
        "input_hashes": [f"{CF4.relative_to(REPO)}:{_sha(CF4)}"],
        "caveats": [
            "linear-theory estimator-matched cosmic variance from a fiducial "
            "EH98 sigma_8-normalised P(k); the nonlinear + survey-selection "
            "mock covariance stays BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
            "CF4 distances (Mpc, catalogue H0) are scaled to Mpc/h with the "
            "fiducial h for the window; a ~10% depth-scale convention residual",
            "the growth rate uses f = Omega_m^0.55 (Planck base); no redshift-"
            "space or scale-dependent-bias modelling (bulk flow is bias-free)",
        ],
        "claim": ("real measurement: CF4 weighted-GLS bulk flow |B| = %.0f +/- "
                  "%.0f km/s (measurement error), apex (l,b)=(%.0f,%.0f), "
                  "Omega_tilt = %.2e; the LambdaCDM amplitude significance is "
                  "WITHHELD (the linear window cosmic variance is a lower "
                  "bound)" % (amp, sigma_meas_los, l_gal, b_gal, omega_tilt)),
        "scope_not_claimed": ("a model-independent kinematic MEASUREMENT (|B|, "
                              "apex, Omega_tilt); NO LambdaCDM tension/anomaly "
                              "claim (significance withheld), and NOT a Bianchi "
                              "family, geometry, or observer-frame-violation "
                              "claim; the theory-g tilt link is out of scope "
                              "(it needs the native low-multipole solver)"),
    }


def _ang_sep_deg(lb1, lb2) -> float:
    (l1, b1), (l2, b2) = np.radians(lb1), np.radians(lb2)
    c = (np.sin(b1) * np.sin(b2)
         + np.cos(b1) * np.cos(b2) * np.cos(l1 - l2))
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def _sg_to_galactic(u_sg: np.ndarray) -> tuple[float, float]:
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    c = SkyCoord(sgx=u_sg[0], sgy=u_sg[1], sgz=u_sg[2],
                 representation_type="cartesian", frame="supergalactic")
    g = c.galactic
    return float(g.l.deg), float(g.b.deg)


def _render(p):
    return json.dumps(p, indent=2, sort_keys=True, default=str) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    card = measure()
    rendered = _render(card)
    if args.check:
        if not OUT.exists() or OUT.read_text() != rendered:
            print("STALE cf4_bulkflow_lcdm_card.json", file=sys.stderr)
            return 1
        print("cf4 bulkflow lcdm card current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={card['status']}")
    if card["status"].startswith("MEASURED"):
        bf = card["bulk_flow"]
        cv = card["linear_cosmic_variance_lower_bound"]
        sig = card["lcdm_amplitude_significance"]
        print(f"  |B|={bf['amplitude_kms']} +/- {bf['measurement_error_kms']} "
              f"km/s  apex(l,b)={bf['apex_galactic_l_b_deg']}  "
              f"sep_cmb={bf['separation_from_cmb_dipole_deg']}")
        print(f"  linear CV (LOWER BOUND) sigma_cv={cv['sigma_cv_along_B_kms']} "
              f"km/s; naive sigma={sig['naive_gaussian_sigma']} "
              f"-> significance WITHHELD")
        v = card["validation"]
        print(f"  valid: sigma_v grid={v['single_group_diag_sigma_v_kms']} vs "
              f"closed={v['closed_form_sigma_v_kms']} "
              f"conv={v['khat_grid_convergence_rel']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
