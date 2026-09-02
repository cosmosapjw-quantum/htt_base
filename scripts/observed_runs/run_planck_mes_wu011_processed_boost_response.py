#!/usr/bin/env python3
"""Generate and verify the synthetic WU-011 Task-7A evidence package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from obsstat.processed_boost_evidence import (
    Task7ATerminal,
    build_task7a_evidence,
    verify_task7a_artifacts,
    write_task7a_artifacts,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic WU-011 Task-7A synthetic evidence."
    )
    parser.add_argument(
        "--source-revision",
        required=True,
        help="Exact 40-hex source commit bound into the receipt.",
    )
    parser.add_argument(
        "--profile",
        default="CI_CORE",
        choices=("CI_CORE",),
        help="Frozen bounded evidence profile.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Absent or empty output directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    report = build_task7a_evidence(
        source_revision=args.source_revision,
        profile=args.profile,
    )
    bundle = write_task7a_artifacts(report, args.output)
    verified = verify_task7a_artifacts(bundle.output_dir)
    print(json.dumps(verified, sort_keys=True, indent=2))
    return (
        0
        if report.terminal is Task7ATerminal.PASS_TASK7A_CORE_EVIDENCE
        else 2
    )


if __name__ == "__main__":
    sys.exit(main())
