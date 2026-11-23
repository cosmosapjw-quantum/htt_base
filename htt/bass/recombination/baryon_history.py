"""Conserved hydrogen current and baryon-rest kinematics for supplied Bianchi trajectories."""
import math
import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator

from bass.background.convention_bridge import build_structure_tensor_with_sign
from bass.background.tilted_bianchi_state import SpeciesFluidCongruence, compute_species_congruence_kinematics


class BaryonHistory:
    """N=ln(a), H, normal shear and spatial commutators in s^-1; beta=v/c.

    Anchor D a³ at today's N=0, D=Gamma n_rest. With VER2 a_sign=+1,
    div_spatial(beta)=-2 a·beta, so d ln(D a³)/dN=2 (a/H)·beta.
    Returned acceleration components are physical acceleration divided by c [s^-1].
    """
    def __init__(self, N, H, normal_shear, a, n, beta):
        self.N = np.asarray(N, dtype=float)
        H, normal_shear, a, n, beta = [np.asarray(t, dtype=float) for t in (H, normal_shear, a, n, beta)]
        k = len(self.N)
        if (self.N.shape != (k,) or k < 2 or np.any(np.diff(self.N) <= 0) or self.N[-1] != 0
                or [t.shape for t in (H, normal_shear, a, n, beta)] != [(k,), (k,3,3), (k,3), (k,3,3), (k,3)]
                or not all(np.isfinite(t).all() for t in (self.N, H, normal_shear, a, n, beta))
                or np.any(H <= 0) or np.any(np.linalg.norm(beta, axis=1) >= 1)):
            raise ValueError("need a finite subluminal Bianchi history ending at N=0 in SI time units")
        self._beta = CubicSpline(self.N, beta)
        self._log_H = PchipInterpolator(self.N, np.log(H))
        self._drift = PchipInterpolator(self.N, 2.0*np.einsum("ij,ij->i", a, beta)/H)
        self._drift_int = self._drift.antiderivative()
        self._drift_zero = float(self._drift_int(0))
        self._drift_first = float(self._drift(self.N[0]))
        theta = np.empty(k)
        shear = np.empty((k,3,3))
        acceleration = np.empty((k,3))
        for i, (hv, v, dv) in enumerate(zip(H, beta, self._beta(self.N, 1))):
            C = build_structure_tensor_with_sign(a[i], n[i], a_sign=1)
            state = SpeciesFluidCongruence("baryon", 1.0, 0.0, v, hv*dv)
            kin = compute_species_congruence_kinematics(state, H=hv, sigma_ab=normal_shear[i], C_spatial=C)
            g = state.gamma
            # Spatial legs E_i^a of the rotation-free boost from the normal tetrad.
            space = np.eye(3) + (g*g/(g+1))*np.outer(v,v)
            E = np.column_stack((g*v, space))
            theta[i] = kin.theta_tilde / hv
            shear[i] = E @ kin.sigma_tilde_4d @ E.T / hv
            acceleration[i] = E @ kin.acceleration_tilde_4d / hv  # kin stores covariant components
        self._theta = CubicSpline(self.N, theta)
        self._shear = CubicSpline(self.N, shear)
        self._acceleration = CubicSpline(self.N, acceleration)

    def _time(self, N):
        # HYREC's Saha warm start can lie earlier than the first background sample.
        # Freeze dimensionless kinematics there; density continues at the first flux slope.
        return min(max(float(N), self.N[0]), self.N[-1])

    def hydrogen_factor(self, N):
        if N > self.N[-1]:
            raise ValueError("hydrogen history stops at the N=0 anchor")
        t = self._time(N)
        return math.exp(float(self._drift_int(t)) - self._drift_zero + self._drift_first*(N-t))

    def H(self, N):
        return math.exp(float(self._log_H(self._time(N))))

    def beta(self, N):
        return self._beta(self._time(N))

    def theta(self, N):
        return self.H(N)*float(self._theta(self._time(N)))

    def shear(self, N):
        return self.H(N)*self._shear(self._time(N))

    def acceleration(self, N):
        return self.H(N)*self._acceleration(self._time(N))
