#!/usr/bin/env python3
"""Prepare, finalize, or verify PMG-WU-005 map-free recovery evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
for candidate in (ROOT, ROOT / "htt", ROOT / "htt/src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from obsstat.planck_paired300_recovery import (  # noqa: E402
    finalize_recovery_evidence,
    install_reviewed_terminal,
    prepare_recovery_evidence,
)
from obsstat.planck_paired300_evidence import (  # noqa: E402
    verify_portable_artifact_manifest,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    mode.add_argument("--install-reviewed-terminal", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frozen-scalar-package", type=Path, required=True)
    parser.add_argument("--frozen-scalar-metadata", type=Path)
    parser.add_argument("--wu004-portable-dir", type=Path)
    parser.add_argument("--wu004-private-manifest", type=Path)
    parser.add_argument("--execution-manifest", type=Path)
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--private-evidence-dir", type=Path)
    parser.add_argument("--fresh-review-receipt", type=Path)
    parser.add_argument("--private-terminal-archive-dir", type=Path)
    parser.add_argument("--base-git-head")
    parser.add_argument("--implementation-git-head")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.prepare:
            required = {
                "frozen scalar metadata": args.frozen_scalar_metadata,
                "WU-004 portable directory": args.wu004_portable_dir,
                "WU-004 private manifest": args.wu004_private_manifest,
                "execution manifest": args.execution_manifest,
                "checkpoint directory": args.checkpoint_dir,
                "private evidence directory": args.private_evidence_dir,
                "base git head": args.base_git_head,
                "implementation git head": args.implementation_git_head,
            }
            missing = [label for label, value in required.items() if value is None]
            if missing:
                parser.error("--prepare missing: " + ", ".join(missing))
            result = prepare_recovery_evidence(
                output_dir=args.output_dir,
                frozen_scalar_package_path=args.frozen_scalar_package,
                frozen_scalar_metadata_path=args.frozen_scalar_metadata,
                wu004_portable_dir=args.wu004_portable_dir,
                wu004_private_manifest_path=args.wu004_private_manifest,
                execution_manifest_path=args.execution_manifest,
                checkpoint_dir=args.checkpoint_dir,
                private_evidence_dir=args.private_evidence_dir,
                base_git_head=args.base_git_head,
                implementation_git_head=args.implementation_git_head,
            )
        elif args.finalize:
            if args.fresh_review_receipt is None:
                parser.error("--finalize requires --fresh-review-receipt")
            result = finalize_recovery_evidence(
                output_dir=args.output_dir,
                frozen_scalar_package_path=args.frozen_scalar_package,
                fresh_review_receipt_path=args.fresh_review_receipt,
            )
        elif args.install_reviewed_terminal:
            if args.private_terminal_archive_dir is None:
                parser.error(
                    "--install-reviewed-terminal requires --private-terminal-archive-dir"
                )
            result = install_reviewed_terminal(
                output_dir=args.output_dir,
                private_archive_dir=args.private_terminal_archive_dir,
            )
        else:
            result = verify_portable_artifact_manifest(
                manifest_path=args.output_dir / "artifact_manifest.json",
                output_root=args.output_dir,
                frozen_scalar_package_path=args.frozen_scalar_package,
            )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "state": "BLOCKED_PMG_WU005_EVIDENCE_REPAIR",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 3
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
