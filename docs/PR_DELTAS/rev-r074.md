# REV-R074 Delta: External Research Input Intake

owner: COMMON
implementation_scope: external_research_input_intake
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `venv/bin/python scripts/inventory_external_research_inputs.py --write`
git_commit_or_worktree_state: 528b64b+dirty; uploaded root inputs hash-bound from working tree

## Evidence Read

- `AGENTS.md` operating contract supplied in-session.
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `scripts/generate_revision_research_program.py`
- `tests/contracts/test_revision_research_program.py`
- `scripts/inventory_revision_program_packages.py`
- `tests/contracts/test_revision_program_inventory.py`
- Root inputs: `RESEARCH_AUDIT_REPORT.md`, `publishable_data_analysis_program.zip`, `htt_publishable_novel_analysis_program_2026-06-19.zip`, `htt_beyond_mes_egs_theorem_program_2026-06-19.zip`, `egs_theorem_program.zip`
- DAG commands reported the canonical PR DAG valid and complete: `62/62`, no unblocked next PR.
- Web search was not used; this intake depends on local uploaded files and repository-local generator style, not live external API or package semantics.

## Role Split

- Code mapper steelman: mirror the existing deterministic generator/check pattern rather than creating a broad audit-package builder. Objection handled: include archive copies as check artifacts so the inventory is not just metadata.
- Harness engineer steelman: make `--check` fail on stale JSON, Markdown, response matrix, or copied inputs. Objection handled: add a stale-output unit test using monkeypatched paths.
- Physics/statistics auditor steelman: treat the uploaded theorem and analysis bundles as proposal material only. Objection handled: response actions stay in P0/P1/P2 intake lanes with explicit kill-switches.
- Claim-gate reviewer steelman: retain the audit report's minor-revision signal without promoting evidence, transfer, or family claims. Objection handled: generated caveats state diagnostic/proposed scope, no native low-ell solver output, and no Bianchi family identification.

## Changes

- Added `scripts/inventory_external_research_inputs.py`.
- Added deterministic JSON and Markdown inventory outputs under `docs/audits/external_research_inputs_2026-06-20/`.
- Added `docs/audits/external_research_inputs_2026-06-20/ARCHIVE_MANIFEST.md` so raw copied inputs are visibly classified as external-input evidence, not repo-authored claims.
- Copied the five uploaded root inputs into `docs/audits/external_research_inputs_2026-06-20/` with SHA256 and size binding.
- Added canonical-source metadata, selected-document lists, supersession notes, and raw-external-input status for each input.
- Hardened archive copy behavior to reject symlink destinations and write hash-stale archive copies through an atomic temporary file.
- Generated `docs/generated/external_research_input_response_matrix.md` with prioritized actions:
  - audit minor revisions,
  - formalism harmonization,
  - CF4++ traceability,
  - local/global joint rest-frame program,
  - finite mock/rank/Fisher/null/PPC plan,
  - theorem program P0/P1/P2 with kill-switches.
- Added `tests/contracts/test_external_research_input_inventory.py` for check mode, hashes, archive copies, zip entries, response-matrix tokens, stale-output failure, and claim-language avoidance.

## Generated Artifacts

- `docs/audits/external_research_inputs_2026-06-20/input_inventory.json`: `sha256:640ac04449c73b405c8703a6b6ecee68e8d072d588531d485a688681bd3af0dc`
- `docs/audits/external_research_inputs_2026-06-20/input_inventory.md`: `sha256:c043e003eeb453e6aa2de07ee773582bf9156f145935ee3c051c5c8839d5211f`
- `docs/generated/external_research_input_response_matrix.md`: `sha256:d0b5860d8f7657ba7bbb4e498c1821a1e3de0584d1249a9d7c9286c0258cb8ac`
- `docs/audits/external_research_inputs_2026-06-20/ARCHIVE_MANIFEST.md`: `sha256:7e15329f91e08201f683e8c2c87a6e72cc1281eb5a54e096641b6b2716a7c68d`
- Archived input hashes are listed in `input_inventory.json` and `input_inventory.md`.

## Validation

- `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` -> pass, `62 PRs, DAG valid`.
- `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` -> pass, `Completed 62/62 = 100.0%`.
- TDD red: `venv/bin/python -m pytest -q tests/contracts/test_external_research_input_inventory.py` -> expected fail before implementation because the new script and generated outputs were missing.
- `venv/bin/python scripts/inventory_external_research_inputs.py --write` -> pass.
- `venv/bin/python scripts/inventory_external_research_inputs.py --check` -> pass.
- `python -m py_compile scripts/inventory_external_research_inputs.py` -> pass.
- `venv/bin/python -m pytest -q tests/contracts/test_external_research_input_inventory.py` -> `6 passed`.
- `venv/bin/python scripts/check_claim_language.py docs/generated/external_research_input_response_matrix.md docs/audits/external_research_inputs_2026-06-20/input_inventory.md docs/audits/external_research_inputs_2026-06-20/ARCHIVE_MANIFEST.md docs/PR_DELTAS/rev-r074.md` -> pass, no forbidden claim language detected.

## Claim Audit

| Claim | Owner | Status | Evidence | Risk | Required fix |
|---|---|---|---|---|---|
| Uploaded inputs are inventoried and archived | COMMON | IMPLEMENTED | script/test/artifact | stale archive copies could drift | `--check` fails on missing or hash-stale copies |
| Response matrix lists next actions | COMMON | SPECIFIED | generated Markdown | action rows could be mistaken for validation | caveats keep rows diagnostic/proposed |
| Theorem program rows are usable work items | physics_audit/COMMON | PROPOSED | uploaded proposal bundles | theorem text could over-promote | P0/P1/P2 kill-switches block promotion without proof review |
| Local/global program is a candidate lane | HTT/obsstat | PROPOSED | uploaded proposal bundle | rest-frame forecast could read as closed inference | response matrix keeps matched-null/covariance/PPC gates explicit |

## Residual Risks

- The root uploaded inputs remain untracked outside the owned path set; this PR archives hash-bound copies under the owned audit directory.
- The inventory records zip structure and hashes only; it does not execute code inside uploaded bundles.
- No manuscript text, solver code, inference code, or canonical DAG status file was changed.
- No native low-ell solver output, matched observed-data null stack, PPC, LOOCV, or family-equivalence gate was added.

## Subagent Closure

- Simulated code mapper, harness engineer, physics/statistics auditor, and claim-gate reviewer roles are closed for REV-R074.
