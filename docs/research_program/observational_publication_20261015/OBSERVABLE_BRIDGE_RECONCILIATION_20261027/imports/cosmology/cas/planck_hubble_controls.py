"""Ideal Gaussian morphology benchmark and a joint Hubble-budget control."""
from pathlib import Path
import json
import numpy as np
from scipy.stats import beta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
seed=20261026;N=2**20;observed_U=.1197448
rng=np.random.default_rng(seed);us=[]
for _ in range(16):
 z=rng.normal(size=(N//16,7));z/=np.linalg.norm(z,axis=1)[:,None]
 us.append(3*np.sqrt(3)*abs(z[:,0]*z[:,1]*z[:,2]))
u=np.concatenate(us);k=int(np.sum(u<=observed_U));cdf=k/N
interval=[float(beta.ppf(.025,k,N-k+1)),float(beta.ppf(.975,k+1,N-k))]
mean_exact=15*np.sqrt(3)/(64*np.pi);second_exact=3/77
summary={'model':'Independent full-sky isotropic Gaussian STF2 and STF3; conditional on a nondegenerate quadrupole; no Planck processing/noise/selection simulation.','U_law':'3 sqrt(3) abs(z1 z2 z3), z uniform on S^6','seed':seed,'sample_size':N,'threshold_pinned_primary_rounded':observed_U,'count_leq':k,'cdf':cdf,'cdf_MC_binomial_95_interval':interval,'upper_tail':1-cdf,'mean_estimate':float(u.mean()),'mean_exact':float(mean_exact),'second_moment_estimate':float(np.mean(u*u)),'second_moment_exact':second_exact}
assert abs(u.mean()-mean_exact)<6*np.sqrt((second_exact-mean_exact**2)/N)

def lift(S,d):
 t=(np.einsum('i,jk->ijk',d,S)+np.einsum('j,ik->ijk',d,S)+np.einsum('k,ij->ijk',d,S))/3
 v=S@d
 return t-2/15*(np.einsum('i,jk->ijk',v,np.eye(3))+np.einsum('j,ik->ijk',v,np.eye(3))+np.einsum('k,ij->ijk',v,np.eye(3)))
S=np.diag([.02,.005,-.025]);L=np.stack([lift(S,np.eye(3)[i]).reshape(-1) for i in range(3)],axis=1)
M=L.T@L;M_exact=np.trace(S@S)/3*np.eye(3)+2/5*S@S
assert np.max(abs(M-M_exact))<1e-17
vals,V=np.linalg.eigh(M);smin=np.sqrt(vals[0]);kap=5/np.log(10);B=1e-4
# Positive STF3 source for an independent null-space direction.
v=np.array([1.,2.,3.]);O=np.einsum('i,j,k->ijk',v,v,v)-(v@v)/5*(np.einsum('i,jk->ijk',v,np.eye(3))+np.einsum('j,ik->ijk',v,np.eye(3))+np.einsum('k,ij->ijk',v,np.eye(3)))
o=O.reshape(-1);perp=o-L@np.linalg.solve(M,L.T@o);perp/=np.linalg.norm(perp)
dhat=.8*B/(kap*smin)*V[:,0];data=kap*L@dhat+.8*B*perp
recovered=np.linalg.solve(M,L.T@data)/kap
orth=data-kap*L@recovered
left=float(np.linalg.norm(data)**2);right=float(orth@orth+kap**2*recovered@M@recovered)
assert abs(left-right)<1e-20
hubble={'scope':'Fixed S, direct d_obs=0, e_d=0, declared total octupole radius B; algebraic counterexample to treating two marginal tests as sufficient.','S':S.tolist(),'B':B,'smin':float(smin),'dipole_separate_ratio':float(np.linalg.norm(recovered)/(B/(kap*smin))),'orthogonal_separate_ratio':float(np.linalg.norm(orth)/B),'joint_ratio':float(np.sqrt(right)/B),'orthogonal_identity_absolute_residual':abs(left-right),'false_pass_of_both_separate_tests':bool(np.linalg.norm(recovered)<=B/(kap*smin) and np.linalg.norm(orth)<=B and np.linalg.norm(data)>B)}
assert hubble['false_pass_of_both_separate_tests']
fig,ax=plt.subplots(1,2,figsize=(10.8,3.5),constrained_layout=True)
ordered=np.sort(u);ids=np.linspace(0,N-1,2000,dtype=int)
ax[0].plot(ordered[ids],(ids+1)/N,color='#176fa8',label='Ideal Gaussian benchmark')
ax[0].axvline(observed_U,color='#b45b28',ls='--',label=f'Pinned PR3 E morphology U={observed_U:.4f}')
ax[0].scatter([observed_U],[cdf],color='#b45b28');ax[0].set(xlabel='Envelope-normalized chirality U',ylabel='Cumulative probability',title='Mathematical null; no processed-sky calibration');ax[0].legend(fontsize=8)
ax[1].bar(['Dipole\nseparate','Residual\nseparate','Joint\nbudget'],[hubble['dipole_separate_ratio'],hubble['orthogonal_separate_ratio'],hubble['joint_ratio']],color=['#68737d','#68737d','#176fa8'])
ax[1].axhline(1,color='#b45b28',ls='--');ax[1].set(ylabel='Normalized compatibility score',title='Shared remainder budget matters')
for aa in ax:aa.grid(alpha=.2)
fig.savefig(ROOT/'figures/planck_hubble_controls.pdf');fig.savefig(ROOT/'figures/planck_hubble_controls.png',dpi=180)
(ROOT/'cas/planck_hubble_results.json').write_text(json.dumps({'ideal_null':summary,'hubble_joint_control':hubble},indent=2)+'\n')
print(json.dumps({'ideal_null':summary,'hubble_joint_control':hubble},indent=2))
