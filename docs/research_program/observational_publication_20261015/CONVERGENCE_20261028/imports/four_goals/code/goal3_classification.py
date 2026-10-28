"""Finite geometry-response classification, not an observed Bianchi detection.

Runs no evolution/ODE. Reuses R36 matched-curvature witnesses and validates
the Gauss bridge, nuisance/common-carrier factorization and orbit tube rule.
"""
from pathlib import Path
import json, hashlib
import numpy as np
from scipy.stats import chi2
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'sources/goal3/R36_GEOMETRY_TABLE.json'
source_bytes=SOURCE.read_bytes()
source_blob=hashlib.sha1(b'blob '+str(len(source_bytes)).encode()+b'\0'+source_bytes).hexdigest()
assert source_blob=='1ae270fec9ae55375c01ec1f346f8755d9257049'
source=json.loads(source_bytes)
rng=np.random.default_rng(202610283)
I=np.eye(3)
def stf(a):return (a+a.T)/2-np.trace(a)*I/3
def norm(a):return float(np.linalg.norm(a))
Eps=np.zeros((3,3,3))
for a,b,c in [(0,1,2),(1,2,0),(2,0,1)]:Eps[a,b,c]=1;Eps[a,c,b]=-1
g=np.diag([-1.,1.,1.,1.])

def gauss_direct(h,S,E,rho,p,pi,lam):
    # kappa=1 in dimensionless curvature units. Weyl electric part is E.
    C=np.zeros((4,4,4,4))
    for i in range(3):
        for j in range(3):
            for a,b,c,d,v in [(0,i+1,0,j+1,E[i,j]),(i+1,0,0,j+1,-E[i,j]),(0,i+1,j+1,0,-E[i,j]),(i+1,0,j+1,0,E[i,j])]:C[a,b,c,d]=v
    C[1:,1:,1:,1:]=-np.einsum('ijm,kln,mn->ijkl',Eps,Eps,E)
    Ric=np.zeros((4,4));Ric[0,0]=(rho+3*p)/2-lam;Ric[1:,1:]=(rho-p)/2*I+pi+lam*I
    scalar=float(np.einsum('ab,ab',g,Ric))
    R=C+.5*(np.einsum('ac,bd->abcd',g,Ric)+np.einsum('bd,ac->abcd',g,Ric)-np.einsum('ad,bc->abcd',g,Ric)-np.einsum('bc,ad->abcd',g,Ric))-scalar/6*(np.einsum('ac,bd->abcd',g,g)-np.einsum('ad,bc->abcd',g,g))
    K=-h*I-S
    R3=R[1:,1:,1:,1:]-np.einsum('ac,bd->abcd',K,K)+np.einsum('ad,bc->abcd',K,K)
    return np.einsum('abad->bd',R3)

def gauss_formula(h,S,E,rho,pi,lam):
    scalar=2*rho+2*lam-6*h*h+np.sum(S*S)
    return E+.5*pi-h*S+stf(S@S)+scalar*I/3

gauss_errors=[];bound_checks=[]
for _ in range(500):
    h=float(rng.uniform(.5,2));S=stf(rng.normal(size=(3,3)));E=stf(rng.normal(size=(3,3)));pi=stf(rng.normal(size=(3,3)));rho=4.;p=.3;lam=.2
    gauss_errors.append(norm(gauss_direct(h,S,E,rho,p,pi,lam)-gauss_formula(h,S,E,rho,pi,lam)))
    dE=.02*stf(rng.normal(size=(3,3)));dS=.03*stf(rng.normal(size=(3,3)));dpi=.01*stf(rng.normal(size=(3,3)));dh=.01*rng.normal();drho=.02*rng.normal();dl=.01*rng.normal()
    a=gauss_formula(h,S,E,rho,pi,lam);b=gauss_formula(h+dh,S+dS,E+dE,rho+drho,pi+dpi,lam+dl)
    es=norm(dS);eh=abs(dh)
    etf=norm(dE)+.5*norm(dpi)+abs(h)*es+eh*norm(S)+eh*es+2*np.linalg.norm(S,2)*es+es*es
    etr=2*abs(drho)+2*abs(dl)+12*abs(h)*eh+6*eh*eh+2*norm(S)*es+es*es
    bound=(etf*etf+etr*etr/3)**.5
    bound_checks.append({'error':norm(b-a),'bound':bound})
assert max(gauss_errors)<4e-14
assert all(x['error']<=x['bound']+1e-13 for x in bound_checks)

# R36-10 instantaneous geometric witnesses, measured in u_*^2.
R1=np.diag(source['images']['II']['Y0'][:3]);R2=np.diag(source['images']['VII0matched']['Y0'][:3]);witness=[R1,R2]
h=source['images']['II']['z0'][6];S=np.diag([.1,-.05,-.05]);rho=source['images']['II']['Y0'][6]
E=[stf(r)+h*S-stf(S@S) for r in witness]
assert max(norm(gauss_formula(h,S,e,rho,np.zeros((3,3)),0)-r) for e,r in zip(E,witness))<5e-15
gap=norm(np.linalg.eigvalsh(R1)-np.linalg.eigvalsh(R2))

# Orthonormal symmetric STF coordinate convention, physical Frobenius norm.
B=np.array([np.diag([1,-1,0])/np.sqrt(2),np.diag([1,1,-2])/np.sqrt(6),
 [[0,1/np.sqrt(2),0],[1/np.sqrt(2),0,0],[0,0,0]],
 [[0,0,1/np.sqrt(2)],[0,0,0],[1/np.sqrt(2),0,0]],
 [[0,0,0],[0,0,1/np.sqrt(2)],[0,1/np.sqrt(2),0]]])
coords=lambda A:np.einsum('aij,ij->a',B,A)
eigs=np.array([np.linalg.eigvalsh(stf(r)) for r in witness])
Q=Rotation.random(random_state=rng).as_matrix()
rotation_error=max(norm(np.linalg.eigvalsh(Q@r@Q.T)-np.linalg.eigvalsh(r)) for r in witness)

# Raw observation has 7 coordinates: trace/sqrt(3), five STF, calibration.
# Nuisance eta shifts both first and last; profiling leaves six coordinates.
# Both models have the same trace, so 5 STF coordinates preserve every LR.
N=np.array([1.,0,0,0,0,0,1.])[:,None];M=np.eye(7)-N@N.T/2
J=np.zeros((7,5));J[1:6]=np.eye(5)
full_rank=int(np.linalg.matrix_rank(M));carrier_rank=int(np.linalg.matrix_rank(M@J))
lr_errors=[]
for _ in range(250):
    y=rng.normal(size=7)
    # Independent orientations are allowed in each model family.
    mean=[]
    for r in witness:
        q=Rotation.random(random_state=rng).as_matrix();mean.append(np.r_[np.trace(r)/np.sqrt(3),coords(q@r@q.T),0])
    full=-.5*norm(M@(y-mean[0]))**2+.5*norm(M@(y-mean[1]))**2
    compressed=-.5*norm(y[1:6]-mean[0][1:6])**2+.5*norm(y[1:6]-mean[1][1:6])**2
    lr_errors.append(abs(full-compressed))
assert max(lr_errors)<2e-14

# An additional channel helps only if it escapes the same nuisance image.
def effective_information(j,n):
    j=np.asarray(j,float)[:,None];n=np.asarray(n,float)[:,None]
    p=np.eye(len(j))-n@np.linalg.pinv(n)
    return float((j.T@p@j).item())
channel_information={'trace_only':effective_information([1],[1]),'complementary_channel':effective_information([1,1],[1,-1]),'duplicated_nuisance_channel':effective_information([1,1],[1,1])}
assert abs(channel_information['trace_only'])<1e-14 and abs(channel_information['duplicated_nuisance_channel'])<1e-14 and abs(channel_information['complementary_channel']-2)<1e-14

# Synthetic calibrated geometry experiment. No claim of an observed Ricci law.
draws=50000;error_radius=.10;alpha=.05;r_alpha=float(np.sqrt(chi2.ppf(1-alpha,6)))
sigmas=np.array([.03,.06,.09,.12,.15,.18,.22,.27,.33,.4,.5])
records=[]
for sigma in sigmas:
    noise=rng.normal(size=(draws,7))*sigma
    mats=stf(R1)+np.einsum('na,aij->nij',noise[:,1:6],B)
    eig=np.linalg.eigvalsh(mats)
    trace_res=(noise[:,0]-noise[:,-1])/np.sqrt(2)
    distances=np.sqrt(np.sum((eig[:,None,:]-eigs[None,:,:])**2,axis=2)+trace_res[:,None]**2)
    tau=sigma*r_alpha+error_radius
    masks=distances<=tau
    records.append({'sigma':float(sigma),'draws':draws,'true_family_retained':float(masks[:,0].mean()),'wrong_family_retained':float(masks[:,1].mean()),'both_retained':float((masks[:,0]&masks[:,1]).mean()),'neither_retained':float((~masks.any(axis=1)).mean()),'nearest_orbit_correct':float((distances[:,0]<distances[:,1]).mean()),'tube_radius':float(tau),'separation_margin':float(gap-2*tau)})

# A matched scalar curvature never distinguishes the two centers. The scalar
# norm-squared does: tensors need not be retained after this question is fixed.
scalar_curvatures=[float(np.trace(r)) for r in witness]
quadratic_invariants=[float(np.trace(r@r)) for r in witness]

# Sharp chirality witness from attached main.pdf, with full ordered tensor norm.
q=np.diag([-1/np.sqrt(2),0,1/np.sqrt(2)]);ww=np.array([np.sqrt(10)/4,1,np.sqrt(10)/4])
L=(np.einsum('i,jk->ijk',ww,q)+np.einsum('j,ik->ijk',ww,q)+np.einsum('k,ij->ijk',ww,q))/3
qw=q@ww;L-=2/15*(np.einsum('ij,k->ijk',I,qw)+np.einsum('ik,j->ijk',I,qw)+np.einsum('jk,i->ijk',I,qw))
v=np.einsum('ijk,jk->i',L,q);chir=float(np.linalg.det(np.column_stack([v,q@v,q@q@v])))
chir_bound=4*np.sqrt(2)/135
assert abs(chir-chir_bound)<1e-15 and abs(norm(L)-1)<1e-15
M_Q=np.sum(q*q)/3*I+2/5*q@q
sign_radius=float(np.min(np.abs(v)/np.sqrt(np.diag(M_Q))))
e1=np.eye(3)[0];q_e1=q@e1
L_e1=(np.einsum('i,jk->ijk',e1,q)+np.einsum('j,ik->ijk',e1,q)+np.einsum('k,ij->ijk',e1,q))/3-2/15*(np.einsum('ij,k->ijk',I,q_e1)+np.einsum('ik,j->ijk',I,q_e1)+np.einsum('jk,i->ijk',I,q_e1))
to_boundary=-v[0]/M_Q[0,0]*L_e1
v_boundary=np.einsum('ijk,jk->i',L+to_boundary,q)
assert abs(norm(to_boundary)-sign_radius)<1e-15 and abs(v_boundary[0])<1e-15

out={'schema':'htt.goal3.response_classification/1','status':'DERIVED_AND_FINITE_CHECKED','seed':202610283,'scope':'Synthetic geometry-response experiment; no observed curvature inference or CMB Bianchi classification','source_head':'7f3f49a6b6d95b6ae0323d5bebd3afce0067b1a7','gauss_direct_index_max_error':max(gauss_errors),'gauss_error_bound_tests':len(bound_checks),'gauss_bound_max_ratio':max(x['error']/x['bound'] for x in bound_checks),'witness_spectra':[np.linalg.eigvalsh(r).tolist() for r in witness],'scalar_curvatures':scalar_curvatures,'quadratic_invariants':quadratic_invariants,'rotation_orbit_gap':gap,'rotation_eigenvalue_max_error':rotation_error,'profiled_dimension':full_rank,'common_LR_carrier_dimension':carrier_rank,'profile_LR_max_error':max(lr_errors),'calibration_nuisance_columns':1,'physical_remainder_radius':error_radius,'confidence_noise_radius':r_alpha,'sigma_certification_threshold':(gap/2-error_radius)/r_alpha,'monte_carlo':records,'trace_out_of_family_example':{'STF_carrier_unchanged':True,'raw_trace_coordinate_shift':1.0,'projected_residual':1/np.sqrt(2),'threshold_at_sigma_0p12':.12*r_alpha+error_radius,'both_families_rejected':bool(1/np.sqrt(2)>.12*r_alpha+error_radius)},'chirality_witness':{'norm_O':norm(L),'chi_plus':chir,'chi_minus':-chir,'same_quadrupole_and_octupole_norms':True,'normalized_endpoints':[-1.,1.],'priority':'reused exact theorem and witness from attached main.pdf'},'native_solver':False,'ODE':False,'push':False}
out['source_table_git_blob']=source_blob
out['new_channel_effective_information']=channel_information
out['chirality_witness']['fixed_Q_sharp_sign_radius']=sign_radius
out['chirality_witness']['sign_radius_domain']='Ambient STF3 Frobenius error ball, Q fixed with simple spectrum; not a joint Q/O bound or a fixed-O-norm sphere bound.'
out['code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
out['skill_context_used']={'version':'PhysMath1.3.0','source':'WORK_PACKET.md','stages':['R2','R3','R4','R5','R7','R9'],'review':'one parent-owned integrated R6 pass'}
out['zero_event_binomial95_upper_at_50000']=float(1-.025**(1/50000))
out['new_theorem_priority']='not established; generic tools identified as prior, physical application and finite fixture newly derived/executed'
(ROOT/'lanes/GOAL3_CLASSIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
fig,ax=plt.subplots(1,3,figsize=(13.2,3.8),layout='constrained')
for i,r in enumerate(witness):ax[0].plot([1,2,3],np.linalg.eigvalsh(r),'o-',label=['II witness','VII0 witness'][i])
ax[0].set(xlabel='Ordered Ricci eigenvalue',ylabel=r'Eigenvalue / $u_*^2$',title='Same scalar curvature, distinct orbits',xticks=[1,2,3]);ax[0].legend()
ax[1].plot(sigmas,[r['nearest_orbit_correct'] for r in records],'o-',label='Nearest orbit correct')
ax[1].plot(sigmas,[r['true_family_retained'] for r in records],'s-',label='True family retained')
ax[1].plot(sigmas,[r['wrong_family_retained'] for r in records],'^-',label='Other family retained')
ax[1].set(xlabel=r'Working noise $\sigma/u_*^2$',ylabel='Frequency',title='50,000 draws per noise level',ylim=(-.02,1.03));ax[1].legend(fontsize=8)
ax[2].plot(sigmas,[r['separation_margin'] for r in records],'o-');ax[2].axhline(0,color='black',ls='--');ax[2].set(xlabel=r'Working noise $\sigma/u_*^2$',ylabel=r'$\delta-2(r_\alpha\sigma+\epsilon)$',title='Guaranteed exclusive compatibility')
fig.suptitle('Geometry-response classifier: synthetic Gaussian law, supplied R36 witnesses',fontsize=12)
for fmt in ['png','pdf']:fig.savefig(ROOT/f'figures/goal3_classification.{fmt}',dpi=180)
print(json.dumps({k:out[k] for k in ['gauss_direct_index_max_error','gauss_bound_max_ratio','rotation_orbit_gap','profile_LR_max_error','sigma_certification_threshold']},indent=2))
print(json.dumps(next(r for r in records if r['sigma']==.12),indent=2))
