#!/usr/bin/env python3
"""Build the PR-114 external audit disclosure package.

The package is a pre-solver audit bundle. It preserves claim tiers, transfer
provenance, manuscript blockers, and future-solver schema boundaries; it does
not certify publication readiness or native solver validation.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from typing import Any, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ZIP = Path("docs/generated/external_audit_package.zip")
DEFAULT_OUTPUT_MANIFEST = Path("docs/generated/external_audit_package_manifest.json")
SCHEMA_VERSION = "common.external_audit_package.v1"
ARTIFACT_ID = "external_audit_package"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class AuditPackageEntry:
    source_path: Path
    archive_path: str
    group: str
    description: str


def _entry(source: str, archive: str, group: str, description: str) -> AuditPackageEntry:
    return AuditPackageEntry(Path(source), archive, group, description)


DEFAULT_PACKAGE_ENTRIES: tuple[AuditPackageEntry, ...] = (
    # Prompts
    _entry("docs/audit_prompts/README.md", "prompts/README.md", "audit_prompts", "audit prompt index"),
    _entry(
        "docs/audit_prompts/claim_firewall_review.md",
        "prompts/claim_firewall_review.md",
        "audit_prompts",
        "claim firewall review prompt",
    ),
    _entry(
        "docs/audit_prompts/future_solver_interface_review.md",
        "prompts/future_solver_interface_review.md",
        "audit_prompts",
        "future solver interface review prompt",
    ),
    _entry(
        "docs/audit_prompts/local_global_review.md",
        "prompts/local_global_review.md",
        "audit_prompts",
        "local/global discrimination review prompt",
    ),
    _entry(
        "docs/audit_prompts/manuscript_figure_review.md",
        "prompts/manuscript_figure_review.md",
        "audit_prompts",
        "manuscript and figure provenance prompt",
    ),
    _entry(
        "docs/audit_prompts/transfer_provenance_review.md",
        "prompts/transfer_provenance_review.md",
        "audit_prompts",
        "transfer provenance review prompt",
    ),
    # Status, claims, and progress.
    _entry("docs/generated/claim_ledger.json", "status/claim_ledger.json", "pr_status", "generated claim ledger"),
    _entry("docs/generated/status_snapshot.json", "status/status_snapshot.json", "pr_status", "generated status snapshot"),
    _entry("docs/generated/status_matrix.md", "status/status_matrix.md", "pr_status", "generated status matrix"),
    _entry("docs/codex_handoff/pr_status.yaml", "status/pr_status.yaml", "pr_status", "DAG PR status"),
    _entry("docs/codex_handoff/pr_backlog.yaml", "status/pr_backlog.yaml", "pr_status", "DAG PR backlog"),
    _entry(
        "docs/generated/progress_checkpoints/progress_scoreboard.md",
        "status/progress_scoreboard.md",
        "pr_status",
        "generated progress scoreboard",
    ),
    _entry(
        "docs/generated/progress_checkpoints/checkpoint_060.md",
        "status/checkpoint_060.md",
        "pr_status",
        "five-PR checkpoint 060",
    ),
    # Result and provenance reports.
    _entry("docs/generated/result_pack_A.md", "reports/result_pack_A.md", "result_packs", "scalar-to-morphology report"),
    _entry("docs/generated/result_pack_B.md", "reports/result_pack_B.md", "result_packs", "local/global report"),
    _entry("docs/generated/result_pack_C.md", "reports/result_pack_C.md", "result_packs", "MIO certificate report"),
    _entry(
        "docs/generated/transfer_sensitivity_report.md",
        "reports/transfer_sensitivity_report.md",
        "transfer_provenance",
        "transfer provenance report",
    ),
    _entry(
        "docs/generated/manuscript_figure_inventory.md",
        "manuscript/manuscript_figure_inventory.md",
        "manuscript_audit",
        "manuscript figure inventory",
    ),
    _entry(
        "docs/generated/missing_figure_references.md",
        "manuscript/missing_figure_references.md",
        "manuscript_audit",
        "missing and quarantined figure references",
    ),
    _entry(
        "docs/generated/quarantined_figures.md",
        "manuscript/quarantined_figures.md",
        "manuscript_audit",
        "repository figure quarantine report",
    ),
    # Dependency PR deltas.
    _entry("docs/PR_DELTAS/pr-110.md", "pr_deltas/pr-110.md", "framework_reports", "Result Pack A PR delta"),
    _entry("docs/PR_DELTAS/pr-111.md", "pr_deltas/pr-111.md", "framework_reports", "Result Pack B PR delta"),
    _entry("docs/PR_DELTAS/pr-112.md", "pr_deltas/pr-112.md", "framework_reports", "Result Pack C PR delta"),
    _entry("docs/PR_DELTAS/pr-113.md", "pr_deltas/pr-113.md", "framework_reports", "manuscript audit PR delta"),
    _entry("docs/PR_DELTAS/pr-080.md", "pr_deltas/pr-080.md", "transfer_provenance", "transfer registry PR delta"),
    _entry("docs/PR_DELTAS/pr-082.md", "pr_deltas/pr-082.md", "transfer_provenance", "atlas transfer PR delta"),
    _entry("docs/PR_DELTAS/pr-083.md", "pr_deltas/pr-083.md", "transfer_provenance", "native schema PR delta"),
    _entry("docs/PR_DELTAS/pr-100.md", "pr_deltas/pr-100.md", "framework_reports", "directional MIO certificate PR delta"),
    _entry("docs/PR_DELTAS/pr-101.md", "pr_deltas/pr-101.md", "framework_reports", "redshift MIO certificate PR delta"),
    _entry("docs/PR_DELTAS/pr-102.md", "pr_deltas/pr-102.md", "framework_reports", "FLRW tension PR delta"),
    _entry("docs/PR_DELTAS/pr-103.md", "pr_deltas/pr-103.md", "framework_reports", "PR-103 trace-anatomy PR delta"),
    # Code snapshot files: scoped sources, not a whole-repo dump.
    _entry(
        "scripts/build_external_audit_package.py",
        "code_snapshot/scripts/build_external_audit_package.py",
        "code_snapshot",
        "audit package generator",
    ),
    _entry(
        "scripts/result_packs/generate_pack_A_scalar_to_morphology.py",
        "code_snapshot/scripts/result_packs/generate_pack_A_scalar_to_morphology.py",
        "code_snapshot",
        "Result Pack A generator",
    ),
    _entry(
        "scripts/result_packs/generate_pack_B_local_global.py",
        "code_snapshot/scripts/result_packs/generate_pack_B_local_global.py",
        "code_snapshot",
        "Result Pack B generator",
    ),
    _entry(
        "scripts/result_packs/generate_pack_C_mio_certificates.py",
        "code_snapshot/scripts/result_packs/generate_pack_C_mio_certificates.py",
        "code_snapshot",
        "Result Pack C generator",
    ),
    _entry(
        "scripts/generate_transfer_sensitivity_report.py",
        "code_snapshot/scripts/generate_transfer_sensitivity_report.py",
        "code_snapshot",
        "transfer sensitivity report generator",
    ),
    _entry(
        "scripts/audit_manuscript_figures.py",
        "code_snapshot/scripts/audit_manuscript_figures.py",
        "code_snapshot",
        "manuscript figure audit generator",
    ),
    _entry("htt/src/common/artifact_manifest.py", "code_snapshot/htt/src/common/artifact_manifest.py", "code_snapshot", "manifest validation"),
    _entry("htt/src/common/transfer_registry.py", "code_snapshot/htt/src/common/transfer_registry.py", "code_snapshot", "transfer registry contract"),
    _entry("htt/src/common/status_snapshot.py", "code_snapshot/htt/src/common/status_snapshot.py", "code_snapshot", "status snapshot generator"),
    _entry("htt/bass/transfer/registry.py", "code_snapshot/htt/bass/transfer/registry.py", "code_snapshot", "external transfer registry"),
    _entry("htt/bass/transfer/aniclass_adapter.py", "code_snapshot/htt/bass/transfer/aniclass_adapter.py", "code_snapshot", "AniCLASS adapter"),
    _entry("htt/bass/transfer/native_schema.py", "code_snapshot/htt/bass/transfer/native_schema.py", "code_snapshot", "future native schema"),
    _entry("htt/bass/transfer/native_adapter.py", "code_snapshot/htt/bass/transfer/native_adapter.py", "code_snapshot", "future native adapter stub"),
    _entry("htt/bass/atlas/atlas_entry.py", "code_snapshot/htt/bass/atlas/atlas_entry.py", "code_snapshot", "AtlasEntryLite contract"),
    _entry("htt/mio/reports/departure_report.py", "code_snapshot/htt/mio/reports/departure_report.py", "code_snapshot", "MIO departure report"),
    _entry("htt/mio/coherence/directional.py", "code_snapshot/htt/mio/coherence/directional.py", "code_snapshot", "directional coherence certificate"),
    _entry("htt/mio/coherence/redshift_binned.py", "code_snapshot/htt/mio/coherence/redshift_binned.py", "code_snapshot", "redshift coherence certificate"),
    _entry("htt/mio/tension/flrw_tension.py", "code_snapshot/htt/mio/tension/flrw_tension.py", "code_snapshot", "FLRW tension gate"),
    _entry("htt/mio/decomposition/evidence_anatomy.py", "code_snapshot/htt/mio/decomposition/evidence_anatomy.py", "code_snapshot", "MIO trace anatomy narrative"),
    _entry("htt/htt/htt/departure/response_overlap.py", "code_snapshot/htt/htt/htt/departure/response_overlap.py", "code_snapshot", "HTT response overlap"),
    _entry("htt/htt/htt/departure/local_global_mixture.py", "code_snapshot/htt/htt/htt/departure/local_global_mixture.py", "code_snapshot", "HTT local/global mixture"),
    _entry("htt/htt/htt/departure/posterior_pushforward.py", "code_snapshot/htt/htt/htt/departure/posterior_pushforward.py", "code_snapshot", "HTT posterior pushforward"),
    _entry("htt/htt/htt/infer/loocv.py", "code_snapshot/htt/htt/htt/infer/loocv.py", "code_snapshot", "HTT LOOCV gate"),
    _entry("htt/htt/htt/infer/posterior_predictive.py", "code_snapshot/htt/htt/htt/infer/posterior_predictive.py", "code_snapshot", "HTT PPC gate"),
    _entry("htt/htt/htt/nulls/local_boost_depth_null.py", "code_snapshot/htt/htt/htt/nulls/local_boost_depth_null.py", "code_snapshot", "local boost null"),
    _entry("htt/htt/htt/nulls/selection_response_depth.py", "code_snapshot/htt/htt/htt/nulls/selection_response_depth.py", "code_snapshot", "survey/systematic null"),
    _entry("htt/obsstat/morphology.py", "code_snapshot/htt/obsstat/morphology.py", "code_snapshot", "OBSSTAT morphology"),
    _entry("htt/obsstat/scalar_lowell.py", "code_snapshot/htt/obsstat/scalar_lowell.py", "code_snapshot", "OBSSTAT scalar low-ell"),
    _entry("htt/obsstat/null_ensembles.py", "code_snapshot/htt/obsstat/null_ensembles.py", "code_snapshot", "OBSSTAT null ensembles"),
)


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _stable_hash(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return _sha256_bytes(data)


def _git_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_state(repo_root: Path) -> str:
    commit = _git_commit(repo_root)
    try:
        dirty = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    except OSError:
        return "unknown"
    return f"{commit}+dirty" if dirty else commit


def _command_from_args(argv: Sequence[str] | None) -> str:
    args = list(sys.argv[1:] if argv is None else argv)
    args = [arg for arg in args if arg != "--check"]
    return " ".join(["python", "scripts/build_external_audit_package.py", *args]).strip()


def _normalise_output_path(path: Path) -> str:
    return path.as_posix()


def _entry_rows(
    repo_root: Path,
    entries: Iterable[AuditPackageEntry],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_archive_paths: set[str] = set()
    missing: list[str] = []
    for entry in sorted(entries, key=lambda item: item.archive_path):
        if entry.archive_path.startswith("/") or ".." in Path(entry.archive_path).parts:
            raise ValueError(f"unsafe archive path: {entry.archive_path}")
        if entry.archive_path in seen_archive_paths:
            raise ValueError(f"duplicate archive path: {entry.archive_path}")
        seen_archive_paths.add(entry.archive_path)
        source = repo_root / entry.source_path
        if not source.is_file():
            missing.append(entry.source_path.as_posix())
            continue
        rows.append(
            {
                "source_path": entry.source_path.as_posix(),
                "archive_path": entry.archive_path,
                "group": entry.group,
                "description": entry.description,
                "sha256": _sha256_file(source),
                "size_bytes": source.stat().st_size,
            }
        )
    if missing:
        raise FileNotFoundError(
            "external audit package required inputs are missing: "
            + ", ".join(sorted(missing))
        )
    return rows


def _required_assertions(rows: Sequence[dict[str, Any]]) -> dict[str, bool]:
    archive_paths = {str(row["archive_path"]) for row in rows}
    groups = {str(row["group"]) for row in rows}
    return {
        "claim_ledger_included": "status/claim_ledger.json" in archive_paths,
        "transfer_provenance_included": "reports/transfer_sensitivity_report.md" in archive_paths,
        "figure_inventory_included": "manuscript/manuscript_figure_inventory.md" in archive_paths
        and "manuscript/missing_figure_references.md" in archive_paths,
        "audit_prompts_included": "audit_prompts" in groups and "prompts/README.md" in archive_paths,
        "code_snapshot_included": "code_snapshot" in groups,
        "future_solver_interface_included": (
            "code_snapshot/htt/bass/transfer/native_schema.py" in archive_paths
            and "code_snapshot/htt/bass/transfer/native_adapter.py" in archive_paths
            and "prompts/future_solver_interface_review.md" in archive_paths
        ),
    }


def _read_text_if_exists(repo_root: Path, relative: str) -> str:
    path = repo_root / relative
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _manuscript_blocker_summary(repo_root: Path) -> dict[str, int | str]:
    text = _read_text_if_exists(repo_root, "docs/generated/missing_figure_references.md")
    summary: dict[str, int | str] = {
        "missing_refs": "unknown",
        "quarantined_refs": "unknown",
        "claim_risk_findings": "unknown",
    }
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- Missing refs:"):
            summary["missing_refs"] = int(stripped.rsplit(":", 1)[1].strip())
        elif stripped.startswith("- Quarantined refs:"):
            summary["quarantined_refs"] = int(stripped.rsplit(":", 1)[1].strip())
        elif stripped.startswith("- Claim-risk findings:"):
            summary["claim_risk_findings"] = int(stripped.rsplit(":", 1)[1].strip())
    return summary


def build_audit_package_payload(
    *,
    repo_root: Path | str = REPO_ROOT,
    output_zip: Path = DEFAULT_OUTPUT_ZIP,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    generating_command: str,
    package_entries: Sequence[AuditPackageEntry] = DEFAULT_PACKAGE_ENTRIES,
    worktree_state: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    rows = _entry_rows(root, package_entries)
    input_hashes = [f"{row['source_path']}:{row['sha256']}" for row in rows]
    assertions = _required_assertions(rows)
    failed_gates = [
        name
        for name, passed in assertions.items()
        if not passed
    ]
    config = {
        "schema_version": SCHEMA_VERSION,
        "archive_paths": [row["archive_path"] for row in rows],
        "required_assertions": sorted(assertions),
    }
    config_hash = _stable_hash(config)
    state = worktree_state or _git_state(root)
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "artifact_path": _normalise_output_path(output_zip),
        "manifest_path": _normalise_output_path(output_manifest),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "scripts/build_external_audit_package.py",
        "git_commit": _git_commit(root),
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "code_version": state,
        "schema_version": SCHEMA_VERSION,
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": state,
        "archive_entries": rows,
        "archive_entry_count": len(rows),
        "required_assertions": assertions,
        "required_gates": sorted(assertions),
        "passed_gates": sorted(name for name, passed in assertions.items() if passed),
        "failed_gates": failed_gates,
        "manuscript_blockers": _manuscript_blocker_summary(root),
        "caveats": [
            "External audit package only; not a publication-readiness or solver-validation artifact.",
            "Current transfer-dependent outputs remain transfer-conditional.",
            "MIO certificates are diagnostic reports and remain separate from HTT inference artifacts.",
            "Missing or quarantined manuscript figure references remain blockers.",
            "Future native solver interface material is schema-only unless native validated artifacts are separately manifested.",
        ],
    }
    return payload


def render_readme(payload: dict[str, Any]) -> str:
    blockers = payload["manuscript_blockers"]
    lines = [
        "# HTT External Audit Package",
        "",
        "This archive is a diagnostic external-audit disclosure package for the pre-solver HTT/MIO/BASS framework.",
        "It is not a publication freeze, not native solver validation, and not a geometry or family claim.",
        "",
        "## Required Assertions",
        "",
    ]
    lines.extend(
        f"- {key}: {value}"
        for key, value in sorted(payload["required_assertions"].items())
    )
    lines.extend(
        [
            "",
            "## Manuscript Blockers Preserved",
            "",
            f"- missing_refs: {blockers['missing_refs']}",
            f"- quarantined_refs: {blockers['quarantined_refs']}",
            f"- claim_risk_findings: {blockers['claim_risk_findings']}",
            "",
            "## Reviewer Entry Points",
            "",
            "- `prompts/`: adversarial review prompts.",
            "- `status/`: DAG, status, and claim ledger artifacts.",
            "- `reports/`: Result Packs A/B/C and transfer provenance report.",
            "- `manuscript/`: manuscript figure inventory and blockers.",
            "- `code_snapshot/`: scoped source files for reproducing the audit surfaces.",
            "",
            "## Caveats",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["caveats"])
    lines.append("")
    return "\n".join(lines)


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def render_manifest_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def build_zip_bytes(repo_root: Path, payload: dict[str, Any]) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        manifest_json = render_manifest_json(payload)
        archive.writestr(_zip_info("MANIFEST.json"), manifest_json.encode("utf-8"))
        archive.writestr(_zip_info("README.md"), render_readme(payload).encode("utf-8"))
        for row in sorted(payload["archive_entries"], key=lambda item: item["archive_path"]):
            data = (repo_root / row["source_path"]).read_bytes()
            archive.writestr(_zip_info(row["archive_path"]), data)
    return buffer.getvalue()


def _write_outputs(repo_root: Path, payload: dict[str, Any], output_zip: Path, output_manifest: Path) -> None:
    output_zip_path = output_zip if output_zip.is_absolute() else repo_root / output_zip
    output_manifest_path = (
        output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    )
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    zip_bytes = build_zip_bytes(repo_root, payload)
    output_zip_path.write_bytes(zip_bytes)
    output_manifest_path.write_text(render_manifest_json(payload), encoding="utf-8")


def _check_outputs(repo_root: Path, payload: dict[str, Any], output_zip: Path, output_manifest: Path) -> int:
    output_zip_path = output_zip if output_zip.is_absolute() else repo_root / output_zip
    output_manifest_path = (
        output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    )
    if not output_zip_path.exists() or not output_manifest_path.exists():
        print("missing audit package output")
        return 1
    expected_manifest = render_manifest_json(payload)
    actual_manifest = output_manifest_path.read_text(encoding="utf-8")
    if actual_manifest != expected_manifest:
        print("stale audit package manifest")
        return 1
    expected_zip = build_zip_bytes(repo_root, payload)
    if output_zip_path.read_bytes() != expected_zip:
        print("stale audit package zip")
        return 1
    print(f"up-to-date {output_zip_path}")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-zip", type=Path, default=DEFAULT_OUTPUT_ZIP)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    payload = build_audit_package_payload(
        repo_root=repo_root,
        output_zip=args.output_zip,
        output_manifest=args.output_manifest,
        generating_command=_command_from_args(argv),
    )
    if payload["failed_gates"]:
        print("audit package failed required gates: " + ", ".join(payload["failed_gates"]))
        return 1
    if args.dry_run:
        print("DRY-RUN: not writing external audit package")
        print(f"archive_entry_count={payload['archive_entry_count']}")
        for key, value in sorted(payload["required_assertions"].items()):
            print(f"{key}={value}")
        return 0
    if args.check:
        return _check_outputs(repo_root, payload, args.output_zip, args.output_manifest)
    _write_outputs(repo_root, payload, args.output_zip, args.output_manifest)
    output_zip = args.output_zip if args.output_zip.is_absolute() else repo_root / args.output_zip
    output_manifest = (
        args.output_manifest if args.output_manifest.is_absolute() else repo_root / args.output_manifest
    )
    print(f"wrote {output_zip}")
    print(f"wrote {output_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
