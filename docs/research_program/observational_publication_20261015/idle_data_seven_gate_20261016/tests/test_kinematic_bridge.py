import numpy as np
import pytest
from htt_gate_precursors.kinematic_bridge import history_matrix,sky_sample,frame_calibration_design,source_matrix_rank


def test_two_windows_one_constant_boost_tilt_degeneracy():
    F=history_matrix(.2,.9)
    r,_=source_matrix_rank(F)
    assert r==2 and np.linalg.norm(F@np.array([1,-1,0]))<1e-14


def test_observer_aberration_anchor_adds_independent_row():
    F=history_matrix(.2,.9,True)
    assert source_matrix_rank(F)[0]==3
    assert np.linalg.det(F)==pytest.approx(.7)


def test_same_window_injection_never_identifies_history_slope():
    F=history_matrix(.2,.2,True)
    assert source_matrix_rank(F)[0]==2


def test_full_galaxy_pm_still_has_frame_spin_nuisance_degeneracy():
    directions=sky_sample(64,12)
    design=frame_calibration_design(directions)
    assert design.shape==(256,15)
    assert source_matrix_rank(design)[0]==12


def test_quasar_frame_calibration_restores_full_idealized_gradient_rank():
    d=sky_sample(64,12);q=sky_sample(50,201)
    with_q=frame_calibration_design(d,q)
    assert with_q.shape==(256+150,15)
    assert source_matrix_rank(with_q)[0]==15


def test_quasars_only_no_matter_kinematic_gradient():
    d=sky_sample(64,12);q=sky_sample(50,201)
    combined=frame_calibration_design(d,q)
    assert np.max(np.abs(combined[-150:,:9]))==0
    assert np.linalg.matrix_rank(combined[-150:,9:])==6
