from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = (
    ROOT
    / "docs"
    / "research_reports"
    / "HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md"
)
THEOREM_PACK = (
    ROOT
    / "docs"
    / "research_reports"
    / "theory_packs"
    / "T2_QO_ORBIT_RECONSTRUCTION_THEOREM_PACK.md"
)


def report_text() -> str:
    return REPORT.read_text(encoding="utf-8")


def theorem_text() -> str:
    return THEOREM_PACK.read_text(encoding="utf-8")


def test_canonical_krylov_frame_has_a_deterministic_so3_section():
    text = report_text()
    assert "The two equations \\(B^TB=G\\) and \\(\\det B=\\chi\\) alone do not select a" in text
    assert "Let\n\\(B_+\\) be the unique upper-triangular Cholesky factor with positive diagonal" in text
    assert "B_+^TB_+=G" in text
    assert "\\det B_+=|\\chi|" in text
    assert "S_\\chi=\\operatorname{diag}" in text
    assert "\\operatorname{sgn}\\chi" in text
    assert "B=S_\\chi B_+" in text
    assert "S_\\chi^TS_\\chi=I" in text
    assert "Choose \\(B\\) with" not in text


def test_t2_cayley_hamilton_source_has_no_truncated_fraction_tokens():
    text = theorem_text()
    assert "\nrac{" not in text
    assert "\\bar Q^3\n =\\frac{s_2}{2}\\bar Q+\\frac{s_3}{3}I." in text
    assert "\\mu_3=\\frac{s_2}{2}\\mu_1+\\frac{s_3}{3}\\mu_0" in text
    assert "\\mu_4=\\frac{s_2}{2}\\mu_2+\\frac{s_3}{3}\\mu_1" in text


def test_r4a0_repair_preserves_report_scope_firewalls():
    text = report_text()
    assert "CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE" in text
    assert "PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER" in text
    assert "FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED" in text
    assert "no finite-HEALPIX no-go theorem is claimed" in text
    assert "no native BASS solver" in text
