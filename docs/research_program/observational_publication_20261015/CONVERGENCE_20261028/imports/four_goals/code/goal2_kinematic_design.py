"""Finite ideal-response and detector-design checks; no catalogue or ODE solver."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import expm, logm
from scipy.stats import chi2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(20261028)
sig=np.array([[[0,1],[1,0]],[[0,-1j],[1j,0]],[[1,0],[0,-1]]],complex)
E=np.concatenate([np.eye(2)[None,:,:],sig])/np.sqrt(2)
tetra=np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]])/np.sqrt(3)
Rfull=np.array([(np.eye(2)+np.einsum('a,aij->ij',v,sig))/4 for v in tetra])
Rhel=np.array([(np.eye(2)+sig[2])/2,(np.eye(2)-sig[2])/2])
Rtrace=np.eye(2)[None,:,:]
gold=(1+np.sqrt(5))/2
dirs=np.array([(0,a,b*gold) for a in (-1,1) for b in (-1,1)]+
              [(a,b*gold,0) for a in (-1,1) for b in (-1,1)]+
              [(b*gold,0,a) for a in (-1,1) for b in (-1,1)],float)
dirs/=np.linalg.norm(dirs,axis=1)[:,None]

def response(Rs,which='both'):
    B=np.einsum('rij,aji->ra',Rs,E).real
    rows=[]
    for n in dirs:
        ref=np.array([0.,0.,1.]) if abs(n[2])<.9 else np.array([1.,0.,0.])
        t=np.cross(ref,n);t/=np.linalg.norm(t);u=np.cross(n,t)
        vectors=[n,t,u] if which=='both' else ([n] if which=='radial' else [t,u])
        for b in B:
            for v in vectors:rows.append(np.kron(b,np.outer(v,n).ravel()))
    return np.array(rows)

rank=lambda a:int(np.linalg.matrix_rank(a,tol=1e-10))
designs={'trace_HQ':response(Rtrace),'helicity_HQ':response(Rhel),
         'full_HQ':response(Rfull),'full_H_only':response(Rfull,'radial'),
         'full_Q_only':response(Rfull,'tangent')}
J=designs['full_HQ'];m,p=J.shape
# An uncalibrated common catalogue rotation is the identity-sector antisymmetry.
G=np.zeros((36,3))
for k in range(3):
    omega=np.eye(3)[k]
    W=np.column_stack([np.cross(np.eye(3)[j],omega) for j in range(3)])
    G[:9,k]=np.sqrt(2)*W.ravel()
N=J@G
std=.04+.03*(np.arange(m)%7)/6
cc=np.linspace(-1,1,m);dd=np.sin(np.arange(m)*.43)
C=np.diag(std**2)+.0002*np.outer(cc,cc)+.0001*np.outer(dd,dd)
L=np.linalg.cholesky(C);WJ=np.linalg.solve(L,J);WN=np.linalg.solve(L,N)
Un,sn,_=np.linalg.svd(WN,full_matrices=False);Mn=np.eye(m)-Un[:,:3]@Un[:,:3].T
B=Mn@WJ;U,s,Vt=np.linalg.svd(B,full_matrices=False);r=int(np.count_nonzero(s>1e-10))
V=Vt[:r].T;U=U[:,:r];s=s[:r]
F=B.T@B;Fplus=(V/s**2)@V.T;P=V@V.T
theta=rng.normal(scale=.15,size=36);eta=np.array([.07,-.03,.05])
y=J@theta+N@eta
est=Fplus@B.T@Mn@np.linalg.solve(L,y)
draws=30000
noise=rng.normal(size=(draws,m))
score_noise=noise@U
q=np.sum(score_noise**2,axis=1);q95=chi2.ppf(.95,r)
eps=.4;shift=np.zeros(r);shift[-1]=eps
q_shift=np.sum((score_noise+shift)**2,axis=1)
coverage=lambda hits:{'fraction':float(np.mean(hits)),'MCSE':float(np.sqrt(np.mean(hits)*(1-np.mean(hits))/draws)),'draws':draws}
unidentifiable_norm=float(np.linalg.norm(P@G))

# Exact ideal matrix-gradient inverse on a spherical second-moment design.
Kcoeff=rng.normal(size=(4,3,3));K=np.einsum('aij,akl->ijkl',Kcoeff,E)
axes=np.vstack([np.eye(3),-np.eye(3)]);Krec=np.zeros_like(K)
for n in axes:
    Kn=np.einsum('abij,b->aij',K,n);H=np.einsum('a,aij->ij',n,Kn)
    Q=Kn-n[:,None,None]*H
    Krec+=3*np.einsum('aij,b->abij',n[:,None,None]*H+Q,n)/6

# Internal basis covariance: states and detector effects transform together.
Ug=expm(1j*np.einsum('a,aij->ij',[.31,-.22,.13],sig))
Kg=np.einsum('ij,abjk,kl->abil',Ug,K,Ug.conj().T)
Rg=np.einsum('ij,rjk,kl->ril',Ug,Rfull,Ug.conj().T)
pred=np.einsum('rij,abji->rab',Rfull,K).real
predg=np.einsum('rij,abji->rab',Rg,Kg).real

# Opposite-parity lift: same STF algebra, distinct parity representation.
S=np.array([[.6,.1,.03],[.1,-.2,.04],[.03,.04,-.4]])
v=np.array([.2,-.4,.5]);eye=np.eye(3)
def lift(S,v):
    Sv=S@v
    return (np.einsum('ij,k->ijk',S,v)+np.einsum('ik,j->ijk',S,v)+np.einsum('jk,i->ijk',S,v))/3-(2/15)*(np.einsum('ij,k->ijk',eye,Sv)+np.einsum('ik,j->ijk',eye,Sv)+np.einsum('jk,i->ijk',eye,Sv))
O=lift(S,v);reflect=np.diag([-1.,1,1]);Oax=lift(reflect@S@reflect.T,np.linalg.det(reflect)*reflect@v)
Oexpected=np.linalg.det(reflect)*np.einsum('ai,bj,ck,ijk->abc',reflect,reflect,reflect,O)
unit=rng.normal(size=(100,3));unit/=np.linalg.norm(unit,axis=1)[:,None]
pol=np.einsum('ni,ij,nj->n',unit,S,unit)*(unit@v)
dec=np.einsum('ijk,ni,nj,nk->n',O,unit,unit,unit)+(2/5)*(unit@(S@v))

# Matrix-log derivative is covariant; scalar flux and chosen analyzers differ.
F0=np.diag([2.,1.]);Xi=np.array([[0.,-.5],[.5,0.]])
derivative=Xi@logm(F0)-logm(F0)@Xi
hs=np.array([.1,.05,.025,.0125,.00625]);errs=[]
for h in hs:
    fp=expm(h*Xi)@F0@expm(-h*Xi);fm=expm(-h*Xi)@F0@expm(h*Xi)
    errs.append(float(np.linalg.norm((logm(fp)-logm(fm))/(2*h)-derivative)))
deltaF=Xi@F0-F0@Xi
Rplus=(np.eye(2)+sig[0])/2
out={'schema':'htt.goal2.kinematic_detector_design/1','seed':20261028,'scope':'Synthetic fixed source/detector linear response; no empirical physical detection',
     'source_equations':['MF02 (1.12.8)','MF02 (2.7.10)','MF02 (2.8.10)-(2.8.11)','main.pdf (21),(26),(31)-(35),(38)-(39)'],
     'rank_cases':{k:rank(v) for k,v in designs.items()},'matrix_parameter_count':36,'full_HQ_measurements':m,
     'nuisance_spin_rank':rank(N),'profile_information_rank':r,'profile_F_positive_eigenvalues':(s**2).tolist(),
     'profiled_spin_projection_norm':unidentifiable_norm,'profiled_estimate_image_error':float(np.linalg.norm(est-P@theta)),
     'confidence95_no_remainder':coverage(q<=q95),'confidence95_shifted_nominal':coverage(q_shift<=q95),
     'confidence95_shifted_with_bound':coverage(q_shift<=(np.sqrt(q95)+eps)**2),'whitened_remainder_radius':eps,
     'ideal_six_axis_inverse_max_error':float(np.max(np.abs(Krec-K))),
     'internal_gauge_measurement_max_error':float(np.max(np.abs(pred-predg))),
     'STF_trace_max_error':float(np.max(np.abs(np.einsum('iik->k',O)))),
     'STF_product_max_error':float(np.max(np.abs(pol-dec))),
     'axial_parity_max_error':float(np.max(np.abs(Oax-Oexpected))),
     'matrix_log_steps':hs.tolist(),'matrix_log_central_difference_errors':errs,'matrix_log_error_ratios':(np.array(errs[:-1])/np.array(errs[1:])).tolist(),
     'trace_rotation_derivative':float(np.trace(deltaF)),'coherence_analyzer_rotation_derivative':float(np.trace(Rplus@deltaF).real),
     'coherence_scalar_log_derivative':float((np.trace(Rplus@deltaF)/np.trace(Rplus@F0)).real),
     'coherence_pairing_matrix_log_derivative':float(np.trace(Rplus@derivative).real),
     'physical_qualification':'H and Q are supplied mathematical response fields; a detector/source law is required to identify them with catalogue redshift, proper motion or polarization drift.'}
assert out['rank_cases']=={'trace_HQ':9,'helicity_HQ':18,'full_HQ':36,'full_H_only':24,'full_Q_only':32}
assert r==33 and unidentifiable_norm<1e-11
for key in ['profiled_estimate_image_error','ideal_six_axis_inverse_max_error','internal_gauge_measurement_max_error','STF_trace_max_error','STF_product_max_error','axial_parity_max_error']:
    assert out[key]<1e-11,(key,out[key])
assert np.all(np.abs(np.array(out['matrix_log_error_ratios'])-4)<.01)
out['finite_identity_assertions']='PASS'
(ROOT/'lanes/GOAL2_KINEMATICS.json').write_text(json.dumps(out,indent=2)+'\n')
fig,ax=plt.subplots(1,2,figsize=(10,4),layout='constrained')
labels=['Trace\nH+Q','Helicity\nH+Q','Full\nH only','Full\nQ only','Full\nH+Q','Full + unknown\nframe spin']
vals=[9,18,24,32,36,r];ax[0].bar(np.arange(6),vals,color=['#b9bec9','#889ab5','#567ba9','#3e8b94','#26715e','#b97549'])
ax[0].set_xticks(np.arange(6),labels,fontsize=8);ax[0].set_ylabel('Identifiable dimensions (out of 36)');ax[0].set_ylim(0,39)
for k,vv in enumerate(vals):ax[0].text(k,vv+.4,str(vv),ha='center',fontsize=9)
ax[0].set_title('Channels and frame calibration determine rank')
ax[1].loglog(hs,errs,'o-',label='Central-difference error');ax[1].loglog(hs,errs[0]*(hs/hs[0])**2,'--',label=r'$h^2$ reference');ax[1].set_xlabel('Rotation step h');ax[1].set_ylabel('Frobenius error');ax[1].legend();ax[1].set_title('Noncommuting matrix-log response')
fig.suptitle('Ideal matrix kinematics: observable rank and a finite algebraic check',fontsize=12)
for ext in ('png','pdf'):fig.savefig(ROOT/f'figures/goal2_kinematic_design.{ext}',dpi=190)
print(json.dumps({k:out[k] for k in ['rank_cases','profile_information_rank','profiled_estimate_image_error','ideal_six_axis_inverse_max_error','internal_gauge_measurement_max_error','STF_product_max_error','confidence95_no_remainder','confidence95_shifted_with_bound']},indent=2))
