import numpy as np
import pytest
from scipy import linalg, optimize, stats

try:
    from htt.htt.infer.r61_kinematic_images import (
        quadratic_ball_extreme, quadratic_ellipsoid_range, norm_ellipsoid_range,
        kinematic_images, directional_expansion_support, stf_basis)
except ModuleNotFoundError:
    from r61_kinematic_images import (
        quadratic_ball_extreme, quadratic_ellipsoid_range, norm_ellipsoid_range,
        kinematic_images, directional_expansion_support, stf_basis)


@pytest.mark.parametrize('B,b,expected',[
    (np.diag([2.,3.]),[0.,0.],0.),
    (np.diag([-2.,1.]),[0.,.3],-2.03),
    (np.diag([0.,2.]),[0.,.4],-.08),
    (np.zeros((2,2)),[1.,2.],-2.*np.sqrt(5.)),
    (np.zeros((2,2)),[0.,0.],0.),
])
def test_hand_solved_minima_and_hard_cases(B,b,expected):
    ans=quadratic_ball_extreme(B,b)
    assert abs(ans['value']-expected)<2e-12
    assert ans['bound']<=expected+1e-13
    assert ans['optimality_gap']<2e-11
    assert ans['norm']<=1.+2e-15


def test_known_ellipsoid_norm_range():
    # A ball centered at (3,4) of radius2 has norm range[3,7].
    ans=norm_ellipsoid_range([3.,4.],np.eye(2),cutoff=4.)
    assert ans['lower']==pytest.approx(3.,abs=1e-11)
    assert ans['upper']==pytest.approx(7.,abs=1e-11)
    inside=norm_ellipsoid_range([.3,.4],np.eye(2),cutoff=4.)
    assert inside['lower']==0.
    assert inside['feasible_lower']<1e-12
    assert inside['upper']==pytest.approx(2.5,abs=1e-11)


def test_mixed_quadratic_independent_cartesian_slsqp():
    rng=np.random.default_rng(6105)
    for case in range(4):
        A=rng.normal(size=(5,5)); C=A@A.T+np.eye(5)
        M=rng.normal(size=(5,5)); M=.5*(M+M.T)
        h=rng.normal(size=5); cutoff=4.2
        result=quadratic_ellipsoid_range(h,C,M,cutoff=cutoff)
        precision=linalg.inv(C)
        objective_scale=np.linalg.norm(M,2)*(np.linalg.norm(h)+
                    np.sqrt(cutoff*np.linalg.norm(C,2)))**2
        for sense,key in [(1,'minimum'),(-1,'maximum')]:
            # Normalize the independent Cartesian optimizer's objective and
            # constraint. Unscaled SLSQP falsely stopped at its line-search
            # tolerance despite a feasible near-optimum on one random case.
            def f(x):return sense*(x@M@x)/objective_scale
            def jac(x):return sense*2*M@x/objective_scale
            cons={'type':'ineq','fun':lambda x:1-(x-h)@precision@(x-h)/cutoff,
                  'jac':lambda x:-2*precision@(x-h)/cutoff}
            best=None
            for start in [h,*[h+.1*rng.normal(size=5) for _ in range(3)]]:
                opt=optimize.minimize(f,start,jac=jac,constraints=cons,method='SLSQP',
                        options={'ftol':1e-12,'maxiter':500})
                if opt.success and (best is None or opt.fun<best.fun):best=opt
            assert best is not None
            assert cons['fun'](best.x)>-2e-10
            assert abs(sense*best.fun*objective_scale-result[key]['direct_value'])<2e-7
            assert result[key]['optimality_gap']<1e-9


def test_rotation_covariance_and_full_calibration_normalization():
    rng=np.random.default_rng(6106)
    A=rng.normal(size=(11,11)); C=(A@A.T+np.eye(11))*.00003
    scale=np.r_[np.ones(3)*20000,np.ones(8)]
    C=scale[:,None]*C*scale[None,:]
    h=rng.normal(size=11)*np.r_[np.ones(3)*200,np.ones(8)*.01]
    R,_=np.linalg.qr(rng.normal(size=(3,3)))
    if np.linalg.det(R)<0:R[:,0]*=-1
    E=stf_basis(); D=np.einsum('aij,ik,bkl,jl->ab',E,R,E,R)
    J=linalg.block_diag(R,R,D)
    cutoff=stats.chi2.ppf(.95,11)
    lhs=kinematic_images(h,C,cutoff=cutoff,rho=.002)
    rhs=kinematic_images(J@h,J@C@J.T,cutoff=cutoff,rho=.002)
    for name in ['Sigma','acceleration_over_cH','relative_speed_over_c','directional_expansion_rms']:
        assert lhs[name]['lower']==pytest.approx(rhs[name]['lower'],abs=2e-11)
        assert lhs[name]['upper']==pytest.approx(rhs[name]['upper'],abs=2e-11)
    for endpoint in ['lower','upper']:
        assert lhs['beta_dot_a'][endpoint]==pytest.approx(rhs['beta_dot_a'][endpoint],abs=1e-13)
    n=rng.normal(size=(40,3)); n/=np.linalg.norm(n,axis=1)[:,None]
    a=directional_expansion_support(h,C,n,cutoff=cutoff,rho=.002)
    b=directional_expansion_support(J@h,J@C@J.T,n@R.T,cutoff=cutoff,rho=.002)
    assert np.max(np.abs(a['lower']-b['lower']))<2e-12
    assert a['calibration_radius']==pytest.approx(np.sqrt(8)*.002)
    # Full-sky normalization: ||STF(nn)||²=2/3, and 3+7.5*(2/3)=8.
    coeff=np.einsum('ni,aij,nj->na',n,E,n)
    assert np.max(np.abs(np.sum(coeff*coeff,axis=1)-2/3))<1e-14


@pytest.mark.parametrize('bad',[-1.,np.nan,np.inf])
def test_invalid_cutoff_fails(bad):
    with pytest.raises(ValueError):quadratic_ellipsoid_range([0,0],np.eye(2),np.eye(2),cutoff=bad)


def test_indefinite_covariance_and_nonunit_direction_fail():
    with pytest.raises(ValueError):norm_ellipsoid_range([0,0],np.diag([1.,-1.]),cutoff=1.)
    with pytest.raises(ValueError):directional_expansion_support(np.zeros(11),np.eye(11),[[1,1,0]],cutoff=1.)


def test_enclosure_contains_random_quadratics_in_ball():
    rng=np.random.default_rng(6107)
    B=rng.normal(size=(8,8));B=.5*(B+B.T);b=rng.normal(size=8)
    low=quadratic_ball_extreme(B,b);high=quadratic_ball_extreme(B,b,sense='max')
    u=rng.normal(size=(2000,8));u/=np.linalg.norm(u,axis=1)[:,None]
    u*=rng.uniform(size=(len(u),1))**(1/8)
    vals=np.einsum('ni,ij,nj->n',u,B,u)+2*u@b
    assert vals.min()>=low['bound']
    assert vals.max()<=high['bound']
