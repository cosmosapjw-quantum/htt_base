"""Claim-adjudication runner: literature-grounded unlock ledger (--write/--check).

Reads the web-CRAG literature verdicts (produced by the adjudication workflow)
and emits the promotion/unlock ledger over every claim family. Incremental:
re-run whenever more cards land or a fresh literature pass is done.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.claim_adjudication_harness import (  # noqa: E402
    FAMILIES,
    adjudicate_all,
    promotion_rank,
)

ADJ_DIR = REPO / "docs/generated/claim_adjudication"
VERDICTS = ADJ_DIR / "literature_verdicts.json"
LEDGER_JSON = ADJ_DIR / "adjudication_ledger.json"
LEDGER_MD = ADJ_DIR / "adjudication_ledger.md"


def _load_verdicts() -> dict[str, dict]:
    if VERDICTS.is_file():
        return json.loads(VERDICTS.read_text())
    return {}


def build_ledger() -> dict:
    verdicts = _load_verdicts()
    adjs = adjudicate_all(verdicts)
    by_status: dict[str, list[str]] = {}
    rows = []
    for a in adjs:
        by_status.setdefault(a.unlock_status, []).append(a.family.id)
        rows.append({
            "family": a.family.id, "title": a.family.title, "lane": a.family.lane,
            "pr_cards": list(a.family.pr_cards),
            "literature_anchor": a.family.literature_anchor,
            "structural_blocker": a.family.structural_blocker,
            "significance": a.significance, "novelty_tier": a.novelty_tier,
            "novelty_rationale": a.novelty_rationale,
            "completeness": a.completeness, "verification": a.verification,
            "provenance_status": a.provenance_status,
            "citation_key": a.citation_key,
            "verdict_survived_refutation": a.verdict_survived_refutation,
            "unlock_status": a.unlock_status, "rationale": a.rationale,
        })
    promotable = sorted(
        [a for a in adjs if a.unlock_status == "PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION"],
        key=promotion_rank, reverse=True)
    promotion_queue = [{"family": a.family.id, "significance": a.significance,
                        "novelty_tier": a.novelty_tier, "title": a.family.title}
                       for a in promotable]
    unlockable_now = [r["family"] for r in rows
                      if r["unlock_status"] in ("PROVENANCE_CORRECTION_REQUIRED",)
                      or (r["provenance_status"] == "cited_correct")]
    return {
        "schema": "htt.claim_adjudication.ledger.v1",
        "generated_by": "run_claim_adjudication.py",
        "n_families": len(FAMILIES),
        "has_literature_verdicts": bool(verdicts),
        "counts_by_unlock_status": {k: len(v) for k, v in sorted(by_status.items())},
        "families_by_unlock_status": {k: sorted(v) for k, v in sorted(by_status.items())},
        "promotion_queue_ranked": promotion_queue,
        "rows": sorted(rows, key=lambda r: r["family"]),
        "policy": {
            "independence_gate_never_fake_passed": True,
            "web_crag_resolves": ["provenance/citation", "external-novelty tier K/C/P/S"],
            "web_crag_cannot_resolve": ["non-author Independence adjudication",
                                        "DESI data acquisition (PR-151)",
                                        "native Bianchi Boltzmann solver (Track II)"],
        },
    }


def render_md(ledger: dict) -> str:
    lines = ["# Claim-adjudication unlock ledger",
             "",
             f"{ledger['n_families']} claim families adjudicated against the external "
             "literature on four axes (significance / novelty K-C-P-S / completeness / "
             "verification). The Independence gate is never fake-passed.",
             ""]
    if not ledger["has_literature_verdicts"]:
        lines += ["> STRUCTURAL-ONLY MODE: no literature verdicts loaded yet; "
                  "run the web-CRAG adjudication workflow to populate the four axes.", ""]
    lines += ["## Counts by unlock status", ""]
    for status, n in ledger["counts_by_unlock_status"].items():
        lines.append(f"- **{status}**: {n} "
                     f"({', '.join(ledger['families_by_unlock_status'][status])})")
    lines += ["", "## Promotion queue (all-axes-pass, one non-author adjudication from VALIDATED)", ""]
    if ledger["promotion_queue_ranked"]:
        for i, q in enumerate(ledger["promotion_queue_ranked"], 1):
            lines.append(f"{i}. **{q['family']}** [{q['significance']}/{q['novelty_tier']}] — {q['title']}")
    else:
        lines.append("_(none yet — populate literature verdicts)_")
    lines += ["", "## Per-family adjudication", ""]
    for r in ledger["rows"]:
        lines.append(f"### {r['family']} — {r['title']}")
        lines.append("")
        lines.append(f"- lane: {r['lane']}; cards: {', '.join(r['pr_cards'])}")
        lines.append(f"- literature: {r['literature_anchor']}")
        lines.append(f"- axes: significance={r['significance']}, novelty={r['novelty_tier']}, "
                     f"completeness={r['completeness']}, verification={r['verification']}, "
                     f"provenance={r['provenance_status']}")
        if r["novelty_rationale"]:
            lines.append(f"- novelty rationale: {r['novelty_rationale']}")
        lines.append(f"- **unlock: {r['unlock_status']}** — {r['rationale']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    ADJ_DIR.mkdir(parents=True, exist_ok=True)
    ledger = build_ledger()
    ledger_bytes = (json.dumps(ledger, sort_keys=True, indent=1) + "\n").encode()
    md = render_md(ledger)
    if args.write:
        LEDGER_JSON.write_bytes(ledger_bytes)
        LEDGER_MD.write_text(md, encoding="utf-8")
        print(f"wrote ledger: {ledger['counts_by_unlock_status']}")
        print(f"promotion queue: {len(ledger['promotion_queue_ranked'])}")
        return 0
    ok = (LEDGER_JSON.exists() and LEDGER_JSON.read_bytes() == ledger_bytes
          and LEDGER_MD.exists() and LEDGER_MD.read_text() == md)
    print(json.dumps({"mode": "check", "ok": ok,
                      "has_verdicts": ledger["has_literature_verdicts"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
