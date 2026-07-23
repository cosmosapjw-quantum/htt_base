"""PR-217 runner: MES attribution surface (frozen-safe, cross-refs PR-186)."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_mes_attribution import (  # noqa: E402
    FROZEN_W2_MAX, GEODESIC_SAG, NON_GEODESIC_UNSOURCED, attribution_surface,
    coefficient_is_live_ceiling, epsilon1_zero_is_branch_choice_not_uniqueness)
SPEC = REPO/"docs/research_program/revival/pr217_spec.yaml"
CARD = REPO/"docs/generated/pr217_result_card.json"
PR186 = REPO/"docs/generated/pr186_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _find(o,key):
    if isinstance(o,dict):
        for k,v in o.items():
            if k==key: return v
            r=_find(v,key)
            if r is not None: return r
    elif isinstance(o,list):
        for x in o:
            r=_find(x,key)
            if r is not None: return r
    return None
def build_payload():
    surf = attribution_surface()
    pr186 = json.loads(PR186.read_text())
    pr186_frozen = _find(pr186,"frozen_mes_vorticity_ceiling_W2_max")
    frozen_consistent = pr186_frozen == FROZEN_W2_MAX == surf["frozen_anchor"]
    geodesic_live = coefficient_is_live_ceiling(GEODESIC_SAG)
    nongeo_live = coefficient_is_live_ceiling(NON_GEODESIC_UNSOURCED)
    branch_choice = epsilon1_zero_is_branch_choice_not_uniqueness()
    ok = (surf["endpoint_matches_frozen_anchor"] and frozen_consistent
          and surf["zero_admissible"] and not surf["full_dipole_admissible"]
          and surf["monotone_increasing"] and geodesic_live and not nongeo_live
          and branch_choice)
    terminal = "MES_ATTRIBUTION_SURFACE_FROZEN_ANCHORED_HIERARCHY_EXCLUDES_FULL_DIPOLE" if ok else "BLOCKED_MES_GATE_FAILURE"
    return {"schema":"htt.pr217.result_card.v1","pr_id":"PR-217",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),"cross_references":["PR-186","MES-BR"],
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr217_mes.py --write"},
      "result":{"attribution_surface":surf,"pr186_frozen_W2_max":pr186_frozen,
        "frozen_anchor_consistent":frozen_consistent,
        "geodesic_is_live_ceiling":geodesic_live,"nongeodesic_unsourced_is_live_ceiling":nongeo_live,
        "epsilon1_zero_is_branch_choice_not_uniqueness":branch_choice,
        "branches":{"geodesic_sag":GEODESIC_SAG,"non_geodesic_unsourced":NON_GEODESIC_UNSOURCED}},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "the frozen W2_max 3.3789222980376e-13 is the intrinsic-zero endpoint, never recomputed or re-frozen",
        "epsilon1=0 is a source-backed branch choice, not a uniqueness theorem",
        "a coefficient with no accessible source equation is never a live ceiling"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
