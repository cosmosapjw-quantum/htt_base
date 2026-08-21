"""PR-226 runner: Track-I data-lane closure (partial, DESI blocked on PR-151)."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_data_lane_closure import closure_summary  # noqa: E402
SPEC = REPO/"docs/research_program/revival/pr226_spec.yaml"
CARD = REPO/"docs/generated/pr226_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build_payload():
    s = closure_summary()
    # success = the three solver-independent lanes close AND DESI is correctly
    # blocked on PR-151 (partial mocks never in a headline)
    ok = (set(s["closed_lanes"]) >= {"planck_k1", "cf4", "act"}
          and s["desi_blocked_on_pr151"] and s["headline_discipline_ok"])
    terminal = "DATA_LANE_CLOSURE_PARTIAL_THREE_LANES_CLOSED_DESI_BLOCKED_ON_PR151" if ok else "BLOCKED_DATA_LANE_GATE_FAILURE"
    return {"schema":"htt.pr226.result_card.v1","pr_id":"PR-226",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),
        "cross_references":["PR-144","PR-145","PR-146","PR-147","PR-148","PR-149","PR-150","PR-152","PR-177"],
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "desi_official_mock_lane":"BLOCKED_ON_PR151_TERMINAL",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr226_datalane.py --write"},
      "result":s,
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "partial DESI mocks never enter any rank/p/covariance/significance or headline",
        "each closed lane carries its own null/covariance/selection receipt",
        "the prior DESI diagnostic is invalidated pending formalism revalidation",
        "the DESI official-mock closure waits for a revalidated PR-151 terminal receipt"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
