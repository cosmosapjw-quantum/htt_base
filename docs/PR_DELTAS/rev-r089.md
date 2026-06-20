# REV-R089 - Strict Claim Downshift And PDF Lint

owner: COMMON
implementation_scope: manuscript_claim_firewall
claim_tier: diagnostic_only
transfer_source: mixed_external_proxy_and_none
sky_support_status: mixed_not_applicable_and_manifest_bound
null_mock_status: mixed_blocked_and_not_applicable
generating_command: `Codex REV-R089 manuscript downshift, latexmk rebuild, and PDF claim lint`
git_commit_or_worktree_state: pending_rev_r089_commit

## Evidence Read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-latex-paper-build/SKILL.md`
- `.agents/skills/htt-manuscript-figure-audit/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md`
- `docs/generated/audit_ver2_response_matrix.md`
- `docs/generated/audit_ver2_response_matrix.json`
- `docs/generated/manuscript_audit_repair_matrix.md`
- `scripts/pdf_claim_lint.py`
- Manuscript chapters `ch01`, `ch02`, `ch04`, `ch07`, `ch08`, `ch09`, and `ch10`.
- Web/docs check: CTAN documents `latexmk` as an automation tool for generating LaTeX documents, matching the chosen rebuild harness: <https://ctan.org/pkg/latexmk/?lang=en>.
- Web/docs check: pytest's official cache documentation confirms the cache plugin can be disabled with `-p no:cacheprovider`, matching the focused contract-test command: <https://docs.pytest.org/en/stable/how-to/cache.html>.

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 2 from the strict research-hardening plan: downgrade
unsafe positive `ln B`, source-origin, scalar-filling, comparator, PPC, and
future-test wording before deeper statistical repair PRs.

## Role Split

- Code cartographer steelman: patch the manuscript surfaces named by the
  strict audit and preserve defensible framework text. Attack: changing only
  PDF lint without source-level tests would let the unsafe prose return.
- Harness engineer steelman: add source tests plus PDF-surface tests for the
  exact re-audit phrases and high-strength `ln B` contexts. Attack: broad
  allowlists around legacy results would hide the problem.
- Physics/statistics auditor steelman: positive Bayes-factor numbers must be
  reclassified as premise-conditioned amplitude fits until matched nulls,
  covariance, PPC, LOOCV, and native atlas gates exist. Attack: a source
  interpretation is not justified by scalar `x/Q/F/Pi` or rest-frame Bayes
  factors.
- Claim-gate reviewer steelman: keep MIO/HTT separation and block geometry,
  family, native-transfer, and source-origin claims. Attack: future-test
  forecasts and survey-independence arguments must not read as current source
  proof.
- Regression tester steelman: require both TeX buildability and extracted-PDF
  prose lint. Attack: source grep alone misses compiled text contexts.

## Changes

- Added `tests/contracts/test_audit_ver2_claim_firewall.py` for strict
  source-level downclaim regressions.
- Extended `tests/contracts/test_pdf_claim_lint.py` with strict phrase,
  context-exemption, and high-strength `ln B` tests.
- Strengthened `scripts/pdf_claim_lint.py` with strict re-audit phrase
  failures and a high-strength `ln B` context gate that only downgrades
  clearly marked premise-conditioned or configured-likelihood-ratio contexts.
- Downshifted manuscript prose:
  - positive Bayes-factor readings now appear as premise-conditioned amplitude
    fits, configured likelihood-ratio values, or legacy diagnostic bins;
  - scalar filling language is class-conditioned and separated from the legacy
    budget-normalised score;
  - PPC wording is a single-`\beta` likelihood/covariance predictive-adequacy
    failure, not a data-property claim;
  - flat comparator language is fiducial-comparator plus comparator-envelope
    language, not a most-conservative assertion;
  - future source/hierarchy wording is compatibility or forecast language, not
    current source-origin evidence.
- Rebuilt `docs/generated/manuscript_pdf/htt_base_research_report.pdf`.
- Regenerated `docs/generated/pdf_claim_lint_report.md`.
- Updated `docs/generated/manuscript_audit_repair_matrix.md` with REV-R089
  closure rows.

## Artifact Metadata

- owner: COMMON
- implementation_scope: manuscript_claim_firewall
- claim_tier: diagnostic_only
- transfer_source: mixed_external_proxy_and_none
- config_hash:
  - `scripts/pdf_claim_lint.py:sha256:af7ab862614dcde965e05c36389ea678b360f27c0784e126e62d7cc88c884015`
- input_hashes:
  - `docs/generated/manuscript_pdf/htt_base_research_report.pdf:sha256:7243cebf41226475f124d9466f3aa81cd5c6cd28ddf0ab9c429669fd76be4239`
  - `docs/generated/pdf_claim_lint_report.md:sha256:8eb6a74b3d1427b0b706001b68765582806964d87aa7d2b9349a91504da5c3e1`
  - `docs/generated/manuscript_audit_repair_matrix.md:sha256:09d69f61f9f3354c797e91668009c634f831c7acbf746cad573c7d21a057682a`
  - `tests/contracts/test_audit_ver2_claim_firewall.py:sha256:4e3a5bb9164f74c065e57c5cb7c7352783a9300184a47fdd80507bd31636648f`
  - `tests/contracts/test_pdf_claim_lint.py:sha256:9e2d4361fa45360823b286140dd00d60f3e30433cd074e9d8d1dd73d93859fa4`
  - `tests/contracts/test_manuscript_audit_repair_matrix.py:sha256:83541681d4426b73932708f96c4ff863a5788988b449907944ee06ae004a7a6a`
- caveats:
  - no native low-ell solver result is introduced;
  - no Bianchi-family naming or selection claim is made;
  - the PDF lint is a prose-surface gate and does not replace matched null,
    covariance, PPC, LOOCV, or native-atlas validation.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_audit_ver2_claim_firewall.py` initially failed before manuscript patches because strict downclaim requirements were not implemented.
- `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_audit_ver2_claim_firewall.py tests/contracts/test_pdf_claim_lint.py tests/contracts/test_manuscript_rearchitecture.py` initially failed with three strict claim-firewall failures before the manuscript wording changes.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=docs/generated/manuscript_pdf docs/manuscript/main.tex` | FAIL | Run from repo root; TeX could not resolve `generated/ver2_titlepage_status.tex`. Correct command must run from `docs/manuscript` with the repo's generated-path assumptions. |
| `SOURCE_DATE_EPOCH=1766102400 FORCE_SOURCE_DATE=1 latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=htt_base_research_report -outdir=../generated/manuscript_pdf main.tex` | PASS | Run from `docs/manuscript`; produced `docs/generated/manuscript_pdf/htt_base_research_report.pdf`, 358 pages. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py` | PASS | Regenerated `docs/generated/pdf_claim_lint_report.md`; `Failed findings: 0`, `Warning findings: 66`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py --check` | PASS | Report up to date. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_audit_ver2_claim_firewall.py tests/contracts/test_pdf_claim_lint.py tests/contracts/test_manuscript_rearchitecture.py tests/contracts/test_manuscript_audit_repair_matrix.py` | PASS | `32 passed in 1.28s`. |
| `rg -n "Citation .* undefined|Reference .* undefined|There were undefined|Rerun to get cross-references|Fatal error|Missing \\\\$" docs/generated/manuscript_pdf/htt_base_research_report.log` | PASS | No matches. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ... --format json` | PASS | `issue_count=0` across touched production, test, generated, and PR delta files. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py ...` | PASS | No forbidden claim patterns detected. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py ...` | PASS | No unmarked strong claims detected after rephrasing negative caveats. |
| `git diff --check` | PASS | No whitespace errors. |

## Review Loop

- Loop 1 finding: strict phrase tests covered source files, but the PDF-surface
  linter still allowed high-strength `ln B` language when the compiled context
  contained evidence/support/odds vocabulary.
- Patch: added strict fail patterns and high-strength context tests in
  `tests/contracts/test_pdf_claim_lint.py`; downshifted manuscript phrases to
  premise-conditioned amplitude fit, configured likelihood-ratio value, and
  legacy diagnostic bin language.
- Loop 2 finding: first rebuilt PDF still failed 13 extracted-text contexts
  around `ln B` plus evidence/support language.
- Patch: narrowed `LNB_DOWNCLAIM_MARKERS` to explicit configured-likelihood
  and premise-conditioned markers, then removed remaining high-strength
  result prose from `ch07`, `ch08`, `ch09`, and `ch10`.
- Loop 3 result: source tests, PDF lint generation, PDF lint check, and TeX log
  scan passed. Remaining PDF lint entries are warnings for numeric `ln B`
  mentions in method, legacy, or explicitly conditioned contexts.

## Claim Audit

| Claim | Owner | Status | Evidence | Risk | Required fix |
| --- | --- | --- | --- | --- | --- |
| Positive `ln B` numbers are premise-conditioned amplitude fits | HTT/manuscript | CONDITIONAL | manuscript wording, PDF lint | could be read as source-origin or geometry support | keep `pdf_claim_lint.py` strict gate and require future matched-null/covariance/PPC/LOOCV/native-atlas PRs |
| MIO/HTT `Pi` and filling terms are namespace-separated | HTT/MIO/manuscript | IMPLEMENTED | source contract test | scalar filling could be mistaken for certified occupancy | preserve `Pi_HTT`/`Pi_MIO`, class-conditioned filling, and legacy budget-normalised score wording |
| PDF-surface lint blocks strict re-audit phrases | COMMON | IMPLEMENTED | `pdf_claim_lint_report.md`, contract tests | extraction context can be imperfect | keep warnings visible and rerun after every manuscript rebuild |

## Residual Risks

- This PR downclaims unsafe text but does not implement the statistical repairs
  scheduled for REV-R090 onward.
- Existing warning-level `ln B` mentions remain where they are methodological,
  legacy, or explicitly conditioned; they are not current native-transfer or
  source-identification claims.
- Matched null, shared covariance, prior/error surfaces, PPC repair, LOOCV, and
  native morphology-atlas support remain future gates.

## Subagent Closure

REV-R089 subagents were spawned for code cartography, harness engineering,
physics/statistics audit, claim-gate review, and regression testing. Their
findings were incorporated before commit and their threads were closed.
