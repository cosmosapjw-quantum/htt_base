"""mio.bridges — HJ-07 re-exports of htt modules that are MIO-owned.

Semantic re-export surface for htt-physically-located modules whose
epistemic ownership is MIO (per v3 §1.4.1). The files themselves
remain under `htt/` to preserve existing import paths; consumers may
import either `htt.<name>` or `mio.bridges.<name>` with identical
semantics. See `PR13AM_te_sign_d1d3_bridge.__mio_owned__` for the
first-line G19 flag.

Landed Week 6 Day 6 (MIO-BRIDGES-01, plan §12.5; PATCH-01 closure).
"""
from __future__ import annotations

# Option A re-export (plan §12.5) — preserve existing `htt.PR13AM_*`
# import path; expose the same module under `mio.bridges.PR13AM_*`.
from htt import PR13AM_te_sign_d1d3_bridge  # noqa: F401 — re-export
from .preliminary_results import (  # noqa: F401 — re-export
    PreliminaryMioHandoff,
    build_preliminary_mio_handoff,
)
from .promoted_artifacts import (  # noqa: F401 — re-export
    ARTEFACT_FILENAME,
    PromotedAxisSummary,
    emit_promoted_axis_ingestion_artefact,
    ingest_fiducial_posterior_bundle,
    to_mio_certificate,
)
from . import preliminary_results  # noqa: F401 — re-export
from . import promoted_artifacts  # noqa: F401 — re-export


__all__ = [
    "PR13AM_te_sign_d1d3_bridge",
    "ARTEFACT_FILENAME",
    "PreliminaryMioHandoff",
    "PromotedAxisSummary",
    "build_preliminary_mio_handoff",
    "emit_promoted_axis_ingestion_artefact",
    "ingest_fiducial_posterior_bundle",
    "preliminary_results",
    "promoted_artifacts",
    "to_mio_certificate",
]
