"""workspace.contracts — frozen dataclass interfaces between HTT, MIO, Atlas.

All contracts here are **cross-package** (imported by more than one of
bass/, htt/, tsc/, mio/). Keeping them in workspace/contracts prevents any
single package from owning a contract it must itself satisfy.

G19 hard-separation (BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3 §10.2bis):
  * MIO outputs (MioCertificate) are diagnostic reports, NOT posteriors and
    NOT truth certificates; they cannot be merged with HTT evidence scores.
  * HTT outputs (PosteriorExportBundle) are cross-check only; they must
    not be ingested as MIO likelihood inputs.
"""

from .htt_to_mio import PosteriorExportBundle

__all__ = ["PosteriorExportBundle"]
