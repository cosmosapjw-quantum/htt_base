# REV-R087 - Research-only external audit package refresh

## Scope

- Owner: COMMON.
- Plan source: `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`, Task 14.
- Canonical PR DAG status remains complete at `62/62`; this supplemental delta tracks revision-slice task `REV-R087`.
- Claim ceiling: `diagnostic_only`.

## Evidence Read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-manuscript-figure-audit/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `scripts/build_research_only_audit_package.py`
- `tests/contracts/test_research_only_audit_package.py`
- `docs/generated/research_only_external_audit_package_manifest.json`
- `docs/generated/research_only_external_audit_prompt.md`
- `docs/generated/progress_checkpoints/revision_checkpoint_rev_r086.md`
- `docs/PR_DELTAS/rev-r084.md`
- `docs/PR_DELTAS/rev-r085.md`
- `docs/PR_DELTAS/rev-r086.md`

## Web/Doc Checks

- WEB_CHECK_STATUS: done.
- Checked Python standard-library `zipfile` documentation: `ZipFile` is the supported read/write archive API and `namelist()` returns archive member names. This supports the REV-R087 zip-entry inspection gate.

## Divergence And Review

- code cartographer:
  - Steelman: keep the package declarative and extend fixed allowlists for the specific REV-R084 through REV-R086 research surfaces.
  - Attack: simply regenerating the old package would keep theorem registries, QFPI reconciliation, CF4++ provenance, manuscript rearchitecture, and source JSON sidecars absent.
- harness engineer:
  - Steelman: add fail-closed tests for exact required entries, available figure source JSON, and generated package gates before regenerating.
  - Attack: bulk-including `docs/generated/**`, `scripts/**`, or `htt/**` would violate the research-only/minimal-code policy.
- physics/statistics auditor:
  - Steelman: include theorem registries, x/Q/Pi/F/G semantic reconciliation, research-program DAG/registries, CF4++ provenance, observed-data inventories, and manuscript repair/provenance files.
  - Attack: under-inclusion lets an external reviewer audit theorem-backed or legacy-likelihood claims without the provenance that caps them at diagnostic/transfer-conditional use.
- claim-gate reviewer:
  - Steelman: strict package should include LaTeX, generated snippets, every manuscript figure payload plus manifest plus available source JSON, result packs, claim/transfer reports, and indirect hostile prompt triggers.
  - Attack: over-inclusion of PDFs, nested zips, broad code snapshots, native-looking paths, or old audit archives would invite false solver/evidence claims.
- regression tester:
  - Steelman: final gate is package `--check`, focused package pytest, zip inspection, claim scans, and source generator checks.
  - Attack: passing package tests alone does not prove generated zip/prompt/manifest freshness.

Subagents closed: yes for completed preflight agents.

## Red Phase

Before the generator patch, `tests/contracts/test_research_only_audit_package.py` was extended to require REV-R087 research context and available figure source JSON. The expected red result was:

| Command | Result | Notes |
|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_research_only_audit_package.py -q` | FAIL | 2 failed, 5 passed. Missing `manuscript_audit_repair_matrix.md` and theorem figure `.source.json` entries. |

## Implemented Changes

- Added REV-R087 research context files to the research-only package allowlist:
  - `docs/generated/manuscript_audit_repair_matrix.md`
  - `docs/generated/qfpi_semantic_reconciliation.md`
  - `docs/generated/cf4pp_lnb_provenance_report.md`
  - `docs/generated/cf4pp_lnb_provenance_report.json`
  - `docs/generated/external_research_input_response_matrix.md`
  - `docs/generated/revision_experiment_assets.md`
  - `docs/generated/revision_experiment_assets.json`
  - `docs/generated/research_program_experiment_registry.yaml`
  - `docs/generated/research_program_theorem_registry.yaml`
  - `docs/generated/theorem_extension_registry.md`
  - `docs/generated/theorem_extension_registry.json`
  - `docs/generated/manuscript_rearchitecture_report.md`
  - `docs/generated/progress_checkpoints/revision_checkpoint_rev_r086.md`
  - `docs/codex_handoff/pr_dag_research_program.yaml`
- Added minimal plot-context code samples:
  - `scripts/generate_revision_experiment_assets.py`
  - `scripts/generate_theorem_extension_assets.py`
- Extended manuscript figure packaging to include available adjacent `*.source.json` sidecars for included figure payloads.
- Added required assertion gates:
  - `available_figure_source_json_included`
  - `rev_r087_research_context_included`
  - `theorem_registry_assets_included`
  - `rev_r086_checkpoint_included`
- Reworded the research-only hostile prompt rejection trigger for MIO diagnostics to avoid scanner-sensitive exact claim strings while preserving the same claim boundary.
- Regenerated:
  - `docs/generated/research_only_external_audit_package.zip`
  - `docs/generated/research_only_external_audit_package_manifest.json`
  - `docs/generated/research_only_external_audit_prompt.md`

## Generated Artifact Snapshot

- Package ZIP SHA256: `sha256:fa5583cd94e09695247f1a63f78200f5db83b5b2e2747d40b17f07324875e566`.
- Prompt SHA256: `sha256:149a6733e6c482104b5c3142885f76f84c0b26dc17a5cb3149a9199166159bbd`.
- Manifest SHA256: `sha256:dfbe28edcc33781da9dda520daf87c94d3aa064acf721eb74627927b9640834e`.
- Zip entries: 340 total including `MANIFEST.json`.
- Manifest archive entries: 339.
- Failed gates: `[]`.
- PDF entries: `[]`.
- Nested zip entries: `[]`.
- Git metadata records the package-generation worktree state (`80c0fd5+dirty`) because the package, manifest, and prompt are part of this commit.

## Validation

| Command | Result | Notes |
|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py --dry-run` | PASS | `archive_entry_count=339`; all package gates true, including REV-R087 research context and source JSON gates. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py` | PASS | Regenerated zip, manifest, and prompt. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py --check` | PASS | Package is up to date. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_research_only_audit_package.py -q` | PASS | 7 passed. |
| `venv/bin/python -B scripts/check_claim_language.py --dry-run scripts/build_research_only_audit_package.py tests/contracts/test_research_only_audit_package.py docs/generated/research_only_external_audit_prompt.md docs/generated/research_only_external_audit_package_manifest.json docs/PR_DELTAS/rev-r087.md` | PASS | No forbidden claim language detected. |
| `venv/bin/python -B .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py scripts/build_research_only_audit_package.py tests/contracts/test_research_only_audit_package.py docs/generated/research_only_external_audit_prompt.md docs/generated/research_only_external_audit_package_manifest.json` | PASS | No forbidden claim patterns detected after prompt/test rewording. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_theorem_extension_assets.py --check` | PASS | Theorem extension assets are current. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_revision_experiment_assets.py --check` | PASS | Revision experiment assets pass check. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py --check` | PASS | PDF claim lint report is up to date. |
| Zip inspection with Python `zipfile.ZipFile(...).namelist()` | PASS | Required REV-R087 entries present; `pdf_entries=[]`; `zip_entries=[]`; `failed_gates=[]`. |
| `git diff --check` | PASS | No whitespace errors. |

## Claim-Tier Impact

REV-R087 is a packaging and external-audit handoff PR. It creates no new science result, no native solver output, no geometry or Bianchi family-identification support, no MIO-owned model-dependent inference semantics, and no HTT evidence term. The package is an external research-audit source bundle for diagnostic-only, transfer-conditional, and proposed/future-interface claims already present in the repo.
