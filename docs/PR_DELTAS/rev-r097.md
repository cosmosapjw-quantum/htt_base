# REV-R097 - Add Joint Survey Hierarchy Gate

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R097 add joint survey hierarchy gate`
git_commit_or_worktree_state: pending_rev_r097_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 10)
- `htt/obsstat/catalogs/cf4.py`, `spectroscopic_dipole.py`
- Web/literature: arXiv 2306.11269 (CF4 estimator/systematic uncertainty) and
  arXiv 2511.00822 (CatWISE mask/clustering/selection) support requiring
  cross-probe covariance and selection metadata before combining amplitudes.

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62` (checkpoint reconfirmed
`62/62 = 100.0%`). This PR implements supplemental REV task 10: a schema-only
joint multi-survey hierarchy contract that blocks the conditional-independence
product until the cross-probe prerequisites are bound.

## Role Split

- Physics/statistics auditor steelman: CatWISE/radio/CF4 amplitudes cannot be
  multiplied or compared as a shared source model without cross-probe
  covariance, mask/selection metadata, calibration nuisance, shared LSS
  covariance, and held-out predictive status.
- Code cartographer steelman: reuse a small fail-closed contract; reference it
  from the catalogs by module name to avoid an obsstat -> infer import.
- Harness engineer steelman: pin the blocked-by-default contract with contract
  tests; keep the existing CF4 and spectroscopic tests green.

## Changes

- `htt/htt/htt/infer/joint_survey_hierarchy.py`: new schema-only contract with
  `build_joint_hierarchy_contract(...)`. Blocks
  `conditional_independence_product_allowed` and sets `claim_tier=blocked` until
  every required field is bound, recording per-field blocked reasons.
- `htt/obsstat/catalogs/cf4.py`,
  `htt/obsstat/catalogs/spectroscopic_dipole.py`: added
  `joint_survey_combination_status()` declaring each probe non-combinable with
  others until the contract is satisfied (referenced by module name only).
- `docs/generated/joint_survey_hierarchy_design.md`: new design note.
- Test: `tests/htt/test_joint_survey_hierarchy.py`.

## Artifact Metadata

- owner: HTT
- implementation_scope: htt
- claim_tier: blocked
- config_hash:
  - `htt/htt/htt/infer/joint_survey_hierarchy.py:sha256:8021231b8c1649bb569a4e335414fed5332e36eab3fa0ecb7eab7b88ac0b2874`
- input_hashes:
  - `htt/obsstat/catalogs/cf4.py:sha256:b6e834f4dd99377a69440d90d2fda634acd19709b72e47336a1e169fc5d35b61`
  - `htt/obsstat/catalogs/spectroscopic_dipole.py:sha256:c74ef8b04fe4ac5fced47203c91603784b6d5abe7e818bed6b3f3e6922f74cb8`
  - `docs/generated/joint_survey_hierarchy_design.md:sha256:aaf70629e7b097dffc8b11bc424396c525e468f90fc1b0c4186f25c620a13a36`
  - `tests/htt/test_joint_survey_hierarchy.py:sha256:81df97f7f06f0a35c78197ab5c699db714f2b0bab8a2c62f333a9a29ef870e86`
- caveats:
  - schema-only contract; no observed-data inference is performed;
  - the conditional-independence product is blocked until every field is bound;
  - no native low-ell solver output is introduced.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/htt/test_joint_survey_hierarchy.py -q` initially failed with `ModuleNotFoundError`.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_joint_survey_hierarchy.py tests/htt/test_cf4_likelihood.py tests/obsstat/test_spectroscopic_dipole.py` | PASS | `12 passed`. |
| `venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` | PASS | Canonical DAG `62/62 = 100.0%` unchanged. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...joint... cf4 spectroscopic design.md` | PASS | `No forbidden claim language detected.` |
