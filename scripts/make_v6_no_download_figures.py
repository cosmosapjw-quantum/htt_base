#!/usr/bin/env python3
"""Generate manifest-backed v6 no-download diagnostic figures.

The inputs are the repo-local v6 research cards produced by
``scripts/build_v6_no_download_research_cards.py``.  This script does not run
K1, K5, or K6 analyses and does not download data.  It only renders current
diagnostic/readiness cards and exports user-run K5/K6 commands.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402


GEN = REPO_ROOT / "docs" / "generated"
FIGURE_DIR = REPO_ROOT / "figures" / "quarantined_meta" / "v6_no_download"

RESEARCH_JSON = GEN / "v6_no_download_research_cards.json"
LEGACY_JSON = GEN / "v6_legacy_figure_classification.json"
PACK_JSON = GEN / "v6_no_download_figure_pack.json"
PACK_MD = GEN / "v6_no_download_figure_pack.md"
COMMANDS_JSON = GEN / "v6_k5_k6_user_commands.json"
COMMANDS_MD = GEN / "v6_k5_k6_user_commands.md"

SOURCE_PATHS = (
    "docs/generated/v6_no_download_research_cards.json",
    "docs/generated/v6_legacy_figure_classification.json",
    "scripts/make_v6_no_download_figures.py",
)

COLORS = {
    "text": "#1f2937",
    "muted": "#6b7280",
    "grid": "#e5e7eb",
    "ok": "#047857",
    "partial": "#d97706",
    "blocked": "#b91c1c",
    "info": "#2563eb",
    "violet": "#7c3aed",
    "teal": "#0f766e",
    "panel": "#f8fafc",
    "line": "#374151",
}


@dataclass(frozen=True)
class FigureSpec:
    artifact_id: str
    file_name: str
    title: str
    source_card: str
    null_mock_status: str
    transfer_source: str
    builder: Callable[[Path, dict[str, Any], dict[str, Any]], None]
    caveats: tuple[str, ...]


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes(paths: tuple[str, ...] = SOURCE_PATHS) -> list[str]:
    rows: list[str] = []
    for relative in paths:
        path = REPO_ROOT / relative
        if path.exists() and path.is_file():
            rows.append(f"{relative}:{_sha256(path)}")
        else:
            rows.append(f"{relative}:missing")
    return rows


def _config_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{_repo_relative(path)} must contain a JSON object")
    return payload


def _command(argv: list[str] | None) -> str:
    args = sys.argv[1:] if argv is None else argv
    return shlex.join(["python", "scripts/make_v6_no_download_figures.py", *args])


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _status_color(value: object) -> str:
    text = str(value or "").lower()
    if "measured" in text or text in {"ready", "available", "true"}:
        return COLORS["ok"]
    if "partial" in text or "descriptor" in text or "insufficient" in text:
        return COLORS["partial"]
    if "fail" in text or "blocked" in text or "no_go" in text:
        return COLORS["blocked"]
    return COLORS["info"]


def _short_status(value: object) -> str:
    text = str(value or "unknown")
    replacements = {
        "fail_closed_structural_no_go": "fail-closed no-go",
        "fail_closed_no_channel": "fail-closed no channel",
        "estimated_conditional_coverage": "conditional coverage",
        "estimated_partial": "partial estimate",
        "insufficient_for_likelihood_branch": "insufficient",
        "data_side_descriptor_only": "data-side only",
        "blocked_for_both_lowell_branches": "blocked",
    }
    return replacements.get(text, text.replace("_", " "))


def _matrix_cell_label(value: object) -> str:
    text = str(value or "unknown")
    labels = {
        "partial": "partial",
        "measured": "measured",
        "fail_closed_structural_no_go": "fail-closed\nno-go",
        "fail_closed_no_channel": "fail-closed\nno channel",
        "e2e_systematics_covariance_not_bound": "E2E cov\nnot bound",
        "true_cr_cell_cell_covariance_not_owned": "true CR cov\nnot owned",
        "conditional_lambdacdm_sigma_cv_prior_not_release_mocks": "CV prior;\nrelease mocks gate",
        "not_bound": "not bound",
        "isotropic_lcdm_grf_only_e2e_blocked": "GRF null;\nE2E blocked",
        "wf_mean_field_no_go_true_cr_posterior_blocked": "WF no-go;\ntrue CR blocked",
        "geometry_and_error_matched_gaussian_bulkflow_mocks": "Gaussian BF mocks;\nrelease gate remains",
        "not_applicable_no_channel": "no channel",
    }
    if text in labels:
        return labels[text]
    return "\n".join(textwrap.wrap(text.replace("_", " "), width=18))


def _branch_label(value: object) -> str:
    labels = {
        "mean_template": "mean\ntemplate",
        "covariance_biposh": "covariance\nBiPoSH",
        "central_scalar_chi_square": "central scalar\nchi-square",
    }
    return labels.get(str(value), str(value).replace("_", "\n"))


def _plot_component_source_matrix(
    out: Path, research: dict[str, Any], legacy: dict[str, Any]
) -> None:
    rows = research["cards"]["component_source_matrix"]["rows"]
    labels = [row["component"] for row in rows]
    cols = ["source", "covariance", "null"]
    matrix: list[list[str]] = []
    for row in rows:
        matrix.append(
            [
                row["source_status"],
                row["covariance_status"],
                row["null_mock_status"],
            ]
        )
    fig, ax = plt.subplots(figsize=(9.2, 4.9))
    ax.set_facecolor("white")
    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            color = _status_color(value)
            ax.add_patch(plt.Rectangle((x, y), 1, 1, color=color, alpha=0.85))
            ax.text(
                x + 0.5,
                y + 0.5,
                _matrix_cell_label(value),
                ha="center",
                va="center",
                color="white",
                fontsize=8.3,
                linespacing=1.15,
            )
    ax.set_xlim(0, len(cols))
    ax.set_ylim(0, len(labels))
    ax.invert_yaxis()
    ax.set_xticks(np.arange(len(cols)) + 0.5, cols, fontsize=10)
    ax.set_yticks(np.arange(len(labels)) + 0.5, labels, fontsize=10)
    ax.tick_params(length=0)
    ax.set_title("v6 component-source matrix", loc="left", fontsize=15, pad=12)
    ax.text(
        0,
        -0.45,
        "Diagnostic/readiness rows only; fail-closed sectors are not zero-filled.",
        color=COLORS["muted"],
        fontsize=9,
        transform=ax.transData,
    )
    for spine in ax.spines.values():
        spine.set_visible(False)
    _save(fig, out)


def _plot_denominator_sensitivity(
    out: Path, research: dict[str, Any], legacy: dict[str, Any]
) -> None:
    rows = research["cards"]["denominator_sensitivity_table"]["rows"]
    policies = sorted({row["denominator_policy"] for row in rows})
    palette = [COLORS["teal"], COLORS["info"], COLORS["violet"], COLORS["partial"]]
    fig, ax = plt.subplots(figsize=(8.8, 5.1))
    for idx, policy in enumerate(policies):
        subset = sorted(
            (row for row in rows if row["denominator_policy"] == policy),
            key=lambda row: float(row["relative_shift"]),
        )
        x = [float(row["relative_shift"]) for row in subset]
        y = [float(row["Q_diagnostic"]) for row in subset]
        ax.plot(
            x,
            y,
            marker="o",
            linewidth=2.2,
            color=palette[idx % len(palette)],
            label=policy.replace("_", " "),
        )
    ax.axhline(1.0, color=COLORS["line"], linewidth=1.0, linestyle="--", alpha=0.55)
    ax.set_title("v6 denominator sensitivity", loc="left", fontsize=15, pad=10)
    ax.set_xlabel("relative denominator shift")
    ax.set_ylabel("Q diagnostic")
    ax.grid(True, axis="y", color=COLORS["grid"], linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.text(
        0.0,
        -0.2,
        "Q is policy-normalized sensitivity, not a calibrated probability.",
        transform=ax.transAxes,
        color=COLORS["muted"],
        fontsize=9,
    )
    _save(fig, out)


def _plot_response_class_ledger(
    out: Path, research: dict[str, Any], legacy: dict[str, Any]
) -> None:
    counts = legacy["summary"]["by_response_class"]
    labels = sorted(counts, key=lambda item: counts[item])
    values = [counts[label] for label in labels]
    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    bars = ax.barh(
        range(len(labels)),
        values,
        color=[COLORS["muted"], COLORS["info"], COLORS["partial"], COLORS["teal"], COLORS["blocked"]][
            : len(labels)
        ],
        alpha=0.9,
    )
    ax.set_yticks(range(len(labels)), [label.replace("_", "\n") for label in labels], fontsize=8)
    ax.set_xlabel("old figures classified")
    ax.set_title("v6 legacy response-class ledger", loc="left", fontsize=15, pad=10)
    ax.grid(True, axis="x", color=COLORS["grid"], linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + 0.6,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            fontsize=9,
            color=COLORS["text"],
        )
    response = research["cards"]["response_class_ledger"]["current_response_overlap"]
    annotation = (
        f"current response rank={response.get('projected_rank')}  "
        f"condition={float(response.get('condition_number', 0.0)):.2f}  "
        "legacy rankings removed"
    )
    ax.text(0.0, -0.18, annotation, transform=ax.transAxes, fontsize=9, color=COLORS["muted"])
    _save(fig, out)


def _plot_optical_ansatz_readiness(
    out: Path, research: dict[str, Any], legacy: dict[str, Any]
) -> None:
    rows = research["cards"]["optical_ansatz_readiness"]
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    ax.axis("off")
    ax.set_title("v6 optical-ansatz readiness", loc="left", fontsize=15, pad=12)
    y0 = 0.78
    row_h = 0.23
    for idx, row in enumerate(rows):
        y = y0 - idx * row_h
        color = _status_color(row["current_status"])
        ax.add_patch(
            plt.Rectangle(
                (0.02, y - 0.075),
                0.24,
                0.13,
                transform=ax.transAxes,
                color=color,
                alpha=0.9,
            )
        )
        ax.text(
            0.14,
            y - 0.01,
            _branch_label(row["branch"]),
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="white",
            fontsize=8.6,
            weight="bold",
            linespacing=1.05,
        )
        ax.text(
            0.31,
            y + 0.025,
            _short_status(row["current_status"]),
            transform=ax.transAxes,
            fontsize=10,
            color=COLORS["text"],
            weight="bold",
        )
        ax.text(
            0.31,
            y - 0.055,
            str(row["blocker"]).replace("_", " "),
            transform=ax.transAxes,
            fontsize=8.4,
            color=COLORS["muted"],
            wrap=True,
        )
    ax.text(
        0.02,
        0.05,
        "Central scalar summaries remain diagnostic; no low-ell theory likelihood branch is certified.",
        transform=ax.transAxes,
        fontsize=9,
        color=COLORS["muted"],
    )
    _save(fig, out)


def _plot_depth_gap_and_readiness(
    out: Path, research: dict[str, Any], legacy: dict[str, Any]
) -> None:
    depth = research["cards"]["depth_gap_card"]
    feasibility = research["cards"]["k5_k6_next_turn_feasibility"]
    bins = list(depth["effective_F_by_bin"].keys())
    raw = [float(depth["raw_F_by_bin"][bin_id]) for bin_id in bins]
    eff = [float(depth["effective_F_by_bin"][bin_id]) for bin_id in bins]
    x = np.arange(len(bins))
    fig, (ax, ax2) = plt.subplots(
        1,
        2,
        figsize=(10.2, 4.8),
        gridspec_kw={"width_ratios": [1.1, 1.0]},
    )
    ax.bar(x - 0.17, raw, width=0.34, color=COLORS["partial"], label="raw F")
    ax.bar(x + 0.17, eff, width=0.34, color=COLORS["teal"], label="effective F")
    ax.set_xticks(x, bins)
    ax.set_ylabel("F display value")
    ax.set_title("v6 depth-gap display contract", loc="left", fontsize=14, pad=10)
    ax.grid(True, axis="y", color=COLORS["grid"], linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=9)
    ax.text(
        0.0,
        -0.22,
        f"G_F={float(depth['G_F']):.2f}; matched null forecast remains blocked.",
        transform=ax.transAxes,
        fontsize=9,
        color=COLORS["muted"],
    )

    ax2.axis("off")
    ax2.set_title("K5/K6 user-run readiness", loc="left", fontsize=14, pad=10)
    for idx, lane in enumerate(("K5", "K6")):
        row = feasibility[lane]
        y = 0.72 - idx * 0.34
        color = COLORS["ok"] if row["next_turn_runnable"] else COLORS["blocked"]
        ax2.add_patch(
            plt.Rectangle((0.02, y - 0.12), 0.94, 0.22, transform=ax2.transAxes, color=COLORS["panel"])
        )
        ax2.add_patch(
            plt.Rectangle((0.04, y - 0.06), 0.08, 0.08, transform=ax2.transAxes, color=color)
        )
        ax2.text(0.15, y + 0.02, lane, transform=ax2.transAxes, fontsize=12, weight="bold")
        ax2.text(
            0.15,
            y - 0.055,
            f"input present={row['input_present']}  size={row['input_size_bytes']} bytes",
            transform=ax2.transAxes,
            fontsize=8.5,
            color=COLORS["muted"],
        )
    ax2.text(
        0.02,
        0.08,
        "Commands are exported for the user; this generator did not execute K5/K6.",
        transform=ax2.transAxes,
        fontsize=9,
        color=COLORS["muted"],
    )
    _save(fig, out)


def _figure_specs(research: dict[str, Any]) -> tuple[FigureSpec, ...]:
    transfer = str(research.get("transfer_source", "mixed_none_and_external_transfer_conditioned"))
    null_status = "mixed_diagnostic_and_blocked"
    return (
        FigureSpec(
            artifact_id="common.v6_no_download_figures.component_source_matrix",
            file_name="fig_v6_component_source_matrix.png",
            title="Component-source matrix",
            source_card="component_source_matrix",
            null_mock_status=null_status,
            transfer_source=transfer,
            builder=_plot_component_source_matrix,
            caveats=(
                "Shows source/readiness status only.",
                "Fail-closed sectors are not zero-filled or promoted to scalar claims.",
                "No family identification or native low-ell solver output is represented.",
            ),
        ),
        FigureSpec(
            artifact_id="common.v6_no_download_figures.denominator_sensitivity",
            file_name="fig_v6_denominator_sensitivity.png",
            title="Denominator sensitivity",
            source_card="denominator_sensitivity_table",
            null_mock_status=null_status,
            transfer_source=transfer,
            builder=_plot_denominator_sensitivity,
            caveats=(
                "Q rows are denominator-policy sensitivity diagnostics only.",
                "External-transfer rows remain transfer-conditional.",
                "No calibrated exceedance probability is shown.",
            ),
        ),
        FigureSpec(
            artifact_id="common.v6_no_download_figures.response_class_ledger",
            file_name="fig_v6_response_class_ledger.png",
            title="Response-class ledger",
            source_card="response_class_ledger",
            null_mock_status="not_statistical",
            transfer_source="none",
            builder=_plot_response_class_ledger,
            caveats=(
                "Old figures are classified, not promoted.",
                "Legacy ranking/posterior labels are removed from current claim lanes.",
                "Counts are figure-governance metadata, not evidence.",
            ),
        ),
        FigureSpec(
            artifact_id="common.v6_no_download_figures.optical_ansatz_readiness",
            file_name="fig_v6_optical_ansatz_readiness.png",
            title="Optical-ansatz readiness",
            source_card="optical_ansatz_readiness",
            null_mock_status=null_status,
            transfer_source=transfer,
            builder=_plot_optical_ansatz_readiness,
            caveats=(
                "Readiness table only; no theory likelihood branch is certified.",
                "Central scalar low-ell summaries remain diagnostic.",
                "Matched E2E covariance/null gates remain blocking.",
            ),
        ),
        FigureSpec(
            artifact_id="common.v6_no_download_figures.depth_gap_and_readiness",
            file_name="fig_v6_depth_gap_and_readiness.png",
            title="Depth gap and K5/K6 readiness",
            source_card="depth_gap_card",
            null_mock_status=null_status,
            transfer_source=transfer,
            builder=_plot_depth_gap_and_readiness,
            caveats=(
                "G_F is a display contract/readiness diagnostic only.",
                "CF4 shell G_F is not attempted without matched covariance and calibrated nulls.",
                "K5/K6 commands are exported for user execution; this generator does not run them.",
            ),
        ),
    )


def _manifest_for_spec(spec: FigureSpec, figure_path: Path, command: str) -> dict[str, Any]:
    rel_path = _repo_relative(figure_path)
    manifest = {
        "artifact_id": spec.artifact_id,
        "artifact_path": rel_path,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "internal_exploratory",
        "allowed_use": "internal_only",
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_state_no_native_low_ell_solver_output",
            "must_state_no_family_identification",
            "must_state_no_k5_k6_execution_by_generator",
        ],
        "promotion_blockers": [
            "native_lowell_morphology_atlas_absent",
            "matched_e2e_or_cf4_nulls_not_bound",
        ],
        "created_by": "scripts/make_v6_no_download_figures.py",
        "git_commit": "content-addressed",
        "config_hash": _config_hash(
            {
                "artifact_id": spec.artifact_id,
                "file_name": spec.file_name,
                "source_card": spec.source_card,
                "source_hashes": _input_hashes(),
                "version": "v6-no-download-figures-v1",
            }
        ),
        "input_hashes": _input_hashes(),
        "code_version": "content-addressed",
        "schema_version": "common.v6_no_download_figure.v1",
        "caveats": list(spec.caveats),
        "required_gates": [
            "v6_no_download_cards_current",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
            "no_k5_k6_long_run_by_generator",
        ],
        "passed_gates": [
            "v6_no_download_cards_current",
            "manifest_metadata_present",
            "no_k5_k6_long_run_by_generator",
        ],
        "failed_gates": [],
        "statistics_definitions": {
            "v6_figure_lane": "quarantined_meta_v6_no_download",
            "source_card": spec.source_card,
            "source_artifacts": list(SOURCE_PATHS[:2]),
            "figure_title": spec.title,
        },
        "transfer_source": spec.transfer_source,
        "sky_support_status": "not_directional",
        "null_mock_status": spec.null_mock_status,
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
    }
    issues = validate_manifest_payload(
        manifest,
        manifest_path=figure_path.with_suffix(".manifest.json"),
        expected_artifact_path=rel_path,
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid manifest for {rel_path}: {rendered}")
    return manifest


def _sidecar_path(figure_path: Path) -> Path:
    return figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json")


def _write_sidecar(spec: FigureSpec, figure_path: Path, command: str) -> None:
    manifest = _manifest_for_spec(spec, figure_path, command)
    _sidecar_path(figure_path).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_commands_payload(command: str, research: dict[str, Any]) -> dict[str, Any]:
    feasibility = research["cards"]["k5_k6_next_turn_feasibility"]
    commands: dict[str, Any] = {}
    for lane, row in feasibility.items():
        script = str(row["script"])
        run_command = f"venv/bin/python {script}"
        commands[lane] = {
            "script": script,
            "input_path": row["input_path"],
            "input_present": row["input_present"],
            "input_size_bytes": row["input_size_bytes"],
            "next_turn_runnable": row["next_turn_runnable"],
            "expected_runtime_note": row["expected_runtime_note"],
            "run_command": run_command,
            "check_command": f"{run_command} --check",
            "report_back": [
                "terminal stdout tail",
                f"docs/generated/{'k5_cf4_release_coverage' if lane == 'K5' else 'k6_cf4_curl_posterior'}.json",
            ],
            "generator_executed_this_turn": False,
        }
    payload = {
        "artifact_id": "common.v6_k5_k6_user_commands",
        "artifact_path": _repo_relative(COMMANDS_JSON),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": research.get("transfer_source", "mixed_none_and_external_transfer_conditioned"),
        "sky_support_status": "not_directional",
        "null_mock_status": "mixed_diagnostic_and_blocked",
        "config_hash": _config_hash(
            {
                "commands": commands,
                "source_hashes": _input_hashes(),
                "version": "v6-k5-k6-user-commands-v1",
            }
        ),
        "input_hashes": _input_hashes(),
        "caveats": [
            "This artifact exports user-run commands only.",
            "The v6 figure generator did not run K5 or K6.",
            "K5/K6 outputs remain diagnostic-only and must retain their existing claim boundaries.",
        ],
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
        "execution_policy": "user_runs_commands_generator_did_not_execute_k5_k6",
        "commands": commands,
    }
    return payload


def render_commands_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# V6 K5/K6 User Commands",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        f"transfer_source: {payload['transfer_source']}",
        "sky_support_status: not_directional",
        "null_mock_status: mixed_diagnostic_and_blocked",
        f"config_hash: `{payload['config_hash']}`",
        "caveats:",
        "- Commands only; this generator did not execute K5 or K6.",
        "- Report stdout tail and the generated JSON path after running.",
        "- No native low-ell solver output or family-identification claim is produced.",
        f"generating_command: {payload['generating_command']}",
        "git_commit_or_worktree_state: content-addressed",
        "",
        "## Commands",
        "",
    ]
    for lane, row in payload["commands"].items():
        lines.extend(
            [
                f"### {lane}",
                "",
                f"- input: `{row['input_path']}`",
                f"- input_present: `{row['input_present']}`",
                f"- next_turn_runnable: `{row['next_turn_runnable']}`",
                f"- run: `{row['run_command']}`",
                f"- check after run: `{row['check_command']}`",
                f"- note: {row['expected_runtime_note']}",
                "",
            ]
        )
    return "\n".join(lines)


def build_pack_payload(
    command: str,
    research: dict[str, Any],
    legacy: dict[str, Any],
    specs: tuple[FigureSpec, ...],
) -> dict[str, Any]:
    figures = []
    for spec in specs:
        figure_path = FIGURE_DIR / spec.file_name
        figures.append(
            {
                "artifact_id": spec.artifact_id,
                "file_name": spec.file_name,
                "artifact_path": _repo_relative(figure_path),
                "manifest_path": _repo_relative(_sidecar_path(figure_path)),
                "source_card": spec.source_card,
                "claim_tier": "diagnostic_only",
                "allowed_use": "internal_only",
                "artifact_mode": "internal_exploratory",
            }
        )
    payload = {
        "artifact_id": "common.v6_no_download_figure_pack",
        "artifact_path": _repo_relative(PACK_JSON),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": research.get("transfer_source", "mixed_none_and_external_transfer_conditioned"),
        "sky_support_status": "not_directional",
        "null_mock_status": "mixed_diagnostic_and_blocked",
        "config_hash": _config_hash(
            {
                "figures": figures,
                "source_hashes": _input_hashes(),
                "research_config_hash": research.get("config_hash"),
                "legacy_config_hash": legacy.get("config_hash"),
                "version": "v6-no-download-figure-pack-v1",
            }
        ),
        "input_hashes": _input_hashes(),
        "caveats": [
            "Figure pack renders existing v6 no-download cards only.",
            "This is quarantined meta/internal-governance material and is not report-facing.",
            "No K1/K5/K6 long analysis is executed by this figure generator.",
            "No native low-ell solver output or Bianchi family-identification claim is represented.",
        ],
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
        "k5_k6_execution_policy": "commands_exported_for_user_not_run_by_generator",
        "report_use_policy": "not_report_facing_internal_meta_quarantine",
        "figures": figures,
        "commands_artifact": _repo_relative(COMMANDS_JSON),
    }
    return payload


def render_pack_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# V6 No-Download Figure Pack",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        f"transfer_source: {payload['transfer_source']}",
        "sky_support_status: not_directional",
        "null_mock_status: mixed_diagnostic_and_blocked",
        f"config_hash: `{payload['config_hash']}`",
        "caveats:",
        "- Existing v6 no-download cards are the only science input.",
        "- This pack is quarantined internal meta material, not a report figure lane.",
        "- K5/K6 commands are exported separately and are not executed here.",
        "- Figure use is internal-only unless the user explicitly asks for an internal audit appendix.",
        f"generating_command: {payload['generating_command']}",
        "git_commit_or_worktree_state: content-addressed",
        "",
        "## Figures",
        "",
        "| Figure | Source card | Manifest |",
        "| --- | --- | --- |",
    ]
    for row in payload["figures"]:
        lines.append(
            f"| `{row['artifact_path']}` | `{row['source_card']}` | `{row['manifest_path']}` |"
        )
    lines.extend(
        [
            "",
            "## K5/K6",
            "",
            f"- command artifact: `{payload['commands_artifact']}`",
            f"- execution policy: `{payload['k5_k6_execution_policy']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _expected_text_outputs(
    pack: dict[str, Any], commands: dict[str, Any]
) -> dict[Path, str]:
    return {
        PACK_JSON: json.dumps(pack, indent=2, sort_keys=True) + "\n",
        PACK_MD: render_pack_markdown(pack),
        COMMANDS_JSON: json.dumps(commands, indent=2, sort_keys=True) + "\n",
        COMMANDS_MD: render_commands_markdown(commands),
    }


def _expected_manifests(
    specs: tuple[FigureSpec, ...], command: str
) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for spec in specs:
        figure_path = FIGURE_DIR / spec.file_name
        manifest = _manifest_for_spec(spec, figure_path, command)
        outputs[_sidecar_path(figure_path)] = (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
    return outputs


def write_outputs(argv: list[str] | None) -> None:
    command = _command([] if argv is None else [arg for arg in argv if arg != "--check"])
    research = _load_json(RESEARCH_JSON)
    legacy = _load_json(LEGACY_JSON)
    specs = _figure_specs(research)
    commands = build_commands_payload(command, research)
    pack = build_pack_payload(command, research, legacy, specs)

    GEN.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        figure_path = FIGURE_DIR / spec.file_name
        spec.builder(figure_path, research, legacy)
        _write_sidecar(spec, figure_path, command)
    for path, text in _expected_text_outputs(pack, commands).items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {_repo_relative(PACK_JSON)}")
    print(f"wrote {_repo_relative(PACK_MD)}")
    print(f"wrote {_repo_relative(COMMANDS_JSON)}")
    print(f"wrote {_repo_relative(COMMANDS_MD)}")
    for spec in specs:
        print(f"wrote {_repo_relative(FIGURE_DIR / spec.file_name)}")


def check_outputs(argv: list[str] | None) -> int:
    command = _command([] if argv is None else [arg for arg in argv if arg != "--check"])
    research = _load_json(RESEARCH_JSON)
    legacy = _load_json(LEGACY_JSON)
    specs = _figure_specs(research)
    commands = build_commands_payload(command, research)
    pack = build_pack_payload(command, research, legacy, specs)

    stale: list[str] = []
    for path, expected in _expected_text_outputs(pack, commands).items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            stale.append(_repo_relative(path))
    for path, expected in _expected_manifests(specs, command).items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            stale.append(_repo_relative(path))
    for spec in specs:
        figure_path = FIGURE_DIR / spec.file_name
        if not figure_path.exists() or figure_path.stat().st_size == 0:
            stale.append(_repo_relative(figure_path))
    if stale:
        print("stale v6 no-download figure artifacts:", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1
    print("v6 no-download figure artifacts are current")
    return 0


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        return check_outputs(argv)
    write_outputs(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
