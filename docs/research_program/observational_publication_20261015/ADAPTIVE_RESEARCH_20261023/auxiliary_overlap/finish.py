"""Finish R25 presentation from the frozen successful numerical core, without new LP calls."""
from __future__ import annotations

import json
from collections import Counter

from compute import HERE, CELLS, SOURCE_HASHES, TASK, PACKET, make_figure, sha, dump


def main():
    for path, expected in SOURCE_HASHES.items():
        assert sha(path) == expected
    result = json.loads((HERE/"RESULT.json").read_text())
    assert result["task_id"] == TASK and result["packet_id"] == PACKET
    assert result["full628"]["status"] == "EXACT_INFEASIBLE"
    assert result["supported625"]["status"] == "STRICTLY_POSITIVE_COARSE_CALIBRATION"
    assert result["supported625_fine"]["status"] == "EXACT_INFEASIBLE_EVEN_SIGNED"
    counts = {tuple(c[k] for k in ("velocity", "incl_available", "Bmag_available")): c
              for c in result["cohort"]["cells"]}
    assert len(counts) == 16
    tc = Counter({c: counts[c]["target"] for c in CELLS})
    oc = Counter({c: counts[c]["observed"] for c in CELLS})
    labels = [(r["scenario"], r["model"]) for r in result["joint_carrier"]["source_fits"]]
    make_figure(tc, oc, labels, result["joint_carrier"]["windows"])
    ess = result["supported625"]["concentration_ESS"]
    lo = result["supported625"]["min_weight"]
    hi = result["supported625"]["max_weight"]
    report = ("# R25 auxiliary overlap\n\n"
              "The 628-target indicator system is exactly infeasible: three target cells have no observed distance. "
              "Deleting those cells defines a different 625-target estimand, with 274 strictly positive calibrated weights "
              f"(concentration ESS {ess:.6f}, range {lo:.8g}–{hi:.8g}). "
              "Fine within-cell velocity balance is again exactly infeasible: the sole observed high-cell velocity "
              "is 10161 km/s, while the four targets sum to 2547 km/s above four times that value.\n\n"
              "The joint NPZ preserves every residual's scalar, direction vector and full STF tensor for all 12 "
              "scenario/model pairs on the same 274 PGCs. RESULT.json gives uniform and calibrated global and L/M/H "
              "window means, masses, differences, and original coefficient/covariance references. The figure shows "
              "observed support and the resulting scalar mean shifts.\n\n"
              "The undefined 354 outcomes, including 351 in supported cells, remain unmeasured. Observed quality "
              "counts 269+1+3+1 apply only to 274. These weights encode auxiliary overlap and do not identify "
              "the missing tensor law, a physical Pi, true depth, or a native Bianchi result. Original acceptance "
              "remains HOLD pending independent review.\n")
    (HERE/"REPORT.md").write_text(report)
    print(json.dumps({"status": "presentation_complete", "figure_bytes": (HERE/"figure.png").stat().st_size}))


if __name__ == "__main__":
    main()
