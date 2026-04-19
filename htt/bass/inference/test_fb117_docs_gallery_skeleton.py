from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.skip(reason="pending FB-11.7 implementation — skeleton only")
def test_fb117_docs_gallery_skeleton_contract() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    spec_doc = repo_root / "docs/lowell_bianchi/05_integrator_spec.md"
    gallery_doc = repo_root / "figures/physics_gallery/16_inference_corner/README.md"

    assert spec_doc.exists()
    assert gallery_doc.exists()
