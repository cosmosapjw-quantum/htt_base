from pathlib import Path
import json, importlib.util, math
import numpy as np
import sympy as sp
R=Path('/mnt/extdrive/workdir/htt_open_data/r35_bandpass_second_repair_fresh_review/raw')
P=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025')
spec=importlib.util.spec_from_file_location('candidate',P/'products/R32-04-BANDPASS-BOUNDS/repair_02/consumer.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
x=json.loads((P/'evidence/R31/report/data/RESULT.json').read_text())['branches']['A_BT_1e-06'];F=np.array(x['F2']['matrix_7xk']);a=np.ones(7);d=np.ones(9);sol=c.solve_metric(F,a,d)
def r(x):return sp.Rational(*float(x).as_integer_ratio())
def exact(x):return {'numerator':str(sp.numer(x)),'denominator':str(sp.denom(x)),'decimal':str(sp.N(x,60))}
f=sp.Matrix([[r(x) for x in row] for row in F]);H=sp.zeros(6,7)
for i in range(6):H[i,0]=-1;H[i,i+1]=1
B=H*f;V=(B*B.T).inv(method='DM');assert B*B.T*V==sp.eye(6)
Y=np.zeros((7,24));Y[:,0]=1.;Y[0,0]+=1e-14;Y[6,0]-=1e-14
y=sp.Matrix([r(x) for x in Y[:,0]]);dy=H*y;u=B.T*V*dy;j=(u.T*u)[0];y_minus_fu=y-f*u
assert all(v==y_minus_fu[0] for v in y_minus_fu)
s=y_minus_fu[0];rho=2*math.sqrt(float(j));out=c.identified(Y,F,a,d,sol,rho)
# Exact constrained minimum cost at the actual serialized candidate center.
k=f*f.T;ki=k.inv(method='DM');aa=sp.ones(7,1);ell2=(aa.T*ki*aa)[0];s_out=r(out['center'][0]);rr=y-aa*s_out;u_out=f.T*ki*rr
assert f*u_out==rr
actual_cost=(u_out.T*u_out)[0];assert actual_cost==j+ell2*(s_out-s)**2
budget=r(rho)**2
hp=c.high_precision_J0(Y,F,a,d,float(np.linalg.cond(sol['K'])),float(np.linalg.norm(np.linalg.solve(sol['L'],Y))**2))
residual_exact_serialized=sp.Matrix([r(x) for x in out['residual_7x24'][:,0]])
result={'branch':'A_BT_1e-06','metric':'raw M=I9','a':[1.]*7,'Y_nonzero_column':0,'Y_col0':[float(x) for x in Y[:,0]],'Y_col0_hex':[float(x).hex() for x in Y[:,0]],'all_other_Y_columns':'exact zero','rho':rho,'rho_hex':rho.hex(),'returned':{'status':out['status'],'center_col0':float(out['center'][0]),'center_col0_hex':float(out['center'][0]).hex(),'other_center_coordinates_exactly_zero':bool(np.all(out['center'][1:]==0)),'J0':out['J0'],'radius':out['radius'],'radius_uncertainty':out['radius_uncertainty'],'residual_col0':out['residual_7x24'][:,0].tolist()},'exact':{'J0':exact(j),'center0':exact(s),'ell2':exact(ell2),'rho_squared':exact(budget),'minimum_budget_at_returned_center':exact(actual_cost),'center_cost_over_rho_squared':exact(actual_cost/budget),'strict_positive_cost_excess':exact(actual_cost-budget),'feasible_U_col0':[exact(v) for v in u],'all_other_U_columns':'exact zero','feasible_U_reconstructs_Y_at_exact_center':True,'returned_center_minimum_U_col0':[exact(v) for v in u_out],'returned_center_minimum_U_reconstructs_Y':True},'high_precision_fallback':{'J0':hp[0],'error_scale':hp[1],'actual_J0_conversion_error':float(abs(r(hp[0])-j)),'J0_error_covered':bool(abs(r(hp[0])-j)<=r(hp[1]))},'proof':'Exact rational B=H F and V=(B B^T)^-1. U*=B^T V H Y minimizes ||U|| under H F U=H Y; Y-FU* has equal rows, giving exact center and J0. Independently, exact K^-1 gives U_at_returned_center and its cost, agreeing exactly with J0+ell2*(s_returned-s_exact)^2 > rho^2. Thus no permitted U realizes the returned center. All other23 columns are zero.'}
(R/'exact_counterexample.json').write_text(json.dumps(result,indent=2)+'\n');print('ratio',float(actual_cost/budget),'J0 error covered',result['high_precision_fallback']['J0_error_covered'])
