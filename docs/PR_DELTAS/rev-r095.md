# REV-R095 - Bind Contamination Null Blocker

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: externally_audited_amplitude_matched_contamination
generating_command: `Codex REV-R095 bind contamination null blocker`
git_commit_or_worktree_state: pending_rev_r095_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 8)
- `htt/htt/htt/infer/finite_mock.py` (existing FPR/interval surface)
- `scripts/result_packs/generate_pack_B_local_global.py`
- `tests/result_packs/test_pack_B.py`
- Web/literature: arXiv 2511.00822 (CatWISE mask/clustering/selection reassessment) supports treating amplitude-matched contamination as a blocking systematic.

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 8: bind the externally audited amplitude-matched
contamination null (95 of 100 lnB>5 triggers on contamination-only mocks) as a
current source-identification blocker and make Result Pack B consume it.

## Role Split

- Physics/statistics auditor steelman: a trigger that fires on 95 of 100
  contamination-only mocks has no source-identification power; the Wilson 95%
  lower bound (~0.888) is far above any tolerable contamination ceiling.
- Harness engineer steelman: record the audited count with an exact Wilson score
  interval and pin the blocked classification with a contract test; do not run
  new long mocks.
- Claim-gate reviewer steelman: while blocked, no positive headline Bayes factor
  may be drawn; Result Pack B must surface the blocked source-identification
  status.

## Changes

- `htt/htt/htt/infer/amplitude_matched_contamination.py`: new module with
  `contamination_fpr_report(...)` (exact Wilson score interval) returning a
  report whose `as_payload()` classifies `source_identification_status` and
  `claim_tier`, blocks `headline_bayes_factor_allowed`, and a `main()` that
  writes the audited 95/100 report artifacts.
- `docs/generated/amplitude_matched_contamination_report.{json,md}`: the audited
  negative result (raw FPR 0.95, Wilson 95% [0.888, 0.978], blocked).
- `scripts/result_packs/generate_pack_B_local_global.py`: Pack B now loads the
  contamination report and exposes `source_identification_status` and an
  `amplitude_matched_contamination` summary, and reports it in the markdown.
- Regenerated `docs/generated/result_pack_B.md`.
- Tests: `tests/htt/test_amplitude_matched_contamination.py` and a Pack B
  consumption assertion.

## Artifact Metadata

- owner: HTT
- implementation_scope: htt
- claim_tier: blocked
- config_hash:
  - `htt/htt/htt/infer/amplitude_matched_contamination.py:sha256:1cbff44a250f05a38d7f21879a59749152956c689067324fe2d04ff8b06a19a1`
  - `scripts/result_packs/generate_pack_B_local_global.py:sha256:40241807de3d70a4fb84a6c378ab9f1b9b442540358c5f3f56f9ddabf153231b`
- input_hashes:
  - `docs/generated/amplitude_matched_contamination_report.json:sha256:d649f0bbf97db0f77e2f53e9dd4e2fde2032386f228bd7ee5d38685aae98b164`
  - `docs/generated/result_pack_B.md:sha256:f70dc4893b79b63822a6c803918cf42f2d9677a623a1b15f22a44ac517aa060c`
  - `tests/htt/test_amplitude_matched_contamination.py:sha256:b27aba99162db7c1c88e2fef25573495bb3038900f37b85dc77a6b3ebda4af19`
  - `tests/result_packs/test_pack_B.py:sha256:900838f6744bae8caf806c86e1046efb1742157e229021a340d8ff3fee533041`
- caveats:
  - no new long mocks were run; the audited 95/100 result is bound as a fixture;
  - while blocked, no positive headline Bayes factor may be drawn;
  - no native low-ell solver output is introduced.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/htt/test_amplitude_matched_contamination.py -q` initially failed with `ModuleNotFoundError` because the module did not exist.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B htt/htt/htt/infer/amplitude_matched_contamination.py` | PASS | Wrote the audited contamination report artifacts. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/result_packs/generate_pack_B_local_global.py` | PASS | Wrote `docs/generated/result_pack_B.md`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_amplitude_matched_contamination.py tests/result_packs/test_pack_B.py` | PASS | `13 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...module... report.md ...pack_B...` | PASS | `No forbidden claim language detected.` |
