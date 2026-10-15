import numpy as np
import pytest

from obsstat.cf4_method_window_calibration import (
    Cf4CalibrationDomainError,method_response,calibration_propagation,
    paired_method_decomposition,
)
from obsstat.htt_hubble_depth_window import K_LOG


def toy():
    method=np.asarray(["FP","FP","TF","TF"])
    # Bin1 80% FP, bin2 20% FP; each source appears in both windows.
    weights=np.asarray([[.4,.4,.1,.1],[.1,.1,.4,.4]])
    return weights,method


def test_exact_method_fraction_and_jacobian():
    L,m=toy()
    q=method_response(L,m)
    assert q["names"]==["FP","TF"]
    np.testing.assert_allclose(q["weighted_fractions"],[[.8,.2],[.2,.8]])
    np.testing.assert_allclose(q["logH_jacobian_mag_inv"],
                               -K_LOG*np.array([[.8,.2],[.2,.8]]))


def test_exact_calibration_shift_of_logh_nuisance():
    L,m=toy()
    q=method_response(L,m)
    sh=np.array([.1,-.04])
    shift=q["logH_jacobian_mag_inv"]@sh
    manual=np.asarray([
        -K_LOG*(.8*.1+.2*(-.04)),
        -K_LOG*(.2*.1+.8*(-.04))])
    np.testing.assert_allclose(shift,manual,atol=1e-15)
    assert np.max(np.abs(shift))>0


def test_common_method_shift_exactly_cancels_in_shell_difference():
    L,m=toy()
    r=paired_method_decomposition(L,m,0,1)
    assert r["common_offset_response"]==pytest.approx(0,abs=1e-15)
    p=calibration_propagation(method_response(L,m),
           magnitude_covariance=np.ones((2,2))*.05**2)
    assert p["pairwise_contrast_std_logH"][0,1]==pytest.approx(0,abs=1e-10)


def test_box_envelope_and_independent_calibration_covariance():
    L,m=toy()
    p=calibration_propagation(method_response(L,m),
         magnitude_bounds=np.full(2,.1),
         magnitude_covariance=np.eye(2)*.05**2)
    assert p["max_abs_shift_logH_pairwise_contrast"][0,1]==pytest.approx(
        K_LOG*1.2*.1,rel=1e-14)
    assert p["pairwise_contrast_std_logH"][0,1]==pytest.approx(
        K_LOG*.05*np.sqrt(.72),rel=1e-13)
    v=np.array([1.,-1.])
    cov=p["propagated_logH_covariance"]
    assert v@cov@v>=0


def test_changed_method_basis_order_keeps_physical_response():
    L,m=toy()
    a=method_response(L,m)
    b=method_response(L,m,declared_methods=["TF","FP"])
    np.testing.assert_allclose(a["weighted_fractions"],b["weighted_fractions"][:,::-1])
    aa=calibration_propagation(a,magnitude_bounds=[.07,.12])
    bb=calibration_propagation(b,magnitude_bounds=[.12,.07])
    np.testing.assert_allclose(aa["max_abs_shift_logH_pairwise_contrast"],
                              bb["max_abs_shift_logH_pairwise_contrast"])


def test_input_weight_and_covariance_rejection():
    L,m=toy()
    with pytest.raises(Cf4CalibrationDomainError,match="normalized"):
        method_response(L+.1,m)
    with pytest.raises(Cf4CalibrationDomainError,match="categories"):
        method_response(L,m,declared_methods=["BAD"])
    with pytest.raises(Cf4CalibrationDomainError,match="box"):
        calibration_propagation(method_response(L,m),magnitude_bounds=[-.1,.1])
    with pytest.raises(Cf4CalibrationDomainError,match="PSD"):
        calibration_propagation(method_response(L,m),
                              magnitude_covariance=np.diag([1.,-1.]))


def test_no_sample_duplication_claim_from_overlapping_windows():
    L,m=toy()
    q=method_response(L,m)
    assert np.any((L[0]>0)&(L[1]>0))
    assert np.allclose(q["weighted_fractions"].sum(axis=1),1.)
    # Both rows share the SAME four source observations.
    base_errors=np.full(len(m),.2**2)
    cov=(L*base_errors[None,:])@L.T
    assert cov[0,1]>0



def test_rank_one_common_mode_stable_contrast_stays_below_roundoff_on_asymmetric_windows():
    # Represents the real CF4 near/far source shares in the published 35,970-group subset.
    frac=np.asarray([[.159896,.150420,.161671,.528013],
                     [.937693,.000974,.058624,.002710]])
    frac/=frac.sum(axis=1)[:,None]
    p=calibration_propagation(
        {"names":["FP","OTHER","SN","TF"],"weighted_fractions":frac},
        magnitude_covariance=.05**2*np.ones((4,4)))
    assert p["pairwise_contrast_std_logH"][0,1] < 1e-16
