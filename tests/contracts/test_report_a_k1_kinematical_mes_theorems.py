from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
EVIDENCE = BASE / "K1_TYPED_KINEMATICAL_MES_EVIDENCE_LEDGER.yaml"
K2_INPUT = BASE / "K2_KINEMATICAL_CLAIM_RECOMPILE_INPUT.yaml"
PACK = ROOT / "docs" / "research_reports" / "theory_packs" / "K1_TYPED_KINEMATICAL_MES_THEOREM_PACK.md"


def _yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_all_k1_theorems_are_supported_without_claim_promotion() -> None:
    data = _yaml(EVIDENCE)
    rows = data["results"]
    assert len(rows) == 10
    assert {row["id"] for row in rows} == {
        "K1-T1-STATE-PARTITION",
        "K1-T2-ANCHOR-SEPARATION",
        "K1-T3-RADIAL-ONLY",
        "K1-T4-PRODUCT-GAUGE",
        "K1-T5-CHANNEL-MATCH",
        "K1-T6-NO-ANCHOR",
        "K1-T7-RESPONSE-IDENTIFIED-SET",
        "K1-T8-BETA-BOUNDARY",
        "K1-T9-PHYSICAL-MORPHOLOGY",
        "K1-T10-SCALAR-INHERITANCE",
    }
    assert all(row["disposition"] == "INCLUDE_CORE" for row in rows)
    assert data["claim_projection"]["no_claim_promotion_in_K1"] is True
    assert data["claim_projection"]["canonical_claims_after_K1"] == 30


def test_anchor_inventory_and_response_boundary_are_explicit() -> None:
    data = _yaml(EVIDENCE)
    rows = {row["id"]: row for row in data["results"]}
    no_anchor = rows["K1-T6-NO-ANCHOR"]
    assert no_anchor["active_numeric_anchors"] == ["MES_G_SIGMA", "MES_G_OMEGA"]
    assert "MES_G_ACCEL" in no_anchor["typed_no_anchor"]
    beta = rows["K1-T8-BETA-BOUNDARY"]
    assert beta["closed"] == ["beta_RO local observer response"]
    assert "global matter tilt" in beta["unresolved"]


def test_k2_projection_normalises_ten_candidates_to_seven_additions() -> None:
    data = _yaml(K2_INPUT)
    norm = data["normalisation_of_K0_candidates"]
    assert norm["provisional_candidates"] == 10
    assert norm["proposed_new_atomic_claims"] == 7
    assert norm["proposed_existing_claim_revisions"] == 3
    assert norm["candidate_total_after_recompile"] == 37
    assert norm["final_count_status"] == "PROVISIONAL_UNTIL_K2_VALIDATION"
    additions = data["proposed_new_claims"]
    revisions = data["proposed_existing_claim_revisions"]
    assert len({row["id"] for row in additions}) == 7
    assert {row["id"] for row in revisions} == {"RA-MES-002", "RA-MES-003", "RA-RESP-001"}


def test_theorem_pack_preserves_scientific_firewalls() -> None:
    text = PACK.read_text(encoding="utf-8")
    required = (
        "An anchor body is not a physical-state estimate",
        "The MES body alone supplies no map",
        "NO_MES_ANCHOR",
        "point attribution remains withheld",
        "no finite-HEALPix no-go theorem",
        "no native BASS result",
    )
    for needle in required:
        assert needle in text
    assert "PASS_K1_TYPED_KINEMATICAL_MES_THEOREM_PACK_SOURCE" in text
