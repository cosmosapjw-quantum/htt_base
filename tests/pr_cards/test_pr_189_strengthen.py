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
CARD = REPO/"docs/generated/pr189_result_card.json"
SPEC = REPO/"docs/research_program/strengthening/pr189_spec.yaml"
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
def test_five_axis_cas():
    cas=_card()["result"]["cas_status"]
    assert cas["aggregate"]=="CAS_5AXIS_PASS"
    assert cas["contract_hash_matches_adjudication"] is True
    assert set(cas["axis_statuses"])=={"wolfram_xact","sympy","sage_singular","lean","rocq"}
    assert all(v=="PASS" for v in cas["axis_statuses"].values())
def test_byte_stable():
    p=subprocess.run([str(REPO/"venv/bin/python"),"-B",str(REPO/"scripts/codex_harness/run_pr189_joint.py"),"--check"],cwd=REPO,capture_output=True,text=True,timeout=300,env={"PYTHONHASHSEED":"0","PATH":"/usr/bin:/bin","OPENBLAS_NUM_THREADS":"4"})
    assert p.returncode==0, p.stdout+p.stderr
    assert json.loads(p.stdout.strip().splitlines()[-1])["ok"] is True
