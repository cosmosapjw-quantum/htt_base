from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
LEDGER = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
    / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V2.yaml"
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


def test_t9_v2_is_self_contained_and_has_exact_claim_surface():
    value = load()
    assert value["schema"] == "htt.report_a.integrated_claim_evidence_ledger.v2"
    claims = value["claims"]
    ids = [claim["id"] for claim in claims]
    assert len(ids) == len(set(ids)) == 29
    assert set(ids) == EXPECTED_IDS
    assert value["coverage"]["claim_count"] == 29
    assert value["coverage"]["canonical_sorted_id_sha256"] == (
        "bc81bdd2d5325f5561834594cb3f4195dc29c22ee461dcf77e067373678b22fe"
    )


def test_t9_v2_preserves_data_and_claim_firewalls():
    value = load()
    assert value["observational_data_used"] is False
    assert value["corrected_planck_tensor_rank"] is None
    assert value["merge_authorized"] is False
    assert value["coverage"]["observational_claim_count"] == 0
    assert value["coverage"]["finite_healpix_no_go_claim_count"] == 0
    assert value["coverage"]["native_bass_claim_count"] == 0
    assert "RA-BOUNDARY-001" in {claim["id"] for claim in value["claims"]}


def test_t9_v2_records_mechanical_and_decoder_execution_boundaries():
    value = load()
    repairs = value["active_repairs"]
    assert repairs["mechanical_survivor_surface"] == {
        "pr": 450,
        "head": "8396f8a927c7ea7ccd3e5b96497e076774b98d7c",
        "source_equivalent_local_tests": "13 passed",
        "exact_head_execution": "PRESTART_NO_EXECUTION",
    }
    assert repairs["qo_packet_image"] == {
        "pr": 451,
        "head": "1fdd499c86e7e4aad8edc71565114a6753ebf767",
        "source_equivalent_local_tests": "26 passed after observed RED",
        "exact_head_execution": "PRESTART_NO_EXECUTION",
    }
    orbit = next(claim for claim in value["claims"] if claim["id"] == "RA-ORBIT-002")
    assert orbit["implementation_repair_pr"] == 451
    assert orbit["implementation_status"] == "SOURCE_IMPLEMENTED_REPAIR_PENDING_EXECUTION"


def test_t9_v2_records_t4_tie_rule_repair_and_finite_operator_boundary():
    value = load()
    stat = next(claim for claim in value["claims"] if claim["id"] == "RA-STAT-002")
    assert stat["exact_counterexample"]["tie_to_coordinate_2"] == {
        "p_1_over_2": 12,
        "p_3_over_4": 12,
        "max_size_violation": "1/4",
    }
    assert stat["exact_counterexample"]["tie_to_coordinate_1"] == {
        "p_1_over_2": 6,
        "p_3_over_4": 18,
        "max_size_violation": "1/4",
    }
    finite = next(claim for claim in value["claims"] if claim["id"] == "RA-PROC-005")
    assert finite["statement"].endswith("rank unresolved, with no containment candidate.")
    assert finite["forbidden_extensions"] == [
        "finite_healpix_high_source_containment_proved"
    ]


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
