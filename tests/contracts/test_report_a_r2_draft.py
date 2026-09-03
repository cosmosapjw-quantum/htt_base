from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT / "docs/research_reports/HTT_REPORT_A_THEORY_METHODS_DRAFT_R2_20260903.md"
LEDGER = ROOT / "docs/codex_handoff/htt_tensorized_report_first_20260903/T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V2.yaml"
CITATIONS = ROOT / "docs/codex_handoff/htt_tensorized_report_first_20260903/REPORT_A_CITATION_PROVENANCE_MATRIX_V1.yaml"

EXPECTED_IDS = {
    "RA-SCOPE-001",
    "RA-REP-001", "RA-REP-002", "RA-REP-003",
    "RA-ORBIT-001", "RA-ORBIT-002", "RA-ORBIT-003", "RA-ORBIT-004",
    "RA-MES-001", "RA-MES-002", "RA-MES-003",
    "RA-STAT-001", "RA-STAT-002", "RA-STAT-003",
    "RA-RESP-001", "RA-RESP-002",
    "RA-PROC-001", "RA-PROC-002", "RA-PROC-003", "RA-PROC-004", "RA-PROC-005",
    "RA-CONT-001", "RA-CONT-002", "RA-CONT-003",
    "RA-ERR-001", "RA-ERR-002", "RA-ERR-003", "RA-ERR-004",
    "RA-BOUNDARY-001",
}


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_r2_draft_exists_and_is_explicitly_nonpublication():
    text = DRAFT.read_text(encoding="utf-8")
    assert "R2 working draft" in text
    assert "not a publication-ready manuscript" in text
    assert "CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE" in text
    assert "observational execution remains deferred" in text


def test_r2_draft_uses_canonical_surfaces_and_execution_boundaries():
    text = DRAFT.read_text(encoding="utf-8")
    assert "29-claim canonical ledger" in text
    assert "37 registered source rows" in text
    assert "36 `INCLUDED`" in text
    assert "one `DEFERRED`" in text
    assert "PR284_NEW:FINITE-REGISTERED-PATH" in text
    assert "PR #450" in text and "PRESTART_NO_EXECUTION" in text
    assert "PR #451" in text and "O:Q" in text and "e_0" in text
    assert "27 claims" not in text


def test_r2_draft_records_exact_tie_rules_and_finite_operator_boundary():
    text = DRAFT.read_text(encoding="utf-8")
    for required in (
        "ties assigned to coordinate 2", "12 rows at `p=1/2`", "12 rows at `p=3/4`",
        "ties assigned to coordinate 1", "6 rows at `p=1/2`", "18 rows at `p=3/4`",
        "maximum size violation is `1/4`", "symmetric pooled rule", "zero maximum violation",
        "finite-HEALPix rank remains unresolved", "no containment candidate",
    ):
        assert required in text


def test_every_canonical_claim_is_mapped_and_external_keys_are_registered():
    text = DRAFT.read_text(encoding="utf-8")
    ledger = load_yaml(LEDGER)
    citations = load_yaml(CITATIONS)
    ids = {claim["id"] for claim in ledger["claims"]}
    assert ids == EXPECTED_IDS
    for claim_id in ids:
        assert claim_id in text
    used = set(re.findall(r"\[@([A-Z0-9_]+)\]", text))
    assert used
    assert used <= set(citations["source_registry"])


def test_claim_firewalls_are_literal():
    text = DRAFT.read_text(encoding="utf-8")
    assert "A local observer boost is not a global matter-frame tilt." in text
    assert "No BASS native-solver claim is part of this report." in text
    assert "Continuum full row rank does not certify finite-HEALPix full row rank." in text
    forbidden = (
        "current scalar MES rank =",
        "corrected Planck tensor rank = 1",
        "finite-HEALPix containment is proved",
    )
    assert not any(item in text for item in forbidden)
