from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.skip(reason="pending FB-9.6 implementation — skeleton only")
def test_fb96_docs_gallery_skeleton_contract() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    spec_doc = repo_root / "docs/lowell_bianchi/01_species_background_spec.md"
    gallery_doc = repo_root / "figures/physics_gallery/15_massive_neutrino/README.md"
    assert spec_doc.exists()
    assert gallery_doc.exists()
