"""Fixed observer-space l=2/3 orbit and mixed-morphology diagnostics.

This module operates only on exact :class:`ObservableIrrepState` values.  Its
coordinates are observer/data-space diagnostics.  Generic/global orbit
completeness is unproven, and no coordinate identifies a physical source or a
Bianchi family.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import ClassVar, Mapping

import numpy as np

from common.observable_irrep_state import (
    ObservableIrrepAvailability,
    ObservableIrrepRepresentation,
    ObservableIrrepState,
)
from obsstat.planck_lowell_irrep_projection import (
    stf2_components_to_tensor,
    stf3_components_to_tensor,
)


FRAME_FREE_FAMILY_ID = "OBSERVABLE_IRREP_ORBIT_V1"
GALACTIC_ORIENTATION_FAMILY_ID = "OBSERVABLE_IRREP_ORBIT_GALACTIC_V1"
FRAME_FREE_FEATURE_IDS = (
    "q2",
    "o2",
    "J_Q",
    "R_v0_normalized",
    "R_v1_normalized",
    "R_v2_normalized",
    "R_QS_normalized",
    "K_v_normalized",
)
FRAME_FREE_TAILS = (
    "two-sided",
    "two-sided",
    "two-sided",
    "upper",
    "two-sided",
    "upper",
    "two-sided",
    "two-sided",
)
GALACTIC_ORIENTATION_FEATURE_IDS = FRAME_FREE_FEATURE_IDS + (
    "Q_galactic_pole_power",
    "O_galactic_pole_power",
)
GALACTIC_ORIENTATION_TAILS = FRAME_FREE_TAILS + ("upper", "upper")
NORMALIZED_SHAPE_FEATURE_IDS = (
    "J_Q",
    "R_v0_normalized",
    "R_v1_normalized",
    "R_v2_normalized",
    "R_QS_normalized",
    "K_v_normalized",
    "Q_galactic_pole_power",
    "O_galactic_pole_power",
)

REPEATED_EIGEN_REL_TOL = 1.0e-12
KRYLOV_REL_TOL = 1.0e-12
JQ_BOUND_TOL = 5.0e-13


class ObservableOrbitError(ValueError):
    """Raised when the fixed observable-orbit contract is violated."""


@dataclass(frozen=True)
class OrbitCoordinate:
    feature_id: str
    status: str
    value: float | None
    tail: str
    parity: str
    units: str
    reason: str | None = None
    stratum: str | None = None

    schema: ClassVar[str] = "HTT_OBSERVABLE_ORBIT_COORDINATE_V1"

    def __post_init__(self) -> None:
        if self.status not in {"AVAILABLE", "ABSENT"}:
            raise ObservableOrbitError("coordinate status must be AVAILABLE or ABSENT")
        if self.tail not in {"two-sided", "upper", "lower"}:
            raise ObservableOrbitError("coordinate tail is outside the frozen registry")
        if self.status == "AVAILABLE":
            if self.value is None or not math.isfinite(float(self.value)):
                raise ObservableOrbitError("available coordinate must have a finite value")
            if self.reason is not None or self.stratum is not None:
                raise ObservableOrbitError("available coordinate cannot carry absence metadata")
        elif self.value is not None or not self.reason or not self.stratum:
            raise ObservableOrbitError("absent coordinate requires reason and stratum")

    def to_payload(self) -> dict[str, object]:
        return {
            "feature_id": self.feature_id,
            "parity": self.parity,
            "reason": self.reason,
            "schema": self.schema,
            "status": self.status,
            "stratum": self.stratum,
            "tail": self.tail,
            "units": self.units,
            "value": self.value,
        }


@dataclass(frozen=True)
class ObservableIrrepOrbitReport:
    row_identity: str
    state_content_id: str
    coordinates: tuple[OrbitCoordinate, ...]
    q_spectrum_status: str
    mixed_vector_status: str
    krylov_plane_status: str
    krylov_rank: int

    schema: ClassVar[str] = "HTT_OBSERVABLE_IRREP_ORBIT_REPORT_V1"
    claim_ceiling: ClassVar[str] = "OBSERVER_SPACE_METHODS_DIAGNOSTIC"
    completeness_status: ClassVar[str] = "GENERIC_GLOBAL_COMPLETENESS_UNPROVEN"
    physical_source_status: ClassVar[str] = "NOT_IDENTIFIED"
    bianchi_family_status: ClassVar[str] = "NOT_IDENTIFIED"

    def __post_init__(self) -> None:
        identifiers = tuple(item.feature_id for item in self.coordinates)
        if len(set(identifiers)) != len(identifiers):
            raise ObservableOrbitError("orbit feature identifiers must be unique")
        if not 0 <= self.krylov_rank <= 3:
            raise ObservableOrbitError("Krylov rank must lie in [0,3]")

    def coordinate(self, feature_id: str) -> OrbitCoordinate:
        for coordinate in self.coordinates:
            if coordinate.feature_id == feature_id:
                return coordinate
        raise ObservableOrbitError(f"unknown orbit coordinate: {feature_id}")

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "bianchi_family_status": self.bianchi_family_status,
            "claim_ceiling": self.claim_ceiling,
            "completeness_status": self.completeness_status,
            "coordinates": [item.to_payload() for item in self.coordinates],
            "family_registries": family_registry_payload(),
            "krylov_plane_status": self.krylov_plane_status,
            "krylov_rank": self.krylov_rank,
            "mixed_vector_status": self.mixed_vector_status,
            "physical_source_status": self.physical_source_status,
            "q_spectrum_status": self.q_spectrum_status,
            "row_identity": self.row_identity,
            "schema": self.schema,
            "state_content_id": self.state_content_id,
        }
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
        payload["content_id"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
        return payload


def family_registry_payload() -> dict[str, object]:
    return {
        FRAME_FREE_FAMILY_ID: {
            "feature_ids": list(FRAME_FREE_FEATURE_IDS),
            "frame_role": "FRAME_FREE_PRIMARY",
            "tails": list(FRAME_FREE_TAILS),
        },
        GALACTIC_ORIENTATION_FAMILY_ID: {
            "feature_ids": list(GALACTIC_ORIENTATION_FEATURE_IDS),
            "frame_role": "ABSOLUTE_GALACTIC_DESCRIPTIVE_COMPANION",
            "tails": list(GALACTIC_ORIENTATION_TAILS),
        },
    }


def _available(
    feature_id: str,
    value: float,
    *,
    tail: str,
    parity: str,
    units: str,
) -> OrbitCoordinate:
    return OrbitCoordinate(
        feature_id=feature_id,
        status="AVAILABLE",
        value=float(value),
        tail=tail,
        parity=parity,
        units=units,
    )


def _absent(
    feature_id: str,
    *,
    tail: str,
    parity: str,
    units: str,
    reason: str,
    stratum: str,
) -> OrbitCoordinate:
    return OrbitCoordinate(
        feature_id=feature_id,
        status="ABSENT",
        value=None,
        tail=tail,
        parity=parity,
        units=units,
        reason=reason,
        stratum=stratum,
    )


def _extract_tensors(state: ObservableIrrepState) -> tuple[np.ndarray, np.ndarray]:
    if type(state) is not ObservableIrrepState:
        raise ObservableOrbitError("state must be an exact ObservableIrrepState")
    state.content_id
    blocks = {block.representation: block for block in state.blocks}
    expected = {
        ObservableIrrepRepresentation.CARTESIAN_STF2_5,
        ObservableIrrepRepresentation.CARTESIAN_STF3_7,
    }
    if set(blocks) != expected:
        raise ObservableOrbitError("state must contain exactly the registered STF2/STF3 blocks")
    if any(
        blocks[representation].availability is not ObservableIrrepAvailability.AVAILABLE
        for representation in expected
    ):
        raise ObservableOrbitError("projected STF2/STF3 blocks must be numerically available")
    q = stf2_components_to_tensor(
        blocks[ObservableIrrepRepresentation.CARTESIAN_STF2_5].components
    )
    o = stf3_components_to_tensor(
        blocks[ObservableIrrepRepresentation.CARTESIAN_STF3_7].components
    )
    return q, o


def observable_irrep_orbit_report(
    state: ObservableIrrepState,
) -> ObservableIrrepOrbitReport:
    """Evaluate the complete frozen observer-space orbit registry for one row."""

    q, o = _extract_tensors(state)
    q2 = float(np.einsum("ab,ab->", q, q))
    q3 = float(np.trace(q @ q @ q))
    o2 = float(np.einsum("abc,abc->", o, o))
    coordinates: list[OrbitCoordinate] = [
        _available("q2", q2, tail="two-sided", parity="EVEN", units=f"{state.units}^2"),
        _available("q3", q3, tail="two-sided", parity="EVEN", units=f"{state.units}^3"),
        _available("o2", o2, tail="two-sided", parity="EVEN", units=f"{state.units}^2"),
    ]

    q_defined = q2 > 0.0
    o_defined = o2 > 0.0
    if q_defined:
        jq = math.sqrt(6.0) * q3 / q2**1.5
        if abs(jq) > 1.0 + JQ_BOUND_TOL:
            raise ObservableOrbitError("J_Q violates the real symmetric STF bound")
        jq = min(1.0, max(-1.0, jq))
        coordinates.append(
            _available("J_Q", jq, tail="two-sided", parity="EVEN", units="dimensionless")
        )
        qhat = q / math.sqrt(q2)
        eigenvalues = np.linalg.eigvalsh(qhat)
        gaps = np.diff(eigenvalues)
        repeated_q = bool(np.min(np.abs(gaps)) <= REPEATED_EIGEN_REL_TOL)
        q_spectrum_status = "REPEATED" if repeated_q else "SIMPLE"
        z = np.asarray([0.0, 0.0, 1.0])
        q_pole = float(np.dot(qhat @ z, qhat @ z))
        coordinates.append(
            _available(
                "Q_galactic_pole_power",
                q_pole,
                tail="upper",
                parity="EVEN",
                units="dimensionless",
            )
        )
    else:
        qhat = None
        repeated_q = False
        q_spectrum_status = "ABSENT_ZERO_AMPLITUDE"
        for feature_id, tail in (("J_Q", "two-sided"), ("Q_galactic_pole_power", "upper")):
            coordinates.append(
                _absent(
                    feature_id,
                    tail=tail,
                    parity="EVEN",
                    units="dimensionless",
                    reason="quadrupole shape is undefined at zero amplitude",
                    stratum="ZERO_Q_AMPLITUDE",
                )
            )

    if o_defined:
        ohat = o / math.sqrt(o2)
        z = np.asarray([0.0, 0.0, 1.0])
        pole_vector = np.einsum("abc,b,c->a", ohat, z, z)
        coordinates.append(
            _available(
                "O_galactic_pole_power",
                float(np.dot(pole_vector, pole_vector)),
                tail="upper",
                parity="EVEN",
                units="dimensionless",
            )
        )
    else:
        ohat = None
        coordinates.append(
            _absent(
                "O_galactic_pole_power",
                tail="upper",
                parity="EVEN",
                units="dimensionless",
                reason="octupole shape is undefined at zero amplitude",
                stratum="ZERO_O_AMPLITUDE",
            )
        )

    mixed_ids = (
        ("R_v0_normalized", "upper", "EVEN"),
        ("R_v1_normalized", "two-sided", "EVEN"),
        ("R_v2_normalized", "upper", "EVEN"),
        ("R_QS_normalized", "two-sided", "EVEN"),
        ("K_v_normalized", "two-sided", "PSEUDOSCALAR"),
    )
    krylov_rank = 0
    mixed_vector_status = "ABSENT"
    krylov_plane_status = "ABSENT"
    if qhat is None or ohat is None:
        stratum = "ZERO_Q_AMPLITUDE" if qhat is None else "ZERO_O_AMPLITUDE"
        for feature_id, tail, parity in mixed_ids:
            coordinates.append(
                _absent(
                    feature_id,
                    tail=tail,
                    parity=parity,
                    units="dimensionless",
                    reason="mixed Q/O shape is undefined when either radial amplitude vanishes",
                    stratum=stratum,
                )
            )
    else:
        v = np.einsum("abc,bc->a", ohat, qhat)
        s = np.einsum("acd,bcd->ab", ohat, ohat)
        s -= np.eye(3) * np.trace(s) / 3.0
        qv = qhat @ v
        q2v = qhat @ qv
        r_v0 = float(np.dot(v, v))
        r_v1 = float(np.dot(v, qv))
        r_v2 = float(np.dot(v, q2v))
        r_qs = float(np.einsum("ab,ab->", qhat, s))
        coordinates.extend(
            (
                _available("R_v0_normalized", r_v0, tail="upper", parity="EVEN", units="dimensionless"),
                _available("R_v1_normalized", r_v1, tail="two-sided", parity="EVEN", units="dimensionless"),
                _available("R_v2_normalized", r_v2, tail="upper", parity="EVEN", units="dimensionless"),
                _available("R_QS_normalized", r_qs, tail="two-sided", parity="EVEN", units="dimensionless"),
            )
        )
        krylov = np.column_stack((v, qv, q2v))
        singular_values = np.linalg.svd(krylov, compute_uv=False)
        if singular_values[0] == 0.0:
            krylov_rank = 0
        else:
            krylov_rank = int(
                np.count_nonzero(singular_values > KRYLOV_REL_TOL * singular_values[0])
            )
        mixed_vector_status = "AVAILABLE" if r_v0 > 0.0 else "ABSENT"
        krylov_plane_status = "AVAILABLE" if krylov_rank >= 2 else "ABSENT"
        if repeated_q:
            coordinates.append(
                _absent(
                    "K_v_normalized",
                    tail="two-sided",
                    parity="PSEUDOSCALAR",
                    units="dimensionless",
                    reason="a repeated Q spectrum cannot define a cyclic three-vector Krylov frame",
                    stratum="REPEATED_Q_SPECTRUM",
                )
            )
        elif krylov_rank < 2:
            coordinates.append(
                _absent(
                    "K_v_normalized",
                    tail="two-sided",
                    parity="PSEUDOSCALAR",
                    units="dimensionless",
                    reason="Krylov directions are coincident and their plane is undefined",
                    stratum="COINCIDENT_KRYLOV_DIRECTIONS",
                )
            )
        elif krylov_rank < 3:
            coordinates.append(
                _absent(
                    "K_v_normalized",
                    tail="two-sided",
                    parity="PSEUDOSCALAR",
                    units="dimensionless",
                    reason="the mixed vector is noncyclic under Q",
                    stratum="NONCYCLIC_KRYLOV",
                )
            )
        else:
            coordinates.append(
                _available(
                    "K_v_normalized",
                    float(np.linalg.det(krylov)),
                    tail="two-sided",
                    parity="PSEUDOSCALAR",
                    units="dimensionless",
                )
            )

    canonical_order = (
        "q2",
        "q3",
        "J_Q",
        "o2",
        "R_v0_normalized",
        "R_v1_normalized",
        "R_v2_normalized",
        "R_QS_normalized",
        "K_v_normalized",
        "Q_galactic_pole_power",
        "O_galactic_pole_power",
    )
    by_id = {item.feature_id: item for item in coordinates}
    if set(by_id) != set(canonical_order):
        raise ObservableOrbitError("complete orbit-coordinate registry was not emitted")
    return ObservableIrrepOrbitReport(
        row_identity=state.row_identity,
        state_content_id=state.content_id,
        coordinates=tuple(by_id[feature_id] for feature_id in canonical_order),
        q_spectrum_status=q_spectrum_status,
        mixed_vector_status=mixed_vector_status,
        krylov_plane_status=krylov_plane_status,
        krylov_rank=krylov_rank,
    )


def orbit_family_vector(
    report: ObservableIrrepOrbitReport,
    family_id: str = FRAME_FREE_FAMILY_ID,
) -> np.ndarray:
    """Return one complete predeclared family or refuse typed-absent rows."""

    if type(report) is not ObservableIrrepOrbitReport:
        raise ObservableOrbitError("report must be an exact ObservableIrrepOrbitReport")
    registries: Mapping[str, tuple[str, ...]] = {
        FRAME_FREE_FAMILY_ID: FRAME_FREE_FEATURE_IDS,
        GALACTIC_ORIENTATION_FAMILY_ID: GALACTIC_ORIENTATION_FEATURE_IDS,
    }
    if family_id not in registries:
        raise ObservableOrbitError("family_id is outside the frozen registry")
    coordinates = [report.coordinate(feature_id) for feature_id in registries[family_id]]
    absent = [item.feature_id for item in coordinates if item.status != "AVAILABLE"]
    if absent:
        raise ObservableOrbitError(f"family contains typed-absent coordinates: {absent}")
    return np.asarray([item.value for item in coordinates], dtype=np.float64)


__all__ = [
    "FRAME_FREE_FAMILY_ID",
    "FRAME_FREE_FEATURE_IDS",
    "FRAME_FREE_TAILS",
    "GALACTIC_ORIENTATION_FAMILY_ID",
    "GALACTIC_ORIENTATION_FEATURE_IDS",
    "GALACTIC_ORIENTATION_TAILS",
    "NORMALIZED_SHAPE_FEATURE_IDS",
    "ObservableIrrepOrbitReport",
    "ObservableOrbitError",
    "OrbitCoordinate",
    "family_registry_payload",
    "observable_irrep_orbit_report",
    "orbit_family_vector",
]
