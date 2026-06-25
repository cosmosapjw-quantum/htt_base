# REV-R112 - dl_pipeline cf4_full stage + LR-06D CF4 bulk-flow likelihood

owner: OBSSTAT
implementation_scope: obsstat + dl_pipeline
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: cf4_full_group_catalog
null_mock_status: forward_mock_coverage_calibrated
generating_command: `fetch.py --stages cf4_full && python scripts/make_cf4_bulkflow_likelihood.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Extend the download pipeline (no low-ell solver) to acquire the external data,
then continue the runnable tickets. This delivers the CF4 full-release binding
that LR-06D required.

## Pipeline extension (cf4_full)

New stage downloads the Cosmicflows-4 FULL release from VizieR J/ApJ/944/94
(`cdsarc.cds.unistra.fr/ftp/...`, fetched with curl) and parses table4 (38053
group distances + peculiar velocities + sky/supergalactic coordinates) into a
release-hashed npz.

- `dl_pipeline/scripts/extract_cf4_full.py`: download table2/3/4 + ReadMe, gunzip,
  parse table4 fixed-width -> `workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz`
  + a release manifest (table4 sha256 `b6edfec6...`, 38053 groups).
- `dl_pipeline/config/sources.json`: new `cf4_full` block + `stage_order` entry.
- `dl_pipeline/scripts/fetch.py`: `stage_cf4_full` registered in STAGES;
  `fetch.py --stages cf4_full` runs idempotently and fail-closes to
  `BLOCKED_MISSING_FULL_RELEASE_BINDING` if the release is unreachable.

The venv-mutating `env` stage is avoided; data stages were run with `--stages`.
(Note: an earlier `--all` run upgraded numpy 2.4.2->2.5.0 / scipy->1.18.0 in the
shared venv; all 23 PR04 gates, proofs, and fast/smoke/ci regression still pass
under the bumped versions.)

## LR-06D - CF4 bulk-flow likelihood (this unblocks the ticket)

`htt/obsstat/bulkflow_mle.py` computes the minimum-variance (inverse-Fisher)
bulk flow B = A^-1 b, A = sum n n^T/sigma^2, with per-group velocity errors from
the distance-modulus uncertainty plus a fitted intrinsic dispersion sigma_star
(reduced chi^2 ~ 1), and a forward-mock coverage calibration.

| depth [Mpc] | N groups | sigma_star | |B| [km/s] | apex (l,b) | mock 1-sigma coverage |
| --- | ---: | ---: | --- | --- | ---: |
| 60  | (subset) | ~ | 320 +/- 7 | (296, 20) | 0.68 |
| 100 | | | 351 +/- 5 | (293, 22) | 0.72 |
| 150 | | | 347 +/- 5 | (293, 21) | 0.65 |
| 200 | | | 346 +/- 5 | (293, 21) | 0.67 |
| 300 | | | 345 +/- 5 | (293, 21) | 0.67 |

The bulk flow is stable at ~345 km/s toward Galactic (l,b) ~ (293, 21), and the
forward-mock coverage sits at ~0.68 (the error model is calibrated). The
amplitude/direction are consistent with the published CF4 bulk-flow literature.

## Claim boundary

Diagnostic-only kinematic descriptor. No global-tilt or Bianchi-geometry claim
from CF4 distance data alone (per the ticket). sigma_star is a fitted nuisance;
covariance is the inverse Fisher matrix; selection/Malmquist biases are not
fully forward-modelled. Status: LR-06D advanced from
`BLOCKED_MISSING_FULL_RELEASE_BINDING` to a calibrated bulk-flow descriptor;
a full method/group/selection-hierarchy forward model + Vh/Vls/V3k frame
ablation remain follow-ups.

## Validation

| Command | Status |
| --- | --- |
| `fetch.py --stages cf4_full` | parsed 38053 groups; release-hashed npz + manifest |
| `pytest tests/obsstat/test_bulkflow_mle.py` | 4 passed (injected-flow recovery, error scaling, ~68% coverage) |
| `python scripts/make_cf4_bulkflow_likelihood.py` | report + figure; coverage 0.65-0.72 |
| sources.json / fetch.py | valid; `--list` shows cf4_full |
