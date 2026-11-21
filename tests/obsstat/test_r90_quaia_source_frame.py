"""R90 actual Quaia source/chart identity: existing joined rows, official maps."""
import json
from pathlib import Path
import numpy as np
from scripts.r90 import qualify_quaia_frame as q

def test_written_qualification_replays_identical_source():
    j=q.evaluate()
    assert j["n_existing_source_rows_checked"]==692154
    assert j["matching_ra_dec_to_preexisting_pixel_fraction"]==1.0
    assert j["G20.0_join_selection_max_abs_error"]<=1e-12
    assert "ICRS" in j["coordinate_result"]
    assert j["G20.0_matched_rows_all_bright"]
    assert not j["G20.5_matches_old_G20.0_join"]
    assert j["G20.5_minus_old_G20.0_median_abs"]>0.005

def test_qualification_byte_identical_to_receipt():
    original=(q.OUT).read_bytes()
    candidate=json.dumps(q.evaluate(),indent=2,ensure_ascii=False).encode()+b"\n"
    assert original==candidate

def test_qualification_is_not_cosmological_null():
    r=json.loads(q.OUT.read_text())
    assert r["physical_Pi"] is None
    assert r["physical_GF"] is None
    assert not r["native_boltzmann_used"]
    assert "UNCHECKED" in r["status"]
