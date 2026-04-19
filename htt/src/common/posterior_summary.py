"""common.posterior_summary — Layer D posterior → direction summaries (COMMON-E).

Takes Layer C posterior samples of :math:`\\mathbf V \\in \\mathbb R^3` and
produces the direction-space artefacts that Mode 2 inference consumes
(BASS_PY_HTT_TSC_RESEARCH_PLAN §4.2 Layer D, §6.4):

* ``samples_to_lb_posterior`` — V-samples → (l, b, amplitude) samples.
* ``credible_cone``           — weighted resultant-vector cone radius.
* ``hpd_region_healpix``      — highest-posterior-density pixel set.
* ``axis_from_posterior``     — posterior median axis → production-gated
                                :class:`common.contracts.PreferredAxis`.
* ``posterior_summary_dict``  — bundled dict for ``fiducial_posterior``.

The ``axis_from_posterior`` constructor is the *only* public path in this
module that returns a ``PreferredAxis`` with ``production_allowed=True``
— every other provenance tag (raw / zoa-masked / selection-aware) must
flow through a diagnostic constructor elsewhere.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

import numpy as np

from common.contracts import PreferredAxis
from common.healpix_selection import (
    lb_to_pix,
    nside_to_npix,
    pixel_centers,
)
from common.sky_geometry import (
    lb_to_unitvec,
    unitvec_to_lb,
)

__all__ = [
    "samples_to_lb_posterior",
    "credible_cone",
    "hpd_region_healpix",
    "axis_from_posterior",
    "posterior_summary_dict",
]


# ---------------------------------------------------------------------------
# V-samples → (l, b, |V|)
# ---------------------------------------------------------------------------

def samples_to_lb_posterior(
    samples: np.ndarray,
    weights: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Convert Cartesian V-samples to direction-amplitude posterior samples.

    Parameters
    ----------
    samples
        Shape ``(n, 3)`` Cartesian posterior samples.
    weights
        Optional importance weights (logwt-exponentiated and renormalised
        before use). When omitted, equal weights are assumed.

    Returns
    -------
    dict with keys

    * ``l_deg, b_deg`` (shape ``(n_active,)``)
    * ``amplitude_kmps``
    * ``weights`` — normalised weights to use with the returned samples.

    Zero-magnitude samples are dropped (their direction is undefined).
    """
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 2 or samples.shape[1] != 3:
        raise ValueError(f"samples must be (n, 3); got {samples.shape}")
    n = samples.shape[0]
    if weights is None:
        w = np.full(n, 1.0 / n, dtype=float)
    else:
        w = np.asarray(weights, dtype=float)
        if w.shape != (n,):
            raise ValueError(f"weights shape {w.shape} incompatible with n={n}")
        if np.any(w < 0.0):
            raise ValueError("weights must be ≥ 0")
        s = float(w.sum())
        if s <= 0:
            raise ValueError("weights sum to zero")
        w = w / s
    amp = np.linalg.norm(samples, axis=1)
    active = amp > 0.0
    unit = samples[active] / amp[active, None]
    l_deg, b_deg = unitvec_to_lb(unit)
    return {
        "l_deg": np.asarray(l_deg, dtype=float),
        "b_deg": np.asarray(b_deg, dtype=float),
        "amplitude_kmps": amp[active],
        "weights": w[active] / w[active].sum() if float(w[active].sum()) > 0
                   else np.full(int(active.sum()), 1.0 / max(int(active.sum()), 1)),
    }


# ---------------------------------------------------------------------------
# Credible cone
# ---------------------------------------------------------------------------

def credible_cone(
    l_deg: np.ndarray,
    b_deg: np.ndarray,
    level: float = 0.68,
    weights: np.ndarray | None = None,
) -> dict[str, float]:
    """Smallest angular cone (centred on the weighted mean direction)
    containing a ``level`` fraction of the posterior samples.

    Returns ``{'center_l_deg', 'center_b_deg', 'radius_deg', 'level'}``.
    ``radius_deg`` is the credibility-level quantile of the great-circle
    separation between each sample and the weighted mean.
    """
    l_deg = np.asarray(l_deg, dtype=float)
    b_deg = np.asarray(b_deg, dtype=float)
    if l_deg.shape != b_deg.shape or l_deg.ndim != 1:
        raise ValueError("l_deg and b_deg must be 1-D arrays of equal length")
    if not (0.0 < level < 1.0):
        raise ValueError(f"level must be in (0, 1); got {level}")
    n = l_deg.size
    if n == 0:
        raise ValueError("credible_cone requires at least one sample")
    w = np.full(n, 1.0 / n) if weights is None else np.asarray(weights, dtype=float)
    if w.shape != (n,):
        raise ValueError("weights shape mismatch")
    w = w / float(w.sum())
    vec = lb_to_unitvec(l_deg, b_deg)
    mean_vec = (w[:, None] * vec).sum(axis=0)
    mean_norm = float(np.linalg.norm(mean_vec))
    if mean_norm < 1e-12:
        raise ValueError("degenerate posterior — mean direction is ill-defined")
    mean_vec = mean_vec / mean_norm
    cos_sep = np.clip(vec @ mean_vec, -1.0, 1.0)
    sep_deg = np.rad2deg(np.arccos(cos_sep))
    # Weighted quantile.
    order = np.argsort(sep_deg)
    cum = np.cumsum(w[order])
    idx = int(np.searchsorted(cum, level))
    idx = min(idx, n - 1)
    radius = float(sep_deg[order][idx])
    center_l, center_b = unitvec_to_lb(mean_vec)
    return {
        "center_l_deg": float(center_l),
        "center_b_deg": float(center_b),
        "radius_deg": radius,
        "level": float(level),
    }


# ---------------------------------------------------------------------------
# HEALPix HPD region
# ---------------------------------------------------------------------------

def hpd_region_healpix(
    l_deg: np.ndarray,
    b_deg: np.ndarray,
    nside: int,
    level: float = 0.68,
    weights: np.ndarray | None = None,
) -> dict[str, Any]:
    """Highest-posterior-density pixel set at the requested credibility.

    Bins samples into the equal-area RING pixelization, sorts pixels by
    posterior mass (descending), and returns the smallest set that
    collectively covers at least ``level`` of the posterior mass.

    Returns
    -------
    dict
        ``{'mask_pix': (n_pix,) bool, 'density': (n_pix,) float,
           'covered_fraction': float, 'level': float, 'n_pix_in_set': int}``.
        ``density`` sums to 1 over all pixels.
    """
    l_deg = np.asarray(l_deg, dtype=float)
    b_deg = np.asarray(b_deg, dtype=float)
    if l_deg.shape != b_deg.shape or l_deg.ndim != 1:
        raise ValueError("l_deg and b_deg must be 1-D arrays of equal length")
    if not (0.0 < level < 1.0):
        raise ValueError(f"level must be in (0, 1); got {level}")
    n = l_deg.size
    w = np.full(n, 1.0 / n) if weights is None else np.asarray(weights, dtype=float)
    if w.shape != (n,):
        raise ValueError("weights shape mismatch")
    w = w / float(w.sum())
    pix = lb_to_pix(l_deg, b_deg, nside)
    n_pix = nside_to_npix(nside)
    density = np.bincount(pix, weights=w, minlength=n_pix).astype(float)
    order = np.argsort(density)[::-1]
    cum = np.cumsum(density[order])
    # First index where cumulative mass reaches the level.
    keep_count = int(np.searchsorted(cum, level) + 1)
    keep_count = max(1, min(keep_count, n_pix))
    kept_pix = order[:keep_count]
    mask = np.zeros(n_pix, dtype=bool)
    mask[kept_pix] = True
    covered = float(density[kept_pix].sum())
    return {
        "mask_pix": mask,
        "density": density,
        "covered_fraction": covered,
        "level": float(level),
        "n_pix_in_set": keep_count,
    }


# ---------------------------------------------------------------------------
# PreferredAxis from posterior
# ---------------------------------------------------------------------------

def _provenance_hash(samples: np.ndarray, config: Mapping[str, Any]) -> str:
    """Deterministic short hash of posterior samples + config for provenance."""
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(samples).tobytes())
    for k in sorted(config):
        h.update(repr((k, config[k])).encode("utf-8"))
    return h.hexdigest()[:16]


def axis_from_posterior(
    samples: np.ndarray,
    *,
    label: str = "fiducial_posterior",
    weight_mode: str = "native",
    selection_mode: str = "mock_calibrated",
    weights: np.ndarray | None = None,
    config: Mapping[str, Any] | None = None,
) -> PreferredAxis:
    """Posterior-mean direction → ``PreferredAxis(production_allowed=True)``.

    This is the only path in :mod:`common` that is permitted to flip
    ``production_allowed=True``. Callers that hold non-posterior directions
    (raw sample mean, ZoA-masked mean, selection-aware estimate) must build
    their :class:`PreferredAxis` via a diagnostic constructor so the
    downstream a_{ℓm} restoration gate (PR13AJ) rejects them.
    """
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 2 or samples.shape[1] != 3:
        raise ValueError(f"samples must be (n, 3); got {samples.shape}")
    if samples.shape[0] == 0:
        raise ValueError("samples is empty — cannot build production axis")
    n = samples.shape[0]
    if weights is None:
        w = np.full(n, 1.0 / n, dtype=float)
    else:
        w = np.asarray(weights, dtype=float)
        if w.shape != (n,):
            raise ValueError("weights shape mismatch")
        if np.any(w < 0.0):
            raise ValueError("weights must be ≥ 0")
        s = float(w.sum())
        if s <= 0:
            raise ValueError("weights sum to zero")
        w = w / s
    mean_vec = (w[:, None] * samples).sum(axis=0)
    norm = float(np.linalg.norm(mean_vec))
    if norm < 1e-12:
        raise ValueError(
            "posterior-mean direction is degenerate (||E[V]|| ≈ 0); "
            "axis_from_posterior refuses to emit a production axis"
        )
    l_deg, b_deg = unitvec_to_lb(mean_vec / norm)
    config_map = dict(config or {})
    config_map.setdefault("weight_mode", weight_mode)
    config_map.setdefault("selection_mode", selection_mode)
    provenance = _provenance_hash(samples, config_map)
    return PreferredAxis(
        l_deg=float(l_deg),
        b_deg=float(b_deg),
        label=label,
        source="fiducial_posterior",
        weight_mode=weight_mode,
        selection_mode=selection_mode,
        production_allowed=True,
        provenance_hash=provenance,
    )


# ---------------------------------------------------------------------------
# Posterior summary bundle
# ---------------------------------------------------------------------------

def posterior_summary_dict(
    samples: np.ndarray,
    evidence: float,
    *,
    level_cone: float = 0.68,
    level_hpd: float = 0.68,
    nside_hpd: int = 32,
    weights: np.ndarray | None = None,
) -> dict[str, Any]:
    """Bundle the four standard summaries into one production dict.

    Returns a dict with keys: ``logz``, ``lb_posterior``, ``amplitude_mean``,
    ``amplitude_std``, ``credible_cone``, ``hpd_region``.
    """
    lb_post = samples_to_lb_posterior(samples, weights=weights)
    cone = credible_cone(
        lb_post["l_deg"], lb_post["b_deg"], level=level_cone,
        weights=lb_post["weights"],
    )
    hpd = hpd_region_healpix(
        lb_post["l_deg"], lb_post["b_deg"], nside=nside_hpd,
        level=level_hpd, weights=lb_post["weights"],
    )
    amp_w = lb_post["weights"]
    amp = lb_post["amplitude_kmps"]
    amp_mean = float((amp_w * amp).sum())
    amp_var = float((amp_w * (amp - amp_mean) ** 2).sum())
    return {
        "logz": float(evidence),
        "lb_posterior": lb_post,
        "amplitude_mean": amp_mean,
        "amplitude_std": float(np.sqrt(max(amp_var, 0.0))),
        "credible_cone": cone,
        "hpd_region": hpd,
    }
