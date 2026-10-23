"""Targeted checks of the retained CMB orbit experiment."""
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation


HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("cmb_orbit", HERE/"orbit.py")
orb=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=orb
SPEC.loader.exec_module(orb)


def test_exact_rotation_and_degenerate_stratum():
    # The bound must survive repeated eigenvalues and a vanishing octupole.
    q=np.diag([2e-7,-1e-7,-1e-7])
    o=np.zeros((3,3,3))
    r=Rotation.from_euler("xyz",[.2,-.3,.5]).as_matrix()
    p=r@q@r.T
    interval=orb.orbit_bounds((None,q,o),(None,p,o))
    assert 0<=interval["lower"]<=interval["feasible_upper"]
    assert interval["lower"]<1e-12
    assert interval["feasible_upper"]<1e-9
    assert interval["SO3_orthogonality_residual"]<1e-12
    assert interval["SO3_determinant_residual"]<1e-12


def test_retained_result_contract():
    d=json.loads((HERE/"RESULT.json").read_text())
    assert d["packet_id"]==orb.PACKET and d["input_identity"]==orb.INPUT_ID
    assert len(d["bundles"])==60 and len(d["comparisons"])==57
    assert len(d["processing_support"])==9
    assert d["p_value"] is None and d["matched_total_field_law"]=="ABSENT"
    assert d["equal_scalar_phase_control"]["C2_C3_relative_power_residual"]<1e-12
    assert d["equal_scalar_phase_control"]["orbit_interval"]["lower"]>0
    for row in d["comparisons"]:
        bound=row["interval"]
        assert 0<=bound["lower"]<=bound["feasible_upper"]
        assert bound["SO3_orthogonality_residual"]<1e-12
        assert bound["SO3_determinant_residual"]<1e-12
    assert {x["source"] for x in d["bundles"]}=={"hash_pinned_primary","pilot_cached"}
    for row in d["processing_support"]:
        assert len(row["support_plus"])==len(row["support_minus"])==12
        assert row["processing_set_size"]==5
