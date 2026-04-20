from __future__ import annotations

from pathlib import Path


def test_fb117_expected_docs_and_gallery_paths_exist() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    expected = [
        repo_root / "docs/lowell_bianchi/05_integrator_spec.md",
        repo_root / "figures/physics_gallery/16_inference_corner/README.md",
        repo_root / "docs/audits/AUDIT_PHASE_FB11_2026-04-20.md",
        repo_root / "docs/audits/AUDIT_SUMMARY_EXTENDED_BUNDLE_2026-04-20.md",
    ]
    for path in expected:
        assert path.exists(), str(path)

