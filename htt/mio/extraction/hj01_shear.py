"""mio.extraction.hj01_shear — MIO HJ-01 non-parametric shear extraction (skeleton).

INDEPENDENT_TRACKS_PLAN v1.2 §21 / Week 10 Days 3-4.
Parent: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md v3 §4.5.3.1 (HJ-01) and v3 §17.3
(K_ℓ atlas dependency on bass_py W10-02 V-gate).

Status (W10): **skeleton only**. The bass_py K_ℓ atlas (W10-02) is not yet
landed; this module ships the schema validator + extraction kernel + tests
against synthetic K_ℓ dicts (no bass_py runtime dependency). When bass_py
W10-02 lands a real ``AtlasEntry`` for the K_ℓ kernel, the production
consumer is one of:

  * ``extract_from_kl_atlas(kl_dict)`` — pass a plain dict with the keys
    documented in :data:`KL_ATLAS_REQUIRED_KEYS`;
  * ``extract_from_atlas_entry(entry)`` — pass a ``workspace.contracts.
    AtlasEntry`` whose ``kernel_name == 'K_ell'`` (the dict path is the
    universal one; the ``AtlasEntry`` path adapts to the dict path).

Until the bass_py V-gate passes, every certificate emitted by this
module carries ``reduction_status='diagnostic-only'`` per parent plan
§17.3 risk row "HJ-01 K_ℓ atlas 의존성 — bass_py W10-02 V-gate 미통과 시
Σ²_MIO 부정확 → diagnostic-only tag".

Core formula (v3 §4.5.3.1):

    Σ²_MIO(ℓ) = (C_ℓ_obs - C_ℓ_LCDM) / K_ℓ

with per-ℓ uncertainty (assuming K_ℓ is theory-exact and observational
variance dominates):

    σ_Σ²(ℓ) ≈ σ_{C_ℓ} / |K_ℓ|

The ℓ-independence test χ² has dof = N-1 with weighted mean
``Σ²_best = Σ_ℓ w_ℓ Σ²_ℓ / Σ_ℓ w_ℓ``, ``w_ℓ = 1/σ_ℓ²``.

G19 hard separation (v3 §4.5.4 + ch11 truth-certificate language): the
output is a `MioCertificate`, which refuses ``as_posterior_bundle()``;
calling code must never combine the Σ²_best returned here with an HTT
posterior in a single likelihood term. Cross-checks via
``tsc.integration.htt_bridge.ff_htt_mc_cross_check`` are the legitimate
channel.
"""
from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

from mio.interface.manifest import (
    MioPrerequisites,
    SkySupportStatus,
    assess_mio_readiness,
)
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from workspace.contracts.atlas_entry import AtlasEntry
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.tsc_overlay import TscAdequacyOverlay


# ---------------------------------------------------------------------------
# Schema for the K_ℓ atlas dict consumed by this module.
# ---------------------------------------------------------------------------

KL_ATLAS_REQUIRED_KEYS: Tuple[str, ...] = (
    "ell",
    "C_ell_obs",
    "C_ell_lcdm",
    "K_ell",
    "sigma_C_ell",
    "bianchi_type",
    "atlas_name",
    "generated_by",
    "git_commit",
    "config_hash",
)
"""Keys that the bass_py K_ℓ atlas producer MUST populate.

The four numeric arrays (``ell``, ``C_ell_obs``, ``C_ell_lcdm``, ``K_ell``,
``sigma_C_ell``) must be 1-D and share the same length. Units:

* ``ell`` — integer multipoles, length N.
* ``C_ell_obs`` — observed angular power, μK² (Planck 2018 mask-corrected).
* ``C_ell_lcdm`` — ΛCDM-best-fit prediction at the same multipoles, μK².
* ``K_ell`` — BASS theory kernel d C_ℓ / d Σ² evaluated at the FLRW point.
* ``sigma_C_ell`` — observational uncertainty on ``C_ell_obs``, μK².

The string fields ``bianchi_type`` / ``atlas_name`` / ``generated_by`` /
``git_commit`` / ``config_hash`` are passed straight through to the
emitted `MioCertificate` for provenance.
"""

KL_ATLAS_OPTIONAL_KEYS: Tuple[str, ...] = ("domain_caveats",)


# ---------------------------------------------------------------------------
# Small math helpers
# ---------------------------------------------------------------------------


def _normal_inv_cdf(p: float) -> float:
    """Inverse standard-normal CDF using Acklam's rational approximation."""

    if not (0.0 < p < 1.0):
        raise ValueError("p must lie in (0, 1)")

    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    plow = 0.02425
    phigh = 1.0 - plow

    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return float(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return float(
            -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )

    q = p - 0.5
    r = q * q
    return float(
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
        * q
        / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    )


# ---------------------------------------------------------------------------
# Config + report dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ShearExtractorConfig:
    """Knobs for non-parametric Σ² extraction.

    Parameters
    ----------
    ell_min, ell_max
        Inclusive bounds on the multipole window used for the weighted mean
        + ℓ-independence test. The per-ℓ array is always returned over the
        full input range; only the summary statistics restrict to this
        window. Default is ``(2, 30)`` matching the v3 §4.5.3.1 low-ℓ
        Σ²_MIO recipe.
    min_kernel_abs
        Floor on ``|K_ℓ|``. Multipoles below this floor are dropped from
        the per-ℓ output (a divide-by-zero guard); they are reported in
        :attr:`ShearExtractorReport.dropped_ells` so callers can audit.
    flrw_null_band_sigma
        How many σ around zero defines the FLRW null band (used by
        :meth:`ShearExtractorReport.is_flrw_consistent`) before any
        multiple-testing correction. Default 2.0.
    bonferroni_adjust_flrw_band
        When true, widen the null band so the family-wise false-flag rate
        across all kept multipoles is bounded by ``flrw_familywise_alpha``.
        This is the safer default for the 29-multipole low-ℓ window.
    flrw_familywise_alpha
        Family-wise false-flag target used by the Bonferroni widening.
    """

    ell_min: int = 2
    ell_max: int = 30
    min_kernel_abs: float = 1e-30
    flrw_null_band_sigma: float = 2.0
    bonferroni_adjust_flrw_band: bool = True
    flrw_familywise_alpha: float = 0.05

    def __post_init__(self) -> None:
        if self.ell_min > self.ell_max:
            raise ValueError(
                f"ell_min must be <= ell_max; got {self.ell_min} > {self.ell_max}"
            )
        if self.min_kernel_abs < 0.0:
            raise ValueError(
                f"min_kernel_abs must be >= 0; got {self.min_kernel_abs}"
            )
        if self.flrw_null_band_sigma <= 0.0:
            raise ValueError(
                "flrw_null_band_sigma must be strictly positive"
            )
        if not (0.0 < self.flrw_familywise_alpha < 1.0):
            raise ValueError(
                "flrw_familywise_alpha must lie in (0, 1)"
            )

    def effective_flrw_null_band_sigma(self, n_multipoles: int) -> float:
        """Return the actual σ-threshold used for the FLRW consistency gate."""
        if n_multipoles <= 0 or not self.bonferroni_adjust_flrw_band:
            return float(self.flrw_null_band_sigma)
        per_test_alpha = self.flrw_familywise_alpha / float(n_multipoles)
        sigma = _normal_inv_cdf(1.0 - per_test_alpha / 2.0)
        return float(max(self.flrw_null_band_sigma, sigma))


@dataclass(frozen=True)
class ShearExtractorReport:
    """Container for the per-ℓ extraction + ℓ-independence summary."""

    ell: np.ndarray                     # 1-D, restricted to (ell_min..ell_max) ∩ kept
    sigma2_per_ell: np.ndarray          # Σ²_MIO(ℓ); shape == ell.shape
    sigma_sigma2_per_ell: np.ndarray    # σ_Σ²(ℓ); shape == ell.shape
    sigma2_best: float                  # inverse-variance weighted mean of sigma2_per_ell
    sigma2_best_uncertainty: float      # 1-σ on sigma2_best
    chi2_independence: float            # χ² for "Σ² is ℓ-independent"
    dof_independence: int               # N - 1
    p_value_independence: float         # χ²-tail probability with dof_independence
    dropped_ells: Tuple[int, ...]       # multipoles dropped by min_kernel_abs guard
    bianchi_type: str
    atlas_name: str

    def is_flrw_consistent(
        self,
        config: Optional[ShearExtractorConfig] = None,
    ) -> bool:
        """True iff every kept ℓ has |Σ²_ℓ| < band·σ_ℓ after config widening."""
        cfg = config if config is not None else ShearExtractorConfig()
        if self.ell.size == 0:
            return True
        z = np.abs(self.sigma2_per_ell) / np.maximum(self.sigma_sigma2_per_ell, 1e-300)
        band_sigma = cfg.effective_flrw_null_band_sigma(int(self.ell.size))
        return bool(np.all(z < band_sigma))


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def validate_kl_atlas_schema(kl: Mapping[str, Any]) -> None:
    """Validate a K_ℓ atlas dict against :data:`KL_ATLAS_REQUIRED_KEYS`.

    Raises
    ------
    KeyError
        If any required key is absent.
    ValueError
        If any of the four numeric arrays are non-1D, mismatched in shape,
        or contain NaNs/infs.
    """
    missing = [k for k in KL_ATLAS_REQUIRED_KEYS if k not in kl]
    if missing:
        raise KeyError(
            f"K_ell atlas dict is missing required keys: {missing}. "
            f"Required keys are {list(KL_ATLAS_REQUIRED_KEYS)}."
        )

    arrays = {k: np.asarray(kl[k], dtype=float) for k in
              ("ell", "C_ell_obs", "C_ell_lcdm", "K_ell", "sigma_C_ell")}
    for name, arr in arrays.items():
        if arr.ndim != 1:
            raise ValueError(f"K_ell atlas '{name}' must be 1-D; got ndim={arr.ndim}")
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"K_ell atlas '{name}' contains non-finite entries")

    n = arrays["ell"].size
    for name, arr in arrays.items():
        if arr.size != n:
            raise ValueError(
                f"K_ell atlas '{name}' length {arr.size} != ell length {n}"
            )
    if np.any(arrays["sigma_C_ell"] <= 0):
        raise ValueError("K_ell atlas 'sigma_C_ell' must be strictly positive")


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------


def _weighted_mean_chi2(
    sigma2: np.ndarray,
    sigma_sigma2: np.ndarray,
) -> Tuple[float, float, float, int]:
    """Inverse-variance weighted mean + χ² for the homogeneous-shear hypothesis.

    Returns
    -------
    tuple
        ``(sigma2_best, sigma2_best_uncertainty, chi2, dof)``.
    """
    n = int(sigma2.size)
    if n == 0:
        return float("nan"), float("nan"), float("nan"), 0
    w = 1.0 / np.maximum(sigma_sigma2 ** 2, 1e-300)
    wsum = float(w.sum())
    sigma2_best = float(np.sum(w * sigma2) / wsum)
    sigma2_best_unc = float(1.0 / np.sqrt(wsum))
    chi2 = float(np.sum(((sigma2 - sigma2_best) / sigma_sigma2) ** 2))
    dof = max(n - 1, 0)
    return sigma2_best, sigma2_best_unc, chi2, dof


def _chi2_sf(chi2: float, dof: int) -> float:
    """Survival function (upper tail) of the χ² distribution.

    Implemented via the regularised upper incomplete gamma so we don't
    require scipy at import time. Falls back to a NaN sentinel on dof<=0.
    """
    if dof <= 0:
        return float("nan")
    if not math.isfinite(chi2) or chi2 < 0:
        return float("nan")
    return float(_gammaincc(dof / 2.0, chi2 / 2.0))


def _warn_gammaincc_nonconvergence(
    *,
    branch: str,
    a: float,
    x: float,
    max_iterations: int,
) -> None:
    warnings.warn(
        "_gammaincc did not converge within "
        f"{max_iterations} iterations on the {branch} branch "
        f"(a={a:.6g}, x={x:.6g}); returning best-effort value",
        RuntimeWarning,
        stacklevel=3,
    )


def _gammaincc(a: float, x: float, *, max_iterations: int = 200) -> float:
    """Regularised upper incomplete gamma Q(a, x) via series / continued fraction.

    Lifted from Numerical Recipes §6.2 — accurate to ~1e-12 in the
    regimes used here (a in [1, 50], x in [0, 200]).
    """
    if x < 0 or a <= 0:
        return float("nan")
    if x == 0:
        return 1.0
    if x < a + 1.0:
        # Use the series for P(a, x), then return 1 - P.
        ap = a
        s = 1.0 / a
        term = s
        converged = False
        for _ in range(max_iterations):
            ap += 1.0
            term *= x / ap
            s += term
            if abs(term) < abs(s) * 1e-15:
                converged = True
                break
        if not converged:
            _warn_gammaincc_nonconvergence(
                branch="series",
                a=a,
                x=x,
                max_iterations=max_iterations,
            )
        p = s * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return 1.0 - p
    # Continued fraction for Q(a, x).
    b = x + 1.0 - a
    c = 1e300
    d = 1.0 / b
    h = d
    converged = False
    for i in range(1, max_iterations + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            converged = True
            break
    if not converged:
        _warn_gammaincc_nonconvergence(
            branch="continued-fraction",
            a=a,
            x=x,
            max_iterations=max_iterations,
        )
    return h * math.exp(-x + a * math.log(x) - math.lgamma(a))


def extract_from_kl_atlas(
    kl: Mapping[str, Any],
    config: Optional[ShearExtractorConfig] = None,
) -> ShearExtractorReport:
    """Apply Σ²_MIO(ℓ) = (C_ℓ_obs − C_ℓ_LCDM) / K_ℓ.

    The input ``kl`` must satisfy :func:`validate_kl_atlas_schema`. The
    returned report covers only multipoles in
    ``[config.ell_min, config.ell_max]`` whose ``|K_ℓ|`` exceeds
    ``config.min_kernel_abs``.

    The summary statistics (``sigma2_best``, ``chi2_independence``,
    ``p_value_independence``) treat the per-ℓ residuals as independent
    Gaussians. For correlated cosmic-variance C_ℓ residuals this is an
    upper bound on the test power; the bass_py W10-02 K_ℓ atlas is
    expected to also expose a per-ℓ covariance for a tightened version
    of this routine — tracked for Week 11+.
    """
    validate_kl_atlas_schema(kl)
    cfg = config if config is not None else ShearExtractorConfig()

    ell = np.asarray(kl["ell"], dtype=float)
    c_obs = np.asarray(kl["C_ell_obs"], dtype=float)
    c_lcdm = np.asarray(kl["C_ell_lcdm"], dtype=float)
    k_ell = np.asarray(kl["K_ell"], dtype=float)
    sig_c = np.asarray(kl["sigma_C_ell"], dtype=float)

    # Window mask first (range), then kernel-floor mask.
    in_range = (ell >= cfg.ell_min) & (ell <= cfg.ell_max)
    keep = in_range & (np.abs(k_ell) > cfg.min_kernel_abs)
    dropped = tuple(int(x) for x in ell[in_range & ~keep].tolist())

    sigma2 = (c_obs[keep] - c_lcdm[keep]) / k_ell[keep]
    sigma_sigma2 = sig_c[keep] / np.abs(k_ell[keep])

    sigma2_best, sigma2_best_unc, chi2, dof = _weighted_mean_chi2(sigma2, sigma_sigma2)
    p_val = _chi2_sf(chi2, dof) if dof > 0 else float("nan")

    return ShearExtractorReport(
        ell=ell[keep].astype(int),
        sigma2_per_ell=sigma2,
        sigma_sigma2_per_ell=sigma_sigma2,
        sigma2_best=sigma2_best,
        sigma2_best_uncertainty=sigma2_best_unc,
        chi2_independence=chi2,
        dof_independence=dof,
        p_value_independence=p_val,
        dropped_ells=dropped,
        bianchi_type=str(kl["bianchi_type"]),
        atlas_name=str(kl["atlas_name"]),
    )


def extract_from_atlas_entry(
    entry: AtlasEntry,
    c_ell_obs: np.ndarray,
    c_ell_lcdm: np.ndarray,
    sigma_c_ell: np.ndarray,
    config: Optional[ShearExtractorConfig] = None,
) -> ShearExtractorReport:
    """Adapt a `workspace.contracts.AtlasEntry` (kernel_name='K_ell') to the
    dict path.

    The bass_py W10-02 producer is expected to ship the K_ℓ kernel as an
    `AtlasEntry`; the observational arrays (``c_ell_obs`` / ``sigma_c_ell``)
    and the ΛCDM prediction (``c_ell_lcdm``) come from separate sources
    and are passed alongside.
    """
    if entry.kernel_name != "K_ell":
        raise ValueError(
            f"extract_from_atlas_entry expects kernel_name='K_ell'; got "
            f"{entry.kernel_name!r}"
        )
    kl_dict = {
        "ell": np.asarray(entry.ell),
        "C_ell_obs": np.asarray(c_ell_obs),
        "C_ell_lcdm": np.asarray(c_ell_lcdm),
        "K_ell": np.asarray(entry.kernel_values),
        "sigma_C_ell": np.asarray(sigma_c_ell),
        "bianchi_type": entry.bianchi_type,
        "atlas_name": entry.atlas_name,
        "generated_by": entry.generated_by,
        "git_commit": entry.git_commit,
        "config_hash": entry.config_hash,
        "domain_caveats": list(entry.domain_caveats),
    }
    return extract_from_kl_atlas(kl_dict, config=config)


# ---------------------------------------------------------------------------
# Certificate packaging
# ---------------------------------------------------------------------------


DIAGNOSTIC_ONLY_CAVEAT = (
    "diagnostic-only-until-bass_py-W10-02-V-gate (parent plan v3 §17.3 risk "
    "row 'HJ-01 K_ℓ atlas 의존성')"
)


def _bianchi_type_to_model_id(bianchi_type: str) -> str:
    """Map a K_ℓ atlas ``bianchi_type`` string to an A37.2 MODEL_ID.

    The bass_py K_ℓ atlas records the Bianchi class as a bare type suffix
    (``'I'``, ``'VIIh'``, ``'IX'``, ``…``) or the literal ``'FLRW'``. A37.2
    grammar v1 requires the emitted ``probe_name`` to be a `MODEL_ID`
    (``FLRW`` or ``Bianchi<I|II|…>`` or ``Tilted<Name>``). This helper
    prepends ``Bianchi`` when absent and returns the input unchanged for
    the two already-compliant prefixes.
    """
    if bianchi_type == "FLRW":
        return "FLRW"
    if bianchi_type.startswith("Bianchi") or bianchi_type.startswith("Tilted"):
        return bianchi_type
    return f"Bianchi{bianchi_type}"


def to_mio_certificate(
    report: ShearExtractorReport,
    *,
    domain_caveats: Optional[List[str]] = None,
    generated_by: str = "mio.extraction.hj01_shear v0.1-skeleton",
    input_data_hashes: Optional[List[str]] = None,
    config_hash: Optional[str] = None,
    htt_cross_check_suggested: Optional[Dict[str, str]] = None,
    config: Optional[ShearExtractorConfig] = None,
    has_covariance: bool = False,
    sky_support_status: SkySupportStatus = "partial",
    artifact_path: str = "artifacts/mio/mio_hj01_shear_extraction_v1.json",
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> MioCertificate:
    """Package a `ShearExtractorReport` into a `MioCertificate`.

    The certificate always carries the ``DIAGNOSTIC_ONLY_CAVEAT`` until
    the bass_py W10-02 V-gate signs off the K_ℓ atlas. Override is by
    explicit `domain_caveats` extension; this keeps the truth-certificate
    epistemic state honest per ch11 §11.14.2.
    """
    cfg = config if config is not None else ShearExtractorConfig()
    effective_band_sigma = cfg.effective_flrw_null_band_sigma(int(report.ell.size))

    departure = {
        "sigma2_best": float(report.sigma2_best),
        "sigma2_best_uncertainty": float(report.sigma2_best_uncertainty),
        "n_kept_ells": float(report.ell.size),
        "n_dropped_ells": float(len(report.dropped_ells)),
    }
    adequacy = {
        "ell_independence_p_lt_0p05": bool(
            report.dof_independence > 0
            and math.isfinite(report.p_value_independence)
            and report.p_value_independence < 0.05
        ),
        "flrw_consistent_within_band": bool(report.is_flrw_consistent(cfg)),
    }
    consistency = {
        "chi2_independence": float(report.chi2_independence),
        "dof_independence": float(report.dof_independence),
        "p_value_independence": float(report.p_value_independence),
        "ell_min": float(cfg.ell_min),
        "ell_max": float(cfg.ell_max),
        "flrw_null_band_sigma": float(cfg.flrw_null_band_sigma),
        "flrw_effective_null_band_sigma": float(effective_band_sigma),
        "bonferroni_adjust_flrw_band": bool(cfg.bonferroni_adjust_flrw_band),
        "flrw_familywise_alpha": float(cfg.flrw_familywise_alpha),
    }

    caveats = [DIAGNOSTIC_ONLY_CAVEAT]
    if domain_caveats:
        caveats.extend(domain_caveats)
    readiness = assess_mio_readiness(
        MioPrerequisites(
            requires_atlas=True,
            has_atlas=True,
            requires_covariance=True,
            has_covariance=has_covariance,
            requires_sky_support=True,
            sky_support_status=sky_support_status,
            eligible_for_production=True,
        )
    )

    return build_mio_certificate(
        report_type="shear_extraction",
        # A37.2 atlas_label singleton form: MODEL_ID only. The atlas_name
        # is preserved separately in the artefact JSON + generated_by.
        probe_name=_bianchi_type_to_model_id(report.bianchi_type),
        channel="TT_low_ell",
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by=generated_by,
        input_data_hashes=list(input_data_hashes) if input_data_hashes else [],
        config_hash=config_hash,
        htt_cross_check_suggested=htt_cross_check_suggested,
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
        readiness=readiness,
        artifact_id="mio.shear_extraction.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "shear_extraction",
            "channel": "TT_low_ell",
        },
    )


# ---------------------------------------------------------------------------
# Convenience class — the v1.2 plan asks for a `ShearExtractor` symbol.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ShearExtractor:
    """Lightweight wrapper bundling a config + extraction call.

    Equivalent to calling :func:`extract_from_kl_atlas` directly; exposed
    as a class so that downstream consumers can pre-configure once and
    reuse against multiple atlas snapshots.
    """

    config: ShearExtractorConfig = field(default_factory=ShearExtractorConfig)

    def extract(self, kl: Mapping[str, Any]) -> ShearExtractorReport:
        return extract_from_kl_atlas(kl, config=self.config)

    def certify(
        self,
        kl: Mapping[str, Any],
        **certificate_kwargs: Any,
    ) -> MioCertificate:
        report = self.extract(kl)
        return to_mio_certificate(report, config=self.config, **certificate_kwargs)


# ---------------------------------------------------------------------------
# Artefact emitter
# ---------------------------------------------------------------------------


ARTEFACT_FILENAME = "mio_hj01_shear_extraction_v1.json"


def emit_shear_extraction_artefact(
    out_path: Path,
    kl: Mapping[str, Any],
    *,
    config: Optional[ShearExtractorConfig] = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> dict:
    """Run the extraction and persist a JSON record.

    Filename must start with ``mio_`` (REG-02 — see W5 audit).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.name.startswith("mio_"):
        raise ValueError(
            f"artefact filename must start with 'mio_' (REG-02): got {out_path.name}"
        )

    cfg = config if config is not None else ShearExtractorConfig()
    report = extract_from_kl_atlas(kl, config=cfg)
    cert = to_mio_certificate(
        report,
        config=cfg,
        artifact_path=str(out_path),
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
    )

    payload = {
        "schema_version": "v1",
        "atlas_name": report.atlas_name,
        "bianchi_type": report.bianchi_type,
        "config": {
            "ell_min": cfg.ell_min,
            "ell_max": cfg.ell_max,
            "min_kernel_abs": cfg.min_kernel_abs,
            "flrw_null_band_sigma": cfg.flrw_null_band_sigma,
            "bonferroni_adjust_flrw_band": cfg.bonferroni_adjust_flrw_band,
            "flrw_familywise_alpha": cfg.flrw_familywise_alpha,
        },
        "per_ell": {
            "ell": report.ell.tolist(),
            "sigma2": report.sigma2_per_ell.tolist(),
            "sigma_sigma2": report.sigma_sigma2_per_ell.tolist(),
        },
        "summary": {
            "sigma2_best": report.sigma2_best,
            "sigma2_best_uncertainty": report.sigma2_best_uncertainty,
            "chi2_independence": report.chi2_independence,
            "dof_independence": report.dof_independence,
            "p_value_independence": report.p_value_independence,
            "dropped_ells": list(report.dropped_ells),
        },
        "certificate": certificate_to_payload(cert),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "ARTEFACT_FILENAME",
    "DIAGNOSTIC_ONLY_CAVEAT",
    "KL_ATLAS_REQUIRED_KEYS",
    "KL_ATLAS_OPTIONAL_KEYS",
    "ShearExtractor",
    "ShearExtractorConfig",
    "ShearExtractorReport",
    "_bianchi_type_to_model_id",
    "emit_shear_extraction_artefact",
    "extract_from_atlas_entry",
    "extract_from_kl_atlas",
    "to_mio_certificate",
    "validate_kl_atlas_schema",
]
