from __future__ import annotations

import ast
import dataclasses
import importlib

import pytest

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
    SkySupport,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="obsstat.test.null_ensembles",
        artifact_path="memory://obsstat/null-ensembles",
        owner=Owner.OBSSTAT,
        implementation_scope=ImplementationScope.OBSSTAT,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by="tests.obsstat",
        git_commit="test",
        config_hash="sha256:test-config",
        input_hashes=["sha256:test-input"],
        code_version="test",
        schema_version="obsstat.null_ensembles.v1",
        caveats=["diagnostic feature extraction only"],
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="none",
        sky_support_hash="sha256:sky",
        mask_hash="sha256:mask",
        mock_coverage_status="mock_coverage_recorded",
        coordinate_frame="galactic",
        sky_fraction=0.75,
        completeness_status="masked_synthetic",
        pixelization="healpix_nside_16",
    )


def _spec(
    null_family: str = "flrw_mask_noise",
    *,
    feature_targets: tuple[str, ...] = ("scalar_lowell", "morphology"),
    statistic_keys: tuple[str, ...] = ("s_one_half", "alignment_to_reference"),
):
    from htt.obsstat.null_ensembles import NullEnsembleSpec

    return NullEnsembleSpec(
        null_ensemble_ref=f"mock://obsstat/{null_family}/v1",
        null_family=null_family,
        mock_count=256,
        feature_targets=feature_targets,
        statistic_keys=statistic_keys,
        sky_support_status="mask_weighted_directional_support",
        mask_status="masked_with_hash",
        noise_model_status="anisotropic_noise_model_recorded",
        covariance_status="mock_covariance_recorded",
        null_mock_status="mock_bank_available",
        random_seed_policy="fixed_seed_manifest:1234",
        config_hash="sha256:null-config",
        input_hashes=("sha256:null-input",),
        generating_command="python -m pytest tests/obsstat/test_null_ensembles.py -q",
        worktree_state="test-clean",
        source_metadata={
            "mask_hash": "sha256:mask",
            "noise_hash": "sha256:noise",
        },
    )


def _look_elsewhere(
    *,
    statistic_keys: tuple[str, ...] = ("s_one_half", "alignment_to_reference"),
    status: str = "global_corrected",
    correction_method: str = "empirical_global_tail",
):
    from htt.obsstat.null_ensembles import LookElsewhereBookkeeping

    return LookElsewhereBookkeeping(
        look_elsewhere_status=status,
        trial_count=12,
        scan_volume={
            "feature_targets": ["scalar_lowell", "morphology"],
            "statistic_keys": list(statistic_keys),
            "trial_count": 12,
            "orientation_count": 4,
            "threshold_count": 3,
            "global_local_status": status,
        },
        correction_method=correction_method,
        pre_registration_status="pre_registered",
        tail_definitions={key: "upper_tail" for key in statistic_keys},
    )


def _payload(
    *,
    spec=None,
    look_elsewhere=None,
    p_values: dict[str, float] | None = None,
):
    from htt.obsstat.null_ensembles import build_null_ensemble_feature_payload

    spec = _spec() if spec is None else spec
    look_elsewhere = (
        _look_elsewhere(statistic_keys=tuple(spec.statistic_keys))
        if look_elsewhere is None
        else look_elsewhere
    )
    p_values = (
        {key: 0.25 for key in spec.statistic_keys}
        if p_values is None
        else p_values
    )
    return build_null_ensemble_feature_payload(
        null_ensemble=spec,
        look_elsewhere=look_elsewhere,
        p_values=p_values,
    )


def test_required_null_families_are_represented_as_diagnostic_metadata() -> None:
    from htt.obsstat.null_ensembles import validate_null_feature_payload

    for null_family in (
        "flrw_mask_noise",
        "local_systematic",
        "injected_template",
    ):
        spec = _spec(null_family)
        payload = _payload(spec=spec)
        validate_null_feature_payload(payload)

        assert payload["owner"] == "OBSSTAT"
        assert payload["implementation_scope"] == "obsstat"
        assert payload["claim_tier"] == "diagnostic_only"
        assert payload["production_status"] == "diagnostic_only"
        assert payload["statistic_role"] == "null_calibrated_feature"
        assert payload["model_role"] == "not_model_input"
        assert payload["transfer_source"] == "none"
        assert payload["null_ensemble"]["null_family"] == null_family
        assert payload["null_ensemble_ref"] == f"mock://obsstat/{null_family}/v1"
        assert payload["mock_count"] == 256
        assert payload["look_elsewhere_status"] == "global_corrected"
        assert payload["does_not_establish"] == [
            "htt_evidence",
            "mio_certificate",
            "transfer_validation",
            "native_solver_validation",
            "morphology_compatibility",
            "geometry_detection",
            "family_identification",
        ]


def test_pvalues_require_complete_null_and_look_elsewhere_provenance() -> None:
    from htt.obsstat.null_ensembles import (
        LookElsewhereBookkeeping,
        NullCalibratedFeature,
        NullEnsembleSpec,
    )

    with pytest.raises(ValueError, match="mock_count"):
        NullEnsembleSpec(
            null_ensemble_ref="mock://bad",
            null_family="flrw_mask_noise",
            mock_count=0,
            feature_targets=("scalar_lowell",),
            statistic_keys=("s_one_half",),
            sky_support_status="mask_weighted_directional_support",
            mask_status="masked_with_hash",
            noise_model_status="anisotropic_noise_model_recorded",
            covariance_status="mock_covariance_recorded",
            null_mock_status="mock_bank_available",
            random_seed_policy="fixed_seed_manifest:1234",
            config_hash="sha256:null-config",
            input_hashes=("sha256:null-input",),
            generating_command="python -m pytest tests/obsstat/test_null_ensembles.py -q",
            worktree_state="test-clean",
        )

    with pytest.raises(ValueError, match="positive integer"):
        dataclasses.replace(_spec(), mock_count=12.75)
    with pytest.raises(ValueError, match="positive integer"):
        dataclasses.replace(_look_elsewhere(), trial_count=3.9)

    with pytest.raises(ValueError, match="look_elsewhere_status"):
        _look_elsewhere(status="not_tracked")

    look = LookElsewhereBookkeeping(
        look_elsewhere_status="global_corrected",
        trial_count=12,
        scan_volume={
            "feature_targets": ["scalar_lowell"],
            "statistic_keys": ["s_one_half"],
            "trial_count": 12,
            "global_local_status": "global_corrected",
        },
        correction_method="empirical_global_tail",
        pre_registration_status="pre_registered",
        tail_definitions={},
    )
    with pytest.raises(ValueError, match="tail_definitions"):
        NullCalibratedFeature(
            null_ensemble=_spec(),
            look_elsewhere=look,
            p_values={"s_one_half": 0.1},
        )

    local = _look_elsewhere(
        statistic_keys=("s_one_half",),
        status="local_unadjusted_with_trials",
        correction_method="none_tracked",
    )
    payload = _payload(
        spec=NullEnsembleSpec(
            null_ensemble_ref="mock://local",
            null_family="local_systematic",
            mock_count=128,
            feature_targets=("scalar_lowell",),
            statistic_keys=("s_one_half",),
            sky_support_status="mask_weighted_directional_support",
            mask_status="masked_with_hash",
            noise_model_status="anisotropic_noise_model_recorded",
            covariance_status="mock_covariance_recorded",
            null_mock_status="mock_bank_available",
            random_seed_policy="fixed_seed_manifest:1234",
            config_hash="sha256:null-config",
            input_hashes=("sha256:null-input",),
            generating_command="python -m pytest tests/obsstat/test_null_ensembles.py -q",
            worktree_state="test-clean",
        ),
        look_elsewhere=local,
        p_values={"s_one_half": 0.1},
    )
    assert payload["look_elsewhere_status"] == "local_unadjusted_with_trials"
    assert payload["look_elsewhere"]["correction_method"] == "none_tracked"
    assert any("local" in caveat for caveat in payload["caveats"])


def test_scan_volume_hash_and_statistic_keys_must_match() -> None:
    from htt.obsstat.null_ensembles import (
        LookElsewhereBookkeeping,
        NullCalibratedFeature,
    )

    with pytest.raises(ValueError, match="scan_volume_hash"):
        LookElsewhereBookkeeping(
            look_elsewhere_status="global_corrected",
            trial_count=12,
            scan_volume={
                "feature_targets": ["scalar_lowell"],
                "statistic_keys": ["s_one_half"],
                "trial_count": 12,
                "global_local_status": "global_corrected",
            },
            correction_method="empirical_global_tail",
            pre_registration_status="pre_registered",
            tail_definitions={"s_one_half": "upper_tail"},
            scan_volume_hash="sha256:not-the-derived-hash",
        )

    with pytest.raises(ValueError, match="statistic_keys"):
        LookElsewhereBookkeeping(
            look_elsewhere_status="global_corrected",
            trial_count=12,
            scan_volume={
                "feature_targets": ["scalar_lowell"],
                "statistic_keys": ["different_statistic"],
                "trial_count": 12,
                "global_local_status": "global_corrected",
            },
            correction_method="empirical_global_tail",
            pre_registration_status="pre_registered",
            tail_definitions={"s_one_half": "upper_tail"},
        )

    with pytest.raises(ValueError, match="available"):
        NullCalibratedFeature(
            null_ensemble=_spec(),
            look_elsewhere=_look_elsewhere(),
            p_values={"not_registered": 0.2},
        )


def test_null_payload_attaches_to_observable_vector_and_free_pvalues_fail() -> None:
    from htt.obsstat.null_ensembles import validate_null_feature_payload
    from htt.obsstat.observable_vector import build_observable_vector

    with pytest.raises(ValueError, match="typed null_features"):
        build_observable_vector(
            ell_max=4,
            channels=("TT",),
            scalar_features={"nested": {"pvalue_tail": 0.03}},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="metadata_schema"):
        build_observable_vector(
            ell_max=4,
            channels=("TT",),
            scalar_features={"nested": {"pvalue_tail": 0.03}},
            null_features={
                "null_ensemble_ref": "mock://legacy",
                "look_elsewhere_status": "tracked",
            },
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    payload = _payload()
    with pytest.raises(ValueError, match="statistic_keys covering"):
        build_observable_vector(
            ell_max=4,
            channels=("TT",),
            scalar_features={"nested": {"pvalue_tail": 0.03}},
            null_features=payload,
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    matched_payload = _payload(
        spec=_spec(
            "flrw_mask_noise",
            feature_targets=("scalar_lowell",),
            statistic_keys=("pvalue_tail",),
        ),
        look_elsewhere=_look_elsewhere(statistic_keys=("pvalue_tail",)),
        p_values={"pvalue_tail": 0.03},
    )
    vector = build_observable_vector(
        ell_max=4,
        channels=("TT",),
        scalar_features={"nested": {"pvalue_tail": 0.03}},
        null_features=matched_payload,
        manifest=_manifest(),
        sky_support=_sky_support(),
    )

    assert vector.alm_features["null_features"]["null_ensemble_ref"] == (
        "mock://obsstat/flrw_mask_noise/v1"
    )
    assert validate_null_feature_payload(vector.alm_features["null_features"]) is None


def test_serialized_null_payload_validator_rejects_tampered_metadata() -> None:
    from copy import deepcopy

    from htt.obsstat.null_ensembles import validate_null_feature_payload

    payload = _payload()

    bad_tail = deepcopy(payload)
    bad_tail["tail_definitions"]["s_one_half"] = "small_angle_tail"
    with pytest.raises(ValueError, match="invalid tails"):
        validate_null_feature_payload(bad_tail)

    bad_scan_hash = deepcopy(payload)
    bad_scan_hash["scan_volume_hash"] = "sha256:not-the-derived-hash"
    with pytest.raises(ValueError, match="scan_volume_hash"):
        validate_null_feature_payload(bad_scan_hash)

    bad_scan_trial = deepcopy(payload)
    bad_scan_trial["scan_volume"]["trial_count"] = 13
    with pytest.raises(ValueError, match="trial_count"):
        validate_null_feature_payload(bad_scan_trial)

    bad_scan_status = deepcopy(payload)
    bad_scan_status["scan_volume"]["global_local_status"] = "tracked_not_corrected"
    with pytest.raises(ValueError, match="global_local_status"):
        validate_null_feature_payload(bad_scan_status)

    bad_targets = deepcopy(payload)
    bad_targets["feature_targets"] = []
    with pytest.raises(ValueError, match="feature_targets"):
        validate_null_feature_payload(bad_targets)

    bad_nested = deepcopy(payload)
    bad_nested["look_elsewhere"]["scan_volume_hash"] = "sha256:nested-drift"
    with pytest.raises(ValueError, match="look_elsewhere.scan_volume_hash"):
        validate_null_feature_payload(bad_nested)


def test_null_payload_rejects_claim_drift_keys_and_values() -> None:
    from htt.obsstat.null_ensembles import NullCalibratedFeature, NullEnsembleSpec

    with pytest.raises(ValueError, match="forbidden claim language"):
        NullEnsembleSpec(
            null_ensemble_ref="mock://bad",
            null_family="flrw_mask_noise",
            mock_count=256,
            feature_targets=("scalar_lowell",),
            statistic_keys=("s_one_half",),
            sky_support_status="mask_weighted_directional_support",
            mask_status="masked_with_hash",
            noise_model_status="anisotropic_noise_model_recorded",
            covariance_status="mock_covariance_recorded",
            null_mock_status="mock_bank_available",
            random_seed_policy="fixed_seed_manifest:1234",
            config_hash="sha256:null-config",
            input_hashes=("sha256:null-input",),
            generating_command="python -m pytest tests/obsstat/test_null_ensembles.py -q",
            worktree_state="test-clean",
            source_metadata={"posterior_odds": 2.0},
        )

    phrase = " ".join(("family", "identified", "by", "null", "tail"))
    with pytest.raises(ValueError, match="forbidden claim language"):
        NullCalibratedFeature(
            null_ensemble=_spec(),
            look_elsewhere=_look_elsewhere(),
            p_values={"s_one_half": 0.1, "alignment_to_reference": 0.2},
            caveats=(phrase,),
        )

    with pytest.raises(ValueError, match="transfer_source"):
        NullEnsembleSpec(
            null_ensemble_ref="mock://bad",
            null_family="flrw_mask_noise",
            mock_count=256,
            feature_targets=("scalar_lowell",),
            statistic_keys=("s_one_half",),
            sky_support_status="mask_weighted_directional_support",
            mask_status="masked_with_hash",
            noise_model_status="anisotropic_noise_model_recorded",
            covariance_status="mock_covariance_recorded",
            null_mock_status="mock_bank_available",
            random_seed_policy="fixed_seed_manifest:1234",
            config_hash="sha256:null-config",
            input_hashes=("sha256:null-input",),
            generating_command="python -m pytest tests/obsstat/test_null_ensembles.py -q",
            worktree_state="test-clean",
            transfer_source="BASS_native_validated",
        )


def test_null_ensemble_exports_and_import_boundaries() -> None:
    from htt.obsstat import (
        LookElsewhereBookkeeping,
        NullCalibratedFeature,
        NullEnsembleSpec,
        build_null_ensemble_feature_payload,
    )
    from htt.obsstat.null_ensembles import NullEnsembleSpec as ModuleSpec

    assert NullEnsembleSpec is ModuleSpec
    assert LookElsewhereBookkeeping is not None
    assert NullCalibratedFeature is not None
    assert build_null_ensemble_feature_payload is not None

    top_level = importlib.import_module("obsstat.null_ensembles")
    htt_level = importlib.import_module("htt.obsstat.null_ensembles")
    assert top_level is htt_level
    assert top_level.NullEnsembleSpec is ModuleSpec

    tree = ast.parse(open("htt/obsstat/null_ensembles.py", encoding="utf-8").read())
    forbidden_roots = (
        "htt.infer",
        "htt.likelihood",
        "mio",
        "bass.transfer.native_adapter",
        "bass.transfer.native_schema",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(forbidden_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert not node.module.startswith(forbidden_roots)
