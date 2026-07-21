"""Contract gate for the v11 external report: byte-stable, quarantine + meta-dev clean."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
TEX = REPO/"external_audit_research_report_20260722_v11/external_audit_research_report_v11.tex"

def test_check_byte_stable():
    r = subprocess.run([sys.executable, "-B", "scripts/build_external_audit_report_v11.py", "--check"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr

def test_no_quarantine_trap_tokens():
    t = TEX.read_text()
    for trap in ("340.7", "4.07e-07", "94 km/s", "405 km"):
        assert trap not in t, trap

def test_no_meta_dev_tokens():
    t = TEX.read_text().lower()
    for banned in ("subagent", "adversarial", "claim-gate", "workflow",
                   "promotion queue", "readiness_state", "checkpoint cp-"):
        assert banned not in t, banned

def test_tier_ledger_and_frozen_anchor_present():
    t = TEX.read_text()
    assert "3.3789222980376e-13" in t          # frozen W2_max unchanged
    assert "394584" in t                        # CAS-certified bridge determinant
    assert t.count("\\code{T-") + t.count("\\code{M-") + t.count("\\code{D-") >= 25
