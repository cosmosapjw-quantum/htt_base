"""R108 review R6: check the numbers quoted in the R107 cloud documents against files.

Reads R107 RESULTS/HYBRID_LOS_CONVERGENCE.json (written by scripts/r107_cloud/
hybrid_los_convergence.py in the cloud) and extracts the quantities that
THEORY_FOUNDATIONS.md TF1/TF3 and RESULTS_KO.md quote; recomputes, with the current
(R108-fixed) line-of-sight code, the native-versus-HEALPix (T, E, B) convention agreement
that TF1 quotes as 1e-14 (the R107 code had a T floor of ~4e-9 from the 1 - 1
cancellation, review R4).  Writes REVIEW/R107_CLAIM_CHECK.json.

Usage: PYTHONPATH=.:htt:htt/src python -m scripts.r108.review_r107_claims
"""

from __future__ import annotations

import json

import numpy as np

from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json

R107 = REPO / "docs/research_program/observational_publication_20261015/R107_CLOUD_SOLVER_DATA_THEORY_20261124"


def healpix_convention_agreement() -> dict:
    from bass.transport.general_lie_stokes import GeneralLieStokesOperator, vector_to_alm_dict
    from bass.transport.hybrid_los_transfer import (LosSourceHistory, healpix_directions, los_alm_healpix, los_sky,
                                                    native_alm_to_healpix, pack_geometry14)

    lmax, nside = 8, 16
    op = GeneralLieStokesOperator(lmax)
    rng = np.random.default_rng(5)
    x = np.zeros(op.dim, dtype=complex)
    for ch, lo, hi in (("T", 1, 2), ("E", 2, 2), ("B", 2, 2)):
        for (ell, m), i in op.idx[ch].items():
            if lo <= ell <= hi and m >= 0:
                x[i] = complex(rng.normal(), rng.normal()) if m else complex(rng.normal(), 0.0)
        for (ell, m), i in op.idx[ch].items():
            if lo <= ell <= hi and m < 0:
                x[i] = (-1) ** m * np.conj(x[op.idx[ch][(ell, -m)]])
    x *= 1e-5
    z14 = pack_geometry14(np.zeros((3, 3)), np.zeros(3), np.zeros((3, 3)))
    em = np.zeros((4, op.dim), dtype=complex)
    em[1] = em[2] = x
    hist = LosSourceHistory(N=np.array([-7.5, -6.901, -6.9, 0.0]), delta_tau=np.array([0.0, 1e6, 0.0]), emission=em,
                            initial_state=np.zeros(op.dim, dtype=complex), geometry_N=np.array([-8.0, 0.0]),
                            geometry14=np.stack([z14, z14]), ell_max_native=op.L)
    sky = los_sky(hist, healpix_directions(nside), max_step=0.05)
    alm = los_alm_healpix(sky, nside, lmax, iterations=8)
    ref = vector_to_alm_dict(x, op.idx)
    out = {}
    for ch in ("T", "E", "B"):
        r = native_alm_to_healpix(ref[ch], lmax)
        out[ch] = float(np.max(np.abs(alm[ch] - r)) / np.max(np.abs(r)))
    return out


def f2_ratios() -> dict:
    """Ratios of successive LoS-minus-native max relative differences (48->96->192->384 cells), cell-end nodes."""
    f2 = json.loads((OUT_DIR / "F2_COUPLED_LOS.json").read_text())["summary_max_rel_diff_gl24_step0.02"]
    out = {}
    for key in ("cell_ends_cap1.0", "cell_ends_cap0.25"):
        rows = f2[key]
        cells = sorted(rows, key=int)
        out[key] = {m: [rows[a][m] / rows[b][m] for a, b in zip(cells[:-1], cells[1:])] for m in ("T1", "T2", "E2", "B2")}
    return out


def main() -> None:
    path = R107 / "RESULTS/HYBRID_LOS_CONVERGENCE.json"
    d = json.loads(path.read_text())
    cases = d["cases"]
    low = {c: {L: v["max_rel_diff"] for L, v in cases[c]["native_vs_los_low_ell"].items()} for c in cases}

    def mx(case, L, prefix=None, ell_max=4):
        vals = {k: v for k, v in low[case][L].items() if int(k[1:]) <= ell_max and (prefix is None or k[0] in prefix)}
        k = max(vals, key=vals.get)
        return {"max": vals[k], "at": k}

    checks = [
        {"doc": "TF1/RESULTS_KO", "claim": "class-B LoS vs native at ell <= 4: T 2e-6, E/B 1e-4 (weak case, L=16)",
         "file_value": {"T": mx("weak_class_B", "16", "T"), "EB": mx("weak_class_B", "16", "EB")}},
        {"doc": "TF3", "claim": "focusing: native L=8 deviates 1e-2 to 2e-1 at ell <= 4 (T4 0.11, E4 0.19)",
         "file_value": {"min": min(v for k, v in low["focusing_class_B"]["8"].items() if int(k[1:]) <= 4),
                        "max": mx("focusing_class_B", "8"), "T4": low["focusing_class_B"]["8"].get("T4"),
                        "E4": low["focusing_class_B"]["8"].get("E4")}},
        {"doc": "TF3", "claim": "focusing: L=12 <= 4e-3", "file_value": mx("focusing_class_B", "12")},
        {"doc": "TF3", "claim": "focusing: L=16 <= 1.6e-4", "file_value": mx("focusing_class_B", "16")},
        {"doc": "TF3", "claim": "weak: L=8 already converged", "file_value": mx("weak_class_B", "8")},
        {"doc": "TF3", "claim": "Nside 32 vs 64 <= 5e-5 (ell <= 56)",
         "file_value": {c: cases[c]["max_rel_change"]["nside_half"] for c in cases}},
        {"doc": "TF3", "claim": "ray step 0.02 vs 0.01 <= 1e-6",
         "file_value": {c: cases[c]["max_rel_change"]["ray_step_0p01_vs_0p02"] for c in cases}},
        {"doc": "TF3", "claim": "node doubling <= 5e-3 (EE, BB) and 7e-4 (TT)",
         "file_value": {c: cases[c]["max_rel_change"]["cells_double"] for c in cases}},
        {"doc": "TF1/handoff", "claim": "native and HEALPix (T,E,B) conventions agree to 1e-14",
         "file_value": "not in any R107 result file (test bound 1e-7)",
         "recomputed_with_R108_code": healpix_convention_agreement()},
        {"doc": "TF1", "claim": "residual falls by about 4 when node spacing halves",
         "file_value": "not in any R107 result file",
         "R108_F2_cell_end_ratio_per_doubling": f2_ratios()},
        {"doc": "RESULTS_KO", "claim": "BJS quadrature 5e-13, m != +-1 power <= 1e-19, 99% TT power at ell 8-20",
         "file_value": "not in any R107 result file"},
    ]
    write_json(OUT_DIR / "REVIEW" / "R107_CLAIM_CHECK.json",
               {"schema": "htt.r108.r107_claim_check.1", "source_file": str(path.relative_to(REPO)),
                "source_sha256": sha256_file(path), "git": git_state(), "checks": checks})


if __name__ == "__main__":
    main()
