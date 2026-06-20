# REV-R086 - Manuscript rearchitecture around gated results

## Scope

- Owner: COMMON/manuscript.
- Plan source: `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`, Task 13.
- Canonical PR DAG status remains complete at `62/62`; this supplemental delta tracks revision-slice task `REV-R086`.
- Claim ceiling: `diagnostic_only`.

## Evidence Read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-latex-paper-build/SKILL.md`
- `.agents/skills/htt-manuscript-figure-audit/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`
- `docs/manuscript/main.tex`
- `docs/manuscript/ch01_introduction.tex`
- `docs/manuscript/ch03_framework.tex`
- `docs/manuscript/ch07_results.tex`
- `docs/manuscript/ch08_robustness.tex`
- `docs/manuscript/ch09_discussion.tex`
- `docs/manuscript/ch10_future.tex`
- `docs/manuscript/appendices.tex`
- `docs/manuscript/references.bib`
- `docs/manuscript/generated/theorem_extension_appendix_figures.tex`
- `docs/generated/qfpi_semantic_reconciliation.md`
- `docs/generated/cf4pp_lnb_provenance_report.md`
- `docs/generated/revision_claim_lanes.md`
- `docs/generated/publication_claim_freeze.md`
- `docs/generated/manuscript_audit_repair_matrix.md`
- `docs/PR_DELTAS/rev-r083.md`
- `docs/PR_DELTAS/rev-r084.md`
- `docs/PR_DELTAS/rev-r085.md`

## Web/Doc Checks

- WEB_CHECK_STATUS: done.
- Checked current external reference context before bibliography edits:
  - Phys. Rev. D page for von Hausegger and Dalang redshift tomography, DOI `10.1103/PhysRevD.111.123547`.
  - Official DESI DR1 release documentation, which reports more than 18 million unique targets from May 2021 through June 2022.
  - arXiv `2606.00551` for a DESI DR1 quasar cosmological-principle analysis, with A&A DOI `10.1051/0004-6361/202556955`.
  - MNRAS grouped Cosmicflows-4 velocity reconstruction, DOI `10.1093/mnras/stad3433`.

## Divergence And Review

- code cartographer:
  - Steelman: add an architecture spine rather than wholesale chapter rewrite, preserving labels and generated snippets.
  - Attack: full chapter reshuffling risks broken references, stale figure placement, and claim-lane drift.
- harness engineer:
  - Steelman: add a source-level contract for narrative order, theorem appendix inclusion, and CRAG bibliography coverage; rebuild PDF with the existing stable job name.
  - Attack: the plan's `audit_manuscript_figures.py --check` command is stale because the script has no `--check` flag.
- physics/statistics auditor:
  - Steelman: lead with scalar-identifiability no-go, finite-mock calibration, channel-matched occupancy, data binding, rest-frame rank gates, and future native-atlas prerequisites.
  - Attack: leading with `ln B`/odds values would let a hostile reviewer read dipole significance as Bianchi evidence.
- claim-gate reviewer:
  - Steelman: theorem figures stay appendix-only; MIO diagnostics stay non-posterior; external/proxy transfer stays non-native.
  - Attack: "headline" language around legacy Bayes factors invites claim promotion even when caveated.
- regression tester:
  - Steelman: focused pytest, stable LaTeX build, PDF claim lint regeneration/check, manuscript figure dry-run, and claim-language scans are the correct REV-R086 gate.
  - Attack: research-only audit package refresh belongs to REV-R087, not this PR.

Subagents closed: yes for completed preflight agents.

## Implemented Changes

- Added a `Revision architecture: safe strong results first` section to `ch01_introduction.tex`.
- Removed the early numeric legacy Bayes-factor lead from the introduction.
- Added the scalar-identifiability no-go anchor in `ch03_framework.tex`.
- Added legacy Bayes-factor demotion paragraphs to `ch07_results.tex` and `ch08_robustness.tex`.
- Reframed `ch09_discussion.tex` around what survives the firewall before legacy likelihood discussion.
- Reframed `ch10_future.tex` around rank/null/prior gates and future native-atlas prerequisites; downgraded future solver wording from current production capability to pre-solver transfer/provenance prototype.
- Added theorem-extension figures to the appendix-only diagnostic lane.
- Added CRAG-verified bibliography entries for redshift tomography, DESI DR1, DESI DR1 quasar cosmological-principle analysis, and grouped CF4 reconstruction.
- Post-review loop 1 fixed the `2606.00551` BibTeX metadata and reframed two residual legacy detection phrases as conditional diagnostic language.
- Added `docs/generated/manuscript_rearchitecture_report.md`.
- Added `tests/contracts/test_manuscript_rearchitecture.py`.

## Validation

| Command | Result | Notes |
|---|---:|---|
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_manuscript_rearchitecture.py` before implementation | FAIL | Red phase: 5 expected failures from missing rearchitecture report and required source wording. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_manuscript_rearchitecture.py` | PASS | 6 passed after adding regression coverage for reference metadata and legacy detection-language reframing. |
| `venv/bin/python -B scripts/check_claim_language.py --dry-run docs/manuscript/main.tex docs/manuscript/ch01_introduction.tex docs/manuscript/ch03_framework.tex docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex docs/manuscript/ch09_discussion.tex docs/manuscript/ch10_future.tex docs/manuscript/appendices.tex docs/generated/manuscript_rearchitecture_report.md docs/PR_DELTAS/rev-r086.md` | PASS | No forbidden claim language detected. |
| `venv/bin/python -B .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py docs/manuscript/main.tex docs/manuscript/ch01_introduction.tex docs/manuscript/ch03_framework.tex docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex docs/manuscript/ch09_discussion.tex docs/manuscript/ch10_future.tex docs/manuscript/appendices.tex docs/generated/manuscript_rearchitecture_report.md docs/PR_DELTAS/rev-r086.md` | PASS | No forbidden claim patterns detected after changing a negative caveat from scanner-sensitive `no ... truth...` wording to explicit `not ...` wording. |
| `SOURCE_DATE_EPOCH=1766102400 FORCE_SOURCE_DATE=1 latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=htt_base_research_report -outdir=../generated/manuscript_pdf main.tex` from `docs/manuscript` | PASS | Built `docs/generated/manuscript_pdf/htt_base_research_report.pdf`, 357 pages, 21,894,202 bytes after the post-review metadata/wording patch. PDF SHA256 `ff7565e3fb7060654a5807991f632c4cfd590a7278400456c071dc8be95120bd`. |
| `rg -n "Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references|Fatal error|Missing \\\\$" docs/generated/manuscript_pdf/htt_base_research_report.log || true` | PASS | No hard LaTeX/citation/reference findings. Existing hyperref/font/box warnings remain. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py` before wording fix | FAIL | Initial rebuilt PDF report had 1 failed finding on a negative `Bianchi family identification` sentence that lacked the scanner's explicit blocked/absent context marker. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py` | PASS | Regenerated `docs/generated/pdf_claim_lint_report.md`; 0 failed findings, 66 warning findings. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py --check` | PASS | Report up to date after serial rerun; earlier parallel check raced the report regeneration and reported stale. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/audit_manuscript_figures.py --dry-run` | PASS | `includegraphics=123 resolved=123 quarantined=0 missing=0 text_findings=14`; remaining text findings are 5 claim-risk phrases in negative theorem captions and 9 manual/status-number findings outside REV-R086. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_manuscript_rearchitecture.py tests/contracts/test_manuscript_audit_repair_matrix.py tests/contracts/test_pdf_claim_lint.py tests/contracts/test_expanded_manuscript_figure_suite.py tests/contracts/test_theorem_extension_assets.py` | PASS | 28 passed in 1.86s after adding the post-review regression checks. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_manuscript_rearchitecture.py tests/contracts/test_manuscript_audit_repair_matrix.py tests/contracts/test_pdf_claim_lint.py tests/contracts/test_current_manuscript_figures.py tests/contracts/test_expanded_manuscript_figure_suite.py tests/contracts/test_theorem_extension_assets.py` | FAIL | 33 passed, 1 failed in `test_current_manuscript_figure_generator_check_mode_is_current`: pre-existing stale `make_current_manuscript_figures.py --check` artifacts (`docs/generated/current_science_plot_payload.json`, four current figure manifests, `formalism_methods_claim_ladder.tex`, and `current_manuscript_plot_list.md`). This drift was observed before REV-R086 and is outside this manuscript-rearchitecture write scope. |
| `git diff --check` | PASS | No whitespace errors. |

## Claim-Tier Impact

REV-R086 changes manuscript architecture only. It does not add observational evidence, native solver output, family-identification support, MIO posterior semantics, or HTT evidence from theorem figures. The strongest positive statement remains a claim-tiered observational/statistical framework with explicit gates and transfer-conditional legacy surfaces.
