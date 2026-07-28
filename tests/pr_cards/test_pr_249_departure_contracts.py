"""PR-249 state, identified-set, stress and legacy-report contracts."""
from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest

from common.statistical_foundations import (
    AnchorAuthorityKind,
    AnchorConditioning,
    AnchorStatus,
    AnchorStressReport,
    BC1_LEGACY_PROJECTION,
    BC2_NO_REPRESENTATION_PROMOTION,
    BudgetRadiusStatus,
    DepartureState,
    DiagnosticScalarReport,
    IdentificationStatus,
    IdentifiedDepartureSet,
    LegacyProjectionReport,
    MESAnchorSpec,
    NullKind,
    ScalarRange,
    SectorStress,
    StatisticalFoundationError,
    StressStatus,
    SummaryDepartureState,
    W2_V2_ALIAS,
    build_anchor_stress_report,
    evaluate_sector_stress,
    im_critical_value,
)
from mio.formalism.physical_pushforward import (
    matrix_budget_radius,
    matrix_budget_radius_report,
)
from obsstat.egs3_coverage_strengthened import (
    im_critical_value as strengthened_im_critical_value,
)
from obsstat.egs3_graded_comparator import (
    graded_comparator,
    legacy_sector_filling,
)
from obsstat.egs3_identified_set import (
    im_critical_value as identified_set_im_critical_value,
)


def _external_anchor(
    value: float = 2.0,
    *,
    conditioning: AnchorConditioning = AnchorConditioning.ENSEMBLE_CALIBRATED,
) -> MESAnchorSpec:
    return MESAnchorSpec(
        anchor_id="EXTERNAL_SIGMA_TEST",
        value=value,
        authority_kind=AnchorAuthorityKind.EXTERNAL_PHYSICAL,
        target_sector="Sigma2",
        target_invariant="sigma_ab_sigma_ab_over_6H2",
        frame="test frame",
        congruence="test congruence",
        normalization="Sigma2_std",
        perturbative_order="registered order",
        branch="external branch",
        attribution="independent fixture",
        conditioning=conditioning,
        validity_domain="unit-test domain",
        source_equations=("fixture eq 1",),
        shared_nuisance=(),
        status=AnchorStatus.VERIFIED,
        allowed_use=("channel-matched stress",),
        forbidden_use=("FLRW converse",),
    )


def test_departure_state_is_immutable_and_metadata_complete() -> None:
    source = [1.0, 0.0, 0.0, 0.0, -1.0]
    state = DepartureState(
        sigma_ab=source,
        omega_a=(0.1, 0.2, 0.3),
        beta_a=(0.4, 0.5, 0.6),
        delta_omega_k=-0.2,
        frame="registered tetrad",
        congruence="geodesic",
        epoch_window="z in [0, 0.1]",
        averaging_scale="100 Mpc",
        basis="stf5-cartesian-v1",
        units="dimensionless H-normalized",
        parity="sigma even; omega axial; beta polar",
        perturbative_order="kinematic state",
    )
    source[0] = 99.0
    assert state.sigma_ab[0] == 1.0
    assert len(state.vector) == 12
    with pytest.raises(StatisticalFoundationError, match="length 5"):
        DepartureState(
            sigma_ab=(0.0,) * 4,
            omega_a=(0.0,) * 3,
            beta_a=(0.0,) * 3,
            delta_omega_k=0.0,
            frame="f",
            congruence="c",
            epoch_window="e",
            averaging_scale="a",
            basis="b",
            units="u",
            parity="p",
            perturbative_order="o",
        )


def test_summary_preserves_signed_xc_but_never_promotes_it() -> None:
    summary = SummaryDepartureState(
        sigma2=0.1,
        w2=0.3,
        omega_tilt=0.05,
        delta_omega_k=-0.02,
        normalization="registered comparator normalization",
        source_state_id="fixture-1",
    )
    assert summary.x_C == pytest.approx(-0.17)
    report = LegacyProjectionReport(
        x_C=DiagnosticScalarReport(
            name="x_C",
            value_range=ScalarRange(summary.x_C, summary.x_C),
            status="HISTORICAL_VALUE_PRESERVED",
            null_calibration="not a null-calibrated evidence quantity",
        )
    )
    assert report.classification == BC1_LEGACY_PROJECTION
    assert report.representation_policy == BC2_NO_REPRESENTATION_PROMOTION
    assert {"departure distance", "occupancy", "evidence"} <= set(
        report.forbidden_use
    )
    assert W2_V2_ALIAS.canonical == "W2"
    assert "Nilsson" in W2_V2_ALIAS.caveat


def test_summary_departure_state_rejects_derived_xc_overflow() -> None:
    with pytest.raises(
        StatisticalFoundationError,
        match="x_C must be a finite real number",
    ):
        SummaryDepartureState(
            sigma2=1.0e308,
            w2=0.0,
            omega_tilt=1.0e308,
            delta_omega_k=1.0e308,
            normalization="overflow regression",
            source_state_id="PR-252-R3",
        )


def test_legacy_projection_rejects_unbounded_numeric_ranges() -> None:
    with pytest.raises(
        StatisticalFoundationError,
        match="legacy projection value ranges must be finite",
    ):
        LegacyProjectionReport(
            x_C=DiagnosticScalarReport(
                name="x_C",
                value_range=ScalarRange(math.inf, math.inf),
                status="HISTORICAL_VALUE_PRESERVED",
                null_calibration="not an evidence calibration",
            )
        )


def test_identified_set_support_preserves_recession_and_null_kind() -> None:
    source_null_kinds = [NullKind.NONE, NullKind.STRUCTURAL]
    identified = IdentifiedDepartureSet(
        coordinate_names=("Sigma2", "W2"),
        vertices=((0.0, 0.0), (1.0, 0.0)),
        recession_directions=((0.0, 1.0),),
        null_kinds=source_null_kinds,  # type: ignore[arg-type]
        assumptions=("registered response map",),
        status=IdentificationStatus.PARTIALLY_IDENTIFIED,
    )
    source_null_kinds[1] = NullKind.LEADING_ORDER
    assert identified.interval((1.0, 0.0)) == ScalarRange(0.0, 1.0)
    assert identified.support((0.0, 1.0)) == math.inf
    assert identified.interval((0.0, 1.0)) == ScalarRange(0.0, math.inf)
    assert identified.null_kinds[1] is NullKind.STRUCTURAL
    rescaled = IdentifiedDepartureSet(
        coordinate_names=("Sigma2", "W2"),
        vertices=((0.0, 0.0), (1.0, 0.0)),
        recession_directions=((0.0, 1.0e-13),),
        null_kinds=(NullKind.NONE, NullKind.STRUCTURAL),
        assumptions=("same cone under positive generator scaling",),
        status=IdentificationStatus.PARTIALLY_IDENTIFIED,
    )
    assert rescaled.support((0.0, 1.0)) == math.inf
    assert rescaled.support((0.0, 1.0e-30)) == math.inf

    near_orthogonal = IdentifiedDepartureSet(
        coordinate_names=("Sigma2", "W2"),
        vertices=((0.0, 0.0),),
        recession_directions=((1.0, 0.0),),
        null_kinds=(NullKind.STRUCTURAL, NullKind.NONE),
        assumptions=("strict positive recession projection",),
        status=IdentificationStatus.PARTIALLY_IDENTIFIED,
    )
    for scale in (1.0e-300, 1.0, 1.0e300):
        assert near_orthogonal.support((1.0e-13 * scale, scale)) == math.inf
    assert near_orthogonal.interval((1.0e-13, 1.0)).upper == math.inf
    tiny_ray = IdentifiedDepartureSet(
        coordinate_names=("Sigma2", "W2"),
        vertices=((0.0, 0.0),),
        recession_directions=((1.0e-300, 0.0),),
        null_kinds=(NullKind.STRUCTURAL, NullKind.NONE),
        assumptions=("same cone under extreme positive ray scaling",),
        status=IdentificationStatus.PARTIALLY_IDENTIFIED,
    )
    assert tiny_ray.support((1.0e-13, 1.0)) == math.inf
    with pytest.raises(
        StatisticalFoundationError,
        match="support topology requires tol=0",
    ):
        near_orthogonal.support((1.0e-13, 1.0), tol=1.0e-12)

    compact_overflow = IdentifiedDepartureSet(
        coordinate_names=("Sigma2",),
        vertices=((1.0e308,),),
        recession_directions=(),
        null_kinds=(NullKind.NONE,),
        assumptions=("compact overflow must remain distinct from recession",),
        status=IdentificationStatus.PARTIALLY_IDENTIFIED,
    )
    with pytest.raises(
        StatisticalFoundationError,
        match="compact support is not representable",
    ):
        compact_overflow.support((1.0e308,))

    empty = IdentifiedDepartureSet(
        coordinate_names=("Sigma2",),
        vertices=(),
        recession_directions=(),
        null_kinds=(NullKind.NONE,),
        assumptions=("stage-1 specification test failed",),
        status=IdentificationStatus.EMPTY,
    )
    with pytest.raises(StatisticalFoundationError, match="no support"):
        empty.support((1.0,))


def test_anchor_stress_is_channel_typed_and_one_way() -> None:
    anchor = _external_anchor(2.0)
    stress = evaluate_sector_stress(
        sector="Sigma2",
        numerator=ScalarRange(1.0, 3.0),
        numerator_channel_key=anchor.channel_key,
        anchor=anchor,
    )
    assert stress.status is StressStatus.DEFINED
    assert stress.saturation == ScalarRange(0.5, 1.5)
    assert stress.exceedance == ScalarRange(0.0, 0.5)
    report = build_anchor_stress_report(
        stresses=(stress,),
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )
    assert report.saturation_vector == (ScalarRange(0.5, 1.5),)
    assert "FLRW converse" in report.forbidden_use
    assert "evidence" in report.forbidden_use
    assert stress.conditioning is AnchorConditioning.ENSEMBLE_CALIBRATED

    mismatch = evaluate_sector_stress(
        sector="Sigma2",
        numerator=ScalarRange(1.0, 1.0),
        numerator_channel_key=(*anchor.channel_key[:-1], "other branch"),
        anchor=anchor,
    )
    assert mismatch.status is StressStatus.CHANNEL_MISMATCH
    assert mismatch.saturation is None

    cross_sector = evaluate_sector_stress(
        sector="W2",
        numerator=ScalarRange(1.0, 1.0),
        numerator_channel_key=anchor.channel_key,
        anchor=anchor,
    )
    assert cross_sector.status is StressStatus.CHANNEL_MISMATCH
    assert cross_sector.saturation is None

    unavailable = evaluate_sector_stress(
        sector="A2",
        numerator=ScalarRange(0.0, 0.0),
        numerator_channel_key=("A2",),
        anchor=None,
    )
    assert unavailable.status is StressStatus.ANCHOR_UNAVAILABLE


def test_anchor_stress_cannot_relabel_random_anchor_or_forge_claim_lanes() -> None:
    anchor = _external_anchor(
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL
    )
    stress = evaluate_sector_stress(
        sector="Sigma2",
        numerator=ScalarRange(1.0, 3.0),
        numerator_channel_key=anchor.channel_key,
        anchor=anchor,
    )
    assert stress.status is StressStatus.RATIO_UNIDENTIFIED
    assert stress.saturation is None
    assert stress.exceedance is None
    assert stress.conditioning is AnchorConditioning.REALIZATION_CONDITIONAL
    assert stress.allowed_use == ("partial-identification status",)

    with pytest.raises(
        StatisticalFoundationError,
        match="report conditioning must match",
    ):
        build_anchor_stress_report(
            stresses=(stress,),
            conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
        )
    report = build_anchor_stress_report(
        stresses=(stress,),
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
    )
    assert "evidence" in report.forbidden_use
    assert "family identification" in report.forbidden_use

    class ForgedStress(SectorStress):
        def __init__(self) -> None:
            object.__setattr__(self, "sector", "Sigma2")
            object.__setattr__(self, "status", StressStatus.DEFINED)
            object.__setattr__(self, "anchor_id", "forged")
            object.__setattr__(
                self,
                "conditioning",
                AnchorConditioning.ENSEMBLE_CALIBRATED,
            )
            object.__setattr__(self, "saturation", ScalarRange(0.0, 0.0))
            object.__setattr__(self, "exceedance", ScalarRange(99.0, 99.0))
            object.__setattr__(self, "rationale", "forged subclass")
            object.__setattr__(self, "allowed_use", ("evidence",))

    with pytest.raises(
        StatisticalFoundationError,
        match="exact factory-derived SectorStress",
    ):
        build_anchor_stress_report(
            stresses=(ForgedStress(),),
            conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
        )

    forged_exact = object.__new__(SectorStress)
    for name, value in {
        "sector": "Sigma2",
        "status": StressStatus.DEFINED,
        "anchor_id": "forged",
        "conditioning": AnchorConditioning.ENSEMBLE_CALIBRATED,
        "saturation": ScalarRange(0.0, 0.0),
        "exceedance": ScalarRange(99.0, 99.0),
        "rationale": "post-init bypass",
        "allowed_use": ("evidence",),
    }.items():
        object.__setattr__(forged_exact, name, value)
    with pytest.raises(
        StatisticalFoundationError,
        match="exceedance must equal",
    ):
        build_anchor_stress_report(
            stresses=(forged_exact,),
            conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
        )

    with pytest.raises(
        StatisticalFoundationError,
        match="must be created by evaluate_sector_stress",
    ):
        SectorStress(
            sector="Sigma2",
            status=StressStatus.DEFINED,
            anchor_id="forged",
            conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
            saturation=ScalarRange(0.5, 0.5),
            exceedance=ScalarRange(99.0, 99.0),
            rationale="forged evidence lane",
        )
    with pytest.raises(
        StatisticalFoundationError,
        match="must be created by build_anchor_stress_report",
    ):
        AnchorStressReport(
            stresses=(stress,),
            conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
        )


def test_budget_radius_exposes_null_residual() -> None:
    result = matrix_budget_radius_report(
        np.array([[1.0, 0.0], [0.0, 2.0]]),
        np.diag([1.0, 0.0]),
    )
    assert result.radius_sq == pytest.approx((1.0, 0.0))
    assert result.rank == 1
    assert result.null_residual == pytest.approx((0.0, 2.0))
    assert result.status is BudgetRadiusStatus.NULL_RESIDUAL_PRESENT
    full_rank = matrix_budget_radius_report(
        np.array([1.0, 1.0]), np.diag([1.0, 2.0])
    )
    scaled = matrix_budget_radius_report(
        np.array([1.0, 1.0]), 1.0e-14 * np.diag([1.0, 2.0])
    )
    assert full_rank.rank == scaled.rank == 2
    assert scaled.radius_sq[0] == pytest.approx(
        full_rank.radius_sq[0] * 1.0e14
    )
    for samples, budget in (
        (np.array([True, False]), np.eye(2)),
        (np.array([1.0, 0.0]), np.array([[True, False], [False, True]])),
        ([True, 0.0], np.eye(2)),
    ):
        with pytest.raises(ValueError, match="boolean"):
            matrix_budget_radius_report(samples, budget)
    with pytest.deprecated_call():
        legacy = matrix_budget_radius([1.0, 0.0], np.diag([1.0, 0.0]))
    assert legacy == pytest.approx([1.0])


def test_graded_comparator_removes_active_sector_filling() -> None:
    comparator = graded_comparator(2.0, 1.0, 0.5, -0.25)
    assert comparator.x_C == pytest.approx(1.25)
    assert "sector_filling" not in comparator.as_dict()
    with pytest.raises(ValueError, match="legacy-only"):
        graded_comparator(2.0, 1.0, 0.5, -0.25, x_max=9.25e-6)
    with pytest.deprecated_call():
        legacy = legacy_sector_filling(
            2.0, 1.0, 0.5, -0.25, x_max=10.0
        )
    assert legacy["anchor_kind"] == "SYNTHETIC_SUPPORT_BOUND"


def test_one_im_critical_value_domain_and_wrappers() -> None:
    expected = im_critical_value(0.5, 1.0, 0.05)
    assert identified_set_im_critical_value(0.5, 1.0, 0.05) == pytest.approx(
        expected, abs=1e-12
    )
    assert strengthened_im_critical_value(0.5, 1.0, 0.05) == pytest.approx(
        expected, abs=1e-12
    )
    for delta, se in ((-1.0, 1.0), (0.0, 0.0), (0.0, -1.0)):
        with pytest.raises(StatisticalFoundationError):
            im_critical_value(delta, se)


def test_legacy_projection_semantics_cannot_be_weakened() -> None:
    x_report = DiagnosticScalarReport(
        name="x_C",
        value_range=ScalarRange(0.0, 0.0),
        status="HISTORICAL_VALUE_PRESERVED",
        null_calibration="not a null-calibrated evidence quantity",
    )
    with pytest.raises(StatisticalFoundationError, match="allowed_use"):
        LegacyProjectionReport(
            x_C=x_report,
            allowed_use=("Bianchi family identification",),
        )
    with pytest.raises(StatisticalFoundationError, match="must be named Pi"):
        LegacyProjectionReport(
            x_C=x_report,
            Pi=DiagnosticScalarReport(
                name="truth_probability",
                value_range=ScalarRange(0.9, 0.9),
                status="LEGACY_DIAGNOSTIC",
                null_calibration="NOT_AVAILABLE_NON_EVIDENCE",
                bin_metadata=(("bin_id", "legacy-bin-1"),),
            ),
        )
    with pytest.raises(StatisticalFoundationError, match="bin metadata"):
        LegacyProjectionReport(
            x_C=x_report,
            G_F=DiagnosticScalarReport(
                name="G_F",
                value_range=ScalarRange(0.1, 0.1),
                status="LEGACY_DIAGNOSTIC",
                null_calibration="NOT_AVAILABLE_NON_EVIDENCE",
            ),
        )
    with pytest.raises(StatisticalFoundationError, match="x_C must be"):
        LegacyProjectionReport(x_C=SimpleNamespace(name="x_C"))
    with pytest.raises(StatisticalFoundationError, match="Pi must be"):
        LegacyProjectionReport(
            x_C=x_report,
            Pi=SimpleNamespace(
                name="Pi",
                bin_metadata=(("bin_id", "legacy-bin-1"),),
                null_calibration="NOT_AVAILABLE_NON_EVIDENCE",
            ),
        )
    with pytest.raises(StatisticalFoundationError, match="value_range"):
        DiagnosticScalarReport(
            name="Q",
            value_range=SimpleNamespace(lower=0.0, upper=1.0),
            status="LEGACY_DIAGNOSTIC",
            null_calibration="NOT_AVAILABLE_NON_EVIDENCE",
            bin_metadata=(("bin_id", "legacy-bin-1"),),
        )
