#!/usr/bin/env python3
"""Install this bundle as a non-destructive overlay in a local htt_base checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = "external_fusion_round3"
EXCLUDE_TOP = {".pytest_cache", ".venv", "__pycache__"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def selected_files(include_context: bool) -> list[Path]:
    out: list[Path] = []
    for p in BUNDLE.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(BUNDLE)
        if any(part in EXCLUDE_TOP for part in rel.parts):
            continue
        if rel.name.endswith((".pyc", ".pyo")):
            continue
        if not include_context and rel.parts and rel.parts[0] == "context":
            continue
        out.append(p)
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Path to the local htt_base checkout")
    ap.add_argument("--target-name", default=DEFAULT_TARGET)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true", help="Replace an existing target directory")
    ap.add_argument("--include-context", action="store_true")
    args = ap.parse_args()
    if args.dry_run == args.apply:
        raise SystemExit("choose exactly one of --dry-run or --apply")

    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        raise SystemExit(f"repo does not exist: {repo}")
    # Fail closed against an arbitrary output path while permitting minimal test repos.
    indicators = [repo / ".git", repo / "pyproject.toml", repo / "Makefile", repo / "htt"]
    if not any(x.exists() for x in indicators):
        raise SystemExit("target does not resemble a repository checkout")

    target = repo / args.target_name
    files = selected_files(args.include_context)
    collision = target.exists()
    report = {
        "schema": "htt.external_fusion_overlay_plan.v1",
        "bundle": str(BUNDLE),
        "repo": str(repo),
        "target": str(target),
        "file_count": len(files),
        "bytes": sum(p.stat().st_size for p in files),
        "include_context": args.include_context,
        "target_exists": collision,
        "action": "dry-run" if args.dry_run else "apply",
    }
    if args.dry_run:
        report["first_files"] = [str(p.relative_to(BUNDLE)) for p in files[:20]]
        print(json.dumps(report, indent=2))
        return 0 if not collision else 3

    if collision:
        if not args.force:
            raise SystemExit("target exists; rerun with --force only after reviewing the existing overlay")
        shutil.rmtree(target)
    for src in files:
        rel = src.relative_to(BUNDLE)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    receipt_files = []
    for src in files:
        rel = src.relative_to(BUNDLE)
        dst = target / rel
        receipt_files.append({"path": rel.as_posix(), "sha256": sha256(dst), "bytes": dst.stat().st_size})
    receipt = {**report, "installed_files": receipt_files}
    (target / "OVERLAY_INSTALL_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({**report, "status": "INSTALLED", "receipt": str(target / "OVERLAY_INSTALL_RECEIPT.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
