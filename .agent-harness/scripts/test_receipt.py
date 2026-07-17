#!/usr/bin/env python3
"""Exact test-execution receipts (audit §7 test-cost policy).

A designated runner records one receipt per selector; reviewers consume the
receipt and rerun only a minimal reproducer when they can name a concrete
failure. The reuse key hashes: the git tree state of the relevant paths, the
exact selector, the runner environment (interpreter version + pip freeze),
and the seed. `check` exits 0 only for a current deterministic PASS receipt;
failing, flaky, or unseeded-random outcomes are never cached.

Named `test_receipt.py` but NOT a pytest module — pytest collection is
scoped by `testpaths` (tests/, scripts/codex_harness) and this directory is
not collected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from _harness import dump_json, load_json, root, utc_now

RECEIPT_DIR = ".agent-harness/receipts/tests"


def _tree_hash(repo: Path, paths: list[str]) -> str:
    """Hash the current bytes of the given paths (tracked or not).

    Uses on-disk content directly so untracked and modified files both
    invalidate the receipt; `git ls-files -s` alone misses untracked files
    and `git diff` misses them too.
    """

    digest = hashlib.sha256()
    for rel in sorted(paths):
        target = repo / rel
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if target.is_file():
            digest.update(hashlib.sha256(target.read_bytes()).digest())
        elif target.is_dir():
            for child in sorted(p for p in target.rglob("*") if p.is_file()):
                digest.update(child.relative_to(repo).as_posix().encode("utf-8"))
                digest.update(b"\0")
                digest.update(hashlib.sha256(child.read_bytes()).digest())
        else:
            digest.update(b"MISSING")
        digest.update(b"\0")
    return digest.hexdigest()


def _environment_hash(repo: Path, interpreter: str) -> str:
    digest = hashlib.sha256()
    version = subprocess.run(
        [interpreter, "-V"], text=True, capture_output=True, check=False
    ).stdout
    digest.update(version.encode("utf-8"))
    freeze = subprocess.run(
        [interpreter, "-m", "pip", "freeze", "--local"],
        text=True,
        capture_output=True,
        check=False,
    ).stdout
    digest.update(freeze.encode("utf-8"))
    return digest.hexdigest()


def reuse_key(
    repo: Path,
    selector: str,
    relevant_paths: list[str],
    interpreter: str,
    seed: str,
) -> str:
    digest = hashlib.sha256()
    digest.update(_tree_hash(repo, relevant_paths).encode("utf-8"))
    digest.update(b"\0")
    digest.update(selector.encode("utf-8"))
    digest.update(b"\0")
    digest.update(_environment_hash(repo, interpreter).encode("utf-8"))
    digest.update(b"\0")
    digest.update(seed.encode("utf-8"))
    return digest.hexdigest()


def _receipt_path(repo: Path, key: str) -> Path:
    return repo / RECEIPT_DIR / f"{key}.json"


def cmd_run(args) -> int:
    repo = root()
    interpreter = args.python or str(repo / "venv" / "bin" / "python")
    key = reuse_key(repo, args.selector, args.path, interpreter, args.seed)
    receipt_file = _receipt_path(repo, key)

    if receipt_file.is_file() and not args.force:
        receipt = load_json(receipt_file)
        if receipt.get("outcome") == "pass":
            print(
                f"REUSED exact receipt {key[:12]} (selector unchanged, tree "
                "unchanged, environment unchanged, seed unchanged) — not rerun"
            )
            return 0

    command = [interpreter, "-B", "-m", "pytest", *args.selector.split(), "-q"]
    completed = subprocess.run(
        command, cwd=repo, text=True, capture_output=True, check=False
    )
    outcome = "pass" if completed.returncode == 0 else "fail"
    receipt = {
        "schema_version": 1,
        "reuse_key": key,
        "selector": args.selector,
        "relevant_paths": args.path,
        "seed": args.seed,
        "command": " ".join(command),
        "exit": completed.returncode,
        "outcome": outcome,
        "tail": (completed.stdout + completed.stderr)[-2000:],
        "recorded_at": utc_now(),
    }
    if outcome == "pass":
        # Never cache failures — they must always re-run.
        dump_json(receipt_file, receipt)
    print(f"{outcome.upper()} {args.selector} (exit {completed.returncode})")
    return completed.returncode


def cmd_check(args) -> int:
    repo = root()
    interpreter = args.python or str(repo / "venv" / "bin" / "python")
    key = reuse_key(repo, args.selector, args.path, interpreter, args.seed)
    receipt_file = _receipt_path(repo, key)
    if not receipt_file.is_file():
        print("no current receipt (source/toolchain/seed changed or never run)")
        return 1
    receipt = load_json(receipt_file)
    if receipt.get("outcome") != "pass":
        print("receipt exists but is not a deterministic pass")
        return 1
    print(json.dumps({"reuse_key": key, "outcome": "pass"}, ensure_ascii=False))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "check"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--selector", required=True,
                         help="exact pytest selector string")
        cmd.add_argument("--path", action="append", required=True,
                         help="relevant source path (repeatable)")
        cmd.add_argument("--seed", default="unseeded")
        cmd.add_argument("--python", default=None)
        if name == "run":
            cmd.add_argument("--force", action="store_true")
    args = parser.parse_args()
    raise SystemExit(cmd_run(args) if args.command == "run" else cmd_check(args))


if __name__ == "__main__":
    main()
