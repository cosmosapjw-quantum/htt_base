"""Positive Thomson optical measure on increasing N=ln(a), observer at the final edge."""

from dataclasses import dataclass
import numpy as np
from scipy.interpolate import PchipInterpolator


@dataclass(frozen=True)
class OpticalCells:
    delta_tau: np.ndarray
    tau_to_observer: np.ndarray
    visibility_mass: np.ndarray


class OpacityHistory:
    """Interpolate nonnegative dτ/dN; integrate each source piece before rebinning.

    Normal opacity uses proper electron density times Γ. For a specified ray the
    propagation-direction factor is applied at the source nodes before interpolation.
    The angular collision operator consumes the monopole (normal) history.
    """

    def __init__(self, N, rate, *, beta=None, direction=None):
        self.N = np.array(N, dtype=float, copy=True)
        q = np.array(rate, dtype=float, copy=True)
        if self.N.ndim != 1 or len(self.N) < 2 or not np.isfinite(self.N).all() or np.any(np.diff(self.N) <= 0):
            raise ValueError("opacity nodes must be finite and strictly increasing")
        if q.shape != self.N.shape or not np.isfinite(q).all() or np.any(q < 0):
            raise ValueError("opacity must be finite, nonnegative and match the nodes")
        if (beta is None) != (direction is None):
            raise ValueError("ray opacity requires both beta and propagation direction")
        if beta is not None:
            shape = (len(q), 3)
            v = np.broadcast_to(np.asarray(beta, dtype=float), shape)
            e = np.broadcast_to(np.asarray(direction, dtype=float), shape)
            if not np.isfinite(v).all() or np.any(np.linalg.norm(v, axis=1) >= 1):
                raise ValueError("electron velocities must be finite and subluminal")
            if not np.isfinite(e).all() or not np.allclose(np.linalg.norm(e, axis=1), 1, atol=2e-14, rtol=0):
                raise ValueError("propagation directions must be unit vectors")
            q *= 1.0 - np.einsum("ij,ij->i", v, e)
        self._rate = q
        self._pchip = PchipInterpolator(self.N, q, extrapolate=False)

    def rate(self, N):
        x = np.asarray(N, dtype=float)
        if not np.isfinite(x).all() or np.any(x < self.N[0]) or np.any(x > self.N[-1]):
            raise ValueError("opacity query outside the finite history")
        # At the terminal node use its value directly (power-basis endpoint cancellation).
        return np.where(x == self.N[-1], self._rate[-1], self._pchip(x))

    def cells(self, edges):
        edges = np.asarray(edges, dtype=float)
        if edges.ndim != 1 or len(edges) < 2 or not np.isfinite(edges).all() or np.any(np.diff(edges) <= 0):
            raise ValueError("cell edges must be finite and strictly increasing")
        if edges[0] < self.N[0] or edges[-1] > self.N[-1]:
            raise ValueError("cell edges outside the finite history")
        cuts = np.union1d(edges, self.N[(self.N > edges[0]) & (self.N < edges[-1])])
        half = np.diff(cuts) * 0.5
        mid = cuts[:-1] + half
        off = half / np.sqrt(3.0)
        # Two-point Gauss is exact for every cubic piece; no subtraction of large
        # prefix integrals when a thin reionization cell follows an opaque epoch.
        depth_piece = half * (self._pchip(mid-off) + self._pchip(mid+off))
        depth = np.add.reduceat(depth_piece, np.searchsorted(cuts, edges[:-1]))
        if not np.isfinite(depth).all() or np.any(depth < 0):
            raise FloatingPointError("opacity integration lost finiteness or positivity")
        tau = np.r_[np.cumsum(depth[::-1])[::-1], 0.0]
        if not np.isfinite(tau).all():
            raise FloatingPointError("optical depth to observer overflowed")
        return OpticalCells(depth, tau, np.exp(-tau[1:]) * (-np.expm1(-depth)))
