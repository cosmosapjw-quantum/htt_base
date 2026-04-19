"""mio.diagnostics.masked_sky_caveats — MIO-HJ-05a-lite sky-coverage caveats.

INDEPENDENT_TRACKS_PLAN v1.2 §12.6 (Week 6 Day 7).
Parent: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md v3 §4.5.3.5 HJ-05a.

Purpose: materialise the sky-coverage caveats (effective f_sky, ZoA
half-angle, ecliptic-pole gap, mask provenance) that feed the
`domain_caveats` field of a `MioCertificate`. The module needs data
only — no HTT posterior, no bass_py forward — which is why this
"lite" slice ships inside Week 6.

The f_sky definition is the straight pixel-count ratio (kept as an
integer fraction so bit-identical mocks produce bit-identical
values). Solid-angle-weighted variants belong to the full HJ-05
landing in Week 8+.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import numpy as np

from common.healpix_selection import nside_to_npix


# ---------------------------------------------------------------------------
# W12D2 / W5 APPLY-BIAS-AMP carry-forward.
#
# ``htt/htt/PR13AH_observables_reintegration.py::_apply_bias_to_direction``
# scales the measured unit vector by the *injected-truth* amplitude
# ``|V_true|`` rather than a measured velocity amplitude — because
# ``ChannelSummary`` does not yet carry a velocity-amplitude field. This
# is the correct *direction* de-bias but is a P2 limitation for any
# pipeline that expects the full bias-vector correction.
#
# The W5 audit (`AUDIT_PHASE_IND_TRACKS_W5_2026-04-19.md` §APPLY-BIAS-AMP)
# explicitly warns against patching `_apply_bias_to_direction` itself
# before the upstream amplitude field lands. Instead, this module exposes
# the canonical caveat string so any MIO consumer that runs on a masked-
# sky catalogue with mock-bias correction applied downstream can
# propagate the limitation into ``MioCertificate.domain_caveats``
# (v3 §4.5.2.1).
# ---------------------------------------------------------------------------

BIAS_AMP_CAVEAT = (
    "apply_bias_to_direction_scales_by_amp_true_not_amp_meas "
    "(W5 APPLY-BIAS-AMP carry-forward; valid until ChannelSummary grows "
    "a velocity-amplitude field — see htt/PR13AH "
    "_apply_bias_to_direction + W5 audit §APPLY-BIAS-AMP)"
)


def apply_bias_amp_caveat() -> str:
    """Return the canonical APPLY-BIAS-AMP caveat string.

    Callers that construct a `MioCertificate` alongside a mock-bias
    correction applied by `htt.PR13AH._apply_bias_to_direction` should
    append this string to the certificate's ``domain_caveats`` so the
    P2 amplitude-scaling limitation is visible to downstream readers.
    """
    return BIAS_AMP_CAVEAT


@dataclass(frozen=True)
class SkyCoverageReport:
    """Masked-sky coverage summary for MIO certificate caveats."""

    nside: int
    n_pix_total: int
    n_pix_kept: int
    f_sky_effective: float
    zoa_half_angle_deg: Optional[float]
    ecliptic_pole_gap_deg: Optional[float]
    mask_provenance: str
    caveats: List[str] = field(default_factory=list)


def _ensure_pixel_mask(mask_pix: Sequence, nside: int) -> np.ndarray:
    arr = np.asarray(mask_pix).astype(bool, copy=False)
    expected = nside_to_npix(nside)
    if arr.shape != (expected,):
        raise ValueError(
            f"mask_pix shape {arr.shape} does not match n_pix={expected} for "
            f"nside={nside}"
        )
    return arr


def build_report(
    mask_pix: Sequence,
    nside: int,
    *,
    zoa_half_angle_deg: Optional[float] = None,
    ecliptic_pole_gap_deg: Optional[float] = None,
    mask_provenance: str = "unknown",
    extra_caveats: Optional[Sequence[str]] = None,
    mock_bias_applied: bool = False,
) -> SkyCoverageReport:
    """Build a `SkyCoverageReport` from a per-pixel mask.

    Parameters
    ----------
    mask_pix
        Boolean per-pixel keep-mask (True = kept). Must match
        ``nside_to_npix(nside)`` in length.
    nside
        Pixelization parameter (positive power of two).
    zoa_half_angle_deg, ecliptic_pole_gap_deg
        Optional documentation fields; captured verbatim.
    mask_provenance
        Free-form string identifying the mask origin (e.g.
        'Planck_SMICA_common_mask_2018').
    extra_caveats
        Optional caller-supplied caveat strings appended to the auto-
        generated list.
    mock_bias_applied
        Set ``True`` when the masked catalogue is being processed
        alongside a mock-bias correction from
        ``htt.PR13AH._apply_bias_to_direction``. When set, the report
        appends :data:`BIAS_AMP_CAVEAT` to ``caveats`` so the APPLY-BIAS-
        AMP P2 limitation (W5 audit carry-forward) is surfaced to
        downstream `MioCertificate.domain_caveats`. Default ``False``
        preserves the pre-W12 call surface exactly.
    """
    mask = _ensure_pixel_mask(mask_pix, nside)
    n_pix_total = int(mask.size)
    n_pix_kept = int(mask.sum())
    f_sky = n_pix_kept / n_pix_total

    auto_caveats: List[str] = []
    if zoa_half_angle_deg is not None:
        auto_caveats.append(
            f"zoa_half_angle_deg={float(zoa_half_angle_deg):g}"
        )
    if ecliptic_pole_gap_deg is not None:
        auto_caveats.append(
            f"ecliptic_pole_gap_deg={float(ecliptic_pole_gap_deg):g}"
        )
    auto_caveats.append(f"f_sky_effective={f_sky:.6f}")
    auto_caveats.append(f"mask_provenance={mask_provenance}")
    if mock_bias_applied:
        auto_caveats.append(BIAS_AMP_CAVEAT)
    if extra_caveats:
        auto_caveats.extend(str(c) for c in extra_caveats)

    return SkyCoverageReport(
        nside=int(nside),
        n_pix_total=n_pix_total,
        n_pix_kept=n_pix_kept,
        f_sky_effective=float(f_sky),
        zoa_half_angle_deg=(float(zoa_half_angle_deg) if zoa_half_angle_deg is not None else None),
        ecliptic_pole_gap_deg=(float(ecliptic_pole_gap_deg) if ecliptic_pole_gap_deg is not None else None),
        mask_provenance=str(mask_provenance),
        caveats=list(auto_caveats),
    )


def as_caveats_list(report: SkyCoverageReport) -> List[str]:
    """Return the caveat strings ready to feed `MioCertificate.domain_caveats`."""
    return list(report.caveats)


__all__ = [
    "BIAS_AMP_CAVEAT",
    "SkyCoverageReport",
    "apply_bias_amp_caveat",
    "as_caveats_list",
    "build_report",
]
