# K1 E2E — disk-swap procedure + minimal reproducibility retention (PR3 / PR4)

- **Status:** operational policy for the K1 E2E lane (roadmap PR-149/PR-150).
- **Owner:** `OBSSTAT`. **Claim tier:** `diagnostic_only`.
- **Binding constraint:** the 1.8 TB NVMe cannot hold PR3 (FFP10, ~1 TB) and PR4 (NPIPE)
  simultaneously, so the data acquisition is a SERIAL swap, and PR3 raw must be reduced to a
  faithful cache BEFORE deletion or the 1 TB download is lost.

## Why this exists

The K1 morphology estimator downgrades every raw Nside=2048 IQU map to the analysis
resolution (NSIDE ≤ 64) as its FIRST step (`k1_global_maxscan._load_sim_map` → `ud_grade`),
so the raw ~1 TB carries nothing the low-ℓ analysis uses beyond that downgraded content.
Deleting PR3 to make room for PR4 is therefore safe **only after** the ensemble is reduced to a
compact, estimator- and mask-agnostic cache and that cache is proven to reproduce the from-raw
estimator bit-for-bit.

## Retention tiers (what is left after PR3 analysis)

| Tier | What | Size | Where | Purpose |
|---|---|---|---|---|
| **Tier-1 receipt** | per-realization 6-statistic matrix + config/cache hashes + ALL raw input sha256 | KB | `docs/generated/k1_e2e_reduced_manifest_<ensemble>_<method>.json` (committed) | re-derive the K1 E2E global-p for the CURRENT statistic set forever, no maps |
| **Tier-2 cache** | PRE-MASK downgraded I-map (NSIDE=128, float64) + a_lm (ℓ≤64) per realization | ~1–2 GB | `/mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced/k1_<ensemble>_reduced_<method>.npz` (NVMe, kept) | recompute NEW statistics / re-mask under a revised convention (PR-135/149/150) with NO re-download |

Tier-2 is estimator- and mask-agnostic because it is stored PRE-mask at NSIDE=128 float64, and
`ud_grade(2048→128)→proc` is bit-identical to `ud_grade(2048→proc)` for any proc ∈ {16,32,64,128}
(associative power-of-two averaging). The one thing that would force a re-download is a convention
(PR-149) demanding proc_nside > 128 — so **freeze the mask/resolution convention (PR-149) before
deleting PR3 raw.**

## The mandatory swap procedure

```bash
# 1. (while PR3/FFP10 is on disk) reduce -> Tier-1 receipt + Tier-2 cache
venv/bin/python scripts/k1_e2e_reduce.py \
    --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \
    --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc \
    --method smica --ensemble ffp10

# 2. FAITHFUL-CACHE GATE (fail-closed): cache must reproduce the from-raw statistics
#    bit-exactly AND all sampled raw hashes must match the manifest.
venv/bin/python scripts/k1_e2e_cache_gate.py \
    --manifest docs/generated/k1_e2e_reduced_manifest_ffp10_smica.json \
    --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \
    --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc --all
#    -> requires safe_to_delete_raw: true (exit 0). If exit 1: DO NOT DELETE.

# 3. only now delete PR3 raw FITS (keep the Tier-2 cache + Tier-1 receipt)
#    rm -rf workdir/raw/planck_ffp10/smica/{cmb_mc,noise_mc}

# 4. measure PR4/NPIPE volume, then download the K1-usable subset into the freed space
venv/bin/python scripts/k1_npipe_size_probe.py --du-listing npipe_listing.txt \
    --pr3-dir /mnt/sn850x2t/htt_base_e2e/workdir/raw/planck_ffp10
# 5. reduce NPIPE the same way (--ensemble npipe), gate, delete NPIPE raw.
```

## PR4 / NPIPE is REQUIRED, not optional

FFP10 (PR3) alone unblocks the first authoritative K1 E2E result. But the Planck team reports that
**NPIPE (PR4) reduces residual systematics** relative to the 2018/FFP10 processing (better
large-scale transfer, lower low-ℓ systematic residuals). The K1 low-ℓ morphology result is
exactly in the regime where that improvement matters, so PR4 is a **required additional analysis**,
not a second-order cross-check: the two ensembles (FFP10 + NPIPE-improved-systematics) must both
be run and reported side by side, never averaged. A divergence between the FFP10-null and the
NPIPE-null global-p is itself the systematics-sensitivity result.

**NPIPE volume caveat:** the FULL NPIPE frequency E2E ensemble (600 full-frequency + detector-set
MC) is multi-TB and will NOT fit the NVMe even after deleting PR3. Download ONLY the K1-usable
product (the NPIPE component-separated CMB sims, or a single cleaned channel to be downgraded) —
`k1_npipe_size_probe.py` decides FITS_AFTER_PR3_DELETE / NEEDS_SUBSET_STREAM / BLOCKED_TOO_LARGE
from the measured size.

## Discipline

- The reduced cache and its receipt are `diagnostic_only`; no family/geometry/native-solver claim.
- The gate is fail-closed: a single realization failing statistic-reproduction OR hash-match blocks
  deletion. Never delete raw on a red gate.
- Freeze the PR-149 mask/convention before deleting raw (the only re-download trigger).
- Both ensembles' Tier-1 receipts are committed; the Tier-2 caches stay on the NVMe as the minimal
  reproducibility retention artifacts (they are the "leave minimal reproducibility data" mandate).
