# PR-014 PR delta: transfer-provenance contract

## Goal

Add a COMMON transfer-provenance contract and registry so
transfer-dependent results can record source, family, valid range, observable
kind, normalization, calibration status, and caveats. External and future
native transfer specifications can coexist, but external transfer paths cannot
claim native validation.

This PR does not compute transfer functions, implement a native low-ell solver,
calibrate AniCLASS as native, generate result artifacts, or make morphology or
family claims.

## Evidence read

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-014 card
- `docs/codex_handoff/pr_status.yaml`
- `docs/codex_handoff/02_long_range_PR_backlog.md`
- `htt/src/common/contracts.py`
- `htt/workspace/contracts/atlas_entry_lite.py`
- `htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py`
- `tests/contracts/test_artifact_manifest.py`
- `tests/contracts/test_ownership_firewall.py`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-transfer-provenance/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`

## Web/doc checks

- WEB_CHECK_STATUS: done
- Python `dataclasses` documentation checked for frozen dataclasses and
  post-init validation behavior.
  URL: https://docs.python.org/3/library/dataclasses.html
- Python `enum` documentation checked for `StrEnum` behavior.
  URL: https://docs.python.org/3/library/enum.html
- Python standard type documentation checked for deterministic dictionary
  behavior used by the registry implementation.
  URL: https://docs.python.org/3/library/stdtypes.html#dict

## Role divergence

The five requested PR-014 subagent threads were spawned but all returned usage
limit errors before producing findings; they were closed immediately. The role
split below was simulated in the main thread from repository evidence.

- code_cartographer:
  - Steelman: add `common.transfer_registry` as the canonical schema and keep
    `workspace.contracts.transfer` as a thin alias.
  - Attack: do not put transfer policy in BASS, HTT, or MIO-specific modules
    before downstream adapters consume it.
- harness_engineer:
  - Steelman: add `tests/contracts/test_transfer_registry.py` with RED tests
    for required metadata, valid range, registry coexistence, duplicate IDs,
    and external/native validation gates.
  - Attack: checking only dataclass construction would miss raw result metadata
    spoofing, so `validate_transfer_dependent_result` needs its own tests.
- physics_stat_auditor:
  - Steelman: transfer provenance records the origin and domain of a transfer
    number without saying the number is native or physics-certified.
  - Attack: external/AniCLASS and empirical proxy paths must not pass native
    validation gates or claim native calibration.
- claim_gate_reviewer:
  - Steelman: safe vocabulary is transfer-conditional and explicit about
    external vs future native paths.
  - Attack: a future native source can be provisional or gate-passed only with
    explicit native validation gates; morphology-atlas readiness is separate.
- regression_tester:
  - Steelman: run focused PR-014 tests, ownership/artifact/common-schema
    adjacent tests, top-level contract tests, package/smoke/collect subsets,
    DAG validation, status mirror, claim scans, and staged whitespace checks.
  - Attack: smoke/package checks alone do not verify the transfer kill switch.

## Chosen plan

1. Add failing PR-014 tests under `tests/contracts/test_transfer_registry.py`.
2. Add `htt/src/common/transfer_registry.py` with enums, frozen
   `TransferValidRange`, frozen `TransferFunctionSpec`, `TransferRegistry`,
   and `validate_transfer_dependent_result`.
3. Add `htt/workspace/contracts/transfer.py` as a thin alias and export it
   from `workspace.contracts`.
4. Add `transfer.py` to the workspace common-schema barrier scan.
5. Record PR-014 completion in both status files and update handoff docs.

## Files changed

- `htt/src/common/transfer_registry.py`
- `htt/workspace/contracts/transfer.py`
- `htt/workspace/contracts/__init__.py`
- `htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py`
- `tests/contracts/test_transfer_registry.py`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/PR_DELTAS/pr-014-transfer-provenance-contract.md`
- `docs/harness/VALIDATION_LEDGER.md`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/CLAIM_LEDGER.md`
- `docs/harness/DECISION_LOG.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | ---: | --- |
| `venv/bin/python -m pytest tests/contracts/test_transfer_registry.py -q` before implementation | repo root | FAIL | Red phase: missing `common.transfer_registry`. |
| `venv/bin/python -m pytest tests/contracts/test_transfer_registry.py -q` after hardening valid-range metadata | repo root | PASS | `11 passed`; covers metadata, invalid domains, external/native kill switches, registry coexistence, duplicate IDs, raw result metadata, caveat shape, and workspace aliasing. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py tests/contracts/test_artifact_manifest.py htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py htt/src/common/test_ver2_contract_layer.py -q` | repo root | PASS | `32 passed`; ownership, manifest/native-transfer gates, workspace schema barrier, and common contract layer preserved. |
| `venv/bin/python -m py_compile htt/src/common/transfer_registry.py htt/workspace/contracts/transfer.py htt/workspace/contracts/__init__.py tests/contracts/test_transfer_registry.py htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py` | repo root | PASS | Touched Python files compile. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After status update: `12/62 = 19.35%`; dependency-weighted `24.62%`; critical path `5/21 = 23.81%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; packaging import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6888 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6835/6894 tests collected (59 deselected)`. |
| `venv/bin/python -m pytest tests/contracts -q` | repo root | PASS | `58 passed`; top-level contract suite remains green. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-014 files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-014 docs>` | repo root | PASS | No unmarked strong claims detected. |
| `git diff --cached --check` | repo root | PASS | Staged PR-014 diff has no whitespace errors. |

## Review findings and fixes

- Finding: raw metadata validation initially checked only field presence, not
  `valid_range` shape. Fix: `validate_transfer_dependent_result` reconstructs
  a `TransferValidRange` from metadata, so malformed domains fail.
- Finding: `TransferFunctionSpec` initially accepted a string as a caveat
  sequence. Fix: string/bytes caveats are rejected and tests cover it.
- Finding: external transfers could have been blocked in the dataclass but
  spoofed in raw metadata. Fix: raw metadata validation repeats the external
  native-validation kill switch.
- Finding: the workspace alias was not part of the schema-barrier scan. Fix:
  `transfer.py` is included in `test_ver2_common_schema_barrier.py`.

## Claim hygiene and scientific scope

Numerical/scientific impact: none; this is metadata/contract plumbing only.

Artifact/claim-tier impact: COMMON L2 transfer-provenance contract metadata.
PR-014 records transfer provenance and validation state for later result
consumers. It does not add solver outputs, native transfer validation,
AniCLASS-native calibration, HTT posterior/evidence validation, MIO
diagnostic certification, null/mock/covariance evidence, sky-support evidence,
morphology compatibility evidence, or family-ID evidence.

## Residual risks

- PR-014 defines the canonical transfer spec and registry but does not migrate
  all transfer-dependent producers to emit it. Downstream PR-080 and related
  adapter work should attach `TransferFunctionSpec` to concrete paths.
- The registry is an in-memory contract helper. It does not yet write generated
  transfer registry artifacts or sensitivity reports.
