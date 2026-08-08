"""PR-281 successor anisotropy report with replay-bound null directions.

The exact PR-267/PR-273 V1 implementation remains byte-frozen in
``common.anisotropy_type_report_v1``.  This module is the additive V2 public
surface: it delegates every existing replay and abstention decision to V1,
then seals the already-replayed anchored-response right-null directions with
their parameter labels, covariance identity, and response identity.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from functools import wraps
from typing import Sequence

from common import anisotropy_type_report_v1 as _v1
from common.anisotropy_type_report_v1 import *  # noqa: F401,F403

# Preserve the legacy module's runtime annotation namespace as well as the
# public call signature exposed by ``functools.wraps``.
AnchoredResponseGeometryReport = _v1.AnchoredResponseGeometryReport
ConditionalExceedanceProfile = _v1.ConditionalExceedanceProfile
DepthCoherenceReport = _v1.DepthCoherenceReport
DepthPath = _v1.DepthPath
JointAnisotropyState = _v1.JointAnisotropyState
NormalizerSpec = _v1.NormalizerSpec
OrbitCatalogueV3Report = _v1.OrbitCatalogueV3Report


def _receipt(value: object, name: str) -> str:
    text = _v1._text(value, name)
    digest = text[7:] if text.startswith("sha256:") else ""
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise _v1.AnisotropyTypeReportError(
            f"{name} must be a lowercase sha256 receipt identity"
        )
    return text


def _directions(
    values: Sequence[Sequence[object]],
) -> tuple[tuple[float, ...], ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise _v1.AnisotropyTypeReportError(
            "uncovered_directions must be a sequence of vectors"
        )
    return tuple(
        _v1._vector(value, f"uncovered_directions[{index}]")
        for index, value in enumerate(values)
    )


@dataclass(frozen=True)
class AnisotropyTypeReport(_v1.AnisotropyTypeReport):
    """V2 report adding an identity-sealed anchored null-space projection."""

    uncovered_directions: tuple[tuple[float, ...], ...] = ()
    uncovered_parameter_labels: tuple[str, ...] = ()
    uncovered_covariance_id: str = ""
    uncovered_response_id: str = ""

    def __post_init__(self, _construction_token: object) -> None:
        super().__post_init__(_construction_token)
        directions = _directions(self.uncovered_directions)
        labels = _v1._texts(
            self.uncovered_parameter_labels,
            "uncovered_parameter_labels",
        )
        covariance_id = _receipt(
            self.uncovered_covariance_id,
            "uncovered_covariance_id",
        )
        response_id = _receipt(
            self.uncovered_response_id,
            "uncovered_response_id",
        )
        if self.response_rank is None or self.response_parameter_dimension is None:
            raise _v1.AnisotropyTypeReportError(
                "replay-bound uncovered directions require measured response dimensions"
            )
        if self.response_rank > self.response_parameter_dimension:
            raise _v1.AnisotropyTypeReportError(
                "response rank must not exceed parameter dimension"
            )
        if len(labels) != self.response_parameter_dimension:
            raise _v1.AnisotropyTypeReportError(
                "uncovered parameter labels must match parameter dimension"
            )
        if any(len(direction) != len(labels) for direction in directions):
            raise _v1.AnisotropyTypeReportError(
                "every uncovered direction must use the labelled parameter basis"
            )
        expected_nullity = self.response_parameter_dimension - self.response_rank
        if len(directions) != expected_nullity:
            raise _v1.AnisotropyTypeReportError(
                "uncovered direction count must equal parameter nullity"
            )
        object.__setattr__(self, "uncovered_directions", directions)
        object.__setattr__(self, "uncovered_parameter_labels", labels)
        object.__setattr__(self, "uncovered_covariance_id", covariance_id)
        object.__setattr__(self, "uncovered_response_id", response_id)
        object.__setattr__(
            self,
            "_identity_seal",
            _v1._sha256_payload(self._payload_unchecked()),
        )

    def _payload_unchecked(self) -> dict[str, object]:
        payload = super()._payload_unchecked()
        payload.update(
            {
                "schema": "HTT_ANISOTROPY_TYPE_REPORT_V2",
                "uncovered_covariance_id": self.uncovered_covariance_id,
                "uncovered_directions": [
                    list(direction) for direction in self.uncovered_directions
                ],
                "uncovered_parameter_labels": list(self.uncovered_parameter_labels),
                "uncovered_response_id": self.uncovered_response_id,
            }
        )
        return payload


@wraps(_v1.build_anisotropy_type_report)
def build_anisotropy_type_report(
    *,
    report_id: str,
    joint_state: JointAnisotropyState,
    orbit_report: OrbitCatalogueV3Report,
    anchored_response: AnchoredResponseGeometryReport,
    anchored_normalizer: NormalizerSpec,
    anchored_comparison_response: object | None,
    local_global: LocalGlobalCompatibilityInput,
    open_set: OpenSetReplayInputs,
    conditional_exceedance: ConditionalExceedanceProfile,
    depth_path: DepthPath,
    depth_coherence: DepthCoherenceReport,
) -> AnisotropyTypeReport:
    """Build V2 after the complete V1 replay and abstention pipeline passes."""

    kwargs = {
        "report_id": report_id,
        "joint_state": joint_state,
        "orbit_report": orbit_report,
        "anchored_response": anchored_response,
        "anchored_normalizer": anchored_normalizer,
        "anchored_comparison_response": anchored_comparison_response,
        "local_global": local_global,
        "open_set": open_set,
        "conditional_exceedance": conditional_exceedance,
        "depth_path": depth_path,
        "depth_coherence": depth_coherence,
    }
    try:
        anchored = _v1._replay_anchored_response(
            anchored_response,
            normalizer=anchored_normalizer,
            comparison_response=anchored_comparison_response,
        )
    except _v1.AnisotropyTypeReportError:
        raise
    except ValueError as exc:
        raise _v1.AnisotropyTypeReportError(
            "anchored response failed exact replay"
        ) from exc
    base = _v1.build_anisotropy_type_report(**kwargs)
    if (
        base.anchored_response_id != _v1._sha256_payload(anchored.as_payload())
        or base.response_rank != anchored.rank
        or base.response_parameter_dimension != anchored.parameter_dimension
    ):
        raise _v1.AnisotropyTypeReportError(
            "anchored response changed between successor and V1 replay"
        )
    if anchored.covariance_id is None or anchored.response_id is None:
        raise _v1.AnisotropyTypeReportError(
            "replayed uncovered directions require covariance and response identities"
        )
    base_fields = {
        item.name: getattr(base, item.name)
        for item in fields(_v1.AnisotropyTypeReport)
        if item.init
    }
    return AnisotropyTypeReport(
        **base_fields,
        uncovered_directions=anchored.null_directions,
        uncovered_parameter_labels=anchored.parameter_labels,
        uncovered_covariance_id=anchored.covariance_id,
        uncovered_response_id=anchored.response_id,
        _construction_token=_v1._REPORT_TOKEN,
    )


build_anisotropy_type_report.__module__ = __name__


# The HTT PR-256 replay adapter intentionally consumes this private factory.
_build_local_global_compatibility_input = _v1._build_local_global_compatibility_input

__all__ = list(_v1.__all__)
