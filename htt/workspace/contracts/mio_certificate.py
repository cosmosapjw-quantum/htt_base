"""workspace.contracts.mio_certificate — `MioCertificate` schema.

Frozen dataclass for the Model-Independent Observatory (MIO) diagnostic
report. Spec source: `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3 §4.5.2.1
and §10.2bis G19 enforcement.

Hard rules (v3 §4.5.4 G19 Hard Separation):
  * This IS NOT a posterior. `as_posterior_bundle()` must raise
    `NotImplementedError` — by design, never implement it.
  * This IS NOT a truth certificate. Consumers may not interpret MIO
    validity as a proof of a specific theory.
  * MIO score + HTT evidence cannot be summed into a single master score.

The *generator* API lives at `bass_py/mio/interface/mio_certificate.py`
(Week 6 MIO-HJ-06a). This module holds only the schema contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from common.contracts import ArtifactManifest

@dataclass(frozen=True)
class MioCertificate:
    """Model-independent diagnostic report. NOT a posterior, NOT a truth certificate."""

    # Identification
    report_type: str                       # 'shear_extraction' | 'directional_coherence' | ...
    probe_name: str                        # 'Planck_TT' | 'CatWISE' | 'CF4pp' | ...
    channel: str                           # 'low_ell' | 'biposh' | 'dipole' | ...

    # Diagnostic quantities (not model parameters)
    departure_variables: Dict[str, float]
    adequacy_indicators: Dict[str, bool]
    consistency_metrics: Dict[str, float]

    # Caveats
    domain_caveats: List[str]
    channel_caveats: List[str]
    reduction_status: str                  # 'theory-direct' | 'theory-approximate' | 'diagnostic-only'

    # Provenance
    generated_by: str
    git_commit: str
    config_hash: str
    input_data_hashes: List[str]
    manifest: ArtifactManifest | None = None
    tsc_overlay_ref: str | None = None

    # Cross-check hints (not posteriors!)
    htt_cross_check_suggested: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        if self.manifest is not None and self.manifest.owner != "MIO":
            raise ValueError(
                "MioCertificate.manifest.owner must be 'MIO' "
                f"(got {self.manifest.owner!r})"
            )

    def as_posterior_bundle(self):
        """Intentionally unimplemented — MIO does NOT generate posteriors (v3 G19)."""
        raise NotImplementedError(
            "MioCertificate is a diagnostic report, not a posterior. "
            "Use HTT's PosteriorExportBundle for posterior operations."
        )
