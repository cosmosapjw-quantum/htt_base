"""Observer-redshift opacity on the finite, non-tilted LRS Bianchi I material donor."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class RayOpacity:
    emission_N: np.ndarray
    optical_depth: np.ndarray
    depth_per_redshift: np.ndarray
    visibility_per_redshift: np.ndarray


class ReiObserverRays:
    """mu is the cosine in the observer tetrad relative to the symmetry axis.

    Metric axes are a exp(-b), a exp(-b), a exp(2b). Interpolation of b
    is linear in N on the signed archived trajectory. The redshift Jacobian
    at an interior knot uses the earlier (larger-redshift) segment.
    """
    def __init__(self, material, observer_z_mean=4.0):
        self.material = material
        if not np.isfinite(observer_z_mean) or not material.z[-1] <= observer_z_mean < material.z[0]:
            raise ValueError("observer must be inside the finite mean-redshift history, after its first event")
        self.N_o = -np.log1p(observer_z_mean)
        self.b_o = np.interp(self.N_o, material.N, material.b)
        self._slopes = np.diff(material.b)/np.diff(material.N)
        used = self._slopes[material.N[:-1] < self.N_o]
        # H_perp/H = 1-b', H_parallel/H = 1+2b'. Both must be
        # positive for a unique emission event on every configured ray.
        if not np.isfinite(used).all() or np.any(used >= 1) or np.any(used <= -0.5):
            raise ValueError("redshift is not strictly monotonic along all principal directions")

    @staticmethod
    def _direction(mu):
        mu = np.asarray(mu, dtype=float)
        if not np.isfinite(mu).all() or np.any(np.abs(mu) > 1):
            raise ValueError("mu must be a finite observer direction cosine in [-1,1]")
        return mu

    def log_frequency_ratio(self, N, mu):
        m = self.material
        N, mu = np.broadcast_arrays(np.asarray(N, dtype=float), self._direction(mu))
        if not np.isfinite(N).all() or np.any(N < m.N[0]) or np.any(N > self.N_o):
            raise ValueError("emission query outside the finite ray history")
        d = np.interp(N, m.N, m.b) - self.b_o
        # log1p/expm1 retain the anisotropic perturbation to the FLRW limit.
        mix = (1-mu**2)*np.expm1(2*d) + mu**2*np.expm1(-4*d)
        return self.N_o - N + 0.5*np.log1p(mix)

    def evaluate(self, redshift, mu):
        """Evaluate tau and e^-tau d tau/dz at the event selected by (z,mu).

        Arrays broadcast, so z[:,None] and mu[None,:] evaluate a sky by shell.
        Finite optical depths integrate material between emission and observer.
        """
        m = self.material
        z, mu = np.broadcast_arrays(np.asarray(redshift, dtype=float), self._direction(mu))
        if z.size == 0 or not np.isfinite(z).all() or np.any(z < 0):
            raise ValueError("require finite nonnegative ray redshifts")
        end = np.expm1(self.log_frequency_ratio(m.N[0], mu))
        if np.any(z > end):
            raise ValueError("requested redshift is outside this ray's material support")
        target = np.log1p(z)
        lo = np.full(z.shape, m.N[0])
        hi = np.full(z.shape, self.N_o)
        for _ in range(54):
            mid = lo + 0.5*(hi-lo)
            earlier = self.log_frequency_ratio(mid, mu) > target
            lo, hi = np.where(earlier, mid, lo), np.where(earlier, hi, mid)
        N = np.where(z == 0, self.N_o, np.where(z == end, m.N[0], lo+0.5*(hi-lo)))
        # Snap an exactly represented knot target back to that knot for the
        # one-sided Jacobian convention. Never snap off-grid redshift inputs.
        j = np.clip(np.searchsorted(m.N,N),1,len(m.N)-1)
        near = np.where(N-m.N[j-1] <= m.N[j]-N,m.N[j-1],m.N[j])
        near = np.minimum(near, self.N_o)
        N = np.where(z == np.expm1(self.log_frequency_ratio(near,mu)),near,N)
        knots, inverse = np.unique(np.r_[N.ravel(),self.N_o],return_inverse=True)
        future = m.cells(knots).tau_to_observer if len(knots)>1 else np.zeros(1)
        tau = future[inverse[:-1]].reshape(N.shape)
        diff_b = np.interp(N,m.N,m.b) - self.b_o
        w_para = mu**2 / (mu**2 + (1-mu**2)*np.exp(6*diff_b))
        i = np.clip(np.searchsorted(m.N,N,side="left")-1,0,len(self._slopes)-1)
        H_ray_over_H = 1+self._slopes[i]*(3*w_para-1)
        jac = m.rate(N) / ((1+z)*H_ray_over_H)
        return RayOpacity(N,tau,jac,np.exp(-tau)*jac)
