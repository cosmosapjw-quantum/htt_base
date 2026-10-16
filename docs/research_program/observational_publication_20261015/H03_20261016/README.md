# HTT six-paper publication P3/H03: fixed-law Cosmicflows-4 direction/redshift tomography

This is the scoped continuation of draft PR #540 H01, on the **2026-10-15 six-paper 42-node publication DAG**. The 9-dimensional observed-source processing calculation does not infer cosmological H(z,n), H0-dipole detection, vorticity, Bianchi shear, a physical null p-value, or an independently validated CF4 selection/method covariance.

## Deterministic replay

The package includes the immutable *derived* 35,970-group source NPZ from the user's prior CF4 release intake, not the raw complete galaxy catalogue. It is SHA-pinned; any missing or changed source raises an error. Use an isolated Python environment with `numpy`, `scipy`, `matplotlib`, `pytest`. From this directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python src/run_h03.py --source inputs/selected_source_observables.npz --output /tmp/new_h03_result_001
python src/plot_h03.py --result /tmp/new_h03_result_001/H03_SOURCE_TOMOGRAPHY.json --output /tmp/new_h03_figures_001
```

`run_h03.py` is create-only, refuses overwrite. In the user's existing `/home/cosmosapjw/Dropbox/bianchi/htt_base`, it can find the exact read-only Loop6 source directly if the package input is not present. GitHub publishes code, tests, small result JSON and paper-specific DAG change but **does not add the 1.2 MB CF4 source**, which is contained in the separate checksum-verified ChatGPT Library backup. No new clone/worktree or main merge should be performed by default.

Primary output `results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json`; `H03_CONDITIONAL_MATRIX.npz` and PNG figures are retained in backup. Per-method zero-point gauge theorem in `H03_MEAN_GAUGE.json` is **first-order fixed-weight mean-design only**.

Six-paper canonical status: P3/H03 `completed_scoped`; P3/H02 selection/shared-calibration law remains input-blocked, P3/H04 still dependency-blocked. The other 41 nodes and six manuscript NOT_READY_TO_SUBMIT statuses remain unchanged.
