"""Independent small matrix controls for the retained K03 power calculation."""

import numpy as np

from design import ALPHA, EPSILONS, TAUS, calculation, load_sources


def test_diagonal_eigenvalue_oracle_and_monotonicity():
    inp, baseline = load_sources()
    result = calculation(inp, baseline)
    assert len(result["rows"]) == 3 * len(TAUS) * len(EPSILONS)
    eigenvalues = np.linalg.eigvalsh(np.array(inp["history_covariance_uasyr2"]))
    for direction in range(3):
        preceding = float("inf")
        for tau in TAUS:
            # Orthogonal original eigendirections make the updated eigenvalues exact.
            modified = eigenvalues.copy()
            modified[direction] += tau**2
            expected_best_info = 1 / min(modified)
            row = next(r for r in result["rows"] if r["covariance_eigenvector_index"] == direction and r["tau_uasyr"] == tau and r["epsilon"] == 0.3)
            assert abs(row["best_information_per_uasyr2"] - expected_best_info) < 2e-14
            assert row["best_information_per_uasyr2"] <= preceding + 2e-14
            assert row["oracle_level_005_power_upper"] >= ALPHA
            preceding = row["best_information_per_uasyr2"]


def test_baseline_and_target_multiplier_definition():
    inp, baseline = load_sources()
    result = calculation(inp, baseline)
    row = next(r for r in result["rows"] if r["covariance_eigenvector_index"] == 0 and r["tau_uasyr"] == 0 and r["epsilon"] == 0.1)
    assert abs(row["oracle_level_005_power_upper"] - 0.05002494221604289) < 1e-12
    assert abs(row["mahalanobis_max"] - 0.00024179087493026385) < 1e-15
    assert row["information_multiplier_to_oracle_power"]["0.9"] > row["information_multiplier_to_oracle_power"]["0.8"] > row["information_multiplier_to_oracle_power"]["0.5"] > 1
    assert result["checks"]["original_schur_vs_inverse_scaled_residual"] < 1e-10
    assert result["checks"]["maximum_updated_inverse_vs_sherman_morrison_scaled_residual"] < 1e-10
