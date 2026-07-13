#!/usr/bin/env python3
"""K5 CF4 velocity correlation function -> f sigma_8 (REV-R196).

The reconstruction-INDEPENDENT statistic (the physical, well-posed replacement
for an ill-posed angular pseudo-C_l): the peculiar velocity correlation function
Psi_par(r)/Psi_perp(r) (Gorski 1988; CF4 precedent arXiv:2604.08314), computed
directly from pairs of observed line-of-sight velocities with NO field
reconstruction. The linear-theory prediction scales as (f sigma_8)^2, so fitting
its amplitude to the data yields a growth-rate f sigma_8 -- a real cosmological
constraint that does not depend on any velocity/density reconstruction.

Run on the DIRECT Vpds (Davis-Scrimgeour, least model-dependent -- the
reconstruction-independence attaches here) and on Vpec (the WF-ramp column, for
contrast). Error via a delete-one-octant jackknife. Cross-check: the CF4 velocity
correlation function fit gives f sigma_8 ~ 0.38 (Planck-consistent). Also reports
the sigma_8-/bias-/window-insensitive cosmic Mach number M = |B|/sigma_1D.

Diagnostic-only kinematic descriptor; a growth-rate constraint, no Bianchi
family, geometry, or observer-frame claim. Outputs
docs/generated/cf4_velocity_correlation_card.json. Deterministic; --check.
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

from htt.obsstat.velocity_power import fiducial, velocity_correlation_functions  # noqa: E402
from htt.obsstat.velocity_correlation import (  # noqa: E402
    pair_correlation, fit_amplitude, cosmic_mach_number)
from htt.obsstat.bulkflow_mle import (  # noqa: E402
    estimate_bulk_flow, fit_sigma_star, velocity_error)

GROUPS = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
VARIANTS = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_pv_variants.npz"
OUT = REPO / "docs/generated/cf4_velocity_correlation_card.json"

R_EDGES = tuple(np.linspace(20.0, 100.0, 9))     # h^-1 Mpc pair-separation bins
# deterministic subsample: the full 38k catalogue gives ~1.25e8 pairs < 100 Mpc/h
# (per-octant jackknife x2 variants is infeasible); ~12k groups -> ~1.3e7 pairs,
# ample for an 8-bin correlation-function amplitude fit (standard PV practice).
N_SUBSAMPLE = 12000
SUBSAMPLE_SEED = 20260713
PV_COLS = ("Vpds", "Vpec")
PV_DESC = {"Vpds": "Davis-Scrimgeour 2014 direct (reconstruction-independent)",
           "Vpec": "ramp Eq.11 (WF blend)"}
CF4_FS8_ANCHOR = 0.38                              # arXiv:2604.08314


def _sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load(h):
    g = np.load(GROUPS, allow_pickle=True)
    var = np.load(VARIANTS)
    sg = np.c_[g["SGX"], g["SGY"], g["SGZ"]].astype(float)
    r_sg = np.linalg.norm(sg, axis=1)
    dist = np.asarray(g["Dist"], float)
    v3k = np.asarray(g["V3k"], float)
    sigma = velocity_error(g["e_DMzp"], v3k)
    good = ((r_sg > 1.0) & np.isfinite(dist) & (dist > 1.0)
            & np.isfinite(sigma) & (sigma > 0) & np.isfinite(v3k))
    idx = np.flatnonzero(good)
    if len(idx) > N_SUBSAMPLE:                       # deterministic subsample
        rng = np.random.default_rng(SUBSAMPLE_SEED)
        idx = np.sort(rng.choice(idx, N_SUBSAMPLE, replace=False))
    n_hat = sg[idx] / r_sg[idx, None]
    pos = n_hat * (dist[idx] * h)[:, None]           # Mpc/h
    return {"n_hat": n_hat, "pos": pos, "sigma": sigma[idx],
            "n_used": int(len(idx)),
            "var": {c: np.asarray(var[c], float)[idx] for c in PV_COLS},
            "octant": (np.sign(sg[idx, 0]).astype(int) * 4
                       + (np.sign(sg[idx, 1]) > 0) * 2
                       + (np.sign(sg[idx, 2]) > 0)).astype(int)}


def _fs8_from_pairs(pos, n_hat, u, sigma, psi_par_th, psi_perp_th, fs8_fid):
    """Bulk-subtracted, inverse-error-weighted Psi_hat -> amplitude A -> f sigma_8.

    The sample bulk flow is subtracted (its coherent monopole biases Psi high at
    large r) and pairs are inverse-error weighted (distant, noisy galaxies
    otherwise dominate). This is a SIMPLIFIED estimator: a precision f sigma_8
    needs the full max-likelihood noise-aware treatment (Johnson 2014; CF4
    arXiv:2604.08314), so the value here is a treatment-dependent diagnostic."""
    ss = fit_sigma_star(n_hat, u, sigma)
    bf = estimate_bulk_flow(n_hat, u, sigma, sigma_star=ss)
    u_res = u - n_hat @ bf.vector
    w_gal = 1.0 / np.sqrt(sigma ** 2 + ss ** 2)
    r_mid, pp, pperp, cnt = pair_correlation(pos, n_hat, u_res, R_EDGES,
                                             w_gal=w_gal)
    A = fit_amplitude(np.concatenate([pp, pperp]),
                      np.concatenate([psi_par_th, psi_perp_th]))
    fs8 = fs8_fid * np.sqrt(A) if A > 0 else float("nan")
    return fs8, r_mid, pp, pperp, cnt, A


def measure() -> dict:
    if not (GROUPS.is_file() and VARIANTS.is_file()):
        return {"schema": "htt.cf4_velocity_correlation.v1",
                "status": "BLOCKED_MISSING_CF4_CATALOGUE"}
    cos = fiducial()
    h, pk, hf2 = cos["h"], cos["pk"], cos["hf2"]
    fs8_fid = cos["f_growth"] * cos["sigma_8"]
    d = _load(h)
    r_mid = 0.5 * (np.asarray(R_EDGES[:-1]) + np.asarray(R_EDGES[1:]))
    psi_par_th, psi_perp_th = velocity_correlation_functions(pk, hf2, r_mid)

    per_variant = {}
    for col in PV_COLS:
        u = d["var"][col]
        m = np.isfinite(u)
        pos, nh, uu = d["pos"][m], d["n_hat"][m], u[m]
        sg, oct_ = d["sigma"][m], d["octant"][m]
        fs8, rmid, pp, pperp, cnt, A = _fs8_from_pairs(
            pos, nh, uu, sg, psi_par_th, psi_perp_th, fs8_fid)
        # delete-one-octant jackknife error on f sigma_8
        octs = np.unique(oct_)
        fs8_jk = []
        for o in octs:
            keep = oct_ != o
            if keep.sum() < 100:
                continue
            fj, *_ = _fs8_from_pairs(pos[keep], nh[keep], uu[keep], sg[keep],
                                     psi_par_th, psi_perp_th, fs8_fid)
            if np.isfinite(fj):
                fs8_jk.append(fj)
        fs8_jk = np.array(fs8_jk)
        njk = len(fs8_jk)
        fs8_err = (float(np.sqrt((njk - 1) / njk * np.sum((fs8_jk - fs8_jk.mean()) ** 2)))
                   if njk > 1 else float("nan"))
        # cosmic Mach number from the GLS bulk on this variant
        ss = fit_sigma_star(nh, uu, d["sigma"][m])
        bf = estimate_bulk_flow(nh, uu, d["sigma"][m], sigma_star=ss)
        mach, sigma_1d = cosmic_mach_number(uu, bf.vector, nh)
        per_variant[col] = {
            "estimator": PV_DESC[col],
            "n_groups": int(m.sum()),
            "n_pairs_total": int(cnt.sum()),
            "f_sigma8": round(fs8, 4),
            "f_sigma8_jackknife_error": round(fs8_err, 4),
            "amplitude_A": round(A, 4),
            "psi_par_data_kms2": [round(float(x), 1) for x in pp],
            "psi_perp_data_kms2": [round(float(x), 1) for x in pperp],
            "cosmic_mach_number": round(mach, 3),
            "sigma_1d_kms": round(sigma_1d, 1),
        }

    vpec, direct = per_variant["Vpec"], per_variant["Vpds"]
    # the Psi statistic is a real reconstruction-independent measurement; the
    # f sigma_8 EXTRACTION with this simplified pair estimator is treatment-
    # dependent (bulk-subtracted + error-weighted here) -> diagnostic tier.
    curves_ok = bool(np.all(np.isfinite(vpec["psi_par_data_kms2"]))
                     and np.isfinite(vpec["f_sigma8"])
                     and 0.1 < vpec["f_sigma8"] < 1.5)
    status = "MEASURED_CORRELATION_DIAGNOSTIC" if curves_ok else "VALIDATION_FAILED"
    return {
        "schema": "htt.cf4_velocity_correlation.v1",
        "status": status,
        "product": "Cosmicflows-4 groups (Tully+ 2023); velocity correlation function",
        "statistic": "Gorski Psi_par(r)/Psi_perp(r) from LOS-velocity pairs "
                     "(reconstruction-independent; bulk-subtracted, error-"
                     "weighted); f sigma_8 amplitude fit is a DIAGNOSTIC",
        "separation_bins_hmpc": [round(float(x), 1) for x in r_mid],
        "fiducial_f_sigma8": round(fs8_fid, 4),
        "theory_psi_par_kms2": [round(float(x), 1) for x in psi_par_th],
        "theory_psi_perp_kms2": [round(float(x), 1) for x in psi_perp_th],
        "per_variant": per_variant,
        "reconstruction_independent_statistic": {
            "what": "the Gorski velocity correlation function Psi_par/Psi_perp "
                    "computed directly from observed LOS velocities (NO field "
                    "reconstruction) is the physical reconstruction-independent "
                    "statistic -- the well-posed replacement for an ill-posed "
                    "angular pseudo-C_l",
            "f_sigma8_diagnostic_vpds_direct": direct["f_sigma8"],
            "f_sigma8_diagnostic_vpec": vpec["f_sigma8"],
            "cf4_published_anchor": CF4_FS8_ANCHOR,
            "cosmic_mach_number_vpds": direct["cosmic_mach_number"],
            "exit_gate": "a precision f sigma_8 needs the full max-likelihood "
                         "noise-aware estimator (Johnson 2014; CF4 "
                         "arXiv:2604.08314); this simplified pair estimator gives "
                         "a treatment-dependent value, not a precision constraint",
        },
        "fiducial_cosmology": {
            "Omega_m": cos["om"], "h": h, "sigma_8": cos["sigma_8"],
            "growth_f": round(cos["f_growth"], 5),
            "P_k": "EH98 no-wiggle, sigma_8-normalised"},
        "input_hashes": [f"{GROUPS.relative_to(REPO)}:{_sha(GROUPS)}",
                         f"{VARIANTS.relative_to(REPO)}:{_sha(VARIANTS)}"],
        "caveats": [
            "the correlation function Psi is computed directly from observed LOS "
            "velocities (no field reconstruction) -- the real reconstruction-"
            "independent statistic; the direct Vpds carries that independence, "
            "Vpec (WF-blended) is shown for contrast",
            "the f sigma_8 is DIAGNOSTIC, not a precision constraint: this "
            "simplified pair estimator is sensitive to the noise treatment -- "
            "raw pairs give f sigma_8 ~ 1-3 (measurement-noise + bulk-flow "
            "contaminated); bulk-flow subtraction + inverse-error pair weighting "
            "(applied here) bring Vpec to ~0.4-0.5, but the Psi_par SHAPE still "
            "departs from linear theory, so a precision value needs the full "
            "max-likelihood noise-aware estimator (registered exit-gate)",
            "the direct Vpds is noisiest (unphysical outliers to +/-24000 km/s) "
            "so its f sigma_8 diagnostic is the least reliable; the jackknife is "
            "a delete-one-octant estimate (rigorous covariance needs mocks)",
            "the estimator runs on a deterministic %d-group subsample (the full "
            "pair count ~1.25e8 makes the octant jackknife infeasible); ~1.3e7 "
            "pairs is ample for the 8-bin fit" % N_SUBSAMPLE,
        ],
        "claim": ("the reconstruction-independent CF4 velocity correlation "
                  "function Psi_par/Psi_perp is measured directly from LOS-"
                  "velocity pairs (no field reconstruction); the simplified "
                  "bulk-subtracted error-weighted amplitude fit gives a "
                  "DIAGNOSTIC f sigma_8 ~ %.2f (Vpec) / %.2f (direct Vpds), "
                  "treatment-dependent -- a precision value vs the published CF4 "
                  "~%.2f needs the max-likelihood estimator"
                  % (vpec["f_sigma8"], direct["f_sigma8"], CF4_FS8_ANCHOR)),
        "scope_not_claimed": ("a reconstruction-independent velocity correlation "
                              "function + a treatment-dependent diagnostic "
                              "f sigma_8 (not a precision growth-rate constraint); "
                              "NOT a Bianchi family, geometry, or observer-frame "
                              "claim; no anisotropy discovery"),
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
            print("STALE cf4_velocity_correlation_card.json", file=sys.stderr)
            return 1
        print("cf4 velocity correlation card current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={card['status']}")
    if card["status"].startswith("MEASURED"):
        for c, v in card["per_variant"].items():
            print(f"  {c}: fsigma8={v['f_sigma8']}+/-{v['f_sigma8_jackknife_error']} "
                  f"Mach={v['cosmic_mach_number']} (npairs={v['n_pairs_total']})")
        print(f"  fiducial fsigma8={card['fiducial_f_sigma8']}, "
              f"CF4 anchor {CF4_FS8_ANCHOR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
