"""R80 selected CF4 source identity and mask-geometry tests.

The archived result is deterministic and generated from exact pinned raw source.
The optional source live cross-check runs only if original raw data are accessible.
"""
import json
from pathlib import Path

import numpy as np
import pytest

RESULT=Path("docs/research_program/observational_publication_20261015/R80_SQ_CF4_SOURCE_BINDING_20261120/RESULT.json")
SEL=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
T4=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")


def _data():
    return json.loads(RESULT.read_text())


def test_selected_identity_and_method_status_are_not_confused():
    d=_data()
    assert d["exact_selected_group_count"]==35970
    assert d["original_all_group_count"]==38053
    assert d["excluded_group_count"]==2083
    assert sum(d["selected_method_family_count"].values())==35970
    assert d["selected_group_zero_method_presence_count"]==185
    assert d["selected_methods_with_zero_table3_method_presence"]=={
        "FP":0,"OTHER":185,"SN":0,"TF":0}
    assert d["exact_selected_modulus_max_abs_error"]==0
    assert d["exact_selected_modulus_uncertainty_max_abs_error"]==0
    assert d["selected_v3k_c_to_z_CMB_max_abs_error"]<1e-12


def test_matched_source_mask_is_not_full_table4_mask():
    d=_data()["angular_mask_diagnostics"]
    assert d["full_table4_40_400"]["n"]==31649
    assert d["selected_40_400"]["n"]==31382
    assert d["selected_40_400"]["backend_actual"]["used"]=="fortran_native"
    mask_full=d["full_table4_40_400"]["sharp_even_shear_to_hemispherical_mean_bound"]
    mask_matched=d["selected_40_400"]["sharp_even_shear_to_hemispherical_mean_bound"]
    assert mask_full>0 and mask_matched>0
    assert abs(mask_full-mask_matched)>4e-5
    for key,row in d.items():
        assert abs(row["sharp_even_shear_to_hemispherical_mean_bound"]-
                   row["explicit_matched_bound_saturation"])<2e-13
        assert sum(row["hemisphere_minus_plus_counts"])==row["n"]


@pytest.mark.skipif(not (T4.is_file() and SEL.is_file()),
                    reason="original CF4 external dataset unavailable on this host")
def test_live_original_selected_group_membership_in_pinned_table4():
    with np.load(SEL,allow_pickle=False) as z:
        ids=z["group_id"]
        n=z["n_J2000"]
    lines={int(s[:7]):s for s in T4.read_text().splitlines() if s.strip()}
    assert len(lines)==38053
    assert all(int(g) in lines for g in ids)
    r=np.array([float(lines[int(g)][21:26]) for g in ids])
    source=(r>=40)&(r<400)
    assert source.sum()==_data()["angular_mask_diagnostics"]["selected_40_400"]["n"]
    assert len(set(map(int,ids)))==35970
    assert np.allclose(np.linalg.norm(n,axis=1),1,atol=1e-12)
