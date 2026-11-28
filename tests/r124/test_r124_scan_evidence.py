import json
from scripts.r124.verify_sources import DOC
def test_actual_constrained_response():
    x=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert x["counts"]=={"base":16,"fine":8,"normal":8,"tensor":4}
    assert x["smoke_LOS_byte_replay"]
    for key,v in x["sectors"].items():
        assert v["fine_host"]["full_relative"]<3e-5
        assert v["fine_normal"]["full_relative"]<3e-5
        assert v["time_error_ratio"]>3.8
        assert v["seed_difference_relative"]<1e-6
        assert v["oracle"]["max_codazzi"]<1e-11
        assert v["velocities"]["initial_host_beta"]["absolute_error"]<1e-10
        assert v["frame"]["native_high_delta"]<1e-8
        assert v["frame"]["doppler_abs_error"]<1e-9
        assert x["oracle_convergence"][key]["L12"]<1e-6
        if key.endswith("m0"):assert v["oracle"]["high_channel_norms"][2]<1e-14
    for v in x["tensor_refinement"].values():
        assert v["relative_6400"]<2e-5
        assert v["error_ratio"]>3.8
def test_actual_audit():
    x=json.loads((DOC/"C9_AUDIT.json").read_text())
    assert x["verified_runs"]==36
    assert x["native_raw_files_verified"]==144
    assert x["oracle_histories_verified"]==16
    assert all(not v["failures"] for v in x["runs"].values())
