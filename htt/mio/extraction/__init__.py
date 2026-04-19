"""mio.extraction — HJ-01 shear-extraction diagnostics.

W10 Days 3-4 landed the ``hj01_shear`` skeleton (parent plan §4.5.3.1).
The bass_py W10-02 K_ℓ atlas has not yet shipped; until it does, every
emitted certificate carries ``reduction_status='diagnostic-only'`` and
the ``DIAGNOSTIC_ONLY_CAVEAT`` (parent plan §17.3 risk row).

Public surface (re-exported here for convenience):

* ``ShearExtractor`` — config-bundled wrapper class
* ``ShearExtractorConfig`` / ``ShearExtractorReport`` — dataclasses
* ``extract_from_kl_atlas`` — main dict-path entry
* ``extract_from_atlas_entry`` — adapter for `workspace.contracts.AtlasEntry`
* ``validate_kl_atlas_schema`` — schema validator
* ``to_mio_certificate`` — `MioCertificate` packager
* ``emit_shear_extraction_artefact`` — JSON artefact writer
* ``KL_ATLAS_REQUIRED_KEYS`` / ``KL_ATLAS_OPTIONAL_KEYS`` — schema constants
* ``DIAGNOSTIC_ONLY_CAVEAT`` / ``ARTEFACT_FILENAME`` — public sentinels
"""
from __future__ import annotations

from .hj01_shear import (  # noqa: F401
    ARTEFACT_FILENAME,
    DIAGNOSTIC_ONLY_CAVEAT,
    KL_ATLAS_OPTIONAL_KEYS,
    KL_ATLAS_REQUIRED_KEYS,
    ShearExtractor,
    ShearExtractorConfig,
    ShearExtractorReport,
    emit_shear_extraction_artefact,
    extract_from_atlas_entry,
    extract_from_kl_atlas,
    to_mio_certificate,
    validate_kl_atlas_schema,
)

__all__ = [
    "ARTEFACT_FILENAME",
    "DIAGNOSTIC_ONLY_CAVEAT",
    "KL_ATLAS_OPTIONAL_KEYS",
    "KL_ATLAS_REQUIRED_KEYS",
    "ShearExtractor",
    "ShearExtractorConfig",
    "ShearExtractorReport",
    "emit_shear_extraction_artefact",
    "extract_from_atlas_entry",
    "extract_from_kl_atlas",
    "to_mio_certificate",
    "validate_kl_atlas_schema",
]
