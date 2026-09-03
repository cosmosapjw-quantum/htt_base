from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
LEDGER = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
    / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V3.yaml"
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


def test_t9_v3_is_self_contained_and_has_exact_claim_surface():
    value = load()
    assert value["schema"] == "htt.report_a.integrated_claim_evidence_ledger.v3"
    claims = value["claims"]
    ids = [claim["id"] for claim in claims]
    assert len(ids) == len(set(ids)) == 30
    assert set(ids) == EXPECTED_IDS
    assert value["coverage"]["claim_count"] == 30
    assert value["coverage"]["canonical_sorted_id_sha256"] is None
    assert value["coverage"]["canonical_sorted_id_sha256_status"] == (
        "PENDING_SUPPORTED_RUNTIME_REPLAY"
    )


def test_finite_sample_theorem_lanes_are_atomic_and_nonconflated():
    value = load()
    exchangeable = by_id(value, "RA-STAT-001")
    randomization = by_id(value, "RA-STAT-004")

    assert exchangeable["assumptions"] == [
        "joint_exchangeability",
        "complete_row_permutation_equivariance",
        "fixed_tie_and_tail_rule",
    ]
    assert "randomization" not in " ".join(exchangeable["assumptions"]).lower()
    assert "joint_exchangeability_or_randomization_group" not in str(exchangeable)

    assert randomization["assumptions"] == [
        "null_law_invariant_under_declared_group",
        "reference_statistics_are_actual_group_orbit",
        "identity_included",
        "exact_or_valid_conditional_monte_carlo_rule",
    ]
    assert randomization["exact_counterexample"]["all_row_p_values"] == [
        "1/4",
        "1/2",
    ]
    assert randomization["exact_counterexample"]["group_orbit_p_values"] == [
        "1/2",
        "1",
    ]
    assert randomization["exact_counterexample"]["all_row_max_size_excess"] == "1/2"
    assert randomization["exact_counterexample"]["group_orbit_max_size_excess"] == "0"


def test_t9_v3_records_current_pr450_pr451_source_boundaries():
    value = load()
    assert value["registered_survivor_source"]["mechanical_implementation_head"] == (
        "ba84912bea165896ec8f0c0e5793b47d1736f512"
    )
    repairs = value["active_repairs"]
    assert repairs["mechanical_survivor_surface"] == {
        "pr": 450,
        "head": "ba84912bea165896ec8f0c0e5793b47d1736f512",
        "source_equivalent_local_tests": "14 passed",
        "seed_schema_repair": "source_kkind_to_source_kind",
        "exact_head_execution": "PRESTART_NO_EXECUTION",
    }
    decoder = repairs["qo_packet_image"]
    assert decoder["pr"] == 451
    assert decoder["head"] == "9f7d06dec0fce1c3a8a53fa5372c84d9c679c037"
    assert decoder["source_equivalent_local_tests"] == "28 passed"
    assert decoder["local_stress"]["forward_generated_pairs"] == 10000
    assert decoder["local_stress"]["typed_chart_refusals"] == 7
    assert decoder["local_stress"]["silent_replay_failures"] == 0
    assert decoder["exact_head_execution"] == "PRESTART_NO_EXECUTION"


def test_t9_v3_preserves_data_and_claim_firewalls():
    value = load()
    assert value["observational_data_used"] is False
    assert value["corrected_planck_tensor_rank"] is None
    assert value["merge_authorized"] is False
    coverage = value["coverage"]
    assert coverage["observational_claim_count"] == 0
    assert coverage["finite_healpix_no_go_claim_count"] == 0
    assert coverage["native_bass_claim_count"] == 0
    assert by_id(value, "RA-PROC-005")["statement"].endswith(
        "rank unresolved, with no containment candidate."
    )


def test_every_claim_has_authority_and_typed_status():
    value = load()
    allowed_truth = set(value["vocabulary"]["truth_status"])
    allowed_impl = set(value["vocabulary"]["implementation_status"])
    allowed_role = set(value["vocabulary"]["report_role"])
    for claim in value["claims"]:
        assert claim["authority"]
        assert claim["truth_status"] in allowed_truth
        assert claim["implementation_status"] in allowed_impl
        assert claim["report_role"] in allowed_role
