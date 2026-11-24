"""R108 A3: merge every reduced Commander pair with the unchanged R105 estimator and record acquisition status.

Inputs: R105 COMMANDER_TRANSFER.json and COMMANDER_PAIR_00001.json (pairs reduced in R105) and
every ~/Downloads/htt_r105_commander/reductions/commander_NNNNN.json (R106 and R108 batches).
``scripts.r105.commander_ensemble.merge`` refuses receipts whose estimator, beam, mask or
observation identities differ, so a successful merge certifies one estimator SHA.  The status
file lists the batch attempts (from their logs), the split products received so far (with
receipt SHA-256) and what remains for >= 300 pairs.

Usage: PYTHONPATH=.:htt:htt/src python -m scripts.r108.commander_status
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.r105.commander_ensemble import merge
from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json

R105 = REPO / "docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124"
RED = Path.home() / "Downloads/htt_r105_commander/reductions"
LOGS = Path.home() / "Downloads/htt_r108/logs"
SPLITS = Path.home() / "Downloads/htt_r108/commander_splits"


def main() -> None:
    files = [R105 / "COMMANDER_TRANSFER.json", R105 / "COMMANDER_PAIR_00001.json",
             *sorted(RED.glob("commander_[0-9][0-9][0-9][0-9][0-9].json"))]
    merged = merge([json.loads(p.read_text()) for p in files])
    write_json(OUT_DIR / "COMMANDER" / "MERGED.json",
               {**merged, "receipts": {p.name: sha256_file(p) for p in files}, "git": git_state(),
                "claim": "ranks against the simulated pairs reduced so far; not a qualified null (fewer than 300 pairs, "
                         "no split-difference check unless SPLIT_DIFFERENCE.json exists)"})
    attempts = []
    for log in sorted(LOGS.glob("A3_commander_*.log")):
        text = log.read_text(errors="replace")
        m = re.search(r"\|rc=(-?\d+)\|wall=([\d.]+)\|", text)
        err = [ln for ln in text.splitlines() if "Error" in ln or "error" in ln][-1:]
        attempts.append({"log": log.name, "rc": int(m.group(1)) if m else None, "wall_s": float(m.group(2)) if m else None,
                         "last_error_line": err[0] if err else None, "finished": m is not None})
    split_receipts = []
    if (SPLITS / "RECEIPTS.jsonl").is_file():
        split_receipts = [json.loads(l) for l in (SPLITS / "RECEIPTS.jsonl").read_text().splitlines() if l.strip()]
    n_pairs = len(merged["indices"])
    write_json(OUT_DIR / "COMMANDER" / "ACQUISITION_STATUS.json", {
        "schema": "htt.r108.commander_status.1", "pairs_merged": n_pairs, "indices": merged["indices"],
        "pairs_missing_for_300": 300 - n_pairs, "estimator_sha256": merged["estimator_sha256"],
        "batch_attempts": attempts,
        "split_products_received": [{k: r.get(k) for k in ("id", "bytes", "sha256", "fetched_at_utc")} for r in split_receipts],
        "split_products_required": 4 + 4 * 7, "git": git_state()})


if __name__ == "__main__":
    main()
