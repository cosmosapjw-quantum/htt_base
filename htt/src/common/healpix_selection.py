"""common.healpix_selection — Layer A sphere pixelization & selection weights.

This module implements the pixelization utilities invoked by the bulk-flow
pipeline (BASS_PY_HTT_TSC_RESEARCH_PLAN §4.2 Layer A, §6.4). It provides:

* ``build_zoa_mask`` — per-pixel hard cut on galactic latitude.
* ``build_occupancy_map`` — source count per pixel.
* ``build_angular_completeness`` — smoothed, area-normalised completeness map.
* ``compute_selection_weights`` — per-source inverse-completeness weights.
* ``posterior_density_map`` — sampler-output density for ``fig_direction_posterior``.
* ``plot_healpix_mask`` — matplotlib helper (lazy import).

Pixelization
------------
The project does not yet depend on ``healpy``. To keep the interface HEALPix-
compatible while staying pure-numpy, this module uses an **equal-area
iso-latitude-ring** pixelization whose pixel indices mirror HEALPix RING
ordering (ring 0 = south pole, growing north; ``ipix = i_ring * n_lon + i_lon``).

Per-ring layout for a given ``nside`` (restricted to positive powers of two
via :class:`common.contracts.SkySelectionConfig`):

* ``n_rings = nside``            — rings of constant latitude
* ``n_lon = 2 * nside``          — pixels per ring
* ``n_pix = 2 * nside ** 2``     — total pixels
* Ring *i* covers ``sin b ∈ [-1 + 2i/n_rings, -1 + 2(i+1)/n_rings]``,
  giving every pixel solid angle ``ΔΩ = 4π / n_pix``.

When ``healpy`` is eventually adopted (see ``BASS_PY_HTT_TSC_RESEARCH_PLAN``
§7.5), the interface of this module is drop-in replaceable; only the
index layout changes.
"""
from __future__ import annotations

from typing import Any

import numpy as np

__all__ = [
    "nside_to_npix",
    "pixel_centers",
    "pixel_solid_angle",
    "lb_to_pix",
    "build_zoa_mask",
    "build_occupancy_map",
    "build_angular_completeness",
    "compute_selection_weights",
    "posterior_density_map",
    "plot_healpix_mask",
]


# ---------------------------------------------------------------------------
# Core pixelization
# ---------------------------------------------------------------------------

def _validate_nside(nside: int) -> int:
    nside = int(nside)
    if nside <= 0 or (nside & (nside - 1)) != 0:
        raise ValueError(
            f"nside must be a positive power of two; got {nside}"
        )
    return nside


def nside_to_npix(nside: int) -> int:
    """Number of pixels in the equal-area ring pixelization."""
    nside = _validate_nside(nside)
    return 2 * nside * nside


def _grid_shape(nside: int) -> tuple[int, int]:
    return int(nside), int(2 * nside)


def pixel_centers(nside: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(l_centers_deg, b_centers_deg)`` for every pixel in RING order.

    Shapes: both ``(n_pix,)``.
    """
    n_rings, n_lon = _grid_shape(nside)
    i_ring = np.arange(n_rings, dtype=float)
    sin_b = -1.0 + 2.0 * (i_ring + 0.5) / n_rings
    b_ring = np.rad2deg(np.arcsin(np.clip(sin_b, -1.0, 1.0)))
    j_lon = np.arange(n_lon, dtype=float)
    l_lon = (j_lon + 0.5) * (360.0 / n_lon)
    b_grid = np.broadcast_to(b_ring[:, None], (n_rings, n_lon)).ravel()
    l_grid = np.broadcast_to(l_lon[None, :], (n_rings, n_lon)).ravel()
    return l_grid.astype(float), b_grid.astype(float)


def pixel_solid_angle(nside: int) -> float:
    """Per-pixel solid angle in steradians (equal-area)."""
    return 4.0 * np.pi / nside_to_npix(nside)


def lb_to_pix(l_deg: np.ndarray, b_deg: np.ndarray, nside: int) -> np.ndarray:
    """Map (l, b) in degrees to RING pixel indices, shape ``(N,)``."""
    n_rings, n_lon = _grid_shape(nside)
    l = np.mod(np.asarray(l_deg, dtype=float), 360.0)
    b = np.clip(np.asarray(b_deg, dtype=float), -90.0, 90.0)
    sin_b = np.sin(np.deg2rad(b))
    # Ring index: int((sin_b + 1) * n_rings / 2), clipped so pole is in ring 0 / last
    i_ring = np.clip(
        np.floor((sin_b + 1.0) * 0.5 * n_rings).astype(int), 0, n_rings - 1
    )
    j_lon = np.mod(
        np.floor(l * n_lon / 360.0).astype(int), n_lon
    )
    return i_ring * n_lon + j_lon


# ---------------------------------------------------------------------------
# Layer A maps
# ---------------------------------------------------------------------------

def _check_lb_shapes(l_deg: np.ndarray, b_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    l = np.asarray(l_deg, dtype=float)
    b = np.asarray(b_deg, dtype=float)
    if l.shape != b.shape:
        raise ValueError(f"l_deg shape {l.shape} != b_deg shape {b.shape}")
    if l.ndim != 1:
        raise ValueError(f"l_deg/b_deg must be 1-D; got ndim={l.ndim}")
    return l, b


def build_zoa_mask(
    l_deg: np.ndarray | None,
    b_deg: np.ndarray | None,
    bcut_deg: float,
    nside: int,
) -> np.ndarray:
    """Per-pixel boolean mask ``True`` where ``|b_center| >= bcut_deg``.

    Parameters
    ----------
    l_deg, b_deg
        Source catalogue coordinates. Retained for interface symmetry with
        :func:`build_occupancy_map` / :func:`build_angular_completeness` and
        validated only for shape consistency; the mask itself depends only
        on ``bcut_deg`` and ``nside``. Either or both may be ``None`` when
        the caller only needs the pixel mask.
    bcut_deg
        Zone-of-avoidance half-angle in degrees.
    nside
        Pixelization parameter (positive power of two).

    Returns
    -------
    np.ndarray
        Boolean array of shape ``(n_pix,)``, True where the pixel is *kept*.
    """
    if l_deg is not None and b_deg is not None:
        _check_lb_shapes(l_deg, b_deg)
    if not np.isfinite(bcut_deg) or bcut_deg < 0.0 or bcut_deg > 90.0:
        raise ValueError(
            f"bcut_deg must be finite and in [0, 90]; got {bcut_deg}"
        )
    _, b_centers = pixel_centers(nside)
    return np.abs(b_centers) >= float(bcut_deg)


def build_occupancy_map(
    l_deg: np.ndarray, b_deg: np.ndarray, nside: int
) -> np.ndarray:
    """Integer count of catalogue sources per pixel, shape ``(n_pix,)``."""
    l, b = _check_lb_shapes(l_deg, b_deg)
    pix = lb_to_pix(l, b, nside)
    return np.bincount(pix, minlength=nside_to_npix(nside)).astype(np.int64)


def build_angular_completeness(
    l_deg: np.ndarray,
    b_deg: np.ndarray,
    nside: int,
    smooth_sigma_pix: float = 1.0,
) -> np.ndarray:
    """Smoothed, area-normalised angular-completeness map.

    The raw occupancy ``N_pix`` is convolved with a Gaussian of width
    ``smooth_sigma_pix`` pixels (longitudinally periodic, latitudinally
    reflected) and then normalised so that ``max(C_pix) = 1``. Empty sky
    corresponds to ``C_pix = 0``.
    """
    from scipy.ndimage import gaussian_filter

    n_rings, n_lon = _grid_shape(nside)
    occ = build_occupancy_map(l_deg, b_deg, nside).astype(float)
    grid = occ.reshape(n_rings, n_lon)
    if smooth_sigma_pix > 0.0:
        grid = gaussian_filter(
            grid,
            sigma=float(smooth_sigma_pix),
            mode=("reflect", "wrap"),
        )
    peak = float(grid.max())
    if peak > 0.0:
        grid = grid / peak
    return grid.ravel()


def compute_selection_weights(
    l_deg: np.ndarray,
    b_deg: np.ndarray,
    mask_pix: np.ndarray,
    C_pix: np.ndarray,
    eps: float = 1e-6,
) -> np.ndarray:
    """Per-source inverse-completeness selection weights.

    ``w_i = mask_pix[pix_i] / (C_pix[pix_i] + eps)`` for sources inside the
    mask; sources whose pixel is masked out receive weight 0. The result is
    **unnormalised**: pass through :func:`common.sky_geometry.normalize_weights`
    with the production-mode gate before consumption.
    """
    l, b = _check_lb_shapes(l_deg, b_deg)
    mask_pix = np.asarray(mask_pix, dtype=bool)
    C_pix = np.asarray(C_pix, dtype=float)
    n_pix = mask_pix.size
    if C_pix.shape != (n_pix,):
        raise ValueError(
            f"C_pix shape {C_pix.shape} incompatible with mask_pix shape "
            f"{mask_pix.shape}"
        )
    if eps <= 0.0:
        raise ValueError(f"eps must be > 0; got {eps}")
    # nside must satisfy n_pix = 2 * nside^2 in this scheme.
    nside = int(np.sqrt(n_pix // 2))
    if nside_to_npix(nside) != n_pix:
        raise ValueError(
            f"mask_pix length {n_pix} is not a valid (2 * nside**2) count"
        )
    pix = lb_to_pix(l, b, nside)
    inside = mask_pix[pix]
    w = np.where(inside, 1.0 / (C_pix[pix] + eps), 0.0)
    return w


def posterior_density_map(
    l_samples: np.ndarray, b_samples: np.ndarray, nside: int
) -> np.ndarray:
    """Normalised posterior density per pixel (for ``fig_direction_posterior``).

    Returns an array of shape ``(n_pix,)`` summing to 1. If no samples fall
    into any pixel (empty input), returns a uniform distribution instead of
    dividing by zero.
    """
    if l_samples is None or b_samples is None:
        raise ValueError("posterior_density_map requires l_samples and b_samples")
    l, b = _check_lb_shapes(l_samples, b_samples)
    if l.size == 0:
        n_pix = nside_to_npix(nside)
        return np.full(n_pix, 1.0 / n_pix, dtype=float)
    pix = lb_to_pix(l, b, nside)
    counts = np.bincount(pix, minlength=nside_to_npix(nside)).astype(float)
    total = counts.sum()
    if total <= 0.0:
        n_pix = counts.size
        return np.full(n_pix, 1.0 / n_pix, dtype=float)
    return counts / total


# ---------------------------------------------------------------------------
# Visualisation (lazy matplotlib import)
# ---------------------------------------------------------------------------

def plot_healpix_mask(
    mask: np.ndarray,
    title: str = "healpix mask",
    **imshow_kwargs: Any,
):
    """Plot a per-pixel scalar map as a Mollweide-free (l, b) grid.

    Returns the ``matplotlib.figure.Figure`` so callers can save or embed it.
    Kept intentionally minimal — full Mollweide projection is the job of the
    downstream figure scripts (``bass_py/htt/figures``).
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover — depends on optional dep.
        raise RuntimeError(
            "plot_healpix_mask requires matplotlib; install the project's "
            "'viz' extras or add matplotlib to the environment."
        ) from exc

    arr = np.asarray(mask)
    n_pix = arr.size
    nside = int(np.sqrt(n_pix // 2))
    if nside_to_npix(nside) != n_pix:
        raise ValueError(
            f"mask length {n_pix} is not a valid (2 * nside**2) count"
        )
    n_rings, n_lon = _grid_shape(nside)
    grid = arr.reshape(n_rings, n_lon)
    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    im = ax.imshow(
        grid,
        origin="lower",
        aspect="auto",
        extent=(0.0, 360.0, -90.0, 90.0),
        **imshow_kwargs,
    )
    ax.set_xlabel("l [deg]")
    ax.set_ylabel("b [deg]")
    ax.set_title(title)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    return fig
