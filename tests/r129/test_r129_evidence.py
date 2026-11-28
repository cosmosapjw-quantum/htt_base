import json
from scripts.r129.verify_sources import DOC

def test_nested_evidence():
    x=json.loads((DOC/"C6_NESTED.json").read_text())
    assert len(x["runs"])==12 and sum(x["counts_by_node_group"])==2981
    assert max(v["coarse_window_relative"] for v in x["runs"].values() if v["L"]==20)<2e-6

def test_profile_evidence():
    x=json.loads((DOC/"C7_PROFILE.json").read_text());assert x["profile_count"]==432
    for key,v in x["sectors"].items():
        for b in v["bands"].values():
            for m in b["metrics"].values():
                for q in m.values():
                    p=q["profiles"]["factor10"]
                    assert p["rank_comparable"]
                    assert p["retained_fraction"]<=1+1e-10
                    assert p["orthogonality"]<1e-10
    q=x["sectors"]["VII0_m0"]["bands"]["full"]["metrics"]["M_tau"]["16"]["profiles"]["factor10"]
    assert q["count_above_difference"]==0 and q["retained_fraction"]<1e-12

def test_direct_and_native_evidence():
    x=json.loads((DOC/"C7_DIRECT.json").read_text())
    assert x["counts"]=={"directional_tangents":2,"native_case_FD_solves":8,"compensation_FD_solves":8}
    for v in x["compensation"].values():
        assert v["initial_relative_shift"]<=.05+1e-14
        assert v["raw_fd_error_over_raw"]<.005 and v["comp_fd_error_over_raw"]<.005
    for v in x["native_cases"].values():assert v["fd"]["h03"]["relative_to_tangent"]<.002
    n=json.loads((DOC/"C8_NATIVE.json").read_text())
    assert n["counts"]=={"base":8,"fine":8} and n["smoke_LOS_byte_replay"]
    for v in n["runs"].values():assert v["native"]["fine"]["relative_to_same_width_oracle"]<.02
def test_audit():
    x=json.loads((DOC/"C9_AUDIT.json").read_text());assert (x["nested_verified"],x["profiles_verified"],x["direct_verified"],x["native_verified"],x["native_raw_verified"])==(12,432,4,16,64)
