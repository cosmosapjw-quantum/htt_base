# V6 No-Download Research Cards

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_and_external_transfer_conditioned
sky_support_status: mixed_diagnostic_metadata_only
null_mock_status: mixed_diagnostic_and_blocked
config_hash: `sha256:c9b3c7d344aabf9b5af9a48473f6454b4d1fa99ba14a71a4dbf58c7478ffbfd7`
caveats:
- No long-run K1/K5/K6 analysis is executed by this artifact.
- No native low-ell solver output is represented.
- All cards are diagnostic/readiness objects and do not identify a Bianchi family.
generating_command: python scripts/build_v6_no_download_research_cards.py
git_commit_or_worktree_state: content-addressed

## Component-Source Matrix

| Component | Mode | Status | Source | Blocker |
| --- | --- | --- | --- | --- |
| `Sigma2` | `estimated_partial` | `partial` | `docs/generated/k1_global_maxscan.json` | BLOCKED_MISSING_PR4_E2E_ACCESS |
| `W2` | `fail_closed_structural_no_go` | `fail_closed_structural_no_go` | `docs/generated/k6_cf4_curl_posterior.json` | BLOCKED_MISSING_FIELD_REALIZATIONS |
| `Omega_tilt` | `estimated_conditional_coverage` | `measured` | `docs/generated/k5_cf4_release_coverage.json` | full_selection_malmquist_grouping_correlated_release_mocks_still_gate |
| `Omega_k` | `absent_no_registered_lowell_channel` | `fail_closed_no_channel` | `none` | native_lowell_transfer_or_higher_order_channel_required |

## Identified-Set Card

- data_rank_count: `2`
- reachable_full: `Omega_tilt`
- reachable_partial: `Sigma2`
- fail_closed_columns: `Omega_k, W2`
- x_C_interval_status: `not_certified_blind_sectors_not_zeroed`
- F_status: `diagnostic_only_not_certified_filling`

## Denominator Sensitivity

| Policy | Shift | Denominator | Q diagnostic | Transfer |
| --- | ---: | ---: | ---: | --- |
| `MES_linear` | -0.2 | 0.0696 | 0.9195402298850576 | `none` |
| `MES_linear` | 0.0 | 0.087 | 0.7356321839080461 | `none` |
| `MES_linear` | 0.2 | 0.10439999999999999 | 0.6130268199233717 | `none` |
| `external_transfer` | -0.2 | 0.0832 | 0.7692307692307693 | `external_transfer` |
| `external_transfer` | 0.0 | 0.104 | 0.6153846153846154 | `external_transfer` |
| `external_transfer` | 0.2 | 0.1248 | 0.5128205128205129 | `external_transfer` |
| `observational` | -0.2 | 0.0608 | 1.0526315789473684 | `none` |
| `observational` | 0.0 | 0.076 | 0.8421052631578948 | `none` |
| `observational` | 0.2 | 0.09119999999999999 | 0.7017543859649124 | `none` |

## Exceedance Calibration

- source_score_label: `Q`
- threshold_policy: `curve_only`
- calibration_status: `raw_exceedance_only_uncalibrated_no_p_value`
- forbidden_use: `p_value_or_truth_probability`

## Depth-Gap Card

- G_F: `6.499999999999999`
- reference/comparison: `near` -> `far`
- matched_null_forecast_status: `forecast_matched_null_blocked`
- cf4_shell_attempt_status: `not_attempted_current_cf4_shells_lack_matched_covariance_and_calibrated_null`

## Optical Ansatz Readiness

| Branch | Status | Blocker |
| --- | --- | --- |
| `mean_template` | `insufficient_for_likelihood_branch` | harmonic_template_plus_orientation_marginalization_or_noncentral_statistic_required |
| `covariance_biposh` | `data_side_descriptor_only` | full_anisotropic_covariance_and_e2e_null_not_bound |
| `central_scalar_chi_square` | `blocked_for_both_lowell_branches` | central_scalar_is_neither_noncentral_template_nor_full_covariance |

## K5/K6 Next-Turn Feasibility

| Lane | Input present | Size bytes | Next-turn runnable | Deferred reason |
| --- | ---: | ---: | ---: | --- |
| `K5` | `True` | 5179298 | `True` | moderate deterministic run; N_MOCK=600 |
| `K6` | `True` | 167773716 | `True` | heavier grid/ensemble run; 128^3 velocity grid, N_CR=400 |

## Legacy Figure Classification

- full ledger: `docs/generated/v6_legacy_figure_classification.json`
- ranking_removed: `True`
