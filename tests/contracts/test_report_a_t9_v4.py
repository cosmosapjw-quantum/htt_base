from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
LEDGER = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
    / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml"
)

EXPECTED_IDS = {
    "RA-SCOPE-001",
    "RA-REP-001",
    "RA-REP-002",
    "RA-REP-003",
    "RA-ORBIT-001",
    "RA-ORBIT-002",
    "RA-ORBIT-003",
    "RA-ORBIT-004",
    "RA-MES-001",
    "RA-MES-002",
    "RA-MES-003",
    "RA-STAT-001",
    "RA-STAT-002",
    "RA-STAT-003",
    "RA-STAT-004",
    "RA-RESP-001",
    "RA-RESP-002",
    "RA-PROC-001",
    "RA-PROC-002",
    "RA-PROC-003",
    "RA-PROC-004",
    "RA-PROC-005",
    "RA-CONT-001",
    "RA-CONT-002",
    "RA-CONT-003",
    "RA-ERR-001",
    "RA-ERR-002",
    "RA-ERR-003",
    "RA-ERR-004",
    "RA-BOUNDARY-001",
}


def load() -> dict:
    value = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def by_id(value: dict, claim_id: str) -> dict:
    return next(claim for claim in value["claims"] if claim["id"] == claim_id)


def test_t9_v4_is_self_contained_and_preserves_the_thirty_claim_surface():
    value = load()
    assert value["schema"] == "htt.report_a.integrated_claim_evidence_ledger.v4"
    ids = [claim["id"] for claim in value["claims"]]
    assert len(ids) == len(set(ids)) == 30
    assert set(ids) == EXPECTED_IDS
    assert value["coverage"]["claim_count"] == 30
    assert value["observational_data_used"] is False
    assert value["corrected_planck_tensor_rank"] is None
    assert value["merge_authorized"] is False


def test_t9_v4_flattens_the_v3_notation_authority_without_changing_claim_truth():
    value = load()
    registry = value["canonical_notation_registry"]
    assert registry["schema"] == "htt.report_a.notation_and_convention_registry.v3"
    assert registry["authority_label"] == "NOTATION_AND_CONVENTION_REGISTRY_v3"

    rep = by_id(value, "RA-REP-002")
    assert "NOTATION_AND_CONVENTION_REGISTRY_v3" in rep["authority"]
    assert "NOTATION_AND_CONVENTION_REGISTRY_v2" not in rep["authority"]
    assert rep["truth_status"] == "DERIVED_EXACT"
    assert rep["implementation_status"] == "SOURCE_IMPLEMENTED"


def test_t9_v4_binds_the_two_finite_sample_domains_atomically():
    value = load()
    row = by_id(value, "RA-STAT-001")
    group = by_id(value, "RA-STAT-004")
    assert row["assumptions"] == [
        "joint_exchangeability",
        "complete_row_permutation_equivariance",
        "fixed_tie_and_tail_rule",
    ]
    assert row["domain_binding"] == "statistical_notation.exchangeable_row_rank"
    assert group["assumptions"] == [
        "null_law_invariant_under_declared_group",
        "reference_statistics_are_actual_group_orbit",
        "identity_included",
        "exact_or_valid_conditional_monte_carlo_rule",
    ]
    assert group["domain_binding"] == "statistical_notation.randomization_group_orbit"


def test_t9_v4_binds_observer_and_numerical_error_domains():
    value = load()
    response = by_id(value, "RA-RESP-001")
    error = by_id(value, "RA-ERR-001")
    assert "NOTATION_AND_CONVENTION_REGISTRY_v3" in response["authority"]
    assert response["domain_binding"] == [
        "spacetime.observer",
        "sky_and_boost.photon",
        "sky_and_boost.local_observer_boost",
    ]
    assert "NOTATION_AND_CONVENTION_REGISTRY_v3" in error["authority"]
    assert error["domain_binding"] == "numerical_uncertainty.domain"


def test_t9_v4_preserves_claim_and_data_firewalls():
    value = load()
    coverage = value["coverage"]
    assert coverage["observational_claim_count"] == 0
    assert coverage["corrected_planck_rank_claim_count"] == 0
    assert coverage["finite_healpix_no_go_claim_count"] == 0
    assert coverage["native_bass_claim_count"] == 0
    assert coverage["canonical_sorted_id_sha256"] is None
    assert coverage["canonical_sorted_id_sha256_status"] == (
        "PENDING_SUPPORTED_RUNTIME_REPLAY"
    )
