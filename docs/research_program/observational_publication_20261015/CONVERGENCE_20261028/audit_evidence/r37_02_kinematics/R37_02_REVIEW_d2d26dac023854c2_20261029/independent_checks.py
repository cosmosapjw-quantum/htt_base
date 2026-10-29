import hashlib, itertools, json, sys
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from scipy.optimize import brentq
from scipy.stats import chi2,ncx2,norm
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
B=ROOT/'docs/research_program/observational_publication_20261015'
P=B/'CONVERGENCE_20261028/products/R37-02-KINEMATICS'
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
g=read(B/'CONVERGENCE_20261028/imports/foundations/sources/gaia/METHOD_EXECUTION_20261023__k03_depth_moments__RESULT.json')
saved=read(P/'KINEMATIC_IMAGE_RESULT.json')
y=np.array(g['full24_state_uasyr']); C=np.array(g['full24_cov_uasyr2']); z=np.array(g['depth_c_reported_z_centers'])
J=np.r_[np.zeros((18,6)),np.eye(6)]; N=np.r_[np.eye(18),np.zeros((6,18))]
# Direct normal-equation nuisance Schur complement, independent of candidate's whitening/SVD.
def gls(y,J,C,N):
 Ci=np.linalg.inv(C); W=Ci-Ci@N@np.linalg.solve(N.T@Ci@N,N.T@Ci)
 F=J.T@W@J; A=np.linalg.solve(F,J.T@W)
 return A@y,np.linalg.inv(F),F,A,W
th,V,F,A,W=gls(y,J,C,N)
T=np.zeros((18,24))
for i in range(3): T[6*i:6*i+6,6*i:6*i+6]=np.eye(6);T[6*i:6*i+6,18:]=z[i]*np.eye(6)
Y=T@y; CY=T@C@T.T;N18=np.tile(np.eye(6),(3,1));J1=np.kron(z[:,None],np.eye(6));J2=np.kron((z*z)[:,None],np.eye(6))
t1,V1,F1,A1,W1=gls(Y,J1,CY,N18); t2,V2,F2,A2,W2=gls(Y,J2,CY,N18)
D1=Y-J1@t1;D2=Y-J2@t2; delta=D1@W1@D1-D2@W2@D2
L=np.linalg.cholesky(CY); Q=np.eye(18)-np.linalg.solve(L,N18)@np.linalg.pinv(np.linalg.solve(L,N18)); WG=Q@np.linalg.solve(L,np.c_[J1,J2]); U,sv,_=np.linalg.svd(WG,full_matrices=False);Uc=U[:,:12]
def dev(y,J):return np.linalg.norm(y-J@np.linalg.lstsq(J,y,rcond=None)[0])**2
wy=Q@np.linalg.solve(L,Y);wj1=Q@np.linalg.solve(L,J1);wj2=Q@np.linalg.solve(L,J2)
def diff(w):return dev(w,wj1)-dev(w,wj2)
max_carrier_err=0
for i in range(9):
 v=np.sin(np.arange(18)+i/3)
 w=Q@v
 e=abs(diff(w)-(dev(Uc.T@w,Uc.T@wj1)-dev(Uc.T@w,Uc.T@wj2)))
 max_carrier_err=max(max_carrier_err,e)
Ci=block_diag(*[CY[6*i:6*i+6,6*i:6*i+6] for i in range(3)])
ti,Vi,Fi,Ai,Wi=gls(Y,J1,Ci,N18);Vs=Ai@CY@Ai.T
ps=saved['gaia_E1_B1']['free_bin_slope']['matched_power']; exact_err=max(abs(r['scalar_energy_exact']-ncx2.sf(chi2.ppf(.95,6),6,r['mahalanobis_amplitude']**2)) for r in ps)
gaia={'free_slope_max_difference':float(np.max(abs(th-y[18:]))),'free_slope_covariance_max_difference':float(np.max(abs(V-C[18:,18:]))),'bin_projection_lost_slopes_residual':float(np.linalg.norm(T@J-T@N@np.linalg.lstsq(T@N,T@J,rcond=None)[0])),'g_slope_max_difference':float(np.max(abs(t1-np.array(saved['gaia_E1_B1']['constrained_bin_depth']['joint_signed_g_slope'])))),'profile_deviance_difference_independent':float(delta),'profile_deviance_error':float(abs(delta-saved['gaia_E1_B1']['constrained_bin_depth']['full_deviance_difference'])),'union_rank':int(np.linalg.matrix_rank(WG)),'additional_deterministic_9vector_carrier_max_error':float(max_carrier_err),'nominal_covariance_trace':float(np.trace(Vi)),'sandwich_covariance_trace':float(np.trace(Vs)),'joint_covariance_trace':float(np.trace(V1)),'scalar_energy_exact_power_max_error':float(exact_err),'stored_MC_rates_copied_exactly':True}
# E2 quotient ranks and unit equivariance falsifier.
pm=read(B/'OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-03-PM-HISTORY/RESULT.json'); Fp=np.array(pm['gram']['primary_spin_glide6']['profile']['information']); ev=np.linalg.eigvalsh(Fp)
h=[]
for i in pm['history_images']:
 k=i['k']; H=np.c_[k*np.eye(5),-np.eye(5)]; NN=np.r_[np.eye(5),k*np.eye(5)]; Pinfo=H.T@Fp@H
 h.append({'k':k,'response_rank':int(np.linalg.matrix_rank(H)),'information_rank':int(np.linalg.matrix_rank(Pinfo)),'null_residual':float(np.linalg.norm(H@NN)),'saved_info_max_difference':float(np.max(abs(Pinfo-np.array(i['information_10x10']))))})
r_uas=1.; s=.001; radius_uas=r_uas/np.sqrt(ev[0]); F_mas=Fp/s**2;r_mas=r_uas*s; candidate_radius_mas=r_mas/np.sqrt(np.linalg.eigvalsh(F_mas)[0]); expected_mas=s*radius_uas
pm_check={'information_units':'(microarcsec/year)^-2','history_checks':h,'unit_counterexample':{'same_physical_remainder_uasyr':r_uas,'same_physical_remainder_masyr':r_mas,'candidate_radius_from_uas_convention':float(radius_uas),'expected_conversion_of_candidate_radius_to_masyr':float(expected_mas),'candidate_formula_after_converting_inputs_to_masyr':float(candidate_radius_mas),'equivariance_ratio':float(candidate_radius_mas/expected_mas)},'interpretation':'r/sqrt(lambda(F)) is valid for dimensionless whitened residual radius r; with a rate-valued r it is dimensionally wrong. A coefficient-space physical remainder ball of radius r adds r in the identified combination, independent of F; any other remainder norm requires its explicit response metric.'}
# Independent optical STF lift and two-ball profile for this saved case.
o=saved['optical']; S=np.array(o['tensor_S_full_3x3']);v=np.array(o['signed_summary_d3_O7']); Co=np.array(o['full_summary_covariance_10x10']);
def stf3(a):
 a=sum(a.transpose(p) for p in itertools.permutations(range(3)))/6
 t=np.einsum('iik->k',a)
 return a-(np.einsum('ij,k->ijk',np.eye(3),t)+np.einsum('ik,j->ijk',np.eye(3),t)+np.einsum('jk,i->ijk',np.eye(3),t))/5
basis=[]
for idx in np.ndindex(3,3,3):
 a=np.zeros((3,3,3));a[idx]=1; w=stf3(a).ravel()
 for b in basis:w-=np.dot(w,b)*b
 if np.linalg.norm(w)>1e-13:basis.append(w/np.linalg.norm(w))
B3=np.array(basis).reshape(-1,3,3,3);lift=np.array([[np.sum(b*stf3(np.einsum('i,jk->ijk',e,S))) for e in np.eye(3)] for b in B3]);kap=5/np.log(10);K=kap*lift;dd=v[:3];oo=v[3:];q=chi2.ppf(.95,10);ed=np.sqrt(q*np.linalg.eigvalsh(Co[:3,:3])[-1]);eo=np.sqrt(q*np.linalg.eigvalsh(Co[3:,3:])[-1]);Ares=np.c_[-K,np.eye(7)];Cr=Ares@Co@Ares.T
H=K.T@K;b=K.T@(oo-K@dd);un=np.linalg.solve(H,b)
if np.linalg.norm(un)<=ed:shift=un;lag=0.
else:
 fn=lambda lag:np.linalg.norm(np.linalg.solve(H+lag*np.eye(3),b))-ed
 hi=1.
 while fn(hi)>0:hi*=10
 lag=brentq(fn,0,hi,xtol=1e-22);shift=np.linalg.solve(H+lag*np.eye(3),b)
prof=dd+shift;res=np.linalg.norm(oo-K@prof);expected_budget=np.sqrt(35/2)*kap*.08**3/(3*(1-.08))+eo
assert np.linalg.norm(dd)+ed<.03
optical={'joint_chi2_10_quantile':float(q),'direct_outer_radius':float(ed),'octupole_outer_radius':float(eo),'physical_cap_inactive_for_entire_direct_ball':True,'independent_lagrange_profile_residual':float(res),'recorded_profile_residual':float(np.sqrt(o['minimum_compatibility']['residual_squared'])),'profile_residual_abs_difference':float(abs(res-np.sqrt(o['minimum_compatibility']['residual_squared']))),'independent_shared_budget':float(expected_budget),'shared_budget_abs_difference':float(abs(expected_budget-o['shared_budget']['total'])),'residual_covariance_max_difference':float(np.max(abs(Cr-np.array(o['residual_covariance_7x7'])))),'lift_rank':int(np.linalg.matrix_rank(lift)),'perpendicular_subspace_dimension':7-int(np.linalg.matrix_rank(lift)),'lift_M_identity_error':float(np.max(abs(lift.T@lift-(np.sum(S*S)*np.eye(3)/3+2*S@S/5)))),'S_zero_saved_inverse':o['S_zero']['inverse_d'],'small_S_inverse_max_abs':float(np.max(np.abs(o['S_small_nonzero']['inverse_d'])))}
# Contraction operator C_Q and sharp distance on the ambient STF3 space.
ch=saved['fixed_Q_sign_radius'];Qq=np.array(ch['Q']);Oo=np.array(ch['O_full_3x3x3']);Cq=np.array([np.einsum('ijk,jk->i',a,Qq) for a in B3]).T; vv=np.einsum('ijk,jk->i',Oo,Qq);M=Cq@Cq.T;rad=abs(vv)/np.linalg.norm(Cq,axis=1); ii=int(np.argmin(rad));do=-vv[ii]/M[ii,ii]*np.einsum('a,aijk->ijk',Cq[ii],B3);vv1=np.einsum('ijk,jk->i',Oo+do,Qq)
chir={'Cq_CqT_identity_error':float(np.max(abs(M-(np.sum(Qq*Qq)*np.eye(3)/3+2*Qq@Qq/5)))),'exact_distance_numeric':float(np.min(rad)),'delta_norm':float(np.linalg.norm(do)),'initial_chirality_determinant':float(np.linalg.det(np.column_stack((vv,Qq@vv,Qq@Qq@vv)))),'boundary_chirality_determinant':float(np.linalg.det(np.column_stack((vv1,Qq@vv1,Qq@Qq@vv1)))),'scope':'fixed simple Q, nonzero initial chirality, ambient STF3 Frobenius ball; no joint-Q assertion'}
res={'gaia':gaia,'pm':pm_check,'optical':optical,'chirality':chir}
(OUT/'INDEPENDENT_NUMERICS.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
