# REV-R072 Delta: Rebuild Formalism Re-Audit Package

owner: COMMON
implementation_scope: statistical_formalism_external_reaudit_package
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: mixed_not_directional_and_manifest_bound_directional_context
null_mock_status: mixed_formalism_tests_diagnostic_nulls_forecast_nulls_and_conditioned_legacy
generating_command: manual Codex REV-R072 package-generator update plus deterministic audit-package regeneration
git_commit_or_worktree_state: 8ac0a31+dirty before REV-R072 commit

## Evidence Read

- `AGENTS.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-manuscript-figure-audit/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/superpowers/plans/2026-06-19-formalism-audit-originality-program.md`
- `docs/PR_DELTAS/rev-r071.md`
- `scripts/build_statistical_formalism_audit_package.py`
- `tests/contracts/test_statistical_formalism_audit_package.py`
- Web CRAG: Python `zipfile` documentation verified current deterministic-archive mechanics for `ZipFile`, `ZipInfo`, fixed timestamps, and compression constants: <https://docs.python.org/3/library/zipfile.html>.

## Role Synthesis

- Code cartographer steelman: the narrow audit bundle should stay small and formalism-focused; attack: the pre-R072 bundle omitted the new claim ladder, chapter context, response matrix, and linter output needed to audit R071.
- Harness engineer steelman: package checks should be deterministic and fail closed on stale artifacts; attack: stale generated packages and stale semantic-firewall reports would make the re-audit bundle untrustworthy even if tests pass.
- Physics/statistics auditor steelman: the audit prompt should focus on definitions, cancellation, denominator policies, threshold semantics, and depth-gap null status; attack: a generic package prompt would let reviewers miss the `x_C/Q/Pi/F/G_F` overinterpretation risks.
- Claim-gate reviewer steelman: rejection triggers are useful for hostile review; attack: production outputs should not repeat exact forbidden claim strings when equivalent indirect wording is available.
- Regression tester steelman: broad collection/smoke/contracts are enough for a packaging-only revision; attack: stale generated packages, linter subprocess output, and manual/status-number findings still need explicit recording.

## Changes

- Expanded the statistical formalism audit package to include manuscript chapter sources, `formalism_methods_claim_ladder.tex`, `formalism_audit_originality_response_matrix.md`, and the hostile review response matrix.
- Added generated `FIGURE_LABEL_LINTER_REPORT.md` to the zip, with hashes for `current_science_plot_payload.json` and `verify_formalism_figure_labels.py`.
- Promoted figure-label linter pass status into required package gates: `figure_label_linter_report_included` and `figure_label_linter_passed`.
- Rewrote the re-audit prompt to foreground novelty/substance, semantic-firewall operational substance, cancellation/magnitude reporting, `Pi/F/G_F` interpretation, and legacy `lnB` leakage.
- Removed exact forbidden claim strings from the generated prompt's rejection-trigger examples while preserving the same claim-firewall intent.
- Regenerated the stale semantic-firewall fuzz reports, full external audit package, research-only external audit package, and statistical formalism audit package.
- Updated the REV-R072 plan checklist.

## Generated Artifacts

- `docs/generated/statistical_formalism_audit_package.zip`: `sha256:90077b0bb380adf45a522c88a25d3f1c7d105343db093b7949ff1250a125a539`
- `docs/generated/statistical_formalism_audit_package_manifest.json`: `sha256:0e3c220c9b908f64d1744e45449ea47026e183d9f186181c5d5ca6eafc67b529`
- `docs/generated/statistical_formalism_audit_prompt.md`: `sha256:e876266eda83a1c04f11f7f07fdd84b6d43cba7d84bc1f8a8fe88a49bfb587ad`
- `docs/generated/statistical_formalism_reaudit_readiness.md`: `sha256:ac849123cead8dbe4363fc00ec1badda726105f0acec4374ab239a4350ecc713`
- `docs/generated/external_audit_package.zip`: `sha256:39764761ae03c8bbf42c900b68c91cf1f2ded7d50b6bdc64b1b95c9f2d820617`
- `docs/generated/research_only_external_audit_package.zip`: `sha256:766e0b0aa37e7c3e3be830fb69de935fd34abea3d68e8d336e4c35d711f89500`
- `docs/generated/semantic_firewall_fuzz_report.json`: `sha256:08ce9205ab94be16e6d2db3a5cee7168720da4cdf8ed3e3a145e088b13c1fd77`
- `docs/generated/semantic_firewall_fuzz_report.md`: `sha256:f20f82dba6b6a328c8effde35b56f0c63f13e497f15dfec5adf1a0d6212d0292`
- Statistical formalism package manifest summary: `archive_entry_count=112`, `failed_gates=[]`, `config_hash=sha256:fe74bec59eaeeb505cf3edd096be45ff52b168936f8fffb9aa62323f96788ee7`.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m py_compile scripts/build_statistical_formalism_audit_package.py tests/contracts/test_statistical_formalism_audit_package.py` -> pass
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_statistical_formalism_audit_package.py --dry-run` -> pass, `archive_entry_count=112`, all required gates true
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_semantic_firewall_fuzz_report.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json` -> pass
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_external_audit_package.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/ver2_artifact_export.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_statistical_formalism_audit_package.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_statistical_formalism_audit_package.py tests/contracts/test_audit_package_generator.py tests/contracts/test_research_only_audit_package.py tests/contracts/test_formalism_figure_labels.py scripts/test_ver2_artifact_export.py -q` -> `50 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider tests/mio tests/htt/test_posterior_pushforward.py tests/contracts -q` -> `355 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -m smoke -q` -> `6 passed, 7491 deselected`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider --collect-only -q` -> `7438/7497 tests collected (59 deselected)`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_publication_claim_freeze.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/audit_manuscript_figures.py --dry-run` -> `includegraphics=118 resolved=118 quarantined=0 missing=0 text_findings=9`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/pdf_claim_lint.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` -> `Completed 62/62 = 100.0%`, dependency-weighted `100.0%`, unblocked next `none`
- Targeted R072 forbidden exact-string scan over generator, generated prompt/readiness, and focused test -> no hits after rewriting rejection examples
- `git diff --check` -> clean

## Review Findings Addressed

- Subagent review found the R071 claim ladder and response matrix absent from the narrow formalism package; both are now included and tested.
- Subagent review found the figure-label linter output absent from the bundle; it is now generated as a virtual zip entry and required to pass.
- Subagent review found stale external/research-only/formalism audit packages; all three package families were regenerated and their `--check` commands pass.
- Final claim-gate scan found exact forbidden strings in prompt rejection examples; those examples were rewritten without weakening the rejection trigger.

## Residual Risks

- The package is a diagnostic external re-audit bundle, not a native low-ell solver validation bundle.
- Legacy or conditioned files remain included only where needed for current figure/formalism interpretation; they do not promote MIO diagnostics into evidence.
- Manuscript figure audit still reports nine manual/status-number findings, all non-failing and already visible in the audit output.
- No native morphology atlas, matched observed-data null stack, PPC, LOOCV, or family-equivalence gate was added.

## Subagent Thread Hygiene

- R072 code cartographer, harness engineer, claim-gate reviewer, and regression tester threads completed read-only reviews.
- No continuing subagent work remains assigned to R072 after this delta.

## Next Candidate

- Re-open DAG/revision planning from the next user-directed audit finding; the canonical PR DAG reports no unblocked remaining PR because `docs/codex_handoff/pr_backlog.yaml` is complete.
