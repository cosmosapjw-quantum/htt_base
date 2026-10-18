"""Finite-design information needed to break a registered CF4 directional q alias.

No probability law or cosmological q measurement: Gram matrices use fixed
released group sky/depth support and a DECLARED WLS proxy. A generalized
Fisher-rank certificate is invariant under invertible q-coordinate changes.
"""
from __future__ import annotations
import numpy as np
from scipy.linalg import eigh


class Cf4QInformationError(ValueError):
    pass


def information_budget(raw_gram, residual_gram, *, minimum_retained_fraction=.05):
    """Provide a NORMALIZED orthogonal Fisher information-lift scenario.

    Raw and residual Gram are 3x3 SPD/PSD real. Let L L.T = Gram_raw,
    M=L^-1 Gram_res L^-T. Its eigenvalues measure retained information
    in corresponding raw Fisher-normalized parameter directions.

    A hypothetical INDEPENDENT orthogonal information source must add
    normalized PSD information N satisfying M+N >= tau I. The construction
    N=(tau I-M)_+ via eigenvalue truncation is a feasible positive
    'floor-lift' that minimizes Frobenius norm in normalized coordinates.
    It does NOT mean existing survey data or any measurement can provide N.
    """
    if np.iscomplexobj(raw_gram) or np.iscomplexobj(residual_gram):
        raise Cf4QInformationError('real Gram matrices only')
    a=np.asarray(raw_gram,dtype=float)
    b=np.asarray(residual_gram,dtype=float)
    tau=float(minimum_retained_fraction)
    if a.shape!=(3,3) or b.shape!=(3,3) or not all(np.isfinite(q).all() for q in (a,b)) or not 0<tau<=1:
        raise Cf4QInformationError('three-dimensional finite Gram and tau in (0,1] required')
    if np.max(np.abs(a-a.T))>1e-8*np.max(np.abs(a))+1e-13:
        raise Cf4QInformationError('raw Gram not symmetric')
    if np.max(np.abs(b-b.T))>1e-8*np.max(np.abs(b))+1e-13:
        raise Cf4QInformationError('residual Gram not symmetric')
    a=(a+a.T)/2
    b=(b+b.T)/2
    if np.linalg.eigvalsh(a)[0]<=0:
        raise Cf4QInformationError('raw Fisher Gram must be SPD')
    eig, v=eigh(b,a)
    if eig.min() < -1e-9 or eig.max()>1+1e-8:
        raise Cf4QInformationError('residual information exceeds raw or negative PSD bound')
    eig=np.maximum(0.,eig)
    deficits=np.maximum(0.,tau-eig)
    assert np.all(eig+deficits>=tau-1e-12)
    return {
      'relative_information_eigenvalues':eig.tolist(),
      'weakest_relative_information':float(eig[0]),
      'largest_relative_information':float(eig[-1]),
      'min_fisher_fraction_floor':tau,
      'hypothetical_normalized_eigenvalue_deficits':deficits.tolist(),
      'normalized_minimum_added_information_trace':float(sum(deficits)),
      'minimum_new_orthogonal_amplitude_ratio':float(np.sqrt(max(0.,tau-eig[0]))),
      'proposed_reference_lift_satisfies_floor':bool(np.all(eig+deficits>=tau-1e-12)),
      'scope':'Idealized independent PSD information oracle; no identified observational provider or physical q posterior.',
    }
