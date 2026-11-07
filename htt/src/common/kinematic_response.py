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
    stf_shear_amplitudes: np.ndarray # 5-vector of dimensionless sigma/H0 E2/STF amplitudes
    e1_polar_vector: np.ndarray  # E1 polar carrier, 3-vector
    b1_axial_vector: np.ndarray  # B1 axial carrier, 3-vector
    closure_type: str = "FIRST_ORDER_SUBTRACTION"
    closure_residual: np.ndarray | None = None
    
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
        exact_composition: bool = False,
    ) -> "KinematicResponseModel":
        """Factory with declared frame-velocity closure.

        When exact_composition is False (default), sets beta_MO = beta_RO - beta_RM
        at first order and records closure_type="FIRST_ORDER_SUBTRACTION".
        When exact_composition is True, computes relativistic composition via
        compose_velocities and records closure_type="EXACT_LORENTZ_BOOST".
        """
        bro = np.asarray(beta_RO, dtype=np.float64)
        if bro.shape != (3,):
            raise KinematicsError("beta_RO must be a 3-vector")
        brm = np.zeros(3, dtype=np.float64) if beta_RM is None else np.asarray(beta_RM, dtype=np.float64)
        if brm.shape != (3,):
            raise KinematicsError("beta_RM must be a 3-vector")
            
        if exact_composition:
            # Under standard boost convention, velocity of Observer in Matter frame
            bmo = compose_velocities(bro, brm)
            closure_type = "EXACT_LORENTZ_BOOST"
        else:
            # First-order only: beta_RO = beta_RM + beta_MO + O(beta^2)
            bmo = bro - brm
            closure_type = "FIRST_ORDER_SUBTRACTION"
        
        residual = (brm + bmo) - bro
        
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
            closure_type=closure_type,
            closure_residual=residual,
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
        """Dimensionless STF shear quadrupole for stored sigma/H0 coefficients.

        Physical sigma_ab must first be divided by the same nonzero H0.
        This carrier adapter is not a replacement for the raw kinematic tensor.
        """
        n = np.asarray(directions, dtype=np.float64)
        # Evaluate n^T E_a n for each basis element a
        stf_angular = np.einsum("ni,aij,nj->na", n, STF_BASIS, n, optimize=True)
        return stf_angular @ self.state.stf_shear_amplitudes

    def directional_hubble_variation(
        self,
        directions: np.ndarray,
        redshift: float = 0.0,
        acceleration_vector: np.ndarray | None = None,
        *,
        acceleration_over_cH: np.ndarray | None = None,
        H0: float | None = None,
        speed_of_light: float | None = None,
    ) -> np.ndarray:
        """Local optical directional Hubble variation Delta H(n) / H_0.

        The shear amplitudes in this legacy response model are already
        dimensionless (sigma/H0). Supply either the dimensionless vector
        A/(c H0), or a physical acceleration A in m s^-2 together with
        explicit nonzero H0 in s^-1 and c in m s^-1. A physical acceleration
        is never subtracted directly from a dimensionless response.
        """
        n = np.asarray(directions, dtype=np.float64)
        if n.ndim != 2 or n.shape[1] != 3:
            raise KinematicsError("directions must be N x 3")
        if not np.all(np.isfinite(n)):
            raise KinematicsError("directions must be finite")
        response = self.optical_shear_quadrupole(n)
        if acceleration_vector is not None and acceleration_over_cH is not None:
            raise KinematicsError("supply physical acceleration or A/(cH), not both")
        if acceleration_over_cH is not None:
            a_over_cH = np.asarray(acceleration_over_cH, dtype=np.float64)
        elif acceleration_vector is not None:
            if H0 is None or speed_of_light is None:
                raise KinematicsError("physical acceleration requires explicit H0 and speed_of_light")
            h0 = float(H0)
            c = float(speed_of_light)
            if not np.isfinite([h0, c]).all() or h0 == 0.0 or c <= 0.0:
                raise KinematicsError("require finite nonzero H0 and positive speed_of_light")
            physical_acceleration = np.asarray(acceleration_vector, dtype=np.float64)
            if physical_acceleration.shape != (3,) or not np.all(np.isfinite(physical_acceleration)):
                raise KinematicsError("physical acceleration must be a finite 3-vector")
            a_over_cH = physical_acceleration / (c * h0)
        else:
            a_over_cH = None
        if a_over_cH is not None:
            if a_over_cH.shape != (3,) or not np.all(np.isfinite(a_over_cH)):
                raise KinematicsError("A/(cH) must be a finite 3-vector")
            response -= n @ a_over_cH
        return response

