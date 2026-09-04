from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
LEDGER = BASE / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml"
MATRIX = BASE / "REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_r4a1nf_citation_matrix_binds_t9_v4_and_covers_every_claim_once():
    ledger = load(LEDGER)
    matrix = load(MATRIX)
    claim_ids = [claim["id"] for claim in ledger["claims"]]
    mapped_ids = list(matrix["claim_citations"])
    assert matrix["schema"] == "htt.report_a.citation_provenance_matrix.v2"
    assert matrix["revision"] == "R4A1NF_T9_V4_BINDING"
    assert matrix["canonical_claim_ledger"] == (
        "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml"
    )
    assert len(claim_ids) == len(set(claim_ids)) == 30
    assert len(mapped_ids) == len(set(mapped_ids)) == 30
    assert set(mapped_ids) == set(claim_ids)
    assert matrix["coverage"]["claim_rows"] == 30
    assert matrix["coverage"]["claim_rows_with_internal_authority"] == 30


def test_r4a1nf_citation_matrix_flattens_notation_v3_authorities():
    matrix = load(MATRIX)
    rep = matrix["claim_citations"]["RA-REP-002"]
    response = matrix["claim_citations"]["RA-RESP-001"]
    error = matrix["claim_citations"]["RA-ERR-001"]
    for item in (rep, response, error):
        assert "NOTATION_AND_CONVENTION_REGISTRY_v3" in item["internal_authority"]


def test_r4a1nf_citation_matrix_preserves_source_and_novelty_boundaries():
    matrix = load(MATRIX)
    orbit = matrix["claim_citations"]["RA-ORBIT-002"]
    assert orbit["direct_match_found"] is False
    assert orbit["novelty_status"] == "UNRESOLVED"
    assert matrix["coverage"]["novelty_decisions_made"] == 0
    assert matrix["coverage"]["observational_sources_used_as_results"] == 0
    assert matrix["coverage"]["formal_bibliography_keys"] == 17
