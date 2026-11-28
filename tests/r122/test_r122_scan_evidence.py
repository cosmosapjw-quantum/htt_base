import json
import numpy as np
from scripts.r122.verify_sources import DOC
def test_actual_response():
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert x["counts"]=={"base":13,"fine":16}
    cross=x["crossover"]["base"]
    assert cross["025"]["zero_odd_ratio"]<1<cross["045"]["zero_odd_ratio"]
    assert abs(cross["035"]["zero_odd_ratio"]-1)<.005
    for v in cross.values():
        assert abs(v["signed_squared_gap"]-v["identity_rhs"])<1e-18
        assert .23<v["cosine_zero_odd"]<.25
    y=x["oracle_comparison"]
    for r in y.values():
        assert r["T20_per_seed"][0]<0 and r["E20_per_seed"][0]<0
        assert r["full_signed_relative_error"]<5e-5
        assert r["off_axis_per_seed_norm"]<1e-6
    t=x["tangent"]
    assert t["time_frobenius_3200_6400"]<t["time_frobenius_1600_3200"]
    assert t["width_frobenius"]>=0
    assert np.isclose(np.linalg.norm(t["weak_direction_scaled_coordinates"]),1)
    assert np.isclose(t["weak_direction_signal"],t["scaled_singular_6400"][-1])

def test_audit():
    x=json.loads((DOC/"C9_AUDIT.json").read_text())
    assert x["verified_runs"]==29
    assert x["native_raw_files_verified"]==139
    assert x["oracle_histories_verified"]==2
    assert all(not v["failures"] for v in x["runs"].values())
