"""Numerical fixed-contraction fibre support; not a confidence certificate.

The caller supplies the actual fixed STF contraction matrix in orthonormal
coordinates. Uncertain q needs its joint inverse image, not this fixed fibre.
"""
import numpy as np
from .r7_contracts import finite_array


def fixed_contraction_support(operator, contraction, direction, *, q_is_fixed):
    if q_is_fixed is not True:
        return {'status': 'JOINT_Q_INVERSE_IMAGE_REQUIRED', 'support': None}
    l = finite_array(operator, ndim=2)
    if l.shape != (3, 7):
        raise ValueError('fixed STF3 to vector contraction must be 3 by 7')
    v = finite_array(contraction, shape=(3,)); a = finite_array(direction, shape=(7,))
    # SVD is numerical, with the same explicit refusal near uncertain strata.
    u, s, vh = np.linalg.svd(l, full_matrices=True)
    error = 64*7*np.finfo(float).eps
    if s[-1] <= error*s[0]:
        return {'status': 'NUMERICALLY_UNRESOLVED', 'support': None}
    center = vh[:3].T @ ((u.T @ v)/s)
    eta = float(center @ center)
    radius2 = 1-eta
    budget = error*max(1., eta)*(s[0]/s[-1])**2
    if radius2 < -budget:
        return {'status': 'EMPTY_FIBRE', 'support': None, 'eta': eta}
    if abs(radius2) <= budget:
        # Floating-point agreement with eta=1 is not an exact boundary proof.
        return {'status': 'BOUNDARY_NUMERICALLY_UNRESOLVED', 'support': None, 'eta': eta}
    null_component = vh[3:].T @ (vh[3:] @ a)
    norm = float(np.linalg.norm(null_component))
    radius = float(np.sqrt(radius2))
    # Any kernel unit vector is a witness when the objective is constant there.
    kernel_direction = null_component/norm if norm else vh[3]
    witness = center+radius*kernel_direction
    return {'status': 'NUMERICALLY_CHECKED_FIXED_FIBRE',
            'support': float(a@center+radius*norm), 'witness': witness, 'eta': eta,
            'scope': 'fixed computed contraction only; no outer confidence guarantee'}
