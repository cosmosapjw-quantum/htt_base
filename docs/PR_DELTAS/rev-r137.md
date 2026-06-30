# REV-R137 - K1 v2 precision statistic set + parallel --jobs

owner: OBSSTAT
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: ffp10_component_separation
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

User (Ryzen 5900X, 64 GB) wants the K1 full-data analysis parallelised and the NSIDE
downgrade relaxed for precision; asked how far is possible + wall-time.

## Key finding (measured, before building)

Raising NSIDE alone does NOT increase ℓ=2–8 precision: NSIDE=16 is Nyquist-sufficient;
the only lever there is the pixel-window suppression (`w₈`: NSIDE16 0.987 → NSIDE64
0.999, i.e. ≤1.3 %), with the ceiling at **NSIDE=64** (128/256 add nothing at ℓ≤8).
Real precision levers: proc-NSIDE, ℓ_max, galactic mask. User chose all three.

## Changes

- **`htt/obsstat/lowell_precision.py`** (new): `PrecisionConfig`, `downgrade_mask`,
  `diffuse_inpaint`, `precision_map_statistics`. Re-registered **v2** statistic set
  (own `statistic_set`/`config_hash`), same six v1 keys at configurable proc-NSIDE
  (default 64) + ℓ_max (default 30 for the ell-summed S₁/₂/parity/planarity; Q-O
  alignment intrinsically ℓ=2,3, unchanged), common mask + diffuse inpainting applied
  identically on observed + sims (look-elsewhere p-value stays valid). +8 unit tests.
- **`scripts/k1_global_maxscan.py`**: `--precision --proc-nside --lmax --no-mask --jobs`.
  `build_e2e_{full,noise}_report` gain `precision`/`jobs`. Under precision the observed
  vector is taken from the **full-res** observed map processed identically; artifacts tag
  the v2 re-registration (`null_model: *_v2_precision`). Parallelism: threads pinned to
  1/worker (set before healpy import) + `ProcessPoolExecutor(spawn)` (avoids the
  fork-after-OpenMP deadlock); noise pre-downgraded once + cached, CMB fanned out. v1
  ℓ≤8 path + canonical GRF artifact untouched. Dropped deprecated `read_map(verbose=)`.
  +5 K1 tests incl. `parallel == serial`.
- **`docs/research_program/K1_E2E_DOWNLOAD_GUIDE.md`**: v2-precision subsection (flags,
  NSIDE-64 ℓ≤8 ceiling + pixel-window table, mask/inpaint method, measured wall-time).
- **`scripts/build_research_evaluation_package.py`**: bundle the precision module + test.

## Wall-time (measured per-map ≈ 3 s at v2; full 1000 CMB + 300 noise, noise cached)

| config | serial | `--jobs 12` |
| --- | --- | --- |
| v1 (NSIDE 16, ℓ≤8) | ~40 min | ~5–7 min |
| v2 (NSIDE 64, ℓ=30, mask) | ~40 min | ~5–7 min |
| v2 `--max-sims 300` | ~10 min | ~2 min |

I/O-bound (~3.5 min nvme read floor) → v1↔v2 and NSIDE 64↔128 barely move wall-time.
RAM ~1 GB/worker → 12 jobs ≈ 12 GB, 24 ≈ 24 GB (no RAM purchase on 64 GB).

## Claim discipline

v2 is diagnostic-only and explicitly re-registered (not a silent change to the frozen v1
set); mask handled identically on obs+sims (no per-statistic deconvolution claimed);
flipping K1 to `measured` remains a manual post-run step.

## Validation

| Command | Status |
| --- | --- |
| `pytest tests/obsstat/test_lowell_precision.py` | 8 passed |
| `pytest tests/obsstat/test_k1_noise_mode.py` (incl parallel==serial, masked) | 12 passed |
| `pytest tests/contracts/` | 355 passed, 0 failed |
| audit packages rebuilt + `--check` | current |
