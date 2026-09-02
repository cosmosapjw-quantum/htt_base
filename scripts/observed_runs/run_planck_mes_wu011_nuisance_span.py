#!/usr/bin/env python3
"""Run the deterministic PMG-WU-011 Task-7C nuisance-span atlas."""

from __future__ import annotations

import argparse
from pathlib import Path

from obsstat.processed_boost_nuisance_span import (
    build_task7c_atlas,
    verify_task7c_artifacts,
    write_task7c_artifacts,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--profile", choices=("SMOKE", "CI_CORE"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    atlas = build_task7c_atlas(
        source_revision=args.source_revision,
        profile=args.profile,
    )
    bundle = write_task7c_artifacts(atlas, args.output)
    verified = verify_task7c_artifacts(args.output)
    if verified["terminal"] != atlas.terminal.value:
        raise RuntimeError("Task-7C terminal changed during artifact verification")
    if verified["atlas_content_id"] != atlas.content_id:
        raise RuntimeError("Task-7C content identity changed during verification")
    if verified["manifest_sha256"] != bundle.manifest_sha256:
        raise RuntimeError("Task-7C manifest identity changed during verification")
    print("TASK7C_TERMINAL", atlas.terminal.value)
    print("TASK7C_CONTENT_ID", atlas.content_id)
    print("TASK7C_MANIFEST_SHA256", bundle.manifest_sha256)
    print("TASK7C_SOURCE_BLOCK_BUILD_COUNT", atlas.source_block_build_count)
    print("TASK7C_PROFILE", atlas.profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
