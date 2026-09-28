"""Bounded author-side algebraic checks. No evolution or repository import."""
import json
from pathlib import Path
import numpy as np

rng = np.random.default_rng(29020)
mu, wm = np.polynomial.legendre.leggauss(48)
phi = 2 * np.pi * np.arange(96) / 96
mu, phi = np.meshgrid(mu, phi, indexing="ij")
e = np.stack([np.sqrt(1-mu**2)*np.cos(phi), np.sqrt(1-mu**2)*np.sin(phi), mu], -1).reshape(-1, 3)
w = np.repeat(wm * 2*np.pi/96, 96)
avg = w / (4*np.pi)
I = np.eye(3)
E = np.einsum('ni,nj->nij', e, e)-I/3
H = .21
a = np.array([.13, -.24, .07])
om = np.array([-.11, .06, .17])
S = rng.normal(size=(3,3)); S = (S+S.T)/2; S -= np.trace(S)*I/3
Se = e @ S.T
s = np.einsum('ni,ni->n', e, Se)
ae = e @ a
V = -(a+Se-e*(ae+s)[:,None]+np.cross(om,e))
R = H + ae + s
Ew = lambda f: np.einsum('n,n...->...', avg, f)
recovered = {
 'H': float(Ew(R)),
 'a_redshift': 3*Ew(e*R[:,None]),
 'S_redshift': 7.5*Ew(E*R[:,None,None]),
 'omega_direction': -1.5*Ew(np.cross(e,V)),
 'a_direction': -1.5*Ew(V),
 'S_direction': -5*Ew((np.einsum('ni,nj->nij',e,V)+np.einsum('ni,nj->nij',V,e))/2),
}
target={'H':H,'a_redshift':a,'S_redshift':S,'omega_direction':om,'a_direction':a,'S_direction':S}
inv_errors={k:float(np.max(np.abs(recovered[k]-target[k]))) for k in target}
norm_errors={
 'R': float(abs(Ew(R**2)-(H**2+a@a/3+2*np.sum(S*S)/15))),
 'V': float(abs(Ew(np.sum(V*V,axis=1))-(2*a@a/3+np.sum(S*S)/5+2*om@om/3))),
}

# Positive, non-polynomial sky prevents polynomial-quadrature tautology.
b=np.array([.22,-.12,.19]); M=np.diag([.2,-.13,.07])
B=np.exp(e@b+np.einsum('ni,ij,nj->n',e,M,e))
g=b+2*e@M.T; gradB=B[:,None]*(g-e*np.einsum('ni,ni->n',e,g)[:,None])
AB=np.einsum('ni,ni->n',V,gradB)+4*R*B
mom=lambda f: np.einsum('n,n,n...->...',w,B,f)
rho=mom(np.ones(len(e))); M1=mom(e); M2=mom(np.einsum('ni,nj->nij',e,e))
M4S=mom(s[:,None,None]*np.einsum('ni,nj->nij',e,e))
Pi=M2-rho*I/3
Rom=np.array([[0,-om[2],om[1]],[om[2],0,-om[0]],[-om[1],om[0],0]])
L=S@M2+M2@S-M4S-I*np.sum(S*M2)/3
theory0=4*H*rho+np.sum(S*M2)+2*a@M1
theory1=4*H*M1+S@M1+np.cross(om,M1)+(rho*I+M2)@a
theory2=4*H*Pi+L+np.outer(a,M1)+np.outer(M1,a)-2*I*(a@M1)/3+Rom@M2-M2@Rom
observed=[np.einsum('n,n->',w,AB),np.einsum('n,n,ni->i',w,AB,e),np.einsum('n,n,nij->ij',w,AB,E)]
weak_errors={str(l):float(np.max(np.abs(x-y))) for l,(x,y) in enumerate(zip(observed,[theory0,theory1,theory2]))}

# Finite Doppler/aberration with Minkowski inner product.
metric=np.diag([-1,1,1,1]); u=np.array([1.,0,0,0]); beta=np.array([0.,.19,-.07,.12])
gam=1/np.sqrt(1-beta@metric@beta); ut=gam*(u+beta)
e4=np.column_stack([np.zeros(len(e)),e]); dop=gam*(1-e4@metric@beta)
et=(u+e4)/dop[:,None]-ut
boost_errors={
 'u_tilde_norm':float(abs(ut@metric@ut+1)),
 'e_tilde_norm':float(np.max(np.abs(np.einsum('ni,ij,nj->n',et,metric,et)-1))),
 'orthogonality':float(np.max(np.abs(et@metric@ut))),
 'photon_reconstruction':float(np.max(np.abs(dop[:,None]*(ut+et)-(u+e4)))),
}

result={'status':'AUTHOR_NUMERICAL_CHECK','current_turn_runtime':'PYTHON_PASS','quadrature':[48,96],
 'inverse_errors':inv_errors,'norm_errors':norm_errors,'weak_block_errors':weak_errors,'boost_errors':boost_errors,
 'scope':'Local identities only; no observed constraints, no evolution, no independent review.'}
assert max(inv_errors.values())<1e-12
assert max(norm_errors.values())<1e-12
assert max(weak_errors.values())<2e-11
assert max(boost_errors.values())<1e-12
path=Path(__file__).with_name('agent_kinematics_checks.json')
path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
