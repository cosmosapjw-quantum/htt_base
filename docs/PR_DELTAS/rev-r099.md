# REV-R099 - Split Low-ell Likelihood Branches

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R099 split low-ell likelihood branches`
git_commit_or_worktree_state: pending_rev_r099_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 12)
- `docs/manuscript/ch07_results.tex` (D2/D3 scalar chi-square channels)
- `docs/manuscript/ch09_discussion.tex`
- Web/literature: Planck 2015 (arXiv 1502.01593) reports no physical Bianchi
  VII_h evidence, consistent with requiring a harmonic/covariance test rather
  than a central scalar chi-square.

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 12: split the low-ell mean-template and covariance/BiPoSH
likelihood branches and forbid a central scalar chi-square from standing in for
either.

## Role Split

- Physics/statistics auditor steelman: a central scalar chi-square on
  $D_2$/$D_3$ is neither a harmonic mean template with orientation
  marginalization nor a full anisotropic covariance, so it tests no Bianchi
  signal.
- Harness engineer steelman: pin both branch requirements with a classifier and
  contract tests.
- Claim-gate reviewer steelman: the manuscript must state that closing either
  branch requires the native low-ell atlas.

## Changes

- `htt/obsstat/lowell_likelihood_branches.py`: new `classify_lowell_likelihood`.
  Mean-template branch requires a harmonic template and orientation
  marginalization or a noncentral statistic; covariance branch requires a full
  anisotropic covariance; a central scalar chi-square closes neither.
- `docs/generated/lowell_likelihood_branch_report.md`: new branch report.
- `docs/manuscript/ch07_results.tex`, `ch09_discussion.tex`: added the low-ell
  likelihood branch caveat at the D2/D3 scalar statistics and in the discussion.
- Test: `tests/obsstat/test_lowell_likelihood_branches.py`.

## Artifact Metadata

- owner: OBSSTAT
- implementation_scope: obsstat
- claim_tier: diagnostic_only
- config_hash:
  - `htt/obsstat/lowell_likelihood_branches.py:sha256:130599005fb2b44392c79f44cab8dee979502bd36b700d9a3833ff9adbce50ee`
- input_hashes:
  - `docs/generated/lowell_likelihood_branch_report.md:sha256:525bd76cc04fae675f9f15a9d9b3d74ac3af1c5622187aaf0b97aedfc73f5ec4`
  - `tests/obsstat/test_lowell_likelihood_branches.py:sha256:8739860ea1af3835cc7513a493532ed8ef748b6273ef814e18beb947bf06d2a1`
  - `docs/manuscript/ch07_results.tex:sha256:ccf34920eae7cc3df6a0df4ceeb2a61c2ded26c4db3f9b69fcf0ffe3079beded`
  - `docs/manuscript/ch09_discussion.tex:sha256:4e8f50a76019dc5f95f0f7c2d2842aeb2dd50318817bf5ae7b8040f4bd83d2d9`
- caveats:
  - both branches remain blocked for a central scalar chi-square;
  - closing either branch requires the native low-ell morphology atlas;
  - no native low-ell solver output is introduced.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/obsstat/test_lowell_likelihood_branches.py -q` initially failed with `ModuleNotFoundError`.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_lowell_likelihood_branches.py tests/contracts/test_audit_ver2_claim_firewall.py` | PASS | `8 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...branches.py report.md ch07 ch09` | PASS | `No forbidden claim language detected.` |
