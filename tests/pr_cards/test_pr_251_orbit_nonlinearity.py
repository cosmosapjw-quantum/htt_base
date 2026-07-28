from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.orbit_nonlinearity import (  # noqa: E402
    CandidateEvaluation,
    CandidateKind,
    DEPARTURE_O3_PARITY,
    InvariantCatalogSpec,
    NonlinearityAttributionStatus,
    OrbitNonlinearityError,
    OrientedDirection,
    PR251_INVARIANT_NAMES,
    ResponseRankReport,
    STF5_CARTESIAN_BASIS,
    VectorParity,
    build_candidate_independence_receipt,
    decompose_nonlinearity,
    evaluate_candidate_predictions,
    orbit_invariants,
    revalidate_nonlinearity_report,
)
from common.statistical_foundations import (  # noqa: E402
    AnchorAuthorityKind,
    AnchorConditioning,
    AnchorStatus,
    DepartureState,
    MESAnchorSpec,
    ScalarRange,
    evaluate_sector_stress,
)
from htt.departure.multicomponent_response import rank_gain_ladder  # noqa: E402
from obsstat.lowell_poles import AntipodalAxis  # noqa: E402


TRANSFER_ID = "sha256:" + "4" * 64
MASK_ID = "sha256:" + "5" * 64
COVARIANCE_ID = "sha256:" + "6" * 64
TRAINING_DATA_ID = "sha256:" + "7" * 64
SPLIT_RECEIPT_ID = "sha256:" + "8" * 64


def _state(beta: tuple[float, float, float]) -> DepartureState:
    return DepartureState(
        sigma_ab=(0.4, -0.2, 0.1, 0.3, -0.5),
        omega_a=(0.2, -0.1, 0.6),
        beta_a=beta,
        delta_omega_k=0.01,
        frame="fixture frame",
        congruence="geodesic",
        epoch_window="fixture epoch",
        averaging_scale="fixture scale",
        basis=STF5_CARTESIAN_BASIS,
        units="dimensionless",
        parity=DEPARTURE_O3_PARITY,
        perturbative_order="diagnostic fixture",
    )


def _catalog() -> InvariantCatalogSpec:
    return InvariantCatalogSpec(
        catalog_id="PR251-CATALOG-V1",
        invariant_names=PR251_INVARIANT_NAMES,
        multiplicity_method="Westfall-Young max-T fixture",
        alignment_null_id="PR251-ALIGNMENT-NULL",
        preregistration_id="PR251",
    )


def _candidate(
    *,
    candidate_id: str,
    kind: CandidateKind,
    held_out_prediction: object,
    held_out_target: object,
    matched_injection_prediction: object,
    matched_injection_target: object,
    model_config_id: str,
    fit_index: int,
) -> CandidateEvaluation:
    receipt = build_candidate_independence_receipt(
        candidate_id=candidate_id,
        model_config_id=model_config_id,
        training_data_id=TRAINING_DATA_ID,
        held_out_target=held_out_target,
        matched_injection_target=matched_injection_target,
        fit_receipt_id="sha256:" + f"{1000 + fit_index:064x}",
        split_receipt_id=SPLIT_RECEIPT_ID,
    )
    return evaluate_candidate_predictions(
        candidate_id=candidate_id,
        kind=kind,
        held_out_prediction=held_out_prediction,
        held_out_target=held_out_target,
        matched_injection_prediction=matched_injection_prediction,
        matched_injection_target=matched_injection_target,
        model_config_id=model_config_id,
        independence_receipt=receipt,
    )


def _competition(
    *,
    winner: CandidateKind,
) -> tuple[CandidateEvaluation, ...]:
    kinds = (
        CandidateKind.NONLINEAR,
        CandidateKind.LINEAR,
        CandidateKind.SYSTEMATICS,
        CandidateKind.FRAME_MISMATCH,
        CandidateKind.DERIVATIVE_FAILURE,
    )
    return tuple(
        _candidate(
            candidate_id=f"{kind.value}-CANDIDATE",
            kind=kind,
            held_out_prediction=(
                (0.01, 0.0) if kind is winner else (3.0, 0.0)
            ),
            held_out_target=(0.0, 0.0),
            matched_injection_prediction=(
                (1.01, 1.0) if kind is winner else (4.0, 1.0)
            ),
            matched_injection_target=(1.0, 1.0),
            model_config_id=(
                "sha256:" + f"{kinds.index(kind) + 10:064x}"
            ),
            fit_index=kinds.index(kind),
        )
        for kind in kinds
    )


def _external_sigma_stress(numerator: float):
    anchor = MESAnchorSpec(
        anchor_id="EXTERNAL-SIGMA-ORBIT-FIXTURE",
        value=1.0,
        authority_kind=AnchorAuthorityKind.EXTERNAL_PHYSICAL,
        target_sector="Sigma2",
        target_invariant="sigma_ab_sigma_ab_over_6H2",
        frame="orbit fixture frame",
        congruence="geodesic",
        normalization="Sigma2_std",
        perturbative_order="registered fixture order",
        branch="external fixture branch",
        attribution="PR-251 separation fixture",
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
        validity_domain="unit-test domain",
        source_equations=("fixture equation",),
        shared_nuisance=(),
        status=AnchorStatus.VERIFIED,
        allowed_use=("channel-matched stress",),
        forbidden_use=("FLRW converse",),
    )
    return evaluate_sector_stress(
        sector="Sigma2",
        numerator=ScalarRange(numerator, numerator),
        numerator_channel_key=anchor.channel_key,
        anchor=anchor,
    )


def test_candidate_evaluation_rejects_role_salted_target_reuse() -> None:
    """Byte-identical targets cannot serve as two evidence roles."""

    shared_target = np.array([0.25, -0.5, 1.25], dtype=np.float64)
    with pytest.raises(
        OrbitNonlinearityError,
        match="data identities must be distinct",
    ):
        build_candidate_independence_receipt(
            candidate_id="nonlinear-reused-target",
            model_config_id="sha256:" + "a" * 64,
            training_data_id=TRAINING_DATA_ID,
            held_out_target=shared_target,
            matched_injection_target=shared_target.copy(),
            fit_receipt_id="sha256:" + "b" * 64,
            split_receipt_id=SPLIT_RECEIPT_ID,
        )


def test_candidate_evaluation_rejects_exact_target_copy() -> None:
    candidate_id = "nonlinear-target-copy"
    model_config_id = "sha256:" + "c" * 64
    held_target = np.array([0.25, -0.5, 1.25], dtype=np.float64)
    injection_target = np.array([0.4, 0.8, -0.2], dtype=np.float64)
    receipt = build_candidate_independence_receipt(
        candidate_id=candidate_id,
        model_config_id=model_config_id,
        training_data_id=TRAINING_DATA_ID,
        held_out_target=held_target,
        matched_injection_target=injection_target,
        fit_receipt_id="sha256:" + "d" * 64,
        split_receipt_id=SPLIT_RECEIPT_ID,
    )
    with pytest.raises(
        OrbitNonlinearityError,
        match="target-copy independence is unverifiable",
    ):
        evaluate_candidate_predictions(
            candidate_id=candidate_id,
            kind=CandidateKind.NONLINEAR,
            held_out_prediction=held_target.copy(),
            held_out_target=held_target,
            matched_injection_prediction=injection_target.copy(),
            matched_injection_target=injection_target,
            model_config_id=model_config_id,
            independence_receipt=receipt,
        )


@pytest.mark.parametrize("copied_role", ("held_out", "matched_injection"))
def test_candidate_evaluation_rejects_signed_zero_target_copy(
    copied_role: str,
) -> None:
    candidate_id = f"nonlinear-signed-zero-{copied_role}"
    model_config_id = "sha256:" + "e" * 64
    held_target = np.array([0.0, 1.0], dtype=np.float64)
    injection_target = np.array([2.0, 0.0], dtype=np.float64)
    receipt = build_candidate_independence_receipt(
        candidate_id=candidate_id,
        model_config_id=model_config_id,
        training_data_id=TRAINING_DATA_ID,
        held_out_target=held_target,
        matched_injection_target=injection_target,
        fit_receipt_id="sha256:" + "f" * 64,
        split_receipt_id=SPLIT_RECEIPT_ID,
    )
    held_prediction = (
        np.array([-0.0, 1.0])
        if copied_role == "held_out"
        else np.array([1.0, 2.0])
    )
    injection_prediction = (
        np.array([3.0, 1.0])
        if copied_role == "held_out"
        else np.array([2.0, -0.0])
    )
    with pytest.raises(
        OrbitNonlinearityError,
        match="target-copy independence is unverifiable",
    ):
        evaluate_candidate_predictions(
            candidate_id=candidate_id,
            kind=CandidateKind.NONLINEAR,
            held_out_prediction=held_prediction,
            held_out_target=held_target,
            matched_injection_prediction=injection_prediction,
            matched_injection_target=injection_target,
            model_config_id=model_config_id,
            independence_receipt=receipt,
        )


def test_nonlinearity_rejects_candidate_evaluation_subclasses() -> None:
    legitimate = _competition(winner=CandidateKind.NONLINEAR)[0]

    class ForgedEvaluation(CandidateEvaluation):
        def __init__(self, source: CandidateEvaluation) -> None:
            for name in (
                "candidate_id",
                "kind",
                "held_out_score",
                "matched_injection_score",
                "held_out_data_id",
                "matched_injection_data_id",
                "model_config_id",
                "scoring_rule",
                "held_out_prediction_id",
                "matched_injection_prediction_id",
                "independence_receipt",
                "evaluation_id",
            ):
                object.__setattr__(self, name, getattr(source, name))

    with pytest.raises(
        OrbitNonlinearityError,
        match="exact factory-derived CandidateEvaluation",
    ):
        _report(
            residual=(0.0, 1.0, 0.0),
            candidates=(ForgedEvaluation(legitimate),),
        )

    forged_exact = object.__new__(CandidateEvaluation)
    for name in (
        "candidate_id",
        "kind",
        "held_out_data_id",
        "matched_injection_data_id",
        "model_config_id",
        "scoring_rule",
        "held_out_prediction_id",
        "matched_injection_prediction_id",
        "independence_receipt",
    ):
        object.__setattr__(forged_exact, name, getattr(legitimate, name))
    object.__setattr__(forged_exact, "held_out_score", 10.0)
    object.__setattr__(forged_exact, "matched_injection_score", 10.0)
    object.__setattr__(
        forged_exact,
        "evaluation_id",
        "sha256:" + "9" * 64,
    )
    with pytest.raises(
        OrbitNonlinearityError,
        match="scores must be non-positive",
    ):
        _report(
            residual=(0.0, 1.0, 0.0),
            candidates=(forged_exact,),
        )


@pytest.mark.parametrize("use_subclass", (False, True))
def test_nonlinearity_rejects_forged_nested_response_rank(
    use_subclass: bool,
) -> None:
    from mio.reports import StatisticalFoundationResultCard

    legitimate = _report(residual=(1.0, 0.0, 0.0))
    rank = legitimate.response_rank

    class ForgedRank(ResponseRankReport):
        pass

    forged_type = ForgedRank if use_subclass else ResponseRankReport
    forged_rank = object.__new__(forged_type)
    for name, value in vars(rank).items():
        object.__setattr__(forged_rank, name, value)
    object.__setattr__(
        forged_rank,
        "allowed_use",
        ("evidence", "Bianchi family identification"),
    )

    forged_report = object.__new__(type(legitimate))
    for name, value in vars(legitimate).items():
        object.__setattr__(forged_report, name, value)
    object.__setattr__(forged_report, "response_rank", forged_rank)

    with pytest.raises(
        OrbitNonlinearityError,
        match=(
            "allowed_use must match|exact factory-derived ResponseRankReport|"
            "fields do not match a factory-derived value"
        ),
    ):
        revalidate_nonlinearity_report(forged_report)
    with pytest.raises(
        (OrbitNonlinearityError, ValueError),
        match="nonlinearity does not satisfy its constructor invariants",
    ):
        StatisticalFoundationResultCard(
            card_id=f"forged-rank-{use_subclass}",
            nonlinearity=forged_report,
        )


def test_nonlinearity_rederives_rank_from_bound_replay_inputs() -> None:
    legitimate = decompose_nonlinearity(
        residual=(1.0, 0.0, 0.0),
        tangent_response=((1.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        covariance=np.eye(3),
        transfer_id=TRANSFER_ID,
        mask_id=MASK_ID,
        covariance_id=COVARIANCE_ID,
        off_manifold_tolerance=1e-12,
        null_residual_tolerance=1e-12,
        nonlinear_gain_margin=1.0,
    )
    rank = legitimate.response_rank
    assert rank.rank == 1

    forged_rank = object.__new__(ResponseRankReport)
    for name, value in vars(rank).items():
        object.__setattr__(forged_rank, name, value)
    object.__setattr__(forged_rank, "rank", 2)
    object.__setattr__(forged_rank, "singular_values", (1.0, 0.5))
    object.__setattr__(forged_rank, "min_singular", 0.5)
    object.__setattr__(forged_rank, "nullspace", ())

    forged_report = object.__new__(type(legitimate))
    for name, value in vars(legitimate).items():
        object.__setattr__(forged_report, name, value)
    object.__setattr__(forged_report, "response_rank", forged_rank)
    object.__setattr__(
        forged_report,
        "attribution_status",
        NonlinearityAttributionStatus.LINEAR_COMPATIBLE,
    )
    object.__setattr__(
        forged_report,
        "attribution_rationale",
        "forged full-rank attribution",
    )

    with pytest.raises(
        OrbitNonlinearityError,
        match="fields do not match a factory-derived value",
    ):
        revalidate_nonlinearity_report(forged_report)


def test_outer_analysis_identity_rejects_factory_valid_rank_transplant() -> None:
    from mio.reports import StatisticalFoundationResultCard

    common = {
        "residual": (1.0, 0.0, 0.0),
        "covariance": np.eye(3),
        "transfer_id": TRANSFER_ID,
        "mask_id": MASK_ID,
        "covariance_id": COVARIANCE_ID,
        "off_manifold_tolerance": 1e-12,
        "null_residual_tolerance": 1e-12,
        "nonlinear_gain_margin": 1.0,
    }
    base = decompose_nonlinearity(
        tangent_response=((1.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        **common,
    )
    alternative = decompose_nonlinearity(
        tangent_response=((1.0, 0.0), (0.0, 1.0), (0.0, 0.0)),
        **common,
    )
    assert (
        base.attribution_status
        is NonlinearityAttributionStatus.NON_IDENTIFIED_RESPONSE
    )
    assert (
        alternative.attribution_status
        is NonlinearityAttributionStatus.LINEAR_COMPATIBLE
    )
    assert base.tangent_statistic == alternative.tangent_statistic
    assert base.perpendicular_statistic == alternative.perpendicular_statistic
    assert base.null_residual_sq == alternative.null_residual_sq
    assert base.response_rank.response_id != alternative.response_rank.response_id
    assert base.analysis_id != alternative.analysis_id
    assert revalidate_nonlinearity_report(alternative) == alternative

    forged = object.__new__(type(base))
    for name, value in vars(base).items():
        object.__setattr__(forged, name, value)
    object.__setattr__(forged, "response_rank", alternative.response_rank)
    object.__setattr__(
        forged, "attribution_status", alternative.attribution_status
    )
    object.__setattr__(
        forged, "attribution_rationale", alternative.attribution_rationale
    )

    with pytest.raises(
        OrbitNonlinearityError,
        match="fields do not match a factory-derived value",
    ):
        revalidate_nonlinearity_report(forged)
    with pytest.raises(
        ValueError,
        match="nonlinearity does not satisfy its constructor invariants",
    ):
        StatisticalFoundationResultCard(
            card_id="rank-transplant",
            nonlinearity=forged,
        )


def _report(
    *,
    residual: tuple[float, float, float],
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
        covariance=np.eye(3),
        transfer_id=TRANSFER_ID,
        mask_id=MASK_ID,
        covariance_id=COVARIANCE_ID,
        candidates=candidates,
        held_out_receipt=receipt,
        matched_injection_receipt=matched_injection_receipt,
        off_manifold_tolerance=1e-12,
        null_residual_tolerance=1e-12,
        nonlinear_gain_margin=1.0,
        delta_nl=1.0 if residual[1] else 0.0,
    )


def test_wide_rank_ladder_exposes_structural_null_as_zero() -> None:
    wide = np.array(((2.0, 0.0, 0.0), (0.0, 3.0, 0.0)))
    ladder = rank_gain_ladder({"wide": wide}, np.eye(2))
    assert ladder == [
        {"added": "wide", "rank": 2, "dimension": 3, "min_singular": 0.0}
    ]


def test_oriented_and_antipodal_axes_cannot_exchange_dot_semantics() -> None:
    oriented = OrientedDirection((1.0, 0.0, 0.0), VectorParity.POLAR)
    antipodal = AntipodalAxis((1.0, 0.0, 0.0))
    with pytest.raises(TypeError, match="OrientedDirection"):
        oriented.signed_dot(antipodal)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="AntipodalAxis"):
        antipodal.abs_dot(oriented)  # type: ignore[arg-type]


def test_equal_norm_relative_orientation_is_not_collapsed() -> None:
    x = orbit_invariants(_state((1.0, 0.0, 0.0)), _catalog())
    y = orbit_invariants(_state((0.0, 1.0, 0.0)), _catalog())
    assert x.beta2 == y.beta2 == 1.0
    assert x.beta_sigma_beta != y.beta_sigma_beta


@pytest.mark.parametrize(
    ("case", "residual", "winner", "expected"),
    (
        (
            "linear-compatible",
            (1.0, 0.0, 0.0),
            None,
            NonlinearityAttributionStatus.LINEAR_COMPATIBLE,
        ),
        (
            "nonlinear-within-anchor",
            (1.0, 1.0, 0.0),
            CandidateKind.NONLINEAR,
            NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE,
        ),
        (
            "nonlinear-plus-exceedance",
            (2.0, 1.0, 0.0),
            CandidateKind.NONLINEAR,
            NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE,
        ),
        (
            "frame-mismatch",
            (1.0, 1.0, 0.0),
            CandidateKind.FRAME_MISMATCH,
            NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD,
        ),
        (
            "derivative-failure",
            (1.0, 1.0, 0.0),
            CandidateKind.DERIVATIVE_FAILURE,
            NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD,
        ),
        (
            "systematics-mimic",
            (1.0, 1.0, 0.0),
            CandidateKind.SYSTEMATICS,
            NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD,
        ),
    ),
)
def test_preregistered_discrepancy_cases(
    case: str,
    residual: tuple[float, float, float],
    winner: CandidateKind | None,
    expected: NonlinearityAttributionStatus,
) -> None:
    del case
    candidates = () if winner is None else _competition(winner=winner)
    report = _report(
        residual=residual,
        candidates=candidates,
    )
    assert report.attribution_status is expected


def test_anchor_stress_and_nonlinearity_remain_separate_outputs() -> None:
    within = _external_sigma_stress(0.8)
    exceeded = _external_sigma_stress(1.2)
    nonlinear = _report(
        residual=(1.0, 1.0, 0.0),
        candidates=_competition(winner=CandidateKind.NONLINEAR),
    )
    assert nonlinear.attribution_status is NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
    assert within.exceedance != exceeded.exceedance
    assert not hasattr(nonlinear, "anchor_stress")


def test_nonlinear_candidate_is_selected_on_both_score_axes() -> None:
    """A held-out-only ranking must not hide the jointly eligible candidate."""

    kinds = (
        CandidateKind.NONLINEAR,
        CandidateKind.NONLINEAR,
        CandidateKind.LINEAR,
        CandidateKind.SYSTEMATICS,
        CandidateKind.FRAME_MISMATCH,
        CandidateKind.DERIVATIVE_FAILURE,
    )
    ids = (
        "nonlinear-held-only",
        "nonlinear-joint-winner",
        "linear-control",
        "systematics-control",
        "frame-control",
        "derivative-control",
    )
    held_predictions = (0.01, 1.0, 2.0, 2.0, 2.0, 2.0)
    injection_predictions = (13.0, 10.01, 12.0, 12.0, 12.0, 12.0)
    candidates = tuple(
        _candidate(
            candidate_id=candidate_id,
            kind=kind,
            held_out_prediction=(held_prediction,),
            held_out_target=(0.0,),
            matched_injection_prediction=(injection_prediction,),
            matched_injection_target=(10.0,),
            model_config_id="sha256:" + f"{index + 100:064x}",
            fit_index=index + 100,
        )
        for index, (
            candidate_id,
            kind,
            held_prediction,
            injection_prediction,
        ) in enumerate(
            zip(
                ids,
                kinds,
                held_predictions,
                injection_predictions,
            )
        )
    )
    report = _report(
        residual=(1.0, 1.0, 0.0),
        candidates=candidates,
    )
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
    )
    assert "nonlinear-joint-winner" in report.attribution_rationale


def test_incomplete_alternative_registry_cannot_authorize_nonlinear_label() -> None:
    incomplete = tuple(
        value
        for value in _competition(winner=CandidateKind.NONLINEAR)
        if value.kind is not CandidateKind.DERIVATIVE_FAILURE
    )
    report = _report(
        residual=(1.0, 1.0, 0.0),
        candidates=incomplete,
    )
    assert (
        report.attribution_status
        is NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD
    )


def test_catalog_requires_multiplicity_and_alignment_null_binding() -> None:
    with pytest.raises(OrbitNonlinearityError):
        InvariantCatalogSpec(
            catalog_id="PR251",
            invariant_names=PR251_INVARIANT_NAMES,
            multiplicity_method="",
            alignment_null_id="NULL",
            preregistration_id="PR251",
        )
