# REV-R101 - Refresh Strict Reaudit Package

owner: COMMON
implementation_scope: research_audit_package
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R101 refresh strict reaudit package`
git_commit_or_worktree_state: pending_rev_r101_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 14)
- `scripts/build_research_only_audit_package.py`
- `tests/contracts/test_research_only_audit_package.py`
- `docs/generated/audit_ver2_response_matrix.md` (REV-R088)

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR closes the
supplemental REV-R088..REV-R101 research-hardening DAG: it rebuilds the
manuscript PDF, makes the research-only audit package source-complete (with the
strict-audit response matrix and completion report, and no PDFs), and freezes
the next-audit prompt.

## Role Split

- Claim-gate reviewer steelman: the next external auditor must read the strict
  `audit_ver2` response matrix and completion report and treat F1-F4 blocks as
  still in force.
- Harness engineer steelman: pin the package contents with a line-stable TeX and
  reaudit-matrix contract test, and keep PDFs out of the archive.
- Regression tester steelman: the rebuilt PDF must pass the claim lint and the
  full final test list.

## Changes

- `docs/generated/audit_ver2_completion_report.md`: new completion report mapping
  F1-F4 and the major fixes to their closing REV PRs.
- `scripts/build_research_only_audit_package.py`: added the strict-audit response
  matrix and completion report to the archived metadata, and added them to the
  frozen next-audit prompt reading order.
- Rebuilt `docs/generated/manuscript_pdf/htt_base_research_report.pdf` and
  refreshed its manifest hash/size/provenance (the manifest is a hand-maintained
  artifact; no in-repo generator exists, so only the PDF-identifying and git
  provenance fields were refreshed).
- Regenerated `docs/generated/pdf_claim_lint_report.md` (0 failed findings, 66
  warnings), `docs/generated/manuscript_figure_inventory.md`,
  `docs/generated/missing_figure_references.md`, and the research-only package
  zip/manifest/prompt.
- `docs/manuscript/ch08_robustness.tex`: added an explicit configured
  likelihood-ratio / matter-dipole-premise / not-source-identification downclaim
  adjacent to the `ln B < 2.5` rho-sweep threshold, so the rebuilt-PDF claim lint
  does not fail on a table-interleaved high-strength proximity (rephrased the
  manuscript rather than weakening the scanner).
- Test: added the line-stable TeX + reaudit-matrix package assertion.

## Artifact Metadata

- owner: COMMON
- implementation_scope: research_audit_package
- claim_tier: diagnostic_only
- config_hash:
  - `scripts/build_research_only_audit_package.py:sha256:ae4c1032e691311681eb65e78c0de8a58f49fbc17e15bba76fd5a9cd2896a0c1`
- input_hashes:
  - `docs/generated/audit_ver2_completion_report.md:sha256:b965a1f5d48b7ce4b42dcdf69522b74ef1d519c99d49f1e0a6d0e107a66acbc0`
  - `docs/generated/research_only_external_audit_prompt.md:sha256:b2f841c9fbe32aefefc1f24e7f49c946ab45498c9d500adb3cd60585ab71eaed`
  - `docs/generated/research_only_external_audit_package_manifest.json:sha256:4bb049467fb71cbabcebd46a6f79badb06288e2e1ad28e0fe2130c3bd8452054`
  - `tests/contracts/test_research_only_audit_package.py:sha256:d8d6cfeb271763a97dca4820d93f0e1c6140bd500b142963c3295fb543adb29b`
  - `docs/manuscript/ch08_robustness.tex:sha256:89edc4f3e598d5286a17390bfa2b6850b2de68edd9075e05a62843fba3b66374`
  - `docs/generated/manuscript_pdf/htt_base_research_report.pdf:sha256:24f7ecc5dfef88d1c7bf81ea6123c5faff2027db8be01b4ad41483d9b9b2d3ac`
- caveats:
  - the research-only package contains line-stable TeX, generated matrices,
    figure payloads/manifests/source JSON, and no PDFs;
  - strict-audit blockers F1-F4 remain in force pending their gate bundles and
    the native low-ell morphology atlas;
  - no native low-ell solver output is introduced.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_research_only_audit_package.py::test_research_only_package_includes_line_stable_tex_and_reaudit_matrix -q` initially failed because `docs/generated/audit_ver2_completion_report.md` (and the audit_ver2 response matrix) were not in the archive.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `cd docs/manuscript && SOURCE_DATE_EPOCH=1766102400 FORCE_SOURCE_DATE=1 latexmk -g -pdf ... main.tex` | PASS | Rebuilt the PDF; log has no undefined references or fatal errors. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py --check` | PASS | `Failed findings: 0`, `Warning findings: 66`; report up-to-date. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/audit_manuscript_figures.py --dry-run` | PASS | `Manual/status-number findings: 0`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py --check` | PASS | Package up-to-date. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q <12 final test files>` | PASS | `62 passed`. |
