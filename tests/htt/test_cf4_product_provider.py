import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import multivariate_normal
from obsstat.catalogs.cf4_grouped_observations import GroupedObservations
from htt.infer.cf4_product_provider import (
    CF4ResponseProvider, ResponseFamily, ProviderUnavailable, SlotAssumptions,
    selected_slot_block, ConditionalCF4CatalogueLaw, area_distance_to_modulus,
    luminosity_to_area_distance, calibration_templates, _log_interval)
from htt.infer.r7_cf4_law import SelectedLatentBlock


def provider(family=ResponseFamily.WEAK12, bound=0.):
    return CF4ResponseProvider(family,'HELIOCENTRIC','HELIOCENTRIC','J2000_EQUATORIAL_SOURCEWARD','manufactured exact truncation',bound)


def assumptions(center=50., width=.002, selection=(-np.inf,np.inf)):
    return SlotAssumptions((np.log(center)-width,np.log(center)+width),(-1.,1.),selection,.2,150.,
                          'uniform slot log dA','supplied mu interval','independent conditional residuals','uniform source motion')


def cat(mu,v):
    n=len(mu)
    return GroupedObservations(np.arange(1,n+1),np.array(mu),np.full(n,.2),np.array(v),
         np.tile([1.,0.,0.],(n,1)),np.zeros((n,7),bool),{'scope':'manufactured','redshift_frame':'HELIOCENTRIC','direction_frame':'J2000_EQUATORIAL_SOURCEWARD'})


def theta():
    x=np.zeros(12); x[3]=70.; return x


@pytest.mark.parametrize('family,count',[(ResponseFamily.AFFINE9,9),(ResponseFamily.WEAK12,12),(ResponseFamily.ENDPOINT13,13)])
def test_capabilities_formula_and_basis(family,count):
    p=provider(family); n=np.array([[1.,0,0],[0,1,0],[0,0,1]]); r=np.array([20.,50,100])
    assert p.design(n,r).shape==(3,count)
    t=np.zeros(count); t[p.names.index('H')]=70
    np.testing.assert_allclose(p.velocity(n,r,t),70*r)
    assert len(p.units)==count
    assert p.capability()['expansion_dipole']==(count!=9)


def test_endpoint_crosswalk_and_rotation_stf():
    from htt.infer.endpoint_cosmography import endpoint_design
    from htt.infer.cf4_information import T_CART_TO_FROB
    rng=np.random.default_rng(23);n=rng.normal(size=(15,3));n/=np.linalg.norm(n,axis=1)[:,None];r=rng.uniform(30,200,15)
    t=rng.normal(size=13); zeta=np.r_[1+t[0]/299792.458,t[1:4]/299792.458,t[4:8],np.linalg.solve(T_CART_TO_FROB,t[8:])]
    np.testing.assert_allclose(provider(ResponseFamily.ENDPOINT13).velocity(n,r,t),299792.458*(endpoint_design(n,r)@zeta-1),atol=1e-10)


def test_refuse_missing_remainder_frame_and_outside_bounds():
    with pytest.raises(ProviderUnavailable): provider(bound=None).velocity([[1,0,0]],[50],theta())
    with pytest.raises(ProviderUnavailable): provider(bound=10).velocity([[1,0,0]],[50],theta())
    with pytest.raises(ValueError): provider(bound=10).velocity([[1,0,0]],[50],theta(),remainder_km_s=[11])
    with pytest.raises(ProviderUnavailable): CF4ResponseProvider(ResponseFamily.WEAK12,'CMB','HELIOCENTRIC','J2000_EQUATORIAL_SOURCEWARD','x',0.)


def test_reciprocity_and_units():
    r=np.array([40.,100]);z=np.array([.01,.04]);mu=area_distance_to_modulus(r,z)
    dl=10**((mu-25)/5)
    np.testing.assert_allclose(luminosity_to_area_distance(dl,z),r,rtol=2e-15)
    for zbad in [-1,-2]:
        with pytest.raises(ValueError): luminosity_to_area_distance(10,zbad)


def test_selected_block_matches_tensor_reference_and_normalization():
    p=provider();a=assumptions(selection=(32.,34.));m=float(area_distance_to_modulus(50,3500/299792.458));c=cat([m],[3500])
    b=selected_slot_block(p,[1,0,0],a,absolute_error=1e-9)
    assert isinstance(b,SelectedLatentBlock)
    law=ConditionalCF4CatalogueLaw(c,p,[a],shared_zero_point_sigma_mag=.03,calibration_source='proper shared prior',conditioned_field_convention='ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO',cross_covariance_mode='INDEPENDENT_GIVEN_SHARED_LATENTS',remainder_km_s=[0],order=32)
    np.testing.assert_allclose(b.loglik([m,3500],theta(),.02,p),law.row_loglik(theta(),.02)[0],atol=2e-8)
    # Integrate measurement density independently; velocity integrates exactly
    # over its full Gaussian support. Inner source integration uses scipy quad.
    def mu_density(y):
        def ell_density(ell):
            r=np.exp(ell)
            def u_density(u):
                mean=float(area_distance_to_modulus(r,(70*r+u)/299792.458,.02))
                return np.exp(-.5*((y-mean)/.2)**2)/(.2*np.sqrt(2*np.pi))/2
            return quad(u_density,-1,1,epsabs=1e-11)[0]/(a.log_distance_bounds[1]-a.log_distance_bounds[0])
        return quad(ell_density,*a.log_distance_bounds,epsabs=1e-10)[0]
    integrated=quad(mu_density,32,34,epsabs=1e-9)[0]
    norm,_=b._integral(lambda ell,u:b.intensity(np.array([ell,u]),theta(),.02,p)*b.selection_mass(np.array([ell,u]),theta(),.02,p),b.latent_bounds)
    assert abs(integrated/norm-1)<2e-8
    assert b.loglik([35,3500],theta(),0,p)==-np.inf


def test_no_selection_narrow_noise_limit_and_shared_zero_point_once():
    p=provider();m=float(area_distance_to_modulus(50,3500/299792.458));c=cat([m+.15,m-.1],[3500.,3500.])
    a=assumptions(width=1e-7)
    # Narrow source motion as well, so exact Gaussian reference is available.
    a=SlotAssumptions(a.log_distance_bounds,(-1e-5,1e-5),a.observed_mu_bounds,a.sigma_mu_mag,a.sigma_velocity_km_s,a.source_id,a.selection_id,a.cross_covariance_id,a.velocity_id)
    law=ConditionalCF4CatalogueLaw(c,p,[a,a],shared_zero_point_sigma_mag=.1,calibration_source='conditional proper eta prior',conditioned_field_convention='ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO',cross_covariance_mode='INDEPENDENT_GIVEN_SHARED_LATENTS',remainder_km_s=[0,0],order=16,calibration_order=48)
    cov=np.diag([.2**2,.2**2])+.1**2*np.ones((2,2))
    expected=multivariate_normal.logpdf(c.modulus,mean=[m,m],cov=cov)+2*multivariate_normal.logpdf([3500],mean=[3500],cov=[[150**2]])
    np.testing.assert_allclose(law.log_likelihood(theta()),expected,atol=2e-9)
    wrong=multivariate_normal.logpdf(c.modulus,mean=[m,m],cov=np.eye(2)*(.2**2+.1**2))+2*multivariate_normal.logpdf([3500],mean=[3500],cov=[[150**2]])
    assert abs(expected-wrong)>.01


def test_templates_and_joint_covariance_refusal():
    c=cat([33.,33.],[3500,3500]);t,names=calibration_templates(c,method_modes=True,angular=np.array([[1.],[-1.]]))
    assert t.shape==(2,9);assert names[0]=='global_zero_point';assert names[-1]=='angular_0'
    with pytest.raises(ProviderUnavailable): ConditionalCF4CatalogueLaw(c,provider(),[assumptions(),assumptions()],shared_zero_point_sigma_mag=.03,calibration_source='x',conditioned_field_convention='ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO',cross_covariance_mode='UNKNOWN',remainder_km_s=[0,0])


def test_tail_selection_is_not_silently_zero():
    assert np.isfinite(_log_interval(np.array([10.,-11.]),np.array([11.,-10.]))).all()


def test_actual_group_factory_reuses_existing_r7_law_and_unique_measurements():
    from htt.infer.cf4_product_provider import build_group_law_factory
    p=provider(ResponseFamily.ENDPOINT13);t=np.zeros(13);t[4]=70
    m=float(area_distance_to_modulus(50,3500/299792.458));c=cat([m],[3500])
    factory=build_group_law_factory(c,0,assumptions(),calibration_source='shared eta source',remainder_km_s=0.)
    law=factory.bind(p)
    assert law.measurement_ids==('CF4:1:mu_mag','CF4:1:Vh_km_s')
    assert law.conditioning_target=='SELECTED_JOINT_BLOCK_GIVEN_LATENT_FIELD_AND_COUNT'
    assert np.isfinite(law.loglik(t,0.))
    np.testing.assert_allclose(law.mean(t,0.),[m,3500],atol=.003)


def test_row_permutation_preserves_shared_likelihood_and_selection_changes_it():
    p=provider();m=float(area_distance_to_modulus(50,3500/299792.458));c=cat([m-.1,m+.1],[3400,3600]);a=assumptions(selection=(-np.inf,m+.2))
    kw=dict(shared_zero_point_sigma_mag=.03,calibration_source='conditional proper prior',conditioned_field_convention='ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO',cross_covariance_mode='INDEPENDENT_GIVEN_SHARED_LATENTS',remainder_km_s=[0,0],order=16)
    law=ConditionalCF4CatalogueLaw(c,p,[a,a],**kw)
    cp=GroupedObservations(c.group_id[::-1],c.modulus[::-1],c.modulus_error[::-1],c.vh_km_s[::-1],c.direction[::-1],c.method_presence[::-1],c.provenance)
    perm=ConditionalCF4CatalogueLaw(cp,p,[a,a],**kw)
    np.testing.assert_allclose(law.log_likelihood(theta()),perm.log_likelihood(theta()),atol=1e-12)
    no=ConditionalCF4CatalogueLaw(c,p,[assumptions(),assumptions()],**kw)
    assert law.log_likelihood(theta())>no.log_likelihood(theta())


def test_catalogue_frame_mismatch_rejected_before_likelihood():
    from obsstat.catalogs.cf4_grouped_observations import load_grouped_observations
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]/'workdir/raw/cf4_full'
    real=load_grouped_observations(root/'table3.dat.gz',root/'table4.dat.gz',root/'ReadMe')
    c=GroupedObservations(real.group_id[:1],real.modulus[:1],real.modulus_error[:1],real.vh_km_s[:1],real.direction[:1],real.method_presence[:1],real.provenance)
    p=CF4ResponseProvider(ResponseFamily.WEAK12,'CMB','CMB','J2000_EQUATORIAL_SOURCEWARD','manufactured',0.)
    with pytest.raises(ProviderUnavailable,match='frame'):
        ConditionalCF4CatalogueLaw(c,p,[assumptions()],shared_zero_point_sigma_mag=.03,calibration_source='x',conditioned_field_convention='ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO',cross_covariance_mode='INDEPENDENT_GIVEN_SHARED_LATENTS',remainder_km_s=[0])


@pytest.mark.parametrize('n,shift,mu_sigma,prior_sigma',[(100,.08,.02,.1),(100,.25,.02,.1),(100,0.,.01,.3)])
def test_high_information_shared_eta_matches_dense_rank_one_gaussian(n,shift,mu_sigma,prior_sigma):
    p=provider();m=float(area_distance_to_modulus(50,3500/299792.458));c=cat(np.full(n,m+shift),np.full(n,3500.))
    a=SlotAssumptions((np.log(50)-1e-9,np.log(50)+1e-9),(-1e-7,1e-7),(-np.inf,np.inf),mu_sigma,150.,'narrow source','no selection','independent residual','narrow motion')
    law=ConditionalCF4CatalogueLaw(c,p,[a]*n,shared_zero_point_sigma_mag=prior_sigma,calibration_source='proper eta prior',conditioned_field_convention='ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO',cross_covariance_mode='INDEPENDENT_GIVEN_SHARED_LATENTS',remainder_km_s=np.zeros(n),order=4)
    expected=multivariate_normal.logpdf(c.modulus,mean=np.full(n,m),cov=np.eye(n)*mu_sigma**2+prior_sigma**2*np.ones((n,n)))+n*multivariate_normal.logpdf([3500.],mean=[3500.],cov=[[150.**2]])
    np.testing.assert_allclose(law.log_likelihood(theta()),expected,atol=1e-7)


def test_selected_block_requires_explicit_nonzero_bound_remainder():
    with pytest.raises(ProviderUnavailable,match='remainder'):
        selected_slot_block(provider(bound=10.),[1,0,0],assumptions())
    block=selected_slot_block(provider(bound=10.),[1,0,0],assumptions(),remainder_km_s=0.)
    assert np.isfinite(block.loglik([33.5,3500],theta(),0.,provider(bound=10.)))


def test_missing_field_convention_refused_and_required_fields_not_zero_filled():
    c=cat([33.5],[3500]);kw=dict(shared_zero_point_sigma_mag=.03,calibration_source='eta',cross_covariance_mode='INDEPENDENT_GIVEN_SHARED_LATENTS',remainder_km_s=[0])
    with pytest.raises(ProviderUnavailable,match='convention'):
        ConditionalCF4CatalogueLaw(c,provider(),[assumptions()],**kw)
    law=ConditionalCF4CatalogueLaw(c,provider(),[assumptions()],conditioned_field_convention='SUPPLIED_FIELDS_REQUIRED',**kw)
    with pytest.raises(ProviderUnavailable,match='supplied'):
        law.log_likelihood(theta())
    assert np.isfinite(law.log_likelihood(theta(),method_offsets_mag=[0.],angular_offsets_mag=[0.],velocity_field_km_s=[0.]))


def test_delayed_selected_block_binding_preserves_omitted_remainder():
    block=selected_slot_block(provider(bound=0.),[1,0,0],assumptions())
    with pytest.raises(ProviderUnavailable,match='remainder'):
        block.loglik([33.5,3500],theta(),0.,provider(bound=10.))


def test_delayed_group_factory_binding_preserves_omitted_remainder():
    from htt.infer.cf4_product_provider import build_group_law_factory
    c=cat([33.5],[3500]);factory=build_group_law_factory(c,0,assumptions(),calibration_source='review prior',remainder_km_s=None)
    with pytest.raises(ProviderUnavailable,match='remainder'):
        factory.bind(provider(ResponseFamily.ENDPOINT13,bound=10.))
    # Omission remains valid under the explicitly exact-zero bound.
    law=factory.bind(provider(ResponseFamily.ENDPOINT13,bound=0.))
    t=np.zeros(13);t[4]=70.
    assert np.isfinite(law.loglik(t,0.))
    assert np.isfinite(law.mean(t,0.)).all()
