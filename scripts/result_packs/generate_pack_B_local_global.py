#!/usr/bin/env python3
"""Generate Result Pack B: local/global discrimination gate summary."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


SCHEMA_VERSION = "common.result_pack_B_local_global.v1"
DEFAULT_OUTPUT = Path("docs/generated/result_pack_B.md")
ARTIFACT_ID = "result_pack_B_local_global"
ARTIFACT_PATH = "docs/generated/result_pack_B.md"
CREATED_BY = "scripts/result_packs/generate_pack_B_local_global.py"
DEPENDENCIES = ("PR-066", "PR-100", "PR-101")
INPUT_FILES = (
    "scripts/result_packs/generate_pack_B_local_global.py",
    "docs/ver2_upgrade/generated/result_pack_B_local_global.json",
    "docs/PR_DELTAS/pr-060.md",
    "docs/PR_DELTAS/pr-061.md",
    "docs/PR_DELTAS/pr-062.md",
    "docs/PR_DELTAS/pr-063.md",
    "docs/PR_DELTAS/pr-064.md",
    "docs/PR_DELTAS/pr-065.md",
    "docs/PR_DELTAS/pr-066.md",
    "docs/PR_DELTAS/pr-100.md",
    "docs/PR_DELTAS/pr-101.md",
    "docs/generated/gf_matched_null_forecast_report.json",
    "htt/htt/htt/departure/response_overlap.py",
    "htt/htt/htt/infer/null_competition.py",
    "htt/htt/htt/nulls/local_boost_depth_null.py",
    "htt/htt/htt/nulls/selection_response_depth.py",
    "htt/htt/htt/departure/local_global_mixture.py",
    "htt/htt/htt/departure/posterior_pushforward.py",
    "htt/mio/coherence/directional.py",
    "htt/mio/coherence/redshift_binned.py",
    "docs/generated/status_snapshot.json",
)
DEFAULT_CAVEATS = (
    "common_diagnostic_only_report_over_existing_dependency_surfaces",
    "rank_or_overlap_blockers_are_no_claim_states",
    "local_and_survey_systematic_fpr_are_prerequisites_not_evidence",
    "mio_directional_and_depth_surfaces_are_diagnostic_cross_checks_only",
    "posterior_pushforward_rows_remain_htt_owned_and_transfer_conditional",
    "legacy_ver2_pack_b_is_prior_context_only_not_promoted",
    "native_morphology_atlas_support_remains_absent",
    "no_htt_evidence_mio_certificate_or_native_solver_output_is_merged",
)


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _git_state(repo_root: Path) -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = subprocess.run(
            ["git", "diff", "--quiet"],
            cwd=repo_root,
            check=False,
        ).returncode != 0
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return f"{commit}+dirty" if dirty else commit


def _load_status_rows(repo_root: Path) -> dict[str, dict[str, Any]]:
    status_path = repo_root / "docs/generated/status_snapshot.json"
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    return {
        str(row.get("artifact_id", "")).replace("codex_dag.", ""): row
        for row in rows
        if isinstance(row, dict)
    }


def _input_hashes(repo_root: Path) -> list[str]:
    hashes: list[str] = []
    for relative in INPUT_FILES:
        path = repo_root / relative
        hashes.append(f"{relative}:{_sha256_file(path)}")
    return hashes


def _load_legacy_ver2_pack(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "docs/ver2_upgrade/generated/result_pack_B_local_global.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    return {
        "source_path": str(path.relative_to(repo_root)),
        "source_title": source.get("title", "unknown"),
        "source_topic": source.get("topic", "unknown"),
        "source_claim_tier": source.get("claim_tier", "unknown"),
        "source_production_status": source.get("production_status", "unknown"),
        "pr111_use": "legacy_context_only_not_promoted",
        "artifacts": [
            {
                "artifact_id": item.get("artifact_id", "unknown"),
                "owner": item.get("owner", "unknown"),
                "source_claim_tier": item.get("claim_tier", "unknown"),
                "source_production_status": item.get(
                    "production_status",
                    "unknown",
                ),
                "pr111_status": "prior_context_only",
            }
            for item in source.get("artifacts", [])
            if isinstance(item, dict)
        ],
        "source_caveats": list(source.get("caveats", [])),
    }


def _dependency_status(
    status_rows: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        pr_id: {
            "implemented": bool(status_rows.get(pr_id, {}).get("implemented")),
            "smoke_tested": bool(status_rows.get(pr_id, {}).get("smoke_tested")),
            "claim_tier": status_rows.get(pr_id, {}).get("claim_tier", "unknown"),
            "production_validated": bool(
                status_rows.get(pr_id, {}).get("production_validated")
            ),
        }
        for pr_id in DEPENDENCIES
    }


def _gate_summary() -> list[dict[str, Any]]:
    return [
        {
            "category": "rank_audit",
            "owner": "HTT",
            "source_pr": "PR-060",
            "surface": "htt.departure.response_overlap.ResponseOverlapAudit",
            "required_status": "full_rank_identifiable",
            "reported_quantities": [
                "rho_LB_GT",
                "projected_rank",
                "rank_status",
                "condition_number",
                "no_claim_reasons",
            ],
            "blocked_policy": "rank_or_overlap_blocker_yields_no_claim",
            "claim_role": "pre_inference_gate",
        },
        {
            "category": "local_null_fpr",
            "owner": "HTT",
            "source_pr": "PR-061",
            "surface": "htt.nulls.local_boost_depth_null.LocalBoostNullFprReport",
            "required_status": "local_boost_null_fpr_available_and_below_threshold",
            "reported_quantities": [
                "false_positive_rate_raw",
                "false_positive_rate_interval",
                "look_elsewhere_adjusted_fpr",
                "blocked_reasons",
            ],
            "blocked_policy": "missing_or_high_fpr_yields_no_claim",
            "claim_role": "prerequisite_not_evidence",
        },
        {
            "category": "survey_systematic_null_fpr",
            "owner": "HTT",
            "source_pr": "PR-062",
            "surface": (
                "htt.nulls.selection_response_depth."
                "SurveySystematicNullFprReport"
            ),
            "required_status": (
                "selection_and_survey_systematic_fpr_available_and_below_threshold"
            ),
            "reported_quantities": [
                "selection_metadata_hash",
                "survey_axis_hash",
                "false_positive_rate_adjusted",
                "blocked_reasons",
            ],
            "blocked_policy": "missing_or_high_fpr_yields_no_claim",
            "claim_role": "prerequisite_not_evidence",
        },
        {
            "category": "local_global_mixture",
            "owner": "HTT",
            "source_pr": "PR-063",
            "surface": "htt.departure.local_global_mixture.LocalGlobalMixtureReport",
            "required_status": "separate_local_global_systematic_noise_blocks",
            "reported_quantities": [
                "full_design_rank_gate",
                "response_consistency_gate",
                "generated_diagnostic_fit_scores",
            ],
            "blocked_policy": "rank_or_response_mismatch_yields_no_claim",
            "claim_role": "conditional_pre_solver_ceiling",
        },
        {
            "category": "posterior_pushforward",
            "owner": "HTT",
            "source_pr": "PR-066",
            "surface": "htt.departure.posterior_pushforward.PosteriorPushforwardReport",
            "required_status": "htt_owned_transfer_conditional_prerequisites",
            "reported_quantities": [
                "local_global_status",
                "prior_ppc_loocv_status",
                "Q_F_Pi_G_F_summaries",
                "transfer_provenance",
            ],
            "blocked_policy": "failed_adequacy_or_mio_input_yields_blocked",
            "claim_role": "htt_pushforward_context_not_mio_input",
        },
        {
            "category": "directional_coherence",
            "owner": "MIO",
            "source_pr": "PR-100",
            "surface": "mio.coherence.directional.to_mio_certificate",
            "required_status": "covariance_null_sky_status_recorded",
            "reported_quantities": [
                "direction_convention",
                "weighting_convention",
                "covariance_status",
                "null_mock_status",
                "sky_support_status",
            ],
            "blocked_policy": "incomplete_covariance_or_null_remains_diagnostic",
            "claim_role": "diagnostic_cross_check_not_htt_evidence",
        },
        {
            "category": "depth_gap",
            "owner": "MIO",
            "source_pr": "PR-101",
            "surface": "mio.coherence.redshift_binned.RedshiftDepthBinMetadata",
            "required_status": "redshift_bin_metadata_and_g_f_bridge_refs_recorded",
            "reported_quantities": [
                "G_F_bridge_ref",
                "G_F_floor_report_ref",
                "denominator_evolution_split_ref",
                "matched_null_forecast_status",
                "depth_bin_covariance_status",
                "depth_bin_null_mock_status",
                "sky_mask_support_status",
            ],
            "blocked_policy": "missing_bridge_or_matched_null_remains_descriptive",
            "claim_role": "diagnostic_depth_bridge_not_htt_evidence",
            "G_F_floor_report_ref": (
                "docs/generated/current_science_plot_payload.json"
                "#/semantic_and_vectors/g_f_display_contract"
            ),
            "denominator_evolution_split_ref": (
                "docs/generated/current_science_plot_payload.json"
                "#/semantic_and_vectors/g_f_display_contract/denominator_evolution_split"
            ),
            "matched_null_forecast_report_ref": (
                "docs/generated/gf_matched_null_forecast_report.json"
            ),
            "matched_null_forecast_status": "forecast_matched_null_blocked",
            "local_global_separation_status": (
                "blocked_existing_null_bank_insufficient"
            ),
        },
    ]


def _rank_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "all_prerequisites_pass",
            "rank_status": "full_rank",
            "null_fpr_status": "local_and_survey_systematic_fpr_recorded",
            "depth_coherence_status": "metadata_recorded",
            "claim_tier": "conditional",
            "production_status": "diagnostic_only_conditional_ceiling",
            "local_global_candidate_status": "local_global_discrimination_candidate",
            "allowed_report_phrase": (
                "conditional local/global discrimination candidate"
            ),
            "blocked_reasons": [],
            "required_before_use": [
                "rank_full",
                "local_null_fpr_below_threshold",
                "survey_systematic_fpr_below_threshold",
                "covariance_mask_sky_support_recorded",
                "depth_and_directional_metadata_recorded",
                "prior_ppc_loocv_status_recorded",
            ],
        },
        {
            "scenario_id": "rank_deficient_projected_response",
            "rank_status": "rank_deficient",
            "null_fpr_status": "not_evaluated_after_rank_block",
            "depth_coherence_status": "not_promoted",
            "claim_tier": "blocked",
            "production_status": "blocked_rank_deficient",
            "local_global_candidate_status": "blocked_no_claim",
            "allowed_report_phrase": "no-claim rank or overlap blocker",
            "blocked_reasons": ["rank_deficient", "projected_rank_less_than_two"],
            "required_before_use": ["rerun_rank_audit_with_identifiable_responses"],
        },
        {
            "scenario_id": "overlap_degenerate_response",
            "rank_status": "full_rank_overlap_degenerate",
            "null_fpr_status": "not_promoted",
            "depth_coherence_status": "not_promoted",
            "claim_tier": "blocked",
            "production_status": "blocked_response_overlap_degenerate",
            "local_global_candidate_status": "blocked_no_claim",
            "allowed_report_phrase": "no-claim rank or overlap blocker",
            "blocked_reasons": ["response_overlap_degenerate"],
            "required_before_use": ["add_discriminating_observable_or_null_support"],
        },
        {
            "scenario_id": "full_design_condition_too_high",
            "rank_status": "full_rank_but_ill_conditioned",
            "null_fpr_status": "not_promoted",
            "depth_coherence_status": "not_promoted",
            "claim_tier": "blocked",
            "production_status": "blocked_ill_conditioned_design",
            "local_global_candidate_status": "blocked_no_claim",
            "allowed_report_phrase": "no-claim rank or overlap blocker",
            "blocked_reasons": ["full_design_condition_too_high"],
            "required_before_use": ["stabilize_response_basis_or_covariance"],
        },
        {
            "scenario_id": "missing_local_null_fpr",
            "rank_status": "full_rank",
            "null_fpr_status": "local_null_fpr_missing",
            "depth_coherence_status": "not_promoted",
            "claim_tier": "blocked",
            "production_status": "blocked_missing_local_fpr",
            "local_global_candidate_status": "blocked_no_claim",
            "allowed_report_phrase": "no-claim missing FPR prerequisite",
            "blocked_reasons": ["local_null_fpr_missing"],
            "required_before_use": ["attach_pr061_local_null_fpr_report"],
        },
        {
            "scenario_id": "high_survey_systematic_fpr",
            "rank_status": "full_rank",
            "null_fpr_status": "survey_systematic_null_fpr_exceeds_threshold",
            "depth_coherence_status": "not_promoted",
            "claim_tier": "blocked",
            "production_status": "blocked_systematic_fpr",
            "local_global_candidate_status": "blocked_no_claim",
            "allowed_report_phrase": "no-claim high FPR prerequisite",
            "blocked_reasons": ["survey_systematic_null_fpr_exceeds_threshold"],
            "required_before_use": [
                "tighten_or_explain_survey_systematic_null_response",
            ],
        },
    ]


def build_result_pack_payload(
    *,
    repo_root: Path | str = Path("."),
    generating_command: str,
    worktree_state: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    status_rows = _load_status_rows(root)
    dependency_status = _dependency_status(status_rows)
    input_hashes = _input_hashes(root)
    legacy_ver2_context = _load_legacy_ver2_pack(root)
    config = {
        "schema_version": SCHEMA_VERSION,
        "dependencies": list(DEPENDENCIES),
        "input_files": list(INPUT_FILES),
        "artifact_id": ARTIFACT_ID,
        "artifact_path": ARTIFACT_PATH,
    }
    config_hash = _stable_hash(config)
    gate_summary = _gate_summary()
    rank_scenarios = _rank_scenarios()
    payload = {
        "artifact_id": ARTIFACT_ID,
        "artifact_path": ARTIFACT_PATH,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "schema_version": SCHEMA_VERSION,
        "created_by": CREATED_BY,
        "transfer_source": "none",
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "caveats": list(DEFAULT_CAVEATS),
        "sky_support_status": "not_directional",
        "null_mock_status": "summarized_from_local_and_survey_systematic_fpr_gates",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": worktree_state or _git_state(root),
        "dependencies": list(DEPENDENCIES),
        "dependency_status": dependency_status,
        "global_tilt_claim_tier_ceiling": "conditional",
        "gate_summary": gate_summary,
        "rank_scenarios": rank_scenarios,
        "legacy_ver2_context": legacy_ver2_context,
        "claim_boundaries": {
            "native_solver_status": "not_native_solver_output",
            "family_status": "blocked_until_native_morphology_atlas",
            "geometry_status": "blocked_until_native_morphology_atlas",
            "mio_coherence_use": "diagnostic_cross_check_not_htt_evidence",
            "htt_pushforward_use": "htt_owned_transfer_conditional_context_only",
            "common_pack_use": "report_composition_not_inference",
        },
        "manifest": {
            "artifact_id": ARTIFACT_ID,
            "artifact_path": ARTIFACT_PATH,
            "owner": "COMMON",
            "implementation_scope": "common",
            "claim_tier": "diagnostic_only",
            "production_status": "diagnostic_only",
            "created_by": CREATED_BY,
            "git_commit": None,
            "config_hash": config_hash,
            "input_hashes": input_hashes,
            "code_version": worktree_state or _git_state(root),
            "schema_version": SCHEMA_VERSION,
            "caveats": list(DEFAULT_CAVEATS),
            "required_gates": [
                "dependencies_implemented",
                "rank_audit_reported",
                "local_and_survey_systematic_fpr_reported",
                "depth_gap_and_directional_coherence_reported",
                "rank_blockers_suppress_candidate_language",
                "manifest_metadata_present",
            ],
            "passed_gates": [
                "rank_audit_reported",
                "local_and_survey_systematic_fpr_reported",
                "depth_gap_and_directional_coherence_reported",
                "rank_blockers_suppress_candidate_language",
                "manifest_metadata_present",
            ],
            "failed_gates": [
                gate
                for gate in ["dependencies_implemented"]
                if not all(item["implemented"] for item in dependency_status.values())
            ],
            "statistics_definitions": {
                "surface": "Result Pack B",
                "rank_section": "PR-060 response-overlap and rank audit",
                "fpr_section": "PR-061 local and PR-062 survey/systematic FPR gates",
                "depth_section": "PR-101 G_F redshift-bin bridge references",
                "directional_section": "PR-100 MIO directional coherence metadata",
                "pushforward_section": "PR-066 HTT pushforward context",
                "legacy_ver2_context": "hashed_prior_context_only",
                "claim_tier_ceiling": "conditional",
            },
        },
    }
    return payload


def _table(headers: tuple[str, ...], rows: list[tuple[Any, ...]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Result Pack B - Local Global Discrimination",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        f"config_hash: `{payload['config_hash']}`",
        "input_hashes:",
    ]
    lines.extend(f"- {item}" for item in payload["input_hashes"])
    lines.extend(
        [
            "sky_support_status: not_directional",
            "null_mock_status: summarized_from_local_and_survey_systematic_fpr_gates",
            f"generating_command: `{payload['generating_command']}`",
            f"git_commit_or_worktree_state: `{payload['git_commit_or_worktree_state']}`",
            "",
            "## Scope",
            "",
            (
                "This COMMON diagnostic-only pack summarizes existing HTT and MIO "
                "gate surfaces for local/global discrimination. It composes report "
                "metadata only. MIO directional and depth diagnostics are a "
                "diagnostic cross-check, not HTT evidence, and legacy VER2 Pack B "
                "rows remain prior context."
            ),
            "",
            f"Global tilt claim tier ceiling: {payload['global_tilt_claim_tier_ceiling']}",
            "",
            "## Gate Summary",
            "",
        ]
    )
    lines.extend(
        _table(
            (
                "Category",
                "Owner",
                "Source PR",
                "Surface",
                "Required Status",
                "Claim Role",
            ),
            [
                (
                    row["category"].replace("_", " "),
                    row["owner"],
                    row["source_pr"],
                    row["surface"],
                    row["required_status"],
                    row["claim_role"],
                )
                for row in payload["gate_summary"]
            ],
        )
    )
    lines.extend(
        [
            "",
            "The local/systematic null FPR rows are prerequisite gates, not "
            "posterior or evidence rows. The rank audit, G_F depth gap, and "
            "directional coherence rows are reported as separate dependency "
            "surfaces.",
            "",
            "## Rank And FPR Scenarios",
            "",
        ]
    )
    lines.extend(
        _table(
            (
                "Scenario",
                "Rank Status",
                "Null FPR Status",
                "Claim Tier",
                "Status",
                "Allowed Phrase",
            ),
            [
                (
                    row["scenario_id"],
                    row["rank_status"],
                    row["null_fpr_status"],
                    row["claim_tier"],
                    row["local_global_candidate_status"],
                    row["allowed_report_phrase"],
                )
                for row in payload["rank_scenarios"]
            ],
        )
    )
    lines.extend(["", "## Dependency Status", ""])
    lines.extend(
        _table(
            ("PR", "Implemented", "Smoke Tested", "Claim Tier", "Production Gate"),
            [
                (
                    pr_id,
                    status["implemented"],
                    status["smoke_tested"],
                    status["claim_tier"],
                    status["production_validated"],
                )
                for pr_id, status in payload["dependency_status"].items()
            ],
        )
    )
    lines.extend(["", "## Legacy VER2 Context", ""])
    legacy = payload["legacy_ver2_context"]
    lines.extend(
        [
            (
                f"Source `{legacy['source_path']}` is hashed as prior context. "
                f"PR-111 status: `{legacy['pr111_use']}`."
            ),
            "",
        ]
    )
    lines.extend(
        _table(
            (
                "Artifact",
                "Owner",
                "Source Tier",
                "Source Gate",
                "PR-111 Status",
            ),
            [
                (
                    item["artifact_id"],
                    item["owner"],
                    item["source_claim_tier"],
                    item["source_production_status"],
                    item["pr111_status"],
                )
                for item in legacy["artifacts"]
            ],
        )
    )
    lines.extend(["", "## Claim Boundaries", ""])
    lines.extend(
        f"- {key}: {value}"
        for key, value in payload["claim_boundaries"].items()
    )
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in payload["caveats"])
    lines.extend(
        [
            "",
            "## Manifest",
            "",
            "```json",
            json.dumps(payload["manifest"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _existing_pack_worktree_state(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("git_commit_or_worktree_state: `") and line.endswith("`"):
            return line.removeprefix("git_commit_or_worktree_state: `").removesuffix("`")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = "python scripts/result_packs/generate_pack_B_local_global.py"
    if args.dry_run:
        command += " --dry-run"
    if args.output != DEFAULT_OUTPUT:
        command += f" --output {args.output}"
    output = args.repo_root / args.output
    worktree_state = _existing_pack_worktree_state(output) if args.check else None
    payload = build_result_pack_payload(
        repo_root=args.repo_root,
        generating_command=command,
        worktree_state=worktree_state,
    )
    markdown = render_markdown(payload)
    if args.dry_run:
        print("DRY-RUN: not writing result pack")
        print(markdown)
        return 0
    if args.check:
        if not output.exists():
            print(f"missing result pack: {output}")
            return 1
        current = output.read_text(encoding="utf-8")
        if current != markdown:
            print(f"stale result pack: {output}")
            return 1
        print(f"up-to-date {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
