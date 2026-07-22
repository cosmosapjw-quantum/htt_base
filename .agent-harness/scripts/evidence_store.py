#!/usr/bin/env python3
"""Content-addressed raw-evidence store (audit §7 retention).

`put PATH` copies the bytes to
`.agent-harness/evidence/sha256/<h[:2]>/<h>` (gitignored) exactly once —
identical bytes stored twice yield a single blob — and prints the typed
reference `{path, sha256, bytes, producer, command_fingerprint}` that result
JSON must embed instead of inlining raw logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from _harness import EVIDENCE_FINGERPRINT_RE, root


def store_bytes(repo: Path, source: Path) -> tuple[str, Path, bool]:
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    blob = repo / ".agent-harness" / "evidence" / "sha256" / digest[:2] / digest
    created = False
    if blob.exists() and (
        not blob.is_file()
        or blob.is_symlink()
        or hashlib.sha256(blob.read_bytes()).hexdigest() != digest
    ):
        raise RuntimeError(f"content-addressed evidence blob is poisoned: {blob}")
    if not blob.is_file():
        blob.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, blob)
        created = True
    return digest, blob, created


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    put = sub.add_parser("put")
    put.add_argument("path")
    put.add_argument("--producer", default="unknown")
    put.add_argument("--command-fingerprint", required=True)
    args = parser.parse_args()

    repo = root()
    source = Path(args.path)
    if not source.is_file():
        raise SystemExit(f"no such file: {source}")
    if EVIDENCE_FINGERPRINT_RE.fullmatch(args.command_fingerprint) is None:
        raise SystemExit("--command-fingerprint must be sha256:<64 lowercase hex>")
    try:
        digest, blob, created = store_bytes(repo, source)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(
        json.dumps(
            {
                "path": blob.relative_to(repo).as_posix(),
                "sha256": digest,
                "bytes": blob.stat().st_size,
                "producer": args.producer,
                "command_fingerprint": args.command_fingerprint,
                "deduplicated": not created,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
