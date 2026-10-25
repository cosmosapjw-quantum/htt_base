#!/usr/bin/env python3
"""Finite checks of the appendix identities; no catalogue or solver is run."""
import itertools,json
from pathlib import Path
import numpy as np

BASE=Path(__file__).resolve().parent
rng=np.random.default_rng(20261024)

def make_tensor(entries):
    O=np.zeros((3,3,3))
    for ijk,v in entries.items():
        for p in set(itertools.permutations(ijk)):O[p]=v
    return O

def kernel(lam):
    d=np.array([lam[1]-lam[2],lam[2]-lam[0],lam[0]-lam[1]])
    return [make_tensor({(0,1,2):1})]+[make_tensor({(i,j,j):d[j] for j in range(3)}) for i in range(3)],d

maximum={k:0. for k in ['trace','kernel_contraction','gram_offdiag','kernel_norm','moment_reconstruction','cayley_hamilton','normalized_envelope_identity']}
for _ in range(100):
    lam=rng.normal(size=3);lam-=lam.mean();lam/=np.linalg.norm(lam)
    Q=np.diag(lam);t=np.trace(Q@Q);j=np.trace(Q@Q@Q)
    ks,d=kernel(lam)
    G=np.array([[np.sum(a*b) for b in ks] for a in ks])
    expected=np.r_[6,9*t-2*d*d]
    maximum['trace']=max(maximum['trace'],max(np.max(np.abs(np.einsum('iik->k',a))) for a in ks))
    maximum['kernel_contraction']=max(maximum['kernel_contraction'],max(np.max(np.abs(np.einsum('ijk,jk->i',a,Q))) for a in ks))
    maximum['gram_offdiag']=max(maximum['gram_offdiag'],np.max(np.abs(G-np.diag(np.diag(G)))))
    maximum['kernel_norm']=max(maximum['kernel_norm'],np.max(np.abs(np.diag(G)-expected)))
    v=rng.normal(size=3);h=np.array([v@np.linalg.matrix_power(Q,k)@v for k in range(3)])
    if min(abs(lam[a]-lam[b]) for a in range(3) for b in range(a))>1e-4:
        recovered=[]
        for a in range(3):
            b,c=[x for x in range(3) if x!=a]
            recovered.append((h[2]-(lam[b]+lam[c])*h[1]+lam[b]*lam[c]*h[0])/((lam[a]-lam[b])*(lam[a]-lam[c])))
        maximum['moment_reconstruction']=max(maximum['moment_reconstruction'],np.max(np.abs(recovered-v*v)))
    maximum['cayley_hamilton']=max(maximum['cayley_hamilton'],np.max(np.abs(Q@Q@Q-t*Q/2-j*np.eye(3)/3)))
    r=j*j/t**3
    E2=((.5-3*r)*(64/675+8*r/1125)/27)/(4*np.sqrt(2)/135)**2
    maximum['normalized_envelope_identity']=max(maximum['normalized_envelope_identity'],abs(E2-(1-6*r)*(1+3*r/40)))
Q=np.diag([-1.,0,1]);O=make_tensor(dict(zip([(0,0,0),(0,0,1),(0,0,2),(0,1,1),(0,1,2),(0,2,2),(1,1,1),(1,1,2),(1,2,2),(2,2,2)],[1,1,1,-2,0,1,-2,-2,1,1])))
assert np.all(np.einsum('iik->k',O)==0)
assert np.all(np.einsum('ijk,jk->i',O,Q)==0)
assert np.sum(O*O)==42
symmetries=[]
for signs in itertools.product([-1,1],repeat=3):
    R=np.diag(signs);Or=np.einsum('ia,jb,kc,abc->ijk',R,R,R,O)
    if np.array_equal(Or,O):symmetries.append(list(signs))
assert symmetries==[[1,1,1]]
assert max(maximum.values())<1e-10
out={'trials':100,'seed':20261024,'maximum_absolute_residuals':maximum,'zero_contraction_chiral_pair':{'Q_norm_squared':2,'O_norm_squared':42,'diagonal_orthogonal_stabilizers':symmetries},'status':'passed'}
(BASE/'output/appendix_checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
