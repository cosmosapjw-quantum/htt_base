"""HTT public surface for COMMON-owned anchored response diagnostics.

All numerical contracts are implemented in :mod:`common` so HTT, MIO and
future adapter consumers cannot acquire divergent definitions.  HTT owns the
model-dependent held-out source competition that may be carried by a phase
diagram; the matrix geometry itself remains a COMMON contract.
"""

from common.anchored_response_geometry import (
    AnchoredResponseGeometryError,
    AnchoredResponseGeometryReport,
    AnchoredResponseStatus,
    IdentifiedSetContractionReport,
    IdentifiedSetContractionStatus,
    NonlinearityDGPKind,
    NonlinearityPhaseCell,
    NonlinearityPhaseDiagramReport,
    NonlinearityPhaseStatus,
    PrincipalAngleReport,
    PrincipalAngleStatus,
    SchurMorphologyInformationReport,
    SchurMorphologyStatus,
    anchored_numeric_content_id,
    build_nonlinearity_phase_cell,
    build_nonlinearity_phase_diagram,
    measure_anchored_response_geometry,
    measure_schur_morphology_information,
    revalidate_anchored_response_geometry,
    revalidate_schur_morphology_information,
)

__all__ = [
    "AnchoredResponseGeometryError",
    "AnchoredResponseGeometryReport",
    "AnchoredResponseStatus",
    "IdentifiedSetContractionReport",
    "IdentifiedSetContractionStatus",
    "NonlinearityDGPKind",
    "NonlinearityPhaseCell",
    "NonlinearityPhaseDiagramReport",
    "NonlinearityPhaseStatus",
    "PrincipalAngleReport",
    "PrincipalAngleStatus",
    "SchurMorphologyInformationReport",
    "SchurMorphologyStatus",
    "anchored_numeric_content_id",
    "build_nonlinearity_phase_cell",
    "build_nonlinearity_phase_diagram",
    "measure_anchored_response_geometry",
    "measure_schur_morphology_information",
    "revalidate_anchored_response_geometry",
    "revalidate_schur_morphology_information",
]
