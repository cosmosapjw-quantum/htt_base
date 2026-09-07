from __future__ import annotations

import csv
from pathlib import Path
import re

import pytest
import yaml

from scripts.compile_report_a_k2f_authority import (
    CompilationError,
    compile_authority_bundle,
    compile_claim_ledger,
    merge_bibliographies,
)


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
REPORT = ROOT / "docs" / "research_reports"
REPORT_A = REPORT / "report_a"


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def test_claim_compiler_applies_revisions_and_additions_without_mutating_inputs(
    tmp_path: Path,
) -> None:
    base = {
        "schema": "base.v1",
        "claims": [
            {
                "id": "A",
                "statement": "old A",
                "truth_status": "DERIVED_EXACT",
                "implementation_status": "NOT_APPLICABLE",
                "report_role": "CORE_THEOREM",
                "authority": ["a0"],
                "forbidden_extensions": ["f0"],
            },
            {
                "id": "B",
                "statement": "B",
                "truth_status": "ESTABLISHED",
                "implementation_status": "NOT_APPLICABLE",
                "report_role": "EVIDENCE_BOUNDARY",
                "authority": ["b0"],
            },
        ],
        "coverage": {"claim_count": 2},
    }
    overlay = {
        "base_claim_ids": ["A", "B"],
        "additions": [
            {
                "id": "C",
                "statement": "C",
                "truth_status": "DERIVED_CONDITIONAL",
                "implementation_status": "SOURCE_SUPPORTED",
                "report_role": "CORE_THEOREM",
                "authority": ["c0"],
                "assumptions": ["c_assumption"],
                "forbidden_extensions": ["c_forbidden"],
            }
        ],
        "revisions": [
            {
                "id": "A",
                "replacement_statement": "new A",
                "add_authority": ["a1"],
                "add_forbidden_extensions": ["f1"],
            }
        ],
        "candidate_claim_ids": ["A", "B", "C"],
        "coverage": {
            "candidate_claim_count": 3,
            "observational_claim_count": 0,
            "corrected_planck_rank_claim_count": 0,
            "finite_healpix_no_go_claim_count": 0,
            "native_bass_claim_count": 0,
        },
    }

    compiled = compile_claim_ledger(base, overlay)
    rows = {row["id"]: row for row in compiled["claims"]}
    assert list(rows) == ["A", "B", "C"]
    assert rows["A"]["statement"] == "new A"
    assert rows["A"]["superseded_statement"] == "old A"
    assert rows["A"]["authority"] == ["a0", "a1"]
    assert rows["A"]["forbidden_extensions"] == ["f0", "f1"]
    assert rows["C"]["assumptions"] == ["c_assumption"]
    assert compiled["coverage"]["claim_count"] == 3
    assert compiled["coverage"]["canonical_sorted_id_sha256"]
    assert base["claims"][0]["statement"] == "old A"


def test_bibliography_merge_rejects_duplicate_keys() -> None:
    with pytest.raises(CompilationError, match="duplicate bibliography key"):
        merge_bibliographies(
            "@article{A,\n  title={one}\n}\n",
            "@book{A,\n  title={two}\n}\n",
        )


def test_exact_repository_inputs_compile_to_one_forty_claim_authority_bundle(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "out"
    receipt = compile_authority_bundle(
        repository_root=ROOT,
        output_root=output_root,
        enforce_registered_input_blobs=True,
    )

    ledger_path = output_root / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V5.yaml"
    citations_path = output_root / "REPORT_A_CITATION_PROVENANCE_MATRIX_V3.yaml"
    section_path = output_root / "REPORT_SECTION_CLAIM_MAP_V3.csv"
    integration_path = output_root / "REPORT_A_ORGANIC_INTEGRATION_MATRIX_V3.yaml"
    bibliography_path = output_root / "HTT_REPORT_A_REFERENCES_V2.bib"

    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    citations = yaml.safe_load(citations_path.read_text(encoding="utf-8"))
    integration = yaml.safe_load(integration_path.read_text(encoding="utf-8"))
    with section_path.open(encoding="utf-8", newline="") as handle:
        section_rows = list(csv.DictReader(handle))
    bib_keys = re.findall(
        r"^@[A-Za-z]+\{([^,]+),",
        bibliography_path.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )

    claim_ids = [row["id"] for row in ledger["claims"]]
    citation_ids = [row["claim_id"] for row in citations["claim_citations"]]
    section_ids = [row["claim_id"] for row in section_rows]
    integration_ids = [
        claim_id
        for layer in integration["layers"]
        for claim_id in layer["claim_ids"]
    ]

    assert len(claim_ids) == len(set(claim_ids)) == 40
    assert set(citation_ids) == set(section_ids) == set(integration_ids) == set(claim_ids)
    assert len(citation_ids) == len(section_ids) == len(integration_ids) == 40
    assert len(bib_keys) == len(set(bib_keys)) == 20
    assert ledger["coverage"] == {
        "claim_count": 40,
        "canonical_sorted_id_sha256": receipt["canonical_sorted_id_sha256"],
        "observational_claim_count": 0,
        "corrected_planck_rank_claim_count": 0,
        "finite_healpix_no_go_claim_count": 0,
        "bianchi_family_claim_count": 0,
        "native_bass_claim_count": 0,
        "all_claims_have_authority": True,
        "all_conditional_claims_have_assumptions_or_boundary": True,
        "all_numerical_claims_have_execution_grade": True,
        "all_source_only_claims_are_not_labelled_implementation_verified": True,
    }
    assert receipt["claim_count"] == 40
    assert receipt["citation_rows"] == 40
    assert receipt["section_rows"] == 40
    assert receipt["integration_rows"] == 40
    assert receipt["bibliography_keys"] == 20
    assert receipt["observational_data_used"] is False
    assert receipt["claim_promotion"] is False
    assert receipt["terminal"] == "K2F_COMPILED_AUTHORITY_BUNDLE_SOURCE_VALIDATED_NO_CLAIM_PROMOTION"

    row_by_id = {row["id"]: row for row in ledger["claims"]}
    assert "data-derived MES ceiling construction" in row_by_id["RA-STAT-002"]["statement"]
    assert "radiation-observer" in row_by_id["RA-RESP-001"]["statement"]
    assert row_by_id["RA-ID-001"]["assumptions"]
    assert row_by_id["RA-MESA-003"]["forbidden_extensions"]


def test_registered_input_blob_mutation_fails_closed(tmp_path: Path) -> None:
    mirror = tmp_path / "repo"
    for relative in (
        BASE / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml",
        BASE / "K2_40_CLAIM_CANDIDATE_OVERLAY.yaml",
        BASE / "REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml",
        BASE / "K2_CITATION_PROVENANCE_CANDIDATE_OVERLAY.yaml",
        BASE / "REPORT_SECTION_CLAIM_MAP_V2_CANDIDATE.csv",
        REPORT_A / "REPORT_A_ORGANIC_INTEGRATION_MATRIX_V2_CANDIDATE.yaml",
        REPORT / "HTT_REPORT_A_REFERENCES.bib",
        REPORT_A / "K2_BIBLIOGRAPHY_SUPPLEMENT_CANDIDATE.bib",
    ):
        target = mirror / relative.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(relative.read_bytes())
    target = mirror / BASE.relative_to(ROOT) / "K2_40_CLAIM_CANDIDATE_OVERLAY.yaml"
    target.write_text(target.read_text(encoding="utf-8") + "# mutation\n", encoding="utf-8")

    with pytest.raises(CompilationError, match="Git blob mismatch"):
        compile_authority_bundle(
            repository_root=mirror,
            output_root=tmp_path / "bad-out",
            enforce_registered_input_blobs=True,
        )
