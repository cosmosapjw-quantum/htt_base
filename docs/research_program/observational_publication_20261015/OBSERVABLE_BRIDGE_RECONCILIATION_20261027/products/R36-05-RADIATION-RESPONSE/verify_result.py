"""Independent recount of saved R36-05 arrays against the candidate summary."""

import json
from pathlib import Path

import numpy as np

from radiation_core import STF_BASIS


HERE = Path(__file__).resolve().parent
ARRAYS = Path("/mnt/extdrive/workdir/htt_open_data/r36_radiation_response_actual/sample_arrays.npz")


def verify() -> dict:
    result = json.loads((HERE / "RESULT.json").read_text())
    details = []
    maximum_carrier_error = 0.0
    with np.load(ARRAYS) as saved:
        for row in result["methods"]:
            stem = f"{row['case']}_{row['method']}"
            truth = result["truth"][row["case"]]
            cal_d = saved[f"{stem}_cal_D"]
            test_d = saved[f"{stem}_test_D"]
            cal_a = saved[f"{stem}_cal_A"]
            test_a = saved[f"{stem}_test_A"]
            r = np.sort(np.linalg.norm(cal_d - row["D_noiseless"], axis=1))
            radius = r[row["quantile_indices_1based"]["D"] - 1]
            assert radius == row["D_radius"]
            e = np.sort(cal_a - row["A_noiseless"])
            lo = e[row["quantile_indices_1based"]["A_low"] - 1]
            hi = e[row["quantile_indices_1based"]["A_high"] - 1]
            assert [lo, hi] == row["A_error_quantiles"]
            valid = saved[f"{stem}_test_valid"]
            d_hit = valid & (np.linalg.norm(test_d - truth["physical_D"], axis=1) <= radius)
            a_low = np.maximum(0, test_a - hi)
            a_high = test_a - lo
            nonempty = valid & (a_high >= 0)
            a_hit = nonempty & (a_low <= truth["physical_A"]) & (truth["physical_A"] <= a_high)
            d_method = valid & (np.linalg.norm(test_d - row["D_noiseless"], axis=1) <= radius)
            a_method = nonempty & (a_low <= row["A_noiseless"]) & (row["A_noiseless"] <= a_high)
            assert int(d_hit.sum()) == row["D_physical_target_coverage"]["hits"]
            assert int(a_hit.sum()) == row["A_physical_target_coverage"]["hits"]
            assert int(d_method.sum()) == row["D_method_target_coverage"]["hits"]
            assert int(a_method.sum()) == row["A_method_target_coverage"]["hits"]
            width = saved[f"{stem}_test_A_width"]
            assert np.array_equal(width, np.where(nonempty, a_high - a_low, np.nan), equal_nan=True)
            covariance = np.cov(saved[f"{stem}_cal_fP"], rowvar=False, ddof=1)
            assert np.array_equal(covariance, np.array(row["fP_covariance"]))
            for phase in ("cal", "test"):
                tensor = saved[f"{stem}_{phase}_stress"]
                rho = saved[f"{stem}_{phase}_rho"]
                f_p = saved[f"{stem}_{phase}_fP"]
                observed_f = tensor[:, 0, 1:] / rho[:, None]
                observed_p = np.einsum("aij,nij->na", STF_BASIS,
                                       tensor[:, 1:, 1:]) / rho[:, None]
                maximum_carrier_error = max(maximum_carrier_error,
                                            float(np.max(abs(f_p[:, :3] - observed_f))),
                                            float(np.max(abs(f_p[:, 3:] - observed_p))))
            details.append({"case": row["case"], "method": row["method"],
                            "D_hits": int(d_hit.sum()), "A_hits": int(a_hit.sum()),
                            "radius": float(radius),
                            "nonempty_A": int(nonempty.sum())})
        if maximum_carrier_error > 2e-14:
            raise AssertionError(f"saved tensor/fP mismatch {maximum_carrier_error}")
        for a in (0, 2e-5, .02):
            for b in (.00123, .3):
                case = f"a{a:g}_b{b:g}"
                assert len(saved[f"{case}_eta_cal"]) == 8191
                assert len(saved[f"{case}_eta_test"]) == 4096
    out = {"status": "PASS_SCOPED_RECOUNT", "rows": len(details),
           "maximum_tensor_to_fP_error": maximum_carrier_error,
           "details": details, "scope": "Saved conditional synthetic arrays only; no empirical calibration."}
    (HERE / "VALIDATION.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in verify().items() if k != "details"}))
