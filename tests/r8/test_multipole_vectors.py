import itertools
from fractions import Fraction
import numpy as np
import pytest
from obsstat.r8_multipole_vectors import mv_to_tensor,tensor_to_mv


def test_vector_sign_has_amplitude_compensation():
    v=np.eye(3);w=v.copy();w[0]*=-1
    assert np.allclose(mv_to_tensor(2.,v,3),mv_to_tensor(-2.,w,3),atol=0)
    assert np.all(mv_to_tensor(0.,v,3)==0)
    for order in itertools.permutations(range(3)):
        assert np.allclose(mv_to_tensor(2.,v[list(order)],3),mv_to_tensor(2.,v,3),atol=0)


@pytest.mark.parametrize('l',[2,3])
def test_trace_and_roundtrip_enclosure(l):
    rng=np.random.default_rng(410)
    for _ in range(12):
        vectors=rng.normal(size=(l,3));vectors/=np.linalg.norm(vectors,axis=1)[:,None]
        t=mv_to_tensor(2.7e-5,vectors,l)
        assert np.max(abs(np.trace(t,axis1=0,axis2=1)))<1e-19
        for order in itertools.permutations(range(l)):
            assert np.array_equal(t,t.transpose(order))
        out=tensor_to_mv(t,l)
        assert out.status=='RECONSTRUCTED_WITH_ERROR_BOUND'
        restored=mv_to_tensor(out.amplitude,out.vectors,l)
        sq=sum((Fraction(float(x))-Fraction(float(y)))**2 for x,y in zip(t.flat,restored.flat))
        assert out.reconstruction_enclosure.lo**2<=sq<=out.reconstruction_enclosure.hi**2
        assert float(out.reconstruction_enclosure.hi)<1e-16
        assert np.allclose(np.linalg.norm(out.vectors,axis=1),1)


@pytest.mark.parametrize('l',[2,3])
def test_zero_and_multiple_roots_retain_tensor(l):
    zero=tensor_to_mv(np.zeros((3,)*l),l)
    assert zero.status=='ZERO_AMPLITUDE_DIRECTIONS_UNIDENTIFIED'
    assert zero.amplitude==0 and zero.vectors is None and zero.reconstruction_enclosure.hi==0
    assert np.all(mv_to_tensor(0.,None,l)==0)
    v=np.tile([1.,0.,0.],(l,1));t=mv_to_tensor(1.,v,l)
    repeated=tensor_to_mv(t,l)
    assert repeated.status=='MULTIPLE_ROOT_UNRESOLVED'
    assert repeated.amplitude is None and np.array_equal(repeated.original_tensor,t)


def test_invalid_tensor_and_vector_inputs():
    with pytest.raises(ValueError):mv_to_tensor(1.,np.ones((2,3)),2)
    with pytest.raises(ValueError):tensor_to_mv(np.eye(3),2)
    with pytest.raises(ValueError):tensor_to_mv(np.full((3,3),np.nan),2)
    with pytest.raises(ValueError):mv_to_tensor(float('nan'),np.eye(3),3)


@pytest.mark.parametrize('l',[2,3])
def test_finite_tensor_amplitude_overflow_retains_row(l):
    rng=np.random.default_rng(410)
    v=rng.normal(size=(l,3));v/=np.linalg.norm(v,axis=1)[:,None]
    t=mv_to_tensor(1.,v,l);t=t/np.max(abs(t))*1.7e308
    out=tensor_to_mv(t,l)
    assert out.status=='RECONSTRUCTION_UNRESOLVED'
    assert np.array_equal(out.original_tensor,t)
