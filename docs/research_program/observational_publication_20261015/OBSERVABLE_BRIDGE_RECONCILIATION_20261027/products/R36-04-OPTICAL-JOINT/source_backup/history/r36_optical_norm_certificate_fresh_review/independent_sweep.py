from pathlib import Path
from fractions import Fraction as F
import sys,json,time
import numpy as np
import mpmath as mp
out=Path(__file__).resolve().parent
code=out/'fixture/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT/repair_02'
sys.path.insert(0,str(code));import optical_joint as oj
rows=[]
def record(name,f):
 try:r=f(); rows.append({'name':name,'result':r})
 except Exception as exc:rows.append({'name':name,'exception':str(exc),'code':getattr(exc,'code',None)})

def bounds_case(n):
 o=np.r_[np.ones(n),np.zeros(7-n)];r=oj.joint_test(o,np.zeros((3,3)),np.zeros(3),2.)
 lo=F(r['certified_lower_bound']);up=F(r['certified_upper_bound'])
 return {'O':o.tolist(),'candidate':r,'exact_lower_exceeds_minimum':lo**2>n,'exact_upper_below_minimum':up**2<n,'exact_score_upper_below_optimum':F(r['score'])**2<F(n,4)}
for n in (2,3):record('display_bound_exact_sqrt_'+str(n),lambda n=n:bounds_case(n))

def sweep():
 s=np.diag([.001,-.001,0.]);counts={'cases':0,'correct_decisions':0,'uncertain':0,'wrong_decisions':0,'invalid_witness':0,'oracle_interval_violations_over_1e-12_relative':0}; details=[]
 for center,ed,rad,target in [(.01,1e-6,.1,.010002),(0,.1,.0001,.0001000000009),(-.003,.001,.1,-.0015),(.003,.001,.003,.005),(0,.01,.005,-.008)]:
  lo=max(center-ed,-rad);hi=min(center+ed,rad)
  for unit in (1e-150,1e-60,1.,1e60,1e120):
   ss=unit*s;scale=np.max(abs(ss));k=(oj.KAPPA*scale)*oj.lift_matrix(ss/scale);o=k@np.array([target,0,0])
   # Independent exact-binary scalar oracle; diagonal STF separates the three signed coordinates.
   with mp.workdps(400):
    a=[mp.mpf(float(x)) for x in k[:,0]];ob=[mp.mpf(float(x)) for x in o];cen=mp.mpf(center);e=mp.mpf(ed);r=mp.mpf(rad)
    exact_lo=max(cen-e,-r);exact_hi=min(cen+e,r);free=sum(x*y for x,y in zip(a,ob))/sum(x*x for x in a);opt=min(max(free,exact_lo),exact_hi);oracle=mp.sqrt(sum((ob[i]-a[i]*opt)**2 for i in range(7)))
   for frac in (.7,1.3):
    budget=float(frac*oracle);entry={'center':center,'ed':ed,'R':rad,'target':target,'unit':unit,'budget_ratio':frac,'oracle':mp.nstr(oracle,35)};counts['cases']+=1
    try:
     result=oj.joint_test(o,ss,np.array([center,0,0]),budget,e_d=ed,d_max=rad)
     correct=result['compatible']==(frac>1);counts['correct_decisions' if correct else 'wrong_decisions']+=1
     witness=[F(x) for x in result['profiled_d']];fc=[F(center),F(0),F(0)];inside=sum((witness[i]-fc[i])**2 for i in range(3))<=F(ed)**2 and sum(x*x for x in witness)<=F(rad)**2
     counts['invalid_witness']+=int(not inside)
     with mp.workdps(400):
      invalid=(mp.mpf(result['certified_lower_bound'])>oracle*(1+mp.mpf('1e-12')) or mp.mpf(result['certified_upper_bound'])<oracle*(1-mp.mpf('1e-12')))
     counts['oracle_interval_violations_over_1e-12_relative']+=int(invalid)
     entry.update(compatible=result['compatible'],correct=correct,exact_witness_inside=inside,lower=result['certified_lower_bound'],upper=result['certified_upper_bound'],method=result['profile_certificate']['candidate_method'])
    except oj.NumericalProfileFailure as exc:counts['uncertain']+=1;entry.update(exception=str(exc),code=exc.code)
    details.append(entry)
 return {'counts':counts,'details':details}
record('independent_one_axis_mp400_oracle_common_output_units',sweep)

def rotations():
 s=np.diag([.001,-.001,0.]);records=[]
 for theta in (.13,.57,1.14):
  axis=np.array([1.,2.,3.]);axis/=np.linalg.norm(axis);cross=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]]);r=np.eye(3)+np.sin(theta)*cross+(1-np.cos(theta))*(cross@cross)
  for center,ed,rad,target,budget,expected in [(.01,1e-6,.1,.0100005,5.606717652542515e-10,True),(0,.1,.0001,.0001000000009,1.0092091825422658e-15,False)]:
   o=oj.KAPPA*oj.lift_matrix(s)@np.array([target,0,0]);tensor=np.tensordot(o,oj.B3,axes=(0,0));rot=np.einsum('ia,jb,kc,abc->ijk',r,r,r,tensor);orc=np.einsum('aijk,ijk->a',oj.B3,rot);cen=r@np.array([center,0,0]);ss=r@s@r.T
   try:
    result=oj.joint_test(orc,ss,cen,budget,e_d=ed,d_max=rad);records.append({'angle':theta,'expected':expected,'compatible':result['compatible'],'correct':result['compatible']==expected})
   except oj.NumericalProfileFailure as exc:records.append({'angle':theta,'expected':expected,'code':exc.code,'exception':str(exc)})
 return records
record('independent_three_axis_rotations',rotations)
record('rank_deficient_S_full_rank_lift',lambda:{'S_rank':int(np.linalg.matrix_rank(np.diag([.001,-.001,0]))),'lift_rank':int(np.linalg.matrix_rank(oj.lift_matrix(np.diag([.001,-.001,0])))),'gram_condition':float(np.linalg.cond(oj.m_matrix(np.diag([.001,-.001,0]))))})
(out/'INDEPENDENT_SWEEP.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n');print(json.dumps([{'name':r['name'],'summary':r.get('result',{}).get('counts') if isinstance(r.get('result'),dict) else r.get('result'),'exception':r.get('exception')} for r in rows],indent=2))
