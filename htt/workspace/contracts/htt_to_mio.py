"""workspace.contracts.htt_to_mio — HTT/MIO cross-check boundaries.

The active export carries only explicitly legacy-classified scalar projections
and an HTT-owned diagnostic manifest.  HTT posterior odds and model evidences
do not cross into MIO.  ``PosteriorExportBundle`` remains below for explicit
historical reproduction only.

Field set (reverse-traced from `bass_py/htt/htt/integration/to_mio.py`
`build_posterior_bundle` construction, plus the v3 §10.2bis
`is_cross_check_only` guard):

    x_median, x_hpd68, x_hpd95        — Layer-1 departure posterior
    Q_median, Q_hpd68                 — Layer-2 policy-normalized HTT posterior score
    Pi_median, Pi_hpd68               — HTT posterior exceedance cross-check
    ln_B_total                        — global Bayes factor
    model_evidences                   — per-model ln-evidence map
    F_median, F_hpd68                 — filling fraction summary
    n_live                            — nested-sampling live points
    is_cross_check_only=True          — G19 guard (ValueError if False)
    model=""                          — optional provenance label
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Tuple

from common.contracts import ArtifactManifest
from common.statistical_foundations import LegacyProjectionReport


@dataclass(frozen=True)
class MioCrossCheckExport:
    """Active HTT → MIO diagnostic cross-check without HTT evidence."""

    model: str
    legacy_projection: LegacyProjectionReport
    manifest: ArtifactManifest
    source_artifact_ref: str
    posterior_ref: str
    is_cross_check_only: bool = True
    evidence_included: bool = False

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (
                self.model,
                self.source_artifact_ref,
                self.posterior_ref,
            )
        ):
            raise ValueError("cross-check model and source refs must be non-empty")
        if not isinstance(self.legacy_projection, LegacyProjectionReport):
            raise TypeError("legacy_projection must be a LegacyProjectionReport")
        if (
            type(self.is_cross_check_only) is not bool
            or type(self.evidence_included) is not bool
        ):
            raise TypeError("cross-check firewall fields must be exact booleans")
        if self.is_cross_check_only is not True or self.evidence_included is not False:
            raise ValueError("MIO cross-check exports cannot carry HTT evidence")
        if self.manifest.owner != "HTT":
            raise ValueError("MioCrossCheckExport.manifest.owner must be 'HTT'")
        if self.manifest.claim_tier != "diagnostic_only":
            raise ValueError("MIO cross-check manifest must be diagnostic_only")
        if self.manifest.production_status != "diagnostic_only":
            raise ValueError(
                "MIO cross-check manifest production_status must be diagnostic_only"
            )

@dataclass(frozen=True)
class PosteriorExportBundle:
    """Legacy HTT → MIO posterior summary; explicit reproduction only."""

    x_median: float
    x_hpd68: Tuple[float, float]
    x_hpd95: Tuple[float, float]
    Q_median: float
    Q_hpd68: Tuple[float, float]
    Pi_median: float
    Pi_hpd68: Tuple[float, float]
    ln_B_total: float
    F_median: float
    F_hpd68: Tuple[float, float]
    n_live: int
    model_evidences: Mapping[str, float] = field(default_factory=dict)
    model: str = ""
    is_cross_check_only: bool = True
    manifest: ArtifactManifest | None = None
    legacy_reproduction_only: bool = True

    def __post_init__(self) -> None:
        if not self.is_cross_check_only:
            raise ValueError(
                "PosteriorExportBundle must be cross-check only (G19). "
                "Cannot be merged into MIO evidence score; cannot be "
                "ingested as an MIO likelihood input."
            )
        if not self.legacy_reproduction_only:
            raise ValueError("PosteriorExportBundle is legacy reproduction only")
        if self.manifest is not None and self.manifest.owner != "HTT":
            raise ValueError(
                "PosteriorExportBundle.manifest.owner must be 'HTT' "
                f"(got {self.manifest.owner!r})"
            )
