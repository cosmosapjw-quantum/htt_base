# CF4 P0 blocked source record

No CF4 numerical replacement is authorized. This record blocks propagation only.

- Status: `QUARANTINED_OPEN_FINDINGS`
- Owner: `COMMON`
- Implementation scope: `propagation_quarantine_only`
- Claim tier: `blocked`
- Transfer source: `none`
- Config hash: `4c54afee9f3fbdf03b30e111fdf97e1c1fe95638120587a7557a48a11a821fe7`
- Inventory SHA-256: `3e1088e9dee36fba8b58574d30e54303958bb2c8d37b0d6594bd97d8fded8b1a`
- Remediation-root SHA-256: `bdb7779955710d3d84b137081748027746ea308fbf89dc0c179dd937f63c6311`
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

- `docs/research_program/long_horizon_rescue/cf4_p0_quarantine_policy.yaml:sha256:4c54afee9f3fbdf03b30e111fdf97e1c1fe95638120587a7557a48a11a821fe7`
- `docs/generated/cf4_p0_quarantine_inventory.json:sha256:3e1088e9dee36fba8b58574d30e54303958bb2c8d37b0d6594bd97d8fded8b1a`
- `docs/codex_handoff/research_remediation_state.yaml:sha256:bdb7779955710d3d84b137081748027746ea308fbf89dc0c179dd937f63c6311`

Generating command: `PYTHONPATH=htt/src venv/bin/python -B scripts/codex_harness/quarantine_cf4_p0_consumers.py --write`
