"""EGS3 external-data lanes (REV-R191): connect the acquired-but-unwired
datasets (DESI LSS, ACT DR6 lensing) into the EGS3 framework, and record the
JWST anchor connection.

Each lane binds the REAL on-disk data through a real loader and a real
estimator, computes every diagnostic that the present products support, and
terminates the parts that need a missing companion product with a registered
blocker code (the same discipline as K1/K5/K6): no substitute estimate beyond
a clearly labelled mock stand-in, and no anisotropy, geometry, family, or
solver claim.

Lanes:

  * DESI number-count dipole (Omega_tilt-sector cross-check). The DESI DR1
    BGS clustering catalogue (4.08M galaxies with unit sky vectors and
    imaging-systematics/FKP weights) supports the linear (Crawford/Secrest)
    number-count dipole estimator. The estimator is VERIFIED on full-sky
    mocks (recovers an injected dipole). Applied to the real footprint it
    returns a WINDOW-dominated value (fsky ~ 0.19), NOT a cosmological
    dipole: separating the survey selection function requires the DESI random
    catalogues (window-function deconvolution), which are not in-tree ->
    BLOCKED_MISSING_DESI_RANDOMS. The cosmological number-count dipole scale
    (comparable to the CMB kinematic dipole, ~7e-3) is quoted for reference
    only.

  * ACT DR6 CMB-lensing auto-bandpower (independent-instrument cross-check).
    The released convergence a_lm (lmax=4000) + N_L noise curve support a
    real auto-bandpower readout. A low-multipole isotropy statistic (the
    dipole/quadrupole of kappa) is dominated by the reconstruction mean
    field at ell <~ 10 and requires the ACT lensing simulation ensemble
    (mean field + N0/N1), which is not in-tree ->
    BLOCKED_MISSING_ACT_LENSING_SIMS.

  * JWST distance anchors: the 14 Cepheid/TRGB/maser anchors cross-matched to
    CF4 already feed the Omega_tilt survey-design forecast
    (scripts/jwst_cf4_crossmatch.py -> joint_pv_cmb_forecast); this lane
    records that connection.

Claim discipline: real-data diagnostics + mock-verified estimators + registered
blockers; model-independent kinematic descriptors only; no anisotropy or family
claim, no geometry or observer-frame claim, no inference or discovery claim.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
DESI_NGC = REPO / "workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz"
DESI_SGC_RAW = REPO / "workdir/raw/desi/BGS_ANY_SGC_clustering.dat.fits"
ACT_ALM = (REPO / "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/"
           "baseline/kappa_alm_data_act_dr6_lensing_v1_baseline.fits")
ACT_NL = (REPO / "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/"
          "baseline/N_L_kk_act_dr6_lensing_v1_baseline.txt")
JWST_ANCHORS = REPO / "docs/generated/jwst_cf4_anchors.json"
DESI_DIPOLE_CARD = REPO / "docs/generated/desi_dipole_card.json"
ACT_KAPPA_CARD = REPO / "docs/generated/act_kappa_card.json"

# Planck 2018 CMB dipole direction (Galactic), for the DESI direction contrast.
CMB_DIPOLE_LB = (264.021, 48.253)
# The kinematic number-count dipole scale D_kin = [2 + x(1+alpha)] beta with
# beta = v/c = 1.23e-3, x ~ 0.75, alpha ~ 1 -> ~7e-3 (reference only).
CMB_KINEMATIC_NUMBER_COUNT_DIPOLE = 7.0e-3
# ACT DR6 baseline mask fsky, computed once from the released NSIDE=4096 mask
# (mean of the apodized weight map); stored to avoid a 1.5 GB read per run.
ACT_BASELINE_FSKY = 0.23388
MOCK_SEED = 20260712


def _round(x, n=6):
    return round(float(x), n)


# --- DESI number-count dipole -----------------------------------------
def _linear_dipole(nhat: np.ndarray, w: np.ndarray) -> tuple[float, np.ndarray]:
    """Linear number-count dipole estimator D = 3 <n_hat>_w; returns the
    amplitude D and the unit direction."""
    mean_vec = (w[:, None] * nhat).sum(axis=0) / w.sum()
    amp = float(np.linalg.norm(mean_vec))
    return 3.0 * amp, mean_vec / amp


@lru_cache(maxsize=1)
def desi_number_count_dipole() -> dict:
    import healpy as hp
    if not DESI_NGC.exists():
        return {"lane": "desi_number_count_dipole",
                "status": "BLOCKED_MISSING_DESI_CATALOGUE",
                "detail": f"{DESI_NGC} not present"}
    d = np.load(DESI_NGC)
    nhat = d["n_hat"].astype(np.float64)
    w = (d["weight_sys"] * d["weight_fkp"]).astype(np.float64)
    n_gal = int(len(w))

    # --- estimator verification on a full-sky mock with an injected dipole ---
    # N and amplitude chosen so the dipole is well above the shot-noise floor
    # sqrt(3/N): N=2e6, A=0.02 -> SNR ~ 16 -> clean deterministic recovery.
    rng = np.random.default_rng(MOCK_SEED)
    n_mock = 2_000_000
    inj_amp = 2.0e-2
    inj_dir = np.array([0.3, -0.4, np.sqrt(1 - 0.09 - 0.16)])
    v = rng.normal(size=(n_mock, 3))
    v /= np.linalg.norm(v, axis=1)[:, None]                 # uniform sphere
    p_keep = 1.0 + inj_amp * (v @ inj_dir)                  # dipole modulation
    mock = v[rng.random(n_mock) < p_keep / p_keep.max()]
    D_rec, u_rec = _linear_dipole(mock, np.ones(len(mock)))
    mock_dir_err_deg = float(np.degrees(
        np.arccos(np.clip(u_rec @ inj_dir, -1, 1))))
    mock_recovers = bool(abs(D_rec - inj_amp) < 3.0e-3
                         and mock_dir_err_deg < 10.0)

    # --- real footprint (window-dominated) ---
    D_real, u_real = _linear_dipole(nhat, w)
    l, b = hp.vec2ang(np.asarray([u_real]), lonlat=True)
    cmb = hp.ang2vec(*CMB_DIPOLE_LB, lonlat=True)
    sep = float(np.degrees(np.arccos(np.clip(u_real @ cmb, -1, 1))))
    nside = 64
    pix = hp.vec2pix(nside, nhat[:, 0], nhat[:, 1], nhat[:, 2])
    fsky = float((np.bincount(pix, minlength=hp.nside2npix(nside)) > 0).sum()
                 / hp.nside2npix(nside))

    # window-corrected measurement (once the DESI randoms are on disk, the
    # standalone scripts/desi_dipole_measure.py writes the card; the lane then
    # flips blocked -> measured)
    measured = None
    if DESI_DIPOLE_CARD.exists():
        card = json.loads(DESI_DIPOLE_CARD.read_text())
        if card.get("status") == "MEASURED_WINDOW_CORRECTED":
            measured = card
    out = {
        "lane": "desi_number_count_dipole",
        "sector": "Omega_tilt (LSS number-count dipole vs CMB kinematic dipole)",
        "sample": "DESI DR1 BGS_ANY NGC",
        "n_galaxies": n_gal,
        "estimator": "linear D = 3 <n_hat>_w (Crawford/Secrest)",
        "mock_verification": {
            "injected_amplitude": inj_amp,
            "recovered_amplitude": _round(D_rec),
            "direction_error_deg": _round(mock_dir_err_deg, 3),
            "recovers_injected_dipole": mock_recovers,
        },
        "real_footprint": {
            "raw_dipole_amplitude": _round(D_real),
            "direction_l_b_deg": [_round(float(l[0]), 3), _round(float(b[0]), 3)],
            "separation_from_cmb_dipole_deg": _round(sep, 3),
            "fsky": _round(fsky, 4),
            "window_dominated": True,
            "cosmological_reference_scale": CMB_KINEMATIC_NUMBER_COUNT_DIPOLE,
        },
    }
    if measured is not None:
        out["window_corrected_measurement"] = {
            "sample": measured["sample"],
            "combined_fsky": measured["combined_fsky"],
            "dipole_amplitude": measured["dipole_amplitude"],
            "dipole_direction_l_b_deg": measured["dipole_direction_l_b_deg"],
            "separation_from_cmb_dipole_deg":
                measured["separation_from_cmb_dipole_deg"],
            "window_suppression_factor": measured["window_suppression_factor"],
            "caveats": measured["caveats"],
        }
        out["status"] = "MEASURED_WINDOW_CORRECTED"
        out["residual_gate"] = ("release-matched mock calibration for the "
                                "mask-coupling amplitude bias + significance; "
                                "the BGS dipole mixes local clustering with "
                                "the kinematic dipole (diagnostic-only)")
        out["scope_not_claimed"] = ("window-corrected overdensity dipole "
                                    "(selection removed via the randoms); "
                                    "clustering+kinematic mixed at BGS depths; "
                                    "no anisotropy, geometry, family, or "
                                    "inference claim; diagnostic-only")
    else:
        out["status"] = "BLOCKED_MISSING_DESI_RANDOMS"
        out["exit_gate"] = ("DESI DR1 BGS random catalogues (BGS_ANY_{NGC,SGC}_"
                            "*_clustering.ran.fits) for window-function "
                            "deconvolution; then the estimator returns the "
                            "selection-corrected number-count dipole")
        out["scope_not_claimed"] = ("the raw footprint dipole is survey-window "
                                    "dominated, NOT a cosmological dipole; no "
                                    "anisotropy or family claim; diagnostic-only")
    out["sgc_available_raw"] = DESI_SGC_RAW.exists()
    return out


# --- ACT DR6 lensing auto-bandpower -----------------------------------
@lru_cache(maxsize=1)
def act_kappa_auto_bandpower() -> dict:
    import healpy as hp
    from astropy.io import fits
    if not ACT_ALM.exists():
        return {"lane": "act_kappa_auto_bandpower",
                "status": "BLOCKED_MISSING_ACT_KAPPA", "detail": str(ACT_ALM)}
    with fits.open(ACT_ALM) as f:
        t = f[1].data
        alm = (t["real"] + 1j * t["imag"]).astype(np.complex128)
    lmax = int(hp.Alm.getlmax(len(alm)))
    cl = hp.alm2cl(alm)
    NL = np.loadtxt(ACT_NL) if ACT_NL.exists() else None
    # a few reconstruction-band centres (raw masked auto-power readout)
    bands = {}
    for L in (40, 100, 200, 400):
        if L <= lmax:
            bands[str(L)] = _round(float(cl[L]), 12)
    out = {
        "lane": "act_kappa_auto_bandpower",
        "sector": "independent-instrument CMB-lensing isotropy cross-check",
        "product": "ACT DR6 baseline kappa a_lm (released)",
        "lmax": lmax,
        "mask_fsky": ACT_BASELINE_FSKY,
        "auto_bandpower_C_L_raw": bands,
        "N_L_rows": (int(NL.shape[0]) if NL is not None else None),
        "low_ell_mean_field_dominated": True,
        "low_ell_C_L_2_10_mean": _round(float(cl[2:11].mean()), 12),
    }
    measured = None
    if ACT_KAPPA_CARD.exists():
        card = json.loads(ACT_KAPPA_CARD.read_text())
        if card.get("status") == "MEASURED_MEAN_FIELD_DEBIASED":
            measured = card
    if measured is not None:
        out["low_ell_isotropy_measurement"] = {
            "n_sims": measured["n_sims"],
            "ell_band": measured["ell_band"],
            "dipole_note": measured["dipole_note"],
            "p_value_data_vs_isotropic_sims":
                measured["p_value_data_vs_isotropic_sims"],
            "consistent_with_isotropic_sims":
                measured["consistent_with_isotropic_sims"],
            "upper_limit_95cl": measured.get("upper_limit_95cl"),
            "caveats": measured["caveats"],
        }
        out["status"] = "MEASURED_MEAN_FIELD_DEBIASED"
        out["real_claim"] = measured.get("claim")
        out["residual_gate"] = ("N0/N1 enter through the end-to-end sim null, "
                                "not a separate analytic subtraction; the "
                                "upper limit is on power above that null")
        out["scope_not_claimed"] = ("a mean-field-debiased low-multipole kappa "
                                    "isotropy consistency test AND a 95% CL "
                                    "model-independent upper limit on excess "
                                    "low-multipole power (ell=2..N; the "
                                    "reconstruction dipole ell=1 is not "
                                    "measurable); an upper-limit/consistency "
                                    "constraint, NOT a detection or a Bianchi "
                                    "family/geometry claim")
    else:
        out["status"] = "BLOCKED_MISSING_ACT_LENSING_SIMS"
        out["exit_gate"] = ("ACT DR6 lensing simulation ensemble (mean field "
                            "+ N0/N1) to debias and calibrate a low-multipole "
                            "kappa isotropy statistic; the auto-bandpower "
                            "readout above is a data-integrity cross-check only")
        out["scope_not_claimed"] = ("raw masked auto-power readout + registered "
                                    "blocker; no anisotropy, geometry, or "
                                    "family claim; diagnostic-only")
    return out


# --- JWST anchor connection -------------------------------------------
def jwst_anchor_connection() -> dict:
    if not JWST_ANCHORS.exists():
        return {"lane": "jwst_cf4_anchors",
                "status": "BLOCKED_MISSING_JWST_ANCHORS"}
    doc = json.loads(JWST_ANCHORS.read_text())
    anchors = doc.get("anchors", [])
    return {
        "lane": "jwst_cf4_anchors",
        "sector": "Omega_tilt survey-design forecast (distance-anchor precision)",
        "n_anchors": len(anchors),
        "methods": sorted({a.get("method", "?") for a in anchors}),
        "connected_to": "scripts/jwst_cf4_crossmatch.py -> "
                        "htt/obsstat/joint_pv_cmb_forecast.py (labelled "
                        "forecast, already wired)",
        "status": "CONNECTED_FORECAST",
        "scope_not_claimed": "the anchors feed a labelled survey-design "
                             "forecast, not a measurement; diagnostic-only",
    }


def external_lanes_seal() -> dict:
    desi = desi_number_count_dipole()
    act = act_kappa_auto_bandpower()
    jwst = jwst_anchor_connection()
    ok = (desi.get("mock_verification", {}).get("recovers_injected_dipole")
          and desi.get("status") in ("BLOCKED_MISSING_DESI_RANDOMS",
                                      "MEASURED_WINDOW_CORRECTED")
          and act.get("status") in ("BLOCKED_MISSING_ACT_LENSING_SIMS",
                                     "MEASURED_MEAN_FIELD_DEBIASED")
          and act.get("lmax") == 4000
          and jwst.get("status") == "CONNECTED_FORECAST")
    return {
        "seal": "egs3.external_lanes",
        "theorem_id": "EXT-LANES",
        "status": "PASS" if ok else "FAIL",
        "desi_number_count_dipole": desi,
        "act_kappa_auto_bandpower": act,
        "jwst_cf4_anchors": jwst,
        "scope_not_claimed": "real-data loaders + mock-verified estimators + "
                             "registered blockers for the missing companion "
                             "products (DESI randoms, ACT lensing sims); "
                             "model-independent kinematic descriptors only; "
                             "no anisotropy, geometry, family, or inference "
                             "claim",
    }


if __name__ == "__main__":
    print(json.dumps(external_lanes_seal(), indent=2, default=str))
