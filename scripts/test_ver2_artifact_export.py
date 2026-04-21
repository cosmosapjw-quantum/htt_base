from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ver2_artifact_export.py"


def _load_export_module():
    spec = importlib.util.spec_from_file_location("ver2_artifact_export_test", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_caption_claim_violation_blocks_stronger_terms() -> None:
    exporter = _load_export_module()
    caption = "\n".join(
        (
            "Claim tier: exploratory.",
            "Validated detection is reported here.",
        )
    )
    assert (
        exporter._caption_claim_violation(caption, "exploratory")
        == "caption_stronger_than_claim_tier"
    )


def test_conditional_pack_caption_includes_caveats() -> None:
    exporter = _load_export_module()
    _, packs = exporter.build_export_bundle()
    pack = next(pack for pack in packs if pack.pack_id == "A")
    caption = exporter._caption_text(pack)
    assert "Claim tier: conditional." in caption
    assert "Caveats:" in caption
    assert "Caveats: none." not in caption


def test_local_global_pack_reflects_calibrated_conditional_discrimination() -> None:
    exporter = _load_export_module()
    records, packs = exporter.build_export_bundle()
    record = records["discrimination"]
    pack = next(pack for pack in packs if pack.pack_id == "B")
    assert record.manifest.claim_tier == "conditional"
    assert record.manifest.production_status == "production_candidate"
    assert pack.claim_tier == "conditional"
    assert pack.production_status == "production_candidate"


def test_validation_pack_carries_representative_family_sweep_evidence() -> None:
    exporter = _load_export_module()
    records, packs = exporter.build_export_bundle()
    family_sweep = records["family_sweep"]
    pack = next(pack for pack in packs if pack.pack_id == "E")
    assert family_sweep.manifest.claim_tier == "conditional"
    assert "representative_tilted_runtime_partial_only" in family_sweep.manifest.caveats
    assert family_sweep.payload["evidence"]["campaign_id"] == "validation.bass_representative_family_sweep"
    assert any(record.key == "family_sweep" for record in pack.artifacts)


def test_scan_figures_blocks_missing_manifest_and_accepts_generated_override(
    tmp_path: Path,
) -> None:
    exporter = _load_export_module()
    root = tmp_path / "paper"
    legacy = root / "ch00_demo"
    generated = tmp_path / "ver2_generated"
    legacy.mkdir(parents=True)
    generated.mkdir(parents=True)

    legacy_base = legacy / "fig_legacy_missing_manifest"
    for suffix in (".png", ".pdf", ".caption.txt"):
        path = (
            legacy_base.with_name(legacy_base.name + suffix)
            if suffix == ".manifest.json"
            else legacy_base.with_suffix(suffix)
        )
        path.write_bytes(b"legacy")

    ready_base = generated / "fig_ready"
    ready_base.with_suffix(".png").write_bytes(b"png")
    ready_base.with_suffix(".pdf").write_bytes(b"pdf")
    ready_base.with_suffix(".caption.txt").write_text(
        "Claim tier: conditional.\nCaveats: demo.\n",
        encoding="utf-8",
    )
    manifest = exporter._make_manifest(
        artifact_id="common.test.figure.ready",
        artifact_path="figures/paper/ver2_generated/fig_ready.png",
        owner="COMMON",
        implementation_scope="common",
        claim_tier="conditional",
        production_status="production_candidate",
        statistics_definitions={"topic": "demo"},
    )
    ready_base.with_name(ready_base.name + ".manifest.json").write_text(
        json.dumps(exporter.asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = exporter._scan_figures(root, generated_root=generated)
    by_stem = {row["stem"]: row for row in rows}

    assert by_stem["fig_legacy_missing_manifest"]["export_status"] == "blocked_no_manifest"
    assert by_stem["fig_ready"]["export_status"] == "manifest_ready"
    assert by_stem["fig_ready"]["chapter"] == "ver2_generated"


def test_stale_generated_figure_assets_detects_changed_bytes(tmp_path: Path) -> None:
    exporter = _load_export_module()
    expected = tmp_path / "expected"
    actual = tmp_path / "actual"
    expected.mkdir()
    actual.mkdir()

    (expected / "fig.caption.txt").write_text("expected\n", encoding="utf-8")
    (actual / "fig.caption.txt").write_text("stale\n", encoding="utf-8")

    stale = exporter._stale_generated_figure_assets(expected, actual)
    assert stale == [str((actual / "fig.caption.txt").as_posix())]


def test_render_outputs_stays_inside_im10d_man_scope(tmp_path: Path) -> None:
    exporter = _load_export_module()
    records, packs = exporter.build_export_bundle()
    generated = tmp_path / "ver2_generated"
    exporter._generate_pack_figures(packs, figure_dir=generated)
    figures = exporter._scan_figures(exporter.FIGURE_ROOT, generated_root=generated)
    outputs = exporter._render_outputs(records, packs, figures)

    output_paths = [
        path.relative_to(exporter.REPO_ROOT).as_posix()
        for path in outputs
    ]
    manuscript_paths = [path for path in output_paths if path.startswith("docs/manuscript/")]
    assert manuscript_paths
    assert all(path.startswith("docs/manuscript/generated/") for path in manuscript_paths)
    assert "docs/manuscript/generated/ver2_result_pack_summary.tex" in output_paths
    assert "docs/manuscript/generated/ver2_validation_status.tex" in output_paths


def test_validation_status_tex_preserves_warn_ceiling(tmp_path: Path) -> None:
    exporter = _load_export_module()
    records, packs = exporter.build_export_bundle()
    generated_root = tmp_path / "ver2_generated"
    exporter._generate_pack_figures(packs, figure_dir=generated_root)
    figures = exporter._scan_figures(exporter.FIGURE_ROOT, generated_root=generated_root)
    outputs = exporter._render_outputs(records, packs, figures)

    validation_tex = outputs[
        exporter.REPO_ROOT / "docs" / "manuscript" / "generated" / "ver2_validation_status.tex"
    ]
    assert "Warn-grade" in validation_tex
    assert "no-claim gates" in validation_tex
    assert "production-validated rows" in validation_tex


def test_mio_export_consumes_live_tier_a_and_tier_b_forward_refs() -> None:
    exporter = _load_export_module()
    records, _ = exporter.build_export_bundle()
    mio_payload = records["mio"].payload
    input_refs = tuple(mio_payload["input_data_hashes"])
    assert "bass.ver2.export.forward.tier_a_validation" in input_refs
    assert "bass.ver2.export.forward.tier_b_runtime" in input_refs
