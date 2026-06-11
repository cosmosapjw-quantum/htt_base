#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HTT_ROOT = REPO_ROOT / "htt"
COMMON_ROOT = HTT_ROOT / "src"
for root in (COMMON_ROOT, HTT_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from common.artifact_manifest import (  # noqa: E402
    DEFAULT_SCAN_ROOTS,
    build_quarantine_report,
    render_quarantine_markdown,
)


DEFAULT_OUTPUT = REPO_ROOT / "docs" / "generated" / "quarantined_figures.md"


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _command_from_args(argv: list[str] | None) -> str:
    command_args = sys.argv[1:] if argv is None else argv
    return shlex.join(["python", "scripts/check_artifact_manifests.py", *command_args])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate artifact manifest sidecars and quarantine unmanifested figures."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="repository root to scan",
    )
    parser.add_argument(
        "--scan-root",
        action="append",
        dest="scan_roots",
        help="repo-relative file or directory to scan; may be repeated",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown quarantine report path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the report without writing it",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    scan_roots = tuple(args.scan_roots or DEFAULT_SCAN_ROOTS)
    output = args.output if args.output.is_absolute() else repo_root / args.output
    command = _command_from_args(argv)

    report = build_quarantine_report(repo_root, scan_roots=scan_roots)
    rendered = render_quarantine_markdown(
        report,
        repo_root=repo_root,
        output_path=output,
        generating_command=command,
    )

    if args.dry_run:
        print(
            "COMMON artifact manifest quarantine -> "
            f"{_repo_relative(output, repo_root)}"
        )
        print(rendered)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"wrote {_repo_relative(output, repo_root)}")

    return 1 if report.manifest_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
