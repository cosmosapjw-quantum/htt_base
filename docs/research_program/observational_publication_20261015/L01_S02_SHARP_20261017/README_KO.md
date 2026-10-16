# HTT six-paper S02/L01 연구 패키지 (2026-10-17)

Authoritative prior: GitHub Draft PR #551, `research/htt-sixpaper-h02-l03-calibration-prior-paired-null-20261017`, SHA `6c97e3be2fae0fbbdb5a7392258f3a78cdc3556c`. **All inputs are complete in this ZIP**, except Planck native high-resolution polarization masks / full real end-to-end null / physical CF4 selection. Nothing contacts the network.

Use Python 3.11+ with NumPy, SciPy, pytest and matplotlib (tested Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, pytest 9.0.2, matplotlib 3.10.8). Commands from extracted ZIP top directory:

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests
OPENBLAS_NUM_THREADS=1 python src/finite_t_lift.py
OPENBLAS_NUM_THREADS=1 python src/s02_interval_coupled.py
python src/signed_sector_box.py
python src/plot_results.py
python scripts/verify_manifest.py
```

Machine-readable source/results: `results/L01_SOURCE_FINITE_MINIMAL_LIFT.json`, `results/S02_CONDITIONAL_SHARP_EVENT_ENVELOPES.json`, and `results/S02_SIGNED_MES_INTERVAL_THEOREM.json` (the last is manufactured, not CF4 physical inference). Figures: `results/L01_SOURCE_MINIMUM_HIGH_LIFT.png`, `results/S02_SHARP_WORKING_EXCEEDANCE_INTERVALS.png`. Source NPZ and original H03 ZIP/CF4 group NPZ reside in `source/` and have SHA-pinned identities in the code. Scientific caveats and proofs: `research/SCIENTIFIC_RESULTS_KO.md`. All `a,b,R` in numeric examples are assumed hard bounds/scenarios, not fitted physical uncertainty.

Scientific statuses: L01 and S02 `pending`. 7 external physical input blockers still unresolved. 6-paper DAG 14/42 completed scoped. Original canonical DAG/ready queue are not changed. Native independent subagents and full repo CI NOT_RUN.
