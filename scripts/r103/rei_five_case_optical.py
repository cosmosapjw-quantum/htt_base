"""Finite reionization depths of five archived materials on the same mean redshift interval."""
import argparse
import json
from pathlib import Path

import numpy as np
from bass.recombination.rei_material_history import CASE_Q, FIVE_CASE_PATH, FIVE_CASE_SHA, REI_COMMIT, ReiMaterialHistory
from bass.recombination.reionization import C_LIGHT, SIGMA_T
from bass.recombination.tilted_hyrec import TiltedHyrecHistory


def compute(path):
    cases = {}
    for case, q in CASE_Q.items():
        src = ReiMaterialHistory(path, case=case)
        if src.sha256 != FIVE_CASE_SHA:
            raise ValueError("five-case inspection archive required")
        hist = TiltedHyrecHistory.from_rei_history(src, [20., 4.])
        proper = C_LIGHT * SIGMA_T * 1e6 * np.trapezoid(src.ne, src.t)
        cases[case] = {"q_ref": q, "rows": len(src.N),
                       "tau": float(hist.kappa[0]), "time_trapezoid_tau": float(proper)}
    def decompose(key, magnitude, plus, minus):
        z = cases["ZERO"][key]
        p, m = cases[plus][key], cases[minus][key]
        return {"q_magnitude": magnitude, "odd": (p-m)/2, "even_minus_zero": (p+m)/2-z}
    response = {
        key: [decompose(key, .005, "SHEAR_HALF_PLUS", "SHEAR_HALF_MINUS"),
              decompose(key, .01, "SHEAR_PLUS", "SHEAR_MINUS")]
        for key in ("tau", "time_trapezoid_tau")
    }
    return {"schema": "htt.r103.rei_five_case_optical/1", "commit": REI_COMMIT,
            "source_path": FIVE_CASE_PATH, "source_sample_sha256": FIVE_CASE_SHA,
            "status": "CONDITIONAL_PRESCRIBED_BACKGROUND_HISTORIES",
            "mean_redshift_interval": [20,4], "cases": cases, "paired_response": response,
            "notes": ["Optical depth is dimensionless; these five signed shear scenarios share a prescribed model.",
                      "Even and odd optical-depth differences are finite differences of inspection samples, without a native trajectory-resolution uncertainty. They do not measure cosmic shear."],
            "physical_Pi": None, "calibrated_p": None}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path, default=Path("docs/research_program/observational_publication_20261015/R103_SOLVER_SOURCE_CONTINUATION_20261123/REI_FIVE_CASE_OPTICAL.json"))
    args = ap.parse_args()
    obj = compute(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
