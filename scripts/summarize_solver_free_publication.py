"""Three solver-free audit calculations from frozen compact result envelopes."""
import json, hashlib
from pathlib import Path
import numpy as np
from scipy.stats import beta, norm, chi2

import argparse
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
ROOT=Path(__file__).resolve().parents[1]
OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/'docs/observational_reboot_20261014/results'
def read(path):
    return json.loads(path.read_text())
def identity(path):
    return {'path':str(path.relative_to(ROOT)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def cp(k,n):
    return [float(beta.ppf(.025,k,n-k+1)) if k else 0.,float(beta.ppf(.975,k+1,n-k)) if k<n else 1.]

cfpath=DATA/'cf4/selected_v2/result.json'; refpath=DATA/'cf4/quadrature_refinement_v2/result.json'
cf=read(cfpath); ref=read(refpath); replacements={r['index']:r for r in ref['refinements']}
base=np.array(cf['fit']['best']['theta'])
rows=[]
for s in cf['sensitivities']:
    new=replacements.get(s['index']); fit=(new or s)['fit']['best']
    accepted=(new['status']=='ACCEPTED_CONDITIONAL_QUADRATURE') if new else s['quadrature_acceptance']
    rows.append({'change':s['change'],'H_endpoint_MLE':fit['theta'][0], 'H_shift_from_baseline_MLE':fit['theta'][0]-float(base[0]), 'accepted_quadrature':accepted,'refinement_source':new is not None})
loo=cf['leave_one_group_out']
a1={'id':'ADD01','kind':'conditional_selected_law_sensitivity_summary','inputs':[identity(cfpath),identity(refpath)], 'baseline_H_MLE':float(base[0]),'sensitivities':rows,'same_preselection_H_MLE_range':[min(r['H_endpoint_MLE'] for r in rows if 'selection_semantics' not in r['change']),max(r['H_endpoint_MLE'] for r in rows if 'selection_semantics' not in r['change'])], 'loo_H_range':[min(r['fit_theta'][0] for r in loo),max(r['fit_theta'][0] for r in loo)],'largest_loo_endpoint_vector_shift_km_s':max(float(np.linalg.norm(np.array(r['fit_theta'][1:])-base[1:])) for r in loo),'scope':'Existing fixed-slot scenario sensitivity; no posterior model weights; refined results supersede failed low-order checks.'}

sp=DATA/'smica_response_scan_v2/calibration.json'; clp=DATA/'class_noise_v1/result.json'; ip=DATA/'cf4/injection_v1/result.json'
sm=read(sp)['global_joint_null']; cl=read(clp)['calibration']; inj=read(ip)['summary']['coverage_proxy']
a2={'id':'ADD02','kind':'finite_monte_carlo_uncertainty','inputs':[identity(sp),identity(clp),identity(ip)],'SMICA_scan':{'k_ge':sm['k_ge'],'B':sm['B'],'plus_one_rank':(sm['k_ge']+1)/(sm['B']+1),'conditional_iid_tail_probability_CP95':cp(sm['k_ge'],sm['B'])},'CLASS_split_noise':{'k_ge':cl['exceedances'],'B':cl['calibration_rows'],'plus_one_rank':(cl['exceedances']+1)/(cl['calibration_rows']+1),'conditional_iid_tail_probability_CP95':cp(cl['exceedances'],cl['calibration_rows'])},'CF4_95_Wald_coverage_proxy':[{'parameter_index':i,'covered':k,'n':32,'CP95':cp(k,32)} for i,k in enumerate(next(r['covered_counts'] for r in inj if r['level']==.95))],'scope':'CI for binomial tail probability conditional on fixed observed statistic/training, not interval for realized rank; physical null adequacy remains separate.'}

gp=DATA/'gaia_bias_sensitivity_v1/result.json'; ga=read(gp)
coef=np.array(ga['coefficients_mas_year'])*1000; sigma=np.array(ga['sampling_sigma_microas_year']); box=np.array(ga['box_support_microas_year'])[ga['bias_sets']['raw_box_microas_year_each_coordinate'].index(10.)]
z=float(norm.ppf(1-.05/(2*6))); ellradius=float(np.sqrt(chi2.ppf(.95,6)))
a3={'id':'ADD03','kind':'gaia_fixed_proxy_simultaneous_sensitivity','inputs':[identity(gp)],'coefficient_order':ga['coefficient_order'],'coefficient_microas_year':coef.tolist(),'z_coordinatewise':(coef/sigma).tolist(),'zero_in_all_coordinatewise_1p96_intervals':bool(np.all(np.abs(coef)<=1.96*sigma)),'box_at_10_over_sampling_1p96sigma':(box/(1.96*sigma)).tolist(),'box_bound_microas_year_where_support_equals_1p96sigma':(10*1.96*sigma/box).tolist(),'Gaussian_proxy_Bonferroni_95_critical':z,'Gaussian_proxy_Bonferroni_halfwidth_without_bias_microas_year':(z*sigma).tolist(),'Gaussian_proxy_Bonferroni_plus_box10_halfwidth_microas_year':(z*sigma+box).tolist(),'Gaussian_proxy_6D_ellipsoid_radius':ellradius,'scope':'Fixed-design block-diagonal Gaussian proxy only; simultaneous coordinatewise rectangle follows union bound plus deterministic per-coefficient support; no empirical selection coverage or physical bias budget inferred.'}
result={'source_commit':'89621f4c9a6f63449813587a0fadeb13287f8e10','requested_runtime':'gpt-6.1-sol/high','observed_runtime':'UNKNOWN','no_native_solver':True,'no_ODE':True,'calculations':[a1,a2,a3]}
(OUT/'ADDITIONAL_CALCULATIONS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'calculations':len(result['calculations']),'output':str(OUT/'ADDITIONAL_CALCULATIONS.json')}))
