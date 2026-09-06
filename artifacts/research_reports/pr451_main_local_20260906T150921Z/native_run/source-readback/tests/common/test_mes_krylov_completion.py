"""Regression oracles for the additive research algebra, not Planck admission."""
from __future__ import annotations
from copy import deepcopy
import importlib.util
from itertools import combinations_with_replacement, permutations
from pathlib import Path
import math
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "mes_krylov_under_test",
    ROOT / "htt/src/common/mes_krylov_completion.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def witness():
    q = np.diag([1., 2., -3.])
    values = {
        (0,0,0):1., (0,0,1):2., (0,0,2):3., (0,1,1):4.,
        (0,1,2):5., (1,1,1):6., (1,1,2):7., (0,2,2):-5.,
        (1,2,2):-8., (2,2,2):-10.,
    }
    o = np.empty((3,3,3))
    for t, v in values.items():
        for p in set(permutations(t)):
            o[p] = v
    return q, o


def test_independent_power_and_bispectrum_witness():
    q,o=witness()
    np.testing.assert_array_equal(
        MOD.ordinary_power_bispectrum(q,o), [14,788,-18,-472]
    )
    v=np.einsum('ijk,jk->i',o,q)
    assert np.isclose(
        np.linalg.det(np.column_stack((v,q@v,q@q@v))),857280
    )


def test_mirror_pair_requires_information_beyond_low_order_bispectrum():
    q,o=witness()
    np.testing.assert_array_equal(
        MOD.ordinary_power_bispectrum(q,o),
        MOD.ordinary_power_bispectrum(q,-o),
    )
    a,b=MOD.krylov16(q,o),MOD.krylov16(q,-o)
    assert a['values'][5] == -b['values'][5]
    assert a['values'][5] != 0
    np.testing.assert_allclose(
        np.delete(a['values'],5),
        np.delete(b['values'],5),
        rtol=1e-13,
        atol=1e-15,
    )


def test_reconstruction_preserves_the_entire_signature():
    q,o=witness(); packet=MOD.krylov16(q,o)
    qr,orr=MOD.reconstruct_krylov16(packet)
    other=MOD.krylov16(qr,orr)
    np.testing.assert_allclose(
        other['values'],packet['values'],rtol=1e-8,atol=1e-12
    )
    np.testing.assert_allclose(
        MOD.ordinary_power_bispectrum(qr,orr),
        MOD.ordinary_power_bispectrum(q,o),
        rtol=1e-8,
        atol=1e-8,
    )


def test_rotation_covariance_not_absolute_frame_recovery():
    q,o=witness(); a=math.pi/7
    r=np.array([
        [math.cos(a),-math.sin(a),0],
        [math.sin(a),math.cos(a),0],
        [0,0,1],
    ])
    qr=r@q@r.T
    orr=np.einsum('ia,jb,kc,abc->ijk',r,r,r,o)
    before=MOD.krylov16(q,o); after=MOD.krylov16(qr,orr)
    np.testing.assert_allclose(
        after['values'],before['values'],rtol=1e-11,atol=1e-14
    )
    q0,o0=MOD.reconstruct_krylov16(before)
    q1,o1=MOD.reconstruct_krylov16(after)
    np.testing.assert_allclose(q1,q0,rtol=1e-8,atol=1e-8)
    np.testing.assert_allclose(o1,o0,rtol=1e-8,atol=1e-8)


@pytest.mark.parametrize('scale',[1e-200,1e-100,1.,1e100,1e200])
def test_common_scale_is_explicit_and_stable(scale):
    q,o=witness()
    p=MOD.krylov16(scale*q,scale*o)
    reference=MOD.krylov16(q,o)
    np.testing.assert_allclose(
        p['values'],reference['values'],rtol=1e-11,atol=1e-14
    )
    qr,orr=MOD.reconstruct_krylov16(p)
    np.testing.assert_allclose(
        MOD.krylov16(qr/scale,orr/scale)['values'],
        reference['values'],
        rtol=1e-8,
        atol=1e-12,
    )


def test_zero_shape_is_typed_unavailable():
    q,o=witness()
    with pytest.raises(MOD.OrbitChartUnavailable):
        MOD.krylov16(q*0,o)
    with pytest.raises(MOD.OrbitChartUnavailable):
        MOD.krylov16(q,o*0)


def test_axisymmetric_stabilizer_cannot_manufacture_a_full_frame():
    q=np.diag([-1.,-1.,2.]);o=np.zeros((3,3,3));o[2,2,2]=2.
    for t in [(0,0,2),(1,1,2)]:
        for p in set(permutations(t)):
            o[p]=-1.
    with pytest.raises(MOD.OrbitChartUnavailable):
        MOD.krylov16(q,o)


@pytest.mark.parametrize(
    'kind',['complex','boolean','object','nonfinite','not_stf','not_symmetric']
)
def test_malformed_q_is_refused(kind):
    q,o=witness()
    if kind=='complex':q=q.astype(complex)
    elif kind=='boolean':q=q.astype(bool)
    elif kind=='object':q=q.astype(object)
    elif kind=='nonfinite':q[0,0]=np.nan
    elif kind=='not_stf':q[0,0]+=1
    else:q[0,1]=1
    with pytest.raises(MOD.OrbitInputError):
        MOD.krylov16(q,o)


@pytest.mark.parametrize(
    'kind',['schema','group','normalization','triple_order','volume','negative_norm']
)
def test_semantic_or_algebraic_signature_mutation_is_refused(kind):
    q,o=witness();p=deepcopy(MOD.krylov16(q,o))
    if kind=='schema':p['schema']='OTHER'
    elif kind=='group':p['action_group']='O3'
    elif kind=='normalization':p['normalization']='RAW_DIMENSIONAL'
    elif kind=='triple_order':p['triple_order']=p['triple_order'][::-1]
    elif kind=='volume':p['values'][5]*=2
    else:p['q_frobenius_amplitude']=-1
    with pytest.raises(MOD.OrbitInputError):
        MOD.reconstruct_krylov16(p)


def test_mes_vorticity_normalization_is_pstf_not_sky_rms():
    c2=210.461847;t0=2725500.
    p=MOD.pstf_mes_ceilings(c2=c2,c3=482.020811,t0=t0,epsilon1=0.)
    assert math.isclose(p['U_omega'],c2/(4*math.pi*t0*t0),rel_tol=2e-15)
    assert math.isclose(
        p['epsilon2_pstf']**2,75*c2/(8*math.pi*t0*t0),rel_tol=2e-15
    )
    assert math.isclose(
        p['epsilon3_pstf']**2,
        245*482.020811/(8*math.pi*t0*t0),
        rel_tol=2e-15,
    )


def test_temperature_unit_conversion_cannot_change_dimensionless_mes_values():
    a=MOD.pstf_mes_ceilings(
        c2=210.,c3=482.,t0=2725500.,epsilon1=1e-5
    )
    b=MOD.pstf_mes_ceilings(
        c2=210e-12,c3=482e-12,t0=2.7255,epsilon1=1e-5
    )
    for key in ['U_sigma','U_omega','epsilon2_pstf','epsilon3_pstf']:
        assert math.isclose(a[key],b[key],rel_tol=3e-15)


def test_reconstruction_rejects_tracefree_unit_o_outside_packet_image():
    """Changing O while preserving old moments must not decode as valid."""
    q, o = witness()
    packet = MOD.krylov16(q, o)
    qr, orr = MOD.reconstruct_krylov16(packet)
    ou = orr / packet['o_frobenius_amplitude']

    s2, s3, m0, m1, m2, kap = packet['values'][:6]
    m3 = s2 * m1 / 2 + s3 * m0 / 3
    m4 = s2 * m2 / 2 + s3 * m1 / 3
    gram = np.array([[m0, m1, m2], [m1, m2, m3], [m2, m3, m4]])
    basis = np.linalg.cholesky(gram).T
    if kap < 0:
        basis[2] *= -1

    rng = np.random.default_rng(20260903)
    delta = rng.normal(size=(3, 3, 3))
    delta = sum(delta.transpose(p) for p in permutations(range(3))) / 6.0
    trace = np.einsum('iik->k', delta)
    eye = np.eye(3)
    delta -= (
        np.einsum('ij,k->ijk', eye, trace)
        + np.einsum('ik,j->ijk', eye, trace)
        + np.einsum('jk,i->ijk', eye, trace)
    ) / 5.0
    delta -= np.sum(delta * ou) * ou
    delta /= np.linalg.norm(delta)
    theta = 0.2
    mutated_o = math.cos(theta) * ou + math.sin(theta) * delta

    mutated = deepcopy(packet)
    triples = tuple(combinations_with_replacement(range(3), 3))
    mutated['values'][6:] = [
        float(
            np.einsum(
                'abc,a,b,c',
                mutated_o,
                basis[:, i],
                basis[:, j],
                basis[:, k],
            )
        )
        for i, j, k in triples
    ]

    with pytest.raises(MOD.OrbitInputError, match='O:Q vector disagrees'):
        MOD.reconstruct_krylov16(mutated)
