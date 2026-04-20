"""
Phase 5: Bridge metadata object per §4.2.

Every bridge observable must carry:
  name, estimator, assumptions, selection_model,
  depth_kernel, nuisance_model, status (always EXPLORATORY).
"""
from dataclasses import dataclass
from typing import Tuple

__all__ = [
    'BridgeMetadata',
    'BridgePromotionDecision',
    'BRIDGE_REGISTRY',
    'directional_bridge_promotion_gate',
]

@dataclass(frozen=True)
class BridgeMetadata:
    name: str
    estimator: str
    assumptions: Tuple[str, ...]
    selection_model: str = 'none'
    depth_kernel: str = 'none'
    nuisance_model: str = 'none'
    status: str = 'EXPLORATORY'
    H0_dependent: bool = False
    validated: bool = False


@dataclass(frozen=True)
class BridgePromotionDecision:
    """Closed-fail decision for any bridge → HTT production promotion attempt."""

    name: str
    allowed: bool
    reason: str
    required_gate: str = 'bridge_exploratory_only'


BRIDGE_REGISTRY = {
    'v_tilt': BridgeMetadata(
        name='v_tilt', estimator='beta * c',
        assumptions=('single-fluid', 'linearised kinematics'),
        H0_dependent=False),
    'delta_H': BridgeMetadata(
        name='delta_H', estimator='beta * c / (3 * d)',
        assumptions=('single-fluid', 'linearised', 'Tsagas formula'),
        depth_kernel='1/d', H0_dependent=False),
    'delta_q': BridgeMetadata(
        name='delta_q', estimator='beta * (lambda_H/d)^3',
        assumptions=('single-fluid', 'linearised', 'adiabatic'),
        depth_kernel='1/d^3', H0_dependent=True),
    'lambda_J_pec': BridgeMetadata(
        name='lambda_J_pec', estimator='c / (H0 * sqrt(Omega_m))',
        assumptions=('single-fluid', 'matter-dominated'),
        H0_dependent=True),
    'age_bias': BridgeMetadata(
        name='age_bias', estimator='delta_t / t_lookback',
        assumptions=('Son+2025 methodology',),
        H0_dependent=True),
}


def directional_bridge_promotion_gate(name: str) -> BridgePromotionDecision:
    """Bridge observables remain exploratory and cannot seed production HTT inputs."""
    if name not in BRIDGE_REGISTRY:
        raise KeyError(f"Unknown bridge observable: {name}")
    return BridgePromotionDecision(
        name=name,
        allowed=False,
        reason=(
            "Bridge observables are exploratory-only and cannot be promoted into "
            "HTT production directional likelihood inputs."
        ),
    )
