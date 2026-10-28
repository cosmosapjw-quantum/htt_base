"""Finite response-error propagation and bias-aware Gaussian confidence checks.

No evolution, ODE, cosmological fit or raw-data access. The physical error budget
is an assumed input of this finite experiment, not an empirically estimated bound.
"""
from pathlib import Path
import json
import numpy as np
from scipy.stats import chi2,ncx2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

W=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(20261028)

# A shared state error generates correlated detector errors. Its exact image
# retains this geometry instead of promoting each component bound to a box.
G=np.diag([1.,4.])
B=np.array([[1.,1.],[1.,-1.],[2.,0.]])
K=B@np.linalg.solve(G,B.T)
angles=np.linspace(0,2*np.pi,10001)
errors=np.diag([1.,.5])@np.vstack([np.cos(angles),np.sin(angles)])
v=np.array([1.,1.,-1.])
exact_support=float(np.sqrt(max(v@K@v,0.)))
sample_support=float(np.max(v@(B@errors)))
box_support=float(np.sum(np.abs(v)*np.sqrt(np.diag(K))))
assert exact_support<1e-12 and abs(sample_support)<1e-12

# A general fixed Gaussian response with nuisance. Correct physical-error
# projection gives the worst Fisher-scaled parameter bias.
n,p,q,k=12,5,2,4
A0=rng.normal(size=(n,n));C=A0@A0.T+np.eye(n)
white=np.linalg.inv(np.linalg.cholesky(C))
N=rng.normal(size=(n,q));J=rng.normal(size=(n,p));Bstate=rng.normal(size=(n,k))
Qn=np.linalg.qr(white@N,mode='reduced')[0];M=np.eye(n)-Qn@Qn.T
A=M@white@J;F=A.T@A
V=np.linalg.inv(F);L=V@A.T@M@white
eigvals,eigvecs=np.linalg.eigh(F)
Fsqrt=(eigvecs*np.sqrt(eigvals))@eigvecs.T
Gstate=np.diag([1.,2.,3.,4.]);Gisqrt=np.diag(1/np.sqrt(np.diag(Gstate)))
R=Fsqrt@L@Bstate@Gisqrt
u,s,vh=np.linalg.svd(R,full_matrices=False)
epsilon_state=0.3;epsilon_bias=float(epsilon_state*s[0])
e=epsilon_state*Gisqrt@vh[0]
attained=float(np.linalg.norm(Fsqrt@L@Bstate@e))
assert abs(attained-epsilon_bias)<1e-12
orth=np.eye(n)-A@np.linalg.solve(F,A.T)
theta_null_error=float(np.linalg.norm(Fsqrt@V@A.T@orth@M))
assert theta_null_error<1e-12

# Uniform coverage over a specified bound on the Fisher-scaled bias. The exact
# noncentral critical radius is smaller than the elementary triangle bound.
df=5;draws=100000;alpha=.05
noise=rng.normal(size=(draws,df));epsilons=np.array([0.,.5,1.,1.5,2.,3.])
rows=[]
central_radius=float(np.sqrt(chi2.ppf(1-alpha,df)))
for eps in epsilons:
    z=noise.copy();z[:,0]+=eps;norms=np.linalg.norm(z,axis=1)
    robust_radius=float(np.sqrt(ncx2.ppf(1-alpha,df,eps*eps)))
    classical=float(ncx2.cdf(central_radius**2,df,eps*eps))
    p_nom=float(np.mean(norms<=central_radius));p_rob=float(np.mean(norms<=robust_radius))
    rows.append({'bias_bound':float(eps),'central_coverage_exact':classical,
                 'central_coverage_MC':p_nom,'robust_coverage_exact':float(ncx2.cdf(robust_radius**2,df,eps*eps)),
                 'robust_coverage_MC':p_rob,'robust_MCSE':float(np.sqrt(p_rob*(1-p_rob)/draws)),
                 'central_radius':central_radius,'noncentral_radius':robust_radius,'triangle_radius':central_radius+float(eps)})

# A causal/positive cone alone has zero gauge inside it. A centered Bloch body
# with an interior anchor instead has the explicit finite asymmetric gauge.
anchor=np.array([.2,-.1,.3]);x=np.array([.4,.15,-.2]);a2=anchor@anchor
gauge=float((anchor@x+np.sqrt((anchor@x)**2+(1-a2)*(x@x)))/(1-a2))
boundary_residual=float(abs(np.linalg.norm(anchor+x/gauge)-1))
assert boundary_residual<1e-12

out={'schema':'htt.joint_physical_remainder/1','seed':20261028,'draws':draws,
     'source_connection':'MF02 Eq13.5.15, extended from scalar dual norm to joint detector Gram',
     'data_status':'synthetic fixed-law conditional experiment; no physical error budget was measured',
     'joint_gram':{'G':G.tolist(),'B':B.tolist(),'K':K.tolist(),'direction':v.tolist(),
       'exact_support':exact_support,'sample_support':sample_support,'coordinate_box_support':box_support},
     'parameter_bias':{'epsilon_state':epsilon_state,'operator_bound':epsilon_bias,'attained':attained,
       'response_orthogonal_error_parameter_effect':theta_null_error},
     'coverage':rows,'bloch_gauge':{'anchor':anchor.tolist(),'difference':x.tolist(),'value':gauge,'boundary_residual':boundary_residual}}
(W/'lanes/JOINT_REMAINDER.json').write_text(json.dumps(out,indent=2)+'\n')
fig,ax=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
ax[0].plot(epsilons,[r['central_coverage_exact'] for r in rows],'o-',label='Ignore bounded response error')
ax[0].plot(epsilons,[r['robust_coverage_MC'] for r in rows],'s-',label='Bias-aware confidence ball')
ax[0].axhline(.95,color='black',ls='--',lw=1);ax[0].set(xlabel='Bound on Fisher-scaled bias',ylabel='Coverage',ylim=(.2,1.01))
ax[0].legend(fontsize=8);ax[0].set_title('Physical approximation error affects coverage')
ax[1].plot(epsilons,[r['noncentral_radius'] for r in rows],'o-',label='Exact worst-bias critical radius')
ax[1].plot(epsilons,[r['triangle_radius'] for r in rows],'s--',label='Triangle-bound radius')
ax[1].axhline(central_radius,color='gray',ls=':',label='Zero-bias radius')
ax[1].set(xlabel='Bound on Fisher-scaled bias',ylabel='Radius in Fisher units');ax[1].legend(fontsize=8)
ax[1].set_title('One common physical confidence event')
for ext in ('png','pdf'):fig.savefig(W/f'figures/joint_remainder.{ext}',dpi=180)
print(json.dumps({'gram_support':exact_support,'box_support':box_support,'bias_bound':epsilon_bias,'bias_attained':attained,'coverage':rows},indent=2))
