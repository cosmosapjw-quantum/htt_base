from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from common.oracle_lab import FROZEN_MUTATION_IDS


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "docs/research_program/long_horizon_rescue/pr123_spec.yaml"
REPORT = REPO_ROOT / "docs/generated/pr123_mutation_lab_report.json"
LINEAGE = REPO_ROOT / "docs/generated/pr123_oracle_lineage_manifest.json"
K6 = REPO_ROOT / "docs/generated/pr123_k6_continuum_card.json"
SURVIVORS = REPO_ROOT / "docs/generated/pr123_surviving_mutations.json"
ATTEMPTS = REPO_ROOT / "docs/generated/pr123_attempt_history.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_reviewed_spec_freezes_exact_scope_claim_and_nine_mutations() -> None:
    payload = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert payload["schema"] == "htt.long_horizon.pr123_oracle_lab.v6"
    assert payload["owner"] == "COMMON"
    assert payload["contributors"] == ["OBSSTAT", "HTT"]
    assert payload["claim_tier_ceiling"] == "conditional"
    assert payload["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert payload["scientific_status"] == "OPEN"
    assert tuple(row["mutation_id"] for row in payload["mutation_registry"]) == FROZEN_MUTATION_IDS
    assert len(payload["review_provenance"]["role_results"]) == 4
    assert payload["scope_and_non_goals"]["production_remediation"] == "forbidden"
    assert payload["scope_and_non_goals"]["observed_data_analysis"] == "forbidden"
    assert payload["spec_amendment"]["previous_attempt_status"] == "INVALIDATED_FALSE_GREEN"
    assert len(payload["spec_amendment"]["invalidated_attempts"]) == 5
    assert payload["spec_amendment"]["prospective_preregistration_claimed_for_v6"] is False


def test_frozen_production_sources_are_historical_and_not_remediated_here() -> None:
    payload = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    frozen = set(payload["scope_and_non_goals"]["mapped_production_files_must_not_change"])
    mapped = set()
    historical_drift: set[str] = set()
    for mutation in payload["mutation_registry"]:
        for record in mutation["production_paths"]:
            path = REPO_ROOT / record["path"]
            assert path.is_file()
            if _sha256(path) != record["sha256"]:
                historical_drift.add(record["path"])
            mapped.add(record["path"])
    assert frozen <= mapped
    assert historical_drift == {"htt/obsstat/joint_pv_cmb_forecast.py"}


def test_all_registered_mutations_execute_and_die_without_scientific_promotion() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    summary = report["summary"]
    assert summary["registered_count"] == 9
    assert summary["executed_count"] == 9
    assert summary["clean_pass_count"] == 9
    assert summary["killed_count"] == 9
    assert summary["survivor_count"] == 0
    assert summary["aggregate_status"] == "PASS_MECHANICS_C2"
    assert summary["scientific_status"] == "OPEN"
    assert summary["claim_promotion_allowed"] is False
    assert tuple(row["mutation_id"] for row in summary["outcomes"]) == FROZEN_MUTATION_IDS
    assert all(row["status"] == "PASS_MECHANICS_C2" for row in summary["outcomes"])


def test_lineage_independence_is_algorithmic_and_explicitly_correlated() -> None:
    payload = json.loads(LINEAGE.read_text(encoding="utf-8"))
    outcomes = {
        row["mutation_id"]: row
        for row in json.loads(REPORT.read_text(encoding="utf-8"))["summary"]["outcomes"]
    }
    assert payload["independence_scope"] == "internal_C2_mechanics_not_external_replication"
    assert payload["all_rows_valid"] is True
    assert len(payload["lineage_rows"]) == 9
    for row in payload["lineage_rows"]:
        assert row["algorithm_id"]
        assert row["equation_or_source_ids"]
        assert row["fixture_ids_and_hashes"]
        assert len(row["design_author_ids"]) >= 2
        assert row["random_stream_namespace"].startswith("PR123/")
        assert "all_internal_codex_roles_are_process_correlated" in row["shared_lineage_disclosures"]
        assert all(row["automated_scan_checks"].values())
        assert row["manual_algorithm_adjudication"]["external_replication_claimed"] is False
        assert row["fixture_ids_and_hashes"][0]["sha256"] == outcomes[row["mutation_id"]]["fixture_hash"]
        assert row["reference_metrics"]["sloc"] < row["complexity_budget"]["mapped_production_call_closure_sloc"]
    source_ids = {
        source_id
        for row in payload["lineage_rows"]
        for source_id in row["equation_or_source_ids"]
    }
    assert source_ids == set(payload["equation_source_definitions"])
    assert all(record["statement"] for record in payload["equation_source_definitions"].values())


def test_k6_card_runs_four_grids_two_orders_and_has_zero_empirical_consumers() -> None:
    payload = json.loads(K6.read_text(encoding="utf-8"))
    assert len(payload["periodic_grids"]) == 4
    assert len(payload["boundary_grids"]) == 4
    assert payload["stencil_orders"] == [2, 4]
    assert set(payload["analytic_fields"]) == {
        "solid_body_rotation",
        "periodic_potential",
        "mixed_helmholtz",
        "manufactured_boundary",
    }
    assert payload["periodic"]["2"]["mixed_observed_order"] >= 1.8
    assert payload["periodic"]["4"]["mixed_observed_order"] >= 3.5
    assert payload["boundary"]["2"]["interior_observed_order"] >= 1.8
    assert payload["boundary"]["2"]["boundary_collar_observed_order"] >= 1.8
    assert payload["boundary"]["4"]["interior_observed_order"] >= 3.5
    assert payload["boundary"]["4"]["boundary_collar_observed_order"] >= 3.5
    assert payload["sqrt2_residual_lock"]["correlated_challenge_suspends_lock"] is True
    assert payload["empirical_inputs"] == []
    assert payload["empirical_consumers"] == []
    assert payload["empirical_consumer_count"] == 0
    assert payload["scientific_status"] == "OPEN"


def test_invalidated_attempt_is_not_laundered_into_the_valid_receipt() -> None:
    payload = json.loads(ATTEMPTS.read_text(encoding="utf-8"))
    first, second, third, fourth, fifth, sixth = payload["attempts"]
    assert all(
        attempt["status"] == "INVALIDATED_FALSE_GREEN"
        for attempt in (first, second, third, fourth, fifth)
    )
    assert all(
        attempt["counts_must_not_be_consumed"] is True
        for attempt in (first, second, third, fourth, fifth)
    )
    assert sixth["status"] == "PASS_MECHANICS_C2"
    assert sixth["prospective_preregistration_claimed"] is False


def test_survivor_report_exists_even_when_every_mutant_is_killed() -> None:
    payload = json.loads(SURVIVORS.read_text(encoding="utf-8"))
    assert payload["registered_count"] == 9
    assert payload["survivor_count"] == 0
    assert payload["survivors"] == []
    assert payload["aggregate_status"] == "PASS_MECHANICS_C2"
    assert payload["scientific_status"] == "OPEN"
