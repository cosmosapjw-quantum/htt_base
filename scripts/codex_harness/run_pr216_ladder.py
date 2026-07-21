"""PR-216 runner: physical sharpness ladder with a blocked global stage."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_sharpness_ladder import (  # noqa: E402
    SharpnessError, SharpnessLadder, build_certified_ladder, homogeneous_momentum_constraint_residual)
SPEC = REPO/"docs/research_program/revival/pr216_spec.yaml"
CARD = REPO/"docs/generated/pr216_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build_payload():
    L = build_certified_ladder(); snap = L.snapshot()
    # decisive falsifier: algebraic-only -> global promotion is refused
    refused = False
    try:
        SharpnessLadder().auto_promote_global_from_algebraic()
    except SharpnessError:
        refused = True
    residual_zero = homogeneous_momentum_constraint_residual() == 0
    ok = (snap["algebraic"]["status"] == "ATTAINED"
          and snap["constraint"]["status"] == "ATTAINED"
          and snap["local"]["status"] == "ATTAINED_WITH_OBLIGATION"
          and snap["global"]["status"] == "BLOCKED"
          and refused and residual_zero)
    terminal = "SHARPNESS_LADDER_STAGED_GLOBAL_BLOCKED_WITH_OBLIGATION" if ok else "BLOCKED_LADDER_GATE_FAILURE"
    return {"schema":"htt.pr216.result_card.v1","pr_id":"PR-216",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr216_ladder.py --write"},
      "result":{"ladder":snap,"algebraic_only_global_promotion_refused":refused,
        "homogeneous_constraint_residual_zero":residual_zero},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "an algebraic PSD witness never auto-promotes global-dynamics sharpness",
        "the global stage is BLOCKED with a research obligation, not scope-reduced",
        "each stage is attained only if every lower stage is attained"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
