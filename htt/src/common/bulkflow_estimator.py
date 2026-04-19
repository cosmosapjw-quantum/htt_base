"""common.bulkflow_estimator — Layer B fast WLS bulk-flow estimator.

Implements the closed-form weighted-least-squares bulk-flow fit and its
diagnostic wrappers (BASS_PY_HTT_TSC_RESEARCH_PLAN §4.2 Layer B, §6.4).

Core formula
------------
Given per-source line-of-sight unit vectors :math:`\\hat n_i`, radial
velocities :math:`u_i`, and combined weights

.. math::
   w_i = \\frac{w_{\\rm native, i}\\, w_{\\rm selection, i}}{\\sigma_{i,\\rm eff}^2},

the bulk-flow estimate is

.. math::
   \\mathbf{A} = \\sum_i w_i\\, \\hat n_i \\hat n_i^\\top,\\quad
   \\mathbf{b} = \\sum_i w_i\\, u_i\\, \\hat n_i,\\quad
   \\hat{\\mathbf V} = \\mathbf{A}^{-1} \\mathbf{b},

with weighted covariance :math:`{\\rm cov}(\\hat{\\mathbf V}) = \\mathbf{A}^{-1}`
(valid when the per-source weights already include :math:`1/\\sigma_{i,\\rm eff}^2`).

The module always exposes the three-factor weight decomposition
(``{w_native, w_selection, w_measurement}``) in its diagnostics — the
REG-01 ``test_weights_decomposition_logged`` item guards that this is
not quietly silently collapsed in downstream consumers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

__all__ = [
    "BulkFlowCatalogue",
    "BulkFlowFit",
    "ZoAResponseResult",
    "wls_bulk_flow",
    "bulk_flow_mask_ladder",
    "bootstrap_covariance",
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BulkFlowCatalogue:
    """Input catalogue for the WLS estimator.

    ``w_native`` is the per-source prior weight shipped with the catalogue
    (often ``1`` when absent). ``w_selection`` is the Layer-A output of
    :func:`common.healpix_selection.compute_selection_weights`.
    ``sigma`` is the per-source velocity uncertainty (km/s) fed into
    :math:`w_{\\rm measurement, i} = 1/(\\sigma_i^2 + \\sigma_\\ast^2)`.
    """

    n_hat: np.ndarray          # shape (N, 3), unit vectors
    u: np.ndarray              # shape (N,), radial velocities
    sigma: np.ndarray          # shape (N,), per-source uncertainty (km/s)
    w_native: np.ndarray       # shape (N,)
    w_selection: np.ndarray    # shape (N,)
    label: str = "catalogue"

    def __post_init__(self) -> None:
        N = self.u.shape[0]
        if self.n_hat.shape != (N, 3):
            raise ValueError(
                f"n_hat shape {self.n_hat.shape} incompatible with u shape {self.u.shape}"
            )
        for name in ("sigma", "w_native", "w_selection"):
            arr = getattr(self, name)
            if arr.shape != (N,):
                raise ValueError(
                    f"{name} shape {arr.shape} incompatible with N={N}"
                )
        norms = np.linalg.norm(self.n_hat, axis=1)
        if not np.allclose(norms, 1.0, atol=1e-6):
            raise ValueError("n_hat rows must be unit vectors (|n| = 1)")
        if np.any(self.sigma <= 0.0):
            raise ValueError("sigma entries must all be > 0")
        if np.any(self.w_native < 0.0) or np.any(self.w_selection < 0.0):
            raise ValueError("w_native / w_selection must be ≥ 0")

    @property
    def n_sources(self) -> int:
        return int(self.u.shape[0])


@dataclass(frozen=True)
class BulkFlowFit:
    """Result of a single WLS call."""

    V_hat: np.ndarray           # shape (3,)
    cov: np.ndarray             # shape (3, 3)
    n_sources: int
    weight_decomposition: Mapping[str, np.ndarray]
    """Three-factor breakdown: keys ``w_native``, ``w_selection``, ``w_measurement``.
    REG-01 ``test_weights_decomposition_logged`` asserts presence of all three."""
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    @property
    def V_magnitude(self) -> float:
        return float(np.linalg.norm(self.V_hat))


@dataclass(frozen=True)
class ZoAResponseResult:
    """Output of :func:`bulk_flow_mask_ladder` — one fit per bcut step."""

    bcut_deg: np.ndarray              # shape (M,)
    retention_fraction: np.ndarray    # shape (M,)
    V_hat: np.ndarray                 # shape (M, 3)
    V_magnitude: np.ndarray           # shape (M,)
    fits: tuple[BulkFlowFit, ...]

    def __post_init__(self) -> None:
        M = self.bcut_deg.shape[0]
        if self.retention_fraction.shape != (M,):
            raise ValueError("retention_fraction shape mismatch")
        if self.V_hat.shape != (M, 3):
            raise ValueError("V_hat shape mismatch")
        if self.V_magnitude.shape != (M,):
            raise ValueError("V_magnitude shape mismatch")
        if len(self.fits) != M:
            raise ValueError("fits length mismatch")


# ---------------------------------------------------------------------------
# Core WLS
# ---------------------------------------------------------------------------

def _measurement_weights(sigma: np.ndarray, sigma_star: float) -> np.ndarray:
    if sigma_star < 0.0:
        raise ValueError(f"sigma_star must be ≥ 0; got {sigma_star}")
    return 1.0 / (np.asarray(sigma, dtype=float) ** 2 + float(sigma_star) ** 2)


def wls_bulk_flow(
    n_hat: np.ndarray,
    u: np.ndarray,
    w: np.ndarray | None = None,
    *,
    sigma: np.ndarray | None = None,
    w_native: np.ndarray | None = None,
    w_selection: np.ndarray | None = None,
    sigma_star: float = 0.0,
) -> BulkFlowFit:
    """Closed-form WLS bulk-flow fit.

    Parameters
    ----------
    n_hat
        Per-source unit vectors, shape ``(N, 3)``.
    u
        Per-source radial velocities, shape ``(N,)``.
    w
        Optional pre-combined weights. When supplied, the three-factor
        decomposition is reconstructed only if all of ``sigma``, ``w_native``,
        ``w_selection`` are also given — otherwise the decomposition records
        ``w_native = ones``, ``w_selection = ones``, ``w_measurement = w``
        so that downstream consumers can still inspect *something* for every
        factor (REG-01).
    sigma, w_native, w_selection
        Three-factor decomposition inputs. When ``w`` is omitted these are
        required and combined as ``w_i = w_native_i * w_selection_i *
        w_measurement_i`` with ``w_measurement_i = 1/(σ_i² + σ*²)``.
    sigma_star
        Additional intrinsic-scatter term added in quadrature to ``sigma``.

    Returns
    -------
    BulkFlowFit
        Carries ``V_hat``, ``cov = A⁻¹``, and the weight decomposition.
    """
    n_hat = np.asarray(n_hat, dtype=float)
    u = np.asarray(u, dtype=float)
    if n_hat.ndim != 2 or n_hat.shape[1] != 3:
        raise ValueError(f"n_hat must be (N, 3); got {n_hat.shape}")
    N = n_hat.shape[0]
    if u.shape != (N,):
        raise ValueError(f"u shape {u.shape} incompatible with N={N}")

    if w is None:
        if sigma is None or w_native is None or w_selection is None:
            raise ValueError(
                "wls_bulk_flow requires either `w` or the full "
                "(sigma, w_native, w_selection) decomposition"
            )
        w_native = np.asarray(w_native, dtype=float)
        w_selection = np.asarray(w_selection, dtype=float)
        w_meas = _measurement_weights(sigma, sigma_star)
        w_combined = w_native * w_selection * w_meas
    else:
        w_combined = np.asarray(w, dtype=float)
        w_native_arr = (
            np.asarray(w_native, dtype=float) if w_native is not None
            else np.ones(N, dtype=float)
        )
        w_selection_arr = (
            np.asarray(w_selection, dtype=float) if w_selection is not None
            else np.ones(N, dtype=float)
        )
        if sigma is not None:
            w_meas = _measurement_weights(sigma, sigma_star)
        else:
            w_meas = w_combined / np.where(
                (w_native_arr * w_selection_arr) > 0.0,
                w_native_arr * w_selection_arr,
                1.0,
            )
        w_native, w_selection = w_native_arr, w_selection_arr

    if w_combined.shape != (N,):
        raise ValueError(f"combined weight shape {w_combined.shape} != (N={N},)")
    if np.any(w_combined < 0.0):
        raise ValueError("combined weights must be ≥ 0")
    if float(w_combined.sum()) <= 0.0:
        raise ValueError("combined weights sum to zero — cannot fit bulk flow")

    A = (w_combined[:, None, None] * n_hat[:, :, None] * n_hat[:, None, :]).sum(axis=0)
    b = (w_combined[:, None] * u[:, None] * n_hat).sum(axis=0)
    try:
        V_hat = np.linalg.solve(A, b)
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            "WLS normal-equation matrix is singular — check sky coverage "
            "and per-source weights"
        ) from exc
    cov = np.linalg.inv(A)

    decomposition = {
        "w_native": np.asarray(w_native, dtype=float).copy(),
        "w_selection": np.asarray(w_selection, dtype=float).copy(),
        "w_measurement": np.asarray(w_meas, dtype=float).copy(),
    }
    return BulkFlowFit(
        V_hat=V_hat,
        cov=cov,
        n_sources=N,
        weight_decomposition=decomposition,
        diagnostics={
            "condition_number": float(np.linalg.cond(A)),
            "effective_weight_sum": float(w_combined.sum()),
            "sigma_star": float(sigma_star),
        },
    )


# ---------------------------------------------------------------------------
# Mask ladder (Mode 0)
# ---------------------------------------------------------------------------

def bulk_flow_mask_ladder(
    catalogue: BulkFlowCatalogue,
    bcut_list: np.ndarray,
    *,
    nside: int = 16,
    sigma_star: float = 0.0,
) -> ZoAResponseResult:
    """Scan the ZoA half-angle ladder and return per-cut WLS fits (Mode 0).

    For each ``bcut`` in ``bcut_list`` we rebuild the ZoA pixel mask, keep
    only the sources whose pixel is retained, and fit the bulk flow on that
    subset. The returned :class:`ZoAResponseResult` exposes the ladder in
    arrays so callers can plot ``fig_zoa_ladder_mode0`` directly.
    """
    from common.healpix_selection import build_zoa_mask, lb_to_pix

    # Convert catalogue's n_hat back to (l, b) so we can query the ZoA pixel mask.
    nx, ny, nz = catalogue.n_hat[:, 0], catalogue.n_hat[:, 1], catalogue.n_hat[:, 2]
    b_deg = np.rad2deg(np.arcsin(np.clip(nz, -1.0, 1.0)))
    l_deg = np.mod(np.rad2deg(np.arctan2(ny, nx)), 360.0)

    bcut_arr = np.asarray(bcut_list, dtype=float)
    if bcut_arr.ndim != 1:
        raise ValueError("bcut_list must be 1-D")

    fits: list[BulkFlowFit] = []
    retention = np.empty_like(bcut_arr)
    V_hat_ladder = np.empty((bcut_arr.size, 3), dtype=float)
    V_mag_ladder = np.empty_like(bcut_arr)

    for k, bcut in enumerate(bcut_arr):
        mask = build_zoa_mask(l_deg, b_deg, bcut_deg=float(bcut), nside=nside)
        pix = lb_to_pix(l_deg, b_deg, nside)
        keep = mask[pix]
        retention[k] = float(keep.mean()) if keep.size else 0.0
        if int(keep.sum()) < 4:
            # Singular geometry — record NaN rather than raise so that
            # ladder plots can still visualise the cutoff transition.
            fits.append(
                BulkFlowFit(
                    V_hat=np.full(3, np.nan),
                    cov=np.full((3, 3), np.nan),
                    n_sources=int(keep.sum()),
                    weight_decomposition={
                        "w_native": catalogue.w_native[keep].copy(),
                        "w_selection": catalogue.w_selection[keep].copy(),
                        "w_measurement": _measurement_weights(
                            catalogue.sigma[keep], sigma_star
                        ),
                    },
                    diagnostics={"underdetermined": True, "bcut_deg": float(bcut)},
                )
            )
            V_hat_ladder[k] = np.nan
            V_mag_ladder[k] = np.nan
            continue
        fit = wls_bulk_flow(
            catalogue.n_hat[keep],
            catalogue.u[keep],
            sigma=catalogue.sigma[keep],
            w_native=catalogue.w_native[keep],
            w_selection=catalogue.w_selection[keep],
            sigma_star=sigma_star,
        )
        fits.append(fit)
        V_hat_ladder[k] = fit.V_hat
        V_mag_ladder[k] = fit.V_magnitude

    return ZoAResponseResult(
        bcut_deg=bcut_arr,
        retention_fraction=retention,
        V_hat=V_hat_ladder,
        V_magnitude=V_mag_ladder,
        fits=tuple(fits),
    )


# ---------------------------------------------------------------------------
# Bootstrap covariance
# ---------------------------------------------------------------------------

def bootstrap_covariance(
    catalogue: BulkFlowCatalogue,
    n_boot: int = 500,
    *,
    sigma_star: float = 0.0,
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    """Resampling covariance for the Mode-1 WLS estimator.

    Returns a dict with keys ``cov`` (3×3), ``V_boot`` ((n_boot, 3)),
    ``V_hat_mean`` ((3,)), and ``n_boot``. Falling-over fits (sparse mask)
    are skipped so the reported ``n_boot`` counts only successful resamples.
    """
    if rng is None:
        rng = np.random.default_rng()
    N = catalogue.n_sources
    V_boot = np.empty((n_boot, 3), dtype=float)
    succeeded = 0
    for k in range(n_boot):
        idx = rng.integers(0, N, size=N)
        try:
            fit = wls_bulk_flow(
                catalogue.n_hat[idx],
                catalogue.u[idx],
                sigma=catalogue.sigma[idx],
                w_native=catalogue.w_native[idx],
                w_selection=catalogue.w_selection[idx],
                sigma_star=sigma_star,
            )
        except (ValueError, np.linalg.LinAlgError):
            continue
        V_boot[succeeded] = fit.V_hat
        succeeded += 1
    if succeeded < 3:
        raise RuntimeError(
            f"bootstrap_covariance: only {succeeded} resamples succeeded — "
            "catalogue is too small or too singular for reliable covariance"
        )
    V_boot = V_boot[:succeeded]
    V_mean = V_boot.mean(axis=0)
    cov = np.cov(V_boot, rowvar=False, ddof=1)
    return {
        "cov": cov,
        "V_boot": V_boot,
        "V_hat_mean": V_mean,
        "n_boot": succeeded,
    }
