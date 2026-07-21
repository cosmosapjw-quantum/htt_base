"""PR-219 runner: response quotient + non-id atlas (extends PR-127)."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_response_quotient import (  # noqa: E402
    LABELS, SCALAR, ENLARGED, quotient, quotient_via_nullspace, rank_lattice,
    reopening_requirement, zero_column_is_not_a_no_go)
SPEC = REPO/"docs/research_program/revival/pr219_spec.yaml"
CARD = REPO/"docs/generated/pr219_result_card.json"
PR127 = REPO/"docs/generated/pr127_response_kernel.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build_payload():
    sq = quotient(LABELS, SCALAR); eq = quotient(LABELS, ENLARGED)
    sq2 = quotient_via_nullspace(LABELS, SCALAR)
    p2_agree = set(map(frozenset, sq)) == set(map(frozenset, sq2))
    ranks = rank_lattice()
    reopen = reopening_requirement()
    zcol = zero_column_is_not_a_no_go()
    pr127 = json.loads(PR127.read_text()); pr127_rank = pr127.get("rank")
    ok = (sq == (("BI","BV","BVIIh"),("FLRW_tilt",)) and len(eq) == 4
          and ranks == [2,3,4] and p2_agree and reopen["reopened_to_singletons"]
          and zcol["scalar_w2_all_zero"] and zcol["enlarged_w2_nonzero"]
          and pr127_rank == 2)
    terminal = "RESPONSE_QUOTIENT_ATLAS_CERTIFIED_PR127_CONSISTENT" if ok else "BLOCKED_QUOTIENT_GATE_FAILURE"
    return {"schema":"htt.pr219.result_card.v1","pr_id":"PR-219",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),"cross_references":["PR-127"],
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr219_quotient.py --write"},
      "result":{"scalar_quotient":[list(c) for c in sq],"enlarged_quotient":[list(c) for c in eq],
        "p2_nullspace_agrees":p2_agree,"rank_lattice":ranks,"reopening_requirement":reopen,
        "zero_column_atlas":zcol,"pr127_kernel_rank":pr127_rank},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "a zero response column is unobserved, never a physical no-go",
        "equivalent families are one quotient class, never separate evidence rows",
        "reopening a class requires a declared new observable, computed not assumed"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
