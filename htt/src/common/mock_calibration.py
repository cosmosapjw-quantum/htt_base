"""common.mock_calibration — Mode 2 mock-bank Layer D machinery (COMMON-F).

Implements the isotropic-null and injected-dipole mock pipelines plus the
coverage/bias diagnostics required for the ``fiducial_posterior`` artefact
(BASS_PY_HTT_TSC_RESEARCH_PLAN §6.4 and §6.7).

The REG-01 item ``test_mock_coverage_within_bounds`` (§6.10) enforces
``coverage_68pct ∈ [0.60, 0.76]`` on a controlled WLS-covariance mock;
that is the core property checked here. Dynesty is *not* a hard dependency
— callers pass in any estimator returning ``(V_hat, cov)`` (WLS bootstrap
is the default).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import platform
from typing import Any, Callable, Mapping

import numpy as np

from common.bulkflow_estimator import (
    BulkFlowCatalogue,
    BulkFlowFit,
    wls_bulk_flow,
)
from common.contracts import MockCalibrationReport, SkySelectionConfig
from common.healpix_selection import (
    build_angular_completeness,
    build_zoa_mask,
    compute_selection_weights,
    lb_to_pix,
)
from common.sky_geometry import lb_to_unitvec, unitvec_to_lb

__all__ = [
    "InjectedMockReport",
    "generate_isotropic_mock",
    "generate_injected_dipole_mock",
    "apply_same_mask",
    "recovered_bias",
    "coverage_test",
    "run_zoa_null_mocks",
    "run_injected_dipole_mocks",
    "apply_bias_correction",
    "mock_calibration_report_artifact",
]

EstimatorFn = Callable[
    [np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    tuple[np.ndarray, np.ndarray],
]


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


# ---------------------------------------------------------------------------
# Mock-report dataclass (injected family)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InjectedMockReport:
    """Injected-dipole mock calibration summary (§6.7)."""

    recovered_V_samples: np.ndarray    # (n_mock, 3)
    amp_bias_fraction: float
    direction_bias_deg: float
    amp_spread_fractional: float
    n_mock: int
    config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.recovered_V_samples.ndim != 2 or self.recovered_V_samples.shape[1] != 3:
            raise ValueError(
                f"recovered_V_samples must be (n, 3); got "
                f"{self.recovered_V_samples.shape}"
            )
        if self.n_mock <= 0:
            raise ValueError(f"n_mock must be > 0; got {self.n_mock}")


# ---------------------------------------------------------------------------
# Mock generation
# ---------------------------------------------------------------------------

def generate_isotropic_mock(
    catalogue: BulkFlowCatalogue,
    *,
    rng: np.random.Generator | None = None,
    sigma_star_kmps: float = 0.0,
) -> BulkFlowCatalogue:
    """Draw an isotropic-null velocity realisation on the *same* geometry.

    Keeps ``n_hat``, ``sigma``, ``w_native``, ``w_selection`` fixed and
    regenerates ``u_i ~ 𝒩(0, σ_eff,i²)`` with no underlying bulk flow. This
    is the realisation used by :func:`run_zoa_null_mocks`.
    """
    if rng is None:
        rng = np.random.default_rng()
    N = catalogue.n_sources
    sigma_eff = np.sqrt(catalogue.sigma ** 2 + float(sigma_star_kmps) ** 2)
    u = rng.normal(0.0, sigma_eff, size=N)
    return BulkFlowCatalogue(
        n_hat=catalogue.n_hat.copy(),
        u=u,
        sigma=catalogue.sigma.copy(),
        w_native=catalogue.w_native.copy(),
        w_selection=catalogue.w_selection.copy(),
        label=f"{catalogue.label}.isotropic_mock",
    )


def generate_injected_dipole_mock(
    catalogue: BulkFlowCatalogue,
    V_true_kmps: np.ndarray,
    *,
    rng: np.random.Generator | None = None,
    sigma_star_kmps: float = 0.0,
) -> BulkFlowCatalogue:
    """Draw a realisation with injected bulk-flow ``V_true`` on the same geometry."""
    if rng is None:
        rng = np.random.default_rng()
    V_true = np.asarray(V_true_kmps, dtype=float)
    if V_true.shape != (3,):
        raise ValueError(f"V_true_kmps must be (3,); got {V_true.shape}")
    N = catalogue.n_sources
    sigma_eff = np.sqrt(catalogue.sigma ** 2 + float(sigma_star_kmps) ** 2)
    u_clean = catalogue.n_hat @ V_true
    u = u_clean + rng.normal(0.0, sigma_eff, size=N)
    return BulkFlowCatalogue(
        n_hat=catalogue.n_hat.copy(),
        u=u,
        sigma=catalogue.sigma.copy(),
        w_native=catalogue.w_native.copy(),
        w_selection=catalogue.w_selection.copy(),
        label=f"{catalogue.label}.injected_dipole",
    )


# ---------------------------------------------------------------------------
# Mask / weight application
# ---------------------------------------------------------------------------

def apply_same_mask(
    catalogue: BulkFlowCatalogue,
    sky_config: SkySelectionConfig,
    *,
    C_pix: np.ndarray | None = None,
) -> BulkFlowCatalogue:
    """Apply the same ZoA + selection weights as the observed data.

    Returns a new catalogue with ``w_selection`` replaced by
    ``compute_selection_weights`` output. Sources whose pixel is outside the
    ZoA mask receive ``w_selection = 0`` (they survive the catalogue so the
    fit can still see their geometry, but the log-likelihood drops them —
    see :class:`common.bulkflow_likelihood.BulkFlowLikelihood`).
    """
    nside = int(sky_config.nside)
    l_deg, b_deg = unitvec_to_lb(catalogue.n_hat)
    mask_pix = build_zoa_mask(
        l_deg, b_deg, bcut_deg=sky_config.zoa_half_angle_deg, nside=nside,
    )
    if C_pix is None:
        C_pix = build_angular_completeness(
            l_deg, b_deg, nside=nside,
            smooth_sigma_pix=sky_config.smooth_sigma_pix,
        )
    w_sel = compute_selection_weights(l_deg, b_deg, mask_pix, C_pix)
    return BulkFlowCatalogue(
        n_hat=catalogue.n_hat.copy(),
        u=catalogue.u.copy(),
        sigma=catalogue.sigma.copy(),
        w_native=catalogue.w_native.copy(),
        w_selection=w_sel,
        label=f"{catalogue.label}.masked",
    )


# ---------------------------------------------------------------------------
# Bias / coverage diagnostics
# ---------------------------------------------------------------------------

def recovered_bias(
    V_true: np.ndarray,
    estimated_V_list: np.ndarray,
) -> dict[str, float]:
    """Amplitude and direction bias between truth and recovered samples.

    ``estimated_V_list`` is ``(n_mock, 3)``. Amplitude bias is the mean
    signed fractional residual ``<|V_hat|>/|V_true| − 1``; direction bias
    is the angular separation between the mean recovered direction and the
    true direction. A zero-amplitude truth is allowed (null tests); the
    amplitude-bias field is then ``None``-like via ``np.nan``.
    """
    V_true = np.asarray(V_true, dtype=float)
    V_hat = np.asarray(estimated_V_list, dtype=float)
    if V_true.shape != (3,):
        raise ValueError(f"V_true must be (3,); got {V_true.shape}")
    if V_hat.ndim != 2 or V_hat.shape[1] != 3:
        raise ValueError(f"estimated_V_list must be (n, 3); got {V_hat.shape}")
    amp_true = float(np.linalg.norm(V_true))
    amp_hat = np.linalg.norm(V_hat, axis=1)
    if amp_true <= 0.0:
        amp_bias = float("nan")
        direction_bias = float("nan")
    else:
        amp_bias = float((amp_hat / amp_true).mean() - 1.0)
        mean_vec = V_hat.mean(axis=0)
        mean_norm = float(np.linalg.norm(mean_vec))
        if mean_norm <= 0.0:
            direction_bias = float("nan")
        else:
            cos_sep = float(np.clip(
                (mean_vec / mean_norm) @ (V_true / amp_true), -1.0, 1.0
            ))
            direction_bias = float(np.rad2deg(np.arccos(cos_sep)))
    return {
        "amp_bias_fraction": amp_bias,
        "direction_bias_deg": direction_bias,
        "amp_spread_fractional": float(
            amp_hat.std() / amp_true if amp_true > 0 else amp_hat.std()
        ),
    }


def coverage_test(
    estimates: np.ndarray,
    covariances: np.ndarray,
    truth: np.ndarray,
    level: float = 0.68,
) -> float:
    """Fraction of mocks whose ``χ²_3`` distance to ``truth`` lies within level.

    For a 3-D Gaussian posterior with mean ``V_hat`` and covariance ``cov``
    the contour at credibility ``level`` is the Mahalanobis sphere with
    radius-squared ``χ²_3(level)``. This is the working-definition coverage
    used in §6.7 (coverage_68pct, coverage_95pct).
    """
    from scipy.stats import chi2

    estimates = np.asarray(estimates, dtype=float)
    covariances = np.asarray(covariances, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimates.ndim != 2 or estimates.shape[1] != 3:
        raise ValueError(f"estimates must be (n, 3); got {estimates.shape}")
    n = estimates.shape[0]
    if covariances.shape != (n, 3, 3):
        raise ValueError(
            f"covariances must be (n, 3, 3); got {covariances.shape}"
        )
    if truth.shape != (3,):
        raise ValueError(f"truth must be (3,); got {truth.shape}")
    if not (0.0 < level < 1.0):
        raise ValueError(f"level must be in (0, 1); got {level}")
    threshold = float(chi2.ppf(level, df=3))
    inside = 0
    for k in range(n):
        diff = estimates[k] - truth
        try:
            mahal = float(diff @ np.linalg.solve(covariances[k], diff))
        except np.linalg.LinAlgError:
            continue
        if mahal <= threshold:
            inside += 1
    return inside / n


# ---------------------------------------------------------------------------
# Production runners
# ---------------------------------------------------------------------------

def _default_estimator(
    n_hat: np.ndarray,
    u: np.ndarray,
    sigma: np.ndarray,
    w_native: np.ndarray,
    w_selection: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    fit = wls_bulk_flow(
        n_hat, u,
        sigma=sigma, w_native=w_native, w_selection=w_selection,
    )
    return fit.V_hat, fit.cov


def _run_mock_bank(
    catalogue: BulkFlowCatalogue,
    sky_config: SkySelectionConfig,
    V_true: np.ndarray,
    *,
    n_mock: int,
    rng: np.random.Generator | None,
    estimator: EstimatorFn | None,
    C_pix: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Common driver for null and injected mock banks.

    Returns ``(estimates, covariances)`` for the ``n_mock`` mocks. Mocks
    whose WLS fit is singular are dropped and do not count toward the
    returned shape (so ``estimates.shape[0] ≤ n_mock``).
    """
    if rng is None:
        rng = np.random.default_rng()
    if estimator is None:
        estimator = _default_estimator
    estimates = np.empty((n_mock, 3), dtype=float)
    covariances = np.empty((n_mock, 3, 3), dtype=float)
    succeeded = 0
    for _ in range(n_mock):
        if np.allclose(V_true, 0.0):
            mock = generate_isotropic_mock(catalogue, rng=rng)
        else:
            mock = generate_injected_dipole_mock(catalogue, V_true, rng=rng)
        masked = apply_same_mask(mock, sky_config, C_pix=C_pix)
        try:
            V_hat, cov = estimator(
                masked.n_hat, masked.u, masked.sigma,
                masked.w_native, masked.w_selection,
            )
        except (ValueError, np.linalg.LinAlgError):
            continue
        estimates[succeeded] = V_hat
        covariances[succeeded] = cov
        succeeded += 1
    return estimates[:succeeded], covariances[:succeeded]


def run_zoa_null_mocks(
    catalogue: BulkFlowCatalogue,
    sky_config: SkySelectionConfig,
    *,
    n_mock: int = 1000,
    rng: np.random.Generator | None = None,
    estimator: EstimatorFn | None = None,
    C_pix: np.ndarray | None = None,
) -> MockCalibrationReport:
    """Null-hypothesis mock bank with ZoA + selection applied (§6.7).

    Returns the ``MockCalibrationReport`` populated with bias/coverage/
    credible_radius summaries. Null-hypothesis bias is the zero-sample
    amplitude of the recovered dipole mean — not a fractional bias.
    """
    estimates, covariances = _run_mock_bank(
        catalogue, sky_config, np.zeros(3),
        n_mock=n_mock, rng=rng, estimator=estimator, C_pix=C_pix,
    )
    if estimates.shape[0] < max(20, n_mock // 10):
        raise RuntimeError(
            f"run_zoa_null_mocks: only {estimates.shape[0]} of {n_mock} mocks "
            "produced a non-singular WLS fit — catalogue geometry is too sparse"
        )

    amp = np.linalg.norm(estimates, axis=1)
    mean_vec = estimates.mean(axis=0)
    mean_norm = float(np.linalg.norm(mean_vec))
    l_mean, b_mean = unitvec_to_lb(mean_vec / max(mean_norm, 1e-12))
    # Under the null, there is no true direction; we report the *recovered*
    # mean direction as the "bias direction" and the mean amplitude as
    # the bias amplitude (both zero in expectation).
    bias_amp = float(amp.mean())
    bias_direction = float(l_mean)    # recovered-mean longitude in degrees

    coverage_68 = coverage_test(estimates, covariances, np.zeros(3), level=0.68)
    coverage_95 = coverage_test(estimates, covariances, np.zeros(3), level=0.95)
    # Credible radius: median of the 1-σ (68%) Gaussian cone over the mocks.
    # For a 3-D Gaussian the 68% Mahalanobis radius is sqrt(chi2.ppf(0.68, 3))
    # in standard-deviation units; we convert to an angular cone using the
    # covariance's trace as a scalar σ_V.
    sigma_V = np.sqrt(covariances.trace(axis1=1, axis2=2) / 3.0)
    # Angular spread ≈ σ_V / |V_hat| rad when |V_hat| ≫ σ_V; at the null it
    # is better-characterised by the distribution of recovered directions.
    with np.errstate(divide="ignore", invalid="ignore"):
        cone_rad = np.where(amp > 0.0, sigma_V / amp, np.nan)
    credible_radius_deg = float(np.nanmedian(np.rad2deg(cone_rad)))

    return MockCalibrationReport(
        bias_amp=bias_amp,
        bias_direction_deg=bias_direction,
        coverage_68=coverage_68,
        credible_radius_deg=credible_radius_deg,
        n_mock=estimates.shape[0],
        config={
            "mode": "zoa_null",
            "zoa_half_angle_deg": sky_config.zoa_half_angle_deg,
            "n_mock_requested": n_mock,
            "coverage_95": coverage_95,
            "null_amplitude_mean": float(amp.mean()),
            "null_amplitude_std": float(amp.std()),
        },
    )


def run_injected_dipole_mocks(
    catalogue: BulkFlowCatalogue,
    V_true_kmps: np.ndarray,
    sky_config: SkySelectionConfig,
    *,
    n_mock: int = 1000,
    rng: np.random.Generator | None = None,
    estimator: EstimatorFn | None = None,
    C_pix: np.ndarray | None = None,
) -> InjectedMockReport:
    """Injected-dipole mock bank. Returns amplitude + direction bias (§6.7)."""
    V_true = np.asarray(V_true_kmps, dtype=float)
    if V_true.shape != (3,):
        raise ValueError(f"V_true_kmps must be (3,); got {V_true.shape}")
    if float(np.linalg.norm(V_true)) <= 0.0:
        raise ValueError(
            "run_injected_dipole_mocks requires a non-zero V_true; "
            "use run_zoa_null_mocks for the null case"
        )
    estimates, _ = _run_mock_bank(
        catalogue, sky_config, V_true,
        n_mock=n_mock, rng=rng, estimator=estimator, C_pix=C_pix,
    )
    if estimates.shape[0] < max(20, n_mock // 10):
        raise RuntimeError(
            f"run_injected_dipole_mocks: only {estimates.shape[0]} of "
            f"{n_mock} mocks converged"
        )
    bias = recovered_bias(V_true, estimates)
    return InjectedMockReport(
        recovered_V_samples=estimates,
        amp_bias_fraction=float(bias["amp_bias_fraction"]),
        direction_bias_deg=float(bias["direction_bias_deg"]),
        amp_spread_fractional=float(bias["amp_spread_fractional"]),
        n_mock=estimates.shape[0],
        config={
            "mode": "injected_dipole",
            "V_true": tuple(float(x) for x in V_true),
            "n_mock_requested": n_mock,
            "zoa_half_angle_deg": sky_config.zoa_half_angle_deg,
        },
    )


# ---------------------------------------------------------------------------
# Bias correction for the 4-summary AH consumer
# ---------------------------------------------------------------------------

def apply_bias_correction(
    V_hat: np.ndarray,
    injected_report: InjectedMockReport,
) -> np.ndarray:
    """De-bias a selection-aware estimate using the injected-mock report.

    Subtracts the mean mock residual ``E[V_hat - V_true]`` from the raw
    estimate. This mirrors the ``mock_calibrated_summary`` slot of the
    PR13AH four-summary structure (§6.3): the selection-aware estimate is
    passed through this correction before being elevated to Mode 2 fiducial.
    """
    V_hat = np.asarray(V_hat, dtype=float)
    if V_hat.shape != (3,):
        raise ValueError(f"V_hat must be (3,); got {V_hat.shape}")
    V_true_tuple = injected_report.config.get("V_true")
    if V_true_tuple is None:
        raise ValueError(
            "injected_report.config is missing 'V_true' — can't compute residual"
        )
    V_true = np.asarray(V_true_tuple, dtype=float)
    residual = injected_report.recovered_V_samples.mean(axis=0) - V_true
    return V_hat - residual


def mock_calibration_report_artifact(
    report: MockCalibrationReport,
    *,
    injected_report: InjectedMockReport | None = None,
    coverage_window_68: tuple[float, float] = (0.60, 0.76),
    bias_fraction_threshold: float = 0.05,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the Mode 2 precondition ``mock_calibration_report_vX.json``.

    When an ``InjectedMockReport`` is available, the artifact also evaluates
    the amplitude-bias leg of the Mode 1 → Mode 2 gate from the research
    plan. Without it, only the coverage gate is assessed.
    """
    if not isinstance(report, MockCalibrationReport):
        raise TypeError(
            "mock_calibration_report_artifact requires a MockCalibrationReport"
        )
    lower, upper = coverage_window_68
    if not (0.0 <= lower <= upper <= 1.0):
        raise ValueError(
            "coverage_window_68 must satisfy 0 <= lower <= upper <= 1"
        )
    if bias_fraction_threshold < 0.0:
        raise ValueError("bias_fraction_threshold must be >= 0")
    coverage_pass = bool(lower <= report.coverage_68 <= upper)
    injected_block: dict[str, Any] | None
    if injected_report is None:
        bias_fraction = None
        bias_pass = None
        injected_block = None
    else:
        bias_fraction = float(abs(injected_report.amp_bias_fraction))
        bias_pass = bool(bias_fraction <= bias_fraction_threshold)
        injected_block = {
            "amp_bias_fraction": float(injected_report.amp_bias_fraction),
            "direction_bias_deg": float(injected_report.direction_bias_deg),
            "amp_spread_fractional": float(injected_report.amp_spread_fractional),
            "n_mock": int(injected_report.n_mock),
            "config": _jsonify(injected_report.config),
        }
    gate_passed = coverage_pass if bias_pass is None else bool(
        coverage_pass and bias_pass
    )
    extra = dict(metadata or {})
    config_payload = {
        "coverage_window_68": coverage_window_68,
        "bias_fraction_threshold": bias_fraction_threshold,
        "metadata": extra,
    }
    return _jsonify({
        "artifact_name": "mock_calibration_report_v1.json",
        "generated_by": extra.get(
            "generated_by",
            "common.mock_calibration.mock_calibration_report_artifact",
        ),
        "git_commit": extra.get("git_commit", ""),
        "config_hash": _config_hash(config_payload),
        "input_data_hashes": list(extra.get("input_data_hashes", [])),
        "random_seed": extra.get("random_seed"),
        "wall_time_sec": extra.get("wall_time_sec"),
        "python_version": extra.get("python_version", platform.python_version()),
        "numpy_version": extra.get("numpy_version", np.__version__),
        "claim_tier": extra.get("claim_tier", "CONDITIONAL"),
        "scope_label": extra.get("scope_label", "fiducial"),
        "production_allowed": False,
        "coverage_window_68": list(coverage_window_68),
        "coverage_pass": coverage_pass,
        "bias_fraction_threshold": float(bias_fraction_threshold),
        "bias_pass": bias_pass,
        "mode1_to_mode2_gate_passed": gate_passed,
        "bias_amp": float(report.bias_amp),
        "bias_direction_deg": float(report.bias_direction_deg),
        "coverage_68": float(report.coverage_68),
        "credible_radius_deg": float(report.credible_radius_deg),
        "n_mock": int(report.n_mock),
        "null_distribution_summary": {
            "coverage_95": report.config.get("coverage_95"),
            "null_amplitude_mean": report.config.get("null_amplitude_mean"),
            "null_amplitude_std": report.config.get("null_amplitude_std"),
        },
        "report_config": _jsonify(report.config),
        "injected_dipole_summary": injected_block,
    })
