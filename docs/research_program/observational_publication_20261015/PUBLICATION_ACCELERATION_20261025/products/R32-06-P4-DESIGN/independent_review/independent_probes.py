#!/usr/bin/env python3
"""Independent finite probes; does not import or execute the candidate consumer."""
import hashlib, json, math, platform
from pathlib import Path
import numpy as np
import sympy as sp
OUT=Path(__file__).resolve().parent
REPO=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
CAND=REPO/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-06-P4-DESIGN'
REPORT=CAND/'report'
def read(name): return json.loads((REPORT/name).read_text())
def err(a,b):
 d=np.asarray(a)-np.asarray(b)
 return float(np.max(np.abs(d))) if d.size else 0.
checks={}
def check(name,value,limit=1e-12):
 checks[name]={'residual':float(value),'limit':limit,'pass':bool(value<=limit)}
 if not value<=limit: raise AssertionError((name,value,limit))
B=np.zeros((5,3,3))
B[0]=np.diag([1,-1,0])/math.sqrt(2)
B[1]=np.diag([1,1,-2])/math.sqrt(6)
for a,(i,j) in enumerate([(0,1),(0,2),(1,2)],2):B[a,i,j]=B[a,j,i]=1/math.sqrt(2)
dirs=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1],[3/5,4/5,0],[3/5,0,4/5],[0,3/5,4/5],[1,0,0],[-1,0,0],[0,1,0],[0,0,1]],float)
names=['baseline','endpoint','history','both']; ranks=[12,15,15,18]; equal_ranks=[8,11,11,14]
def construct(q,name,sl=1,sg=1):
 rows=[]
 for i,n in enumerate(dirs):
  r=1 if i<9 else q
  rows.append(list(-n)+list(n)+[r]+list(r*n)+[r*float(n@F@n) for F in B]+[0]*3)
 weights=[1]*13
 if name in ['endpoint','both']:
  for i in range(3):
   row=[0]*18; row[i]=1;rows.append(row);weights.append(1/sl)
 if name in ['history','both']:
  for i in range(3):
   row=[0]*18;row[7+i]=1;row[15+i]=1/3;rows.append(row);weights.append(1/sg)
 J=np.array(rows,float);N=np.zeros(len(rows));N[:13]=1;W=np.diag(weights)
 # This exact scalar quotient is identical for all declared positive addition precisions.
 P=np.eye(len(rows));P[:13,:13]-=np.ones((13,13))/13
 return J,N,W,P,P@W@J
J,N,W,P,A=construct(2,'both');d=np.sqrt(np.sum(A*A,axis=0));L=np.diag(1/d)
def null_basis(q,name):
 cols=[]
 if name in ['baseline','history']:
  for i in range(3):
   c=np.zeros(18);c[i]=c[3+i]=1;cols.append(c)
 if name in ['baseline','endpoint']:
  for i in range(3):
   c=np.zeros(18);c[15+i]=1;cols.append(c)
 if q==1:
  for i in range(3):
   c=np.zeros(18);c[3+i]=-1;c[7+i]=1
   if name in ['history','both']:c[15+i]=-3
   cols.append(c)
  c=np.zeros(18);c[6]=1;cols.append(c)
 return np.column_stack(cols) if cols else np.zeros((18,0))

def proj(K):
 if not K.shape[1]:return np.zeros((18,18))
 Q=np.linalg.qr(K)[0];return Q@Q.T

scales=read('column_scales.json');saved=read('matrices.json');spectra=read('spectra.json')
check('STF_orthonormal',err(B.reshape(5,9)@B.reshape(5,9).T,np.eye(5)))
check('STF_basis',err(B,scales['STF_basis']))
check('scale_d',err(d,scales['d']));check('scale_L',err(np.diag(L),scales['L_diagonal']))
check('STF_signed_reconstruction',err(np.tensordot(scales['example_signed_s'],B,axes=1),scales['example_full_S']))
summary=[]
for name,rank in zip(names,ranks):
 J,N,W,P,A=construct(2,name);a=A@L
 for k,v in {'J':J,'N':N,'W':W,'P':P,'L':L,'A':a,'A_physical':A}.items():check(name+'_'+k,err(v,saved[name][k]))
 check(name+'_P_idempotent',err(P@P,P));check(name+'_P_nuisance',err(P@W@N,0))
 U,s,Vt=np.linalg.svd(a,full_matrices=True);V=Vt.T;rec=spectra[name]
 check(name+'_singular_values',err(s,rec['singular_values_scaled']))
 check(name+'_unscaled_values',err(np.linalg.svd(A,compute_uv=False),rec['singular_values_unscaled']))
 K=d[:,None]*null_basis(2,name);PK=proj(K)
 check(name+'_analytic_kernel_residual',err(a@K,0))
 check(name+'_analytic_kernel_projector',err(PK,rec['kernel_projector']))
 check(name+'_numerical_kernel_projector',err(V[:,rank:]@V[:,rank:].T,rec['kernel_projector']))
 check(name+'_identified_projector',err(np.eye(18)-PK,rec['identified_projector']))
 rv=np.array(rec['full_right_basis'])
 check(name+'_saved_right_orthogonal',err(rv.T@rv,np.eye(18)))
 check(name+'_physical_combinations',err(rv[:,:rank].T@np.diag(d),rec['identified_physical_combinations']))
 nums={str(t):int(sum(s>t*s[0])) for t in [1e-12,1e-10,1e-8]}
 assert all(n==rank for n in nums.values()) and nums==rec['numerical_rank_by_cutoff']
 assert rec['kernel_dimension']==18-rank
 assert (rec['full_vector_inverse_gain'] is None)==(rank<18)
 if rank==18:check('full_inverse_gain',abs(rec['full_vector_inverse_gain']-1/s[-1]))
 summary.append({'design':name,'rank':rank,'nullity':18-rank,'smin':float(s[rank-1]),'cutoffs':nums})
# Independent exact rational-basis rank probes. Rational basis differs by invertible sqrt(2/6) column factors.
rdirs=[[sp.Rational(str(x)) for x in n] for n in dirs]
qb=sp.Symbol('q'); xr=[]
for i,n in enumerate(rdirs):
 x,y,z=n;rho=1 if i<9 else qb;quadr=[x*x-y*y,x*x+y*y-2*z*z,2*x*y,2*x*z,2*y*z]
 xr.append([1,x,y,z]+[rho*x for x in [1,x,y,z]+quadr])
X=sp.Matrix(xr);det=sp.factor(X.det())
assert sp.simplify(det/(qb-1)**4).is_number and det!=0
exact=[]
for q in [sp.Rational(1),sp.Rational(2),sp.Rational(1,2)]:
 for name in names:
  jr=[]
  for i,n in enumerate(rdirs):
   x,y,z=n;r=1 if i<9 else q
   jr.append([-x,-y,-z,x,y,z,r,r*x,r*y,r*z,r*(x*x-y*y),r*(x*x+y*y-2*z*z),r*2*x*y,r*2*x*z,r*2*y*z,0,0,0])
  if name in ['endpoint','both']:
   for i in range(3):row=[0]*18;row[i]=1;jr.append(row)
  if name in ['history','both']:
   for i in range(3):row=[0]*18;row[7+i]=1;row[15+i]=sp.Rational(1,3);jr.append(row)
  j=sp.Matrix(jr);nn=sp.Matrix([1]*13+[0]*(len(jr)-13));rank=j.row_join(nn).rank()-1
  expected=(equal_ranks if q==1 else ranks)[names.index(name)];assert rank==expected
  exact.append({'q':str(q),'design':name,'quotient_rank':rank})
# Complete q=1 kernel spans, and all saved radius/precision grids.
radial=read('radial_grid.json')
near=[]
for row in radial:
 for name in names:
  q=row['q'];rank=(equal_ranks if q==1 else ranks)[names.index(name)]
  a=construct(q,name)[-1]@L;U,s,Vt=np.linalg.svd(a,full_matrices=True)
  check(f'radial_{q}_{name}',err(s,row[name]['singular_values_scaled']))
  K=d[:,None]*null_basis(q,name);assert K.shape[1]==18-rank
  check(f'kernel_residual_{q}_{name}',err(a@K,0))
  near.append({'q':q,'design':name,'analytic_rank':rank,'smin_positive':float(s[rank-1]),'projector_max_error':err(proj(K),Vt[rank:].T@Vt[rank:]),'threshold_ranks':{str(t):int(sum(s>t*s[0])) for t in [1e-12,1e-10,1e-8]}})
for row in read('precision_grid.json'):
 a=construct(2,'both',row['sigma_L'],row['sigma_G'])[-1]@L;s=np.linalg.svd(a,compute_uv=False)
 check(f"precision_{row['sigma_L']}_{row['sigma_G']}",err(s,row['spectrum']))
 check('precision_condition_'+str((row['sigma_L'],row['sigma_G'])),abs(s[0]/s[-1]-row['condition']),1e-10)
# Binary64 near-coincident boundary is outside the prescribed grid, diagnostic only.
finite=[]
for gap in [1e-6,1e-8,1e-10,1e-12,1e-14,1e-16,0]:
 a=construct(1+gap,'both')[-1]@L;s=np.linalg.svd(a,compute_uv=False)
 finite.append({'requested_gap':gap,'represented_gap':float((1+gap)-1),'smin':float(s[-1]),'rank_by_relative_cutoff':{str(t):int(sum(s>t*s[0])) for t in [1e-12,1e-10,1e-8]},'rank_np_default':int(np.linalg.matrix_rank(a))})
# Signed witness values including the alpha compensation.
for name,rec in read('witnesses.json').items():
 J,N,W,P,A=construct(1 if name.startswith('equal_') else 2,'both');theta=np.array(rec['theta']);raw=J@theta+rec['alpha']*N
 assert np.max(abs(theta))<=1
 check(name+'_raw_physical',err(J@theta,rec['raw_physical']))
 check(name+'_raw_nuisance',err(raw,rec['raw_with_nuisance']))
 check(name+'_projected',err(P@W@raw,rec['projected']))
# Deterministic fixtures and saved operator-error grid.
a=construct(2,'both')[-1]@L;s=np.linalg.svd(a,compute_uv=False);smin=s[-1]
f=read('bound_fixture.json');z=np.array(f['z']);D=np.array(f['delta']);e=np.array(f['projected_error']);ah=a+D
eta=float(np.linalg.norm(D,2));eps=float(np.linalg.norm(e));zh=np.linalg.lstsq(ah,a@z+e,rcond=None)[0];bound=(eps+eta*np.linalg.norm(z))/(smin-eta)
check('fixture_estimator',err(zh,f['estimated_z']))
check('fixture_bound',abs(bound-f['certified_bound']))
check('fixture_error',abs(np.linalg.norm(zh-z)-f['actual_error']))
assert np.linalg.norm(zh-z)<=bound+1e-12
P=construct(2,'both')[3];check('full_fixture_error_in_quotient',err(P@e,e))
a0=construct(2,'baseline')[-1]@L;P0=construct(2,'baseline')[3];z0=np.array(f['deficient_z']);e0=np.array(f['deficient_projected_error']);est=np.linalg.pinv(a0,rcond=1e-12)@(a0@z0+e0)
check('deficient_estimator',err(est,f['deficient_estimate']))
check('deficient_target',err((np.eye(18)-proj(d[:,None]*null_basis(2,'baseline')))@z0,f['deficient_identified_target']))
deficient_quotient={'residual_max':err(P0@e0,e0),'norm_stored':float(np.linalg.norm(e0)),'norm_after_projection':float(np.linalg.norm(P0@e0)),'estimate_unchanged_after_projection':err(est,np.linalg.pinv(a0,rcond=1e-12)@(a0@z0+P0@e0))}
for row in read('error_grid.json'):
 ratio=row['eta_ratio']
 if ratio>=1:assert row['status']=='NOT_CERTIFIED_BY_THIS_BOUND' and row['error_bound'] is None
 else:check('error_grid_'+str(ratio),abs(row['error_bound']-(.001+ratio*smin)/(smin*(1-ratio))),1e-10)
# Deterministic independent finite perturbations, including a constructive rank-loss boundary.
rng=np.random.default_rng(270125);max_ratio=0
for _ in range(64):
 zz=rng.normal(size=18);zz/=max(1,np.linalg.norm(zz));ee=rng.normal(size=19);ee=P@ee;ee*=.001/np.linalg.norm(ee)
 dd=rng.normal(size=a.shape);dd=P@dd;dd*=.4*smin/np.linalg.norm(dd,2)
 zz_hat=np.linalg.lstsq(a+dd,a@zz+ee,rcond=None)[0];bb=(np.linalg.norm(ee)+np.linalg.norm(dd,2)*np.linalg.norm(zz))/(smin-np.linalg.norm(dd,2));rr=np.linalg.norm(zz_hat-zz)/bb
 max_ratio=max(max_ratio,float(rr));assert rr<=1+1e-10
u,ss,vt=np.linalg.svd(a,full_matrices=False);boundary=a-smin*np.outer(u[:,-1],vt[-1]);boundary_s=np.linalg.svd(boundary,compute_uv=False)
# Probe the necessary independent-calibration assumption: arbitrary offsets on all six added channels erase both gains.
J,N,W,P,A=construct(2,'both');nuis=np.zeros((19,7));nuis[:13,0]=1;nuis[13:,1:]=np.eye(6);pn=np.eye(19)-nuis@np.linalg.pinv(nuis);unknown_offset_rank=int(np.linalg.matrix_rank(pn@J@L));assert unknown_offset_rank==12
out={'scope':'independent finite response-design probes only','numpy':np.__version__,'sympy':sp.__version__,'python':platform.python_version(),'checks':checks,'nominal':summary,'exact_rank_results':exact,'rational_basis_determinant':str(det),'near_equality_projector_diagnostics':near,'binary64_boundary_diagnostics':finite,'deficient_fixture_quotient_diagnostic':deficient_quotient,'additional_error_cases':64,'maximum_actual_to_bound_ratio':max_ratio,'rank_loss_eta_equals_smin':{'perturbation_norm':smin,'smallest_singular_value':float(boundary_s[-1])},'unknown_added_offsets_quotient_rank':unknown_offset_rank,'all_assertions_passed':True}
(OUT/'raw/probes.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['checks','near_equality_projector_diagnostics','binary64_boundary_diagnostics']},indent=2))
print('check_count',len(checks))
