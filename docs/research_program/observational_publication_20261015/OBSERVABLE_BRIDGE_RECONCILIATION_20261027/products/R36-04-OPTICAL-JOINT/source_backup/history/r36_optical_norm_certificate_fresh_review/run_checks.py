from pathlib import Path
from fractions import Fraction as F
import sys,json,time,subprocess,os,hashlib
import numpy as np
out=Path(__file__).resolve().parent
rel=Path('docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT/repair_02')
code=out/'fixture'/rel
sys.path.insert(0,str(code))
import optical_joint as oj
checks=[]
def run(name,fun):
 t=time.monotonic()
 try:r=fun(); result={'name':name,'result':r}
 except Exception as e:result={'name':name,'exception_type':type(e).__name__,'exception':str(e),'code':getattr(e,'code',None)}
 result['wall_seconds']=time.monotonic()-t;checks.append(result);print(json.dumps(result,allow_nan=False),flush=True)

def empty_case():
 s=np.diag([.001,-.001,0.]);d=np.array([.125,1e-60,0]);rad=.125
 gap=sum(F(float(x))**2 for x in d)-F(rad)**2
 o=oj.KAPPA*oj.lift_matrix(s)@d
 result=oj.joint_test(o,s,d,1e-7,e_d=0,d_max=rad)
 return {'input':{'S':s.tolist(),'d_obs':d.tolist(),'e_d':0,'d_max':rad,'O':o.tolist(),'budget':1e-7},'exact_feasible_set_empty':gap>0,'squared_norm_excess_numerator':str(gap.numerator),'squared_norm_excess_denominator':str(gap.denominator),'candidate':result,'unexpected_compatible':result['compatible']}
run('strict_original_physical_ball_fraction_counterexample',empty_case)
run('exact_tangent_representable',lambda:oj.joint_test(np.zeros(7),np.diag([.001,-.001,0]),np.array([.25,0,0]),1e-3,e_d=.125,d_max=.125))
run('empty_separated',lambda:oj.joint_test(np.zeros(7),np.diag([.001,-.001,0]),np.array([.251,0,0]),1,e_d=.125,d_max=.125))
run('physical_zero',lambda:oj.joint_test(np.zeros(7),np.diag([.001,-.001,0]),np.array([.125,0,0]),0,e_d=.125,d_max=0))
run('zero_s_equal_budget_boundary',lambda:oj.joint_test(np.r_[.001,np.zeros(6)],np.zeros((3,3)),np.zeros(3),.001))
run('zero_s_exact_zero',lambda:oj.joint_test(np.zeros(7),np.zeros((3,3)),np.zeros(3),0))
(out/'INDEPENDENT_INITIAL_CHECKS.json').write_text(json.dumps(checks,indent=2,allow_nan=False)+'\n')
commands=[]
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(out/'mplconfig'))
for name,cmd in [('PYTEST',[sys.executable,'-m','pytest','-q','-c','/dev/null','-p','no:cacheprovider',str(code/'test_optical_joint.py')]),('CONSUMER',[sys.executable,str(code/'consume.py')])]:
 t=time.monotonic()
 with (out/(name+'.stdout')).open('w') as stdout,(out/(name+'.stderr')).open('w') as stderr:
  p=subprocess.run(cmd,cwd=out/'fixture',env=env,stdout=stdout,stderr=stderr)
 receipt={'name':name,'command':cmd,'cwd':str(out/'fixture'),'exit_code':p.returncode,'wall_seconds':time.monotonic()-t,'stdout':str(out/(name+'.stdout')),'stderr':str(out/(name+'.stderr'))};commands.append(receipt);print(json.dumps(receipt),flush=True)
(out/'COMMAND_RECEIPT.json').write_text(json.dumps(commands,indent=2)+'\n')
