"""HTT bridge subpackage -- exploratory estimators (permanently segregated).

All outputs are EXPLORATORY and quarantined in Appendix J.
They do NOT enter the core established result path.
"""

from htt.bridge.estimators import (
    BridgeResult, tilt_velocity, delta_H, delta_q,
    lambda_J_pec, BRIDGE_STATUS,
)
from htt.bridge.metadata import directional_bridge_promotion_gate
from htt.bridge.runner import run_bridge_bundle

__all__ = [
    'BridgeResult', 'tilt_velocity', 'delta_H', 'delta_q',
    'lambda_J_pec', 'BRIDGE_STATUS', 'directional_bridge_promotion_gate',
    'run_bridge_bundle',
]
