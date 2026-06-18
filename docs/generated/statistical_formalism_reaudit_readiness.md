# Statistical Formalism Re-Audit Readiness Checklist

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: not_directional
null_mock_status: mixed_formalism_tests_and_diagnostic_null_context
config_hash: none_manual_REV_R063_reaudit_readiness_update
input_hashes:
- `formalism_originality_program.zip`: `57c00c1f3868fe0e62270b9625d5e97386c57925363a9bfb21137d9d8348bbc9`
- `statistical_formalism_audit_report.zip`: `bdfb44061817bf01ca543356daaf3110cff70878edd14d3d4c5cc27cc4f34377`
- `AUDIT_REPORT (1).md`: `6da68d227f733049ac8664893534867db0dac0e6c9002f55b0650b84eb4e026c`
- `docs/generated/formalism_audit_originality_response_matrix.md`: `99aeab0266b8c244a37ea8f7dfc00aa8ed3a725579bef76228a182fe28164f78`
caveats:
- This readiness checklist records audit intake and scheduling state only.
- Open semantic-split, prose, cancellation-display, and legacy-label findings remain unresolved until later REV patches close them with tests.
- The archived proposal scripts are reference/proposal material, not production HTT/MIO implementation.
generating_command: manual REV-R063 archive intake and response-matrix update
git_commit_or_worktree_state: `40f789da0e8b70472d6384d1f7a7b12019b50329` with untracked REV-R063 archive/matrix inputs before commit

## Commit Policy Check

- No explicit user or repo instruction forbids commits in the current `htt_base` contract.
- `AGENTS.md` requires commit after tests and self-review for DAG PR work.
- This checklist is not a request to make scientific claims stronger.
- REV-R063 override: the user explicitly assigned commits to the main thread, so
  REV-R063 archive/matrix work must not be committed by the implementation agent.

## REV-R063 Incoming Audit Archive

| Item | Status | Evidence |
| --- | --- | --- |
| Incoming audit/proposal zips archived | done | `docs/audits/formalism_audit_2026-06-19/ARCHIVE_MANIFEST.md` records source filenames, SHA256 hashes, extraction time, and git state. |
| Root extracted audit markdown archived | done | `docs/audits/formalism_audit_2026-06-19/AUDIT_REPORT (1).md`; hash matches extracted `AUDIT_REPORT.md`. |
| Archived verifier placed at required path | done | `docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py`. |
| Response matrix created | done | `docs/generated/formalism_audit_originality_response_matrix.md`. |
| Archived verifier re-run on current payload | ran with open findings | `python3 docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py docs/generated/current_science_plot_payload.json` exited 0 but reported `cancellation trap reproduced: YES` and `semantic-split mismatch found: YES`; these remain open/blocking. |
| Claim-language scan of REV-R063 docs | pass | `venv/bin/python scripts/check_claim_language.py --dry-run --include-archives docs/generated/formalism_audit_originality_response_matrix.md docs/generated/statistical_formalism_reaudit_readiness.md docs/audits/formalism_audit_2026-06-19/ARCHIVE_MANIFEST.md` reported no forbidden claim language. |

## Prior Audit Findings And Fix Status

| Finding | Status | Evidence | Residual risk |
| --- | --- | --- | --- |
| Full external audit package missed PDF/figure payload context | addressed | `scripts/build_external_audit_package.py --check` passes; package contains PDF and figure payloads | package remains diagnostic-only |
| Research-only package was stale | addressed | `scripts/build_research_only_audit_package.py --check` passes | intentionally excludes PDF |
| VER2 sidecars carried production promotion labels | addressed | included VER2 manuscript figure sidecars are diagnostic-only | legacy result-pack text may mention readiness labels as historical context |
| Manifest self-reference caused post-commit stale loops | addressed | VER2 and package check-mode preserve/normalise self-referential git fields | generated manifests still record worktree state as provenance |
| LaTeX byproducts polluted worktree/package risk | addressed | byproducts ignored and package tests exclude logs/aux files | local scratch files may exist after future latexmk runs |
| Native solver/family-ID overclaim risk | guarded | claim-lint, figure audit, package manifests keep native/family gates failed | stronger claims still require native morphology atlas and matched null/mask/covariance gates |

## Prior Baseline Validation Commands To Re-Run

- `venv/bin/python scripts/build_external_audit_package.py --check` -> pass
- `venv/bin/python scripts/build_research_only_audit_package.py --check` -> pass
- `venv/bin/python scripts/ver2_artifact_export.py --check` -> pass
- `venv/bin/python scripts/check_publication_claim_freeze.py --check` -> pass
- `venv/bin/python scripts/audit_manuscript_figures.py --dry-run` -> 0 missing, 0 quarantined, 0 claim-risk
- `venv/bin/python -m pytest tests/contracts/test_audit_package_generator.py tests/contracts/test_research_only_audit_package.py scripts/test_ver2_artifact_export.py -q` -> pass

These are prior package-readiness commands from the previous re-audit package
state. REV-R063 did not re-run the full package suite because it only archives
incoming audit/proposal files and creates a response matrix; later REV patches
must rerun the relevant generation and package checks after changing code,
figures, or manuscript text.

## x_C/Q/Pi/F/G_F Audit Focus

- `x_C`: signed comparator coordinate, not invariant anisotropy magnitude.
- `Q`: policy-normalized score with explicit numerator and denominator policy.
- `Pi`: exceedance curve only, not truth probability.
- `F`: certified filling fraction only under sign-clean samples and admissible ceiling.
- `G_F`: depth-gap diagnostic requiring bin metadata and null/calibration status.
- MIO formalism remains diagnostic; HTT evidence/posterior surfaces are separate.
- Scalar formalism values cannot imply geometry detection or Bianchi family identification.
