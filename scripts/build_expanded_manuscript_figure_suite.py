#!/usr/bin/env python3
"""Build the expanded manuscript figure suite.

This script has two intentionally separate phases:

* ``conservative`` generates the current VER2 pack figures that already have
  manifest sidecars in the export path.
* ``aggressive`` copies existing legacy figures into a conditioned gallery and
  adds explicit sidecar manifests plus claim-bounded captions.

The aggressive phase does not promote legacy plots as current production
results. It makes their assumptions machine-visible so they can be shown only
as hypothesis-conditioned appendix diagnostics.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


FIGURES_ROOT = REPO_ROOT / "figures"
CONDITIONED_DIR = FIGURES_ROOT / "conditioned_legacy"
MANUSCRIPT_GENERATED = REPO_ROOT / "docs" / "manuscript" / "generated"
GENERATED_DOCS = REPO_ROOT / "docs" / "generated"
VER2_GEN = REPO_ROOT / "docs" / "ver2_upgrade" / "generated"
VER2_FIGURE_DIR = FIGURES_ROOT / "paper" / "ver2_generated"
CONSERVATIVE_SNIPPET = MANUSCRIPT_GENERATED / "current_figures_ver2_exports.tex"
CONDITIONED_SNIPPET = MANUSCRIPT_GENERATED / "conditioned_legacy_figure_gallery.tex"
EXPANDED_PLOT_LIST = GENERATED_DOCS / "expanded_manuscript_plot_list.md"
SUMMARY_JSON = GENERATED_DOCS / "expanded_manuscript_figure_suite.json"
CURRENT_PLOT_LIST = GENERATED_DOCS / "current_manuscript_plot_list.md"

FIGURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf"}
VER2_FIGURES = (
    {
        "pack": "A",
        "pack_json": "result_pack_A_scalar_to_morphology.json",
        "base": "fig_ver2a_scalar_to_morphology_summary",
        "label": "fig:ver2-current-scalar-morphology-summary",
        "caption": (
            "VER2 scalar-to-morphology summary generated from the current "
            "export records.  This is a conditional morphology-compatibility "
            "diagnostic: scalar summaries and proxy labels are not a Bianchi "
            "family-ID result, not native low-ell transfer output, and not an "
            "HTT evidence statement."
        ),
    },
    {
        "pack": "B",
        "pack_json": "result_pack_B_local_global.json",
        "base": "fig_ver2b_local_global_discrimination_matrix",
        "label": "fig:ver2-current-local-global-matrix",
        "caption": (
            "VER2 local/global discrimination matrix generated from the "
            "current HTT export surface.  The matrix is a transfer-conditional "
            "candidate diagnostic for separating local response, global tilt, "
            "and null/systematic alternatives; it is not an odds or evidence "
            "calculation and does not identify geometry."
        ),
    },
    {
        "pack": "C",
        "pack_json": "result_pack_C_departure_cards.json",
        "base": "fig_ver2c_departure_card_summary",
        "label": "fig:ver2-current-departure-card-summary",
        "caption": (
            "VER2 departure-card summary generated from current COMMON/MIO "
            "records.  The x, Q, Pi, F, and G quantities are descriptive "
            "diagnostics under the recorded budget assumptions; they do not "
            "certify a model family or replace transfer provenance."
        ),
    },
    {
        "pack": "D",
        "pack_json": "result_pack_D_mio_certificates.json",
        "base": "fig_ver2d_mio_predictive_residuals",
        "label": "fig:ver2-current-mio-residuals",
        "caption": (
            "VER2 MIO predictive-residual summary generated from current "
            "diagnostic certificates.  MIO owns the residual diagnostic only; "
            "HTT evidence, posterior bundles, and model ranking remain outside "
            "this figure."
        ),
    },
    {
        "pack": "E",
        "pack_json": "result_pack_E_equivalence_classes.json",
        "base": "fig_ver2e_validation_campaign_matrix",
        "label": "fig:ver2-current-validation-campaign-matrix",
        "caption": (
            "VER2 validation-campaign matrix generated from current export "
            "metadata.  Family names or campaign labels in the source records "
            "are implementation labels for coverage auditing only; native "
            "morphology atlas support is still absent."
        ),
    },
)


@dataclass(frozen=True)
class ConditionedFigure:
    source_path: Path
    output_path: Path
    manifest_path: Path
    label: str
    title: str
    condition: str
    caption: str
    transfer_source: str
    sky_support_status: str
    null_mock_status: str


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _git_state() -> tuple[str | None, str]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None, "git_state_unavailable"
    return commit, f"{commit}+dirty" if status else commit


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ver2_manifest_path(base: str) -> Path:
    return VER2_FIGURE_DIR / f"{base}.manifest.json"


def _ver2_figure_path(base: str) -> Path:
    return VER2_FIGURE_DIR / f"{base}.png"


def _validate_manifest(path: Path, artifact_path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    issues = validate_manifest_payload(
        payload,
        manifest_path=path,
        expected_artifact_path=_repo_relative(artifact_path),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise RuntimeError(f"invalid manifest {path}: {rendered}")


def _pack_json_path(item: dict[str, object]) -> Path:
    return VER2_GEN / str(item["pack_json"])


def _pack_payload(item: dict[str, object]) -> dict[str, Any]:
    path = _pack_json_path(item)
    if not path.exists():
        raise RuntimeError(f"missing VER2 pack JSON: {_repo_relative(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_owner(artifact: dict[str, Any]) -> str:
    manifest = artifact.get("manifest")
    if isinstance(manifest, dict):
        return str(manifest.get("owner", "UNKNOWN"))
    artifact_id = str(artifact.get("artifact_id", ""))
    prefix = artifact_id.split(".", 1)[0].upper()
    if prefix in {"BASS", "HTT", "MIO", "COMMON"}:
        return prefix
    if prefix == "TSC":
        return "TSC_LEGACY"
    return "UNKNOWN"


def _count_by(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _plot_ver2_pack(item: dict[str, object], payload: dict[str, Any], output: Path) -> None:
    artifacts = [a for a in payload.get("artifacts", []) if isinstance(a, dict)]
    owner_counts = _count_by(_artifact_owner(a) for a in artifacts)
    tier_counts = _count_by(str(a.get("claim_tier", "unknown")) for a in artifacts)
    caveats = payload.get("caveats", [])
    caveat_count = len(caveats) if isinstance(caveats, list) else 0

    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.4), gridspec_kw={"width_ratios": [1.1, 1.0]})
    owners = list(owner_counts) or ["none"]
    owner_values = [owner_counts.get(owner, 0) for owner in owners]
    axes[0].barh(owners, owner_values, color="#0f766e")
    axes[0].set_title("Artifact ownership", loc="left", fontweight="bold")
    axes[0].set_xlabel("artifact count")
    axes[0].grid(axis="x", color="#cbd5e1", linewidth=0.7)
    axes[0].spines["top"].set_visible(False)
    axes[0].spines["right"].set_visible(False)

    tiers = list(tier_counts) or ["unknown"]
    tier_values = [tier_counts.get(tier, 0) for tier in tiers]
    axes[1].bar(tiers, tier_values, color="#b45309")
    axes[1].set_title("Claim-tier mix", loc="left", fontweight="bold")
    axes[1].set_ylabel("artifact count")
    axes[1].grid(axis="y", color="#cbd5e1", linewidth=0.7)
    axes[1].spines["top"].set_visible(False)
    axes[1].spines["right"].set_visible(False)
    axes[1].tick_params(axis="x", rotation=20)

    title = str(payload.get("title", item["base"]))
    pack = str(payload.get("pack_id", item["pack"]))
    production = "diagnostic_only"
    claim = str(payload.get("claim_tier", "unknown"))
    fig.suptitle(f"VER2 pack {pack}: {title}", x=0.02, ha="left", fontweight="bold")
    fig.text(
        0.99,
        0.02,
        f"pack tier={claim}; status={production}; caveats={caveat_count}; diagnostic use only",
        ha="right",
        va="bottom",
        fontsize=8.5,
        color="#334155",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _ver2_manifest_payload(item: dict[str, object], payload: dict[str, Any]) -> dict[str, Any]:
    figure_path = _ver2_figure_path(str(item["base"]))
    pack_path = _pack_json_path(item)
    commit, worktree_state = _git_state()
    claim_tier = "diagnostic_only"
    production = "diagnostic_only"
    caveats = payload.get("caveats", [])
    raw_caveats = [str(caveat) for caveat in caveats] if isinstance(caveats, list) else []
    caveat_list = [
        caveat
        for caveat in raw_caveats
        if not caveat.lower().startswith(("public_grade=", "production_status="))
    ]
    caveat_list.extend(
        [
            "Figure is generated from current VER2 pack JSON artifacts, not from a native low-ell solver.",
            "No Bianchi family-ID or geometry-detection claim is made.",
            "Source-pack readiness labels are provenance only and are not promoted into the manuscript figure lane.",
            "Manuscript figure lane is diagnostic-only regardless of source-pack readiness vocabulary.",
        ]
    )
    return {
        "artifact_id": f"common.manuscript.ver2_pack_figure.{item['base']}",
        "artifact_path": _repo_relative(figure_path),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": claim_tier,
        "production_status": production,
        "created_by": "scripts/build_expanded_manuscript_figure_suite.py",
        "git_commit": commit,
        "config_hash": _stable_hash(
            {
                "phase": "conservative_ver2_pack",
                "pack_json": _repo_relative(pack_path),
                "figure": _repo_relative(figure_path),
            }
        ),
        "input_hashes": [
            f"{_repo_relative(pack_path)}:sha256:{_sha256(pack_path)}",
            f"scripts/build_expanded_manuscript_figure_suite.py:sha256:{_sha256(Path(__file__))}",
        ],
        "code_version": "ver2-pack-figure-v1",
        "schema_version": "artifact-manifest-v2",
        "caveats": caveat_list,
        "required_gates": ["manifest_sidecar_before_manuscript_use"],
        "passed_gates": ["ver2_pack_json_loaded", "figure_manifest_validated"],
        "failed_gates": [],
        "statistics_definitions": {
            "pack_id": str(payload.get("pack_id", item["pack"])),
            "source_pack_json": _repo_relative(pack_path),
            "manuscript_role": "current_code_diagnostic",
        },
        "transfer_source": "VER2_pack_export_context_external_or_schema_bound",
        "sky_support_status": "pending_or_unknown_for_existing_directional_artifacts",
        "null_mock_status": "pack_declared_or_not_refreshed",
        "generating_command": "python scripts/build_expanded_manuscript_figure_suite.py --phase conservative",
        "git_commit_or_worktree_state": worktree_state,
    }


def _generate_lightweight_ver2_figures() -> dict[str, Any]:
    generated: list[str] = []
    manifests: list[str] = []
    for item in VER2_FIGURES:
        payload = _pack_payload(item)
        figure_path = _ver2_figure_path(str(item["base"]))
        manifest_path = _ver2_manifest_path(str(item["base"]))
        _plot_ver2_pack(item, payload, figure_path)
        _write_json(manifest_path, _ver2_manifest_payload(item, payload))
        caption_path = figure_path.with_suffix(".caption.txt")
        caption_path.write_text(str(item["caption"]) + "\n", encoding="utf-8")
        _validate_manifest(manifest_path, figure_path)
        generated.append(_repo_relative(figure_path))
        manifests.append(_repo_relative(manifest_path))
    return {"figures": generated, "manifests": manifests}


def write_conservative_snippet() -> dict[str, Any]:
    generated = _generate_lightweight_ver2_figures()
    missing: list[str] = []
    for item in VER2_FIGURES:
        figure_path = _ver2_figure_path(str(item["base"]))
        manifest_path = _ver2_manifest_path(str(item["base"]))
        if not figure_path.exists():
            missing.append(_repo_relative(figure_path))
        if not manifest_path.exists():
            missing.append(_repo_relative(manifest_path))
        if figure_path.exists() and manifest_path.exists():
            _validate_manifest(manifest_path, figure_path)
    if missing:
        raise RuntimeError("missing VER2 generated figure assets: " + ", ".join(missing))

    lines = [
        "% Auto-generated by scripts/build_expanded_manuscript_figure_suite.py --phase conservative",
        "% Current-code VER2 figures. Captions intentionally restate claim ceilings.",
        "",
    ]
    for item in VER2_FIGURES:
        lines.extend(
            [
                r"\begin{figure}[t]",
                r"\centering",
                rf"\includegraphics[width=0.88\textwidth]{{paper/ver2_generated/{item['base']}}}",
                rf"\caption{{{item['caption']}}}",
                rf"\label{{{item['label']}}}",
                r"\end{figure}",
                "",
            ]
        )
    CONSERVATIVE_SNIPPET.parent.mkdir(parents=True, exist_ok=True)
    CONSERVATIVE_SNIPPET.write_text("\n".join(lines), encoding="utf-8")
    return {
        "snippet": _repo_relative(CONSERVATIVE_SNIPPET),
        "figures": [
            {
                "base": item["base"],
                "path": _repo_relative(_ver2_figure_path(str(item["base"]))),
                "manifest": _repo_relative(_ver2_manifest_path(str(item["base"]))),
                "pack": item["pack"],
                "label": item["label"],
            }
            for item in VER2_FIGURES
        ],
        "generation": generated,
    }


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug or "figure"


def _display_title(source_path: Path) -> str:
    stem = source_path.stem
    for prefix in ("fig_",):
        if stem.startswith(prefix):
            stem = stem[len(prefix) :]
    stem = re.sub(r"^\d+_", "", stem)
    return stem.replace("_", " ")


def _iter_legacy_candidates() -> tuple[Path, ...]:
    excluded_parts = {"current", "observed_current", "paper", "conditioned_legacy"}
    candidates: list[Path] = []
    for path in sorted(FIGURES_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in FIGURE_SUFFIXES:
            continue
        rel_parts = path.relative_to(FIGURES_ROOT).parts
        if rel_parts and rel_parts[0] in excluded_parts:
            continue
        candidates.append(path)
    return tuple(candidates)


def _copy_name(source_path: Path) -> str:
    rel = source_path.relative_to(FIGURES_ROOT)
    if len(rel.parts) == 1:
        prefix = "root"
    else:
        prefix = "_".join(rel.parts[:-1])
    return f"{_slug(prefix)}__{source_path.name}"


def _infer_transfer_source(source_path: Path) -> str:
    text = source_path.as_posix().lower()
    if "validation/flrw" in text:
        return "FLRW_validation_context"
    if any(token in text for token in ("transfer", "route_b", "aniclass", "planck", "camb")):
        return "external_or_legacy_transfer_context"
    if any(token in text for token in ("triangle", "bvii", "bianchi", "sigma", "omega")):
        return "legacy_analytic_or_proxy_context"
    return "none_or_legacy_context"


def _infer_sky_support_status(source_path: Path) -> str:
    text = source_path.as_posix().lower()
    if any(
        token in text
        for token in (
            "sky",
            "direction",
            "mollweide",
            "coverage",
            "dipole",
            "hemispherical",
            "orientation",
            "separations",
            "alignment",
        )
    ):
        return "pending_or_unknown_for_existing_directional_artifacts"
    return "not_directional"


def _infer_null_mock_status(source_path: Path) -> str:
    text = source_path.as_posix().lower()
    if any(token in text for token in ("validation", "null", "pvalue", "sbc", "injection", "leave_one_out")):
        return "legacy_mock_or_validation_context"
    if any(token in text for token in ("evidence", "bf", "posterior", "triangle")):
        return "legacy_statistical_context_no_current_null_refresh"
    return "not_statistical_or_legacy_context"


def _infer_condition(source_path: Path) -> str:
    rel = _repo_relative(source_path)
    text = rel.lower()
    if rel.startswith("figures/validation/"):
        return (
            "shown as a validation-context diagnostic tied to the existing "
            "FLRW/CAMB/BASS comparison artifact; not a production validation "
            "of anisotropic native low-ell transfer."
        )
    if rel.startswith("figures/parallel_track/"):
        return (
            "shown as parallel-track prior context under the assumptions of "
            "the original helper script; it is not a current main-claim result."
        )
    if any(token in text for token in ("evidence", "bf", "posterior", "triangle")):
        return (
            "shown only under the legacy statistical assumptions encoded by "
            "the original manuscript generator; no current null/PPC/LOOCV "
            "refresh is implied."
        )
    if any(token in text for token in ("sky", "direction", "dipole", "mollweide")):
        return (
            "shown only as a directional diagnostic with unresolved current "
            "sky-support and mask metadata."
        )
    return (
        "shown only as a legacy manuscript-generator diagnostic under its "
        "original assumptions, with current claim ceilings made explicit."
    )


def _short_condition(source_path: Path) -> str:
    rel = _repo_relative(source_path)
    text = rel.lower()
    if rel.startswith("figures/validation/"):
        return "FLRW validation-context diagnostic; not anisotropic native-transfer validation"
    if rel.startswith("figures/parallel_track/"):
        return "parallel-track prior context"
    if any(token in text for token in ("evidence", "bf", "posterior", "triangle")):
        return "legacy statistical assumptions without current null/PPC/LOOCV refresh"
    if any(token in text for token in ("sky", "direction", "dipole", "mollweide")):
        return "directional artifact with current sky/mask support unresolved"
    return "legacy manuscript-generator assumptions"


def _caption_for(source_path: Path) -> str:
    title = _display_title(source_path)
    condition = _short_condition(source_path)
    return (
        f"Conditioned legacy diagnostic: {title}. Condition: {condition}. "
        "See sidecar manifest for provenance and caveats; appendix-only, "
        "not native-transfer or family-ID evidence."
    )


def _legacy_manifest_payload(
    conditioned: ConditionedFigure,
    *,
    command: str,
    commit: str | None,
    worktree_state: str,
) -> dict[str, Any]:
    source_rel = _repo_relative(conditioned.source_path)
    output_rel = _repo_relative(conditioned.output_path)
    payload = {
        "artifact_id": f"common.conditioned_legacy_figure.{conditioned.output_path.stem}",
        "artifact_path": output_rel,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "exploratory",
        "production_status": "diagnostic_only",
        "created_by": "scripts/build_expanded_manuscript_figure_suite.py",
        "git_commit": commit,
        "config_hash": _stable_hash(
            {
                "phase": "aggressive_conditioned_legacy_gallery",
                "source_path": source_rel,
                "output_path": output_rel,
                "condition": conditioned.condition,
            }
        ),
        "input_hashes": [
            f"{source_rel}:sha256:{_sha256(conditioned.source_path)}",
            f"scripts/build_expanded_manuscript_figure_suite.py:sha256:{_sha256(Path(__file__))}",
        ],
        "code_version": "conditioned-legacy-gallery-v1",
        "schema_version": "artifact-manifest-v2",
        "caveats": [
            "Conditionally included legacy figure; not a refreshed current-code production result.",
            conditioned.condition,
            "No native low-ell solver output is represented.",
            "No Bianchi family-ID or geometry-detection claim is made.",
            "MIO diagnostics, HTT inference, and transfer provenance remain separated by owner.",
        ],
        "required_gates": [
            "native_low_ell_morphology_atlas_before_family_id",
            "manifest_sidecar_before_manuscript_use",
        ],
        "passed_gates": ["conditioned_legacy_manifest_sidecar"],
        "failed_gates": [],
        "statistics_definitions": {
            "legacy_source_path": source_rel,
            "manuscript_role": "appendix_only_conditioned_diagnostic",
        },
        "transfer_source": conditioned.transfer_source,
        "sky_support_status": conditioned.sky_support_status,
        "null_mock_status": conditioned.null_mock_status,
        "generating_command": command,
        "git_commit_or_worktree_state": worktree_state,
    }
    return payload


def _conditioned_records(command: str) -> tuple[ConditionedFigure, ...]:
    records: list[ConditionedFigure] = []
    for source in _iter_legacy_candidates():
        output = CONDITIONED_DIR / _copy_name(source)
        title = _display_title(source)
        label = f"fig:conditioned-legacy-{_slug(output.stem)}"
        records.append(
            ConditionedFigure(
                source_path=source,
                output_path=output,
                manifest_path=output.with_suffix("").with_name(output.with_suffix("").name + ".manifest.json"),
                label=label,
                title=title,
                condition=_infer_condition(source),
                caption=_caption_for(source),
                transfer_source=_infer_transfer_source(source),
                sky_support_status=_infer_sky_support_status(source),
                null_mock_status=_infer_null_mock_status(source),
            )
        )
    return tuple(records)


def write_conditioned_gallery(command: str) -> dict[str, Any]:
    commit, worktree_state = _git_state()
    records = _conditioned_records(command)
    CONDITIONED_DIR.mkdir(parents=True, exist_ok=True)
    for record in records:
        shutil.copy2(record.source_path, record.output_path)
        payload = _legacy_manifest_payload(
            record,
            command=command,
            commit=commit,
            worktree_state=worktree_state,
        )
        _write_json(record.manifest_path, payload)
        _validate_manifest(record.manifest_path, record.output_path)

    lines = [
        "% Auto-generated by scripts/build_expanded_manuscript_figure_suite.py --phase aggressive",
        r"\chapter{Conditioned Legacy Figure Gallery}",
        r"\label{app:conditioned-legacy-figure-gallery}",
        "",
        (
            "This appendix includes legacy figures only after adding explicit "
            "condition, provenance, and claim-ceiling sidecars.  These figures "
            "are appendix-only diagnostics.  They are not current production "
            "results, not native low-ell outputs, and not Bianchi family-ID "
            "or geometry-detection evidence."
        ),
        "",
        r"\captionsetup{hypcap=false}",
        "",
    ]
    for record in records:
        rel_without_suffix = _repo_relative(record.output_path.with_suffix(""))
        rel_without_figures = rel_without_suffix.removeprefix("figures/")
        lines.extend(
            [
                r"\clearpage",
                r"\begin{center}",
                r"\centering",
                rf"\includegraphics[width=0.82\textwidth,height=0.58\textheight,keepaspectratio]{{{rel_without_figures}}}",
                rf"\captionof{{figure}}{{{record.caption}}}",
                rf"\label{{{record.label}}}",
                r"\end{center}",
                "",
            ]
        )
    CONDITIONED_SNIPPET.parent.mkdir(parents=True, exist_ok=True)
    CONDITIONED_SNIPPET.write_text("\n".join(lines), encoding="utf-8")
    return {
        "snippet": _repo_relative(CONDITIONED_SNIPPET),
        "figures": [
            {
                "source": _repo_relative(record.source_path),
                "path": _repo_relative(record.output_path),
                "manifest": _repo_relative(record.manifest_path),
                "label": record.label,
                "condition": record.condition,
                "transfer_source": record.transfer_source,
                "sky_support_status": record.sky_support_status,
                "null_mock_status": record.null_mock_status,
            }
            for record in records
        ],
    }


def _current_figure_count() -> int:
    if not CURRENT_PLOT_LIST.exists():
        return 6
    for line in CURRENT_PLOT_LIST.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Current manifest-backed plot count:"):
            try:
                return int(line.rsplit("`", 2)[1])
            except (IndexError, ValueError):
                break
    return 6


def write_plot_list(summary: dict[str, Any]) -> None:
    conservative = summary.get("conservative", {})
    aggressive = summary.get("aggressive", {})
    conservative_figs = conservative.get("figures", [])
    aggressive_figs = aggressive.get("figures", [])
    current_count = _current_figure_count()
    total = current_count + len(conservative_figs) + len(aggressive_figs)
    lines = [
        "# Expanded Manuscript Plot List",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: mixed_manifest_backed_current_and_conditioned_legacy",
        "sky_support_status: pending_or_unknown_for_existing_directional_artifacts",
        "null_mock_status: mixed_current_and_legacy_context",
        f"config_hash: `{_stable_hash(summary)}`",
        "input_hashes:",
        f"- scripts/build_expanded_manuscript_figure_suite.py:sha256:{_sha256(Path(__file__))}",
        *(
            [f"- {_repo_relative(CURRENT_PLOT_LIST)}:sha256:{_sha256(CURRENT_PLOT_LIST)}"]
            if CURRENT_PLOT_LIST.exists()
            else []
        ),
        f"caveats:",
        "- The manifest-backed current figure deck remains the conservative core manuscript deck.",
        "- VER2 pack figures are current-code, manifest-backed diagnostics with explicit claim ceilings.",
        "- Conditioned legacy figures are appendix-only hypothesis-conditioned diagnostics.",
        "- No listed figure claims native low-ell solver output or Bianchi family-ID.",
        f"generating_command: `{summary['command']}`",
        f"git_commit_or_worktree_state: `{summary['git_commit_or_worktree_state']}`",
        "",
        "## Summary",
        "",
        f"- Existing current-code core figures: {current_count}",
        f"- Added current-code VER2 pack figures: {len(conservative_figs)}",
        f"- Added conditioned legacy appendix figures: {len(aggressive_figs)}",
        f"- Manuscript figure target after expansion: {total}",
        "",
        "## Added Current-Code VER2 Figures",
        "",
        "| Pack | Figure | Manifest | Role |",
        "| --- | --- | --- | --- |",
    ]
    for fig in conservative_figs:
        lines.append(
            f"| `{fig['pack']}` | `{fig['path']}` | `{fig['manifest']}` | current-code diagnostic |"
        )
    if not conservative_figs:
        lines.append("| none | none | none | none |")

    lines.extend(
        [
            "",
            "## Added Conditioned Legacy Figures",
            "",
            "| Source | Conditioned Figure | Manifest | Condition |",
            "| --- | --- | --- | --- |",
        ]
    )
    for fig in aggressive_figs:
        lines.append(
            f"| `{fig['source']}` | `{fig['path']}` | `{fig['manifest']}` | {fig['condition']} |"
        )
    if not aggressive_figs:
        lines.append("| none | none | none | none |")
    EXPANDED_PLOT_LIST.parent.mkdir(parents=True, exist_ok=True)
    EXPANDED_PLOT_LIST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_suite(phase: str, *, command: str) -> dict[str, Any]:
    commit, worktree_state = _git_state()
    summary: dict[str, Any] = {
        "phase": phase,
        "command": command,
        "git_commit": commit,
        "git_commit_or_worktree_state": worktree_state,
    }
    if phase in {"conservative", "all"}:
        summary["conservative"] = write_conservative_snippet()
    if phase in {"aggressive", "all"}:
        summary["aggressive"] = write_conditioned_gallery(command)
    _write_json(SUMMARY_JSON, summary)
    write_plot_list(summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=("conservative", "aggressive", "all"),
        default="all",
        help="which expansion phase to run",
    )
    args = parser.parse_args(argv)
    command_args = sys.argv[1:] if argv is None else argv
    command = shlex.join(["python", "scripts/build_expanded_manuscript_figure_suite.py", *command_args])
    summary = build_suite(args.phase, command=command)
    conservative = len(summary.get("conservative", {}).get("figures", []))
    aggressive = len(summary.get("aggressive", {}).get("figures", []))
    print(
        "expanded manuscript figures: "
        f"{conservative} conservative, {aggressive} conditioned legacy"
    )
    print(f"wrote {_repo_relative(SUMMARY_JSON)}")
    print(f"wrote {_repo_relative(EXPANDED_PLOT_LIST)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
