from __future__ import annotations

import importlib.util
from pathlib import Path

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script(path: str):
    script = REPO_ROOT / path
    spec = importlib.util.spec_from_file_location(script.stem, script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v7_external_audit_synthesis_maps_four_zip_inputs():
    mod = _load_script("scripts/build_v7_external_audit_synthesis.py")
    payload = mod.build_payload(
        generating_command="venv/bin/python scripts/build_v7_external_audit_synthesis.py")

    assert payload["schema"] == "htt.v7_external_audit_synthesis_matrix.v1"
    assert payload["owner"] == "COMMON"
    assert payload["claim_tier"] == "diagnostic_only"
    assert len(payload["zip_inputs"]) == 4
    assert all(row["integrity"] == "PASS" for row in payload["zip_inputs"])
    assert {row["id"] for row in payload["findings"]} >= {"F1", "F2", "M1", "M3"}
    assert any(row["id"] == "V7-002" for row in payload["v7_work_packages"])
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://v7_external_audit_synthesis_matrix.json",
        expected_artifact_path="docs/generated/v7_external_audit_synthesis_matrix.json",
    ) == ()


def test_v7_fortification_witnesses_cover_audit_repairs():
    mod = _load_script("scripts/run_v7_fortification_witnesses.py")
    payload = mod.build_payload(
        generating_command="venv/bin/python scripts/run_v7_fortification_witnesses.py")

    witnesses = payload["witnesses"]
    assert witnesses["F1_signed_box_identified_set"]["verdict"] == "PASS"
    assert witnesses["M1_gf_strictness"]["deterministic_sweep"]["agreement_exact_1.0"] is True
    assert witnesses["M3_estimated_covariance_two_stage"]["invalid_n_sim_rejected"] is True
    assert witnesses["M8_gate_policy"]["verdict"] == "PASS"
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://v7_fortification_witnesses.json",
        expected_artifact_path="docs/generated/v7_fortification_witnesses.json",
    ) == ()


def test_k5_cf4_identified_interval_card_blocks_observational_promotion():
    mod = _load_script("scripts/k5_cf4_identified_interval_card.py")
    payload = mod.build_payload(
        generating_command="venv/bin/python scripts/k5_cf4_identified_interval_card.py")

    assert payload["schema"] == "htt.k5.cf4_identified_interval_card.v1"
    assert payload["owner"] == "OBSSTAT"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["observational_claim_allowed"] is False
    # W2_upper promoted to the registered MES ceiling; Sigma2/Omega_k still block promotion
    assert {"Sigma2_hat", "Omega_k_upper"} <= set(payload["blocked_components"])
    assert "W2_upper" not in payload["blocked_components"]
    assert payload["component_input_modes"]["W2_upper"] == "REGISTERED_MES_CEILING"
    assert payload["component_input_modes"]["CF4_bulk_amplitude"] == "REAL"
    assert payload["component_input_modes"]["Omega_m"] == "DECLARED_OBS_DEFAULT"
    for policy in payload["policies"].values():
        assert set(policy["branches"]) == {"open_branch[0,Uk]", "all_branch[-Uk,Uk]"}
        assert all(branch["status"] == "FEASIBLE" for branch in policy["branches"].values())
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://k5_cf4_identified_interval_card.json",
        expected_artifact_path="docs/generated/k5_cf4_identified_interval_card.json",
    ) == ()


def test_v7_paper_a_revision_packet_records_claim_safe_replacements():
    mod = _load_script("scripts/build_v7_paper_a_revision_packet.py")
    payload = mod.build_payload(
        generating_command="venv/bin/python scripts/build_v7_paper_a_revision_packet.py")

    targets = {row["target"] for row in payload["replacement_rules"]}
    assert {"P31", "P35", "P36", "MES", "figures"} <= targets
    assert payload["tex_skeleton_path"] == "docs/generated/v7_paper_a_skeleton.tex"
    assert any(
        "estimated_covariance_f" in row["replacement"]
        for row in payload["replacement_rules"]
    )
    assert any(
        "shared-extrema conflict" in row["replacement"]
        for row in payload["replacement_rules"]
    )
    assert "observed x_C result while any component remains PLUGIN/BLOCKED" in (
        payload["forbidden_promotions"]
    )
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://v7_paper_a_revision_packet.json",
        expected_artifact_path="docs/generated/v7_paper_a_revision_packet.json",
    ) == ()
