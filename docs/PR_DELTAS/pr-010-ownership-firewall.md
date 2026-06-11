# PR-010 PR delta: canonical ownership and role firewall

## Goal

Add machine-checkable owner, claim-tier, implementation-scope, and bundle-role
contracts for the active `codex_handoff` DAG. The change introduces canonical
`COMMON`, `HTT`, `MIO`, `BASS`, `OBSSTAT`, and `TSC_LEGACY` ownership while
normalizing legacy `TSC`/`tsc` inputs at canonical contract boundaries.

This is COMMON L2 contract infrastructure. It does not implement inference,
MIO diagnostics, transfer generation, observable extraction, or a native
low-ell solver.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-010 card
- `htt/src/common/contracts.py`
- `htt/src/common/test_contracts.py`
- `htt/src/common/test_ver2_contract_layer.py`
- `htt/workspace/contracts/validation_registry.py`
- `htt/workspace/contracts/__init__.py`
- `htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py`
- `htt/workspace/contracts/tests/test_g19_enforcement.py`
- legacy workspace contract tests for atlas, forward output, HTT-to-MIO, and
  MIO certificate dataclasses

## Web/doc checks

- WEB_CHECK_STATUS: done
- Python `enum` documentation checked for `StrEnum` string-compatible enum
  behavior.
  URL: https://docs.python.org/3/library/enum.html
- Python `dataclasses` documentation checked for frozen dataclass contract
  behavior.
  URL: https://docs.python.org/3/library/dataclasses.html

## Subagent divergence

- code_cartographer:
  - Steelman: add canonical enums and helpers in `common.contracts`, with
    `workspace/contracts/ownership.py` as a thin facade.
  - Attack: a repo-wide migration from legacy `TSC` strings would break
    existing TSC-local manifest checks and is larger than PR-010.
- harness_engineer:
  - Steelman: TDD should pin enum membership, string compatibility, legacy
    normalization, MIO/HTT bundle-role rejection, and workspace facade imports.
  - Attack: tests must include existing common/workspace contract suites, not
    only the new file.
- physics_stat_auditor:
  - Steelman: owner roles are schema/firewall metadata only.
  - Attack: no owner enum or bundle gate may imply solver readiness, transfer
    calibration, MIO posterior ownership, HTT certificate ownership, or family
    identification.
- claim_gate_reviewer:
  - Steelman: safe language is canonical ownership and role-firewall
    infrastructure.
  - Attack: avoid turning smoke/contract tests into scientific readiness or
    publication-grade evidence.
- regression_tester:
  - Steelman: regression matrix must include existing dataclasses that compare
    manifests to legacy strings.
  - Attack: the workspace facade must re-export common schema rather than
    redefine owner names.

## Chosen plan

1. Add failing PR-010 contract tests under `tests/contracts/`.
2. Replace `Literal` aliases for `Owner`, `ClaimTier`, and
   `ImplementationScope` with `StrEnum` classes in `common.contracts`.
3. Add `BundleKind`, normalization helpers, `owner_can_emit_bundle`, and
   `assert_owner_can_emit_bundle`.
4. Keep dataclass validators string-compatible and keep legacy `"TSC"` accepted
   for existing artifacts, while storing canonical contract rows as
   `Owner.TSC_LEGACY` / `ImplementationScope.TSC_LEGACY`.
5. Align `workspace/contracts/validation_registry.py` with the canonical common
   owner and implementation-scope vocabulary.
6. Add `workspace/contracts/ownership.py` as a thin facade over the canonical
   common schema.
7. Run the new PR-card test and existing common/workspace compatibility suites.

## Files changed

- `htt/src/common/contracts.py`
- `htt/workspace/contracts/validation_registry.py`
- `htt/workspace/contracts/ownership.py`
- `tests/contracts/test_ownership_firewall.py`
- `htt/src/common/test_ver2_contract_layer.py`
- `htt/tsc/test_ver2_tsc_contracts.py`
- `htt/tsc/reports/test_overlay_builder.py`
- `htt/tsc/adapters/test_preliminary_results.py`
- `htt/workspace/contracts/tests/test_preliminary_results.py`
- `htt/mio/tests/test_preliminary_results_bridge.py`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/PR_DELTAS/pr-010-ownership-firewall.md`
- `docs/harness/VALIDATION_LEDGER.md`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py -q` before implementation | repo root | FAIL | Red phase: `BundleKind` and ownership firewall API were missing. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py -q` after reviewer regression tests | repo root | FAIL | Red phase: canonical dataclasses preserved raw `TSC`, and the validation registry still exported active `TSC`/`tsc`. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py -q` | repo root | PASS | `9 passed`; covers enum membership, string compatibility, canonical TSC_LEGACY normalization, validation-registry vocabulary, role gates, and workspace facade. |
| `venv/bin/python -m pytest htt/src/common/test_contracts.py htt/src/common/test_ver2_contract_layer.py -q` | repo root | PASS | `32 passed`; legacy common contracts remain compatible with canonical TSC_LEGACY storage. |
| `venv/bin/python -m pytest htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py htt/workspace/contracts/tests/test_g19_enforcement.py -q` | repo root | PASS | `8 passed`; workspace schema barrier and G19 separation still hold. |
| `venv/bin/python -m pytest htt/workspace/contracts/tests/test_htt_to_mio_roundtrip.py htt/workspace/contracts/tests/test_mio_certificate.py htt/workspace/contracts/tests/test_htt_forward_output.py htt/workspace/contracts/tests/test_atlas_entry.py -q` | repo root | PASS | `23 passed`; legacy string-manifest dataclasses remain compatible. |
| `venv/bin/python -m pytest htt/tsc/test_ver2_tsc_contracts.py htt/tsc/reports/test_overlay_builder.py htt/tsc/adapters/test_preliminary_results.py -q` | repo root | PASS | `12 passed`; TSC overlays still load and now expose canonical legacy owner. |
| `venv/bin/python -m pytest htt/tsc/adapters/test_bass_runtime.py htt/tsc/adapters/test_htt_inference.py htt/tsc/adapters/test_mio_certificate.py htt/tsc/admissibility/test_domain.py htt/tsc/residuals/test_observable_bridge.py htt/tsc/budget/test_source_to_channel.py htt/tsc/integration/test_active_service.py htt/tsc/source/test_thomson_bridge.py -q` | repo root | PASS | `39 passed`; legacy TSC builder fixtures normalize without breaking advisory outputs. |
| `venv/bin/python -m pytest htt/mio/tests/test_predictive_residuals_shared_schema.py htt/mio/tests/test_mio_certificate_generator.py -q` | repo root | PASS | `19 passed`; MIO bridge/certificate fixtures remain compatible. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py htt/src/common/test_contracts.py htt/src/common/test_ver2_contract_layer.py htt/workspace/contracts/tests/test_ver2_common_schema_barrier.py htt/workspace/contracts/tests/test_g19_enforcement.py htt/workspace/contracts/tests/test_ver2_validation_registry.py htt/workspace/contracts/tests/test_preliminary_results.py htt/mio/tests/test_preliminary_results_bridge.py -q` | repo root | PASS | `74 passed`; combined ownership, validation-registry, preliminary-result bridge suite. |
| `venv/bin/python -m pytest htt/tsc/test_ver2_tsc_contracts.py htt/tsc/reports/test_overlay_builder.py htt/tsc/adapters/test_preliminary_results.py htt/tsc/adapters/test_bass_runtime.py htt/tsc/adapters/test_htt_inference.py htt/tsc/adapters/test_mio_certificate.py htt/tsc/admissibility/test_domain.py htt/tsc/residuals/test_observable_bridge.py htt/tsc/budget/test_source_to_channel.py htt/tsc/integration/test_active_service.py htt/tsc/source/test_thomson_bridge.py htt/mio/tests/test_predictive_residuals_shared_schema.py htt/mio/tests/test_mio_certificate_generator.py -q` | repo root | PASS | `70 passed`; combined TSC/MIO compatibility slice. |
| `venv/bin/python -m py_compile htt/src/common/contracts.py htt/workspace/contracts/validation_registry.py htt/workspace/contracts/ownership.py` | repo root | PASS | Touched Python modules compile. |
| Inline `venv/bin/python` StrEnum/asdict/json smoke | repo root | PASS | `ArtifactManifest(owner="TSC", implementation_scope="tsc")` stores canonical enum fields and JSON-serializes to strings. |
| `git diff --check -- <PR-010 files>` | repo root | PASS | No whitespace errors in scoped PR-010 diff. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | `8/62 = 12.90%`; dependency-weighted `14.87%`; critical-path `4/21 = 19.05%`; checkpoint not due; next candidates `PR-021`, `PR-011`, `PR-013`, `PR-014`. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-010 docs> && python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-010 docs>` | repo root | PASS | No forbidden claim patterns or unmarked strong claims detected. |

## Review findings and fixes

- Finding: broad coercion of every legacy `TSC` manifest to the new enum would
  break existing TSC-local owner checks unless those checks use canonical
  ownership. Fix: `ArtifactManifest`, `StatusSnapshotEntry`, and
  `ClaimLedgerEntry` normalize legacy TSC inputs at construction, and TSC report
  owner checks now require `Owner.TSC_LEGACY`.
- Finding: `workspace/contracts/validation_registry.py` still carried a
  separate owner/scope vocabulary and a default `owner="TSC"`,
  `implementation_scope="tsc"` row. Fix: the registry imports the canonical
  common vocabulary and stores the TSC theorem row as `TSC_LEGACY` /
  `tsc_legacy`.
- Finding: workspace contracts must not redefine common schema names. Fix:
  `workspace/contracts/ownership.py` re-exports common schema directly.
- Finding: MIO and HTT role misuse needs a concrete gate, not only vocabulary.
  Fix: add `BundleKind` with `owner_can_emit_bundle` and
  `assert_owner_can_emit_bundle`.

## Claim hygiene and scientific scope

Numerical/scientific impact: none; schema and role-firewall code only.

Artifact/claim-tier impact: COMMON L2 contract metadata. The new ownership
firewall separates HTT posterior bundles from MIO diagnostic certificates and
keeps TSC as legacy reproduction scope. It does not validate native solver
behavior, transfer calibration, HTT posterior/evidence content, MIO diagnostic
adequacy, null/mask/covariance adequacy, morphology compatibility, or
family-identification evidence.

## Residual risks

- Existing legacy artifacts still carry string owners; that is intentional for
  reproducibility and should be migrated in dedicated TSC-legacy PRs.
- `ImplementationScope.BASS_NATIVE` preserves the existing
  `canonical_BASS` string value for compatibility.
