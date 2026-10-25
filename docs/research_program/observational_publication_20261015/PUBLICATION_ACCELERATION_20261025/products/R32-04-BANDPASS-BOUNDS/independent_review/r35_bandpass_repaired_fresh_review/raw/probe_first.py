import os,sys,json,hashlib,importlib.util,io,contextlib,datetime
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r35_bandpass_repaired_fresh_review')
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025')
P=ROOT/'products/R32-04-BANDPASS-BOUNDS/repair_01'; OLD=P.parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='6567e6a41858b7d549656cd078fcbcc815a04ffa804db5e0c9882bef6a7b252b'
assert H(P/'ARTIFACT_MANIFEST.json')==expected
man=json.loads((P/'ARTIFACT_MANIFEST.json').read_text()); checks=[]
for x in man['files']:
 f=P/x['path']; checks.append({'path':x['path'],'sha256':H(f),'size_bytes':f.stat().st_size,'match':H(f)==x['sha256'] and f.stat().st_size==x['size_bytes']})
assert all(x['match'] for x in checks)
source=ROOT/'evidence/R31/report/data/RESULT.json'; assert H(source)==man['input_sha256']
new=json.loads((P/'RESULT.json').read_text()); old=json.loads((OLD/'RESULT.json').read_text()); src=json.loads(source.read_text())
sp=importlib.util.spec_from_file_location('reviewed_candidate',P/'consumer.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
assert m.SOURCE==source
rows=[]; failures=[]
for name,b in src['branches'].items():
 F=np.array(b['F2']['matrix_7xk']);a=np.array(b['cmb_unity_responses'])
 for metric,d in [('common_reference',m.D),('raw_identity',np.ones(9))]:
  stored=new['branches'][name][metric]; sol=m.solve_metric(F,a,d)
  G=F/d; us,sv,vt=np.linalg.svd(G,full_matrices=True); wa=(us.T@a)/sv;ell=np.linalg.norm(wa); c=(vt[:7].T@(wa/sv))/d
  Nc=np.array(stored['coefficient_nullspace_directions_2x9']).T;Nz=np.array(stored['whitened_nullspace_directions_2x9']).T
  zerr={
   'Nc_transport_max_abs':float(np.max(np.abs(Nc-Nz/d[:,None]))),
   'G_Nz_relative':float(np.linalg.norm(G@Nz)/np.linalg.norm(G)),
   'F_Nc_relative':float(np.linalg.norm(F@Nc)/np.linalg.norm(F)),
   'Nc_M_Nc_error':float(np.linalg.norm(Nc.T@(d[:,None]**2*Nc)-np.eye(2))),
   'Nc_M_c_relative':float(np.linalg.norm(Nc.T@(d*d*np.array(stored['minimum_coefficients_c9'])))/np.linalg.norm(d*np.array(stored['minimum_coefficients_c9']))),
   'full24_null_lift_relative':float(np.linalg.norm(np.kron(F,np.eye(24))@np.kron(Nc,np.eye(24)))/(np.linalg.norm(F)*np.linalg.norm(np.kron(Nc,np.eye(24))))),
   'ell_vs_independent_SVD_relative':float(abs(stored['minimum_budget_ell']-ell)/ell),
   'c_vs_independent_SVD_relative':float(np.linalg.norm(np.array(stored['minimum_coefficients_c9'])-c)/np.linalg.norm(c)),
   'rank_ratio':float(sv[-1]/sv[0]),
   'Fc_relative':float(np.linalg.norm(F@np.array(stored['minimum_coefficients_c9'])-a)/np.linalg.norm(a))}
  assert zerr['Nc_transport_max_abs']==0
  for k in ('G_Nz_relative','F_Nc_relative','Nc_M_Nc_error','Nc_M_c_relative','full24_null_lift_relative','ell_vs_independent_SVD_relative','c_vs_independent_SVD_relative','Fc_relative'):
   assert zerr[k]<1e-10,(name,metric,k,zerr[k])
  Y=np.zeros((7,24));Y[:,0]=F[:,0]+.2*F[:,3];Y[:,1]=-.4*F[:,2];Y[:,13]=.3*a+.1*F[:,8]
  WY=(us.T@Y)/sv[:,None];sref=(wa@WY)/(ell*ell);Wres=WY-wa[:,None]*sref;J=float(np.sum(Wres**2))
  generic=[];zero=[];pure=[];domain=[]
  for scale in [1e-6,1.,1e6]:
   for case,rho,stat in [('empty',.5*np.sqrt(J),'EMPTY'),('equality',np.sqrt(J),'BOUNDARY_UNCERTAIN'),('ball',np.sqrt(J+ell*ell*.25),'BALL')]:
    q=m.identified(scale*Y,F,a,d,sol,float(scale*rho))
    rec={'scale':scale,'case':case,'status':q['status'],'J0':q['J0'],'radius':q['radius'],'center_vs_independent_relative':float(np.linalg.norm(q['center']/scale-sref)/np.linalg.norm(sref)),'uncertainty':q['radius_uncertainty']}
    assert q['status']==stat,(name,metric,rec)
    assert rec['center_vs_independent_relative']<1e-9
    if stat=='BALL':assert abs(q['radius']/scale-.5)<1e-9
    else:assert q['radius'] is None
    generic.append(rec)
   for rho in [0.,1e-6,1.]:
    q=m.identified(np.zeros((7,24)),F,a,d,sol,float(scale*rho))
    assert q['status']==('SINGLETON_EXACT_ZERO' if rho==0 else 'BALL')
    assert np.linalg.norm(q['center'])==0
    assert abs(q['radius']-scale*rho/ell)<=1e-10*max(scale*rho/ell,1e-300)
    zero.append({'scale':scale,'rho':scale*rho,'status':q['status'],'radius':q['radius']})
   yp=np.zeros((7,24));yp[:,0]=scale # Exactly a times (scale*e_0): all seven row bytes equal.
   for rho in [0.,scale*1e-20]:
    q=m.identified(yp,F,a,d,sol,float(rho));rec={'scale':scale,'rho':rho,'status':q['status'],'J0':q['J0'],'radius':q['radius'],'center0':float(q['center'][0]),'exact_center0':scale,'exact_J0':0,'exact_radius':rho/ell,'exact_nonempty_witness':'s=scale*e0,U=0'}
    pure.append(rec)
    if q['status']=='EMPTY':failures.append({'branch':name,'metric':metric,**rec})
  for rho in [-1.,-1e-6,float('nan'),float('inf'),-float('inf'),1e200]:
   try:m.identified(np.zeros((7,24)),F,a,d,sol,rho)
   except ValueError as e:domain.append({'rho':repr(rho),'exception':str(e)})
   else:raise AssertionError(('accepted invalid rho',rho))
  near=[]
  for relgap,stat in [(-1e-7,'EMPTY'),(-1e-11,'BOUNDARY_UNCERTAIN'),(1e-11,'BOUNDARY_UNCERTAIN'),(1e-7,'BALL')]:
   rho=float(np.sqrt(J*(1+relgap)));q=m.identified(Y,F,a,d,sol,rho)
   assert q['status']==stat,(name,metric,relgap,q['status'])
   near.append({'relative_gap':relgap,'status':q['status'],'radius':q['radius']})
  rows.append({'branch':name,'metric':metric,'independent_checks':zerr,'generic_scaling':generic,'zero_data':zero,'invalid_budget':domain,'near_boundary':near,'pure_cmb_zero_residual':pure})
# Retain all exact old/new differences, including changed coordinate serialization.
def diffs(x,y,path=''):
 if isinstance(x,dict) and isinstance(y,dict):
  o=[]
  for k in sorted(set(x)|set(y)):
   pp=path+'/'+k
   if k not in x:o.append({'path':pp,'kind':'added'})
   elif k not in y:o.append({'path':pp,'kind':'removed'})
   else:o+=diffs(x[k],y[k],pp)
  return o
 if x!=y:return [{'path':path,'kind':'changed','old':x if not isinstance(x,list) else 'array','new':y if not isinstance(y,list) else 'array'}]
 return []
delta=diffs(old,new)
branch_equal=[]
for name in m.BRANCHES:
 for metric in ('common_reference','raw_identity'):
  for key in ('minimum_budget_ell','minimum_budget_ell_squared','minimum_coefficients_c9','singular_values_7','CMB_left_projections_7','budget_squared_contributions_7','row_Gram_K_7x7','row_Gram_inverse_7x7','Fc_equals_a_relative_residual','KKT_relative_residual','minimum_budget_from_SVD'):
   assert old['branches'][name][metric][key]==new['branches'][name][metric][key],(name,metric,key)
 branch_equal.append(name)
 npold=np.load(OLD/f'report/generated/{name}_full24.npz');npnew=np.load(P/f'report/generated/{name}_full24.npz')
 assert set(npold.files)==set(npnew.files)
 for key in npold.files:assert np.array_equal(npold[key],npnew[key]),(name,key)
# Execute unmodified candidate once; only relocate its output root into reviewer ownership.
m.HERE=OUT/'replay'
with (OUT/'raw/consumer_replay.stdout').open('w') as f,contextlib.redirect_stdout(f):m.main()
replay=json.loads((OUT/'replay/RESULT.json').read_text());replay_delta=diffs(new,replay)
assert all(x['path'].endswith('/full24_binary') for x in replay_delta),replay_delta
for name in m.BRANCHES:
 p0=np.load(P/f'report/generated/{name}_full24.npz');pr=np.load(OUT/f'replay/report/generated/{name}_full24.npz')
 for key in p0.files:assert np.array_equal(p0[key],pr[key]),(name,key)
result={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_identity':'sha256:'+expected,'input_identity':man['input_identity'],'source_sha256':H(source),'old_candidate_identity':'sha256:'+H(OLD/'ARTIFACT_MANIFEST.json'),'manifest_files_verified':checks,'rows':rows,'pure_cmb_false_empty_cases':failures,'old_new_result_differences':delta,'old_numerical_branch_values_unchanged':branch_equal,'all_six_old_npz_arrays_unchanged':True,'candidate_replay_result_differences':replay_delta,'candidate_replay_all_arrays_equal':True,'formal_packet_binding':'NOT_YET_SELECTED','review_status':'HOLD' if failures else 'SCOPED_PASS'}
(OUT/'raw/independent_probe.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':result['review_status'],'branch_metric_pairs':len(rows),'false_empty_cases':len(failures),'manifest_files':len(checks),'old_result_diff_count':len(delta),'replay_only_differences':'output path relocation','max_null_F_relative':max(x['independent_checks']['F_Nc_relative'] for x in rows),'max_null_M_error':max(x['independent_checks']['Nc_M_Nc_error'] for x in rows),'max_full24_lift_relative':max(x['independent_checks']['full24_null_lift_relative'] for x in rows),'max_c_SVD_relative':max(x['independent_checks']['c_vs_independent_SVD_relative'] for x in rows)},indent=2))
