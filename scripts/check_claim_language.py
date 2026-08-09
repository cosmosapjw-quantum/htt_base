#!/usr/bin/env python3
"""Check repository text for forbidden production claim language."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_SRC = REPO_ROOT / "htt" / "src"
if str(COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(COMMON_SRC))

from common.semantic_guards.no_overclaim import (  # noqa: E402
    issue_to_dict,
    render_issues,
    scan_paths,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail on forbidden HTT/MIO/BASS claim language."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("docs"), Path("manuscripts")],
        help="Files or directories to scan. Missing paths are reported and skipped.",
    )
    parser.add_argument(
        "--strict-missing",
        action="store_true",
        help="Return usage error before scanning when any requested path is missing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report without writing files. Forbidden production claims still fail.",
    )
    parser.add_argument(
        "--include-archives",
        action="store_true",
        help="Also scan archived/generated/provenance document trees.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for scan results.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    existing: list[Path] = []
    missing: list[Path] = []
    for path in args.paths:
        (existing if path.exists() else missing).append(path)
    if missing and args.strict_missing:
        print(
            "strict missing-path check failed: "
            + ", ".join(str(path) for path in missing),
            file=sys.stderr,
        )
        return 2
    for path in missing:
        print(f"skipped missing path: {path}", file=sys.stderr)
    if not existing:
        print("No existing paths to scan.", file=sys.stderr)
        return 2
    issues = scan_paths(existing, include_archives=args.include_archives)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "issue_count": len(issues),
                    "issues": [issue_to_dict(issue) for issue in issues],
                    "missing_paths": [str(path) for path in missing],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render_issues(issues))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
