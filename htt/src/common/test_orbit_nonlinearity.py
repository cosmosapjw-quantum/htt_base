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
    measure_response_rank,
    orbit_invariants,
    transform_departure_state,
)
from common.statistical_foundations import DepartureState


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
    receipt: str = "HOLDOUT-PR251",
) -> tuple[CandidateEvaluation, ...]:
    scores = {
        CandidateKind.NONLINEAR: nonlinear_score,
        CandidateKind.LINEAR: 3.0,
        CandidateKind.SYSTEMATICS: 5.0,
        CandidateKind.FRAME_MISMATCH: frame_score,
        CandidateKind.DERIVATIVE_FAILURE: 2.0,
    }
    return tuple(
        CandidateEvaluation(
            candidate_id=f"candidate-{kind.value.lower()}",
            kind=kind,
            held_out_score=score,
            matched_injection_score=score - 0.5,
            held_out_data_id=receipt,
        )
        for kind, score in scores.items()
    )


def _nonlinearity(
    residual: tuple[float, float, float],
    *,
    covariance: object = np.eye(3),
    candidates: tuple[CandidateEvaluation, ...] = (),
    receipt: str | None = None,
):
    return decompose_nonlinearity(
        residual=residual,
        tangent_response=((1.0,), (0.0,), (0.0,)),
        covariance=covariance,
        transfer_id="TRANSFER-FIXTURE",
        mask_id="MASK-FIXTURE",
        covariance_id="COV-FIXTURE",
        candidates=candidates,
        held_out_receipt=receipt,
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


def test_oriented_direction_keeps_sign_and_parity_type() -> None:
    positive = OrientedDirection((1.0, 0.0, 0.0), VectorParity.POLAR)
    negative = OrientedDirection((-1.0, 0.0, 0.0), VectorParity.POLAR)
    axial = OrientedDirection((1.0, 0.0, 0.0), VectorParity.AXIAL)
    assert positive.signed_dot(negative) == -1.0
    with pytest.raises(OrbitNonlinearityError, match="matching"):
        positive.signed_dot(axial)


def test_rank_comes_from_supplied_response_and_exposes_wide_null() -> None:
    report = measure_response_rank(
        response=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        covariance=np.eye(2),
        transfer_id="T",
        mask_id="M",
        covariance_id="C",
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
            transfer_id="T",
            mask_id="M",
            covariance_id=f"C-{scale}",
        )
        for scale in (1e-30, 1.0, 1e30)
    ]
    assert [report.rank for report in reports] == [2, 2, 2]


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
        receipt="HOLDOUT-PR251",
    )
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
    )
    assert report.found_equiv_status == FOUND_EQUIV_STATUS
    assert report.found_equiv_prerequisite == FOUND_EQUIV_PREREQUISITE
    assert "family identification" in " ".join(report.forbidden_use)


def test_report_constructor_cannot_forge_nonlinear_compatibility() -> None:
    linear = _nonlinearity((2.0, 0.0, 0.0))
    with pytest.raises(OrbitNonlinearityError, match="does not follow"):
        replace(
            linear,
            attribution_status=(
                NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
            ),
            held_out_receipt="FORGED",
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
        receipt="HOLDOUT-PR251",
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
    ),
)
def test_rank_rejects_boolean_and_nonfinite_response(bad: object) -> None:
    with pytest.raises(OrbitNonlinearityError):
        measure_response_rank(
            response=bad,
            covariance=np.eye(2),
            transfer_id="T",
            mask_id="M",
            covariance_id="C",
        )
