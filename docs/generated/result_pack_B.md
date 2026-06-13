# Result Pack B - Local Global Discrimination

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
config_hash: `sha256:7979b3ddfd1bd9d40bc483461c1c6e8ddd8b2f19d9df4035b918a5acfce2565a`
input_hashes:
- scripts/result_packs/generate_pack_B_local_global.py:sha256:b5b4fc6e12ee73dace9d04f1df1587ce65b60ff664c8df748932c1072b8071ec
- docs/ver2_upgrade/generated/result_pack_B_local_global.json:sha256:b5b9c8de5aa0ee2867279033dba5cc042158220934f5d68194770542eaf8319b
- docs/PR_DELTAS/pr-060.md:sha256:5aaa5d40a13e045ef11d48ac6cb931575cff014015122a620985605138aaf1b1
- docs/PR_DELTAS/pr-061.md:sha256:d0d92499aad9c78a6c4a7a268d2efaaca8a1c44c701e1f407697fbfee4666839
- docs/PR_DELTAS/pr-062.md:sha256:a58b15c94ba24ab1b92c764880ab9faa5108f9d0d92f94c9bfdea667b6c24fb9
- docs/PR_DELTAS/pr-063.md:sha256:0827a75a07227360230784a3d8cb084ac97aceb5c900deb7adb5bdf8a0f13358
- docs/PR_DELTAS/pr-064.md:sha256:03e817de24563bc574354243c53510444ccdb4a733e0d84572071ef0f8f88e31
- docs/PR_DELTAS/pr-065.md:sha256:ee9aec15fb62312537be098f977c6f409b809185712f6b69c5d09db7d9bc9ea9
- docs/PR_DELTAS/pr-066.md:sha256:724f3ae5b429ff8853c3757fc6dd73048d5fe72e0fdf99c5d47ef2a105f0c070
- docs/PR_DELTAS/pr-100.md:sha256:aa59e1e6c159f2911a2f01378fa622a63363d2322afd2d979189b7b14a50df02
- docs/PR_DELTAS/pr-101.md:sha256:d6e78b134d34f3bc88a8ac384afe38e6be968f514c592fec1af50d97f5ba690a
- htt/htt/htt/departure/response_overlap.py:sha256:2ea56655e8b8c419239459bdbe4d79c755d00115ce4bd6e6e00b447d51c1f139
- htt/htt/htt/nulls/local_boost_depth_null.py:sha256:b0d5d0b6a4b3fe534d1eefc630b9954a33d82555520f644f779dd6725e25609c
- htt/htt/htt/nulls/selection_response_depth.py:sha256:cac8f08d6618519e95147acde5ae0f567035206d14c595b3b917bf548a2a3cd3
- htt/htt/htt/departure/local_global_mixture.py:sha256:53803d5a056af6fcd0a4b1a348f87ac7002ec2c5764a4bb80f97c5154a21c914
- htt/htt/htt/departure/posterior_pushforward.py:sha256:e2385b5ad836957a61f78cdf26eb6c9f7991549188bd4ce951b83141fd2f5a5b
- htt/mio/coherence/directional.py:sha256:13f06d76ba1208ac5c4b1c03a5b04ce48c83a7bfdc5df5d1a85009a2df7051f3
- htt/mio/coherence/redshift_binned.py:sha256:6e47f6ac5145caa66d784a392b4301a28492080ddd136de4c7e53c2017c175b5
- docs/generated/status_snapshot.json:sha256:99ff7e02c6063bf3330103c989891ce9fd8da6da7249d2d64058a645e91ceb61
sky_support_status: not_directional
null_mock_status: summarized_from_local_and_survey_systematic_fpr_gates
generating_command: `python scripts/result_packs/generate_pack_B_local_global.py`
git_commit_or_worktree_state: `54b53c2+dirty`

## Scope

This COMMON diagnostic-only pack summarizes existing HTT and MIO gate surfaces for local/global discrimination. It composes report metadata only. MIO directional and depth diagnostics are a diagnostic cross-check, not HTT evidence, and legacy VER2 Pack B rows remain prior context.

Global tilt claim tier ceiling: conditional

## Gate Summary

| Category | Owner | Source PR | Surface | Required Status | Claim Role |
| --- | --- | --- | --- | --- | --- |
| rank audit | HTT | PR-060 | htt.departure.response_overlap.ResponseOverlapAudit | full_rank_identifiable | pre_inference_gate |
| local null fpr | HTT | PR-061 | htt.nulls.local_boost_depth_null.LocalBoostNullFprReport | local_boost_null_fpr_available_and_below_threshold | prerequisite_not_evidence |
| survey systematic null fpr | HTT | PR-062 | htt.nulls.selection_response_depth.SurveySystematicNullFprReport | selection_and_survey_systematic_fpr_available_and_below_threshold | prerequisite_not_evidence |
| local global mixture | HTT | PR-063 | htt.departure.local_global_mixture.LocalGlobalMixtureReport | separate_local_global_systematic_noise_blocks | conditional_pre_solver_ceiling |
| posterior pushforward | HTT | PR-066 | htt.departure.posterior_pushforward.PosteriorPushforwardReport | htt_owned_transfer_conditional_prerequisites | htt_pushforward_context_not_mio_input |
| directional coherence | MIO | PR-100 | mio.coherence.directional.to_mio_certificate | covariance_null_sky_status_recorded | diagnostic_cross_check_not_htt_evidence |
| depth gap | MIO | PR-101 | mio.coherence.redshift_binned.RedshiftDepthBinMetadata | redshift_bin_metadata_and_g_f_bridge_refs_recorded | diagnostic_depth_bridge_not_htt_evidence |

The local/systematic null FPR rows are prerequisite gates, not posterior or evidence rows. The rank audit, G_F depth gap, and directional coherence rows are reported as separate dependency surfaces.

## Rank And FPR Scenarios

| Scenario | Rank Status | Null FPR Status | Claim Tier | Status | Allowed Phrase |
| --- | --- | --- | --- | --- | --- |
| all_prerequisites_pass | full_rank | local_and_survey_systematic_fpr_recorded | conditional | local_global_discrimination_candidate | conditional local/global discrimination candidate |
| rank_deficient_projected_response | rank_deficient | not_evaluated_after_rank_block | blocked | blocked_no_claim | no-claim rank or overlap blocker |
| overlap_degenerate_response | full_rank_overlap_degenerate | not_promoted | blocked | blocked_no_claim | no-claim rank or overlap blocker |
| full_design_condition_too_high | full_rank_but_ill_conditioned | not_promoted | blocked | blocked_no_claim | no-claim rank or overlap blocker |
| missing_local_null_fpr | full_rank | local_null_fpr_missing | blocked | blocked_no_claim | no-claim missing FPR prerequisite |
| high_survey_systematic_fpr | full_rank | survey_systematic_null_fpr_exceeds_threshold | blocked | blocked_no_claim | no-claim high FPR prerequisite |

## Dependency Status

| PR | Implemented | Smoke Tested | Claim Tier | Production Gate |
| --- | --- | --- | --- | --- |
| PR-066 | True | True | diagnostic_only | False |
| PR-100 | True | True | diagnostic_only | False |
| PR-101 | True | True | diagnostic_only | False |

## Legacy VER2 Context

Source `docs/ver2_upgrade/generated/result_pack_B_local_global.json` is hashed as prior context. PR-111 status: `legacy_context_only_not_promoted`.

| Artifact | Owner | Source Tier | Source Gate | PR-111 Status |
| --- | --- | --- | --- | --- |
| htt.ver2.export.discrimination_matrix | HTT | conditional | production_candidate | prior_context_only |

## Claim Boundaries

- native_solver_status: not_native_solver_output
- family_status: blocked_until_native_morphology_atlas
- geometry_status: blocked_until_native_morphology_atlas
- mio_coherence_use: diagnostic_cross_check_not_htt_evidence
- htt_pushforward_use: htt_owned_transfer_conditional_context_only
- common_pack_use: report_composition_not_inference

## Caveats

- common_diagnostic_only_report_over_existing_dependency_surfaces
- rank_or_overlap_blockers_are_no_claim_states
- local_and_survey_systematic_fpr_are_prerequisites_not_evidence
- mio_directional_and_depth_surfaces_are_diagnostic_cross_checks_only
- posterior_pushforward_rows_remain_htt_owned_and_transfer_conditional
- legacy_ver2_pack_b_is_prior_context_only_not_promoted
- native_morphology_atlas_support_remains_absent
- no_htt_evidence_mio_certificate_or_native_solver_output_is_merged

## Manifest

```json
{
  "artifact_id": "result_pack_B_local_global",
  "artifact_path": "docs/generated/result_pack_B.md",
  "caveats": [
    "common_diagnostic_only_report_over_existing_dependency_surfaces",
    "rank_or_overlap_blockers_are_no_claim_states",
    "local_and_survey_systematic_fpr_are_prerequisites_not_evidence",
    "mio_directional_and_depth_surfaces_are_diagnostic_cross_checks_only",
    "posterior_pushforward_rows_remain_htt_owned_and_transfer_conditional",
    "legacy_ver2_pack_b_is_prior_context_only_not_promoted",
    "native_morphology_atlas_support_remains_absent",
    "no_htt_evidence_mio_certificate_or_native_solver_output_is_merged"
  ],
  "claim_tier": "diagnostic_only",
  "code_version": "54b53c2+dirty",
  "config_hash": "sha256:7979b3ddfd1bd9d40bc483461c1c6e8ddd8b2f19d9df4035b918a5acfce2565a",
  "created_by": "scripts/result_packs/generate_pack_B_local_global.py",
  "failed_gates": [],
  "git_commit": null,
  "implementation_scope": "common",
  "input_hashes": [
    "scripts/result_packs/generate_pack_B_local_global.py:sha256:b5b4fc6e12ee73dace9d04f1df1587ce65b60ff664c8df748932c1072b8071ec",
    "docs/ver2_upgrade/generated/result_pack_B_local_global.json:sha256:b5b9c8de5aa0ee2867279033dba5cc042158220934f5d68194770542eaf8319b",
    "docs/PR_DELTAS/pr-060.md:sha256:5aaa5d40a13e045ef11d48ac6cb931575cff014015122a620985605138aaf1b1",
    "docs/PR_DELTAS/pr-061.md:sha256:d0d92499aad9c78a6c4a7a268d2efaaca8a1c44c701e1f407697fbfee4666839",
    "docs/PR_DELTAS/pr-062.md:sha256:a58b15c94ba24ab1b92c764880ab9faa5108f9d0d92f94c9bfdea667b6c24fb9",
    "docs/PR_DELTAS/pr-063.md:sha256:0827a75a07227360230784a3d8cb084ac97aceb5c900deb7adb5bdf8a0f13358",
    "docs/PR_DELTAS/pr-064.md:sha256:03e817de24563bc574354243c53510444ccdb4a733e0d84572071ef0f8f88e31",
    "docs/PR_DELTAS/pr-065.md:sha256:ee9aec15fb62312537be098f977c6f409b809185712f6b69c5d09db7d9bc9ea9",
    "docs/PR_DELTAS/pr-066.md:sha256:724f3ae5b429ff8853c3757fc6dd73048d5fe72e0fdf99c5d47ef2a105f0c070",
    "docs/PR_DELTAS/pr-100.md:sha256:aa59e1e6c159f2911a2f01378fa622a63363d2322afd2d979189b7b14a50df02",
    "docs/PR_DELTAS/pr-101.md:sha256:d6e78b134d34f3bc88a8ac384afe38e6be968f514c592fec1af50d97f5ba690a",
    "htt/htt/htt/departure/response_overlap.py:sha256:2ea56655e8b8c419239459bdbe4d79c755d00115ce4bd6e6e00b447d51c1f139",
    "htt/htt/htt/nulls/local_boost_depth_null.py:sha256:b0d5d0b6a4b3fe534d1eefc630b9954a33d82555520f644f779dd6725e25609c",
    "htt/htt/htt/nulls/selection_response_depth.py:sha256:cac8f08d6618519e95147acde5ae0f567035206d14c595b3b917bf548a2a3cd3",
    "htt/htt/htt/departure/local_global_mixture.py:sha256:53803d5a056af6fcd0a4b1a348f87ac7002ec2c5764a4bb80f97c5154a21c914",
    "htt/htt/htt/departure/posterior_pushforward.py:sha256:e2385b5ad836957a61f78cdf26eb6c9f7991549188bd4ce951b83141fd2f5a5b",
    "htt/mio/coherence/directional.py:sha256:13f06d76ba1208ac5c4b1c03a5b04ce48c83a7bfdc5df5d1a85009a2df7051f3",
    "htt/mio/coherence/redshift_binned.py:sha256:6e47f6ac5145caa66d784a392b4301a28492080ddd136de4c7e53c2017c175b5",
    "docs/generated/status_snapshot.json:sha256:99ff7e02c6063bf3330103c989891ce9fd8da6da7249d2d64058a645e91ceb61"
  ],
  "owner": "COMMON",
  "passed_gates": [
    "rank_audit_reported",
    "local_and_survey_systematic_fpr_reported",
    "depth_gap_and_directional_coherence_reported",
    "rank_blockers_suppress_candidate_language",
    "manifest_metadata_present"
  ],
  "production_status": "diagnostic_only",
  "required_gates": [
    "dependencies_implemented",
    "rank_audit_reported",
    "local_and_survey_systematic_fpr_reported",
    "depth_gap_and_directional_coherence_reported",
    "rank_blockers_suppress_candidate_language",
    "manifest_metadata_present"
  ],
  "schema_version": "common.result_pack_B_local_global.v1",
  "statistics_definitions": {
    "claim_tier_ceiling": "conditional",
    "depth_section": "PR-101 G_F redshift-bin bridge references",
    "directional_section": "PR-100 MIO directional coherence metadata",
    "fpr_section": "PR-061 local and PR-062 survey/systematic FPR gates",
    "legacy_ver2_context": "hashed_prior_context_only",
    "pushforward_section": "PR-066 HTT pushforward context",
    "rank_section": "PR-060 response-overlap and rank audit",
    "surface": "Result Pack B"
  }
}
```
