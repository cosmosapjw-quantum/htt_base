from __future__ import annotations

import importlib.util
import json
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
    payload = json.loads(
        (REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["schema"] == "htt.cf4_p0_quarantine_block.v1"
    assert payload["owner"] == "COMMON"
    assert payload["claim_tier"] == "blocked"
    assert payload["status"] == "QUARANTINED_OPEN_FINDINGS"
    assert payload["allowed_use"] == "blocked_source_record_only"
    assert payload["replacement_value"] is None
    assert "component_input_modes" not in payload
    assert "policies" not in payload
    assert all(row["scientific_status"] == "OPEN" for row in payload["findings"])


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
