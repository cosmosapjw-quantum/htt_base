"""PR-250 joint-anchor, partial-ID, finite-covariance and prior contracts."""
from __future__ import annotations

from dataclasses import replace
import math
from fractions import Fraction

import numpy as np
import pytest
from scipy.stats import beta

from common.joint_feasible_set import exact_support
from common.revival_estcov_evalue import (
    HARTLAP_INFERENCE_ROLE,
    hartlap_stress,
)
from common.statistical_foundations import (
    AnchorConditioning,
    IdentificationStatus,
    NullKind,
    ScalarRange,
    StressStatus,
)
from common.statistical_inference import (
    CovarianceLikelihoodStatus,
    CrossCovarianceStatus,
    CrossFitFold,
    FactorizationPremise,
    FiellerConfidenceSet,
    FiellerSetKind,
    FiniteCovarianceAssumptions,
    FiniteCovarianceLikelihoodResult,
    InferenceLane,
    JointRandomAnchorEstimate,
    NullSectorReport,
    PriorLearningMode,
    PriorLearningReceipt,
    RatioInferenceResult,
    StatisticalInferenceError,
    assemble_block_covariance,
    covariance_marginalized_t_loglikelihood,
    fieller_ratio,
)
from common.partial_id_coverage import coverage_mc


def _joint(
    *,
    numerator: float = 2.0,
    anchor: float = 4.0,
    var_n: float = 0.04,
    var_d: float = 0.04,
    covariance: float | None = 0.01,
    covariance_status: CrossCovarianceStatus = CrossCovarianceStatus.BOUND,
    identification: IdentificationStatus = IdentificationStatus.POINT_IDENTIFIED,
) -> JointRandomAnchorEstimate:
    return JointRandomAnchorEstimate(
        numerator_estimate=numerator,
        anchor_estimate=anchor,
        numerator_variance=var_n,
        anchor_variance=var_d,
        cross_covariance=covariance,
        cross_covariance_status=covariance_status,
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
        identification_status=identification,
        shared_data_id="joint-fixture-1",
        assumptions=("joint asymptotic normal approximation",),
    )


def _assumptions(**overrides: bool) -> FiniteCovarianceAssumptions:
    values = {
        "gaussian_simulations": True,
        "wishart_sample_covariance": True,
        "observation_independent_of_simulations": True,
        "known_simulation_mean": True,
    }
    values.update(overrides)
    return FiniteCovarianceAssumptions(**values)


def test_random_anchor_ratio_is_joint_and_channel_covariance_matters() -> None:
    positive = fieller_ratio(
        _joint(covariance=0.015),
        confidence_level=0.95,
        atol=1e-12,
        rtol=1e-12,
        lane=InferenceLane.CLAIM_BEARING,
    )
    negative = fieller_ratio(
        _joint(covariance=-0.015),
        confidence_level=0.95,
        atol=1e-12,
        rtol=1e-12,
        lane=InferenceLane.CLAIM_BEARING,
    )
    assert positive.status is StressStatus.DEFINED
    assert positive.point_estimate == pytest.approx(0.5)
    assert positive.confidence_set.kind is FiellerSetKind.BOUNDED
    assert positive.confidence_set != negative.confidence_set
    with pytest.raises(StatisticalInferenceError, match="positive semidefinite"):
        _joint(var_n=0.0, var_d=0.0, covariance=1e-10)


@pytest.mark.parametrize("scale", (1.0, 1.0e-9, 1.0e9))
def test_deterministic_fieller_ratio_is_scale_invariant(scale: float) -> None:
    result = fieller_ratio(
        _joint(
            numerator=2.0 * scale,
            anchor=1.0 * scale,
            var_n=0.0,
            var_d=0.0,
            covariance=0.0,
        ),
        confidence_level=0.95,
        atol=0.0,
        rtol=0.0,
        lane=InferenceLane.CLAIM_BEARING,
    )
    assert result.status is StressStatus.DEFINED
    assert result.point_estimate == pytest.approx(2.0)
    assert result.confidence_set.kind is FiellerSetKind.BOUNDED
    assert result.confidence_set.intervals == (ScalarRange(2.0, 2.0),)


def test_zero_crossing_denominator_never_returns_finite_ratio() -> None:
    result = fieller_ratio(
        _joint(anchor=0.05, var_d=0.25, covariance=0.0),
        confidence_level=0.95,
        atol=1e-8,
        rtol=1e-8,
        lane=InferenceLane.CLAIM_BEARING,
    )
    assert result.status is StressStatus.RATIO_UNIDENTIFIED
    assert result.point_estimate is None
    assert result.confidence_set.is_unbounded
    assert not result.denominator_interval.separated_from_zero(
        atol=result.atol, rtol=result.rtol
    )


def test_inference_results_are_factory_only_and_cannot_forge_claim_states() -> None:
    defined = fieller_ratio(
        _joint(),
        confidence_level=0.95,
        atol=1e-12,
        rtol=1e-12,
        lane=InferenceLane.CLAIM_BEARING,
    )
    with pytest.raises(
        StatisticalInferenceError,
        match="must be created by fieller_ratio",
    ):
        RatioInferenceResult(
            status=StressStatus.DEFINED,
            point_estimate=1.0,
            confidence_set=FiellerConfidenceSet(
                FiellerSetKind.BOUNDED,
                (ScalarRange(-1.0, 1.0),),
            ),
            denominator_interval=ScalarRange(-1.0, 1.0),
            confidence_level=2.0,
            atol=-1.0,
            rtol=-1.0,
            lane=InferenceLane.CLAIM_BEARING,
            conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
            assumptions=defined.assumptions,
        )
    with pytest.raises(
        StatisticalInferenceError,
        match="must be created by fieller_ratio",
    ):
        replace(defined, point_estimate=999.0)

    likelihood = covariance_marginalized_t_loglikelihood(
        [1.0],
        [[2.0]],
        n_simulations=100,
        assumptions=_assumptions(),
        rcond=1e-12,
        null_atol=1e-12,
    )
    with pytest.raises(
        StatisticalInferenceError,
        match="must be created by covariance_marginalized",
    ):
        FiniteCovarianceLikelihoodResult(
            status=CovarianceLikelihoodStatus.DEFINED,
            log_likelihood=float("nan"),
            chi2_supported=-1.0,
            rank=-1,
            null_residual_norm=0.0,
            n_simulations=100,
            method="forged",
            assumptions=_assumptions(),
            rcond=1e-12,
            null_atol=1e-12,
            evidence_null_atol_ceiling=likelihood.evidence_null_atol_ceiling,
        )
    with pytest.raises(
        StatisticalInferenceError,
        match="must be created by covariance_marginalized",
    ):
        replace(likelihood, rank=-1)


def test_missing_cross_covariance_fails_claim_bearing_lane() -> None:
    missing = _joint(
        covariance=None,
        covariance_status=CrossCovarianceStatus.MISSING,
    )
    with pytest.raises(StatisticalInferenceError, match="cross covariance"):
        fieller_ratio(
            missing,
            confidence_level=0.95,
            atol=0.0,
            rtol=1e-12,
            lane=InferenceLane.CLAIM_BEARING,
        )
    factorized = JointRandomAnchorEstimate(
        **{
            **missing.__dict__,
            "cross_covariance": 0.0,
            "cross_covariance_status": CrossCovarianceStatus.EXPLORATORY_FACTORIZED,
            "assumptions": ("explicit exploratory factorization assumption",),
        }
    )
    exploratory = fieller_ratio(
        factorized,
        confidence_level=0.95,
        atol=0.0,
        rtol=1e-12,
        lane=InferenceLane.EXPLORATORY,
    )
    assert exploratory.lane is InferenceLane.EXPLORATORY


def test_nonidentified_numerator_returns_set_status_not_point() -> None:
    for status in (
        IdentificationStatus.PARTIALLY_IDENTIFIED,
        IdentificationStatus.NON_IDENTIFIED,
        IdentificationStatus.EMPTY,
    ):
        result = fieller_ratio(
            _joint(identification=status),
            confidence_level=0.95,
            atol=0.0,
            rtol=1e-12,
            lane=InferenceLane.CLAIM_BEARING,
        )
        assert result.status is StressStatus.NUMERATOR_UNIDENTIFIED
        assert result.point_estimate is None


def test_exact_support_preserves_recession_without_big_m() -> None:
    result = exact_support(
        [Fraction(1)],
        [[Fraction(-1)]],
        [Fraction(0)],
    )
    assert result["exact_lo"] == 0
    assert result["exact_hi"] == math.inf
    assert result["upper_unbounded"] is True
    assert result["topology"] == "UNBOUNDED"


def test_covariance_marginalized_t_supported_quotient_and_null_residual() -> None:
    defined = covariance_marginalized_t_loglikelihood(
        [1.0, 0.0],
        [[2.0, 0.0], [0.0, 0.0]],
        n_simulations=100,
        assumptions=_assumptions(),
        rcond=1e-12,
        null_atol=1e-12,
    )
    assert defined.status is CovarianceLikelihoodStatus.DEFINED
    assert defined.rank == 1
    assert defined.chi2_supported == pytest.approx(0.5)
    assert defined.rcond == 1e-12
    assert defined.null_atol == 1e-12
    assert defined.null_atol <= defined.evidence_null_atol_ceiling
    outside = covariance_marginalized_t_loglikelihood(
        [1.0, 0.1],
        [[2.0, 0.0], [0.0, 0.0]],
        n_simulations=100,
        assumptions=_assumptions(),
        rcond=1e-12,
        null_atol=1e-12,
    )
    assert outside.status is CovarianceLikelihoodStatus.OUTSIDE_SUPPORTED_QUOTIENT
    assert outside.log_likelihood is None


def test_accepted_covariance_roundoff_is_orientation_invariant() -> None:
    covariance = np.array([[2.0, 0.25], [0.250000001, 1.0]])
    direct = covariance_marginalized_t_loglikelihood(
        [0.4, -0.3],
        covariance,
        n_simulations=100,
        assumptions=_assumptions(),
        rcond=1e-8,
        null_atol=1e-12,
    )
    transposed = covariance_marginalized_t_loglikelihood(
        [0.4, -0.3],
        covariance.T,
        n_simulations=100,
        assumptions=_assumptions(),
        rcond=1e-8,
        null_atol=1e-12,
    )
    assert direct.log_likelihood == transposed.log_likelihood
    assert direct.chi2_supported == transposed.chi2_supported


def test_evidence_covariance_tolerances_cannot_erase_support() -> None:
    with pytest.raises(
        StatisticalInferenceError,
        match="rcond must be less than 1",
    ):
        covariance_marginalized_t_loglikelihood(
            [100.0],
            [[1.0]],
            n_simulations=100,
            assumptions=_assumptions(),
            rcond=1.0,
            null_atol=100.0,
        )
    with pytest.raises(
        StatisticalInferenceError,
        match="null_atol exceeds",
    ):
        covariance_marginalized_t_loglikelihood(
            [100.0],
            [[1.0]],
            n_simulations=100,
            assumptions=_assumptions(),
            rcond=1e-12,
            null_atol=100.0,
        )
    with pytest.raises(
        StatisticalInferenceError,
        match="at least one supported direction",
    ):
        covariance_marginalized_t_loglikelihood(
            [0.0],
            [[0.0]],
            n_simulations=100,
            assumptions=_assumptions(),
            rcond=1e-12,
            null_atol=0.0,
        )


def test_covariance_likelihood_rejects_nonfinite_derived_quadratic_form() -> None:
    with pytest.raises(
        StatisticalInferenceError,
        match="quadratic form is non-finite",
    ):
        covariance_marginalized_t_loglikelihood(
            [1e308],
            [[1.0]],
            n_simulations=100,
            assumptions=_assumptions(),
            rcond=1e-12,
            null_atol=0.0,
        )


def test_finite_covariance_t_approaches_gaussian_limit() -> None:
    covariance = np.array([[1.5, 0.2], [0.2, 0.8]])
    residual = np.array([0.4, -0.7])
    result = covariance_marginalized_t_loglikelihood(
        residual,
        covariance,
        n_simulations=1_000_000,
        assumptions=_assumptions(),
        rcond=1e-12,
        null_atol=1e-12,
    )
    sign, logdet = np.linalg.slogdet(covariance)
    gaussian = -0.5 * (
        2 * math.log(2 * math.pi)
        + logdet
        + residual @ np.linalg.solve(covariance, residual)
    )
    assert sign == 1
    assert result.log_likelihood == pytest.approx(gaussian, abs=3e-6)
    blocked = covariance_marginalized_t_loglikelihood(
        residual,
        covariance,
        n_simulations=50,
        assumptions=_assumptions(gaussian_simulations=False),
        rcond=1e-12,
        null_atol=1e-12,
    )
    assert blocked.status is CovarianceLikelihoodStatus.BLOCKED_ASSUMPTIONS


def test_cross_block_covariance_is_never_silently_zeroed() -> None:
    blocks = {"anchor": [[1.0]], "numerator": [[2.0]]}
    with pytest.raises(StatisticalInferenceError, match="missing cross"):
        assemble_block_covariance(
            blocks,
            {},
            lane=InferenceLane.CLAIM_BEARING,
        )
    exploratory = assemble_block_covariance(
        blocks,
        {},
        lane=InferenceLane.EXPLORATORY,
        factorization_assumption=(
            FactorizationPremise.EXPLORATORY_ZERO_CROSS_COVARIANCE
        ),
    )
    assert exploratory.cross_covariance_status is (
        CrossCovarianceStatus.EXPLORATORY_FACTORIZED
    )
    with pytest.raises(StatisticalInferenceError, match="positive semidefinite"):
        assemble_block_covariance(
            blocks,
            {("anchor", "numerator"): [[2.0]]},
            lane=InferenceLane.CLAIM_BEARING,
        )


def test_empirical_bayes_requires_split_or_cross_fit() -> None:
    with pytest.raises(
        StatisticalInferenceError,
        match="must not be data learned",
    ):
        PriorLearningReceipt(
            mode=PriorLearningMode.FIXED_PHYSICAL,
            prior_center=1.0,
            data_dependent=False,
            selection_ids=(),
            estimation_ids=("hidden-estimation-use",),
        )
    with pytest.raises(StatisticalInferenceError, match="disjoint"):
        PriorLearningReceipt(
            mode=PriorLearningMode.SPLIT_SAMPLE,
            prior_center=1.0,
            data_dependent=True,
            selection_ids=("same",),
            estimation_ids=("same",),
        )
    split = PriorLearningReceipt(
        mode=PriorLearningMode.SPLIT_SAMPLE,
        prior_center=1.0,
        data_dependent=True,
        selection_ids=("selection",),
        estimation_ids=("estimation",),
    )
    assert split.allowed_use == ("conditional prior-sensitivity analysis",)
    cross_fit = PriorLearningReceipt(
        mode=PriorLearningMode.CROSS_FIT,
        prior_center=1.0,
        data_dependent=True,
        selection_ids=("a", "b"),
        estimation_ids=("a", "b"),
        folds=(
            CrossFitFold(selection_ids=("b",), estimation_ids=("a",)),
            CrossFitFold(selection_ids=("a",), estimation_ids=("b",)),
        ),
    )
    assert cross_fit.mode is PriorLearningMode.CROSS_FIT
    with pytest.raises(StatisticalInferenceError, match="may not select"):
        CrossFitFold(selection_ids=("same",), estimation_ids=("same",))
    with pytest.raises(StatisticalInferenceError, match="at least two"):
        PriorLearningReceipt(
            mode=PriorLearningMode.CROSS_FIT,
            prior_center=1.0,
            data_dependent=True,
            selection_ids=("train",),
            estimation_ids=("held-out",),
            folds=(
                CrossFitFold(
                    selection_ids=("train",),
                    estimation_ids=("held-out",),
                ),
            ),
        )
    mutable_folds = [
        CrossFitFold(selection_ids=("b",), estimation_ids=("a",)),
        CrossFitFold(selection_ids=("a",), estimation_ids=("b",)),
    ]
    frozen = PriorLearningReceipt(
        mode=PriorLearningMode.CROSS_FIT,
        prior_center=1.0,
        data_dependent=True,
        selection_ids=("a", "b"),
        estimation_ids=("a", "b"),
        folds=mutable_folds,
    )
    mutable_folds.append(mutable_folds[0])
    assert len(frozen.folds) == 2


def test_null_sector_cannot_create_posterior_evidence() -> None:
    report = NullSectorReport(
        null_kind=NullKind.STRUCTURAL,
        bounds=ScalarRange(-math.inf, math.inf),
        prior_sensitivity_class="all proper symmetric physical priors",
    )
    assert report.posterior_created is False
    with pytest.raises(StatisticalInferenceError, match="never posterior"):
        NullSectorReport(
            null_kind=NullKind.LEADING_ORDER,
            bounds=ScalarRange(-1.0, 1.0),
            prior_sensitivity_class="bounded class",
            posterior_created=True,
        )


def test_hartlap_is_diagnostic_and_unknown_coverage_method_fails() -> None:
    diagnostic = hartlap_stress(nrep=20, m=2, nsim=20)
    assert HARTLAP_INFERENCE_ROLE == "DIAGNOSTIC_COMPARATOR_ONLY"
    assert "inference_role" not in diagnostic
    with pytest.raises(ValueError, match="method must be"):
        coverage_mc(
            half_width=1.0,
            sigma=1.0,
            alpha=0.05,
            reps=1,
            seed=1,
            method="typo",
        )
    with pytest.raises(ValueError, match="nsim > m"):
        hartlap_stress(nrep=1, m=4, nsim=6)


def test_preregistered_ratio_dgp_seed_grid_preserves_coverage_and_status() -> None:
    def contains(result, value: float) -> bool:
        return any(
            interval.lower <= value <= interval.upper
            for interval in result.confidence_set.intervals
        )

    regimes = (
        ("point", np.array([1.0, 2.0]), np.array([[0.04, 0.01], [0.01, 0.04]])),
        ("weak", np.array([0.1, 0.2]), np.array([[0.04, 0.01], [0.01, 0.04]])),
        ("active_constraint", np.array([0.0, 2.0]), np.array([[0.04, 0.0], [0.0, 0.04]])),
    )
    preregistered_seeds = tuple(range(250_000, 250_010))
    draws_per_cell = 5_000
    for regime_index, (name, mean, covariance) in enumerate(regimes):
        for seed in preregistered_seeds:
            rng = np.random.default_rng(seed + 100 * regime_index)
            covered = 0
            for numerator, anchor in rng.multivariate_normal(
                mean, covariance, size=draws_per_cell
            ):
                result = fieller_ratio(
                    _joint(
                        numerator=float(numerator),
                        anchor=float(anchor),
                        var_n=float(covariance[0, 0]),
                        var_d=float(covariance[1, 1]),
                        covariance=float(covariance[0, 1]),
                    ),
                    confidence_level=0.95,
                    atol=1e-12,
                    rtol=1e-12,
                    lane=InferenceLane.CLAIM_BEARING,
                )
                covered += contains(result, float(mean[0] / mean[1]))
            cp_lower_99 = (
                0.0
                if covered == 0
                else float(
                    beta.ppf(
                        0.01,
                        covered,
                        draws_per_cell - covered + 1,
                    )
                )
            )
            assert cp_lower_99 >= 0.93, (name, seed, cp_lower_99)

    for status in (
        IdentificationStatus.PARTIALLY_IDENTIFIED,
        IdentificationStatus.NON_IDENTIFIED,
    ):
        result = fieller_ratio(
            _joint(identification=status),
            confidence_level=0.95,
            atol=1e-12,
            rtol=1e-12,
            lane=InferenceLane.CLAIM_BEARING,
        )
        assert result.status is StressStatus.NUMERATOR_UNIDENTIFIED


def test_finite_n_t_matches_independent_formula_and_not_gaussian() -> None:
    covariance = np.array([[1.5, 0.2], [0.2, 0.8]])
    residual = np.array([0.4, -0.7])
    n_simulations = 8
    result = covariance_marginalized_t_loglikelihood(
        residual,
        covariance,
        n_simulations=n_simulations,
        assumptions=_assumptions(known_simulation_mean=True),
        rcond=1e-12,
        null_atol=1e-12,
    )
    rank = 2
    chi2 = float(residual @ np.linalg.solve(covariance, residual))
    logdet = float(np.linalg.slogdet(covariance)[1])
    expected = (
        math.lgamma((n_simulations + 1.0) / 2.0)
        - math.lgamma((n_simulations - rank + 1.0) / 2.0)
        - 0.5 * rank * math.log(math.pi * n_simulations)
        - 0.5 * logdet
        - 0.5
        * (n_simulations + 1.0)
        * math.log1p(chi2 / n_simulations)
    )
    gaussian = -0.5 * (
        rank * math.log(2.0 * math.pi) + logdet + chi2
    )
    assert result.log_likelihood == pytest.approx(expected, abs=1e-14)
    assert abs(float(result.log_likelihood) - gaussian) > 1e-3
