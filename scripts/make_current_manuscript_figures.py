#!/usr/bin/env python3
"""Generate current manifest-backed manuscript figures.

The figures produced here are report diagnostics over current generated
artifacts. They are not native low-ell outputs, not HTT evidence, and not MIO
final-certification objects. Each PNG receives a valid sidecar manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
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
from htt.departure.response_overlap import build_response_overlap_audit  # noqa: E402
from mio.formalism.budget_spec import (  # noqa: E402
    BudgetUse,
    build_budget_spec,
    compare_denominator_policies,
)
from mio.formalism.departure_bundle import build_departure_bundle  # noqa: E402
from mio.formalism.exceedance import (  # noqa: E402
    MeasureKind,
    build_exceedance_curve_from_normalized_scores,
)
from mio.formalism.filling_fraction import build_certified_filling_fraction  # noqa: E402
from mio.formalism.isotropy_gap import (  # noqa: E402
    DepthBinMetadata,
    build_depth_bin_f_record,
    build_isotropy_gap,
)
from mio.formalism.normalized_score import (  # noqa: E402
    build_comparator_multiverse_summary,
    build_normalized_score,
)
from htt.infer.matched_complexity import MatchedComplexityHook  # noqa: E402
from htt.infer.null_competition import (  # noqa: E402
    FamilyCompetitionResult,
    NullCompetitionResult,
    build_gf_matched_null_forecast_report,
)
from htt.nulls.local_boost_depth_null import (  # noqa: E402
    DepthBinSpec,
    LocalBoostDepthNull,
    LocalBoostNullConfig,
    build_local_boost_null_fpr_report,
)
from htt.nulls.selection_response_depth import (  # noqa: E402
    SelectionResponseDepthNull,
    SelectionResponseMetadata,
    build_survey_systematic_null_fpr_report,
)


FIGURE_DIR = REPO_ROOT / "figures" / "current"
SNIPPET_DIR = REPO_ROOT / "docs" / "manuscript" / "generated"
PLOT_LIST = REPO_ROOT / "docs" / "generated" / "current_manuscript_plot_list.md"
CURATION_REPORT = REPO_ROOT / "docs" / "generated" / "current_manuscript_figure_curation.json"
SCIENCE_PAYLOAD = REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json"
GF_FORECAST_REPORT_JSON = REPO_ROOT / "docs" / "generated" / "gf_matched_null_forecast_report.json"
GF_FORECAST_REPORT_MD = REPO_ROOT / "docs" / "generated" / "gf_matched_null_forecast_report.md"

COLORS = {
    "common": "#334155",
    "htt": "#0f766e",
    "mio": "#7c2d12",
    "bass": "#6d28d9",
    "obsstat": "#b45309",
    "ok": "#15803d",
    "warn": "#ca8a04",
    "block": "#b91c1c",
    "muted": "#64748b",
    "panel": "#f8fafc",
}
_GIT_STATE_OVERRIDE: tuple[str | None, str] | None = None


@dataclass(frozen=True)
class FigureSpec:
    artifact_id: str
    file_name: str
    title: str
    flow_slot: str
    source_paths: tuple[str, ...]
    caption: str
    label: str
    snippet: str
    builder: Callable[[Path], None]
    transfer_source: str = "none"
    null_mock_status: str = "not_statistical"
    artifact_mode: str = "governance_diagnostic"
    allowed_use: str = "external_audit"
    figure_kind: str = "diagnostic_manuscript_plot"
    owner: str = "COMMON"
    implementation_scope: str = "common"
    caption_policy: tuple[str, ...] = (
        "must_state_diagnostic_only",
        "must_state_no_native_low_ell_solver_output",
        "must_state_no_family_identification",
    )
    promotion_blockers: tuple[str, ...] = (
        "native_solver_validation_absent",
        "native_morphology_atlas_absent",
    )
    caveats: tuple[str, ...] = (
        "Generated from current repo-local metadata only.",
        "Diagnostic-only figure; not externally validated native low-ell output.",
        "No Bianchi family-ID or geometry-detection claim is made.",
    )


def _repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes(paths: tuple[str, ...]) -> list[str]:
    hashes: list[str] = []
    for rel in paths:
        path = REPO_ROOT / rel
        if path.exists():
            hashes.append(f"{rel}:sha256:{_sha256(path)}")
        else:
            hashes.append(f"{rel}:missing")
    return hashes


def _read_text(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _git_state(repo_root: Path = REPO_ROOT) -> tuple[str | None, str]:
    if _GIT_STATE_OVERRIDE is not None:
        return _GIT_STATE_OVERRIDE
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=repo_root,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None, "git_state_unavailable"
    return commit, f"{commit}+dirty" if status else commit


def _config_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _table_after_heading(text: str, heading: str) -> list[dict[str, str]]:
    marker = f"## {heading}"
    idx = text.find(marker)
    if idx < 0:
        return []
    lines = text[idx + len(marker) :].splitlines()
    table_lines: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            started = True
            table_lines.append(stripped)
        elif started:
            break
    if len(table_lines) < 3:
        return []
    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def _sha_label(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _galactic_unit_vector(l_deg: float, b_deg: float) -> tuple[float, float, float]:
    l_rad = np.deg2rad(float(l_deg))
    b_rad = np.deg2rad(float(b_deg))
    vector = np.asarray(
        [
            np.cos(b_rad) * np.cos(l_rad),
            np.cos(b_rad) * np.sin(l_rad),
            np.sin(b_rad),
        ],
        dtype=float,
    )
    vector /= np.linalg.norm(vector)
    return tuple(float(item) for item in vector)


def _external_transfer_metadata() -> dict[str, object]:
    return {
        "transfer_source": "external_transfer",
        "family": "diagnostic_denominator_proxy",
        "valid_range": {"k_min": 1.0e-4, "k_max": 0.2, "ell_min": 2, "ell_max": 64},
        "observable_kind": "scalar_summary",
        "normalization": "dimensionless_denominator_scale",
        "calibration_status": "external_calibrated",
        "caveats": [
            "external transfer conditioned denominator proxy",
            "not native low-ell solver output",
        ],
        "source_ref": "docs/generated/transfer_sensitivity_report.md",
        "version": "current-science-plot-payload-v1",
        "passed_validation_gates": ["external_transfer_provenance_recorded"],
    }


def _budget_specs() -> tuple[object, ...]:
    input_hash = _sha_label("current-science-budget-inputs")
    transfer_metadata = _external_transfer_metadata()
    base = {
        "comparator": "diagnostic_current_code_stress_payload",
        "frame": "observer_scalar_budget",
        "units": "dimensionless",
        "input_hashes": (input_hash,),
        "assumptions": (
            "deterministic_current_code_plot_payload",
            "diagnostic_denominator_sensitivity_only",
        ),
        "config_hash": _sha_label("current-science-budget-config"),
    }
    return (
        build_budget_spec(
            **base,
            policy="MES_linear",
            denominator_value=0.087,
            denominator_label="MES linear ceiling",
            source_description="MIO linearized denominator for budget stress testing",
            native_morphology_atlas_status="not_available_pre_solver",
        ),
        build_budget_spec(
            **base,
            policy="external_transfer",
            denominator_value=0.104,
            denominator_label="external transfer scale",
            transfer_source="external_transfer",
            transfer_spec_id="current.external.transfer.scale.proxy",
            transfer_metadata=transfer_metadata,
            source_description="external-transfer denominator scale used only for sensitivity display",
            native_morphology_atlas_status="not_available_pre_solver",
        ),
        build_budget_spec(
            **base,
            policy="observational",
            denominator_value=0.076,
            denominator_label="directional mock envelope",
            source_description="diagnostic sky-support envelope from current local/null gate machinery",
            sky_support_status="pr040_sky_support_attached",
            covariance_status="diagnostic_covariance_supplied",
            null_mock_status="local_boost_null_bank_generated",
            native_morphology_atlas_status="not_available_pre_solver",
        ),
    )


def _q_comparator_scores() -> tuple[object, ...]:
    samples = (
        (
            "CMB_FLRW_reference",
            {
                "Sigma2_std": 0.052,
                "W2_std": 0.009,
                "Omega_tilt": 0.018,
                "Omega_k_aniso": 0.003,
            },
            0.087,
            "current-code CMB FLRW comparator denominator",
            ("q-cmb-comparator-x",),
            ("q-cmb-comparator-budget",),
        ),
        (
            "observer_frame_reference",
            {
                "Sigma2_std": 0.047,
                "W2_std": 0.012,
                "Omega_tilt": 0.015,
                "Omega_k_aniso": 0.004,
            },
            0.096,
            "current-code observer-frame comparator denominator",
            ("q-observer-comparator-x",),
            ("q-observer-comparator-budget",),
        ),
        (
            "stress_payload_reference",
            {
                "Sigma2_std": 0.058,
                "W2_std": 0.006,
                "Omega_tilt": 0.021,
                "Omega_k_aniso": 0.002,
            },
            0.078,
            "current-code stress-payload comparator denominator",
            ("q-stress-comparator-x",),
            ("q-stress-comparator-budget",),
        ),
    )
    scores = []
    for comparator, components, denominator, label, x_hashes, budget_hashes in samples:
        bundle = build_departure_bundle(
            components,
            comparator=comparator,
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash=_sha_label(f"{comparator}:q-comparator-bundle"),
            input_hashes=x_hashes,
            caveats=(
                "deterministic current-code comparator sample for display metadata only",
            ),
        )
        budget = build_budget_spec(
            policy="MES_linear",
            denominator_value=denominator,
            denominator_label=label,
            comparator=comparator,
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash=_sha_label(f"{comparator}:q-comparator-budget"),
            input_hashes=budget_hashes,
            assumptions=(
                "deterministic current-code comparator sensitivity sample",
            ),
            admissible_uses=(
                BudgetUse.DENOMINATOR_SENSITIVITY,
                BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
                BudgetUse.EXCEEDANCE_THRESHOLD,
            ),
            source_description="MIO comparator sensitivity denominator sample",
            native_morphology_atlas_status="not_available_pre_solver",
        )
        scores.append(
            build_normalized_score(
                bundle,
                budget,
                numerator_policy="absolute",
                artifact_metadata={"report_role": "Q comparator sensitivity"},
            )
        )
    return tuple(scores)


def _pi_policy_display_summary(curve_payload: dict[str, object]) -> dict[str, object]:
    display_metadata = dict(curve_payload["display_metadata"])
    display_metadata["calibration_status"] = "raw_exceedance_only_uncalibrated_no_p_value"
    return {
        "owner": "MIO",
        "implementation_scope": "mio",
        "claim_tier": "diagnostic_only",
        "summary_label": "Pi_policy_display_contract",
        "summary_kind": "noncanonical_pi_policy_metadata_summary",
        "source_score_label": curve_payload["source_score_label"],
        "source_kind": curve_payload["source_kind"],
        "measure_kind": curve_payload["measure_kind"],
        "threshold_policy": curve_payload["threshold_policy"],
        "threshold_registration_status": curve_payload[
            "threshold_registration_status"
        ],
        "threshold_grid": curve_payload["threshold_grid"],
        "look_elsewhere_trials": curve_payload["look_elsewhere_trials"],
        "exceedance_rule": curve_payload["exceedance_rule"],
        "sample_count": curve_payload["sample_count"],
        "calibration_status": "raw_exceedance_only_uncalibrated_no_p_value",
        "covariance_status": curve_payload["covariance_status"],
        "null_mock_status": curve_payload["null_mock_status"],
        "sky_support_status": curve_payload["sky_support_status"],
        "source_curve_config_hash": curve_payload["config_hash"],
        "source_config_hashes": curve_payload["source_config_hashes"],
        "input_hashes": curve_payload["input_hashes"],
        "source_metadata": curve_payload["source_metadata"],
        "display_metadata": display_metadata,
        "artifact_metadata": {
            "report_role": "Pi display policy metadata summary",
            "canonical_pi_curve_payload": "not_exported_in_current_semantic_split",
        },
        "caveats": [
            "Policy summary only; current semantic split does not plot a canonical Pi row.",
            "Raw exceedance metadata is uncalibrated and must not be read as a p-value.",
        ],
        "generating_command": curve_payload["generating_command"],
        "git_commit": curve_payload["git_commit"],
        "worktree_state": curve_payload["worktree_state"],
    }


def _gf_budget(
    *,
    bin_id: str,
    sample_index: int,
    denominator_value: float,
) -> object:
    return build_budget_spec(
        policy="MES_linear",
        denominator_value=denominator_value,
        denominator_label=f"MES depth-gap denominator {bin_id} sample {sample_index}",
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash=_sha_label(f"current-gf-budget-{bin_id}-{sample_index}"),
        input_hashes=(_sha_label(f"current-gf-budget-input-{bin_id}-{sample_index}"),),
        assumptions=(
            "deterministic current-code G_F display contract fixture",
            "samplewise denominator-evolution provenance only",
        ),
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
            BudgetUse.CERTIFIED_FILLING_CEILING,
            BudgetUse.EXCEEDANCE_THRESHOLD,
            BudgetUse.DEPTH_GAP_REFERENCE,
        ),
        is_admissible_ceiling=True,
        source_description="MIO G_F display-contract denominator sample",
        native_morphology_atlas_status="not_available_pre_solver",
    )


def _gf_filling_fraction(
    *,
    bin_id: str,
    x_samples: tuple[float, ...],
    denominator_samples: tuple[float, ...],
    command: str,
    git_commit: str | None,
    worktree: str,
) -> object:
    bundles = []
    budgets = []
    for sample_index, (x_c, denominator) in enumerate(
        zip(x_samples, denominator_samples, strict=True)
    ):
        bundles.append(
            build_departure_bundle(
                {
                    "Sigma2_std": x_c,
                    "W2_std": 0.0,
                    "Omega_tilt": 0.0,
                    "Omega_k_aniso": 0.0,
                },
                comparator="CMB_FLRW_reference",
                frame="normal_frame",
                units="dimensionless_hubble_normalized",
                config_hash=_sha_label(f"current-gf-bundle-{bin_id}-{sample_index}"),
                input_hashes=(
                    _sha_label(f"current-gf-bundle-input-{bin_id}-{sample_index}"),
                ),
                caveats=(
                    "deterministic current-code G_F display contract sample",
                ),
            )
        )
        budgets.append(
            _gf_budget(
                bin_id=bin_id,
                sample_index=sample_index,
                denominator_value=denominator,
            )
        )
    return build_certified_filling_fraction(
        tuple(bundles),
        tuple(budgets),
        generating_command=command,
        git_commit=git_commit,
        worktree_state=worktree,
        artifact_metadata={"report_role": "G_F display contract F sample"},
    )


def _gf_depth_bin(bin_id: str, start: float, stop: float) -> DepthBinMetadata:
    return DepthBinMetadata(
        bin_id=bin_id,
        depth_min=start,
        depth_max=stop,
        depth_unit="redshift",
        depth_convention="z_cmb_bin_edges_left_closed_right_open",
        selection_rule="pre-registered current-code G_F display depth bin",
        selection_hash=_sha_label(f"current-gf-selection-{bin_id}"),
        bin_assignment_hash=_sha_label(f"current-gf-assignment-{bin_id}"),
        sky_support_status="mask_weighted_directional_support",
        mask_status="masked_with_hash",
        covariance_status="diagnostic_unmatched_covariance",
        covariance_metadata={
            "covariance_hash": _sha_label(f"current-gf-covariance-{bin_id}"),
            "shape": [2, 2],
            "estimator": "current_code_diagnostic_fixture",
            "off_diagonal_policy": "included",
            "calibration_status": "diagnostic_unmatched",
        },
        null_mock_status="diagnostic_unmatched_null",
        null_metadata={
            "mock_bank_hash": _sha_label(f"current-gf-null-bank-{bin_id}"),
            "calibration_status": "diagnostic_unmatched",
        },
        denominator_evolution_status="samplewise_denominator_values_recorded",
        sample_count=2,
    )


def _build_gf_payload(command: str, git_commit: str | None, worktree: str) -> dict[str, object]:
    near = build_depth_bin_f_record(
        _gf_filling_fraction(
            bin_id="near",
            x_samples=(0.010, 0.018),
            denominator_samples=(1.0, 0.9),
            command=command,
            git_commit=git_commit,
            worktree=worktree,
        ),
        depth_bin=_gf_depth_bin("near", 0.0, 0.08),
        source_metadata={"source_role": "current_code_gf_display_contract_near"},
    )
    far = build_depth_bin_f_record(
        _gf_filling_fraction(
            bin_id="far",
            x_samples=(0.180, 0.240),
            denominator_samples=(0.72, 0.60),
            command=command,
            git_commit=git_commit,
            worktree=worktree,
        ),
        depth_bin=_gf_depth_bin("far", 0.08, 0.30),
        source_metadata={"source_role": "current_code_gf_display_contract_far"},
    )
    return build_isotropy_gap(
        (near, far),
        reference_bin_id="near",
        comparison_bin_id="far",
        floor_value=0.05,
        floor_label="pre_registered_positive_F_floor",
        floor_reason=(
            "floor chosen before displaying G_F to keep log depth-gap finite "
            "without altering raw F values"
        ),
        generating_command=command,
        git_commit=git_commit,
        worktree_state=worktree,
        artifact_metadata={"report_role": "current G_F display contract"},
        caveats=(
            "Current-code G_F display contract fixture only.",
            "Mean numerator and denominator deltas are provenance summaries only.",
            "Does not authorize local/global separation or model ranking.",
        ),
    ).as_payload()


def _forecast_null_result() -> NullCompetitionResult:
    families = {
        "local_boost_depth_bank": FamilyCompetitionResult(
            family_name="local_boost_depth_bank",
            n_realizations=192,
            n_false_positives=54,
            fpr=54 / 192,
            mean_lnB_null=0.16,
            std_lnB_null=0.05,
            robust=False,
        ),
        "survey_selection_depth_bank": FamilyCompetitionResult(
            family_name="survey_selection_depth_bank",
            n_realizations=192,
            n_false_positives=91,
            fpr=91 / 192,
            mean_lnB_null=0.31,
            std_lnB_null=0.09,
            robust=False,
        ),
    }
    worst = max(families.values(), key=lambda item: item.fpr)
    robust = sum(1 for item in families.values() if item.robust)
    return NullCompetitionResult(
        families_tested=len(families),
        families_robust=robust,
        families_vulnerable=len(families) - robust,
        worst_family=worst.family_name,
        worst_fpr=worst.fpr,
        overall_robust=False,
        family_results=families,
    )


def _build_gf_matched_null_forecast_payload(
    command: str,
    git_commit: str | None,
    worktree: str,
) -> dict[str, object]:
    report = build_gf_matched_null_forecast_report(
        null_result=_forecast_null_result(),
        matched_complexity_hook=MatchedComplexityHook(
            controls_required=("local_boost_depth_bank", "survey_selection_depth_bank"),
            overall_pass=True,
            violations=tuple(),
        ),
        alternative_complexity_score=6,
        null_flexibility_scores={
            "local_boost_depth_bank": 6,
            "survey_selection_depth_bank": 6,
        },
        artifact_id="htt.rev069.gf_matched_null_forecast",
        config_hash=_sha_label("rev069-gf-matched-null-forecast-config"),
        input_hashes=(
            _sha_label("rev069-gf-matched-null-local-bank"),
            _sha_label("rev069-gf-matched-null-survey-bank"),
        ),
        generating_command=command,
        worktree_state=worktree,
        git_commit=git_commit,
        threshold_config_hash=_sha_label("rev069-gf-threshold-policy"),
        threshold_selection_rationale=(
            "pre-registered REV-R069 forecast threshold; failures are reported "
            "as blocked rather than retuned"
        ),
    )
    return report.as_payload()


def _render_gf_forecast_report(payload: dict[str, object]) -> str:
    statement = payload["false_positive_rate_statement"]
    assert isinstance(statement, dict)
    return "\n".join(
        [
            "# G_F Matched-Null Forecast Report",
            "",
            "owner: HTT",
            "implementation_scope: htt",
            f"claim_tier: {payload['claim_tier']}",
            "artifact_mode: forecast_only",
            "allowed_use: external_audit",
            "transfer_source: none",
            "sky_support_status: not_directional",
            f"null_mock_status: {payload['null_mock_status']}",
            f"config_hash: {payload['config_hash']}",
            "input_hashes:",
            *[f"- {item}" for item in payload["input_hashes"]],
            "caveats:",
            "- Forecast-only matched-null diagnostic.",
            "- Does not promote observed-data evidence, global-tilt wording, native solver validation, geometry detection, or family identification.",
            f"generating_command: {payload['generating_command']}",
            f"git_commit_or_worktree_state: {payload['git_commit_or_worktree_state']}",
            "artifact_path: docs/generated/gf_matched_null_forecast_report.json",
            "",
            "## Status",
            "",
            f"- matched_null_status: `{payload['matched_null_status']}`",
            f"- local_global_separation_status: `{payload['local_global_separation_status']}`",
            f"- observed_data_evidence: `{payload['observed_data_evidence']}`",
            f"- global_tilt_wording_allowed: `{payload['global_tilt_wording_allowed']}`",
            f"- retuning_after_failure: `{payload['retuning_after_failure']}`",
            f"- forecast_source_kind: `{payload['forecast_source_kind']}`",
            f"- forecast_source_description: {payload['forecast_source_description']}",
            f"- FPR statement: {statement['wording']}",
            "",
        ]
    )


def _write_gf_forecast_report(payload: dict[str, object]) -> None:
    GF_FORECAST_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    GF_FORECAST_REPORT_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    GF_FORECAST_REPORT_MD.write_text(
        _render_gf_forecast_report(payload),
        encoding="utf-8",
    )


def _build_transfer_budget_payload(
    command: str,
    git_commit: str | None,
    worktree: str,
) -> dict[str, object]:
    x_reference = 0.064
    reference_departure = build_departure_bundle(
        {
            "Sigma2_std": 0.052,
            "W2_std": 0.009,
            "Omega_tilt": 0.018,
            "Omega_k_aniso": 0.003,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="current-code-diagnostic-x-reference-v1",
        input_hashes=("scripts/make_current_manuscript_figures.py:x_reference",),
        caveats=(
            "deterministic current-code sector decomposition for display metadata only",
        ),
    )
    points = compare_denominator_policies(
        _budget_specs(),
        relative_shifts=(-0.2, 0.0, 0.2),
    )
    baseline_by_policy = {
        point.policy.value: x_reference / point.denominator_value
        for point in points
        if point.relative_shift == 0.0
    }
    rows: list[dict[str, object]] = []
    for point in points:
        q_value = x_reference / point.denominator_value
        baseline_q = baseline_by_policy[point.policy.value]
        payload = point.as_payload()
        payload.update(
            {
                "x_reference": x_reference,
                "Q_diagnostic": q_value,
                "relative_Q_vs_policy_baseline": q_value / baseline_q - 1.0,
            }
        )
        rows.append(payload)
    q_scores = _q_comparator_scores()
    q_summary = build_comparator_multiverse_summary(
        q_scores,
        baseline_comparator="CMB_FLRW_reference",
        generating_command=command,
        git_commit=git_commit,
        worktree_state=worktree,
        artifact_metadata={"report_role": "Q comparator specification sensitivity"},
    )
    pi_policy_curve = build_exceedance_curve_from_normalized_scores(
        q_scores,
        thresholds=(0.65, 0.75, 0.85),
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        look_elsewhere_trials=1,
        generating_command=command,
        git_commit=git_commit,
        worktree_state=worktree,
        artifact_metadata={"report_role": "Pi policy metadata summary"},
    )
    pi_policy_summary = _pi_policy_display_summary(pi_policy_curve.as_payload())
    return {
        "x_reference": x_reference,
        "x_reference_comparator": reference_departure.comparator,
        "x_reference_frame": reference_departure.frame,
        "x_reference_units": reference_departure.units,
        "x_reference_sector_profile": reference_departure.sector_profile,
        "x_reference_display_metadata": reference_departure.display_metadata,
        "q_comparator_multiverse": q_summary.as_payload(),
        "pi_policy_summary": pi_policy_summary,
        "relative_shifts": [-0.2, 0.0, 0.2],
        "points": rows,
        "contract": "MIO BudgetSpec/compare_denominator_policies",
        "interpretation": "denominator-policy sensitivity only; not a model likelihood",
    }


def _response_overlap_payload(command: str, git_commit: str | None, worktree: str) -> dict[str, object]:
    covariance = np.diag((1.0, 0.82, 1.15, 1.35, 0.94))
    audit = build_response_overlap_audit(
        local_boost_response=(0.92, 0.34, 0.11, -0.06, 0.25),
        global_tilt_response=(0.31, 0.84, -0.24, 0.38, -0.05),
        covariance=covariance,
        observable_labels=(
            "axis_projection",
            "quadrupole_template",
            "depth_gradient_G_F",
            "morphology_axis_score",
            "selection_residual",
        ),
        nuisance_responses=((0.08, 0.16, 0.31, 0.10, 0.22),),
        nuisance_labels=("selection_depth_mode",),
        artifact_id="htt.current_science_plot_payload.response_overlap",
        artifact_path="docs/generated/current_science_plot_payload.json#/response_overlap",
        input_hashes=_input_hashes(
            (
                "htt/htt/htt/departure/response_overlap.py",
                "docs/generated/result_pack_B.md",
            )
        ),
        generating_command=command,
        git_commit=git_commit,
        worktree_state=worktree,
        covariance_status="diagnostic_covariance_supplied",
        null_mock_status="paired_with_current_code_null_fpr_payload",
    )
    payload = audit.as_payload()
    payload["covariance"] = covariance.tolist()
    return payload


def _null_config(
    *,
    seed: int,
    command: str,
    worktree: str,
    git_commit: str | None,
    label: str,
    target_direction: tuple[float, float, float],
) -> LocalBoostNullConfig:
    depth_bins = (
        DepthBinSpec("z0_0p04", 0.0, 0.04, 0.0, 170.0, response_weight=0.88),
        DepthBinSpec("z0p04_0p08", 0.04, 0.08, 170.0, 350.0, response_weight=1.0),
        DepthBinSpec("z0p08_0p16", 0.08, 0.16, 350.0, 720.0, response_weight=1.12),
        DepthBinSpec("z0p16_0p30", 0.16, 0.30, 720.0, 1280.0, response_weight=0.92),
    )
    return LocalBoostNullConfig(
        n_mocks=192,
        seed=seed,
        depth_bins=depth_bins,
        target_direction=target_direction,
        sky_support_hash=_sha_label(f"{label}-sky-support"),
        mask_hash=_sha_label(f"{label}-mask"),
        scan_volume_hash=_sha_label(f"{label}-scan-volume"),
        config_hash=_sha_label(f"{label}-config"),
        input_hashes=(_sha_label(f"{label}-input"),),
        generating_command=command,
        worktree_state=worktree,
        git_commit=git_commit,
        gf_threshold=2.2,
        direction_threshold_deg=25.0,
        look_elsewhere_trials=3,
        max_false_positive_rate=0.15,
        amplitude_beta_mean=1.0e-3,
        amplitude_beta_sigma=2.0e-4,
        direction_jitter_sigma=0.055,
        gf_beta_scale=1.05e-3,
        covariance_status="diagnostic_covariance_supplied",
        sky_support_status="pr040_sky_support_attached",
        null_mock_status="current_code_diagnostic_null_bank_generated",
    )


def _build_rank_null_payload(command: str, git_commit: str | None, worktree: str) -> dict[str, object]:
    response = _response_overlap_payload(command, git_commit, worktree)
    target = _galactic_unit_vector(264.0, 48.0)
    local_config = _null_config(
        seed=24061,
        command=command,
        worktree=worktree,
        git_commit=git_commit,
        label="local-boost-null",
        target_direction=target,
    )
    local_bank = LocalBoostDepthNull(local_config).generate()
    local_report = build_local_boost_null_fpr_report(
        local_bank,
        response_overlap_audit=build_response_overlap_audit(
            local_boost_response=response["local_boost_response"],
            global_tilt_response=response["global_tilt_response"],
            covariance=response["covariance"],
            observable_labels=response["observable_labels"],
            nuisance_responses=response["nuisance_responses"],
            nuisance_labels=response["nuisance_labels"],
            artifact_id="htt.current_science_plot_payload.response_overlap.local_fpr",
            artifact_path="docs/generated/current_science_plot_payload.json#/local_null_fpr",
            input_hashes=response["input_hashes"],
            generating_command=command,
            git_commit=git_commit,
            worktree_state=worktree,
            covariance_status="diagnostic_covariance_supplied",
            null_mock_status="local_boost_null_fpr_available",
        ),
    )
    survey_config = _null_config(
        seed=24062,
        command=command,
        worktree=worktree,
        git_commit=git_commit,
        label="survey-systematic-null",
        target_direction=target,
    )
    selection = SelectionResponseMetadata(
        selection_function_id="current_code_depth_selection_stress",
        selection_function_hash=_sha_label("selection-function"),
        selection_metadata_hash=_sha_label("selection-metadata"),
        depth_response_hash=_sha_label("selection-depth-response"),
        source_catalog="deterministic_current_code_gate_stress_payload",
        completeness_status="selection_response_metadata_attached",
        completeness_axis=_galactic_unit_vector(275.0, 35.0),
        depth_response_label="coherent_depth_selection_axis",
    )
    survey_bank = SelectionResponseDepthNull(
        survey_config,
        selection_metadata=selection,
    ).generate()
    survey_report = build_survey_systematic_null_fpr_report(
        survey_bank,
        response_overlap_audit=build_response_overlap_audit(
            local_boost_response=response["local_boost_response"],
            global_tilt_response=response["global_tilt_response"],
            covariance=response["covariance"],
            observable_labels=response["observable_labels"],
            nuisance_responses=response["nuisance_responses"],
            nuisance_labels=response["nuisance_labels"],
            artifact_id="htt.current_science_plot_payload.response_overlap.survey_fpr",
            artifact_path="docs/generated/current_science_plot_payload.json#/survey_null_fpr",
            input_hashes=response["input_hashes"],
            generating_command=command,
            git_commit=git_commit,
            worktree_state=worktree,
            covariance_status="diagnostic_covariance_supplied",
            null_mock_status="survey_systematic_null_fpr_available",
        ),
    )
    return {
        "response_overlap": response,
        "local_null_bank": local_bank.to_payload(),
        "local_null_fpr": local_report.to_metadata(),
        "survey_systematic_bank": survey_bank.to_payload(),
        "survey_systematic_fpr": survey_report.to_metadata(),
    }


def _depth_p95_by_label(bank_payload: dict[str, object]) -> dict[str, float]:
    distributions = bank_payload["distributions"]
    assert isinstance(distributions, dict)
    g_f = distributions["g_f"]
    assert isinstance(g_f, dict)
    by_depth = g_f["by_depth"]
    assert isinstance(by_depth, dict)
    return {
        str(label): float(values["p95"])
        for label, values in by_depth.items()
        if isinstance(values, dict)
    }


def _build_semantic_and_vector_payload(
    transfer_payload: dict[str, object],
    rank_payload: dict[str, object],
    gf_payload: dict[str, object],
    gf_forecast_payload: dict[str, object],
) -> dict[str, object]:
    points = [
        point
        for point in transfer_payload["points"]
        if isinstance(point, dict) and float(point["relative_shift"]) == 0.0
    ]
    q_summary = transfer_payload["q_comparator_multiverse"]
    assert isinstance(q_summary, dict)
    pi_policy_summary = transfer_payload["pi_policy_summary"]
    assert isinstance(pi_policy_summary, dict)
    q_by_comparator = q_summary["q_by_comparator"]
    assert isinstance(q_by_comparator, dict)
    q_values = np.asarray(
        [float(value) for value in q_by_comparator.values()],
        dtype=float,
    )
    local_fpr = rank_payload["local_null_fpr"]["false_positive_rate"]
    survey_fpr = rank_payload["survey_systematic_fpr"]["false_positive_rate"]
    assert isinstance(local_fpr, dict)
    assert isinstance(survey_fpr, dict)
    local_depth = _depth_p95_by_label(rank_payload["local_null_bank"])
    survey_depth = _depth_p95_by_label(rank_payload["survey_systematic_bank"])
    depth_spread = float(
        np.std(np.asarray(list(local_depth.values()) + list(survey_depth.values()), dtype=float))
    )
    q_spread = float(np.percentile(q_values, 95.0) - np.percentile(q_values, 5.0))
    singular_values = np.asarray(
        rank_payload["response_overlap"]["singular_values"],
        dtype=float,
    )
    x_sector_profile = transfer_payload["x_reference_sector_profile"]
    assert isinstance(x_sector_profile, dict)
    x_display_metadata = {
        "requires_sector_profile": True,
        "requires_absolute_component_total": True,
        "requires_cancellation_index": True,
        "requires_magnitude_companion_M": True,
        "requires_comparator_label": True,
        "comparator": transfer_payload["x_reference_comparator"],
        "frame": transfer_payload["x_reference_frame"],
        "units": transfer_payload["x_reference_units"],
        "sector_profile_ref": "/transfer_sensitivity/x_reference_sector_profile",
        "M_sector_magnitude": float(x_sector_profile["absolute_component_total"]),
        "interpretation": (
            "x_C is a signed comparator projection; near-zero x_C can reflect "
            "inter-sector cancellation, not isotropy."
        ),
        "blocked_use_codes": [
            "isotropy_certificate",
            "scalar_classification",
            "htt_inference_consumption",
            "solver_validation",
            "material_occupancy",
        ],
    }
    q_display_metadata = dict(q_summary["display_metadata"])
    q_display_metadata.update(
        {
            "requires_comparator_label": True,
            "comparator": q_summary["baseline_comparator"],
            "comparator_multiverse_ref": (
                "/transfer_sensitivity/q_comparator_multiverse"
            ),
            "q_spread_absolute": q_summary["q_spread_absolute"],
            "q_spread_relative_to_baseline": (
                q_summary["q_spread_relative_to_baseline"]
            ),
            "config_hash": q_summary["config_hash"],
            "input_hashes": q_summary["input_hashes"],
        }
    )
    departure_display_contract = {
        "required_for_symbols": ["x", "F"],
        "requires_sector_profile": True,
        "requires_absolute_component_total": True,
        "requires_cancellation_index": True,
        "requires_magnitude_companion_M": True,
        "scope": (
            "Every displayed x_C or F summary must expose a signed sector "
            "profile, unsigned sector magnitude M, and cancellation metadata."
        ),
        "F_definition": (
            "F is x_C divided by an admissible sign-clean ceiling U; no "
            "clipping or volume-occupancy interpretation is permitted."
        ),
        "x_C_interpretation": (
            "x_C is a signed comparator projection; x_C near zero can reflect "
            "cancellation, not isotropy."
        ),
        "blocked_use_codes": [
            "isotropy_certificate",
            "scalar_classification",
            "htt_inference_consumption",
            "solver_validation",
            "material_occupancy",
        ],
    }
    cancellation_bundle = build_departure_bundle(
        {
            "Sigma2_std": 0.004,
            "W2_std": 0.004,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="current-code-cancellation-counterexample-v1",
        input_hashes=(
            "scripts/make_current_manuscript_figures.py:cancellation_counterexample",
        ),
        caveats=(
            "worked formalism counterexample for display metadata only",
        ),
    )
    cancellation_counterexample = {
        "components": cancellation_bundle.component_breakdown.component_values,
        "signed_component_vector": (
            cancellation_bundle.component_breakdown.signed_contributions
        ),
        "sector_profile": cancellation_bundle.sector_profile,
        "x_C": cancellation_bundle.x_C,
        "absolute_component_total": cancellation_bundle.absolute_component_total,
        "M_sector_magnitude": cancellation_bundle.sector_magnitude_companion,
        "cancellation_index": cancellation_bundle.cancellation_index,
        "interpretation": (
            "This worked x_C=0 profile has nonzero sector magnitude; the "
            "near-zero scalar is cancellation-compatible and not isotropy."
        ),
    }
    semantic = [
        {
            "symbol": "x",
            "label": "departure size",
            "owner": "MIO",
            "display_value": float(transfer_payload["x_reference"]),
            "definition": "raw diagnostic departure scalar in the stress payload",
            "display_metadata": x_display_metadata,
        },
        {
            "symbol": "Q",
            "label": "budget-normalized score",
            "owner": "MIO",
            "display_value": float(q_summary["baseline_q"]),
            "definition": "x divided by explicit denominator policy",
            "display_metadata": q_display_metadata,
        },
        {
            "symbol": "Q-spread",
            "label": "comparator spread",
            "owner": "MIO",
            "display_value": float(q_summary["q_spread_absolute"]),
            "definition": (
                "specification-curve spread across explicit Q comparators"
            ),
            "display_metadata": dict(q_summary["display_metadata"]),
        },
        {
            "symbol": "1-FPR",
            "label": "local-null survival",
            "owner": "HTT",
            "display_value": 1.0 - float(local_fpr["adjusted"]),
            "definition": "one minus look-elsewhere adjusted local-null false-positive rate",
        },
        {
            "symbol": "G-envelope",
            "label": "depth response",
            "owner": "HTT",
            "display_value": min(1.0, float(np.log1p(max(survey_depth.values()))) / 4.0),
            "definition": "normalized log depth-response envelope from null-bank payload",
        },
    ]
    vectors = [
        {
            "name": "response rank separation",
            "magnitude": float(np.min(singular_values) / np.max(singular_values)),
            "missing_prerequisites": [],
        },
        {
            "name": "denominator policy spread",
            "magnitude": min(1.0, q_spread),
            "missing_prerequisites": ["native_morphology_atlas_absent"],
        },
        {
            "name": "local-null FPR headroom",
            "magnitude": max(0.0, 1.0 - float(local_fpr["adjusted"]) / float(local_fpr["max_false_positive_rate"])),
            "missing_prerequisites": [],
        },
        {
            "name": "survey systematic pressure",
            "magnitude": min(1.0, float(survey_fpr["adjusted"]) / float(survey_fpr["max_false_positive_rate"])),
            "missing_prerequisites": ["survey_axis_external_validation_absent"],
        },
        {
            "name": "depth G_F spread",
            "magnitude": min(1.0, depth_spread / max(survey_depth.values())),
            "missing_prerequisites": ["matched_observed_depth_residual_absent"],
        },
    ]
    gf_display_contract = {
        "summary_label": "G_F_display_contract",
        "owner": "MIO",
        "implementation_scope": "mio",
        "claim_tier": "diagnostic_only",
        "score_label": "G_F",
        "score_kind": gf_payload["score_kind"],
        "G_F": gf_payload["G_F"],
        "log_g_F": gf_payload["log_g_F"],
        "reference_bin_id": gf_payload["reference_bin_id"],
        "comparison_bin_id": gf_payload["comparison_bin_id"],
        "floor_value": gf_payload["floor_value"],
        "floor_label": gf_payload["floor_label"],
        "floor_reason": gf_payload["floor_reason"],
        "floor_applied_by_bin": gf_payload["floor_applied_by_bin"],
        "raw_F_by_bin": gf_payload["raw_F_by_bin"],
        "effective_F_by_bin": gf_payload["effective_F_by_bin"],
        "depth_bins": gf_payload["depth_bins"],
        "denominator_evolution_split": gf_payload[
            "denominator_evolution_split"
        ],
        "g_f_payload": gf_payload,
        "g_f_payload_ref": "/semantic_and_vectors/g_f_display_contract/g_f_payload",
        "floor_applied_by_bin_ref": (
            "/semantic_and_vectors/g_f_display_contract/floor_applied_by_bin"
        ),
        "denominator_evolution_split_ref": (
            "/semantic_and_vectors/g_f_display_contract/denominator_evolution_split"
        ),
        "depth_bin_metadata_ref": (
            "/semantic_and_vectors/g_f_display_contract/depth_bins"
        ),
        "requires_floor_applied_by_bin": True,
        "requires_raw_effective_f_by_bin": True,
        "requires_denominator_evolution_split": True,
        "requires_depth_bin_metadata": True,
        "forecast_only": True,
        "observed_data_evidence": False,
        "matched_null_forecast_status": gf_forecast_payload[
            "matched_null_status"
        ],
        "local_global_separation_status": (
            "blocked_existing_null_bank_insufficient"
        ),
        "global_tilt_wording_allowed": False,
        "forecast_report_ref": "docs/generated/gf_matched_null_forecast_report.json",
        "interpretation": (
            "G_F is computed from floor-stabilized per-bin F summaries. "
            "Mean numerator and denominator deltas are provenance summaries "
            "only; they do not decompose the reported G_F."
        ),
        "blocked_use_codes": [
            "htt_evidence",
            "posterior_claim",
            "global_tilt_claim",
            "family_identification",
            "native_solver_validation",
            "geometry_detection",
        ],
    }
    return {
        "semantic_split": semantic,
        "diagnostic_vectors": vectors,
        "depth_p95": {"local_null": local_depth, "survey_systematic": survey_depth},
        "departure_display_contract": departure_display_contract,
        "cancellation_counterexample": cancellation_counterexample,
        "pi_display_contract": dict(pi_policy_summary["display_metadata"]),
        "g_f_display_contract": gf_display_contract,
        "g_f_matched_null_forecast": gf_forecast_payload,
        "interpretation": (
            "normalized display values; x and Q keep canonical MIO meanings, "
            "x displays require sector/cancellation/M metadata, Q displays "
            "carry comparator-multiverse specification-curve metadata, G_F "
            "display metadata exposes floor/split provenance, and 1-FPR plus "
            "G-envelope remain noncanonical current-code proxies"
        ),
    }


def _write_current_science_payload(command: str) -> dict[str, object]:
    git_commit, worktree = _git_state()
    transfer_payload = _build_transfer_budget_payload(command, git_commit, worktree)
    rank_payload = _build_rank_null_payload(command, git_commit, worktree)
    gf_payload = _build_gf_payload(command, git_commit, worktree)
    gf_forecast_payload = _build_gf_matched_null_forecast_payload(
        command,
        git_commit,
        worktree,
    )
    semantic_payload = _build_semantic_and_vector_payload(
        transfer_payload,
        rank_payload,
        gf_payload,
        gf_forecast_payload,
    )
    _write_gf_forecast_report(gf_forecast_payload)
    payload = {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "mixed_none_and_external_transfer_conditioned",
        "sky_support_status": "diagnostic_sky_support_attached_for_null_stress_payload",
        "null_mock_status": "current_code_diagnostic_null_banks_generated",
        "schema_version": "common.current_science_plot_payload.v1",
        "artifact_path": _repo_relative(SCIENCE_PAYLOAD),
        "config_hash": _config_hash(
            {
                "command": command,
                "payload_version": "current-science-plot-payload-v1",
                "inputs": [
                    "htt.mio.formalism.budget_spec",
                    "htt.mio.formalism.component_breakdown",
                    "htt.mio.formalism.departure_bundle",
                    "htt.mio.formalism.exceedance",
                    "htt.mio.formalism.filling_fraction",
                    "htt.mio.formalism.isotropy_gap",
                    "htt.mio.formalism.normalized_score",
                    "htt.departure.response_overlap",
                    "htt.infer.null_competition",
                    "htt.nulls.local_boost_depth_null",
                    "htt.nulls.selection_response_depth",
                ],
            }
        ),
        "input_hashes": _input_hashes(
            (
                "scripts/make_current_manuscript_figures.py",
                "htt/mio/formalism/budget_spec.py",
                "htt/mio/formalism/component_breakdown.py",
                "htt/mio/formalism/departure_bundle.py",
                "htt/mio/formalism/exceedance.py",
                "htt/mio/formalism/filling_fraction.py",
                "htt/mio/formalism/isotropy_gap.py",
                "htt/mio/formalism/normalized_score.py",
                "htt/htt/htt/infer/null_competition.py",
                "htt/htt/htt/departure/response_overlap.py",
                "htt/htt/htt/nulls/local_boost_depth_null.py",
                "htt/htt/htt/nulls/selection_response_depth.py",
                "docs/generated/transfer_sensitivity_report.md",
                "docs/generated/result_pack_A.md",
                "docs/generated/result_pack_B.md",
                "docs/generated/result_pack_C.md",
            )
        ),
        "caveats": [
            "Deterministic current-code physics diagnostic payload for manuscript plots.",
            "Not an observed-data production result.",
            "No native low-ell solver output is represented.",
            "No Bianchi family-ID or geometry-detection claim is made.",
        ],
        "generating_command": command,
        "git_commit": git_commit,
        "git_commit_or_worktree_state": worktree,
        "transfer_sensitivity": transfer_payload,
        "rank_and_null_fpr": rank_payload,
        "semantic_and_vectors": semantic_payload,
    }
    SCIENCE_PAYLOAD.parent.mkdir(parents=True, exist_ok=True)
    SCIENCE_PAYLOAD.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _read_science_payload() -> dict[str, object]:
    return json.loads(SCIENCE_PAYLOAD.read_text(encoding="utf-8"))


def _style_axes(ax: plt.Axes) -> None:
    ax.set_facecolor(COLORS["panel"])
    ax.grid(axis="x", color="#cbd5e1", linewidth=0.7, alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#94a3b8")
    ax.spines["bottom"].set_color("#94a3b8")
    ax.tick_params(colors="#334155", labelsize=9)


def _save_figure(fig: plt.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _plot_dag_progress(output: Path) -> None:
    payload = json.loads(_read_text("docs/generated/status_snapshot.json"))
    rows = payload["rows"]
    owners = sorted({row["owner"] for row in rows})
    implemented = [sum(1 for row in rows if row["owner"] == owner and row["implemented"]) for owner in owners]
    smoke = [sum(1 for row in rows if row["owner"] == owner and row["smoke_tested"]) for owner in owners]
    production = [
        sum(1 for row in rows if row["owner"] == owner and row["production_validated"])
        for owner in owners
    ]
    y = np.arange(len(owners))
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    ax.barh(y + 0.18, implemented, height=0.32, color="#0f766e", label="implemented")
    ax.barh(y - 0.18, smoke, height=0.32, color="#ca8a04", label="smoke tested")
    ax.scatter(production, y, color="#b91c1c", s=48, zorder=3, label="production validated")
    ax.set_yticks(y, owners)
    ax.set_xlabel("PR count by owner")
    ax.set_title("Current DAG status snapshot", loc="left", fontweight="bold")
    _style_axes(ax)
    total = payload["metadata"]["total_prs"]
    complete = payload["metadata"]["completed_prs"]
    ax.text(
        0.99,
        0.05,
        f"{complete}/{total} bookkeeping-complete; production validation remains false",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color=COLORS["common"],
    )
    ax.legend(loc="lower right", frameon=True, fontsize=8)
    _save_figure(fig, output)


def _plot_transfer_provenance(output: Path) -> None:
    text = _read_text("docs/generated/transfer_sensitivity_report.md")
    rows = _table_after_heading(text, "Current Transfer Dependencies")
    source_counts: dict[str, int] = {}
    callable_counts = {"callable": 0, "metadata_only": 0}
    for row in rows:
        source_counts[row["source"]] = source_counts.get(row["source"], 0) + 1
        callable_counts["callable" if row.get("callable") else "metadata_only"] += 1
    downstream = _table_after_heading(text, "Downstream Result-Card Status")
    downstream_status = {
        "external/proxy rows": sum(
            1
            for row in downstream
            if "external" in row.get("transfer_source", "").lower()
            or "proxy" in row.get("transfer_source", "").lower()
            or "aniclass" in row.get("transfer_source", "").lower()
        ),
        "native schema-only rows": sum(
            1
            for row in downstream
            if "native" in row.get("transfer_source", "").lower()
        ),
    }
    source_labels = list(source_counts)
    labels = [label.replace("_", "\n") for label in source_labels]
    values = [source_counts[label] for label in source_labels]
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.5), gridspec_kw={"width_ratios": [1.15, 1]})
    axes[0].bar(labels, values, color=["#0f766e", "#b45309", "#6d28d9"][: len(labels)])
    axes[0].set_title("Current transfer dependencies", loc="left", fontweight="bold")
    axes[0].set_ylabel("registered paths")
    _style_axes(axes[0])
    axes[0].tick_params(axis="x", rotation=0)
    ds_label_keys = list(downstream_status)
    ds_labels = [label.replace(" rows", "\nrows") for label in ds_label_keys]
    ds_values = [downstream_status[label] for label in ds_label_keys]
    axes[1].barh(ds_labels, ds_values, color=["#ca8a04", "#b91c1c"])
    axes[1].set_title("Downstream status rows", loc="left", fontweight="bold")
    axes[1].set_xlabel("row count")
    _style_axes(axes[1])
    _save_figure(fig, output)


def _plot_transfer_sensitivity_tornado(output: Path) -> None:
    payload = _read_science_payload()["transfer_sensitivity"]
    assert isinstance(payload, dict)
    points = [point for point in payload["points"] if isinstance(point, dict)]
    policies = sorted({str(point["denominator_policy"]) for point in points})
    baseline: list[float] = []
    q_min: list[float] = []
    q_max: list[float] = []
    transfer_flags: list[str] = []
    for policy in policies:
        policy_points = [point for point in points if point["denominator_policy"] == policy]
        q_values = np.asarray([float(point["Q_diagnostic"]) for point in policy_points], dtype=float)
        baseline_point = next(
            point for point in policy_points if float(point["relative_shift"]) == 0.0
        )
        baseline.append(float(baseline_point["Q_diagnostic"]))
        q_min.append(float(np.min(q_values)))
        q_max.append(float(np.max(q_values)))
        transfer_flags.append(str(baseline_point["transfer_source"]))

    y = np.arange(len(policies))
    left_err = np.asarray(baseline) - np.asarray(q_min)
    right_err = np.asarray(q_max) - np.asarray(baseline)
    colors = [
        COLORS["bass"] if "external" in source else COLORS["mio"]
        for source in transfer_flags
    ]
    fig, ax = plt.subplots(figsize=(9.8, 5.2))
    ax.barh(y, baseline, color=colors, alpha=0.85)
    ax.errorbar(
        baseline,
        y,
        xerr=np.vstack([left_err, right_err]),
        fmt="none",
        ecolor="#111827",
        elinewidth=1.2,
        capsize=4,
    )
    labels = [policy.replace("_", "\n") for policy in policies]
    ax.set_yticks(y, labels)
    ax.set_xlabel("Q diagnostic under +/-20% denominator shifts")
    ax.set_title("Transfer/denominator sensitivity of Q", loc="left", fontweight="bold")
    _style_axes(ax)
    for idx, source in enumerate(transfer_flags):
        ax.text(
            q_max[idx] + 0.02,
            idx,
            source.replace("_", " "),
            va="center",
            fontsize=8.5,
            color=COLORS["common"],
        )
    ax.text(
        0.99,
        0.04,
        "MIO denominator policy scan; external-transfer row is conditional, not native",
        transform=ax.transAxes,
        ha="right",
        fontsize=8.5,
        color=COLORS["common"],
    )
    _save_figure(fig, output)


def _plot_scalar_morphology_boundary(output: Path) -> None:
    text = _read_text("docs/generated/result_pack_A.md")
    rows = _table_after_heading(text, "Comparison Matrix")
    scalars = ["Q", "F", "Pi"]
    morphology = ["Low-ell scalar features", "Morphology axes", "MES I_morph"]
    matrix = np.zeros((len(scalars), len(morphology)))
    for row in rows:
        if row.get("Status") == "diagnostic_side_by_side":
            matrix[scalars.index(row["Scalar"]), morphology.index(row["Morphology/MES"])] = 1
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    ax.imshow(matrix, cmap=matplotlib.colors.ListedColormap(["#e2e8f0", "#0f766e"]), vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(morphology)), morphology, rotation=20, ha="right")
    ax.set_yticks(np.arange(len(scalars)), scalars)
    for i in range(len(scalars)):
        for j in range(len(morphology)):
            ax.text(j, i, "side-by-side\nonly", ha="center", va="center", color="white", fontsize=9)
    ax.set_title("Scalar diagnostics vs morphology/MES boundary", loc="left", fontweight="bold")
    ax.tick_params(colors="#334155", labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    _save_figure(fig, output)


def _plot_local_global_gates(output: Path) -> None:
    text = _read_text("docs/generated/result_pack_B.md")
    rows = _table_after_heading(text, "Rank And FPR Scenarios")
    labels = [row["Scenario"].replace("_", " ") for row in rows]
    status = [row["Status"] for row in rows]
    values = [1 for _ in rows]
    colors = [
        COLORS["ok"] if item == "local_global_discrimination_candidate" else COLORS["block"]
        for item in status
    ]
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(10.2, 5.1))
    ax.barh(y, values, color=colors)
    ax.set_yticks(y, labels)
    ax.set_xticks([])
    ax.set_title("Local/global discrimination gate scenarios", loc="left", fontweight="bold")
    for idx, row in enumerate(rows):
        ax.text(
            0.02,
            idx,
            row["Allowed Phrase"],
            va="center",
            ha="left",
            color="white",
            fontsize=8.5,
        )
    ax.invert_yaxis()
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
    _save_figure(fig, output)


def _plot_local_global_rank_fpr(output: Path) -> None:
    payload = _read_science_payload()["rank_and_null_fpr"]
    assert isinstance(payload, dict)
    response = payload["response_overlap"]
    assert isinstance(response, dict)
    singular_values = np.asarray(response["singular_values"], dtype=float)
    local_fpr = payload["local_null_fpr"]["false_positive_rate"]
    survey_fpr = payload["survey_systematic_fpr"]["false_positive_rate"]
    assert isinstance(local_fpr, dict)
    assert isinstance(survey_fpr, dict)
    fpr_labels = ["local-only null", "survey/systematic null"]
    adjusted = [float(local_fpr["adjusted"]), float(survey_fpr["adjusted"])]
    interval = [
        tuple(float(item) for item in local_fpr["adjusted_interval"]),
        tuple(float(item) for item in survey_fpr["adjusted_interval"]),
    ]
    threshold = float(local_fpr["max_false_positive_rate"])

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.8), gridspec_kw={"width_ratios": [1, 1.25]})
    axes[0].bar(np.arange(len(singular_values)), singular_values, color="#0f766e")
    axes[0].set_xticks(np.arange(len(singular_values)), [f"s{i+1}" for i in range(len(singular_values))])
    axes[0].set_ylabel("projected singular value")
    axes[0].set_title(
        f"rank={response['projected_rank']}; rho={float(response['rho_LB_GT']):.2f}",
        loc="left",
        fontweight="bold",
    )
    _style_axes(axes[0])

    y = np.arange(len(fpr_labels))
    colors = [COLORS["ok"], COLORS["warn"]]
    axes[1].barh(y, adjusted, color=colors)
    for idx, (lo, hi) in enumerate(interval):
        axes[1].plot([lo, hi], [idx, idx], color="#111827", linewidth=1.5)
        axes[1].plot([lo, lo], [idx - 0.08, idx + 0.08], color="#111827", linewidth=1.5)
        axes[1].plot([hi, hi], [idx - 0.08, idx + 0.08], color="#111827", linewidth=1.5)
    axes[1].axvline(threshold, color=COLORS["block"], linestyle="--", linewidth=1.2)
    axes[1].set_yticks(y, fpr_labels)
    axes[1].set_xlabel("look-elsewhere adjusted FPR")
    axes[1].set_title("Current-code null FPR stress reports", loc="left", fontweight="bold")
    axes[1].set_xlim(0, max(1.0, max(item[1] for item in interval) * 1.1))
    _style_axes(axes[1])
    axes[1].text(
        threshold,
        -0.42,
        "gate",
        ha="center",
        va="bottom",
        fontsize=8,
        color=COLORS["block"],
    )
    fig.text(
        0.99,
        0.01,
        "diagnostic gate stress payload; no posterior/evidence or family-ID claim",
        ha="right",
        fontsize=8.5,
        color=COLORS["common"],
    )
    _save_figure(fig, output)


def _plot_mio_certificate_status(output: Path) -> None:
    text = _read_text("docs/generated/result_pack_C.md")
    rows = _table_after_heading(text, "Certificate Rows")
    labels = [row["Name"].replace(" certificate", "").replace(" context", "") for row in rows]
    blocked_counts: list[int] = []
    diagnostic_counts: list[int] = []
    for row in rows:
        tokens = [token.strip() for token in row["Diagnostic Statuses"].split(",")]
        blocked_counts.append(sum(1 for token in tokens if token.startswith("blocked")))
        diagnostic_counts.append(len(tokens) - blocked_counts[-1])
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(10.2, 5.0))
    ax.barh(y, blocked_counts, color=COLORS["block"], label="blocked/missing-gate labels")
    ax.barh(
        y,
        diagnostic_counts,
        left=blocked_counts,
        color=COLORS["warn"],
        label="diagnostic/descriptive labels",
    )
    ax.set_yticks(y, labels)
    ax.set_xlabel("status label count")
    ax.set_title("MIO diagnostic certificate readiness", loc="left", fontweight="bold")
    ax.invert_yaxis()
    _style_axes(ax)
    ax.legend(loc="lower right", frameon=True, fontsize=8)
    _save_figure(fig, output)


def _plot_qfpi_gf_semantic_split(output: Path) -> None:
    payload = _read_science_payload()["semantic_and_vectors"]
    assert isinstance(payload, dict)
    rows = [row for row in payload["semantic_split"] if isinstance(row, dict)]
    labels = [f"{row['symbol']}\n{row['label']}" for row in rows]
    values = np.asarray([float(row["display_value"]) for row in rows], dtype=float)
    owners = [str(row["owner"]) for row in rows]
    colors = [COLORS["htt"] if owner == "HTT" else COLORS["mio"] for owner in owners]
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.bar(np.arange(len(rows)), values, color=colors)
    ax.set_xticks(np.arange(len(rows)), labels)
    ax.set_ylabel("normalized display value")
    ax.set_title("Semantic split: x, Q, and current proxy lanes", loc="left", fontweight="bold")
    _style_axes(ax)
    ax.grid(axis="y", color="#cbd5e1", linewidth=0.7)
    ax.grid(axis="x", visible=False)
    for idx, row in enumerate(rows):
        ax.text(
            idx,
            values[idx] + 0.025,
            str(row["owner"]),
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=COLORS["common"],
        )
    ax.text(
        0.01,
        0.96,
        "proxy lanes are not canonical Pi/F/G_F diagnostics",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color=COLORS["common"],
    )
    _save_figure(fig, output)


def _plot_mio_depth_residual_vectors(output: Path) -> None:
    payload = _read_science_payload()["semantic_and_vectors"]
    assert isinstance(payload, dict)
    vectors = [row for row in payload["diagnostic_vectors"] if isinstance(row, dict)]
    depth_p95 = payload["depth_p95"]
    assert isinstance(depth_p95, dict)
    local_depth = depth_p95["local_null"]
    survey_depth = depth_p95["survey_systematic"]
    assert isinstance(local_depth, dict)
    assert isinstance(survey_depth, dict)

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.2), gridspec_kw={"width_ratios": [1.2, 1]})
    labels = [str(row["name"]).replace(" ", "\n") for row in vectors]
    magnitudes = [float(row["magnitude"]) for row in vectors]
    missing_counts = [
        len(row["missing_prerequisites"]) if isinstance(row["missing_prerequisites"], list) else 0
        for row in vectors
    ]
    y = np.arange(len(vectors))
    axes[0].barh(y, magnitudes, color="#7c2d12")
    axes[0].scatter(
        [min(1.0, 0.12 + 0.12 * count) for count in missing_counts],
        y,
        s=[42 + 24 * count for count in missing_counts],
        color=[COLORS["ok"] if count == 0 else COLORS["block"] for count in missing_counts],
        zorder=4,
        label="missing prerequisites",
    )
    axes[0].set_yticks(y, labels)
    axes[0].set_xlim(0, 1.05)
    axes[0].set_xlabel("diagnostic vector magnitude")
    axes[0].set_title("MIO/HTT readiness vectors", loc="left", fontweight="bold")
    axes[0].invert_yaxis()
    _style_axes(axes[0])

    depth_labels = list(local_depth)
    local_values = [float(local_depth[label]) for label in depth_labels]
    survey_values = [float(survey_depth[label]) for label in depth_labels]
    x = np.arange(len(depth_labels))
    width = 0.36
    axes[1].bar(x - width / 2, local_values, width=width, color=COLORS["htt"], label="local null")
    axes[1].bar(x + width / 2, survey_values, width=width, color=COLORS["warn"], label="survey null")
    axes[1].set_xticks(x, [label.replace("_", "\n") for label in depth_labels])
    axes[1].set_ylabel("G_F p95")
    axes[1].set_title("Depth response envelope", loc="left", fontweight="bold")
    axes[1].legend(frameon=True, fontsize=8)
    _style_axes(axes[1])
    axes[1].grid(axis="y", color="#cbd5e1", linewidth=0.7)
    axes[1].grid(axis="x", visible=False)
    fig.text(
        0.99,
        0.01,
        "diagnostic readiness and null envelopes only; no MIO posterior or HTT evidence",
        ha="right",
        fontsize=8.5,
        color=COLORS["common"],
    )
    _save_figure(fig, output)


def _plot_public_claim_freeze(output: Path) -> None:
    text = _read_text("docs/generated/publication_claim_freeze.md")
    rows = _table_after_heading(text, "Frozen Public Claims")
    status_counts: dict[str, int] = {}
    owner_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["Status"]] = status_counts.get(row["Status"], 0) + 1
        owner_counts[row["Owner"]] = owner_counts.get(row["Owner"], 0) + 1
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.6), gridspec_kw={"width_ratios": [1.1, 1]})
    status_label_keys = list(status_counts)
    status_labels = [
        label.replace("_with_", "\nwith ").replace("_for_", "\nfor ").replace("_", " ")
        for label in status_label_keys
    ]
    status_values = [status_counts[label] for label in status_label_keys]
    axes[0].barh(status_labels, status_values, color=[COLORS["ok"] if "allowed" in s else COLORS["block"] for s in status_labels])
    axes[0].set_title("Publication claim freeze status", loc="left", fontweight="bold")
    axes[0].set_xlabel("claims")
    _style_axes(axes[0])
    owner_labels = list(owner_counts)
    owner_values = [owner_counts[label] for label in owner_labels]
    axes[1].bar(owner_labels, owner_values, color=["#334155", "#0f766e", "#7c2d12", "#b45309", "#6d28d9"][: len(owner_labels)])
    axes[1].set_title("Claim owners", loc="left", fontweight="bold")
    axes[1].set_ylabel("claims")
    _style_axes(axes[1])
    axes[1].tick_params(axis="x", rotation=20)
    _save_figure(fig, output)


def _figure_specs() -> tuple[FigureSpec, ...]:
    return (
        FigureSpec(
            artifact_id="common.current_figures.dag_progress",
            file_name="fig_current_dag_progress.png",
            title="Current DAG status snapshot",
            flow_slot="Framework and repository status",
            source_paths=("docs/generated/status_snapshot.json",),
            caption=(
                "Current DAG/status snapshot by repository owner. The panel is "
                "bookkeeping evidence only: completion and smoke status do not "
                "promote any result to production validation."
            ),
            label="fig:current-dag-progress",
            snippet="current_figures_framework.tex",
            builder=_plot_dag_progress,
            null_mock_status="not_statistical_status_snapshot",
        ),
        FigureSpec(
            artifact_id="common.current_figures.scalar_morphology_boundary",
            file_name="fig_current_scalar_morphology_boundary.png",
            title="Scalar diagnostics vs morphology/MES boundary",
            flow_slot="Framework claim boundary",
            source_paths=("docs/generated/result_pack_A.md",),
            caption=(
                "Current scalar-to-morphology comparison matrix. The allowed "
                "state is diagnostic side-by-side reporting with separate "
                "provenance; scalar diagnostics and low-ell summaries do not "
                "identify geometry or provide Bianchi family-ID."
            ),
            label="fig:current-scalar-morphology-boundary",
            snippet="current_figures_framework.tex",
            builder=_plot_scalar_morphology_boundary,
            null_mock_status="summarized_from_dependency_surfaces",
        ),
        FigureSpec(
            artifact_id="common.current_figures.transfer_provenance",
            file_name="fig_current_transfer_provenance.png",
            title="Transfer provenance inventory",
            flow_slot="Observational pipeline",
            source_paths=("docs/generated/transfer_sensitivity_report.md",),
            caption=(
                "Current transfer-provenance inventory. External and empirical "
                "proxy paths remain transfer-conditional; future native rows are "
                "schema-only and non-consumable until validation gates exist."
            ),
            label="fig:current-transfer-provenance",
            snippet="current_figures_pipeline.tex",
            builder=_plot_transfer_provenance,
            transfer_source="external_transfer_inventory",
        ),
        FigureSpec(
            artifact_id="common.current_figures.transfer_sensitivity_tornado",
            file_name="fig_current_transfer_sensitivity_tornado.png",
            title="Transfer and denominator sensitivity",
            flow_slot="Observational pipeline",
            source_paths=(
                "docs/generated/current_science_plot_payload.json",
                "docs/generated/transfer_sensitivity_report.md",
                "htt/mio/formalism/budget_spec.py",
            ),
            caption=(
                "Current transfer/denominator-sensitivity tornado for the "
                "diagnostic Q score. The plotted values are generated from "
                "MIO BudgetSpec denominator policies and a deterministic "
                "current-code stress payload; external-transfer rows remain "
                "transfer-conditional and are not native low-ell solver output."
            ),
            label="fig:current-transfer-sensitivity-tornado",
            snippet="current_figures_pipeline.tex",
            builder=_plot_transfer_sensitivity_tornado,
            transfer_source="mixed_none_and_external_transfer_conditioned",
            null_mock_status="not_statistical_denominator_sensitivity",
            artifact_mode="paper_appendix_conditioned",
            allowed_use="paper_appendix",
            figure_kind="conditioned_physics_diagnostic_plot",
            caption_policy=(
                "must_state_transfer_conditional",
                "must_state_no_native_low_ell_solver_output",
                "must_not_use_for_family_identification_or_family_selection",
                "must_state_denominator_sensitivity_only",
            ),
            promotion_blockers=(
                "native_solver_validation_absent",
                "native_morphology_atlas_absent",
                "observed_transfer_sensitivity_payload_absent",
            ),
            caveats=(
                "Generated from current repo-local code and deterministic diagnostic payload.",
                "Conditioned physics diagnostic; not an observed-data production result.",
                "External-transfer rows are not native low-ell solver output.",
                "No Bianchi family-ID or geometry-detection claim is made.",
            ),
        ),
        FigureSpec(
            artifact_id="common.current_figures.local_global_gates",
            file_name="fig_current_local_global_gates.png",
            title="Local/global discrimination gates",
            flow_slot="Results and robustness",
            source_paths=("docs/generated/result_pack_B.md",),
            caption=(
                "Current local/global discrimination gate scenarios. Candidate "
                "wording is conditional on rank and null-FPR prerequisites; "
                "blocked rows carry no claim."
            ),
            label="fig:current-local-global-gates",
            snippet="current_figures_results.tex",
            builder=_plot_local_global_gates,
            null_mock_status="summarized_from_local_and_survey_systematic_fpr_gates",
        ),
        FigureSpec(
            artifact_id="common.current_figures.local_global_rank_fpr",
            file_name="fig_current_local_global_rank_fpr.png",
            title="Local/global rank and null-FPR diagnostics",
            flow_slot="Results and robustness",
            source_paths=(
                "docs/generated/current_science_plot_payload.json",
                "htt/htt/htt/departure/response_overlap.py",
                "htt/htt/htt/nulls/local_boost_depth_null.py",
                "htt/htt/htt/nulls/selection_response_depth.py",
            ),
            caption=(
                "Current-code local/global rank and null-FPR diagnostic. The "
                "left panel is the nuisance-projected response-overlap SVD; "
                "the right panel shows local-only and survey/systematic null "
                "false-positive rates from generated diagnostic mock banks. "
                "This is a gate stress plot, not HTT evidence or a posterior."
            ),
            label="fig:current-local-global-rank-fpr",
            snippet="current_figures_results.tex",
            builder=_plot_local_global_rank_fpr,
            null_mock_status="current_code_diagnostic_local_and_survey_fpr_reports",
            artifact_mode="paper_appendix_conditioned",
            allowed_use="paper_appendix",
            figure_kind="conditioned_physics_diagnostic_plot",
            caption_policy=(
                "must_state_gate_stress_payload",
                "must_state_no_posterior_or_evidence",
                "must_state_no_family_identification",
                "must_state_no_native_low_ell_solver_output",
            ),
            promotion_blockers=(
                "observed_rank_payload_absent",
                "matched_observed_null_mock_stack_absent",
                "native_solver_validation_absent",
                "native_morphology_atlas_absent",
            ),
            caveats=(
                "Generated from current repo-local HTT rank and null-FPR code.",
                "Deterministic gate stress payload; not an observed-data production result.",
                "No HTT posterior, evidence, or family-ID claim is made.",
            ),
        ),
        FigureSpec(
            artifact_id="common.current_figures.mio_certificate_status",
            file_name="fig_current_mio_certificate_status.png",
            title="MIO diagnostic certificate readiness",
            flow_slot="Results and robustness",
            source_paths=("docs/generated/result_pack_C.md",),
            caption=(
                "Current MIO certificate/status rows. The rows remain "
                "diagnostic reports, not HTT inference quantities, model "
                "rankings, or HTT evidence."
            ),
            label="fig:current-mio-certificate-status",
            snippet="current_figures_results.tex",
            builder=_plot_mio_certificate_status,
            null_mock_status="summarized_from_mio_certificate_status_metadata",
        ),
        FigureSpec(
            artifact_id="common.current_figures.qfpi_gf_semantic_split",
            file_name="fig_current_qfpi_gf_semantic_split.png",
            title="x/Q/proxy semantic split",
            flow_slot="Results and robustness",
            source_paths=(
                "docs/generated/current_science_plot_payload.json",
                "docs/generated/result_pack_A.md",
                "htt/src/common/departure_contracts.py",
                "htt/mio/formalism/budget_spec.py",
                "htt/mio/formalism/component_breakdown.py",
                "htt/mio/formalism/departure_bundle.py",
                "htt/mio/formalism/exceedance.py",
                "htt/mio/formalism/filling_fraction.py",
                "htt/mio/formalism/normalized_score.py",
            ),
            caption=(
                "Current $x$, $Q$, and noncanonical proxy-lane semantic split. The bars are normalized "
                "display values from the deterministic current-code diagnostic "
                "payload; displayed $x_C$ is a signed comparator projection "
                "with sector profile, cancellation index, and unsigned $M$ "
                "companion metadata, so near-zero $x_C$ or $F$ would be "
                "cancellation-compatible rather than an isotropy statement. "
                "Displayed $Q$ carries explicit comparator labels and an "
                "across-comparator specification-curve sensitivity; the "
                "$\\Pi$ policy summary records measure kind, threshold policy, "
                "and look-elsewhere trial metadata for the source $Q$ samples. "
                "The bars show ownership and semantic separation, not a single "
                "interchangeable statistic, not formal $\\Pi$, $F$, or $G_F$ "
                "diagnostics, and not a family-ID signal."
            ),
            label="fig:current-qfpi-gf-semantic-split",
            snippet="current_figures_results.tex",
            builder=_plot_qfpi_gf_semantic_split,
            transfer_source="mixed_none_and_external_transfer_conditioned",
            null_mock_status="current_code_diagnostic_null_banks_generated",
            artifact_mode="paper_appendix_conditioned",
            allowed_use="paper_appendix",
            figure_kind="conditioned_physics_diagnostic_plot",
            caption_policy=(
                "must_state_distinct_semantics",
                "must_state_diagnostic_only",
                "must_state_no_family_identification",
                "must_state_no_native_low_ell_solver_output",
                "must_show_sector_profile_for_x_or_f",
                "must_state_x_f_near_zero_not_isotropy",
                "must_state_f_requires_magnitude_companion",
                "must_show_q_comparator_multiverse",
                "must_state_pi_policy_metadata_when_pi_is_shown",
            ),
            promotion_blockers=(
                "native_solver_validation_absent",
                "native_morphology_atlas_absent",
                "observed_departure_bundle_payload_absent",
            ),
            caveats=(
                "Generated from current repo-local code and deterministic diagnostic payload.",
                "Normalized display only; proxy bars are not canonical Pi, F, or G_F diagnostics.",
                "x_C/F display metadata must include sector profile, cancellation index, and M companion.",
                "Q display metadata must include comparator labels and specification-curve spread.",
                "Pi policy metadata blocks calibrated-tail interpretation unless future matched-null gates exist.",
                "No Bianchi family-ID or geometry-detection claim is made.",
            ),
        ),
        FigureSpec(
            artifact_id="common.current_figures.mio_depth_residual_vectors",
            file_name="fig_current_mio_depth_residual_vectors.png",
            title="MIO/HTT diagnostic vectors and depth response",
            flow_slot="Results and robustness",
            source_paths=(
                "docs/generated/current_science_plot_payload.json",
                "docs/generated/gf_matched_null_forecast_report.json",
                "docs/generated/result_pack_C.md",
                "htt/htt/htt/nulls/local_boost_depth_null.py",
                "htt/htt/htt/nulls/selection_response_depth.py",
                "htt/mio/formalism/isotropy_gap.py",
            ),
            caption=(
                "Current MIO/HTT diagnostic vector and depth-response summary. "
                "The left panel shows normalized readiness/vector magnitudes "
                "and missing prerequisites; the right panel shows $G_F$ depth "
                "response envelopes from current-code local and survey null "
                "banks, while the payload exposes the canonical MIO $G_F$ "
                "floor-applied-by-bin and denominator-evolution split contract. "
                "The matched-null path is forecast-only and blocked from "
                "observed-data local/global wording. MIO rows remain diagnostic "
                "certificates, not model rankings or HTT evidence."
            ),
            label="fig:current-mio-depth-residual-vectors",
            snippet="current_figures_results.tex",
            builder=_plot_mio_depth_residual_vectors,
            null_mock_status="current_code_diagnostic_local_and_survey_null_banks",
            artifact_mode="paper_appendix_conditioned",
            allowed_use="paper_appendix",
            figure_kind="conditioned_physics_diagnostic_plot",
            caption_policy=(
                "must_state_diagnostic_certificate_only",
                "must_state_no_model_ranking",
                "must_state_no_htt_evidence",
                "must_state_no_native_low_ell_solver_output",
                "must_not_use_for_family_identification_or_family_selection",
                "matched_null_forecast_report_required",
                "must_expose_gf_floor_and_denominator_split",
            ),
            promotion_blockers=(
                "matched_observed_depth_residual_absent",
                "native_morphology_atlas_absent",
                "external_null_validation_absent",
            ),
            caveats=(
                "Generated from current repo-local null-bank and diagnostic-vector payloads.",
                "Diagnostic readiness plot; not a production certificate.",
                "No MIO posterior, model ranking, or HTT evidence is made.",
            ),
        ),
        FigureSpec(
            artifact_id="common.current_figures.public_claim_freeze",
            file_name="fig_current_public_claim_freeze.png",
            title="Publication claim freeze map",
            flow_slot="Governance and submission boundary",
            source_paths=("docs/generated/publication_claim_freeze.md",),
            caption=(
                "Current publication claim-freeze map. The freeze permits only "
                "caveated framework, provenance, diagnostic, and audit-package "
                "claims and blocks native-solver, geometry-detection, or "
                "family-ID wording."
            ),
            label="fig:current-public-claim-freeze",
            snippet="current_figures_governance.tex",
            builder=_plot_public_claim_freeze,
        ),
    )


def _manifest_for_spec(spec: FigureSpec, figure_path: Path, command: str) -> dict[str, Any]:
    rel_path = _repo_relative(figure_path)
    git_commit, worktree = _git_state()
    manifest = {
        "artifact_id": spec.artifact_id,
        "artifact_path": rel_path,
        "owner": spec.owner,
        "implementation_scope": spec.implementation_scope,
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": spec.artifact_mode,
        "allowed_use": spec.allowed_use,
        "caption_policy": list(spec.caption_policy),
        "promotion_blockers": list(spec.promotion_blockers),
        "created_by": "scripts/make_current_manuscript_figures.py",
        "git_commit": git_commit,
        "config_hash": _config_hash(
            {
                "artifact_id": spec.artifact_id,
                "file_name": spec.file_name,
                "source_paths": spec.source_paths,
                "caption": spec.caption,
                "artifact_mode": spec.artifact_mode,
                "allowed_use": spec.allowed_use,
                "version": "current-manuscript-figures-v2",
            }
        ),
        "input_hashes": _input_hashes(spec.source_paths),
        "code_version": worktree,
        "schema_version": "common.current_manuscript_figure.v1",
        "caveats": list(spec.caveats),
        "required_gates": [
            "current_generated_input_only",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "passed_gates": [
            "current_generated_input_only",
            "manifest_metadata_present",
        ],
        "failed_gates": [],
        "statistics_definitions": {
            "flow_slot": spec.flow_slot,
            "source_artifacts": list(spec.source_paths),
            "figure_kind": spec.figure_kind,
        },
        "transfer_source": spec.transfer_source,
        "sky_support_status": "not_directional",
        "null_mock_status": spec.null_mock_status,
        "generating_command": command,
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


def _write_sidecar(spec: FigureSpec, figure_path: Path, command: str) -> None:
    manifest = _manifest_for_spec(spec, figure_path, command)
    sidecar = figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json")
    sidecar.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _latex_figure(spec: FigureSpec) -> str:
    graphic_path = "current/" + Path(spec.file_name).with_suffix("").name
    return "\n".join(
        [
            "\\begin{figure}[htbp]",
            "\\centering",
            f"\\includegraphics[width=0.92\\textwidth]{{{graphic_path}}}",
            f"\\caption{{{spec.caption}}}",
            f"\\label{{{spec.label}}}",
            "\\end{figure}",
            "",
        ]
    )


def _write_snippets(specs: tuple[FigureSpec, ...]) -> None:
    SNIPPET_DIR.mkdir(parents=True, exist_ok=True)
    by_snippet: dict[str, list[FigureSpec]] = {}
    for spec in specs:
        by_snippet.setdefault(spec.snippet, []).append(spec)
    for snippet, snippet_specs in by_snippet.items():
        body = [
            "% Generated by scripts/make_current_manuscript_figures.py.",
            "% Do not edit figure paths by hand; regenerate instead.",
            "",
        ]
        for spec in snippet_specs:
            body.append(_latex_figure(spec))
        (SNIPPET_DIR / snippet).write_text("\n".join(body), encoding="utf-8")


def _write_plot_list(specs: tuple[FigureSpec, ...], command: str) -> None:
    curation: dict[str, Any] = {}
    if CURATION_REPORT.exists():
        curation = json.loads(CURATION_REPORT.read_text(encoding="utf-8"))
    input_paths = [
        "scripts/make_current_manuscript_figures.py",
        "docs/generated/current_manuscript_figure_curation.json",
        *sorted({path for spec in specs for path in spec.source_paths}),
    ]
    rows = [
        "| Flow slot | Figure | Source artifacts | Claim tier | Artifact mode | Allowed use | Caveat |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for spec in specs:
        figure = f"figures/current/{spec.file_name}"
        sources = "<br>".join(f"`{path}`" for path in spec.source_paths)
        caveat = spec.caveats[1]
        rows.append(
            f"| {spec.flow_slot} | `{figure}` | {sources} | diagnostic_only | `{spec.artifact_mode}` | `{spec.allowed_use}` | {caveat} |"
        )
    removed = curation.get("total_removed_includes", 0)
    git_commit, worktree = _git_state()
    metadata = [
        "# Current Manuscript Plot List",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: mixed_none_and_external_transfer_conditioned",
        "sky_support_status: mixed_not_directional_and_diagnostic_sky_support",
        "null_mock_status: mixed_not_statistical_and_current_code_diagnostic_null_banks",
        "config_hash: `" + _config_hash({"specs": [spec.artifact_id for spec in specs], "removed": removed}) + "`",
        "input_hashes:",
        *[f"- `{path}:sha256:{_sha256(REPO_ROOT / path)}`" for path in input_paths if (REPO_ROOT / path).exists()],
        "caveats:",
        "- Excluded legacy figure references are removed from manuscript use, not deleted from disk.",
        "- Current figures include governance summaries and conditioned current-code physics diagnostics.",
        "- No figure claims native low-ell output, geometry-detection status, or Bianchi family-ID.",
        f"generating_command: `{command}`",
        f"git_commit_or_worktree_state: `{worktree}`",
        "artifact_path: docs/generated/current_manuscript_plot_list.md",
        "",
        "## Excluded Legacy Plot References",
        "",
        f"- Excluded includegraphics references: `{removed}`",
        "- Exclusion rule: no current manifest-ready sidecar, missing source, or non-current legacy/ver2 figure provenance.",
        "- Physical legacy files are retained for audit/recovery; they are not manuscript figures after curation.",
        "",
        "## Current Plot Sequence",
        "",
        f"- Current manifest-backed plot count: `{len(specs)}`",
        "- Conditioned physics diagnostics are appendix-eligible only until observed-data/native-solver promotion gates exist.",
        "",
        *rows,
        "",
        "## Claim Boundary",
        "",
        "- These plots support only claim-tiered observational/statistical framework reporting.",
        "- Transfer-dependent surfaces remain transfer-conditional.",
        "- MIO certificate/status plots are diagnostic-only and do not rank models.",
        "- Scalar diagnostics and low-ell summaries do not provide Bianchi family-ID.",
    ]
    PLOT_LIST.parent.mkdir(parents=True, exist_ok=True)
    PLOT_LIST.write_text("\n".join(metadata) + "\n", encoding="utf-8")


def _command(argv: list[str] | None) -> str:
    args = sys.argv[1:] if argv is None else argv
    return shlex.join(["python", "scripts/make_current_manuscript_figures.py", *args])


def _generation_args(argv: list[str] | None) -> list[str]:
    args = list(sys.argv[1:] if argv is None else argv)
    return [arg for arg in args if arg != "--check"]


def _sidecar_path(figure_path: Path) -> Path:
    return figure_path.with_suffix("").with_name(
        figure_path.stem + ".manifest.json"
    )


def _generated_paths(
    specs: tuple[FigureSpec, ...],
    *,
    skip_snippets: bool,
    skip_plot_list: bool,
) -> tuple[Path, ...]:
    paths: list[Path] = [SCIENCE_PAYLOAD, GF_FORECAST_REPORT_JSON, GF_FORECAST_REPORT_MD]
    for spec in specs:
        figure_path = FIGURE_DIR / spec.file_name
        paths.extend((figure_path, _sidecar_path(figure_path)))
    if not skip_snippets:
        paths.extend(
            SNIPPET_DIR / snippet
            for snippet in sorted({spec.snippet for spec in specs})
        )
    if not skip_plot_list:
        paths.append(PLOT_LIST)
    return tuple(dict.fromkeys(paths))


def _snapshot(paths: tuple[Path, ...]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.exists() else None for path in paths}


def _restore(snapshot: dict[Path, bytes | None]) -> None:
    for path, content in snapshot.items():
        if content is None:
            if path.exists():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _stored_git_state_for_check() -> tuple[str | None, str] | None:
    if not SCIENCE_PAYLOAD.exists():
        return None
    try:
        payload = json.loads(SCIENCE_PAYLOAD.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    commit = payload.get("git_commit")
    worktree = payload.get("git_commit_or_worktree_state")
    if not isinstance(worktree, str) or not worktree.strip():
        return None
    return (commit if isinstance(commit, str) and commit.strip() else None, worktree)


def _write_outputs(
    *,
    command: str,
    specs: tuple[FigureSpec, ...],
    skip_snippets: bool,
    skip_plot_list: bool,
    quiet: bool,
) -> None:
    _write_current_science_payload(command)
    if not quiet:
        print(f"wrote {_repo_relative(SCIENCE_PAYLOAD)}")
    for spec in specs:
        output = FIGURE_DIR / spec.file_name
        spec.builder(output)
        _write_sidecar(spec, output, command)
        if not quiet:
            print(f"wrote {_repo_relative(output)}")
    if not skip_snippets:
        _write_snippets(specs)
        if not quiet:
            print(f"wrote {_repo_relative(SNIPPET_DIR)} current figure snippets")
    if not skip_plot_list:
        _write_plot_list(specs, command)
        if not quiet:
            print(f"wrote {_repo_relative(PLOT_LIST)}")


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate current manifest-backed manuscript figures."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--skip-snippets", action="store_true")
    parser.add_argument("--skip-plot-list", action="store_true")
    args = parser.parse_args(argv)

    command = _command(_generation_args(argv))
    specs = _figure_specs()
    if args.check:
        paths = _generated_paths(
            specs,
            skip_snippets=args.skip_snippets,
            skip_plot_list=args.skip_plot_list,
        )
        before = _snapshot(paths)
        global _GIT_STATE_OVERRIDE
        _GIT_STATE_OVERRIDE = _stored_git_state_for_check()
        try:
            _write_outputs(
                command=command,
                specs=specs,
                skip_snippets=args.skip_snippets,
                skip_plot_list=args.skip_plot_list,
                quiet=True,
            )
        finally:
            _GIT_STATE_OVERRIDE = None
        after = _snapshot(paths)
        changed = [path for path in paths if before.get(path) != after.get(path)]
        if changed:
            _restore(before)
            print("stale current manuscript figure artifacts:", file=sys.stderr)
            for path in changed:
                print(f"- {_repo_relative(path)}", file=sys.stderr)
            return 1
        print("current manuscript figure artifacts are current")
        return 0

    _write_outputs(
        command=command,
        specs=specs,
        skip_snippets=args.skip_snippets,
        skip_plot_list=args.skip_plot_list,
        quiet=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
