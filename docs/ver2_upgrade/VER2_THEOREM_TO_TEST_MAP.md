# VER2 Theorem-To-Test Map

## Status

- Authority: `docs/ver2_upgrade/*`
- Packet owner: `SK-08V`
- Registry source of truth: `htt/workspace/contracts/validation_registry.py`
- Current phase state: skeleton registry active, campaign status machine-readable, all entries remain conservative and no-claim aware.

## Core entries

| Theorem ID | Owner | Guard | Test category | Primary linked test | Explicit no-claim conditions |
|---|---|---|---|---|---|
| `V8_isotropic_limit_recovery` | `BASS` | anisotropic outputs must recover the isotropic null before promotion | `baseline_reproduction` | `htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py::test_fb72_type_i_off_diagonal_vanishes_identically` | `missing_observable_vector`, `sparse_proxy_only` |
| `V8_biposh_Lgt0_null_or_proxy_block` | `BASS` | proxy sparse morphology may not be promoted as invariant BiPoSH evidence | `physics_sanity` | `htt/bass/observational/test_ver2_observable_atlas.py::test_covariance_proxy_and_feature_summary_record_guards` | `sparse_mode_block_proxy`, `missing_biposh_basis` |
| `V8_template_injection_recovery` | `HTT` | injection claims require declared null/injection manifests | `adversarial_edge` | `tests/validation/test_template_injection_recovery.py` | `missing_injection_campaign`, `missing_scan_volume` |
| `V8_mes_rank_no_claim` | `BASS` | rank-deficient covariance upgrades are explicit no-claim outputs | `adversarial_edge` | `htt/bass/observational/test_ver2_mes_departure.py::test_full_cov_mes_rank_failure_returns_no_claim` | `response_rank_deficient`, `missing_covariance_features` |
| `V8_filling_requires_certification` | `COMMON` | uncertified normalized scores remain `Q`, not certified `F` | `physics_sanity` | `htt/bass/observational/test_ver2_mes_departure.py::test_departure_report_stays_descriptive_without_claim_gate` | `claim_gate_not_passed`, `occupancy_not_certified` |
| `V8_local_vs_global_discrimination` | `HTT` | local boost may not be promoted to global tilt | `adversarial_edge` | `tests/validation/test_local_boost_not_promoted_to_global.py` | `missing_response_library`, `missing_null_ensemble` |
| `V8_tsc_no_overclaim` | `TSC` | TSC remains advisory and cannot own posterior/runtime truth | `regression` | `htt/tsc/test_theorem_map_contains_core_tests.py` | `missing_tsc_overlay`, `posterior_correction_attempted` |

## Rules

1. Every theorem entry must carry at least one artifact reference.
2. Every theorem entry must carry explicit no-claim conditions.
3. Planned tests may be referenced before executable implementation packets land, but the registry must not present them as completed validation.
4. `warn` never promotes a claim to `validated`.
5. `fail` in a manuscript-blocking campaign blocks export.

## Check command

```bash
PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_validation_registry.py --check
```
