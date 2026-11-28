import json
from pathlib import Path
import numpy as np
from scripts.r120.native_scan import DOC

def test_actual_results_and_strata():
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert [x["by_mode"][n]["validated_scoped"] for n in ("base","fine","angular")]==[63,24,4]
    assert len(x["representative_pairs"])==66
    assert set(x["excluded_from_shape"])=={"FLRW","VIIh_zero_shear"}
    for n in ("VIh","VIIh"):
        y=x["local"][n];assert y["status"]=="computed_finite_chart"
        for key in ("base_04","base_02","fine_02"):
            q=y[key];g=np.array(q["gram"]);s=np.array(q["singular_values"])
            np.testing.assert_allclose(g,g.T,rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(np.linalg.eigvalsh(g)[::-1],s*s,rtol=1e-7,atol=1e-10)
            assert q["nuisance_rank"]==4
    for p in x["representative_pairs"]:
        assert 0<=p["lower"]<=p["sampled_upper_256"]+2e-7
        assert p["sampled_upper_256"]<=p["sampled_upper_64"]+2e-7<=p["identity_upper"]+4e-7
    z=x["zero_shear"]
    assert z["VIIh"]["zero"]["norm"]<x["numeric_shape_floor"]
    assert z["VIh"]["zero"]["norm"]>1e-3

def test_archive_receipts():
    a=json.loads((DOC/"C9_RAW_AUDIT.json").read_text())
    assert a["verified_runs"]==91 and a["verified_raw_files"]==455
    assert a["max_rec_post_stop_drift"]==0
