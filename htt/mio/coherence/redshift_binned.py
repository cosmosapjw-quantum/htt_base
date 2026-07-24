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
across probes (keeping directions fixed); it is a descriptive
label-exchangeability tail fraction unless matched null/mock metadata
is attached.
"""
from __future__ import annotations

import itertools
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np

from common.sky_geometry import (
    angular_separation_matrix,
    lb_to_unitvec,
    spherical_mean,
)
from mio.interface.manifest import (
    MioReadiness,
    MioPrerequisites,
    SkySupportStatus,
    assess_mio_readiness,
)
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from mio.interface.sigma_cone_provenance import placeholder_caveats_for
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.tsc_overlay import TscAdequacyOverlay


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


DEFAULT_REDSHIFT_DEPTH_BIN_CAVEAT = (
    "Redshift-bin metadata supports MIO diagnostic coherence and G_F bridge "
    "bookkeeping only; it is not HTT inference or solver validation."
)

_ALLOWED_COVARIANCE_STATUSES = frozenset(
    {
        "mock_covariance",
        "matched_calibrated_covariance",
        "diagnostic_unmatched_covariance",
    }
)
_ALLOWED_NULL_MOCK_STATUSES = frozenset(
    {
        "mock_calibrated",
        "matched_calibrated_null",
        "diagnostic_unmatched_null",
    }
)
_ALLOWED_STATISTICAL_CALIBRATION_STATUSES = frozenset(
    {
        "matched_calibrated",
        "diagnostic_unmatched",
    }
)
_ALLOWED_BIN_SKY_SUPPORT_STATUSES = frozenset({"partial", "complete"})
_ALLOWED_BIN_MASK_STATUSES = frozenset({"partial", "complete", "masked_with_hash"})
_FORBIDDEN_METADATA_TERMS = (
    "probability_anisotropy_true",
    "anisotropy is true",
    "truth probability",
    "posterior",
    "posterior odds",
    "evidence",
    "likelihood",
    "bayes factor",
    "model weight",
    "htt evidence",
    "mio posterior",
    "truth certificate",
    "certifies truth",
    "model-independent proof",
    "global " + "tilt",
    "family_id",
    "family identification",
    "family identified",
    "family classification",
    "geometry",
    "class label",
    "class-label",
    "solver result",
    "native solver result",
    "external transfer " + "validated as " + "native",
    "validated as native",
    "native_validated",
    "morphology compatibility",
)


def _normalise_claim_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _scan_reserved_language(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _scan_reserved_language(key, name)
            _scan_reserved_language(item, name)
        return
    if isinstance(value, (str, bytes)):
        text = _normalise_claim_text(value)
        for term in _FORBIDDEN_METADATA_TERMS:
            if _normalise_claim_text(term) in text:
                raise ValueError(
                    f"{name} must not use reserved redshift-bin metadata "
                    f"language: {term}"
                )
        return
    if isinstance(value, Sequence):
        for item in value:
            _scan_reserved_language(item, name)


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} must be non-empty")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _finite_float(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _positive_int(value: object, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if number <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return number


def _plain_metadata(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_metadata(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_plain_metadata(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("metadata floats must be finite")
        return value
    if isinstance(value, (int, bool)) or value is None:
        return value
    raise TypeError(f"metadata value {value!r} is not JSON-compatible")


def _normalise_metadata(
    metadata: Mapping[str, object] | None,
    name: str,
) -> dict[str, Any]:
    if metadata is None:
        raise ValueError(f"{name} is required")
    if not isinstance(metadata, Mapping):
        raise ValueError(f"{name} must be a mapping")
    try:
        result = _plain_metadata(dict(metadata))
        json.dumps(result, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc
    if not isinstance(result, dict) or not result:
        raise ValueError(f"{name} must be a non-empty mapping")
    _scan_reserved_language(result, name)
    return result


def _normalise_optional_metadata(
    metadata: Mapping[str, object] | None,
    name: str,
) -> dict[str, Any] | None:
    if metadata is None:
        return None
    return _normalise_metadata(metadata, name)


def _require_metadata_key(metadata: Mapping[str, object], key: str, name: str) -> None:
    _non_empty(metadata.get(key), f"{name}.{key}")


def _require_status_value(
    value: object,
    name: str,
    allowed: frozenset[str],
) -> str:
    status = _non_empty(value, name)
    if status not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {allowed_text}")
    return status


@dataclass(frozen=True)
class RedshiftDepthBinMetadata:
    """Per-redshift-bin metadata required for production-grade coherence gates.

    The payload is intentionally metadata-only: it records the covariance,
    null, selection, and optional G_F bridge provenance needed to decide whether
    the redshift-binned coherence certificate is descriptive fallback or
    production-candidate diagnostic output.
    """

    bin_id: str
    z_min: float
    z_max: float
    selection_rule: str
    selection_hash: str
    bin_assignment_hash: str
    sky_support_status: str
    mask_status: str
    covariance_status: str
    covariance_metadata: Mapping[str, object]
    null_mock_status: str
    null_metadata: Mapping[str, object]
    sample_count: int
    g_f_payload_ref: str | None = None
    g_f_bridge_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(
        default_factory=lambda: (DEFAULT_REDSHIFT_DEPTH_BIN_CAVEAT,)
    )

    def __post_init__(self) -> None:
        bin_id = _non_empty(self.bin_id, "bin_id")
        z_min = _finite_float(self.z_min, "z_min")
        z_max = _finite_float(self.z_max, "z_max")
        if z_max <= z_min:
            raise ValueError("redshift-bin metadata requires z_max > z_min")
        selection_rule = _non_empty(self.selection_rule, "selection_rule")
        selection_hash = _non_empty(self.selection_hash, "selection_hash")
        bin_assignment_hash = _non_empty(
            self.bin_assignment_hash,
            "bin_assignment_hash",
        )
        sky_support_status = _non_empty(
            self.sky_support_status,
            "sky_support_status",
        )
        if sky_support_status not in _ALLOWED_BIN_SKY_SUPPORT_STATUSES:
            allowed = ", ".join(sorted(_ALLOWED_BIN_SKY_SUPPORT_STATUSES))
            raise ValueError(f"sky_support_status must be one of: {allowed}")
        mask_status = _non_empty(self.mask_status, "mask_status")
        if mask_status not in _ALLOWED_BIN_MASK_STATUSES:
            allowed = ", ".join(sorted(_ALLOWED_BIN_MASK_STATUSES))
            raise ValueError(f"mask_status must be one of: {allowed}")
        covariance_status = _require_status_value(
            self.covariance_status,
            "covariance_status",
            _ALLOWED_COVARIANCE_STATUSES,
        )
        covariance_metadata = _normalise_metadata(
            self.covariance_metadata,
            "covariance_metadata",
        )
        _require_metadata_key(
            covariance_metadata,
            "covariance_hash",
            "covariance_metadata",
        )
        _require_metadata_key(covariance_metadata, "estimator", "covariance_metadata")
        if "shape" not in covariance_metadata:
            raise ValueError("covariance_metadata.shape is required")
        _require_status_value(
            covariance_metadata.get("calibration_status"),
            "covariance_metadata.calibration_status",
            _ALLOWED_STATISTICAL_CALIBRATION_STATUSES,
        )
        null_mock_status = _require_status_value(
            self.null_mock_status,
            "null_mock_status",
            _ALLOWED_NULL_MOCK_STATUSES,
        )
        null_metadata = _normalise_metadata(self.null_metadata, "null_metadata")
        _require_metadata_key(null_metadata, "mock_bank_hash", "null_metadata")
        _require_status_value(
            null_metadata.get("calibration_status"),
            "null_metadata.calibration_status",
            _ALLOWED_STATISTICAL_CALIBRATION_STATUSES,
        )
        sample_count = _positive_int(self.sample_count, "sample_count")
        g_f_payload_ref = (
            None
            if self.g_f_payload_ref is None
            else _non_empty(self.g_f_payload_ref, "g_f_payload_ref")
        )
        g_f_bridge_metadata = _normalise_optional_metadata(
            self.g_f_bridge_metadata,
            "g_f_bridge_metadata",
        )
        if g_f_bridge_metadata is not None:
            if g_f_payload_ref is None:
                raise ValueError(
                    "g_f_bridge_metadata requires a non-empty g_f_payload_ref"
                )
            _require_metadata_key(
                g_f_bridge_metadata,
                "g_f_payload_ref",
                "g_f_bridge_metadata",
            )
            if str(g_f_bridge_metadata["g_f_payload_ref"]) != g_f_payload_ref:
                raise ValueError(
                    "g_f_bridge_metadata.g_f_payload_ref must match "
                    "g_f_payload_ref"
                )
            _require_metadata_key(
                g_f_bridge_metadata,
                "g_f_payload_hash",
                "g_f_bridge_metadata",
            )
            if str(g_f_bridge_metadata.get("score_label")) != "G_F":
                raise ValueError("g_f_bridge_metadata.score_label must be G_F")
            if str(g_f_bridge_metadata.get("claim_tier")) != "diagnostic_only":
                raise ValueError(
                    "g_f_bridge_metadata.claim_tier must be diagnostic_only"
                )
            if str(g_f_bridge_metadata.get("bin_id")) != bin_id:
                raise ValueError("g_f_bridge_metadata.bin_id must match bin_id")
            if str(g_f_bridge_metadata.get("selection_hash")) != selection_hash:
                raise ValueError(
                    "g_f_bridge_metadata.selection_hash must match selection_hash"
                )
            covariance_hash = covariance_metadata.get("covariance_hash")
            if str(g_f_bridge_metadata.get("covariance_hash")) != str(covariance_hash):
                raise ValueError(
                    "g_f_bridge_metadata.covariance_hash must match "
                    "covariance_metadata.covariance_hash"
                )
            _require_metadata_key(
                g_f_bridge_metadata,
                "config_hash",
                "g_f_bridge_metadata",
            )
            input_hashes = g_f_bridge_metadata.get("input_hashes")
            if isinstance(input_hashes, (str, bytes)) or not isinstance(
                input_hashes,
                Sequence,
            ):
                raise ValueError(
                    "g_f_bridge_metadata.input_hashes must be a non-empty sequence"
                )
            if not input_hashes or any(not str(item).strip() for item in input_hashes):
                raise ValueError(
                    "g_f_bridge_metadata.input_hashes must contain non-empty values"
                )
        caveats = tuple(str(item).strip() for item in self.caveats)
        if any(not item for item in caveats):
            raise ValueError("caveats must contain only non-empty strings")
        if DEFAULT_REDSHIFT_DEPTH_BIN_CAVEAT not in caveats:
            caveats = (DEFAULT_REDSHIFT_DEPTH_BIN_CAVEAT, *caveats)
        _scan_reserved_language(
            (
                bin_id,
                selection_rule,
                selection_hash,
                bin_assignment_hash,
                sky_support_status,
                mask_status,
                covariance_status,
                null_mock_status,
                g_f_payload_ref,
                caveats,
            ),
            "redshift_bin_metadata",
        )

        object.__setattr__(self, "bin_id", bin_id)
        object.__setattr__(self, "z_min", z_min)
        object.__setattr__(self, "z_max", z_max)
        object.__setattr__(self, "selection_rule", selection_rule)
        object.__setattr__(self, "selection_hash", selection_hash)
        object.__setattr__(self, "bin_assignment_hash", bin_assignment_hash)
        object.__setattr__(self, "sky_support_status", sky_support_status)
        object.__setattr__(self, "mask_status", mask_status)
        object.__setattr__(self, "covariance_status", covariance_status)
        object.__setattr__(self, "covariance_metadata", covariance_metadata)
        object.__setattr__(self, "null_mock_status", null_mock_status)
        object.__setattr__(self, "null_metadata", null_metadata)
        object.__setattr__(self, "sample_count", sample_count)
        object.__setattr__(self, "g_f_payload_ref", g_f_payload_ref)
        object.__setattr__(self, "g_f_bridge_metadata", g_f_bridge_metadata)
        object.__setattr__(self, "caveats", tuple(dict.fromkeys(caveats)))

    def as_payload(self) -> dict[str, object]:
        return {
            "bin_id": self.bin_id,
            "z_min": self.z_min,
            "z_max": self.z_max,
            "selection_rule": self.selection_rule,
            "selection_hash": self.selection_hash,
            "bin_assignment_hash": self.bin_assignment_hash,
            "sky_support_status": self.sky_support_status,
            "mask_status": self.mask_status,
            "covariance_status": self.covariance_status,
            "covariance_metadata": dict(self.covariance_metadata),
            "null_mock_status": self.null_mock_status,
            "null_metadata": dict(self.null_metadata),
            "sample_count": self.sample_count,
            "g_f_payload_ref": self.g_f_payload_ref,
            "g_f_bridge_metadata": (
                None
                if self.g_f_bridge_metadata is None
                else dict(self.g_f_bridge_metadata)
            ),
            "caveats": list(self.caveats),
        }


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
    if not np.all(np.isfinite(w)) or np.any(w < 0):
        raise ValueError("probe weights must be finite and nonnegative")
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


EXACT_ENUMERATION_MAX_PERMUTATIONS = 10_000
"""Hard ceiling on ``N!`` for the exact-enumeration path.

At :data:`EXACT_ENUMERATION_MAX_PERMUTATIONS` = 10 000 the exact path
is tractable up to ``N = 7`` (``7! = 5040``); ``N = 8`` (``40320``)
is refused so callers don't accidentally stall a test on a 40k-way
drift recomputation.
"""


def drift_pvalue(
    probes: Sequence[RedshiftBinnedProbe],
    bins: Sequence[Tuple[float, float]] = DEFAULT_Z_BINS,
    n_mock: int = 5_000,
    rng: Optional[np.random.Generator] = None,
    *,
    exact: bool = False,
) -> float:
    """Permutation p-value for the 'no z-drift' null hypothesis.

    Holds the N probe directions fixed and permutes the z_eff labels
    across them; for each permutation, recomputes the per-bin resultant
    axes and the total-drift statistic. Returns the fraction of
    permutations whose drift meets or exceeds the observed drift.

    Rationale: under the null "axis direction is independent of the
    probe's z_eff", any label permutation is equally plausible. The returned
    value is a descriptive label-exchangeability tail fraction, not calibrated
    evidence for a physical drift mechanism.

    Parameters
    ----------
    exact
        If ``True``, enumerate every label permutation via
        :func:`itertools.permutations` instead of Monte-Carlo sampling.
        Requires ``N! < EXACT_ENUMERATION_MAX_PERMUTATIONS``; otherwise
        raises ``ValueError``. The exact path is deterministic (ignores
        ``n_mock`` / ``rng``) and gives bit-reproducible p-values at
        small ``N`` — closing W11 F1 for the low-N reproducibility
        regime flagged in `AUDIT_PHASE_IND_TRACKS_W11_2026-04-19.md` §6.
    """
    if n_mock < 1:
        raise ValueError("n_mock must be >= 1")
    if len(probes) < 2:
        # A single probe cannot drift; call it fully consistent with the null.
        return 1.0

    observed = total_drift_deg(per_bin_resultants(probes, bins))
    z_labels = [float(p.z_eff) for p in probes]

    if exact:
        n_perm = math.factorial(len(probes))
        if n_perm > EXACT_ENUMERATION_MAX_PERMUTATIONS:
            raise ValueError(
                f"drift_pvalue(exact=True) refuses to enumerate {n_perm} "
                f"permutations (N={len(probes)}); ceiling is "
                f"{EXACT_ENUMERATION_MAX_PERMUTATIONS}. Drop to MC by "
                f"calling with exact=False."
            )
        count = 0
        for perm in itertools.permutations(z_labels):
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
        # Exact fraction; matches the MC estimator in the n_mock → ∞ limit.
        return count / n_perm

    if rng is None:
        rng = np.random.default_rng()
    z_arr = np.array(z_labels, dtype=float)
    count = 0
    for _ in range(n_mock):
        perm = rng.permutation(z_arr)
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


def _coerce_depth_bin_metadata(
    value: RedshiftDepthBinMetadata | Mapping[str, object],
    index: int,
) -> RedshiftDepthBinMetadata:
    if isinstance(value, RedshiftDepthBinMetadata):
        return value
    if isinstance(value, Mapping):
        try:
            return RedshiftDepthBinMetadata(**dict(value))
        except TypeError as exc:
            raise ValueError(
                f"depth_bin_metadata[{index}] is missing required fields"
            ) from exc
    raise TypeError(
        "depth_bin_metadata entries must be RedshiftDepthBinMetadata or mappings"
    )


def _normalise_depth_bin_metadata(
    depth_bin_metadata: Sequence[RedshiftDepthBinMetadata | Mapping[str, object]]
    | None,
    bin_results: Sequence[ZBinResult],
) -> tuple[RedshiftDepthBinMetadata, ...]:
    if depth_bin_metadata is None:
        return tuple()
    if isinstance(depth_bin_metadata, (str, bytes)):
        raise TypeError("depth_bin_metadata must be a sequence, not a string")
    metadata = tuple(
        _coerce_depth_bin_metadata(item, i)
        for i, item in enumerate(depth_bin_metadata)
    )
    if len(metadata) != len(bin_results):
        raise ValueError(
            "depth_bin_metadata length must match redshift bin result count "
            f"({len(metadata)} != {len(bin_results)})"
        )
    for i, (meta, result) in enumerate(zip(metadata, bin_results)):
        if not (
            math.isclose(meta.z_min, result.z_min, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(meta.z_max, result.z_max, rel_tol=0.0, abs_tol=1e-12)
        ):
            raise ValueError(
                "depth_bin_metadata entries must match redshift bin intervals; "
                f"entry {i} has ({meta.z_min}, {meta.z_max}) but result has "
                f"({result.z_min}, {result.z_max})"
            )
    return metadata


def _depth_metadata_statuses(
    metadata: Sequence[RedshiftDepthBinMetadata],
    bin_results: Sequence[ZBinResult],
) -> dict[str, object]:
    expected_count = len(bin_results)
    complete = len(metadata) == expected_count and expected_count > 0
    covariance_complete = bool(
        complete
        and all(
            meta.covariance_status == "matched_calibrated_covariance"
            and meta.covariance_metadata.get("calibration_status")
            == "matched_calibrated"
            for meta in metadata
        )
    )
    selection_complete = bool(complete)
    null_complete = bool(
        complete
        and all(
            meta.null_mock_status == "matched_calibrated_null"
            and meta.null_metadata.get("calibration_status")
            == "matched_calibrated"
            for meta in metadata
        )
    )
    sky_mask_complete = bool(
        complete
        and all(
            meta.sky_support_status == "complete"
            and meta.mask_status in {"complete", "masked_with_hash"}
            for meta in metadata
        )
    )
    g_f_refs = [meta.g_f_payload_ref for meta in metadata if meta.g_f_payload_ref]
    g_f_bridge_complete = bool(
        complete
        and len(g_f_refs) == expected_count
        and all(meta.g_f_bridge_metadata is not None for meta in metadata)
    )
    return {
        "metadata_complete": complete,
        "covariance_complete": covariance_complete,
        "selection_complete": selection_complete,
        "null_complete": null_complete,
        "sky_mask_complete": sky_mask_complete,
        "g_f_bridge_complete": g_f_bridge_complete,
        "g_f_payload_refs": g_f_refs,
        "g_f_payload_hashes": [
            str(meta.g_f_bridge_metadata["g_f_payload_hash"])
            for meta in metadata
            if meta.g_f_bridge_metadata is not None
            and meta.g_f_bridge_metadata.get("g_f_payload_hash") is not None
        ],
    }


def _augment_redshift_readiness(
    readiness: MioReadiness,
    *,
    covariance_complete: bool,
    selection_complete: bool,
    null_complete: bool,
    sky_mask_complete: bool,
    g_f_bridge_complete: bool,
) -> MioReadiness:
    required = list(readiness.required_gates)
    passed = list(readiness.passed_gates)
    failed = list(readiness.failed_gates)
    caveats = list(readiness.caveats)

    for gate_name, ok, missing_caveat in (
        (
            "depth_bin_covariance_metadata_complete",
            covariance_complete,
            "depth_bin_covariance_metadata_missing",
        ),
        (
            "depth_bin_selection_metadata_complete",
            selection_complete,
            "depth_bin_selection_metadata_missing",
        ),
        (
            "depth_bin_null_metadata_complete",
            null_complete,
            "depth_bin_null_metadata_missing",
        ),
        (
            "depth_bin_sky_mask_metadata_complete",
            sky_mask_complete,
            "depth_bin_sky_mask_metadata_incomplete",
        ),
        (
            "g_f_bridge_metadata_attached",
            g_f_bridge_complete,
            "g_f_bridge_metadata_missing",
        ),
    ):
        required.append(gate_name)
        if ok:
            passed.append(gate_name)
        else:
            failed.append(gate_name)
            caveats.append(missing_caveat)

    production_status = readiness.production_status
    claim_tier = readiness.claim_tier
    public_grade_label = readiness.public_grade_label
    if production_status == "production_candidate" and not g_f_bridge_complete:
        production_status = "diagnostic_only"
        claim_tier = "exploratory"
        public_grade_label = "diagnostic-only"
        caveats.append("redshift_binned_coherence_descriptive_fallback")

    return MioReadiness(
        production_status=production_status,
        claim_tier=claim_tier,
        required_gates=tuple(dict.fromkeys(required)),
        passed_gates=tuple(dict.fromkeys(passed)),
        failed_gates=tuple(dict.fromkeys(failed)),
        caveats=tuple(dict.fromkeys(caveats)),
        public_grade_label=public_grade_label,
    )


def _metadata_values(
    metadata: Sequence[RedshiftDepthBinMetadata],
    *,
    covariance_key: str | None = None,
    attr: str | None = None,
) -> list[str]:
    values: list[str] = []
    for item in metadata:
        if covariance_key is not None:
            raw = item.covariance_metadata.get(covariance_key)
        elif attr is not None:
            raw = getattr(item, attr)
        else:
            raise ValueError("covariance_key or attr must be provided")
        if raw is not None:
            values.append(str(raw))
    return values


def _metadata_status_label(
    ready: bool,
    *,
    metadata_present: bool,
    incomplete_label: str = "diagnostic_unmatched",
) -> str:
    if ready:
        return "complete"
    return incomplete_label if metadata_present else "missing"


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
    has_covariance: bool = False,
    has_null_mocks: bool = False,
    sky_support_status: SkySupportStatus = "partial",
    depth_bin_metadata: Sequence[RedshiftDepthBinMetadata | Mapping[str, object]]
    | None = None,
    artifact_path: str = "artifacts/mio/mio_redshift_coherence_v1.json",
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
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
    metadata = _normalise_depth_bin_metadata(depth_bin_metadata, bin_results)
    metadata_status = _depth_metadata_statuses(metadata, bin_results)
    effective_has_covariance = bool(
        has_covariance and metadata_status["covariance_complete"]
    )
    effective_has_null_mocks = bool(
        has_null_mocks and metadata_status["null_complete"]
    )
    effective_sky_support_status: SkySupportStatus = (
        "complete"
        if sky_support_status == "complete" and metadata_status["sky_mask_complete"]
        else "partial"
    )
    caveats = list(domain_caveats) if domain_caveats is not None else []
    for placeholder in placeholder_caveats_for(p.name for p in probes):
        if placeholder not in caveats:
            caveats.append(placeholder)
    if not metadata_status["metadata_complete"]:
        caveats.append("redshift_binned_coherence_descriptive_fallback")
    readiness = assess_mio_readiness(
        MioPrerequisites(
            requires_covariance=True,
            has_covariance=effective_has_covariance,
            requires_null_mocks=True,
            has_null_mocks=effective_has_null_mocks,
            requires_sky_support=True,
            sky_support_status=effective_sky_support_status,
            eligible_for_production=True,
        )
    )
    readiness = _augment_redshift_readiness(
        readiness,
        covariance_complete=bool(metadata_status["covariance_complete"]),
        selection_complete=bool(metadata_status["selection_complete"]),
        null_complete=bool(metadata_status["null_complete"]),
        sky_mask_complete=bool(metadata_status["sky_mask_complete"]),
        g_f_bridge_complete=bool(metadata_status["g_f_bridge_complete"]),
    )
    all_probe_names = {p.name for p in probes}
    assigned_probe_names = {
        name for result in bin_results for name in result.probe_names
    }
    status_metadata = {
        "covariance_status": (
            "available" if effective_has_covariance else "missing"
        ),
        "null_mock_status": (
            "available" if effective_has_null_mocks else "missing"
        ),
        "sky_support_status": effective_sky_support_status,
        "caller_sky_support_status": sky_support_status,
        "transfer_source": "none",
        "direction_convention": "oriented_unit_direction",
        "weighting_convention": "diagonal_sigma_cone_inverse_variance",
        "binning_convention": "redshift_bins_left_closed_final_right_closed",
        "null_calibration_status": (
            "matched_null_mocks_available"
            if effective_has_null_mocks
            else "permutation_label_exchangeability_unmatched"
        ),
        "claim_scope": "diagnostic_only_redshift_binned_coherence",
        "depth_bin_covariance_status": _metadata_status_label(
            bool(metadata_status["covariance_complete"]),
            metadata_present=bool(metadata_status["metadata_complete"]),
        ),
        "depth_bin_selection_status": _metadata_status_label(
            bool(metadata_status["selection_complete"]),
            metadata_present=bool(metadata_status["metadata_complete"]),
            incomplete_label="incomplete",
        ),
        "depth_bin_null_metadata_status": _metadata_status_label(
            bool(metadata_status["null_complete"]),
            metadata_present=bool(metadata_status["metadata_complete"]),
        ),
        "depth_bin_sky_mask_status": _metadata_status_label(
            bool(metadata_status["sky_mask_complete"]),
            metadata_present=bool(metadata_status["metadata_complete"]),
            incomplete_label="partial",
        ),
        "g_f_bridge_status": (
            "linked" if metadata_status["g_f_bridge_complete"] else "not_attached"
        ),
        "descriptive_fallback": bool(readiness.public_grade_label != "production-grade"),
        "bin_metadata": [item.as_payload() for item in metadata],
        "bin_ids": [item.bin_id for item in metadata],
        "covariance_hashes": _metadata_values(
            metadata,
            covariance_key="covariance_hash",
        ),
        "selection_hashes": _metadata_values(metadata, attr="selection_hash"),
        "bin_assignment_hashes": _metadata_values(
            metadata,
            attr="bin_assignment_hash",
        ),
        "g_f_payload_refs": list(metadata_status["g_f_payload_refs"]),
        "g_f_payload_hashes": list(metadata_status["g_f_payload_hashes"]),
        "probe_names_by_bin": {
            f"{result.z_min:g}:{result.z_max:g}": list(result.probe_names)
            for result in bin_results
        },
        "excluded_probe_names": sorted(all_probe_names - assigned_probe_names),
        "required_gates": list(readiness.required_gates),
        "passed_gates": list(readiness.passed_gates),
        "failed_gates": list(readiness.failed_gates),
        "production_status": readiness.production_status,
        "claim_tier": readiness.claim_tier,
        "public_grade_label": readiness.public_grade_label,
    }
    adequacy.update(
        {
            "covariance_ready": bool(effective_has_covariance),
            "null_mocks_ready": bool(effective_has_null_mocks),
            "sky_support_complete": bool(effective_sky_support_status == "complete"),
            "depth_bin_metadata_ready": bool(metadata_status["metadata_complete"]),
            "g_f_bridge_ready": bool(metadata_status["g_f_bridge_complete"]),
        }
    )

    return build_mio_certificate(
        report_type="redshift_binned_coherence",
        # A37.2 rule 2: bundle form is alphabetically sorted for stable cross-cert keys.
        probe_name="+".join(sorted(p.name for p in probes)),
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
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
        readiness=readiness,
        artifact_id="mio.redshift_binned_coherence.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "redshift_binned_coherence",
            "channel": "dipole_vs_z",
            "certificate_status_metadata": status_metadata,
        },
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
    has_covariance: bool = False,
    has_null_mocks: bool = False,
    sky_support_status: SkySupportStatus = "partial",
    depth_bin_metadata: Sequence[RedshiftDepthBinMetadata | Mapping[str, object]]
    | None = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
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
        probes,
        bin_results,
        p_drift=p_drift,
        total_drift=total_drift,
        has_covariance=has_covariance,
        has_null_mocks=has_null_mocks,
        sky_support_status=sky_support_status,
        depth_bin_metadata=depth_bin_metadata,
        artifact_path=str(out_path),
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
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
        "certificate": certificate_to_payload(cert),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "ARTEFACT_FILENAME",
    "DEFAULT_Z_BINS",
    "EXACT_ENUMERATION_MAX_PERMUTATIONS",
    "RedshiftBinnedProbe",
    "RedshiftDepthBinMetadata",
    "STANDARD_Z_PROBES",
    "ZBinResult",
    "assign_probes_to_bins",
    "drift_pvalue",
    "emit_redshift_coherence_artefact",
    "pairwise_bin_separations",
    "per_bin_resultants",
    "to_mio_certificate",
    "total_drift_deg",
]
