from pathlib import Path
import sys,json
import numpy as np
from scipy.linalg import norm
P=Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_repair_independent_review')
C=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT/repair_01')
sys.path.insert(0,str(C))
from optical_joint import joint_test,lift_matrix,KAPPA,NumericalProfileFailure,B3
s=np.diag([.001,-.001,0.]);k=KAPPA*lift_matrix(s)
records=[];bad=[]
for r in (1.,.01,1e-4):
 for ed_ratio in (100.,1000.,10000.):
  ed=ed_ratio*r
  for c_ratio in (0.,.5,1.,1.0001):
   c=c_ratio*r;lo=max(c-ed,-r);hi=min(c+ed,r)
   if lo>hi:continue
   for delta in (1e-10,1e-9,3e-9,9e-9,1e-7,1e-5):
    target=hi+delta*r
    o=k@np.array([target,0.,0.]);exact_min=float(norm(k[:,0]))*(target-hi)
    b=exact_min*.5
    args={'o':o.tolist(),'s':s.tolist(),'d_obs':[c,0,0],'budget':b,'e_d':ed,'d_max':r}
    case={'inputs':args,'interval':[lo,hi],'target':target,'analytic_minimum_residual':exact_min}
    try:
     out=joint_test(o,s,np.array([c,0,0]),b,e_d=ed,d_max=r)
     case['observed']=out
     if out['compatible']:
      d=np.array(out['profiled_d']); case['direct_violation']=float(norm(d-[c,0,0]))-ed;case['physical_violation']=float(norm(d))-r
      bad.append(case)
    except Exception as ex:case['exception']={'type':type(ex).__name__,'code':getattr(ex,'code',None),'message':str(ex)}
    records.append(case)
(P/'EXTREME_RATIO_INTERVAL_CASES.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
(P/'EXTREME_RATIO_INTERVAL_COUNTEREXAMPLES.json').write_text(json.dumps(bad,indent=2,allow_nan=False)+'\n')
print(json.dumps({'cases':len(records),'typed_failure_count':sum('exception'in q for q in records),'false_accept_count':len(bad),'first_10':bad[:10]},indent=2))
