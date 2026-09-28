"""Bounded synthetic checks for a proposed R9 plan extension; no production data."""
import json
import math
from pathlib import Path

import numpy as np


def fisher(covariance, derivatives):
    inverse = np.linalg.inv(covariance)
    return np.array(
        [[0.5 * np.trace(inverse @ s @ inverse @ t) for t in derivatives]
         for s in derivatives]
    )


rng = np.random.default_rng(20260913)
blocks = rng.integers(-2, 3, size=(3, 7, 5)).astype(float)
c2, c3 = 2.0, 5.0
covariance = np.diag([c2] * 5 + [c3] * 7)
generators = []
for b in blocks:
    generators.append(np.block([[np.zeros((5, 5)), -b.T], [b, np.zeros((7, 7))]]))
derivatives = [g @ covariance + covariance @ g.T for g in generators]
f_joint = fisher(covariance, derivatives)
f_formula = (c2 - c3) ** 2 / (c2 * c3) * np.einsum('iab,jab->ij', blocks, blocks)
equal_covariance = 3.0 * np.eye(12)
equal_derivatives = [g @ equal_covariance + equal_covariance @ g.T for g in generators]

# Independent fixed processing plus independent parameter-free Gaussian noise.
processing = rng.normal(size=(8, 12)) / np.sqrt(12)
processed_covariance = processing @ covariance @ processing.T + 0.2 * np.eye(8)
processed_derivatives = [processing @ s @ processing.T for s in derivatives]
f_processed = fisher(processed_covariance, processed_derivatives)

# Unknown diagonal powers are orthogonal to beta in the ideal law, but can
# overlap the beta score after a fixed non-isometric projection.
power_derivatives = [np.diag([1.] * 5 + [0.] * 7), np.diag([0.] * 5 + [1.] * 7)]
f_with_powers = fisher(covariance, derivatives + power_derivatives)
f_processed_with_powers = fisher(
    processed_covariance,
    processed_derivatives + [processing @ s @ processing.T for s in power_derivatives],
)
cross = f_processed_with_powers[:3, 3:]
efficient = f_processed - cross @ np.linalg.pinv(f_processed_with_powers[3:, 3:]) @ cross.T

# An exactly matching nuisance covariance tangent removes its beta direction.
f_duplicate = fisher(covariance, derivatives + [derivatives[0]])
duplicate_cross = f_duplicate[:3, 3:]
duplicate_efficient = f_joint - duplicate_cross @ np.linalg.pinv(f_duplicate[3:, 3:]) @ duplicate_cross.T

def risk(delta):
    return 0.5 * math.erfc(delta / (2 * math.sqrt(2)))

results = {
    "scope": "synthetic matrices; conditional algebra corroboration only; no physical boost implementation or data admission",
    "seed": 20260913,
    "C2": c2,
    "C3": c3,
    "joint_fisher": f_joint.tolist(),
    "formula_max_abs_error": float(np.max(np.abs(f_joint - f_formula))),
    "equal_power_derivative_max_abs": float(max(np.max(np.abs(s)) for s in equal_derivatives)),
    "ideal_beta_power_cross_max_abs": float(np.max(np.abs(f_with_powers[:3, 3:]))),
    "processed_beta_power_cross_max_abs": float(np.max(np.abs(cross))),
    "raw_minus_processed_eigenvalues": np.linalg.eigvalsh(f_joint - f_processed).tolist(),
    "processed_minus_efficient_eigenvalues": np.linalg.eigvalsh(f_processed - efficient).tolist(),
    "efficient_fisher_eigenvalues": np.linalg.eigvalsh(efficient).tolist(),
    "duplicate_nuisance_direction0_remaining_max_abs": float(np.max(np.abs(duplicate_efficient[0]))),
    "rank_full_resolution_counterexample": {
        "epsilon": 0.01,
        "delta_theta": 1.0,
        "noise_sd_after_whitening": 1.0,
        "no_discrepancy_distance": 0.01,
        "no_discrepancy_equal_prior_minimax_error": risk(0.01),
        "discrepancy_radius": 0.006,
        "with_discrepancy_distance": max(0.01 - 2 * 0.006, 0.0),
        "overlap_witness_mean": 0.005,
        "with_discrepancy_equal_prior_minimax_error": 0.5,
    },
}
assert results['formula_max_abs_error'] < 1e-12
assert results['equal_power_derivative_max_abs'] == 0
assert results['ideal_beta_power_cross_max_abs'] == 0
assert min(results['raw_minus_processed_eigenvalues']) > -1e-10
assert min(results['processed_minus_efficient_eigenvalues']) > -1e-10
assert results['duplicate_nuisance_direction0_remaining_max_abs'] < 1e-12
Path(__file__).with_name('check_results.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
