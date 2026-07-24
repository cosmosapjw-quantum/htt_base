"""mio.coherence.directional — MIO-HJ-02a directional coherence.

INDEPENDENT_TRACKS_PLAN v1.2 §12.3 (Week 6 Day 3-5).
Parent: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md v3 §4.5.3.2 (HJ-02).

This module is the single *completely independent* MIO diagnostic in
v3 §16.2 — it needs neither a bass_py forward K_ell atlas nor an HTT
posterior. It answers one question on data alone: do the five
independent directional probes (CMB / CatWISE / Radio / CF4++ / BiPoSH)
point to a common axis on the sky, or are they mutually isotropic?

The computation is:

  * Resultant vector of the 5 unit-direction probes weighted by
    inverse-variance (1 / sigma_cone²).
  * Monte-Carlo p-value for the null hypothesis of isotropy: the
    fraction of isotropic mocks whose resultant length |R| meets or
    exceeds the observed |R|.
  * Pairwise separation matrix (deg) — literature cross-check.
  * χ² for the common-axis hypothesis: Σ (Δ_i / σ_i)² with Δ_i the
    angular separation between probe i and the fitted axis.

Outputs are packaged into a ``workspace.contracts.MioCertificate`` via
the Day-2 generator API. G19 hard separation: no posterior is ever
produced, and the certificate refuses any ``as_posterior_bundle``
request (NotImplementedError).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

from common.sky_geometry import (
    angular_separation_matrix,
    lb_to_unitvec,
    spherical_mean,
    unitvec_to_lb,
)
from mio.interface.manifest import (
    MioPrerequisites,
    SkySupportStatus,
    assess_mio_readiness,
)
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from mio.interface.sigma_cone_provenance import placeholder_caveats_for
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.tsc_overlay import TscAdequacyOverlay


# ---------------------------------------------------------------------------
# Probe datatype
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DirectionalProbe:
    """One measured preferred-axis probe.

    Parameters
    ----------
    name
        Short identifier. One of the ``STANDARD_PROBES`` names in production.
    l_deg, b_deg
        Galactic longitude / latitude (degrees) of the measured axis.
    sigma_cone_deg
        1-σ half-angle of the uncertainty cone around (l_deg, b_deg).
    weight
        Optional extra prefactor. Defaults to 1.0. The actual direction-
        weighting used by :func:`resultant_vector` is
        ``weight / sigma_cone_deg**2`` (inverse-variance), so ``weight``
        is only needed for intentional down-weighting.
    """

    name: str
    l_deg: float
    b_deg: float
    sigma_cone_deg: float
    weight: float = 1.0


# Hardcoded 5-probe SSOT per plan §12.3.
# Literature anchors:
#   CMB      Planck 2018 dipole         (Planck 2018 VIII; l, b ≈ 264.02°, 48.25°)
#   CatWISE  Secrest+2020               (l, b ≈ 238.2°,  28.8°)
#   Radio    NVSS+RACS combined         (l, b ≈ 251°,    38°)
#   CF4pp    Tully+2023 CosmicFlows-4   (l, b ≈ 289°,    30°)
#   BiPoSH   Preliminary Planck BiPoSH  (l, b ≈ 220°,    65°)
STANDARD_PROBES: Tuple[DirectionalProbe, ...] = (
    DirectionalProbe(name="CMB",     l_deg=264.021, b_deg=48.253, sigma_cone_deg=0.5),
    DirectionalProbe(name="CatWISE", l_deg=238.2,   b_deg=28.8,   sigma_cone_deg=6.0),
    DirectionalProbe(name="Radio",   l_deg=251.0,   b_deg=38.0,   sigma_cone_deg=10.0),
    DirectionalProbe(name="CF4pp",   l_deg=289.0,   b_deg=30.0,   sigma_cone_deg=15.0),
    DirectionalProbe(name="BiPoSH",  l_deg=220.0,   b_deg=65.0,   sigma_cone_deg=20.0),
)


# ---------------------------------------------------------------------------
# Core statistics
# ---------------------------------------------------------------------------


def _probe_weights(probes: Sequence[DirectionalProbe]) -> np.ndarray:
    """Inverse-variance-scaled weights used everywhere as the SSOT."""
    sig = np.array([p.sigma_cone_deg for p in probes], dtype=float)
    w = np.array([p.weight for p in probes], dtype=float)
    if np.any(sig <= 0):
        raise ValueError("sigma_cone_deg must be strictly positive")
    if not np.all(np.isfinite(w)) or np.any(w < 0):
        raise ValueError("probe weights must be finite and nonnegative")
    return w / (sig * sig)


def resultant_vector(probes: Sequence[DirectionalProbe]) -> Tuple[float, float, float]:
    """Inverse-variance weighted spherical mean of the probes.

    Returns
    -------
    tuple
        ``(l_best_deg, b_best_deg, R)`` with ``R ∈ [0, 1]``. When the
        probes cancel (``R ≈ 0``) the direction is flagged as NaN.
    """
    if len(probes) == 0:
        raise ValueError("resultant_vector requires at least one probe")
    l = np.array([p.l_deg for p in probes], dtype=float)
    b = np.array([p.b_deg for p in probes], dtype=float)
    w = _probe_weights(probes)
    out = spherical_mean(l, b, w)
    return out["l_deg"], out["b_deg"], out["resultant_R"]


def pairwise_separations(probes: Sequence[DirectionalProbe]) -> np.ndarray:
    """N×N angular separation matrix (degrees) with zero diagonal."""
    l = np.array([p.l_deg for p in probes], dtype=float)
    b = np.array([p.b_deg for p in probes], dtype=float)
    return angular_separation_matrix(l, b)


def coherence_chi2(probes: Sequence[DirectionalProbe]) -> Tuple[float, int]:
    """χ² test for the "all probes share a common axis" hypothesis.

    Returns
    -------
    tuple
        ``(chi2, dof)``. ``dof = max(N - 2, 1)`` (two angular
        coordinates fitted from the probes).
    """
    if len(probes) < 2:
        raise ValueError("coherence_chi2 requires at least two probes")
    l_star, b_star, r_val = resultant_vector(probes)
    if not np.isfinite(l_star) or not np.isfinite(b_star):
        # Fully canceled probe set → return +inf χ² (no common axis).
        return float("inf"), max(len(probes) - 2, 1)
    axis = lb_to_unitvec(np.array(l_star), np.array(b_star))
    vecs = lb_to_unitvec(
        np.array([p.l_deg for p in probes], dtype=float),
        np.array([p.b_deg for p in probes], dtype=float),
    )
    cos_sep = np.clip(vecs @ axis, -1.0, 1.0)
    sep_deg = np.rad2deg(np.arccos(cos_sep))
    sig = np.array([p.sigma_cone_deg for p in probes], dtype=float)
    chi2 = float(np.sum((sep_deg / sig) ** 2))
    return chi2, max(len(probes) - 2, 1)


def _sample_isotropic_unit_vectors(n: int, rng: np.random.Generator) -> np.ndarray:
    """Draw ``n`` unit vectors uniformly on S²."""
    u = rng.uniform(-1.0, 1.0, size=n)
    phi = rng.uniform(0.0, 2 * np.pi, size=n)
    s = np.sqrt(1.0 - u * u)
    return np.stack([s * np.cos(phi), s * np.sin(phi), u], axis=-1)


def _observed_resultant_R(probes: Sequence[DirectionalProbe]) -> float:
    return resultant_vector(probes)[2]


def isotropy_pvalue(
    probes: Sequence[DirectionalProbe],
    n_mock: int = 10_000,
    rng: Optional[np.random.Generator] = None,
) -> float:
    """Monte-Carlo p-value for the isotropy null.

    Draws ``n_mock`` sets of N isotropic unit vectors, forms the same
    inverse-variance weighted spherical mean, and returns the fraction
    whose resultant length meets or exceeds the observed ``|R|``.
    """
    if n_mock < 1:
        raise ValueError("n_mock must be >= 1")
    if rng is None:
        rng = np.random.default_rng()

    observed_R = _observed_resultant_R(probes)
    n = len(probes)
    w = _probe_weights(probes)
    w_col = w[:, None]
    wsum = float(w.sum())
    if wsum <= 0:
        raise ValueError("probe weight sum must be > 0")

    count = 0
    # Loop in chunks to keep memory bounded even for n_mock ~ 1e6.
    chunk = 2048
    drawn = 0
    while drawn < n_mock:
        m = min(chunk, n_mock - drawn)
        # Shape (m, n, 3)
        vecs = np.stack(
            [_sample_isotropic_unit_vectors(n, rng) for _ in range(m)],
            axis=0,
        )
        # Weighted mean per mock
        mean_vec = (vecs * w_col).sum(axis=1) / wsum
        r_vals = np.linalg.norm(mean_vec, axis=-1)
        count += int(np.sum(r_vals >= observed_R))
        drawn += m
    # Lidstone-type additive smoothing to avoid 0 on tiny samples.
    return (count + 1) / (n_mock + 1)


def to_mio_certificate(
    probes: Sequence[DirectionalProbe],
    p_iso: float,
    resultant: Tuple[float, float, float],
    *,
    chi2_stat: Optional[Tuple[float, int]] = None,
    domain_caveats: Optional[List[str]] = None,
    generated_by: str = "mio.coherence.directional v0.1",
    input_data_hashes: Optional[List[str]] = None,
    config_hash: Optional[str] = None,
    htt_cross_check_suggested: Optional[dict] = None,
    has_covariance: bool = False,
    has_null_mocks: bool = False,
    sky_support_status: SkySupportStatus = "partial",
    artifact_path: str = "artifacts/mio/mio_directional_coherence.json",
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> MioCertificate:
    """Package directional-coherence results into a `MioCertificate`.

    This is the single exit point from the module; it never exposes
    posterior samples or marginals — only diagnostic departure
    variables (resultant_R, fitted axis) + adequacy indicators
    (isotropy_p_lt_0p01) + consistency metrics (χ² per dof).
    """
    l_star, b_star, r_star = resultant
    if chi2_stat is None:
        chi2_stat = coherence_chi2(probes)
    chi2, dof = chi2_stat
    per_dof = chi2 / dof if dof > 0 else float("inf")

    departure = {
        "resultant_R": float(r_star),
        "l_best_deg": float(l_star) if np.isfinite(l_star) else float("nan"),
        "b_best_deg": float(b_star) if np.isfinite(b_star) else float("nan"),
        "n_probes": float(len(probes)),
    }
    adequacy = {
        "isotropy_p_lt_0p01": bool(p_iso < 0.01),
        "isotropy_p_lt_0p05": bool(p_iso < 0.05),
        "covariance_ready": bool(has_covariance),
        "null_mocks_ready": bool(has_null_mocks),
        "sky_support_complete": bool(sky_support_status == "complete"),
    }
    consistency = {
        "isotropy_pvalue": float(p_iso),
        "coherence_chi2": float(chi2),
        "coherence_dof": float(dof),
        "coherence_chi2_per_dof": float(per_dof),
    }
    caveats = list(domain_caveats) if domain_caveats is not None else []
    for placeholder in placeholder_caveats_for(p.name for p in probes):
        if placeholder not in caveats:
            caveats.append(placeholder)
    readiness = assess_mio_readiness(
        MioPrerequisites(
            requires_covariance=True,
            has_covariance=has_covariance,
            requires_null_mocks=True,
            has_null_mocks=has_null_mocks,
            requires_sky_support=True,
            sky_support_status=sky_support_status,
            eligible_for_production=True,
        )
    )
    status_metadata = {
        "covariance_status": "available" if has_covariance else "missing",
        "null_mock_status": "available" if has_null_mocks else "missing",
        "sky_support_status": sky_support_status,
        "transfer_source": "none",
        "direction_convention": "oriented_unit_direction",
        "weighting_convention": "diagonal_sigma_cone_inverse_variance",
        "cross_probe_covariance_status": (
            "available" if has_covariance else "not_attached"
        ),
        "null_calibration_status": (
            "matched_null_mocks_available"
            if has_null_mocks
            else "toy_isotropy_mc_unmatched"
        ),
        "claim_scope": "diagnostic_only_directional_coherence",
        "required_gates": list(readiness.required_gates),
        "passed_gates": list(readiness.passed_gates),
        "failed_gates": list(readiness.failed_gates),
        "production_status": readiness.production_status,
        "claim_tier": readiness.claim_tier,
        "public_grade_label": readiness.public_grade_label,
    }

    return build_mio_certificate(
        report_type="directional_coherence",
        # A37.2 rule 2: bundle form is alphabetically sorted for stable cross-cert keys.
        probe_name="+".join(sorted(p.name for p in probes)),
        channel="dipole",
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by=generated_by,
        input_data_hashes=list(input_data_hashes) if input_data_hashes else [],
        htt_cross_check_suggested=htt_cross_check_suggested,
        config_hash=config_hash,
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
        readiness=readiness,
        artifact_id="mio.directional_coherence.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "directional_coherence",
            "channel": "dipole",
            "certificate_status_metadata": status_metadata,
        },
    )


# ---------------------------------------------------------------------------
# Artefact emitter
# ---------------------------------------------------------------------------

ARTEFACT_FILENAME = "mio_directional_coherence.json"


def emit_directional_coherence_artefact(
    out_path: Path,
    probes: Sequence[DirectionalProbe] = STANDARD_PROBES,
    *,
    n_mock: int = 10_000,
    rng: Optional[np.random.Generator] = None,
    has_covariance: bool = False,
    has_null_mocks: bool = False,
    sky_support_status: SkySupportStatus = "partial",
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> dict:
    """Run the full analysis and persist JSON.

    Returns the dict that was written so callers can inspect it.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.name.startswith("mio_"):
        raise ValueError(
            f"artefact filename must start with 'mio_' (REG-02): got {out_path.name}"
        )

    if rng is None:
        rng = np.random.default_rng(seed=20260419)

    resultant = resultant_vector(probes)
    p_iso = isotropy_pvalue(probes, n_mock=n_mock, rng=rng)
    chi2_stat = coherence_chi2(probes)
    sep = pairwise_separations(probes)

    cert = to_mio_certificate(
        probes,
        p_iso=p_iso,
        resultant=resultant,
        chi2_stat=chi2_stat,
        has_covariance=has_covariance,
        has_null_mocks=has_null_mocks,
        sky_support_status=sky_support_status,
        artifact_path=str(out_path),
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
    )

    payload = {
        "schema_version": "v1",
        "probes": [asdict(p) for p in probes],
        "resultant": {
            "l_deg": float(resultant[0]) if np.isfinite(resultant[0]) else None,
            "b_deg": float(resultant[1]) if np.isfinite(resultant[1]) else None,
            "R": float(resultant[2]),
        },
        "isotropy_pvalue": float(p_iso),
        "n_mock": int(n_mock),
        "coherence": {
            "chi2": float(chi2_stat[0]),
            "dof": int(chi2_stat[1]),
            "chi2_per_dof": float(chi2_stat[0] / chi2_stat[1]) if chi2_stat[1] > 0 else None,
        },
        "pairwise_separations_deg": sep.tolist(),
        "certificate": certificate_to_payload(cert),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "DirectionalProbe",
    "STANDARD_PROBES",
    "ARTEFACT_FILENAME",
    "resultant_vector",
    "pairwise_separations",
    "coherence_chi2",
    "isotropy_pvalue",
    "to_mio_certificate",
    "emit_directional_coherence_artefact",
]
