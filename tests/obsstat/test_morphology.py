from __future__ import annotations

import ast
import importlib
import sys

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
        artifact_id="obsstat.test.morphology",
        artifact_path="memory://obsstat/morphology",
        owner=Owner.OBSSTAT,
        implementation_scope=ImplementationScope.OBSSTAT,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by="tests.obsstat",
        git_commit="test",
        config_hash="sha256:test-config",
        input_hashes=["sha256:test-input"],
        code_version="test",
        schema_version="obsstat.morphology.v1",
        caveats=["diagnostic feature extraction only"],
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="none",
        sky_support_hash="sha256:sky",
        mask_hash="sha256:mask",
        mock_coverage_status="not_statistical",
        coordinate_frame="galactic",
        sky_fraction=1.0,
        completeness_status="full_sky_synthetic",
        pixelization="none",
    )


def test_tensor_morphology_extracts_diagnostic_axes_and_alignment_features() -> None:
    from htt.obsstat.morphology import summarize_morphology_axes
    from htt.obsstat.observable_vector import build_observable_vector

    summary = summarize_morphology_axes(
        morphology_tensor=[
            [4.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.25],
        ],
        reference_axes={"reference_direction": [1.0, 0.0, 0.0]},
        null_calibration=None,
        config_hash="sha256:config",
        input_hashes=("sha256:input",),
    )
    payload = summary.to_feature_payload()

    assert payload["owner"] == "OBSSTAT"
    assert payload["implementation_scope"] == "obsstat"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["model_role"] == "not_model_input"
    assert payload["transfer_source"] == "none"
    assert payload["axis_claim_status"] == "diagnostic_axis_not_production_axis"
    assert payload["principal_axis"]["axis_role"] == "diagnostic_morphology_axis"
    assert payload["principal_axis"]["l_deg"] == pytest.approx(0.0)
    assert payload["principal_axis"]["b_deg"] == pytest.approx(0.0)
    assert payload["principal_axis"]["production_allowed"] is False
    assert payload["plane_normal_axis"]["b_deg"] == pytest.approx(90.0)
    assert payload["alignment_features"]["reference_direction"][
        "antipodal_angle_deg"
    ] == pytest.approx(0.0)
    assert payload["alignment_features"]["reference_direction"][
        "antipodal_abs_dot"
    ] == pytest.approx(1.0)
    assert payload["null_calibration"]["status"] == "not_null_calibrated"

    vector = build_observable_vector(
        ell_max=4,
        channels=("TT",),
        morphology_features={"tensor_morphology": payload},
        manifest=_manifest(),
        sky_support=_sky_support(),
    )
    assert (
        vector.alm_features["morphology_features"]["tensor_morphology"][
            "axis_claim_status"
        ]
        == "diagnostic_axis_not_production_axis"
    )


def test_morphology_axis_adapter_cannot_bypass_preferred_axis_gate() -> None:
    from htt.obsstat.morphology import summarize_morphology_axes
    from htt.zoa.axis_promotion import (
        evaluate_axis_promotion,
        require_axis_for_harmonic_synthesis,
    )

    summary = summarize_morphology_axes(
        morphology_tensor=[
            [2.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.5],
        ],
        config_hash="sha256:config",
        input_hashes=("sha256:input",),
    )
    axis = summary.principal_axis.to_preferred_axis()

    assert axis.production_allowed is False
    assert axis.source == "raw_diagnostic"
    decision = evaluate_axis_promotion(
        axis,
        sky_support=_sky_support(),
        target="a_lm",
    )

    assert decision.allowed is False
    assert "axis_not_production_promoted" in decision.blocked_reasons
    assert "diagnostic_axis_cannot_rotate_a_lm" in decision.blocked_reasons
    with pytest.raises(RuntimeError, match="diagnostic_axis_cannot_rotate_a_lm"):
        require_axis_for_harmonic_synthesis(
            axis,
            sky_support=_sky_support(),
            target="a_lm",
        )


def test_look_elsewhere_null_metadata_is_required_for_morphology_pvalues() -> None:
    from htt.obsstat.morphology import (
        MorphologyNullCalibration,
        summarize_morphology_axes,
    )
    from htt.obsstat.observable_vector import build_observable_vector

    with pytest.raises(ValueError, match="tail_definitions"):
        MorphologyNullCalibration(
            null_ensemble_ref="mock://morphology-axis-nulls",
            look_elsewhere_status="tracked",
            p_values={"alignment_to_reference": 0.04},
            mock_count=256,
            covariance_status="directional_mock_covariance_available",
            mask_status="full_sky_synthetic",
            scan_volume={"targets": ["reference_direction"]},
            look_elsewhere_trials=3,
        )
    with pytest.raises(ValueError, match="p_values keys"):
        MorphologyNullCalibration(
            null_ensemble_ref="mock://morphology-axis-nulls",
            look_elsewhere_status="tracked",
            p_values={"axis_nonexistent": 0.04},
            tail_definitions={"axis_nonexistent": "small_angle_tail"},
            mock_count=256,
            covariance_status="directional_mock_covariance_available",
            mask_status="full_sky_synthetic",
            scan_volume={
                "targets": ["reference_direction"],
                "statistic_keys": ["axis_nonexistent"],
                "look_elsewhere_trials": 3,
                "global_local_status": "global_corrected",
            },
            look_elsewhere_trials=3,
        )
    with pytest.raises(ValueError, match="mock_count"):
        MorphologyNullCalibration(
            null_ensemble_ref="mock://morphology-axis-nulls",
            look_elsewhere_status="tracked",
            p_values={"alignment_to_reference": 0.04},
            tail_definitions={"alignment_to_reference": "small_angle_tail"},
            mock_count=1,
            covariance_status="directional_mock_covariance_available",
            mask_status="full_sky_synthetic",
            scan_volume={
                "targets": ["reference_direction"],
                "statistic_keys": ["alignment_to_reference"],
                "look_elsewhere_trials": 3,
                "global_local_status": "global_corrected",
            },
            look_elsewhere_trials=3,
        )

    calibration = MorphologyNullCalibration(
        null_ensemble_ref="mock://morphology-axis-nulls",
        look_elsewhere_status="tracked",
        p_values={"alignment_to_reference": 0.04},
        tail_definitions={"alignment_to_reference": "small_angle_tail"},
        mock_count=256,
        covariance_status="directional_mock_covariance_available",
        mask_status="full_sky_synthetic",
        scan_volume={
            "targets": ["reference_direction"],
            "statistic_keys": ["alignment_to_reference"],
            "look_elsewhere_trials": 3,
            "global_local_status": "global_corrected",
        },
        look_elsewhere_trials=3,
    )
    summary = summarize_morphology_axes(
        morphology_tensor=[
            [3.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.25],
        ],
        reference_axes={"reference_direction": [1.0, 0.0, 0.0]},
        null_calibration=calibration,
        config_hash="sha256:config",
        input_hashes=("sha256:input",),
    )
    payload = summary.to_feature_payload()

    assert payload["statistic_role"] == "null_calibrated_feature"
    assert payload["null_calibration"]["null_ensemble_ref"] == (
        "mock://morphology-axis-nulls"
    )
    assert payload["null_calibration"]["look_elsewhere_trials"] == 3
    assert payload["null_calibration"]["p_values"]["alignment_to_reference"] == 0.04

    vector = build_observable_vector(
        ell_max=4,
        channels=("TT",),
        morphology_features={"tensor_morphology": payload},
        manifest=_manifest(),
        sky_support=_sky_support(),
    )
    assert (
        vector.alm_features["morphology_features"]["tensor_morphology"][
            "null_calibration"
        ]["look_elsewhere_status"]
        == "tracked"
    )


def test_degenerate_morphology_tensor_is_flagged_not_promoted() -> None:
    from htt.obsstat.morphology import summarize_morphology_axes

    summary = summarize_morphology_axes(
        morphology_tensor=[
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0],
        ],
        config_hash="sha256:config",
        input_hashes=("sha256:input",),
    )
    payload = summary.to_feature_payload()

    assert payload["principal_axis"]["axis_status"] == "degenerate"
    assert payload["principal_axis"]["production_allowed"] is False
    assert "degenerate" in payload["principal_axis"]["caveats"]
    assert payload["axis_identifiability_status"] == "partial"
    assert payload["axis_identifiability_rank"] == 1
    assert payload["condition_status"] == "singular_or_rank_deficient"
    assert payload["planarity"]["axiality_ratio"] == pytest.approx(0.0)
    assert payload["planarity"]["planarity_ratio"] == pytest.approx(0.5)

    with_reference = summarize_morphology_axes(
        morphology_tensor=[
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0],
        ],
        reference_axes={"reference_direction": [1.0, 0.0, 0.0]},
        config_hash="sha256:config",
        input_hashes=("sha256:input",),
    ).to_feature_payload()
    assert (
        with_reference["alignment_features"]["reference_direction"]["status"]
        == "axis_degenerate"
    )
    assert (
        with_reference["alignment_features"]["reference_direction"][
            "antipodal_angle_deg"
        ]
        is None
    )

    isotropic = summarize_morphology_axes(
        morphology_tensor=[
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        config_hash="sha256:config",
        input_hashes=("sha256:input",),
    ).to_feature_payload()
    assert isotropic["axis_identifiability_status"] == "degenerate"
    assert isotropic["axis_identifiability_rank"] == 0
    assert isotropic["condition_status"] == "finite"


def test_morphology_rejects_inference_transfer_or_family_claim_payloads() -> None:
    from htt.obsstat.morphology import (
        DiagnosticMorphologyAxis,
        summarize_morphology_axes,
    )

    with pytest.raises(ValueError, match="transfer_source"):
        summarize_morphology_axes(
            morphology_tensor=[[1.0, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.1]],
            transfer_source="external_transfer",
            config_hash="sha256:config",
            input_hashes=("sha256:input",),
        )

    with pytest.raises(ValueError, match="overclaim"):
        summarize_morphology_axes(
            morphology_tensor=[[1.0, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.1]],
            tensor_label=("posterior" + " odds summary"),
            config_hash="sha256:config",
            input_hashes=("sha256:input",),
        )

    with pytest.raises(ValueError, match="production_allowed"):
        DiagnosticMorphologyAxis(
            vector=(1.0, 0.0, 0.0),
            l_deg=0.0,
            b_deg=0.0,
            label="bad-axis",
            axis_role="diagnostic_morphology_axis",
            axis_status="resolved",
            provenance_hash="sha256:" + "a" * 64,
            production_allowed=True,
        )
    with pytest.raises(ValueError, match="source"):
        DiagnosticMorphologyAxis(
            vector=(1.0, 0.0, 0.0),
            l_deg=0.0,
            b_deg=0.0,
            label="bad-axis",
            axis_role="diagnostic_morphology_axis",
            axis_status="resolved",
            provenance_hash="sha256:" + "a" * 64,
            source="fiducial_posterior",
        )
    with pytest.raises(ValueError, match="config_hash"):
        summarize_morphology_axes(
            morphology_tensor=[[1.0, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.1]],
            config_hash="sha256:config-not-supplied",
            input_hashes=("sha256:input",),
        )
    with pytest.raises(ValueError, match="input_hashes"):
        summarize_morphology_axes(
            morphology_tensor=[[1.0, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.1]],
            config_hash="sha256:config",
            input_hashes=(),
        )


def test_obsstat_morphology_import_has_no_inference_or_mio_side_effects() -> None:
    before = set(sys.modules)

    importlib.import_module("htt.obsstat.morphology")

    loaded = set(sys.modules) - before
    assert not [
        module
        for module in loaded
        if module.startswith(("mio", "htt.mio", "htt.htt.infer"))
        or "likelihood" in module
        or "mio_certificate" in module
    ]

    source_path = "htt/obsstat/morphology.py"
    tree = ast.parse(open(source_path, encoding="utf-8").read())
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not [
        module
        for module in imported
        if module.startswith(("htt.htt", "htt.infer", "mio", "htt.mio"))
        or "likelihood" in module
    ]
