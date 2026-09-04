from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = ROOT / "docs" / "research_reports"
ASSEMBLY = REPORT_ROOT / "report_a"
SPEC = ASSEMBLY / "R4B0_PUBLICATION_ASSEMBLY_SPEC.yaml"
INTEGRATION = ASSEMBLY / "REPORT_A_ORGANIC_INTEGRATION_MATRIX.yaml"
PANDOC = ASSEMBLY / "pandoc.yaml"
METADATA = ASSEMBLY / "metadata.yaml"
FILTER = ASSEMBLY / "structure.lua"
HEADER = ASSEMBLY / "header.tex"
README = ASSEMBLY / "README.md"
LEDGER = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
    / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml"
)
WORKFLOW = ROOT / ".github" / "workflows" / "report-a-publication.yml"


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_r4b0_preserves_one_scientific_prose_authority():
    spec = load_yaml(SPEC)
    source = spec["source_of_truth"]
    assert source["manuscript"] == (
        "docs/research_reports/HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md"
    )
    assert source["bibliography"] == "docs/research_reports/HTT_REPORT_A_REFERENCES.bib"
    assert spec["generated_outputs"]["edit_policy"] == "GENERATED_DO_NOT_EDIT"
    assert spec["generated_outputs"]["status"] == "NOT_GENERATED_IN_R4B0"
    serialized = SPEC.read_text(encoding="utf-8") + README.read_text(encoding="utf-8")
    assert "docs/manuscript/main.tex" in serialized
    assert "not an input" in serialized or "not an authority or assembly input" in serialized
    defaults = load_yaml(PANDOC)
    assert defaults["input-files"] == ["../HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md"]
    assert defaults["bibliography"] == ["../HTT_REPORT_A_REFERENCES.bib"]
    assert defaults["output-file"].startswith("build/")


def test_r4b0_integration_matrix_covers_the_canonical_claim_surface_once():
    matrix = load_yaml(INTEGRATION)
    ledger = load_yaml(LEDGER)
    expected_layers = {
        "scope_and_supersession",
        "harmonic_and_tensor_representation",
        "conditional_mes_geometry",
        "finite_null_statistics",
        "local_observer_response",
        "processed_response_and_identifiability",
        "verification_and_publication_authority",
    }
    layers = matrix["layers"]
    assert {item["id"] for item in layers} == expected_layers
    mapped = [claim for item in layers for claim in item["claim_ids"]]
    canonical = [claim["id"] for claim in ledger["claims"]]
    assert len(mapped) == len(set(mapped)) == len(canonical) == 30
    assert set(mapped) == set(canonical)
    assert matrix["central_thesis"].startswith("Tensorization preserves observable")
    excluded = set(matrix["excluded_from_current_report"])
    assert "corrected Planck or FFP10 result" in excluded
    assert "finite-HEALPix containment theorem" in excluded
    assert "native BASS solver background recombination or reionization result" in excluded


def test_r4b0_structure_filter_removes_control_plane_but_not_science():
    text = FILTER.read_text(encoding="utf-8")
    assert 'stringify(block.content) == "Abstract"' in text
    assert 'pandoc.RawBlock("latex", "\\\\appendix")' in text
    assert "strip_numeric_prefix" in text
    assert "Appendix%s+[A-Z]" in text
    assert "could not locate the level-2 Abstract heading" in text
    assert "could not locate Appendix A" in text
    assert "CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK" not in text
    assert "BASS" not in text


def test_r4b0_metadata_and_header_are_publication_only():
    metadata = load_yaml(METADATA)
    assert metadata["title"].startswith("Tensorized Low-Multipole CMB Inference")
    assert metadata["author"] == ["Jiwon Park"]
    assert metadata["lang"] == "en-GB"
    assert metadata["documentclass"] == "article"
    header = HEADER.read_text(encoding="utf-8")
    for package in ("amsmath", "mathrsfs", "booktabs", "microtype"):
        assert package in header
    assert "Bianchi" not in header
    assert "MES" not in header
    assert "Planck" not in header


def test_r4b0_toolchain_and_static_workflow_are_pinned():
    spec = load_yaml(SPEC)
    tools = spec["toolchain"]
    assert tools["pandoc"]["version"] == 3.11
    assert tools["pandoc"]["sha256"] == (
        "37edb3bbcf722f921a009941bf5874e2e0c09263226c9b4a2d980788cb062ab6"
    )
    assert tools["tectonic"]["version"] == "0.17.0"
    assert tools["tectonic"]["sha256"] == (
        "1a715688baf591e650c8aeb160ae934e181685eecbb38b317de30b269ac5d606"
    )
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "11d5960a326750d5838078e36cf38b85af677262" in workflow
    assert "a26af69be951a213d495a4c3e4e4022e16d87065" in workflow
    assert "test_report_a_r4b0_assembly.py" in workflow
    assert "tectonic" not in workflow.lower()
    assert "pandoc --defaults" not in workflow


def test_r4b0_claim_firewalls_remain_closed():
    spec = load_yaml(SPEC)
    assert spec["execution_state"]["pdf_compilation"] == "NOT_STARTED"
    assert spec["execution_state"]["page_visual_audit"] == "NOT_STARTED"
    assert spec["execution_state"]["accepted_static_execution"] is False
    text = INTEGRATION.read_text(encoding="utf-8")
    prohibited_positive_claims = (
        "corrected tensorized Planck rank is",
        "finite-HEALPix containment is proved",
        "BASS solver result",
    )
    for phrase in prohibited_positive_claims:
        assert phrase not in text
    assert re.search(r"OBSERVATIONAL_DATA_DEFERRED|observational data.*deferred", text, re.I)
