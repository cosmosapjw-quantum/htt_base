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
    STF5_CARTESIAN_BASIS,
    VectorParity,
    decompose_nonlinearity,
    orbit_invariants,
)
from common.statistical_foundations import (  # noqa: E402
    DepartureState,
    ScalarRange,
    SectorStress,
    StressStatus,
)
from htt.departure.multicomponent_response import rank_gain_ladder  # noqa: E402
from obsstat.lowell_poles import AntipodalAxis  # noqa: E402


HELD_OUT_RECEIPT = "sha256:" + "c" * 64
MATCHED_INJECTION_RECEIPT = "sha256:" + "d" * 64


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


def _competition(
    *,
    winner: CandidateKind,
    receipt: str = HELD_OUT_RECEIPT,
    matched_injection_receipt: str = MATCHED_INJECTION_RECEIPT,
) -> tuple[CandidateEvaluation, ...]:
    kinds = (
        CandidateKind.NONLINEAR,
        CandidateKind.LINEAR,
        CandidateKind.SYSTEMATICS,
        CandidateKind.FRAME_MISMATCH,
        CandidateKind.DERIVATIVE_FAILURE,
    )
    return tuple(
        CandidateEvaluation(
            candidate_id=f"{kind.value}-CANDIDATE",
            kind=kind,
            held_out_score=10.0 if kind is winner else 1.0,
            matched_injection_score=9.0 if kind is winner else 0.5,
            held_out_data_id=receipt,
            matched_injection_data_id=matched_injection_receipt,
        )
        for kind in kinds
    )


def _report(
    *,
    residual: tuple[float, float, float],
    candidates: tuple[CandidateEvaluation, ...] = (),
    receipt: str | None = None,
    matched_injection_receipt: str | None = None,
):
    return decompose_nonlinearity(
        residual=residual,
        tangent_response=((1.0,), (0.0,), (0.0,)),
        covariance=np.eye(3),
        transfer_id="TRANSFER-COEFFICIENT-FIXTURE",
        mask_id="MASK-FIXTURE",
        covariance_id="COVARIANCE-FIXTURE",
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
    receipt = None if winner is None else HELD_OUT_RECEIPT
    matched_receipt = (
        None if winner is None else MATCHED_INJECTION_RECEIPT
    )
    report = _report(
        residual=residual,
        candidates=candidates,
        receipt=receipt,
        matched_injection_receipt=matched_receipt,
    )
    assert report.attribution_status is expected


def test_anchor_stress_and_nonlinearity_remain_separate_outputs() -> None:
    within = SectorStress(
        sector="Sigma2",
        status=StressStatus.DEFINED,
        anchor_id="MES-G-SIGMA",
        saturation=ScalarRange(0.8, 0.8),
        exceedance=ScalarRange(0.0, 0.0),
        allowed_use=("one-way stress",),
        rationale="fixture",
    )
    exceeded = SectorStress(
        sector="Sigma2",
        status=StressStatus.DEFINED,
        anchor_id="MES-G-SIGMA",
        saturation=ScalarRange(1.2, 1.2),
        exceedance=ScalarRange(0.2, 0.2),
        allowed_use=("one-way stress",),
        rationale="fixture",
    )
    nonlinear = _report(
        residual=(1.0, 1.0, 0.0),
        candidates=_competition(winner=CandidateKind.NONLINEAR),
        receipt=HELD_OUT_RECEIPT,
        matched_injection_receipt=MATCHED_INJECTION_RECEIPT,
    )
    assert nonlinear.attribution_status is NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
    assert within.exceedance != exceeded.exceedance
    assert not hasattr(nonlinear, "anchor_stress")


def test_incomplete_alternative_registry_cannot_authorize_nonlinear_label() -> None:
    incomplete = tuple(
        value
        for value in _competition(winner=CandidateKind.NONLINEAR)
        if value.kind is not CandidateKind.DERIVATIVE_FAILURE
    )
    report = _report(
        residual=(1.0, 1.0, 0.0),
        candidates=incomplete,
        receipt=HELD_OUT_RECEIPT,
        matched_injection_receipt=MATCHED_INJECTION_RECEIPT,
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
