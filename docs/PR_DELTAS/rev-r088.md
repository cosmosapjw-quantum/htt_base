# REV-R088 - Strict Research Re-Audit Intake

owner: COMMON
implementation_scope: external_research_input_intake
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R088 archive copy and response matrix`
git_commit_or_worktree_state: working-tree input snapshot hash-bound during REV-R088

## Evidence Read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md`
- `audit_ver2.md` external strict re-audit input
- `RESEARCH_AUDIT_REPORT.md` external near-pass re-audit input
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- Prior intake style: `docs/PR_DELTAS/rev-r074.md`
- Web/docs check: pytest's official cache documentation confirms the internal cache plugin is enabled by default and can be disabled by plugin name `cacheprovider`, matching the focused test command's `-p no:cacheprovider` usage: <https://docs.pytest.org/en/stable/how-to/cache.html>.

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR starts a supplemental `REV-R088+` research-hardening slice because the new inputs are post-canonical external audit findings. The stricter re-audit controls conflict resolution; the near-pass report is retained only for quick wording and hygiene fixes.

## Role Split

- Code cartographer steelman: mirror the existing external-input archive style from REV-R074. Attack: do not create a broad package refresh in this intake PR.
- Harness engineer steelman: make the matrix test assert F1-F4 policies, archive hashes, category coverage, and markdown claim boundary. Attack: weak prose-only archive would let strict blockers drift.
- Physics/statistics auditor steelman: the strict audit must dominate because it blocks source identification, frame identity, scalar occupancy, and prior/error-budget claims. Attack: near-pass positive-evidence summaries are unsafe as a planning baseline.
- Claim-gate reviewer steelman: matrix rows must be diagnostic planning rows only. Attack: avoid wording that could read as native output, geometry support, family support, MIO evidence, or publication readiness; category names must route work without implying certification.

## Changes

- Archived strict and near-pass re-audit inputs under `docs/audits/external_research_inputs_2026-06-20_reaudit/`.
- Archived the repo-authored execution plan under the same folder for hash-bound traceability.
- Added `ARCHIVE_MANIFEST.md` and `input_inventory.md`.
- Added `docs/generated/audit_ver2_response_matrix.json`.
- Added `docs/generated/audit_ver2_response_matrix.md`.
- Added `tests/contracts/test_audit_ver2_response_matrix.py`.
- Used `minor_repair_from_near_pass_audit` and `defensible_boundary_statement` categories instead of near-pass approval or safe-claim certification labels.

## Artifact Metadata

- owner: COMMON
- implementation_scope: external_research_input_intake
- claim_tier: diagnostic_only
- transfer_source: none
- config_hash: `sha256:4e7afaf16c97c5d1aeb174238c7ac9ef3cd19038fb0a0fb7a7730353cf4fd163`
- input_hashes:
  - `docs/audits/external_research_inputs_2026-06-20_reaudit/audit_ver2.md:sha256:4c7cda3a41ea58c15d6382be7a523c57c2a2b0314250a2c78beada7bff515ddb`
  - `docs/audits/external_research_inputs_2026-06-20_reaudit/RESEARCH_AUDIT_REPORT.md:sha256:08c30c1df76a7808bfcbc31959d33660f10a45aaba2735935ed4ee1daa665b2d`
  - `docs/audits/external_research_inputs_2026-06-20_reaudit/2026-06-20-audit-ver2-research-hardening.md:sha256:18f1b0b3886af572ea3ad4282a4197d9735fc37360455cba289d6c0baa1298c1`
- sky_support_status: not_directional
- null_mock_status: not_statistical
- caveats:
  - response matrix only
  - no scientific result promoted
  - canonical PR DAG not rewritten
  - no native low-ell morphology atlas present

## TDD Red

`venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_audit_ver2_response_matrix.py -q` failed before implementation with five missing-artifact failures for `audit_ver2_response_matrix.json`, `audit_ver2_response_matrix.md`, and the re-audit archive manifest.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_audit_ver2_response_matrix.py -q` | PASS | `5 passed in 0.03s`; matrix/archive contract. |
| `venv/bin/python -B scripts/check_claim_language.py --dry-run docs/generated/audit_ver2_response_matrix.md docs/generated/audit_ver2_response_matrix.json docs/audits/external_research_inputs_2026-06-20_reaudit/ARCHIVE_MANIFEST.md docs/audits/external_research_inputs_2026-06-20_reaudit/input_inventory.md docs/PR_DELTAS/rev-r088.md --format json` | PASS | `issue_count=0`; raw external audit text intentionally excluded from production-language scan. |
| `venv/bin/python -B .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py docs/generated/audit_ver2_response_matrix.md docs/generated/audit_ver2_response_matrix.json docs/audits/external_research_inputs_2026-06-20_reaudit/ARCHIVE_MANIFEST.md docs/audits/external_research_inputs_2026-06-20_reaudit/input_inventory.md docs/PR_DELTAS/rev-r088.md` | PASS | No forbidden claim patterns detected. |
| `venv/bin/python -B .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py docs/generated/audit_ver2_response_matrix.md docs/generated/audit_ver2_response_matrix.json docs/audits/external_research_inputs_2026-06-20_reaudit/ARCHIVE_MANIFEST.md docs/audits/external_research_inputs_2026-06-20_reaudit/input_inventory.md docs/PR_DELTAS/rev-r088.md` | PASS | No unmarked strong claims detected. |
| `venv/bin/python -B -m json.tool docs/generated/audit_ver2_response_matrix.json >/tmp/audit_ver2_response_matrix.pretty.json && git diff --check` | PASS | JSON parses; whitespace check clean. |
| `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | PASS | Canonical DAG still valid. |
| `venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` | PASS | Canonical DAG remains `62/62`, unblocked next none. |

## Review Loop

- Loop 1 finding: claim-gate review flagged `near_pass_quick_fix` and `safe_claim` as labels that could imply external-audit approval or scientific certification.
- Patch: replaced them with `minor_repair_from_near_pass_audit` and `defensible_boundary_statement` in JSON, Markdown, and the focused test.
- Revalidation: focused pytest, claim-language scan, claim-provenance scans, JSON parse, and diff check passed.

## Claim Audit

| Claim | Owner | Status | Evidence | Risk | Required fix |
| --- | --- | --- | --- | --- | --- |
| Strict external re-audit inputs are archived | COMMON | IMPLEMENTED | hash-bound files | source files could drift if root copies are used | use archive copies in downstream PRs |
| F1-F4 strict blockers control the supplemental DAG | COMMON | SPECIFIED | response matrix | could be mistaken for completed fixes | every row points to future REV task and blocked status |
| Near-pass report contributes quick fixes only | COMMON | SPECIFIED | response matrix | could reintroduce positive evidence framing | strict audit controls conflicts |

## Residual Risks

- This PR does not fix manuscript/result-pack claims; it only stages the strict response matrix.
- This PR does not add new nulls, covariance, PPC, LOOCV, prior-sensitivity runs, frame derivations, or native atlas support.
- Downstream PRs must not promote any strict blocker before its named gate passes.

## Subagent Closure

REV-R088 preflight subagents were spawned for code cartography, harness, physics/statistics, and claim-gate review. Their findings were incorporated before commit and their threads were closed.
