from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_JSON = REPO_ROOT / "docs" / "generated" / "theorem_extension_registry.json"
ARTIFACT_MD = REPO_ROOT / "docs" / "generated" / "theorem_extension_registry.md"
GENERATOR = REPO_ROOT / "scripts" / "generate_theorem_extension_assets.py"


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


def _payload() -> dict[str, object]:
    return json.loads(ARTIFACT_JSON.read_text(encoding="utf-8"))


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


def test_generated_theorem_extension_assets_match_registry_and_metadata() -> None:
    payload = _payload()
    metadata = payload["metadata"]
    rows = payload["theorems"]

    assert metadata["schema_version"] == "rev-r084.theorem_extension_registry.v1"
    assert metadata["owner"] == "COMMON"
    assert metadata["implementation_scope"] == "common"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["transfer_source"] == "none"
    assert metadata["sky_support_status"] == "not_directional"
    assert metadata["covariance_status"] == "synthetic_only"
    assert metadata["null_mock_status"] == "synthetic_only"
    assert metadata["production_claim_allowed"] is False
    assert metadata["native_solver_result"] is False
    assert metadata["family_identification"] is False
    assert metadata["config_hash"]
    assert metadata["input_hashes"]
    assert metadata["generating_command"]
    assert metadata["git_commit_or_worktree_state"]
    assert metadata["caveats"]
    assert set(metadata["required_kill_switches"]) >= REQUIRED_KILL_SWITCHES
    assert {row["theorem_id"] for row in rows} == EXPECTED_THEOREM_IDS


def test_generator_rebuilds_same_registry_rows(tmp_path: Path) -> None:
    output_json = tmp_path / "registry.json"
    output_md = tmp_path / "registry.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--write",
            "--json-output",
            str(output_json),
            "--markdown-output",
            str(output_md),
            "--generated-on",
            "2026-06-20T00:00:00+00:00",
            "--git-state",
            "test-state",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    regenerated = json.loads(output_json.read_text(encoding="utf-8"))
    current = _payload()
    assert regenerated["theorems"] == current["theorems"]
    ignored = {"generated_on", "generating_command", "git_commit_or_worktree_state"}
    assert {
        key: value
        for key, value in regenerated["metadata"].items()
        if key not in ignored
    } == {
        key: value for key, value in current["metadata"].items() if key not in ignored
    }
    assert output_md.read_text(encoding="utf-8").startswith("# Theorem Extension Registry")


def test_generated_markdown_states_synthetic_only_boundary() -> None:
    text = ARTIFACT_MD.read_text(encoding="utf-8").lower()

    for phrase in (
        "synthetic/manufactured verification only",
        "diagnostic-only",
        "not htt evidence",
        "not a mio certificate",
        "not native solver validation",
        "not geometry or family identification",
        "generated_on:",
        "generating_command:",
        "git_commit_or_worktree_state:",
        "input_hashes:",
        "data_residual_provenance_not_bound_blocks_data_facing_residual",
        "visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound",
    ):
        assert phrase in text
