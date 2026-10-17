# HTT P2/L01 OE provenance and PMASK semantic audit (2026-10-17)

This package is a bounded **repair/enabling research result** stacked on GitHub Draft PR #553. The existing six-paper DAG and previous physical claim gates are unchanged.

## What was fixed

The published OE SHA-256 constant contains **45 hexadecimal characters**, not the required 64. The old script's `FITS original SHA drift OE` is an uninformative conflation. `verify_native_files` now throws a typed `SourceIdentityError` with receipt; `--verify-only` emits structured JSON for all three source files and exits **2** while any source is unverified. No bypass is added to the actual scientific operator. The wrong 45-digit original remains recorded as evidence, never quietly replaced by the hash measured on the local copy.

The independent narrow `fits_source_identity.py` audits the official Planck two-HDU `PMASK` Galactic NESTED float32 format without requiring healpy or astropy. Optional `--compare-root` compares each decoded PMASK pixel with an independently held reference in bounded memory. Only identical decoded values with matching semantic-critical layout yield `SEMANTIC_EQUIVALENT_PMASK`; it does **not** admit a different byte source as the original or establish a physical E/B result. Other FITS types, transformed coordinate frames and different HEALPix ordering require another validated adapter and remain unsupported, not silently certified.

## Commands

From extracted directory:

```bash
python -m pytest -q tests
python src/native_planck_pol_response.py --root /mnt/extdrive/workdir/htt_open_data --verify-only > OE_IDENTITY_AUDIT.json
# exit 2 is expected until all three independently source-qualified 64-hex SHA values match
python src/native_planck_pol_response.py --root /mnt/extdrive/workdir/htt_open_data --compare-root /path/to/INDEPENDENT_REFERENCE_ROOT --verify-only > OE_SEMANTIC_COMPARE.json
```

Only after OE provenance is genuinely repaired and the full source-byte lock admits every file should the original production command be attempted. This package keeps the historical OE lock malformed to preserve provenance of the observed defect. Do not simply set `SOURCE['OE']` to the currently observed digest; compare an independently downloaded original with publisher headers/checksums and record the qualified 64-hex digest in a new versioned source manifest before deliberately migrating the lock.

Tested in sandbox: Python 3 with NumPy/SciPy/pytest, **11 targeted tests passed** (synthetic FITS byte/hash/semantic distinctions, malformed lock, truncation, ordering, pixel-change, Gram resolvent). `astropy` and `healpy` unavailable in sandbox; 2048 native source/effective K physical run NOT_RUN. Code is a standalone copy of original PR #553 local script plus typed audit repair; existing PR #553 source is unchanged until posted in follow-on draft.
