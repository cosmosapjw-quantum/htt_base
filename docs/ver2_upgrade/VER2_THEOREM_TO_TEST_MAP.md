# VER2 Theorem-To-Test Map

## Status

- Authority: `docs/ver2_upgrade/*`
- Packet owner: `IM-08V`
- Registry source of truth: `htt/workspace/contracts/validation_registry.py`
- Current phase state: executable minimal campaign set active; planned placeholder tests were replaced with live repo-relative test entrypoints.

## Core entries

| Theorem ID | Owner | Guard | Primary linked tests | Explicit no-claim conditions |
|---|---|---|---|---|
| `V8_isotropic_limit_recovery` | `BASS` | anisotropic outputs must recover the isotropic null before promotion | `flrw_limit_zero_offdiag`, `type_i_observable_marks_isotropic_null_proxy` | `missing_observable_vector`, `sparse_proxy_only` |
| `V8_biposh_Lgt0_null_or_proxy_block` | `BASS` | proxy sparse morphology may not be promoted as invariant BiPoSH evidence | `rotating_types_activate_offdiag_blocks`, `proxy_mode_records_no_claim` | `sparse_mode_block_proxy`, `missing_biposh_basis` |
| `V8_template_injection_recovery` | `HTT` | injection claims require declared null/injection manifests | `injected_dipole_projection_recovered`, `synthetic_injection_coverage_reaches_nominal_band` | `missing_injection_campaign`, `missing_scan_volume` |
| `V8_mes_rank_no_claim` | `BASS` | rank-deficient covariance upgrades are explicit no-claim outputs | `mes_rank_failure_returns_no_claim`, `full_cov_contract_rejects_negative_rank` | `response_rank_deficient`, `missing_covariance_features` |
| `V8_filling_requires_certification` | `COMMON` | uncertified normalized scores remain `Q`, not certified `F` | `uncertified_f_downgrades_to_proxy`, `mock_coverage_within_published_window` | `claim_gate_not_passed`, `occupancy_not_certified` |
| `V8_local_vs_global_discrimination` | `HTT` | local boost may not be promoted to global tilt | `local_boost_and_global_tilt_are_not_merged`, `directional_promotion_gate_closed` | `missing_response_library`, `missing_null_ensemble` |
| `V8_tsc_no_overclaim` | `TSC` | TSC remains advisory and cannot own posterior/runtime truth | `tsc_quarantine_flags_emitted`, `tsc_theorem_map_covers_export_claims` | `missing_tsc_overlay`, `posterior_correction_attempted` |

## Rules

1. Every theorem entry must carry at least one artifact reference.
2. Every theorem entry must carry explicit no-claim conditions.
3. Every theorem-linked test path must resolve to a live repo-relative function or class-method symbol.
4. Every theorem must be covered by at least one executable validation campaign.
5. `warn` never promotes a claim to `validated`.
6. `fail` in a manuscript-blocking campaign blocks export.

## Check command

```bash
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_validation_registry.py --check
```
