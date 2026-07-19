# K1 E2E — disk-swap procedure + minimal reproducibility retention (PR3 / PR4)

- **Status:** operational retention policy for the PR-150 conditional result and future PR4 swap.
- **Owner:** `OBSSTAT`. **Claim tier:** `conditional` for the measurement; input-retention metadata is provenance-only.
- **Binding constraint:** the 1.8 TB NVMe currently holds 731 GB of PR3 FFP10 raw inputs and
  cannot safely reserve an unmeasured PR4/NPIPE payload at the same time, so acquisition is a
  SERIAL swap and PR3 raw must be reduced to a faithful cache before any later deletion.

## Why this exists

The K1 morphology estimator downgrades every raw Nside=2048 IQU map to the analysis
resolution (NSIDE ≤ 64) as its FIRST step (`k1_global_maxscan._load_sim_map` → `ud_grade`),
so the raw 731 GB carries nothing the registered low-ℓ analysis uses beyond that downgraded content.
Deleting PR3 to make room for PR4 is therefore eligible for consideration **only after** the ensemble is reduced to a
compact registered-estimator cache and that cache is proven to reproduce the direct raw-to-NSIDE64
input arrays and full precision result bit-for-bit. Even then, deletion remains forbidden until a
separate authenticated PR4 replacement-ready receipt exists and the user explicitly starts the swap.

## Retention tiers (what is left after PR3 analysis)

| Tier | What | Size | Where | Purpose |
|---|---|---|---|---|
| **Tier-1 receipt** | exact 999×6 paired precision matrix, observed six-vector, max scores/ranks, config/cache hashes, pairing table, and all 1299 raw SHA256 values | ~MB | `docs/generated/k1_e2e_reduced_manifest_<ensemble>_<method>.json` plus cache-gate receipt | re-derive and audit the registered PR-150 result without raw maps |
| **Tier-2 cache** | direct PRE-MASK NSIDE=64 float64 I-map + ℓ≤8 a_lm per realization, replay NPZ files, observed/map compact arrays | ~1 GB | `/mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced_pr150/` (NVMe, kept) | rerun the actual PR-150 precision estimator without the 731 GB raw ensemble |
| **Independent copy** | byte-identical combined Tier-2 archive | 489 MiB | a different filesystem under `workdir/compact_products/planck_pr3_pr150/` | survive loss or replacement of the data NVMe |

Tier-2 is deliberately narrower and stronger: it stores the exact direct raw→NSIDE64 float64
pre-mask transform used by PR-150.  It makes no unverified claim that a staged NSIDE128 downgrade is
bit-identical.  A future analysis needing NSIDE>64 is outside this retention contract and must use
the still-retained raw maps or build a separately gated higher-resolution cache before deletion.

## The mandatory swap procedure

```bash
# 1. (while PR3/FFP10 is on disk) reduce -> Tier-1 receipt + Tier-2 cache
venv/bin/python scripts/k1_e2e_reduce.py \
    --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \
    --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc \
    --method smica --ensemble ffp10 --reduce-nside 64 --lmax 8 \
    --max-sims 1000 --require-pr150-inventory \
    --cache-dir /mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced_pr150 \
    --backup-dir workdir/compact_products/planck_pr3_pr150

# 2. Rerun PR-150 from the per-realization replay directories, retaining the 999x6 matrix.
venv/bin/python scripts/k1_global_maxscan.py --precision --proc-nside 64 --lmax 30 \
    --cmb-mc-dir /mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced_pr150/k1_ffp10_smica_replay/cmb_mc \
    --noise-mc-dir /mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced_pr150/k1_ffp10_smica_replay/noise_mc \
    --max-sims 1000 --jobs 20

# The ell<=8 alm stored by the reducer is an auxiliary convenience only; the
# authoritative NSIDE64 maps replay the registered ell_max=30 calculation.

# 3. FAITHFUL-CACHE GATE: all 1299 raw hashes/maps + compact replay + backup + result.
venv/bin/python scripts/k1_e2e_cache_gate.py \
    --manifest docs/generated/k1_e2e_reduced_manifest_ffp10_smica.json \
    --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \
    --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc --all --tol 0 \
    --result-artifact docs/generated/k1_global_maxscan_e2e_full.json
#    -> cache_reproducibility_green may be true; safe_to_delete_raw remains false now.

# 4. KEEP all PR3 raw FITS until PR4 access, exact subset, size, and checksums are verified.
#    No deletion command belongs in this phase.

# 5. measure PR4/NPIPE volume and create an authenticated PR4_REPLACEMENT_READY receipt.
venv/bin/python scripts/k1_npipe_size_probe.py --du-listing npipe_listing.txt \
    --pr3-dir /mnt/sn850x2t/htt_base_e2e/workdir/raw/planck_ffp10
# 6. only a later explicit migration command may consume both green receipts and delete PR3 raw.
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

- The reduced cache is an input-retention artifact; the PR-150 measurement remains conditional.
- The gate is fail-closed: all 999+300 maps, observed map, common mask, independent copy, 999×6
  result matrix, and exact rank products must agree. Sampling can never authorize deletion.
- The reduced manifest's embedded gate flag is its immutable pre-gate creation state; the
  content-addressed `k1_e2e_cache_gate_ffp10_smica.json` receipt is the authoritative verdict.
- A green cache gate alone does not authorize deletion. PR4 must first have an authenticated
  `PR4_REPLACEMENT_READY` receipt; the current external-access blocker keeps raw PR3 retained.
- Both ensembles' Tier-1 receipts are committed; the Tier-2 caches stay on the NVMe as the minimal
  reproducibility retention artifacts (they are the "leave minimal reproducibility data" mandate).
