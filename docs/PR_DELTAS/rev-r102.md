# REV-R102 - Null-Calibrated Low-ell Morphology of the Real Planck Map (new result K1)

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: full_sky_cleaned_map
null_mock_status: null_calibrated_isotropic_lcdm_ensemble
generating_command: `Codex REV-R102 low-ell morphology of the real Planck map`
git_commit_or_worktree_state: pending_rev_r102_commit

## Evidence Read

- `AGENTS.md`
- `.claude/skills/htt-revision-planner/SKILL.md`, `htt-observable-statistics`, `htt-statistical-hardening`, `htt-plot-provenance`
- `htt/obsstat/scalar_lowell.py`, `morphology.py`, `null_ensembles.py` (existing, tested estimators)
- `workdir/obs_bundle/cmb/maps/smica_nside16.npz`, `data/camb_ref_planck2018.npz`
- Code-cartographer + data-inventory subagent maps (this session).

## New-Result Rationale

Supplemental research result K1 from the new-results plan: the first application
of the existing OBSSTAT low-ell estimator stack to the REAL Planck PR3 SMICA
map, with a 10000-sim isotropic LambdaCDM null calibration. The manuscript only
reported the binned-TT-spectrum low-ell residual; the real-map a_lm morphology
(S_{1/2}, parity, planarity, preferred-axis alignment) calibrated against nulls
is new. Diagnostic-only; no Bianchi family-ID, geometry detection, native solver
output, or HTT/MIO evidence. Canonical PR-* / prior REV-R0xx DAGs unchanged.

## Result Summary

Real Planck PR3 SMICA NSIDE=16, full-sky, ell=2..8, n=10000 nulls (seed=12345):
parity even/odd ratio p=0.018 and parity asymmetry p=0.018 (odd-power excess),
S_{1/2} p=0.059, planarity mean p=0.043; the power-inertia ell2-ell3 axis
alignment (p=0.65) and axis-to-CMB-apex alignment (p=0.71) show no anomaly.
Look-elsewhere across the six statistics is tracked, not globally corrected. The
framework recovers the known low-ell anomalies as model-independent features and
produces no Bianchi or source-identification claim.

## Role Split

- Physics/statistics auditor steelman: the statistics must be calibrated against
  a real null ensemble and look-elsewhere tracked; the ell2-ell3 power-inertia
  axis is not the multipole-vector axis-of-evil and must be labelled so.
- Code cartographer steelman: reuse the built `summarize_lowell_scalars` /
  `summarize_morphology_axes`; keep OBSSTAT healpy-free by passing pixel vectors
  and packed a_lm into pure-numpy helpers.
- Claim-gate reviewer steelman: feature payloads and figure manifests must keep
  family-ID and native-solver use blocked; p-values are model-independent
  features, not Bianchi evidence.

## Changes

- `htt/obsstat/lowell_map_features.py`: new pure-numpy `densify_alm` (reality
  condition), `power_inertia_tensor`, `empirical_pvalue`.
- `scripts/make_lowell_morphology_real_map.py`: driver (map2alm -> dense a_lm ->
  estimators + synfast null calibration) -> report + 2 gated figures.
- `docs/generated/lowell_morphology_real_map_report.{json,md}`: the result.
- `figures/observed_current/fig_observed_lowell_morphology_axis.png`,
  `fig_observed_lowell_null_significance.png` (+ manifests).
- `docs/generated/new_results_real_data_summary.md`: combined K1+K4 publishable
  summary with the critically-excluded candidates documented.
- Tests: `tests/obsstat/test_lowell_map_features.py`,
  `tests/obsstat/test_lowell_morphology_real_map.py`.

## Artifact Metadata

- owner: OBSSTAT
- implementation_scope: obsstat
- claim_tier: diagnostic_only
- config_hash:
  - `htt/obsstat/lowell_map_features.py:sha256:0d1d80591b1c50b5ac843faaaefc1dbd3ad846e5cb41a518e10fa8ddb2dba08d`
  - `scripts/make_lowell_morphology_real_map.py:sha256:283867d15c70a3e365740baf0ed39f92c589816e6189575b4e3f2d5dc218759a`
- input_hashes:
  - `docs/generated/lowell_morphology_real_map_report.json:sha256:d1bf061318211814cf8f588bc4640d7c7bd754d2cfb4714aed32d7c804f45470`
  - `tests/obsstat/test_lowell_map_features.py:sha256:4a68a0d024d52c70847353afdaf6d4828ff588c1badee77641fe747ca0dbcc0d`
  - `tests/obsstat/test_lowell_morphology_real_map.py:sha256:a4b9c9e15517ee7149e3080f3315c3bce16a520005693f07e8e8e8dfd72dae1b`
  - `figures/observed_current/fig_observed_lowell_morphology_axis.png:sha256:7b8bd2d2d1395e396ea0217c0cc4f9c16ec34ac0f9b41969b677fff5cbcabda1`
  - `figures/observed_current/fig_observed_lowell_null_significance.png:sha256:65ee8b5084e6c4db089f02d39e4d952b12234366b6f6fbfeaea2cc2f781a821d`
- caveats:
  - model-independent low-ell feature p-values; not evidence for any Bianchi model;
  - full-sky cleaned map, no mask deconvolution or full pixel-pixel covariance;
  - look-elsewhere tracked, not globally corrected (six statistics);
  - `--check` regenerates the n=10000 ensemble and is therefore minutes-long;
    determinism is covered by the seeded n=120 contract test;
  - no native low-ell solver output or Bianchi family identification.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/obsstat/test_lowell_map_features.py -q` initially failed with `ModuleNotFoundError` before `lowell_map_features.py` existed.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_lowell_morphology_real_map.py --null-count 10000` | PASS | Wrote report + 2 figures + manifests; recovers parity/S_1/2 anomalies. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_lowell_map_features.py tests/obsstat/test_lowell_morphology_real_map.py tests/contracts/test_current_manuscript_figures.py::test_current_and_observed_manifests_carry_claim_lane_policy` | PASS | `8 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...lowell... report.md` | PASS | `No forbidden claim language detected.` |
