# REV-R077: bind or quarantine CF4++ legacy evidence

owner: HTT
implementation_scope: cf4pp_lnb_provenance_gate
claim_tier: blocked
transfer_source: legacy_external_transfer_or_unbound
config_hash: sha256:manual-rev-r077
input_hashes:
- scripts/reproduce_cf4pp_lnb.py
- docs/generated/cf4pp_lnb_provenance_report.json
- docs/generated/cf4pp_lnb_provenance_report.md
- docs/manuscript/ch07_results.tex
- docs/manuscript/ch08_robustness.tex
- docs/manuscript/ch09_discussion.tex
sky_support_status: not_directional
null_mock_status: not_bound
generating_command: venv/bin/python scripts/reproduce_cf4pp_lnb.py --write
git_commit_or_worktree_state: pending_rev_r077_commit
caveats:
- not used in manuscript headline
- dedicated rerun required
- not native transfer
- no family identification
- no geometry-detection claim

## Intent

Close the external audit finding that the CF4++ legacy sensitivity value was
headline-adjacent but not traceable to canonical repo inputs.  REV-R077 adds a
binary provenance gate: preserve a CF4++ value only if a repo-local JSON object
binds the target value to config hash, input hashes, command, claim tier, and
transfer source; otherwise quarantine it.

## Evidence Gathering

- Repo evidence: `docs/audits/external_research_inputs_2026-06-20/RESEARCH_AUDIT_REPORT.md`
  flags the CF4++ value as untraceable and recommends reproduction or removal.
- Repo evidence: the conditioned legacy CF4++ figure manifest binds the image
  wrapper and gallery builder, but not a likelihood rerun JSON for the CF4++
  scalar-amplitude value.
- Web/documentation evidence: CF4 grouped data and column documentation support
  treating CF4/CF4++ as external observed-input catalogues, not native solver
  outputs.  Checked sources: MNRAS CF4 grouped analysis, Whitford/Howlett/Davis
  CF4 bulk-flow estimator caveat paper, and the Extragalactic Distance Database
  `kcf4allvel` column documentation.

## Divergence And Selection

- Code cartographer steelman: keep the CF4++ sensitivity number if a canonical
  JSON likelihood artifact already binds it.  Attack: current hits are
  manuscript prose, hard-coded legacy figure inputs, or image manifests that do
  not bind likelihood settings.
- Harness engineer steelman: implement `--write`/`--check` and a source override
  so future bound reruns can be accepted without rewriting the gate.  Attack:
  fail closed for hard-coded rows without config/input hashes.
- Physics/statistics auditor steelman: if a rerun binds all inputs, CF4++ can be
  a labeled transfer-conditional sensitivity row.  Attack: current values lack
  matched nulls, PPC, LOOCV, full covariance/mask support, and source binding,
  so they cannot be a manuscript headline.
- Claim-gate reviewer steelman: HTT may own a blocked provenance report.
  Attack: no CF4++ sensitivity value may imply native transfer, Bianchi family
  identification, geometry detection, or merged MIO/HTT evidence.
- Regression tester steelman: targeted provenance tests suffice for a narrow
  quarantine PR.  Attack: add claim-language, PDF claim lint, manuscript figure
  audit, smoke, contracts collect, and DAG validation.

## Changes

- Added `scripts/reproduce_cf4pp_lnb.py`, a no-rerun provenance gate with
  `--write`, `--check`, `--json`, and `--source-json` modes.
- Generated `docs/generated/cf4pp_lnb_provenance_report.json` and `.md`; current
  status is `quarantined_untraceable`, with no accepted source and no bound
  result config/input hashes.
- Added `tests/contracts/test_cf4pp_lnb_provenance.py`, including a temp-fixture
  proof that a fully bound CF4++ JSON can be accepted while an unbound hard-coded
  row remains quarantined.
- Removed unbound CF4++/Watkins numeric sensitivity values from manuscript
  result-facing prose/table cells.  The rows now report `unbound` provenance
  pending a dedicated rerun.
- Removed indirect threshold/headline remnants from Chapter 6, Chapter 8, and
  Chapter 9: only WFH2009 is described as the canonical legacy summary, while
  CF4++/Watkins rows are sensitivity inputs with unbound provenance.

## Verification

- `venv/bin/python scripts/reproduce_cf4pp_lnb.py --write`
  - result: wrote JSON and Markdown provenance reports.
- `venv/bin/python scripts/reproduce_cf4pp_lnb.py --check`
  - result: OK, reports are current.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider --collect-only tests/contracts/test_cf4pp_lnb_provenance.py -q`
  - result: 4 tests collected.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/contracts/test_cf4pp_lnb_provenance.py`
  - result after review-loop fixes: 7 passed.
- Fixed-string/regex search for `All three versions remain above`, `reports the evidence under each`, `headline number`, literal `+44/44.0/+105.8/105.8/+106`, and `threshold-crossing evidence` in `docs/manuscript/ch06_pipeline.tex`, `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch08_robustness.tex`, and `docs/manuscript/ch09_discussion.tex`
  - result after review-loop fixes: no hits.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/contracts/test_cf4pp_lnb_provenance.py tests/contracts/test_manuscript_audit_repair_matrix.py tests/contracts/test_claim_language_lint.py tests/contracts/test_pdf_claim_lint.py tests/contracts/test_manuscript_figure_audit.py`
  - result after review-loop fixes: 40 passed.
- `venv/bin/python scripts/check_claim_language.py docs/manuscript/ch06_pipeline.tex docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex docs/manuscript/ch09_discussion.tex docs/generated/cf4pp_lnb_provenance_report.md scripts/reproduce_cf4pp_lnb.py tests/contracts/test_cf4pp_lnb_provenance.py docs/PR_DELTAS/rev-r077.md --dry-run --format json`
  - result: 0 issues.
- `venv/bin/python scripts/pdf_claim_lint.py --check`
  - result: up to date.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -m smoke -q`
  - result: 6 passed, 7520 deselected.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider --collect-only tests/contracts -q`
  - result: 232 tests collected.
- `venv/bin/python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml`
  - result: OK, 62 PRs, DAG valid.
- `venv/bin/python scripts/audit_manuscript_figures.py --manuscript-root docs/manuscript --dry-run`
  - result: includegraphics=118, resolved=118, quarantined=0, missing=0,
    text_findings=9 pre-existing manual/status-number findings.
- `git diff --check`
  - result: pass.

## Review Status

- `/review` loop 1 harness must-fix findings: `--source-json` could write/check
  production reports from external files; blocked source tiers could validate a
  numeric source; Markdown omitted full artifact metadata.  Fixed by limiting
  `--source-json` to `--json`, removing `blocked` from accepted bound-source
  tiers, and adding Markdown covariance/input-hash coverage plus regression
  tests.
- `/review` loop 1 claim-gate must-fix findings: Chapter 6 still described all
  three CF4 versions as threshold-crossing, Chapter 8 said the table reports
  evidence under each version, and Chapter 9 retained an indirect numeric
  headline-shift claim.  Fixed with WFH2009-only legacy summary language and
  CF4++/Watkins unbound provenance language.
- `/review` loop 2 harness: approved; residual note that `--json --source-json`
  is diagnostic/probe output only, not production provenance.
- `/review` loop 2 claim gate: approved; applied the optional copy-edit to make
  the Chapter 8 sensitivity-spread sentence drier.

## Known Residuals

- Current CF4++ and Watkins legacy sensitivity values remain quarantined until a
  dedicated rerun binds variant observed inputs, likelihood settings, sampler
  settings, config hash, input hashes, command, output manifest, and
  null/covariance/PPC/LOOCV status.
- Existing generated PDF artifacts were not rebuilt in this PR; source TeX now
  removes the unbound CF4++/Watkins numeric sensitivity values from result-facing
  prose/table cells.
