"""PR-222 runner: stochastic bulk->tilt bridge + five-axis CAS status."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_bulk_bridge import fisher_rank, recover, single_window_cannot_identify  # noqa: E402
SPEC = REPO/"docs/research_program/revival/pr222_spec.yaml"
CARD = REPO/"docs/generated/pr222_result_card.json"
CAS_CONTRACT = REPO/"docs/generated/pr222_cas/CAS_CONTRACT_PR222_BRIDGE.json"
CAS_AXIS_RESULTS = tuple(
    REPO / f"docs/generated/pr222_cas/axis_result_{axis}.json"
    for axis in ("wolfram_xact", "sympy", "sage_singular", "lean", "rocq")
)
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _cas():
    csha = _sha(CAS_CONTRACT)
    command = [
        sys.executable,
        "-B",
        ".agent-harness/scripts/cas_gate.py",
        "adjudicate",
        "--contract",
        str(CAS_CONTRACT.relative_to(REPO)),
        "--results",
        *(str(path.relative_to(REPO)) for path in CAS_AXIS_RESULTS),
        "--historical-replay",
    ]
    completed = subprocess.run(
        command,
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        diagnostic = json.loads(completed.stdout)
    except json.JSONDecodeError:
        diagnostic = {}
    valid_diagnostic = (
        completed.returncode == 2
        and diagnostic.get("aggregate_status") == "CAS_BLOCKED"
        and diagnostic.get("claim_promotion_cas_eligible") is False
        and diagnostic.get("evidence_origin") == "stored_axis_result_envelopes"
    )
    return {"contract":"docs/generated/pr222_cas/CAS_CONTRACT_PR222_BRIDGE.json","contract_sha256":csha,
            "contract_hash_matches_adjudication":(
                valid_diagnostic and diagnostic.get("contract_sha256") == csha),
            "aggregate":"CAS_BLOCKED","required_axes":diagnostic.get("required_axes", []),
            "axis_statuses":diagnostic.get("axis_statuses", {}),
            "kernel_independent_lineages":["lean","rocq"]}
def build_payload():
    fr = fisher_rank(); rec = recover(); single = single_window_cannot_identify(); cas=_cas()
    ranks = {"multi_window_rank": fr["multi_window_rank"], "single_window_rank": fr["single_window_rank"]}
    ok = (ranks["multi_window_rank"]==3 and ranks["single_window_rank"]==1
          and rec["recovers"] and single and cas["aggregate"]=="CAS_5AXIS_PASS"
          and cas["contract_hash_matches_adjudication"])
    terminal = "BULK_TO_TILT_BRIDGE_RANK3_CERTIFIED_CAS_5AXIS_PASS" if ok else "BLOCKED_BRIDGE_GATE_FAILURE"
    return {"schema":"htt.pr222.result_card.v1","pr_id":"PR-222",
      "metadata":{"owner":"COMMON","spec_sha256":_sha(SPEC),"cross_references":["PR-145","PR-146"],
        "claim_level":{"scheme":"roadmap_rescue_v1","level":"C1"},"public_use":False,
        "readiness_state":"EVIDENCE_READY","independence_gate":"OPEN",
        "generating_command":"env PYTHONHASHSEED=0 venv/bin/python -B scripts/codex_harness/run_pr222_bridge.py --write"},
      "result":{"ranks":ranks,"gls_recovery":rec,"single_window_cannot_identify":single,"cas_status":cas},
      "terminal":terminal,
      "forbidden_claims_reaffirmed":[
        "a single bulk-flow amplitude cannot point-identify the 3-D homogeneous tilt",
        "homogeneous tilt is identifiable only through a declared multi-window field bridge",
        "this is pre-solver stochastic-operator mechanics; no native transfer is claimed"]}
def _render(o): return (json.dumps(o,sort_keys=True,indent=1)+"\n").encode()
def main(argv=None):
    ap=argparse.ArgumentParser(); m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true")
    a=ap.parse_args(argv); p=build_payload()
    if a.write: CARD.write_bytes(_render(p)); print(f"wrote {CARD.name}; terminal={p['terminal']}"); return 0
    ok=CARD.exists() and CARD.read_bytes()==_render(p)
    print(json.dumps({"mode":"check","ok":ok,"read_only":True,"terminal":p["terminal"]},sort_keys=True)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
