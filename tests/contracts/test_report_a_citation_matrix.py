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
LEDGER = BASE / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V2.yaml"
MATRIX = BASE / "REPORT_A_CITATION_PROVENANCE_MATRIX_V1.yaml"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_citation_matrix_covers_every_canonical_claim_once():
    ledger = load(LEDGER)
    matrix = load(MATRIX)
    claim_ids = [claim["id"] for claim in ledger["claims"]]
    mapped_ids = list(matrix["claim_citations"])
    assert len(claim_ids) == len(set(claim_ids)) == 29
    assert len(mapped_ids) == len(set(mapped_ids)) == 29
    assert set(mapped_ids) == set(claim_ids)
    assert matrix["coverage"]["claim_rows"] == 29
    assert matrix["coverage"]["claim_rows_with_internal_authority"] == 29


def test_external_source_roles_do_not_promote_adjacent_literature():
    matrix = load(MATRIX)
    orbit = matrix["claim_citations"]["RA-ORBIT-002"]
    assert orbit["direct_match_found"] is False
    assert orbit["novelty_status"] == "UNRESOLVED"
    assert matrix["coverage"]["novelty_decisions_made"] == 0
    for source_id in orbit["external_sources"]:
        assert matrix["source_registry"][source_id]["role"].startswith("ADJACENT_")


def test_primary_source_identifiers_and_scope_boundaries_are_present():
    matrix = load(MATRIX)
    sources = matrix["source_registry"]
    assert sources["MES_1995_LIMITS"]["doi"] == "10.1103/PhysRevD.51.1525"
    assert sources["DAI_CHLUBA_2014"]["arxiv"] == "1403.6117"
    assert sources["YASINI_PIERPAOLI_2017"]["arxiv"] == "1709.08298"
    assert sources["RANDOMIZATION_2024"]["arxiv"] == "2406.09521"
    assert sources["CAI_ZHANG_2018"]["arxiv"] == "1605.00353"
    assert matrix["coverage"]["observational_sources_used_as_results"] == 0


def test_continuum_discrete_and_execution_grades_remain_separate():
    matrix = load(MATRIX)
    continuum = matrix["claim_citations"]["RA-CONT-002"]
    finite = matrix["claim_citations"]["RA-PROC-005"]
    assert continuum["citation_role"] == "MULTI_ENGINE_NUMERICAL_RESULT"
    assert finite["citation_role"] == "REGISTERED_UNRESOLVED_RESULT_AND_RANK_BOUNDARY"
    assert matrix["citation_rules"][3] == (
        "A source-only implementation is never cited as an executed validation."
    )
    assert matrix["citation_rules"][4] == (
        "Continuum and finite-HEALPix claims receive separate citations and labels."
    )
