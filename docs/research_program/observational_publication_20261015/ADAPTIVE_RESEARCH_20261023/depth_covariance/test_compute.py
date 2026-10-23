"""Independent deterministic falsifiers for the frozen full24 contract."""
import importlib.util
from pathlib import Path

import numpy as np
from scipy.stats import chi2

PATH = Path(__file__).with_name('compute.py')
SPEC = importlib.util.spec_from_file_location('r25_depth_cov_compute', PATH)
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def state():
    r = c.calculate()
    return r, np.array(r['full24']['mean_uasyr']), np.array(r['full24']['cov_uasyr2']), np.array(r['A12x24'])


def test_independent_map_rank_and_source():
    r, mu, C, A = state()
    M = np.zeros((18,24))
    for b,(num,den) in enumerate([(1,4),(7,12),(26,33)]):
        for j in range(6):
            M[6*b+j,6*b+j] = 1
            M[6*b+j,18+j] = num/den
    D = np.zeros((12,18))
    for j in range(6):
        D[j,j],D[j,6+j] = -1,1
        D[6+j,6+j],D[6+j,12+j] = -1,1
    assert np.array_equal(M,np.array(r['M24_to_Y18']))
    assert np.array_equal(D@M,A)
    assert [np.linalg.matrix_rank(A,tol=t) for t in (1e-8,1e-10,1e-12)] == [12]*3
    assert np.linalg.eigvalsh(C)[0] > 0
    assert np.allclose(A@mu,np.array(r['contrast12_mean_uasyr']),rtol=0,atol=1e-14)


def test_quadratic_tails_roots_and_full_cross_covariance():
    r, mu, C, A = state()
    d = A@mu
    for row in r['reference_curves']:
        tau=row['tau_uasyr']
        V = A@(C+tau*tau*np.eye(24))@A.T
        w,vec = np.linalg.eigh(V)
        independent = np.sum((vec.T@d)**2/w)
        assert np.allclose(row['V12_uasyr2'],V,rtol=0,atol=2e-13)
        assert np.isclose(row['T12'],independent,rtol=1e-9,atol=1e-10)
        assert np.isclose(row['gaussian_reference_survival'],chi2.sf(independent,12),rtol=1e-12)
        assert np.isclose(row['moment_reference_upper_bound'],min(1,12/independent),rtol=1e-12)
    for roots in r['reference_crossings'].values():
        for root in roots.values():
            if root['status']=='CROSSED':
                t=root['tau_uasyr']
                assert root['bracket_uasyr'][0]<=t<=root['bracket_uasyr'][1]
                assert abs(c.statistic(d,A,C,t)[0]-root['critical'])<=1e-8


def test_common_mode_and_permutation():
    _,mu,C,A=state()
    U=np.vstack((np.eye(6),np.eye(6),np.eye(6),np.zeros((6,6))))
    assert np.max(np.abs(A@U))<1e-14
    for lam in (0,1,100):
        assert np.isclose(c.statistic(A@mu,A,C+lam*U@U.T,0)[0],
                          c.statistic(A@mu,A,C,0)[0],rtol=1e-12)
    p=np.array(list(range(23,-1,-1)))
    assert np.isclose(c.statistic(A[:,p]@mu[p],A[:,p],C[np.ix_(p,p)],.3)[0],
                      c.statistic(A@mu,A,C,.3)[0],rtol=1e-12)


def test_proper_rotation_and_polar_axial_parity():
    _,mu,C,A=state()
    angle=.37
    R=np.array([[np.cos(angle),-np.sin(angle),0],
                [np.sin(angle),np.cos(angle),0],[0,0,1]])
    for polar,axial in ((R,R),(-np.eye(3),np.eye(3))):
        block=np.zeros((6,6));block[:3,:3]=polar;block[3:,3:]=axial
        P=np.kron(np.eye(4),block)
        D=np.kron(np.eye(2),block)
        assert np.allclose(A@P,D@A,rtol=0,atol=1e-14)
        t0=c.statistic(A@mu,A,C,1)[0]
        t1=c.statistic(A@P@mu,A,P@C@P.T,1)[0]
        assert np.isclose(t0,t1,rtol=1e-12)


def test_support_and_gap_cross_blocks():
    r,mu,C,A=state()
    v=np.arange(1,25,dtype=float);v=v/np.linalg.norm(v)
    for tau in (0,.3,3):
        U=C+tau*tau*np.eye(24)
        L=np.linalg.cholesky(U)
        direction=L.T@v
        boundary=mu+2*L@(direction/np.linalg.norm(direction))
        assert np.isclose(v@boundary,c.support(mu,U,v,2),rtol=1e-12)
    G=np.array(r['G_F']['map24_to_Z18'])
    V=np.array(r['G_F']['cov18_at_tau0_uasyr2'])
    assert np.allclose(V,G@C@G.T,rtol=0,atol=2e-13)
    assert np.max(np.abs(V[:6,6:12]))>0
    assert np.max(np.abs(V[6:12,12:18]))>0
    assert r['Pi']['newly_calibrated_Pi'] is False
    assert r['Q']['physical_status']=='UNAVAILABLE'
