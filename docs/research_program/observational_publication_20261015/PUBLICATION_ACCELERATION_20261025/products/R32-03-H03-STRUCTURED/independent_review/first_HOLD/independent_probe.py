from pathlib import Path
import ast, hashlib, json, platform, time
import numpy as np
import scipy
from scipy.linalg import eigh, null_space, lstsq, solve_triangular
from scipy.optimize import brentq, minimize
from scipy.stats import chi2
start=time.perf_counter()
repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
base=repo/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'
p=base/'products/R32-03-H03-STRUCTURED'
out=Path('/mnt/extdrive/workdir/htt_open_data/r35_h03_fresh_independent_review')
a=json.loads((p/'generated/analysis.json').read_text()); car=json.loads((p/'generated/source_carrier.json').read_text())
src=json.loads((base/'evidence/sources/H03_SOURCE_TOMOGRAPHY.json').read_text())
old=json.loads((base/'evidence/output/physical_results.json').read_text())
man=json.loads((p/'ARTIFACT_MANIFEST.json').read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def err(a,b):return float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
ident={'manifest':sha(p/'ARTIFACT_MANIFEST.json'),'artifacts':{},'sources':{}}
assert ident['manifest']=='85ac1bfdfc71dea645c01421811ed1e5d95df617034077c532feee6052a769ba'
for x in man['artifacts']:
 f=p/x['path'];ok=sha(f)==x['sha256'] and f.stat().st_size==x['bytes'];assert ok;ident['artifacts'][x['path']]=ok
for x in man['source_identities']:
 f=Path(x['path']);ok=sha(f)==x['sha256'];assert ok;ident['sources'][x['path']]=ok
wins=src['monopole_dipole_STF2_windows'];ids=np.array([[9*i+1,9*i+2,9*i+3] for i in range(4)]).ravel()
C36=np.array(src['joint_covariance_36x36']);C=C36[np.ix_(ids,ids)]
y=np.array([w['theta9'][1:4] for w in wins]).ravel();R=np.concatenate([np.array(w['bulk_velocity_design_response_9x3_per_Mpc'])[1:4] for w in wins]);X=np.concatenate((R,np.tile(np.eye(3),(4,1))),axis=1)
assert err(y,old['data_dipoles'])==0 and err(C,old['data_covariance'])==0 and err(R,old['bulk_response'])==0
assert err(C36,car['source_joint_covariance_36x36'])==0
assert err(car['window_theta9_all_physical_coefficients_km_s_Mpc'],[w['theta9'] for w in wins])==0
assert car['physical_rate_tensors']==old['rate_tensors']
for arr,key in ((y,'y_signed_12_km_s_Mpc'),(C,'C_dipole_12x12'),(R,'R_12x3_inverse_Mpc'),(X,'X_12x6')):assert err(arr,car[key])==0
# Independent symmetric-eigen whitening and six-dimensional left-nullspace.
evalC,vecC=eigh(C);W=(vecC/np.sqrt(evalC))@vecC.T;A=W@X
Z=null_space(A.T);r=Z.T@W@y
T=float(r@r);tau=float(chi2.ppf(.95,6));eta=float(np.sqrt(T)-np.sqrt(tau))
assert Z.shape==(12,6) and np.linalg.norm(Z.T@A)<1e-10
assert abs(T-23.396720522667167)<1e-9 and abs(tau-12.591587243743977)<1e-12 and abs(eta-1.2885530036501112)<1e-9
z=np.array([w['z_center'] for w in wins]);fp=np.array([w['source_method_distance_weight_fractions']['FP'] for w in wins]);Dz=np.kron(((z-.04)/src['width_z'])[:,None],np.eye(3));Df=np.kron((fp-fp[0])[:,None],np.eye(3));designs={'depth_slope':Dz,'FP_composition':Df,'joint':np.column_stack((Dz,Df))}
results={}
for name,D in designs.items():
 ref=a['designs'][name];B=Z.T@W@D;H=B.T@B;g=B.T@r
 U,s,Vt=np.linalg.svd(B,full_matrices=False);rank=int(np.sum(s/s[0]>=1e-10))
 ls=lstsq(B,r,lapack_driver='gelsy')[0];perp=r-B@ls;floor=float(perp@perp);sat=float(np.linalg.norm(ls))
 assert err(D,ref['D_12xp_km_s_Mpc_per_unit_eta'])<1e-14
 assert rank==ref['rank_B'] and abs(floor-ref['T_floor'])<1e-10 and abs(sat-ref['rho_sat'])<1e-10
 assert err(s,ref['singular_values_all'])<1e-10
 # Check signed 12D data with the candidate's declared Cholesky coordinate frame.
 L=np.linalg.cholesky(C);Ac=solve_triangular(L,X,lower=True);qc=np.linalg.qr(Ac)[0];Pc=np.eye(12)-qc@qc.T;rc=Pc@solve_triangular(L,y,lower=True);Bc=Pc@solve_triangular(L,D,lower=True)
 assert err(Bc,ref['B_12xp_whitened'])<1e-12
 assert err(rc-Bc@ls,ref['r_perp_signed_whitened_12'])<1e-11
 def solve_lam(lam):return np.linalg.solve(H+lam*np.eye(D.shape[1]),g)
 def loss(e):return float(np.linalg.norm(r-B@e)**2)
 row={'rank':rank,'T_floor':floor,'rho_sat':sat,'minimum_singular_ratio':float(s[-1]/s[0])}
 if floor<tau:
  hi=1.
  while loss(solve_lam(hi))<tau:hi*=2
  lam=brentq(lambda t:loss(solve_lam(t))-tau,0,hi,xtol=1e-14,rtol=1e-14)
  opt=solve_lam(lam);rho=float(np.linalg.norm(opt));w=ref['crossing_witness']
  assert abs(rho-ref['rho95'])<1e-10 and err(opt,w['eta_dimensionless'])<1e-10
  # A second independent constrained solve of min ||eta||^2 subject to full residual <= tau.
  fit=minimize(lambda e:float(e@e),np.zeros(D.shape[1]),jac=lambda e:2*e,
    constraints=[{'type':'ineq','fun':lambda e:tau-loss(e),'jac':lambda e:2*B.T@(r-B@e)}],method='SLSQP',options={'ftol':1e-12,'maxiter':300})
  assert abs(np.linalg.norm(fit.x)-rho)<1e-7 and abs(loss(fit.x)-tau)<1e-7
  signal=lstsq(W@X,W@(y-D@opt),lapack_driver='gelsy')[0];res=y-D@opt-X@signal;direct=float(res@np.linalg.solve(C,res));kkt=float(np.linalg.norm((H+lam*np.eye(D.shape[1]))@opt-g))
  assert abs(direct-tau)<1e-8 and kkt<1e-10
  for actual,key in ((D@opt,'D_eta_signed_12_km_s_Mpc'),(Bc@opt,'projected_correction_signed_whitened_12'),(X@signal,'signal_fit_signed_12_km_s_Mpc'),(res,'signed_residual_12_km_s_Mpc'),(solve_triangular(L,res,lower=True),'signed_whitened_residual_12')):assert err(actual,w[key])<1e-10
  assert err(signal[:3],w['bulk_b_km_s'])<1e-8 and err(signal[3:],w['rate_d_km_s_Mpc'])<1e-10
  assert np.linalg.norm(B@opt)>=eta and rho>=eta/s[0]
  lower=opt*(1-1e-5);assert loss(lower)>tau
  row.update(rho95=rho,q95=float(np.linalg.norm(B@opt)),q_min=float(np.sqrt(T-floor)-np.sqrt(tau-floor)),lambda95=lam,T_direct=direct,KKT_norm=kkt,SLSQP_success=bool(fit.success),SLSQP_message=fit.message,SLSQP_norm=float(np.linalg.norm(fit.x)),SLSQP_T=loss(fit.x),threshold_T_bracket=[loss(solve_lam(0)),loss(solve_lam(hi))])
 else:row.update(rho95=None,unattainable_proved_by_floor=True)
 # Every exported curve point is reconstructed using a normal-equation trust-region root.
 curve_error=0.
 for rho,v in zip(ref['curve']['rho'],ref['curve']['T_min']):
  if rho==0:t=T
  elif rho>=sat:t=floor
  else:
   hi=1.
   while np.linalg.norm(solve_lam(hi))>rho:hi*=2
   lam=brentq(lambda t:np.linalg.norm(solve_lam(t))-rho,0,hi,xtol=1e-13,rtol=1e-14)
   t=loss(solve_lam(lam))
  curve_error=max(curve_error,abs(t-v))
 assert curve_error<1e-8;row['curve_max_abs_error']=curve_error
 results[name]=row
# Independent proof-oriented floor equality fixture, and concrete helper probes.
namespace={'np':np,'brentq':brentq}
tree=ast.parse((p/'consumer.py').read_text())
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ('svd_data','at_lambda','bracket_root','threshold','curve_at_rho'):
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(p/'consumer.py'),'exec'),namespace)
probe={}
for delta in (0.,5e-10,-5e-10):
 fl=tau+delta;res=namespace['threshold'](np.array([1.]),np.array([1.]),fl,1.,fl+1.,tau)
 probe['floor_minus_tau_'+str(delta)]={'status':res[0],'returned_budget':res[1],'actual_min_T':fl,'strictly_attainable':bool(fl<=tau)}
Bd=Pc@Ac;ud,sd,ssd,vd,ad,pd,fd,satd,rankd=namespace['svd_data'](Bd,rc)
probe['D_equals_X_actual_svd']={'projected_norm':float(np.linalg.norm(Bd)),'rank':rankd,'floor':fd,'saturation':satd,'threshold_status':namespace['threshold'](ssd,ad,fd,satd,T,tau)[0]}
# q_min expression as written in analyse omits exact floor equality.
probe['exact_floor_equality_image_budget']={'contract_expected':1.,'consumer_ternary_result':float(np.sqrt(tau+1-tau)-np.sqrt(tau-tau)) if tau<tau<tau+1 else (0. if tau+1<=tau else None)}
block=C.copy()
for i in range(4):
 for j in range(4):
  if i!=j:block[3*i:3*i+3,3*j:3*j+3]=0
 eb,vb=eigh(block);Wb=(vb/np.sqrt(eb))@vb.T;zb=null_space((Wb@X).T);rb=zb.T@Wb@y;wrong=float(rb@rb)
assert abs(wrong-8.925712182985682)<1e-9
report={'candidate_identity':ident['manifest'],'identity_checks':ident,'method':'independent symmetric eigen whitening plus 6D left nullspace; normal-equation lambda solves; separate SLSQP constrained budget solve; no candidate main or repository audit harness executed','environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'T0':T,'tau95':tau,'eta95':eta,'covariance_min_eigenvalue':float(evalC[0]),'full_source_36_covariance_min_eigenvalue':float(eigh(C36,eigvals_only=True)[0]),'wrong_block_covariance_T':wrong,'designs':results,'edge_probes':probe,'elapsed_seconds':time.perf_counter()-start}
(out/'INDEPENDENT_NUMERICS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
