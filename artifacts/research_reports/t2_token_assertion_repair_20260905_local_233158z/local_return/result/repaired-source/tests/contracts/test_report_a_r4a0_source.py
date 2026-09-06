from __future__ import annotations

import re
from pathlib import Path

import pytest

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


_CHOLESKY_SENTENCE = (
    r"Let \(B_+\) be the unique upper-triangular Cholesky factor "
    "with positive diagonal"
)
_SIGNED_DIAGONAL = (
    r"S_\chi=\operatorname{diag}\!\left(1,1,\operatorname{sgn}\chi\right)"
)
_T2_FORMULAS = (
    "\\bar Q^3\n =\\frac{s_2}{2}\\bar Q+\\frac{s_3}{3}I.",
    r"\mu_3=\frac{s_2}{2}\mu_1+\frac{s_3}{3}\mu_0",
    r"\mu_4=\frac{s_2}{2}\mu_2+\frac{s_3}{3}\mu_1",
)
_DENIAL = "no finite-HEALPix no-go theorem is claimed"


def _assert_raw_controls_absent(text: str) -> None:
    forbidden = [
        (offset, ord(char))
        for offset, char in enumerate(text)
        if (ord(char) < 32 and char not in "\t\n\r") or ord(char) == 127
    ]
    assert not forbidden, f"forbidden raw control characters: {forbidden}"


def _ascii_layout(text: str) -> str:
    # Check raw bytes' decoded characters before permitting ASCII wrapping.
    _assert_raw_controls_absent(text)
    return re.sub(r"[ \t\n\r]+", " ", text)


def _assert_canonical_section(text: str) -> None:
    layout = _ascii_layout(text)
    assert "The two equations \\(B^TB=G\\) and \\(\\det B=\\chi\\) alone do not select a" in text
    assert _CHOLESKY_SENTENCE in layout, "canonical Cholesky sentence missing"
    assert "B_+^TB_+=G" in text
    assert "\\det B_+=|\\chi|" in text
    assert "S_\\chi=\\operatorname{diag}" in text
    assert "\\operatorname{sgn}\\chi" in text
    assert _SIGNED_DIAGONAL in text, "signed diagonal orientation changed"
    assert "B=S_\\chi B_+" in text
    assert "S_\\chi^TS_\\chi=I" in text
    assert "Choose \\(B\\) with" not in text


def _assert_t2_formulas(text: str) -> None:
    _assert_raw_controls_absent(text)
    assert "\nrac{" not in text, "truncated fraction token"
    for formula in _T2_FORMULAS:
        assert formula in text, f"missing Cayley-Hamilton/moment formula: {formula}"


def _assert_scope_firewalls(text: str) -> None:
    layout = _ascii_layout(text)
    assert "CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE" in text
    assert "PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER" in text
    assert "FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED" in text
    assert any(
        sentence in layout
        for sentence in (_DENIAL, _DENIAL.replace("HEALPix", "HEALPIX"))
    ), "finite-HEALPix negative scope sentence missing"
    assert "no native BASS solver" in text


def test_canonical_krylov_frame_has_a_deterministic_so3_section():
    _assert_canonical_section(report_text())


def test_t2_cayley_hamilton_source_has_no_truncated_fraction_tokens():
    _assert_t2_formulas(theorem_text())


def test_r4a0_repair_preserves_report_scope_firewalls():
    _assert_scope_firewalls(report_text())


def _mutate_once(original: str, needle: str, replacement: str) -> str:
    assert original.count(needle) == 1, "mutation must target one existing passage"
    mutated = original.replace(needle, replacement, 1)
    assert mutated != original, "negative fixture must change the source"
    return mutated


@pytest.mark.parametrize(
    "wrapping", [" ", "\n", "\t", "\r", " \t\r\n"],
    ids=["pinned-one-line", "LF", "TAB", "CR", "mixed-ASCII"],
)
def test_canonical_section_accepts_ascii_wrapping(wrapping):
    original = report_text()
    assert original.count(_CHOLESKY_SENTENCE) == 1
    varied = original.replace(_CHOLESKY_SENTENCE, _CHOLESKY_SENTENCE.replace(" ", wrapping), 1)
    _assert_canonical_section(varied)


@pytest.mark.parametrize("spelling", ["HEALPix", "HEALPIX"])
def test_scope_accepts_only_the_two_declared_positive_spellings(spelling):
    original = report_text()
    assert original.count(_DENIAL) == 1
    _assert_scope_firewalls(original.replace(_DENIAL, _DENIAL.replace("HEALPix", spelling), 1))


@pytest.mark.parametrize("formula_index", range(3), ids=["Q-cubic", "mu3", "mu4"])
def test_t2_rejects_each_form_feed_fraction(formula_index):
    original = theorem_text()
    formula = _T2_FORMULAS[formula_index]
    damaged = formula.replace(r"\frac{s_3}{3}", "\x0crac{s_3}{3}", 1)
    mutated = _mutate_once(original, formula, damaged)
    with pytest.raises(AssertionError, match="forbidden raw control characters"):
        _assert_t2_formulas(mutated)


def test_t2_rejects_an_actually_truncated_fraction_token():
    formula = _T2_FORMULAS[0]
    damaged = formula.replace(r"\frac{s_3}{3}", "\nrac{s_3}{3}", 1)
    mutated = _mutate_once(theorem_text(), formula, damaged)
    with pytest.raises(AssertionError, match="truncated fraction token"):
        _assert_t2_formulas(mutated)


@pytest.mark.parametrize(
    "formula_index,needle,replacement",
    [(0, r"\frac{s_3}{3}", r"\frac{s_3}{4}"),
     (1, r"\mu_0", r"\mu_2"),
     (2, r"\frac{s_2}{2}", r"\frac{s_2}{3}")],
    ids=["Q-coefficient", "mu3-moment-index", "mu4-coefficient"],
)
def test_t2_rejects_formula_semantic_mutations(formula_index, needle, replacement):
    formula = _T2_FORMULAS[formula_index]
    mutated = _mutate_once(theorem_text(), formula, formula.replace(needle, replacement, 1))
    with pytest.raises(AssertionError, match="missing Cayley-Hamilton/moment formula"):
        _assert_t2_formulas(mutated)


@pytest.mark.parametrize(
    "needle,replacement",
    [("unique upper-triangular", "upper-triangular"),
     (_CHOLESKY_SENTENCE, _CHOLESKY_SENTENCE.replace(" with positive diagonal", "")),
     (_SIGNED_DIAGONAL, _SIGNED_DIAGONAL.replace(r"\operatorname{sgn}", r"-\operatorname{sgn}")),
     (r"B=S_\chi B_+", r"B=B_+ S_\chi"),
     (r"B_+^TB_+=G", r"B_+B_+^T=G"),
     (_CHOLESKY_SENTENCE, _CHOLESKY_SENTENCE + r" Choose \(B\) with")],
    ids=["no-uniqueness", "no-positive-diagonal", "wrong-orientation-sign",
         "wrong-factor-order", "wrong-transpose", "nonunique-choice"],
)
def test_canonical_section_rejects_semantic_mutations(needle, replacement):
    mutated = _mutate_once(report_text(), needle, replacement)
    with pytest.raises(AssertionError):
        _assert_canonical_section(mutated)


@pytest.mark.parametrize(
    "needle,replacement",
    [(_DENIAL, ""),
     (_DENIAL, "a finite-HEALPix no-go theorem is claimed"),
     (_DENIAL, _DENIAL.replace("HEALPix", "HEALpix")),
     ("FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED", "FINITE_HEALPIX_CONTAINMENT = RESOLVED"),
     ("no native BASS solver", "native BASS solver")],
    ids=["missing-denial", "reversed-denial", "unapproved-spelling",
         "changed-boundary", "missing-native-BASS-denial"],
)
def test_scope_rejects_semantic_mutations(needle, replacement):
    mutated = _mutate_once(report_text(), needle, replacement)
    with pytest.raises(AssertionError):
        _assert_scope_firewalls(mutated)


@pytest.mark.parametrize(
    "checker,reader",
    [(_assert_canonical_section, report_text), (_assert_t2_formulas, theorem_text),
     (_assert_scope_firewalls, report_text)],
    ids=["canonical-section", "T2-formulas", "scope"],
)
@pytest.mark.parametrize(
    "control", ["\x00", "\x0b", "\x0c", "\x1f", "\x7f"],
    ids=["NUL", "VT", "FF", "US", "DEL"],
)
def test_checked_text_rejects_forbidden_controls(checker, reader, control):
    original = reader()
    mutated = original + control
    assert mutated != original
    with pytest.raises(AssertionError, match="forbidden raw control characters"):
        checker(mutated)
