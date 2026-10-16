# Loop 9: full SMICA finite masked response

`C8-SMICA-FULL-MASK-FINITE-RESPONSE` uses the exact Loop 5 NSIDE64 RING support and the released Planck PR3 full SMICA temperature product. The calculation is a source-bound finite ℓ6..16 harmonic response. It is not a physical almost-EGS epsilon or Bianchi response.

From this directory:

```sh
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_finite_response.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -B run.py --output /path/to/new/output
```

The runner is create-only and validates all seven exact input hashes before reading the raw map. Local raw FITS and the K1 reduced cache remain outside Git. `results/response_v1/result.json` holds numbers, source identity, singular spectra and scope limits; `baseline_response_matrices.npz` holds the small response matrices. `REPORT_KO.md` records interpretation; `NEXT_RESEARCH_DAG.json` and its `machine_readable/` mirror record the next research transition.
