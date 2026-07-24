"""PR-227 runner: Track-I reproduction capsule (Independence gate OPEN)."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_reproduction import reproduce_all, environment_recipe  # noqa: E402
SPEC = REPO/"docs/research_program/revival/pr227_spec.yaml"
CARD = REPO/"docs/generated/pr227_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build_payload(rep=None):
    rep = rep if rep is not None else reproduce_all()
    env = environment_recipe()
    ok = rep["all_byte_stable"]
    terminal = "TRACK_I_AUTHOR_REPRODUCTION_VERIFIED_INDEPENDENCE_OPEN" if ok else "BLOCKED_REPRODUCTION_FAILURE"
    return {"schema":"htt.pr227.result_card.v1","pr_id":"PR-227",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "independence_note":"non-author clean-machine reproduction deferred to capacity; never fake-passed",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr227_reproduce.py --write"},
      "result":{"reproduction":rep,"environment_recipe":env},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "author-side byte-stability is verified; the non-author Independence gate stays OPEN",
        "the Independence gate is never fake-passed",
        "results are regenerated from runners, not from an author cache"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv)
    if a.write:
        p=build_payload(); CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    # A stored terminal is diagnostic-only. Re-run every registered card check
    # and compare the resulting payload byte-for-byte with the stored capsule.
    p = build_payload()
    ok = CARD.exists() and CARD.read_bytes() == _render(p)
    failed_cards = sorted(
        pr for pr, result in p["result"]["reproduction"]["per_card"].items()
        if not result["byte_stable"]
    )
    print(json.dumps({
        "failed_cards": failed_cards,
        "live_author_reproduction": p["result"]["reproduction"][
            "author_reproduction"
        ],
        "mode": "check",
        "ok": ok,
        "read_only": True,
        "terminal": p["terminal"],
    }, sort_keys=True))
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
