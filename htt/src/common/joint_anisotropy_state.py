"""PR-281 public successor surface for the canonical joint state.

The PR-261/PR-269 implementation is byte-frozen in
``common.joint_anisotropy_state_v1``.  This module re-exports that unchanged
state contract and adds a separate, dimension-aware orbit acceptance value
object without widening ``HTT_JOINT_ANISOTROPY_STATE_V1``.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Mapping

import numpy as np

from common import joint_anisotropy_state_v1 as _v1
from common.enum_compat import StrEnum
from common.joint_anisotropy_state_v1 import *  # noqa: F401,F403


class OrbitAcceptanceCase(StrEnum):
    """Registered invariant-quotient cases; no case is inferred from data."""

    PRINCIPAL_BASE = "PRINCIPAL_BASE"
    PRINCIPAL_WITH_ACCELERATION = "PRINCIPAL_WITH_ACCELERATION"
    PRINCIPAL_WITH_ACCELERATION_AND_VELOCITY_SPLIT = (
        "PRINCIPAL_WITH_ACCELERATION_AND_VELOCITY_SPLIT"
    )
    OFF_STRATUM_SINGLE_VECTOR_U1 = "OFF_STRATUM_SINGLE_VECTOR_U1"


ORBIT_TYPE_GENERIC_COMPLETENESS_STATUS = "UNPROVEN"

_REGISTERED_ORBIT_ACCEPTANCE: Mapping[
    OrbitAcceptanceCase,
    tuple[int, int, int, str, str],
] = {
    OrbitAcceptanceCase.PRINCIPAL_BASE: (
        12,
        9,
        3,
        "PRINCIPAL_FINITE_ISOTROPY",
        "FINITE_GENERIC",
    ),
    OrbitAcceptanceCase.PRINCIPAL_WITH_ACCELERATION: (
        15,
        12,
        3,
        "PRINCIPAL_FINITE_ISOTROPY",
        "FINITE_GENERIC",
    ),
    OrbitAcceptanceCase.PRINCIPAL_WITH_ACCELERATION_AND_VELOCITY_SPLIT: (
        18,
        15,
        3,
        "PRINCIPAL_FINITE_ISOTROPY",
        "FINITE_GENERIC",
    ),
    OrbitAcceptanceCase.OFF_STRATUM_SINGLE_VECTOR_U1: (
        3,
        1,
        2,
        "OFF_STRATUM_SINGLE_VECTOR",
        "U(1)",
    ),
}

_ORBIT_ACCEPTANCE_TOKEN = object()


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, int):
        raise JointAnisotropyStateError(f"{name} must be an integer")
    if value <= 0:
        raise JointAnisotropyStateError(f"{name} must be positive")
    return value


@dataclass(frozen=True)
class OrbitTypeAcceptance:
    """Exact acceptance of one registered orbit-quotient dimension case.

    The object records an algebraic quotient count only. It remains separate
    from response rank, data identifiability, and global orbit completeness.
    """

    case: OrbitAcceptanceCase
    state_dimension: int
    quotient_rank: int
    orbit_dimension: int
    stratum: str
    stabilizer: str
    generic_completeness_status: str = ORBIT_TYPE_GENERIC_COMPLETENESS_STATUS
    claim_ceiling: str = JOINT_STATE_CLAIM_CEILING
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _ORBIT_ACCEPTANCE_TOKEN:
            raise JointAnisotropyStateError("OrbitTypeAcceptance must be factory-built")
        if type(self.case) is not OrbitAcceptanceCase:
            raise JointAnisotropyStateError("case must use OrbitAcceptanceCase")
        state_dimension = _positive_integer(
            self.state_dimension,
            "state_dimension",
        )
        quotient_rank = _positive_integer(
            self.quotient_rank,
            "quotient_rank",
        )
        orbit_dimension = _positive_integer(
            self.orbit_dimension,
            "orbit_dimension",
        )
        expected = _REGISTERED_ORBIT_ACCEPTANCE[self.case]
        observed = (
            state_dimension,
            quotient_rank,
            orbit_dimension,
            _v1._text(self.stratum, "stratum"),
            _v1._text(self.stabilizer, "stabilizer"),
        )
        if observed != expected:
            raise JointAnisotropyStateError(
                "orbit acceptance must match its exact registered case"
            )
        if quotient_rank + orbit_dimension != state_dimension:
            raise JointAnisotropyStateError(
                "quotient rank plus orbit dimension must equal state dimension"
            )
        if self.generic_completeness_status != ORBIT_TYPE_GENERIC_COMPLETENESS_STATUS:
            raise JointAnisotropyStateError(
                "generic orbit completeness must remain UNPROVEN"
            )
        if self.claim_ceiling != JOINT_STATE_CLAIM_CEILING:
            raise JointAnisotropyStateError("claim ceiling drifted")
        object.__setattr__(self, "state_dimension", state_dimension)
        object.__setattr__(self, "quotient_rank", quotient_rank)
        object.__setattr__(self, "orbit_dimension", orbit_dimension)
        object.__setattr__(
            self,
            "_identity_seal",
            _v1._content_id(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "case": self.case.value,
            "claim_ceiling": self.claim_ceiling,
            "generic_completeness_status": self.generic_completeness_status,
            "orbit_dimension": self.orbit_dimension,
            "quotient_rank": self.quotient_rank,
            "schema": "HTT_ORBIT_TYPE_ACCEPTANCE_V1",
            "stabilizer": self.stabilizer,
            "state_dimension": self.state_dimension,
            "stratum": self.stratum,
        }

    def _assert_identity_sealed(self) -> None:
        if _v1._content_id(self._payload_unchecked()) != self._identity_seal:
            raise JointAnisotropyStateError(
                "orbit type acceptance identity drifted after construction"
            )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_orbit_type_acceptance(
    *,
    case: OrbitAcceptanceCase | str,
    state_dimension: object,
    quotient_rank: object,
) -> OrbitTypeAcceptance:
    """Accept exactly one registered stratum-aware quotient-rank triple."""

    normalized_case = _v1._enum(case, OrbitAcceptanceCase, "case")
    if not isinstance(normalized_case, OrbitAcceptanceCase):
        raise JointAnisotropyStateError("case must use OrbitAcceptanceCase")
    state = _positive_integer(state_dimension, "state_dimension")
    quotient = _positive_integer(quotient_rank, "quotient_rank")
    expected = _REGISTERED_ORBIT_ACCEPTANCE[normalized_case]
    if (state, quotient) != expected[:2]:
        raise JointAnisotropyStateError(
            "state_dimension and quotient_rank do not match the registered "
            f"{normalized_case.value} case"
        )
    return OrbitTypeAcceptance(
        case=normalized_case,
        state_dimension=state,
        quotient_rank=quotient,
        orbit_dimension=expected[2],
        stratum=expected[3],
        stabilizer=expected[4],
        _construction_token=_ORBIT_ACCEPTANCE_TOKEN,
    )


__all__ = [
    *_v1.__all__,
    "ORBIT_TYPE_GENERIC_COMPLETENESS_STATUS",
    "OrbitAcceptanceCase",
    "OrbitTypeAcceptance",
    "build_orbit_type_acceptance",
]
