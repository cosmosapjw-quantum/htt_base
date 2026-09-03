#!/usr/bin/env python3
"""Run the deterministic PMG-WU-011 Task-7C nuisance-span atlas."""

from __future__ import annotations

import argparse
from pathlib import Path

from obsstat.processed_boost_matched_control import (
    build_matched_fullsky_control,
    verify_matched_control_receipt,
    write_matched_control_receipt,
)
from obsstat.processed_boost_matched_control_artifacts import (
    verify_matched_control_adjudication_artifacts,
    write_matched_control_adjudication_artifacts,
)
from obsstat.processed_boost_nuisance_span import (
    build_task7c_atlas,
    task7c_case_specs,
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

    primary_spec = task7c_case_specs(args.profile)[0]
    primary_case = atlas.cases[0]
    if primary_case.case_id != primary_spec.case_id:
        raise RuntimeError("Task-7C primary case differs from the matched-control source")
    matched_control = build_matched_fullsky_control(primary_spec)
    matched_target = args.output / "matched_control"
    matched_bundle = write_matched_control_receipt(
        primary_case,
        matched_control,
        matched_target,
        source_revision=args.source_revision,
    )
    matched_verified = verify_matched_control_receipt(matched_target)
    if matched_verified["source_revision"] != args.source_revision:
        raise RuntimeError("Task-7C matched-control source revision differs")
    if (
        matched_verified["receipt_content_id"]
        != matched_bundle["receipt_content_id"]
    ):
        raise RuntimeError("Task-7C matched-control content identity differs")
    if matched_verified["manifest_sha256"] != matched_bundle["manifest_sha256"]:
        raise RuntimeError("Task-7C matched-control manifest identity differs")

    adjudication_target = matched_target / "adjudication"
    adjudication_bundle = write_matched_control_adjudication_artifacts(
        rank_sensitivity_csv=matched_target / "rank_sensitivity.csv",
        matrices_npz=args.output / "matrices.npz",
        target=adjudication_target,
        nominal_control_factor=5.0,
    )
    adjudication_verified = verify_matched_control_adjudication_artifacts(
        adjudication_target
    )
    if adjudication_verified["terminal"] != adjudication_bundle["terminal"]:
        raise RuntimeError("Task-7C matched-control adjudication terminal differs")
    if adjudication_verified["content_id"] != adjudication_bundle["content_id"]:
        raise RuntimeError("Task-7C matched-control adjudication identity differs")
    if (
        adjudication_verified["manifest_sha256"]
        != adjudication_bundle["manifest_sha256"]
    ):
        raise RuntimeError("Task-7C matched-control adjudication manifest differs")

    print("TASK7C_TERMINAL", atlas.terminal.value)
    print("TASK7C_CONTENT_ID", atlas.content_id)
    print("TASK7C_MANIFEST_SHA256", bundle.manifest_sha256)
    print("TASK7C_SOURCE_BLOCK_BUILD_COUNT", atlas.source_block_build_count)
    print("TASK7C_PROFILE", atlas.profile)
    print("TASK7C_MATCHED_CONTROL_STATUS", matched_verified["status"])
    print("TASK7C_MATCHED_CONTROL_CONTENT_ID", matched_verified["receipt_content_id"])
    print("TASK7C_MATCHED_CONTROL_MANIFEST_SHA256", matched_verified["manifest_sha256"])
    print("TASK7C_MATCHED_CONTROL_ANALYSIS_COUNT", matched_verified["analysis_count"])
    print(
        "TASK7C_MATCHED_CONTROL_ADJUDICATION_TERMINAL",
        adjudication_verified["terminal"],
    )
    print(
        "TASK7C_MATCHED_CONTROL_ADJUDICATION_CONTENT_ID",
        adjudication_verified["content_id"],
    )
    print(
        "TASK7C_MATCHED_CONTROL_ADJUDICATION_MANIFEST_SHA256",
        adjudication_verified["manifest_sha256"],
    )
    print(
        "TASK7C_MATCHED_CONTROL_NOMINAL_AMBIGUOUS_COUNT",
        adjudication_verified["nominal_ambiguous_count"],
    )
    print(
        "TASK7C_MATCHED_CONTROL_NOMINAL_RESOLVED_COUNT",
        adjudication_verified["nominal_resolved_count"],
    )
    print(
        "TASK7C_MATCHED_CONTROL_BEST_SATURATION_MARGIN",
        adjudication_verified["best_saturation_margin"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
