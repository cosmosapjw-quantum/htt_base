"""Read-only verification of HTT R97 CF4/P1 on the canonical owner's checkout.
Usage from the repository root: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. .venv/bin/python -B /path/to/review.py
The positional membership of one common nuisance vector is a finite counterexample. No optimization is required.
"""
import numpy as np, scipy, sys, hashlib
from scipy.linalg import solve, subspace_angles
from scipy.stats import chi2
from scripts.r97 import cf4_genealogy_and_partial_id as r
import json
R=r.r95
h=R._load_h03(); p=h.source(R.SELECT); n=len(p.z); d=h.proxy_distance(p.mu); sig=h.working_sigma(d,p.e_mu); X=h.velocity_design(d,p.n); y=h.C_KM_S*p.z; weights=[h.window(p.z,sig,c) for c in h.CENTERS]
fits=[h.fit(X,y,w) for w in weights]; A=np.vstack([k['A'] for k in fits]); t=np.concatenate([k['theta'] for k in fits])
with np.load(r.R36_NPZ) as z: pv=z['pv_total'][:36,:36]; c36=z['conditional_R5']; K=z['method_K']; S4=z['method_Sigma']
with np.load(r.R27_NPZ) as z: sb=z['selected_support_7']; print("ids_match",np.array_equal(p.ids,z['group_id']))
c0=pv+(A*sig)@(A*sig).T; D=np.tile(np.eye(9),(4,1))
t3=r._parse_complete_table3_for_selected(p.ids); F=r.cf4_p0b.profile_method_offsets(t3['dm_vals_6'],t3['e_vals_6']); e=t3['e_vals_6']; w=e**-2; wt=w.sum(axis=1); W=np.zeros_like(sb,float); np.divide(w,wt[:,None],where=wt[:,None]>0,out=W[:,:6]); W[wt==0,6]=1
J=A@(W*r.DCZ_DMU_FACTOR*d[:,None]); Jb=A@(sb*r.DCZ_DMU_FACTOR*d[:,None]); S=np.zeros((7,7));S[1:6,1:6]=F['cov_working_mag2'][1:,1:]; u=np.ones(7); v=np.eye(7)[0]-np.eye(7)[6]; M=S+.087**2*np.outer(u,u)
E=np.zeros((7,7));E[:6,:6]=F['F']; print('overlap_F7_rank_null',np.linalg.matrix_rank(E),np.linalg.norm(E@u),np.linalg.norm(E@np.eye(7)[6])); print('cov_ranks',np.linalg.matrix_rank(S),np.linalg.matrix_rank(M),np.linalg.matrix_rank(M+1e-8*np.eye(7))); print('S_common_eig',np.linalg.eigvalsh(M),'M(v)',np.linalg.norm(M@v))
print('centers',h.CENTERS,'window_supports',[np.count_nonzero(w) for w in weights],'intersect',np.logical_and.reduce([w>0 for w in weights]).sum())
print('table_checks',n,(wt>0).sum(),(np.isfinite(e).sum(1)>1).sum(),np.min((t3['dmzp']-t3['dmav'])[wt>0]),np.max((t3['dmzp']-t3['dmav'])[wt>0]),np.max(np.abs(W.sum(1)-1)))
print('rank(K,Jb,Jiv), C0 C36 PV min/max eig',*(np.linalg.matrix_rank(k) for k in (K,Jb,J)),*[(np.linalg.eigvalsh(k)[0],np.linalg.eigvalsh(k)[-1]) for k in (c0,c36,pv)])
L=np.linalg.cholesky(c0);kw=np.linalg.solve(L,K)
for name,j in [('binary',Jb),('ivw',J)]:
 jw=np.linalg.solve(L,j); q=np.linalg.qr(jw)[0]; kproj=q@(q.T@kw); print(name,'inside',np.trace(kproj@S4@kproj.T)/np.trace(kw@S4@kw.T),'angles',np.rad2deg(subspace_angles(kw,jw)))
for name,c in [('r95',c0),('r36',c36)]:
 Z=np.linalg.solve(c,D); B=np.linalg.solve(D.T@Z,Z.T); b=B@t; G=B@J; s=np.sqrt(G[0]@M@G[0]); print(name,'b0',b[0],'w',s,'95_rank6',s*np.sqrt(chi2.ppf(.95,6)),'95_rank7',s*np.sqrt(chi2.ppf(.95,7)),'ridge_std_DirectCal_minus_SNIa',np.sqrt(v@(M+1e-8*np.eye(7))@v),'J_direct',G[:,6])
 print('common_only',name,'linear_unit_mono_dip_quad',.087*(G@u)[0],.087*np.linalg.norm((G@u)[1:4]),.087*np.linalg.norm((G@u)[4:]),'reference_limit')
 for delta in [-.087,.087]:
  k=10**(delta/5); tt=np.concatenate([h.fit(k*X,y,w,influence=False)['theta'] for w in weights]); snew=h.working_sigma(d*k,p.e_mu); tt2=np.concatenate([h.fit(k*X,y,h.window(p.z,snew,cx),influence=False)['theta'] for cx in h.CENTERS]); bb=B@tt; bb2=B@tt2; print('source_shift',name,delta,'fixedw_H_absolute_dip_quad_shifts',bb[0],np.linalg.norm((bb-b)[1:4]),np.linalg.norm((bb-b)[4:]),'scaling_error',np.amax(np.abs(bb-b/k)),'updatedw_H_absolute_dip_quad_shifts',bb2[0],np.linalg.norm((bb2-b)[1:4]),np.linalg.norm((bb2-b)[4:]))
a=json.loads(r.OUT_JSON.read_text());print('closure_hash_valid', [(k,a['sources_sha256'][k]==r._sha(f)) for k,f in [('selected_35970',R.SELECT),('table3_dat',r.RAW_CF4/'table3.dat'),('r36_matrices_npz',r.R36_NPZ),('r27_factor_npz',r.R27_NPZ)]])
print('scipy/numpy/python',scipy.__version__,np.__version__,sys.version.split()[0])

from pathlib import Path
p1=next(Path('docs/research_program/observational_publication_20261015/CONTINUATION_20261018/P1/results').glob('paired_functional_arrays.npz'))
with np.load(p1,allow_pickle=False) as data:
    draws=data['draws']; q=data['q_app']; sample_ids=data['sample_id']; weights=data['weights']
print('P1_input_sha256',r._sha(p1))
print('P1_ratio_parity',np.max(np.abs(q-np.linalg.norm(draws[:,:,4:9],axis=2)/draws[:,:,0])))
C = M + 1e-8*np.eye(7)
r2=chi2.ppf(.95,7)
a=json.loads(r.OUT_JSON.read_text())['sharp_partial_identification_bounds']['R95_R5_ivw_overlap_plus_0p087_tully23sys_95pct_ellipsoid']
width=a['quad_max_ellipsoid_shift']/a['H0_point']
deltacommon=np.sqrt(r2)*.087*np.ones(7)
print('common_delta_mag',deltacommon[0],'mahal2',deltacommon@np.linalg.solve(C,deltacommon),'cutoff',r2)
for sign in [-1,1]:
    s1=(J@(sign*deltacommon)).reshape(4,9)
    x=draws+s1; q1=np.linalg.norm(x[:,:,4:9],axis=2)/x[:,:,0]
    print('sign',sign,'max_abs_dq_by_window',np.max(abs(q-q1),axis=0),'counts_exceed_width',np.sum(abs(q-q1)>width,axis=0),'tails',weights@(q1>.05))
delta=np.array([.315481238721,.301087828206,.304561550799,.305795937348,.308176649253,.321630403743,.315480198825])
mahal=delta@np.linalg.solve(C,delta)
T=J.reshape(4,9,7)[2]
x=draws[:,2]+T@delta
q3=np.linalg.norm(x[:,4:9],axis=1)/x[:,0]
actual_count=np.count_nonzero(q3>.05)
reported_count=np.count_nonzero(q[:,2]+width>.05)
print('delta_mag',delta.tolist(),'mahal2',mahal,'chi2_cutoff',r2,'window_index',2)
print('third_window_response',T@delta)
print('width',width,'n_draws',len(draws),'actual_count',actual_count,'reported_upper_count',reported_count,'actual_weighted_tail',weights@(q3>.05),'reported_weighted_upper',weights@(q[:,2]+width>.05))
print('min_positive_margin',min((q3-.05)[q3>.05]))
assert mahal < r2 and actual_count == 1972 and reported_count == 1971
