#!/usr/bin/env python3
"""Curate report-facing and quarantined figure lanes.

This script performs mechanical filesystem/provenance cleanup only:

* root-level legacy ``figures/fig_*.png`` files move to
  ``figures/quarantined_legacy/root_sources``;
* conditioned legacy manifests are rewritten to point at the relocated source;
* the v6 no-download meta lane moves under ``figures/quarantined_meta``.

It does not alter figure pixels and does not promote any scientific claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402


FIGURES = REPO_ROOT / "figures"
GEN = REPO_ROOT / "docs" / "generated"

ROOT_LEGACY_DIR = FIGURES / "quarantined_legacy" / "root_sources"
OLD_V6_DIR = FIGURES / "v6_no_download"
META_V6_DIR = FIGURES / "quarantined_meta" / "v6_no_download"
REPORT_JSON = GEN / "figure_lane_curation_report.json"
REPORT_MD = GEN / "figure_lane_curation_report.md"
FIGURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".pdf"}


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _command(argv: list[str] | None) -> str:
    args = sys.argv[1:] if argv is None else argv
    return shlex.join(["python", "scripts/curate_figure_lanes.py", *args])


def _root_figure_paths() -> list[Path]:
    if not FIGURES.exists():
        return []
    return sorted(
        path
        for path in FIGURES.iterdir()
        if path.is_file() and path.suffix.lower() in FIGURE_SUFFIXES
    )


def _move_file(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if src.exists() and _sha256(src) == _sha256(dst):
            src.unlink()
            return "deduplicated_existing_target"
        raise FileExistsError(f"target already exists with different content: {dst}")
    src.rename(dst)
    return "moved"


def _move_root_figures() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for src in _root_figure_paths():
        dst = ROOT_LEGACY_DIR / src.name
        status = _move_file(src, dst)
        rows.append(
            {
                "source_before": _repo_relative(src),
                "source_after": _repo_relative(dst),
                "status": status,
                "sha256": _sha256(dst),
            }
        )
    return rows


def _move_v6_meta_lane() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not OLD_V6_DIR.exists():
        return rows
    META_V6_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(OLD_V6_DIR.iterdir()):
        if not src.is_file():
            continue
        dst = META_V6_DIR / src.name
        status = _move_file(src, dst)
        rows.append(
            {
                "source_before": _repo_relative(src),
                "source_after": _repo_relative(dst),
                "status": status,
                "sha256": _sha256(dst),
            }
        )
    try:
        OLD_V6_DIR.rmdir()
    except OSError:
        pass
    return rows


def _rewrite_root_manifest(path: Path) -> bool:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return False
    stats = payload.get("statistics_definitions")
    if not isinstance(stats, dict):
        return False
    old_source = stats.get("legacy_source_path")
    if not isinstance(old_source, str) or not old_source.startswith("figures/fig_"):
        return False
    new_source = f"figures/quarantined_legacy/root_sources/{Path(old_source).name}"
    stats["legacy_source_path"] = new_source
    old_prefix = f"{old_source}:"
    new_prefix = f"{new_source}:"
    payload["input_hashes"] = [
        new_prefix + row[len(old_prefix) :]
        if isinstance(row, str) and row.startswith(old_prefix)
        else row
        for row in payload.get("input_hashes", [])
    ]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def _rewrite_conditioned_root_manifests() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted((FIGURES / "conditioned_legacy").glob("root__*.manifest.json")):
        changed = _rewrite_root_manifest(path)
        if changed:
            rows.append({"manifest": _repo_relative(path), "status": "rewritten"})
    return rows


def _sidecar_path(figure_path: Path) -> Path:
    return figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json")


def _manifest_for_root_source(figure_path: Path, command: str) -> dict[str, Any]:
    rel_path = _repo_relative(figure_path)
    manifest = {
        "artifact_id": f"common.quarantined_legacy_root_source.{figure_path.stem}",
        "artifact_path": rel_path,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "internal_exploratory",
        "allowed_use": "internal_only",
        "caption_policy": [
            "must_not_use_as_report_figure",
            "must_not_promote_legacy_claim",
        ],
        "promotion_blockers": [
            "legacy_root_source_quarantined",
            "conditioned_legacy_copy_required_for_any_appendix_use",
        ],
        "created_by": "scripts/curate_figure_lanes.py",
        "git_commit": "content-addressed",
        "config_hash": "sha256:"
        + hashlib.sha256(
            json.dumps(
                {
                    "artifact_path": rel_path,
                    "source_hash": _sha256(figure_path),
                    "version": "quarantined-legacy-root-source-v1",
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "input_hashes": [f"{rel_path}:{_sha256(figure_path)}"],
        "code_version": "content-addressed",
        "schema_version": "common.quarantined_legacy_root_source.v1",
        "caveats": [
            "Quarantined legacy root source only.",
            "Not report-facing and not a current result.",
            "Use the conditioned_legacy copy and its manifest for any legacy appendix context.",
        ],
        "required_gates": [
            "legacy_source_quarantined",
            "manifest_metadata_present",
        ],
        "passed_gates": [
            "legacy_source_quarantined",
            "manifest_metadata_present",
        ],
        "failed_gates": [
            "report_lane_not_allowed",
        ],
        "statistics_definitions": {
            "figure_lane": "quarantined_legacy_root_source",
            "conditioned_legacy_copy": (
                f"figures/conditioned_legacy/root__{figure_path.name}"
            ),
        },
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
    }
    issues = validate_manifest_payload(
        manifest,
        manifest_path=_sidecar_path(figure_path),
        expected_artifact_path=rel_path,
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid root-source manifest for {rel_path}: {rendered}")
    return manifest


def _write_root_source_manifests(command: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not ROOT_LEGACY_DIR.exists():
        return rows
    for figure_path in sorted(ROOT_LEGACY_DIR.glob("fig_*.png")):
        sidecar = _sidecar_path(figure_path)
        manifest = _manifest_for_root_source(figure_path, command)
        sidecar.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        rows.append({"manifest": _repo_relative(sidecar), "status": "written"})
    return rows


def build_report(
    command: str,
    *,
    moved_roots: list[dict[str, str]],
    moved_meta: list[dict[str, str]],
    rewritten: list[dict[str, str]],
    root_source_manifests: list[dict[str, str]],
) -> dict[str, Any]:
    root_sources = sorted(ROOT_LEGACY_DIR.glob("fig_*.png")) if ROOT_LEGACY_DIR.exists() else []
    root_source_sidecars = (
        sorted(ROOT_LEGACY_DIR.glob("fig_*.manifest.json"))
        if ROOT_LEGACY_DIR.exists()
        else []
    )
    meta_files = sorted(META_V6_DIR.glob("*")) if META_V6_DIR.exists() else []
    payload = {
        "artifact_id": "common.figure_lane_curation_report",
        "artifact_path": _repo_relative(REPORT_JSON),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "config_hash": "sha256:"
        + hashlib.sha256(
            json.dumps(
                {
                    "root_sources": [_repo_relative(path) for path in root_sources],
                    "meta_files": [_repo_relative(path) for path in meta_files],
                    "rewritten": rewritten,
                "root_source_manifests": root_source_manifests,
                "root_source_sidecars": [
                    _repo_relative(path) for path in root_source_sidecars
                ],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "input_hashes": [
            f"{_repo_relative(path)}:{_sha256(path)}"
            for path in [*root_sources, *root_source_sidecars, *meta_files]
            if path.is_file()
        ],
        "caveats": [
            "Curation report only; it does not promote any figure.",
            "Root legacy figures are retained only as quarantined source material.",
            "V6 no-download meta figures are internal-only and not report-facing.",
        ],
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
        "summary": {
            "root_level_figures_remaining": len(_root_figure_paths()),
            "root_legacy_sources": len(root_sources),
            "v6_meta_files": len(meta_files),
            "root_conditioned_manifests_rewritten": len(rewritten),
            "root_source_manifests": len(root_source_manifests),
        },
        "moved_root_figures": moved_roots,
        "moved_v6_meta_files": moved_meta,
        "rewritten_conditioned_root_manifests": rewritten,
        "root_source_manifests": root_source_manifests,
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Figure Lane Curation Report",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        f"config_hash: `{payload['config_hash']}`",
        "caveats:",
        "- Root legacy figures are quarantined source material, not current results.",
        "- V6 no-download meta figures are isolated as internal-only material.",
        "- Report-facing figures must come from actual data-analysis lanes.",
        f"generating_command: {payload['generating_command']}",
        "git_commit_or_worktree_state: content-addressed",
        "",
        "## Summary",
        "",
        f"- Root-level figures remaining: {summary['root_level_figures_remaining']}",
        f"- Quarantined root legacy sources: {summary['root_legacy_sources']}",
        f"- V6 meta files: {summary['v6_meta_files']}",
        f"- Conditioned root manifests rewritten: {summary['root_conditioned_manifests_rewritten']}",
        f"- Root source manifests: {summary['root_source_manifests']}",
        "",
    ]
    return "\n".join(lines)


def _check_state() -> list[str]:
    failures: list[str] = []
    root_figures = _root_figure_paths()
    if root_figures:
        failures.append(f"root figures remain: {len(root_figures)}")
    if not ROOT_LEGACY_DIR.exists() or len(list(ROOT_LEGACY_DIR.glob("fig_*.png"))) < 70:
        failures.append("root legacy source directory is incomplete")
    if not ROOT_LEGACY_DIR.exists() or len(list(ROOT_LEGACY_DIR.glob("fig_*.manifest.json"))) < 70:
        failures.append("root legacy source manifests are incomplete")
    if OLD_V6_DIR.exists():
        failures.append("old figures/v6_no_download directory still exists")
    if not META_V6_DIR.exists() or len(list(META_V6_DIR.glob("fig_v6_*.png"))) != 5:
        failures.append("quarantined v6 meta lane is incomplete")
    for path in sorted((FIGURES / "conditioned_legacy").glob("root__*.manifest.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        source = payload.get("statistics_definitions", {}).get("legacy_source_path")
        if not isinstance(source, str) or not source.startswith(
            "figures/quarantined_legacy/root_sources/"
        ):
            failures.append(f"manifest still points at old root source: {_repo_relative(path)}")
            break
        if not (REPO_ROOT / source).is_file():
            failures.append(f"manifest source missing: {source}")
            break
    if ROOT_LEGACY_DIR.exists():
        for figure_path in sorted(ROOT_LEGACY_DIR.glob("fig_*.png")):
            sidecar = _sidecar_path(figure_path)
            if not sidecar.is_file():
                failures.append(f"root source manifest missing: {_repo_relative(sidecar)}")
                break
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            issues = validate_manifest_payload(
                payload,
                manifest_path=sidecar,
                expected_artifact_path=_repo_relative(figure_path),
            )
            if issues:
                failures.append(f"root source manifest invalid: {_repo_relative(sidecar)}")
                break
    return failures


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        failures = _check_state()
        if failures:
            print("figure lane curation is stale:", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
        print("figure lane curation is current")
        return 0

    command = _command([])
    moved_roots = _move_root_figures()
    moved_meta = _move_v6_meta_lane()
    rewritten = _rewrite_conditioned_root_manifests()
    root_source_manifests = _write_root_source_manifests(command)
    GEN.mkdir(parents=True, exist_ok=True)
    report = build_report(
        command,
        moved_roots=moved_roots,
        moved_meta=moved_meta,
        rewritten=rewritten,
        root_source_manifests=root_source_manifests,
    )
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {_repo_relative(REPORT_JSON)}")
    print(f"wrote {_repo_relative(REPORT_MD)}")
    print(f"root figures moved: {len(moved_roots)}")
    print(f"v6 meta files moved: {len(moved_meta)}")
    print(f"root manifests rewritten: {len(rewritten)}")
    print(f"root source manifests written: {len(root_source_manifests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
