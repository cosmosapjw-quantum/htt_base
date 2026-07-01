# REV-R139 - K1 id-based CMB/noise pairing (missing 00970) + PLA-available claim correction

owner: OBSSTAT
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: ffp10_component_separation
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Planck FFP10 SMICA CMB realization 00970 is missing/corrupt (999 usable of a nominal
1000). Fix the pairing to parse the MC id (so the gap does not misalign the sim loop),
and correct the claims to the PLA-available set.

## Changes

- **`scripts/k1_global_maxscan.py`** --- id-based pairing:
  - `_parse_mc_id(path)` parses the 5-digit MC id (tolerant to `..._mc_00970_raw.fits[.gz]`
    and the `.npz` fixtures); unparseable names raise (kill switch).
  - `_pair_cmb_noise_by_id` pairs each available CMB with `noise[cmb_id mod n_noise]` looked
    up in a `{noise_id: path}` dict --- robust to arbitrary gaps (positional
    `noise[i mod n]` would shift every CMB after the missing 00970).
  - The precision worker `_w_full` uses an **id-keyed** noise cache and an explicit
    `noise_id` task field; `_e2e_full_null` / `_e2e_full_null_precision` both rewritten.
  - Full-E2E artifact records `n_cmb_used`/`n_noise_used`, `nominal_cmb`/`nominal_noise`,
    `known_missing_cmb_ids` ([970]), disk-detected `observed_cmb_id_gaps`, `pla_confirmation`
    ("pending"); provenance rows carry `cmb_id`/`noise_id`; pairing string is now
    `cmb_mc[id] + noise_mc[id mod n_noise] (id-parsed, gap-robust)`.
- **Claim correction** (runner strings + `K1_E2E_DOWNLOAD_GUIDE.md` + root report
  `htt_progress_and_planck_plan.tex`):
  - "full 1000 FFP10 SMICA E2E ensemble" -> "PLA-available FFP10 SMICA E2E ensemble";
  - "all 1000 CMB MC" -> "999 usable CMB MC + 300 noise MC";
  - explicit "known missing/corrupt CMB realization: 00970 (ESA/PLA confirmation pending)".
  - Report recompiled (6 pp, 0 undefined refs).
- +3 tests: `_parse_mc_id` real/fixture names, id-based pairing survives a missing CMB
  realization, full-E2E artifact records the missing id + PLA status.

## Claim discipline

The E2E artifact stays diagnostic-only; the ensemble is honestly the PLA-available subset,
not "all 1000". Flipping K1 to `measured` remains a manual post-run step. The canonical GRF
artifact and the v1 path are untouched.

## Validation

| Command | Status |
| --- | --- |
| `pytest tests/obsstat/test_k1_noise_mode.py tests/obsstat/test_lowell_precision.py` | 23 passed |
| `pytest tests/contracts/` | 355 passed, 0 failed |
| `latexmk` report | exit 0; 6 pages; 0 undefined refs |
| audit packages rebuilt + `--check` | current |
