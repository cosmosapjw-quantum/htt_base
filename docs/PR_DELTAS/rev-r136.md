# REV-R136 - K1 full Route-A E2E runner (real CMB + real noise)

owner: OBSSTAT
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: ffp10_component_separation
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

User is installing a 2 TB nvme to download the FULL FFP10 set (1000 CMB MC + 300 noise
MC, ~1 TB) instead of the reduced route-4 noise-only set; re-guide the method.

## Why a new runner

rev-r135 built only the noise-only + local-ΛCDM runner (`--noise-mc-dir`), which stays
`measured_partial` (no matched signal / residual foregrounds). The full download enables the
matched FFP10 E2E null (real CMB + real noise) — the exit-gate null that flips K1
`measured_partial → measured` and closes `BLOCKED_MISSING_PR4_E2E_ACCESS`. That runner did
not exist, so this adds it.

## Changes

- **`scripts/k1_global_maxscan.py`**:
  - `--cmb-mc-dir` (requires `--noise-mc-dir`) + `--max-sims` → `build_e2e_full_report` /
    `_e2e_full_null`. Real component-separated CMB MC + real instrument-noise MC, downgrade-on-
    read to NSIDE=16, paired `cmb_mc[i] + noise_mc[i mod n_noise]` (300 noise cycled across
    1000 CMB, Planck-2018 permutation), six registered statistics, frozen max-scan vs the real
    observed 6-vector.
  - Separate artifact `docs/generated/k1_global_maxscan_e2e_full.json`
    (`null_model: ffp10_cmb_plus_noise_e2e`, `blocker_closes`, paired provenance per sim);
    canonical GRF + route-4 artifacts untouched (3 distinct OUT paths).
  - Generalized sim loader/lister (`_load_sim_map`/`_list_sims`) with back-compat aliases
    (`_load_noise_sim_map`/`_list_noise_sims`); route-4 path byte-unchanged.
- **`tests/obsstat/test_k1_noise_mode.py`**: +4 full-E2E tests (runs + exit-gate labelling,
  index-cycled pairing provenance, `--max-sims` cap, empty-dir FileNotFoundError); 8 passed.
- **`docs/research_program/K1_E2E_DOWNLOAD_GUIDE.md`**: full Route-A presented as the
  recommendation for a 2 TB nvme (download list + `smica/{cmb_mc,noise_mc}` layout + the
  implemented `--cmb-mc-dir --noise-mc-dir --max-sims 1000` command + method cross-check +
  exit gate); footprint reducers marked optional; stale "extend the script" step replaced.

## Claim discipline

Full E2E artifact is diagnostic-only (no family/geometry/native-solver, no MIO-as-odds).
Flipping the `egs_results_table` K1 row to `measured` is a deliberate manual step after the
real run, per the guide's exit gate.

## Validation

| Command | Status |
| --- | --- |
| `python -m pytest tests/obsstat/test_k1_noise_mode.py` | 8 passed (noise + full modes) |
| argparse guard `--cmb-mc-dir` without `--noise-mc-dir` | errors as designed |
| `pytest tests/contracts/` | 355 passed, 0 failed |
| all audit packages rebuilt | current |
