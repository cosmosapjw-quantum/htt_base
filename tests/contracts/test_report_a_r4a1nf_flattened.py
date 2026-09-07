from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "research_reports" / "HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md"
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
LEDGER = BASE / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml"
MATRIX = BASE / "REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def text() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_r4a1nf_manuscript_flattens_observer_photon_and_boost_domains():
    value = text()
    required = (
        "u^a u_a=-1",
        "p^a p_a=0",
        "E_\\gamma=-c\\,p_a u^a>0",
        "p^a=\\frac{E_\\gamma}{c}(u^a+e^a)",
        "u_a e^a=0",
        "e_a e^a=1",
        "u_a\\beta_{\\rm obs}^a=0",
        "0\\leq\\beta_{\\rm obs}^2<1",
        "\\widetilde u^a\\widetilde u_a=-1",
    )
    for needle in required:
        assert needle in value


def test_r4a1nf_manuscript_flattens_numerical_error_domain():
    value = text()
    assert "with \\(r_f>0\\). Fix \\(\\lambda_{\\rm reg}>0\\)" in value
    assert "The strictly positive regularisation implies \\(\\Gamma_E\\succ0\\)" in value
    assert "\\Gamma_E^{-1/2}\\) is well defined" in value


def test_r4a1nf_manuscript_uses_self_contained_v4_authorities():
    value = text()
    ledger = load(LEDGER)
    matrix = load(MATRIX)
    ids = [claim["id"] for claim in ledger["claims"]]
    assert len(ids) == len(set(ids)) == 30
    assert matrix["canonical_claim_ledger"] == "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml"
    for claim_id in ids:
        assert claim_id in value
    assert "and define\n\n\\[\nC=" not in value


def test_r4a1nf_preserves_scope_firewalls():
    value = text()
    assert "CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE" in value
    assert "PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER" in value
    assert "FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED" in value
    assert "no finite-HEALPix no-go theorem is claimed" in value
    assert "no native BASS solver" in value
