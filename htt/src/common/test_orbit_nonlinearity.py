from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from common.orbit_nonlinearity import (
    CandidateEvaluation,
    CandidateKind,
    DEPARTURE_O3_PARITY,
    FOUND_EQUIV_PREREQUISITE,
    FOUND_EQUIV_STATUS,
    InvariantCatalogSpec,
    NonlinearityAttributionStatus,
    O3Transform,
    OrbitNonlinearityError,
    OrientedDirection,
    PR251_INVARIANT_NAMES,
    ResponseRankStatus,
    STF5_CARTESIAN_BASIS,
    VectorParity,
    decompose_nonlinearity,
    evaluate_candidate_predictions,
    measure_response_rank,
    orbit_invariants,
    transform_departure_state,
)
from common.statistical_foundations import DepartureState


TRANSFER_ID = "sha256:" + "1" * 64
MASK_ID = "sha256:" + "2" * 64
COVARIANCE_ID = "sha256:" + "3" * 64
FORGED_HELD_OUT_RECEIPT = "sha256:" + "a" * 64
FORGED_MATCHED_INJECTION_RECEIPT = "sha256:" + "b" * 64


def _state(*, beta: tuple[float, float, float] = (0.4, 0.5, 0.6)) -> DepartureState:
    return DepartureState(
        sigma_ab=(1.0, 2.0, 0.2, 0.3, 0.4),
        omega_a=(0.1, 0.2, 0.3),
        beta_a=beta,
        delta_omega_k=-0.01,
        frame="registered test frame",
        congruence="geodesic",
        epoch_window="z=0",
        averaging_scale="unit fixture",
        basis=STF5_CARTESIAN_BASIS,
        units="dimensionless",
        parity=DEPARTURE_O3_PARITY,
        perturbative_order="fixture",
    )


def _catalog() -> InvariantCatalogSpec:
    return InvariantCatalogSpec(
        catalog_id="PR251-CATALOG-V1",
        invariant_names=PR251_INVARIANT_NAMES,
        multiplicity_method="max-T across the six preregistered invariants",
        alignment_null_id="ALIGNMENT-NULL-PR251-FIXTURE",
        preregistration_id="PR251",
    )


def _rotation() -> O3Transform:
    angle = 0.37
    c, s = math.cos(angle), math.sin(angle)
    return O3Transform(
        matrix=((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0)),
        transform_id="RZ-0.37",
        coordinate_frame="registered test frame",
    )


def _candidates(
    *,
    nonlinear_score: float = 12.0,
    frame_score: float = 4.0,
) -> tuple[CandidateEvaluation, ...]:
    scores = {
        CandidateKind.NONLINEAR: nonlinear_score,
        CandidateKind.LINEAR: 3.0,
        CandidateKind.SYSTEMATICS: 5.0,
        CandidateKind.FRAME_MISMATCH: frame_score,
        CandidateKind.DERIVATIVE_FAILURE: 2.0,
    }
    maximum = max(scores.values())
    return tuple(
        evaluate_candidate_predictions(
            candidate_id=f"candidate-{kind.value.lower()}",
            kind=kind,
            held_out_prediction=(math.sqrt(maximum - score), 0.0),
            held_out_target=(0.0, 0.0),
            matched_injection_prediction=(
                1.0 + math.sqrt(maximum - score),
                1.0,
            ),
            matched_injection_target=(1.0, 1.0),
            model_config_id=(
                "sha256:" + f"{list(scores).index(kind) + 1:064x}"
            ),
        )
        for kind, score in scores.items()
    )


def _nonlinearity(
    residual: tuple[float, float, float],
    *,
    covariance: object = np.eye(3),
    candidates: tuple[CandidateEvaluation, ...] = (),
    receipt: str | None = None,
    matched_injection_receipt: str | None = None,
):
    if candidates:
        if receipt is None:
            receipt = candidates[0].held_out_data_id
        if matched_injection_receipt is None:
            matched_injection_receipt = (
                candidates[0].matched_injection_data_id
            )
    return decompose_nonlinearity(
        residual=residual,
        tangent_response=((1.0,), (0.0,), (0.0,)),
        covariance=covariance,
        transfer_id=TRANSFER_ID,
        mask_id=MASK_ID,
        covariance_id=COVARIANCE_ID,
        candidates=candidates,
        held_out_receipt=receipt,
        matched_injection_receipt=matched_injection_receipt,
        off_manifold_tolerance=1e-12,
        null_residual_tolerance=1e-12,
        nonlinear_gain_margin=1.0,
    )


def test_proper_rotation_is_equivariant_and_preserves_catalogue() -> None:
    state = _state()
    transformed = transform_departure_state(state, _rotation())
    before = orbit_invariants(state, _catalog())
    after = orbit_invariants(transformed, _catalog())
    assert np.allclose(before.even_values, after.even_values, atol=1e-12)
    assert after.parity_odd_det == pytest.approx(before.parity_odd_det)
    assert transformed.delta_omega_k == state.delta_omega_k


def test_reflection_flips_only_parity_odd_invariant_and_axial_action() -> None:
    state = _state()
    reflection = O3Transform(
        matrix=((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        transform_id="REFLECT-X",
        coordinate_frame="registered test frame",
    )
    transformed = transform_departure_state(state, reflection)
    before = orbit_invariants(state, _catalog())
    after = orbit_invariants(transformed, _catalog())
    assert np.allclose(before.even_values, after.even_values, atol=1e-12)
    assert after.parity_odd_det == pytest.approx(-before.parity_odd_det)
    assert transformed.beta_a == pytest.approx((-0.4, 0.5, 0.6))
    assert transformed.omega_a == pytest.approx((0.1, -0.2, -0.3))


def test_o3_action_rejects_frame_mismatch() -> None:
    wrong_frame = O3Transform(
        matrix=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        transform_id="IDENTITY-WRONG-FRAME",
        coordinate_frame="different frame",
    )
    with pytest.raises(OrbitNonlinearityError, match="frames"):
        transform_departure_state(_state(), wrong_frame)


def test_catalogue_separates_equal_beta_norm_different_orientation() -> None:
    left = orbit_invariants(_state(beta=(1.0, 0.0, 0.0)), _catalog())
    right = orbit_invariants(_state(beta=(0.0, 1.0, 0.0)), _catalog())
    assert left.beta2 == right.beta2
    assert left.beta_sigma_beta != right.beta_sigma_beta


@pytest.mark.parametrize(
    "field_value",
    (
        {"parity": "SIGMA_STF2;OMEGA_POLAR;BETA_AXIAL;DELTA_OMEGA_K_SCALAR"},
        {"units": "km / s"},
    ),
)
def test_catalogue_requires_registered_parity_and_units(
    field_value: dict[str, str],
) -> None:
    with pytest.raises(OrbitNonlinearityError, match="registered"):
        orbit_invariants(replace(_state(), **field_value), _catalog())


def test_orbit_report_rewrite_cannot_forge_values_or_claim_lanes() -> None:
    report = orbit_invariants(_state(), _catalog())
    with pytest.raises(OrbitNonlinearityError, match="must be created"):
        replace(
            report,
            beta2=999.0,
            allowed_use=("Bianchi family identification",),
            forbidden_use=("none",),
        )


def test_oriented_direction_keeps_sign_and_parity_type() -> None:
    positive = OrientedDirection((1.0, 0.0, 0.0), VectorParity.POLAR)
    negative = OrientedDirection((-1.0, 0.0, 0.0), VectorParity.POLAR)
    axial = OrientedDirection((1.0, 0.0, 0.0), VectorParity.AXIAL)
    assert positive.signed_dot(negative) == -1.0
    with pytest.raises(OrbitNonlinearityError, match="matching"):
        positive.signed_dot(axial)


def test_oriented_direction_normalizes_extreme_finite_values_stably() -> None:
    direction = OrientedDirection((1.0e308, -1.0e308, 0.0), VectorParity.POLAR)
    assert np.linalg.norm(direction.vector) == pytest.approx(1.0)
    assert direction.vector[0] == pytest.approx(1.0 / math.sqrt(2.0))


def test_o3_contract_rejects_an_oversized_tolerance() -> None:
    with pytest.raises(OrbitNonlinearityError, match="at most"):
        O3Transform(
            matrix=((0.0, 0.0, 0.0),) * 3,
            transform_id="NOT-O3",
            coordinate_frame="registered test frame",
            atol=2.0,
        )


def test_rank_comes_from_supplied_response_and_exposes_wide_null() -> None:
    report = measure_response_rank(
        response=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        covariance=np.eye(2),
        transfer_id=TRANSFER_ID,
        mask_id=MASK_ID,
        covariance_id=COVARIANCE_ID,
    )
    assert report.status is ResponseRankStatus.MEASURED
    assert report.rank == 2
    assert report.parameter_dimension == 3
    assert report.min_singular == 0.0
    assert len(report.nullspace) == 1
    assert not report.identifiable


def test_rank_missing_inputs_never_defaults_to_eight_or_full_rank() -> None:
    report = measure_response_rank(
        response=None,
        covariance=None,
        transfer_id=None,
        mask_id=None,
        covariance_id=None,
    )
    assert report.status is ResponseRankStatus.MISSING_INPUT
    assert report.rank is None
    assert report.parameter_dimension is None
    assert set(report.missing_inputs) == {
        "response",
        "covariance",
        "transfer_id",
        "mask_id",
        "covariance_id",
    }


def test_rank_is_invariant_to_common_covariance_scale() -> None:
    response = np.array(((1.0, 0.0), (0.0, 1e-8), (0.0, 0.0)))
    reports = [
        measure_response_rank(
            response=response,
            covariance=scale * np.eye(3),
            transfer_id=TRANSFER_ID,
            mask_id=MASK_ID,
            covariance_id=COVARIANCE_ID,
        )
        for scale in (1e-30, 1.0, 1e30)
    ]
    assert [report.rank for report in reports] == [2, 2, 2]


def test_rank_does_not_underflow_for_finite_common_whitening_scale() -> None:
    report = measure_response_rank(
        response=1.0e-308 * np.eye(2),
        covariance=1.0e308 * np.eye(2),
        transfer_id=TRANSFER_ID,
        mask_id=MASK_ID,
        covariance_id=COVARIANCE_ID,
    )
    assert report.rank == 2
    assert report.identifiable


@pytest.mark.parametrize(
    ("response", "covariance", "rtol"),
    (
        (np.asarray(((1.0 + 1.0j,),)), np.eye(1), 1.0e-12),
        (np.empty((2, 0)), np.eye(2), 1.0e-12),
        (((1.0,),), ((-1.0,),), 2.0),
    ),
)
def test_rank_rejects_complex_empty_and_oversized_tolerance_inputs(
    response: object,
    covariance: object,
    rtol: float,
) -> None:
    with pytest.raises(OrbitNonlinearityError):
        measure_response_rank(
            response=response,
            covariance=covariance,
            transfer_id=TRANSFER_ID,
            mask_id=MASK_ID,
            covariance_id=COVARIANCE_ID,
            rtol=rtol,
        )


def test_singular_covariance_reports_supported_rank_and_null_residual() -> None:
    report = _nonlinearity(
        (0.0, 0.0, 1.0),
        covariance=np.diag((1.0, 1.0, 0.0)),
    )
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.OUTSIDE_SUPPORTED_QUOTIENT
    )
    assert report.response_rank.supported_data_dimension == 2
    assert report.null_residual_sq == pytest.approx(1.0)


def test_linear_residual_stays_linear_compatible() -> None:
    report = _nonlinearity((2.0, 0.0, 0.0))
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.LINEAR_COMPATIBLE
    )
    assert report.tangent_statistic == pytest.approx(4.0)
    assert report.perpendicular_statistic == pytest.approx(0.0)


def test_off_manifold_without_complete_held_out_competition_is_unattributed() -> None:
    report = _nonlinearity((2.0, 1.0, 0.0))
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD
    )


def test_nonlinear_compatibility_requires_both_held_out_wins() -> None:
    report = _nonlinearity(
        (2.0, 1.0, 0.0),
        candidates=_candidates(),
    )
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
    )
    assert report.found_equiv_status == FOUND_EQUIV_STATUS
    assert report.found_equiv_prerequisite == FOUND_EQUIV_PREREQUISITE
    assert "family identification" in " ".join(report.forbidden_use)


def test_candidate_scores_are_factory_derived_and_rewrite_protected() -> None:
    candidate = _candidates()[0]
    with pytest.raises(OrbitNonlinearityError, match="must be created"):
        replace(candidate, held_out_score=999.0)
    changed = evaluate_candidate_predictions(
        candidate_id=candidate.candidate_id,
        kind=candidate.kind,
        held_out_prediction=(3.0, 0.0),
        held_out_target=(0.0, 0.0),
        matched_injection_prediction=(4.0, 1.0),
        matched_injection_target=(1.0, 1.0),
        model_config_id=candidate.model_config_id,
    )
    assert changed.held_out_data_id == candidate.held_out_data_id
    assert changed.held_out_prediction_id != candidate.held_out_prediction_id
    assert changed.evaluation_id != candidate.evaluation_id
    assert changed.held_out_score != candidate.held_out_score


def test_rank_deficiency_blocks_nonlinear_attribution() -> None:
    candidates = _candidates()
    report = decompose_nonlinearity(
        residual=(2.0, 1.0, 0.0),
        tangent_response=((1.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        covariance=np.eye(3),
        transfer_id=TRANSFER_ID,
        mask_id=MASK_ID,
        covariance_id=COVARIANCE_ID,
        candidates=candidates,
        held_out_receipt=candidates[0].held_out_data_id,
        matched_injection_receipt=(
            candidates[0].matched_injection_data_id
        ),
        off_manifold_tolerance=1.0e-12,
        null_residual_tolerance=1.0e-12,
        nonlinear_gain_margin=1.0,
    )
    assert not report.response_rank.identifiable
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.NON_IDENTIFIED_RESPONSE
    )


def test_report_constructor_cannot_forge_nonlinear_compatibility() -> None:
    linear = _nonlinearity((2.0, 0.0, 0.0))
    with pytest.raises(OrbitNonlinearityError, match="must be created"):
        replace(
            linear,
            attribution_status=(
                NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
            ),
            held_out_receipt=FORGED_HELD_OUT_RECEIPT,
            matched_injection_receipt=FORGED_MATCHED_INJECTION_RECEIPT,
        )


def test_missing_response_report_cannot_be_relabelled_nonlinear() -> None:
    missing = decompose_nonlinearity(
        residual=(1.0,),
        tangent_response=None,
        covariance=None,
        transfer_id=None,
        mask_id=None,
        covariance_id=None,
        off_manifold_tolerance=0.0,
        null_residual_tolerance=0.0,
        nonlinear_gain_margin=1.0,
    )
    with pytest.raises(OrbitNonlinearityError, match="must be created"):
        replace(
            missing,
            attribution_status=(
                NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
            ),
            tangent_statistic=0.0,
            perpendicular_statistic=1.0,
            null_residual_sq=0.0,
            off_manifold_tolerance=0.0,
            null_residual_tolerance=0.0,
            nonlinear_gain_margin=1.0,
            held_out_receipt=FORGED_HELD_OUT_RECEIPT,
            matched_injection_receipt=FORGED_MATCHED_INJECTION_RECEIPT,
            attribution_rationale="forged",
        )


def test_matched_injection_identity_must_match_every_candidate() -> None:
    stale = "sha256:" + "e" * 64
    report = _nonlinearity(
        (2.0, 1.0, 0.0),
        candidates=_candidates(),
        matched_injection_receipt=stale,
    )
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD
    )


@pytest.mark.parametrize(
    ("frame_score", "nonlinear_score"),
    ((13.0, 12.0), (12.0, 12.5)),
)
def test_frame_or_insufficient_gain_remains_unattributed(
    frame_score: float,
    nonlinear_score: float,
) -> None:
    report = _nonlinearity(
        (2.0, 1.0, 0.0),
        candidates=_candidates(
            nonlinear_score=nonlinear_score,
            frame_score=frame_score,
        ),
    )
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD
    )


@pytest.mark.parametrize(
    "bad",
    (
        [[True, False], [False, True]],
        [[1.0, math.nan], [0.0, 1.0]],
        np.asarray([["1.0", "0.0"], ["0.0", "1.0"]], dtype=object),
    ),
)
def test_rank_rejects_boolean_and_nonfinite_response(bad: object) -> None:
    with pytest.raises(OrbitNonlinearityError):
        measure_response_rank(
            response=bad,
            covariance=np.eye(2),
            transfer_id=TRANSFER_ID,
            mask_id=MASK_ID,
            covariance_id=COVARIANCE_ID,
        )


def test_rank_report_rewrite_cannot_forge_identifiability() -> None:
    measured = measure_response_rank(
        response=((1.0, 0.0), (0.0, 0.0)),
        covariance=np.eye(2),
        transfer_id=TRANSFER_ID,
        mask_id=MASK_ID,
        covariance_id=COVARIANCE_ID,
    )
    with pytest.raises(OrbitNonlinearityError, match="must be created"):
        replace(
            measured,
            rank=2,
            singular_values=(1.0, 0.0),
            nullspace=(),
        )


def test_covariance_psd_validity_is_not_weakened_by_rank_tolerance() -> None:
    covariance = np.diag((-1.0, 0.0, 1000.0, 2000.0))
    with pytest.raises(OrbitNonlinearityError, match="semidefinite"):
        measure_response_rank(
            response=np.eye(4),
            covariance=covariance,
            transfer_id=TRANSFER_ID,
            mask_id=MASK_ID,
            covariance_id=COVARIANCE_ID,
            rtol=1.0e-3,
        )


@pytest.mark.parametrize(
    "bad",
    (
        np.asarray([[True, 0.0], [0.0, 1.0]], dtype=object),
        np.asarray([[1.0 + 0.0j, 0.0], [0.0, 1.0]], dtype=object),
    ),
)
def test_object_arrays_cannot_hide_boolean_or_complex_response(
    bad: np.ndarray,
) -> None:
    with pytest.raises(OrbitNonlinearityError):
        measure_response_rank(
            response=bad,
            covariance=np.eye(2),
            transfer_id=TRANSFER_ID,
            mask_id=MASK_ID,
            covariance_id=COVARIANCE_ID,
        )
