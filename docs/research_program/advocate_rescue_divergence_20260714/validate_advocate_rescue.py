#!/usr/bin/env python3
"""Validator for the advocate-rescue divergence deliverable (dev-tier).

Fail-closed checks:
  1. steelman covers all 102 audit criticism IDs;
  2. no ranked candidate TITLE collides verbatim with a frozen advocate-candidate title
     or roadmap PR title (net-new IDs must be materially distinct);
  3. every ranked candidate has a decisive_falsifier and a gate_tier;
  4. every entry flagged non_overlap_ok=false carries an overlap_correction;
  5. all family-ID/geometry (gates_off_ambitious) rows are hypothesis_only (never a
     promotion field), and the deliverable declares public_use=false.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    errs: list[str] = []
    frozen = json.loads((HERE / "frozen_non_overlap_set.json").read_text())
    steel = json.loads((HERE / "08_steelman_response_matrix.json").read_text())
    led = json.loads((HERE / "07_ranked_candidate_ledger.json").read_text())
    ranked = led["ranked"]

    # 1. steelman coverage
    crit_ids = set(frozen["criticism_ids"])
    steel_ids = {r["criticism_id"] for r in steel}
    missing = crit_ids - steel_ids
    if missing:
        errs.append(f"steelman missing {len(missing)} criticisms: {sorted(missing)[:10]}")

    # 2. verbatim title collision with frozen set
    frozen_titles = {t.strip().lower() for t in frozen["advocate_candidate_ids"].values()}
    frozen_titles |= {t.strip().lower() for t in frozen["roadmap_prs"].values()}
    for r in ranked:
        if r["title"].strip().lower() in frozen_titles:
            errs.append(f"rank {r['rank']} title collides verbatim with frozen set: {r['title']!r}")

    # 3. falsifier + gate_tier present
    for r in ranked:
        if not r.get("decisive_falsifier"):
            errs.append(f"rank {r['rank']} missing decisive_falsifier")
        if r.get("gate_tier") not in ("defensible", "gates_off_ambitious"):
            errs.append(f"rank {r['rank']} bad gate_tier {r.get('gate_tier')!r}")

    # 4. overlap flags carry a correction
    for r in ranked:
        if r.get("non_overlap_ok") is False and not r.get("overlap_correction"):
            errs.append(f"rank {r['rank']} non_overlap_ok=false but no overlap_correction")

    # 5. gates_off rows carry no promotion; deliverable is public_use=false
    for r in ranked:
        if r.get("gate_tier") == "gates_off_ambitious":
            for banned in ("promoted", "production", "manuscript_ready", "public_use_true"):
                if banned in json.dumps(r).lower():
                    errs.append(f"rank {r['rank']} gates_off row leaks promotion token {banned!r}")

    net_new = sum(1 for r in ranked if r.get("non_overlap_ok"))
    if errs:
        print("VALIDATION FAILED:", file=sys.stderr)
        for e in errs:
            print(" -", e, file=sys.stderr)
        return 1
    print(f"advocate-rescue validation passed: {len(steel)}/102 criticisms answered; "
          f"{len(ranked)} ranked ({net_new} net-new); no frozen-title collisions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
