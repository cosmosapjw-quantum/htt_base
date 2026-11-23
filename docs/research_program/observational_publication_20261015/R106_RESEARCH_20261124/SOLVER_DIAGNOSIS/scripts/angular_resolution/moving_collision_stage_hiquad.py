"""Finite harmonic Thomson generator on the outward normal-tetrad sky.

For dimensionless baryon velocity beta=v/c, photon p=-n, D=gamma*(1+beta.n),
the conserved-anchor clock multiplies the sink by mu=D/gamma. Electrons are
cold and polarization is bolometric. Coefficients and velocity are frozen at
the cell midpoint. The angular quadrature and the finite (ell,m) space are
independent approximations. The same projected operator acts at both stages.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import lu_factor, lu_solve
from scipy.sparse.linalg import splu

from bass.collision.coherency import symmetric_screen_columns
from bass.collision.moving_thomson import boost_photon_and_screen
from bass.transport.general_bianchi_transfer import _spherical_screen_basis


def _project_columns(op, maps):
    """Project batches of I,Q,U,V maps onto the operator's orthonormal basis."""
    theta, _, _, weights = op._grid
    ntheta, nphi = theta.shape
    samples = maps.reshape(ntheta, nphi, 4, -1)
    # Weight per azimuthal sample; fft sums over phi, without dividing by nphi.
    ft = np.fft.fft(samples, axis=1) * weights[:, :1, None, None]
    out = np.empty((op.dim, samples.shape[-1]), dtype=complex)
    for (ell, m), index in op.idx["T"].items():
        ring = ft[:, m % nphi]
        y = op._basis_theta[0, ell, m].conj()
        out[index] = y @ ring[:, 0]
        out[op.idx["V"][ell, m]] = y @ ring[:, 3]
        if ell >= 2:
            yp = op._basis_theta[2, ell, m].conj()
            ym = op._basis_theta[-2, ell, m].conj()
            plus = -yp @ (ring[:, 1] + 1j*ring[:, 2])
            minus = -ym @ (ring[:, 1] - 1j*ring[:, 2])
            out[op.idx["E"][ell, m]] = (plus + minus)/2
            out[op.idx["B"][ell, m]] = (plus - minus)/(2j)
    return out


def initial_radiation_stokes(op, beta):
    """Project a boosted isotropic blackbody, normalized by normal-frame energy.

    I/E on the outward sphere is D^-4/[4 pi gamma^2(1+beta^2/3)].
    Match the conserved first two stress moments analytically; quadrature sets
    the resolved higher multipoles of this specific isotropic-rest-frame IC.
    """
    b = np.asarray(beta, dtype=float)
    if b.shape != (3,) or not np.all(np.isfinite(b)) or b @ b >= 1.:
        raise ValueError("initial radiation velocity must be finite and subluminal")
    b2 = float(b @ b)
    if b2 == 0.:
        return np.zeros(op.dim, dtype=complex)
    n = op._grid[2].reshape(-1, 3)
    # -4 log(D) - log[E/rho_rest] for the normalized angular distribution.
    log_ratio = 3*np.log1p(-b2) - 4*np.log1p(n @ b) - np.log1p(b2/3)
    sky = np.zeros((len(n), 4, 1))
    sky[:, 0, 0] = .25*np.expm1(log_ratio)
    state = _project_columns(op, sky)[:, 0]
    q_over_E = 4*b/(3+b2)
    pi_over_E = np.outer(b, q_over_E) - (b @ q_over_E)*np.eye(3)/3
    exact_low = (op.dipole_source_vector(-.75*q_over_E)
                 + op.shear_source_vector(pi_over_E, amplitude=-15/8))
    for (ell, m), i in op.idx["T"].items():
        if ell <= 2:
            state[i] = exact_low[i]
    return state


RINGS = 64
_AUX = {}


def _aux_operator(op, rings):
    """Cached quadrature-only operator with the same harmonic index table."""
    from bass.transport.general_lie_stokes import GeneralLieStokesOperator
    rings = int(rings)
    if rings == op.n_gl_theta:
        return op
    key = (op.L, tuple(op.m_values), rings)
    if key not in _AUX:
        aux = GeneralLieStokesOperator(op.L, m_values=tuple(op.m_values), n_gl_theta=rings)
        if aux.idx != op.idx or aux.dim != op.dim:
            raise ValueError("auxiliary quadrature operator has a different harmonic index table")
        _AUX[key] = aux
    return _AUX[key]


class MovingCollisionStage:
    """Galerkin gain L R* of rank <=9 and sparse directional loss.

    The Lorentz screen is carried from the outward sphere using spatial parity
    (p,beta) -> (n,-beta). The reflected polarization orientation occurs on both
    sides of the Thomson kernel; V transports in its separate vector block.
    """
    def __init__(self, op, beta):
        self.op = op
        # R106 H4 VARIANT: project the moving kernel (gain columns and boosted
        # isotropic emission) on an auxiliary Gauss-Legendre grid with RINGS
        # rings instead of the transport operator's own grid. The harmonic
        # index table is identical (same L and m_values); the loss term below
        # still uses the transport operator.
        q = _aux_operator(op, RINGS)
        n = q._grid[2].reshape(-1, 3)
        u, v = _spherical_screen_basis(n)
        beta = np.asarray(beta, dtype=float)
        geometry = boost_photon_and_screen(n, -beta, basis_u=u, basis_v=v)
        D = geometry.doppler_D
        mu = geometry.one_minus_beta_dot_n
        up, vp, np_ = geometry.basis_u_rest, geometry.basis_v_rest, geometry.directions_rest

        # Six symmetric-tensor and three circular-vector moments. The input
        # moment weight D^2 comes from D^4 S and dOmega'=D^-2 dOmega.
        columns = np.zeros((len(n), 4, 9))
        columns[:, :3, :6] = symmetric_screen_columns(up, vp)
        columns[:, 3, 6:] = np_
        self.left = _project_columns(q, (mu/D**4)[:, None, None] * columns)
        right = _project_columns(q, (3/(16*np.pi) * D**2)[:, None, None] * columns)
        right[:, 6:] *= 2  # vector moment of circular polarization
        self.right_h = right.conj().T
        # M_stream(k) = -i n.k. The conserved-anchor loss is -(1+n.beta).
        self.loss = -op._I_sp - 1j * op.base_operator(np.zeros(14), k_eff=beta)

        # Scatter-in of isotropic normal I_bg=1/4 from its analytically boosted
        # stress tensor. This avoids subtracting O(1) angular quadratures at small beta.
        b2 = float(beta @ beta)
        g2 = geometry.gamma**2
        logD = -.5*np.log1p(-b2) + np.log1p(n @ beta)
        bo_u, bo_v = up @ beta, vp @ beta
        source = np.zeros((len(n), 4))
        source[:, 0] = np.expm1(-4*logD) + D**-4 * g2*(b2 + (np_ @ beta)**2)
        source[:, 1] = -D**-4 * g2*(bo_u**2 - bo_v**2)
        source[:, 2] = -2*D**-4 * g2*bo_u*bo_v
        self.emission = _project_columns(q, (.25*mu)[:, None, None]*source[..., None])[:, 0]

    def apply(self, state):
        """Return the homogeneous projected rate per unit conserved-anchor depth."""
        return self.loss @ state + self.left @ (self.right_h @ state)

    def factor_sdirk_stage(self, base, gamma_h, delta_tau):
        """Solve I-h_gamma(base + delta_tau*C) by a sparse LU and a nine-moment Schur solve."""
        s = gamma_h * delta_tau
        lu = splu((self.op._I_sp - gamma_h*base - s*self.loss).tocsc())
        scaled_left = lu.solve(np.asfortranarray(s*self.left))
        cap = lu_factor(np.eye(9) - self.right_h @ scaled_left)

        def solve(rhs):
            initial = lu.solve(rhs)
            return initial + scaled_left @ lu_solve(cap, self.right_h @ initial)

        return solve
