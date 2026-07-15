#!/usr/bin/env python3
"""Generate or verify the PR-120 CF4 P0 propagation quarantine."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "htt" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from common.cf4_p0_quarantine import (  # noqa: E402
    canonical_artifact_bytes,
    load_policy,
    validate_repository,
)


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _artifact_drift(
    root: Path, expected: Mapping[str, bytes]
) -> list[dict[str, object]]:
    drift: list[dict[str, object]] = []
    for relative, content in sorted(expected.items()):
        path = root / relative
        if not path.is_file():
            drift.append({"path": relative, "code": "missing_generated_artifact"})
            continue
        actual = path.read_bytes()
        if actual != content:
            drift.append(
                {
                    "path": relative,
                    "code": "generated_artifact_drift",
                    "expected_size": len(content),
                    "actual_size": len(actual),
                }
            )
    return drift


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write canonical artifacts")
    mode.add_argument("--check", action="store_true", help="verify canonical artifacts")
    mode.add_argument(
        "--list-signatures",
        action="store_true",
        help="print configured contextual signature IDs",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the validation summary as JSON",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="repository root (defaults to the script checkout)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.repo_root.resolve()
    if args.list_signatures:
        policy, policy_hash = load_policy(root)
        payload = {
            "schema": "htt.cf4_p0_quarantine_signature_list.v1",
            "policy_sha256": policy_hash,
            "signature_ids": [rule["id"] for rule in policy["stale_signatures"]],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    expected = canonical_artifact_bytes(root)
    if args.write:
        for relative, content in sorted(expected.items()):
            _atomic_write(root / relative, content)

    drift = _artifact_drift(root, expected)
    report = validate_repository(root)
    payload = report.to_dict()
    payload["mode"] = "write" if args.write else "check"
    payload["generated_artifact_drift"] = drift
    payload["ok"] = report.ok and not drift
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "CF4 P0 quarantine: "
            f"ok={payload['ok']} scanned={payload['scanned_path_count']} "
            f"issues={len(payload['issues'])} drift={len(drift)}"
        )
        for item in drift:
            print(f"DRIFT {item['path']}: {item['code']}", file=sys.stderr)
        for issue in report.issues:
            print(
                f"ISSUE {issue.path}:{issue.line or 0} {issue.code}: {issue.detail}",
                file=sys.stderr,
            )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
