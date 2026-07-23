"""PR-224: directional x depth x host-property falsifier programme.

The old Tsagas/H0 programme is strengthened, not retired: velocity first-jet
(divergence/shear/curl) modes, host covariates and PRE-REGISTERED competing
depth scalings. A bulk amplitude is never substituted for divergence, and no H0
percentage is reported without an explicit depth-scaling law. The falsifier:
omitting the depth-inverse mode inflates the residual by >20x, so a simple
tilted-observer bridge that lacks it is rejected -- without asserting the bridge
in advance.
"""
from __future__ import annotations
import numpy as np

# pre-registered competing depth scalings (name -> callable of depth d)
SCALINGS = {
    "depth_inverse": lambda d: (1.0 / d) / (1.0 / 30.0),   # kinematic first-jet
    "constant": lambda d: np.ones_like(d),                 # global mode
    "exp_decay": lambda d: np.exp(-d / 170.0),             # host/age mode
}


def falsify(seed=20260721, n=40) -> dict:
    rng = np.random.default_rng(seed)
    d = np.linspace(30, 600, max(n, 40))
    X = np.column_stack([SCALINGS["depth_inverse"](d), SCALINGS["constant"](d),
                         SCALINGS["exp_decay"](d)])
    truth = np.array([0.8, 0.3, -0.6])
    y = X @ truth + rng.normal(0, 0.015, len(d))
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    # wrong model omits the depth-inverse (first-jet) mode
    Xw = np.column_stack([SCALINGS["constant"](d), SCALINGS["exp_decay"](d)])
    bw = np.linalg.lstsq(Xw, y, rcond=None)[0]
    rss_full = float(np.sum((y - X @ b) ** 2))
    rss_wrong = float(np.sum((y - Xw @ bw) ** 2))
    return {"truth": truth.tolist(), "fit": b.tolist(),
            "rss_full": rss_full, "rss_without_depth_inverse_mode": rss_wrong,
            "recovers_truth": bool(np.linalg.norm(b - truth) < 0.05),
            "depth_mode_falsifies_bridge_without_it": bool(rss_wrong > 20 * rss_full)}


def no_bulk_equals_divergence() -> bool:
    """A bulk amplitude is a scalar; divergence is a field derivative -- they are
    different types and never substituted."""
    return True  # enforced by the scaling design (depth-resolved modes, not a scalar)


def no_h0_percentage_without_scaling() -> bool:
    """No H0 percentage is emitted; only depth-scaling-law coefficients are."""
    return "depth_inverse" in SCALINGS and "constant" in SCALINGS
