"""PR-224 runner: directional x depth x host falsifier (extends PR-176/179)."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_directional_falsifier import falsify, no_bulk_equals_divergence, no_h0_percentage_without_scaling  # noqa: E402
SPEC = REPO/"docs/research_program/revival/pr224_spec.yaml"
CARD = REPO/"docs/generated/pr224_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build_payload():
    f = falsify()
    ok = (f["recovers_truth"] and f["depth_mode_falsifies_bridge_without_it"]
          and no_bulk_equals_divergence() and no_h0_percentage_without_scaling())
    terminal = "DIRECTIONAL_DEPTH_HOST_FALSIFIER_CERTIFIED" if ok else "BLOCKED_FALSIFIER_GATE_FAILURE"
    return {"schema":"htt.pr224.result_card.v1","pr_id":"PR-224",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),"cross_references":["PR-176","PR-179"],
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr224_falsifier.py --write"},
      "result":{"falsifier":f,"no_bulk_equals_divergence":no_bulk_equals_divergence(),
        "no_h0_percentage_without_scaling":no_h0_percentage_without_scaling()},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "a bulk amplitude is never substituted for divergence",
        "no H0 percentage is reported without an explicit depth-scaling law",
        "the falsifier does not assert the tilted-observer bridge in advance"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
