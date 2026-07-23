"""PR-220 runner: inactive-prior invariance + legacy lnB negative control."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_inactive_evidence import (  # noqa: E402
    inactive_invariance, sympy_mass_seal, duplicate_response_no_preference, legacy_lnb_is_negative_control)
SPEC = REPO/"docs/research_program/revival/pr220_spec.yaml"
CARD = REPO/"docs/generated/pr220_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build_payload():
    inv = inactive_invariance(); seal = sympy_mass_seal()
    dup = duplicate_response_no_preference(); neg = legacy_lnb_is_negative_control()
    ok = (inv["inactive_creates_no_occam"] and inv["unnormalized_mutation_caught"]
          and seal["seal_pass"] and dup and neg)
    terminal = "INACTIVE_INVARIANCE_CERTIFIED_LEGACY_LNB_NEGATIVE_CONTROL" if ok else "BLOCKED_EVIDENCE_GATE_FAILURE"
    return {"schema":"htt.pr220.result_card.v1","pr_id":"PR-220",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),"cross_references":["PR-140","PR-129"],
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr220_evidence.py --write"},
      "result":{"inactive_invariance":inv,"sympy_mass_seal":seal,
        "duplicate_response_no_preference":dup,"legacy_lnb_negative_control":neg},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "the retired lnB=26.4 is a negative control, never a live result",
        "an inactive normalized parameter creates no Occam penalty",
        "a duplicate response cannot manufacture a geometry preference"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
