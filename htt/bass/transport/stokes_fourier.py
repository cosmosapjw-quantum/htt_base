"""Fourier-mode polarized streaming and cold Thomson collisions on a flat FLRW sky."""
from __future__ import annotations

from numbers import Integral

import numpy as np

from bass.collision.coherency import ThomsonCoherencyPropagator
from bass.collision.electron_frame import _coerce_unit_directions


class FourierStokesPropagator:
    """Integrate a complex I,Q,U,V mode on a common electron-rest angular grid.

    Real perturbations are recovered as Re[S_k(n) exp(+i k.x)]. The spatial
    coordinates are comoving in Mpc, k in radians/Mpc, and delta_chi=c delta_eta
    in Mpc. The source-free brightness variables have the homogeneous FLRW
    redshift factored out. Linear polarization uses a fixed screen per ray.
    """

    def __init__(self, directions, weights, k_per_mpc, basis_u=None, basis_v=None):
        n = _coerce_unit_directions(directions, name="directions")
        k = np.asarray(k_per_mpc)
        if k.shape != (3,) or not np.isrealobj(k) or not np.all(np.isfinite(k)):
            raise ValueError("k_per_mpc must be a finite real comoving 3-vector")
        self._k_dot_n = n @ k.astype(float)
        self.collision = ThomsonCoherencyPropagator(n, weights, basis_u, basis_v)

    def advance(self, stokes, delta_chi_mpc, delta_tau, *, substeps=1, source_increment=None,
                method="sdirk2"):
        """Evolve the coupled operators with a constant affine cell source.

        Coefficients are constant in cell phase 0<=u<=1. delta_tau is a scalar
        electron-rest optical depth. The caller controls time resolution with
        substeps. The default is a stiffly accurate, L-stable second-order
        diagonally implicit Runge--Kutta scheme used continuously through
        zero opacity and zero wavevector. The optional 'strang' method is
        exact on either axis and can require finer steps at high opacity.
        """
        if method not in ("sdirk2", "strang"):
            raise ValueError("method must be 'sdirk2' or 'strang'")
        if np.ndim(delta_chi_mpc) != 0 or not np.isrealobj(delta_chi_mpc):
            raise ValueError("delta_chi_mpc must be a nonnegative finite scalar")
        distance = float(delta_chi_mpc)
        if not np.isfinite(distance) or distance < 0:
            raise ValueError("delta_chi_mpc must be a nonnegative finite scalar")
        if isinstance(substeps, (bool, np.bool_)) or not isinstance(substeps, Integral) or substeps < 1:
            raise ValueError("substeps must be a positive integer")
        t = self.collision.validate_optical_depth(delta_tau)
        sky = np.array(stokes, dtype=complex, copy=True)
        if sky.shape != (len(self._k_dot_n), 4) or not np.all(np.isfinite(sky)):
            raise ValueError("Fourier Stokes amplitudes must be finite with shape (N,4)")
        phase = -1j*distance*self._k_dot_n[:, None]
        source = None
        if source_increment is not None:
            source = np.asarray(source_increment, dtype=complex)
            if source.shape != sky.shape or not np.all(np.isfinite(source)):
                raise ValueError("integrated Fourier source must be finite and match the Stokes amplitudes")
        if t == 0. and method == "strang":
            evolved = np.exp(phase)*sky
            if source is not None:
                phi1 = np.ones_like(phase)
                np.divide(np.expm1(phase), phase, out=phi1, where=phase != 0)
                evolved += phi1*source
            return evolved
        if not np.any(phase) and method == "strang":
            substeps = 1
        if source is not None:
            source = source/substeps
        if method == "sdirk2":
            gamma = 1. - 1./np.sqrt(2.)
            solve = self.collision.factor_shifted_collision(
                1.-gamma*phase[:, 0]/substeps, gamma*t/substeps)
            increment = 0. if source is None else gamma*source
            for _ in range(substeps):
                y1 = solve(sky+increment)
                sky = solve(sky + ((1.-gamma)/gamma)*(y1-sky) + increment)
            return sky
        half = np.exp(phase/(2*substeps))
        for _ in range(substeps):
            sky *= half
            if source is None:
                sky = (self.collision.advance(sky.real, t/substeps)
                       + 1j*self.collision.advance(sky.imag, t/substeps))
            else:
                sky = (self.collision.advance_with_source(sky.real, t/substeps, source.real)
                       + 1j*self.collision.advance_with_source(sky.imag, t/substeps, source.imag))
            sky *= half
        return sky
