import json
import numpy as np
from scripts.r126.verify_sources import DOC

def test_budget_evidence():
    x=json.loads((DOC/"C6_BUDGET.json").read_text())
    assert len(x["runs"])==36
    assert max(v["relative_sky"] for v in x["prior_R125_baseline"].values())<1e-6
    for v in x["runs"].values():
        assert v["closure_relative"]<2e-8
        assert v["min_D_eigenvalue"]>=-1e-9
        assert v["max_constraint"]<1e-9
    assert max(v["relative_generator_gap"] for v in x["local_collision_audit"].values())<1e-12

def test_adjoint_evidence():
    x=json.loads((DOC/"C7_ADJOINT.json").read_text())
    assert set(x["runs"])=={"VII0_m0","VIIh_m1","VIIh_m2"}
    for v in x["runs"].values():
        assert v["duality_relative"]<1e-6
        assert v["adjoint_transfer_relative"]<2e-6
        assert v["projection_relative"]<2e-6
        # Independent centered FD is a finite-width check, not exact differentiation.
        assert v["fd"][1]["relative_error"]<3e-3 or v["fd"][1]["absolute_error"]<1e-8

def test_native_and_spectra():
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert x["counts"]=={"base":4,"fine":4,"oracle":36}
    assert x["smoke_LOS_byte_replay"]
    assert set(x["native"])=={"VIIh_m1","VIIh_m2"}
    for v in x["native"].values():
        assert v["fine"]["relative_signed_error"]<2e-4
        assert v["time_error_ratio"]>2.5
    for sector,scales in x["sectors"].items():
        assert set(scales)=={"0","025","05","1"}
        assert all(v["collision_budget_over_initial"]==0 for v in scales["0"]["columns"].values())
        for t in ("025","1"):
            q=scales[t]
            for key in ("state","host","high","normal","radiation"):
                r=q[key]
                assert r["count_above_difference"]==sum(v>r["empirical_op_difference"] for v in r["singular_values"])
        if sector=="VII0_m0":
            for t in scales.values():
                assert t["scalar_B_exact"]["relative_difference"]<.02
                assert t["scalar_B_exact"]["nonpolarization_leak"]<1e-12

def test_audit():
    x=json.loads((DOC/"C9_AUDIT.json").read_text())
    assert (x["budgets_verified"],x["adjoints_verified"],x["native_verified"],x["native_raw_files_verified"])==(36,3,8,32)
