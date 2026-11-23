"""Reproduce the finite zbar=20..4 REI source-to-HTT optical check on a pinned native product."""
import argparse
import json
from pathlib import Path

import numpy as np

from bass.recombination.rei_material_history import ReiMaterialHistory, REI_COMMIT, SAMPLE_PATH, _expansion
from bass.recombination.reionization import C_LIGHT, SIGMA_T
from bass.recombination.tilted_hyrec import TiltedHyrecHistory


def compute(path):
    source = ReiMaterialHistory(path)
    requested = np.array([4., 5., 6., 8., 10., 15., 20.])
    history = TiltedHyrecHistory.from_rei_history(source, requested)
    measure = history.opacity_history()
    whole = measure.cells(source.N)
    suite = measure.cells(np.sort(history.N_grid))
    t = source.t
    independent_tau = C_LIGHT * SIGMA_T * 1e6 * np.trapezoid(source.ne, t)
    dtau = float(history.kappa[-1])
    native_nodes = measure.rate(source.N)
    charge_rate = C_LIGHT * SIGMA_T * 1e6 * source.ne / _expansion(np.exp(source.N))
    relative = float(np.max(np.abs(native_nodes / charge_rate - 1)))
    relative_to_proper_time = dtau / independent_tau - 1
    visibility_error = abs(np.sum(suite.visibility_mass) + np.expm1(-dtau))
    rebin = abs(whole.delta_tau.sum() - suite.delta_tau.sum())
    if relative > 2e-8 or abs(relative_to_proper_time) > 1e-4 or rebin > 1e-13 or visibility_error > 1e-13:
        raise ValueError("source density, proper-time integration, partition or visibility cross-check failed")
    for z_bad in ([0, 5], [5, 21], [8, 8]):
        try:
            source.evaluate(z_bad)
        except ValueError:
            continue
        raise ValueError("invalid REI support was accepted")
    return {
        "schema": "htt.r103.rei_material_source/1",
        "repository": "cosmosapjw-quantum/rei_bianchi",
        "commit": REI_COMMIT, "public_sample_path": SAMPLE_PATH,
        "input_sha256": source.sha256, "input_kind": source.sampling, "input_rows": len(t),
        "source_scenario": "PLANCKLIKE_MD14_BB50K_CONDITIONAL_HHE_V1 / SHEAR_PLUS +0.01",
        "mean_z_window_high_to_low": [20., 4.], "observer_mean_z": 4.,
        "proper_time_elapsed_s": float(t[-1] - t[0]),
        "conditional_delta_tau_20_to_4": dtau, "independent_ne_proper_time_trapezoid": float(independent_tau),
        "relative_vs_proper_time_quadrature": float(relative_to_proper_time),
        "rebin_abs": float(rebin), "visibility_telescoping_abs": float(visibility_error),
        "max_abs_charge_identity": source.charge_error, "max_relative_density_product_error": source.relative_density_error,
        "max_relative_rate_vs_donor_ne_on_knots": relative,
        "mean_z": requested.tolist(), "x_e_per_H": history.x_e.tolist(), "finite_tau_from_z4": history.kappa.tolist(),
        "outside_support_and_duplicate_nodes_rejected": True, "observed_reionization_constraint": None,
        "notes": ["Native conditional prescribed-background source, with no tilt, fitted ionizing source or post-z4 foreground.",
                  "Public inspection output has 1001 samples of the 312238-row full native history. Time-trapezoid difference diagnoses sampling/quadrature and does not bound microphysical or model uncertainty.",
                  "zbar is the mean-scale-factor redshift. A ray/observer redshift conversion needs a separate transfer."],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="REI fifth_abundances.csv.gz, or hash-verified full normalized file")
    p.add_argument("--output", type=Path, default=Path("docs/research_program/observational_publication_20261015/R103_SOLVER_SOURCE_CONTINUATION_20261123/REI_SOURCE_RESULT.json"))
    args = p.parse_args()
    result = compute(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
