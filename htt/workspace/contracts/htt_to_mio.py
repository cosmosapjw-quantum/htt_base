"""workspace.contracts.htt_to_mio — HTT posterior export bundle.

Frozen dataclass that packages an HTT pipeline's posterior summary for
**cross-check** consumption by MIO. Per BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN
v3 §10.2bis G19 hard-separation rule, this bundle is NEVER a likelihood
input to MIO — MIO may inspect it only to reconcile direction / amplitude
with its own independent observatory report.

Field set (reverse-traced from `bass_py/htt/htt/integration/to_mio.py`
`build_posterior_bundle` construction, plus the v3 §10.2bis
`is_cross_check_only` guard):

    x_median, x_hpd68, x_hpd95        — Layer-1 departure posterior
    Q_median, Q_hpd68                 — Layer-2 occupancy posterior
    Pi_median, Pi_hpd68               — Layer-3 exceedance posterior
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

@dataclass(frozen=True)
class PosteriorExportBundle:
    """HTT → MIO posterior summary (cross-check only; NOT a likelihood)."""

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

    def __post_init__(self) -> None:
        if not self.is_cross_check_only:
            raise ValueError(
                "PosteriorExportBundle must be cross-check only (G19). "
                "Cannot be merged into MIO evidence score; cannot be "
                "ingested as an MIO likelihood input."
            )
        if self.manifest is not None and self.manifest.owner != "HTT":
            raise ValueError(
                "PosteriorExportBundle.manifest.owner must be 'HTT' "
                f"(got {self.manifest.owner!r})"
            )
