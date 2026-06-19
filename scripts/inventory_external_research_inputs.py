#!/usr/bin/env python3
"""Inventory newly uploaded external research audit/proposal inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/audits/external_research_inputs_2026-06-20"
ARCHIVE_MANIFEST = OUT_DIR / "ARCHIVE_MANIFEST.md"
INVENTORY_JSON = OUT_DIR / "input_inventory.json"
INVENTORY_MD = OUT_DIR / "input_inventory.md"
RESPONSE_MATRIX = ROOT / "docs/generated/external_research_input_response_matrix.md"

INPUTS = (
    "RESEARCH_AUDIT_REPORT.md",
    "publishable_data_analysis_program.zip",
    "htt_publishable_novel_analysis_program_2026-06-19.zip",
    "htt_beyond_mes_egs_theorem_program_2026-06-19.zip",
    "egs_theorem_program.zip",
)

CANONICAL_SOURCES = {
    "manuscript_audit": "RESEARCH_AUDIT_REPORT.md",
    "data_analysis_program": "htt_publishable_novel_analysis_program_2026-06-19.zip",
    "theorem_program": "htt_beyond_mes_egs_theorem_program_2026-06-19.zip",
}

SOURCE_DETAILS = {
    "RESEARCH_AUDIT_REPORT.md": {
        "source_role": "external_current_manuscript_audit",
        "selected_documents": ["RESEARCH_AUDIT_REPORT.md"],
        "supersession_note": "canonical immediate manuscript-audit input for REV-R075",
    },
    "publishable_data_analysis_program.zip": {
        "source_role": "external_compact_data_analysis_precursor",
        "selected_documents": [
            "00_STRATEGY_AND_PIPELINE.md",
            "04_THEOREM_CANDIDATES.md",
            "07_AXIS_C_data.md",
            "08_PRIOR_ART_CRAG.md",
        ],
        "supersession_note": (
            "precursor cross-check; superseded for implementation by "
            "htt_publishable_novel_analysis_program_2026-06-19.zip"
        ),
    },
    "htt_publishable_novel_analysis_program_2026-06-19.zip": {
        "source_role": "external_canonical_data_analysis_program",
        "selected_documents": [
            "docs/00_executive_strategy.md",
            "docs/03_flagship_joint_rest_frame_analysis.md",
            "docs/04_theorem_candidates_and_proofs.md",
            "docs/06_data_null_and_validation_requirements.md",
            "machine_readable/pr_dag.yaml",
            "machine_readable/experiment_registry.yaml",
            "machine_readable/theorem_registry.yaml",
        ],
        "supersession_note": "canonical joint rest-frame/data-analysis proposal input",
    },
    "htt_beyond_mes_egs_theorem_program_2026-06-19.zip": {
        "source_role": "external_canonical_theorem_extension_program",
        "selected_documents": [
            "docs/02_math_statistics_axis.md",
            "docs/03_gr_cosmology_axis.md",
            "docs/04_boltzmann_kinetic_axis.md",
            "docs/05_egs_synthesis_and_data_axis.md",
            "docs/07_proof_obligations_and_kill_switches.md",
            "docs/15_theorem_dependency_and_promotion_dag.md",
        ],
        "supersession_note": "canonical beyond-MES/EGS theorem-extension proposal input",
    },
    "egs_theorem_program.zip": {
        "source_role": "external_compact_egs_theorem_precursor",
        "selected_documents": [
            "00_STRATEGY_AND_PIPELINE.md",
            "04_THEOREM_CANDIDATES.md",
            "08_PRIOR_ART_CRAG.md",
        ],
        "supersession_note": (
            "precursor cross-check; superseded for implementation by "
            "htt_beyond_mes_egs_theorem_program_2026-06-19.zip"
        ),
    },
}

CAVEATS = (
    "diagnostic/proposed inputs",
    "not publication evidence",
    "no native low-ell solver output or validation is present",
    "no Bianchi family identification",
    "no geometry-detection wording or evidence promotion",
)

RESPONSE_ACTIONS = (
    {
        "priority": "P0",
        "action": "audit minor revisions",
        "source": "RESEARCH_AUDIT_REPORT.md",
        "owner": "COMMON/manuscript",
        "next_step": (
            "Track the minor-revision items as bounded repo deltas: prose downgrades, "
            "cross-chapter numeric reconciliation, and Pi/Q/F terminology cleanup."
        ),
        "kill_switch": (
            "Stop promotion if a requested edit needs native solver validation, "
            "geometry-detection wording, or Bianchi family identification."
        ),
    },
    {
        "priority": "P0",
        "action": "formalism harmonization",
        "source": "RESEARCH_AUDIT_REPORT.md; publishable_data_analysis_program.zip",
        "owner": "COMMON/MIO/HTT",
        "next_step": (
            "Reserve MIO Pi/Q/F language for diagnostic exceedance and filling reports, "
            "and keep HTT posterior semantics separate in manuscript-facing text."
        ),
        "kill_switch": (
            "Block any row that merges MIO diagnostics with HTT evidence terms or "
            "turns a diagnostic score into a truth claim."
        ),
    },
    {
        "priority": "P0",
        "action": "CF4++ traceability",
        "source": "RESEARCH_AUDIT_REPORT.md; htt_publishable_novel_analysis_program_2026-06-19.zip",
        "owner": "obsstat/HTT",
        "next_step": (
            "Bind any CF4++ number to canonical input hashes, config hashes, and a "
            "rerunnable command before it appears in a result table."
        ),
        "kill_switch": (
            "Remove the number from result prose if canonical inputs cannot reproduce it."
        ),
    },
    {
        "priority": "P1",
        "action": "local/global joint rest-frame program",
        "source": "htt_publishable_novel_analysis_program_2026-06-19.zip",
        "owner": "HTT/obsstat",
        "next_step": (
            "Map the joint rest-frame proposal onto the existing local/global "
            "candidate lane with observer-frame caveats and transfer provenance."
        ),
        "kill_switch": (
            "Keep it in forecast/candidate status until matched nulls, covariance, "
            "and observer-motion marginalization exist."
        ),
    },
    {
        "priority": "P1",
        "action": "finite mock/rank/Fisher/null/PPC plan",
        "source": "htt_publishable_novel_analysis_program_2026-06-19.zip; publishable_data_analysis_program.zip",
        "owner": "HTT/obsstat",
        "next_step": (
            "Stage finite mock calibration, response-rank checks, Fisher diagnostics, "
            "matched nulls, and PPC/LOOCV gates before stronger inference wording."
        ),
        "kill_switch": (
            "Do not promote a likelihood or local/global statement when any rank, "
            "null, covariance, PPC, or LOOCV gate is missing."
        ),
    },
    {
        "priority": "P0",
        "action": "theorem program P0",
        "source": "htt_beyond_mes_egs_theorem_program_2026-06-19.zip; egs_theorem_program.zip",
        "owner": "COMMON/physics_audit",
        "next_step": (
            "Extract theorem statements, assumptions, units, frame conventions, and "
            "proof obligations into a repo-local audit table."
        ),
        "kill_switch": (
            "Abort promotion when assumptions depend on unavailable native transfer, "
            "unstated regularity, or hidden observer-frame choices."
        ),
    },
    {
        "priority": "P1",
        "action": "theorem program P1",
        "source": "htt_beyond_mes_egs_theorem_program_2026-06-19.zip",
        "owner": "physics_audit/obsstat",
        "next_step": (
            "Convert surviving theorem obligations into synthetic or analytic tests "
            "that exercise signs, limits, denominators, and finite-cover behavior."
        ),
        "kill_switch": (
            "Keep theorem artifacts proposed-only if tests are toy-only or lack "
            "dimension/frame coverage."
        ),
    },
    {
        "priority": "P2",
        "action": "theorem program P2",
        "source": "htt_beyond_mes_egs_theorem_program_2026-06-19.zip",
        "owner": "manuscript/COMMON",
        "next_step": (
            "Only after P0/P1 closure, draft manuscript-safe theorem wording with "
            "explicit claim tier and caveat boxes."
        ),
        "kill_switch": (
            "Do not move proposed theorem text into publication-facing claims without "
            "independent proof review and validation evidence."
        ),
    },
)


def _repo_relative(path: Path) -> str:
    if path.is_relative_to(ROOT):
        return path.relative_to(ROOT).as_posix()
    return path.as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _zip_summary(path: Path) -> dict[str, object]:
    with ZipFile(path) as archive:
        names = sorted(info.filename for info in archive.infolist())

    top_level: dict[str, dict[str, int]] = {}
    for name in names:
        stripped = name.strip("/")
        if not stripped:
            continue
        top = stripped.split("/", 1)[0]
        summary = top_level.setdefault(
            top,
            {
                "entry_count": 0,
                "file_entry_count": 0,
                "directory_entry_count": 0,
                "max_depth": 0,
            },
        )
        summary["entry_count"] += 1
        if name.endswith("/"):
            summary["directory_entry_count"] += 1
        else:
            summary["file_entry_count"] += 1
        summary["max_depth"] = max(summary["max_depth"], len(stripped.split("/")))

    return {
        "entry_count": len(names),
        "file_entry_count": sum(not name.endswith("/") for name in names),
        "directory_entry_count": sum(name.endswith("/") for name in names),
        "top_level_summary": [
            {"name": name, **top_level[name]} for name in sorted(top_level)
        ],
        "entries": names,
    }


def _input_record(name: str) -> dict[str, object]:
    source = ROOT / name
    if not source.exists():
        raise FileNotFoundError(source)
    archive_path = OUT_DIR / name
    details = SOURCE_DETAILS[name]
    record = {
        "name": name,
        "source_path": name,
        "archive_path": _repo_relative(archive_path),
        "source_role": details["source_role"],
        "selected_documents": details["selected_documents"],
        "supersession_note": details["supersession_note"],
        "external_input_status": "raw_external_input_hash_preserved",
        "content_type": "zip" if name.endswith(".zip") else "markdown",
        "sha256": sha256(source),
        "size_bytes": source.stat().st_size,
        "zip": _zip_summary(source) if name.endswith(".zip") else None,
    }
    return record


def _config_hash() -> str:
    return _stable_hash(
        {
            "schema_version": "htt.external_research_input_inventory.v1",
            "inputs": INPUTS,
            "outputs": (
                _repo_relative(ARCHIVE_MANIFEST),
                _repo_relative(INVENTORY_JSON),
                _repo_relative(INVENTORY_MD),
                _repo_relative(RESPONSE_MATRIX),
            ),
            "canonical_sources": CANONICAL_SOURCES,
            "caveats": CAVEATS,
            "response_actions": RESPONSE_ACTIONS,
        }
    )


def build_payload() -> dict[str, object]:
    inputs = [_input_record(name) for name in INPUTS]
    return {
        "schema_version": "htt.external_research_input_inventory.v1",
        "owner": "COMMON",
        "implementation_scope": "external_research_input_intake",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "archive_directory": _repo_relative(OUT_DIR),
        "archive_manifest": _repo_relative(ARCHIVE_MANIFEST),
        "canonical_sources": dict(CANONICAL_SOURCES),
        "config_hash": _config_hash(),
        "input_hashes": [
            {"name": item["name"], "sha256": item["sha256"]} for item in inputs
        ],
        "generating_command": "venv/bin/python scripts/inventory_external_research_inputs.py --write",
        "git_commit_or_worktree_state": (
            "working-tree input snapshot hash-bound; uploaded root inputs were "
            "untracked at intake"
        ),
        "archive_copy_policy": (
            "write mode copies each root input into the archive directory when "
            "missing or hash-stale; check mode fails on missing or hash-stale copies"
        ),
        "inputs": inputs,
        "response_actions": list(RESPONSE_ACTIONS),
        "caveats": list(CAVEATS),
    }


def json_text(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KiB"
    return f"{size_bytes / (1024 * 1024):.1f} MiB"


def _format_top_level(zip_payload: object) -> str:
    if not isinstance(zip_payload, dict):
        return "n/a"
    rows = zip_payload["top_level_summary"]
    assert isinstance(rows, list)
    parts = []
    for row in rows[:8]:
        assert isinstance(row, dict)
        parts.append(
            f"{row['name']} ({row['file_entry_count']} files, {row['directory_entry_count']} dirs)"
        )
    if len(rows) > 8:
        parts.append(f"... {len(rows) - 8} more")
    return "; ".join(parts)


def render_inventory_markdown(payload: dict[str, object]) -> str:
    inputs = payload["inputs"]
    caveats = payload["caveats"]
    canonical_sources = payload["canonical_sources"]
    assert isinstance(inputs, list)
    assert isinstance(caveats, list)
    assert isinstance(canonical_sources, dict)

    lines = [
        "# External Research Input Inventory",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        f"transfer_source: {payload['transfer_source']}",
        f"config_hash: {payload['config_hash']}",
        f"sky_support_status: {payload['sky_support_status']}",
        f"null_mock_status: {payload['null_mock_status']}",
        f"archive_directory: `{payload['archive_directory']}`",
        f"archive_manifest: `{payload['archive_manifest']}`",
        f"generating_command: `{payload['generating_command']}`",
        f"git_commit_or_worktree_state: {payload['git_commit_or_worktree_state']}",
        "",
        "## External-Input Status",
        "",
        "Files copied into this directory are raw external audit/proposal inputs. "
        "They are hash-preserved for traceability and are not repo-authored "
        "current research claims, validation artifacts, publication evidence, "
        "or native-solver outputs.",
        "",
        "## Canonical Sources",
        "",
        "| Lane | Canonical input |",
        "| --- | --- |",
    ]
    for lane, source in canonical_sources.items():
        lines.append(f"| `{lane}` | `{source}` |")

    lines.extend(
        [
            "",
        "## Inputs",
        "",
            "| Input | Role | SHA256 | Size | Archive copy | Zip entries | Supersession | Top-level summary |",
            "| --- | --- | --- | ---: | --- | ---: | --- | --- |",
        ]
    )
    for item in inputs:
        assert isinstance(item, dict)
        zip_payload = item["zip"]
        zip_entries = zip_payload["entry_count"] if isinstance(zip_payload, dict) else "n/a"
        lines.append(
            f"| `{item['name']}` | `{item['source_role']}` | `{item['sha256']}` | "
            f"{_format_size(int(item['size_bytes']))} | `{item['archive_path']}` | "
            f"{zip_entries} | {item['supersession_note']} | {_format_top_level(zip_payload)} |"
        )

    lines.extend(["", "## Selected Documents", ""])
    for item in inputs:
        assert isinstance(item, dict)
        lines.append(f"### `{item['name']}`")
        selected_documents = item["selected_documents"]
        assert isinstance(selected_documents, list)
        for selected in selected_documents:
            lines.append(f"- `{selected}`")
        lines.append("")

    lines.extend(["", "## Input Hash List", ""])
    for item in inputs:
        assert isinstance(item, dict)
        lines.append(f"- `{item['name']}`: `{item['sha256']}`")

    lines.extend(["", "## Caveats", ""])
    for caveat in caveats:
        lines.append(f"- {caveat}")
    lines.append("")
    return "\n".join(lines)


def render_archive_manifest(payload: dict[str, object]) -> str:
    inputs = payload["inputs"]
    caveats = payload["caveats"]
    assert isinstance(inputs, list)
    assert isinstance(caveats, list)
    lines = [
        "# External Research Input Archive Manifest",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        f"transfer_source: {payload['transfer_source']}",
        f"config_hash: {payload['config_hash']}",
        f"generating_command: `{payload['generating_command']}`",
        "",
        "## Boundary",
        "",
        "This folder contains raw external audit/proposal inputs copied from the "
        "repository root for traceability. Raw Markdown and ZIP files in this "
        "archive are external-input evidence only. They are not repo-authored "
        "current research claims, validation artifacts, publication evidence, "
        "native-transfer outputs, or family-identification support.",
        "",
        "## Files",
        "",
        "| File | External role | SHA256 | Status |",
        "| --- | --- | --- | --- |",
    ]
    for item in inputs:
        assert isinstance(item, dict)
        lines.append(
            f"| `{item['archive_path']}` | `{item['source_role']}` | "
            f"`{item['sha256']}` | `{item['external_input_status']}` |"
        )
    lines.extend(["", "## Caveats", ""])
    for caveat in caveats:
        lines.append(f"- {caveat}")
    lines.append("")
    return "\n".join(lines)


def render_response_matrix(payload: dict[str, object]) -> str:
    actions = payload["response_actions"]
    caveats = payload["caveats"]
    assert isinstance(actions, list)
    assert isinstance(caveats, list)

    lines = [
        "# External Research Input Response Matrix",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        f"transfer_source: {payload['transfer_source']}",
        f"config_hash: {payload['config_hash']}",
        f"input_inventory: `{_repo_relative(INVENTORY_JSON)}`",
        f"sky_support_status: {payload['sky_support_status']}",
        f"null_mock_status: {payload['null_mock_status']}",
        f"generating_command: `{payload['generating_command']}`",
        f"archive_manifest: `{_repo_relative(ARCHIVE_MANIFEST)}`",
        "",
        "## Prioritized Actions",
        "",
        "| Priority | Action | Source inputs | Owner | Next step | kill-switches |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for action in actions:
        assert isinstance(action, dict)
        lines.append(
            f"| {action['priority']} | {action['action']} | `{action['source']}` | "
            f"{action['owner']} | {action['next_step']} | {action['kill_switch']} |"
        )

    lines.extend(
        [
            "",
            "## Intake Boundary",
            "",
            "These rows convert uploaded audit/proposal material into repo-local work items. "
            "They do not promote any result, theorem, transfer output, or manuscript number.",
            "",
            "## Caveats",
            "",
        ]
    )
    for caveat in caveats:
        lines.append(f"- {caveat}")
    lines.append("")
    return "\n".join(lines)


def _assert_archive_destination(path: Path) -> None:
    out_resolved = OUT_DIR.resolve()
    parent_resolved = path.parent.resolve()
    if parent_resolved != out_resolved and not parent_resolved.is_relative_to(out_resolved):
        raise RuntimeError(f"archive destination escapes output directory: {path}")
    if path.is_symlink():
        raise RuntimeError(f"archive destination is a symlink: {path}")
    if path.exists() and not path.is_file():
        raise RuntimeError(f"archive destination is not a regular file: {path}")


def _copy_inputs(payload: dict[str, object]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = payload["inputs"]
    assert isinstance(inputs, list)
    for item in inputs:
        assert isinstance(item, dict)
        source = ROOT / str(item["source_path"])
        archived = ROOT / str(item["archive_path"])
        _assert_archive_destination(archived)
        if not archived.exists() or sha256(archived) != item["sha256"]:
            tmp = archived.with_name(f".{archived.name}.tmp")
            _assert_archive_destination(tmp)
            if tmp.exists():
                tmp.unlink()
            shutil.copy2(source, tmp)
            os.replace(tmp, archived)


def write_outputs(payload: dict[str, object]) -> None:
    _copy_inputs(payload)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSE_MATRIX.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_MANIFEST.write_text(render_archive_manifest(payload), encoding="utf-8")
    INVENTORY_JSON.write_text(json_text(payload), encoding="utf-8")
    INVENTORY_MD.write_text(render_inventory_markdown(payload), encoding="utf-8")
    RESPONSE_MATRIX.write_text(render_response_matrix(payload), encoding="utf-8")


def _archive_copy_issues(payload: dict[str, object]) -> list[str]:
    issues: list[str] = []
    inputs = payload["inputs"]
    assert isinstance(inputs, list)
    for item in inputs:
        assert isinstance(item, dict)
        archived = ROOT / str(item["archive_path"])
        if archived.is_symlink():
            issues.append(f"symlink archive copy is forbidden: {_repo_relative(archived)}")
            continue
        if not archived.exists():
            issues.append(f"missing archive copy: {_repo_relative(archived)}")
            continue
        actual_sha = sha256(archived)
        if actual_sha != item["sha256"]:
            issues.append(
                f"stale archive copy: {_repo_relative(archived)} "
                f"expected {item['sha256']} got {actual_sha}"
            )
    return issues


def check_outputs(payload: dict[str, object]) -> int:
    missing = [
        _repo_relative(path)
        for path in (ARCHIVE_MANIFEST, INVENTORY_JSON, INVENTORY_MD, RESPONSE_MATRIX)
        if not path.exists()
    ]
    issues = _archive_copy_issues(payload)
    if missing:
        issues.append("missing generated files: " + ", ".join(missing))

    if not missing:
        expected = {
            ARCHIVE_MANIFEST: render_archive_manifest(payload),
            INVENTORY_JSON: json_text(payload),
            INVENTORY_MD: render_inventory_markdown(payload),
            RESPONSE_MATRIX: render_response_matrix(payload),
        }
        stale = [
            _repo_relative(path)
            for path, text in expected.items()
            if path.read_text(encoding="utf-8") != text
        ]
        if stale:
            issues.append("stale generated files: " + ", ".join(stale))

    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        print(
            "run: venv/bin/python scripts/inventory_external_research_inputs.py --write",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write inventory and response matrix")
    mode.add_argument("--check", action="store_true", help="verify generated outputs are current")
    args = parser.parse_args(argv)

    try:
        payload = build_payload()
    except (FileNotFoundError, OSError) as exc:
        print(f"inventory failed: {exc}", file=sys.stderr)
        return 1

    if args.write:
        write_outputs(payload)
        return 0
    if args.check:
        return check_outputs(payload)

    print(json_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
