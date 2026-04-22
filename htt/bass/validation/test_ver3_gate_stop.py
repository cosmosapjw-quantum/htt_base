from __future__ import annotations

from bass.validation import (
    GATE_LADDER,
    GateBundle,
    collect_gate_bundles,
    hard_gate_before_fitting,
    make_gate_bundle,
    score_branch_readiness,
    summarize_gate_status,
)


def _bundle(gate_name: str, *, passed: bool = True) -> GateBundle:
    return make_gate_bundle(
        gate_name,
        family="VII_h",
        branch="orthogonal",
        backend="class_b_helical_matrix_approx",
        truncation={"ell_max": 6},
        residual_summary={"max_residual": 1.0e-8},
        known_limit_checks={"status": "passed"},
        forbidden_shortcut_checks={"no_fake_support": True},
        metadata={"schema_version": "ver3-gate-bundle-v1"},
        passed=passed,
        opened_claim=f"{gate_name}: test-opened",
    )


def test_hard_gate_before_fitting_blocks_when_output_split_missing() -> None:
    report = hard_gate_before_fitting(
        {
            "authority_freeze": True,
            "tensor_helper_correctness": True,
                "family_registry_freeze": True,
                "geometry_diagnostics_gate": True,
                "matter_projection_gate": True,
                "background_core_gate": True,
                "exact_thomson_gate": True,
                "visibility_history_gate": True,
                "family_backend_gate": True,
                "hierarchy_layout_gate": True,
                "output_split_gate": False,
        }
    )
    assert report["allowed"] is False
    assert "output_split_gate" in report["missing_gates"]
    assert report["gate_status"]["output_split_gate"] == "closed"
    assert report["gate_status"]["fitting_gate"] == "unavailable"


def test_hard_gate_before_fitting_opens_only_after_all_upstream_gates() -> None:
    report = hard_gate_before_fitting({gate: _bundle(gate) for gate in GATE_LADDER[:-1]})
    assert report["allowed"] is True
    assert report["missing_gates"] == ()
    assert report["bundle_gates"] == GATE_LADDER[:-1]
    assert report["gate_status"]["fitting_gate"] == "closed"


def test_hard_gate_before_fitting_preserves_residual_and_metadata_payloads() -> None:
    report = hard_gate_before_fitting(
        {gate: _bundle(gate) for gate in GATE_LADDER[:-1]},
        residuals={"gauss_abs": 1.0e-8},
        metadata={"family": "VII_h"},
    )
    assert report["residuals"]["gauss_abs"] == 1.0e-8
    assert report["metadata"]["family"] == "VII_h"


def test_collect_gate_bundles_normalizes_mapping_payloads() -> None:
    registry = {
        "authority_freeze": _bundle("authority_freeze"),
        "tensor_helper_correctness": _bundle("tensor_helper_correctness").as_payload(),
    }
    bundles = collect_gate_bundles(registry)
    assert set(bundles) == {"authority_freeze", "tensor_helper_correctness"}
    assert bundles["tensor_helper_correctness"].opened_claim == (
        "tensor_helper_correctness: test-opened"
    )


def test_summarize_gate_status_marks_higher_gates_unavailable() -> None:
    registry = {
        "authority_freeze": _bundle("authority_freeze"),
        "tensor_helper_correctness": _bundle("tensor_helper_correctness"),
        "family_registry_freeze": _bundle("family_registry_freeze"),
        "geometry_diagnostics_gate": _bundle("geometry_diagnostics_gate", passed=False),
    }
    summary = summarize_gate_status(registry)
    assert summary["geometry_diagnostics_gate"] == "closed"
    assert summary["matter_projection_gate"] == "unavailable"
    assert summary["fitting_gate"] == "unavailable"


def test_score_branch_readiness_tracks_gate_ladder() -> None:
    assert score_branch_readiness({}) == 0
    assert score_branch_readiness(
        {
            "authority_freeze": True,
            "tensor_helper_correctness": True,
            "family_registry_freeze": True,
        }
    ) == 4
    assert score_branch_readiness(
        {
            "authority_freeze": True,
            "tensor_helper_correctness": True,
            "family_registry_freeze": True,
            "geometry_diagnostics_gate": True,
            "matter_projection_gate": True,
            "exact_thomson_gate": True,
            "visibility_history_gate": True,
            "family_backend_gate": True,
        }
    ) == 6
    assert score_branch_readiness({gate: True for gate in GATE_LADDER[:-1]}) == 8
    assert score_branch_readiness({gate: True for gate in GATE_LADDER}) == 10
