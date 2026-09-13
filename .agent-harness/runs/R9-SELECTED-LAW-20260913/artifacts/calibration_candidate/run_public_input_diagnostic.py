"""Run only the public exact-PGC overlap diagnostic; no official-offset replay."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from cf3_sdss_calibration_candidate import cf3_eta_from_distance_modulus, read_public_pgc_join


ROOT = Path(__file__).resolve().parent
SDSS = Path("/mnt/sn850x2t/htt_base_e2e/workdir/raw/sdss_pv_zenodo_6824749/SDSS_PV_public.dat")
CF3 = ROOT / "sources" / "CF3_table3.dat"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    joined = read_public_pgc_join(SDSS, CF3, corrected=False)
    eta = cf3_eta_from_distance_modulus(joined.cf3_distance_modulus, joined.sdss_zcmb)
    finite = np.isfinite(eta) & np.isfinite(joined.sdss_logdist)
    diagnostic_width = np.hypot(joined.sdss_logdist_err, joined.cf3_distance_modulus_err / 5.0)
    weights = 1.0 / diagnostic_width[finite] ** 2
    delta = eta[finite] - joined.sdss_logdist[finite]
    tf_excluded = np.isin(joined.cf3_distance_source, ["H", "I"])
    retained = finite & ~tf_excluded
    retained_weights = 1.0 / diagnostic_width[retained] ** 2
    payload = {
        "status": "PUBLIC_INPUT_DIAGNOSTIC_ONLY",
        "sdss_sha256": sha256(SDSS),
        "cf3_table3_sha256": sha256(CF3),
        "exact_pgc_overlap_rows": int(len(joined.pgc)),
        "finite_eta_rows": int(finite.sum()),
        "unweighted_cf3_minus_sdss_dex_descriptive": float(np.mean(delta)),
        "per_row_width_weighted_cf3_minus_sdss_dex_descriptive": float(np.average(delta, weights=weights)),
        "rule_based_public294": {
            "rule": "exclude CF3 r_Dist tracer codes H or I, documented as Tully-Fisher in CF3 ReadMe",
            "retained_rows": int(retained.sum()),
            "excluded_pgc": joined.pgc[tf_excluded].tolist(),
            "per_row_width_weighted_cf3_minus_sdss_dex_descriptive": float(np.average(eta[retained] - joined.sdss_logdist[retained], weights=retained_weights))
        },
        "diagnostic_weight_definition": "1/(logdist_err^2 + (e_DM/5)^2); not a joint covariance or standard-error law",
        "cf3_r_Dist_codes_among_overlap": sorted(set(joined.cf3_distance_source.tolist())),
        "cf3_r_Dist_H_rows": int(np.sum(joined.cf3_distance_source == "H")),
        "cf3_r_Dist_H_pgc": joined.pgc[joined.cf3_distance_source == "H"].tolist(),
        "joint_covariance_status": "UNAVAILABLE_NOT_ZERO_FILLED",
        "official_eq24_eq25_replay": "UNAVAILABLE",
        "why": [
            "The public PGC join does not encode the paper's two TF exclusions.",
            "No released CF3-to-Tempel group membership crosswalk establishes the paper's 292 group membership.",
            "The documented H/I tracer rule yields 294 public rows, but this is a rule-based public reproduction rather than byte-exact author pair replay.",
            "No joint SDSS-CF3 covariance is public in these inputs, so no weighted offset or standard error is reported.",
        ],
        "convention": "eta_CF3=log10[D_comoving(SDSS zcmb; H0=75,Omega_m=.31)/(10^((CF3 DM-25)/5)/(1+SDSS zcmb))], both distances physical Mpc",
        "sdss_value": "unshifted released logdist (single FP), no CF3 shift applied",
    }
    np.savez_compressed(
        ROOT / "public_pgc_overlap_rows.npz",
        pgc=joined.pgc,
        sdss_logdist_unshifted=joined.sdss_logdist,
        sdss_logdist_err=joined.sdss_logdist_err,
        cf3_eta_diagnostic=eta,
        cf3_distance_modulus=joined.cf3_distance_modulus,
        cf3_distance_modulus_err=joined.cf3_distance_modulus_err,
        sdss_zcmb=joined.sdss_zcmb,
        cf3_r_Dist=joined.cf3_distance_source,
        rule_based_public294_mask=retained,
        sdss_tempel_group_id=joined.sdss_group_id,
        sdss_tempel_group_richness=joined.sdss_group_richness,
        joint_covariance_status=np.asarray("UNAVAILABLE_NOT_ZERO_FILLED"),
    )
    (ROOT / "public_input_diagnostic.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
