"""PR-190: typed comparator attainability with fail-closed sharpness levels."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.comparator_attainability import (  # noqa: E402
    ComparatorAttainabilityError,
    CongruenceClass,
    EndpointKind,
    ProgrammeOutcome,
    REGISTERED_TARGETS,
    SharpnessLevel,
    SharpnessStatus,
    bind_registered_witness,
    build_registered_typed_witnesses,
    evaluate_registered_attainability,
)
from common.joint_anisotropy_state import JointAnisotropyState  # noqa: E402
from common.transfer_registry import TransferSource  # noqa: E402


SPEC = REPO / "docs/research_program/strengthening/pr190_spec.yaml"
POLICY = REPO / "docs/research_program/strengthening/pr190_publication_policy.json"
CAS_CONTRACT = REPO / "docs/research_program/strengthening/pr190_cas/CAS_CONTRACT.json"
CAS_ADJUDICATION = REPO / "docs/research_program/strengthening/pr190_cas/CAS_ADJUDICATION.json"
RESULT = REPO / "docs/generated/pr190_attainability/attainability_report.json"
RUNNER = REPO / "scripts/codex_harness/run_pr190_attainability.py"
BACKLOG = REPO / "docs/codex_handoff/pr_backlog.yaml"
STATUS = REPO / "docs/codex_handoff/pr_status.yaml"
REQUIRED_AXES = ["wolfram_xact", "sympy", "sage_singular", "lean"]


@pytest.fixture(scope="module")
def witnesses():
    return build_registered_typed_witnesses()


@pytest.fixture(scope="module")
def report(witnesses):
    return evaluate_registered_attainability(witnesses)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_spec_freezes_unweakened_four_level_claim_and_canonical_axes():
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert spec["baseline_commit"] == "7214ef7e91763ed807e0e350e1cfeffb82cec0f5"
    assert spec["claim_tier_ceiling"] == "theorem_candidate"
    assert spec["public_use"] is False
    assert spec["required_cas_axes"] == REQUIRED_AXES
    assert spec["optional_non_gating_axes"] == ["rocq"]
    assert [item["id"] for item in spec["sharpness_levels"]] == [
        "algebraic",
        "constraint",
        "local_dynamical",
        "global_dynamical",
    ]
    assert "every interior value" in spec["claim_identity"]["statement"]
    assert "the statement must be weakened to pass" in spec["kill_conditions"]


def test_registered_targets_are_exact_and_reproduce_comparator():
    expected = {
        EndpointKind.LOWER: (Fraction(3, 25), Fraction(1, 25), Fraction(3, 100), Fraction(0), Fraction(11, 100)),
        EndpointKind.INTERIOR_CHALLENGE: (Fraction(3, 25), Fraction(3, 100), Fraction(3, 100), Fraction(0), Fraction(3, 25)),
        EndpointKind.UPPER: (Fraction(3, 25), Fraction(0), Fraction(3, 100), Fraction(1, 50), Fraction(17, 100)),
    }
    for kind, values in expected.items():
        target = REGISTERED_TARGETS[kind]
        assert (
            target.sigma2,
            target.w2,
            target.omega_tilt,
            target.delta_omega_k,
            target.x_c,
        ) == values
        assert target.sigma2 - target.w2 + target.omega_tilt + target.delta_omega_k == target.x_c


def test_each_witness_seals_typed_state_orbit_frame_matter_epoch_and_scale(witnesses):
    assert tuple(item.target.kind for item in witnesses) == tuple(EndpointKind)
    for witness in witnesses:
        replay = JointAnisotropyState.from_payload(witness.state.to_payload())
        assert replay.content_id == witness.state.content_id
        assert witness.orbit_report.source_state_id == witness.state.content_id
        assert witness.matter_model.frame == witness.state.frame
        assert witness.epoch_window == witness.state.epoch_window
        assert witness.averaging_scale == witness.state.averaging_scale
        assert witness.state.transfer_source is TransferSource.NONE
        assert witness.state.transfer_spec is None
        assert witness.matter_model.net_flux_parity_sum == 0
        assert witness.matter_model.omega_tilt == Fraction(3, 100)
        assert witness.algebraically_matches_target is True


def test_factory_rejects_cross_state_orbit_and_frame_substitution(witnesses):
    lower, _, upper = witnesses
    with pytest.raises(ComparatorAttainabilityError, match="orbit report"):
        bind_registered_witness(
            kind=EndpointKind.LOWER,
            state=lower.state,
            orbit_report=upper.orbit_report,
            matter_model=lower.matter_model,
            solution_receipt=lower.solution_receipt,
        )
    with pytest.raises(ComparatorAttainabilityError, match="same frame"):
        bind_registered_witness(
            kind=EndpointKind.LOWER,
            state=lower.state,
            orbit_report=lower.orbit_report,
            matter_model=replace(lower.matter_model, frame="different frame"),
            solution_receipt=lower.solution_receipt,
        )


def test_lower_and_interior_normal_targets_are_constraint_refutations(report):
    by_pair = {(item.target_id, item.level): item for item in report.decisions}
    lower = REGISTERED_TARGETS[EndpointKind.LOWER]
    interior = REGISTERED_TARGETS[EndpointKind.INTERIOR_CHALLENGE]
    upper = REGISTERED_TARGETS[EndpointKind.UPPER]
    for target in (lower, interior):
        assert target.congruence_class is CongruenceClass.HYPERSURFACE_NORMAL
        assert by_pair[(target.endpoint_id, SharpnessLevel.ALGEBRAIC)].status is SharpnessStatus.ATTAINED
        assert by_pair[(target.endpoint_id, SharpnessLevel.CONSTRAINT)].status is SharpnessStatus.REFUTED
        assert by_pair[(target.endpoint_id, SharpnessLevel.LOCAL_DYNAMICAL)].status is SharpnessStatus.BLOCKED
        assert by_pair[(target.endpoint_id, SharpnessLevel.GLOBAL_DYNAMICAL)].status is SharpnessStatus.BLOCKED
    assert by_pair[(upper.endpoint_id, SharpnessLevel.CONSTRAINT)].status is SharpnessStatus.ATTAINED
    assert by_pair[(upper.endpoint_id, SharpnessLevel.LOCAL_DYNAMICAL)].status is SharpnessStatus.INCONCLUSIVE
    assert by_pair[(upper.endpoint_id, SharpnessLevel.GLOBAL_DYNAMICAL)].status is SharpnessStatus.BLOCKED


def test_full_statement_closes_as_failed_receipt_without_theorem_capability(report):
    assert report.outcome is ProgrammeOutcome.FULL_TYPED_DYNAMICAL_SHARPNESS_REFUTED
    assert report.execution_resolution == "COMPLETED_FAILED_WITH_RECEIPT"
    assert report.success_dependency_satisfied is False
    assert report.theorem_capability == "WITHHELD_PENDING_PR285"
    assert report.claim_ceiling == "theorem_candidate"
    assert report.public_use is False
    assert report.decisive_falsifier
    with pytest.raises(ComparatorAttainabilityError, match="evaluator-only"):
        replace(report)


def test_four_axis_contract_covers_both_exact_normal_frame_residuals():
    contract = json.loads(CAS_CONTRACT.read_text(encoding="utf-8"))
    obligations = contract["target"]["exact_test_obligations"]
    expected = contract["target"]["expected_exact_values"]
    assert contract["required_axes"] == REQUIRED_AXES
    assert "lower_endpoint_same_frame_contradiction" in obligations
    assert "interior_endpoint_same_frame_contradiction" in obligations
    assert expected["lower_contradiction_residual"] == "1/25"
    assert expected["interior_contradiction_residual"] == "3/100"
    assert contract["exceptions_adjudication"]["preregistered_exceptions"] == []


def test_cas_adjudication_is_bound_four_axis_evidence_only():
    adjudication = json.loads(CAS_ADJUDICATION.read_text(encoding="utf-8"))
    assert adjudication["aggregate_status"] == "CAS_4AXIS_PASS"
    assert adjudication["required_axes"] == REQUIRED_AXES
    assert adjudication["axis_statuses"] == {axis: "PASS" for axis in REQUIRED_AXES}
    assert adjudication["contract_sha256"] == _sha256(CAS_CONTRACT)
    assert adjudication["missing_axes"] == []
    assert adjudication["exceptions_applied"] == []


def test_generated_result_is_source_bound_and_negative():
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    assert payload["terminal"] == "COMPLETED_FAILED_WITH_RECEIPT"
    assert payload["success_dependency_satisfied"] is False
    assert payload["scientific_disposition"] == {
        "capability_granted": False,
        "statement_weakened": False,
        "status": "REFUTED_REGISTERED_FULL_ATTAINABILITY_STATEMENT",
        "theorem_capability": "WITHHELD_PENDING_PR285",
    }
    assert payload["metadata"]["observed_data_executed"] is False
    assert payload["metadata"]["transfer_source"] == "none"
    assert payload["metadata"]["public_use"] is False
    assert payload["metadata"]["generated_from"]["spec"]["sha256"] == _sha256(SPEC)
    assert payload["cas_evidence"]["aggregate_status"] == "CAS_4AXIS_PASS"
    assert payload["result"]["refuted_stage_count"] == 2


def test_generator_replay_is_byte_stable():
    completed = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "check"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout.strip().splitlines()[-1]) == {
        "mode": "check",
        "ok": True,
        "read_only": True,
        "terminal": "COMPLETED_FAILED_WITH_RECEIPT",
    }


def test_publication_policy_keeps_external_delivery_and_claim_boundaries_closed():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["publication_requires_external_publisher"] is True
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert policy["claim_ceiling"] == "theorem_candidate"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert "theorem_capability_withheld_until_pr285" in policy["required_review_cells"]


def test_canonical_status_closes_success_edge_without_unblocking_pr191():
    status = yaml.safe_load(STATUS.read_text(encoding="utf-8"))
    cards = {
        card["id"]: card
        for card in yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))["prs"]
    }
    assert "PR-190" in status["blocked"]
    assert "PR-190" not in status["pending"]
    active = status["in_progress"]
    if active is not None:
        stack = status["stacked_pr_execution"]
        assert stack["execution_mode"] == "AUTO_STACKED_PR"
        assert stack["active_implementation_pr"] == active
    assert active != "PR-191"
    assert "PR-191" in status["pending"]
    assert "PR-191" not in status["completed"]
    resolution = status["execution_resolutions"]["PR-190"]
    assert resolution["resolution"] == "COMPLETED_FAILED_WITH_RECEIPT"
    assert resolution["success_dependency_satisfied"] is False
    assert resolution["aggregate_cas_verdict"] == "CAS_4AXIS_PASS"
    assert resolution["public_use"] is False
    assert cards["PR-191"]["dependency_contracts"] == [
        {"upstream_id": "PR-187", "mode": "requires_success"},
        {"upstream_id": "PR-190", "mode": "requires_success"},
    ]
