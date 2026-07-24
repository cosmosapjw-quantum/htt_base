"""PR-200 gates: calibrated partial-ID coverage (R2, H14)."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.partial_id_coverage import coverage_mc  # noqa: E402
from scripts.codex_harness import run_pr200_coverage as runner  # noqa: E402
CARD=REPO/"docs/generated/pr200_result_card.json"; SPEC=REPO/"docs/research_program/strengthening/pr200_spec.yaml"
def _card(): return json.loads(CARD.read_text())
def test_spec_and_terminal():
    c=_card()
    assert c["metadata"]["spec_sha256"]==hashlib.sha256(SPEC.read_bytes()).hexdigest()
    assert c["metadata"]["public_use"] is False and c["metadata"]["independence_gate"]=="OPEN"
    assert c["terminal"]=="PARTIAL_ID_COVERAGE_CALIBRATED_POINT_CI_UNDERCOVERS"
def test_im_covers_all_regimes():
    g=_card()["result"]["im_coverage_grid"]
    assert g["all_cells_pass"] is True
    assert g["worst_cp_lower_99"] >= g["lower_threshold"]
    assert g["publication_budget"]["n_dgp"]==25
def test_point_ci_undercovers():
    pg=_card()["result"]["point_gaussian_undercoverage"]
    assert pg["undercovers"] is True and pg["monotone_worse_with_width"] is True
    assert pg["worst_coverage"] < 0.94
def test_mesh_and_pseudotrue():
    r=_card()["result"]
    assert r["mesh_stability"]["stable"] is True
    assert r["pseudotrue_never_empty"]["never_empty"] is True

def test_pseudotrue_gate_observes_crossings_and_interval_validity():
    result=coverage_mc(
        half_width=0.05, sigma=3.0, alpha=0.05, reps=2000, seed=11, method="im")
    assert result["crossing_samples"] > 0
    assert result["invalid_intervals"] == 0

def test_pseudotrue_gate_rejects_an_unexercised_crossing_branch(monkeypatch):
    monkeypatch.setattr(
        runner,
        "coverage_mc",
        lambda **kwargs: {
            "coverage": 1.0,
            "crossing_samples": 0,
            "invalid_intervals": 0,
        },
    )
    assert runner._pseudotrue_never_empty()["never_empty"] is False

def test_im_beats_point_ci_independently():
    im=coverage_mc(half_width=3.0,sigma=1.0,alpha=0.05,reps=8000,seed=7,method="im")
    pg=coverage_mc(half_width=3.0,sigma=1.0,alpha=0.05,reps=8000,seed=7,method="point_gaussian")
    assert im["cp_lower_99"] >= 0.94 and pg["coverage"] < 0.5
def test_byte_stable():
    p=subprocess.run([str(REPO/"venv/bin/python"),"-B",str(REPO/"scripts/codex_harness/run_pr200_coverage.py"),"--check"],cwd=REPO,capture_output=True,text=True,timeout=400,env={"PYTHONHASHSEED":"0","PATH":"/usr/bin:/bin","OPENBLAS_NUM_THREADS":"4"})
    assert p.returncode==0, p.stdout+p.stderr
    assert json.loads(p.stdout.strip().splitlines()[-1])["ok"] is True
