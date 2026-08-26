"""Pure rowwise MES-anchor operator for corrected low-ell feature rows.

This module consumes the active typed authority only.  It converts corrected
``C_l`` values in ``microK_CMB^2`` to dimensionless multipole amplitudes and
then constructs realization-conditional geodesic MES anchors.  A row-derived
anchor is a nonlinear coordinate of that same row; it is not an independent
data source or a physical source attribution.
"""
from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum
import hashlib
import json
import math
import re
from typing import Sequence

import numpy as np

from common.statistical_foundations import (
    AnchorConditioning,
    MESAnchorSpec,
    registered_geodesic_mes_anchors,
)
from htt.core.ssot import C


class MesRowAnchorError(ValueError):
    """Raised when a row cannot enter the active MES anchor operator."""


class ResidualDipoleAttribution(str, Enum):
    """Explicit residual-dipole branches admitted by this observed lane."""

    SAG_OBSERVER_MOTION_EPS1_ZERO = "SAG_OBSERVER_MOTION_EPS1_ZERO"


_SAG_ATTRIBUTION = (
    "SAG observer-motion convention: observed CMB dipole attributed to "
    "observer peculiar motion; residual cosmological eps1=0"
)
_CONTENT_IDENTITY_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_IDENTITY_ROLE = "REPRODUCIBILITY_IDENTITY_NOT_AUTHORITY"
_METHODOLOGY_ROLE = "ROWWISE_SELF_ANCHOR_NONLINEAR_STATISTIC"
_STATE_TOKEN = object()


@dataclass(frozen=True)
class MesRowAnchorState:
    """Typed active MES anchors and their row-level calibration values."""

    row_id: str
    epsilon_l: tuple[tuple[int, float], ...]
    residual_dipole_attribution: ResidualDipoleAttribution
    source_identity: str
    covariance_identity: str
    operator_identity: str
    row_content_identity: str
    feature_schema_identity: str
    identity_role: str
    methodology_role: str
    shared_data_dependence: bool
    independent_information_gain: bool
    anchors: tuple[tuple[str, MESAnchorSpec], ...]
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _STATE_TOKEN:
            raise MesRowAnchorError(
                "MesRowAnchorState must be created by the row-anchor factory"
            )
        if self.identity_role != _IDENTITY_ROLE:
            raise MesRowAnchorError("row identity role drifted")
        if (
            self.methodology_role != _METHODOLOGY_ROLE
            or self.shared_data_dependence is not True
            or self.independent_information_gain is not False
        ):
            raise MesRowAnchorError("row self-anchor claim semantics drifted")
        if not isinstance(
            self.residual_dipole_attribution, ResidualDipoleAttribution
        ):
            raise MesRowAnchorError("BLOCKED_MES_ATTRIBUTION")
        for field_name in (
            "source_identity",
            "covariance_identity",
            "operator_identity",
            "row_content_identity",
            "feature_schema_identity",
        ):
            _required_content_identity(getattr(self, field_name), field_name)
        expected_names = (
            "sigma",
            "omega",
            "acceleration",
            "anisotropic_curvature",
        )
        if tuple(name for name, _ in self.anchors) != expected_names or not all(
            type(anchor) is MESAnchorSpec for _, anchor in self.anchors
        ):
            raise MesRowAnchorError("row anchors are not the exact typed active set")

    def anchor(self, name: str) -> MESAnchorSpec:
        try:
            return dict(self.anchors)[name]
        except KeyError as exc:
            raise MesRowAnchorError(f"unknown MES anchor: {name}") from exc

    def as_payload(self) -> dict[str, object]:
        return {
            "format": "HTT_MES_ROW_ANCHOR_STATE_V1",
            "row_id": self.row_id,
            "row_content_identity": self.row_content_identity,
            "feature_schema_identity": self.feature_schema_identity,
            "source_identity": self.source_identity,
            "covariance_identity": self.covariance_identity,
            "operator_identity": self.operator_identity,
            "identity_role": self.identity_role,
            "epsilon_l": {
                str(ell): value for ell, value in self.epsilon_l
            },
            "residual_dipole_attribution": (
                self.residual_dipole_attribution.value
            ),
            "methodology_role": self.methodology_role,
            "shared_data_dependence": self.shared_data_dependence,
            "independent_information_gain": self.independent_information_gain,
            "anchors": {
                name: _anchor_payload(anchor) for name, anchor in self.anchors
            },
        }


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise MesRowAnchorError(f"{field_name} must be a non-empty trimmed string")
    return value


def _content_identity(payload: object, *, role: str) -> str:
    encoded = json.dumps(
        {"role": role, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _required_content_identity(value: object, field_name: str) -> str:
    text = _required_text(value, field_name)
    if _CONTENT_IDENTITY_RE.fullmatch(text) is None:
        raise MesRowAnchorError(
            f"{field_name} must be a sha256 content identity"
        )
    return text


def numeric_array_content_identity(values: object, *, role: str) -> str:
    """Bind exact finite float64 array content for reproducibility only."""

    role = _required_text(role, "role")
    raw = np.asarray(values)
    if raw.dtype.kind == "b":
        raise MesRowAnchorError("numeric content must not contain booleans")
    try:
        array = np.asarray(values, dtype="<f8")
    except (TypeError, ValueError) as exc:
        raise MesRowAnchorError("numeric content must be real-valued") from exc
    if array.size == 0 or not np.all(np.isfinite(array)):
        raise MesRowAnchorError("numeric content must be finite and non-empty")
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(role.encode("utf-8") + b"\0")
    digest.update(contiguous.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(contiguous.shape).encode("ascii") + b"\0")
    digest.update(memoryview(contiguous).cast("B"))
    return "sha256:" + digest.hexdigest()


def _anchor_payload(anchor: MESAnchorSpec) -> dict[str, object]:
    return {
        "anchor_id": anchor.anchor_id,
        "value": anchor.value,
        "authority_kind": anchor.authority_kind.value,
        "target_sector": anchor.target_sector,
        "target_invariant": anchor.target_invariant,
        "frame": anchor.frame,
        "congruence": anchor.congruence,
        "normalization": anchor.normalization,
        "perturbative_order": anchor.perturbative_order,
        "branch": anchor.branch,
        "attribution": anchor.attribution,
        "conditioning": anchor.conditioning.value,
        "validity_domain": anchor.validity_domain,
        "source_equations": list(anchor.source_equations),
        "shared_nuisance": list(anchor.shared_nuisance),
        "status": anchor.status.value,
        "allowed_use": list(anchor.allowed_use),
        "forbidden_use": list(anchor.forbidden_use),
        "withheld_reason": anchor.withheld_reason,
        "calibration_values": {
            name: value for name, value in anchor.calibration_values
        },
        "channel_key": list(anchor.channel_key),
    }


def _epsilon_from_cl(cl_value: float, ell: int) -> float:
    if isinstance(cl_value, bool) or not isinstance(cl_value, (int, float)):
        raise MesRowAnchorError("C_l must be a finite non-negative real number")
    value = float(cl_value)
    if not math.isfinite(value) or value < 0.0:
        raise MesRowAnchorError("C_l must be a finite non-negative real number")
    return math.sqrt((2 * ell + 1) * value / (4.0 * math.pi)) / C.T0_uK


def build_mes_row_anchor_state(
    *,
    row_id: str,
    feature_values: Sequence[float],
    feature_ids: Sequence[str],
    feature_units: Sequence[str],
    residual_dipole_attribution: ResidualDipoleAttribution,
    source_identity: str,
    covariance_identity: str,
    operator_identity: str,
) -> MesRowAnchorState:
    """Apply the registered geodesic MES factory to one corrected row."""

    if not isinstance(residual_dipole_attribution, ResidualDipoleAttribution):
        raise MesRowAnchorError("BLOCKED_MES_ATTRIBUTION")
    row_id = _required_text(row_id, "row_id")
    ids = tuple(_required_text(value, "feature_id") for value in feature_ids)
    units = tuple(_required_text(value, "feature_unit") for value in feature_units)
    values = tuple(feature_values)
    if len(ids) != len(units) or len(ids) != len(values):
        raise MesRowAnchorError("feature values, ids and units must align")
    if len(set(ids)) != len(ids):
        raise MesRowAnchorError("duplicate feature_ids are forbidden")
    try:
        positions = (ids.index("cl_l2"), ids.index("cl_l3"))
    except ValueError as exc:
        raise MesRowAnchorError("corrected cl_l2 and cl_l3 are required") from exc
    if tuple(units[index] for index in positions) != (
        "microK_CMB^2",
        "microK_CMB^2",
    ):
        raise MesRowAnchorError("C_l units must be microK_CMB^2")
    eps2 = _epsilon_from_cl(values[positions[0]], 2)
    eps3 = _epsilon_from_cl(values[positions[1]], 3)
    numeric_values: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MesRowAnchorError("feature values must be finite real numbers")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise MesRowAnchorError("feature values must be finite real numbers")
        numeric_values.append(numeric)
    source_identity = _required_content_identity(
        source_identity, "source_identity"
    )
    covariance_identity = _required_content_identity(
        covariance_identity, "covariance_identity"
    )
    operator_identity = _required_content_identity(
        operator_identity, "operator_identity"
    )
    feature_schema_identity = _content_identity(
        {"feature_ids": ids, "feature_units": units}, role="feature_schema"
    )
    row_content_identity = _content_identity(
        {
            "feature_schema_identity": feature_schema_identity,
            "feature_values_float_hex": [value.hex() for value in numeric_values],
        },
        role="corrected_lowell_feature_row",
    )
    anchors = registered_geodesic_mes_anchors(
        eps1=0.0,
        eps2=eps2,
        eps3=eps3,
        attribution=_SAG_ATTRIBUTION,
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
    )
    return MesRowAnchorState(
        row_id=row_id,
        epsilon_l=((2, eps2), (3, eps3)),
        residual_dipole_attribution=residual_dipole_attribution,
        source_identity=source_identity,
        covariance_identity=covariance_identity,
        operator_identity=operator_identity,
        row_content_identity=row_content_identity,
        feature_schema_identity=feature_schema_identity,
        identity_role=_IDENTITY_ROLE,
        methodology_role=_METHODOLOGY_ROLE,
        shared_data_dependence=True,
        independent_information_gain=False,
        anchors=tuple(anchors.items()),
        _construction_token=_STATE_TOKEN,
    )


def build_mes_row_anchor_pool(
    *,
    row_ids: Sequence[str],
    feature_matrix: Sequence[Sequence[float]],
    feature_ids: Sequence[str],
    feature_units: Sequence[str],
    residual_dipole_attribution: ResidualDipoleAttribution,
    source_identity: str,
    covariance_identity: str,
    operator_identity: str,
) -> tuple[MesRowAnchorState, ...]:
    """Apply exactly one row operator to an ordered observation/null pool."""

    ids = tuple(row_ids)
    rows = tuple(feature_matrix)
    if not ids or len(ids) != len(rows):
        raise MesRowAnchorError("row_ids and feature_matrix must align")
    if len(set(ids)) != len(ids):
        raise MesRowAnchorError("row_ids must be unique")
    return tuple(
        build_mes_row_anchor_state(
            row_id=row_id,
            feature_values=row,
            feature_ids=feature_ids,
            feature_units=feature_units,
            residual_dipole_attribution=residual_dipole_attribution,
            source_identity=source_identity,
            covariance_identity=covariance_identity,
            operator_identity=operator_identity,
        )
        for row_id, row in zip(ids, rows, strict=True)
    )


def mes_row_anchor_pool_payload(
    states: Sequence[MesRowAnchorState],
) -> dict[str, object]:
    """Serialize one shared-identity row pool without promoting its claims."""

    rows = tuple(states)
    if not rows or not all(type(row) is MesRowAnchorState for row in rows):
        raise MesRowAnchorError("states must be a non-empty typed row pool")
    if len({row.row_id for row in rows}) != len(rows):
        raise MesRowAnchorError("row state identifiers must be unique")
    shared_fields = (
        "source_identity",
        "covariance_identity",
        "operator_identity",
        "feature_schema_identity",
        "residual_dipole_attribution",
    )
    for field_name in shared_fields:
        if len({getattr(row, field_name) for row in rows}) != 1:
            raise MesRowAnchorError(
                f"row pool does not share one {field_name}"
            )
    pool_identity = _content_identity(
        {
            "row_ids": [row.row_id for row in rows],
            "row_content_identities": [
                row.row_content_identity for row in rows
            ],
            "source_identity": rows[0].source_identity,
            "covariance_identity": rows[0].covariance_identity,
            "operator_identity": rows[0].operator_identity,
            "feature_schema_identity": rows[0].feature_schema_identity,
        },
        role="ordered_mes_row_anchor_pool",
    )
    return {
        "format": "HTT_MES_ROW_ANCHOR_POOL_V1",
        "claim_tier": "diagnostic_only",
        "row_count": len(rows),
        "row_operator_scope": f"ONE_PURE_OPERATOR_ALL_{len(rows)}_ROWS",
        "shared_source_identity": rows[0].source_identity,
        "shared_covariance_identity": rows[0].covariance_identity,
        "shared_operator_identity": rows[0].operator_identity,
        "shared_feature_schema_identity": rows[0].feature_schema_identity,
        "pool_content_identity": pool_identity,
        "identity_role": _IDENTITY_ROLE,
        "residual_dipole_attribution": (
            rows[0].residual_dipole_attribution.value
        ),
        "methodology_role": _METHODOLOGY_ROLE,
        "shared_data_dependence": True,
        "independent_information_gain": False,
        "row_anchor_states": [row.as_payload() for row in rows],
    }


__all__ = [
    "MesRowAnchorError",
    "MesRowAnchorState",
    "ResidualDipoleAttribution",
    "build_mes_row_anchor_pool",
    "build_mes_row_anchor_state",
    "mes_row_anchor_pool_payload",
    "numeric_array_content_identity",
]
