from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_expanded_manuscript_figure_suite.py"


def _load_suite_module():
    spec = importlib.util.spec_from_file_location(
        "build_expanded_manuscript_figure_suite_test", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_conditioned_legacy_gallery_covers_existing_noncurrent_figures():
    suite = _load_suite_module()

    candidates = suite._iter_legacy_candidates()

    assert len(candidates) == 88
    assert all("current" not in path.relative_to(suite.FIGURES_ROOT).parts for path in candidates)
    assert all("paper" not in path.relative_to(suite.FIGURES_ROOT).parts for path in candidates)
    assert all(
        "conditioned_legacy" not in path.relative_to(suite.FIGURES_ROOT).parts
        for path in candidates
    )


def test_high_risk_legacy_caption_blocks_family_and_native_claims():
    suite = _load_suite_module()
    source = REPO_ROOT / "figures" / "fig_equiv_class_evidence.png"

    caption = suite._caption_for(source)

    assert "appendix-only" in caption
    assert "family-ID evidence" in caption
    assert "native-transfer" in caption


def test_generated_ver2_and_conditioned_manifests_are_valid():
    ver2_manifest = (
        REPO_ROOT
        / "figures"
        / "paper"
        / "ver2_generated"
        / "fig_ver2b_local_global_discrimination_matrix.manifest.json"
    )
    conditioned_manifest = (
        REPO_ROOT
        / "figures"
        / "conditioned_legacy"
        / "root__fig_equiv_class_evidence.manifest.json"
    )

    for manifest_path in (ver2_manifest, conditioned_manifest):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifact_path = REPO_ROOT / payload["artifact_path"]
        issues = validate_manifest_payload(
            payload,
            manifest_path=manifest_path,
            expected_artifact_path=payload["artifact_path"],
        )
        assert artifact_path.exists()
        assert issues == ()
        assert payload["owner"] == "COMMON"
        assert payload["implementation_scope"] == "common"
        assert "native_solver" not in str(payload["transfer_source"])
