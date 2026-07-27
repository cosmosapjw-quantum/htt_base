"""PR-249 state, identified-set, stress and legacy-report contracts."""
from __future__ import annotations

import math

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
    StatisticalFoundationError,
    StressStatus,
    SummaryDepartureState,
    W2_V2_ALIAS,
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


def _external_anchor(value: float = 2.0) -> MESAnchorSpec:
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
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
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


def test_identified_set_support_preserves_recession_and_null_kind() -> None:
    identified = IdentifiedDepartureSet(
        coordinate_names=("Sigma2", "W2"),
        vertices=((0.0, 0.0), (1.0, 0.0)),
        recession_directions=((0.0, 1.0),),
        null_kinds=(NullKind.NONE, NullKind.STRUCTURAL),
        assumptions=("registered response map",),
        status=IdentificationStatus.PARTIALLY_IDENTIFIED,
    )
    assert identified.interval((1.0, 0.0)) == ScalarRange(0.0, 1.0)
    assert identified.support((0.0, 1.0)) == math.inf
    assert identified.interval((0.0, 1.0)) == ScalarRange(0.0, math.inf)
    assert identified.null_kinds[1] is NullKind.STRUCTURAL

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
    report = AnchorStressReport(
        stresses=(stress,),
        conditioning=AnchorConditioning.ENSEMBLE_CALIBRATED,
    )
    assert report.saturation_vector == (ScalarRange(0.5, 1.5),)
    assert "FLRW converse" in report.forbidden_use

    mismatch = evaluate_sector_stress(
        sector="Sigma2",
        numerator=ScalarRange(1.0, 1.0),
        numerator_channel_key=(*anchor.channel_key[:-1], "other branch"),
        anchor=anchor,
    )
    assert mismatch.status is StressStatus.CHANNEL_MISMATCH
    assert mismatch.saturation is None

    unavailable = evaluate_sector_stress(
        sector="A2",
        numerator=ScalarRange(0.0, 0.0),
        numerator_channel_key=("A2",),
        anchor=None,
    )
    assert unavailable.status is StressStatus.ANCHOR_UNAVAILABLE


def test_budget_radius_exposes_null_residual() -> None:
    result = matrix_budget_radius_report(
        np.array([[1.0, 0.0], [0.0, 2.0]]),
        np.diag([1.0, 0.0]),
    )
    assert result.radius_sq == pytest.approx((1.0, 0.0))
    assert result.rank == 1
    assert result.null_residual == pytest.approx((0.0, 2.0))
    assert result.status is BudgetRadiusStatus.NULL_RESIDUAL_PRESENT
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
