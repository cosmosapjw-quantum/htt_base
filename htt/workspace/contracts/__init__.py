"""workspace.contracts — frozen dataclass interfaces between HTT, MIO, Atlas.

All contracts here are **cross-package** (imported by more than one of
bass/, htt/, tsc/, mio/). Keeping them in workspace/contracts prevents any
single package from owning a contract it must itself satisfy.

G19 hard-separation (BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3 §10.2bis):
  * MIO outputs (MioCertificate) are diagnostic reports, NOT posteriors and
    NOT truth certificates; they cannot be merged with HTT evidence scores.
  * HTT outputs (PosteriorExportBundle) are cross-check only; they must
    not be ingested as MIO likelihood inputs.
  * BASS theory bundles (HttForwardOutput, AtlasEntry) are model-dependent
    predictions; they are NOT observational data.
"""

from .atlas_entry import AtlasEntry
from .atlas_entry_lite import AtlasEntryLite
from .departure_report import DepartureReport
from .htt_forward_output import HttForwardOutput
from .htt_to_mio import PosteriorExportBundle
from .mio_certificate import MioCertificate
from .tsc_overlay import TscAdequacyOverlay

__all__ = [
    "AtlasEntry",
    "AtlasEntryLite",
    "DepartureReport",
    "HttForwardOutput",
    "MioCertificate",
    "PosteriorExportBundle",
    "TscAdequacyOverlay",
]
