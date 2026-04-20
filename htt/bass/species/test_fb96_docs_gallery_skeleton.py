from __future__ import annotations

from pathlib import Path

import pytest


_TOPIC_DIR = Path(__file__).resolve().parents[3] / "figures" / "physics_gallery" / "15_massive_neutrino"
_SPEC_DOC = Path(__file__).resolve().parents[3] / "docs" / "lowell_bianchi" / "01_species_background_spec.md"
_CH11 = Path(__file__).resolve().parents[3] / "docs" / "manuscript" / "ch11_error_hierarchy.tex"
_CH08 = Path(__file__).resolve().parents[3] / "docs" / "manuscript" / "ch08_robustness.tex"
_CH01 = Path(__file__).resolve().parents[3] / "docs" / "manuscript" / "ch01_introduction.tex"


def test_fb96_required_docs_exist() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    assert (repo_root / "docs/lowell_bianchi/01_species_background_spec.md").exists()
    assert (_TOPIC_DIR / "README.md").exists()


@pytest.mark.parametrize(
    "filename",
    [
        "01_w_of_a_sweep.png",
        "02_rho_p_NR_transition.png",
        "03_kfs_vs_a.png",
        "04_dPk_over_Pk.png",
    ],
)
def test_fb96_gallery_pngs_are_rendered(filename: str) -> None:
    assert (_TOPIC_DIR / filename).exists()


def test_fb96_species_spec_mentions_massive_neutrino_contract() -> None:
    text = _SPEC_DOC.read_text(encoding="utf-8")
    assert "Massive neutrino" in text
    assert "phase_space_grid" in text
    assert "w(a)" in text


def test_fb96_ch11_contains_massive_neutrino_section() -> None:
    text = _CH11.read_text(encoding="utf-8")
    assert "Massive neutrino as a systematic" in text


def test_fb96_ch08_cross_references_massive_neutrino_systematic() -> None:
    text = _CH08.read_text(encoding="utf-8")
    assert "Massive neutrino" in text


def test_fb96_ch01_introduction_points_forward() -> None:
    text = _CH01.read_text(encoding="utf-8")
    assert "massive neutrino" in text.lower()
