"""PR-215 runner: joint comparator interval vs product box (RESCUE->PR-189)."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_joint_comparator import analysis, grid_joint_interval, joint_interval_exact  # noqa: E402
from fractions import Fraction as Fr  # noqa: E402
SPEC = REPO/"docs/research_program/revival/pr215_spec.yaml"
CARD = REPO/"docs/generated/pr215_result_card.json"
PR189 = REPO/"docs/generated/pr189_result_card.json"
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _xref():
    c = json.loads(PR189.read_text()); r = c.get("result",{})
    cas = r.get("cas_status",{})
    return {"pr189_terminal": c.get("terminal"),
            "pr189_cas": cas.get("aggregate"),
            "pr189_joint_subset_of_product": r.get("coupled_fixture",{}).get("joint_subset_of_product")}
def build_payload():
    an = analysis()
    jlo, jhi = joint_interval_exact()
    glo, ghi = grid_joint_interval()
    grid_agrees = abs(glo-float(jlo))<1e-9 and abs(ghi-float(jhi))<1e-9
    xref = _xref()
    ok = (an["joint_subset_of_product"] and an["strictly_narrower"]
          and an["coupling_kills_t_dependence"] and grid_agrees
          and xref["pr189_cas"]=="CAS_5AXIS_PASS" and xref["pr189_joint_subset_of_product"])
    terminal = "JOINT_COMPARATOR_STRICTLY_NARROWER_PR189_CERTIFIED" if ok else "BLOCKED_JOINT_GATE_FAILURE"
    return {"schema":"htt.pr215.result_card.v1","pr_id":"PR-215",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),"disposition":"LITERAL_RESCUE",
        "cross_references":["PR-189"],"claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},
        "public_use":False,"readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr215_joint.py --write"},
      "result":{"coupled_manifold_analysis":an,
        "grid_second_lineage":{"grid_interval":[glo,ghi],"agrees_with_exact":grid_agrees},
        "pr189_crossref":xref},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "the product box is a corollary; a coupled manifold gives a strictly narrower joint set",
        "a marginal-box endpoint is never reported sharp when the joint interval is narrower",
        "the coupling can null a component (t drops out of x_C), never inflate the set"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True))
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
