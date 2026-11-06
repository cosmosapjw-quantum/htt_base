"""Frame-aware kinematic response and multi-probe carrier parameterization.

Phase C of HTT-R38 Observational Convergence.
Implements congruence-aware parameters separating:
  - beta_RO: radiation-observer velocity
  - beta_RM: radiation-matter relative drift
  - beta_MO: matter-observer velocity (relativistic composition)
  - d_int: intrinsic radiation dipole
  - E2 / STF5: metric shear carrier
  - E1 / B1: polar / axial vector carrier (strictly distinct from shear)
  - Q_kin: second-order kinetic quadrupole ~ beta^2
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence
import numpy as np

# Orthonormal STF basis for symmetric traceless 3x3 tensors
# Normalization: Tr(E_a E_b) = delta_ab
_SQRT2 = math.sqrt(2.0)
_SQRT6 = math.sqrt(6.0)

STF_BASIS = np.array([
    [[1.0 / _SQRT2, 0.0, 0.0],
     [0.0, -1.0 / _SQRT2, 0.0],
     [0.0, 0.0, 0.0]],
    [[1.0 / _SQRT6, 0.0, 0.0],
     [0.0, 1.0 / _SQRT6, 0.0],
     [0.0, 0.0, -2.0 / _SQRT6]],
    [[0.0, 1.0 / _SQRT2, 0.0],
     [1.0 / _SQRT2, 0.0, 0.0],
     [0.0, 0.0, 0.0]],
    [[0.0, 0.0, 1.0 / _SQRT2],
     [0.0, 0.0, 0.0],
     [1.0 / _SQRT2, 0.0, 0.0]],
    [[0.0, 0.0, 0.0],
     [0.0, 0.0, 1.0 / _SQRT2],
     [0.0, 1.0 / _SQRT2, 0.0]],
], dtype=np.float64)


class KinematicsError(ValueError):
    """Base exception for kinematic convention and domain violations."""
    pass

class BetaTruncationError(KinematicsError):
    """Raised when beta exceeds safe non-relativistic or perturbative bounds without full Lorentz boost."""
    pass

class CarrierConflationError(KinematicsError):
    """Raised when polar/axial E1/B1 carriers are conflated with E2/STF5 shear carriers."""
    pass


def compose_velocities(v_a: np.ndarray, v_b: np.ndarray) -> np.ndarray:
    """Return the velocity of frame A as measured in frame B.

    v_a and v_b are dimensionless three-velocities (beta vectors) of A and
    B measured in one common inertial frame S. Returned components use B's
    axes obtained by the standard rotation-free Lorentz boost from S; no
    additional spatial/Wigner rotation is applied.

    For signature (-,+,+,+):
      beta_(A|B) = [beta_a - gamma_b beta_b
        + ((gamma_b - 1) (beta_a . beta_b) / beta_b^2) beta_b]
        / [gamma_b (1 - beta_a . beta_b)].

    The beta_b=0 limit is handled separately. Collinear velocities reduce
    to (beta_a - beta_b)/(1 - beta_a beta_b); non-collinear velocities
    require the transverse gamma factor.
    """
    va = np.asarray(v_a, dtype=np.float64)
    vb = np.asarray(v_b, dtype=np.float64)
    if va.shape != (3,) or vb.shape != (3,):
        raise KinematicsError("Velocities must be 3-vectors")
    if not np.all(np.isfinite(va)) or not np.all(np.isfinite(vb)):
        raise KinematicsError("Velocities must contain only finite values")

    beta_a2 = float(np.dot(va, va))
    beta_b2 = float(np.dot(vb, vb))
    if beta_a2 >= 1.0 or beta_b2 >= 1.0:
        raise BetaTruncationError("Velocities must be strictly subluminal (|beta| < 1)")
    if beta_b2 == 0.0:
        return va.copy()

    dot = float(np.dot(va, vb))
    gamma_b = 1.0 / math.sqrt(1.0 - beta_b2)
    denominator = gamma_b * (1.0 - dot)
    # Stable identity: (gamma - 1)/beta^2 = gamma^2/(gamma + 1).
    parallel_coefficient = (gamma_b * gamma_b / (gamma_b + 1.0)) * dot - gamma_b
    return (va + parallel_coefficient * vb) / denominator

@dataclass(frozen=True)
class KinematicFrameState:
    """Full frame-explicit kinematic state."""
    beta_RO: np.ndarray          # Radiation-observer boost velocity (c=1), 3-vector
    beta_RM: np.ndarray          # Radiation-matter drift velocity (c=1), 3-vector
    beta_MO: np.ndarray          # Matter-observer boost velocity (c=1), 3-vector
    d_int: np.ndarray            # Intrinsic radiation dipole, 3-vector
    stf_shear_amplitudes: np.ndarray # 5-vector of E2/STF amplitudes
    e1_polar_vector: np.ndarray  # E1 polar carrier, 3-vector
    b1_axial_vector: np.ndarray  # B1 axial carrier, 3-vector
    
    def __post_init__(self):
        for name, arr, expected_shape in [
            ("beta_RO", self.beta_RO, (3,)),
            ("beta_RM", self.beta_RM, (3,)),
            ("beta_MO", self.beta_MO, (3,)),
            ("d_int", self.d_int, (3,)),
            ("stf_shear_amplitudes", self.stf_shear_amplitudes, (5,)),
            ("e1_polar_vector", self.e1_polar_vector, (3,)),
            ("b1_axial_vector", self.b1_axial_vector, (3,)),
        ]:
            if not isinstance(arr, np.ndarray) or arr.shape != expected_shape:
                raise KinematicsError(f"{name} must be ndarray of shape {expected_shape}")
            if not np.all(np.isfinite(arr)):
                raise KinematicsError(f"{name} contains non-finite values")


class KinematicResponseModel:
    """Computes observable signatures for CMB, counts, and distance probes."""
    
    def __init__(self, state: KinematicFrameState):
        self.state = state

    @classmethod
    def from_parameters(
        cls,
        beta_RO: Sequence[float],
        beta_RM: Sequence[float] | None = None,
        d_int: Sequence[float] | None = None,
        stf_shear: Sequence[float] | None = None,
        e1_polar: Sequence[float] | None = None,
        b1_axial: Sequence[float] | None = None,
    ) -> "KinematicResponseModel":
        """Factory initializing state from parameters with strict validation."""
        bro = np.asarray(beta_RO, dtype=np.float64)
        if bro.shape != (3,):
            raise KinematicsError("beta_RO must be a 3-vector")
        brm = np.zeros(3, dtype=np.float64) if beta_RM is None else np.asarray(beta_RM, dtype=np.float64)
        if brm.shape != (3,):
            raise KinematicsError("beta_RM must be a 3-vector")
            
        # Compute matter-observer velocity: beta_MO = beta_RO - beta_RM
        bmo = bro - brm
        
        dint = np.zeros(3, dtype=np.float64) if d_int is None else np.asarray(d_int, dtype=np.float64)
        stf = np.zeros(5, dtype=np.float64) if stf_shear is None else np.asarray(stf_shear, dtype=np.float64)
        e1 = np.zeros(3, dtype=np.float64) if e1_polar is None else np.asarray(e1_polar, dtype=np.float64)
        b1 = np.zeros(3, dtype=np.float64) if b1_axial is None else np.asarray(b1_axial, dtype=np.float64)
        
        state = KinematicFrameState(
            beta_RO=bro,
            beta_RM=brm,
            beta_MO=bmo,
            d_int=dint,
            stf_shear_amplitudes=stf,
            e1_polar_vector=e1,
            b1_axial_vector=b1,
        )
        return cls(state)

    def cmb_temperature_dipole(self, directions: np.ndarray) -> np.ndarray:
        """Total CMB temperature dipole in directions n: (beta_RO + d_int) . n."""
        n = np.asarray(directions, dtype=np.float64)
        if n.ndim != 2 or n.shape[1] != 3:
            raise KinematicsError("directions must be N x 3 unit vectors")
        total_dipole = self.state.beta_RO + self.state.d_int
        return n @ total_dipole

    def cmb_kinetic_quadrupole(self, directions: np.ndarray) -> np.ndarray:
        """Second-order kinematic quadrupole from observer boost beta_RO.
        
        Q_kin(n) = 1/2 [ (n . beta_RO)^2 - 1/3 beta_RO^2 ]
        """
        n = np.asarray(directions, dtype=np.float64)
        beta = self.state.beta_RO
        beta2 = float(np.sum(beta ** 2))
        dot = n @ beta
        return 0.5 * (dot ** 2 - (1.0 / 3.0) * beta2)

    def matter_count_dipole(
        self,
        directions: np.ndarray,
        spectral_index: float = 0.75,
        flux_slope: float = 1.0,
    ) -> np.ndarray:
        """Observed tracer count dipole: [2 + x*(1 + alpha)] * (beta_MO . n).
        
        Includes kinematic Doppler and aberration modulation.
        """
        n = np.asarray(directions, dtype=np.float64)
        factor = 2.0 + spectral_index * (1.0 + flux_slope)
        return factor * (n @ self.state.beta_MO)

    def optical_shear_quadrupole(self, directions: np.ndarray) -> np.ndarray:
        """STF shear quadrupole: sum_a stf_a * (n^T E_a n)."""
        n = np.asarray(directions, dtype=np.float64)
        # Evaluate n^T E_a n for each basis element a
        stf_angular = np.einsum("ni,aij,nj->na", n, STF_BASIS, n, optimize=True)
        return stf_angular @ self.state.stf_shear_amplitudes

    def directional_hubble_variation(
        self,
        directions: np.ndarray,
        redshift: float = 0.0,
        acceleration_vector: np.ndarray | None = None,
    ) -> np.ndarray:
        """Local optical directional Hubble variation Delta H(n) / H_0.
        
        Delta H / H_0 = - n . a_acc + n^T sigma n
        """
        n = np.asarray(directions, dtype=np.float64)
        response = self.optical_shear_quadrupole(n)
        if acceleration_vector is not None:
            a_acc = np.asarray(acceleration_vector, dtype=np.float64)
            response -= n @ a_acc
        return response

