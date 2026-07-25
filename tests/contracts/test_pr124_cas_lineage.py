"""PR-124 contract tests: historical CAS record + derivation-lineage oracle.

Covers historical CAS_4AXIS_PASS binding without current authority, honest
theorem counting (the 65-entry overstatement must fail), branch/lineage
fail-closed validation, D2 receipt zero-test, and mutation-report completeness.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from common.mes_theorem_authority import (
    AUTHORITY_TABLE_PATH,
    BRANCHES,
    CAS_ADJUDICATION_PATH,
    CAS_CONTRACT_PATH,
    D2_RECEIPT_PATH,
    LINEAGE_RECEIPT_PATH,
    MesAuthorityError,
    branch_table_payload,
    count_independent_lineages,
    sha256_file,
    validate_branch_entry,
    validate_claimed_lineage_count,
    validate_d2_receipt,
    verify_authority_receipt,
)
from common.theorem_signatures import (
    LEGACY_REGISTRY_SHA256,
    TheoremSignatureError,
    load_signature_registry,
)
from scripts.codex_harness import run_pr124_cas_lineage as pr124_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = (
    REPO_ROOT / "docs/research_program/long_horizon_rescue/pr124_spec.yaml"
)


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def adjudication() -> dict:
    return json.loads(
        (REPO_ROOT / CAS_ADJUDICATION_PATH).read_text(encoding="utf-8")
    )


def test_spec_schema_and_remediation_contract(spec: dict) -> None:
    assert spec["schema"] == "htt.long_horizon.pr124_cas_lineage.v1"
    contract = spec["remediation_state_contract"]
    assert contract["finding_count"] == 102
    assert contract["required_scientific_status_counts"] == {"OPEN": 102}
    assert contract["rescued_count"] == 0
    assert spec["claim_level"]["level"] == "C1"
    assert spec["claim_tier_ceiling"] == "conditional"


def test_historical_generation_location_is_not_live_check_authority() -> None:
    frozen = {
        "payload": {"value": 1},
        "generating_command": "/owner/checkout/venv/bin/python runner.py",
        "git_commit_or_worktree_state": "old-commit; dirty",
    }
    current = {
        "payload": {"value": 1},
        "generating_command": "/clean/clone/venv/bin/python runner.py",
        "git_commit_or_worktree_state": "new-commit",
    }
    assert pr124_runner._semantic(frozen) == pr124_runner._semantic(current)
    current["payload"]["value"] = 2
    assert pr124_runner._semantic(frozen) != pr124_runner._semantic(current)


def test_historical_cas_adjudication_is_four_axis_pass_bound_to_contract(
    adjudication: dict,
) -> None:
    assert adjudication["aggregate_status"] == "CAS_4AXIS_PASS"
    contract_sha = sha256_file(REPO_ROOT / CAS_CONTRACT_PATH)
    assert adjudication["contract_sha256"] == contract_sha
    statuses = adjudication["axis_statuses"]
    assert sorted(statuses) == ["lean", "sage_singular", "sympy", "wolfram_xact"]
    assert all(status == "PASS" for status in statuses.values())
    assert adjudication["missing_axes"] == []
    assert adjudication["errors"] == []


def test_stored_axis_replay_is_currently_blocked() -> None:
    axis_rel = {
        axis: f"docs/generated/pr124_cas/axis_result_{axis}.json"
        for axis in ("wolfram_xact", "sympy", "sage_singular", "lean")
    }
    replay = pr124_runner._adjudicate(CAS_CONTRACT_PATH, axis_rel)
    assert replay["gate_exit_code"] == 2
    assert replay["verification_state"] == "HISTORICAL_REPLAY"
    assert replay["aggregate_status"] == "CAS_BLOCKED"
    assert replay["historical_aggregate_status"] == "CAS_4AXIS_PASS"
    assert replay["claim_promotion_cas_requirement"] == "NOT_SATISFIED"


def test_axis_envelopes_bind_contract_and_agree_exactly(spec: dict) -> None:
    expected = spec["cas_contract"]["expected_exact_values"]
    contract_sha = sha256_file(REPO_ROOT / CAS_CONTRACT_PATH)
    computed_values = []
    for axis in ("wolfram_xact", "sympy", "sage_singular", "lean"):
        envelope = json.loads(
            (REPO_ROOT / f"docs/generated/pr124_cas/axis_result_{axis}.json")
            .read_text(encoding="utf-8")
        )
        assert envelope["axis"] == axis
        assert envelope["status"] == "PASS"
        assert envelope["contract_sha256"] == contract_sha
        assert envelope["evidence_class"] == "exact"
        assert envelope["commands"], "axis must record actual commands"
        checks = envelope["checks"]
        assert set(checks) == {
            "sigma_reduction", "omega_reduction", "e1_crit_coefficients",
            "w2_ceiling_exact", "sigma2_ceiling_exact",
            "hierarchy_e1_zero_strict", "hierarchy_observed_fails",
            "boundary_e1_crit_equality",
        }
        assert all(checks.values())
        assert envelope["source_output_hashes"], (
            "axis-script bytes must be hash-recorded"
        )
        if envelope.get("computed"):
            computed_values.append(envelope["computed"])
    # zero sign/coefficient/domain disagreement between engines — ALL FOUR
    # axes must emit cross-checkable computed values
    assert len(computed_values) == 4
    for computed in computed_values:
        assert [Fraction(v) for v in computed["sigma_triple"]] == [
            Fraction(v) for v in expected["sigma_triple"]
        ]
        assert [Fraction(v) for v in computed["omega_triple"]] == [
            Fraction(v) for v in expected["omega_triple"]
        ]
        assert Fraction(computed["W2_max_exact"]) == Fraction(
            expected["W2_max_exact"]
        )
        assert Fraction(computed["Sigma2_max_exact"]) == Fraction(
            expected["Sigma2_max_exact"]
        )


def test_engine_agreement_never_counts_as_derivation_independence() -> None:
    lineage = json.loads(
        (REPO_ROOT / LINEAGE_RECEIPT_PATH).read_text(encoding="utf-8")
    )
    assert "COMPUTATIONAL REPRODUCIBILITY" in lineage["metric_separation_note"]
    # four passing engines exist, yet the geodesic sigma branch counts
    # exactly its registered non-engine lineages
    sigma = lineage["branches"]["MES_G_SIGMA"]
    assert sigma["independent_derivation_count"] == 2


def test_theorem_inventory_honest_count_and_overstatement_kill() -> None:
    inventory = json.loads(
        (REPO_ROOT / "docs/generated/pr124_theorem_inventory.json")
        .read_text(encoding="utf-8")
    )
    assert inventory["legacy_entry_count"] == 65
    assert inventory["legacy_registry_sha256"] == LEGACY_REGISTRY_SHA256
    assert inventory["honest_theorem_count"] < inventory["legacy_entry_count"]
    assert inventory["old_overstatement_killed"] is True
    registry = load_signature_registry(REPO_ROOT)
    assert registry.theorem_count() == inventory["honest_theorem_count"]
    with pytest.raises(TheoremSignatureError, match="exceeds the honest"):
        registry.reject_overstated_count(65)


def test_sanity_anchor_and_specification_never_count() -> None:
    registry = load_signature_registry(REPO_ROOT)
    for entry in registry.entries:
        if entry.evidence_grade.value in {
            "sanity_anchor", "specification", "numerical_test"
        }:
            assert entry.counts_toward_theorem_count is False
        if entry.legacy_status in {"SUPERSEDED", "RETRACTED", "WITHHELD",
                                   "PLANNED"}:
            assert entry.counts_toward_theorem_count is False
        if entry.signature_status.value == "MIGRATION_PENDING":
            assert entry.counts_toward_theorem_count is False
            with pytest.raises(TheoremSignatureError, match="CHECKED"):
                entry.all_parameter_prose()


def test_branch_swap_and_inflation_are_killed() -> None:
    with pytest.raises(MesAuthorityError, match="does not match"):
        validate_branch_entry(
            "MES_NG_OMEGA",
            {
                "congruence": "non_geodesic",
                "status": "UNVERIFIED_PRINT_ONLY",
                "coefficients_exact": ["10/3", "2/15", "0"],
                "independent_derivation_count": 1,
            },
        )
    with pytest.raises(MesAuthorityError, match="exceeds the fingerprint"):
        validate_claimed_lineage_count(
            [
                {"lineage_id": "a", "implementation_fingerprint": "same"},
                {"lineage_id": "b", "implementation_fingerprint": "same"},
            ],
            2,
        )
    assert count_independent_lineages(
        [
            {"lineage_id": "a", "implementation_fingerprint": "same"},
            {"lineage_id": "b", "implementation_fingerprint": "same"},
        ]
    ) == 1


def test_non_geodesic_branches_stay_unverified() -> None:
    table = branch_table_payload()
    for branch_id in ("MES_NG_OMEGA", "MES_NG_ACCEL"):
        row = table[branch_id]
        assert row["status"] == "UNVERIFIED_PRINT_ONLY"
        assert row["independent_derivation_count"] < 2
    for branch_id in ("MES_G_SIGMA", "MES_G_OMEGA", "MES_G_ACCEL"):
        assert table[branch_id]["independent_derivation_count"] >= 2


def test_d2_receipt_nonzero_and_zero_mutant_killed() -> None:
    receipt = json.loads(
        (REPO_ROOT / D2_RECEIPT_PATH).read_text(encoding="utf-8")
    )
    assert receipt["rust_target"]["d2_value_uK2"] > 0.0
    assert receipt["rust_target"]["tests_passed"] >= 1
    assert receipt["python_anchor"]["tests_passed"] == receipt[
        "python_anchor"]["tests_collected"]
    validate_d2_receipt(receipt, REPO_ROOT)
    mutant = json.loads(json.dumps(receipt))
    mutant["rust_target"]["d2_value_uK2"] = 0.0
    with pytest.raises(MesAuthorityError, match="NONZERO"):
        validate_d2_receipt(mutant, REPO_ROOT)
    for malformed in (float("inf"), True):
        mutant = json.loads(json.dumps(receipt))
        mutant["rust_target"]["d2_value_uK2"] = malformed
        with pytest.raises(MesAuthorityError, match="finite numeric"):
            validate_d2_receipt(mutant, REPO_ROOT)
    # the receipt must not claim the bit-identical dump anchor
    assert "1002.086744" not in json.dumps(receipt["rust_target"])


def test_mutation_report_complete_and_zero_survivors(spec: dict) -> None:
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr124_mutation_report.json")
        .read_text(encoding="utf-8")
    )
    registered = [m["mutation_id"] for m in spec["mutation_registry"]]
    executed = [m["mutation_id"] for m in report["mutations"]]
    assert executed == registered
    assert all(m["executed"] and m["killed"] for m in report["mutations"])
    assert report["surviving_mutation_count"] == 0


def test_authority_receipt_is_historical_and_binds_artifacts() -> None:
    table = json.loads(
        (REPO_ROOT / AUTHORITY_TABLE_PATH).read_text(encoding="utf-8")
    )
    assert table["branch_table"] == branch_table_payload()
    for rel, digest in table["bound_artifacts"].items():
        assert sha256_file(REPO_ROOT / rel) == digest
    with pytest.raises(MesAuthorityError, match="diagnostic-only"):
        verify_authority_receipt(REPO_ROOT)


def test_successor_pointer_receipt_bytes_do_not_grant_current_authority() -> None:
    from common.mes_successor_registry import (
        PR124_AUTHORITY_RECEIPT_SHA256,
        PR124_AUTHORITY_SOURCE_SHA256,
        current_mes_successor_registry,
    )

    assert PR124_AUTHORITY_RECEIPT_SHA256 == sha256_file(
        REPO_ROOT / AUTHORITY_TABLE_PATH
    )
    assert PR124_AUTHORITY_SOURCE_SHA256 == sha256_file(
        REPO_ROOT / "htt/src/common/mes_theorem_authority.py"
    )
    registry = current_mes_successor_registry()
    assert registry.successor.scientific_authority is False
    assert registry.as_payload()["release_claim_allowed"] is False


def test_frozen_modules_untouched(spec: dict) -> None:
    """The legacy registry and the frozen MES modules stay byte-identical to
    the spec-pinned hashes (quarantine discipline; hash pins survive
    commits, unlike a `git diff HEAD` check)."""
    frozen = spec["scope_and_non_goals"]["frozen_modules_must_not_change"]
    assert isinstance(frozen, dict) and frozen
    for rel, digest in frozen.items():
        assert sha256_file(REPO_ROOT / rel) == digest, (
            f"frozen module changed: {rel}"
        )


def test_branches_registry_shape() -> None:
    assert set(BRANCHES) == {
        "MES_G_SIGMA", "MES_G_OMEGA", "MES_G_ACCEL",
        "MES_NG_OMEGA", "MES_NG_ACCEL",
    }
    for branch_id, entry in BRANCHES.items():
        assert entry["congruence"] in {"geodesic", "non_geodesic"}
        assert entry["sources"], branch_id
        assert entry["physical_assumption_uncertainty"], branch_id


def test_branches_bound_to_adjudicated_contract_values() -> None:
    """P0 guard regression: BRANCHES coefficients must equal the four-axis
    adjudicated contract values; a corrupted expected-value set is rejected
    by the same guard that runs inside the authority verification."""
    from common.mes_theorem_authority import _branches_match_contract

    contract = json.loads(
        (REPO_ROOT / CAS_CONTRACT_PATH).read_text(encoding="utf-8")
    )
    expected = contract["target"]["expected_exact_values"]
    _branches_match_contract(expected)  # clean twin passes

    corrupted = json.loads(json.dumps(expected))
    corrupted["sigma_triple"] = ["5/3", "3", "3/8"]
    with pytest.raises(MesAuthorityError, match="differ from the"):
        _branches_match_contract(corrupted)

    bad_ceiling = json.loads(json.dumps(expected))
    bad_ceiling["W2_max_exact"] = str(
        Fraction(bad_ceiling["W2_max_exact"]) / 3
    )
    with pytest.raises(MesAuthorityError, match="ceiling map violated"):
        _branches_match_contract(bad_ceiling)
