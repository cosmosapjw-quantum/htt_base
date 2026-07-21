"""PR-218 runner: Teff certified surrogate (no native -> no inference)."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_teff_surrogate import certify, overlapping_split_is_a_defect  # noqa: E402
SPEC = REPO/"docs/research_program/revival/pr218_spec.yaml"
CARD = REPO/"docs/generated/pr218_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build_payload():
    c = certify()
    overlap_flagged = overlapping_split_is_a_defect()
    ok = (c["held_out_envelope_holds"] and c["out_of_domain_rejected"]
          and c["nested_split_disjoint"] and not c["authorizes_inference"]
          and overlap_flagged)
    terminal = "TEFF_SURROGATE_CERTIFIED_METHODOLOGY_INFERENCE_WITHHELD_NO_NATIVE" if ok else "BLOCKED_SURROGATE_GATE_FAILURE"
    return {"schema":"htt.pr218.result_card.v1","pr_id":"PR-218",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr218_surrogate.py --write"},
      "result":{"certificate":c,"overlapping_split_flagged":overlap_flagged},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "with no native solver the surrogate authorizes NO inference",
        "out-of-domain output is rejected, never passed as inference",
        "training and calibration points never overlap"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
