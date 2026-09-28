#!/usr/bin/env python3
"""Build the bounded 57-PR disposition snapshot from the supplied audit matrix."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "PR_DISPOSITION_MATRIX.csv"
OUTPUT = Path(__file__).resolve().parents[1] / "PR_DISPOSITION.json"
INTEGRATED = {440, 449, 460, 461, 463, 465, 466, 467}
SUPERSEDED = {468, 470}
OUT_OF_SCOPE = {428}
CURRENT_HEAD_OVERRIDES = {469: "f621a581f9ca468e4f4cc2b71ac2867c687138ca"}


def classify(number: int) -> str:
    if number in INTEGRATED:
        return "ALREADY_INTEGRATED_CLOSED"
    if number in SUPERSEDED:
        return "SUPERSEDED_CLOSED"
    if number in OUT_OF_SCOPE:
        return "OUT_OF_SCOPE"
    return "OPEN_HOLD"


def reason(number: int, source_action: str) -> str:
    fixed = {
        427: "337-file actual diff conflicts with the one-marker smoke description; rebase and scope audit required",
        428: "2131-file retirement delta includes 2106 deletions and is outside the bounded Loop 2 closeout",
        444: "same-head run 33718012456 attempt 3 job 109007095833 completed all 8 steps and closed issue 448; the PR remains open for its own base, increment, and dependency review",
        469: "PR-304/315 lineage is absent from current main; repair and two independent exact-head Repository integrity runs are required before integration",
        468: "published R9 revision-2 successor and current 211-card DAG preserve the usable requirements; no old DAG overwrite",
        470: "all 25 blobs are historically preserved and optical requirements are represented by current R9/optical follow-up boundaries; inactive old DAG is not restored",
    }
    if number in INTEGRATED:
        return "latest audited head is an ancestor of de3ab202; closed as integrated without a redundant merge"
    return fixed.get(number, f"deferred for its own base/increment/dependency review; audit action={source_action}")


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    payload = {
        "format": "TYPEFREE_LOOP2_PR_DISPOSITION_V1",
        "as_of": "2026-09-29",
        "audit_commit": "de3ab20219c46c2b14f1d2ec6bb87508c331634d",
        "canonical_dag_cards": 211,
        "classification_is_not_merge": True,
        "pull_requests": [
            {
                "number": int(row["pr"]), "url": row["url"], "title": row["title"],
                "audited_head": row["head"], "current_head": CURRENT_HEAD_OVERRIDES.get(int(row["pr"]), row["head"]),
                "audited_base": row["base"],
                "delta_file_count": int(row["delta_file_count"]) if row["delta_file_count"] else 0,
                "disposition": classify(int(row["pr"])),
                "remote_action": "CLOSE_WITH_EVIDENCE" if classify(int(row["pr"])) in {"ALREADY_INTEGRATED_CLOSED", "SUPERSEDED_CLOSED"} else "KEEP_OPEN",
                "observed_remote_state": "CLOSED" if classify(int(row["pr"])) in {"ALREADY_INTEGRATED_CLOSED", "SUPERSEDED_CLOSED"} else "OPEN",
                "reason": reason(int(row["pr"]), row["action"]),
            }
            for row in rows
        ],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
