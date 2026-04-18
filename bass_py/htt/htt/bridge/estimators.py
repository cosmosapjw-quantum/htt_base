"""
htt/bridge/estimators.py — Bridge Estimator Wrappers
======================================================
C-08 deliverable. Re-exports bridge estimators from htt.infer.estimators
with explicit EXPLORATORY status enforcement.

All bridge outputs are permanently segregated from the core result path.
They are EXPLORATORY (○) and quarantined in Appendix J.
"""
from htt.infer.estimators import (
    BridgeResult, tilt_velocity, delta_H, delta_q,
    lambda_J_pec, age_bias,
)

__all__ = [
    'BridgeResult', 'tilt_velocity', 'delta_H', 'delta_q',
    'lambda_J_pec', 'age_bias',
    'BRIDGE_STATUS',
]

BRIDGE_STATUS = 'EXPLORATORY'


def verify_all_exploratory():
    """Verify that all bridge estimators produce EXPLORATORY results."""
    results = [
        tilt_velocity(beta=1e-3),
        delta_H(beta=1e-3, d_Mpc=100),
        delta_q(beta=1e-3, d_Mpc=100),
        lambda_J_pec(beta=1e-3),
    ]
    for r in results:
        assert r.status == BRIDGE_STATUS, \
            f"Bridge result has status '{r.status}', expected '{BRIDGE_STATUS}'"
    return True
