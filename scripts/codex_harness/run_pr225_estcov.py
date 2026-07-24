"""PR-225 runner: estimated-cov partial-ID + anytime e-value (extends PR-200/197)."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_estcov_evalue import hartlap_stress, evalue_anytime  # noqa: E402
SPEC = REPO/"docs/research_program/revival/pr225_spec.yaml"
CARD = REPO/"docs/generated/pr225_result_card.json"
PR200 = REPO/"docs/generated/pr200_result_card.json"
PR197 = REPO/"docs/generated/pr197_result_card.json"
REQUIRED_CROSSREFS = {
    "pr200_terminal": "PARTIAL_ID_COVERAGE_CALIBRATED_POINT_CI_UNDERCOVERS",
    "pr197_terminal": "CLUSTER_EXACT_RANK_VERIFIED_NAIVE_LABEL_REFUSED",
}
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _xref():
    x={}
    if PR200.exists():
        c=json.loads(PR200.read_text()); x["pr200_terminal"]=c.get("terminal")
    if PR197.exists():
        c=json.loads(PR197.read_text()); x["pr197_terminal"]=c.get("terminal")
    return x
def build_payload():
    h=hartlap_stress(); ev=evalue_anytime(); xref=_xref()
    ok = (h["raw_inflated"] and h["corrected_calibrated"]
          and ev["merged_mean_le_one"] and ev["tails_within_markov"] and ev["ville_holds"]
          and xref == REQUIRED_CROSSREFS)
    terminal = "ESTCOV_PARTIAL_ID_ANYTIME_EVALUE_CALIBRATED" if ok else "BLOCKED_ESTCOV_GATE_FAILURE"
    return {"schema":"htt.pr225.result_card.v1","pr_id":"PR-225",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),"cross_references":["PR-200","PR-197"],
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr225_estcov.py --write"},
      "result":{"hartlap_stress":h,"anytime_evalue":ev,"crossref":xref},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "the Hartlap-uncorrected precision matrix inflates chi^2; corrected calibrates it",
        "a merged e-value has mean <= 1 and obeys Ville's inequality under optional stopping",
        "partial-ID coverage/cluster rank cross-reference PR-200/PR-197"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
