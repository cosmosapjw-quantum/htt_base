"""mio.coherence.redshift_binned — MIO-HJ-02b redshift-binned coherence.

INDEPENDENT_TRACKS_PLAN v1.3 §20 (Week 11 Days 3-4).
Parent: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md v3 §4.5.3.2 row 2
        (`redshift_binned.py` — z-bin별 probe direction + drift rate).

Builds on `mio.coherence.directional` (HJ-02a, Week 6). Where HJ-02a
tests whether the five standard direction probes point at a common
axis on the sky, HJ-02b tests whether that common-axis hypothesis is
**z-independent** — i.e. does the fitted axis drift between low-z
(CF4++), intermediate-z (CatWISE / Radio AGN), and the z ≈ 1100 CMB
bin?

The module is completely independent of any bass_py forward output
or HTT posterior: inputs are probe `(l, b, σ_cone, z_eff)` tuples
plus user-specified z bins. Outputs feed a `MioCertificate` with
`reduction_status='diagnostic-only'` — HJ-02b is never mergeable
into a posterior.

Null-test construction: the drift statistic is the sum of angular
separations between consecutive per-bin resultant axes. The p-value
for the "no drift" null is built by permuting the `z_eff` label
across probes (keeping directions fixed); a real directional-drift
signal should be rare under permutation.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

from common.sky_geometry import (
    angular_separation_matrix,
    lb_to_unitvec,
    spherical_mean,
)
from mio.interface.mio_certificate import build_mio_certificate
from workspace.contracts.mio_certificate import MioCertificate


# ---------------------------------------------------------------------------
# 1. Probe datatype + SSOT catalogue
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RedshiftBinnedProbe:
    """One direction probe with an effective redshift tag.

    Parameters
    ----------
    name
        Short identifier. One of the ``STANDARD_Z_PROBES`` names in production.
    l_deg, b_deg
        Galactic longitude / latitude (degrees) of the measured axis.
    sigma_cone_deg
        1-σ half-angle of the uncertainty cone.
    z_eff
        Effective redshift of the probe (where the direction is measured).
        CF4pp peculiar velocities ≈ 0.02; CatWISE / Radio AGN ≈ 0.5 – 1.5;
        CMB dipole / BiPoSH ≈ 1100 (surface of last scattering).
    weight
        Optional prefactor. Defaults to 1.0. Inverse-variance weighting
        uses ``weight / sigma_cone_deg ** 2``.
    """

    name: str
    l_deg: float
    b_deg: float
    sigma_cone_deg: float
    z_eff: float
    weight: float = 1.0


# Hardcoded 5-probe SSOT paralleling HJ-02a `STANDARD_PROBES`, with
# literature-anchored z_eff tags. References:
#   CF4pp   Tully+ 2023 CosmicFlows-4 (peculiar velocities, z ≈ 0.02)
#   CatWISE Secrest+ 2020 (mid-IR AGN, z ≈ 0.8)
#   Radio   NVSS + RACS AGN (z ≈ 1.0)
#   CMB     Planck 2018 dipole (surface of last scattering, z ≈ 1100)
#   BiPoSH  Planck preliminary BiPoSH (z ≈ 1100)
STANDARD_Z_PROBES: Tuple[RedshiftBinnedProbe, ...] = (
    RedshiftBinnedProbe(name="CF4pp",   l_deg=289.0,   b_deg=30.0,   sigma_cone_deg=15.0, z_eff=0.02),
    RedshiftBinnedProbe(name="CatWISE", l_deg=238.2,   b_deg=28.8,   sigma_cone_deg=6.0,  z_eff=0.8),
    RedshiftBinnedProbe(name="Radio",   l_deg=251.0,   b_deg=38.0,   sigma_cone_deg=10.0, z_eff=1.0),
    RedshiftBinnedProbe(name="CMB",     l_deg=264.021, b_deg=48.253, sigma_cone_deg=0.5,  z_eff=1100.0),
    RedshiftBinnedProbe(name="BiPoSH",  l_deg=220.0,   b_deg=65.0,   sigma_cone_deg=20.0, z_eff=1100.0),
)


# Three-bin default: low-z local flow, intermediate-z AGN, surface-of-
# last-scattering. The upper bound of the final bin is inclusive.
DEFAULT_Z_BINS: Tuple[Tuple[float, float], ...] = (
    (0.0, 0.1),
    (0.1, 10.0),
    (100.0, 2000.0),
)


# ---------------------------------------------------------------------------
# 2. Binning + per-bin resultant
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ZBinResult:
    """Resultant-vector summary inside one z bin."""

    z_min: float
    z_max: float
    probe_names: Tuple[str, ...]
    l_deg: float
    b_deg: float
    resultant_R: float
    n_probes: int


def _probe_weights(probes: Sequence[RedshiftBinnedProbe]) -> np.ndarray:
    sig = np.array([p.sigma_cone_deg for p in probes], dtype=float)
    w = np.array([p.weight for p in probes], dtype=float)
    if np.any(sig <= 0):
        raise ValueError("sigma_cone_deg must be strictly positive")
    return w / (sig * sig)


def assign_probes_to_bins(
    probes: Sequence[RedshiftBinnedProbe],
    bins: Sequence[Tuple[float, float]] = DEFAULT_Z_BINS,
) -> List[List[RedshiftBinnedProbe]]:
    """Group probes into user-specified z bins.

    The lower bound is inclusive; the upper bound is exclusive except
    for the final bin which is inclusive on both sides (so that a
    probe at ``z_eff = z_max_last`` still lands in the final bin
    rather than being silently dropped).
    """
    if not bins:
        raise ValueError("bins must be a non-empty sequence of (z_min, z_max) tuples")
    for lo, hi in bins:
        if not (hi > lo):
            raise ValueError(f"z bin upper bound must exceed lower: got ({lo}, {hi})")
    out: List[List[RedshiftBinnedProbe]] = [[] for _ in bins]
    last_idx = len(bins) - 1
    for p in probes:
        for i, (lo, hi) in enumerate(bins):
            if i == last_idx:
                if lo <= p.z_eff <= hi:
                    out[i].append(p)
                    break
            else:
                if lo <= p.z_eff < hi:
                    out[i].append(p)
                    break
    return out


def per_bin_resultants(
    probes: Sequence[RedshiftBinnedProbe],
    bins: Sequence[Tuple[float, float]] = DEFAULT_Z_BINS,
) -> List[ZBinResult]:
    """Inverse-variance weighted spherical mean within each z bin.

    Empty bins are returned with ``n_probes=0`` and NaN direction; they
    contribute no entries to the drift statistic.
    """
    grouped = assign_probes_to_bins(probes, bins)
    results: List[ZBinResult] = []
    for (lo, hi), probes_in in zip(bins, grouped):
        if len(probes_in) == 0:
            results.append(
                ZBinResult(
                    z_min=float(lo), z_max=float(hi),
                    probe_names=tuple(),
                    l_deg=float("nan"), b_deg=float("nan"),
                    resultant_R=0.0, n_probes=0,
                )
            )
            continue
        l = np.array([p.l_deg for p in probes_in], dtype=float)
        b = np.array([p.b_deg for p in probes_in], dtype=float)
        w = _probe_weights(probes_in)
        out = spherical_mean(l, b, w)
        results.append(
            ZBinResult(
                z_min=float(lo), z_max=float(hi),
                probe_names=tuple(p.name for p in probes_in),
                l_deg=float(out["l_deg"]),
                b_deg=float(out["b_deg"]),
                resultant_R=float(out["resultant_R"]),
                n_probes=len(probes_in),
            )
        )
    return results


# ---------------------------------------------------------------------------
# 3. Drift statistic + permutation p-value
# ---------------------------------------------------------------------------


def _populated_axes(bin_results: Sequence[ZBinResult]) -> np.ndarray:
    """Return Cartesian axes (M, 3) for the M bins with ≥ 1 probe."""
    keep = [r for r in bin_results if r.n_probes > 0 and np.isfinite(r.l_deg)]
    if not keep:
        return np.empty((0, 3), dtype=float)
    l = np.array([r.l_deg for r in keep], dtype=float)
    b = np.array([r.b_deg for r in keep], dtype=float)
    return lb_to_unitvec(l, b)


def total_drift_deg(bin_results: Sequence[ZBinResult]) -> float:
    """Sum of angular separations between consecutive populated bins."""
    axes = _populated_axes(bin_results)
    if axes.shape[0] < 2:
        return 0.0
    # Pairwise between consecutive axes only.
    cos_sep = np.clip(np.sum(axes[:-1] * axes[1:], axis=-1), -1.0, 1.0)
    return float(np.sum(np.rad2deg(np.arccos(cos_sep))))


def pairwise_bin_separations(bin_results: Sequence[ZBinResult]) -> np.ndarray:
    """M×M angular separation matrix across populated z bins (degrees)."""
    axes = _populated_axes(bin_results)
    if axes.shape[0] == 0:
        return np.zeros((0, 0))
    # Reuse COMMON-A helper for consistency with HJ-02a output.
    keep = [r for r in bin_results if r.n_probes > 0 and np.isfinite(r.l_deg)]
    l = np.array([r.l_deg for r in keep], dtype=float)
    b = np.array([r.b_deg for r in keep], dtype=float)
    return angular_separation_matrix(l, b)


def drift_pvalue(
    probes: Sequence[RedshiftBinnedProbe],
    bins: Sequence[Tuple[float, float]] = DEFAULT_Z_BINS,
    n_mock: int = 5_000,
    rng: Optional[np.random.Generator] = None,
) -> float:
    """Permutation p-value for the 'no z-drift' null hypothesis.

    Holds the N probe directions fixed and permutes the z_eff labels
    across them; for each permutation, recomputes the per-bin resultant
    axes and the total-drift statistic. Returns the fraction of
    permutations whose drift meets or exceeds the observed drift.

    Rationale: under the null "axis direction is independent of the
    probe's z_eff", any label permutation is equally plausible; a
    genuine z-drift signal should be rare in the permutation distribution.
    """
    if n_mock < 1:
        raise ValueError("n_mock must be >= 1")
    if rng is None:
        rng = np.random.default_rng()
    if len(probes) < 2:
        # A single probe cannot drift; call it fully consistent with the null.
        return 1.0

    observed = total_drift_deg(per_bin_resultants(probes, bins))

    z_labels = np.array([p.z_eff for p in probes], dtype=float)
    count = 0
    for _ in range(n_mock):
        perm = rng.permutation(z_labels)
        shuffled = [
            RedshiftBinnedProbe(
                name=p.name, l_deg=p.l_deg, b_deg=p.b_deg,
                sigma_cone_deg=p.sigma_cone_deg, z_eff=float(z),
                weight=p.weight,
            )
            for p, z in zip(probes, perm)
        ]
        mock_drift = total_drift_deg(per_bin_resultants(shuffled, bins))
        if mock_drift >= observed:
            count += 1
    return (count + 1) / (n_mock + 1)


# ---------------------------------------------------------------------------
# 4. MioCertificate exit
# ---------------------------------------------------------------------------


def to_mio_certificate(
    probes: Sequence[RedshiftBinnedProbe],
    bin_results: Sequence[ZBinResult],
    p_drift: float,
    total_drift: float,
    *,
    domain_caveats: Optional[List[str]] = None,
    generated_by: str = "mio.coherence.redshift_binned v0.1",
    input_data_hashes: Optional[List[str]] = None,
    config_hash: Optional[str] = None,
    htt_cross_check_suggested: Optional[dict] = None,
) -> MioCertificate:
    """Package z-binned-coherence results into a ``MioCertificate``.

    Departure variables carry the total inter-bin drift (degrees) and the
    number of populated bins. Adequacy indicators flag whether the p-value
    is below 0.01 / 0.05 thresholds. Consistency metrics expose the per-bin
    resultant R and the probe counts. ``reduction_status`` is hard-pinned
    to ``'diagnostic-only'``: HJ-02b never merges into a posterior.
    """
    n_populated = sum(1 for r in bin_results if r.n_probes > 0)
    mean_R = (
        float(np.mean([r.resultant_R for r in bin_results if r.n_probes > 0]))
        if n_populated > 0
        else 0.0
    )
    departure = {
        "total_drift_deg": float(total_drift),
        "n_populated_bins": float(n_populated),
        "n_probes": float(len(probes)),
    }
    adequacy = {
        "drift_p_lt_0p01": bool(p_drift < 0.01),
        "drift_p_lt_0p05": bool(p_drift < 0.05),
    }
    consistency = {
        "drift_pvalue": float(p_drift),
        "mean_per_bin_resultant_R": mean_R,
        "n_bins_total": float(len(bin_results)),
    }
    caveats = list(domain_caveats) if domain_caveats is not None else []

    return build_mio_certificate(
        report_type="redshift_binned_coherence",
        probe_name="+".join(p.name for p in probes),
        channel="dipole_vs_z",
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by=generated_by,
        input_data_hashes=list(input_data_hashes) if input_data_hashes else [],
        htt_cross_check_suggested=htt_cross_check_suggested,
        config_hash=config_hash,
    )


# ---------------------------------------------------------------------------
# 5. Artefact emitter
# ---------------------------------------------------------------------------


ARTEFACT_FILENAME = "mio_redshift_coherence_v1.json"


def emit_redshift_coherence_artefact(
    out_path: Path,
    probes: Sequence[RedshiftBinnedProbe] = STANDARD_Z_PROBES,
    bins: Sequence[Tuple[float, float]] = DEFAULT_Z_BINS,
    *,
    n_mock: int = 5_000,
    rng: Optional[np.random.Generator] = None,
) -> dict:
    """Run the full analysis and persist JSON.

    Filename must start with ``mio_`` per REG-02 (v3 §12.2bis).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.name.startswith("mio_"):
        raise ValueError(
            f"artefact filename must start with 'mio_' (REG-02): got {out_path.name}"
        )

    if rng is None:
        rng = np.random.default_rng(seed=20260419)

    bin_results = per_bin_resultants(probes, bins)
    total_drift = total_drift_deg(bin_results)
    p_drift = drift_pvalue(probes, bins, n_mock=n_mock, rng=rng)
    sep = pairwise_bin_separations(bin_results)

    cert = to_mio_certificate(
        probes, bin_results, p_drift=p_drift, total_drift=total_drift,
    )

    payload = {
        "schema_version": "v1",
        "probes": [asdict(p) for p in probes],
        "bins": [{"z_min": float(lo), "z_max": float(hi)} for (lo, hi) in bins],
        "bin_results": [
            {
                "z_min": r.z_min, "z_max": r.z_max,
                "probe_names": list(r.probe_names),
                "l_deg": None if not np.isfinite(r.l_deg) else float(r.l_deg),
                "b_deg": None if not np.isfinite(r.b_deg) else float(r.b_deg),
                "resultant_R": float(r.resultant_R),
                "n_probes": int(r.n_probes),
            }
            for r in bin_results
        ],
        "total_drift_deg": float(total_drift),
        "drift_pvalue": float(p_drift),
        "n_mock": int(n_mock),
        "pairwise_bin_separations_deg": sep.tolist(),
        "certificate": {
            "report_type": cert.report_type,
            "probe_name": cert.probe_name,
            "channel": cert.channel,
            "departure_variables": cert.departure_variables,
            "adequacy_indicators": cert.adequacy_indicators,
            "consistency_metrics": cert.consistency_metrics,
            "domain_caveats": cert.domain_caveats,
            "reduction_status": cert.reduction_status,
            "generated_by": cert.generated_by,
            "git_commit": cert.git_commit,
            "config_hash": cert.config_hash,
        },
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "RedshiftBinnedProbe",
    "STANDARD_Z_PROBES",
    "DEFAULT_Z_BINS",
    "ZBinResult",
    "ARTEFACT_FILENAME",
    "assign_probes_to_bins",
    "per_bin_resultants",
    "total_drift_deg",
    "pairwise_bin_separations",
    "drift_pvalue",
    "to_mio_certificate",
    "emit_redshift_coherence_artefact",
]
