"""Read-only independent counterexamples against the frozen R36 candidate."""
from pathlib import Path
import json
import sys

import numpy as np
import scipy

PRODUCT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT')
sys.path.insert(0, str(PRODUCT))
from optical_joint import joint_test

s = np.diag([0.001, -0.001, 0.0])
d_obs = np.array([0.001, 0.0, 0.0])
o = np.zeros(7)
false_rejection = joint_test(o, s, d_obs, 1e-8, e_d=0.002, d_max=0.01)
tiny_o = np.array([1e-200, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
false_acceptance = joint_test(tiny_o, np.zeros((3, 3)), np.zeros(3), 0.0)
tiny_s = np.diag([1e-200, -1e-200, 0.0])
wrong_zero_branch = joint_test(tiny_o, tiny_s, np.zeros(3), 0.0)

print(json.dumps({
    'python': sys.version,
    'numpy': np.__version__,
    'scipy': scipy.__version__,
    'false_rejection': {
        'inputs': {'S': s.tolist(), 'O': o.tolist(), 'd_obs': d_obs.tolist(),
                   'budget': 1e-8, 'e_d': 0.002, 'd_max': 0.01},
        'witness': {'d': [0.0, 0.0, 0.0], 'distance_to_d_obs': 0.001,
                    'physical_norm': 0.0, 'residual_norm': 0.0,
                    'strictly_inside_both_balls': True},
        'expected_compatible': True,
        'observed': false_rejection,
    },
    'false_acceptance': {
        'inputs': {'S': np.zeros((3, 3)).tolist(), 'O': tiny_o.tolist(),
                   'd_obs': [0.0, 0.0, 0.0], 'budget': 0.0, 'e_d': 0.0},
        'exact_residual_norm': 1e-200,
        'expected_compatible': False,
        'observed': false_acceptance,
    },
    'wrong_zero_branch': {
        'inputs': {'S': tiny_s.tolist(), 'O': tiny_o.tolist(),
                   'd_obs': [0.0, 0.0, 0.0], 'budget': 0.0, 'e_d': 0.0},
        'S_has_nonzero_entries': bool(np.any(tiny_s != 0)),
        'expected_branch': 'INVERTIBLE_S',
        'expected_compatible': False,
        'observed': wrong_zero_branch,
    },
}, indent=2, allow_nan=False))
