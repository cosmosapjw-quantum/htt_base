"""Static radiation-tensor and confidence-ball checks; no transport solver."""
from pathlib import Path
import json
import numpy as np
from numpy.polynomial.legendre import leggauss
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
metric=np.diag([-1.,1.,1.,1.])
def stf(a):
    a=(a+a.T)/2
    return a-np.eye(3)*np.trace(a)/3
def boost(v):
    b2=v@v; gamma=1/np.sqrt(1-b2)
    L=np.eye(4);L[0,0]=gamma;L[0,1:]=L[1:,0]=gamma*v
    if b2:L[1:,1:]+=(gamma-1)*np.outer(v,v)/b2
    return L
def kappa(s):return 3/(2+np.sqrt(4-3*s))
def kappaprime(s):return 9/(2*np.sqrt(4-3*s)*(2+np.sqrt(4-3*s))**2)
def G(f):return kappa(f@f)*stf(np.outer(f,f))
def readout(T):
    rho=T[0,0];f=T[0,1:]/rho;P=stf(T[1:,1:])/rho;D=P-G(f)
    eig,V=np.linalg.eig(T@metric)
    timelike=[i for i in range(4) if np.real(V[:,i].conj()@metric@V[:,i]) < -1e-10]
    assert len(timelike)==1 and np.max(abs(eig.imag))<1e-12
    i=timelike[0];rhoL=-eig[i].real;p=np.delete(eig.real,i)
    A=np.linalg.norm(p-rhoL/3)/rhoL
    return rho,f,P,D,A
def tensor(a):
    T=np.diag([1.,1/3-a/15,1/3-a/15,1/3+2*a/15])
    return T

records=[];max_null=0.;max_landau=0.
for a in [0.,2e-5,.02]:
    for b in np.linspace(0,.3,121):
        L=boost(np.array([.6*b,0,.8*b]));T=L@tensor(a)@L.T
        rho,f,P,D,A=readout(T);expected=np.sqrt(6)*abs(a)/15
        max_landau=max(max_landau,abs(A-expected))
        if a==0:max_null=max(max_null,np.linalg.norm(D))
        records.append([float(a),float(b),float(np.linalg.norm(P)),float(np.linalg.norm(D)),float(A)])
assert max_null<2e-15 and max_landau<2e-15

# Exact declared error-ball certificate, not observed or Gaussian confidence data.
a=2e-5;b=.00123;L=boost(np.array([0.,0.,b]));rho,f,P,D,A=readout(L@tensor(a)@L.T)
epsP=5e-7;epsf=1e-5;r=np.linalg.norm(f)+epsf
Lip=2*kappa(r*r)*r+2*np.sqrt(2/3)*kappaprime(r*r)*r**3
radius=epsP+Lip*epsf
certificate={'a':a,'observer_beta':b,'flux_norm':float(np.linalg.norm(f)),'landau_A':float(A),'D_norm':float(np.linalg.norm(D)),'eps_P':epsP,'eps_f':epsf,'flux_ball_radius':float(r),'G_lipschitz':float(Lip),'D_error_bound':float(radius),'D_norm_lower':float(max(0,np.linalg.norm(D)-radius)),'pure_boost_null_excluded_for_declared_ball':bool(np.linalg.norm(D)>radius)}

# Nonlinear harmonic/STF conversion, quadrature and cubic-remainder scaling.
mu,w=leggauss(36);phi=np.linspace(0,2*np.pi,73,endpoint=False)
n=np.stack(np.broadcast_arrays(np.sqrt(1-mu[:,None]**2)*np.cos(phi),np.sqrt(1-mu[:,None]**2)*np.sin(phi),mu[:,None]+0*phi),axis=-1).reshape(-1,3)
weights=np.repeat(w/2/len(phi),len(phi))
d0=np.array([.11,-.07,.13]);Q0=stf(np.array([[.07,.02,-.01],[.02,-.03,.04],[-.01,.04,.01]]))
v=np.array([.3,-.2,.4]);O0=np.einsum('i,j,k->ijk',v,v,v)-(v@v)/5*(np.einsum('i,jk->ijk',v,np.eye(3))+np.einsum('j,ik->ijk',v,np.eye(3))+np.einsum('k,ij->ijk',v,np.eye(3)))
errors=[]
for scale in [.2,.1,.05]:
    d=scale*d0;Q=scale*Q0;O=scale*O0
    theta=n@d+np.einsum('ni,ij,nj->n',n,Q,n)+np.einsum('ijk,ni,nj,nk->n',O,n,n,n)
    I=(1+theta)**4;rr=weights@I
    # Outward n means propagation -n.
    j=-np.einsum('n,n,ni->i',weights,I,n)
    M=np.einsum('n,n,ni,nj->ij',weights,I,n,n)
    exactP=stf(M)/rr;exactD=exactP-G(j/rr)
    approxP=8*Q/15+4*stf(np.outer(d,d))/5+24*np.einsum('c,abc->ab',d,O)/35+16*stf(Q@Q)/35+8*stf(np.einsum('acd,bcd->ab',O,O))/35
    approxD=approxP-4*stf(np.outer(d,d))/3
    errors.append({'scale':scale,'stress_error':float(np.linalg.norm(exactP-approxP)),'D_error':float(np.linalg.norm(exactD-approxD))})
ratios=[errors[i]['D_error']/errors[i+1]['D_error'] for i in range(2)]
assert all(7<q<9 for q in ratios)

rng=np.random.default_rng(61326);rotation_errors=[];lip_ratios=[]
for _ in range(200):
    R,_=np.linalg.qr(rng.normal(size=(3,3)));R[:,0]*=np.linalg.det(R)
    RR=np.eye(4);RR[1:,1:]=R
    rt=readout(RR@(L@tensor(a)@L.T)@RR.T)
    rotation_errors.append(np.linalg.norm(rt[3]-R@D@R.T))
    f1=rng.normal(size=3);f1*=rng.uniform(0,.8)/np.linalg.norm(f1)
    f2=rng.normal(size=3);f2*=rng.uniform(0,.8)/np.linalg.norm(f2)
    r0=max(np.linalg.norm(f1),np.linalg.norm(f2));lip=2*kappa(r0*r0)*r0+2*np.sqrt(2/3)*kappaprime(r0*r0)*r0**3
    lip_ratios.append(np.linalg.norm(G(f1)-G(f2))/(lip*np.linalg.norm(f1-f2)))
assert max(rotation_errors)<2e-15 and max(lip_ratios)<=1+1e-13

fig,ax=plt.subplots(1,3,figsize=(13,3.6),constrained_layout=True)
data=np.array(records)
for a0,color in [(0.,'#68737d'),(.02,'#176fa8')]:
    v=data[data[:,0]==a0];ax[0].plot(v[:,1],v[:,2],color=color,label=f'a={a0:g}')
    ax[1].plot(v[:,1],v[:,4],color=color,label=f'a={a0:g}')
ax[0].set(title='Observer-resolved stress',xlabel=r'Observer speed $|\beta|$',ylabel=r'$\|\pi(U)\|/\rho(U)$')
ax[1].set(title='Radiation-rest stress: invariant',xlabel=r'Observer speed $|\beta|$',ylabel=r'$\mathcal{A}_\gamma$')
ax[0].legend();ax[1].legend()
ax[2].bar(['Null\nthreshold','Toy residual'],[radius,np.linalg.norm(D)],color=['#68737d','#176fa8'])
ax[2].set(title='Declared joint-error certificate',ylabel=r'Dimensionless STF norm')
ax[2].ticklabel_format(axis='y',style='sci',scilimits=(0,0));ax[2].axhline(radius,color='#b45b28',ls='--')
for a1 in ax:a1.grid(alpha=.18)
fig.suptitle('Static radiation tensor controls — analytical toy, no observed CMB fit',fontsize=12)
fig.savefig(ROOT/'figures/radiation_stress_constraint.pdf');fig.savefig(ROOT/'figures/radiation_stress_constraint.png',dpi=180)
result={'scope':'Static analytic tensor transforms, finite quadrature and declared error balls. No observational fit.','max_pure_boost_null_residual':float(max_null),'max_landau_invariant_error':float(max_landau),'max_rotation_covariance_error':float(max(rotation_errors)),'lipschitz_cases':200,'max_observed_lipschitz_ratio':float(max(lip_ratios)),'certificate':certificate,'nonlinear_scaling':errors,'D_cubic_error_ratios':ratios,'boost_curves':records}
(ROOT/'cas/stress_constraint_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='boost_curves'},indent=2))
