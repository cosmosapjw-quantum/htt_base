# VER2 Hostile Audit Runbooks

## Purpose

These runbooks keep hostile audit categories explicit and separated:

- baseline reproduction
- adversarial edge
- physics sanity
- numerical stability
- regression

## Runbooks

### `runbook.observable_promotion`

- baseline: `recover_flrw_limit`
- adversarial: `proxy_not_promoted_as_biposh`, `rank_failure_not_spun_as_signal`
- physics: `diagonal_only_not_sufficient`, `no_claim_conditions_explicit`
- numerical: `psd_guard_present`, `scan_volume_hash_recorded`
- regression: `observable_manifest_owner_scope`
- quarantine: `sparse_proxy_only`, `response_rank_deficient`

### `runbook.semantic_firewall`

- baseline: `q_f_separation_preserved`
- adversarial: `local_boost_not_global_tilt`, `tsc_not_posterior`
- physics: `certified_f_requires_admissible_ceiling`
- numerical: `manuscript_blocking_fail_semantics`
- regression: `workspace_schema_barrier`
- quarantine: `claim_gate_not_passed`, `posterior_correction_attempted`

## Check command

```bash
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_hostile_audit.py --check
```
