#!/usr/bin/env python3
"""Generate Result Pack C: MIO observatory certificate status summary."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


SCHEMA_VERSION = "common.result_pack_C_mio_certificates.v1"
DEFAULT_OUTPUT = Path("docs/generated/result_pack_C.md")
ARTIFACT_ID = "result_pack_C_mio_certificates"
ARTIFACT_PATH = "docs/generated/result_pack_C.md"
CREATED_BY = "scripts/result_packs/generate_pack_C_mio_certificates.py"
DEPENDENCIES = ("PR-100", "PR-101", "PR-102", "PR-103")
INPUT_FILES = (
    "scripts/result_packs/generate_pack_C_mio_certificates.py",
    "docs/ver2_upgrade/generated/result_pack_D_mio_certificates.json",
    "docs/PR_DELTAS/pr-100.md",
    "docs/PR_DELTAS/pr-101.md",
    "docs/PR_DELTAS/pr-102.md",
    "docs/PR_DELTAS/pr-103.md",
    "htt/mio/coherence/directional.py",
    "htt/mio/coherence/redshift_binned.py",
    "htt/mio/tension/flrw_tension.py",
    "htt/mio/diagnostics/predictive_residuals.py",
    "htt/mio/decomposition/evidence_anatomy.py",
    "htt/mio/interface/mio_certificate.py",
    "htt/workspace/contracts/mio_certificate.py",
    "docs/generated/status_snapshot.json",
)
DEFAULT_CAVEATS = (
    "common_diagnostic_only_report_over_existing_mio_surfaces",
    "mio_certificates_are_diagnostic_reports_not_model_rankings",
    "legacy_readiness_labels_are_not_current_public_production",
    "blocked_or_descriptive_certificate_rows_remain_no_claim",
    "htt_evidence_trace_context_is_read_only_and_not_mio_evidence",
    "legacy_ver2_mio_certificate_pack_is_prior_context_only_not_promoted",
    "native_morphology_atlas_support_remains_absent",
    "readiness labels are provenance only; not current production readiness",
)
CURRENT_PUBLIC_PRODUCTION_STATUS = "diagnostic_only"
LEGACY_READINESS_STATUS = "legacy_not_current"
NATIVE_MORPHOLOGY_ATLAS_STATUS = "unavailable_pre_native_solver"
READINESS_CAVEAT = (
    "readiness labels are provenance only; not current production readiness"
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
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=normal"],
                cwd=repo_root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
        )
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
    path = repo_root / "docs/ver2_upgrade/generated/result_pack_D_mio_certificates.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    return {
        "source_path": str(path.relative_to(repo_root)),
        "source_title": source.get("title", "unknown"),
        "source_topic": source.get("topic", "unknown"),
        "source_claim_tier": source.get("claim_tier", "unknown"),
        "current_public_production_status": CURRENT_PUBLIC_PRODUCTION_STATUS,
        "legacy_readiness_status": LEGACY_READINESS_STATUS,
        "native_morphology_atlas_status": NATIVE_MORPHOLOGY_ATLAS_STATUS,
        "readiness_caveat": READINESS_CAVEAT,
        "pr112_use": "legacy_context_only_not_promoted",
        "legacy_pack_id": source.get("pack_id", "unknown"),
        "artifacts": [
            {
                "artifact_id": item.get("artifact_id", "unknown"),
                "owner": item.get("owner", "unknown"),
                "source_claim_tier": item.get("claim_tier", "unknown"),
                "current_public_production_status": CURRENT_PUBLIC_PRODUCTION_STATUS,
                "legacy_readiness_status": LEGACY_READINESS_STATUS,
                "native_morphology_atlas_status": NATIVE_MORPHOLOGY_ATLAS_STATUS,
                "pr112_status": "prior_context_only",
            }
            for item in source.get("artifacts", [])
            if isinstance(item, dict)
        ],
        "source_caveat_count": len(source.get("caveats", [])),
        "source_caveat_status": "not_republished_prior_context_only",
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


def _certificate_rows() -> list[dict[str, Any]]:
    return [
        {
            "category": "directional_coherence_certificate",
            "name": "directional coherence certificate",
            "owner": "MIO",
            "source_pr": "PR-100",
            "surface": "mio.coherence.directional.to_mio_certificate",
            "status_metadata_surface": (
                "manifest.statistics_definitions.certificate_status_metadata"
            ),
            "diagnostic_statuses": [
                "blocked_missing_covariance",
                "blocked_missing_null_mocks",
                "diagnostic_only",
            ],
            "legacy_readiness_statuses": [LEGACY_READINESS_STATUS],
            "required_metadata": [
                "covariance_status",
                "null_mock_status",
                "sky_support_status",
                "direction_convention",
                "weighting_convention",
            ],
            "caveat_policy": "incomplete_covariance_null_or_sky_remains_diagnostic",
            "model_ranking_status": "forbidden_not_ranked",
        },
        {
            "category": "redshift_binned_coherence_certificate",
            "name": "redshift binned coherence certificate",
            "owner": "MIO",
            "source_pr": "PR-101",
            "surface": "mio.coherence.redshift_binned.to_mio_certificate",
            "status_metadata_surface": (
                "manifest.statistics_definitions.certificate_status_metadata"
            ),
            "diagnostic_statuses": [
                "blocked_missing_covariance",
                "diagnostic_only",
                "descriptive_fallback",
            ],
            "legacy_readiness_statuses": [LEGACY_READINESS_STATUS],
            "required_metadata": [
                "depth_bin_selection_status",
                "depth_bin_covariance_status",
                "depth_bin_null_metadata_status",
                "depth_bin_sky_mask_status",
                "g_f_bridge_status",
            ],
            "caveat_policy": "missing_depth_or_g_f_bridge_metadata_remains_descriptive",
            "model_ranking_status": "forbidden_not_ranked",
        },
        {
            "category": "flrw_null_predictive_certificate",
            "name": "FLRW null predictive certificate",
            "owner": "MIO",
            "source_pr": "PR-102",
            "surface": "mio.tension.flrw_tension.to_mio_certificate",
            "status_metadata_surface": (
                "manifest.statistics_definitions.certificate_status_metadata"
            ),
            "diagnostic_statuses": [
                "blocked_missing_null_mocks",
                "blocked_missing_covariance",
                "descriptive_only_blocked",
            ],
            "legacy_readiness_statuses": [LEGACY_READINESS_STATUS],
            "required_metadata": [
                "null_predictive_distribution_status",
                "look_elsewhere_status",
                "tail_probability_export_status",
                "matched_covariance_calibrated",
                "matched_null_mocks_calibrated",
            ],
            "caveat_policy": "raw_empirical_tails_are_descriptive_until_matched",
            "model_ranking_status": "forbidden_not_ranked",
        },
        {
            "category": "predictive_residual_context",
            "name": "predictive residual context",
            "owner": "MIO",
            "source_pr": "PR-103",
            "surface": "mio.diagnostics.predictive_residuals",
            "status_metadata_surface": "predictive_residual_atlas_payload",
            "diagnostic_statuses": ["diagnostic_only", "residual_context_only"],
            "legacy_readiness_statuses": [],
            "required_metadata": [
                "covariance_status",
                "rank_status",
                "native_atlas_status",
                "single_score_status",
                "residual_convention",
            ],
            "caveat_policy": "raw_residual_context_not_htt_evidence",
            "model_ranking_status": "forbidden_not_ranked",
        },
        {
            "category": "evidence_anatomy_narrative",
            "name": "evidence anatomy narrative",
            "owner": "MIO",
            "source_pr": "PR-103",
            "surface": "mio.decomposition.evidence_anatomy",
            "status_metadata_surface": "EvidenceAnatomyNarrativeReport.as_payload",
            "diagnostic_statuses": [
                "diagnostic_only",
                "blocked_provenance_mismatch",
            ],
            "legacy_readiness_statuses": [],
            "required_metadata": [
                "trace_source_owner",
                "htt_evidence_modification_status",
                "single_score_status",
                "prior_sweep_status",
                "posterior_predictive_status",
                "loocv_status",
                "matched_null_status",
            ],
            "caveat_policy": "read_only_trace_context_without_owner_merge",
            "model_ranking_status": "forbidden_not_ranked",
        },
    ]


def _status_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "complete_mio_metadata",
            "public_readiness_label": "diagnostic-only",
            "legacy_readiness_status": LEGACY_READINESS_STATUS,
            "claim_tier_ceiling": "conditional",
            "certificate_use": "diagnostic_certificate_with_complete_metadata",
            "model_ranking_status": "forbidden_not_ranked",
            "required_before_use": [
                "matched_covariance",
                "matched_null_mocks",
                "complete_sky_or_mask_support",
                "complete_status_metadata",
            ],
            "caveats": [
                "legacy_readiness_is_not_current_public_production",
            ],
        },
        {
            "scenario_id": "missing_covariance_or_null",
            "public_readiness_label": "diagnostic-only",
            "legacy_readiness_status": LEGACY_READINESS_STATUS,
            "claim_tier_ceiling": "blocked",
            "certificate_use": "blocked_or_diagnostic_no_claim",
            "model_ranking_status": "forbidden_not_ranked",
            "required_before_use": [
                "attach_covariance_status",
                "attach_matched_null_metadata",
            ],
            "caveats": [
                "incomplete_covariance_or_null_blocks_current_readiness",
            ],
        },
        {
            "scenario_id": "descriptive_tail_only",
            "public_readiness_label": "diagnostic-only",
            "legacy_readiness_status": LEGACY_READINESS_STATUS,
            "claim_tier_ceiling": "blocked",
            "certificate_use": "diagnostic_only_descriptive",
            "model_ranking_status": "forbidden_not_ranked",
            "required_before_use": [
                "global_look_elsewhere_correction",
                "typed_null_predictive_payload",
                "matched_mask_noise_sky_support",
            ],
            "caveats": [
                "raw_or_local_tail_summaries_do_not_promote_certificate_readiness",
            ],
        },
        {
            "scenario_id": "htt_evidence_trace_narrative",
            "public_readiness_label": "diagnostic-only",
            "legacy_readiness_status": LEGACY_READINESS_STATUS,
            "claim_tier_ceiling": "diagnostic_only",
            "certificate_use": "read_only_context_not_mio_evidence",
            "model_ranking_status": "forbidden_not_ranked",
            "required_before_use": [
                "htt_source_owner",
                "prior_ppc_loocv_matched_null_ready",
                "single_score_absent",
            ],
            "caveats": [
                "mio_narrative_does_not_modify_htt_trace_values",
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
    certificate_rows = _certificate_rows()
    status_scenarios = _status_scenarios()
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
        "null_mock_status": "summarized_from_mio_certificate_status_metadata",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": worktree_state or _git_state(root),
        "dependencies": list(DEPENDENCIES),
        "dependency_status": dependency_status,
        "certificate_rows": certificate_rows,
        "status_scenarios": status_scenarios,
        "report_gates": {
            "markdown_rendered": "pass",
            "manifest_metadata_present": "pass",
            "mio_certificate_statuses_gathered": "pass",
            "dependencies_gathered": (
                "pass"
                if all(item["implemented"] for item in dependency_status.values())
                else "fail"
            ),
        },
        "science_gates": {
            "covariance_null_complete": "not_bound",
            "model_ranking_allowed": "forbidden",
            "native_morphology_atlas_bound": "not_bound",
            "predictive_adequacy_ppc": "not_bound",
            "loocv_status": "not_run",
        },
        "gate_separation_note": (
            "report_gates describe report-generation only; a clean report render "
            "does not imply any science gate is met."
        ),
        "legacy_ver2_context": legacy_ver2_context,
        "claim_boundaries": {
            "certificate_ranking_status": "forbidden_not_ranked",
            "mio_status": "diagnostic_observatory_surfaces_only",
            "htt_status": "read_only_context_by_reference_only",
            "common_pack_use": "report_composition_not_inference",
            "native_solver_status": "not_native_solver_output",
            "family_status": "blocked_until_native_morphology_atlas",
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
                "mio_certificate_statuses_gathered",
                "diagnostic_public_readiness_explicit",
                "certificate_ranking_forbidden",
                "manifest_metadata_present",
            ],
            "passed_gates": [
                "mio_certificate_statuses_gathered",
                "diagnostic_public_readiness_explicit",
                "certificate_ranking_forbidden",
                "manifest_metadata_present",
            ],
            "failed_gates": [
                gate
                for gate in ["dependencies_implemented"]
                if not all(item["implemented"] for item in dependency_status.values())
            ],
            "statistics_definitions": {
                "surface": "Result Pack C",
                "certificate_section": "MIO certificate/status rows",
                "status_section": "Diagnostic-only public readiness labels",
                "legacy_ver2_context": "hashed_prior_context_only",
                "ranking_status": "forbidden_not_ranked",
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
        "# Result Pack C - MIO Observatory Certificates",
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
            "null_mock_status: summarized_from_mio_certificate_status_metadata",
            f"generating_command: `{payload['generating_command']}`",
            f"git_commit_or_worktree_state: `{payload['git_commit_or_worktree_state']}`",
            "",
            "## Scope",
            "",
            (
                "This COMMON diagnostic-only pack gathers MIO observatory "
                "certificate/status surfaces by reference. It does not rank "
                "models, does not modify HTT-owned evidence traces, and does "
                "not promote legacy VER2 certificate rows."
            ),
            "",
            "Diagnostic-only public readiness is explicit.",
            "",
            "## Gate Separation",
            "",
            payload["gate_separation_note"],
            "",
        ]
    )
    lines.extend(
        _table(
            ("Report Gate", "Status"),
            [(name.replace("_", " "), status) for name, status in payload["report_gates"].items()],
        )
    )
    lines.extend(["", "Science gates remain separate from report gates:", ""])
    lines.extend(
        _table(
            ("Science Gate", "Status"),
            [(name.replace("_", " "), status) for name, status in payload["science_gates"].items()],
        )
    )
    lines.extend(
        [
            "",
            "## Certificate Rows",
            "",
        ]
    )
    lines.extend(
        _table(
            (
                "Name",
                "Owner",
                "Source PR",
                "Surface",
                "Diagnostic Statuses",
                "Legacy Readiness Statuses",
                "Ranking",
            ),
            [
                (
                    row["name"],
                    row["owner"],
                    row["source_pr"],
                    row["surface"],
                    ", ".join(row["diagnostic_statuses"]),
                    ", ".join(row["legacy_readiness_statuses"]) or "none",
                    row["model_ranking_status"],
                )
                for row in payload["certificate_rows"]
            ],
        )
    )
    lines.extend(["", "## Status Scenarios", ""])
    lines.extend(
        _table(
            (
                "Scenario",
                "Public Readiness Label",
                "Legacy Readiness",
                "Claim Tier Ceiling",
                "Certificate Use",
                "Ranking",
            ),
            [
                (
                    row["scenario_id"],
                    row["public_readiness_label"],
                    row["legacy_readiness_status"],
                    row["claim_tier_ceiling"],
                    row["certificate_use"],
                    row["model_ranking_status"],
                )
                for row in payload["status_scenarios"]
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
                f"Legacy pack `{legacy['legacy_pack_id']}` status under PR-112: "
                f"`{legacy['pr112_use']}`. The readiness labels are provenance only."
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
                "Current Public Status",
                "Legacy Readiness",
                "PR-112 Status",
            ),
            [
                (
                    item["artifact_id"],
                    item["owner"],
                    item["source_claim_tier"],
                    item["current_public_production_status"],
                    item["legacy_readiness_status"],
                    item["pr112_status"],
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
    command = "python scripts/result_packs/generate_pack_C_mio_certificates.py"
    if args.dry_run:
        command += " --dry-run"
    if args.output != DEFAULT_OUTPUT:
        command += f" --output {args.output}"
    payload = build_result_pack_payload(
        repo_root=args.repo_root,
        generating_command=command,
    )
    markdown = render_markdown(payload)
    if args.dry_run:
        print("DRY-RUN: not writing result pack")
        print(markdown)
        return 0
    output = args.repo_root / args.output
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
