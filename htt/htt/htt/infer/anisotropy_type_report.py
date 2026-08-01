"""HTT replay adapter for COMMON anisotropy-compatibility reports.

HTT owns the PR-256 model-dependent local/global response construction.  This
adapter replays that report under its original normalizer and exports only a
sealed COMMON compatibility snapshot.  It creates no probability-bearing MIO
inference, geometry label, family label, or native-solver result.
"""

from __future__ import annotations

import hashlib
import json

from common.anchor_geometry import NormalizerSpec
from common.anisotropy_type_report import (
    LocalGlobalCompatibilityInput,
    _build_local_global_compatibility_input,
)
from htt.departure.velocity_frame_decomposition import (
    SourceResponseGeometryReport,
    revalidate_source_response_geometry,
)


def _report_id(report: SourceResponseGeometryReport) -> str:
    encoded = json.dumps(
        report.as_payload(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_local_global_compatibility_input(
    *,
    report: SourceResponseGeometryReport,
    normalizer: NormalizerSpec,
) -> LocalGlobalCompatibilityInput:
    """Replay PR-256 and project it into the COMMON PR-267 contract."""

    replayed = revalidate_source_response_geometry(
        report,
        normalizer=normalizer,
    )
    return _build_local_global_compatibility_input(
        source_report_id=_report_id(replayed),
        status=replayed.status.value,
        local_rank=replayed.local_rank,
        global_rank=replayed.global_rank,
        joint_rank=replayed.joint_rank,
        principal_angles_radians=replayed.principal_angles_radians,
        minimum_principal_angle_radians=(
            replayed.minimum_principal_angle_radians
        ),
        separation_threshold_radians=(
            replayed.separation_threshold_radians
        ),
        direct_sum=replayed.direct_sum,
        observable_labels=replayed.observable_labels,
        covariance_id=replayed.covariance_id,
        mask_id=replayed.mask_id,
        normalizer_id=replayed.normalizer_id,
        normalizer_source_identity=(
            replayed.normalizer_source_identity
        ),
        local_provider_id=replayed.local_provider.provider_id,
        global_provider_id=replayed.global_provider.provider_id,
        local_response_id=replayed.local_provider.response_id,
        global_response_id=replayed.global_provider.response_id,
        joint_transfer_id=replayed.joint_transfer_id,
        assumptions=replayed.assumptions,
    )


__all__ = [
    "LocalGlobalCompatibilityInput",
    "build_local_global_compatibility_input",
]
