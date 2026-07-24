"""PR-171 acceptance tests for the class-conditional counterexample audit."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt/src"))
sys.path.insert(0, str(REPO / "scripts/codex_harness"))

from common.tilt_relaxation import (  # noqa: E402
    DragTiltSystem,
    LinearTiltSystem,
    TiltRelaxationError,
    phenomenological_alpha,
    route_terminal_result,
    rw_relaxation_sign,
    rw_velocity_rhs,
    source_counterexample_fixture,
    suppression_functional,
)
from pr171_cas_support import assignment_self_hash, load, sha, validate_contract  # noqa: E402


GENERATION_3 = Path("docs/generated/pr171_cas/generation_3")
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
ASSIGNMENTS = {
    "wolfram_xact": "A-PR171-CAS3-WOLFRAM",
    "sympy": "A-PR171-CAS3-SYMPY",
    "sage_singular": "A-PR171-CAS3-SAGE",
    "lean": "A-PR171-CAS3-LEAN",
}


def _json(path: str | Path) -> dict:
    return json.loads((REPO / path).read_text(encoding="utf-8"))


def _module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_restricted_rw_and_drag_mechanics_are_exact_and_scoped() -> None:
    assert rw_relaxation_sign(Fraction(1, 2), Fraction(1, 4)) is True
    assert rw_velocity_rhs(Fraction(1, 2), Fraction(1, 4)) < 0
    assert phenomenological_alpha(Fraction(1, 4), Fraction(0)) == Fraction(1, 4)
    with pytest.raises(TiltRelaxationError):
        rw_velocity_rhs(Fraction(1, 2), Fraction(1, 3))

    drag = DragTiltSystem(Fraction(1, 4), Fraction(1, 2), Fraction(1, 3))
    assert drag.trace == -Fraction(25, 12)
    assert drag.determinant == Fraction(5, 6)
    assert drag.strictly_stable is True
    persistent = LinearTiltSystem(Fraction(1), Fraction(1), Fraction(1), Fraction(1))
    assert persistent.determinant == 0
    assert persistent.strictly_stable is False


def test_published_counterexample_mapping_retires_blanket_no_go() -> None:
    fixture = source_counterexample_fixture()
    assert fixture["gamma"] == "5/4"
    assert fixture["w"] == "1/4"
    assert fixture["Gamma"] == "0"
    assert fixture["w_less_than_one_third"] is True
    assert fixture["Gamma_nonnegative"] is True
    assert fixture["weak_energy_condition"] is True
    assert fixture["dominant_energy_condition"] is True
    assert fixture["blanket_no_go_disposition"] == "RETIRED_BY_PUBLISHED_COUNTEREXAMPLE"


def test_suppression_value_is_not_invented_without_duration() -> None:
    receipt = suppression_functional(w=Fraction(1, 4), g=Fraction(0), delta_n=None)
    assert receipt["status"] == "SUPPRESSION_CEILING_NOT_IDENTIFIED"
    assert receipt["value"] is None
    assert receipt["missing_inputs"] == ["N_f-N_i"]


def test_source_records_and_historical_archive_receipt_are_authenticated() -> None:
    provenance = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/pr171_primary_source_provenance.yaml").read_text(encoding="utf-8")
    )
    receipt = _json("docs/generated/pr171_source_verification.json")
    assert len(provenance["sources"]) == 5
    verified = {
        row["source_id"]: row
        for row in receipt["verified_sources"]
    }
    for row in provenance["sources"]:
        raw = REPO / row["raw_archive"]
        record = REPO / row["record"]
        assert record.is_file() and not record.is_symlink()
        assert sha(record) == row["record_sha256"]
        historical = verified[row["source_id"]]
        assert historical["ok"] is True
        assert historical["raw_path"] == row["raw_archive"]
        assert historical["raw_sha256"] == row["raw_sha256"]
        assert historical["raw_bytes"] == row["raw_bytes"]
        assert historical["record_path"] == row["record"]
        assert historical["record_sha256"] == row["record_sha256"]
        assert not raw.is_symlink()
        if raw.exists():
            assert raw.is_file()
            assert sha(raw) == row["raw_sha256"]
            assert raw.stat().st_size == row["raw_bytes"]
    assert receipt["ok"] is True
    assert receipt["source_count"] == 5


def test_contract_authorization_and_four_blind_receipts_are_hash_bound() -> None:
    contract = _json("docs/generated/pr171_cas/CAS_CONTRACT_PR171_CLASS_CONDITIONAL_TILT_V3.json")
    assert validate_contract(contract) == []
    authorization = _json("docs/generated/pr171_cas/preaxis_authorization_v3.json")
    assert authorization["axes_authorized"] is True
    assert authorization["all_results_absent_before_authorization"] is True
    assert authorization["errors"] == []
    collection = _json("docs/generated/pr171_cas_collection_receipt.json")
    contract_sha = sha(REPO / "docs/generated/pr171_cas/CAS_CONTRACT_PR171_CLASS_CONDITIONAL_TILT_V3.json")
    for axis in AXES:
        assignment_id = ASSIGNMENTS[axis]
        assignment_path = (
            REPO / GENERATION_3 / "assignments" / f"assignment_{axis}.json"
        )
        result_path = (
            REPO / GENERATION_3 / "outer_results" / f"outer_result_{axis}.json"
        )
        assignment = _json(assignment_path.relative_to(REPO))
        outer = _json(result_path.relative_to(REPO))
        nested = outer["payload"]["cas_axis_result"]
        assert assignment["assignment_sha256"] == assignment_self_hash(assignment)
        assert (
            authorization["assignments"][assignment_id]
            == collection["receipt_hashes"][axis]["assignment_sha256"]
        )
        assert assignment["allowed_sibling_results"] == []
        assert nested["sibling_results_read"] == []
        assert nested["contract_sha256"] == contract_sha
        assert set(nested["checks"] or {}) in (set(), set(contract["target"]["exact_test_obligations"]))


def test_historical_collection_is_strict_and_no_majority_vote_is_used() -> None:
    collection = _json("docs/generated/pr171_cas_collection_receipt.json")
    assert collection["aggregate_status"] in {"CAS_4AXIS_PASS", "CAS_BLOCKED"}
    assert collection["majority_vote_used"] is False
    assert collection["registered_exception_used"] is False
    assert collection["cross_generation_result_reuse"] is False
    assert collection["errors"] == []

    adjudication = _json(GENERATION_3 / "adjudication.json")
    assert adjudication == collection
    authorization = _json(
        "docs/generated/pr171_cas/preaxis_authorization_v3.json"
    )
    for axis in AXES:
        outer_path = (
            REPO / GENERATION_3 / "outer_results" / f"outer_result_{axis}.json"
        )
        nested_path = REPO / GENERATION_3 / f"axis_result_{axis}.json"
        assignment_id = ASSIGNMENTS[axis]
        outer = _json(outer_path.relative_to(REPO))
        receipt = collection["receipt_hashes"][axis]
        assert (
            authorization["assignments"][assignment_id]
            == receipt["assignment_sha256"]
        )
        assert outer["payload"]["cas_axis_result"] == _json(
            nested_path.relative_to(REPO)
        )
        assert receipt["outer_result_sha256"] == sha(outer_path)
        assert receipt["normalized_result_sha256"] == sha(nested_path)


def test_stored_four_axis_results_are_diagnostic_only() -> None:
    runner = _module(
        "scripts/codex_harness/run_pr171_tilt_relaxation.py",
        "pr171_current_cas_runner",
    )
    cas = runner._cas_status()
    assert cas["aggregate_status"] == "CAS_BLOCKED"
    assert cas["historical_aggregate_status"] == "CAS_4AXIS_PASS"
    assert cas["stored_cas_diagnostic_only"] is True
    assert cas["claim_promotion_cas_eligible"] is False


def test_generation_one_failures_are_preserved_and_not_reused() -> None:
    first = _json("docs/generated/pr171_cas/generation_1/adjudication.json")
    assert first["aggregate_status"] == "PROCESS_EVIDENCE_INVALID"
    assert first["axis_statuses"] == {
        "lean": "MISSING",
        "sage_singular": "FAIL",
        "sympy": "FAIL",
        "wolfram_xact": "PASS",
    }
    snapshot = _json("docs/generated/pr171_cas/generation_1/source_snapshot_manifest.json")
    assert snapshot["file_count"] >= 30
    second = _json("docs/generated/pr171_cas/generation_2/adjudication.json")
    assert second["aggregate_status"] == "CAS_FAIL"
    assert second["axis_statuses"] == {
        "lean": "FAIL",
        "sage_singular": "FAIL",
        "sympy": "FAIL",
        "wolfram_xact": "PASS",
    }
    second_snapshot = _json("docs/generated/pr171_cas/generation_2/source_snapshot_manifest.json")
    assert second_snapshot["file_count"] >= 30
    collection = _json("docs/generated/pr171_cas_collection_receipt.json")
    assert collection["cross_generation_result_reuse"] is False


def test_total_router_withholds_nonpass_exact_targets() -> None:
    blocked = route_terminal_result(
        "CAS_BLOCKED", provenance_ok=True, counterexample_gate=False, source_space_closed=False
    )
    assert blocked["process_gate_status"] == "BLOCKED"
    assert blocked["suppression_result"] is None
    failed = route_terminal_result(
        "CAS_FAIL", provenance_ok=True, counterexample_gate=False, source_space_closed=False
    )
    assert failed["process_gate_status"] == "FAIL"
    retired = route_terminal_result(
        "CAS_4AXIS_PASS", provenance_ok=True, counterexample_gate=True, source_space_closed=False
    )
    assert retired["candidate_disposition"] == "RETIRED"
    assert retired["suppression_result"] is None


def test_result_pack_is_claim_safe_and_all_live_mutants_are_killed() -> None:
    runner = _module("scripts/codex_harness/run_pr171_tilt_relaxation.py", "pr171_result_runner")
    artifacts = runner.build()
    result = artifacts["result"]
    runner.validate_terminal_card(result)
    assert result["cas_status"] == "CAS_BLOCKED"
    assert result["historical_cas_status"] == "CAS_4AXIS_PASS"
    assert result["exact_stability_result"] is None
    assert result["claim_promotion_cas_eligible"] is False
    assert result["blanket_no_go_status"] == "RETIRED_BY_AUTHENTICATED_EXTERNAL_SOURCE"
    assert result["suppression_result"] is None
    assert result["suppression_status"] == "SUPPRESSION_CEILING_NOT_IDENTIFIED"
    assert result["public_use"] is False
    mutations = artifacts["mutations"]
    assert mutations["registered_count"] == mutations["killed_count"] == 9
    assert mutations["survivors"] == []


def test_generated_pack_replays_byte_for_byte() -> None:
    done = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr171_tilt_relaxation.py"),
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert done.returncode == 2, done.stdout + done.stderr
    receipt = json.loads(done.stdout)
    assert receipt["ok"] is False
    assert receipt["cas_status"] == "CAS_BLOCKED"
    assert receipt["scientific_result"] == (
        "source_counterexample_audit_only_cas_blocked"
    )


def test_write_refuses_to_replace_frozen_result_pack() -> None:
    paths = sorted((REPO / "docs/generated").glob("pr171_*.json"))
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    done = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr171_tilt_relaxation.py"),
            "--write",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert done.returncode == 2
    assert "refusing to overwrite" in done.stderr
    assert {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    } == before


def test_review_archive_and_postcas_erratum_are_reproducible() -> None:
    archived = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/archive_pr171_reviews.py"),
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert archived.returncode == 0, archived.stdout + archived.stderr
    manifest = _json("docs/generated/pr171_reviews/manifest.json")
    assert manifest["copy_mode"] == "byte_for_byte"
    assert manifest["review_count"] == 4
    assert manifest["owner"] == "COMMON"
    assert manifest["config_hash"] == sha(
        REPO / "docs/research_program/long_horizon_rescue/pr171_spec.yaml"
    )
    assert set(manifest["input_hashes"]) == {
        row["source_path"] for row in manifest["reviews"]
    }
    archive_module = _module(
        "scripts/codex_harness/archive_pr171_reviews.py", "pr171_review_archive"
    )
    archive_module.SOURCES = {
        role: Path("workdir/nonexistent-clean-checkout") / f"{role}.json"
        for role in archive_module.SOURCES
    }
    assert archive_module.check_archive() == []

    erratum = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/pr171_spec_erratum.yaml").read_text(encoding="utf-8")
    )
    assert erratum["interpretation"]["sole_generation_3_cas_sealed_fixture"]["gamma"] == "5/4"
    assert erratum["interpretation"]["unregistered_source_only_alternate"]["cas_sealed"] is False
    assert erratum["adjudicator"]["path"] == "docs/generated/pr171_reviews/adjudicator.json"

    closeout = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/verify_pr171_postcas_closeout.py"),
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert closeout.returncode == 2, closeout.stdout + closeout.stderr
    current_closeout = json.loads(closeout.stdout)
    assert current_closeout["ok"] is False
    assert current_closeout["errors"] == [
        "pre-axis-bound result router drifted"
    ]
    closeout_manifest = _json("docs/generated/pr171_closeout_manifest.json")
    for key in (
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "mask_status",
        "covariance_status",
        "null_mock_status",
        "generating_command",
        "git_commit",
        "worktree_state",
    ):
        assert key in closeout_manifest


def test_stale_roadmap_number_is_explicitly_non_authoritative() -> None:
    spec = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/pr171_spec.yaml").read_text(encoding="utf-8")
    )
    assert spec["authority_resolution"]["output_value_frozen_in_advance"] is False
    assert "not an expected answer" in spec["authority_resolution"]["disposition"]
    assert spec["suppression_functional"]["numerical_result"] is None
