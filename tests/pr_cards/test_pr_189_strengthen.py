"""PR-189 gates: joint feasible-set support theorem (R3-CAS, H05/H06)."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from fractions import Fraction
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
import pytest  # noqa: E402
from common.joint_feasible_set import analyze, exact_support, InfeasibleError  # noqa: E402
from scripts.codex_harness import run_pr189_joint as runner  # noqa: E402
CARD = REPO/"docs/generated/pr189_result_card.json"
SPEC = REPO/"docs/research_program/strengthening/pr189_spec.yaml"
RUNNER = REPO/"scripts/codex_harness/run_pr189_joint.py"
def _card(): return json.loads(CARD.read_text())
def test_spec_and_terminal():
    c=_card()
    assert c["metadata"]["spec_sha256"]==hashlib.sha256(SPEC.read_bytes()).hexdigest()
    assert c["metadata"]["public_use"] is False
    assert c["metadata"]["independence_gate"]=="OPEN"
    assert c["terminal"]=="JOINT_IDENTIFIED_SET_CERTIFIED_CAS_5AXIS_PASS"
def test_coupled_strict_and_highs():
    r=_card()["result"]["coupled_fixture"]
    assert r["joint_subset_of_product"] and r["strict_narrower"]
    assert r["joint_interval"]==["0","1"] and r["product_interval"]==["0","2"]
    assert r["highs_cross_check_agrees"] is True
def test_factorized_corollary():
    assert _card()["result"]["factorized_fixture"]["joint_equals_product"] is True
def test_empty_and_witnesses():
    r=_card()["result"]
    assert r["empty_system_classified"] is True
    assert r["random_witnesses_inside_certified_interval"] is True
    # independent: an infeasible system raises
    A=[[1,0],[-1,0]]; b=[0,-1]
    with pytest.raises(InfeasibleError):
        exact_support([Fraction(1),Fraction(0)],[[Fraction(x) for x in r] for r in A],[Fraction(x) for x in b])
def test_stored_five_axis_cas_is_diagnostic_only():
    cas=runner._cas_status()
    assert cas["aggregate"]=="CAS_BLOCKED"
    assert cas["historical_aggregate"]=="CAS_5AXIS_PASS"
    assert cas["stored_cas_diagnostic_only"] is True
    assert cas["claim_promotion_cas_eligible"] is False
    assert cas["contract_hash_matches_adjudication"] is True
    assert set(cas["axis_statuses"])=={"wolfram_xact","sympy","sage_singular","lean","rocq"}
    assert all(v=="PASS" for v in cas["axis_statuses"].values())

def test_historical_card_preserves_pre_ma04_cas_label():
    cas=_card()["result"]["cas_status"]
    assert cas["aggregate"]=="CAS_5AXIS_PASS"
    assert _card()["terminal"]=="JOINT_IDENTIFIED_SET_CERTIFIED_CAS_5AXIS_PASS"

def test_current_check_blocks_without_live_parent_execution():
    p=subprocess.run([sys.executable,"-B",str(RUNNER),"--check"],cwd=REPO,capture_output=True,text=True,timeout=300,env={"PYTHONHASHSEED":"0","PATH":"/usr/bin:/bin","OPENBLAS_NUM_THREADS":"4"})
    assert p.returncode==1, p.stdout+p.stderr
    result=json.loads(p.stdout.strip().splitlines()[-1])
    assert result["ok"] is False
    assert result["terminal"]=="BLOCKED_JOINT_SET_GATE_FAILURE"

def test_write_refuses_to_overwrite_historical_card():
    before=hashlib.sha256(CARD.read_bytes()).hexdigest()
    p=subprocess.run([sys.executable,"-B",str(RUNNER),"--write"],cwd=REPO,capture_output=True,text=True,timeout=300)
    assert p.returncode==2
    assert "refusing to overwrite" in p.stderr
    assert hashlib.sha256(CARD.read_bytes()).hexdigest()==before
