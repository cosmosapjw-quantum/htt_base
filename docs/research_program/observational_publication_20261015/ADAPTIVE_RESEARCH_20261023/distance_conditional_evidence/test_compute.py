"""R25 controls using retained products; never reruns a training or null fit."""
import json
import math

import numpy as np
from scipy.special import logsumexp

import compute as c


def test_retained_source_and_full_permutation():
    rows, ids, groups, folds, y, s, features, oof, saved = c.read_sources()
    result = json.loads((c.HERE / "RESULT.json").read_text())
    assert len(rows) == 274 and len(result["components"]) == 40
    assert len(result["null_fits"]) == 20
    permuted = {}
    for scen, sc in saved["scenarios"].items():
        V = c.covariance(s, groups, sc["a_mag"], sc["b_mag"])
        for fold in range(5):
            tr = np.flatnonzero(folds != fold)[::-1]
            te = np.flatnonzero(folds == fold)[::-1]
            B, _, L, _ = c.conditional(V, y, tr, te)
            for model in ("B_optical_STF", "C_union"):
                X = np.column_stack([features[z] for z in c.MODEL_NAMES[model]])
                fit = sc["models"][model]["folds"][fold]
                beta = np.asarray(fit["coefficient_raw_units"])
                pred = X[te] @ beta + B @ (y[tr]-X[tr]@beta)
                score, _ = c.density(y[te], pred, L, fit["sigma2_ML_train"])
                ref = next(z for z in result["components"] if z["scenario"] == scen
                           and z["model"] == model and z["fold"] == fold)
                c.check_close(score, ref["log_density"], "all 40 permutation block scores", atol=1e-8)
                permuted[(scen, model, fold)] = score
    fold_logs = []
    for fold in range(5):
        logq = logsumexp([score for (scen, model, f), score in permuted.items() if f == fold])-math.log(8)
        den = max(z["ellstar"] for z in result["null_fits"] if z["fold"] == fold)
        fold_logs.append(logq-den)
    c.check_close(logsumexp(fold_logs)-math.log(5), result["logE_arithmetic_fold_average"],
                  "permuted arithmetic fold aggregate", atol=1e-8)
    for scen, models in result["full_tensor_carrier"].items():
        for model, carrier in models.items():
            full = saved["scenarios"][scen]["models"][model]["full_fit"]
            assert carrier["coefficient_raw_units"] == full["coefficient_raw_units"]
            assert carrier["coefficient_covariance_raw_units"] == full["coefficient_covariance_raw_units"]
            assert carrier["angular_tensor_state"] == full["angular_tensor_state"]


def test_correlated_normalization_and_saturated_control():
    f = c.fixture_controls()
    c.check_close(f["quadrature_conditional_expectation"], 1, "conditional integral", atol=1e-12)
    assert f["saturated_fold_E"] == 0


if __name__ == "__main__":
    test_retained_source_and_full_permutation()
    test_correlated_normalization_and_saturated_control()
    print("2 R25 tests PASS; 40 permuted blocks and aggregate checked")
