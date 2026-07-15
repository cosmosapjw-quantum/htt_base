"""
htt/bridge/runner.py — Bridge Bundle Runner
=============================================
C-08 deliverable. Runs all bridge estimators and collects results.
All outputs are tagged EXPLORATORY and quarantined.  Callers must supply an
explicit non-CF4 synthetic/user parameter; no observational default exists.
"""
import math

from htt.bridge.estimators import (
    tilt_velocity, delta_H, delta_q, lambda_J_pec,
    BridgeResult, BRIDGE_STATUS,
)
from htt.core.cf4_observational_input import (
    OPEN_FINDING_IDS,
    require_cf4_observational_input,
)

__all__ = ['run_bridge_bundle']


def run_bridge_bundle(
    beta: float | None = None,
    H0: float = 67.36,
    *,
    input_mode: str | None = None,
) -> dict:
    """Run all bridge estimators and return a bundle.

    All results are tagged EXPLORATORY (permanently segregated). ``input_mode``
    must be ``synthetic`` or ``user_supplied_non_cf4``; observational CF4 use
    is not an active route.
    """
    if beta is None:
        require_cf4_observational_input(consumer="run_bridge_bundle default beta")
    if input_mode not in {'synthetic', 'user_supplied_non_cf4'}:
        raise ValueError(
            "run_bridge_bundle requires input_mode="
            "'synthetic' or 'user_supplied_non_cf4'; CF4 defaults are quarantined"
        )
    beta = float(beta)
    if not math.isfinite(beta):
        raise ValueError("explicit beta must be finite")
    depths = [30, 50, 75, 100, 150, 222, 500, 1000]

    results = {
        'status': BRIDGE_STATUS,
        'input_mode': input_mode,
        'excluded_channels': ['c'],
        'cf4_channel_status': 'QUARANTINED_OPEN_FINDINGS',
        'cf4_finding_ids': list(OPEN_FINDING_IDS),
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
