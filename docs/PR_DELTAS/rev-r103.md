# REV-R103 - CF4++ Bulk-Flow Apex Versus Depth (new result K4)

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: cf4_reconstruction_grid
null_mock_status: bootstrap_over_correlated_reconstruction_cells
generating_command: `Codex REV-R103 CF4 bulk-flow apex versus depth`
git_commit_or_worktree_state: pending_rev_r103_commit

## Evidence Read

- `AGENTS.md`
- `.claude/skills/htt-revision-planner/SKILL.md`, `htt-observable-statistics`, `htt-statistical-hardening`
- `workdir/obs_bundle/pecvel/cf4/query_batch.npz` (163,760-cell CF4++ reconstruction grid)
- `htt/workspace/data/obs_defaults.json` (CMB dipole apex)
- Code cartographer + data-inventory subagent maps (this session).

## New-Result Rationale

Supplemental research result K4 from the new-results plan. The manuscript
already reports the CF4 scalar radial-velocity-vs-radius profile; the bulk-flow
apex DIRECTION versus depth (and its drift) is new. This is a model-independent
kinematic descriptor, not a Bianchi/tilt/frame-violation claim, and the
canonical PR-* / REV-R0xx DAGs remain unchanged.

## Result Summary

Volume-averaged CF4++ bulk flow in 7 radial shells (90-450 Mpc/h): amplitude
rises to ~590 km/s at 250-300 Mpc/h then falls to ~130-190 km/s in the deep
shells; the apex stays within ~5-46 deg of the full-sample apex out to
300 Mpc/h and then reverses (~120-149 deg drift) at the reconstruction edge.
Reported strictly as a descriptor with a bootstrap apex dispersion (lower bound
on uncertainty; correlated reconstruction cells); the deep-shell reversal is
flagged as a likely reconstruction-edge effect.

## Role Split

- Physics/statistics auditor steelman: the apex drift is a real kinematic
  descriptor; the deep-shell reversal must be flagged as a probable edge effect,
  and the bootstrap (correlated cells) is a lower bound, not a covariance.
- Code cartographer steelman: reuse pure-numpy shell aggregation + the existing
  obs_defaults CMB apex; astropy for the supergalactic->Galactic conversion.
- Claim-gate reviewer steelman: no frame-violation, tilt, or family claim; the
  figure manifest blocks family-ID and native-solver use.

## Changes

- `htt/obsstat/bulkflow_depth.py`: new pure-numpy `radial_shell_bulkflow`,
  `bootstrap_apex_dispersion`, `angle_between_deg`.
- `scripts/make_cf4_bulkflow_apex_depth.py`: driver -> report + figure +
  gated manifest (supergalactic->Galactic via astropy).
- `docs/generated/cf4_bulkflow_apex_depth_report.{json,md}`: the result.
- `figures/observed_current/fig_observed_cf4_bulkflow_apex_depth.png` (+ manifest).
- Tests: `tests/obsstat/test_bulkflow_depth.py`,
  `tests/obsstat/test_cf4_bulkflow_apex_depth.py`.

## Artifact Metadata

- owner: OBSSTAT
- implementation_scope: obsstat
- claim_tier: diagnostic_only
- config_hash:
  - `htt/obsstat/bulkflow_depth.py:sha256:eda7e7122383cb8b2e2a3d0018f6312e449f7bfa34586e007b4e644a1bb43463`
  - `scripts/make_cf4_bulkflow_apex_depth.py:sha256:f00f1ee55db9883ced3fc78ad97ccaeef37e1215101d7efa503ca9004093b22f`
- input_hashes:
  - `docs/generated/cf4_bulkflow_apex_depth_report.json:sha256:8f1b75f342052dc72bc3266c4bae17b0ce82bae0bf8ee6148fdce12745346892`
  - `tests/obsstat/test_bulkflow_depth.py:sha256:fe45a9050f080ea0cb5c3ec212e8a7d02aee9c74d7eda4220fc2e96d3510b5d2`
  - `tests/obsstat/test_cf4_bulkflow_apex_depth.py:sha256:05972046aeadbf514098e19c7fe8cf6651f3a02548abe4ea7e3ffd5ea2cbf150`
  - `figures/observed_current/fig_observed_cf4_bulkflow_apex_depth.png:sha256:89fb323feb9dddd1bd7df9ffc80ec44882780b54ff968f93bd9c62a285a74423`
- caveats:
  - model-independent kinematic descriptor; not Bianchi/tilt/frame evidence;
  - bootstrap over correlated reconstruction cells is a lower bound;
  - deep-shell apex reversal is a likely reconstruction-edge effect;
  - no native low-ell solver output or Bianchi family identification.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/obsstat/test_bulkflow_depth.py -q` initially failed with `ModuleNotFoundError` before `bulkflow_depth.py` existed.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_cf4_bulkflow_apex_depth.py` | PASS | Wrote report + figure + manifest. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_cf4_bulkflow_apex_depth.py --check` | PASS | Artifacts up to date. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_bulkflow_depth.py tests/obsstat/test_cf4_bulkflow_apex_depth.py tests/contracts/test_current_manuscript_figures.py::test_current_and_observed_manifests_carry_claim_lane_policy` | PASS | `8 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...bulkflow... report.md` | PASS | `No forbidden claim language detected.` |
