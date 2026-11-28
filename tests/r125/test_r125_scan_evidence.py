import json
from scripts.r125.verify_sources import DOC
def test_actual_initial_response():
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert x["counts"]=={"base":12,"fine":12,"oracle_solves":24}
    assert x["smoke_LOS_byte_replay"]
    assert x["max_heldout_sky_relative"]<1e-6
    for key,v in x["sectors"].items():
        assert v["prior_shear_relative"]<1e-6
        assert v["tight_max_constraint"]<1e-9
        assert v["native"]["fine"]["relative_signed_error"]<1e-4
        assert v["native"]["time_error_ratio"]>3
        for f in v["frames"].values():
            for k in ("full","high"):
                z=f[k]
                assert z["count_above_empirical_scale"]==sum(s>z["empirical_scale"] for s in z["singular_values"])
        if key.endswith("m0") and key.startswith("VII0"):
            assert v["frames"]["host"]["full"]["count_above_empirical_scale"]<=4
            assert v["frames"]["host"]["high"]["count_above_empirical_scale"]<=3
        assert max(v["frames"]["radiation"]["dipole_column_norms"].values())<1e-12
def test_actual_audit():
    x=json.loads((DOC/"C9_AUDIT.json").read_text())
    assert x["verified_runs"]==24
    assert x["native_raw_files_verified"]==96
    assert x["oracle_npz_verified"]==24
    assert all(not v["failures"] for v in x["runs"].values())
