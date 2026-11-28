import json
import numpy as np
from scripts.r127.verify_sources import DOC

def test_tangent_population_and_prior():
    x=json.loads((DOC/"C6_TANGENT.json").read_text())
    assert len(x["runs"])==12
    assert max(v["max_constraint"] for v in x["runs"].values())<1e-8
    assert max(v["prior_R126_sky_relative"] for v in x["runs"].values() if v["L"]==20)<2e-6

def test_goal_kernel_evidence():
    x=json.loads((DOC/"C7_KERNEL.json").read_text())
    assert len(x["runs"])==6
    for r in x["runs"].values():
        assert r["adjoint_tangent_relative"]<2e-5
        assert r["quadrature_group_abs"]<1e-8
        assert r["duality_abs"]<1e-7
        assert r["tau_gap_max"]<1e-8
        assert np.min(r["loss"])>=-1e-10
        if "prior_R126_global_abs_gap" in r:assert r["prior_R126_global_abs_gap"]<1e-7

def test_native_and_fd_evidence():
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert x["counts"]=={"base":8,"fine":8,"tangent":12,"adjoint":6,"independent_FD_solves":8}
    assert x["smoke_LOS_byte_replay"]
    assert set(x["native"])=={"VIIh_m1","VIIh_m2"}
    for v in x["native"].values():
        assert v["fd"]["h03"]["relative_to_tangent"]<.02
        assert v["fd"]["h01"]["relative_to_tangent"]<.02
        # Derivatives involve two signed stencils; retain finite mismatch.
        assert v["native"]["fine"]["relative_to_matched_fd"]<.02
    for v in x["sectors"].values():
        assert v["tangent_L12_to_L20_relative"]<.01

def test_audit_counts():
    x=json.loads((DOC/"C9_AUDIT.json").read_text())
    assert (x["tangent_verified"],x["kernel_verified"],x["fd_records_verified"],x["native_verified"],x["native_raw_verified"])==(12,6,2,16,64)
