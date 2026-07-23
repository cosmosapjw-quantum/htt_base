"""PR-223: species-resolved multi-fluid moment and frame atlas.

The single-beta programme is extended to a species/stream-resolved moment
hierarchy. The load-bearing fact: a zero first moment (zero net flux) does NOT
imply zero tilt energy (second-moment trace) or zero anisotropic stress
(traceless second moment). Two antipodal streams are the minimal witness; the
multi-stream moment cone is the set of admissible (trace, anisotropic-stress)
pairs at fixed zero flux.
"""

from __future__ import annotations

import numpy as np


def moments(streams: list[tuple[float, np.ndarray]]) -> dict:
    """First moment (flux), second moment K, its trace and traceless part."""
    first = sum((w * v for w, v in streams), np.zeros(3))
    K = sum((w * np.outer(v, v) for w, v in streams), np.zeros((3, 3)))
    tr = float(np.trace(K))
    Pi = K - (tr / 3.0) * np.eye(3)
    return {"first_moment": first, "K": K, "trace": tr, "aniso_stress": Pi}


def antipodal_pair(v: float = 1.0) -> dict:
    """The minimal zero-flux, nonzero-tilt-energy witness."""
    e = np.array([v, 0.0, 0.0])
    m = moments([(1.0, e), (1.0, -e)])
    return {
        "flux_norm": float(np.linalg.norm(m["first_moment"])),
        "trace": m["trace"],
        "aniso_stress_norm": float(np.linalg.norm(m["aniso_stress"])),
        "aniso_3Pi_diag": [float(3 * m["aniso_stress"][i, i]) for i in range(3)],
        "zero_flux": bool(np.linalg.norm(m["first_moment"]) < 1e-15),
        "nonzero_tilt_energy": m["trace"] > 0,
        "nonzero_anisotropic_stress": float(np.linalg.norm(m["aniso_stress"])) > 0,
    }


def isotropic_same_trace_has_no_stress(trace: float) -> bool:
    """The same-trace isotropic comparator diag(tr/3) has zero anisotropic
    stress -- so F=0 alone cannot distinguish it from the antipodal pair; the
    anisotropic stress does."""
    iso = (trace / 3.0) * np.eye(3)
    iso_stress = iso - (np.trace(iso) / 3.0) * np.eye(3)
    return bool(np.linalg.norm(iso_stress) < 1e-15)


def moment_cone_samples(n: int = 200, seed: int = 20260721) -> dict:
    """Sample zero-net-flux multi-stream configurations; every one has
    trace >= |aniso_stress|/sqrt(2/3) >= 0 and can carry stress at zero flux."""
    rng = np.random.default_rng(seed)
    min_trace = np.inf
    stress_at_zero_flux = 0
    for _ in range(n):
        # antipodal quadruple: +u,-u,+w,-w -> net flux exactly 0
        u = rng.normal(size=3) * 0.01
        w = rng.normal(size=3) * 0.01
        m = moments([(1.0, u), (1.0, -u), (0.5, w), (0.5, -w)])
        min_trace = min(min_trace, m["trace"])
        if np.linalg.norm(m["first_moment"]) < 1e-15 and np.linalg.norm(m["aniso_stress"]) > 0:
            stress_at_zero_flux += 1
    return {"n": n, "min_trace": float(min_trace),
            "fraction_stress_at_zero_flux": stress_at_zero_flux / n,
            "trace_always_nonnegative": bool(min_trace >= -1e-18)}
