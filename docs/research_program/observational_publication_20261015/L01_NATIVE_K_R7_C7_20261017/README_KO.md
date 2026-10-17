# HTT P2/L01 native POL geometry spectral audit (2026-10-17)

This additive package reuses exact tested PR #555 v2 source-lock and local spin-2 code. It implements scoped R7/C7 for the **actual native Planck PR3 mask geometry output already reported by the user**, without recreating inaccessible FITS or promoting a physical P2 claim. The user should keep the original native source JSON and both NPZ files unchanged.

Requirements: Python 3.11+, NumPy, SciPy, pytest. For optional `--all-m-spin-check` or `--native-replay`, also healpy and astropy are needed on the user's local machine. The actual original operator is NOT shipped inside this archive.

```bash
python -m pytest -q tests
python scripts/verify_manifest.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/l01_k_spectral_certificate.py \
  --receipt /mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json \
  --out /mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_SPECTRAL_CERT_20261017.json \
  --all-m-spin-check
```

The analyzer checks both NPZ against the user-reported SHA pins, computes spectral E/B symmetry and rank, low-B reachability from high-E, sharp coefficient-space envelope and actual norm of the two-mask difference. The physical high-E norm is not provided and is never inferred. For optional independent source replay, append:

```bash
--native-replay --root /mnt/extdrive/workdir/htt_open_data \
  --compare-root /mnt/extdrive/workdir/htt_planck_irsa_reference
```

See `research/R7_C7_NATIVE_GEOMETRY_THEORY_KO.md` for complete mathematical proof and evidence status. User-local native source results: reported; sandbox code tests: actually run; optional all-m native healpy: NOT_RUN in this sandbox. Official 6-paper DAG remains 14/42, READY L01/S02, all six NOT_READY_TO_SUBMIT. Do not treat K as Planck measured BB power or as an E2E calibrated null.
