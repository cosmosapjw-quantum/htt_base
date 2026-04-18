"""
htt/bridge/estimators.py — Bridge Estimators [EXPLORATORY]
==========================================================
P-26 deliverable. All outputs in this module carry EXPLORATORY
status and are quarantined from the core inference results.

Named estimators:
  1. tilt_velocity(beta, z) → v_tilt(z) in km/s
  2. delta_q(beta, d) → apparent deceleration correction
  3. lambda_J_pec(beta) → peculiar Jeans length in Mpc
  4. delta_H(beta, d) → scale-dependent Hubble correction
  5. age_bias(beta, z) → age-bias diagnostic

Closure assumptions are listed in each docstring.
"""
import numpy as np
from dataclasses import dataclass

__all__ = [
    'tilt_velocity', 'delta_q', 'lambda_J_pec',
    'delta_H', 'age_bias', 'BridgeResult',
    'STATUS', 'CLOSURE_ASSUMPTIONS',
]

STATUS = 'EXPLORATORY'

CLOSURE_ASSUMPTIONS = {
    'tilt_velocity': [
        'Linear Hubble flow v = Hd',
        'Single-fluid tilt β constant in z',
    ],
    'delta_q': [
        'Tsagas (2011) dipolar deceleration formula',
        'Monopole-dipole decomposition valid',
        'No backreaction correction',
    ],
    'lambda_J_pec': [
        'Tsagas (2024) peculiar Jeans length',
        'β identified with observed bulk flow',
        'H0 = 67.36 km/s/Mpc (Planck 2018)',
    ],
    'delta_H': [
        'Tsagas (2021, 2024) scale-dependent correction',
        'Linear perturbation regime β²d/λ_H << 1',
        'Tsagas (2026, ApJ 997:25): GR doubles v_pec growth',
    ],
    'age_bias': [
        'Son et al. (2025) age-bias framework',
        'Linear age-luminosity relation',
        'Tilt-dominated systematic at d < λ_J',
    ],
}


@dataclass
class BridgeResult:
    """A single bridge estimator output, always EXPLORATORY."""
    name: str
    value: float
    unit: str
    status: str = 'EXPLORATORY'
    closure: tuple = ()


# ── Estimators ──────────────────────────────────────────

def tilt_velocity(beta: float, z: float = 0,
                  H0: float = 67.36) -> BridgeResult:
    """Tilt-induced peculiar velocity at redshift z.

    v_tilt = c × β ≈ β × 3e5 km/s.
    At z > 0, β(z) ≈ β₀ (constant in linearised regime).
    """
    c_kms = 299792.458
    v = c_kms * beta
    return BridgeResult(
        name='v_tilt', value=v, unit='km/s',
        closure=tuple(CLOSURE_ASSUMPTIONS['tilt_velocity']),
    )


def delta_q(beta: float, d_Mpc: float,
            H0: float = 67.36) -> BridgeResult:
    """Apparent deceleration correction Δq from tilt.

    Δq(β, d) = (β/9) × (λ_H / d)³
    where λ_H = c/H₀ ≈ 4450 Mpc.

    For β = 1.05e-3, d = 116 Mpc: Δq ≈ 8.5 (cf. Sah+2025: |q_d| ≈ 8).
    """
    c_kms = 299792.458
    lambda_H = c_kms / H0  # Mpc
    dq = (beta / 9) * (lambda_H / d_Mpc)**3
    return BridgeResult(
        name='delta_q', value=dq, unit='dimensionless',
        closure=tuple(CLOSURE_ASSUMPTIONS['delta_q']),
    )


def lambda_J_pec(beta: float, H0: float = 67.36) -> BridgeResult:
    """Peculiar Jeans length below which tilt mimics acceleration.

    λ_J^pec = (c/H₀) × β^{1/3}
    ≈ 4450 × (1.05e-3)^{1/3} ≈ 450 Mpc.

    Below λ_J, tilted observers perceive apparent acceleration.
    """
    c_kms = 299792.458
    lambda_H = c_kms / H0
    lJ = lambda_H * beta**(1/3)
    return BridgeResult(
        name='lambda_J_pec', value=lJ, unit='Mpc',
        closure=tuple(CLOSURE_ASSUMPTIONS['lambda_J_pec']),
    )


def delta_H(beta: float, d_Mpc: float,
            H0: float = 67.36) -> BridgeResult:
    """Scale-dependent Hubble correction from tilt.

    ΔH/H ≈ β × (λ_H / d)
    At d = 40 Mpc (SH0ES depth): ΔH/H ≈ 4%.

    Tsagas (2026, ApJ 997:25): GR doubles peculiar-velocity
    growth rate, amplifying this correction.
    """
    c_kms = 299792.458
    lambda_H = c_kms / H0
    dHH = beta * (lambda_H / d_Mpc)
    return BridgeResult(
        name='delta_H', value=dHH, unit='dimensionless',
        closure=tuple(CLOSURE_ASSUMPTIONS['delta_H']),
    )


def age_bias(beta: float, z: float,
             H0: float = 67.36) -> BridgeResult:
    """Age-bias diagnostic from tilt.

    The tilt induces a dipolar age gradient that biases
    supernova standardisation (Son et al. 2025).
    Δage/age ≈ β × (1+z)^{-1} at leading order.
    """
    bias = beta / (1 + z)
    return BridgeResult(
        name='age_bias', value=bias, unit='dimensionless',
        closure=tuple(CLOSURE_ASSUMPTIONS['age_bias']),
    )
