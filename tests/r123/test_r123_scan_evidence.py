import json
from scripts.r123.verify_sources import DOC
def test_actual_curved_response():
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert x["counts"]=={"base":8,"fine":4,"angular":4}
    assert x["smoke_LOS_byte_replay"]
    assert x["flat_I_relative_to_R122_Radau"]<2e-7
    for n,v in x["families"].items():
        assert v["base_seed_difference_relative"]<1e-6
        assert v["fine_lo"]["relative_signed_error"]<1e-4
        assert v["time_error_ratio_to_L20"]>3
        assert v["angular_difference_relative"]<1e-6
        assert v["fine_lo"]["forbidden_m_per_seed_norm"]<1e-7
        assert v["base_hi"]["even_midpoint_norm"]>3*v["base_lo"]["even_midpoint_norm"]
        assert v["oracle_reference"]["B_over_E"]>0
        assert x["oracle_convergence"][n][n+"_L12"]<1e-6
def test_actual_audit():
    x=json.loads((DOC/"C9_AUDIT.json").read_text())
    assert x["verified_runs"]==16
    assert x["native_raw_files_verified"]==64
    assert x["oracle_histories_verified"]==9
    assert all(not v["failures"] for v in x["runs"].values())
