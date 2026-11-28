import json
from scripts.r128.verify_sources import DOC

def test_shape_spectra():
    x=json.loads((DOC/"C6_SPECTRA.json").read_text())
    assert len(x["sectors"])==6
    for v in x["sectors"].values():
        for m in v["metrics"].values():
            assert len(m["tail_locked"]["full"]["singular_values"])==3
            assert m["late_swap"]["full"]["count_above_difference"]==1
            assert m["tail_locked"]["full"]["count_above_difference"]==3
            for t in m.values():
                for r in t.values():assert r["max_depth_residual"]<1e-10
def test_direct_shapes():
    x=json.loads((DOC/"C7_SHAPES.json").read_text())
    assert len(x["runs"])==4
    for v in x["runs"].values():
        assert abs(v["depth_residual"])<2e-12
        assert v["fd"]["h03"]["separation_over_baseline"]>1e-5
        assert v["fd"]["h03"]["relative_to_tangent"]<.002
        for r in v["visibility"].values():
            assert abs(r["tau_difference"])<2e-11
            assert abs(r["mass"]-r["exact_mass"])<1e-10
    assert max(v["relative_error"] for v in x["scalar_B_control"])<2e-5
def test_native_audit():
    x=json.loads((DOC/"C8_NATIVE.json").read_text());assert x["counts"]=={"base":8,"fine":8} and x["smoke_LOS_byte_replay"]
    for v in x["runs"].values():
        assert v["native"]["fine"]["relative_to_same_width_oracle"]<.01
    a=json.loads((DOC/"C9_AUDIT.json").read_text())
    assert (a["spectra_verified"],a["shape_npz_verified"],a["native_verified"],a["native_raw_verified"])==(108,4,16,64)
