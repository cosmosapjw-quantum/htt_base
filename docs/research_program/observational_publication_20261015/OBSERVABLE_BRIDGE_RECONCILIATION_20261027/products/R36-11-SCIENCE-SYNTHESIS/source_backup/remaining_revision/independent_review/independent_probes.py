from pathlib import Path
import json,hashlib,numpy as np
from scipy.stats import beta,chi2
R=Path('/mnt/extdrive/workdir/htt_open_data/r36_remaining_manuscript_fresh_review');repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base');pkg=repo/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-11-SCIENCE-SYNTHESIS/remaining_manuscript_candidate';c=json.loads((pkg/'EDITOR_CONTRACT.json').read_text());m=json.loads((pkg/'candidate/OVERLAY_MANIFEST.json').read_text());out={}
def p(k):return repo/c['source_bindings'][k]['repo_relative_path']
def j(k):return json.loads(p(k).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b,tol=1e-12):assert np.allclose(a,b,atol=tol,rtol=tol),(np.max(abs(np.array(a)-b)),tol)
for k,b in c['source_bindings'].items():assert sha(p(k))==b['sha256'],k
for b in m['files']:assert sha(pkg/'candidate'/b['path'])==b['postimage_sha256'],b['path']
# Installed preimage and source locators, checked without importing the assembler.
s=R/'fixture'/c['publication_plan'][0]['root']/'r36_bridge';sources={}
for k,b in c['source_bindings'].items():
 current=R/'fixture'/b['repo_relative_path'];old=s/'baseline'/b['repo_relative_path'];q=current if sha(current)==b['sha256'] else old
 assert q.exists() and sha(q)==b['sha256'],k;sources[k]=str(q)
for rel,b in c['production_preimages_and_retained_artifacts'].items():
 q=s/'baseline'/rel if b['mutable_in_overlay'] else R/'fixture'/rel
 assert sha(q)==b['sha256'],rel
out['identities']={'sources':len(sources),'candidate_files':len(m['files']),'old_preimages_retained':len(c['production_preimages_and_retained_artifacts'])}
(R/'INSTALLED_SOURCE_RESOLUTION.json').write_text(json.dumps(sources,indent=2)+'\n')
# Complete source data equality, not merely summaries or helper status words.
supp=json.loads((s/'NUMERICAL_SUPPLEMENT.json').read_text())
for target,key in [('01_operator_result','01_result'),('02_result','02_result'),('02_sensitivity','02_sensitivity'),('08_full_result','08_result'),('05_full_result','05_result'),('10_full_table','10_table')]:assert supp[target]==j(key),target
# CF4 old and stipulated covariance owners remain distinct; direct saved-array contraction.
A=np.load(p('01_operator'));M=np.load(p('02_matrices'));sub=np.load(p('02_subset_matrices'))
near(M['baseline'],A['covariance36']);near(M['conditional_R5'],M['pv_total'][:36,:36]+150**2*(A['A_raw']@A['A_raw'].T)+M['method_K']@M['method_Sigma']@M['method_K'].T)
near(M['pv_total'],M['band1']+M['band2']);near(A['AN'],j('01_result')['AN_36x3_inverse_Mpc']);assert np.linalg.norm(M['pv_total'][:36,36:])>0
ratios={}
for name,v in j('02_sensitivity')['results'].items():
 ratios[name]=[]
 for a,b in enumerate(v['bands_sum_blocks']):
  sl=slice(a*36,a*36+36);ratio=float(np.trace(sub[name][sl,sl])/np.trace(M['pv_total'][sl,sl]));near(ratio,b['trace_ratio_to_full_sample']);ratios[name].append(ratio)
assert abs(ratios['exclude_FP'][2]-1.1710463175)<1e-10
out['CF4']={'same_radius_ratios':ratios,'conditional_trace':float(np.trace(M['conditional_R5'])),'baseline_trace':float(np.trace(M['baseline'])),'total_PV_R5_trace':float(np.trace(M['pv_total'][:36,:36])),'full_cross_radius_and_window_retained':True}
# SN fit algebra and contrast from sealed coefficient outputs, no raw refit.
sn=j('08_result');out['SN']={}
for key in ['primary','lower_z_sensitivity']:
 v=sn[key];f=v['fits']['full'];C=np.array(v['full_16x16_covariance_mag2']);a=np.array(v['low_8_mag']);b=np.array(v['high_8_mag']);D=np.c_[-np.eye(8),np.eye(8)]
 near(D@C@D.T,v['high_minus_low_8x8_covariance_mag2']);near(b-a,v['high_minus_low_8_mag']);near(C,f['covariance_mag2']);near(np.r_[a,b],f['coefficients_mag']);near(f['delta_T'],f['T_null']-f['T_full']);near(f['p_chi2_conditional'],chi2.sf(f['delta_T'],16));near(v['simultaneous_95pct_16D_ellipsoid_squared_radius'],chi2.ppf(.95,16))
 assert np.linalg.eigvalsh(C)[0]>0 and np.any(C[:8,8:]!=0);assert v['chart_both_side_max_coefficient_difference_mag']<1e-14;assert v['chart_one_side_falsifier_max_difference_mag']>1e-4
 out['SN'][key]={'rows':[v['n_low'],v['n_high']],'DeltaT':f['delta_T'],'conditional_p':f['p_chi2_conditional'],'full_covariance_min_eigenvalue':float(np.linalg.eigvalsh(C)[0]),'chart_coefficient_difference':v['chart_both_side_max_coefficient_difference_mag']}
# Radiation: reconstruct order-statistic regions/physical hits using saved outputs.
rad=j('05_result');samples=np.load(p('05_samples'));out['radiation']=[]
for v in rad['methods']:
 pre=v['case']+'_'+v['method'];truth=rad['truth'][v['case']]
 calD=samples[pre+'_cal_D'];testD=samples[pre+'_test_D'];calA=samples[pre+'_cal_A'];testA=samples[pre+'_test_A'];errors=np.linalg.norm(calD-np.array(v['D_noiseless']),axis=1);radius=np.sort(errors)[7782];near(radius,v['D_radius']);near(2*radius,v['D_width'])
 qs=np.sort(calA-v['A_noiseless'])[[203,7987]];near(qs,v['A_error_quantiles']);lo=np.maximum(0,testA-qs[1]);hi=testA-qs[0];empty=hi<0;width=np.where(empty,np.nan,hi-lo)
 d_hit=np.linalg.norm(testD-np.array(truth['physical_D']),axis=1)<=radius;a_hit=(~empty)&(lo<=truth['physical_A'])&(truth['physical_A']<=hi)
 near(np.cov(samples[pre+'_cal_fP'],rowvar=False),v['fP_covariance']);near(np.nanmean(width),v['A_nonempty_width']['mean']);assert int((~empty).sum())==v['A_nonempty_width']['count'];near(empty.mean(),v['A_empty_fraction'])
 for target,hit in [('D',d_hit),('A',a_hit)]:
  cv=v[target+'_physical_target_coverage'];k=int(hit.sum());assert k==cv['hits'];N=len(hit);bounds=[0 if k==0 else beta.ppf(.025,k,N-k+1),1 if k==N else beta.ppf(.975,k+1,N-k)];near(bounds,[cv['lower'],cv['upper']]);assert np.array_equal(hit,samples[pre+'_test_'+target+'_physical_hit'])
 near(v['calibration_content']['D_beta95'],beta.ppf([.025,.975],7783,8192-7783));near(v['calibration_content']['A_equal_tail_beta95'],beta.ppf([.025,.975],7988-204,8192-(7988-204)))
 out['radiation'].append({'case':v['case'],'method':v['method'],'D_hits':int(d_hit.sum()),'A_hits':int(a_hit.sum()),'empty':int(empty.sum()),'nonempty_mean_width':float(np.nanmean(width))})
for im in rad['response_compression']['L2_L4']:
 mat=np.array(im['response_matrix_over_rho0']);assert mat.shape==(5,5);near(mat,mat.T);near(np.linalg.eigvalsh(mat),im['response_eigenvalues_over_rho0']);assert np.linalg.eigvalsh(mat)[0]>0
# Geometry tensor equations, spectra and derivative ranks independently from retained objects.
g=j('10_table');out['geometry']={}
for name in ['II','VII0matched','I','flatVII0']:
 center=g['controls'][name];n=np.array(center['n_bar']);S=np.array(center['S_bar']);h=center['h_bar'];ric=2*n@n-np.trace(n)*n+(.5*np.trace(n)**2-np.trace(n@n))*np.eye(3);near(ric,center['ricci']);near(np.trace(ric),center['scalar']);near(3*h*h-.5*np.sum(S*S)+.5*np.trace(ric),center['density_bar'])
 im=g['images'][name];JJ=np.array(im['joint_J']);H=np.array(im['joint_H']);JG=np.array(im['geometry_J']);assert JJ.shape==(10,12) and H.shape==(10,12,12);near(H,H.transpose(0,2,1));gr=int(np.linalg.matrix_rank(JG,tol=1e-10));jr=int(np.linalg.matrix_rank(JJ,tol=1e-10));assert (gr,jr)=={'II':(6,9),'VII0matched':(6,10),'I':(0,1),'flatVII0':(3,6)}[name]
 for key,mat in [('geometry_svd',JG),('joint_svd',JJ)]:near(np.linalg.svd(mat,compute_uv=False),im[key]['singular_values'])
 out['geometry'][name]={'geometry_rank':gr,'joint_rank':jr,'Ricci_spectrum':np.linalg.eigvalsh(ric).tolist(),'full_J_H_retained':True}
near(g['matched_orbit_separation'],np.sqrt(2));near(g['matched_tensor_radius_sum'],g['images']['II']['ricci_F_bound']+g['images']['VII0matched']['ricci_F_bound']);assert g['matched_orbit_separation']>g['matched_tensor_radius_sum']
assert len(p('10_lrs').read_text().splitlines())==280
out['status']='PASS';(R/'INDEPENDENT_NUMERIC_PROBES.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
