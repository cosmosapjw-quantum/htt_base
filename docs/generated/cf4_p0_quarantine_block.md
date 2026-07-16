# CF4 P0 blocked source record

No CF4 numerical replacement is authorized. This record blocks propagation only.

- Status: `QUARANTINED_OPEN_FINDINGS`
- Owner: `COMMON`
- Implementation scope: `propagation_quarantine_only`
- Claim tier: `blocked`
- Transfer source: `none`
- Config hash: `a6ebc87d0ea2008427c9663fca118c8a9fb2ce6a839191cd8274f5dab349a165`
- Inventory SHA-256: `91d2b4dbeb189c3a143ff6f4bf74fcaef243dfb91be8974d2b710a0dc37c1bae`
- Remediation-root SHA-256: `77d36878315f041c7bb6c273a2d650f7d3fa1c8a8dc635a577527d646fa40109`
- Sky support: `not_applicable_to_propagation_quarantine`
- Null/mock status: `not_applicable_quarantine_is_not_validation`
- Git/worktree state: `baseline_commit:e6da3670043596efdcd93f9ba5e631e1462146c7; PR-120 worktree hashes are bound by the canonical inventory`

| Finding | Severity | Scientific status | Ceiling |
|---|---|---|---|
| `C1-K5-MV-F1` | `P0` | `OPEN` | `blocked` |
| `C3-K5-VCORR-ML-F1` | `P0` | `OPEN` | `blocked` |
| `N-DATA-CF4-DOWNSTREAM` | `P1` | `OPEN` | `blocked` |

## Caveats

- Quarantine is propagation control, not scientific remediation or validation.
- All three findings remain OPEN; zero stale active consumers does not close them.
- No audit sensitivity or alternative number is a replacement result.
- Historical audits and frozen external packages remain immutable evidence.
- PR4/NPIPE download, reduction, and analysis remain skipped by user scope.

## Input hashes

- `docs/research_program/long_horizon_rescue/cf4_p0_quarantine_policy.yaml:sha256:a6ebc87d0ea2008427c9663fca118c8a9fb2ce6a839191cd8274f5dab349a165`
- `docs/generated/cf4_p0_quarantine_inventory.json:sha256:91d2b4dbeb189c3a143ff6f4bf74fcaef243dfb91be8974d2b710a0dc37c1bae`
- `docs/codex_handoff/research_remediation_state.yaml:sha256:77d36878315f041c7bb6c273a2d650f7d3fa1c8a8dc635a577527d646fa40109`

Generating command: `PYTHONPATH=htt/src venv/bin/python -B scripts/codex_harness/quarantine_cf4_p0_consumers.py --write`
