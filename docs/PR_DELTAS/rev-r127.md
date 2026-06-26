# REV-R127 - Real-data blocker discharges: K5 (CF4 coverage) + K6 (CF4 curl no-go) + K1 (global max-scan, partial)

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only_measured
transfer_source: mixed_none_and_cf4_wf_proxy
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

New external-audit drop (`CODE_AND_RESULTS_AUDIT_REPORT.md`, `BLOCKER_RESOLUTION_PLAN.md`,
`publishable_analysis_pack_2026-06-26/`) + user enablement (>300 GB nvme, long runs OK).
Discharge the K1/K5/K6 data blockers on real inputs.

## Key finding

The controlling inputs were already in-repo (no download needed for K5/K6):
- `workdir/raw/cf4/CF4pp_mean_std_grids.npz` - CF4++ 3D WF velocity field (K6).
- `workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz` - real CF4 catalogue, 38053
  groups, Tully+2023 (K5).
- `workdir/raw/planck_data/COM_CMB_IQU-{smica,commander}_..._full.fits` +
  pre-downgraded NSIDE=16 maps (K1).
A matched component-separated FFP10/NPIPE E2E *simulation* ensemble is NOT plain-URL
downloadable (PLA interactive query portal / NERSC auth; confirmed by probing
PLA + IRSA + NERSC), so K1 is a partial (look-elsewhere) discharge under a LambdaCDM null.

## Changes

- `scripts/k6_cf4_curl_posterior.py` (new) -> `docs/generated/k6_cf4_curl_posterior.json`:
  affine velocity-gradient decomposition (`htt/obsstat/affine_flow.py`) of the real
  CF4++ WF field over nested radii, with a per-cell N(v_mean,v_std) CR ensemble.
  Result: **structural no-go** - vorticity <= 0.6 % of shear at every radius while
  the estimator recovers an injected solid-body rotation to machine precision
  (curl-suppressed reconstruction; not a physical-vorticity detection).
- `scripts/k5_cf4_release_coverage.py` (new) -> `docs/generated/k5_cf4_release_coverage.json`:
  weighted-GLS bulk flow (`htt/obsstat/bulkflow_mle.py`) on the real catalogue with
  release-matched forward mocks (real positions + real distance-error model + injected
  LambdaCDM cosmic-variance flow). Result: **|B| = 341 +/- 102 km/s**, error budget
  cosmic-variance-dominated (102 vs 5 km/s measurement); CV-inclusive coverage 0.67
  (nominal) vs measurement-only 0.19 (under-covers); unbiased; depth-shell ablation.
- `scripts/k1_global_maxscan.py` (new) -> `docs/generated/k1_global_maxscan.json`:
  stacks the six registered low-ell statistics on the real SMICA/Commander maps into
  the frozen max-scan (`htt/obsstat/lowell_global_calibration.py`). Result: **global
  look-elsewhere p = 0.097 (SMICA), 0.121 (Commander)** under an isotropic LambdaCDM
  null (parity asymmetry the strongest single local, p=0.02). Partial: E2E-systematics
  null remains BLOCKED_MISSING_PR4_E2E_ACCESS.
- `tests/obsstat/test_k{1,5,6}_*.py` (new): claim-firewall + result-property regressions.
- `scripts/build_egs_results_table.py`: K1->measured_partial, K5->measured, K6->measured_no_go;
  zero `blocked` rows remain; `discharges_rev_r127` recorded.
- `docs/research_program/BLOCKERS.md`: discharge status table + per-blocker results.
- `scripts/build_pr04_research_audit_package.py`: +3 discharge JSONs, +3 scripts; deltas r108..r127.

## Claim discipline

K5 and K6 are model-independent OBSSTAT descriptors; K6 is an honest structural no-go
(curl-suppressed WF reconstruction), not a vorticity detection; K1 is an explicit
partial discharge (look-elsewhere done, E2E null open + documented). No Bianchi family,
geometry, anisotropy-evidence, or native-solver claim. Raw maps/fields stay outside git.

## Validation

| Command | Status |
| --- | --- |
| `k6_cf4_curl_posterior.py` | structural no-go; curl-injection rel-err ~1e-16 |
| `k5_cf4_release_coverage.py` | CV coverage 0.67 / meas-only 0.19; bias 0.7 km/s |
| `k1_global_maxscan.py` | global p 0.097/0.121 (real PR3 maps, 2000 nulls) |
| `pytest tests/obsstat/test_k{1,5,6}_* test_affine_flow test_bulkflow_mle` | passed |
| `build_egs_results_table.py` | 17 rows, 0 blocked (3 measured/partial/no-go) |
