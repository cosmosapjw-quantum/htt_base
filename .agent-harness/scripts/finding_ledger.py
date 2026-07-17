#!/usr/bin/env python3
"""Cross-run finding ledger (audit H7).

Records resolved findings as `{claim_id, evidence_fingerprint, verdict,
resolution_commit, recorded_at}` JSON lines in the tracked
`.agent-harness/ledger/FINDING_LEDGER.jsonl`, so an already-fixed attack is
not re-raised under a new run name. `merge_results.py` consults this ledger
and annotates matching findings `previously_resolved`.
"""
from __future__ import annotations

import argparse
import json
import subprocess

from _harness import load_json, root, utc_now

LEDGER_REL = ".agent-harness/ledger/FINDING_LEDGER.jsonl"


def _ledger_path(repo):
    path = repo / LEDGER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _rows(repo) -> list[dict]:
    path = _ledger_path(repo)
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def cmd_record(args) -> int:
    repo = root()
    commit = args.resolution_commit
    if commit == "HEAD":
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
    merged = load_json(repo / args.merged)
    existing = {
        (r.get("claim_id"), r.get("evidence_fingerprint"), r.get("verdict"))
        for r in _rows(repo)
    }
    added = 0
    with _ledger_path(repo).open("a", encoding="utf-8") as handle:
        for finding in merged.get("findings", []):
            key = (
                str(finding.get("claim_id", "")),
                str(finding.get("evidence_fingerprint", "")),
                str(finding.get("verdict", "")),
            )
            if key in existing:
                continue
            handle.write(
                json.dumps(
                    {
                        "claim_id": key[0],
                        "evidence_fingerprint": key[1],
                        "verdict": key[2],
                        "resolution_commit": commit,
                        "recorded_at": utc_now(),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            existing.add(key)
            added += 1
    print(f"recorded {added} resolved findings at {commit[:12]}")
    return 0


def cmd_check(args) -> int:
    repo = root()
    for row in _rows(repo):
        if (
            row.get("claim_id") == args.claim
            and row.get("evidence_fingerprint") == args.fingerprint
            and (args.verdict is None or row.get("verdict") == args.verdict)
        ):
            print(json.dumps(row, ensure_ascii=False))
            return 0
    print("not recorded")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record")
    record.add_argument("--merged", required=True,
                        help="path to a MERGED_RESULTS.json")
    record.add_argument("--resolution-commit", required=True,
                        help="commit that resolved the findings (or HEAD)")

    check = sub.add_parser("check")
    check.add_argument("--claim", required=True)
    check.add_argument("--fingerprint", required=True)
    check.add_argument("--verdict", default=None)

    args = parser.parse_args()
    raise SystemExit(cmd_record(args) if args.command == "record" else cmd_check(args))


if __name__ == "__main__":
    main()
