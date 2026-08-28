from __future__ import annotations

import pytest


EXPECTED_THEOREM_IDS = {"S1", "S3", "S4", "S5", "G2", "G5", "B4"}
REQUIRED_KILL_SWITCHES = {
    "unbounded_multipole_bridge_blocks_s2_observational_use",
    "acceleration_temp_gradient_block_missing_blocks_flrw_egs_promotion",
    "stiff_fluid_singularity_blocks_g3_inversion",
    "bianchi_i_assumptions_missing_blocks_g4_exact_flow_use",
    "slope_degeneracy_blocks_slope_only_source_discrimination",
    "collision_gap_nonpositive_blocks_exponential_forgetting_language",
    "source_rank_near_zero_blocks_inverse_source_claim",
    "line_of_sight_sign_phase_incoherence_blocks_source_upper_bound",
    "derivative_weyl_diagnostics_missing_blocks_almost_egs_promotion",
    "data_residual_provenance_not_bound_blocks_data_facing_residual",
    "visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound",
}


def test_default_theorem_registry_entries_are_complete_and_diagnostic_only() -> None:
    from common.theorem_registry import default_theorem_registry

    registry = default_theorem_registry()
    assert set(registry.ids()) == EXPECTED_THEOREM_IDS

    for theorem_id in EXPECTED_THEOREM_IDS:
        entry = registry.get(theorem_id)
        payload = entry.as_payload()
        assert payload["theorem_id"] == theorem_id
        assert payload["status"] in {
            "analytic",
            "convention_conditional",
            "program_theorem",
            "observational_blocked",
        }
        assert payload["proof_status"] in {
            "assumption_recorded",
            "convention_conditional",
            "program_obligation",
            "observational_blocked",
        }
        assert payload["implementation_test_status"] == "synthetic_manufactured_only"
        assert payload["claim_status"] == "diagnostic_observational_use_blocked"
        assert payload["owner"] == "COMMON"
        assert payload["claim_tier"] == "diagnostic_only"
        assert payload["transfer_source"] == "none"
        assert payload["production_claim_allowed"] is False
        assert payload["observation_claim_allowed"] is False
        assert payload["native_solver_result"] is False
        assert payload["consumable_as_htt_evidence"] is False
        assert payload["consumable_as_mio_certificate"] is False
        assert payload["consumable_as_family_identification"] is False
        assert payload["assumptions"]
        assert payload["kill_switches"]
        assert payload["allowed_use"]
        assert payload["forbidden_use"]
        assert payload["test_file"].startswith("tests/")
        assert payload["generated_artifact_ids"]
        assert payload["caveats"]


def test_s1_registry_records_missing_kl_to_temperature_bridge_as_blocker() -> None:
    from common.theorem_registry import default_theorem_registry

    s1 = default_theorem_registry().get("S1").as_payload()

    assert s1["harmonic_convention_status"] == "declared_synthetic_density_only"
    assert s1["kl_to_temperature_bridge_status"] == "not_bound"
    assert "unbounded_multipole_bridge_blocks_s2_observational_use" in s1["kill_switches"]


def test_registry_tracks_required_kill_switches_without_observational_promotion() -> None:
    from common.theorem_registry import default_theorem_registry

    registry = default_theorem_registry()
    assert set(registry.required_kill_switches()) >= REQUIRED_KILL_SWITCHES

    blocked = registry.blocked_observational_uses()
    assert set(blocked) >= EXPECTED_THEOREM_IDS
    for reason in blocked.values():
        assert "synthetic" in reason or "blocked" in reason


def test_registry_lists_active_g2_b4_provenance_gates() -> None:
    from common.theorem_registry import default_theorem_registry

    registry = default_theorem_registry()
    assert (
        "data_residual_provenance_not_bound_blocks_data_facing_residual"
        in registry.get("G2").kill_switches
    )
    assert (
        "visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound"
        in registry.get("B4").kill_switches
    )


def test_theorem_registry_rejects_missing_claim_firewall_fields() -> None:
    from common.theorem_registry import TheoremEntry

    base = {
        "theorem_id": "BAD",
        "title": "Bad theorem",
        "status": "analytic",
        "assumptions": ("synthetic fixture",),
        "kill_switches": ("missing_gate",),
        "allowed_use": ("appendix synthetic check",),
        "forbidden_use": ("observed claim",),
        "test_file": "tests/contracts/test_theorem_registry.py",
        "generated_artifact_ids": ("bad",),
    }
    with pytest.raises(ValueError, match="claim_tier"):
        TheoremEntry(**base, claim_tier="validated")
    with pytest.raises(ValueError, match="transfer_source"):
        TheoremEntry(**base, transfer_source="BASS_native_validated")
    with pytest.raises(ValueError, match="native_solver_result"):
        TheoremEntry(**base, native_solver_result=True)
