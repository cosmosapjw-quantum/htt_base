"""Physical identities and statistical semantics for the R66 finite experiment."""
import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest
from scipy import stats
from htt.htt.infer import r66_radiation_quotient as rq

ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-05-RADIATION-RESPONSE/radiation_core.py'
spec=importlib.util.spec_from_file_location('r66_r36_test_core',CORE_PATH)
core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)


def test_known_spherical_harmonic_normalization_and_sign():
    n,w=core.sphere_rule(18,40)
    design,labels=rq.harmonic_design(n,6)
    q=np.array([1.,-2.,3.,-4.,5.])
    sky=design[:,4:9]@q
    theta=np.arccos(n[:,2]);phi=np.arctan2(n[:,1],n[:,0])
    a=[4*np.pi*np.sum(w*sky*rq.special.sph_harm_y(2,m,theta,phi).conj()) for m in range(3)]
    d=np.array([a[0].real,np.sqrt(2)*a[1].real,-np.sqrt(2)*a[1].imag,
                np.sqrt(2)*a[2].real,-np.sqrt(2)*a[2].imag])
    expected=np.sqrt(8*np.pi/15)*np.array([-q[1],-q[3],-q[4],q[0],q[2]])
    np.testing.assert_allclose(d,expected,atol=2e-13)


def test_actual_mask_ols_preserves_quadrupole_and_removes_monopole_dipole():
    n,w=core.sphere_rule(20,50);h,labels=rq.harmonic_design(n,6)
    keep=(abs(n[:,2])>.18)&(n[:,0]<.9)
    e=rq.estimator(h,keep,labels)
    coeff=np.zeros(h.shape[1]);coeff[:4]=[1e4,3300,1500,-2000];coeff[4:9]=[2,-3,5,7,-11]
    np.testing.assert_allclose(e.extract(h@coeff)[4:9],coeff[4:9],atol=1e-10)
    assert e.condition<100


def test_four_dimensional_dq_quotient_is_shift_invariant():
    u=rq.quotient_basis(rq.DQ_UK);q=np.arange(5.)
    assert u.shape==(5,4)
    for alpha in [-100.,-.1,0,2,100]:
        np.testing.assert_allclose(u.T@(q+alpha*rq.DQ_UK),u.T@q,atol=5e-13)
    assert np.linalg.matrix_rank(u.T)==4


def test_covariance_profile_and_quotient_are_equivalent():
    rng=np.random.default_rng(6601);a=rng.normal(size=(5,5));cov=a@a.T+np.eye(5)
    b=rq.DQ_UK;u=rq.quotient_basis(b);q=rng.normal(size=5)
    qp=q@rq.profile_precision(cov,b)@q
    qu=(u.T@q)@np.linalg.solve(u.T@cov@u,u.T@q)
    np.testing.assert_allclose(qp,qu,rtol=2e-13)


def test_rotated_tensors_have_same_quotient_norm():
    rng=np.random.default_rng(6602);rot=stats.special_ortho_group.rvs(3,random_state=rng)
    q=rng.normal(size=5);b=rq.DQ_UK
    def rotate(v):return rq.matrix_to_stf5(rot@rq.stf5_to_matrix(v)@rot.T)
    x=rq.quotient_basis(b).T@q
    xp=rq.quotient_basis(rotate(b)).T@rotate(q)
    np.testing.assert_allclose(x@x,xp@xp,rtol=2e-13)


@pytest.mark.parametrize('beta',[0.,.00123,.2])
def test_reused_r36_exact_boost_matches_stress_tensor_and_landau(beta):
    n,w=core.sphere_rule(40,48);v=np.array([0.,0.,beta]);g=1/np.sqrt(1-beta**2)
    t=1/(g*(1-n@v))
    m=core.moments(n,w,t**4,1.)
    np.testing.assert_allclose(m.rho,g*g*(1+beta*beta/3),atol=2e-13)
    np.testing.assert_allclose(m.pi,4/3*g*g*core.stf2(np.outer(v,v)),atol=2e-13)
    np.testing.assert_allclose(m.flux/rq.c,-4/3*g*g*v,atol=2e-13)
    read=core.stress_readout(m)
    assert read['D_norm']<2e-13 and read['A_gamma']<2e-13


def test_dipole_octupole_quadratic_stress_coupling():
    # STF octupole with axis z: O(n,n,n)=n_z^3-3n_z/5.
    n,w=core.sphere_rule(20,40);d=np.array([0.,0.,.002]);o_amp=1e-5
    octupole=o_amp*(n[:,2]**3-3*n[:,2]/5)
    cross=12*(n@d)*octupole
    stress=np.einsum('n,n,ni,nj->ij',w,cross,n,n)
    # d_k O_kij = d_z o_amp diag(-1/5,-1/5,2/5).
    expected=24/35*d[2]*o_amp*np.diag([-1/5,-1/5,2/5])
    np.testing.assert_allclose(stress,expected,atol=1e-20)


def test_retained_t4_remainder_bound_and_normalization():
    n,w=core.sphere_rule(20,40);h,_=rq.harmonic_design(n,6)
    coeff=np.random.default_rng(6603).normal(size=h.shape[1])*2e-5
    coeff[1:4]=[.001,.0001,.0005];coeff[0]=0
    t=h@coeff
    nonlinear=6*t*t+4*t**3+t**4
    delta=core.stf2(np.einsum('n,n,ni,nj->ij',w,nonlinear,n,n))
    result=rq.nonlinear_remainder(t,w)
    assert np.linalg.norm(delta)<=result['norm_bound_nonlinear_over_rho0']
    with pytest.raises(ValueError):rq.nonlinear_remainder(np.full(len(w),-2.),w)


def test_missing_mode_bound_covers_an_independent_l7_completion():
    n,w=core.sphere_rule(48,96)
    low=.001*n[:,2]+2e-5*(n[:,0]**2-n[:,1]**2)
    h=3e-5*rq.special.sph_harm_y(7,3,np.arccos(n[:,2]),np.arctan2(n[:,1],n[:,0])).real
    difference=(1+low+h)**4-(1+low)**4
    actual=core.stf2(np.einsum('n,n,ni,nj->ij',w,difference,n,n))
    bound=rq.missing_mode_bound(abs(low).max(),abs(h).max(),np.sqrt(w@(h*h)))
    assert np.linalg.norm(actual)<bound


def test_finite_n_predictive_distribution_via_independent_wishart_draws():
    # This checks the formula against actual independent covariance/sky draws,
    # not the implementation's own t sampler. N and p deliberately small.
    rng=np.random.default_rng(6604);n,p=12,4;trials=12000
    w=stats.wishart.rvs(df=n,scale=np.eye(p),size=trials,random_state=rng)
    skies=rng.normal(size=(trials,p))
    q2=np.einsum('ni,ni->n',skies,np.linalg.solve(w/n,skies[...,None])[...,0])
    f=(n-p+1)*q2/(p*n)
    statistic,pvalue=stats.kstest(f,stats.f(p,n-p+1).cdf)
    assert statistic<.018 and pvalue>.01
    ref=rq.ConditionalReference(np.eye(p),n,p)
    x=np.array([1.,2.,0.,1.]);tail=ref.tail(x)
    np.testing.assert_allclose(tail['F'],(n-p+1)*6/(p*n))
    np.testing.assert_allclose(tail['lower']+tail['upper'],1.)
    np.testing.assert_allclose(ref.logpdf(x),stats.multivariate_t.logpdf(x,shape=n/(n-p+1)*np.eye(p),df=n-p+1))


def test_positive_radiation_body_and_occupancy_not_probability():
    rng=np.random.default_rng(6605);q=rng.normal(size=(200,5));q/=np.linalg.norm(q,axis=1)[:,None]
    for row in q:
        assert np.linalg.eigvalsh(np.eye(3)/3+rq.stf5_to_matrix(row*rq.ADMISSIBLE_INNER_RADIUS))[0]>=-1e-14
    r=.01;shape=np.eye(4)*r*r
    out=rq.occupation_of_inner_body(np.zeros(4),shape,1.)
    np.testing.assert_allclose(out['F'],(r/rq.ADMISSIBLE_INNER_RADIUS)**4,rtol=1e-13)
    assert rq.occupation_of_inner_body(np.ones(4),shape,1.)['status']=='INTERSECTION_NOT_COMPUTED'


def test_five_views_do_not_invent_redshift_information():
    rng=np.random.default_rng(6606);mc=rng.normal(size=(100,5))*30
    out=rq.five_views(np.arange(5.),mc)
    assert len(out['x']['quotient4_pi_linear_over_rho0'])==4
    assert out['G_F']['status']=='NOT_APPLICABLE'
    assert out['F']['status']=='CONDITIONAL_VOLUME_OCCUPANCY'
    assert not out['five_views_add_information']
    assert out['Pi']['quotient']['df2']==97


def test_scalar_power_loses_a_signed_physical_alternative():
    q=np.array([1.,2.,3.,4.,5.]);other=-q
    assert q@q==other@other
    assert not np.allclose(rq.stf5_to_matrix(q),rq.stf5_to_matrix(other))
    u=rq.quotient_basis(rq.DQ_UK);x=u.T@q
    assert x@x>0
    # Gaussian vector log-likelihood ratio at means +/-x is 2|x|^2.
    ratio=stats.multivariate_normal.logpdf(x,mean=x)-stats.multivariate_normal.logpdf(x,mean=-x)
    np.testing.assert_allclose(ratio,2*(x@x),rtol=1e-13)


def test_paired_gls_keeps_shared_cosmic_variance_and_unit_response():
    # Exact training scatter: a common sky variance plus independent noise.
    c=np.block([[2*np.eye(4),np.eye(4)],[np.eye(4),2*np.eye(4)]])
    x=np.vstack([np.sqrt(8)*np.linalg.cholesky(c).T,np.sqrt(8)*np.linalg.cholesky(c).T])
    j=np.vstack([np.eye(4),np.eye(4)])
    w,s=rq.paired_operator_weights(x,j)
    np.testing.assert_allclose(w,.5*np.hstack([np.eye(4),np.eye(4)]),atol=2e-13)
    np.testing.assert_allclose(w@s@w.T,1.5*np.eye(4),atol=2e-13)
    # Treating the two skies as independent would give variance 1, not 1.5.
    assert (w@s@w.T)[0,0]>1.


def test_duplicate_sky_rows_are_not_independent_information():
    rng=np.random.default_rng(6607);x=rng.normal(size=(50,4));j=np.vstack([np.eye(4),np.eye(4)])
    with pytest.raises(ValueError):rq.paired_operator_weights(np.c_[x,x],j)


def test_conventional_power_tensor_trace_rotation_and_sign_ambiguity():
    q=np.array([1.,-2.,3.,-4.,5.]);r=stats.special_ortho_group.rvs(3,random_state=6608)
    out=rq.power_tensor_quadrupole(q)
    np.testing.assert_allclose(out['C2_uK2'],8*np.pi/75*(q@q),rtol=1e-14)
    qp=rq.matrix_to_stf5(r@rq.stf5_to_matrix(q)@r.T)
    np.testing.assert_allclose(rq.power_tensor_quadrupole(qp)['tensor_uK2'],r@out['tensor_uK2']@r.T,atol=3e-13)
    np.testing.assert_array_equal(out['tensor_uK2'],rq.power_tensor_quadrupole(-q)['tensor_uK2'])
    assert rq.power_tensor_quadrupole(np.zeros(5))['entropy'] is None


def test_reject_nonidentifiable_or_invalid_inputs():
    with pytest.raises(ValueError):rq.quotient_basis(np.zeros(5))
    with pytest.raises(ValueError):rq.ConditionalReference.from_draws(np.zeros((10,5)))
    with pytest.raises(ValueError):rq.missing_mode_bound(.1,.01,.02)


def test_known_covariance_reference_does_not_reestimate_from_validation_rows():
    q=np.arange(1.,6.);cov=np.diag(np.arange(1.,6.))
    out=rq.five_views(q,np.zeros((7,5)),known_covariance_uk2=cov)
    u=rq.quotient_basis(rq.DQ_UK);s=u.T@q
    expected=s@np.linalg.solve(u.T@cov@u,s)
    np.testing.assert_allclose(out['Pi']['quotient']['q2'],expected,rtol=1e-13)
    assert out['Pi']['quotient']['df']==4
    assert 'analytic' in out['Pi']['covariance_definition']
    with pytest.raises(ValueError,match='all-zero'):
        rq.ConditionalReference.from_draws(np.zeros((100,5)))


def test_unit_free_angular_density_radial_student_integral():
    from scipy.integrate import quad
    s=np.diag([1.,2.,3.,4.]);x=np.array([1.,-2.,3.,4.]);u=x/np.linalg.norm(x)
    ref=rq.ConditionalReference(s,16,4)
    actual=quad(lambda r:np.exp(ref.logpdf(r*u))*r**3,0,np.inf,epsabs=1e-12)[0]
    np.testing.assert_allclose(actual,np.exp(rq.angular_logpdf(x,s)),rtol=2e-10)
    for scale in [1e-12,1.,1e12]:
        np.testing.assert_allclose(rq.angular_logpdf(x,s*scale),rq.angular_logpdf(x,s),atol=2e-14)
    with pytest.raises(ValueError):rq.angular_logpdf(np.zeros(4),s)


def test_angular_density_is_normalized_on_directed_sphere():
    rng=np.random.default_rng(6609);x=rng.normal(size=(60000,4));x/=np.linalg.norm(x,axis=1)[:,None]
    s=np.diag([1.,1.5,2.,2.5]);density=np.linalg.det(s)**(-.5)*(np.einsum('ni,ij,nj->n',x,np.linalg.inv(s),x))**(-2)
    assert abs(density.mean()-1)<5*density.std()/np.sqrt(len(x))
    np.testing.assert_allclose(rq.angular_logpdf(x[0],np.eye(4)),-np.log(2*np.pi**2),rtol=1e-14)


def test_healpix_adjoint_reference_matches_direct_finite_harmonic_sum():
    import healpy as hp
    ns=4;lmax=4;rng=np.random.default_rng(6610)
    w=rng.normal(size=(3,hp.nside2npix(ns)))
    a=np.array([hp.map2alm(row/hp.nside2pixarea(ns),lmax=lmax,iter=0,pol=False) for row in w])
    th,ph=hp.pix2ang(ns,np.arange(w.shape[1]));le,me=hp.Alm.getlm(lmax)
    direct=np.column_stack([w@rq.special.sph_harm_y(int(l),int(m),th,ph).conj() for l,m in zip(le,me)])
    np.testing.assert_allclose(a,direct,rtol=1e-12,atol=3e-14)
    cl=np.arange(lmax+1,dtype=float);cl[:2]=0
    cov=((a*cl[le]*np.where(me==0,1,2))@a.conj().T).real
    real=[]
    for l in range(2,lmax+1):
        real.append(np.sqrt(cl[l])*(w@rq.special.sph_harm_y(l,0,th,ph).real))
        for m in range(1,l+1):
            y=rq.special.sph_harm_y(l,m,th,ph)
            real.extend([np.sqrt(2*cl[l])*(w@y.real),np.sqrt(2*cl[l])*(w@y.imag)])
    real=np.column_stack(real)
    np.testing.assert_allclose(cov,real@real.T,rtol=1e-12,atol=1e-10)


def test_scalar_temperature_ring_mask_average_handles_empty_selected_chunks(tmp_path):
    import healpy as hp
    from astropy.io import fits
    apath=ROOT/'scripts/r66/acquire_r66_temperature_pilot.py'
    sp=importlib.util.spec_from_file_location('r66_acquisition_test',apath)
    mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
    ns,nt,nm=8,2,4
    n=np.column_stack(hp.pix2vec(ns,np.arange(hp.nside2npix(ns))))
    values=2+n[:,0]+n[:,1]**2
    mask=np.array(hp.pix2vec(nm,np.arange(hp.nside2npix(nm)),nest=True))[2]>.6
    f=tmp_path/'scalar_temperature.fits'
    table=fits.BinTableHDU.from_columns([fits.Column(name='I_Stokes',format='D',array=values)])
    table.header['NSIDE']=ns;table.header['ORDERING']='RING'
    table.writeto(f)
    result,counts,header=mod.ring_coarse(f,mask,native=ns,target=nt,mask_nside=nm,chunk_pixels=16)
    valid=np.repeat(mask,(ns//nm)**2);factor=(ns//nt)**2
    expect_counts=valid.reshape(-1,factor).sum(axis=1)
    expect=(hp.reorder(values,r2n=True)*valid).reshape(-1,factor).sum(axis=1)/np.maximum(expect_counts,1)
    np.testing.assert_array_equal(counts,expect_counts)
    np.testing.assert_allclose(result,expect,atol=2e-15)
    assert header['retained_raw_rms']>0 and header['TUNIT1']==''
    with pytest.raises(ValueError,match='all-zero'):
        mod.ring_coarse(f,np.zeros_like(mask),native=ns,target=nt,mask_nside=nm,chunk_pixels=16)
