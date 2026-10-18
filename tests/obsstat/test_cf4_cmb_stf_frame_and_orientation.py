"""Frames must be physically compared after J2000 ICRS -> Planck Galactic rotation."""
import numpy as np
import pytest
from obsstat.cf4_cmb_stf_frame_and_orientation import (
   icrs_to_galactic_rotation,stf_tensor_cosine,stf_principal_axis_separation
)


def test_ICRS_to_GAL_axes_matches_IAU_pole_and_is_orthogonal():
    R=icrs_to_galactic_rotation()
    expected=np.array([
      [-.0548756577,-.873437052,-.4838350736],
      [.494109437,-.4448297212,.746982184],
      [-.86766613756,-.1980763373,.4559838137]])
    np.testing.assert_allclose(R,expected,atol=1e-8,rtol=0)
    np.testing.assert_allclose(R.T@R,np.eye(3),atol=5e-14)
    assert np.linalg.det(R)==pytest.approx(1.,abs=5e-14)


def test_common_SO3_rotation_keeps_stf_cosine_and_axis_separation():
    from scipy.spatial.transform import Rotation
    R=Rotation.from_euler('yxz',[37,19,60],degrees=True).as_matrix()
    A=np.diag([1.,-1.,0.])
    B=np.array([[.3,.2,.1],[.2,-.4,.15],[.1,.15,.1]])
    u=stf_tensor_cosine(A,B)
    v=stf_tensor_cosine(R@A@R.T,R@B@R.T)
    assert v==pytest.approx(u,abs=1e-14)
    a=stf_principal_axis_separation(A,B)
    b=stf_principal_axis_separation(R@A@R.T,R@B@R.T)
    assert a==pytest.approx(b,abs=1e-13)


def test_source_norm_and_symmetry_required():
    with pytest.raises(ValueError):
        stf_tensor_cosine(np.eye(3),np.eye(3))
    with pytest.raises(ValueError):
        stf_principal_axis_separation(np.zeros((3,3)),np.zeros((3,3)))
