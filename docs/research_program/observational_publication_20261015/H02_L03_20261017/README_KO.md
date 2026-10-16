# HTT six-paper H02/L03 independent source-conditional research loop

The original publication DAG and existing `main` are **not modified**. This packet adds an independent analysis of known CF4 35,970 selected group records and six paired Planck temperature-processing conditions, not new observational data. It does not close H02/L03 physical acceptance or S02/L01 READY nodes.

## Sandbox / local replay

```bash
unzip -q HTT_H02_L03_SOURCE_CONDITIONAL_20261017.zip -d /tmp
cd /tmp/htt_h02_l03_20261017
python -m pip install numpy scipy pytest matplotlib
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests
OPENBLAS_NUM_THREADS=1 python src/run_studies.py
OPENBLAS_NUM_THREADS=1 python src/plot_results.py
python scripts/verify_manifest.py
```

The `inputs/` files are original-source-derived, SHA-256 locked **previous** NPZs, not copies of the user's recently downloaded complete 38,053-group catalog or Planck Q/U FITS masks. For a full 55,877-galaxy/38,053-group source audit use the preceding PR #550 scripts on `/mnt/extdrive/workdir/htt_open_data` and supply its generated `CF4_RAW_FULL_SOURCE_AUDIT.json`.

## Outputs and interpretation

- `results/H02_ACTUAL_SELECTED_SOURCE_FISHER.json`: real selected-source angular Fisher spectrum under *assumed* independent diagonal `e_DMzp` noise and assumed Gaussian method-specific angular calibration priors; **not a calibrated CF4 likelihood**.
- `results/L03_ACTUAL_SOURCE_PAIRED_SCAN.json`: source-bounded 100-training/200-heldout 6-condition paired source scan; **not a physical E2E PTE**.
- `results/*.png`: H02 calibration sensitivity and L03 paired-condition covariance heatmap.
- `docs/RESEARCH_LOOP_KO.md`: derivations, numerical outcomes, required physical sources and claim-gate status.
- `results/TEST_RECEIPT.json`: actual test commands/results and identity scope.

The scientific next actions: empirically source-calibrate CF4 W1-TF parent completeness and calibration/velocity covariance (H02); obtain real PR3 polarization mask/beam E2E simulated products with common sky IDs and method-specific systematics (L01/L03); allow S02 signed posterior pushforward only after the necessary physical sectors or a justified partially identifiable narrower estimand exists.
