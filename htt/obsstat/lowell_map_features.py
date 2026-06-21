"""Pure-numpy helpers that bridge a real sky map to OBSSTAT low-ell features.

These helpers are deliberately healpy-free so OBSSTAT carries no hard map I/O
dependency: the calling driver supplies the healpy-packed a_lm array and the
pixel unit vectors. The helpers only reshape and reduce. They are observer-side
feature plumbing, not HTT evidence, MIO output, or family identification.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np

__all__ = [
    "densify_alm",
    "power_inertia_tensor",
    "empirical_pvalue",
]


def _packed_index(lmax: int, ell: int, m: int) -> int:
    """healpy RING-packed a_lm index for m >= 0."""
    return m * (2 * lmax + 1 - m) // 2 + ell


def densify_alm(
    alm_packed: Sequence[complex] | np.ndarray, lmax: int
) -> dict[tuple[int, int], complex]:
    """Expand a healpy-packed (m>=0) a_lm array to dense full (ell, m) storage.

    The negative-m coefficients are filled by the reality condition for a real
    field, ``a_{l,-m} = (-1)^m conj(a_{l,m})``, so the result is the dense
    ``-l..+l`` mapping required by ``summarize_lowell_scalars``.
    """

    packed = np.asarray(alm_packed)
    lmax_i = int(lmax)
    dense: dict[tuple[int, int], complex] = {}
    for ell in range(lmax_i + 1):
        for m in range(0, ell + 1):
            coeff = complex(packed[_packed_index(lmax_i, ell, m)])
            dense[(ell, m)] = coeff
            if m > 0:
                dense[(ell, -m)] = ((-1) ** m) * coeff.conjugate()
    return dense


def power_inertia_tensor(
    temp_map: Sequence[float] | np.ndarray,
    pix_vectors: Sequence[Sequence[float]] | np.ndarray,
    *,
    weights: Sequence[float] | np.ndarray | None = None,
) -> np.ndarray:
    """Return the temperature-power inertia tensor ``M_ij = sum_p w_p T_p^2 n_i n_j``.

    Diagonalising ``M`` yields a diagnostic preferred axis of the supplied
    (typically low-ell-filtered) temperature map. The largest-eigenvalue
    eigenvector is the power-weighted axis. This is a descriptor only; it does
    not identify a Bianchi family or detect geometry.
    """

    temperature = np.asarray(temp_map, dtype=float)
    vectors = np.asarray(pix_vectors, dtype=float)
    if vectors.ndim != 2 or vectors.shape[1] != 3:
        raise ValueError("pix_vectors must have shape (Npix, 3)")
    if temperature.shape[0] != vectors.shape[0]:
        raise ValueError("temp_map and pix_vectors must share the pixel count")
    if weights is None:
        pixel_weights = np.ones_like(temperature)
    else:
        pixel_weights = np.asarray(weights, dtype=float)
        if pixel_weights.shape[0] != temperature.shape[0]:
            raise ValueError("weights must match the pixel count")
    power = pixel_weights * temperature * temperature
    tensor = np.einsum("p,pi,pj->ij", power, vectors, vectors)
    return 0.5 * (tensor + tensor.T)


def empirical_pvalue(
    observed: float,
    null_samples: Sequence[float] | np.ndarray,
    *,
    tail: str = "upper",
) -> float:
    """Add-one (conservative) empirical p-value of ``observed`` against nulls.

    ``tail`` is one of ``"upper"`` (P(null >= obs)), ``"lower"``
    (P(null <= obs)), or ``"two_sided_abs"`` (P(|null| >= |obs|)).
    """

    nulls = np.asarray(null_samples, dtype=float)
    if nulls.size == 0:
        raise ValueError("null_samples must be non-empty")
    obs = float(observed)
    if tail == "upper":
        count = int(np.sum(nulls >= obs))
    elif tail == "lower":
        count = int(np.sum(nulls <= obs))
    elif tail == "two_sided_abs":
        count = int(np.sum(np.abs(nulls) >= abs(obs)))
    else:
        raise ValueError("tail must be 'upper', 'lower', or 'two_sided_abs'")
    return (count + 1) / (nulls.size + 1)
