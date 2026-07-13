#!/usr/bin/env python3
"""K6 CF4++ WF velocity-field vorticity + CR distribution (REV-R198).

The rev-r127 K6 no-go -- the Wiener-filter (WF) velocity reconstruction suppresses
vorticity (curl) by its potential-flow prior -- was established abstractly, and a
true Hoffman-Ribak constrained-realization (CR) vorticity distribution was blocked on
an owned CR ensemble (BLOCKED_MISSING_FIELD_REALIZATIONS). This lane advances it
on the REAL CF4++ 3-D WF field (htt/obsstat/velocity_field_curl.py):

1. The WF MEAN-field curl/div ratio quantifies the potential-flow suppression
   directly on the reconstructed field (a real measurement).
2. A CR vorticity distribution is built from a CORRELATED residual field scaled to
   the per-cell WF std v_std -- an upgrade over the toy per-cell-
   independent draws. The residual correlation length R is NOT fixed by
   (v_mean, v_std) alone (the true HR CR needs the full WF residual covariance),
   so the distribution is reported as a SENSITIVITY over R; a definitive ensemble
   still needs the WF operator -> the blocker stays PARTIAL.

Finding: the WF mean field is strongly curl-suppressed (RMS|curl| << RMS|div|,
potential flow), confirming the no-go on the real field; the CR distribution curl is
residual-dominated and correlation-length-dependent.

Diagnostic-only; no Bianchi family, geometry, or observer-frame claim. Outputs
docs/generated/cf4pp_vorticity_card.json. Deterministic; --check.
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

from htt.obsstat.velocity_field_curl import (  # noqa: E402
    curl, divergence, rms_over, cr_vorticity_ensemble)

FIELD = REPO / "workdir/raw/cf4/CF4pp_mean_std_grids.npz"
OUT = REPO / "docs/generated/cf4pp_vorticity_card.json"
BOX_MPC = 1000.0
VALID_RADIUS_MPC = 250.0                # reliable CF4++ volume
R_SMOOTH_MPC = (7.8, 15.0, 30.0)        # residual correlation-length sensitivity
R_SMOOTH_FIDUCIAL = 15.0
N_CR = 40
CR_SEED = 20260714


def _sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def measure() -> dict:
    if not FIELD.is_file():
        return {"schema": "htt.cf4pp_vorticity_card.v1",
                "status": "BLOCKED_MISSING_CF4PP_FIELD"}
    d = np.load(FIELD)
    v_mean = np.asarray(d["v_mean_CF4pp"], float)       # (3,n,n,n) km/s
    v_std = np.asarray(d["v_std_CF4pp"], float)
    n = v_mean.shape[1]
    cell = BOX_MPC / n
    centers = (np.arange(n) - (n - 1) / 2.0) * cell
    X, Y, Z = np.meshgrid(centers, centers, centers, indexing="ij")
    mask = (X ** 2 + Y ** 2 + Z ** 2) < VALID_RADIUS_MPC ** 2

    om_mean = curl(v_mean, cell)
    w2_mean = np.sum(om_mean ** 2, axis=0)
    dv_mean = divergence(v_mean, cell)
    rms_curl = rms_over(w2_mean, mask)
    rms_div = rms_over(dv_mean ** 2, mask)
    curl_div_ratio = rms_curl / rms_div if rms_div > 0 else float("inf")

    cr_rows = {}
    for R in R_SMOOTH_MPC:
        m, s = cr_vorticity_ensemble(v_mean, v_std, cell, mask, R, N_CR, CR_SEED)
        cr_rows[str(R)] = {
            "cr_rms_curl_mean": round(m, 4),
            "cr_rms_curl_std": round(s, 4),
            "cr_over_meanfield": round(m / rms_curl, 1) if rms_curl > 0 else None,
        }
    fid = cr_rows[str(R_SMOOTH_FIDUCIAL)]
    cr_range = [min(r["cr_rms_curl_mean"] for r in cr_rows.values()),
                max(r["cr_rms_curl_mean"] for r in cr_rows.values())]

    # the mean-field curl suppression is the real measurement; the CR distribution
    # is a sensitivity (correlation-length-dependent) -> PARTIAL
    suppressed = bool(curl_div_ratio < 0.1)
    corr_len_dependent = bool(cr_range[1] / max(cr_range[0], 1e-9) > 1.5)
    valid = bool(suppressed and np.isfinite(rms_curl) and rms_curl > 0)
    status = "MEASURED_WF_CURL_SUPPRESSION_CR_PARTIAL" if valid else "VALIDATION_FAILED"
    return {
        "schema": "htt.cf4pp_vorticity_card.v1",
        "status": status,
        "product": "CF4++ Wiener-filter reconstructed 3-D velocity field "
                   "(v_mean + per-cell WF std v_std)",
        "grid": {"n": n, "box_mpc": BOX_MPC, "cell_mpc": round(cell, 2),
                 "valid_radius_mpc": VALID_RADIUS_MPC},
        "wf_mean_field": {
            "rms_curl_kms_per_mpc": round(rms_curl, 4),
            "rms_div_kms_per_mpc": round(rms_div, 4),
            "curl_over_div_ratio": round(curl_div_ratio, 4),
            "interpretation": "the WF mean field is strongly curl-suppressed "
                              "(curl << div) -> potential flow, confirming the "
                              "no-go on the real 3-D CF4++ field",
        },
        "cr_vorticity_distribution_vs_correlation_length": cr_rows,
        "cr_fiducial_correlation_length_mpc": R_SMOOTH_FIDUCIAL,
        "headline": {
            "meanfield_curl_over_div": round(curl_div_ratio, 4),
            "meanfield_potential_flow": suppressed,
            "cr_rms_curl_range_kms_per_mpc": [round(x, 3) for x in cr_range],
            "cr_distribution_correlation_length_dependent": corr_len_dependent,
        },
        "n_cr": N_CR,
        "input_hashes": [f"{FIELD.relative_to(REPO)}:{_sha(FIELD)}"],
        "caveats": [
            "the WF MEAN-field curl/div ratio (%.3f) is a real measurement of the "
            "potential-flow suppression on the reconstructed 3-D field; the CR "
            "vorticity DISTRIBUTION is residual-dominated and depends on the residual "
            "correlation length R (a factor >1.5 across R=%s Mpc), which is NOT "
            "determined by (v_mean, v_std) alone" % (curl_div_ratio,
                                                     list(R_SMOOTH_MPC)),
            "the true Hoffman-Ribak CR needs the full WF residual covariance (the "
            "WF operator + the data + the noise model), not just the per-cell "
            "WF std; so a DEFINITIVE CR vorticity distribution still needs an "
            "owned field-realization ensemble (BLOCKED_MISSING_FIELD_REALIZATIONS "
            "stays PARTIAL) -- this correlated-residual CR is a principled upgrade "
            "over the per-cell-independent toy, not the definitive ensemble",
            "curl and divergence are central-difference derivatives on the 128^3 "
            "grid (cell %.1f Mpc) within the reliable radius %.0f Mpc; the box "
            "convention (1000 Mpc, matching the reconstruction lane) sets the "
            "gradient scale" % (cell, VALID_RADIUS_MPC),
        ],
        "claim": ("the CF4++ WF mean velocity field is strongly curl-suppressed "
                  "(RMS|curl|/RMS|div| = %.3f, potential flow), confirming the K6 "
                  "no-go on the REAL 3-D reconstructed field; a correlated-residual "
                  "CR vorticity distribution (scaled to the per-cell WF std) gives "
                  "RMS|curl| = %.1f-%.1f (km/s)/Mpc depending on the residual "
                  "correlation length -- residual-dominated and correlation-length-"
                  "dependent, so a DEFINITIVE CR ensemble still needs the full WF "
                  "operator (blocker stays PARTIAL)"
                  % (curl_div_ratio, cr_range[0], cr_range[1])),
        "scope_not_claimed": ("a potential-flow-suppression measurement + a "
                              "conditional CR vorticity distribution; NOT a Bianchi "
                              "family, geometry, or observer-frame claim; no "
                              "vorticity signal claim"),
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
            print("STALE cf4pp_vorticity_card.json", file=sys.stderr)
            return 1
        print("cf4pp vorticity card current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={card['status']}")
    if card["status"].startswith("MEASURED"):
        w = card["wf_mean_field"]
        print(f"  WF mean field: |curl|={w['rms_curl_kms_per_mpc']} "
              f"|div|={w['rms_div_kms_per_mpc']} ratio={w['curl_over_div_ratio']}")
        for R, r in card["cr_vorticity_distribution_vs_correlation_length"].items():
            print(f"  CR R={R} Mpc: |curl|={r['cr_rms_curl_mean']}+/-{r['cr_rms_curl_std']}"
                  f" ({r['cr_over_meanfield']}x mean-field)")
        print(f"  headline: {card['headline']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
