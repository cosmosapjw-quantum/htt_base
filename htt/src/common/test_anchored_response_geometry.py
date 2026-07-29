from __future__ import annotations

import hashlib
import math

import numpy as np
import pytest

from common.anchor_geometry import (
    AnchorGaugeInterval,
    AnchorGaugeStatus,
    NormalizerAvailability,
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (
    AnchoredResponseGeometryError,
    AnchoredResponseGeometryReport,
    AnchoredResponseStatus,
    IdentifiedSetContractionStatus,
    NonlinearityDGPKind,
    NonlinearityPhaseStatus,
    PrincipalAngleStatus,
    SchurMorphologyStatus,
    anchored_numeric_content_id,
    build_nonlinearity_phase_cell,
    build_nonlinearity_phase_diagram,
    measure_anchored_response_geometry,
    measure_schur_morphology_information,
    revalidate_anchored_response_geometry,
    revalidate_schur_morphology_information,
)
from common.orbit_nonlinearity import (
    NonlinearityAttributionStatus,
    decompose_nonlinearity,
)
from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferSource,
    TransferValidRange,
)


def _semantic_receipt(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


TRANSFER_ID = _semantic_receipt("pr255-test-synthetic-transfer-none-v1")
MASK_ID = _semantic_receipt("pr255-test-full-synthetic-mask-v1")
ORBIT_COVARIANCE_ID = _semantic_receipt(
    "pr255-test-orbit-nonlinearity-covariance-v1"
)
BASELINE_ID = _semantic_receipt("pr255-test-baseline-observable-v1")
MORPHOLOGY_ID = _semantic_receipt("pr255-test-morphology-observable-v1")


def _normalizer(
    dimension: int,
    *,
    diagonal: tuple[float, ...] | None = None,
    availability: NormalizerAvailability = NormalizerAvailability.AVAILABLE,
) -> NormalizerSpec:
    labels = tuple(f"u{index}" for index in range(dimension))
    if diagonal is None:
        diagonal = tuple(float(index + 2) for index in range(dimension))
    return NormalizerSpec(
        normalizer_id=f"fixture-normalizer-{dimension}",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=labels,
        coordinate_map=(
            tuple(
                tuple(
                    diagonal[row] if row == column else 0.0
                    for column in range(dimension)
                )
                for row in range(dimension)
            )
            if availability is NormalizerAvailability.AVAILABLE
            else ()
        ),
        source_identity="PR255-SYNTHETIC-NORMALIZER",
        availability=availability,
        unavailable_reason=(
            None
            if availability is NormalizerAvailability.AVAILABLE
            else "fixture anchor unavailable"
        ),
    )


def _geometry(**overrides):
    covariance = np.diag((1.0, 2.0, 3.0))
    values = {
        "response": ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0)),
        "covariance": covariance,
        "normalizer": _normalizer(2),
        "parameter_labels": ("u0", "u1"),
        "transfer_id": TRANSFER_ID,
        "transfer_source": TransferSource.NONE,
        "mask_id": MASK_ID,
        "covariance_id": anchored_numeric_content_id(covariance),
    }
    values.update(overrides)
    if "covariance" in overrides and "covariance_id" not in overrides:
        value = values["covariance"]
        if value is not None:
            values["covariance_id"] = anchored_numeric_content_id(value)
    return measure_anchored_response_geometry(**values)


def _schur(**overrides):
    joint_covariance = np.eye(2)
    values = {
        "baseline_response": ((1.0,),),
        "morphology_response": ((1.0,),),
        "joint_covariance": joint_covariance,
        "normalizer": _normalizer(1, diagonal=(1.0,)),
        "parameter_labels": ("u0",),
        "transfer_id": TRANSFER_ID,
        "transfer_source": TransferSource.NONE,
        "mask_id": MASK_ID,
        "joint_covariance_id": anchored_numeric_content_id(joint_covariance),
        "baseline_observable_id": BASELINE_ID,
        "morphology_observable_id": MORPHOLOGY_ID,
    }
    values.update(overrides)
    if (
        "joint_covariance" in overrides
        and "joint_covariance_id" not in overrides
    ):
        value = values["joint_covariance"]
        if value is not None:
            values["joint_covariance_id"] = anchored_numeric_content_id(value)
    return measure_schur_morphology_information(**values)


def _gauge(value: float) -> AnchorGaugeInterval:
    return AnchorGaugeInterval(
        anchor_id="fixture-anchor",
        vector_id=f"fixture-vector-{value}",
        lower=value,
        upper=value,
        status=AnchorGaugeStatus.DEFINED,
        conditional_values=(("fixture-anchor", value),),
        assumptions=("synthetic fixture",),
    )


def _external_transfer_spec(
    transfer_id: str = "external.fixture",
) -> TransferFunctionSpec:
    return TransferFunctionSpec(
        transfer_id=transfer_id,
        source=TransferSource.EXTERNAL_TRANSFER,
        family="synthetic response fixture",
        valid_range=TransferValidRange(
            k_min=1.0e-4,
            k_max=1.0,
            ell_min=2,
            ell_max=4,
        ),
        observable_kind=ObservableKind.TEMPLATE,
        normalization="fixture normalization",
        calibration_status=CalibrationStatus.EXTERNAL_CALIBRATED,
        caveats=("external-transfer conditional test only",),
        source_ref="fixture://external-response",
    )


def _nonlinearity(
    residual: tuple[float, float],
    *,
    transfer_id: str = TRANSFER_ID,
):
    return decompose_nonlinearity(
        residual=residual,
        tangent_response=((1.0,), (0.0,)),
        covariance=np.eye(2),
        transfer_id=transfer_id,
        mask_id=MASK_ID,
        covariance_id=ORBIT_COVARIANCE_ID,
        off_manifold_tolerance=1.0e-12,
        null_residual_tolerance=1.0e-12,
        nonlinear_gain_margin=0.1,
    )


def test_anchored_geometry_reports_rank_spectrum_and_principal_angles() -> None:
    report = _geometry(
        comparison_response=((0.0, 1.0), (1.0, 0.0), (0.0, 0.0))
    )
    assert report.status is AnchoredResponseStatus.MEASURED
    assert report.rank == report.original_rank == 2
    assert report.identifiable is True
    assert report.singular_values == pytest.approx((math.sqrt(4.5), 2.0))
    assert report.null_directions == ()
    assert report.covariance_null_response == ()
    assert report.principal_angles.status is PrincipalAngleStatus.DEFINED
    assert report.principal_angles.angles_radians == pytest.approx((0.0, 0.0))
    assert report.normalizer_id == "fixture-normalizer-2"
    assert report.response_id.startswith("sha256:")

    replayed = revalidate_anchored_response_geometry(
        report,
        normalizer=_normalizer(2),
        comparison_response=((0.0, 1.0), (1.0, 0.0), (0.0, 0.0)),
    )
    assert replayed == report


def test_missing_response_and_unavailable_normalizer_never_become_zero() -> None:
    missing = _geometry(response=None)
    assert missing.status is AnchoredResponseStatus.MISSING_INPUT
    assert missing.rank is None
    assert missing.response_replay_matrix is None
    assert missing.anchored_response_replay_matrix is None
    assert missing.missing_inputs == ("response",)

    unavailable = _geometry(
        normalizer=_normalizer(
            2, availability=NormalizerAvailability.UNAVAILABLE
        )
    )
    assert unavailable.status is AnchoredResponseStatus.MISSING_INPUT
    assert "normalizer_available" in unavailable.missing_inputs
    assert unavailable.singular_values == ()

    with pytest.raises(
        AnchoredResponseGeometryError,
        match="TransferSource vocabulary",
    ):
        _geometry(response=None, transfer_source="invented_native_source")


def test_singular_covariance_exposes_null_response_instead_of_zero_cost() -> None:
    report = _geometry(
        response=((1.0, 0.0), (0.0, 1.0)),
        covariance=np.diag((1.0, 0.0)),
    )
    assert report.status is AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE
    assert report.supported_data_dimension == 1
    assert report.rank == 1
    assert np.asarray(report.covariance_null_response) == pytest.approx(
        np.asarray(((0.0, 3.0),))
    )
    assert report.covariance_null_response_norm_sq == pytest.approx(9.0)
    assert len(report.null_directions) == 1

    outside = _geometry(
        response=((1.0, 0.0), (0.0, 1.0)),
        covariance=np.zeros((2, 2)),
    )
    assert outside.status is AnchoredResponseStatus.OUTSIDE_SUPPORTED_QUOTIENT
    assert outside.supported_data_dimension == 0
    assert outside.rank == 0
    assert outside.covariance_null_response_norm_sq == pytest.approx(13.0)


def test_exact_covariance_null_response_is_invariant_to_supported_scale() -> None:
    reports = tuple(
        _geometry(
            response=np.eye(2),
            covariance=np.diag((scale, 0.0)),
            normalizer=_normalizer(2, diagonal=(1.0, 1.0)),
            rtol=1.0e-12,
        )
        for scale in (1.0, 1.0e12)
    )
    assert tuple(report.status for report in reports) == (
        AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE,
        AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE,
    )
    assert tuple(
        report.covariance_null_response_norm_sq for report in reports
    ) == pytest.approx((1.0, 1.0))


def test_covariance_receipt_must_bind_canonical_numeric_content() -> None:
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="canonical covariance content identity",
    ):
        _geometry(covariance_id=_semantic_receipt("wrong-covariance"))


def test_nuisance_projection_is_applied_in_the_supported_data_space() -> None:
    report = _geometry(
        response=((1.0, 0.0), (0.0, 1.0)),
        covariance=np.eye(2),
        nuisance_response=((1.0,), (0.0,)),
    )
    assert report.nuisance_rank == 1
    assert report.rank == 1
    assert np.asarray(report.null_directions) == pytest.approx(
        np.asarray(((1.0, 0.0),))
    )


def test_numerically_rank_creating_anchor_scaling_fails_closed() -> None:
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="anchor scaling changed",
    ):
        _geometry(
            response=np.eye(2),
            covariance=np.eye(2),
            normalizer=_normalizer(2, diagonal=(1.0e-8, 1.0)),
            rtol=1.0e-6,
        )


def test_normalizer_without_response_conditioning_purpose_is_rejected() -> None:
    normalizer = NormalizerSpec(
        normalizer_id="wrong-purpose",
        kind=NormalizerKind.PRIOR_QUANTILE,
        purposes=(NormalizerPurpose.PORTABILITY,),
        coordinate_labels=("u0", "u1"),
        coordinate_map=((1.0, 0.0), (0.0, 1.0)),
        source_identity="PR255-WRONG-PURPOSE",
    )
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="RESPONSE_CONDITIONING",
    ):
        _geometry(normalizer=normalizer)


def test_external_transfer_requires_matching_full_provenance_spec() -> None:
    missing = _geometry(
        transfer_id="external.fixture",
        transfer_source=TransferSource.EXTERNAL_TRANSFER,
    )
    assert missing.status is AnchoredResponseStatus.MISSING_INPUT
    assert "transfer_spec" in missing.missing_inputs

    spec = _external_transfer_spec()
    report = _geometry(
        transfer_id=spec.transfer_id,
        transfer_source=spec.source,
        transfer_spec=spec,
    )
    assert report.status is AnchoredResponseStatus.MEASURED
    assert report.transfer_spec == spec
    assert report.as_payload()["transfer_metadata"] == spec.to_metadata()

    missing_id = _geometry(
        transfer_id=None,
        transfer_source=spec.source,
        transfer_spec=spec,
    )
    assert missing_id.status is AnchoredResponseStatus.MISSING_INPUT
    assert "transfer_id" in missing_id.missing_inputs

    missing_source = _geometry(
        transfer_id=spec.transfer_id,
        transfer_source=None,
        transfer_spec=spec,
    )
    assert missing_source.status is AnchoredResponseStatus.MISSING_INPUT
    assert "transfer_source" in missing_source.missing_inputs

    with pytest.raises(
        AnchoredResponseGeometryError,
        match="transfer_id must match",
    ):
        _geometry(
            transfer_id="external.other",
            transfer_source=spec.source,
            transfer_spec=spec,
        )
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="must not carry",
    ):
        _geometry(
            transfer_source=TransferSource.NONE,
            transfer_spec=spec,
        )


@pytest.mark.parametrize(
    "bad",
    (
        ((True, 0.0), (0.0, 1.0)),
        ((np.nan, 0.0), (0.0, 1.0)),
        ((np.inf, 0.0), (0.0, 1.0)),
        ((1.0 + 1.0j, 0.0), (0.0, 1.0)),
    ),
)
def test_response_rejects_bool_nonfinite_and_complex_inputs(bad) -> None:
    with pytest.raises(AnchoredResponseGeometryError):
        _geometry(response=bad, covariance=np.eye(2))


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        (
            {"response": np.empty((0, 2)), "covariance": np.empty((0, 0))},
            "must not be empty",
        ),
        (
            {
                "response": np.eye(2),
                "covariance": ((1.0, 0.25), (0.0, 1.0)),
            },
            "symmetric",
        ),
        (
            {
                "response": np.eye(2),
                "covariance": ((1.0, 0.0), (0.0, -1.0)),
            },
            "positive semidefinite",
        ),
        (
            {"response": np.eye(2), "covariance": np.eye(3)},
            "shape",
        ),
        (
            {
                "response": np.eye(2),
                "covariance": np.eye(2),
                "parameter_labels": ("u0", "u0"),
            },
            "duplicates",
        ),
        (
            {
                "response": np.eye(2),
                "covariance": np.eye(2),
                "parameter_labels": ("u0",),
            },
            "column count",
        ),
    ),
)
def test_geometry_rejects_empty_shape_duplicate_and_non_psd_inputs(
    overrides,
    message: str,
) -> None:
    with pytest.raises(AnchoredResponseGeometryError, match=message):
        _geometry(**overrides)


def test_direct_report_construction_is_blocked() -> None:
    legitimate = _geometry()
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="must be created",
    ):
        AnchoredResponseGeometryReport(
            **{
                name: value
                for name, value in vars(legitimate).items()
                if name != "_construction_token"
            }
        )


def test_schur_information_uses_one_joint_covariance() -> None:
    report = _schur(
        joint_covariance=((1.0, 0.5), (0.5, 1.0)),
    )
    assert report.status is SchurMorphologyStatus.MEASURED
    assert np.asarray(report.conditional_response) == pytest.approx(
        np.asarray(((0.5,),))
    )
    assert np.asarray(report.conditional_covariance) == pytest.approx(
        np.asarray(((0.75,),))
    )
    assert np.asarray(report.baseline_information) == pytest.approx(
        np.asarray(((1.0,),))
    )
    assert np.asarray(report.incremental_information) == pytest.approx(
        np.asarray(((1.0 / 3.0,),))
    )
    assert np.asarray(report.joint_information) == pytest.approx(
        np.asarray(((4.0 / 3.0,),))
    )
    assert report.contraction.status is (
        IdentifiedSetContractionStatus.DEFINED_FULL_DIMENSION
    )
    assert report.contraction.confidence_ellipsoid_volume_ratio == pytest.approx(
        math.sqrt(3.0 / 4.0)
    )
    assert revalidate_schur_morphology_information(
        report, normalizer=_normalizer(1, diagonal=(1.0,))
    ) == report


def test_schur_rank_gain_has_no_finite_contraction_ratio() -> None:
    report = _schur(
        baseline_response=((1.0, 0.0),),
        morphology_response=((0.0, 1.0),),
        normalizer=_normalizer(2, diagonal=(1.0, 1.0)),
        parameter_labels=("u0", "u1"),
    )
    assert report.contraction.status is (
        IdentifiedSetContractionStatus.RANK_GAIN_NO_FINITE_RATIO
    )
    assert report.contraction.confidence_ellipsoid_volume_ratio is None
    assert report.contraction.log_pseudodeterminant_gain is None


def test_schur_singular_conditional_covariance_keeps_null_response() -> None:
    report = _schur(
        baseline_response=((1.0,),),
        morphology_response=((0.0,),),
        joint_covariance=((1.0, 1.0), (1.0, 1.0)),
    )
    assert report.status is SchurMorphologyStatus.OUTSIDE_SUPPORTED_QUOTIENT
    conditional = report.conditional_morphology_geometry
    assert conditional.status is AnchoredResponseStatus.OUTSIDE_SUPPORTED_QUOTIENT
    assert np.asarray(conditional.covariance_null_response) == pytest.approx(
        np.asarray(((-1.0,),))
    )
    assert conditional.covariance_null_response_norm_sq == pytest.approx(1.0)


def test_schur_hidden_null_response_blocks_scalar_reduction_at_large_scale() -> None:
    report = _schur(
        baseline_response=((1.0,),),
        morphology_response=((0.0,), (1.0,)),
        joint_covariance=np.diag((1.0, 1.0e12, 0.0)),
        rtol=1.0e-12,
    )
    assert report.status is SchurMorphologyStatus.EXPLICIT_NULL_RESPONSE
    assert report.conditional_morphology_geometry.status is (
        AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE
    )
    assert (
        report.conditional_morphology_geometry
        .covariance_null_response_norm_sq
        == pytest.approx(1.0)
    )
    assert report.exact_one_dimensional_reduction is False


def test_schur_null_status_is_invariant_to_observable_units() -> None:
    reports = tuple(
        _schur(
            baseline_response=((scale,),),
            morphology_response=((scale,), (1.0,)),
            joint_covariance=np.diag(
                (scale * scale, scale * scale, 0.0)
            ),
            rtol=1.0e-12,
        )
        for scale in (1.0, 1.0e13)
    )
    for report in reports:
        assert report.status is SchurMorphologyStatus.EXPLICIT_NULL_RESPONSE
        assert report.conditional_morphology_geometry.status is (
            AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE
        )
        assert (
            report.conditional_morphology_geometry
            .covariance_null_response_norm_sq
            == pytest.approx(1.0)
        )
        assert report.exact_one_dimensional_reduction is False
    assert np.asarray(reports[0].baseline_information) == pytest.approx(
        np.asarray(reports[1].baseline_information)
    )
    assert np.asarray(reports[0].incremental_information) == pytest.approx(
        np.asarray(reports[1].incremental_information)
    )
    assert np.asarray(reports[0].joint_information) == pytest.approx(
        np.asarray(reports[1].joint_information)
    )


def test_schur_rejects_indefinite_covariance_hidden_by_dynamic_range() -> None:
    covariance = np.asarray(
        (
            (1.0e12, 0.0, 0.0),
            (0.0, 0.0, 0.5),
            (0.0, 0.5, 1.0),
        )
    )
    assert float(np.min(np.linalg.eigvalsh(covariance))) < -0.2
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="positive semidefinite",
    ):
        _schur(
            baseline_response=((1.0,),),
            morphology_response=((1.0,), (1.0,)),
            joint_covariance=covariance,
            rtol=1.0e-12,
        )


def test_schur_information_is_invariant_to_diagonal_unit_congruence() -> None:
    baseline = np.asarray(((2.0,),))
    morphology = np.asarray(((3.0,),))
    covariance = np.asarray(((4.0, 1.0), (1.0, 9.0)))
    reference = _schur(
        baseline_response=baseline,
        morphology_response=morphology,
        joint_covariance=covariance,
    )
    unit_map = np.diag((1.0e13, 1.0e-7))
    transformed = _schur(
        baseline_response=unit_map[:1, :1] @ baseline,
        morphology_response=unit_map[1:, 1:] @ morphology,
        joint_covariance=unit_map @ covariance @ unit_map,
    )
    assert transformed.status is reference.status
    assert np.asarray(transformed.baseline_information) == pytest.approx(
        np.asarray(reference.baseline_information)
    )
    assert np.asarray(transformed.incremental_information) == pytest.approx(
        np.asarray(reference.incremental_information)
    )
    assert np.asarray(transformed.joint_information) == pytest.approx(
        np.asarray(reference.joint_information)
    )
    assert transformed.contraction.status is reference.contraction.status
    assert (
        transformed.contraction.confidence_ellipsoid_volume_ratio
        == pytest.approx(
            reference.contraction.confidence_ellipsoid_volume_ratio
        )
    )


@pytest.mark.parametrize(
    ("baseline_scale", "morphology_scale"),
    ((1.0, 1.0), (1.0e-8, 1.0e8), (1.0e8, 1.0e-8)),
)
def test_schur_does_not_readmit_a_jointly_excluded_near_singular_mode(
    baseline_scale: float,
    morphology_scale: float,
) -> None:
    # The joint small eigenvalue is epsilon while the scalar Schur variance is
    # approximately 2 * epsilon.  This value sits in the historical
    # re-admission gap: the joint mode is excluded, but a separately
    # thresholded scalar conditional block would appear measured.
    epsilon = 1.5e-12
    unit_map = np.diag((baseline_scale, morphology_scale))
    covariance = np.asarray(
        ((1.0, 1.0 - epsilon), (1.0 - epsilon, 1.0))
    )
    transformed_covariance = unit_map @ covariance @ unit_map
    report = _schur(
        baseline_response=((baseline_scale,),),
        morphology_response=((0.0,),),
        joint_covariance=transformed_covariance,
        rtol=1.0e-12,
    )
    response = np.asarray(((baseline_scale,), (0.0,)))
    inverse_standard_deviation = 1.0 / np.sqrt(
        np.diag(transformed_covariance)
    )
    standardized_covariance = (
        inverse_standard_deviation[:, None]
        * transformed_covariance
        * inverse_standard_deviation[None, :]
    )
    standardized_response = inverse_standard_deviation[:, None] * response
    direct_information = (
        standardized_response.T
        @ np.linalg.pinv(
            standardized_covariance,
            rcond=1.0e-12,
            hermitian=True,
        )
        @ standardized_response
    )
    assert direct_information[0, 0] == pytest.approx(0.25)
    assert report.status is SchurMorphologyStatus.OUTSIDE_SUPPORTED_QUOTIENT
    assert report.conditional_morphology_geometry.status is (
        AnchoredResponseStatus.OUTSIDE_SUPPORTED_QUOTIENT
    )
    assert report.conditional_morphology_geometry.supported_data_dimension == 0
    assert report.exact_one_dimensional_reduction is False


def test_schur_joint_support_cutoff_has_a_registered_boundary() -> None:
    excluded = _schur(
        baseline_response=((1.0,),),
        morphology_response=((0.0,),),
        joint_covariance=((1.0, 1.0 - 1.5e-12), (1.0 - 1.5e-12, 1.0)),
        rtol=1.0e-12,
    )
    retained = _schur(
        baseline_response=((1.0,),),
        morphology_response=((0.0,),),
        joint_covariance=((1.0, 1.0 - 2.5e-12), (1.0 - 2.5e-12, 1.0)),
        rtol=1.0e-12,
    )
    assert excluded.status is SchurMorphologyStatus.OUTSIDE_SUPPORTED_QUOTIENT
    assert excluded.exact_one_dimensional_reduction is False
    assert retained.status is SchurMorphologyStatus.MEASURED
    assert retained.exact_one_dimensional_reduction is True


def test_dynamic_range_subspace_switch_has_no_finite_contraction_ratio() -> None:
    report = _schur(
        baseline_response=((1.0, 0.0),),
        morphology_response=((0.0, 1.0e6),),
        joint_covariance=np.eye(2),
        normalizer=_normalizer(2, diagonal=(1.0, 1.0)),
        parameter_labels=("u0", "u1"),
        rtol=1.0e-12,
    )
    assert report.contraction.status is (
        IdentifiedSetContractionStatus.SUBSPACE_CHANGED
    )
    assert report.contraction.log_pseudodeterminant_gain is None
    assert report.contraction.confidence_ellipsoid_volume_ratio is None


def test_phase_cell_never_uses_stress_to_attribute_source() -> None:
    off_manifold = _nonlinearity((0.0, 2.0))
    assert off_manifold.attribution_status is (
        NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD
    )
    cell = build_nonlinearity_phase_cell(
        cell_id="unknown-exceeding",
        dgp_kind=NonlinearityDGPKind.UNKNOWN_SOURCE,
        anchor_gauge=_gauge(2.0),
        nonlinearity=off_manifold,
    )
    assert cell.status is NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD
    assert cell.premise_exceeded is True
    assert cell.stress_used_for_attribution is False
    payload = cell.as_payload()
    assert payload["t_parallel"] == pytest.approx(0.0)
    assert payload["t_perp"] == pytest.approx(4.0)
    assert payload["delta_nl"] is None
    assert payload["delta_nl_status"] == (
        "NOT_COMPUTED_NO_NONLINEAR_MANIFOLD_DISTANCE"
    )
    assert payload["nonlinear_candidate_gains"] == []


def test_phase_diagram_requires_all_eight_synthetic_cells_and_no_pr151() -> None:
    linear = _nonlinearity((1.0, 0.0))
    assert linear.attribution_status is (
        NonlinearityAttributionStatus.LINEAR_COMPATIBLE
    )
    cells = tuple(
        build_nonlinearity_phase_cell(
            cell_id=kind.value.lower(),
            dgp_kind=kind,
            anchor_gauge=_gauge(0.5),
            nonlinearity=linear,
        )
        for kind in NonlinearityDGPKind
    )
    report = build_nonlinearity_phase_diagram(
        cells=cells,
        master_seed=20260728,
        transfer_id=TRANSFER_ID,
        transfer_source=TransferSource.NONE,
    )
    assert len(report.cells) == 8
    assert report.data_source == "synthetic_only"
    assert report.transfer_source is TransferSource.NONE
    assert report.transfer_spec is None
    assert report.transfer_id == TRANSFER_ID
    assert report.pr151_data_used is False
    assert report.forced_classification is False
    assert report.as_payload()["transfer_source"] == "none"
    assert report.as_payload()["transfer_id"] == TRANSFER_ID

    with pytest.raises(
        AnchoredResponseGeometryError,
        match="exactly one cell",
    ):
        build_nonlinearity_phase_diagram(
            cells=cells[:-1],
            master_seed=20260728,
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
        )
    with pytest.raises(AnchoredResponseGeometryError, match="PR-151"):
        build_nonlinearity_phase_diagram(
            cells=cells,
            master_seed=20260728,
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
            pr151_data_used=True,
        )

    with pytest.raises(
        AnchoredResponseGeometryError,
        match="require TransferFunctionSpec",
    ):
        build_nonlinearity_phase_diagram(
            cells=cells,
            master_seed=20260728,
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.EXTERNAL_TRANSFER,
        )

    external_spec = _external_transfer_spec(TRANSFER_ID)
    external = build_nonlinearity_phase_diagram(
        cells=cells,
        master_seed=20260728,
        transfer_id=TRANSFER_ID,
        transfer_source=external_spec.source,
        transfer_spec=external_spec,
    )
    assert external.transfer_spec == external_spec
    assert (
        external.as_payload()["transfer_metadata"]
        == external_spec.to_metadata()
    )

    external_other = _semantic_receipt("external-other-transfer")
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="transfer identities do not match",
    ):
        build_nonlinearity_phase_diagram(
            cells=cells,
            master_seed=20260728,
            transfer_id=external_other,
            transfer_source=TransferSource.EXTERNAL_TRANSFER,
            transfer_spec=_external_transfer_spec(external_other),
        )

    mixed_cells = list(cells)
    mixed_cells[0] = build_nonlinearity_phase_cell(
        cell_id=mixed_cells[0].cell_id,
        dgp_kind=mixed_cells[0].dgp_kind,
        anchor_gauge=_gauge(0.5),
        nonlinearity=_nonlinearity(
            (1.0, 0.0),
            transfer_id=_semantic_receipt("different-synthetic-transfer"),
        ),
    )
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="transfer identities do not match",
    ):
        build_nonlinearity_phase_diagram(
            cells=tuple(mixed_cells),
            master_seed=20260728,
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
        )

    forged = cells[0]
    object.__setattr__(
        forged,
        "status",
        NonlinearityPhaseStatus.NONLINEAR_WITHIN_ANCHOR,
    )
    with pytest.raises(
        AnchoredResponseGeometryError,
        match="fields do not match",
    ):
        build_nonlinearity_phase_diagram(
            cells=cells,
            master_seed=20260728,
            transfer_id=TRANSFER_ID,
            transfer_source=TransferSource.NONE,
        )
