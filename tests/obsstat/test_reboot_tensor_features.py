import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from obsstat.reboot_tensor_features import tensors_from_real, tensor_shape_features, feature_vector
from obsstat.planck_lowell_irrep_projection import stf2_to_real_harmonic, stf3_to_real_harmonic
from obsstat.r7_cmb_product_response import stored_to_real


def test_normalization_roundtrip_rotation_and_parity():
    a=np.random.default_rng(20261014).normal(size=32)
    q,o=tensors_from_real(a)
    np.testing.assert_allclose(stored_to_real(stf2_to_real_harmonic(q),2)[0],a[:5],atol=1e-13)
    np.testing.assert_allclose(stored_to_real(stf3_to_real_harmonic(o),3)[0],a[5:12],atol=1e-13)
    assert np.sum(q*q)==pytest.approx(15/(8*np.pi)*np.sum(a[:5]**2))
    assert np.sum(o*o)==pytest.approx(35/(8*np.pi)*np.sum(a[5:12]**2))
    r=Rotation.from_rotvec([.2,-.6,.4]).as_matrix()
    qr=r@q@r.T;orr=np.einsum('ia,jb,kc,abc->ijk',r,r,r,o)
    np.testing.assert_allclose(tensor_shape_features(qr,orr),tensor_shape_features(q,o),atol=1e-12)
    parity=tensor_shape_features(q,-o)
    np.testing.assert_allclose(parity[:3],tensor_shape_features(q,o)[:3],atol=1e-14)
    assert parity[3]==pytest.approx(-tensor_shape_features(q,o)[3])
    assert feature_vector(a)[0]==pytest.approx(np.sum(a[:5]**2)/5)


def test_undefined_and_invalid_carriers_refused():
    with pytest.raises(ValueError,match='zero tensor'):tensor_shape_features(np.zeros((3,3)),np.ones((3,3,3)))
    with pytest.raises(ValueError,match='vector'):feature_vector(np.zeros(31))
    row=np.random.default_rng(5).normal(size=32)
    with pytest.raises(ValueError,match='real'):feature_vector(row+1j)
    q,o=tensors_from_real(row)
    with pytest.raises(ValueError,match='real'):tensor_shape_features(q+1j,o)
    assert np.isfinite(feature_vector(row*1e100)).all()
    with np.errstate(over='ignore',invalid='ignore'):
        with pytest.raises(ValueError,match='overflow'):feature_vector(row*1e200)
