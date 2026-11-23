"""Time the analytic predictor and a direct GLS finite-difference reference at matched accuracy."""
import argparse
import json
import os
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import scipy

from htt.infer.cf4_predictive_response import predictive_contrasts, predictive_covariance_response
from scripts.r101.cf4_predictive_response import R100


def direct_kriging(y, c, x, h):
    """R99 block GLS in an arbitrary train/test design, using direct linear solves."""
    n = len(x)
    t = c[:n, :n]
    kr = np.linalg.solve(t, c[:n, n:]).T
    v = np.linalg.solve(t, x)
    beta_cov = np.linalg.inv(x.T @ v)
    beta = beta_cov @ v.T @ y[:n]
    d = h - kr @ x
    mean = h @ beta + kr @ (y[:n] - x @ beta)
    s = c[n:, n:] - kr @ c[:n, n:] + d @ beta_cov @ d.T
    residual = y[n:] - mean
    chi = residual @ np.linalg.solve(s, residual)
    logp = -0.5*(np.linalg.slogdet(s)[1] + chi + len(h)*np.log(2*np.pi))
    return mean, s, chi, logp


def benchmark(path):
    with np.load(path, allow_pickle=False) as f:
        c0, c1 = f["C_WF_R5_inherited"], f["C_WF_R5_full_k"]
        y = f["b_published_4x9"].ravel()
    dc = c1-c0
    x = np.tile(np.eye(9), (2, 1))
    contrasts = predictive_contrasts(x, x)
    keys = ["mean", "covariance", "chi2", "log_density"]

    def direct(alpha):
        c = c0+alpha*dc
        base = direct_kriging(y, c, x, x)
        step = 1.e-5
        plus = direct_kriging(y, c+step*dc, x, x)
        minus = direct_kriging(y, c-step*dc, x, x)
        return [*base, *((a-b)/(2*step) for a, b in zip(plus, minus))]

    def analytic(alpha):
        out = predictive_covariance_response(y, c0+alpha*dc, dc, contrasts)
        return [out[k] for k in keys + [s+"_tangent" for s in keys]]

    grid = np.linspace(0, 1, 21)
    worst = max(np.max(np.abs(q-r)) for a in grid for q, r in zip(direct(a), analytic(a)))
    if worst > 1e-7:
        raise ArithmeticError(f"unmatched accuracy: {worst}")
    times = [[], []]
    for repeat in range(11):
        for i in (repeat%2, (repeat+1)%2):
            function = (direct, analytic)[i]
            start = perf_counter()
            for alpha in grid:
                function(alpha)
            times[i].append((perf_counter()-start)/len(grid))
    us = np.median(times, axis=1)*1e6
    return dict(method="21 alpha points, one warm pass, 11 alternating runs, median per point; "
                       "full means, covariances, log densities, chi2 and all tangents. "
                       "QR contrasts reused once for the fixed design. Reference is classic GLS "
                       "plus two neighboring GLS calls for central differences.",
                max_absolute_output_discrepancy=worst, target_max_absolute_error=1.e-7,
                reference_median_us=us[0], analytic_median_us=us[1],
                reference_over_analytic=us[0]/us[1],
                threads={k: os.getenv(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
                scipy=scipy.__version__, numpy=np.__version__, python=platform.python_version(),
                scope="Compressed 36x36 R100 STF/monopole/dipole window problem only")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=R100 / "CF4_FULL_KBAND_COVARIANCES.npz")
    args = parser.parse_args()
    print(json.dumps(benchmark(args.matrix), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
