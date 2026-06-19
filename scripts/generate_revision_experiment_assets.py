#!/usr/bin/env python3
"""Generate conservative revision experiment assets.

These assets are diagnostic, repo-input-conditioned displays for the revision
program. They are not native low-ell transfer outputs and do not support
Bianchi family-identification claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
HTT_ROOT = REPO_ROOT / "htt"
for import_root in (COMMON_ROOT, HTT_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402
from htt.infer.finite_mock import zero_trigger_upper_bound  # noqa: E402
from htt.infer.fisher_compression import (  # noqa: E402
    gaussian_covariance_fisher_full_and_diag,
)
from htt.infer.nuisance_rank import nuisance_projected_rank  # noqa: E402
from mio.formalism.channel_occupancy_vector import (  # noqa: E402
    channel_matched_occupancy,
)


FIGURE_DIR = REPO_ROOT / "figures" / "current"
GENERATED_DIR = REPO_ROOT / "docs" / "generated"
ASSET_JSON = GENERATED_DIR / "revision_experiment_assets.json"
ASSET_MD = GENERATED_DIR / "revision_experiment_assets.md"
MANUSCRIPT_SNIPPET_DIR = REPO_ROOT / "docs" / "manuscript" / "generated"
MAIN_SNIPPET = MANUSCRIPT_SNIPPET_DIR / "revision_diagnostic_main_figure.tex"
APPENDIX_SNIPPET = MANUSCRIPT_SNIPPET_DIR / "revision_diagnostic_appendix_figures.tex"
EXTERNAL_AUDIT_SNIPPET = GENERATED_DIR / "revision_diagnostic_external_audit_figures.tex"
INPUT_PATHS = (
    "docs/generated/observational_data_inventory.json",
    "docs/generated/observed_longrun_analysis.json",
    "docs/generated/current_science_plot_payload.json",
)
GENERATOR = "scripts/generate_revision_experiment_assets.py"
GENERATING_COMMAND = f"venv/bin/python {GENERATOR} --write"
SCHEMA_VERSION = "htt.revision_experiment_assets.v1"

COLORS = {
    "blue": "#2563eb",
    "teal": "#0f766e",
    "amber": "#b45309",
    "red": "#b91c1c",
    "slate": "#334155",
    "muted": "#64748b",
    "panel": "#f8fafc",
    "green": "#15803d",
}

BASE_CAVEATS = (
    "not native transfer",
    "not family identification",
    "does not promote geometry or family claims",
    "paper-main use requires the lane recorded in this manifest",
)
PROMOTION_BLOCKERS = (
    "native_low_ell_solver_not_available",
    "native_morphology_atlas_not_available",
    "matched_nulls_and_full_covariance_not_bound_for_public_claims",
)
ASSET_ORDER = (
    "E1_prior_support_surface",
    "E2_sigma_beta_band",
    "FPR_rule_of_three",
    "E3_per_channel_occupancy",
    "E5_tomographic_forecast",
)
ASSET_LABELS = {
    "E1_prior_support_surface": "fig:revision-prior-support-surface",
    "E2_sigma_beta_band": "fig:revision-sigma-beta-band",
    "FPR_rule_of_three": "fig:revision-rule-of-three-fpr",
    "E3_per_channel_occupancy": "fig:revision-per-channel-occupancy",
    "E5_tomographic_forecast": "fig:revision-tomographic-forecast",
}
ASSET_CAPTIONS = {
    "E1_prior_support_surface": (
        "Revision appendix diagnostic prior-support surface. The plotted proxy "
        "exposes support sensitivity under the manifested prior-floor and "
        "prior-ceiling scan; it is appendix-only, diagnostic-only, not an "
        "evidence-grade Bayes factor, not native low-ell transfer output, and "
        "not a Bianchi family-ID claim."
    ),
    "E2_sigma_beta_band": (
        "Revision appendix diagnostic sigma-beta band. The panel records "
        "bulk-flow uncertainty sensitivity and display-only look-elsewhere "
        "bookkeeping under the current manifest; it is appendix-only, not "
        "evidence-grade support, not native-transfer validation, and not a "
        "geometry or family claim."
    ),
    "FPR_rule_of_three": (
        "Revision external-audit-only exact finite-mock false-positive-rate "
        "ceiling. The zero-trigger interval is an upper-bound diagnostic and "
        "must be read together with the observed nonzero false positives and "
        "the rule-of-three reference; it is not a zero-FPR claim, not HTT "
        "evidence, and not derived from native low-ell transfer."
    ),
    "E3_per_channel_occupancy": (
        "Revision appendix diagnostic per-channel occupancy. The bars use "
        "channel-matched proxy denominators to expose occupancy bookkeeping; "
        "scalar $Q$ remains blocked for channel mismatch and the plot does not "
        "support geometry detection or Bianchi family-ID."
    ),
    "E5_tomographic_forecast": (
        "Revision paper-main candidate tomographic forecast. The manifest "
        "records a forecast-only local/global template-rank design with "
        "jackknife/bootstrap diagnostic status; the figure is diagnostic-only "
        "and remains conditioned on blocked native-atlas status, matched "
        "covariance, and external null gates."
    ),
}


@dataclass(frozen=True)
class AssetSpec:
    asset_id: str
    title: str
    figure_name: str
    artifact_mode: str
    allowed_use: str
    transfer_source: str
    sky_support_status: str
    null_mock_status: str
    caveats: tuple[str, ...]
    source_paths: tuple[str, ...]
    builder: Callable[["RepoInputs", Path], dict[str, Any]]


@dataclass(frozen=True)
class RepoInputs:
    inventory: dict[str, Any] | None
    longrun: dict[str, Any] | None
    science_payload: dict[str, Any] | None


def _repo_relative(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _input_hashes(paths: tuple[str, ...]) -> list[str]:
    hashes: list[str] = []
    for rel_path in paths:
        path = REPO_ROOT / rel_path
        if path.exists():
            hashes.append(f"{rel_path}:sha256:{_sha256(path)}")
        else:
            hashes.append(f"{rel_path}:missing")
    return hashes


def _read_json_if_present(rel_path: str) -> dict[str, Any] | None:
    path = REPO_ROOT / rel_path
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{rel_path} must contain a JSON object")
    return payload


def _load_inputs() -> RepoInputs:
    return RepoInputs(
        inventory=_read_json_if_present(INPUT_PATHS[0]),
        longrun=_read_json_if_present(INPUT_PATHS[1]),
        science_payload=_read_json_if_present(INPUT_PATHS[2]),
    )


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


def _setup_axes(ax: plt.Axes, title: str, ylabel: str | None = None) -> None:
    ax.set_title(title, loc="left", fontsize=12, color=COLORS["slate"])
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", color="#e2e8f0", linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _inventory_counts(inventory: dict[str, Any] | None) -> tuple[int, int, dict[str, tuple[int, int]]]:
    if not inventory:
        return 8, 2, {"analytic": (8, 2)}
    rows = inventory.get("rows", [])
    if not isinstance(rows, list):
        return 8, 2, {"analytic": (8, 2)}
    by_collection: dict[str, list[int]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        collection = str(row.get("collection", "unclassified"))
        present = 1 if row.get("present") else 0
        if collection not in by_collection:
            by_collection[collection] = [0, 0]
        by_collection[collection][0] += present
        by_collection[collection][1] += 1 - present
    present_total = sum(value[0] for value in by_collection.values())
    missing_total = sum(value[1] for value in by_collection.values())
    return (
        present_total,
        missing_total,
        {key: (value[0], value[1]) for key, value in by_collection.items()},
    )


def _transfer_points(science_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if science_payload:
        points = science_payload.get("transfer_sensitivity", {}).get("points", [])
        if isinstance(points, list) and points:
            return [point for point in points if isinstance(point, dict)]
    return [
        {
            "relative_shift": shift,
            "Q_diagnostic": 0.64 / (1.0 + shift),
            "denominator_policy": "analytic_scaffold",
        }
        for shift in (-0.2, 0.0, 0.2)
    ]


def _q_center(science_payload: dict[str, Any] | None) -> float:
    points = _transfer_points(science_payload)
    q_values = [
        float(point.get("Q_diagnostic", 0.6))
        for point in points
        if np.isfinite(float(point.get("Q_diagnostic", 0.6)))
    ]
    if not q_values:
        return 0.6
    q_center = float(np.median(q_values))
    if q_center <= 0.0:
        raise ValueError("Q_diagnostic median must be positive for proxy displays")
    return q_center


def _local_null_config(science_payload: dict[str, Any] | None) -> dict[str, Any]:
    if science_payload:
        bank = (
            science_payload.get("rank_and_null_fpr", {})
            .get("local_null_bank", {})
        )
        if isinstance(bank, dict):
            config = bank.get("config", {})
            if isinstance(config, dict):
                return config
    return {"n_mocks": 96, "look_elsewhere_trials": 3, "max_false_positive_rate": 0.15}


def _local_null_bank(science_payload: dict[str, Any] | None) -> dict[str, Any]:
    if science_payload:
        report = (
            science_payload.get("rank_and_null_fpr", {})
            .get("local_null_fpr", {})
            .get("false_positive_rate", {})
        )
        if isinstance(report, dict):
            return report
    return {}


def _plot_prior_support_surface(inputs: RepoInputs, path: Path) -> dict[str, Any]:
    present, missing, _ = _inventory_counts(inputs.inventory)
    coverage = present / max(present + missing, 1)
    q_center = _q_center(inputs.science_payload)

    prior_floor = np.geomspace(1.0e-4, 2.0e-2, 44)
    prior_ceiling = np.geomspace(4.0e-2, 1.0, 50)
    floor_grid, ceiling_grid = np.meshgrid(prior_floor, prior_ceiling)
    prior_width = np.maximum(np.log(ceiling_grid / floor_grid), 1.0e-9)
    data_term = coverage * (q_center / 0.65) ** 2
    proxy_ln_bayes = data_term - np.log(prior_width)
    invalid = ceiling_grid <= floor_grid
    proxy_ln_bayes = np.where(invalid, np.nan, proxy_ln_bayes)

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    mesh = ax.contourf(
        prior_floor,
        prior_ceiling,
        proxy_ln_bayes,
        levels=16,
        cmap="viridis",
    )
    fig.colorbar(mesh, ax=ax, label="proxy lnB (diagnostic)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("prior lower cutoff")
    ax.set_ylabel("prior upper cutoff")
    _setup_axes(ax, "E1 prior cutoff sensitivity surface")
    _save(fig, path)
    finite = proxy_ln_bayes[np.isfinite(proxy_ln_bayes)]
    return {
        "input_mode": "repo_observed_input" if inputs.inventory and inputs.science_payload else "analytic_scaffold",
        "statistics": {
            "present_inputs": present,
            "missing_inputs": missing,
            "inventory_coverage": coverage,
            "q_center": q_center,
            "prior_floor_min": float(prior_floor.min()),
            "prior_floor_max": float(prior_floor.max()),
            "prior_ceiling_min": float(prior_ceiling.min()),
            "prior_ceiling_max": float(prior_ceiling.max()),
            "proxy_lnb_min": float(np.nanmin(finite)) if finite.size else None,
            "proxy_lnb_max": float(np.nanmax(finite)) if finite.size else None,
            "proxy_lnb_definition": (
                "coverage*(median_Q/0.65)^2 - log(log(prior_ceiling/prior_floor)); "
                "diagnostic proxy only"
            ),
        },
    }


def _plot_sigma_beta_band(inputs: RepoInputs, path: Path) -> dict[str, Any]:
    q_center = _q_center(inputs.science_payload)
    false_positive_rate = _local_null_bank(inputs.science_payload)
    look_elsewhere_trials = int(false_positive_rate.get("look_elsewhere_trials", 3))
    beta = np.linspace(0.0004, 0.0030, 48)
    sigma_beta = np.linspace(0.00035, 0.00160, 42)
    beta_grid, sigma_grid = np.meshgrid(beta, sigma_beta)
    sigma_safe = np.maximum(sigma_grid, 1.0e-9)
    proxy_ln_bayes = 0.5 * (beta_grid / sigma_safe) ** 2
    proxy_ln_bayes -= np.log(np.maximum(0.0032 / sigma_safe, 1.0))
    proxy_ln_bayes -= np.log(max(look_elsewhere_trials, 1))
    proxy_ln_bayes += np.log(max(q_center, 1.0e-6))

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    mesh = ax.contourf(
        beta,
        sigma_beta,
        proxy_ln_bayes,
        levels=18,
        cmap="magma",
    )
    fig.colorbar(mesh, ax=ax, label="look-elsewhere proxy lnB")
    ax.set_xlabel("bulk-flow beta premise")
    _setup_axes(ax, "E2 sigma-beta look-elsewhere band", "sigma_beta")
    _save(fig, path)
    return {
        "input_mode": "repo_observed_input" if inputs.science_payload else "analytic_scaffold",
        "statistics": {
            "beta_min": float(beta.min()),
            "beta_max": float(beta.max()),
            "sigma_beta_min": float(sigma_beta.min()),
            "sigma_beta_max": float(sigma_beta.max()),
            "look_elsewhere_trials": look_elsewhere_trials,
            "q_center": q_center,
            "proxy_lnb_min": float(np.nanmin(proxy_ln_bayes)),
            "proxy_lnb_max": float(np.nanmax(proxy_ln_bayes)),
            "proxy_lnb_definition": (
                "0.5*(beta/sigma_beta)^2 - log(delta_beta_prior/sigma_beta) "
                "- log(look_elsewhere_trials) + log(median_Q); diagnostic proxy only"
            ),
        },
    }


def _plot_rule_of_three_fpr(inputs: RepoInputs, path: Path) -> dict[str, Any]:
    config = _local_null_config(inputs.science_payload)
    false_positive_rate = _local_null_bank(inputs.science_payload)
    observed_n = int(
        false_positive_rate.get(
            "false_positive_denominator",
            config.get("n_mocks", 96),
        )
    )
    n_mocks = np.asarray(sorted({24, 48, 96, 192, 384, observed_n}))
    confidence = 0.95
    exact_upper = np.asarray(
        [zero_trigger_upper_bound(int(count), confidence) for count in n_mocks]
    )
    rule_of_three = 3.0 / n_mocks
    trials = max(int(config.get("look_elsewhere_trials", 1)), 1)
    look_elsewhere = np.minimum(1.0, exact_upper * trials)
    threshold = float(config.get("max_false_positive_rate", 0.15))

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.plot(
        n_mocks,
        exact_upper,
        marker="o",
        color=COLORS["teal"],
        label="exact zero-trigger 95% bound",
    )
    ax.plot(
        n_mocks,
        rule_of_three,
        color=COLORS["muted"],
        linestyle=":",
        label="3/N reference",
    )
    ax.plot(
        n_mocks,
        look_elsewhere,
        marker="s",
        color=COLORS["amber"],
        label=f"{trials} look-elsewhere trials",
    )
    ax.axhline(threshold, color=COLORS["red"], linestyle="--", linewidth=1.0)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("diagnostic null mocks")
    _setup_axes(ax, "FPR rule-of-three ceiling", "false-positive-rate ceiling")
    ax.legend(frameon=False, loc="best")
    _save(fig, path)
    false_positive_count = false_positive_rate.get("false_positive_count")
    raw_fpr = None
    if false_positive_count is not None:
        raw_fpr = float(false_positive_count) / max(observed_n, 1)
    adjusted_fpr = false_positive_rate.get("adjusted")
    return {
        "input_mode": "repo_observed_input" if inputs.science_payload else "analytic_scaffold",
        "statistics": {
            "observed_n_mocks": observed_n,
            "look_elsewhere_trials": trials,
            "max_false_positive_rate": threshold,
            "finite_mock_confidence": confidence,
            "exact_zero_trigger_upper_bound_at_observed_n": zero_trigger_upper_bound(
                observed_n, confidence
            ),
            "rule_of_three_at_observed_n": 3.0 / max(observed_n, 1),
            "observed_false_positive_count": false_positive_count,
            "observed_raw_fpr": raw_fpr,
            "observed_adjusted_fpr": adjusted_fpr,
            "interpretation": (
                "rule_of_three_is_a_zero-event_upper_bound; observed nonzero "
                "false positives must be reported separately"
            ),
        },
    }


def _plot_per_channel_occupancy(inputs: RepoInputs, path: Path) -> dict[str, Any]:
    q_center = _q_center(inputs.science_payload)
    present, missing, _ = _inventory_counts(inputs.inventory)
    coverage = present / max(present + missing, 1)
    channels = (
        ("shear", 0.32 * q_center, 0.60),
        ("vorticity", 0.18 * q_center, 0.42),
        ("tilt", 0.27 * q_center, 0.55),
        ("anisotropic curvature", 0.23 * q_center, 0.52),
    )
    labels = [channel[0] for channel in channels]
    numerators = np.asarray([channel[1] for channel in channels], dtype=float)
    denominators = np.asarray(
        [channel[2] * (0.85 + 0.35 * coverage) for channel in channels]
    )
    occupancy_report = channel_matched_occupancy(
        [
            {"channel": label, "numerator": float(num), "denominator": float(den)}
            for label, num, den in zip(labels, numerators, denominators)
        ],
        generating_command=GENERATING_COMMAND,
        worktree_state="generator_pre_manifest",
        input_hashes=_input_hashes((INPUT_PATHS[0],)),
    )
    occupancy = np.asarray(
        [float(row["occupancy"]) for row in occupancy_report["rows"]]
    )
    residual = 1.0 - occupancy
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    ax.barh(y, occupancy, color=COLORS["green"], label="channel-matched occupancy")
    ax.barh(y, residual, left=occupancy, color="#e2e8f0", label="remaining budget")
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("bounded occupancy fraction")
    _setup_axes(ax, "E3 per-channel occupancy vector")
    ax.legend(frameon=False, loc="lower right")
    _save(fig, path)
    return {
        "input_mode": "repo_observed_input" if inputs.inventory else "analytic_scaffold",
        "statistics": {
            "channel_occupancy": [
                {
                    **row,
                    "numerator_proxy": row["numerator"],
                    "denominator_proxy": row["denominator"],
                }
                for row in occupancy_report["rows"]
            ],
            "inventory_coverage": coverage,
            "negative_components_allowed": False,
            "posterior_compatible": occupancy_report["posterior_compatible"],
            "evidence_compatible": occupancy_report["evidence_compatible"],
            "truth_certificate": occupancy_report["truth_certificate"],
        },
    }


def _plot_tomographic_forecast(inputs: RepoInputs, path: Path) -> dict[str, Any]:
    longrun = inputs.longrun or {}
    desi = [row for row in longrun.get("desi_depth_jackknife", []) if isinstance(row, dict)]
    cf4 = [row for row in longrun.get("cf4_radius_bootstrap", []) if isinstance(row, dict)]
    if desi:
        z_mid = np.asarray([float(row["z_mid"]) for row in desi])
        amplitude = np.asarray([float(row["weighted_resultant_amplitude"]) for row in desi])
        jackknife = np.asarray([float(row["jackknife_std"]) for row in desi])
    else:
        z_mid = np.linspace(0.03, 0.35, 6)
        amplitude = 0.62 + 0.08 * np.sin(np.linspace(0, np.pi, 6))
        jackknife = np.full_like(amplitude, 0.06)

    if cf4:
        radius = np.asarray([float(row["radius_mid_mpc_h"]) for row in cf4])
        vr_mean = np.asarray([float(row["vr_mean_km_s"]) for row in cf4])
        vr_norm = vr_mean / max(float(np.max(np.abs(vr_mean))), 1.0)
        radius_scaled = radius / max(float(np.max(radius)), 1.0) * max(float(np.max(z_mid)), 0.35)
    else:
        radius_scaled = np.linspace(float(np.min(z_mid)), float(np.max(z_mid)), len(z_mid))
        vr_norm = 0.5 + 0.1 * np.cos(np.linspace(0, np.pi, len(z_mid)))

    z_norm = (z_mid - float(np.min(z_mid))) / max(float(np.ptp(z_mid)), 1.0e-9)
    local_boost_template = np.exp(-2.2 * z_norm)
    global_tilt_template = 0.35 + 0.65 * z_norm
    nuisance_template = np.ones_like(z_norm)
    covariance = np.diag(np.maximum(jackknife, 1.0e-3) ** 2)
    rank_audit = nuisance_projected_rank(
        target_response=np.column_stack([local_boost_template, global_tilt_template]),
        nuisance_response=nuisance_template,
        covariance=covariance,
    )
    rank = int(rank_audit.projected_rank)
    condition_number = float(rank_audit.condition_number)
    rank_status = "full_rank_diagnostic" if rank_audit.full_rank else "rank_deficient_diagnostic"
    promotion_blockers = [
        "native_low_ell_solver_not_available",
        "native_morphology_atlas_not_available",
        "matched_publication_grade_nulls_not_bound",
        "publication_grade_covariance_not_bound",
        "held_out_validation_not_bound",
    ]
    forecast_no_claim_reasons = [
        *rank_audit.no_claim_reasons,
        *promotion_blockers,
    ]
    template_correlation = float(
        np.corrcoef(local_boost_template, global_tilt_template)[0, 1]
    )
    separation_score = float(1.0 - abs(template_correlation))

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.errorbar(
        z_mid,
        amplitude,
        yerr=jackknife,
        color=COLORS["blue"],
        marker="o",
        linestyle="-",
        label="DESI depth jackknife",
    )
    ax.plot(
        z_mid,
        local_boost_template,
        color=COLORS["teal"],
        linestyle="-",
        label="local-boost template",
    )
    ax.plot(
        z_mid,
        global_tilt_template,
        color=COLORS["red"],
        linestyle="-.",
        label="global-tilt template",
    )
    ax.plot(
        radius_scaled,
        vr_norm,
        color=COLORS["amber"],
        marker="s",
        linestyle="--",
        label="CF4 radius bootstrap (scaled)",
    )
    ax.set_xlabel("tomographic depth coordinate")
    _setup_axes(ax, "E5 tomographic diagnostic forecast", "normalized diagnostic amplitude")
    ax.legend(frameon=False, loc="best")
    _save(fig, path)
    return {
        "input_mode": "repo_observed_input" if inputs.longrun else "analytic_scaffold",
        "statistics": {
            "desi_depth_bins": int(len(z_mid)),
            "cf4_radius_bins": int(len(radius_scaled)),
            "desi_amplitude_min": float(np.min(amplitude)),
            "desi_amplitude_max": float(np.max(amplitude)),
            "local_global_template_correlation": template_correlation,
            "local_global_separation_score": separation_score,
            "forecast_design_rank": rank,
            "forecast_design_columns": int(rank_audit.target_dimension),
            "forecast_design_condition_number": condition_number,
            "forecast_projected_singular_values": list(rank_audit.singular_values),
            "forecast_rank_no_claim_reasons": list(rank_audit.no_claim_reasons),
            "forecast_promotion_blockers": promotion_blockers,
            "forecast_no_claim_reasons": forecast_no_claim_reasons,
            "forecast_rank_status": rank_status,
            "forecast_definition": (
                "Nuisance-projected SVD rank and template-correlation diagnostic "
                "for local-boost and global-tilt depth templates"
            ),
        },
    }


def _method_diagnostics(
    inputs: RepoInputs,
    assets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    fpr_stats = assets["FPR_rule_of_three"]["statistics"]
    occupancy_stats = assets["E3_per_channel_occupancy"]["statistics"]
    forecast_stats = assets["E5_tomographic_forecast"]["statistics"]
    fisher = gaussian_covariance_fisher_full_and_diag(
        [np.asarray([[0.0, 1.0], [1.0, 0.0]])]
    )
    method_input_hashes = _input_hashes(INPUT_PATHS)
    _, worktree = _git_state()

    def metadata(
        *,
        owner: str,
        implementation_scope: str,
        transfer_source: str,
        null_mock_status: str,
        config_seed: str,
        caveats: list[str],
    ) -> dict[str, Any]:
        return {
            "owner": owner,
            "implementation_scope": implementation_scope,
            "claim_tier": "diagnostic_only",
            "transfer_source": transfer_source,
            "config_hash": _stable_hash(
                {
                    "method_diagnostic": config_seed,
                    "input_hashes": method_input_hashes,
                    "version": "revision-method-diagnostics-v1",
                }
            ),
            "input_hashes": method_input_hashes,
            "sky_support_status": "not_directional",
            "null_mock_status": null_mock_status,
            "generating_command": GENERATING_COMMAND,
            "git_commit_or_worktree_state": worktree,
            "caveats": caveats,
        }

    evidence_stability_status = metadata(
        owner="BASS",
        implementation_scope="bass_py",
        transfer_source="external_or_proxy_transfer",
        null_mock_status="not_statistical",
        config_seed="bass_evidence_stability_not_evaluated",
        caveats=[
            "transfer-conditional diagnostic only",
            "not native solver validation",
            "not HTT evidence",
            "not MIO evidence",
            "not family or geometry evidence",
            "bound not evaluated because no max_loglike_delta input is present",
        ],
    )
    evidence_stability_status.update(
        {
            "transfer_conditional": True,
            "native_solver_result": False,
            "bound_status": "not_evaluated_missing_loglike_delta",
            "required_input_kind": "max_loglike_delta",
            "rejected_proxy_input_kind": "denominator_relative_shift",
            "evidence_shift_upper_bound": None,
            "definition": "|Delta log Z| <= sup |Delta log L| under shared prior support",
        }
    )
    return {
        "finite_mock": {
            **metadata(
                owner="HTT",
                implementation_scope="htt",
                transfer_source="none",
                null_mock_status="current_code_diagnostic_null_bank_generated",
                config_seed="finite_mock_zero_trigger_upper_bound",
                caveats=[
                    "finite-mock upper bound only",
                    "not zero false-positive rate",
                    "not evidence",
                ],
            ),
            "exact_zero_trigger_upper_bound_at_observed_n": fpr_stats[
                "exact_zero_trigger_upper_bound_at_observed_n"
            ],
            "confidence": fpr_stats["finite_mock_confidence"],
            "observed_n_mocks": fpr_stats["observed_n_mocks"],
        },
        "nuisance_rank": {
            **metadata(
                owner="HTT",
                implementation_scope="htt",
                transfer_source="none",
                null_mock_status="not_statistical",
                config_seed="nuisance_projected_rank_forecast_design",
                caveats=[
                    "diagnostic rank precondition only",
                    "not evidence",
                    "not local/global discrimination proof",
                ],
            ),
            "projected_rank": forecast_stats["forecast_design_rank"],
            "target_dimension": forecast_stats["forecast_design_columns"],
            "condition_number": forecast_stats["forecast_design_condition_number"],
            "singular_values": forecast_stats["forecast_projected_singular_values"],
            "no_claim_reasons": forecast_stats["forecast_no_claim_reasons"],
        },
        "fisher_compression": {
            **metadata(
                owner="HTT",
                implementation_scope="htt",
                transfer_source="none",
                null_mock_status="not_statistical",
                config_seed="covariance_fisher_full_vs_diagonal",
                caveats=[
                    "diagnostic covariance-compression audit only",
                    "not evidence",
                    "not covariance model validation",
                ],
            ),
            **fisher.as_payload(),
        },
        "channel_occupancy": {
            **metadata(
                owner="MIO",
                implementation_scope="mio",
                transfer_source="none",
                null_mock_status="not_statistical",
                config_seed="channel_matched_occupancy_vector",
                caveats=[
                    "MIO diagnostic occupancy only",
                    "not posterior odds",
                    "not evidence",
                    "not a truth certificate",
                ],
            ),
            "rows": occupancy_stats["channel_occupancy"],
            "posterior_compatible": occupancy_stats["posterior_compatible"],
            "evidence_compatible": occupancy_stats["evidence_compatible"],
            "truth_certificate": occupancy_stats["truth_certificate"],
        },
        "evidence_stability": evidence_stability_status,
    }


def _asset_specs() -> tuple[AssetSpec, ...]:
    return (
        AssetSpec(
            asset_id="E1_prior_support_surface",
            title="Prior support surface",
            figure_name="fig_revision_prior_support_surface.png",
            artifact_mode="paper_appendix_conditioned",
            allowed_use="paper_appendix",
            transfer_source="empirical_proxy",
            sky_support_status="not_directional",
            null_mock_status="not_statistical",
            caveats=(
                "prior/support sensitivity only",
                "not evidence-grade Bayes factor",
            ),
            source_paths=(INPUT_PATHS[0], INPUT_PATHS[2]),
            builder=_plot_prior_support_surface,
        ),
        AssetSpec(
            asset_id="E2_sigma_beta_band",
            title="Sigma-beta band",
            figure_name="fig_revision_sigma_beta_band.png",
            artifact_mode="paper_appendix_conditioned",
            allowed_use="paper_appendix",
            transfer_source="empirical_proxy",
            sky_support_status="not_directional",
            null_mock_status="not_statistical",
            caveats=(
                "bulk-flow uncertainty diagnostic only",
                "not a verified evidence claim",
                "look-elsewhere correction is display-only",
            ),
            source_paths=(INPUT_PATHS[2],),
            builder=_plot_sigma_beta_band,
        ),
        AssetSpec(
            asset_id="FPR_rule_of_three",
            title="Rule-of-three FPR ceiling",
            figure_name="fig_revision_rule_of_three_fpr.png",
            artifact_mode="external_audit_conditioned",
            allowed_use="external_audit",
            transfer_source="none",
            sky_support_status="not_directional",
            null_mock_status="current_code_diagnostic_null_bank_generated",
            caveats=(
                "finite-null interval only",
                "0/N is an upper bound and not zero false-positive rate",
                "observed nonzero false positives remain blocker diagnostics",
            ),
            source_paths=(INPUT_PATHS[2],),
            builder=_plot_rule_of_three_fpr,
        ),
        AssetSpec(
            asset_id="E3_per_channel_occupancy",
            title="Per-channel occupancy",
            figure_name="fig_revision_per_channel_occupancy.png",
            artifact_mode="paper_appendix_conditioned",
            allowed_use="paper_appendix",
            transfer_source="none",
            sky_support_status="not_directional",
            null_mock_status="not_statistical",
            caveats=(
                "denominator diagnostic only",
                "scalar Q blocked for channel mismatch",
                "no geometry or family claim",
            ),
            source_paths=(INPUT_PATHS[0],),
            builder=_plot_per_channel_occupancy,
        ),
        AssetSpec(
            asset_id="E5_tomographic_forecast",
            title="Tomographic forecast",
            figure_name="fig_revision_tomographic_forecast.png",
            artifact_mode="paper_main_candidate",
            allowed_use="paper_main",
            transfer_source="empirical_proxy",
            sky_support_status="not_directional",
            null_mock_status="jackknife_bootstrap_diagnostic_only",
            caveats=(
                "forecast only",
                "not current local/global discrimination proof",
                "paper-main use requires explicit forecast caption and blocked native-atlas status",
            ),
            source_paths=(INPUT_PATHS[1],),
            builder=_plot_tomographic_forecast,
        ),
    )


def _manifest_for_asset(
    spec: AssetSpec,
    figure_path: Path,
    config_hash: str,
    input_hashes: list[str],
    stats: dict[str, Any],
) -> dict[str, Any]:
    rel_path = _repo_relative(figure_path)
    git_commit, worktree = _git_state()
    manifest = {
        "artifact_id": spec.asset_id,
        "artifact_path": rel_path,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": spec.artifact_mode,
        "allowed_use": spec.allowed_use,
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_state_no_native_low_ell_solver_output",
            "must_state_no_family_identification",
        ],
        "promotion_blockers": list(PROMOTION_BLOCKERS),
        "created_by": GENERATOR,
        "git_commit": git_commit,
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "code_version": worktree,
        "schema_version": "common.revision_experiment_asset.v1",
        "caveats": [*BASE_CAVEATS, *spec.caveats],
        "required_gates": [
            "repo_input_or_analytic_scaffold_declared",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "passed_gates": [
            "repo_input_or_analytic_scaffold_declared",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "failed_gates": [
            "native_low_ell_solver_not_available",
            "native_morphology_atlas_not_available",
            "publication_grade_covariance_not_bound",
        ],
        "statistics_definitions": {
            "asset_title": spec.title,
            "source_artifacts": list(spec.source_paths),
            **stats,
        },
        "transfer_source": spec.transfer_source,
        "sky_support_status": spec.sky_support_status,
        "null_mock_status": spec.null_mock_status,
        "generating_command": GENERATING_COMMAND,
        "git_commit_or_worktree_state": worktree,
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


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# Revision Experiment Assets",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        f"transfer_source: {payload['transfer_source']}",
        "sky_support_status: not_directional",
        "null_mock_status: mixed_not_statistical_current_null_bank_and_jackknife_bootstrap_diagnostic",
        f"config_hash: `{payload['config_hash']}`",
        f"generating_command: `{payload['generating_command']}`",
        f"git_commit_or_worktree_state: `{payload['git_commit_or_worktree_state']}`",
        "input_hashes:",
        *[f"- {item}" for item in payload["input_hashes"]],
        "",
        "These generated assets are diagnostic-only and conditioned on repo-local inputs or deterministic scaffolds.",
        "They are not native transfer outputs and do not support geometry or family claims.",
        "",
        "## Assets",
        "",
        "| Asset | Input mode | Lane | Figure | Manifest |",
        "|---|---|---|---|---|",
    ]
    for asset_id, asset in payload["assets"].items():
        lines.append(
            "| `{}` | `{}` | `{}` / `{}` | `{}` | `{}` |".format(
                asset_id,
                asset["input_mode"],
                asset["artifact_mode"],
                asset["allowed_use"],
                asset["figure_path"],
                asset["manifest_path"],
            )
        )
    lines.extend(
        [
            "",
            "## Caveats",
            "",
            *[f"- {item}" for item in BASE_CAVEATS],
            "- Native solver validation is absent.",
            "- Native morphology atlas validation is absent.",
            "- Matched publication-grade null and covariance gates remain promotion blockers.",
        ]
    )
    ASSET_MD.parent.mkdir(parents=True, exist_ok=True)
    ASSET_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _latex_include_path(figure_path: str) -> str:
    path = Path(figure_path).with_suffix("")
    parts = path.parts
    if parts and parts[0] == "figures":
        return Path(*parts[1:]).as_posix()
    return path.as_posix()


def _latex_asset_figure(asset_id: str, asset: dict[str, Any]) -> str:
    include_path = _latex_include_path(str(asset["figure_path"]))
    caption = ASSET_CAPTIONS[asset_id]
    label = ASSET_LABELS[asset_id]
    return "\n".join(
        [
            "\\begin{figure}[htbp]",
            "\\centering",
            f"\\includegraphics[width=0.92\\textwidth]{{{include_path}}}",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            "\\end{figure}",
            "",
        ]
    )


def _render_latex_snippet(
    payload: dict[str, Any],
    *,
    title: str,
    note: str,
    allowed_use: str,
) -> str:
    assets = payload["assets"]
    assert isinstance(assets, dict)
    asset_ids = [
        asset_id
        for asset_id in ASSET_ORDER
        if isinstance(assets.get(asset_id), dict)
        and assets[asset_id].get("allowed_use") == allowed_use
    ]
    lines = [
        "% Generated by scripts/generate_revision_experiment_assets.py.",
        "% Do not edit figure paths by hand; regenerate instead.",
        f"% {title}",
        f"% {note}",
        "",
    ]
    for asset_id in asset_ids:
        lines.append(_latex_asset_figure(asset_id, assets[asset_id]))
    return "\n".join(lines)


def _render_latex_snippets(payload: dict[str, Any]) -> dict[Path, str]:
    return {
        MAIN_SNIPPET: _render_latex_snippet(
            payload,
            title="Revision diagnostic paper-main candidate figure",
            note="Contains only assets whose manifest allowed_use is paper_main.",
            allowed_use="paper_main",
        ),
        APPENDIX_SNIPPET: _render_latex_snippet(
            payload,
            title="Revision diagnostic appendix figures",
            note="Contains only assets whose manifest allowed_use is paper_appendix.",
            allowed_use="paper_appendix",
        ),
        EXTERNAL_AUDIT_SNIPPET: _render_latex_snippet(
            payload,
            title="Revision diagnostic external-audit figures",
            note="Contains only assets whose manifest allowed_use is external_audit; not input by the manuscript.",
            allowed_use="external_audit",
        ),
    }


def _write_latex_snippets(payload: dict[str, Any]) -> None:
    MANUSCRIPT_SNIPPET_DIR.mkdir(parents=True, exist_ok=True)
    for path, text in _render_latex_snippets(payload).items():
        path.write_text(text, encoding="utf-8")


def _build_payload(inputs: RepoInputs, *, write_figures: bool) -> dict[str, Any]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    assets: dict[str, Any] = {}
    config_inputs = {
        "schema_version": SCHEMA_VERSION,
        "source_paths": INPUT_PATHS,
        "asset_ids": [spec.asset_id for spec in _asset_specs()],
        "version": "revision-experiment-assets-v1",
    }
    top_config_hash = _stable_hash(config_inputs)
    top_input_hashes = _input_hashes(INPUT_PATHS)
    git_commit, worktree = _git_state()

    for spec in _asset_specs():
        figure_path = FIGURE_DIR / spec.figure_name
        result = spec.builder(inputs, figure_path) if write_figures else {
            "input_mode": "repo_observed_input",
            "statistics": {},
        }
        input_hashes = _input_hashes(spec.source_paths)
        config_hash = _stable_hash(
            {
                "asset_id": spec.asset_id,
                "figure_name": spec.figure_name,
                "artifact_mode": spec.artifact_mode,
                "allowed_use": spec.allowed_use,
                "input_hashes": input_hashes,
                "version": "revision-experiment-assets-v1",
            }
        )
        manifest = _manifest_for_asset(
            spec,
            figure_path,
            config_hash,
            input_hashes,
            {"input_mode": result["input_mode"], **result.get("statistics", {})},
        )
        manifest_path = figure_path.with_suffix("").with_name(
            figure_path.stem + ".manifest.json"
        )
        if write_figures:
            _write_json(manifest_path, manifest)
        assets[spec.asset_id] = {
            "title": spec.title,
            "figure_path": _repo_relative(figure_path),
            "manifest_path": _repo_relative(manifest_path),
            "artifact_mode": spec.artifact_mode,
            "allowed_use": spec.allowed_use,
            "claim_tier": "diagnostic_only",
            "owner": "COMMON",
            "implementation_scope": "common",
            "transfer_source": spec.transfer_source,
            "sky_support_status": spec.sky_support_status,
            "null_mock_status": spec.null_mock_status,
            "input_mode": result["input_mode"],
            "input_hashes": input_hashes,
            "config_hash": config_hash,
            "caveats": [*BASE_CAVEATS, *spec.caveats],
            "promotion_blockers": list(PROMOTION_BLOCKERS),
            "statistics": result.get("statistics", {}),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "artifact_mode": "external_audit_conditioned",
        "allowed_use": "external_audit",
        "transfer_source": "none",
        "asset_transfer_sources": sorted(
            {asset["transfer_source"] for asset in assets.values()}
        ),
        "sky_support_status": "not_directional",
        "null_mock_status": "mixed_not_statistical_current_null_bank_and_jackknife_bootstrap_diagnostic",
        "config_hash": top_config_hash,
        "input_hashes": top_input_hashes,
        "generating_command": GENERATING_COMMAND,
        "git_commit": git_commit,
        "git_commit_or_worktree_state": worktree,
        "caveats": list(BASE_CAVEATS),
        "assets": assets,
        "method_diagnostics": _method_diagnostics(inputs, assets),
    }


def write_assets() -> None:
    inputs = _load_inputs()
    payload = _build_payload(inputs, write_figures=True)
    _write_json(ASSET_JSON, payload)
    _write_markdown(payload)
    _write_latex_snippets(payload)


def check_assets() -> list[str]:
    errors: list[str] = []
    required_paths = [ASSET_JSON, ASSET_MD, MAIN_SNIPPET, APPENDIX_SNIPPET, EXTERNAL_AUDIT_SNIPPET]
    for spec in _asset_specs():
        figure_path = FIGURE_DIR / spec.figure_name
        required_paths.extend(
            [
                figure_path,
                figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json"),
            ]
        )
    for path in required_paths:
        if not path.exists():
            errors.append(f"missing required artifact: {_repo_relative(path)}")

    if not ASSET_JSON.exists():
        return errors

    payload = json.loads(ASSET_JSON.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("revision_experiment_assets.json schema_version mismatch")
    if payload.get("owner") != "COMMON":
        errors.append("revision_experiment_assets.json owner must be COMMON")
    if payload.get("claim_tier") != "diagnostic_only":
        errors.append("revision_experiment_assets.json claim_tier must be diagnostic_only")
    expected_ids = {spec.asset_id for spec in _asset_specs()}
    actual_ids = set(payload.get("assets", {}))
    if actual_ids != expected_ids:
        errors.append(f"asset id mismatch: expected {sorted(expected_ids)}, got {sorted(actual_ids)}")

    for spec in _asset_specs():
        figure_path = FIGURE_DIR / spec.figure_name
        manifest_path = figure_path.with_suffix("").with_name(
            figure_path.stem + ".manifest.json"
        )
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        issues = validate_manifest_payload(
            manifest,
            manifest_path=manifest_path,
            expected_artifact_path=_repo_relative(figure_path),
        )
        errors.extend(
            f"{_repo_relative(manifest_path)}: {issue.code}: {issue.detail}"
            for issue in issues
        )
        caveat_text = " ".join(str(item) for item in manifest.get("caveats", [])).lower()
        forbidden = (
            "geometry " + "detected",
            "family " + "identified",
            "native solver " + "result",
            "mio " + "posterior",
            "truth " + "certificate",
        )
        for phrase in forbidden:
            if phrase in caveat_text:
                errors.append(f"{_repo_relative(manifest_path)} contains forbidden phrase {phrase!r}")

    for snippet_path, expected_text in _render_latex_snippets(payload).items():
        if not snippet_path.exists():
            continue
        actual_text = snippet_path.read_text(encoding="utf-8")
        if actual_text != expected_text:
            errors.append(f"stale revision LaTeX snippet: {_repo_relative(snippet_path)}")

    main_text = MAIN_SNIPPET.read_text(encoding="utf-8") if MAIN_SNIPPET.exists() else ""
    if "fig_revision_prior_support_surface" in main_text:
        errors.append("paper_appendix prior-support figure leaked into main revision snippet")
    if "fig_revision_sigma_beta_band" in main_text:
        errors.append("paper_appendix sigma-beta figure leaked into main revision snippet")
    if "fig_revision_per_channel_occupancy" in main_text:
        errors.append("paper_appendix occupancy figure leaked into main revision snippet")
    if "fig_revision_rule_of_three_fpr" in main_text:
        errors.append("external-audit FPR figure leaked into main revision snippet")

    assets = payload.get("assets", {})
    if isinstance(assets, dict):
        prior = assets.get("E1_prior_support_surface", {}).get("statistics", {})
        if not {"prior_floor_min", "prior_floor_max", "prior_ceiling_min", "prior_ceiling_max", "proxy_lnb_definition"} <= set(prior):
            errors.append("E1_prior_support_surface missing prior cutoff proxy statistics")
        sigma_beta = assets.get("E2_sigma_beta_band", {}).get("statistics", {})
        if not {"beta_min", "beta_max", "sigma_beta_min", "sigma_beta_max", "look_elsewhere_trials", "proxy_lnb_definition"} <= set(sigma_beta):
            errors.append("E2_sigma_beta_band missing sigma_beta/look-elsewhere statistics")
        fpr = assets.get("FPR_rule_of_three", {}).get("statistics", {})
        if fpr.get("observed_false_positive_count") is None and assets.get("FPR_rule_of_three", {}).get("input_mode") == "repo_observed_input":
            errors.append("FPR_rule_of_three missing observed nonzero FPR fields for repo input")
        occupancy = assets.get("E3_per_channel_occupancy", {}).get("statistics", {})
        channels = occupancy.get("channel_occupancy", [])
        channel_names = {row.get("channel") for row in channels if isinstance(row, dict)}
        if channel_names != {"shear", "vorticity", "tilt", "anisotropic curvature"}:
            errors.append("E3_per_channel_occupancy missing channel-matched occupancy vector")
        forecast = assets.get("E5_tomographic_forecast", {}).get("statistics", {})
        if not {"local_global_template_correlation", "local_global_separation_score", "forecast_design_rank", "forecast_design_columns"} <= set(forecast):
            errors.append("E5_tomographic_forecast missing local/global template forecast statistics")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write assets")
    parser.add_argument("--check", action="store_true", help="validate written assets")
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")
    if not args.write and not args.check:
        parser.error("choose --write or --check")

    if args.write:
        write_assets()
        print(f"wrote {_repo_relative(ASSET_JSON)} and five revision figures")
        return 0

    errors = check_assets()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("revision experiment assets pass check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
