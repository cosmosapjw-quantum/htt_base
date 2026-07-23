"""PR-221 runner: cross-survey dipole source discrimination."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_dipole_discrimination import run  # noqa: E402
SPEC = REPO/"docs/research_program/revival/pr221_spec.yaml"
CARD = REPO/"docs/generated/pr221_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build_payload():
    r = run()
    ok = r["gate_pass"]
    terminal = "DIPOLE_SOURCE_DISCRIMINATION_WITH_MANDATORY_ABSTENTION" if ok else "BLOCKED_DISCRIMINATION_GATE_FAILURE"
    return {"schema":"htt.pr221.result_card.v1","pr_id":"PR-221",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),"cross_references":["PR-141"],
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr221_dipole.py --write"},
      "result":r,
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "a confusable/misspecified source triggers mandatory abstention, never a global selection",
        "discrimination is diagnostic mechanics on synthetic surveys, not a cosmic-dipole detection",
        "the competitor list is fixed and pre-registered"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1,default=float)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
