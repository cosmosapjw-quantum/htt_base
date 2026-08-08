"""PR-281 orbit acceptance and uncovered-direction contracts."""

from __future__ import annotations

import pytest

from common.anisotropy_type_report import (
    ANISOTROPY_TYPE_CLAIM_CEILING,
    ANISOTROPY_TYPE_FAMILY_GATE,
    AnisotropyTypeReportError,
    build_anisotropy_type_report,
)
from common.joint_anisotropy_state import (
    JointAnisotropyState,
    JointAnisotropyStateError,
    OrbitAcceptanceCase,
    OrbitTypeAcceptance,
    build_orbit_type_acceptance,
)
from common.orbit_catalogue_v3 import CatalogueProofStatus
from tests.contracts.test_anisotropy_type_report import _inputs, _joint


@pytest.mark.parametrize(
    ("case", "state_dimension", "quotient_rank", "orbit_dimension"),
    (
        (OrbitAcceptanceCase.PRINCIPAL_BASE, 12, 9, 3),
        (OrbitAcceptanceCase.PRINCIPAL_WITH_ACCELERATION, 15, 12, 3),
        (
            OrbitAcceptanceCase.PRINCIPAL_WITH_ACCELERATION_AND_VELOCITY_SPLIT,
            18,
            15,
            3,
        ),
        (OrbitAcceptanceCase.OFF_STRATUM_SINGLE_VECTOR_U1, 3, 1, 2),
    ),
)
def test_registered_orbit_acceptance_table(
    case: OrbitAcceptanceCase,
    state_dimension: int,
    quotient_rank: int,
    orbit_dimension: int,
) -> None:
    acceptance = build_orbit_type_acceptance(
        case=case,
        state_dimension=state_dimension,
        quotient_rank=quotient_rank,
    )
    assert type(acceptance) is OrbitTypeAcceptance
    assert acceptance.state_dimension == state_dimension
    assert acceptance.quotient_rank == quotient_rank
    assert acceptance.orbit_dimension == orbit_dimension
    assert acceptance.generic_completeness_status == "UNPROVEN"
    assert "identifiable" not in acceptance.as_payload()
    assert "complete" not in acceptance.as_payload()


@pytest.mark.parametrize(
    ("case", "state_dimension", "quotient_rank"),
    (
        (OrbitAcceptanceCase.PRINCIPAL_BASE, 12, 12),
        (OrbitAcceptanceCase.PRINCIPAL_BASE, 15, 9),
        (OrbitAcceptanceCase.PRINCIPAL_WITH_ACCELERATION, 15, 9),
        (
            OrbitAcceptanceCase.PRINCIPAL_WITH_ACCELERATION_AND_VELOCITY_SPLIT,
            18,
            12,
        ),
        (OrbitAcceptanceCase.OFF_STRATUM_SINGLE_VECTOR_U1, 3, 0),
        (OrbitAcceptanceCase.OFF_STRATUM_SINGLE_VECTOR_U1, 12, 9),
        (OrbitAcceptanceCase.PRINCIPAL_BASE, True, 9),
        (OrbitAcceptanceCase.PRINCIPAL_BASE, 12, False),
    ),
)
def test_invalid_or_cross_case_pairs_fail_closed(
    case: OrbitAcceptanceCase,
    state_dimension: object,
    quotient_rank: object,
) -> None:
    with pytest.raises(JointAnisotropyStateError):
        build_orbit_type_acceptance(
            case=case,
            state_dimension=state_dimension,
            quotient_rank=quotient_rank,
        )


def test_single_vector_exception_blocks_naive_dim_minus_three() -> None:
    acceptance = build_orbit_type_acceptance(
        case=OrbitAcceptanceCase.OFF_STRATUM_SINGLE_VECTOR_U1,
        state_dimension=3,
        quotient_rank=1,
    )
    assert acceptance.orbit_dimension == 2
    assert acceptance.stabilizer == "U(1)"
    assert acceptance.stratum == "OFF_STRATUM_SINGLE_VECTOR"
    assert acceptance.quotient_rank != acceptance.state_dimension - 3


def test_joint_state_v1_payload_is_not_widened() -> None:
    state = _joint()
    payload = state.to_payload()
    assert payload["schema"] == "HTT_JOINT_ANISOTROPY_STATE_V1"
    assert "orbit_type_acceptance" not in payload
    assert JointAnisotropyState.from_payload(payload) == state


def test_public_v2_factory_preserves_missing_argument_type_error() -> None:
    with pytest.raises(TypeError, match="missing 11 required keyword-only arguments"):
        build_anisotropy_type_report()


def test_rank_deficient_report_binds_replayed_uncovered_directions() -> None:
    values = _inputs(anchored_rank_deficient=True)
    anchored = values["anchored_response"]
    report = build_anisotropy_type_report(**values)

    assert anchored.rank == 1
    assert anchored.parameter_dimension == 2
    assert report.uncovered_directions == anchored.null_directions
    assert report.uncovered_parameter_labels == anchored.parameter_labels
    assert report.uncovered_covariance_id == anchored.covariance_id
    assert report.uncovered_response_id == anchored.response_id
    assert len(report.uncovered_directions) == 1
    assert all(
        len(direction) == len(report.uncovered_parameter_labels)
        for direction in report.uncovered_directions
    )
    assert report.orbit_proof_statuses == (
        CatalogueProofStatus.UNPROVEN.value,
        CatalogueProofStatus.UNPROVEN.value,
        CatalogueProofStatus.UNPROVEN.value,
    )
    assert report.claim_ceiling == ANISOTROPY_TYPE_CLAIM_CEILING
    assert report.family_identification_gate == ANISOTROPY_TYPE_FAMILY_GATE

    payload = report.as_payload()
    assert payload["schema"] == "HTT_ANISOTROPY_TYPE_REPORT_V2"
    assert payload["uncovered_directions"] == [
        list(direction) for direction in anchored.null_directions
    ]
    for forbidden in (
        "family_label",
        "geometry_label",
        "nearest_label",
        "identifiable",
        "completeness_proof",
    ):
        assert forbidden not in payload


def test_full_rank_report_retains_empty_but_identity_bound_projection() -> None:
    values = _inputs()
    anchored = values["anchored_response"]
    report = build_anisotropy_type_report(**values)
    assert report.uncovered_directions == ()
    assert report.uncovered_parameter_labels == anchored.parameter_labels
    assert report.uncovered_covariance_id == anchored.covariance_id
    assert report.uncovered_response_id == anchored.response_id


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("null_directions", ((1.0, 0.0),)),
        ("covariance_id", "sha256:" + "1" * 64),
        ("response_id", "sha256:" + "2" * 64),
    ),
)
def test_upstream_uncovered_binding_mutations_fail_replay(
    name: str,
    replacement: object,
) -> None:
    values = _inputs(anchored_rank_deficient=True)
    object.__setattr__(values["anchored_response"], name, replacement)
    with pytest.raises(AnisotropyTypeReportError, match="failed exact replay"):
        build_anisotropy_type_report(**values)


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("uncovered_directions", ((1.0, 0.0),)),
        ("uncovered_parameter_labels", ("forged", "labels")),
        ("uncovered_covariance_id", "sha256:" + "3" * 64),
        ("uncovered_response_id", "sha256:" + "4" * 64),
    ),
)
def test_projected_uncovered_binding_is_identity_sealed(
    name: str,
    replacement: object,
) -> None:
    report = build_anisotropy_type_report(**_inputs(anchored_rank_deficient=True))
    object.__setattr__(report, name, replacement)
    with pytest.raises(AnisotropyTypeReportError, match="identity drifted"):
        report.as_payload()
