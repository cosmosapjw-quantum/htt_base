from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "research_reports" / "HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md"
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
LEDGER = BASE / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V3.yaml"
MATRIX = BASE / "REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml"
BIB = ROOT / "docs" / "research_reports" / "HTT_REPORT_A_REFERENCES.bib"
PROVENANCE = (
    ROOT
    / "docs"
    / "research_reports"
    / "appendices"
    / "HTT_REPORT_A_AUTHORITY_AND_EXECUTION_PROVENANCE.md"
)


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def report_text() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_r3_flattened_report_covers_the_canonical_30_claim_surface():
    text = report_text()
    ledger = load_yaml(LEDGER)
    claim_ids = [claim["id"] for claim in ledger["claims"]]
    assert len(claim_ids) == len(set(claim_ids)) == 30
    assert "Canonical 30-claim map" in text
    for claim_id in claim_ids:
        assert claim_id in text
    assert "29-claim canonical ledger" not in text
    assert "canonical_report_claims: 29" not in text


def test_finite_sample_theorem_lanes_are_separate_and_atomic():
    text = report_text()
    ledger = load_yaml(LEDGER)
    row_claim = next(c for c in ledger["claims"] if c["id"] == "RA-STAT-001")
    group_claim = next(c for c in ledger["claims"] if c["id"] == "RA-STAT-004")
    assert row_claim["assumptions"] == [
        "joint_exchangeability",
        "complete_row_permutation_equivariance",
        "fixed_tie_and_tail_rule",
    ]
    assert group_claim["assumptions"] == [
        "null_law_invariant_under_declared_group",
        "reference_statistics_are_actual_group_orbit",
        "identity_included",
        "exact_or_valid_conditional_monte_carlo_rule",
    ]
    assert "joint_exchangeability_or_randomization_group" not in LEDGER.read_text(
        encoding="utf-8"
    )
    assert "Exchangeable-row rank" in text
    assert "Finite transformation-group randomization" in text
    assert "12 permutations give" in text
    assert "12 rows at" not in text
    assert "p_{\\rm all}(z^{(1)})=\\frac14" in text
    assert "p_{\\mathcal G}=1/2" in text


def test_scientific_abstract_is_free_of_repository_execution_detail():
    text = report_text()
    abstract = text.split("## Abstract", 1)[1].split("## 1.", 1)[0]
    assert "PR #" not in abstract
    assert "passed" not in abstract.lower()
    assert "CI" not in abstract
    assert "runner" not in abstract.lower()
    assert "PRESTART" not in abstract
    assert "E_\\gamma" not in abstract  # notation belongs to conventions, not abstract


def test_notation_and_scope_firewalls_are_explicit():
    text = report_text()
    assert "p^a=\\frac{E_\\gamma}{c}(u^a+e^a)" in text
    assert "p^a=\\frac{\\epsilon}{c}" not in text
    assert "CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE" in text
    assert "PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER" in text
    assert "FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED" in text
    assert "no finite-HEALPix no-go theorem is claimed" in text
    assert "no native BASS solver" in text
    assert "O:Q=A_QA_O\\,\\mathscr K_{QO}e_0" in text


def test_formal_bibliography_and_provenance_are_single_authorities():
    text = report_text()
    matrix = load_yaml(MATRIX)
    assert BIB.exists()
    assert PROVENANCE.exists()
    assert matrix["formal_bibliography"] == "docs/research_reports/HTT_REPORT_A_REFERENCES.bib"
    assert "# Appendix D. Bibliography authority" in text
    assert "# Appendix D. References and declared roles" not in text
    assert "HTT_REPORT_A_REFERENCES.bib" in text
    assert "HTT_REPORT_A_AUTHORITY_AND_EXECUTION_PROVENANCE.md" in text
    assert "No manual reference list is a competing authority." in text


def test_all_registered_citation_keys_are_used_and_no_unknown_key_appears():
    text = report_text()
    matrix = load_yaml(MATRIX)
    registered = set(matrix["source_registry"])
    used = set()
    marker = "[@"
    start = 0
    while True:
        index = text.find(marker, start)
        if index < 0:
            break
        end = text.find("]", index)
        assert end >= 0
        used.add(text[index + len(marker) : end])
        start = end + 1
    assert used == registered


def test_continuum_discrete_and_execution_grades_remain_separate():
    text = report_text()
    assert "The five non-axial results are multi-engine numerical evidence" in text
    assert "Continuum full row rank does not certify finite-HEALPix full row rank" in text
    assert "finite Task-7C matched control        IMPLEMENTATION_VERIFIED; RANK_UNRESOLVED" in text
    assert "finite-HEALPix robust containment     UNRESOLVED" in text
