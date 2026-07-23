"""PR-222: finite-window stochastic bulk-flow to homogeneous-tilt bridge.

The CF4-to-homogeneous-tilt relation is a multi-window stochastic forward
operator, not a point substitution. A single bulk-flow amplitude (one window)
has rank 1 and cannot identify the 3-component homogeneous tilt; a multi-window
field bridge has rank 3 and does. The GLS estimator through the multi-window
operator recovers the truth with small bias. The exact rank fact is CAS-verified
(PR-222 five-axis: multi-window Gram det = 394584 != 0).
"""
from __future__ import annotations
import numpy as np

# window operator (rows = windows, cols = homogeneous tilt components)
W = np.array([[1.0, 0.1, 0.0], [0.2, 0.8, 0.1], [0.0, 0.2, 0.7], [0.6, 0.3, 0.2]])


def fisher_rank(cov_diag: float = 0.3, cov_off: float = 0.08) -> dict:
    C = cov_diag * np.eye(4) + cov_off * np.ones((4, 4))
    Ci = np.linalg.inv(C)
    F = W.T @ Ci @ W
    return {"multi_window_rank": int(np.linalg.matrix_rank(F)),
            "single_window_rank": int(np.linalg.matrix_rank(W[:1])),
            "fisher": F}


def recover(truth=(0.8, -0.3, 0.2), nrep: int = 5000, seed: int = 20260721,
            cov_diag: float = 0.3, cov_off: float = 0.08) -> dict:
    rng = np.random.default_rng(seed)
    truth = np.asarray(truth, float)
    C = cov_diag * np.eye(4) + cov_off * np.ones((4, 4))
    Ci = np.linalg.inv(C)
    F = W.T @ Ci @ W
    A = np.linalg.inv(F) @ W.T @ Ci    # GLS estimator
    est = np.array([A @ (W @ truth + rng.multivariate_normal(np.zeros(4), C))
                    for _ in range(nrep)])
    bias = float(np.linalg.norm(est.mean(0) - truth))
    return {"truth": truth.tolist(), "estimated_mean": est.mean(0).tolist(),
            "bias_norm": bias, "recovers": bias < 0.03}


def single_window_cannot_identify() -> bool:
    """One bulk amplitude (rank 1) cannot point-identify a 3-D tilt."""
    return int(np.linalg.matrix_rank(W[:1])) < 3
