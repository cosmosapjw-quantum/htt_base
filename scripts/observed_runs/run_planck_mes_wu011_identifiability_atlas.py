#!/usr/bin/env python3
"""Generate and verify the synthetic WU-011 Task-7B identifiability atlas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from obsstat.processed_boost_identifiability import (
    Task7BTerminal,
    build_task7b_atlas,
    verify_task7b_artifacts,
    write_task7b_artifacts,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the deterministic WU-011 Task-7B mask, transfer, "
            "conditioning, and extended-source sensitivity atlas."
        )
    )
    parser.add_argument(
        "--source-revision",
        required=True,
        help="Exact 40-hex source commit bound into the atlas receipt.",
    )
    parser.add_argument(
        "--profile",
        default="CI_CORE",
        choices=("SMOKE", "CI_CORE"),
        help="Frozen bounded atlas profile.",
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
    atlas = build_task7b_atlas(
        source_revision=args.source_revision,
        profile=args.profile,
    )
    bundle = write_task7b_artifacts(atlas, args.output)
    verified = verify_task7b_artifacts(bundle.output_dir)
    print(json.dumps(verified, sort_keys=True, indent=2))
    return (
        0
        if atlas.terminal
        in {
            Task7BTerminal.PASS_TASK7B_ATLAS_CANDIDATE_FOUND,
            Task7BTerminal.PASS_TASK7B_ATLAS_NO_CANDIDATE,
        }
        else 2
    )


if __name__ == "__main__":
    sys.exit(main())
