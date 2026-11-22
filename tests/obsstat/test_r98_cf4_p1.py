"""R98 regression contracts for the new log-distance law and common-slice threshold solver."""
import numpy as np
import pytest

from scripts.r98 import cf4_p1 as r


def test_one_common_nuisance_and_strict_coincident_roots():
    # Two draw IDs cross threshold 1 in opposite senses at zero. At zero, all events tie.
    q = np.ones((2,4,1))
    q[1] = -1
    m = r.finite_slice(q,np.ones((4,1)),np.ones((2,4)),np.zeros(4),.3,np.array([.7,.3]),1.)
    np.testing.assert_allclose(m["min_mass"],0.)
    np.testing.assert_allclose(m["max_mass"],.7)
    np.testing.assert_allclose(m["min_at"],0.)
    assert m["n_distinct_interior_roots"] == 1


def test_true_tangency_and_joint_window_events():
    q = np.zeros((1,4,2)); q[:,:,1] = 1.
    q[0,1:,1] = 2.
    v = np.zeros((4,2)); v[:,0] = 1.
    m = r.finite_slice(q,v,np.ones((1,4)),np.zeros(4),.5,np.ones(1),1.)
    np.testing.assert_equal(m["min_mass"],[0,1,1,1,1,0])
    np.testing.assert_equal(m["max_mass"],np.ones(6))
    assert m["n_distinct_interior_roots"] == 1


def test_slice_matches_exhaustive_direct_ratios_and_singular_denominators():
    rng = np.random.default_rng(4207)
    q = rng.normal(size=(25,4,3)); d = rng.uniform(3.,5.,(25,4))
    v = rng.normal(size=(4,3)); h = np.array([1.1,-.3,.9,-2.])
    w = rng.uniform(.1,1.,25); w /= w.sum()
    m = r.finite_slice(q,v,d,h,.8,w,.45)
    def events(s):
        y = np.linalg.norm(q+s*v,axis=-1) > .45*(d+s*h)
        return w@np.column_stack((y,y.any(axis=1),y.all(axis=1)))
    grid = np.array([events(s) for s in np.linspace(-.8,.8,2001)])
    np.testing.assert_allclose(grid.min(axis=0),m["min_mass"],atol=2e-14)
    np.testing.assert_allclose(grid.max(axis=0),m["max_mass"],atol=2e-14)
    with pytest.raises(ValueError,match="denominator"):
        r.finite_slice(q,v,d,h,4.,w,.45)


def test_sharp_support_and_free_directcal():
    T = np.array([[1.,2.,3.,4.,5.,6.,7.],[-2.,0.,0.,0.,0.,0.,2.]])
    S = np.diag([.01,.02,.03,.04,.05])
    width = r.support_width(T,S,1.4,.087,.5)
    for row, b in zip(T,width):
        e = row[1:6]; den = np.sqrt(e @ S @ e)
        delta = np.full(7,.087*np.sign(row.sum()))
        if den:
            delta[1:6] += (1.4/den)*(S@e)
        delta[6] += .5*np.sign(row[6])
        assert row@delta == pytest.approx(b)
    assert np.isclose(width[1],1.)


def test_finite_modulus_response_and_covariance_on_independent_mock():
    H = r.r95._load_h03()
    rng = np.random.default_rng(739)
    n = rng.normal(size=(300,3)); n /= np.linalg.norm(n,axis=1)[:,None]
    cz = r.C*rng.uniform(.015,.085,len(n)); v = cz*(1.+.8*cz/r.C)
    mu = 25.+np.log(v/71.)/r.MAG+rng.normal(0,.15,len(n))
    emu = rng.uniform(.05,.4,len(n))
    W = rng.dirichlet(np.ones(7),size=len(n)); delta=np.linspace(-1.,1.,7)
    _,_,_,A,cov,b=r.tomography(H,n,cz,v,mu,emu)
    _,_,_,_,other,shift=r.tomography(H,n,cz,v,mu+W@delta,emu)
    np.testing.assert_allclose((shift-b).ravel(),-r.MAG*A@W@delta,atol=1e-14)
    np.testing.assert_array_equal(other,cov)
    np.testing.assert_allclose((A@W).sum(axis=1),np.tile(np.eye(9)[:,0],4),atol=2e-14)
    assert np.any(abs(cov[0,9:])>1e-10)


def test_complete_method_partition():
    e = np.array([[np.inf]*6,[.2,.3,np.inf,np.inf,np.inf,np.inf]])
    W = r.magnitude_weights(dict(e_vals_6=e,dmav=np.array([0.,35.]),cal_vals=np.array([30.,np.nan])))
    np.testing.assert_array_equal(W[0],np.eye(7)[6])
    assert W[1,0]==pytest.approx(9./13.)
    np.testing.assert_allclose(W.sum(axis=1),1.)


@pytest.mark.skipif(not (r.r97.RAW_CF4/"table4.dat").exists(), reason="original CF4 mirror required")
def test_release_velocity_convention_independent_named_cds_reader():
    # Astropy consumes the CDS ReadMe; its parser does not use the production byte slices.
    from astropy import units as u
    from astropy.table import Table
    raw = r.r97.RAW_CF4
    t = Table.read(raw/"table4.dat",format="ascii.cds",readme=str(raw/"ReadMe"),guess=False)
    assert len(t) == 38053
    assert t["Vpwf"].unit == t["Vpds"].unit == t["fV3k"].unit == u.km/u.s
    v = np.asarray(t["fV3k"],float)
    d = 10.**((np.asarray(t["DMzp"],float)-25.)/5.)
    positive = v>0
    vp = v[positive]
    scale = vp/(1+vp/299792.458)
    u_raw = np.asarray(t["Vpwf"],float)[positive]
    implied_scale = (vp/d[positive])*10.**(-u_raw/scale)
    assert len(vp) == 38004
    assert np.median(implied_scale) == pytest.approx(75.,abs=.001)
    np.testing.assert_allclose(scale*np.log10(vp/75./d[positive]),u_raw,rtol=0,atol=1.)
    assert np.sqrt(np.mean((scale*np.log(vp/75./d[positive])-u_raw)**2)) > 1500.
    np.testing.assert_allclose((v-75.*d)/(1.+75.*d/299792.458),
                               np.asarray(t["Vpds"],float),rtol=0,atol=1.)


def test_c9_two_distinct_sub_roundoff_tangent_roots():
    # Exactly representable binary inputs. The constant terms 2**-80 and 2**-82
    # are lost by evaluating (1+epsilon**2)-1 even in extended precision.
    q=np.ones((2,4,2)); q[0,:,1]=2.**-40; q[1,:,1]=2.**-41
    direction=np.tile([0.,1.],(4,1))
    result=r.finite_slice(q,direction,np.ones((2,4)),np.zeros(4),1.,[.5,.5],1.)
    np.testing.assert_array_equal(result["nominal"],np.ones(6))
    np.testing.assert_array_equal(result["min_mass"],np.full(6,.5))
    np.testing.assert_array_equal(result["max_mass"],np.ones(6))
    assert result["n_distinct_interior_roots"]==2
    assert "exact binary-rational" in result["method"]


def test_exact_fallback_algebraic_crossings_and_shared_draw():
    # First draw triggers exact handling. The second has irrational roots +-sqrt(3)/2.
    q=np.zeros((2,4,2)); q[0,:,0]=1.; q[0,:,1]=2.**-40; q[1,:,0]=.5
    result=r.finite_slice(q,np.tile([0.,1.],(4,1)),np.ones((2,4)),np.zeros(4),1.,[.4,.6],1.)
    assert result["n_distinct_interior_roots"]==3
    np.testing.assert_array_equal(result["nominal"],np.full(6,.4))
    np.testing.assert_array_equal(result["min_mass"],np.zeros(6))
    np.testing.assert_array_equal(result["max_mass"],np.ones(6))
