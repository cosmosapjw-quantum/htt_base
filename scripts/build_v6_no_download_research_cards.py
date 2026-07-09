#!/usr/bin/env python3
"""Build v6 no-download research cards and legacy-figure classification.

The v6 report asks for audit-grade objects, not new headline plots.  This
script only consumes existing repo-local artifacts and current figure manifests.
It does not run K1/K5/K6 long analyses and does not download data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / "docs" / "generated"
FIGURES = REPO_ROOT / "figures"

RESEARCH_JSON = GEN / "v6_no_download_research_cards.json"
RESEARCH_MD = GEN / "v6_no_download_research_cards.md"
FIGURE_JSON = GEN / "v6_legacy_figure_classification.json"
FIGURE_MD = GEN / "v6_legacy_figure_classification.md"

FIGURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".pdf"}
ROOT_LEGACY_SOURCES = FIGURES / "quarantined_legacy" / "root_sources"
OLD_FIGURE_ROOTS = (
    ROOT_LEGACY_SOURCES,
    FIGURES / "parallel_track",
    FIGURES / "validation",
)


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(relative: str) -> dict[str, Any]:
    path = REPO_ROOT / relative
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes(paths: Iterable[str]) -> list[str]:
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


def _command(argv: list[str] | None) -> str:
    args = sys.argv[1:] if argv is None else argv
    return shlex.join(["python", "scripts/build_v6_no_download_research_cards.py", *args])


def _sidecar_manifest(path: Path) -> Path | None:
    base = path.with_suffix("")
    for candidate in (
        base.with_name(base.name + ".manifest.json"),
        path.with_name(path.name + ".manifest.json"),
    ):
        if candidate.exists():
            return candidate
    return None


def _conditioned_replacement(path: Path) -> Path | None:
    if path.parent == ROOT_LEGACY_SOURCES and path.name.startswith("fig_"):
        return FIGURES / "conditioned_legacy" / f"root__{path.name}"
    if path.parent == FIGURES / "parallel_track":
        return FIGURES / "conditioned_legacy" / f"parallel-track__{path.name}"
    if path.parent == FIGURES / "validation":
        return FIGURES / "conditioned_legacy" / f"validation__{path.name}"
    return None


def _old_figure_kind(path: Path) -> str:
    if path.parent == ROOT_LEGACY_SOURCES:
        return "old_root_result_figure"
    if path.parent == FIGURES / "parallel_track":
        return "old_parallel_track_figure"
    if path.parent == FIGURES / "validation":
        return "old_validation_figure"
    return "unknown_old_figure"


def _legacy_response_class(path: Path) -> str:
    name = path.stem.lower()
    if any(token in name for token in ("evidence", "bf", "posterior", "type_by_type")):
        return "legacy_ranking_or_posterior_removed"
    if any(token in name for token in ("direction", "skymap", "mollweide", "dipole")):
        return "directional_style_only_no_geometry_claim"
    if any(token in name for token in ("planck", "cf4", "act", "validation")):
        return "observed_or_validation_style_only"
    if any(token in name for token in ("mes", "sigma", "vorticity", "filling", "q_")):
        return "method_or_denominator_context_only"
    return "legacy_response_label_only"


def build_legacy_figure_classification(command: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for root in OLD_FIGURE_ROOTS:
        if root == ROOT_LEGACY_SOURCES:
            if not root.exists():
                candidates = []
            else:
                candidates = sorted(
                    p for p in root.iterdir() if p.is_file() and p.suffix.lower() in FIGURE_SUFFIXES
                )
        elif root == FIGURES:
            candidates = sorted(
                p for p in root.iterdir() if p.is_file() and p.suffix.lower() in FIGURE_SUFFIXES
            )
        else:
            candidates = sorted(
                p for p in root.glob("*") if p.is_file() and p.suffix.lower() in FIGURE_SUFFIXES
            )
        for path in candidates:
            replacement = _conditioned_replacement(path)
            replacement_manifest = (
                _sidecar_manifest(replacement) if replacement is not None and replacement.exists() else None
            )
            rows.append(
                {
                    "path": _repo_relative(path),
                    "sha256": _sha256(path),
                    "legacy_kind": _old_figure_kind(path),
                    "response_class": _legacy_response_class(path),
                    "current_disposition": "discarded_from_current_claim_lane",
                    "physical_file_state": (
                        "retained_as_hash_source_only_for_conditioned_legacy_manifest"
                        if replacement_manifest is not None
                        else "quarantined_missing_manifest_backing_copy"
                    ),
                    "replacement_path": (
                        _repo_relative(replacement)
                        if replacement is not None and replacement.exists()
                        else None
                    ),
                    "replacement_manifest": (
                        _repo_relative(replacement_manifest)
                        if replacement_manifest is not None
                        else None
                    ),
                    "allowed_use": "none_as_current_result",
                    "forbidden_uses": [
                        "headline_plot",
                        "family_identification",
                        "geometry_detection",
                        "htt_evidence",
                        "native_solver_validation",
                    ],
                }
            )

    by_kind: dict[str, int] = {}
    by_class: dict[str, int] = {}
    missing_replacement = 0
    for row in rows:
        by_kind[row["legacy_kind"]] = by_kind.get(row["legacy_kind"], 0) + 1
        by_class[row["response_class"]] = by_class.get(row["response_class"], 0) + 1
        if row["replacement_manifest"] is None:
            missing_replacement += 1

    payload = {
        "artifact_id": "common.v6_legacy_figure_classification",
        "artifact_path": _repo_relative(FIGURE_JSON),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "config_hash": _config_hash(
            {
                "roots": [_repo_relative(root) for root in OLD_FIGURE_ROOTS],
                "rows": [
                    {
                        "path": row["path"],
                        "sha256": row["sha256"],
                        "replacement_manifest": row["replacement_manifest"],
                        "response_class": row["response_class"],
                    }
                    for row in rows
                ],
            }
        ),
        "input_hashes": [f"{row['path']}:{row['sha256']}" for row in rows],
        "caveats": [
            "Classification only; old figures are not promoted by this artifact.",
            "Old root/parallel/validation figures are discarded from current claim lanes.",
            "Manifest-backed conditioned_legacy copies remain available only as conditioned legacy gallery material.",
        ],
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
        "summary": {
            "classified_old_figures": len(rows),
            "by_legacy_kind": by_kind,
            "by_response_class": by_class,
            "missing_conditioned_replacement_manifest": missing_replacement,
        },
        "rows": rows,
    }
    return payload


def _source_hash(path: str) -> str | None:
    p = REPO_ROOT / path
    return _sha256(p) if p.exists() else None


def _component_source_matrix(
    *, k1: dict[str, Any], k5: dict[str, Any], k6: dict[str, Any], pr08: dict[str, Any]
) -> list[dict[str, Any]]:
    sectors = pr08.get("sectors", {})
    if not isinstance(sectors, dict):
        sectors = {}
    return [
        {
            "component": "Sigma2",
            "signed_xC_coefficient": +1,
            "owner": "OBSSTAT",
            "local_file": "docs/generated/k1_global_maxscan.json",
            "file_hash": _source_hash("docs/generated/k1_global_maxscan.json"),
            "source_status": sectors.get("Sigma2", {}).get("status", "partial"),
            "source_mode": "estimated_partial",
            "value_summary": {
                "global_p_smica": k1.get("smica", {}).get("global_p"),
                "global_p_commander": k1.get("commander", {}).get("global_p"),
            },
            "covariance_status": "e2e_systematics_covariance_not_bound",
            "null_mock_status": "isotropic_lcdm_grf_only_e2e_blocked",
            "blocker": k1.get("blocker_partial", "BLOCKED_MISSING_PR4_E2E_ACCESS"),
            "allowed_use": "partial_lowell_descriptor_not_family_identification",
        },
        {
            "component": "W2",
            "signed_xC_coefficient": -1,
            "owner": "OBSSTAT",
            "local_file": "docs/generated/k6_cf4_curl_posterior.json",
            "file_hash": _source_hash("docs/generated/k6_cf4_curl_posterior.json"),
            "source_status": sectors.get("W2", {}).get("status", "fail_closed"),
            "source_mode": "fail_closed_structural_no_go",
            "value_summary": {
                "vorticity_over_shear_max": k6.get("vorticity_over_shear_ratio_max"),
                "structural_no_go": k6.get("structural_no_go"),
            },
            "covariance_status": "true_cr_cell_cell_covariance_not_owned",
            "null_mock_status": "wf_mean_field_no_go_true_cr_posterior_blocked",
            "blocker": "BLOCKED_MISSING_FIELD_REALIZATIONS",
            "allowed_use": "no_go_diagnostic_not_zeroed_component",
        },
        {
            "component": "Omega_tilt",
            "signed_xC_coefficient": +1,
            "owner": "OBSSTAT",
            "local_file": "docs/generated/k5_cf4_release_coverage.json",
            "file_hash": _source_hash("docs/generated/k5_cf4_release_coverage.json"),
            "source_status": sectors.get("Omega_tilt", {}).get("status", "measured"),
            "source_mode": "estimated_conditional_coverage",
            "value_summary": {
                "bulk_amplitude_kms": k5.get("measured_bulk", {}).get("amplitude_kms"),
                "total_error_kms": k5.get("coverage", {}).get("total_amplitude_error_kms"),
                "cv_inclusive_coverage": k5.get("coverage", {})
                .get("cosmic_variance_inclusive", {})
                .get("amplitude_coverage"),
            },
            "covariance_status": "conditional_lambdacdm_sigma_cv_prior_not_release_mocks",
            "null_mock_status": "geometry_and_error_matched_gaussian_bulkflow_mocks",
            "blocker": "full_selection_malmquist_grouping_correlated_release_mocks_still_gate",
            "allowed_use": "model_independent_kinematic_descriptor",
        },
        {
            "component": "Omega_k",
            "signed_xC_coefficient": +1,
            "owner": "OBSSTAT/BASS",
            "local_file": None,
            "file_hash": None,
            "source_status": sectors.get("Omega_k", {}).get("status", "fail_closed_no_channel"),
            "source_mode": "absent_no_registered_lowell_channel",
            "value_summary": None,
            "covariance_status": "not_bound",
            "null_mock_status": "not_applicable_no_channel",
            "blocker": "native_lowell_transfer_or_higher_order_channel_required",
            "allowed_use": "fail_closed_blind_sector_not_zeroed",
        },
    ]


def _denominator_rows(science: dict[str, Any]) -> list[dict[str, Any]]:
    points = science.get("transfer_sensitivity", {}).get("points", [])
    rows: list[dict[str, Any]] = []
    for point in points if isinstance(points, list) else []:
        if not isinstance(point, dict):
            continue
        rows.append(
            {
                "denominator_policy": point.get("denominator_policy"),
                "relative_shift": point.get("relative_shift"),
                "denominator_value": point.get("denominator_value"),
                "Q_diagnostic": point.get("Q_diagnostic"),
                "transfer_source": point.get("transfer_source"),
                "claim_tier": point.get("claim_tier", "diagnostic_only"),
                "allowed_use": "denominator_sensitivity_only",
            }
        )
    return rows


def _identified_set_card(science: dict[str, Any], pr08: dict[str, Any]) -> dict[str, Any]:
    response = science.get("rank_and_null_fpr", {}).get("response_overlap", {})
    if not isinstance(response, dict):
        response = {}
    data_rank = pr08.get("data_rank", {}) if isinstance(pr08.get("data_rank"), dict) else {}
    sectors = pr08.get("sectors", {}) if isinstance(pr08.get("sectors"), dict) else {}
    fail_closed = [
        name
        for name, row in sectors.items()
        if isinstance(row, dict) and str(row.get("status", "")).startswith("fail_closed")
    ]
    return {
        "card_id": "v6_current_identified_set",
        "owner": "HTT/MIO/OBSSTAT",
        "claim_tier": "diagnostic_only",
        "data_rank_count": data_rank.get("data_rank_count"),
        "reachable_full": data_rank.get("reachable_full", []),
        "reachable_partial": data_rank.get("reachable_partial", []),
        "fail_closed_columns": fail_closed,
        "response_overlap_projected_rank": response.get("projected_rank"),
        "response_overlap_singular_values": response.get("singular_values"),
        "response_overlap_rho_LB_GT": response.get("rho_LB_GT"),
        "x_C_interval_status": "not_certified_blind_sectors_not_zeroed",
        "x_C_point_status": pr08.get("x_C_withheld_reason"),
        "F_status": "diagnostic_only_not_certified_filling",
        "kill_switch": (
            "if any fail_closed sector is numerically zero-filled, withhold x_C/Q/F and report vector sectors only"
        ),
    }


def _exceedance_card(science: dict[str, Any]) -> dict[str, Any]:
    pi = science.get("transfer_sensitivity", {}).get("pi_policy_summary", {})
    if not isinstance(pi, dict):
        pi = {}
    return {
        "card_id": "v6_pi_exceedance_calibration",
        "owner": pi.get("owner", "MIO"),
        "claim_tier": pi.get("claim_tier", "diagnostic_only"),
        "source_score_label": pi.get("source_score_label"),
        "measure_kind": pi.get("measure_kind"),
        "threshold_policy": pi.get("threshold_policy"),
        "threshold_grid": pi.get("threshold_grid"),
        "sample_count": pi.get("sample_count"),
        "calibration_status": pi.get("calibration_status"),
        "null_mock_status": pi.get("null_mock_status"),
        "covariance_status": pi.get("covariance_status"),
        "allowed_use": "descriptive_exceedance_policy_metadata_only",
        "forbidden_use": "p_value_or_truth_probability",
    }


def _depth_gap_card(science: dict[str, Any], cf4_depth: dict[str, Any]) -> dict[str, Any]:
    gf = science.get("semantic_and_vectors", {}).get("g_f_display_contract", {})
    if not isinstance(gf, dict):
        gf = {}
    return {
        "card_id": "v6_depth_gap_gf_card",
        "owner": gf.get("owner", "MIO"),
        "claim_tier": gf.get("claim_tier", "diagnostic_only"),
        "G_F": gf.get("G_F"),
        "log_g_F": gf.get("log_g_F"),
        "reference_bin_id": gf.get("reference_bin_id"),
        "comparison_bin_id": gf.get("comparison_bin_id"),
        "raw_F_by_bin": gf.get("raw_F_by_bin"),
        "effective_F_by_bin": gf.get("effective_F_by_bin"),
        "floor_applied_by_bin": gf.get("floor_applied_by_bin"),
        "matched_null_forecast_status": gf.get("matched_null_forecast_status"),
        "local_global_separation_status": gf.get("local_global_separation_status"),
        "cf4_shell_attempt_status": (
            "not_attempted_current_cf4_shells_lack_matched_covariance_and_calibrated_null"
        ),
        "cf4_shell_evidence_read": "docs/generated/cf4_bulkflow_apex_depth_report.json",
        "cf4_shell_null_mock_status": cf4_depth.get("null_mock_status"),
        "cf4_shell_covariance_status": cf4_depth.get("covariance_status", "not_bound"),
        "allowed_use": "display_contract_and_readiness_only",
    }


def _optical_ansatz_readiness(k1: dict[str, Any], biposh: dict[str, Any], branch_md_hash: str | None) -> list[dict[str, Any]]:
    return [
        {
            "branch": "mean_template",
            "available_summary": "K1 low-ell morphology scalar summaries",
            "current_status": "insufficient_for_likelihood_branch",
            "evidence": "docs/generated/k1_global_maxscan.json",
            "evidence_hash": _source_hash("docs/generated/k1_global_maxscan.json"),
            "blocker": "harmonic_template_plus_orientation_marginalization_or_noncentral_statistic_required",
            "allowed_use": "diagnostic_lowell_descriptor",
            "smica_global_p": k1.get("smica", {}).get("global_p"),
            "commander_global_p": k1.get("commander", {}).get("global_p"),
        },
        {
            "branch": "covariance_biposh",
            "available_summary": "SMICA BipoSH/SI descriptor",
            "current_status": "data_side_descriptor_only",
            "evidence": "docs/generated/k1_biposh_smica.json",
            "evidence_hash": _source_hash("docs/generated/k1_biposh_smica.json"),
            "blocker": "full_anisotropic_covariance_and_e2e_null_not_bound",
            "allowed_use": "observable_statistic_not_theory_likelihood",
            "theory_side_status": biposh.get("theory_side_status"),
        },
        {
            "branch": "central_scalar_chi_square",
            "available_summary": "D2/D3 style scalar summaries",
            "current_status": "blocked_for_both_lowell_branches",
            "evidence": "docs/generated/lowell_likelihood_branch_report.md",
            "evidence_hash": branch_md_hash,
            "blocker": "central_scalar_is_neither_noncentral_template_nor_full_covariance",
            "allowed_use": "caveated_diagnostic_only",
        },
    ]


def _k5_k6_feasibility() -> dict[str, Any]:
    k5_input = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
    k6_input = REPO_ROOT / "workdir/raw/cf4/CF4pp_mean_std_grids.npz"
    return {
        "K5": {
            "script": "scripts/k5_cf4_release_coverage.py",
            "input_path": _repo_relative(k5_input),
            "input_present": k5_input.exists(),
            "input_size_bytes": k5_input.stat().st_size if k5_input.exists() else None,
            "check_option_available": True,
            "heavy_run_deferred_this_turn": True,
            "next_turn_runnable": k5_input.exists(),
            "expected_runtime_note": "moderate deterministic run; N_MOCK=600",
        },
        "K6": {
            "script": "scripts/k6_cf4_curl_posterior.py",
            "input_path": _repo_relative(k6_input),
            "input_present": k6_input.exists(),
            "input_size_bytes": k6_input.stat().st_size if k6_input.exists() else None,
            "check_option_available": True,
            "heavy_run_deferred_this_turn": True,
            "next_turn_runnable": k6_input.exists(),
            "expected_runtime_note": "heavier grid/ensemble run; 128^3 velocity grid, N_CR=400",
        },
    }


def build_research_cards(command: str, figure_payload: dict[str, Any]) -> dict[str, Any]:
    science = _load_json("docs/generated/current_science_plot_payload.json")
    pr08 = _load_json("docs/generated/pr08_006_joint_artifact.json")
    k1 = _load_json("docs/generated/k1_global_maxscan.json")
    k5 = _load_json("docs/generated/k5_cf4_release_coverage.json")
    k6 = _load_json("docs/generated/k6_cf4_curl_posterior.json")
    biposh = _load_json("docs/generated/k1_biposh_smica.json")
    cf4_depth = _load_json("docs/generated/cf4_bulkflow_apex_depth_report.json")

    input_paths = [
        "docs/generated/current_science_plot_payload.json",
        "docs/generated/pr08_006_joint_artifact.json",
        "docs/generated/k1_global_maxscan.json",
        "docs/generated/k5_cf4_release_coverage.json",
        "docs/generated/k6_cf4_curl_posterior.json",
        "docs/generated/k1_biposh_smica.json",
        "docs/generated/cf4_bulkflow_apex_depth_report.json",
        "docs/generated/lowell_likelihood_branch_report.md",
    ]
    component_rows = _component_source_matrix(k1=k1, k5=k5, k6=k6, pr08=pr08)
    denominator_rows = _denominator_rows(science)
    payload = {
        "artifact_id": "common.v6_no_download_research_cards",
        "artifact_path": _repo_relative(RESEARCH_JSON),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": science.get("transfer_source", "mixed_none_and_external_transfer_conditioned"),
        "sky_support_status": "mixed_diagnostic_metadata_only",
        "null_mock_status": "mixed_diagnostic_and_blocked",
        "config_hash": _config_hash(
            {
                "input_paths": input_paths,
                "component_count": len(component_rows),
                "denominator_rows": denominator_rows,
                "legacy_figure_config_hash": figure_payload["config_hash"],
            }
        ),
        "input_hashes": _input_hashes(input_paths),
        "caveats": [
            "No long-run K1/K5/K6 analysis is executed by this artifact.",
            "No native low-ell solver output is represented.",
            "All cards are diagnostic/readiness objects and do not identify a Bianchi family.",
            "K1 E2E remains blocked until the external simulation maps are locally bound.",
        ],
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
        "cards": {
            "component_source_matrix": {
                "description": "one row per g component with source mode and gate status",
                "rows": component_rows,
            },
            "identified_set_card": _identified_set_card(science, pr08),
            "denominator_sensitivity_table": {
                "description": "MES/external/observational denominator sensitivity from current payload",
                "rows": denominator_rows,
            },
            "response_class_ledger": {
                "description": "current response rows plus old labels with ranking removed",
                "current_response_overlap": science.get("rank_and_null_fpr", {}).get(
                    "response_overlap", {}
                ),
                "legacy_figure_classification_ref": _repo_relative(FIGURE_JSON),
                "legacy_response_class_counts": figure_payload["summary"]["by_response_class"],
                "ranking_removed": True,
            },
            "exceedance_calibration_card": _exceedance_card(science),
            "depth_gap_card": _depth_gap_card(science, cf4_depth),
            "optical_ansatz_readiness": _optical_ansatz_readiness(
                k1,
                biposh,
                _source_hash("docs/generated/lowell_likelihood_branch_report.md"),
            ),
            "cf4_shell_gf_attempt": {
                "attempted": False,
                "reason": "existing CF4 shell artifacts do not provide matched covariance plus calibrated null status required by v6",
                "evidence_read": [
                    "docs/generated/cf4_bulkflow_apex_depth_report.json",
                    "docs/generated/cf4_affine_flow_report.json",
                    "docs/generated/cf4_bulkflow_likelihood_report.json",
                ],
                "allowed_next_step": "bind a matched shell covariance/null artifact before computing observed G_F",
            },
            "k5_k6_next_turn_feasibility": _k5_k6_feasibility(),
        },
    }
    return payload


def render_figure_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# V6 Legacy Figure Classification",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        f"config_hash: `{payload['config_hash']}`",
        "caveats:",
        "- Old root/parallel/validation figures are discarded from current claim lanes.",
        "- Manifest-backed conditioned_legacy copies are the only retained legacy figure lane.",
        "- This file classifies figures; it does not promote or reinterpret them.",
        f"generating_command: {payload['generating_command']}",
        "git_commit_or_worktree_state: content-addressed",
        "",
        "## Summary",
        "",
        f"- Classified old figures: {summary['classified_old_figures']}",
        f"- Missing conditioned replacement manifests: {summary['missing_conditioned_replacement_manifest']}",
        "",
        "## By Kind",
        "",
        "| Kind | Count |",
        "| --- | ---: |",
    ]
    for key, count in sorted(summary["by_legacy_kind"].items()):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(["", "## By Response Class", "", "| Class | Count |", "| --- | ---: |"])
    for key, count in sorted(summary["by_response_class"].items()):
        lines.append(f"| `{key}` | {count} |")
    lines.extend(
        [
            "",
            "## Classified Figures",
            "",
            "| Path | Disposition | Response class | Replacement |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| "
            f"`{row['path']}` | "
            f"`{row['current_disposition']}` | "
            f"`{row['response_class']}` | "
            f"`{row['replacement_path'] or 'none'}` |"
        )
    lines.append("")
    return "\n".join(lines)


def render_research_markdown(payload: dict[str, Any]) -> str:
    cards = payload["cards"]
    identified = cards["identified_set_card"]
    depth = cards["depth_gap_card"]
    exceed = cards["exceedance_calibration_card"]
    feasibility = cards["k5_k6_next_turn_feasibility"]
    lines = [
        "# V6 No-Download Research Cards",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        f"transfer_source: {payload['transfer_source']}",
        "sky_support_status: mixed_diagnostic_metadata_only",
        "null_mock_status: mixed_diagnostic_and_blocked",
        f"config_hash: `{payload['config_hash']}`",
        "caveats:",
        "- No long-run K1/K5/K6 analysis is executed by this artifact.",
        "- No native low-ell solver output is represented.",
        "- All cards are diagnostic/readiness objects and do not identify a Bianchi family.",
        f"generating_command: {payload['generating_command']}",
        "git_commit_or_worktree_state: content-addressed",
        "",
        "## Component-Source Matrix",
        "",
        "| Component | Mode | Status | Source | Blocker |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in cards["component_source_matrix"]["rows"]:
        lines.append(
            "| "
            f"`{row['component']}` | "
            f"`{row['source_mode']}` | "
            f"`{row['source_status']}` | "
            f"`{row['local_file'] or 'none'}` | "
            f"{row['blocker']} |"
        )
    lines.extend(
        [
            "",
            "## Identified-Set Card",
            "",
            f"- data_rank_count: `{identified['data_rank_count']}`",
            f"- reachable_full: `{', '.join(identified['reachable_full']) or 'none'}`",
            f"- reachable_partial: `{', '.join(identified['reachable_partial']) or 'none'}`",
            f"- fail_closed_columns: `{', '.join(identified['fail_closed_columns']) or 'none'}`",
            f"- x_C_interval_status: `{identified['x_C_interval_status']}`",
            f"- F_status: `{identified['F_status']}`",
            "",
            "## Denominator Sensitivity",
            "",
            "| Policy | Shift | Denominator | Q diagnostic | Transfer |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in cards["denominator_sensitivity_table"]["rows"]:
        lines.append(
            "| "
            f"`{row['denominator_policy']}` | "
            f"{row['relative_shift']} | "
            f"{row['denominator_value']} | "
            f"{row['Q_diagnostic']} | "
            f"`{row['transfer_source']}` |"
        )
    lines.extend(
        [
            "",
            "## Exceedance Calibration",
            "",
            f"- source_score_label: `{exceed['source_score_label']}`",
            f"- threshold_policy: `{exceed['threshold_policy']}`",
            f"- calibration_status: `{exceed['calibration_status']}`",
            f"- forbidden_use: `{exceed['forbidden_use']}`",
            "",
            "## Depth-Gap Card",
            "",
            f"- G_F: `{depth['G_F']}`",
            f"- reference/comparison: `{depth['reference_bin_id']}` -> `{depth['comparison_bin_id']}`",
            f"- matched_null_forecast_status: `{depth['matched_null_forecast_status']}`",
            f"- cf4_shell_attempt_status: `{depth['cf4_shell_attempt_status']}`",
            "",
            "## Optical Ansatz Readiness",
            "",
            "| Branch | Status | Blocker |",
            "| --- | --- | --- |",
        ]
    )
    for row in cards["optical_ansatz_readiness"]:
        lines.append(
            f"| `{row['branch']}` | `{row['current_status']}` | {row['blocker']} |"
        )
    lines.extend(
        [
            "",
            "## K5/K6 Next-Turn Feasibility",
            "",
            "| Lane | Input present | Size bytes | Next-turn runnable | Deferred reason |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for lane, row in feasibility.items():
        lines.append(
            "| "
            f"`{lane}` | "
            f"`{row['input_present']}` | "
            f"{row['input_size_bytes']} | "
            f"`{row['next_turn_runnable']}` | "
            f"{row['expected_runtime_note']} |"
        )
    lines.extend(
        [
            "",
            "## Legacy Figure Classification",
            "",
            f"- full ledger: `{cards['response_class_ledger']['legacy_figure_classification_ref']}`",
            f"- ranking_removed: `{cards['response_class_ledger']['ranking_removed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _write_outputs(research_payload: dict[str, Any], figure_payload: dict[str, Any]) -> None:
    GEN.mkdir(parents=True, exist_ok=True)
    FIGURE_JSON.write_text(
        json.dumps(figure_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    FIGURE_MD.write_text(render_figure_markdown(figure_payload), encoding="utf-8")
    RESEARCH_JSON.write_text(
        json.dumps(research_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    RESEARCH_MD.write_text(render_research_markdown(research_payload), encoding="utf-8")


def _expected_outputs(research_payload: dict[str, Any], figure_payload: dict[str, Any]) -> dict[Path, str]:
    return {
        FIGURE_JSON: json.dumps(figure_payload, indent=2, sort_keys=True) + "\n",
        FIGURE_MD: render_figure_markdown(figure_payload),
        RESEARCH_JSON: json.dumps(research_payload, indent=2, sort_keys=True) + "\n",
        RESEARCH_MD: render_research_markdown(research_payload),
    }


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    generation_args = [] if argv is None else [arg for arg in argv if arg != "--check"]
    command = _command(generation_args)
    figure_payload = build_legacy_figure_classification(command)
    research_payload = build_research_cards(command, figure_payload)

    if args.check:
        stale = []
        for path, expected in _expected_outputs(research_payload, figure_payload).items():
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(_repo_relative(path))
        if stale:
            print("stale v6 no-download artifacts:", file=sys.stderr)
            for path in stale:
                print(f"- {path}", file=sys.stderr)
            return 1
        print("v6 no-download research artifacts are current")
        return 0

    _write_outputs(research_payload, figure_payload)
    print(f"wrote {_repo_relative(RESEARCH_JSON)}")
    print(f"wrote {_repo_relative(RESEARCH_MD)}")
    print(f"wrote {_repo_relative(FIGURE_JSON)}")
    print(f"wrote {_repo_relative(FIGURE_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
