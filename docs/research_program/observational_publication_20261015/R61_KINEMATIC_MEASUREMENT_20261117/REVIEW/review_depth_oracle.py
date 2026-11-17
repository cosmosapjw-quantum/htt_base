#!/usr/bin/env python3
"""Read-only source-level counterexample for R61-F1.

Run from the existing checkout:
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
    .venv/bin/python -B /path/to/r61_review_depth_oracle.py --repo-root .
No results or repository files are written.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np
from scipy.linalg import cholesky, solve_triangular

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo-root", type=Path, required=True)
args = parser.parse_args()
root = args.repo_root.resolve()
sys.path.insert(0, str(root / "scripts/r58"))
import run_r58_owned_tensor as old
de, _, cf, _ = old.import_modules(root, None)
data = cf.load()
cat = data["cat"]
n, z = cat["n_J2000"], cat["z_CMB"]
lr = de.log_distance_ratio(cat["dmzp"], z, cf.OMEGA_M)
tau2 = de.log_noise_variance(cat["e_dmzp"], lr["g_per_km_s"], cf.SIGMA_STAR)
with np.load(cf.OUT_DIR / "R54_L04_SURVEY_LABELS.npz", allow_pickle=False) as lab:
    if not np.array_equal(lab["group_id"], cat["group_id"]):
        raise ValueError("Survey label/source order mismatch")
    survey = dict(labels=lab["survey"].copy(),
                  raw_labels=lab["survey_unpooled"].copy(), min_side=100)
ops, _ = cf.build_operators(cat, data["a_raw"], tau2, survey=survey)
prefix = root / "docs/research_program/observational_publication_20261015"
carrier_path = prefix / "R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/OWNED_TENSOR_CARRIERS.npz"
expected = "42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d"
observed = hashlib.sha256(carrier_path.read_bytes()).hexdigest()
if observed != expected:
    raise ValueError("R58 carrier identity mismatch")
carrier = np.load(carrier_path, allow_pickle=False)
depth = np.load(prefix / "R61_KINEMATIC_MEASUREMENT_20261117/RESULTS/DEPTH/DEPTH_RESPONSE_CARRIERS.npz",
                allow_pickle=False)

# E0 is the first Frobenius-normalized STF tensor. Its angular column is 4:
# column 0=monopole, columns 1..3=dipole, columns 4..8=STF5.
f = ((z - .02) / .05) * ((z - .08) / .05)
raw = .01 * f * de.multipole_basis(n)[:, 4]
rows = carrier["row_indices32"]
result = []
for name in old.VARIANTS:
    op = ops[name][rows]
    X = depth[name + "__response32x16"]
    C = carrier[name + "__cov32"]
    L = cholesky(C, lower=True)
    scale = np.r_[carrier["parameter_scale"], np.full(5, .01)]
    Xw = solve_triangular(L, X, lower=True)
    Q, R = np.linalg.qr(Xw * scale)
    dy = op @ raw
    bias = scale * np.linalg.solve(R, Q.T @ solve_triangular(L, dy, lower=True))
    contrast = 1.2 * bias[11:]
    result.append({
        "model": name,
        "calibration_endpoint_RMS_difference": 0.,
        "fitted_contrast_RMS_bias": float(np.sqrt(2 / 15) * np.linalg.norm(contrast)),
        "fitted_delta_kappa": contrast.tolist(),
        "whitened_omitted_mean_norm": float(np.linalg.norm(solve_triangular(L, dy, lower=True))),
    })
print(json.dumps({
    "finding": "R61-F1",
    "profile": ".01*((z-.02)/.05)*((z-.08)/.05)*E0",
    "physical_endpoints": [.02, .08],
    "carrier_sha256": observed,
    "method": "Cholesky whitening followed by independent QR; no fit_linear or R61 optimizer",
    "results": result,
}, indent=2))
