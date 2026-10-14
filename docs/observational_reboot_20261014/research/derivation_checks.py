"""Bounded algebra checks; synthetic calculations, no observational p value."""
import json
from pathlib import Path
import numpy as np

rng = np.random.default_rng(20261014)
q = rng.normal(size=(3, 3)); q = (q + q.T)/2; q -= np.trace(q)*np.eye(3)/3
def bq(beta):
    sym = (np.einsum('i,jk->ijk',beta,q)+np.einsum('j,ik->ijk',beta,q)+np.einsum('k,ij->ijk',beta,q))/3
    t = 2*q@beta/3
    trace = (np.einsum('ij,k->ijk',np.eye(3),t)+np.einsum('ik,j->ijk',np.eye(3),t)+np.einsum('jk,i->ijk',np.eye(3),t))/5
    return 3*(sym-trace)
b = np.column_stack([bq(np.eye(3)[j]).ravel() for j in range(3)])
mq = np.sum(q*q)*np.eye(3) + 6*q@q/5
gram_error = float(np.linalg.norm(b.T@b-3*mq))
assert gram_error < 1e-12
beta=rng.normal(size=3); n=rng.normal(size=(200,3));n/=np.linalg.norm(n,axis=1)[:,None]
raw = 3*(n@beta)*np.einsum('ni,ij,nj->n',n,q,n)-2*n@(q@beta)
decomposed = np.einsum('ijk,ni,nj,nk->n',bq(beta),n,n,n)-4*n@(q@beta)/5
decomp_error=float(np.max(np.abs(raw-decomposed)));assert decomp_error<1e-12
one = np.hstack([np.eye(3),np.eye(3)])
two = np.vstack([np.hstack([np.eye(3),0.5*np.eye(3)]),np.hstack([np.eye(3),2*np.eye(3)])])
assert np.linalg.matrix_rank(one)==3 and np.linalg.matrix_rank(two)==6
d2,d3,t0 = 225.9,936.9,2.7255e6
result={
 'execution':'ACTUALLY_EXECUTED_SYNTHETIC_ALGEBRA', 'seed':20261014,
 'BQ_gram_error':gram_error,'boost_Q_dipole_octupole_error':decomp_error,
 'MQ_condition':float(np.linalg.cond(mq)), 'condition_bound':5/3,
 'same_shell_rank':int(np.linalg.matrix_rank(one)), 'distinct_shell_rank':int(np.linalg.matrix_rank(two)),
 'normalization':{'D2_uK2':d2,'D3_uK2':d3,'C2_uK2':2*np.pi*d2/6,'C3_uK2':2*np.pi*d3/12,
 'Q_norm_squared_uK2':75*d2/12,'O_norm_squared_uK2':245*d3/48,
 'epsilon2_STF_norm':np.sqrt(75*d2/12)/t0,'epsilon3_STF_norm':np.sqrt(245*d3/48)/t0},
 'same_sky_counterexample':{'C11':1,'C22':1,'C12':1,'true_difference_variance':0,'omitted_cross_term_variance':2},
 'observational_p':'NOT_COMPUTED','native_Bianchi_atlas':'NOT_EXECUTED'
}
Path(__file__).with_name('DERIVATION_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
