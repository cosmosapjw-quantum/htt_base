"""Bounded synthetic optical angular calculation; no evolution or observational fit."""
from pathlib import Path
from fractions import Fraction as F
import json, itertools
import numpy as np
from numpy.polynomial.legendre import leggauss
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
KAPPA=5/np.log(10)

def coupling(d,S):
    T=(np.einsum('i,jk->ijk',d,S)+np.einsum('j,ik->ijk',d,S)+np.einsum('k,ij->ijk',d,S))/3
    v=S@d; I=np.eye(3)
    return T-(2/15)*(np.einsum('ij,k->ijk',I,v)+np.einsum('ik,j->ijk',I,v)+np.einsum('jk,i->ijk',I,v))

def cube_stf(d):
    T=np.einsum('i,j,k->ijk',d,d,d);I=np.eye(3)
    return T-(np.dot(d,d)/5)*(np.einsum('ij,k->ijk',I,d)+np.einsum('ik,j->ijk',I,d)+np.einsum('jk,i->ijk',I,d))

def grid(nz,nphi):
    z,w=leggauss(nz);p=np.arange(nphi)*2*np.pi/nphi
    xx=np.sqrt(1-z[:,None]**2)*np.cos(p)[None,:]; yy=np.sqrt(1-z[:,None]**2)*np.sin(p)[None,:]
    n=np.stack([xx,yy,np.broadcast_to(z[:,None],xx.shape)],axis=-1).reshape(-1,3)
    wt=np.repeat(w/(2*nphi),nphi)
    T=np.einsum('ni,nj,nk->nijk',n,n,n);I=np.eye(3)
    T-=(np.einsum('ij,nk->nijk',I,n)+np.einsum('ik,nj->nijk',I,n)+np.einsum('jk,ni->nijk',I,n))/5
    return n,wt,T

def project(f,w,T): return (35/2)*np.einsum('n,n,nijk->ijk',w,f,T)

# Exact rational finite tests supplement the proof in theory_expansion.md.
frac_checks=[]
for k in range(1,8):
    d=[F(k,7),F(2-k,9),F(k+1,11)]
    S=[[F(k,13),F(1,8),F(-1,10)],[F(1,8),F(-k-2,17),F(1,12)],[F(-1,10),F(1,12),F(0)]]
    S[2][2]=-S[0][0]-S[1][1]
    v=[sum(S[i][j]*d[j] for j in range(3)) for i in range(3)]
    T=[[[ (d[i]*S[j][l]+d[j]*S[i][l]+d[l]*S[i][j])/3-F(2,15)*((i==j)*v[l]+(i==l)*v[j]+(j==l)*v[i]) for l in range(3)] for j in range(3)] for i in range(3)]
    norm=sum(T[i][j][l]**2 for i,j,l in itertools.product(range(3),repeat=3))
    ss=sum(S[i][j]**2 for i,j in itertools.product(range(3),repeat=2));dd=sum(x*x for x in d)
    rhs=dd*ss/3+F(2,5)*sum(x*x for x in v)
    contraction=[sum(T[i][j][l]*S[j][l] for j,l in itertools.product(range(3),repeat=2)) for i in range(3)]
    adjoint=[ss*d[i]/3+F(2,5)*sum(S[i][j]*v[j] for j in range(3)) for i in range(3)]
    assert norm==rhs and contraction==adjoint
    assert all(sum(T[i][i][l] for i in range(3))==0 for l in range(3))
    def matvec(M,b): return [sum(M[i][j]*b[j] for j in range(3)) for i in range(3)]
    def detcols(a,b,c): return sum(F(sign)*a[i]*b[j]*c[l] for i,j,l,sign in [(0,1,2,1),(1,2,0,1),(2,0,1,1),(0,2,1,-1),(1,0,2,-1),(2,1,0,-1)])
    KM=[[ss*F(i==j)/3+F(2,5)*sum(S[i][l]*S[l][j] for l in range(3)) for j in range(3)] for i in range(3)]
    detK=detcols(*[[KM[i][j] for i in range(3)] for j in range(3)])
    assert detcols(contraction,matvec(S,contraction),matvec(S,matvec(S,contraction)))==detK*detcols(d,v,matvec(S,v))
    frac_checks.append({'case':k,'norm_identity':True,'contraction_identity':True,'STF_trace':True,'chirality_factorization':True})

n,w,T=grid(40,80);n2,w2,T2=grid(60,120)
d0=np.array([1.,2.,3.]);d0/=np.linalg.norm(d0);S0=np.diag([.6,-.2,-.4])
rows=[]
for a in np.geomspace(.002,.25,45):
    d=a*d0; S=a*S0;q=n@d+np.einsum('ni,ij,nj->n',n,S,n)
    f=-KAPPA*np.log1p(q);O=project(f,w,T);Oq=KAPPA*coupling(d,S)
    q2=n2@d+np.einsum('ni,ij,nj->n',n2,S,n2);O2=project(-KAPPA*np.log1p(q2),w2,T2)
    Op=project(-KAPPA*np.log1p(n@d),w,T);Opc=-KAPPA*cube_stf(d)/3
    eps=np.linalg.norm(d)+np.linalg.norm(S,2)
    bound=np.sqrt(35/2)*KAPPA*eps**3/(3*(1-eps))
    exact_quad=project(-KAPPA*(q-q*q/2),w,T)
    err=np.linalg.norm(O-Oq)
    assert err<=bound+1e-13
    assert np.linalg.norm(exact_quad-Oq)<1e-12
    K=np.sum(S*S)/3*np.eye(3)+(2/5)*(S@S)
    rec=np.linalg.solve(K,np.einsum('ijk,jk->i',Oq,S))/KAPPA
    assert np.linalg.norm(rec-d)<1e-13
    rows.append({'amplitude':float(a),'epsilon_upper':float(eps),'coupled_exact_norm':float(np.linalg.norm(O)), 'coupled_quadratic_norm':float(np.linalg.norm(Oq)), 'pure_dipole_exact_norm':float(np.linalg.norm(Op)), 'pure_dipole_cubic_norm':float(np.linalg.norm(Opc)), 'coupled_remainder_norm':float(err),'remainder_bound':float(bound),'quadrature_difference':float(np.linalg.norm(O2-O))})

fig,axs=plt.subplots(1,2,figsize=(10.2,4.05),layout='constrained')
a=np.array([r['amplitude'] for r in rows])
axs[0].loglog(a,[r['coupled_exact_norm'] for r in rows],color='#174f75',label='Acceleration + shear: exact log')
axs[0].loglog(a,[r['coupled_quadratic_norm'] for r in rows],'--',color='#29a4b5',label='Quadratic coupling')
axs[0].loglog(a,[r['pure_dipole_exact_norm'] for r in rows],color='#9c4937',label='Acceleration only: exact log')
axs[0].loglog(a,[r['pure_dipole_cubic_norm'] for r in rows],':',color='#e59766',label='Cubic dipole term')
axs[0].set_ylabel(r'Octupole tensor norm $\|O_\mu\|_F$ [mag]');axs[0].legend(fontsize=8,loc='upper left')
axs[1].loglog(a,[r['coupled_remainder_norm'] for r in rows],color='#174f75',label='Exact minus quadratic')
axs[1].loglog(a,[r['remainder_bound'] for r in rows],'--',color='#9c4937',label='Analytic uniform bound')
axs[1].set_ylabel('Octupole tensor error [mag]');axs[1].legend(fontsize=8,loc='upper left')
for ax in axs:
    ax.set_xlabel(r'Common dimensionless amplitude $t$');ax.grid(True,which='both',alpha=.2)
    ax.spines[['top','right']].set_visible(False)
fig.savefig(ROOT/'figures/theory_induced_octupole.pdf');fig.savefig(ROOT/'figures/theory_induced_octupole.png',dpi=200)
summary={'scope':'Synthetic local optical logarithmic response; no finite-redshift fit, CMB transfer, Boltzmann or ODE calculation','normalization':'f=-5/ln(10)*ln(1+d.n+S:nn); P3 f=O_mu:nnn; full-sphere normalized measure','parameters':{'d0':d0.tolist(),'S0':S0.tolist(),'d':'t d0','S':'t S0'},'quadrature':{'primary':[40,80],'comparison':[60,120]},'exact_rational_checks':frac_checks,'max_quadrature_tensor_difference':max(r['quadrature_difference'] for r in rows),'all_45_remainder_bounds_satisfied':True,'rows':rows}
(ROOT/'research/theory_bridge_result.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('rows','exact_rational_checks')},indent=2))
