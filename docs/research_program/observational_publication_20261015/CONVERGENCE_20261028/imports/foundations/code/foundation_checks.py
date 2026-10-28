"""Finite checks of target-qualified compression; synthetic, no catalogue fit."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import null_space
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(20261028)

def basis(a,tol=1e-11):
    u,s,_=np.linalg.svd(a,full_matrices=False)
    return u[:,s>tol*(s[0] if len(s) else 1)]

# Common covariance, common linear nuisance, affine-family mean offsets.
n=15
r=rng.normal(size=(n,n));C=r@r.T+np.eye(n)
L=np.linalg.cholesky(C)
N=rng.normal(size=(n,3));W=np.linalg.solve(L,np.eye(n))
Q=basis(W@N);M=np.eye(n)-Q@Q.T
J=[M@W@rng.normal(size=(n,k)) for k in (2,3)]
a=[np.zeros(n),M@W@rng.normal(size=n)]
U=basis(np.column_stack([*J,a[1]]))
errors=[]
for _ in range(200):
    z=M@rng.normal(size=n)
    means=[a[k]+J[k]@rng.normal(size=J[k].shape[1]) for k in range(2)]
    full=-.5*np.sum((z-means[0])**2)+.5*np.sum((z-means[1])**2)
    compressed=-.5*np.sum((U.T@(z-means[0]))**2)+.5*np.sum((U.T@(z-means[1]))**2)
    errors.append(abs(full-compressed))
assert max(errors)<1e-11

# Explicit model-offset counterexample: tangent-only compression loses y3.
offset_y0=np.array([0.,0.,0.]);offset_y1=np.array([0.,0.,2.])
offset_mu=np.array([0.,0.,1.])
offset_lr=lambda y: float(y@offset_mu-.5*(offset_mu@offset_mu))
assert np.array_equal(offset_y0[:2],offset_y1[:2])

# Closed-family LR does not retain sensitivity to an unlisted residual mode.
u=np.eye(4)[:,:2];y0=np.zeros(4);y1=np.array([0,0,0,5.])
assert np.array_equal(u.T@y0,u.T@y1)
q=lambda y:float(np.linalg.norm(y-u@(u.T@y))**2)

# Nonlinear response omitted by a fiducial tangent space, with finite certificate.
theta=np.linspace(-1,1,401);z=np.array([.4,1.7])
delta=theta**2*.3
mu=np.column_stack([theta,delta])
log_full=mu@z-.5*np.sum(mu**2,axis=1)
log_compressed=theta*z[0]-.5*theta**2
loss=log_full-log_compressed
bound=abs(z[1])*abs(delta)+.5*delta**2
assert np.all(abs(loss)<=bound+1e-14)

# Same Gaussian mean score, distinct covariance-family likelihoods.
def covariance_lr(y,lam=.5):
    return float(-.5*np.log1p(lam)+.5*y[1]**2*lam/(1+lam))
cv0=np.array([0.,0.]);cv1=np.array([0.,3.])

# A same-data radial normalization loses its denominator unless retained.
v=np.array([1.,2.,-1.]);v2=4*v
assert np.allclose(v/np.linalg.norm(v),v2/np.linalg.norm(v2))

# A nuisance-aware 24->18 reduction can erase six slope parameters exactly.
T=np.column_stack([np.eye(18),rng.normal(size=(18,6))])
N24=np.vstack([np.eye(18),np.zeros((6,18))]);J24=np.vstack([np.zeros((18,6)),np.eye(6)])
N18=T@N24;J18=T@J24
M18=np.eye(18)-basis(N18)@basis(N18).T
assert np.linalg.norm(M18@J18)<1e-12

results={
 'scope':'synthetic finite identities and counterexamples; no observed sky fit',
 'seed':20261028,
 'common_affine_family':{'original_dimension':n,'nuisance_rank':3,'retained_dimension':U.shape[1],'trials':200,'max_log_likelihood_ratio_error':max(errors)},
 'omitted_affine_offset':{'same_tangent_summary':True,'full_logLR_values':[offset_lr(offset_y0),offset_lr(offset_y1)]},
 'omitted_goodness_of_fit':{'same_family_summary':True,'residual_norm_squared':[q(y0),q(y1)]},
 'nonlinear_remainder':{'max_actual_logLR_error':float(max(abs(loss))),'max_certified_bound':float(max(bound)),'all_401_bounds_pass':True},
 'parameter_dependent_covariance':{'same_mean_score':True,'logLR_values':[covariance_lr(cv0),covariance_lr(cv1)]},
 'same_data_normalization':{'same_normalized_vector':True,'lost_radius_ratio':4},
 'abstract_24_to_18_slope_loss':{'original_interest_rank':6,'compressed_nuisance_rank':18,'compressed_interest_rank':0},
 'interpretation':'Exact known-family likelihood equivalence, conditional Fisher efficiency, and general departure diagnostics are different targets.'}
(ROOT/'lanes/FOUNDATION_CHECKS.json').write_text(json.dumps(results,indent=2)+'\n')

fig,ax=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
ax[0].plot(theta,log_full,label='Full nonlinear response',lw=2)
ax[0].plot(theta,log_compressed,label='Fiducial tangent only',lw=2,ls='--')
ax[0].set(xlabel='Synthetic physical parameter',ylabel='Log likelihood ratio to zero',title='A tangent score can lose finite-response curvature')
ax[0].legend(fontsize=8)
ax[1].plot(theta,abs(loss),label='Actual omitted-response error',lw=2)
ax[1].plot(theta,bound,label='Finite response certificate',lw=2,ls='--')
ax[1].set(xlabel='Synthetic physical parameter',ylabel='Absolute log likelihood-ratio error',title='A physical remainder gives an error budget')
ax[1].legend(fontsize=8)
for a0 in ax:a0.grid(alpha=.18)
fig.savefig(ROOT/'figures/compression_remainder.png',dpi=180)
fig.savefig(ROOT/'figures/compression_remainder.pdf')
print(json.dumps(results,indent=2))
