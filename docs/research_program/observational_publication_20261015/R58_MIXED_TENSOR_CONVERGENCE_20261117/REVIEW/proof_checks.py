"""Independent review checks. Reads the frozen git object; never writes the repo."""
import ast
import hashlib
import json
import math
import subprocess
from pathlib import Path
import numpy as np

ROOT=Path('/workspace/scratch/ca5a06f498ba/htt_base')
SHA='77f61c17ba33ff28ff4f16a7d42621d8041e5ce4'
PATH='htt/htt/htt/infer/r54_identifiability.py'
source=subprocess.check_output(['git','show',f'{SHA}:{PATH}'],cwd=ROOT,text=True)
module=ast.parse(source)
ns={'np':np,'math':math,'SQRT6':math.sqrt(6.)}
for name in ('wishart_gls_factors','rho_ratio'):
    fun=next(v for v in module.body if isinstance(v,ast.FunctionDef) and v.name==name)
    exec(compile(ast.Module(body=[fun],type_ignores=[]),PATH,'exec'),ns)
res={'source_commit':SHA,'source_path':PATH,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'checks':{}}
res['checks']['T5_invalid_domain_accepted']={'input':{'n':2,'p':3,'k':3},'actual':ns['wishart_gls_factors'](2,3,3),'sample_matrix_rank_max':2,'inverse_defined':False}
with np.errstate(over='ignore',invalid='ignore'):
    actual=ns['rho_ratio'](np.array([0.,1.,1000.,1100.,10000.]))
res['checks']['rho_large_optical_depth']={'tau':[0.,1.,1000.,1100.,10000.],'actual':[float(x) if math.isfinite(x) else 'NaN' for x in actual],'expected_limit':math.sqrt(6.)}
r=.9
prior=np.array([[1.,r],[r,1.]])
rows=[]
for n in (0,1,10,10000):
    cov=np.linalg.inv(np.linalg.inv(prior)+np.diag([n,0.]))
    formula=1-r*r+r*r/(n+1)
    assert math.isclose(cov[1,1],formula,abs_tol=1e-12)
    rows.append({'n':n,'marginal_nu_variance':float(cov[1,1]),'equal_tail_95_width':2*1.959963984540054*math.sqrt(cov[1,1])})
res['checks']['T3_marginal_contraction_counterexample']={'prior_correlation':r,'conditional_nu_variance':1-r*r,'variance_formula':'1-r^2+r^2/(n+1)','derivative':'-r^2/(n+1)^2','values':rows}
c=299792.458
v0=np.array([10.,20.,30.])
v_o=np.array([300.,0.,0.]); v_r=np.zeros(3)
shells=[]
for z in (.1,.2,.5):
    vj=(1+z)*v0
    dr=(v_o-v_r)/c
    da=3.0*(v_o-vj)/c
    closure=da/3.0-dr+(vj-v_r)/c
    shells.append({'z':z,'Vj_km_s':vj.tolist(),'closure_max_abs':float(np.max(np.abs(closure)))})
res['checks']['T9_evolving_homogeneous_tilt']={'approximation':'test congruence of freely moving nonrelativistic particles on FLRW, first order in velocity; physical peculiar velocity scales as a^-1','samples':shells,'constant_velocity_submodel':False,'shell_closure_identity':True}
Path('/workspace/scratch/ca5a06f498ba/proof_checks.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
