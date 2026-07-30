"""PR-265 law-typed conditional-exceedance contracts."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

from common.conditional_exceedance import (
    CONDITIONAL_EXCEEDANCE_CLAIM_CEILING,
    ConditionalExceedanceError,
    ConditioningSource,
    EnvelopeCertificate,
    ExceedanceLane,
    ExceedanceStatus,
    PosteriorCalibrationStatus,
    SamplingLaw,
    build_conditional_exceedance_envelope,
    build_likelihood_objective,
    build_missing_probability_law_profile,
    build_null_calibrated_exceedance,
    build_posterior_calibration_report,
    build_posterior_exceedance,
    build_sampling_draws,
    build_sampling_law_spec,
    identified_vertex_id,
)
from common.statistical_foundations import (
    IdentificationStatus,
    IdentifiedDepartureSet,
    NullKind,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/research_program/vector_tensor/pr265_spec.yaml"
BACKLOG_PATH = ROOT / "docs/codex_handoff/pr_backlog.yaml"


def _null_law(
    *,
    conditioning: ConditioningSource = ConditioningSource.INJECTED,
):
    return build_sampling_law_spec(
        law_id="PR265-FIXED-MOCK-LAW",
        sampling_law=SamplingLaw.FIXED_INJECTION_MOCK,
        conditioning_source=conditioning,
        lane=ExceedanceLane.MIO_NULL,
        source_identity="PR265 preregistered synthetic null DGP",
        covariance_id="PR265-COVARIANCE",
        transfer_source="none",
        assumptions=("exchangeable draws under the declared null DGP",),
    )


def _posterior_law():
    return build_sampling_law_spec(
        law_id="PR265-POSTERIOR-PREDICTIVE-LAW",
        sampling_law=SamplingLaw.POSTERIOR_PREDICTIVE,
        conditioning_source=ConditioningSource.POSTERIOR,
        lane=ExceedanceLane.HTT_POSTERIOR,
        source_identity="PR265 explicit synthetic posterior",
        covariance_id="PR265-POSTERIOR-COVARIANCE",
        transfer_source="external_transfer",
        assumptions=("samples target the declared HTT posterior predictive",),
    )


def _draws(law, values, *, suffix: str = "BASE"):
    return build_sampling_draws(
        draws_id=f"PR265-DRAWS-{suffix}",
        law=law,
        values=values,
        source_artifact_id=f"PR265-SOURCE-{suffix}",
        sample_unit="dimensionless functional value",
    )


def _calibration(
    status: PosteriorCalibrationStatus = PosteriorCalibrationStatus.PASSED,
):
    return build_posterior_calibration_report(
        calibration_id=f"PR265-SBC-{status.value}",
        status=status,
        method="simulation-based calibration rank-uniformity",
        dgp_id="PR265-SYNTHETIC-DGP-V1",
        seed_family="PR265-SEEDS-0-63",
        tolerance=0.05,
        diagnostic_values=(0.48, 0.52, 0.04),
    )


def _identified(
    *,
    vertices=((-1.0,), (1.0,)),
    recession=(),
    status=IdentificationStatus.PARTIALLY_IDENTIFIED,
):
    return IdentifiedDepartureSet(
        coordinate_names=("eta",),
        vertices=vertices,
        recession_directions=recession,
        null_kinds=(NullKind.NONE,),
        assumptions=("PR265 convex vertex-recession representation",),
        status=status,
    )


def test_spec_and_backlog_bind_pr265_ownership_and_dependencies() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    backlog = yaml.safe_load(BACKLOG_PATH.read_text())
    card = next(card for card in backlog["prs"] if card["id"] == "PR-265")
    assert spec["work_unit_id"] == "PR-265"
    assert spec["dependencies"] == ["PR-264", "PR-250"]
    assert card["depends"] == ["PR-264", "PR-250"]
    assert spec["ownership"]["MIO"] == "matched-null and empirical laws only"
    assert spec["ownership"]["HTT"] == (
        "likelihood objectives and explicit posterior laws only"
    )
    assert spec["claim_boundary"]["ceiling"] == "diagnostic_only"


@pytest.mark.parametrize(
    ("law", "conditioning", "lane"),
    (
        (
            SamplingLaw.FIXED_INJECTION_MOCK,
            ConditioningSource.INJECTED,
            ExceedanceLane.MIO_NULL,
        ),
        (
            SamplingLaw.BOOTSTRAP_RESAMPLING,
            ConditioningSource.EXTERNALLY_ESTIMATED,
            ExceedanceLane.MIO_NULL,
        ),
        (
            SamplingLaw.PROFILE_LIKELIHOOD,
            ConditioningSource.PROFILED,
            ExceedanceLane.HTT_OBJECTIVE,
        ),
        (
            SamplingLaw.POSTERIOR_PREDICTIVE,
            ConditioningSource.POSTERIOR,
            ExceedanceLane.HTT_POSTERIOR,
        ),
        (
            SamplingLaw.OBSERVATIONAL_POSTERIOR_PUSHFORWARD,
            ConditioningSource.POSTERIOR,
            ExceedanceLane.HTT_POSTERIOR,
        ),
    ),
)
def test_all_declared_laws_have_one_non_interchangeable_lane(
    law,
    conditioning,
    lane,
) -> None:
    spec = build_sampling_law_spec(
        law_id=f"PR265-{law.value}",
        sampling_law=law,
        conditioning_source=conditioning,
        lane=lane,
        source_identity="PR265 exact source",
        covariance_id=None,
        transfer_source="none",
        assumptions=("PR265 declared law assumption",),
    )
    assert spec.lane is lane
    assert spec.probability_eligible is (
        law is not SamplingLaw.PROFILE_LIKELIHOOD
    )
    assert spec.content_id.startswith("sha256:")


def test_law_owner_and_conditioning_mutations_fail_closed() -> None:
    with pytest.raises(ConditionalExceedanceError, match="belongs to"):
        build_sampling_law_spec(
            law_id="PR265-FORGED-MIO-POSTERIOR",
            sampling_law=SamplingLaw.POSTERIOR_PREDICTIVE,
            conditioning_source=ConditioningSource.POSTERIOR,
            lane=ExceedanceLane.MIO_NULL,
            source_identity="forged",
            covariance_id=None,
            transfer_source="none",
            assumptions=("forged owner",),
        )
    with pytest.raises(ConditionalExceedanceError, match="incompatible"):
        build_sampling_law_spec(
            law_id="PR265-FORGED-CONDITIONING",
            sampling_law=SamplingLaw.FIXED_INJECTION_MOCK,
            conditioning_source=ConditioningSource.POSTERIOR,
            lane=ExceedanceLane.MIO_NULL,
            source_identity="forged",
            covariance_id=None,
            transfer_source="none",
            assumptions=("forged conditioning",),
        )


def test_profile_likelihood_is_an_objective_not_sampling_draws() -> None:
    law = build_sampling_law_spec(
        law_id="PR265-PROFILE-LAW",
        sampling_law=SamplingLaw.PROFILE_LIKELIHOOD,
        conditioning_source=ConditioningSource.PROFILED,
        lane=ExceedanceLane.HTT_OBJECTIVE,
        source_identity="PR265 profile surface",
        covariance_id="PR265-PROFILE-COVARIANCE",
        transfer_source="external_transfer",
        assumptions=("profile objective is not normalized as a law",),
    )
    objective = build_likelihood_objective(
        objective_id="PR265-PROFILE-OBJECTIVE",
        law=law,
        coordinate_names=("eta",),
        coordinates=((-1.0,), (0.0,), (1.0,)),
        objective_values=(2.0, 0.0, 2.0),
        optimizer_point=(0.0,),
        source_artifact_id="PR265-PROFILE-SOURCE",
    )
    assert objective.optimizer_point == (0.0,)
    assert "probability" not in objective.as_payload()
    with pytest.raises(
        ConditionalExceedanceError, match="not sampling draws"
    ):
        build_sampling_draws(
            draws_id="PR265-FORGED-DRAWS",
            law=law,
            values=(0.0,),
            source_artifact_id="PR265-PROFILE-SOURCE",
            sample_unit="objective",
        )
    with pytest.raises(
        ConditionalExceedanceError, match="requires sampling draws"
    ):
        build_null_calibrated_exceedance(
            profile_id="PR265-OBJECTIVE-AS-NULL",
            functional_id="pr264.tr_sigma2",
            thresholds=(0.0,),
            law=law,
            draws=objective,
            conditioning_id="PR265-PROFILED",
        )


def test_empirical_null_profile_is_tail_monotone_with_finite_dkw_band() -> None:
    law = _null_law()
    values = tuple((index + 0.5) / 100.0 for index in range(100))
    result = build_null_calibrated_exceedance(
        profile_id="PR265-NULL-PROFILE",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.2, 0.5, 0.8),
        law=law,
        draws=_draws(law, values),
        conditioning_id="PR265-INJECTED-ETA-0",
        alpha=0.05,
    )
    assert result.owner == "MIO"
    assert result.profile.status is ExceedanceStatus.DEFINED_POINT
    assert result.profile.point == pytest.approx((0.8, 0.5, 0.2))
    assert all(
        left >= right
        for left, right in zip(
            result.profile.point,
            result.profile.point[1:],
        )
    )
    assert result.coverage is not None
    expected_radius = math.sqrt(math.log(40.0) / 200.0)
    assert result.coverage.simultaneous_radius == pytest.approx(expected_radius)
    for truth, lower, upper in zip(
        (0.8, 0.5, 0.2),
        result.coverage.lower,
        result.coverage.upper,
        strict=True,
    ):
        assert lower <= truth <= upper


def test_strict_tail_rule_and_finite_draw_refusal_are_explicit() -> None:
    law = _null_law()
    exact = build_null_calibrated_exceedance(
        profile_id="PR265-STRICT-TAIL",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.5,),
        law=law,
        draws=_draws(law, (0.5, 0.6), suffix="STRICT"),
        conditioning_id="PR265-STRICT",
    )
    assert exact.profile.point == (0.5,)
    insufficient = build_null_calibrated_exceedance(
        profile_id="PR265-ONE-DRAW",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.5,),
        law=law,
        draws=_draws(law, (0.6,), suffix="ONE"),
        conditioning_id="PR265-ONE",
    )
    assert insufficient.profile.status is ExceedanceStatus.INSUFFICIENT_DRAWS
    assert insufficient.profile.point is None
    assert insufficient.coverage is None


def test_posterior_exceedance_requires_explicit_law_and_passed_calibration() -> None:
    law = _posterior_law()
    draws = _draws(law, (0.1, 0.2, 0.4, 0.8), suffix="POSTERIOR")
    passed = build_posterior_exceedance(
        profile_id="PR265-POSTERIOR",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.15, 0.5),
        law=law,
        draws=draws,
        conditioning_id="PR265-POSTERIOR-ETA",
        calibration=_calibration(),
    )
    assert passed.owner == "HTT"
    assert passed.profile.point == pytest.approx((0.75, 0.25))
    assert passed.profile.calibration_id is not None
    failed = build_posterior_exceedance(
        profile_id="PR265-POSTERIOR-BLOCKED",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.15, 0.5),
        law=law,
        draws=draws,
        conditioning_id="PR265-POSTERIOR-ETA",
        calibration=_calibration(PosteriorCalibrationStatus.FAILED),
    )
    assert failed.profile.status is (
        ExceedanceStatus.POSTERIOR_CALIBRATION_REQUIRED
    )
    assert failed.profile.point is None


def test_missing_probability_law_returns_typed_refusal_without_pi() -> None:
    profile = build_missing_probability_law_profile(
        profile_id="PR265-MISSING-LAW",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.1, 0.2),
        conditioning_id="PR265-UNKNOWN-CONDITIONING",
        reason="input artifact names no probability law",
    )
    assert profile.status is ExceedanceStatus.MISSING_PROBABILITY_LAW
    assert profile.sampling_law is None
    assert profile.point is None
    assert profile.lower is None
    assert profile.claim_ceiling == CONDITIONAL_EXCEEDANCE_CLAIM_CEILING


def test_bounded_monotone_identified_set_yields_only_an_envelope() -> None:
    law = _null_law(conditioning=ConditioningSource.IDENTIFIED_SET)
    identified = _identified()
    profiles = {}
    for vertex, values in (
        ((-1.0,), (0.1, 0.0, 0.0)),
        ((1.0,), (0.9, 0.5, 0.1)),
    ):
        result = build_null_calibrated_exceedance(
            profile_id=f"PR265-VERTEX-{vertex[0]}",
            functional_id="pr264.tr_sigma2",
            thresholds=(0.2, 0.5, 0.8),
            law=law,
            draws=_draws(law, values, suffix=f"VERTEX-{vertex[0]}"),
            conditioning_id=f"eta={vertex[0]}",
        )
        profiles[
            identified_vertex_id(identified.coordinate_names, vertex)
        ] = result.profile
    envelope = build_conditional_exceedance_envelope(
        profile_id="PR265-IDENTIFIED-ENVELOPE",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.2, 0.5, 0.8),
        identified_set=identified,
        profiles_by_vertex=profiles,
        certificate=EnvelopeCertificate.MONOTONE,
        conditioning_id="PR265-ETA-SET",
    )
    assert envelope.status is ExceedanceStatus.DEFINED_ENVELOPE
    assert envelope.point is None
    assert envelope.lower == pytest.approx((0.0, 0.0, 0.0))
    assert envelope.upper == pytest.approx((2 / 3, 1 / 3, 1 / 3))
    assert envelope.identified_set_id is not None


def test_quasi_convex_upper_alone_cannot_fabricate_lower_endpoint() -> None:
    refusal = build_conditional_exceedance_envelope(
        profile_id="PR265-ETA2-REFUSAL",
        functional_id="eta_squared_counterexample",
        thresholds=(0.5,),
        identified_set=_identified(),
        profiles_by_vertex={},
        certificate=EnvelopeCertificate.UPPER_QUASI_CONVEX_ONLY,
        conditioning_id="eta in conv{-1,+1}",
    )
    assert refusal.status is ExceedanceStatus.OPTIMIZER_REQUIRED
    assert refusal.lower is None
    assert "upper and lower" in refusal.refusal_reasons[0]


def test_unbounded_and_empty_identified_sets_never_return_one_pi() -> None:
    unbounded = build_conditional_exceedance_envelope(
        profile_id="PR265-UNBOUNDED",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.1,),
        identified_set=_identified(
            recession=((1.0,),),
            status=IdentificationStatus.NON_IDENTIFIED,
        ),
        profiles_by_vertex={},
        certificate=EnvelopeCertificate.MONOTONE,
        conditioning_id="PR265-UNBOUNDED-ETA",
    )
    assert unbounded.status is ExceedanceStatus.OPTIMIZER_REQUIRED
    empty = build_conditional_exceedance_envelope(
        profile_id="PR265-EMPTY",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.1,),
        identified_set=_identified(
            vertices=(),
            status=IdentificationStatus.EMPTY,
        ),
        profiles_by_vertex={},
        certificate=EnvelopeCertificate.MONOTONE,
        conditioning_id="PR265-EMPTY-ETA",
    )
    assert empty.status is ExceedanceStatus.EMPTY_IDENTIFIED_SET
    assert empty.point is None


@pytest.mark.parametrize(
    "target",
    (
        "law",
        "draws",
        "profile",
        "coverage",
        "null_wrapper",
        "objective",
        "calibration",
        "posterior_wrapper",
    ),
)
def test_post_construction_law_objective_and_result_mutations_are_refused(
    target: str,
) -> None:
    law = _null_law()
    draws = _draws(law, (0.1, 0.3, 0.5), suffix="MUTATION")
    result = build_null_calibrated_exceedance(
        profile_id="PR265-MUTATION",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.2,),
        law=law,
        draws=draws,
        conditioning_id="PR265-MUTATION",
    )
    posterior_law = _posterior_law()
    calibration = _calibration()
    objective_law = build_sampling_law_spec(
        law_id="PR265-MUTATED-OBJECTIVE-LAW",
        sampling_law=SamplingLaw.PROFILE_LIKELIHOOD,
        conditioning_source=ConditioningSource.PROFILED,
        lane=ExceedanceLane.HTT_OBJECTIVE,
        source_identity="PR265 objective",
        covariance_id=None,
        transfer_source="none",
        assumptions=("objective-only",),
    )
    objective = build_likelihood_objective(
        objective_id="PR265-MUTATED-OBJECTIVE",
        law=objective_law,
        coordinate_names=("eta",),
        coordinates=((0.0,), (1.0,)),
        objective_values=(0.0, 1.0),
        optimizer_point=(0.0,),
        source_artifact_id="PR265-OBJECTIVE",
    )
    if target == "law":
        object.__setattr__(law, "source_identity", "forged")
        with pytest.raises(ConditionalExceedanceError, match="identity drifted"):
            build_null_calibrated_exceedance(
                profile_id="PR265-FORGED-LAW",
                functional_id="pr264.tr_sigma2",
                thresholds=(0.2,),
                law=law,
                draws=draws,
                conditioning_id="PR265-FORGED",
            )
    elif target == "draws":
        object.__setattr__(draws, "values", (999.0,))
        with pytest.raises(ConditionalExceedanceError, match="identity drifted"):
            build_null_calibrated_exceedance(
                profile_id="PR265-FORGED-DRAWS",
                functional_id="pr264.tr_sigma2",
                thresholds=(0.2,),
                law=law,
                draws=draws,
                conditioning_id="PR265-FORGED",
            )
    elif target == "profile":
        object.__setattr__(result.profile, "point", (0.99,))
        with pytest.raises(ConditionalExceedanceError, match="identity drifted"):
            result.as_payload()
    elif target == "coverage":
        assert result.coverage is not None
        object.__setattr__(result.coverage, "lower", (0.99,))
        with pytest.raises(ConditionalExceedanceError, match="identity drifted"):
            result.as_payload()
    elif target == "null_wrapper":
        object.__setattr__(result, "owner", "HTT")
        with pytest.raises(ConditionalExceedanceError, match="identity drifted"):
            result.as_payload()
    elif target == "objective":
        object.__setattr__(objective, "objective_values", (0.0, 999.0))
        with pytest.raises(ConditionalExceedanceError, match="identity drifted"):
            objective.as_payload()
    elif target == "calibration":
        object.__setattr__(
            calibration,
            "status",
            PosteriorCalibrationStatus.FAILED,
        )
        with pytest.raises(ConditionalExceedanceError, match="identity drifted"):
            build_posterior_exceedance(
                profile_id="PR265-FORGED-CALIBRATION",
                functional_id="pr264.tr_sigma2",
                thresholds=(0.2,),
                law=posterior_law,
                draws=_draws(
                    posterior_law,
                    (0.1, 0.3),
                    suffix="CAL-MUTATION",
                ),
                conditioning_id="PR265-FORGED",
                calibration=calibration,
            )
    else:
        posterior = build_posterior_exceedance(
            profile_id="PR265-POSTERIOR-WRAPPER",
            functional_id="pr264.tr_sigma2",
            thresholds=(0.2,),
            law=posterior_law,
            draws=_draws(
                posterior_law,
                (0.1, 0.3),
                suffix="POSTERIOR-WRAPPER",
            ),
            conditioning_id="PR265-POSTERIOR-WRAPPER",
            calibration=calibration,
        )
        object.__setattr__(posterior, "owner", "MIO")
        with pytest.raises(ConditionalExceedanceError, match="identity drifted"):
            posterior.as_payload()


def test_mio_and_htt_public_surfaces_do_not_cross_own_probability_types() -> None:
    import htt.infer.conditional_exceedance as htt_lane
    import mio.formalism.conditional_exceedance as mio_lane

    assert mio_lane.NullCalibratedExceedance is not None
    assert not hasattr(mio_lane, "PosteriorExceedance")
    assert not hasattr(mio_lane, "build_posterior_exceedance")
    assert not hasattr(mio_lane, "LikelihoodObjective")
    assert htt_lane.PosteriorExceedance is not None
    assert htt_lane.LikelihoodObjective is not None
    assert not hasattr(htt_lane, "NullCalibratedExceedance")
    assert not hasattr(htt_lane, "build_null_calibrated_exceedance")


def test_no_active_surface_promotes_truth_native_or_family_semantics() -> None:
    profile = build_missing_probability_law_profile(
        profile_id="PR265-CLAIM-BOUNDARY",
        functional_id="pr264.tr_sigma2",
        thresholds=(0.1,),
        conditioning_id="PR265-NO-LAW",
        reason="law unavailable",
    )
    text = str(profile.as_payload()).lower()
    assert "truth probability" in text
    assert "native solver" in text
    assert "family identification" in text
    assert profile.claim_ceiling == "diagnostic_only"
