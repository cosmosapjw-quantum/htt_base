# HTT P2/L01 Planck PR3 POL OE: source-lock v2, 국소 비교 및 기하 응답 실행 계약

2026-10-17 KST. Parent: [Draft PR #554](https://github.com/cosmosapjw-quantum/htt_base/pull/554); historical PR #553 and 45-digit OE lock unchanged. The six-paper publication DAG remains 14/42 completed_scoped, 28 pending; all six papers **NOT_READY_TO_SUBMIT**.

## Newly supplied evidence

The user executed original `--verify-only --compare-root` with Planck PR3 polarization masks and provided a structured receipt. Common and HM matched their pinned 64-hex SHA-256 and native PMASK layout. OE observed at both the local and separately held reference paths matched `1b2b4138f791b739938485fa0ebcac5f462e04fbc55626e93d71abd04aac3900` (64 hex), with pixel-by-pixel `SEMANTIC_EQUIVALENT_PMASK`. Historical 45-character constant differs by deletion of contiguous `fbc55626e93d71abd04`. This is user-supplied stdout, not assistant-executed local readback. The independent reference's official IRSA download origin is user-reported, not publisher-signed or machine-authenticated by this package.

## Opt-in v2, preserving original v1

`research/OE_SOURCE_LOCK_V2.json` is an explicitly versioned candidate source-lock, not a silent replacement of `SOURCE['OE']`. The code keeps `--source-lock v1` as default and preserves the historical malformed OE digest. `--source-lock v2` requires that `common` and `HM` still match their previous pinned SHA-256, and additionally requires a **distinct, non-symlink, non-hardlink OE reference** at `--compare-root`, matching the fixed 64-digit SHA, Galactic NESTED PMASK layout and every decoded PMASK pixel. Do not redownload `common`/`HM`: their v1 byte identity is reused.

The successful v2 admission is named `V2_REFERENCE_LOCK_ADMITTED_GEOMETRY_ONLY`, not official publisher-signed provenance, physical E/B signal, mask+beam transfer, FFP end-to-end or Planck detection. If the reference is not actually a faithful independent IRSA download, the external source-authenticity claim remains unresolved even with a PASS receipt.

## Run on the owner's local machine

From the extracted ZIP top directory:

```bash
python -m pytest -q tests
python scripts/verify_manifest.py
ROOT=/mnt/extdrive/workdir/htt_open_data
REF=/mnt/extdrive/workdir/htt_planck_irsa_reference
# common/HM are admitted by their existing v1 SHA; only OE needs the extra reference.
python src/native_planck_pol_response.py \
  --root "$ROOT" --compare-root "$REF" \
  --source-lock v2 --verify-only | tee OE_SOURCE_LOCK_V2_RECEIPT.json

# With v2 geometry admission PASS, and local healpy+astropy installed:
python src/native_planck_pol_response.py \
  --root "$ROOT" --compare-root "$REF" --source-lock v2 \
  --out "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json"
```

`--verify-only` exits 0 only if v2 admission for all three files succeeds; otherwise exits 2. The full path additionally performs `healpy.alm2map_spin` crosscheck, NESTED2048->RING64, thresholding, source-intersection matrix and K64x90 responses, and produces canonical RING64 binary-mask SHA-256 in JSON. **Do not interpret K as a measured Planck B-mode contamination or a calibrated physical null.** For publishing P2, subsequent beam/foreground/FFP matched null and selection correction remain mandatory.

## Validation evidence and narrower geometry semantics

Current sandbox (Python 3.13 / NumPy 2.3.5 / SciPy 1.17.0 / pytest 9.0.2): 24/24 tests PASS. Included: byte/semantic mismatch, defective v1 lock regression, v2 missing/modified/aliased reference fail-closed tests, positive CLI mock with only OE reference, source hash, and one analytic example showing **threshold-after-downsampling does not commute with intersection-before-downsampling**. The selected operator is explicitly `[(D common)>t] & [(D HM)>t] & [(D OE)>t]`, and does not silently claim to represent `D(common & HM & OE)>t`. Its source/mask receipts allow later physical preprocessing comparisons.

Native 2048 FITS, real 64x90 response and beam/FFP/null on user's computer: **NOT_RUN in this sandbox**. Local connected desktop-command execution: unavailable under service usage quota. `research/OE_REFERENCE_V2_HANDOFF_KO.md` contains exact assumptions, DAG preservation, uncertainty and next run.
