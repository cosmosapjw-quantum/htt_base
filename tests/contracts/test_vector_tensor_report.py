from __future__ import annotations

from collections import Counter
import copy
from io import BytesIO
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

from PIL import Image
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/vector_tensor/pr275_spec.yaml"
POLICY = ROOT / "docs/research_program/vector_tensor/pr275_publication_policy.json"
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
SIGNATURES = ROOT / "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
PROGRAMME_INTAKE = ROOT / "docs/research_program/vector_tensor/PROGRAM_INTAKE_REGISTRY_V1.yaml"
PROPOSAL = ROOT / "docs/research_program/vector_tensor/proof_registry_two_pillars.yaml"
T_CORE = ROOT / "docs/research_program/vector_tensor/proofs/PILLAR_T_CORE_PROOFS_V1.yaml"
T_CAS = ROOT / "docs/research_program/vector_tensor/proofs/PILLAR_T_CAS_PROOFS_V1.yaml"
S_CORE = ROOT / "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml"
S_INFERENCE = ROOT / "docs/research_program/vector_tensor/proofs/PILLAR_S_INFERENCE_VALIDATION_V1.yaml"
PR273_PACK = ROOT / "docs/research_program/vector_tensor/integration/PR273_DIAGNOSTIC_PACK.json"
PR274_RESULT = ROOT / "docs/research_program/vector_tensor/data_admission/PR274_ADMISSION_RESULT.json"
GENERATOR = ROOT / "scripts/vector_tensor/build_pr275_proof_atlas.py"
REPORT_DIR = ROOT / "docs/research_program/vector_tensor/report"
ATLAS = REPORT_DIR / "PROOF_ATLAS.json"
ATLAS_MD = REPORT_DIR / "PROOF_ATLAS.md"
ANALYSIS = REPORT_DIR / "SYNTHETIC_CASE_ANALYSIS.json"
FIGURE = REPORT_DIR / "fig_pr275_synthetic_case_diagnostics.png"
MANIFEST = REPORT_DIR / "fig_pr275_synthetic_case_diagnostics.manifest.json"
REPLICATION = REPORT_DIR / "REPLICATION_PACKAGE.json"
REPORT = REPORT_DIR / "VECTOR_TENSOR_PROGRAM_REPORT.md"


def _yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _module():
    module_spec = importlib.util.spec_from_file_location("pr275_builder_test", GENERATOR)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_pr275_spec_card_policy_and_outputs_are_exact() -> None:
    spec = _yaml(SPEC)
    policy = _json(POLICY)
    backlog = _yaml(BACKLOG)
    card = next(record for record in backlog["prs"] if record["id"] == "PR-275")
    assert spec["dependencies"] == card["depends"] == ["PR-274"]
    assert spec["owner"] == card["owner"] == "COMMON"
    assert spec["claim_ceiling"] == policy["claim_ceiling"] == "diagnostic_only"
    assert spec["observed_data_used"] is False
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert policy["ordinary_agent_push_forbidden"] is True
    assert sorted(path.name for path in REPORT_DIR.iterdir()) == sorted(
        spec["outputs"]["required"]
    )


def test_every_frozen_input_matches_its_declared_identity() -> None:
    import hashlib

    spec = _yaml(SPEC)
    for label, record in spec["frozen_inputs"].items():
        path = ROOT / record["path"]
        assert path.is_file(), label
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], label


def test_source_obligation_rows_stay_unadjudicated_and_are_not_proof_counts() -> None:
    atlas = _json(ATLAS)
    source = atlas["source_obligation_registry"]
    assert source["row_count"] == 123
    assert source["row_count_is_proved_theorem_count"] is False
    assert source["proof_adjudication_status_counts"] == {"NOT_ADJUDICATED": 123}
    assert len(source["records"]) == 123
    assert all(
        record["proof_adjudication_status"] == "NOT_ADJUDICATED"
        for record in source["records"]
    )
    signatures = _yaml(SIGNATURES)
    assert signatures["proof_adjudication_status"] == "NOT_ADJUDICATED"


def test_cardinality_aliases_are_inventories_not_literal_proof_pillars() -> None:
    atlas = _json(ATLAS)
    summaries = atlas["source_obligation_registry"]["group_summaries"]
    assert atlas["cardinality_aliases"] == {
        "requested_pillar_T_65": "legacy_signature_inventory",
        "requested_pillar_S_58": "proposal_registry_rows",
    }
    assert summaries["legacy_signature_inventory"]["row_count"] == 65
    assert summaries["legacy_signature_inventory"]["partition_counts"] == {
        "S": 34,
        "T": 31,
    }
    assert summaries["proposal_registry_rows"]["row_count"] == 58
    assert summaries["proposal_registry_rows"]["partition_counts"] == {
        "BRIDGE": 4,
        "I": 30,
        "II": 24,
    }
    assert "not literal proof-pillar theorem counts" in atlas["counting_rule"]


def test_vt_programme_obligations_are_registered_linkable_and_unadjudicated() -> None:
    atlas = _json(ATLAS)["vt_programme_registry"]
    source = _yaml(PROGRAMME_INTAKE)["vt_theorem_obligations"]
    assert atlas["row_count"] == len(source["entries"]) == 28
    assert atlas["row_count_is_proved_theorem_count"] is False
    assert atlas["partition_counts"] == source["expected_counts"] == {
        "VT-S": 14,
        "VT-T": 14,
    }
    assert atlas["proof_adjudication_status_counts"] == {"NOT_ADJUDICATED": 28}
    assert [record["entry_id"] for record in atlas["records"]] == [
        record["id"] for record in source["entries"]
    ]
    assert all(
        record["proof_adjudication_status"] == "NOT_ADJUDICATED"
        and record["registration_status"] == "REGISTERED_OBLIGATION"
        for record in atlas["records"]
    )


@pytest.mark.parametrize(
    ("layer_id", "source_path", "source_field"),
    [
        ("pillar_t_core", T_CORE, "verdict"),
        ("pillar_t_cas", T_CAS, "verdict"),
        ("pillar_s_core", S_CORE, "verdict"),
        ("pillar_s_inference", S_INFERENCE, "validation_status"),
    ],
)
def test_evidence_layer_counts_and_verdicts_are_derived(
    layer_id: str,
    source_path: Path,
    source_field: str,
) -> None:
    source_records = _yaml(source_path)["records"]
    expected = dict(sorted(Counter(record[source_field] for record in source_records).items()))
    layer = _json(ATLAS)["evidence_layers"][layer_id]
    assert layer["record_count"] == len(source_records)
    assert layer["record_count_is_theorem_count"] is False
    assert layer["verdict_counts"] == expected
    assert all(
        record["source_proof_adjudication_status"] == "NOT_ADJUDICATED"
        for record in layer["records"]
    )
    assert all(
        record["source_reference"]["registry_id"]
        in {
            "theorem_signatures_v3",
            "theorem_signatures_v3_oracle_alias",
            "vt_programme_intake",
        }
        and record["source_reference"]["entry_id"]
        for record in layer["records"]
    )


def test_inconclusive_restricted_partial_and_failed_labels_render_exactly() -> None:
    atlas = _json(ATLAS)
    all_verdicts = {
        record["verdict"]
        for layer in atlas["evidence_layers"].values()
        for record in layer["records"]
    }
    assert "INCONCLUSIVE_MISSING_SIGNATURE" in all_verdicts
    assert "RESTRICTED_WITNESS_CONFIRMED" in all_verdicts
    assert "PARTIAL_CHAIN_RULE_CAS4" in all_verdicts
    assert "INCONCLUSIVE_NATIVE_GEOMETRY_GATE" in all_verdicts
    markdown = ATLAS_MD.read_text(encoding="utf-8")
    for verdict in (
        "INCONCLUSIVE_MISSING_SIGNATURE",
        "RESTRICTED_WITNESS_CONFIRMED",
        "PARTIAL_CHAIN_RULE_CAS4",
        "INCONCLUSIVE_NATIVE_GEOMETRY_GATE",
    ):
        assert verdict in markdown


def test_cas_aggregate_is_exception_free_but_has_no_source_promotion() -> None:
    cas = _json(ATLAS)["cas_adjudication"]
    assert cas["aggregate_status"] == "CAS_4AXIS_PASS"
    assert cas["missing_axes"] == []
    assert cas["exceptions_applied"] == []
    assert cas["source_status_effect"] == "none"
    assert set(cas["axis_statuses"]) == {
        "wolfram_xact",
        "sympy",
        "sage_singular",
        "lean",
    }


def test_proposal_registry_statuses_are_source_statuses_only() -> None:
    atlas = _json(ATLAS)["proposal_registry"]
    source = _yaml(PROPOSAL)["entries"]
    assert atlas["row_count"] == len(source) == 58
    assert atlas["pillar_counts"] == {"BRIDGE": 4, "I": 30, "II": 24}
    assert atlas["source_status_counts"] == dict(
        sorted(Counter(record["status"] for record in source).items())
    )
    assert atlas["row_count_is_proved_theorem_count"] is False


def test_synthetic_analysis_is_bound_to_five_registered_cases() -> None:
    analysis = _json(ANALYSIS)
    pack = _json(PR273_PACK)
    rows = analysis["case_summaries"]
    assert [record["case_id"] for record in rows] == ["C01", "C02", "C03", "C04", "C05"]
    assert analysis["partition_counts"] == {"development": 3, "held_out": 2}
    assert analysis["depth_alert_threshold"] == pack["depth_alert_threshold"] == 25.0
    assert analysis["source_pack"]["seed"] == pack["seed"] == 27320260730
    assert analysis["observed_data"] is False
    assert rows[2]["missing_functional"] is True
    assert rows[4]["depth_mean_normalized_score"] == 130.0
    assert rows[4]["depth_alert"] is True
    for source_record, derived in zip(pack["case_results"], rows, strict=True):
        assert derived["max_finite_abs_x"] == max(
            abs(value) for value in source_record["x_values"] if value is not None
        )
        assert derived["max_finite_abs_q"] == max(
            abs(value) for value in source_record["q_values"] if value is not None
        )


def test_figure_is_exactly_one_validation_category_and_synthetic_only() -> None:
    manifest = _json(MANIFEST)
    assert manifest["plot_category"] == "VALIDATION"
    assert manifest["categories"] == ["VALIDATION"]
    assert manifest["artifact_mode"] == "synthetic_diagnostic"
    assert manifest["claim_tier"] == "diagnostic_only"
    assert manifest["observed_data"] is False
    assert manifest["transfer_source"] == "none"
    assert manifest["sky_support_status"] == "synthetic_not_applicable"
    assert manifest["source_json"]["path"].endswith("SYNTHETIC_CASE_ANALYSIS.json")
    with Image.open(BytesIO(FIGURE.read_bytes())) as image:
        assert image.format == "PNG"
        assert image.size == (1600, 928)


def test_report_has_plot_summary_provenance_and_explicit_nonclaims() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for heading in (
        "## Plot summary",
        "## Quantity plotted",
        "## Data/script/manifest provenance",
        "## Category and claim tier",
        "## Interpretation",
        "## What this plot does not show",
        "## Missing validation before publication",
    ):
        assert heading in report
    assert "No manuscript number is assigned" in report
    assert re.search(r"manuscript\s+(?:no\.?|number)\s*[:#]?\s*\d", report, re.I) is None
    assert "registration alone confers no proof status" in report
    assert "VT programme partition: `" in report
    assert "NO_ADMITTED_DATA_PILOT" in report
    assert "Category: `VALIDATION` (exactly one category)" in report


def test_replication_package_carries_commands_environment_seeds_and_tolerances() -> None:
    package = _json(REPLICATION)
    assert package["claim_ceiling"] == "diagnostic_only"
    assert package["observed_data"] is False
    assert len(package["commands"]) >= 10
    assert package["environment"]["source_layout"] == "PYTHONPATH=htt/src:htt"
    assert package["seeds"]["pr272_master_seed"] == 27220260730
    assert package["seeds"]["pr272_seed_family"] == [
        272003,
        272005,
        272007,
        272009,
        272011,
    ]
    assert package["seeds"]["pr273_seed"] == 27320260730
    assert package["tolerances_and_acceptance"]["pr272_rank_tolerance"] == 1.0e-12
    assert package["tolerances_and_acceptance"]["pr273_depth_alert_threshold"] == 25.0
    assert package["source_identities"]
    assert package["generated_artifact_identities"]


def test_pr274_no_admitted_data_boundary_is_preserved() -> None:
    result = _json(PR274_RESULT)
    atlas = _json(ATLAS)
    assert result["status"] == "NO_ADMITTED_DATA_PILOT"
    assert result["admitted_count"] == 0
    assert result["pilot_executed"] is False
    assert atlas["data_admission"] == {
        "status": "NO_ADMITTED_DATA_PILOT",
        "admitted_count": 0,
        "pilot_executed": False,
        "observed_data_figure_allowed": False,
    }


def test_generator_check_passes_and_is_portable_outside_repo_cwd(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(GENERATOR), "--check"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        env={**__import__("os").environ, "MPLBACKEND": "Agg", "MPLCONFIGDIR": str(tmp_path / "mpl")},
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "are current" in completed.stdout


def test_source_proof_promotion_mutation_fails_closed() -> None:
    module = _module()
    spec = module._load_yaml(SPEC)
    sources, source_hashes = module._verify_frozen_inputs(spec)
    mutated = copy.deepcopy(sources)
    mutated["theorem_signatures_v3"]["source_groups"]["legacy_signature_inventory"]["entries"][0][
        "proof_adjudication_status"
    ] = "PROVED"
    with pytest.raises(RuntimeError, match="source proof status promoted"):
        module.build_proof_atlas(spec=spec, sources=mutated, source_hashes=source_hashes)


def test_evidence_verdict_distribution_is_recomputed_not_hand_copied() -> None:
    module = _module()
    spec = module._load_yaml(SPEC)
    sources, source_hashes = module._verify_frozen_inputs(spec)
    mutated = copy.deepcopy(sources)
    old = mutated["pillar_t_core"]["records"][0]["verdict"]
    mutated["pillar_t_core"]["records"][0]["verdict"] = "INCONCLUSIVE_MUTATION_SENTINEL"
    atlas = module.build_proof_atlas(spec=spec, sources=mutated, source_hashes=source_hashes)
    counts = atlas["evidence_layers"]["pillar_t_core"]["verdict_counts"]
    assert counts["INCONCLUSIVE_MUTATION_SENTINEL"] == 1
    assert counts[old] == Counter(
        record["verdict"] for record in mutated["pillar_t_core"]["records"]
    )[old]
    assert atlas["source_obligation_registry"]["proof_adjudication_status_counts"] == {
        "NOT_ADJUDICATED": 123
    }


def test_unresolved_or_mutated_evidence_source_reference_fails_closed() -> None:
    module = _module()
    spec = module._load_yaml(SPEC)
    sources, source_hashes = module._verify_frozen_inputs(spec)
    unresolved = copy.deepcopy(sources)
    unresolved["pillar_t_cas"]["records"][0]["obligation_id"] = "VT-T999"
    with pytest.raises(RuntimeError, match="unresolved obligation"):
        module.build_proof_atlas(
            spec=spec,
            sources=unresolved,
            source_hashes=source_hashes,
        )

    promoted = copy.deepcopy(sources)
    promoted["pillar_t_cas"]["records"][0][
        "source_proof_adjudication_status"
    ] = "PROVED"
    with pytest.raises(RuntimeError, match="disagrees with source proof status"):
        module.build_proof_atlas(
            spec=spec,
            sources=promoted,
            source_hashes=source_hashes,
        )


def test_data_admission_and_synthetic_membership_mutations_fail_closed() -> None:
    module = _module()
    spec = module._load_yaml(SPEC)
    sources, source_hashes = module._verify_frozen_inputs(spec)
    admitted = copy.deepcopy(sources)
    admitted["pr274_admission_result"]["status"] = "ADMITTED_INPUTS_AWAITING_EXECUTION_AUTHORIZATION"
    admitted["pr274_admission_result"]["admitted_count"] = 1
    with pytest.raises(RuntimeError, match="data-admission boundary drifted"):
        module.build_proof_atlas(spec=spec, sources=admitted, source_hashes=source_hashes)

    pack = copy.deepcopy(sources["pr273_diagnostic_pack"])
    pack["case_results"].pop()
    with pytest.raises(RuntimeError, match="case membership/order drifted"):
        module.build_synthetic_analysis(
            spec=spec,
            pack=pack,
            pack_sha256="0" * 64,
        )


def test_strict_yaml_and_json_loaders_reject_ambiguous_authority(tmp_path: Path) -> None:
    module = _module()
    duplicate_yaml = tmp_path / "duplicate.yaml"
    duplicate_yaml.write_text("schema: attacker\nschema: canonical\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="duplicate PR-275 YAML mapping key"):
        module._load_yaml(duplicate_yaml)
    duplicate_json = tmp_path / "duplicate.json"
    duplicate_json.write_text('{"status":"attacker","status":"canonical"}\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="duplicate PR-275 JSON key"):
        module._load_json(duplicate_json)
    nonfinite_json = tmp_path / "nonfinite.json"
    nonfinite_json.write_text('{"value":NaN}\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="non-finite JSON constant"):
        module._load_json(nonfinite_json)


def test_generated_surfaces_have_no_family_or_native_result_fields() -> None:
    for path in (ATLAS, ANALYSIS, MANIFEST, REPLICATION):
        payload = _json(path)
        assert "family_id" not in payload
        assert "family_label" not in payload
        assert "native_solver_result" not in payload
        assert "geometry_result" not in payload
