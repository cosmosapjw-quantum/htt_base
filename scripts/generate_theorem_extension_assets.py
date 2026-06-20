#!/usr/bin/env python3
"""Generate the REV-R084 theorem-extension registry assets."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
for import_root in (REPO_ROOT / "htt" / "src", REPO_ROOT / "htt"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from bass.geometry.egs_rigidity import (  # noqa: E402
    boosted_radiation_orbit,
    classify_slope_degeneracy,
)
from bass.kinetic.tight_coupling_bounds import angular_kl_multipole_bound  # noqa: E402
from bass.kinetic.visibility_rigidity import visibility_cancellation_no_go  # noqa: E402
from common.artifact_manifest import validate_manifest_payload  # noqa: E402
from common.theorem_registry import default_theorem_registry
from mio.formalism.dynamic_budget import dynamic_comparison_budget_barrier  # noqa: E402


DEFAULT_JSON = REPO_ROOT / "docs" / "generated" / "theorem_extension_registry.json"
DEFAULT_MARKDOWN = REPO_ROOT / "docs" / "generated" / "theorem_extension_registry.md"
THEOREM_FIGURE_DIR = REPO_ROOT / "figures" / "current"
THEOREM_APPENDIX_SNIPPET = (
    REPO_ROOT / "docs" / "manuscript" / "generated" / "theorem_extension_appendix_figures.tex"
)
SCHEMA_VERSION = "rev-r084.theorem_extension_registry.v1"
FIGURE_SOURCE_SCHEMA_VERSION = "rev-r085.theorem_appendix_figure_source.v1"
FIGURE_MANIFEST_SCHEMA_VERSION = "common.theorem_appendix_figure.v1"
SOURCE_PATHS = (
    REPO_ROOT / "scripts" / "generate_theorem_extension_assets.py",
    REPO_ROOT / "htt" / "src" / "common" / "theorem_registry.py",
    REPO_ROOT / "htt" / "mio" / "formalism" / "dynamic_budget.py",
    REPO_ROOT / "htt" / "mio" / "formalism" / "bound_pushforward.py",
    REPO_ROOT / "htt" / "bass" / "kinetic" / "boltzmann_memory.py",
    REPO_ROOT / "htt" / "bass" / "kinetic" / "tight_coupling_bounds.py",
    REPO_ROOT / "htt" / "bass" / "kinetic" / "visibility_rigidity.py",
    REPO_ROOT / "htt" / "bass" / "geometry" / "egs_rigidity.py",
    REPO_ROOT / "tests" / "contracts" / "test_theorem_registry.py",
    REPO_ROOT / "tests" / "mio" / "test_dynamic_budget.py",
    REPO_ROOT / "tests" / "bass" / "test_boltzmann_memory_bounds.py",
    REPO_ROOT / "tests" / "bass" / "test_egs_rigidity_theorems.py",
)
FIGURE_SOURCE_PATHS = (
    *SOURCE_PATHS,
    REPO_ROOT / "tests" / "contracts" / "test_theorem_extension_assets.py",
)
GLOBAL_CAVEATS = (
    "synthetic/manufactured verification only",
    "diagnostic-only",
    "not HTT evidence",
    "not a MIO certificate",
    "not native solver validation",
    "not geometry or family identification",
)
FIGURE_GLOBAL_CAVEATS = (
    "synthetic/manufactured input mode only",
    "appendix-only diagnostic figure",
    "not HTT evidence",
    "not a MIO certificate",
    "not native solver validation",
    "not geometry or family identification",
)


@dataclass(frozen=True)
class TheoremFigureSpec:
    stem: str
    theorem_id: str
    title: str
    owner: str
    implementation_scope: str
    caption: str
    label: str
    plotted_value_key: str
    forbidden_use: tuple[str, ...]
    promotion_blockers: tuple[str, ...]


THEOREM_FIGURE_SPECS = (
    TheoremFigureSpec(
        stem="fig_theorem_angular_kl_bound",
        theorem_id="S1",
        title="Angular KL Multipole Bound",
        owner="BASS",
        implementation_scope="bass_py",
        caption=(
            "Appendix-only synthetic angular KL multipole bound. The panel shows a "
            "manufactured density-fixture scaling and remains diagnostic-only; it is "
            "not HTT evidence, not a MIO certificate, not native solver validation, "
            "and not geometry or family identification."
        ),
        label="fig:theorem-angular-kl-bound",
        plotted_value_key="multipole_bound",
        forbidden_use=(
            "observed temperature multipole bound",
            "S2 observational use",
            "native solver validation",
            "geometry or family identification",
        ),
        promotion_blockers=(
            "unbounded_multipole_bridge_blocks_s2_observational_use",
            "harmonic_convention_not_bound_blocks_kl_bound_use",
        ),
    ),
    TheoremFigureSpec(
        stem="fig_theorem_dynamic_budget_barrier",
        theorem_id="S3",
        title="Dynamic Budget Barrier",
        owner="MIO",
        implementation_scope="mio",
        caption=(
            "Appendix-only synthetic dynamic budget barrier. The plotted margin is a "
            "same-channel manufactured comparison diagnostic; it is not HTT evidence, "
            "not a MIO certificate, not native solver validation, and not geometry or "
            "family identification."
        ),
        label="fig:theorem-dynamic-budget-barrier",
        plotted_value_key="barrier_margin",
        forbidden_use=(
            "observational denominator certification",
            "HTT likelihood evidence",
            "posterior odds",
            "geometry or family identification",
        ),
        promotion_blockers=(
            "collision_gap_nonpositive_blocks_exponential_forgetting_language",
            "channel_operator_mismatch_blocks_dynamic_budget_certification",
        ),
    ),
    TheoremFigureSpec(
        stem="fig_theorem_boosted_radiation_orbit",
        theorem_id="G2",
        title="Boosted Radiation Orbit Gate",
        owner="BASS",
        implementation_scope="bass_py",
        caption=(
            "Appendix-only synthetic boosted-radiation orbit gate. The curve is a "
            "manufactured Lorentz-orbit diagnostic and the data-facing residual gate "
            "remains blocked; it is not HTT evidence, not a MIO certificate, not "
            "native solver validation, and not geometry or family identification."
        ),
        label="fig:theorem-boosted-radiation-orbit",
        plotted_value_key="gamma_minus_one",
        forbidden_use=(
            "intrinsic geometry detection",
            "family ranking",
            "data-facing residual claim",
            "native solver validation",
        ),
        promotion_blockers=(
            "acceleration_temp_gradient_block_missing_blocks_flrw_egs_promotion",
            "derivative_weyl_diagnostics_missing_blocks_almost_egs_promotion",
            "bianchi_i_assumptions_missing_blocks_g4_exact_flow_use",
            "data_residual_provenance_not_bound_blocks_data_facing_residual",
        ),
    ),
    TheoremFigureSpec(
        stem="fig_theorem_slope_degeneracy",
        theorem_id="G5",
        title="Slope Degeneracy Gate",
        owner="BASS",
        implementation_scope="bass_py",
        caption=(
            "Appendix-only synthetic slope-degeneracy gate. The shaded band marks "
            "manufactured slope-only degeneracy, which blocks source discrimination; "
            "it is not HTT evidence, not a MIO certificate, not native solver "
            "validation, and not geometry or family identification."
        ),
        label="fig:theorem-slope-degeneracy",
        plotted_value_key="slope_difference",
        forbidden_use=(
            "slope-only source discrimination",
            "local/global origin ranking",
            "geometry or family identification",
        ),
        promotion_blockers=(
            "stiff_fluid_singularity_blocks_g3_inversion",
            "slope_degeneracy_blocks_slope_only_source_discrimination",
        ),
    ),
    TheoremFigureSpec(
        stem="fig_theorem_visibility_cancellation",
        theorem_id="B4",
        title="Visibility Cancellation Gate",
        owner="BASS",
        implementation_scope="bass_py",
        caption=(
            "Appendix-only synthetic visibility-cancellation gate. The bars show "
            "manufactured fail-closed source upper-bound conditions; it is not HTT "
            "evidence, not a MIO certificate, not native solver validation, and not "
            "geometry or family identification."
        ),
        label="fig:theorem-visibility-cancellation",
        plotted_value_key="source_upper_bound_allowed",
        forbidden_use=(
            "inverse source claim",
            "observed line-of-sight upper bound",
            "native solver validation",
            "geometry or family identification",
        ),
        promotion_blockers=(
            "collision_gap_nonpositive_blocks_exponential_forgetting_language",
            "source_rank_near_zero_blocks_inverse_source_claim",
            "line_of_sight_sign_phase_incoherence_blocks_source_upper_bound",
            "visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound",
        ),
    ),
)


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _path_hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{_display_path(path)}:{digest}"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_state() -> str:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "git_state_unavailable"
    return f"{commit}+dirty" if status else commit


def build_payload(
    *,
    generated_on: str | None = None,
    generating_command: str | None = None,
    git_state: str | None = None,
) -> dict[str, Any]:
    registry = default_theorem_registry()
    theorem_rows = registry.to_payload()
    input_hashes = [_path_hash(path) for path in SOURCE_PATHS]
    config_hash = _config_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "theorems": theorem_rows,
            "required_kill_switches": registry.required_kill_switches(),
            "source_paths": [_display_path(path) for path in SOURCE_PATHS],
            "input_hashes": input_hashes,
        }
    )
    command = generating_command or (
        f"{Path(sys.executable).as_posix()} scripts/generate_theorem_extension_assets.py --write"
    )
    return {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "owner": "COMMON",
            "implementation_scope": "common",
            "claim_tier": "diagnostic_only",
            "transfer_source": "none",
            "sky_support_status": "not_directional",
            "covariance_status": "synthetic_only",
            "null_mock_status": "synthetic_only",
            "production_status": "diagnostic_only",
            "artifact_role": "theorem_extension_registry",
            "production_claim_allowed": False,
            "observation_claim_allowed": False,
            "native_solver_result": False,
            "family_identification": False,
            "consumable_as_htt_evidence": False,
            "consumable_as_mio_certificate": False,
            "consumable_as_family_identification": False,
            "required_kill_switches": list(registry.required_kill_switches()),
            "blocked_observational_uses": registry.blocked_observational_uses(),
            "source_paths": [_display_path(path) for path in SOURCE_PATHS],
            "config_hash": config_hash,
            "input_hashes": input_hashes,
            "generated_on": generated_on
            or datetime.now(UTC).replace(microsecond=0).isoformat(),
            "generating_command": command,
            "git_commit_or_worktree_state": git_state or _git_state(),
            "caveats": list(GLOBAL_CAVEATS),
        },
        "theorems": theorem_rows,
    }


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


def render_markdown(payload: dict[str, Any]) -> str:
    metadata = payload["metadata"]
    lines = [
        "# Theorem Extension Registry",
        "",
        f"owner: {metadata['owner']}",
        f"implementation_scope: {metadata['implementation_scope']}",
        f"claim_tier: {metadata['claim_tier']}",
        f"transfer_source: {metadata['transfer_source']}",
        f"sky_support_status: {metadata['sky_support_status']}",
        f"covariance_status: {metadata['covariance_status']}",
        f"null_mock_status: {metadata['null_mock_status']}",
        f"native_solver_result: {str(metadata['native_solver_result']).lower()}",
        f"family_identification: {str(metadata['family_identification']).lower()}",
        f"config_hash: `{metadata['config_hash']}`",
        f"generated_on: `{metadata['generated_on']}`",
        f"generating_command: `{metadata['generating_command']}`",
        f"git_commit_or_worktree_state: `{metadata['git_commit_or_worktree_state']}`",
        "source_paths:",
    ]
    lines.extend(f"- `{path}`" for path in metadata["source_paths"])
    lines.extend(
        [
            "input_hashes:",
        ]
    )
    lines.extend(f"- `{digest}`" for digest in metadata["input_hashes"])
    lines.extend(
        [
            "caveats:",
        ]
    )
    lines.extend(f"- {caveat}" for caveat in metadata["caveats"])
    lines.extend(
        [
            "",
            "This registry is synthetic/manufactured verification only. It is diagnostic-only, not HTT evidence, not a MIO certificate, not native solver validation, and not geometry or family identification.",
            "",
            "| Theorem | Status | Proof Status | Implementation Test Status | Claim Status | Key Kill Switches |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in payload["theorems"]:
        switches = ", ".join(row["kill_switches"])
        lines.append(
            f"| {row['theorem_id']} | {row['status']} | {row['proof_status']} | "
            f"{row['implementation_test_status']} | {row['claim_status']} | {switches} |"
        )
    lines.extend(
        [
            "",
            "## Required Kill Switches",
            "",
        ]
    )
    lines.extend(f"- {switch}" for switch in metadata["required_kill_switches"])
    return "\n".join(lines) + "\n"


def _git_commit_from_state(git_state: str) -> str | None:
    if git_state == "git_state_unavailable":
        return None
    return git_state.split("+", 1)[0]


def _figure_paths(spec: TheoremFigureSpec) -> tuple[Path, Path, Path]:
    figure_path = THEOREM_FIGURE_DIR / f"{spec.stem}.png"
    source_path = THEOREM_FIGURE_DIR / f"{spec.stem}.source.json"
    manifest_path = THEOREM_FIGURE_DIR / f"{spec.stem}.manifest.json"
    return figure_path, source_path, manifest_path


def _source_hashes() -> list[str]:
    return [_path_hash(path) for path in FIGURE_SOURCE_PATHS]


def _theorem_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["theorem_id"]): row for row in payload["theorems"]}


def _synthetic_rows(spec: TheoremFigureSpec) -> tuple[dict[str, Any], ...]:
    if spec.theorem_id == "S1":
        rows = [
            angular_kl_multipole_bound(
                ell_max=ell,
                bridge_operator_norm=0.2,
                source_norm=0.3,
                theorem_id=spec.theorem_id,
            ).as_payload()
            for ell in (2, 4, 8, 12, 16, 20)
        ]
        rows.extend(
            [
                angular_kl_multipole_bound(
                    ell_max=8,
                    bridge_operator_norm=None,
                    source_norm=0.3,
                    theorem_id=spec.theorem_id,
                ).as_payload(),
                angular_kl_multipole_bound(
                    ell_max=8,
                    bridge_operator_norm=0.2,
                    source_norm=0.3,
                    theorem_id=spec.theorem_id,
                    harmonic_convention_status="not_bound",
                ).as_payload(),
                angular_kl_multipole_bound(
                    ell_max=8,
                    bridge_operator_norm=0.2,
                    source_norm=0.3,
                    theorem_id=spec.theorem_id,
                    density_positive=False,
                ).as_payload(),
            ]
        )
        return tuple(rows)
    if spec.theorem_id == "S3":
        rows = [
            dynamic_comparison_budget_barrier(
                initial_budget=0.2,
                forcing_envelope=0.1,
                damping_integral=damping,
                comparison_budget=0.6,
                collision_gap=0.4,
                theorem_id=spec.theorem_id,
            ).as_payload()
            for damping in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5)
        ]
        rows.extend(
            [
                dynamic_comparison_budget_barrier(
                    initial_budget=0.2,
                    forcing_envelope=0.1,
                    damping_integral=1.0,
                    comparison_budget=0.6,
                    collision_gap=0.0,
                    theorem_id=spec.theorem_id,
                ).as_payload(),
                dynamic_comparison_budget_barrier(
                    initial_budget=0.2,
                    forcing_envelope=0.1,
                    damping_integral=1.0,
                    comparison_budget=0.6,
                    collision_gap=0.4,
                    theorem_id=spec.theorem_id,
                    numerator_channel="TT",
                    budget_channel="EE",
                ).as_payload(),
                dynamic_comparison_budget_barrier(
                    initial_budget=0.4,
                    forcing_envelope=0.4,
                    damping_integral=0.4,
                    comparison_budget=0.2,
                    collision_gap=0.2,
                    theorem_id=spec.theorem_id,
                ).as_payload(),
            ]
        )
        return tuple(rows)
    if spec.theorem_id == "G2":
        return tuple(
            {
                **boosted_radiation_orbit(
                    beta=beta,
                    direction_norm=1.0,
                    theorem_id=spec.theorem_id,
                ).as_payload(),
                "gamma_minus_one": math.cosh(beta) - 1.0,
            }
            for beta in (0.0, 0.04, 0.08, 0.12, 0.16, 0.20)
        )
    if spec.theorem_id == "G5":
        rows = [
            classify_slope_degeneracy(
                slope_a=1.0,
                slope_b=1.0 + delta,
                tolerance=1.0e-4,
                equation_of_state_w=0.0,
                theorem_id=spec.theorem_id,
            ).as_payload()
            for delta in (0.0, 5.0e-5, 1.0e-4, 4.0e-4, 1.0e-3, 2.0e-3)
        ]
        rows.append(
            classify_slope_degeneracy(
                slope_a=1.0,
                slope_b=1.2,
                tolerance=1.0e-4,
                equation_of_state_w=1.0,
                theorem_id=spec.theorem_id,
            ).as_payload()
        )
        return tuple(rows)
    if spec.theorem_id == "B4":
        cases = (
            (
                "all_provenance_bound",
                visibility_cancellation_no_go(
                    source_rank=2,
                    line_of_sight_phase_coherent=True,
                    visibility_width=0.04,
                    theorem_id=spec.theorem_id,
                    collision_gap_status="positive_bound",
                    kernel_floor_status="positive_bound",
                    mask_support_status="bound",
                ).as_payload(),
            ),
            (
                "missing_gap_kernel_mask",
                visibility_cancellation_no_go(
                    source_rank=2,
                    line_of_sight_phase_coherent=True,
                    visibility_width=0.04,
                    theorem_id=spec.theorem_id,
                ).as_payload(),
            ),
            (
                "phase_incoherent",
                visibility_cancellation_no_go(
                    source_rank=2,
                    line_of_sight_phase_coherent=False,
                    visibility_width=0.04,
                    theorem_id=spec.theorem_id,
                ).as_payload(),
            ),
            (
                "rank_lost",
                visibility_cancellation_no_go(
                    source_rank=0,
                    line_of_sight_phase_coherent=True,
                    visibility_width=0.04,
                    theorem_id=spec.theorem_id,
                ).as_payload(),
            ),
        )
        return tuple({**payload, "case": label} for label, payload in cases)
    raise ValueError(f"no synthetic rows configured for theorem {spec.theorem_id}")


def _figure_config_hash(spec: TheoremFigureSpec, theorem: dict[str, Any], rows: tuple[dict[str, Any], ...]) -> str:
    return _config_hash(
        {
            "schema_version": FIGURE_SOURCE_SCHEMA_VERSION,
            "stem": spec.stem,
            "theorem_id": spec.theorem_id,
            "theorem_status": theorem["status"],
            "kill_switches": theorem["kill_switches"],
            "rows": rows,
            "caption": spec.caption,
            "promotion_blockers": spec.promotion_blockers,
        }
    )


def _build_figure_source_payload(
    spec: TheoremFigureSpec,
    theorem: dict[str, Any],
    *,
    generated_on: str,
    generating_command: str,
    git_state: str,
) -> dict[str, Any]:
    figure_path, source_path, manifest_path = _figure_paths(spec)
    rows = _synthetic_rows(spec)
    source_hashes = _source_hashes()
    source = {
        "schema_version": FIGURE_SOURCE_SCHEMA_VERSION,
        "artifact_id": f"common.theorem_appendix.{spec.stem}",
        "artifact_path": _display_path(figure_path),
        "source_json_path": _display_path(source_path),
        "manifest_path": _display_path(manifest_path),
        "theorem_id": spec.theorem_id,
        "theorem_title": theorem["title"],
        "theorem_status": theorem["status"],
        "proof_status": theorem["proof_status"],
        "implementation_test_status": theorem["implementation_test_status"],
        "claim_status": theorem["claim_status"],
        "owner": "COMMON",
        "implementation_scope": "common",
        "theorem_helper_owner": spec.owner,
        "theorem_helper_scope": spec.implementation_scope,
        "claim_tier": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "transfer_source": "none",
        "source_input_mode": "synthetic_manufactured",
        "production_status": "diagnostic_only",
        "production_claim_allowed": False,
        "observation_claim_allowed": False,
        "native_solver_result": False,
        "family_identification": False,
        "consumable_as_htt_evidence": False,
        "consumable_as_mio_certificate": False,
        "consumable_as_family_identification": False,
        "sky_support_status": "not_directional",
        "covariance_status": "synthetic_manufactured_only",
        "null_mock_status": "synthetic_manufactured_only",
        "plotted_value_key": spec.plotted_value_key,
        "rows": list(rows),
        "registry_assumptions": theorem["assumptions"],
        "kill_switches": list(dict.fromkeys([*theorem["kill_switches"], *spec.promotion_blockers])),
        "forbidden_use": list(spec.forbidden_use),
        "caption": spec.caption,
        "label": spec.label,
        "caption_policy": [
            "must_state_appendix_only",
            "must_state_synthetic_manufactured_inputs",
            "must_state_diagnostic_only",
            "must_state_no_htt_evidence",
            "must_state_no_mio_certificate",
            "must_state_no_native_solver_validation",
            "must_state_no_geometry_or_family_identification",
        ],
        "required_gates": [
            "theorem_registry_entry_present",
            "source_json_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "passed_gates": [
            "theorem_registry_entry_present",
            "source_json_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "failed_gates": list(spec.promotion_blockers),
        "promotion_blockers": list(spec.promotion_blockers),
        "caveats": list(FIGURE_GLOBAL_CAVEATS),
        "source_paths": [_display_path(path) for path in FIGURE_SOURCE_PATHS],
        "input_hashes": source_hashes,
        "config_hash": _figure_config_hash(spec, theorem, rows),
        "generated_on": generated_on,
        "generating_command": generating_command,
        "git_commit_or_worktree_state": git_state,
        "matplotlib_savefig_reference": "https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html",
    }
    return source


def _render_figure_source_json(source: dict[str, Any]) -> str:
    return json.dumps(source, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


def _plot_theorem_figure(source: dict[str, Any], figure_path: Path) -> None:
    rows = source["rows"]
    theorem_id = source["theorem_id"]
    fig, ax = plt.subplots(figsize=(6.6, 4.0), constrained_layout=True)
    ax.set_title(str(source["theorem_title"]), fontsize=11)
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("white")
    if theorem_id == "S1":
        valid = [row for row in rows if row.get("multipole_bound") is not None]
        ax.plot(
            [row["ell_max"] for row in valid],
            [row["multipole_bound"] for row in valid],
            color="#0f766e",
            marker="o",
            linewidth=2.0,
        )
        ax.set_xlabel(r"$\ell_{\max}$")
        ax.set_ylabel("synthetic bound")
    elif theorem_id == "S3":
        valid = [row for row in rows if row.get("barrier_margin") is not None]
        ax.axhline(0.0, color="#475569", linewidth=1.0)
        ax.plot(
            [row["collision_gap"] * idx for idx, row in enumerate(valid)],
            [row["barrier_margin"] for row in valid],
            color="#7c2d12",
            marker="o",
            linewidth=2.0,
        )
        ax.set_xlabel("synthetic damping index")
        ax.set_ylabel("comparison margin")
    elif theorem_id == "G2":
        ax.plot(
            [row["beta"] for row in rows],
            [row["gamma_minus_one"] for row in rows],
            color="#6d28d9",
            marker="o",
            linewidth=2.0,
        )
        ax.set_xlabel(r"synthetic $\beta$")
        ax.set_ylabel(r"$\gamma-1$")
    elif theorem_id == "G5":
        ax.axhspan(0.0, 1.0e-4, color="#fde68a", alpha=0.5, label="degeneracy band")
        ax.scatter(
            list(range(len(rows))),
            [row["slope_difference"] for row in rows],
            color="#b45309",
            s=42,
        )
        ax.set_xlabel("synthetic slope case")
        ax.set_ylabel("absolute slope difference")
        ax.legend(loc="upper left", fontsize=8)
    elif theorem_id == "B4":
        ax.bar(
            [row["case"] for row in rows],
            [1.0 if row["source_upper_bound_allowed"] else 0.0 for row in rows],
            color=["#15803d" if row["source_upper_bound_allowed"] else "#b91c1c" for row in rows],
        )
        ax.set_ylim(0.0, 1.15)
        ax.set_ylabel("synthetic gate open")
        ax.tick_params(axis="x", labelrotation=25)
    else:
        raise ValueError(f"unsupported theorem figure {theorem_id}")
    ax.grid(True, alpha=0.25, linewidth=0.8)
    ax.text(
        0.01,
        0.01,
        "synthetic/manufactured; appendix-only; no native/family claim",
        transform=ax.transAxes,
        fontsize=7.5,
        color="#334155",
        va="bottom",
    )
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        figure_path,
        dpi=160,
        bbox_inches="tight",
        metadata={
            "Title": str(source["theorem_title"]),
            "Description": "synthetic/manufactured appendix-only theorem diagnostic",
            "Software": "htt_base scripts/generate_theorem_extension_assets.py",
        },
    )
    plt.close(fig)


def _manifest_for_figure_source(source: dict[str, Any], figure_sha256: str, source_sha256: str) -> dict[str, Any]:
    manifest = {
        "artifact_id": source["artifact_id"],
        "artifact_path": source["artifact_path"],
        "source_json_path": source["source_json_path"],
        "theorem_id": source["theorem_id"],
        "theorem_title": source["theorem_title"],
        "owner": source["owner"],
        "implementation_scope": source["implementation_scope"],
        "claim_tier": source["claim_tier"],
        "production_status": source["production_status"],
        "artifact_mode": source["artifact_mode"],
        "allowed_use": source["allowed_use"],
        "caption_policy": source["caption_policy"],
        "promotion_blockers": source["promotion_blockers"],
        "created_by": "scripts/generate_theorem_extension_assets.py",
        "git_commit": _git_commit_from_state(str(source["git_commit_or_worktree_state"])),
        "config_hash": source["config_hash"],
        "input_hashes": [*source["input_hashes"], f"{source['source_json_path']}:{source_sha256}"],
        "code_version": source["git_commit_or_worktree_state"],
        "schema_version": FIGURE_MANIFEST_SCHEMA_VERSION,
        "caveats": source["caveats"],
        "required_gates": source["required_gates"],
        "passed_gates": source["passed_gates"],
        "failed_gates": source["failed_gates"],
        "statistics_definitions": {
            "source_input_mode": source["source_input_mode"],
            "theorem_id": source["theorem_id"],
            "plotted_value_key": source["plotted_value_key"],
            "source_json_path": source["source_json_path"],
            "forbidden_use": source["forbidden_use"],
            "row_count": len(source["rows"]),
            "artifact_sha256": figure_sha256,
        },
        "transfer_source": source["transfer_source"],
        "sky_support_status": source["sky_support_status"],
        "covariance_status": source["covariance_status"],
        "null_mock_status": source["null_mock_status"],
        "generating_command": source["generating_command"],
        "git_commit_or_worktree_state": source["git_commit_or_worktree_state"],
        "native_solver_result": source["native_solver_result"],
        "family_identification": source["family_identification"],
    }
    issues = validate_manifest_payload(
        manifest,
        manifest_path=source["manifest_path"],
        expected_artifact_path=str(source["artifact_path"]),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid theorem figure manifest for {source['artifact_path']}: {rendered}")
    return manifest


def _render_manifest_json(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


def _render_appendix_snippet(sources: Sequence[dict[str, Any]]) -> str:
    lines = [
        "% Generated by scripts/generate_theorem_extension_assets.py.",
        "% Do not edit figure paths by hand; regenerate instead.",
        "% Theorem extension appendix figures.",
        "% Contains only assets whose manifest allowed_use is paper_appendix.",
        "",
    ]
    for source in sources:
        include_path = Path(str(source["artifact_path"])).with_suffix("")
        if include_path.parts and include_path.parts[0] == "figures":
            include_path = Path(*include_path.parts[1:])
        lines.extend(
            [
                "\\begin{figure}[htbp]",
                "\\centering",
                f"\\includegraphics[width=0.92\\textwidth]{{{include_path.as_posix()}}}",
                f"\\caption{{{source['caption']}}}",
                f"\\label{{{source['label']}}}",
                "\\end{figure}",
                "",
            ]
        )
    return "\n".join(lines)


def _write_theorem_figure_assets(payload: dict[str, Any]) -> None:
    meta = payload["metadata"]
    by_id = _theorem_by_id(payload)
    sources: list[dict[str, Any]] = []
    THEOREM_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for spec in THEOREM_FIGURE_SPECS:
        source = _build_figure_source_payload(
            spec,
            by_id[spec.theorem_id],
            generated_on=str(meta["generated_on"]),
            generating_command=str(meta["generating_command"]),
            git_state=str(meta["git_commit_or_worktree_state"]),
        )
        figure_path, source_path, manifest_path = _figure_paths(spec)
        _plot_theorem_figure(source, figure_path)
        source_path.write_text(_render_figure_source_json(source), encoding="utf-8")
        manifest = _manifest_for_figure_source(
            source,
            figure_sha256=_sha256_file(figure_path),
            source_sha256=_sha256_file(source_path),
        )
        manifest_path.write_text(_render_manifest_json(manifest), encoding="utf-8")
        sources.append(source)
    THEOREM_APPENDIX_SNIPPET.parent.mkdir(parents=True, exist_ok=True)
    THEOREM_APPENDIX_SNIPPET.write_text(_render_appendix_snippet(sources), encoding="utf-8")


def _check_theorem_figure_assets(expected_registry_payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    meta = expected_registry_payload["metadata"]
    by_id = _theorem_by_id(expected_registry_payload)
    expected_sources: list[dict[str, Any]] = []
    for spec in THEOREM_FIGURE_SPECS:
        figure_path, source_path, manifest_path = _figure_paths(spec)
        if not figure_path.exists():
            issues.append(f"{_display_path(figure_path)} is missing")
            continue
        if not source_path.exists():
            issues.append(f"{_display_path(source_path)} is missing")
            continue
        if not manifest_path.exists():
            issues.append(f"{_display_path(manifest_path)} is missing")
            continue
        expected_source = _build_figure_source_payload(
            spec,
            by_id[spec.theorem_id],
            generated_on=str(meta["generated_on"]),
            generating_command=str(meta["generating_command"]),
            git_state=str(meta["git_commit_or_worktree_state"]),
        )
        expected_source_text = _render_figure_source_json(expected_source)
        if source_path.read_text(encoding="utf-8") != expected_source_text:
            issues.append(f"{_display_path(source_path)} is stale")
            continue
        expected_manifest = _manifest_for_figure_source(
            expected_source,
            figure_sha256=_sha256_file(figure_path),
            source_sha256=hashlib.sha256(expected_source_text.encode("utf-8")).hexdigest(),
        )
        if manifest_path.read_text(encoding="utf-8") != _render_manifest_json(expected_manifest):
            issues.append(f"{_display_path(manifest_path)} is stale")
        expected_sources.append(expected_source)
    if not THEOREM_APPENDIX_SNIPPET.exists():
        issues.append(f"{_display_path(THEOREM_APPENDIX_SNIPPET)} is missing")
    else:
        expected_snippet = _render_appendix_snippet(expected_sources)
        if THEOREM_APPENDIX_SNIPPET.read_text(encoding="utf-8") != expected_snippet:
            issues.append(f"{_display_path(THEOREM_APPENDIX_SNIPPET)} is stale")
    return issues


def write_assets(json_path: Path, markdown_path: Path, payload: dict[str, Any]) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(render_json(payload), encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    if json_path == DEFAULT_JSON and markdown_path == DEFAULT_MARKDOWN:
        _write_theorem_figure_assets(payload)


def check_assets(json_path: Path, markdown_path: Path) -> tuple[bool, list[str]]:
    if not json_path.exists() or not markdown_path.exists():
        return False, ["generated theorem extension assets are missing"]
    current_payload = json.loads(json_path.read_text(encoding="utf-8"))
    current_meta = current_payload.get("metadata", {})
    expected = build_payload(
        generated_on=current_meta.get("generated_on"),
        generating_command=current_meta.get("generating_command"),
        git_state=current_meta.get("git_commit_or_worktree_state"),
    )
    issues: list[str] = []
    if json_path.read_text(encoding="utf-8") != render_json(expected):
        issues.append(f"{_display_path(json_path)} is stale")
    if markdown_path.read_text(encoding="utf-8") != render_markdown(expected):
        issues.append(f"{_display_path(markdown_path)} is stale")
    if json_path == DEFAULT_JSON and markdown_path == DEFAULT_MARKDOWN:
        issues.extend(_check_theorem_figure_assets(expected))
    return not issues, issues


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated JSON and Markdown assets.")
    parser.add_argument("--check", action="store_true", help="Check generated JSON and Markdown assets for drift.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--generated-on", default=None)
    parser.add_argument("--git-state", default=None)
    args = parser.parse_args(argv)
    command = f"{Path(sys.executable).as_posix()} scripts/generate_theorem_extension_assets.py {' '.join(sys.argv[1:])}".rstrip()
    if args.check:
        ok, issues = check_assets(args.json_output, args.markdown_output)
        if not ok:
            for issue in issues:
                print(issue, file=sys.stderr)
            return 1
        print("theorem extension assets are current")
        return 0
    payload = build_payload(
        generated_on=args.generated_on,
        generating_command=command,
        git_state=args.git_state,
    )
    if args.write:
        write_assets(args.json_output, args.markdown_output, payload)
        print(f"wrote {args.json_output}")
        print(f"wrote {args.markdown_output}")
        return 0
    print(render_json(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
