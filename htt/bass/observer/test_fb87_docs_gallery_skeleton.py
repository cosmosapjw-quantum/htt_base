from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = REPO_ROOT / "figures" / "physics_gallery" / "14_observer_frame"
TOPIC_README = TOPIC_DIR / "README.md"
ROOT_GALLERY_README = REPO_ROOT / "figures" / "physics_gallery" / "README.md"
GALLERY_SCRIPT = REPO_ROOT / "scripts" / "make_physics_gallery.py"
CONVENTIONS = REPO_ROOT / "docs" / "lowell_bianchi" / "00_conventions.md"
CH02 = REPO_ROOT / "docs" / "manuscript" / "ch02_dipole_anomaly.tex"
CH09 = REPO_ROOT / "docs" / "manuscript" / "ch09_discussion.tex"
REFERENCES = REPO_ROOT / "docs" / "manuscript" / "references.bib"

EXPECTED_PNGS = (
    "01_kernel_heatmap_1p23e-3.png",
    "02_Cl_ratio_before_after.png",
    "03_alm_mixing_demo.png",
    "04_discriminator_coverage.png",
)
EXPECTED_PLOTTERS = (
    "plot_14_01_kernel_heatmap_1p23e_3",
    "plot_14_02_cl_ratio_before_after",
    "plot_14_03_alm_mixing_demo",
    "plot_14_04_discriminator_coverage",
)
EXPECTED_SUBSECTIONS = (
    r"\subsection{Linear aberration kernel}",
    r"\subsection{Observer-frame $C_\ell$ and $a_{\ell m}$ adapters}",
    r"\subsection{Composition order and non-commutation}",
    r"\subsection{Likelihood-ratio discriminator and coverage}",
)
EXPECTED_REFERENCES = (
    "ChallinorVanLeeuwen2002",
    "Planck2013XXVII",
    "KosowskyKahniashvili2011",
)


@pytest.mark.parametrize("name", EXPECTED_PNGS)
def test_fb87_gallery_png_exists_and_is_nonempty(name: str) -> None:
    path = TOPIC_DIR / name
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize("name", EXPECTED_PNGS)
def test_fb87_topic_readme_mentions_each_png(name: str) -> None:
    text = TOPIC_README.read_text(encoding="utf-8")
    assert "placeholder" not in text.lower()
    assert name in text


@pytest.mark.parametrize("name", EXPECTED_PNGS)
def test_fb87_root_gallery_readme_indexes_each_png(name: str) -> None:
    text = ROOT_GALLERY_README.read_text(encoding="utf-8")
    assert "## 14 · Observer frame (FB-8)" in text
    assert name in text


@pytest.mark.parametrize("plotter_name", EXPECTED_PLOTTERS)
def test_fb87_gallery_script_exports_each_plotter(plotter_name: str) -> None:
    text = GALLERY_SCRIPT.read_text(encoding="utf-8")
    assert plotter_name in text


def test_fb87_gallery_script_dispatch_includes_topic_14() -> None:
    text = GALLERY_SCRIPT.read_text(encoding="utf-8")
    assert 'TOPIC_14 = "14_observer_frame"' in text
    assert "TOPIC_14: [" in text


def test_fb87_conventions_section_is_populated() -> None:
    text = CONVENTIONS.read_text(encoding="utf-8")
    assert "## 13. Observer-frame layering (FB-8)" in text
    assert "cosmo-tilt -> observer-boost" in text
    assert "ObserverBoost" in text
    assert "placeholder" not in text.split("## 13. Observer-frame layering (FB-8)", 1)[1][:800].lower()


@pytest.mark.parametrize("subsection", EXPECTED_SUBSECTIONS)
def test_fb87_ch02_contains_all_observer_frame_subsections(subsection: str) -> None:
    text = CH02.read_text(encoding="utf-8")
    assert subsection in text


def test_fb87_ch02_contains_observer_frame_section_and_coverage_figure() -> None:
    text = CH02.read_text(encoding="utf-8")
    assert r"\section{Observer-frame discriminator: separating kinematic dipole from Bianchi tilt}" in text
    assert r"\label{sec:dipole-discriminator}" in text
    assert "04_discriminator_coverage.png" in text


def test_fb87_ch09_points_back_to_the_new_observer_frame_section() -> None:
    text = CH09.read_text(encoding="utf-8")
    assert "Section~\\ref{sec:dipole-discriminator}" in text


@pytest.mark.parametrize("reference_key", EXPECTED_REFERENCES)
def test_fb87_references_include_new_observer_frame_sources(reference_key: str) -> None:
    text = REFERENCES.read_text(encoding="utf-8")
    assert f"@article{{{reference_key}" in text
