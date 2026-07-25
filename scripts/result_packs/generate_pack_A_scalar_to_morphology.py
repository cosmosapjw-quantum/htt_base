#!/usr/bin/env python3
"""Generate Result Pack A: scalar-to-morphology diagnostic comparison."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


SCHEMA_VERSION = "common.result_pack_A_scalar_to_morphology.v1"
DEFAULT_OUTPUT = Path("docs/generated/result_pack_A.md")
ARTIFACT_ID = "result_pack_A_scalar_to_morphology"
ARTIFACT_PATH = "docs/generated/result_pack_A.md"
CREATED_BY = "scripts/result_packs/generate_pack_A_scalar_to_morphology.py"
DEPENDENCIES = ("PR-056", "PR-076", "PR-092")
INPUT_FILES = (
    "scripts/result_packs/generate_pack_A_scalar_to_morphology.py",
    "docs/ver2_upgrade/generated/result_pack_A_scalar_to_morphology.json",
    "docs/PR_DELTAS/pr-056.md",
    "docs/PR_DELTAS/pr-076.md",
    "docs/PR_DELTAS/pr-092.md",
    "htt/mio/reports/departure_report.py",
    "htt/obsstat/scalar_lowell.py",
    "htt/obsstat/morphology.py",
    "htt/obsstat/null_ensembles.py",
    "htt/htt/htt/statistics/mes_information_gain.py",
    "docs/generated/status_snapshot.json",
)
DEFAULT_CAVEATS = (
    "diagnostic-only comparison over existing contract-backed report surfaces",
    "scalar Q/F/Pi values do not identify geometry or a Bianchi family",
    "morphology and MES features are observer/statistics diagnostics, not native atlas support",
    "native morphology atlas support remains absent",
    "no HTT evidence, MIO output, or native solver output is merged",
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
    path = repo_root / "docs/ver2_upgrade/generated/result_pack_A_scalar_to_morphology.json"
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
        "pr110_use": "legacy_context_only_not_promoted",
        "artifacts": [
            {
                "artifact_id": item.get("artifact_id", "unknown"),
                "owner": item.get("owner", "unknown"),
                "source_claim_tier": item.get("claim_tier", "unknown"),
                "current_public_production_status": CURRENT_PUBLIC_PRODUCTION_STATUS,
                "legacy_readiness_status": LEGACY_READINESS_STATUS,
                "native_morphology_atlas_status": NATIVE_MORPHOLOGY_ATLAS_STATUS,
                "pr110_status": "prior_context_only",
            }
            for item in source.get("artifacts", [])
            if isinstance(item, dict)
        ],
        "source_caveats": list(source.get("caveats", [])),
    }


def _diagnostic_payloads() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scalar = [
        {
            "name": "Q",
            "owner": "MIO",
            "source_pr": "PR-056",
            "surface": "DepartureReport.sections.Q",
            "role": "policy-normalized diagnostic score",
            "claim_tier": "diagnostic_only",
            "required_provenance": "denominator policy and transfer provenance by section",
            "comparison_use": "scalar compression for side-by-side reporting only",
        },
        {
            "name": "F",
            "owner": "MIO",
            "source_pr": "PR-056",
            "surface": "DepartureReport.sections.F",
            "role": "certified filling-fraction diagnostic when supplied",
            "claim_tier": "diagnostic_only",
            "required_provenance": "admissible ceiling budget and samplewise input hashes",
            "comparison_use": "occupancy-style diagnostic status, not evidence",
        },
        {
            "name": "Pi",
            "owner": "MIO",
            "source_pr": "PR-056",
            "surface": "DepartureReport.sections.Pi",
            "role": "empirical exceedance curve",
            "claim_tier": "diagnostic_only",
            "required_provenance": "measure kind, thresholds, and source score label",
            "comparison_use": "tail-shape descriptor, not truth probability",
        },
    ]
    morphology_mes = [
        {
            "name": "Low-ell scalar features",
            "owner": "OBSSTAT",
            "source_pr": "PR-076",
            "surface": "obsstat.scalar_lowell.LowEllScalarSummary",
            "role": "observer-side scalar feature extraction",
            "claim_tier": "diagnostic_only",
            "required_provenance": "null ensemble and look-elsewhere metadata for p-values",
            "comparison_use": "records scalar feature provenance feeding the upgrade context",
        },
        {
            "name": "Morphology axes",
            "owner": "OBSSTAT",
            "source_pr": "PR-076",
            "surface": "obsstat.morphology.MorphologyAxisSummary",
            "role": "diagnostic morphology-axis and alignment features",
            "claim_tier": "diagnostic_only",
            "required_provenance": "mask, covariance, null, and scan-volume metadata",
            "comparison_use": "morphology descriptors without native atlas or family labels",
        },
        {
            "name": "MES I_morph",
            "owner": "COMMON",
            "source_pr": "PR-092",
            "surface": "htt.statistics.mes_information_gain.MesInformationGainReport",
            "role": "branch-separated MES morphology information-gain report",
            "claim_tier": "diagnostic_only_or_blocked",
            "required_provenance": "positive finite branch bounds and matched source manifests",
            "comparison_use": "reports template/covariance tightening status under caveats",
        },
    ]
    return scalar, morphology_mes


def _comparison_matrix(
    scalar: list[dict[str, Any]],
    morphology_mes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scalar_item in scalar:
        for morphology_item in morphology_mes:
            rows.append(
                {
                    "scalar": scalar_item["name"],
                    "morphology_mes": morphology_item["name"],
                    "comparison_status": "diagnostic_side_by_side",
                    "allowed_statement": (
                        f"{scalar_item['name']} and {morphology_item['name']} "
                        "can be reported together only as claim-tiered diagnostics "
                        "with separate provenance."
                    ),
                    "blocked_statement": (
                        "Do not infer geometry, family labels, native-solver support, "
                        "or posterior/evidence from this comparison."
                    ),
                }
            )
    return rows


def build_result_pack_payload(
    *,
    repo_root: Path | str = Path("."),
    generating_command: str,
    worktree_state: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    status_rows = _load_status_rows(root)
    scalar, morphology_mes = _diagnostic_payloads()
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
    dependency_status = {
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
        "null_mock_status": "summarized_from_dependency_surfaces",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": worktree_state or _git_state(root),
        "dependencies": list(DEPENDENCIES),
        "dependency_status": dependency_status,
        "scalar_diagnostics": scalar,
        "morphology_mes_diagnostics": morphology_mes,
        "legacy_ver2_context": legacy_ver2_context,
        "comparison_matrix": _comparison_matrix(scalar, morphology_mes),
        "claim_boundaries": {
            "native_solver_status": "not_native_solver_output",
            "family_status": "blocked_until_native_morphology_atlas",
            "geometry_status": "blocked_until_native_morphology_atlas",
            "htt_status": "no_posterior_or_evidence_content",
            "mio_status": "diagnostics_remain_separate_from_common_pack",
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
                "scalar_and_morphology_provenance_separate",
                "no_native_or_family_claim",
                "manifest_metadata_present",
            ],
            "passed_gates": [
                "scalar_and_morphology_provenance_separate",
                "no_native_or_family_claim",
                "manifest_metadata_present",
            ],
            "failed_gates": [
                gate
                for gate in ["dependencies_implemented"]
                if not all(item["implemented"] for item in dependency_status.values())
            ],
            "statistics_definitions": {
                "surface": "Result Pack A",
                "scalar_section": "MIO Q/F/Pi diagnostic report surfaces",
                "morphology_mes_section": (
                    "OBSSTAT morphology/null metadata plus COMMON MES I_morph report"
                ),
                "comparison_status": "diagnostic_side_by_side",
                "native_atlas_status": "absent",
                "legacy_ver2_context": "hashed_prior_context_only",
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
        "# Result Pack A - Scalar To Morphology Upgrade",
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
            "null_mock_status: summarized_from_dependency_surfaces",
            f"generating_command: `{payload['generating_command']}`",
            f"git_commit_or_worktree_state: `{payload['git_commit_or_worktree_state']}`",
            "",
            "## Scope",
            "",
            (
                "This is a diagnostic-only comparison pack. It compares scalar "
                "MIO Q/F/Pi report surfaces with OBSSTAT morphology features and "
                "COMMON MES I_morph status under explicit caveats. Native "
                "morphology atlas support remains absent."
            ),
            "",
            "## Scalar Diagnostics",
            "",
        ]
    )
    lines.extend(
        _table(
            ("Name", "Owner", "Surface", "Role", "Required Provenance"),
            [
                (
                    item["name"],
                    item["owner"],
                    item["surface"],
                    item["role"],
                    item["required_provenance"],
                )
                for item in payload["scalar_diagnostics"]
            ],
        )
    )
    lines.extend(["", "## Morphology And MES Diagnostics", ""])
    lines.extend(
        _table(
            ("Name", "Owner", "Surface", "Role", "Required Provenance"),
            [
                (
                    item["name"],
                    item["owner"],
                    item["surface"],
                    item["role"],
                    item["required_provenance"],
                )
                for item in payload["morphology_mes_diagnostics"]
            ],
        )
    )
    lines.extend(["", "## Comparison Matrix", ""])
    lines.extend(
        _table(
            ("Scalar", "Morphology/MES", "Status", "Allowed Statement"),
            [
                (
                    row["scalar"],
                    row["morphology_mes"],
                    row["comparison_status"],
                    row["allowed_statement"],
                )
                for row in payload["comparison_matrix"]
            ],
        )
    )
    lines.extend(["", "## Legacy VER2 Context", ""])
    legacy = payload["legacy_ver2_context"]
    lines.extend(
        [
            (
                f"Source `{legacy['source_path']}` is hashed as prior context. "
                "This PR records those source rows without promoting their source "
                "tier or source readiness labels. The readiness labels are provenance only."
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
                "PR-110 Status",
            ),
            [
                (
                    item["artifact_id"],
                    item["owner"],
                    item["source_claim_tier"],
                    item["current_public_production_status"],
                    item["legacy_readiness_status"],
                    item["pr110_status"],
                )
                for item in legacy["artifacts"]
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
    command = "python scripts/result_packs/generate_pack_A_scalar_to_morphology.py"
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
