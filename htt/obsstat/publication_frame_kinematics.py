"""Finite local-frame composition and the radial kinematical response.

Research-stage, local tetrad (-,+,+,+), u.u=-c*c, not an observational
velocity field or Einstein-Boltzmann transfer. Spatial beta=v/c is dimensionless.
"""
from __future__ import annotations

import numpy as np

C_SI = 299792458.0


def _beta(value):
    b = np.asarray(value, dtype=np.float64)
    if b.shape != (3,) or not np.isfinite(b).all():
        raise ValueError('beta must be a finite 3-vector')
    if float(np.dot(b, b)) >= 1.0:
        raise ValueError('superluminal beta')
    return b


def gamma(beta):
    b = _beta(beta)
    return 1.0 / np.sqrt(1.0 - float(np.dot(b, b)))


def relative_beta(beta_of_object_in_reference, beta_of_new_frame_in_reference):
    """Einstein velocity transform into canonical (unrotated) boost frame.

    E.g. beta_RO = O in R, beta_RM = M in R; beta_MO = O in M.
    For noncollinear frames, the ordered canonical boosts carry a Wigner rotation.
    """
    b = _beta(beta_of_object_in_reference)
    u = _beta(beta_of_new_frame_in_reference)
    g = gamma(u)
    dot = float(np.dot(u, b))
    out = (b / g - u + (g / (g + 1.0)) * dot * u) / (1.0 - dot)
    _beta(out)
    return out


def velocity_from_beta(beta, c=C_SI):
    b = _beta(beta)
    if not np.isfinite(c) or c <= 0:
        raise ValueError('c must be finite positive')
    return c * b


def rapidity(beta):
    b = _beta(beta)
    return float(np.arctanh(np.linalg.norm(b)))


def relative_gamma_from_rest_frame_vectors(beta_a, beta_b):
    """Invariant gamma_ab=-u_a.u_b / c^2 in one R orthonormal tetrad."""
    a, b = _beta(beta_a), _beta(beta_b)
    return gamma(a) * gamma(b) * (1.0 - float(np.dot(a, b)))


def rapidity_between(beta_a, beta_b):
    return float(np.arccosh(max(1.0, relative_gamma_from_rest_frame_vectors(beta_a, beta_b))))


def source_frame_packet(beta_RO, beta_RM, B_W_km_s=None):
    """Typed frame velocities, not physical global tilt or measured peculiar flow."""
    o, m = _beta(beta_RO), _beta(beta_RM)
    packet = {
        'frame_convention': 'beta_RO = O in radiation frame R; beta_RM = M in R; beta_MO = O in M',
        'beta_RO': o.tolist(), 'beta_RM': m.tolist(),
        'beta_MO': relative_beta(o, m).tolist(),
        'rapidity_RO': rapidity(o),
        'rapidity_RM': rapidity(m),
        'rapidity_MO_invariant': rapidity_between(o, m),
        'physical_transfer_status': 'not_applied',
    }
    if B_W_km_s is not None:
        B = np.asarray(B_W_km_s, dtype=float)
        if B.shape != (3,) or not np.isfinite(B).all():
            raise ValueError('B_W must have three finite physical velocity components')
        packet['B_W_km_s'] = B.tolist()
        packet['B_W_is_tilt'] = False
    return packet


def STF(matrix):
    m = np.asarray(matrix, dtype=float)
    if m.shape != (3, 3) or not np.isfinite(m).all():
        raise ValueError('matrix must be real finite 3x3')
    return (m + m.T) / 2 - np.trace(m) * np.eye(3) / 3


def radial_gradient(n, J):
    """1/sec, J_ij=d_i v_j, no optical/lightcone terms."""
    n = np.asarray(n, dtype=float)
    J = np.asarray(J, dtype=float)
    if n.shape != (3,) or J.shape != (3, 3) or not np.isfinite(n).all() or not np.isfinite(J).all():
        raise ValueError('invalid direction or gradient')
    if abs(np.linalg.norm(n) - 1.0) > 1e-10:
        raise ValueError('unit direction required')
    return float(n @ J @ n)


def antisymmetric_from_pseudovector(w):
    """W_ij=epsilon_ijk w^k. Exact radial null for every unit n."""
    a = np.asarray(w, dtype=float)
    if a.shape != (3,) or not np.isfinite(a).all():
        raise ValueError('omega must be finite 3-vector, 1/s')
    x, y, z = a
    return np.array([[0,z,-y],[-z,0,x],[y,-x,0]], dtype=float)


def radial_operator(directions):
    """Design n^T J n on vec(J), row=9. Independent image rank <=6."""
    ns = np.asarray(directions, dtype=float)
    if ns.ndim != 2 or ns.shape[1] != 3 or not np.isfinite(ns).all() or np.any(abs(np.linalg.norm(ns,axis=1)-1)>1e-10):
        raise ValueError('directions must be unit N-by-3')
    return np.einsum('ni,nj->nij',ns,ns).reshape(-1,9)
