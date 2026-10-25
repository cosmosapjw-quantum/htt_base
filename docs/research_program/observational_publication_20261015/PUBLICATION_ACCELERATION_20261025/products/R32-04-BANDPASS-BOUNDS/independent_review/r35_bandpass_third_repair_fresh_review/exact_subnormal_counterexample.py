"""Exact-binary, rational-contrast falsifier: no model change or new inputs."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
import pathlib,importlib.util,json,hashlib,numpy as np,sympy as sp,mpmath as mp
OUT=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-04-BANDPASS-BOUNDS/repair_03')
spec=importlib.util.spec_from_file_location('candidate',ROOT/'consumer.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
assert hashlib.sha256(c.SOURCE.read_bytes()).hexdigest()==c.SOURCE_SHA
F=np.array(json.loads(c.SOURCE.read_text())['branches']['A_BT_1e-06']['F2']['matrix_7xk'],float);d=np.ones(9);a=np.ones(7)
Y=np.zeros((7,24));Y[:,0]=[float.fromhex(x) for x in ['0x1.a2fe76a3fb140p-499',*['0x1.a2fe76a3f9475p-499']*5,'0x1.a2fe76a3f77aap-499']]
rho=float.fromhex('0x1.1b1bf25a690e5p-535')
rat=lambda x:sp.Rational(*float(x).as_integer_ratio())
H=sp.zeros(6,7)
for i in range(6):H[i,0]=-1;H[i,i+1]=1
G=sp.Matrix([[rat(x) for x in row] for row in F]);A=H*G;W=(A*A.T).inv(method='DM');P=sp.eye(9)-A.T*W*A
ell2=1/(G[0,:]*P*G[0,:].T)[0];y=sp.Matrix([rat(x) for x in Y[:,0]]);h=H*y
J0=(h.T*W*h)[0];center=y[0]-(G[0,:]*A.T*W*h)[0];budget=rat(rho)**2
out=c.identified(Y,F,a,d,c.solve_metric(F,a,d),rho)
serial=json.loads(json.dumps({k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in out.items()},allow_nan=False))
assert serial['status']=='BALL'
cs=rat(serial['center'][0]);radius=rat(serial['radius']);error=abs(cs-center)
maxcost=J0+ell2*(radius+error)**2;mincost=J0+ell2*(radius-error)**2
maxerr=max(abs(maxcost-budget),abs(mincost-budget))
policy=sp.Rational(1,10**9)*budget
# With one active coordinate, both continuous extrema are rational. These
# decisions use exact integers; decimal formatting is only for the receipt.
assert maxerr>policy
witnesses=[]
for sign in [-1,1]:
 w=float(serial['center'][0]+sign*serial['radius']);cost=J0+ell2*(rat(w)-center)**2
 witnesses.append({'sign':sign,'coordinate_hex':w.hex(),'cost_over_budget':str(sp.N(cost/budget,45)),'relative_budget_error':str(sp.N((cost-budget)/budget,45)),'violates_fixed_relative_policy':bool(abs(cost-budget)>policy)})
assert any(w['violates_fixed_relative_policy'] for w in witnesses)
result={'finding_id':'BP-05','class':'numeric','branch':'A_BT_1e-06','metric':'raw_identity','source_sha256':c.SOURCE_SHA,'candidate_sha256':hashlib.sha256((ROOT/'ARTIFACT_MANIFEST.json').read_bytes()).hexdigest(),'consumer_sha256':hashlib.sha256((ROOT/'consumer.py').read_bytes()).hexdigest(),'input_generation':'Y[:,0]=1e-150; Y[0,0]+=1e-150*1e-12; Y[6,0]-=1e-150*1e-12; all other 23 coordinates zero','Y_col0_hex':[float(x).hex() for x in Y[:,0]],'rho_hex':rho.hex(),'exact_budget_squared':str(sp.N(budget,55)),'exact_J0':str(sp.N(J0,55)),'exact_center_col0':str(sp.N(center,55)),'exact_ell_squared':str(sp.N(ell2,55)),'reported':serial,'reported_center_hex':serial['center'][0].hex(),'reported_radius_hex':serial['radius'].hex(),'reported_J0_relative_error':str(sp.N(abs(rat(serial['J0'])-J0)/J0,45)),'binary64_tolerance':1e-9*max(rho*rho,serial['J0']),'full_sphere_maximum_relative_budget_error':str(sp.N(maxerr/budget,45)),'full_sphere_error_over_fixed_policy':str(sp.N(maxerr/policy,45)),'full_sphere_maximum_cost_over_budget':str(sp.N(maxcost/budget,45)),'exact_rational_policy_violation':bool(maxerr>policy),'serialized_direction_witnesses':witnesses,'mathematical_reference':'Rational 6x9 contrast minimum; ell2=1/(g0 (I-A.T(AA.T)^-1 A) g0.T); J0=(Hy).T(AA.T)^-1(Hy); center=y0-g0 A.T(AA.T)^-1 Hy. Continuous extrema J0+ell2*(r +/- abs(c_report-c_exact))^2.'}
(OUT/'raw/exact_subnormal_counterexample.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='reported'},indent=2))
