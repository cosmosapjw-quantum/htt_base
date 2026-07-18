# CF4 P0 blocked source record

No CF4 numerical replacement is authorized. This record blocks propagation only.

- Status: `QUARANTINED_OPEN_FINDINGS`
- Owner: `COMMON`
- Implementation scope: `propagation_quarantine_only`
- Claim tier: `blocked`
- Transfer source: `none`
- Config hash: `3b4eff6b07b9e3a6dfb67852bda4332541a446fcefa59c2ea95747d55e2f5ab6`
- Inventory SHA-256: `522af349ad2543c2bb1e99498fbfd5a5ca7133cc6bd081c3f854a7c55234bd6e`
- Remediation-root SHA-256: `f16d9754828bb32ae4cef92f585af82ae7fd1caa2687a7b4144bc1e942328dd9`
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

- `docs/research_program/long_horizon_rescue/cf4_p0_quarantine_policy.yaml:sha256:3b4eff6b07b9e3a6dfb67852bda4332541a446fcefa59c2ea95747d55e2f5ab6`
- `docs/generated/cf4_p0_quarantine_inventory.json:sha256:522af349ad2543c2bb1e99498fbfd5a5ca7133cc6bd081c3f854a7c55234bd6e`
- `docs/codex_handoff/research_remediation_state.yaml:sha256:f16d9754828bb32ae4cef92f585af82ae7fd1caa2687a7b4144bc1e942328dd9`

Generating command: `PYTHONPATH=htt/src venv/bin/python -B scripts/codex_harness/quarantine_cf4_p0_consumers.py --write`
