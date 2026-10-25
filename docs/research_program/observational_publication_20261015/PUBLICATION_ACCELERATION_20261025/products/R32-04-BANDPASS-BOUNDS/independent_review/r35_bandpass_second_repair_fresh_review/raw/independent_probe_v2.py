from pathlib import Path
import hashlib, importlib.util, json, math, platform, sys, time
import numpy as np
import sympy as sp
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025')
CAND=ROOT/'products/R32-04-BANDPASS-BOUNDS/repair_02'
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r35_bandpass_second_repair_fresh_review/raw')
spec=importlib.util.spec_from_file_location('candidate',CAND/'consumer.py'); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
data=json.loads((ROOT/'evidence/R31/report/data/RESULT.json').read_text())
def rat(x):
 p,q=float(x).as_integer_ratio(); return sp.Rational(p,q)
def dec(x):return str(sp.N(x,50))
H=sp.zeros(6,7)
for i in range(6):H[i,0]=-1;H[i,i+1]=1
result={'method':'exact rational contrast quotient: H rows e_i-e_0; W=(H F diag(d)^-2 F^T H^T)^-1; J0=(HY)^T W(HY). Center Y0-(K[0,:]H^T)W HY; ell2=1/(K00-k0H W k0H^T). All inputs lifted by float.as_integer_ratio. No mpmath, no consumer J0 or Kinv used in reference.','python':sys.version,'numpy':np.__version__,'sympy':sp.__version__,'pairs':[],'counterexamples':[]}
t0=time.monotonic()
for name,branch in data['branches'].items():
 F=np.array(branch['F2']['matrix_7xk']);a=np.array(branch['cmb_unity_responses'])
 for metric,d in [('common',mod.D),('raw',np.ones(9))]:
  sol=mod.solve_metric(F,a,d)
  G=sp.Matrix([[rat(F[i,j])/rat(d[j]) for j in range(9)] for i in range(7)])
  K=G*G.T;B=H*G;W=(B*B.T).inv(method='DM');kh=K[0,:]*H.T
  ell2=1/(K[0,0]-(kh*W*kh.T)[0]);pair={'branch':name,'metric':metric,'ell2_exact_decimal':dec(ell2),'condition_K':float(np.linalg.cond(sol['K'])),'cases':[]}
  for scale in [1e-6,1.,1e6]:
   for perturb in [1e-4,1e-12,1e-14]:
    Y=np.zeros((7,24));Y[:,0]=scale;Y[0,0]+=scale*perturb;Y[6,0]-=scale*perturb
    y=sp.Matrix([rat(x) for x in Y[:,0]]);dy=H*y
    j=(dy.T*W*dy)[0];center=y[0]-(kh*W*dy)[0]
    for side,factor in [('low',.5),('near_low',1.-1e-7),('boundary',1.),('near_high',1.+1e-7),('high',2.)]:
     rho=factor*math.sqrt(float(j));rr=mod.identified(Y,F,a,d,sol,rho)
     budget=rat(rho)**2;computed_center=rat(rr['center'][0]);cost=j+ell2*(computed_center-center)**2
     classified_side='EMPTY' if budget<j else 'BALL' if budget>j else 'BOUNDARY'
     case={'scale':scale,'perturbation_relative':perturb,'side':side,'rho':rho,'status':rr['status'],'J0':rr['J0'],'J0_exact_decimal':dec(j),'center0':float(rr['center'][0]),'center0_exact_decimal':dec(center),'center_error_abs':float(abs(computed_center-center)),'radius':rr['radius'],'exact_radius':math.sqrt(float((budget-j)/ell2)) if budget>=j else None,'center_min_budget_over_rho2':float(cost/budget),'exact_side':classified_side,'false_side':rr['status'] in ['EMPTY','BALL'] and rr['status']!=classified_side,'returned_ball_center_infeasible':bool(rr['status']=='BALL' and cost>budget)}
     pair['cases'].append(case)
     if case['returned_ball_center_infeasible'] or case['false_side']:
      result['counterexamples'].append({'branch':name,'metric':metric,**case})
  result['pairs'].append(pair)
  print(name,metric,'counterexamples',sum(x['returned_ball_center_infeasible'] or x['false_side'] for x in pair['cases']),flush=True)
result['elapsed_seconds']=time.monotonic()-t0
result['total_cases']=sum(len(x['cases']) for x in result['pairs'])
result['false_side_count']=sum(x['false_side'] for x in result['counterexamples'])
result['infeasible_center_count']=sum(x['returned_ball_center_infeasible'] for x in result['counterexamples'])
(OUT/'independent_probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['elapsed_seconds','total_cases','false_side_count','infeasible_center_count']})); print('FIRST',json.dumps(result['counterexamples'][:1],indent=2))
