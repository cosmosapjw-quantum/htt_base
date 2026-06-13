"""mio.decomposition — HJ-04 evidence-anatomy diagnostics.

The minimal non-BASS surface exposes two pure-python report builders:

* ``evidence_anatomy`` — channel-by-channel ``Δln B`` decomposition
* ``redshift_tomography`` — coarse redshift-era decomposition

These helpers consume externally produced HTT evidence deltas and emit
diagnostic artifacts / `MioCertificate`s without redefining evidence as
MIO adjudication output.
"""
from __future__ import annotations

from .evidence_anatomy import (  # noqa: F401
    ARTEFACT_FILENAME,
    EvidenceAnatomyContribution,
    EvidenceAnatomyNarrativeReport,
    EvidenceAnatomyReport,
    HttEvidenceTrace,
    HttEvidenceTraceTerm,
    build_evidence_anatomy_narrative_report,
    build_htt_evidence_trace_from_payload,
    emit_evidence_anatomy_artefact,
    summarize_evidence_anatomy,
    to_mio_certificate,
)
from .redshift_tomography import (  # noqa: F401
    REDSHIFT_ARTEFACT_FILENAME,
    RedshiftEvidenceSlice,
    RedshiftTomographyReport,
    emit_redshift_tomography_artefact,
    summarize_redshift_tomography,
    to_mio_certificate as to_redshift_mio_certificate,
)

__all__ = [
    "ARTEFACT_FILENAME",
    "REDSHIFT_ARTEFACT_FILENAME",
    "EvidenceAnatomyContribution",
    "EvidenceAnatomyNarrativeReport",
    "EvidenceAnatomyReport",
    "HttEvidenceTrace",
    "HttEvidenceTraceTerm",
    "RedshiftEvidenceSlice",
    "RedshiftTomographyReport",
    "build_evidence_anatomy_narrative_report",
    "build_htt_evidence_trace_from_payload",
    "emit_evidence_anatomy_artefact",
    "emit_redshift_tomography_artefact",
    "summarize_evidence_anatomy",
    "summarize_redshift_tomography",
    "to_mio_certificate",
    "to_redshift_mio_certificate",
]
