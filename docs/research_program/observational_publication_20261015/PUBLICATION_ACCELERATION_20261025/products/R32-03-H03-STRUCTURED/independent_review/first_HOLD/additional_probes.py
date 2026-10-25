from pathlib import Path
import ast,json,time
import numpy as np
from scipy.linalg import eigh,null_space
from scipy.optimize import brentq
p=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-03-H03-STRUCTURED');o=Path('/mnt/extdrive/workdir/htt_open_data/r35_h03_fresh_independent_review');start=time.perf_counter();a=json.loads((p/'generated/analysis.json').read_text());c=json.loads((p/'generated/source_carrier.json').read_text());y=np.array(c['y_signed_12_km_s_Mpc']);C=np.array(c['C_dipole_12x12']);X=np.array(c['X_12x6']);tau=a['tau95']
ns={'np':np,'brentq':brentq}
for n in ast.parse((p/'consumer.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name in ('svd_data','at_lambda','bracket_root','threshold','curve_at_rho'):exec(compile(ast.Module(body=[n],type_ignores=[]),str(p/'consumer.py'),'exec'),ns)
Q=np.linalg.qr(np.linalg.solve(np.linalg.cholesky(C),X))[0];P=np.eye(12)-Q@Q.T;r=P@np.linalg.solve(np.linalg.cholesky(C),y);B=P@np.linalg.solve(np.linalg.cholesky(C),X)
U,s,ss,Vt,alpha,perp,floor,sat,rank=ns['svd_data'](B,r)
zero_result=ns['curve_at_rho'](sat,ss,alpha,floor,sat,float(r@r))[0]
assert rank==6 and abs(zero_result-float(r@r))>.8
# Dense deterministic orthogonal rotation, unlike the producer's 90-degree axis permutation.
R=np.linalg.qr(np.array([[1.,2.,4.],[-3.,2.,5.],[2.,-5.,3.]]))[0];R12=np.kron(np.eye(4),R);R6=np.kron(np.eye(2),R)
rotation={}
for name,d in a['designs'].items():
 D=np.array(d['D_12xp_km_s_Mpc_per_unit_eta']);Dp=R12@D@np.kron(np.eye(D.shape[1]//3),R).T;Cp=R12@C@R12.T;yp=R12@y;Xp=R12@X@R6.T
 ev,V=eigh(Cp);W=(V/np.sqrt(ev))@V.T;Z=null_space((W@Xp).T);rr=Z.T@W@yp;BB=Z.T@W@Dp
 U,s,Vt=np.linalg.svd(BB,full_matrices=False);al=U.T@rr;pp=rr-U@al;fl=float(pp@pp)
 row={'floor_error':abs(fl-d['T_floor']),'T0_error':abs(float(rr@rr)-a['T0'])}
 assert row['floor_error']<1e-10 and row['T0_error']<1e-10
 if fl<tau:
  fun=lambda lam:fl+np.sum((lam*al/(s*s+lam))**2)-tau
  hi=1.
  while fun(hi)<0:hi*=2
  lam=brentq(fun,0,hi);rho=float(np.linalg.norm(s*al/(s*s+lam)))
  row['rho_error']=abs(rho-d['rho95']);assert row['rho_error']<1e-10
 rotation[name]=row
# Support and nonattainment of an out-of-column-space target for a declared non-spanning design.
D=np.array(a['designs']['depth_slope']['D_12xp_km_s_Mpc_per_unit_eta']);B=P@np.linalg.solve(np.linalg.cholesky(C),D);u=np.arange(1.,13.);rho=.8;eta=rho*(B.T@u)/np.linalg.norm(B.T@u);support=float(u@B@eta);expected=rho*np.linalg.norm(B.T@u);assert abs(support-expected)<1e-10
rperp=np.array(a['designs']['depth_slope']['r_perp_signed_whitened_12']);qin=B@eta;qout=qin+rperp/np.linalg.norm(rperp);assert np.linalg.norm(qout-B@np.linalg.pinv(B)@qout)>.999999
result={'zero_design_solver_false_gain':{'expected_rank':0,'observed_rank':rank,'projected_norm':float(np.linalg.norm(P@np.linalg.solve(np.linalg.cholesky(C),X))),'baseline':float(r@r),'solver_T_at_saturation':zero_result,'saturation_budget':sat,'false_improvement':float(r@r)-zero_result},'dense_rotation':rotation,'support_error':float(abs(support-expected)),'out_of_image_distance':float(np.linalg.norm(qout-B@np.linalg.pinv(B)@qout)),'elapsed_seconds':time.perf_counter()-start}
(o/'ADDITIONAL_PROBES.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
