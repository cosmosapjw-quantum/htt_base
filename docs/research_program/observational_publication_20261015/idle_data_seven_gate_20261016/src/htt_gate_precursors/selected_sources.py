"""Hierarchical fixed-selected-count likelihood precursor for H02/S04.

This is a mathematical calibration test, NOT a fitted CF4 source-selection law.
Prior class probabilities refer to the unselected parent population.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import exp, isfinite, log, pi
import numpy as np
from scipy.special import log_ndtr, logsumexp


def _logdiff(a: float, b: float) -> float:
    """Return log(exp(a)-exp(b)), allowing b=-inf and a>b."""
    if b == -np.inf:
        return float(a)
    if not a > b:
        raise ValueError('empty or unresolved interval')
    return float(a + np.log(-np.expm1(b-a)))


def normal_log_selection(mu: float, sigma: float, low: float=-np.inf,
                         high: float=np.inf) -> float:
    """P(low < y < high | N(mu,sigma)), robust even in distant tails."""
    if not all(np.isfinite(x) for x in (mu,sigma)) or sigma <= 0 or not low < high:
        raise ValueError('invalid location/scale/selection')
    if np.isnan(low) or np.isnan(high):
        raise ValueError('nan selection boundary')
    a=(low-mu)/sigma
    b=(high-mu)/sigma
    if a == -np.inf and b == np.inf:
        return 0.0
    if a == -np.inf:
        return float(log_ndtr(b))
    if b == np.inf:
        return float(log_ndtr(-a))
    if a >= 0:
        return _logdiff(float(log_ndtr(-a)),float(log_ndtr(-b)))
    return _logdiff(float(log_ndtr(b)),float(log_ndtr(a)))


@dataclass(frozen=True)
class LatentNormal:
    probability: float
    mean: float
    sigma: float


@dataclass(frozen=True)
class SelectedMixture:
    components: tuple[LatentNormal,...]
    parent_source_id: str
    selection_source_id: str
    low: float=0.0
    high: float=np.inf

    def __post_init__(self):
        if not self.parent_source_id.strip() or not self.selection_source_id.strip():
            raise ValueError('source ids required')
        if not self.components or not self.low < self.high:
            raise ValueError('no components or empty support')
        ps=np.array([x.probability for x in self.components],dtype=float)
        if not np.all(np.isfinite(ps)) or np.any(ps<=0) or abs(float(ps.sum())-1)>1e-12:
            raise ValueError('positive normalized parent probabilities required')
        for x in self.components:
            normal_log_selection(x.mean,x.sigma,self.low,self.high)

    def _log_normalizer_terms(self) -> np.ndarray:
        return np.array([log(c.probability)+normal_log_selection(c.mean,c.sigma,self.low,self.high)
                         for c in self.components])

    def log_selected_mass(self) -> float:
        return float(logsumexp(self._log_normalizer_terms()))

    def selected_type_probabilities(self) -> np.ndarray:
        """Correct post-selection type weights: pi_j Z_j / sum pi_k Z_k."""
        terms=self._log_normalizer_terms()
        return np.exp(terms-logsumexp(terms))

    def log_density(self, y: float) -> float:
        if not np.isfinite(y):
            raise ValueError('observed y must be finite')
        if not (self.low < y < self.high):
            return float('-inf')
        terms=[log(c.probability)-log(c.sigma)-0.5*log(2*pi)-0.5*((y-c.mean)/c.sigma)**2
               for c in self.components]
        return float(logsumexp(terms)-self.log_selected_mass())

    def density(self, y: float) -> float:
        return float(exp(self.log_density(y)))


def wrong_fixed_parent_weight_density(model:SelectedMixture,y:float)->float:
    """Counterexample: mixing individually selected components with *parent* weights.

    It integrates to one but describes a different model and type fraction.
    Use only in negative regression tests.
    """
    if not model.low < y < model.high: return 0.0
    return float(sum(c.probability*exp(
        -0.5*((y-c.mean)/c.sigma)**2-log(c.sigma)-0.5*log(2*pi)
        -normal_log_selection(c.mean,c.sigma,model.low,model.high))
        for c in model.components))


def gaussian_nuisance_projector(F:np.ndarray,Z:np.ndarray,C:np.ndarray):
    """Whiten and orthogonally project away unconstrained calibration columns.

    The rank is source-conditional and is NOT a physical H0 detection.
    """
    F=np.asarray(F,dtype=float);Z=np.asarray(Z,dtype=float);C=np.asarray(C,dtype=float)
    if F.ndim!=2 or Z.ndim!=2 or F.shape[0]!=Z.shape[0] or C.shape!=(len(F),len(F)):
        raise ValueError('incompatible designs')
    L=np.linalg.cholesky(C)
    A=np.linalg.solve(L,F);N=np.linalg.solve(L,Z)
    U,s,_=np.linalg.svd(N,full_matrices=False)
    rank=int(np.sum(s>max(s[0] if len(s) else 1,1)*1e-11))
    P=np.eye(len(F))-U[:,:rank]@U[:,:rank].T
    projected=P@A
    return projected,np.linalg.svd(projected,compute_uv=False),rank

@dataclass(frozen=True)
class SharedSelectedLatent:
    """One proper shared two/multi-state latent for N selected labelled slots.

    Conditional row noises independent given the common latent. Selection is
    included at the *joint* distribution level before marginalizing the shared
    latent. Never use this as an assumed CF4 calibration posterior by default.
    """
    latent: SelectedMixture

    def posterior_common_latent_after_N_admissions(self,N:int):
        if not isinstance(N,int) or N<1:raise ValueError('N selected slots required')
        terms=self.latent._log_normalizer_terms()
        weights=np.array([log(c.probability) + N*normal_log_selection(
            c.mean,c.sigma,self.latent.low,self.latent.high)
            for c in self.latent.components])
        return np.exp(weights-logsumexp(weights))

    def joint_log_density(self, ys):
        ys=np.asarray(ys,dtype=float)
        if ys.ndim!=1 or len(ys)==0 or not np.all(np.isfinite(ys)):
            raise ValueError('nonempty ordered data vector required')
        if not np.all((ys>self.latent.low)&(ys<self.latent.high)):
            return float('-inf')
        N=len(ys)
        logterms=[]; zterms=[]
        for c in self.latent.components:
            logprior=log(c.probability)
            # This is the N-dimensional normalized selected-count density.
            logterms.append(logprior-N*(log(c.sigma)+0.5*log(2*pi))
                            -0.5*np.sum(((ys-c.mean)/c.sigma)**2))
            zterms.append(logprior+N*normal_log_selection(c.mean,c.sigma,
                                                          self.latent.low,self.latent.high))
        return float(logsumexp(logterms)-logsumexp(zterms))

    def wrong_held_parent_joint_density(self,ys):
        """Counterexample only: integrate per-latent selected densities using parent pi."""
        ys=np.asarray(ys,dtype=float)
        if ys.ndim!=1 or not np.all(np.isfinite(ys)) or len(ys)<1:
            raise ValueError('invalid y')
        if not np.all((ys>self.latent.low)&(ys<self.latent.high)):
            return 0.0
        N=len(ys)
        terms=[]
        for c in self.latent.components:
            terms.append(log(c.probability)-N*(log(c.sigma)+0.5*log(2*pi))
                         -0.5*np.sum(((ys-c.mean)/c.sigma)**2)
                         -N*normal_log_selection(c.mean,c.sigma,self.latent.low,self.latent.high))
        return float(exp(logsumexp(terms)))
