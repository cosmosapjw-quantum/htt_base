"""Source-qualified six-paper DAG P3/H01 working estimator and response study."""
from __future__ import annotations
from pathlib import Path
import hashlib,json,sys,argparse
import numpy as np
from hubble_window import (SOURCE_SHA,load_cf4,radial_weights,window_hubble,
    cross_window_covariance,dipole_bulk_principal_cosines,inject_response)
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
P=BASE/'source'/'selected_source_observables.npz'
# GitHub-only stage: resolve the existing owner's untouched Loop6 original by SHA.
OWNER_FALLBACK=(HERE.parents[4]/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz') if len(HERE.parents)>4 else Path('/ABSENT_OWNER_CHECKOUT')
OUT=BASE/'results'


def run(output:Path|None=None) -> dict:
    src=load_cf4(P if P.is_file() else OWNER_FALLBACK)
    centers=[.025,.04,.06,.08]
    bandwidth=.012
    ids=['z025','z040','z060','z080']
    scenarios=[];alpha=[];sigmas=[]
    for label,anis in [('source_window',0.),('north_weighted',.6)]:
        this=[]
        for name,center in zip(ids,centers):
            w,d,sig=radial_weights(src,center,bandwidth,ang_alpha=anis)
            h,m=window_hubble(d,src.n,src.z,w)
            method_power={x:float(np.sum((w*d*d)[src.method==x])/np.sum(w*d*d)) for x in np.unique(src.method)}
            cos=dipole_bulk_principal_cosines(d,src.n,w)
            D=np.array([2.,-1.,.5]);B=np.array([240.,-120.,60.]);Q=np.diag([.5,-.25,-.25])
            di,pr=inject_response(d,src.n,w,70.,D,B,Q)
            this.append({'id':name,'redshift_center':center,'angular_coefficient':anis,
                'H_app_working_km_s_Mpc':float(h),
                'effective_distance_Mpc':m['effective_distance_mpc'],
                'directional_window_dipole':m['angular_moment'].tolist(),
                'bulk_response_inverse_Mpc':m['bulk_inverse_mpc'].tolist(),
                'STF2_window_quadrupole':m['quadrupole_moment'].tolist(),
                'method_fraction_of_denominator':method_power,
                'n_eff_diagonal_weight':m['n_eff_weighted'],
                'dipole_vs_bulk_principal_cosines':cos.tolist(),
                'fixed_synthetic_injection':{'direct':di,'moments':pr,'delta':di-pr}})
            alpha.append(m['alpha']);sigmas.append(sig)
        scenarios.append({'model':label,'windows':this})
    # One common declared approximate conditional diagonal sigma_i law.
    # The angular weighting does not change the noise law itself.
    C,R=cross_window_covariance(alpha,sigmas[0])
    # Empirical Monte-Carlo sanity on exactly these *working* window maps;
    # no cosmological/null/selection interpretation.
    rng=np.random.default_rng(20261016);n_mc=3000
    a=np.stack(alpha)
    yy=rng.standard_normal((n_mc,len(src.z)))
    v= (yy*sigmas[0])@a.T
    c_mc=np.cov(v,rowvar=False,ddof=1)
    relative=float(np.linalg.norm(c_mc-C)/np.linalg.norm(C))
    if relative>.10:raise RuntimeError('conditional covariance MC witness failed')
    result={
      'schema':'htt.six_paper_P3_H01_windowed_effective_H/1',
      'paper_dag_ref':'research/htt-observation-publication-dag-20261015@58bb3fa00093e36b5915c8ba87f03d7b14568bd8',
      'paper_id':'P3','node_id':'H01','claim_tier':'SOURCE_CONDITIONED_WORKING_WINDOW_ESTIMATOR_ONLY',
      'source_npz_sha256':SOURCE_SHA,'n_real_CF4_groups':len(src.z),
      'distance':'d_Mpc=10**((dmzp-25)/5), dmzp is published shifted group DM, not true latent distance',
      'redshift_to_velocity':'u_km_s=c*z_CMB linear proxy, NOT exact cosmological recession velocity',
      'noise_assumption':'diagonal sigma²=250²+(H_ref*ln10/5*d*e_dmzp)² (km/s)²; H_ref=70; zero-point covariance & selection unknown',
      'window':'w_i=exp(-0.5*((z_i-zcenter)/0.012)^2)*(1+alpha*n_z)/sigma_i² with alpha 0 or 0.6',
      'conditional_formula':'H_W=sum(w*d*u)/sum(w*d²); C_window=A diag(sigma²) A^T, A_wi=w_wi*d_i/den_w',
      'data_statistical_independence':'SHARED_35970_GROUPS_CORRELATED_WINDOWS_AND_CALIBRATION_UNMODELED',
      'scenarios':scenarios,
      'cross_window_covariance_diagonal_working_law':C.tolist(),
      'cross_window_correlation_diagonal_working_law':R.tolist(),
      'same_conditional_noise_mc_3000':{'seed':20261016,'draws':n_mc,'frobenius_relative_error':relative},
      'physical_status':{'H_geom_Theta_over_3':'NOT_IDENTIFIED','CF4_actual_selection':'UNKNOWN',
        'method_shared_covariance':'UNKNOWN','peculiar_flow_likelihood':'UNKNOWN',
        'geometry_shear_vorticity':'NOT_MEASURED','Bayesian_evidence':'NOT_COMPUTED'},
      'literature_comparators':[
        {'authors':'Boubel et al','doi':'10.1088/1475-7516/2025/03/066'},
        {'authors':'Stiskalek, Desmond, Lavaux','arxiv':'2509.14997'},
        {'authors':'Salzano et al','doi':'10.1016/j.dark.2026.102382'},
        {'authors':'Kalbouneh et al','doi':'10.1088/1475-7516/2026/03/084',
         'note':'additional priority P3 H05 novelty comparator absent from original six-paper novelty matrix'}]
    }
    target=Path(output) if output else OUT/'H01_SOURCE_WINDOW_RESULT.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    return result

if __name__=='__main__':
    cli=argparse.ArgumentParser(description='source-locked P3/H01 working H-window generator')
    cli.add_argument('--output',type=Path,default=None,help='new create-only output JSON; default results/H01_SOURCE_WINDOW_RESULT.json')
    args=cli.parse_args()
    result=run(args.output)
    for group in result['scenarios']:
      print(group['model'],[(x['id'],round(x['H_app_working_km_s_Mpc'],3),round(x['effective_distance_Mpc'],1),max(x['dipole_vs_bulk_principal_cosines'])) for x in group['windows']])
    print('MC covariance error',result['same_conditional_noise_mc_3000']['frobenius_relative_error'])
