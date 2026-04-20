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
import hashlib
import json
import platform
from typing import Any, Mapping

import numpy as np

__all__ = [
    "BulkFlowCatalogue",
    "BulkFlowFit",
    "ZoAResponseResult",
    "wls_bulk_flow",
    "bulk_flow_mask_ladder",
    "bootstrap_covariance",
    "diagnostic_zoa_ladder_artifact",
    "diagnostic_plane_alignment_artifact",
    "baseline_selection_aware_artifact",
    "retention_vs_posterior_artifact",
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
# Artifact helpers
# ---------------------------------------------------------------------------

def _jsonify(obj: Any) -> Any:
    """Recursively convert numpy-heavy structures to JSON-native values."""
    if isinstance(obj, float):
        return obj if np.isfinite(obj) else None
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        item = obj.item()
        return item if not isinstance(item, float) or np.isfinite(item) else None
    if isinstance(obj, Mapping):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    return obj


def _config_hash(payload: Mapping[str, Any]) -> str:
    """Stable SHA256 hash for artifact configuration payloads."""
    blob = json.dumps(_jsonify(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _catalog_lb(catalogue: BulkFlowCatalogue) -> tuple[np.ndarray, np.ndarray]:
    """Convert a catalogue's line-of-sight unit vectors back to (l, b)."""
    from common.sky_geometry import unitvec_to_lb

    return unitvec_to_lb(catalogue.n_hat)


def _axis_from_vector(V_hat: np.ndarray) -> dict[str, float | bool]:
    """Convert a 3-vector into an axis record with validity flags."""
    from common.sky_geometry import unitvec_to_lb

    V_hat = np.asarray(V_hat, dtype=float)
    if V_hat.shape != (3,):
        raise ValueError(f"V_hat must be (3,); got {V_hat.shape}")
    amp = float(np.linalg.norm(V_hat))
    if not np.isfinite(amp) or amp <= 0.0:
        return {
            "l_deg": float("nan"),
            "b_deg": float("nan"),
            "amplitude_kmps": amp,
            "valid": False,
        }
    l_deg, b_deg = unitvec_to_lb(V_hat / amp)
    return {
        "l_deg": float(l_deg),
        "b_deg": float(b_deg),
        "amplitude_kmps": amp,
        "valid": True,
    }


def _angular_sep_deg(
    l1_deg: float,
    b1_deg: float,
    l2_deg: float,
    b2_deg: float,
) -> float:
    """Great-circle separation between two directions in degrees."""
    from common.sky_geometry import lb_to_unitvec

    u1 = lb_to_unitvec(np.array([l1_deg]), np.array([b1_deg]))[0]
    u2 = lb_to_unitvec(np.array([l2_deg]), np.array([b2_deg]))[0]
    cos_sep = float(np.clip(u1 @ u2, -1.0, 1.0))
    return float(np.degrees(np.arccos(cos_sep)))


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


# ---------------------------------------------------------------------------
# JSON artifacts (Mode 0 / Mode 1)
# ---------------------------------------------------------------------------

def diagnostic_zoa_ladder_artifact(
    catalogue: BulkFlowCatalogue,
    *,
    bcut_list: np.ndarray | None = None,
    nside: int = 16,
    sigma_star: float = 0.0,
    stability_threshold_deg: float = 20.0,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the Mode 0 ``diag_zoa_ladder_vX.json`` artifact.

    The stability threshold is operational and intentionally configurable:
    the research plan requires a boolean ``zoa_ladder_stable`` gate but does
    not prescribe a unique angle.
    """
    if bcut_list is None:
        bcut_list = np.array([0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0])
    ladder = bulk_flow_mask_ladder(
        catalogue,
        np.asarray(bcut_list, dtype=float),
        nside=nside,
        sigma_star=sigma_star,
    )
    axis_l = np.full(ladder.bcut_deg.shape, np.nan, dtype=float)
    axis_b = np.full(ladder.bcut_deg.shape, np.nan, dtype=float)
    axis_instability = np.full(ladder.bcut_deg.shape, np.nan, dtype=float)
    valid = np.isfinite(ladder.V_magnitude) & (ladder.V_magnitude > 0.0)
    if np.any(valid):
        ref_idx = int(np.flatnonzero(valid)[0])
        ref = _axis_from_vector(ladder.V_hat[ref_idx])
        for idx in np.flatnonzero(valid):
            axis = _axis_from_vector(ladder.V_hat[idx])
            axis_l[idx] = float(axis["l_deg"])
            axis_b[idx] = float(axis["b_deg"])
            axis_instability[idx] = _angular_sep_deg(
                float(ref["l_deg"]),
                float(ref["b_deg"]),
                float(axis["l_deg"]),
                float(axis["b_deg"]),
            )
        max_instability = float(np.nanmax(axis_instability))
        zoa_ladder_stable = bool(max_instability <= stability_threshold_deg)
    else:
        ref_idx = None
        max_instability = float("nan")
        zoa_ladder_stable = False

    extra = dict(metadata or {})
    config_payload = {
        "bcut_list": np.asarray(bcut_list, dtype=float),
        "nside": nside,
        "sigma_star": sigma_star,
        "stability_threshold_deg": stability_threshold_deg,
        "metadata": extra,
    }
    return _jsonify({
        "artifact_name": "diag_zoa_ladder_v1.json",
        "generated_by": extra.get(
            "generated_by",
            "common.bulkflow_estimator.diagnostic_zoa_ladder_artifact",
        ),
        "git_commit": extra.get("git_commit", ""),
        "config_hash": _config_hash(config_payload),
        "input_data_hashes": list(extra.get("input_data_hashes", [])),
        "random_seed": extra.get("random_seed"),
        "wall_time_sec": extra.get("wall_time_sec"),
        "python_version": extra.get("python_version", platform.python_version()),
        "numpy_version": extra.get("numpy_version", np.__version__),
        "claim_tier": extra.get("claim_tier", "EXPLORATORY"),
        "scope_label": extra.get("scope_label", "diagnostic"),
        "production_allowed": False,
        "bcut_deg": ladder.bcut_deg.tolist(),
        "retention_fraction": ladder.retention_fraction.tolist(),
        "V_hat_kmps": ladder.V_hat.tolist(),
        "V_magnitude_kmps": ladder.V_magnitude.tolist(),
        "axis_l_deg": axis_l.tolist(),
        "axis_b_deg": axis_b.tolist(),
        "axis_instability_deg": axis_instability.tolist(),
        "reference_bcut_deg": (
            None if ref_idx is None else float(ladder.bcut_deg[ref_idx])
        ),
        "stability_threshold_deg": float(stability_threshold_deg),
        "max_axis_instability_deg": max_instability,
        "zoa_ladder_stable": zoa_ladder_stable,
        "n_source_total": int(catalogue.n_sources),
        "n_valid_fits": int(np.count_nonzero(valid)),
    })


def diagnostic_plane_alignment_artifact(
    diagnostic_artifact: Mapping[str, Any],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``diag_plane_alignment_v1.json`` from the Mode 0 ladder artifact.

    The plan requests the ladder's ``(l, b)`` path plus a compact alignment
    diagnostic. We operationalise that as the retention-weighted spherical
    mean of the valid ladder axes and its resultant length ``R``.
    """
    from common.sky_geometry import spherical_mean

    bcut = np.asarray(diagnostic_artifact.get("bcut_deg"), dtype=float)
    retention = np.asarray(
        diagnostic_artifact.get("retention_fraction"),
        dtype=float,
    )
    axis_l = np.asarray(diagnostic_artifact.get("axis_l_deg"), dtype=float)
    axis_b = np.asarray(diagnostic_artifact.get("axis_b_deg"), dtype=float)
    if (
        bcut.ndim != 1
        or retention.shape != bcut.shape
        or axis_l.shape != bcut.shape
        or axis_b.shape != bcut.shape
    ):
        raise ValueError(
            "diagnostic_plane_alignment_artifact requires a diag_zoa_ladder "
            "payload with aligned bcut/retention/axis arrays"
        )

    valid = np.isfinite(axis_l) & np.isfinite(axis_b)
    if not np.any(valid):
        raise ValueError(
            "diagnostic_plane_alignment_artifact: diagnostic ladder "
            "contains no valid axis samples"
        )

    weights = retention[valid]
    if float(np.sum(weights)) <= 0.0:
        weights = np.ones(int(np.count_nonzero(valid)), dtype=float)
    mean_axis = spherical_mean(axis_l[valid], axis_b[valid], weights)

    step_drift = np.full(bcut.shape, np.nan, dtype=float)
    last_valid_idx: int | None = None
    for idx in np.flatnonzero(valid):
        if last_valid_idx is not None:
            step_drift[idx] = _angular_sep_deg(
                float(axis_l[last_valid_idx]),
                float(axis_b[last_valid_idx]),
                float(axis_l[idx]),
                float(axis_b[idx]),
            )
        last_valid_idx = int(idx)

    extra = dict(metadata or {})
    config_payload = {
        "diagnostic_artifact_name": diagnostic_artifact.get("artifact_name", ""),
        "diagnostic_config_hash": diagnostic_artifact.get("config_hash", ""),
        "metadata": extra,
    }
    finite_step = step_drift[np.isfinite(step_drift)]
    return _jsonify({
        "artifact_name": "diag_plane_alignment_v1.json",
        "generated_by": extra.get(
            "generated_by",
            "common.bulkflow_estimator.diagnostic_plane_alignment_artifact",
        ),
        "git_commit": extra.get("git_commit", ""),
        "config_hash": _config_hash(config_payload),
        "input_data_hashes": list(extra.get("input_data_hashes", [])),
        "random_seed": extra.get("random_seed"),
        "wall_time_sec": extra.get("wall_time_sec"),
        "python_version": extra.get("python_version", platform.python_version()),
        "numpy_version": extra.get("numpy_version", np.__version__),
        "claim_tier": extra.get("claim_tier", "EXPLORATORY"),
        "scope_label": extra.get("scope_label", "diagnostic"),
        "production_allowed": False,
        "source_artifact": {
            "artifact_name": diagnostic_artifact.get("artifact_name", ""),
            "config_hash": diagnostic_artifact.get("config_hash", ""),
        },
        "bcut_deg": bcut.tolist(),
        "retention_fraction": retention.tolist(),
        "axis_l_deg": axis_l.tolist(),
        "axis_b_deg": axis_b.tolist(),
        "valid_axis": valid.tolist(),
        "step_drift_deg": step_drift.tolist(),
        "mean_axis": {
            "l_deg": float(mean_axis["l_deg"]),
            "b_deg": float(mean_axis["b_deg"]),
            "resultant_R": float(mean_axis["resultant_R"]),
        },
        "resultant_R": float(mean_axis["resultant_R"]),
        "n_valid_axes": int(np.count_nonzero(valid)),
        "max_step_drift_deg": (
            None if finite_step.size == 0 else float(np.max(finite_step))
        ),
    })


def baseline_selection_aware_artifact(
    catalogue: BulkFlowCatalogue,
    sky_config: "SkySelectionConfig",
    *,
    C_pix: np.ndarray | None = None,
    n_boot: int = 256,
    sigma_star: float = 0.0,
    diagnostic_artifact: Mapping[str, Any] | None = None,
    stability_threshold_deg: float = 20.0,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the Mode 1 ``baseline_selection_aware_vX.json`` artifact."""
    from common.contracts import SkySelectionConfig
    from common.healpix_selection import (
        build_angular_completeness,
        build_zoa_mask,
        compute_selection_weights,
        lb_to_pix,
    )

    if not isinstance(sky_config, SkySelectionConfig):
        raise TypeError(
            "baseline_selection_aware_artifact requires a SkySelectionConfig"
        )
    l_deg, b_deg = _catalog_lb(catalogue)
    mask_pix = build_zoa_mask(
        l_deg,
        b_deg,
        bcut_deg=sky_config.zoa_half_angle_deg,
        nside=sky_config.nside,
    )
    if C_pix is None:
        C_pix = build_angular_completeness(
            l_deg,
            b_deg,
            nside=sky_config.nside,
            smooth_sigma_pix=sky_config.smooth_sigma_pix,
        )
    pix = lb_to_pix(l_deg, b_deg, sky_config.nside)
    w_selection = compute_selection_weights(l_deg, b_deg, mask_pix, C_pix)
    active = w_selection > 0.0
    retention_fraction = float(active.mean()) if active.size else 0.0
    if int(np.count_nonzero(active)) < 4:
        raise RuntimeError(
            "baseline_selection_aware_artifact: fewer than four active sources "
            "survive the ZoA/completeness mask"
        )
    active_catalogue = BulkFlowCatalogue(
        n_hat=catalogue.n_hat[active],
        u=catalogue.u[active],
        sigma=catalogue.sigma[active],
        w_native=catalogue.w_native[active],
        w_selection=w_selection[active],
        label=f"{catalogue.label}.selection_aware",
    )
    fit = wls_bulk_flow(
        active_catalogue.n_hat,
        active_catalogue.u,
        sigma=active_catalogue.sigma,
        w_native=active_catalogue.w_native,
        w_selection=active_catalogue.w_selection,
        sigma_star=sigma_star,
    )
    seed_value = (metadata or {}).get("random_seed")
    boot = bootstrap_covariance(
        active_catalogue,
        n_boot=n_boot,
        sigma_star=sigma_star,
        rng=np.random.default_rng(
            None if seed_value is None else int(seed_value)
        ),
    )
    diag = (
        diagnostic_artifact
        if diagnostic_artifact is not None
        else diagnostic_zoa_ladder_artifact(
            catalogue,
            nside=sky_config.nside,
            sigma_star=sigma_star,
            stability_threshold_deg=stability_threshold_deg,
            metadata=metadata,
        )
    )
    axis = _axis_from_vector(fit.V_hat)
    gate_passed = bool(
        retention_fraction >= sky_config.min_retention_fraction
        and diag.get("zoa_ladder_stable", False)
    )
    extra = dict(metadata or {})
    config_payload = {
        "sky_config": {
            "zoa_half_angle_deg": sky_config.zoa_half_angle_deg,
            "min_retention_fraction": sky_config.min_retention_fraction,
            "nside": sky_config.nside,
            "smooth_sigma_pix": sky_config.smooth_sigma_pix,
        },
        "n_boot": n_boot,
        "sigma_star": sigma_star,
        "stability_threshold_deg": stability_threshold_deg,
        "metadata": extra,
    }
    return _jsonify({
        "artifact_name": "baseline_selection_aware_v1.json",
        "generated_by": extra.get(
            "generated_by",
            "common.bulkflow_estimator.baseline_selection_aware_artifact",
        ),
        "git_commit": extra.get("git_commit", ""),
        "config_hash": _config_hash(config_payload),
        "input_data_hashes": list(extra.get("input_data_hashes", [])),
        "random_seed": extra.get("random_seed"),
        "wall_time_sec": extra.get("wall_time_sec"),
        "python_version": extra.get("python_version", platform.python_version()),
        "numpy_version": extra.get("numpy_version", np.__version__),
        "claim_tier": extra.get("claim_tier", "CONDITIONAL"),
        "scope_label": extra.get("scope_label", "baseline"),
        "production_allowed": False,
        "retention_fraction": retention_fraction,
        "min_retention_fraction": float(sky_config.min_retention_fraction),
        "zoa_ladder_stable": bool(diag.get("zoa_ladder_stable", False)),
        "mode0_to_mode1_gate_passed": gate_passed,
        "n_source_total": int(catalogue.n_sources),
        "n_source_active": int(active_catalogue.n_sources),
        "V_hat_kmps": fit.V_hat.tolist(),
        "cov_kmps2": fit.cov.tolist(),
        "effective_weight_sum": float(fit.diagnostics["effective_weight_sum"]),
        "axis": {
            "l_deg": axis["l_deg"],
            "b_deg": axis["b_deg"],
            "source": "selection_aware",
            "weight_mode": "native",
            "selection_mode": "angular_completeness",
            "production_allowed": False,
        },
        "bootstrap": {
            "cov_kmps2": boot["cov"].tolist(),
            "V_hat_mean_kmps": boot["V_hat_mean"].tolist(),
            "n_boot": int(boot["n_boot"]),
        },
    })


def retention_vs_posterior_artifact(
    diagnostic_artifact: Mapping[str, Any],
    fiducial_bundle: Mapping[str, Any],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``retention_vs_posterior_v1.json`` from Mode 0 and Mode 2 artifacts.

    This compares each diagnostic ladder axis against the fiducial posterior
    axis and records how directional drift scales with retained sky fraction.
    """
    from common.posterior_summary import credible_cone

    bcut = np.asarray(diagnostic_artifact.get("bcut_deg"), dtype=float)
    retention = np.asarray(
        diagnostic_artifact.get("retention_fraction"),
        dtype=float,
    )
    axis_l = np.asarray(diagnostic_artifact.get("axis_l_deg"), dtype=float)
    axis_b = np.asarray(diagnostic_artifact.get("axis_b_deg"), dtype=float)
    if (
        bcut.ndim != 1
        or retention.shape != bcut.shape
        or axis_l.shape != bcut.shape
        or axis_b.shape != bcut.shape
    ):
        raise ValueError(
            "retention_vs_posterior_artifact requires a diag_zoa_ladder "
            "payload with aligned bcut/retention/axis arrays"
        )

    axis_payload = fiducial_bundle.get("axis")
    if not isinstance(axis_payload, Mapping):
        raise ValueError(
            "retention_vs_posterior_artifact requires a fiducial bundle "
            "with an `axis` record"
        )
    fid_l = float(axis_payload["l_deg"])
    fid_b = float(axis_payload["b_deg"])

    summary = fiducial_bundle.get("posterior_summary", {})
    if not isinstance(summary, Mapping):
        raise ValueError(
            "retention_vs_posterior_artifact requires a fiducial bundle "
            "with `posterior_summary`"
        )
    lb_post = summary.get("lb_posterior", {})
    if not isinstance(lb_post, Mapping):
        raise ValueError(
            "retention_vs_posterior_artifact requires posterior_summary.lb_posterior"
        )
    cone_68 = summary.get("credible_cone", {})
    if not isinstance(cone_68, Mapping) or "radius_deg" not in cone_68:
        raise ValueError(
            "retention_vs_posterior_artifact requires posterior_summary.credible_cone"
        )
    cone_95 = credible_cone(
        np.asarray(lb_post["l_deg"], dtype=float),
        np.asarray(lb_post["b_deg"], dtype=float),
        level=0.95,
        weights=np.asarray(lb_post["weights"], dtype=float),
    )

    shift = np.full(bcut.shape, np.nan, dtype=float)
    valid = np.isfinite(axis_l) & np.isfinite(axis_b)
    for idx in np.flatnonzero(valid):
        shift[idx] = _angular_sep_deg(
            float(axis_l[idx]),
            float(axis_b[idx]),
            fid_l,
            fid_b,
        )

    valid_shift = np.isfinite(shift)
    corr = None
    if int(np.count_nonzero(valid_shift)) >= 2:
        corr = float(np.corrcoef(retention[valid_shift], shift[valid_shift])[0, 1])

    extra = dict(metadata or {})
    config_payload = {
        "diagnostic_artifact_name": diagnostic_artifact.get("artifact_name", ""),
        "diagnostic_config_hash": diagnostic_artifact.get("config_hash", ""),
        "fiducial_artifact_name": fiducial_bundle.get("artifact_name", ""),
        "fiducial_config_hash": fiducial_bundle.get("config_hash", ""),
        "metadata": extra,
    }
    finite_shift = shift[np.isfinite(shift)]
    radius_68 = float(cone_68["radius_deg"])
    radius_95 = float(cone_95["radius_deg"])
    return _jsonify({
        "artifact_name": "retention_vs_posterior_v1.json",
        "generated_by": extra.get(
            "generated_by",
            "common.bulkflow_estimator.retention_vs_posterior_artifact",
        ),
        "git_commit": extra.get("git_commit", ""),
        "config_hash": _config_hash(config_payload),
        "input_data_hashes": list(extra.get("input_data_hashes", [])),
        "random_seed": extra.get("random_seed"),
        "wall_time_sec": extra.get("wall_time_sec"),
        "python_version": extra.get("python_version", platform.python_version()),
        "numpy_version": extra.get("numpy_version", np.__version__),
        "claim_tier": extra.get("claim_tier", "CONDITIONAL"),
        "scope_label": extra.get("scope_label", "diagnostic_vs_fiducial"),
        "production_allowed": False,
        "source_artifacts": {
            "diagnostic": {
                "artifact_name": diagnostic_artifact.get("artifact_name", ""),
                "config_hash": diagnostic_artifact.get("config_hash", ""),
            },
            "fiducial": {
                "artifact_name": fiducial_bundle.get("artifact_name", ""),
                "config_hash": fiducial_bundle.get("config_hash", ""),
            },
        },
        "bcut_deg": bcut.tolist(),
        "retention_fraction": retention.tolist(),
        "axis_l_deg": axis_l.tolist(),
        "axis_b_deg": axis_b.tolist(),
        "posterior_shift_deg": shift.tolist(),
        "within_68_cone": (shift <= radius_68).tolist(),
        "within_95_cone": (shift <= radius_95).tolist(),
        "fiducial_axis": {
            "l_deg": fid_l,
            "b_deg": fid_b,
        },
        "credible_cone_68_deg": radius_68,
        "credible_cone_95_deg": radius_95,
        "max_shift_deg": (
            None if finite_shift.size == 0 else float(np.max(finite_shift))
        ),
        "correlation_retention_vs_shift": corr,
    })
