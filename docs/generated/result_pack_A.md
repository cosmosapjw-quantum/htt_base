# Result Pack A - Scalar To Morphology Upgrade

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
config_hash: `sha256:e7e0272ceb046b83e5a9e25f150e807eb780ab9924a9b724d36d0cc2f2527f62`
input_hashes:
- scripts/result_packs/generate_pack_A_scalar_to_morphology.py:sha256:2ce369fd60461d35dbc93416f82cf8d52e9805db8eb5989c28aaa970f965848d
- docs/ver2_upgrade/generated/result_pack_A_scalar_to_morphology.json:sha256:2cb5c46c2eaacb5fe400b5910b8ebe85c7b78b5ae448772ea5c9be2d0b07beca
- docs/PR_DELTAS/pr-056.md:sha256:ca22c09c8a1822c1894fd775e2991932e9a6c28ba55ec9876a137e6000bf4207
- docs/PR_DELTAS/pr-076.md:sha256:a32bf4e530c1af1dcd941c9af73c7bc3d678eae8c7767c5f37179cf9b9a6906a
- docs/PR_DELTAS/pr-092.md:sha256:01f50c7a4cf69ec2c02d02be60c2373f7eb24167da25123464153a720340104c
- htt/mio/reports/departure_report.py:sha256:ed4a43543f103cd9dee9f3f335cc8d37f25558c313de01df6fa817388fb1cefe
- htt/obsstat/scalar_lowell.py:sha256:c7bf763cb684d183a13e6f1dd51369a93f79ab8f3ac3eef27be7e68c98fe12e9
- htt/obsstat/morphology.py:sha256:67899dad4232f0c944fb766db2c48b16bdd19efae95df58fd1fbd243e3261108
- htt/obsstat/null_ensembles.py:sha256:1033f1f4a5a105f455bf11b83bd421052b1520a486493560abd0f80fda16658c
- htt/htt/htt/statistics/mes_information_gain.py:sha256:251c44f18fbfe7949dc5b02e6b96db12154ce0488560748c8987458446d991b1
- htt/src/common/statistical_foundations.py:sha256:830d1698a8f57dd3a050862f4ee1b59da3b64688774e439171e4c40165939eff
- docs/generated/status_snapshot.json:sha256:90f804c527b01b112c1ef2c076f37086fa1bbc4edb3b390a0f05e4851a4dccf7
sky_support_status: not_directional
null_mock_status: summarized_from_dependency_surfaces
generating_command: `python scripts/result_packs/generate_pack_A_scalar_to_morphology.py`
git_commit_or_worktree_state: `declared-input-set:sha256:2277dae240782157ff303feb6e1ab897818050fec715e407f7c7475a408315ce`

## Scope

This is a diagnostic-only comparison pack. It compares scalar MIO Q/F/Pi legacy-projection report surfaces with OBSSTAT morphology features and COMMON MES I_morph status under explicit caveats. BC1 preserves recorded scalar values and BC2 forbids interpreting their representation as distance, occupancy, probability, or evidence. Native morphology atlas support remains absent.

## Scalar Diagnostics

| Name | Owner | Classification | Status | Role | Allowed Use | Forbidden Use |
| --- | --- | --- | --- | --- | --- | --- |
| Q | MIO | BC1_LEGACY_PROJECTION | legacy_projection_only | legacy signed policy-normalized ratio | historical reproduction and signed ratio reporting | departure distance, occupancy, probability, or evidence |
| F | MIO | BC1_LEGACY_PROJECTION | legacy_projection_only | legacy policy-normalized ratio when supplied | historical reproduction and declared ratio reporting | filling, occupancy, saturation, probability, or evidence |
| Pi | MIO | BC1_LEGACY_PROJECTION | legacy_projection_only | empirical exceedance curve | threshold summary of the recorded legacy ratio | truth probability, occupancy, or evidence |

## Morphology And MES Diagnostics

| Name | Owner | Surface | Role | Required Provenance |
| --- | --- | --- | --- | --- |
| Low-ell scalar features | OBSSTAT | obsstat.scalar_lowell.LowEllScalarSummary | observer-side scalar feature extraction | null ensemble and look-elsewhere metadata for p-values |
| Morphology axes | OBSSTAT | obsstat.morphology.MorphologyAxisSummary | diagnostic morphology-axis and alignment features | mask, covariance, null, and scan-volume metadata |
| MES I_morph | COMMON | htt.statistics.mes_information_gain.MesInformationGainReport | branch-separated MES morphology information-gain report | positive finite branch bounds and matched source manifests |

## Comparison Matrix

| Scalar | Morphology/MES | Status | Allowed Statement |
| --- | --- | --- | --- |
| Q | Low-ell scalar features | diagnostic_side_by_side | Q and Low-ell scalar features can be reported together only as claim-tiered diagnostics with separate provenance. |
| Q | Morphology axes | diagnostic_side_by_side | Q and Morphology axes can be reported together only as claim-tiered diagnostics with separate provenance. |
| Q | MES I_morph | diagnostic_side_by_side | Q and MES I_morph can be reported together only as claim-tiered diagnostics with separate provenance. |
| F | Low-ell scalar features | diagnostic_side_by_side | F and Low-ell scalar features can be reported together only as claim-tiered diagnostics with separate provenance. |
| F | Morphology axes | diagnostic_side_by_side | F and Morphology axes can be reported together only as claim-tiered diagnostics with separate provenance. |
| F | MES I_morph | diagnostic_side_by_side | F and MES I_morph can be reported together only as claim-tiered diagnostics with separate provenance. |
| Pi | Low-ell scalar features | diagnostic_side_by_side | Pi and Low-ell scalar features can be reported together only as claim-tiered diagnostics with separate provenance. |
| Pi | Morphology axes | diagnostic_side_by_side | Pi and Morphology axes can be reported together only as claim-tiered diagnostics with separate provenance. |
| Pi | MES I_morph | diagnostic_side_by_side | Pi and MES I_morph can be reported together only as claim-tiered diagnostics with separate provenance. |

## Legacy VER2 Context

Source `docs/ver2_upgrade/generated/result_pack_A_scalar_to_morphology.json` is hashed as prior context. This PR records those source rows without promoting their source tier or source readiness labels. The readiness labels are provenance only.

| Artifact | Owner | Source Tier | Current Public Status | Legacy Readiness | PR-110 Status |
| --- | --- | --- | --- | --- | --- |
| bass.ver2.export.solver_core_output_tier_b.observable_vector | BASS | conditional | diagnostic_only | legacy_not_current | prior_context_only |
| bass.ver2.export.solver_core_output_tier_b.atlas_lite | BASS | conditional | diagnostic_only | legacy_not_current | prior_context_only |
| bass.ver2.export.solver_core_output_tier_b.atlas_lite.mes.R_sigma_proxy | BASS | conditional | diagnostic_only | legacy_not_current | prior_context_only |

## Dependency Status

| PR | Implemented | Smoke Tested | Claim Tier | Production Gate |
| --- | --- | --- | --- | --- |
| PR-056 | True | False | diagnostic_only | False |
| PR-076 | True | False | diagnostic_only | False |
| PR-092 | True | False | diagnostic_only | False |

## Caveats

- diagnostic-only comparison over existing contract-backed report surfaces
- Q/F/Pi rows are BC1_LEGACY_PROJECTION with BC2_NO_REPRESENTATION_PROMOTION
- legacy scalar values are not departure distance, occupancy, probability, or evidence
- scalar Q/F/Pi values do not identify geometry or a Bianchi family
- morphology and MES features are observer/statistics diagnostics, not native atlas support
- native morphology atlas support remains absent
- no HTT evidence, MIO output, or native solver output is merged
- readiness labels are provenance only; not current production readiness

## Manifest

```json
{
  "artifact_id": "result_pack_A_scalar_to_morphology",
  "artifact_path": "docs/generated/result_pack_A.md",
  "caveats": [
    "diagnostic-only comparison over existing contract-backed report surfaces",
    "Q/F/Pi rows are BC1_LEGACY_PROJECTION with BC2_NO_REPRESENTATION_PROMOTION",
    "legacy scalar values are not departure distance, occupancy, probability, or evidence",
    "scalar Q/F/Pi values do not identify geometry or a Bianchi family",
    "morphology and MES features are observer/statistics diagnostics, not native atlas support",
    "native morphology atlas support remains absent",
    "no HTT evidence, MIO output, or native solver output is merged",
    "readiness labels are provenance only; not current production readiness"
  ],
  "claim_tier": "diagnostic_only",
  "code_version": "declared-input-set:sha256:2277dae240782157ff303feb6e1ab897818050fec715e407f7c7475a408315ce",
  "config_hash": "sha256:e7e0272ceb046b83e5a9e25f150e807eb780ab9924a9b724d36d0cc2f2527f62",
  "created_by": "scripts/result_packs/generate_pack_A_scalar_to_morphology.py",
  "failed_gates": [],
  "git_commit": null,
  "implementation_scope": "common",
  "input_hashes": [
    "scripts/result_packs/generate_pack_A_scalar_to_morphology.py:sha256:2ce369fd60461d35dbc93416f82cf8d52e9805db8eb5989c28aaa970f965848d",
    "docs/ver2_upgrade/generated/result_pack_A_scalar_to_morphology.json:sha256:2cb5c46c2eaacb5fe400b5910b8ebe85c7b78b5ae448772ea5c9be2d0b07beca",
    "docs/PR_DELTAS/pr-056.md:sha256:ca22c09c8a1822c1894fd775e2991932e9a6c28ba55ec9876a137e6000bf4207",
    "docs/PR_DELTAS/pr-076.md:sha256:a32bf4e530c1af1dcd941c9af73c7bc3d678eae8c7767c5f37179cf9b9a6906a",
    "docs/PR_DELTAS/pr-092.md:sha256:01f50c7a4cf69ec2c02d02be60c2373f7eb24167da25123464153a720340104c",
    "htt/mio/reports/departure_report.py:sha256:ed4a43543f103cd9dee9f3f335cc8d37f25558c313de01df6fa817388fb1cefe",
    "htt/obsstat/scalar_lowell.py:sha256:c7bf763cb684d183a13e6f1dd51369a93f79ab8f3ac3eef27be7e68c98fe12e9",
    "htt/obsstat/morphology.py:sha256:67899dad4232f0c944fb766db2c48b16bdd19efae95df58fd1fbd243e3261108",
    "htt/obsstat/null_ensembles.py:sha256:1033f1f4a5a105f455bf11b83bd421052b1520a486493560abd0f80fda16658c",
    "htt/htt/htt/statistics/mes_information_gain.py:sha256:251c44f18fbfe7949dc5b02e6b96db12154ce0488560748c8987458446d991b1",
    "htt/src/common/statistical_foundations.py:sha256:830d1698a8f57dd3a050862f4ee1b59da3b64688774e439171e4c40165939eff",
    "docs/generated/status_snapshot.json:sha256:90f804c527b01b112c1ef2c076f37086fa1bbc4edb3b390a0f05e4851a4dccf7"
  ],
  "owner": "COMMON",
  "passed_gates": [
    "scalar_and_morphology_provenance_separate",
    "no_native_or_family_claim",
    "manifest_metadata_present"
  ],
  "production_status": "diagnostic_only",
  "required_gates": [
    "dependencies_implemented",
    "scalar_and_morphology_provenance_separate",
    "no_native_or_family_claim",
    "manifest_metadata_present"
  ],
  "schema_version": "common.result_pack_A_scalar_to_morphology.v2",
  "statistics_definitions": {
    "comparison_status": "diagnostic_side_by_side",
    "legacy_ver2_context": "hashed_prior_context_only",
    "morphology_mes_section": "OBSSTAT morphology/null metadata plus COMMON MES I_morph report",
    "native_atlas_status": "absent",
    "scalar_section": "MIO Q/F/Pi diagnostic report surfaces",
    "surface": "Result Pack A"
  }
}
```
