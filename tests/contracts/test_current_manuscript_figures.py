from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_curation_removes_only_graphic_figure_blocks_and_inserts_snippet(tmp_path: Path):
    module = _load_script("curate_current_manuscript_figures")
    chapter = tmp_path / "docs" / "manuscript" / "ch03_framework.tex"
    chapter.parent.mkdir(parents=True)
    chapter.write_text(
        r"""
Before.
\begin{figure}
\centering
\includegraphics[width=\linewidth]{legacy_plot}
\caption{Legacy plot}
\end{figure}
Figure~\ref{fig:legacy_plot} should not survive.
\begin{figure}
This non-graphic figure-like environment is kept.
\end{figure}
After.
""".lstrip(),
        encoding="utf-8",
    )

    updated, result = module.curate_file(chapter, repo_root=tmp_path)

    assert result.removed_blocks == 1
    assert result.removed_includes == ("legacy_plot",)
    assert result.replaced_figure_refs == ("fig:legacy_plot",)
    assert "legacy_plot" not in updated
    assert "Legacy plot" not in updated
    assert r"\ref{fig:legacy_plot}" not in updated
    assert r"\emph{legacy figure removed}" in updated
    assert "non-graphic figure-like environment is kept" in updated
    assert r"\input{generated/current_figures_framework}" in updated


def test_current_figure_specs_are_repo_local_and_claim_gated():
    module = _load_script("make_current_manuscript_figures")
    specs = module._figure_specs()

    assert len(specs) >= 10
    required = {
        "fig_current_transfer_sensitivity_tornado.png",
        "fig_current_local_global_rank_fpr.png",
        "fig_current_qfpi_gf_semantic_split.png",
        "fig_current_mio_depth_residual_vectors.png",
    }
    assert required <= {spec.file_name for spec in specs}
    captions = "\n".join(spec.caption for spec in specs).lower()
    assert "family identified" not in captions
    assert "geometry detected" not in captions
    assert "external transfer validated as native" not in captions
    assert "mio posterior" not in captions
    assert "truth certificate" not in captions
    assert all(spec.source_paths for spec in specs)
    assert all(spec.artifact_mode for spec in specs)
    assert all(spec.allowed_use for spec in specs)
    assert all(spec.caption_policy for spec in specs)
    assert all(spec.promotion_blockers for spec in specs)
    depth_spec = next(
        spec
        for spec in specs
        if spec.file_name == "fig_current_mio_depth_residual_vectors.png"
    )
    assert "docs/generated/gf_matched_null_forecast_report.json" in depth_spec.source_paths
    assert "docs/generated/current_science_plot_payload.json" in depth_spec.source_paths
    assert "matched_null_forecast_report_required" in depth_spec.caption_policy
    for spec in specs:
        for rel_path in spec.source_paths:
            assert (REPO_ROOT / rel_path).exists(), rel_path
        assert spec.snippet.startswith("current_figures_")


def test_current_payload_exposes_gf_floor_split_and_forecast_report():
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )
    semantic = payload["semantic_and_vectors"]
    contract = semantic["g_f_display_contract"]
    forecast = semantic["g_f_matched_null_forecast"]

    assert contract["summary_label"] == "G_F_display_contract"
    assert contract["owner"] == "MIO"
    assert contract["implementation_scope"] == "mio"
    assert contract["claim_tier"] == "diagnostic_only"
    assert contract["forecast_only"] is True
    assert contract["observed_data_evidence"] is False
    assert contract["global_tilt_wording_allowed"] is False
    assert contract["matched_null_forecast_status"] == "forecast_matched_null_blocked"
    assert contract["local_global_separation_status"] == (
        "blocked_existing_null_bank_insufficient"
    )
    assert contract["floor_value"] > 0.0
    assert contract["floor_label"]
    assert contract["floor_reason"]
    assert isinstance(contract["floor_applied_by_bin"], dict)
    assert isinstance(contract["raw_F_by_bin"], dict)
    assert isinstance(contract["effective_F_by_bin"], dict)
    assert isinstance(contract["denominator_evolution_split"], dict)
    assert contract["denominator_evolution_split"]["mean_summary_is_decompositional"] is False
    assert contract["g_f_payload_ref"] == "/semantic_and_vectors/g_f_display_contract/g_f_payload"
    assert contract["floor_applied_by_bin_ref"] == (
        "/semantic_and_vectors/g_f_display_contract/floor_applied_by_bin"
    )
    assert forecast["artifact_path"] == "docs/generated/gf_matched_null_forecast_report.json"
    assert forecast["artifact_mode"] == "forecast_only"
    assert forecast["allowed_use"] == "external_audit"
    assert forecast["forecast_source_kind"] == "deterministic_current_code_fixture"
    assert forecast["matched_null_status"] == "forecast_matched_null_blocked"
    assert forecast["retuning_after_failure"] is False
    assert forecast["global_tilt_wording_allowed"] is False


def test_current_manuscript_figure_generator_check_mode_is_current():
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "make_current_manuscript_figures.py"),
            "--check",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_current_and_observed_manifests_carry_claim_lane_policy():
    manifest_paths = [
        *sorted((REPO_ROOT / "figures" / "current").glob("*.manifest.json")),
        *sorted((REPO_ROOT / "figures" / "observed_current").glob("*.manifest.json")),
    ]

    assert manifest_paths
    assert any("observed_current" in path.parts for path in manifest_paths)

    for path in manifest_paths:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for field in (
            "claim_tier",
            "artifact_mode",
            "allowed_use",
            "caption_policy",
            "promotion_blockers",
        ):
            assert manifest.get(field), f"{path}: missing {field}"
        policy_text = " ".join(
            str(item)
            for item in (
                list(manifest["caption_policy"])
                + list(manifest["promotion_blockers"])
                + list(manifest.get("caveats", []))
            )
        ).lower()
        assert "family" in policy_text, f"{path}: policy must prohibit family use"
        assert "native" in policy_text and "solver" in policy_text, (
            f"{path}: policy must prohibit native-solver use"
        )
