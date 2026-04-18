"""
htt/bridge/runner.py — Bridge Bundle Runner
=============================================
C-08 deliverable. Runs all bridge estimators and collects results.
All outputs are tagged EXPLORATORY and quarantined.
"""
from htt.bridge.estimators import (
    tilt_velocity, delta_H, delta_q, lambda_J_pec,
    BridgeResult, BRIDGE_STATUS,
)

__all__ = ['run_bridge_bundle']


def run_bridge_bundle(beta: float = 1.334e-3,
                      H0: float = 67.36) -> dict:
    """Run all bridge estimators and return a bundle.

    All results are tagged EXPLORATORY (permanently segregated).
    """
    depths = [30, 50, 75, 100, 150, 222, 500, 1000]

    results = {
        'status': BRIDGE_STATUS,
        'beta': beta,
        'H0': H0,
        'tilt_velocity': {
            'value': tilt_velocity(beta).value,
            'unit': 'km/s',
        },
        'lambda_J': {
            'value': lambda_J_pec(beta, H0).value,
            'unit': 'Mpc',
        },
        'delta_H_profile': {},
        'delta_q_profile': {},
    }

    for d in depths:
        dH = delta_H(beta, d)
        dq = delta_q(beta, d)
        results['delta_H_profile'][str(d)] = {
            'value': dH.value, 'unit': 'km/s/Mpc',
        }
        results['delta_q_profile'][str(d)] = {
            'value': dq.value,
        }

    return results
