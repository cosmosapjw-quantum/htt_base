# REV-R091 - Split Report And Science Gates

owner: COMMON
implementation_scope: result_pack_gate_separation
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: summarized_blocked_and_not_bound
generating_command: `Codex REV-R091 split report-generation gates from science gates`
git_commit_or_worktree_state: pending_rev_r091_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 4)
- `docs/generated/audit_ver2_response_matrix.md`
- `scripts/result_packs/generate_pack_B_local_global.py`
- `scripts/result_packs/generate_pack_C_mio_certificates.py`
- `tests/result_packs/test_pack_B.py`
- `tests/result_packs/test_pack_C.py`

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 4 from the strict research-hardening plan: separate
report-generation gates from science gates so a clean markdown render is never
read as a clean science gate, and downgrade the Pack B observed global-tilt
ceiling from conditional to blocked.

## Role Split

- Claim-gate reviewer steelman: a `conditional` observed global-tilt ceiling in
  Pack B would make the next audit fail; observed inference must be blocked
  until cross-probe covariance, amplitude-matched null, response rank, PPC, and
  LOOCV payloads are bound, while synthetic-design wording stays conditional.
- Harness engineer steelman: pin the split with payload-level contract tests so
  a clean report render cannot silently imply science readiness.
- Physics/statistics auditor steelman: model ranking stays forbidden and the
  covariance/null science gate stays `not_bound`; report-generation passing is
  bookkeeping, not evidence.
- Regression tester steelman: keep the existing Pack B/C CLI, manifest, and
  forbidden-language guards green while flipping the observed ceiling.

## Changes

- `scripts/result_packs/generate_pack_B_local_global.py`:
  - `global_tilt_claim_tier_ceiling` is now `blocked` (was `conditional`);
  - added `observed_inference_status: blocked_observed_inference`,
    `synthetic_design_ceiling: conditional`, and
    `observed_inference_unblock_requirements`;
  - manifest `claim_tier_ceiling` is now
    `blocked_observed_conditional_synthetic`;
  - markdown scope states local/global wording is admissible only for the
    synthetic design ceiling and prints the observed/synthetic split.
- `scripts/result_packs/generate_pack_C_mio_certificates.py`:
  - added `report_gates` (markdown render, manifest metadata, certificate
    gather, dependency gather), `science_gates`
    (covariance/null `not_bound`, model ranking `forbidden`, native atlas,
    PPC, LOOCV), and a `gate_separation_note`;
  - markdown renders a Gate Separation section with both gate tables.
- Updated `tests/result_packs/test_pack_B.py` and
  `tests/result_packs/test_pack_C.py` with the new gate-split contract tests and
  the flipped observed ceiling assertions.
- Regenerated `docs/generated/result_pack_B.md` and
  `docs/generated/result_pack_C.md`.

## Artifact Metadata

- owner: COMMON
- implementation_scope: result_pack_gate_separation
- claim_tier: diagnostic_only
- transfer_source: none
- config_hash:
  - `scripts/result_packs/generate_pack_B_local_global.py:sha256:3df404ff173bd1b51aa8a1874ea06470cd6d787a74cdb114dfb77562b174d3f2`
  - `scripts/result_packs/generate_pack_C_mio_certificates.py:sha256:1e1c7d4dc420978eb9b829cc93257fea671fc1363a36aa3725211c851db6818f`
- input_hashes:
  - `docs/generated/result_pack_B.md:sha256:7d55ded6678510deedf62eaeacad89e94b7d0d9481632fb19b9a5178cbea7413`
  - `docs/generated/result_pack_C.md:sha256:a8335933b110bae061ff527f91aef424996311396cc52881eec05e583577e2fe`
  - `tests/result_packs/test_pack_B.py:sha256:e48b79e92695197ef1f42086afff99fac73d7ac652c7f75a69bf1761977513bd`
  - `tests/result_packs/test_pack_C.py:sha256:70bc9c0d6efb9bdc10ad780aaa1eaf45da3f459f1c8ace6c5db7207370076361`
- caveats:
  - no native low-ell solver result is introduced;
  - report-gate pass is report-generation bookkeeping, not science readiness;
  - observed local/global inference remains blocked until the listed observed
    payloads are bound.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/result_packs/test_pack_B.py::test_pack_b_observed_inference_is_blocked_until_observed_payloads_exist tests/result_packs/test_pack_C.py::test_pack_c_separates_report_and_science_gates` initially failed with `KeyError` on the missing `observed_inference_status`/`report_gates` keys.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/result_packs/generate_pack_B_local_global.py` | PASS | Wrote `docs/generated/result_pack_B.md`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/result_packs/generate_pack_C_mio_certificates.py` | PASS | Wrote `docs/generated/result_pack_C.md`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/result_packs/test_pack_B.py tests/result_packs/test_pack_C.py` | PASS | `16 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run scripts/result_packs/...B... ...C... docs/generated/result_pack_B.md docs/generated/result_pack_C.md` | PASS | `No forbidden claim language detected.` |
