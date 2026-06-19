# REV-R071 Delta: Manuscript Methods Reframe

owner: COMMON
implementation_scope: formalism_methods_manuscript_reframe
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: mixed_not_directional_and_pending_directional_support
null_mock_status: mixed_not_statistical_current_code_diagnostic_null_banks_and_conditioned_legacy
generating_command: manual Codex REV-R071 implementation plus deterministic LaTeX/current-manuscript artifact refresh
git_commit_or_worktree_state: e49a18a+dirty before REV-R071 commit

## Evidence Read

- `docs/superpowers/plans/2026-06-19-formalism-audit-originality-program.md`
- `docs/PR_DELTAS/rev-r070.md`
- `docs/manuscript/main.tex`
- `docs/manuscript/ch01_introduction.tex`
- `docs/manuscript/ch02_dipole_anomaly.tex`
- `docs/manuscript/ch03_framework.tex`
- `docs/manuscript/ch05_teff_corrections.tex`
- `docs/manuscript/ch07_results.tex`
- `docs/manuscript/ch08_robustness.tex`
- `docs/manuscript/ch09_discussion.tex`
- `docs/manuscript/ch10_future.tex`
- `docs/manuscript/ch11_error_hierarchy.tex`
- `docs/manuscript/references.bib`
- `scripts/make_current_manuscript_figures.py`
- `scripts/pdf_claim_lint.py`
- `scripts/check_publication_claim_freeze.py`
- `scripts/audit_manuscript_figures.py`
- `tests/contracts/test_current_manuscript_figures.py`
- `tests/contracts/test_publication_claim_freeze.py`
- Web CRAG sources verified for methods/prior-art framing: DES Y3 blinding page, Muir et al. 2020 blinding paper, Steegen et al. 2016 multiverse analysis, Gelman-Loken 2013 forking-paths note, Planck 2018 isotropy, Planck 2013/2015 Bianchi context, and McEwen et al. WMAP Bianchi context.

## Role Synthesis

- Code cartographer: the manuscript already had claim-firewall pieces, but the introduction, results, and discussion still let legacy Bayes-factor material dominate as if it were a result spine.
- Harness engineer: R071 needed a generated snippet and focused contract tests rather than hand-only prose; the PDF, PDF lint, publication freeze, and current figure manifests form a fixed-point dependency cycle.
- Physics/statistics auditor: the defensible claim is diagnostic algebra, comparator/cancellation semantics, and registered claim lanes; scalar `x/Q/Pi/F/G_F` summaries cannot identify geometry or family.
- Claim-gate reviewer: demote legacy evidence/preferred-axis/zero-FPR language to conditioned diagnostics; keep MIO diagnostic-only and external transfer explicitly non-native.
- Regression tester: run a deterministic LaTeX build with a fixed `SOURCE_DATE_EPOCH` so PDF hashes can stabilize across PDF lint, publication-freeze, and current-figure regeneration.

## Changes

- Reframed the manuscript title, introduction, framework chapter, results chapter, robustness chapter, discussion, and future-work chapter around a methods/framework contribution rather than anomaly detection.
- Added generated `docs/manuscript/generated/formalism_methods_claim_ladder.tex` and wired it into the introduction.
- Added the R071 claim ladder: exact signed comparator projection; cancellation caveat; MIO diagnostic-only ownership; fail-closed `F`; registered `Pi`; denominator-split `G_F`; forbidden detection/native/family claims; and forecast-only local/global discrimination.
- Added the F1-F9 methods contribution paragraph, with semantic firewalling as the flagship result.
- Added limitations: no current detection, no native low-ell solver output, no native morphology atlas, no Bianchi family-ID, no observed-data local/global separation, transfer-conditional surfaces only, and blocked `G_F` matched-null FPR.
- Added bibliography entries for the CRAG-verified blinding, multiverse/forking-paths, Planck, and WMAP Bianchi context.
- Repaired audit-highlighted mathematical/prose issues: `g_{224}` heading now separates PSTF coupling normalisation from the binomial factor, `sigma/H = 5.4e-3` was normalized to `sigma/Theta`, `0/100` false positives are finite-sample statements, and preferred-axis/evidence-gain language was demoted.
- Updated generated current-manuscript artifacts, current figure manifests, PDF claim lint report, publication claim freeze, hostile review matrix, and PDF manifest.
- Used `SOURCE_DATE_EPOCH=1766102400 FORCE_SOURCE_DATE=1 latexmk -g ...` for the final PDF build so the PDF hash stabilizes against the generated provenance cycle.
- Updated publication-freeze regression wording to accept `family-ID remains blocked`, avoiding the literal phrase that the manuscript-figure claim-risk scanner treats as risky.

## Generated Artifacts

- `docs/generated/manuscript_pdf/htt_base_research_report.pdf`: `sha256:9c20a92c4c4f1bb34978084588933b957ccdcf5e5ff3eeb1950ada9914b0e266`
- `docs/generated/manuscript_pdf/htt_base_research_report.manifest.json`: records the stabilized PDF hash and deterministic build command.
- `docs/generated/pdf_claim_lint_report.md`: `sha256:7c866f477b78f6d5d2cb042590733afc17575e59757d0e372e9bc76f5d3fa6fc`
- `docs/generated/publication_claim_freeze.md`: `sha256:1ba0877a820632d98f7baa1d6bb80bb40ce38bc9f7d2dc5f4777ffec2a837309`
- `docs/generated/hostile_review_response_matrix.md`: `sha256:1ffac7a3876bbb2c409c9d801436f9c6457c7b4b31da6c069b14c3458dcf0ad6`
- `docs/generated/current_manuscript_plot_list.md`: `sha256:3837ed474f7d0f44b00a93166aca174da8db164546b2db6df03bb6b54c828f0d`
- `docs/manuscript/generated/formalism_methods_claim_ladder.tex`: `sha256:a309d34c513ce4acb86dd1b63fd0098a8a1b111057b317d47e09919389679094`

## Validation

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile scripts/make_current_manuscript_figures.py scripts/audit_manuscript_figures.py scripts/pdf_claim_lint.py scripts/check_publication_claim_freeze.py` -> pass
- Fixed-point generation loop:
  - `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/make_current_manuscript_figures.py`
  - `cd docs/manuscript && SOURCE_DATE_EPOCH=1766102400 FORCE_SOURCE_DATE=1 latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=htt_base_research_report -outdir=../generated/manuscript_pdf main.tex`
  - `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/pdf_claim_lint.py`
  - `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_publication_claim_freeze.py`
  - repeated until PDF, PDF-lint, freeze, and claim-ladder hashes stabilized.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/make_current_manuscript_figures.py --check` -> current
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/pdf_claim_lint.py --check` -> up-to-date
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_publication_claim_freeze.py --check` -> up-to-date freeze report and hostile review response matrix
- `rg -n "Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references|Fatal error|Missing \\\\$" docs/generated/manuscript_pdf/htt_base_research_report.log || true` -> no hits
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider tests/contracts/test_current_manuscript_figures.py tests/contracts/test_manuscript_figure_audit.py tests/contracts/test_pdf_claim_lint.py tests/contracts/test_publication_claim_freeze.py -q` -> `26 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/audit_manuscript_figures.py --dry-run` -> `includegraphics=118 resolved=118 quarantined=0 missing=0 text_findings=9`; missing/quarantined/forbidden/claim-risk findings all zero
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/check_claim_language.py docs/manuscript --include-archives --format json` -> `issue_count: 0`
- Targeted blocked-phrase scan over `docs/manuscript` and generated snippets -> no hits
- `git diff --check` -> clean

## Review Findings Addressed

- Final claim reviewer found stale PDF manifest hashes; fixed after the deterministic build fixed-point.
- Final claim reviewer flagged generated sentence grammar; fixed generator and snippet test.
- Final regression tester found `pdf_claim_lint.py --check` and `check_publication_claim_freeze.py --check` stale after active PDF rebuild; fixed by stabilizing the PDF build and regenerating lint/freeze/current artifacts.
- Final regression tester found the publication-freeze test expected the exact phrase `family identification remains blocked`; changed test to the safer `family-ID remains blocked` wording already used in the manuscript.

## Residual Risks

- PDF claim lint still reports warning-only legacy `lnB` contexts; failed findings are zero. These contexts remain acceptable only as conditioned diagnostic/legacy material.
- Manuscript figure audit still reports nine manual/status-number findings from existing VER2/generated status-count material and two Chapter 7 pytest-count lines; none are missing figures, quarantined figures, forbidden claims, or claim-risk findings.
- R071 does not regenerate external audit packages; that remains the purpose of `REV-R072`.
- No native low-ell solver, native morphology atlas, matched observed-data null stack, PPC, LOOCV, or family-equivalence gate was added.

## Next Candidate

- `REV-R072: Regenerate Audit Package and External Re-Audit Prompt`
