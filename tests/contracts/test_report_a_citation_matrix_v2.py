from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
)
LEDGER = BASE / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V3.yaml"
MATRIX = BASE / "REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml"
BIB = ROOT / "docs" / "research_reports" / "HTT_REPORT_A_REFERENCES.bib"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_citation_matrix_covers_every_canonical_claim_once():
    ledger = load(LEDGER)
    matrix = load(MATRIX)
    claim_ids = [claim["id"] for claim in ledger["claims"]]
    mapped_ids = list(matrix["claim_citations"])
    assert len(claim_ids) == len(set(claim_ids)) == 30
    assert len(mapped_ids) == len(set(mapped_ids)) == 30
    assert set(mapped_ids) == set(claim_ids)
    assert matrix["coverage"]["claim_rows"] == 30
    assert matrix["coverage"]["claim_rows_with_internal_authority"] == 30
    assert matrix["formal_bibliography"] == (
        "docs/research_reports/HTT_REPORT_A_REFERENCES.bib"
    )


def test_finite_sample_claims_have_distinct_citation_roles():
    matrix = load(MATRIX)
    exchangeable = matrix["claim_citations"]["RA-STAT-001"]
    orbit = matrix["claim_citations"]["RA-STAT-004"]
    assert exchangeable["citation_role"] == (
        "EXCHANGEABLE_ROW_FINITE_RANK_WITH_PROJECT_EQUIVARIANT_PROOF"
    )
    assert orbit["citation_role"] == (
        "FINITE_GROUP_ORBIT_RANDOMIZATION_THEOREM_AND_SUBGROUP_BOUNDARY"
    )
    assert "R3_SUBGROUP_COUNTEREXAMPLE_RECEIPT" in orbit["internal_authority"]
    assert "RANDOMIZATION_2024" in orbit["external_sources"]


def test_external_source_roles_do_not_promote_adjacent_literature():
    matrix = load(MATRIX)
    orbit = matrix["claim_citations"]["RA-ORBIT-002"]
    assert orbit["direct_match_found"] is False
    assert orbit["novelty_status"] == "UNRESOLVED"
    assert matrix["coverage"]["novelty_decisions_made"] == 0
    for source_id in orbit["external_sources"]:
        assert matrix["source_registry"][source_id]["role"].startswith("ADJACENT_")


def test_primary_source_identifiers_and_corrected_metadata_are_present():
    matrix = load(MATRIX)
    sources = matrix["source_registry"]
    assert sources["MES_1995_LIMITS"]["doi"] == "10.1103/PhysRevD.51.1525"
    assert sources["MES_1995_LIMITS"]["journal"].endswith("1525-1535")
    assert sources["MES_1995_IMPROVED"]["journal"].endswith("5942-5945")
    assert sources["MASTER_2002"]["doi"] == "10.1086/338126"
    assert sources["LEUNG_2022"]["journal"].endswith("928(2), 109")
    assert sources["CAI_ZHANG_2018"]["journal"].endswith("46(1), 60-89")
    assert sources["RANDOMIZATION_2024"]["arxiv"] == "2406.09521"
    assert matrix["coverage"]["observational_sources_used_as_results"] == 0


def test_formal_bibliography_is_the_single_rendered_authority():
    matrix = load(MATRIX)
    assert matrix["citation_rules"][6] == (
        "The formal BibTeX file is the sole rendered bibliography authority; "
        "manual reference lists are noncanonical history."
    )
    bib = BIB.read_text(encoding="utf-8")
    assert bib.count("@") == 17
    assert "10.1086/338126" in bib
    assert "1525--1535" in bib
    assert "5942--5945" in bib
    assert "60--89" in bib


def test_continuum_discrete_and_execution_grades_remain_separate():
    matrix = load(MATRIX)
    continuum = matrix["claim_citations"]["RA-CONT-002"]
    finite = matrix["claim_citations"]["RA-PROC-005"]
    assert continuum["citation_role"] == "MULTI_ENGINE_NUMERICAL_RESULT"
    assert finite["citation_role"] == (
        "REGISTERED_UNRESOLVED_RESULT_AND_RANK_BOUNDARY"
    )
    assert matrix["citation_rules"][3] == (
        "A source-only implementation is never cited as an executed validation."
    )
    assert matrix["citation_rules"][4] == (
        "Continuum and finite-HEALPix claims receive separate citations and labels."
    )
