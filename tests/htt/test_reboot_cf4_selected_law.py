import importlib.util
import json
import os
from pathlib import Path
import sys
import numpy as np
import pytest
from scipy.stats import norm

REPO=Path(os.environ.get('HTT_RB07_REPO',Path.cwd())).resolve()
CANDIDATE=Path(__file__).resolve().parents[2]
for p in (REPO/'htt',REPO/'htt/src',REPO/'htt/htt'):
    sys.path.insert(0,str(p))
path=CANDIDATE/'htt/htt/htt/infer/reboot_cf4_selected_law.py'
if not path.exists():
    path=REPO/'htt/htt/htt/infer/reboot_cf4_selected_law.py'
spec=importlib.util.spec_from_file_location('rb07_law',path)
law=importlib.util.module_from_spec(spec);sys.modules[spec.name]=law;spec.loader.exec_module(law)


def test_stable_gaussian_interval_both_tails():
    for lo,hi in [(-14.,-13.5),(12.,13.),(-2.,1.)]:
        expected=norm.logsf(lo)+np.log1p(-np.exp(norm.logsf(hi)-norm.logsf(lo))) if lo>0 else norm.logcdf(hi)+np.log1p(-np.exp(norm.logcdf(lo)-norm.logcdf(hi)))
        assert abs(law.log_cdf_interval(lo,hi)-expected)<1e-11
    with pytest.raises(ValueError,match='real'):law.log_cdf_interval(1+1j,2)


def synthetic_sample():
    return law.Sample(np.array([1,2]),np.array([33.,33.2]),np.array([.1,.2]),
                      np.array([4000.,5000.]),np.array([[1.,0.,0.],[0.,1.,0.]]))


def test_analytic_redshift_marginal_matches_bivariate_gaussian():
    from scipy.stats import multivariate_normal
    s=synthetic_sample();model=law.SelectedLaw(s,distance_order=128,eta_order=24)
    theta=[73,100,-200,0];f,z=model.row_terms(theta)
    i,j,e=0,15,10;x=model.x[j];eta=model.eta[e]
    m=73*np.exp(x)+100+model.scenario.kappa*(75*np.exp(x))**2/law.C
    su=model.scenario.s_u_km_s;sp=model.scenario.s_spec_km_s;sm=s.sigma_mu[i]
    mean=[25+law.A*x+law.K*m+eta,m]
    cov=[[sm**2+law.K**2*su**2,law.K*su**2],[law.K*su**2,su**2+sp**2]]
    y=model.y[i]
    direct=multivariate_normal.logpdf([s.mu[i],y],mean=mean,cov=cov)+model.log_jac[i]
    sy2=su**2+sp**2;t=m+su**2/sy2*(y-m)
    condvar=sm**2+law.K**2*su**2*sp**2/sy2
    analytic=norm.logpdf(y,m,np.sqrt(sy2))+norm.logpdf(s.mu[i],25+law.A*x+law.K*t+eta,np.sqrt(condvar))+model.log_jac[i]
    assert abs(direct-analytic)<1e-12
    assert np.isfinite(f).all() and np.isfinite(z).all()


def test_selection_normalizers_distinct_and_loo_retains_known_slot():
    s=synthetic_sample();theta=[73,100,-200,0]
    pre=law.SelectedLaw(s,distance_order=128,eta_order=24)
    post=law.SelectedLaw(s,law.Scenario(selection_semantics=law.SEMANTICS[1]),128,24)
    f,z=pre.row_terms(theta)
    expected=law.logsumexp(pre.log_eta_w+f.sum(0))-law.logsumexp(pre.log_eta_w+z.sum(0))
    held=law.logsumexp(pre.log_eta_w+f[1]+z[0])-law.logsumexp(pre.log_eta_w+z.sum(0))
    assert pre.log_likelihood(theta)==pytest.approx(expected)
    assert pre.log_likelihood(theta,held_index=0)==pytest.approx(held)
    assert abs(pre.log_likelihood(theta)-post.log_likelihood(theta))>1e-5
    with pytest.raises(ValueError):post.log_likelihood(theta,held_index=0)


def test_fitted_generator_obeys_observed_modulus_cut():
    model=law.SelectedLaw(synthetic_sample(),distance_order=128,eta_order=24)
    result=model.predictive([73,100,-200,0],draws=10,seed=123)
    assert result['mu_interval_fraction']==1
    assert result['generator_scope']=='FRESH_SELECTED_CATALOGUE'
    assert len(result['mu_quantiles'][0])==2
    with pytest.raises(ValueError,match='real'):model.log_likelihood(np.array([73,100,-200,0],complex)+1j)


def test_latent_t_conditional_gaussian_precision_and_mean():
    s=synthetic_sample();scenario=law.Scenario()
    m,x,eta,mu,y,sigma=6000.,np.log(90.),.12,33.1,6100.,s.sigma_mu[0]
    mean,var=law.conditional_t_parameters(m,x,eta,mu,y,sigma,scenario)
    expected_precision=(1/scenario.s_u_km_s**2+1/scenario.s_spec_km_s**2+
                        law.K**2/sigma**2)
    expected_mean=(m/scenario.s_u_km_s**2+y/scenario.s_spec_km_s**2+
                   law.K*(mu-25-law.A*x-eta)/sigma**2)/expected_precision
    assert var==pytest.approx(1/expected_precision)
    assert mean==pytest.approx(expected_mean)
    grid=mean+np.linspace(-3,3,31)*np.sqrt(var)
    direct=(norm.logpdf(grid,m,scenario.s_u_km_s)+
            norm.logpdf(y,grid,scenario.s_spec_km_s)+
            norm.logpdf(mu,25+law.A*x+law.K*grid+eta,sigma))
    analytic=norm.logpdf(grid,mean,np.sqrt(var))
    assert np.max(np.abs((direct-direct[15])-(analytic-analytic[15])))<1e-10


def test_latent_bridge_same_state_weights_units_reciprocity_and_ppc():
    model=law.SelectedLaw(synthetic_sample(),distance_order=128,eta_order=24)
    posterior={'status':'NUMERICAL_POSTERIOR_DIAGNOSTIC_ONLY',
               'parameter_draws_H_B':[[73,100,-200,0],[1e9,0,0,0]],
               'normalized_weights':[1.,0.], 'draw_ids':['kept','zero']}
    arrays,summary=law.posterior_latent_bridge(model,posterior,seed=20261014)
    assert arrays['draw_id'].tolist()==['kept','zero']
    assert arrays['normalized_weight'].tolist()==[1.,0.]
    assert arrays['status'].tolist()==['POSITIVE_WEIGHT','ZERO_WEIGHT']
    assert np.isnan(arrays['dA_Mpc'][1]).all()
    assert np.isnan(arrays['eta_mag'][1])
    assert np.isfinite(arrays['dA_Mpc'][0]).all()
    assert np.isfinite(arrays['t_km_s'][0]).all()
    assert np.all(arrays['dA_Mpc'][0]>0)
    assert np.allclose(arrays['dL_Mpc'][0],arrays['dA_Mpc'][0]*(1+arrays['z_true'][0])**2,
                       rtol=2e-15,atol=0)
    assert np.allclose(arrays['raw_Vh_replicated_km_s'][0],
                       law.C*np.expm1(arrays['y_replicated_km_s'][0]/law.C),rtol=1e-15)
    assert summary['positive_weight_draws']==1
    assert summary['zero_weight_draws']==1
    assert summary['weight_sum_unchanged']==1
    assert 0<=summary['repeated_measurement_ppc']['weighted_exceedance_descriptive']<=1
    assert summary['repeated_measurement_ppc']['uniform_p_value_claim'] is False
    assert summary['physical_MES']['unknown_mass']==1
    assert np.isfinite(arrays['chi_square_48_observed_conditional'][0])
    assert np.isfinite(arrays['chi_square_48_replicated_conditional'][0])


def test_latent_eta_condition_uses_shared_observed_f_without_selection_z(monkeypatch):
    model=law.SelectedLaw(synthetic_sample(),distance_order=128,eta_order=24)
    posterior={'status':'NUMERICAL_POSTERIOR_DIAGNOSTIC_ONLY',
               'parameter_draws_H_B':[[73,100,-200,0]],
               'normalized_weights':[1.], 'draw_ids':['kept']}
    original=model.row_terms
    f,z=original(posterior['parameter_draws_H_B'][0])
    expect=model.log_eta_w+f.sum(axis=0)
    expect=np.exp(expect-law.logsumexp(expect))
    assert np.isclose(expect.sum(),1.)
    first,_=law.posterior_latent_bridge(model,posterior,seed=411)
    def changed_z(theta):
        ff,zz=original(theta)
        return ff,zz+np.linspace(-1000,1000,len(model.eta))[None,:]
    monkeypatch.setattr(model,'row_terms',changed_z)
    second,_=law.posterior_latent_bridge(model,posterior,seed=411)
    assert first['eta_quadrature_index'][0]==second['eta_quadrature_index'][0]
    assert first['eta_mag'][0]==second['eta_mag'][0]
    assert np.array_equal(first['x_log_dA_Mpc'],second['x_log_dA_Mpc'])


def test_frozen_source_subset_and_reference_quadrature():
    from obsstat.catalogs.cf4_grouped_observations import load_grouped_observations
    packet=json.loads((REPO/'docs/observational_reboot_20261014/task_packets/RB07_selected_scenario.json').read_text())
    root=REPO/'workdir/raw/cf4_full'
    if not root.exists():pytest.skip('raw CF4 source absent')
    catalog=load_grouped_observations(root/'table3.dat.gz',root/'table4.dat.gz',root/'ReadMe')
    sample=law.selected_sample(catalog,packet)
    assert sample.group_id.tolist()==packet['subset']['group_ids']
    theta=[packet['reference']['H'],*packet['reference']['B']]
    ll192=law.SelectedLaw(sample,distance_order=192,eta_order=40).log_likelihood(theta)
    ll256=law.SelectedLaw(sample,distance_order=256,eta_order=64).log_likelihood(theta)
    assert abs(ll192-packet['reference']['logL'])<1e-9
    assert abs(ll192-ll256)<1e-6
