# REV-R073 Delta: Refresh Research-Only External Audit Package

owner: COMMON
implementation_scope: research_report_external_audit_package_refresh
claim_tier: diagnostic_only
transfer_source: mixed_none_observed_reference_external_transfer_conditioned_legacy
sky_support_status: pending_or_unknown_for_existing_directional_artifacts
null_mock_status: mixed_not_statistical_jackknife_bootstrap_diagnostic_and_legacy_conditioned
generating_command: `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py`
git_commit_or_worktree_state: b772c0f+dirty before REV-R073 commit

## Evidence Read

- `scripts/build_research_only_audit_package.py`
- `tests/contracts/test_research_only_audit_package.py`
- `docs/generated/research_only_external_audit_package_manifest.json`
- `docs/generated/research_only_external_audit_prompt.md`
- `docs/generated/research_only_external_audit_package.zip`
- `docs/generated/manuscript_figure_inventory.md`
- `docs/generated/missing_figure_references.md`
- `docs/generated/publication_claim_freeze.md`
- `docs/generated/pdf_claim_lint_report.md`

## Changes

- Rebuilt `docs/generated/research_only_external_audit_package.zip` for the current post-R072 research report state.
- Rebuilt `docs/generated/research_only_external_audit_package_manifest.json` and `docs/generated/research_only_external_audit_prompt.md`.
- Preserved the research-only package policy: compiled PDF excluded, LaTeX source included, manuscript figure payloads and manifests included, generated plot/result/claim metadata included, and code samples limited to plot-context files.
- Reworded rejection-trigger examples in the research-only audit prompt to avoid exact forbidden claim strings while preserving the same hostile-review checks.
- Added a contract test that prevents the exact forbidden examples from reappearing in the generated research-only prompt.

## Generated Artifacts

- `docs/generated/research_only_external_audit_package.zip`: `sha256:32f51df6deb069740f76eacb9d024dbbdb779d661c2923a969e4b506e03e9183`
- `docs/generated/research_only_external_audit_package_manifest.json`: `sha256:91427ee15053139bc78bfb12542336547aaa617722e376587ec50cd88901c454`
- `docs/generated/research_only_external_audit_prompt.md`: `sha256:d01e9c23644fc53603aaa203fc5eef81aa5223409b3b1f602dc6845e40894155`
- Manifest summary: `archive_entry_count=307`, `failed_gates=[]`, `compiled_pdf_excluded=True`, `all_manuscript_figures_have_payload_and_manifest=True`, `config_hash=sha256:e35a5ec772a391496bb4ba8b0756de32c04d3cb41225ca16f4a4a60636dac05c`.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m py_compile scripts/build_research_only_audit_package.py tests/contracts/test_research_only_audit_package.py` -> pass
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_research_only_audit_package.py -q` -> `5 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py --dry-run` -> all required assertions true, `archive_entry_count=307`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py --check` -> current
- Zip inspection -> `pdf_entries=0`, `has_prompt=True`, no exact forbidden rejection-trigger strings in packaged prompt
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_publication_claim_freeze.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/audit_manuscript_figures.py --dry-run` -> `includegraphics=118 resolved=118 quarantined=0 missing=0 text_findings=9`; missing/quarantined/forbidden/claim-risk findings all zero
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/pdf_claim_lint.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_external_audit_package.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_statistical_formalism_audit_package.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_semantic_firewall_fuzz_report.py --check` -> current
- Targeted exact-string scan over the research-only generator, generated prompt, and focused test -> no hits
- `git diff --check` -> clean

## Residual Risks

- This package is for external research-formalization audit only; it is not native low-ell solver validation and not publication readiness.
- The generated manifest records `b772c0f+dirty` because the package, prompt, manifest, and generator/test changes were produced before this commit.
- Manuscript figure audit still reports nine manual/status-number findings; these are non-failing but remain visible to reviewers.
- No native morphology atlas, matched observed-data null stack, PPC, LOOCV, or family-equivalence gate was added.

## Next Candidate

- Send `docs/generated/research_only_external_audit_package.zip` and `docs/generated/research_only_external_audit_prompt.md` for external research-only review.
