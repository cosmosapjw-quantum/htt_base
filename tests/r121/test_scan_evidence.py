import json
import numpy as np
from scripts.r121.verify_sources import DOC

def test_real_scan_and_conditioning():
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert x["counts"]=={"base":26,"fine":20}
    for n in ("03","01"):
        v=x["weak"]["VI"][n]
        assert abs(v["zero_log_slope_from_previous"]-2)<.01
    for v in x["weak"]["VII"].values():assert v["norms"]["zero"]<x["shape_floor"]
    t=x["tangent"]
    a=t["fine"];g=np.asarray(a["grad_log_amplitude"]);G=np.asarray(a["shape_gram"])
    np.testing.assert_allclose(a["absolute_gram"],a["amplitude"]**2*(G+np.outer(g,g)),rtol=1e-10,atol=1e-15)
    for d in (t["scaled_shape_time"],t["scaled_shape_width"],t["fixed_reference_projection_time"],t["scaled_absolute_time"]):
        for v in d["errors"].values():assert v["scaled_operator"]<=v["scaled_frobenius"]+1e-14
    assert x["external_aniclass"]["exit_code"]==0 and x["external_aniclass"]["alm"]["positive_m"]==2
    assert x["tensor_support"]["base_hi"]["relative_off_m2"]<.01
    assert x["tensor_support"]["fine_lo"]["relative_off_m2"]<.01

def test_raw_audit():
    x=json.loads((DOC/"C9_AUDIT.json").read_text())
    assert x["verified_runs"]==46 and x["native_raw_files_verified"]==230
    assert x["external_raw_files_verified"]>=4
    for v in x["runs"].values():assert v["failures"]==[]
