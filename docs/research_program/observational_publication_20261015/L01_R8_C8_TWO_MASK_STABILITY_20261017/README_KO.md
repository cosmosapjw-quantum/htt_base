# HTT / P2-L01 : R8 + C8 two-mask finite-spin geometry

2026-10-17. Parent Draft PR #556 `cdfb86b8b9fb3238061136ea0f90d668dc49de94`. This is an **additive run package**, containing the same prior v2 source code and tests plus a new R8 scientific decision and C8 small-matrix stability script. No original Planck FITS, Q/U observations or user-native K NPZ are packaged. Original 42-node paper DAG is not changed.

## Tested sandbox contract

Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, pytest 9.0.2. Tests include native-independent manufactured masks, exact complex-doublet and sharpness witnesses, fail-closed native SHA and spectral receipt source mismatch, Weyl conditional rank, and zero-difference edge case. The `--all-m-spin-check` from R7/C7 was user-run and not replicated here. The optional 3D projection Matplotlib warning is not a failure of the analysis.

```bash
python -m pytest -q tests
python scripts/verify_manifest.py
```

## Actual user-local C8 computation

Run on your local machine with **the existing, unchanged** prior native JSON and two SHA-pinned NPZ plus the just-produced spectral JSON. Do not regenerate K to work around an identity mismatch.

```bash
ROOT=/mnt/extdrive/workdir/htt_open_data
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python src/l01_mask_difference_stability.py \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --spectral-receipt "$ROOT/provenance/L01_NATIVE_SPECTRAL_CERT_20261017.json" \
  --out "$ROOT/provenance/L01_R8_C8_TWO_MASK_STABILITY_20261017.json" \
  --benchmark-repeats 7
```

Only if a **separately justified** upper bound `epsilon` on spectral matrix numerical error `||δ(ΔK)||₂` exists, append `--operator-error-upper epsilon`. Do not equate tiny test residuals with an error *bound*. The script emits actual norm E_high-to-B_low difference, rank, paired SVD residual, fixed low-B contrast, NPZ pinned receipt, and local time measurements.

The exact conditional common-source bound for the real operator difference is `0.43962877239085046 * R` in the coefficient-space Euclidean norm for `||h_ell6..8|| <= R`; no physical `R` is identified. `ell>8`, beam, noise, foreground and end-to-end null remain outside the finite geometry model.

Scientific report: `research/R8_RESULT_ADMISSION_AND_C8_NUMERICS_KO.md`.

## Current bounded verification

Standalone sandbox (not user-native original FITS): `50 passed` using `OPENBLAS_NUM_THREADS=1`, including 39 previously frozen regressions and 11 new C8 checks. Manufactured example output is stored in `results/MANUFACTURED_R8_C8_NUMERICS.json`. It must never be substituted for the real native K spectra. NumPy and SciPy may share LAPACK; dual-library agreement is a useful numerical regression, not an independent algorithmic proof.
