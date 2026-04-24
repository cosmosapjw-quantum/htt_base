"""mio.interface — HJ-06 / SK-07M external interface surface.

HJ-06a (Week 6 Day 2) lands `mio_certificate.py` with the
`build_mio_certificate(...)` generator that produces
`workspace.contracts.MioCertificate` instances with auto-populated
provenance (git_commit, config_hash). SK-07M adds MIO-local readiness
helpers that map covariance / atlas / null-mock prerequisites onto the
canonical VER2 `ArtifactManifest`.
"""
from __future__ import annotations

from .manifest import (  # noqa: F401
    MioPrerequisites,
    MioReadiness,
    SkySupportStatus,
    assess_mio_readiness,
    build_mio_manifest,
    merge_domain_caveats,
)
from .mio_certificate import (  # noqa: F401
    build_mio_certificate,
    certificate_to_payload,
)
from .htt_cross_check import (  # noqa: F401
    CrossCheckRow,
    CrossCheckTable,
    STATUS_CONSISTENT,
    STATUS_DIVERGENT,
    STATUS_INCOMPARABLE,
    build_cross_check_table,
    register_rule,
    table_to_payload,
)
from .probe_name_registry import (  # noqa: F401
    REGISTERED_PROBE_IDS,
    is_registered_probe_id,
)
from .sigma_cone_provenance import (  # noqa: F401
    PLACEHOLDER_CAVEAT_SUFFIX,
    PROMOTED_SIGMA_CONE_PROBES,
    placeholder_caveats_for,
    is_promoted as is_sigma_cone_promoted,
)

__all__ = [
    "CrossCheckRow",
    "CrossCheckTable",
    "MioPrerequisites",
    "MioReadiness",
    "PLACEHOLDER_CAVEAT_SUFFIX",
    "PROMOTED_SIGMA_CONE_PROBES",
    "REGISTERED_PROBE_IDS",
    "STATUS_CONSISTENT",
    "STATUS_DIVERGENT",
    "STATUS_INCOMPARABLE",
    "SkySupportStatus",
    "assess_mio_readiness",
    "build_cross_check_table",
    "build_mio_certificate",
    "build_mio_manifest",
    "certificate_to_payload",
    "is_registered_probe_id",
    "is_sigma_cone_promoted",
    "merge_domain_caveats",
    "placeholder_caveats_for",
    "register_rule",
    "table_to_payload",
]
