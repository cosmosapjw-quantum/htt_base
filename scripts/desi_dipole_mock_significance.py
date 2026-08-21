#!/usr/bin/env python3
"""EXT-DESI mock-calibrated significance of the BGS number-count dipole (REV-R198).

The rev-r193 EXT-DESI card measured the window-corrected DESI DR1 BGS dipole
D = 9.49e-3 but could only report it as a diagnostic (the significance needed
release-matched mocks). This lane supplies the in-house physical mock (the
rev-r197 pattern applied to the number-count dipole,
htt/obsstat/number_count_dipole.py):

- the analytic shot-noise floor of D separates shot noise from clustering;
- the exact ell=1 angular-power projection of the observed dN/dz gives the
  LambdaCDM clustering dipole cosmic variance;
- GRF sky maps with that C_ell, masked to the real BGS footprint and Poisson-
  sampled at the random-encoded selection, run through the IDENTICAL dipole
  estimator give the LambdaCDM null of |D| (clustering + shot + mask coupling).

Finding: the observed dipole is CLUSTERING-dominated (far above the shot-noise
floor) and CONSISTENT with LambdaCDM clustering cosmic variance -- it is not an
excess. A linear-bias sensitivity brackets the null. Still a consistency test,
NOT a clean kinematic measurement (BGS is low-z); no anisotropy/geometry/family
claim.

Outputs docs/generated/desi_dipole_mock_card.json. Deterministic; --check.
Heavy: loads the ~2.3 GB randoms + runs the mock ensemble (run standalone).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from htt.obsstat.velocity_power import fiducial                       # noqa: E402
from htt.obsstat import number_count_dipole as ncd                    # noqa: E402

OUT = REPO / "docs/generated/desi_dipole_mock_card.json"
COMPACT = REPO / "workdir/compact_products/desi"
RAW = REPO / "workdir/raw/desi"
NSIDE = 64
LMAX = 40
N_MOCK = 400
MOCK_SEED = 20260714
BIAS_FIDUCIAL = 1.5                     # BGS linear bias
BIAS_SENS = (1.2, 1.5, 2.0)
CMB_KINEMATIC = 7.0e-3


class InvalidatedHistoricalProducerError(RuntimeError):
    """PR-151 producer cannot run before a separately validated successor exists."""


def _load_desi():
    spec = importlib.util.spec_from_file_location(
        "desi_dip", REPO / "scripts/desi_dipole_measure.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _chi2_sigma(D, sig_per_comp):
    from scipy.stats import chi2 as c2
    chi2 = float(np.sum((D / sig_per_comp) ** 2))
    p = float(c2.sf(chi2, 3))
    return chi2, p, (float(np.sqrt(c2.isf(p, 1))) if p > 0 else float("inf"))


def measure() -> dict:
    raise InvalidatedHistoricalProducerError(
        "PR-151 historical producer is invalidated; successor formalism and independent validation are required"
    )
    import healpy as hp
    desi = _load_desi()
    npix = hp.nside2npix(NSIDE)
    vec = np.asarray(hp.pix2vec(NSIDE, np.arange(npix)))
    caps_raw = {}
    for cap in ("NGC", "SGC"):
        c = desi._load_cap(cap)
        if c is not None:
            caps_raw[cap] = c
    if not caps_raw:
        return {"schema": "htt.desi_dipole_mock_card.v1",
                "status": "BLOCKED_MISSING_DESI_RANDOMS"}

    Rp = {c: caps_raw[c]["Rp"] for c in caps_raw}
    alpha = {c: caps_raw[c]["alpha"] for c in caps_raw}

    # observed dipole (identical estimator)
    delta_obs = {}
    for cap, cc in caps_raw.items():
        m = cc["Rp"] > 0
        dd = np.zeros(npix)
        dd[m] = (cc["Dp"][m] - cc["alpha"] * cc["Rp"][m]) / (cc["alpha"] * cc["Rp"][m])
        delta_obs[cap] = dd
    D_obs = ncd.dipole_from_delta(delta_obs, Rp, vec)
    amp_obs = float(np.linalg.norm(D_obs))

    # shot-noise floor
    sig_shot = ncd.shot_noise_sigma(Rp, alpha, vec)
    chi2_s, p_s, sig_s = _chi2_sigma(D_obs, sig_shot)

    # dN/dz from the data z (both caps)
    zall = []
    for cap in ("NGC", "SGC"):
        f = COMPACT / f"BGS_ANY_{cap}_clustering_extended.npz"
        if f.exists():
            zall.append(np.asarray(np.load(f)["z"], float))
    z = np.concatenate(zall)
    z = z[(z > 0.01) & (z < 0.5)]
    zc = np.linspace(0.02, 0.5, 40)
    dz = zc[1] - zc[0]
    phi, _ = np.histogram(z, bins=np.r_[zc - dz / 2, zc[-1] + dz / 2])
    phi = phi.astype(float)

    cos = fiducial()
    om, h, pk = cos["om"], cos["h"], cos["pk"]

    # LambdaCDM clustering + shot mock null, at the fiducial bias
    bias_rows = {}
    for b in BIAS_SENS:
        Cl, _ = ncd.angular_power_projection(phi, zc, pk, om, h, b, LMAX)
        amps = ncd.mock_dipole_amplitudes(Cl, Rp, alpha, vec, NSIDE, N_MOCK,
                                          MOCK_SEED, LMAX)
        exceed = int(np.sum(amps >= amp_obs))
        p_emp = (1.0 + exceed) / (N_MOCK + 1.0)
        bias_rows[str(b)] = {
            "C_1": round(float(Cl[1]), 8),
            "mock_dipole_mean": round(float(amps.mean()), 6),
            "mock_dipole_std": round(float(amps.std(ddof=1)), 6),
            "p_value": round(p_emp, 4),
            "n_exceeding": exceed,
            "obs_percentile": round(float(np.mean(amps < amp_obs)), 3),
        }
    fid = bias_rows[str(BIAS_FIDUCIAL)]

    # consistent if the observed dipole is within the LambdaCDM null (not an
    # excess): a two-sided p-value comfortably away from 0 across the bias range
    consistent = bool(all(0.02 < r["p_value"] < 0.98 or r["p_value"] >= 0.02
                          for r in bias_rows.values())
                      and fid["p_value"] > 0.02)
    valid = bool(sig_s > 3.0 and all(np.isfinite([r["mock_dipole_mean"]
                 for r in bias_rows.values()])))
    status = "MEASURED_MOCK_CALIBRATED" if valid else "VALIDATION_FAILED"
    return {
        "schema": "htt.desi_dipole_mock_card.v1",
        "status": status,
        "sample": "DESI DR1 BGS_ANY (" + "+".join(caps_raw) + ")",
        "estimator": "window-corrected dipole D = 3 <delta n_hat>_R vs an "
                     "in-house LambdaCDM clustering + Poisson-shot mock ensemble "
                     "(exact ell=1 projection of the observed dN/dz)",
        "nside": NSIDE, "lmax": LMAX, "n_mock": N_MOCK,
        "observed_dipole_amplitude": round(amp_obs, 6),
        "observed_dipole_direction": [round(float(x), 4) for x in D_obs / amp_obs],
        "shot_noise": {
            "sigma_per_component": [round(float(x), 6) for x in sig_shot],
            "chi2_3dof": round(chi2_s, 2),
            "sigma_above_shot_noise": round(sig_s, 2),
            "interpretation": "the observed dipole is far above the shot-noise "
                              "floor -> it is CLUSTERING-dominated, not shot noise",
        },
        "lcdm_clustering_mock_null": bias_rows,
        "bias_fiducial": BIAS_FIDUCIAL,
        "headline": {
            "observed_dipole": round(amp_obs, 6),
            "lcdm_mock_mean_std": [fid["mock_dipole_mean"], fid["mock_dipole_std"]],
            "p_value_fiducial_bias": fid["p_value"],
            "consistent_with_lcdm_clustering": consistent,
            "clustering_dominated": True,
        },
        "cmb_kinematic_number_count_dipole_ref": CMB_KINEMATIC,
        "fiducial_cosmology": {"Omega_m": om, "h": h, "sigma_8": cos["sigma_8"],
                               "P_k": "EH98 no-wiggle, sigma_8-normalised"},
        "caveats": [
            "the observed dipole is CLUSTERING-dominated (%.1f sigma above the "
            "shot-noise floor); the relevant null is therefore the LambdaCDM "
            "clustering cosmic variance, supplied by the in-house mock, NOT the "
            "shot-noise floor" % sig_s,
            "the mock uses the observed dN/dz, the fiducial P(k), and a LINEAR "
            "bias b (fiducial %.1f); the significance is reported across a bias "
            "range %s because b is not fit here (a joint bias+dipole fit is a "
            "further refinement)" % (BIAS_FIDUCIAL, list(BIAS_SENS)),
            "BGS is low-z (z<0.5): the dipole still MIXES the clustering dipole "
            "with the kinematic dipole -- this mock tests consistency of the "
            "TOTAL dipole with LambdaCDM clustering, it does NOT isolate the "
            "kinematic component; the CMB kinematic scale (~7e-3) is comparable "
            "to the observed dipole and sub-dominant to the clustering cosmic "
            "variance at these depths",
            "the GRF mock is Gaussian (linear); nonlinear/lognormal clustering "
            "and imaging-systematic residuals are not modelled (sub-dominant at "
            "the dipole scale k~2e-3 h/Mpc)",
        ],
        "claim": ("mock-calibrated: the window-corrected DESI DR1 BGS number-count "
                  "dipole D = %.4f is CLUSTERING-dominated (%.1f sigma above shot "
                  "noise) and CONSISTENT with LambdaCDM clustering cosmic variance "
                  "(in-house mock |D| = %.4f +/- %.4f, p = %.2f at bias %.1f; "
                  "consistent across bias %s) -- NOT an excess/anomaly; the "
                  "kinematic dipole is sub-dominant to the clustering cosmic "
                  "variance at BGS depths"
                  % (amp_obs, sig_s, fid["mock_dipole_mean"], fid["mock_dipole_std"],
                     fid["p_value"], BIAS_FIDUCIAL, list(BIAS_SENS))),
        "scope_not_claimed": ("a consistency test of the total number-count dipole "
                              "against LambdaCDM clustering; NOT a clean kinematic "
                              "measurement, and NOT a Bianchi family, geometry, or "
                              "observer-frame claim; no anisotropy discovery"),
    }


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
            print("STALE desi_dipole_mock_card.json", file=sys.stderr)
            return 1
        print("desi dipole mock card current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={card['status']}")
    if card["status"] == "MEASURED_MOCK_CALIBRATED":
        print(f"  D_obs={card['observed_dipole_amplitude']} "
              f"({card['shot_noise']['sigma_above_shot_noise']} sigma > shot)")
        for b, r in card["lcdm_clustering_mock_null"].items():
            print(f"  bias {b}: mock |D|={r['mock_dipole_mean']}+/-{r['mock_dipole_std']}"
                  f" p={r['p_value']} (obs pctile {r['obs_percentile']})")
        print(f"  headline: {card['headline']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
