# Statistical Formalism Re-Audit Readiness Checklist

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: not_directional_for_formalism_package
null_mock_status: mixed_formalism_tests_and_diagnostic_null_context

## Commit Policy Check

- No explicit user or repo instruction forbids commits in the current `htt_base` contract.
- `AGENTS.md` requires commit after tests and self-review for DAG PR work.
- This checklist is not a request to make scientific claims stronger.

## Prior Audit Findings And Fix Status

| Finding | Status | Evidence | Residual risk |
| --- | --- | --- | --- |
| Full external audit package missed PDF/figure payload context | quarantined | PR-120 withholds the non-binding PDF pair and includes the canonical block/inventory | no current PDF is distributed |
| Research-only package was stale | guarded | the PR-120 content gate rejects stale package entries | intentionally excludes PDF |
| Statistical-formalism package embedded stale manuscript/lint surfaces | quarantined | exact previous ZIP/manifest/prompt bytes moved under `legacy/cf4_p0/packages/statistical_formalism_audit/`; retained TeX/Bib rows are typed historical evidence | a diagnostic package may rebuild only when its content gate is clean; manuscript publication remains unauthorized |
| VER2 sidecars carried production promotion labels | addressed | included VER2 manuscript figure sidecars are diagnostic-only | legacy result-pack text may mention readiness labels as historical context |
| Manifest self-reference caused post-commit stale loops | addressed | VER2 and package check-mode preserve/normalise self-referential git fields | generated manifests still record worktree state as provenance |
| LaTeX byproducts polluted worktree/package risk | addressed | byproducts ignored and package tests exclude logs/aux files | local scratch files may exist after future latexmk runs |
| Native solver/family-ID overclaim risk | guarded | claim-lint, figure audit, package manifests keep native/family gates failed | stronger claims still require native morphology atlas and matched null/mask/covariance gates |
| Manuscript result framing did not foreground method-level contribution | addressed | `docs/manuscript/generated/formalism_methods_claim_ladder.tex` and chapter sources are included for audit | still not an observed-data discovery claim |
| Formalism-audit response matrix absent from narrow re-audit bundle | addressed | `docs/generated/formalism_audit_originality_response_matrix.md` is packaged | matrix is a response target, not proof of correctness |
| Figure-label linter output absent from narrow re-audit bundle | addressed | `FIGURE_LABEL_LINTER_REPORT.md` is generated and required to pass | linter checks labels, not physical validity |

## Validation Commands To Re-Run

- `venv/bin/python scripts/build_external_audit_package.py --check` -> pass
- `venv/bin/python scripts/build_research_only_audit_package.py --check` -> pass
- `venv/bin/python scripts/ver2_artifact_export.py --check` -> pass
- `venv/bin/python scripts/check_publication_claim_freeze.py --check` -> blocked_nonzero_pdf_claim_lint_passed
- `venv/bin/python scripts/audit_manuscript_figures.py --dry-run` -> 0 missing, 0 quarantined, 0 claim-risk
- `venv/bin/python -m pytest tests/contracts/test_audit_package_generator.py tests/contracts/test_research_only_audit_package.py scripts/test_ver2_artifact_export.py -q` -> pass

## x_C/Q/Pi/F/G_F Audit Focus

- `x_C`: signed comparator coordinate, not invariant anisotropy magnitude.
- `Q`: policy-normalized score with explicit numerator and denominator policy.
- `Pi`: exceedance curve only, not truth probability.
- `F`: certified filling fraction only under sign-clean samples and admissible ceiling.
- `G_F`: depth-gap diagnostic requiring bin metadata and null/calibration status.
- MIO formalism remains diagnostic; HTT evidence/posterior surfaces are separate.
- Scalar formalism values cannot imply geometry detection or Bianchi family-ID.
- The LaTeX tree is retained as immutable historical evidence with public_use false; main.tex is a fail-closed notice, not a current build entrypoint.
