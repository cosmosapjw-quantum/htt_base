from __future__ import annotations

from bass.validation import GATE_LADDER, hard_gate_before_fitting, score_branch_readiness


def test_hard_gate_before_fitting_blocks_when_output_split_missing() -> None:
    report = hard_gate_before_fitting(
        {
            "authority_freeze": True,
            "tensor_helper_correctness": True,
            "family_registry_freeze": True,
            "geometry_diagnostics_gate": True,
            "matter_projection_gate": True,
            "exact_thomson_gate": True,
            "visibility_history_gate": True,
            "family_backend_gate": True,
            "hierarchy_layout_gate": True,
            "output_split_gate": False,
        }
    )
    assert report["allowed"] is False
    assert "output_split_gate" in report["missing_gates"]


def test_hard_gate_before_fitting_opens_only_after_all_upstream_gates() -> None:
    report = hard_gate_before_fitting({gate: True for gate in GATE_LADDER[:-1]})
    assert report["allowed"] is True
    assert report["missing_gates"] == ()


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
