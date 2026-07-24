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
    """Keep the current depth-inverse and constant proxy responses distinct.

    This is a structural anti-aliasing check, not physical identification of a
    velocity-gradient component.
    """
    depths = np.array([30.0, 60.0, 120.0, 240.0])
    try:
        depth_inverse = np.asarray(SCALINGS["depth_inverse"](depths), dtype=float)
        constant = np.asarray(SCALINGS["constant"](depths), dtype=float)
    except (KeyError, TypeError, ValueError):
        return False
    if (
        depth_inverse.shape != depths.shape
        or constant.shape != depths.shape
        or not np.all(np.isfinite(depth_inverse))
        or not np.all(np.isfinite(constant))
    ):
        return False
    design = np.column_stack([depth_inverse, constant])
    return bool(np.linalg.matrix_rank(design) == 2)


def no_h0_percentage_without_scaling(result: dict | None = None) -> bool:
    """Require any emitted H0 percentage to name a registered depth scaling."""
    result = falsify() if result is None else result
    percentage_keys = [
        str(key).lower()
        for key in result
        if "h0" in str(key).lower() and "percent" in str(key).lower()
    ]
    if not percentage_keys:
        return True
    scaling = result.get("depth_scaling_law")
    return isinstance(scaling, str) and scaling in SCALINGS
