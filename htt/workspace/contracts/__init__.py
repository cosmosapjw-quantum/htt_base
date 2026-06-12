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
from .full_cov_mes_report import FullCovMESReport
from .htt_forward_output import HttForwardOutput
from .htt_posterior import (
    HTTPosteriorBundle,
    HttLikelihoodTerm,
    reject_mio_likelihood_inputs,
)
from .htt_to_mio import PosteriorExportBundle
from .mio_certificate import MioCertificate
from .observable_vector import ObservableVector
from .preliminary_results import (
    ExportedArtifactEnvelope,
    ExportedTscActiveServiceBundle,
    ExportedTscPolicyLedger,
    PreliminaryPackArtifactRef,
    PreliminaryResultPack,
    load_exported_artifact,
    load_exported_tsc_active_service_bundle,
    load_exported_atlas_entry_lite,
    load_exported_discrimination_matrix,
    load_exported_mio_certificate,
    load_exported_observable_vector,
    load_exported_tsc_overlay,
    load_exported_tsc_policy_ledger,
    load_preliminary_result_pack,
)
from .transfer import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferRegistry,
    TransferSource,
    TransferValidRange,
    validate_transfer_dependent_result,
)
from .tsc_overlay import TscAdequacyOverlay
from .validation_registry import (
    HostileAuditRunbook,
    InjectionCampaignManifest,
    NullEnsembleManifest,
    TheoremToTestEntry,
    ValidationCampaign,
    ValidationTestLink,
)

__all__ = [
    "AtlasEntry",
    "AtlasEntryLite",
    "CalibrationStatus",
    "DepartureReport",
    "FullCovMESReport",
    "HostileAuditRunbook",
    "HTTPosteriorBundle",
    "HttForwardOutput",
    "HttLikelihoodTerm",
    "InjectionCampaignManifest",
    "MioCertificate",
    "NullEnsembleManifest",
    "ObservableVector",
    "ObservableKind",
    "ExportedArtifactEnvelope",
    "ExportedTscActiveServiceBundle",
    "ExportedTscPolicyLedger",
    "PreliminaryPackArtifactRef",
    "PreliminaryResultPack",
    "PosteriorExportBundle",
    "TransferFunctionSpec",
    "TransferRegistry",
    "TransferSource",
    "TransferValidRange",
    "TheoremToTestEntry",
    "TscAdequacyOverlay",
    "ValidationCampaign",
    "ValidationTestLink",
    "load_exported_artifact",
    "load_exported_tsc_active_service_bundle",
    "load_exported_atlas_entry_lite",
    "load_exported_discrimination_matrix",
    "load_exported_mio_certificate",
    "load_exported_observable_vector",
    "load_exported_tsc_overlay",
    "load_exported_tsc_policy_ledger",
    "load_preliminary_result_pack",
    "reject_mio_likelihood_inputs",
    "validate_transfer_dependent_result",
]
