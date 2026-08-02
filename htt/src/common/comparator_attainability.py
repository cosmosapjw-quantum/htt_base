"""Typed PR-190 comparator-attainability programme.

The registered claim is conjunctive: algebraic, constraint, local-dynamical,
and global-dynamical sharpness must all hold for both endpoints and every
interior comparator value.  This module deliberately preserves a negative
scientific result.  A syntactically valid :class:`JointAnisotropyState` is not
automatically a physical Einstein--matter witness.

In particular, the registered lower endpoint assigns non-zero ``W2`` to the
Bianchi-I hypersurface normal.  That congruence is hypersurface orthogonal, so
its vorticity is zero.  The mismatch refutes the constraint-level witness and
prevents promotion to either dynamical level.  The statement is not weakened
by silently moving ``W2`` to a tilted matter threading.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from fractions import Fraction
import hashlib
import json
import math
from types import MappingProxyType
from typing import ClassVar, Mapping, Sequence

import numpy as np

from common.enum_compat import StrEnum
from common.joint_anisotropy_state import (
    BetaSemanticRole,
    CongruenceKinematics,
    GeometryState,
    JointAnisotropyState,
    JointStateSourceKind,
    MissingComponentStatus,
    UnitsConvention,
    VelocityNormalization,
    build_velocity_frame_bundle,
    missing_component,
)
from common.orbit_catalogue_v3 import (
    OrbitCatalogueV3Report,
    build_orbit_catalogue_v3_spec,
    orbit_catalogue_v3,
)
from common.orbit_nonlinearity import STF5_CARTESIAN_BASIS, stf5_to_matrix
from common.transfer_registry import TransferSource


class ComparatorAttainabilityError(ValueError):
    """Raised when a PR-190 witness or programme result is inconsistent."""


class EndpointKind(StrEnum):
    LOWER = "LOWER"
    INTERIOR_CHALLENGE = "INTERIOR_CHALLENGE"
    UPPER = "UPPER"


class SolutionClass(StrEnum):
    BIANCHI_I_HOMOGENEOUS = "BIANCHI_I_HOMOGENEOUS"
    BIANCHI_V_HOMOGENEOUS = "BIANCHI_V_HOMOGENEOUS"


class CongruenceClass(StrEnum):
    HYPERSURFACE_NORMAL = "HYPERSURFACE_NORMAL"
    ROTATING_MATTER_THREADING = "ROTATING_MATTER_THREADING"


class SharpnessLevel(StrEnum):
    ALGEBRAIC = "ALGEBRAIC"
    CONSTRAINT = "CONSTRAINT"
    LOCAL_DYNAMICAL = "LOCAL_DYNAMICAL"
    GLOBAL_DYNAMICAL = "GLOBAL_DYNAMICAL"


class SharpnessStatus(StrEnum):
    ATTAINED = "ATTAINED"
    REFUTED = "REFUTED"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ProgrammeOutcome(StrEnum):
    FULL_TYPED_DYNAMICAL_SHARPNESS_CANDIDATE = (
        "FULL_TYPED_DYNAMICAL_SHARPNESS_CANDIDATE"
    )
    FULL_TYPED_DYNAMICAL_SHARPNESS_REFUTED = (
        "FULL_TYPED_DYNAMICAL_SHARPNESS_REFUTED"
    )
    FULL_TYPED_DYNAMICAL_SHARPNESS_BLOCKED_WITH_RECEIPT = (
        "FULL_TYPED_DYNAMICAL_SHARPNESS_BLOCKED_WITH_RECEIPT"
    )


PR190_CLAIM_CEILING = "theorem_candidate"
PR190_THEOREM_CAPABILITY = "WITHHELD_PENDING_PR285"
PR190_PUBLIC_USE = False
PR190_TRANSFER_SOURCE = TransferSource.NONE
PR190_METRIC_SIGNATURE = "(-,+,+,+)"
PR190_COMPARATOR = "x_C=Sigma2-W2+Omega_tilt+DeltaOmega_k"
PR190_ALLOWED_USE = (
    "typed comparator attainability audit",
    "receipt-bearing negative scientific result",
    "PR-285 theorem-candidate input",
)
PR190_FORBIDDEN_USE = (
    "observed-data inference",
    "native solver or native morphology atlas result",
    "Bianchi family identification",
    "theorem capability before PR-285 adjudication",
)

_WITNESS_TOKEN = object()
_STAGE_TOKEN = object()
_REPORT_TOKEN = object()
_TOLERANCE = 1.0e-12


def _content_id(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ComparatorAttainabilityError(
            f"{name} must be non-empty trimmed text"
        )
    return value


def _fraction(value: object, name: str) -> Fraction:
    if isinstance(value, bool):
        raise ComparatorAttainabilityError(f"{name} must not be boolean")
    try:
        out = Fraction(value)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ComparatorAttainabilityError(
            f"{name} must be a finite rational value"
        ) from exc
    if not math.isfinite(float(out)):
        raise ComparatorAttainabilityError(f"{name} must be finite")
    return out


@dataclass(frozen=True)
class MatterModelBinding:
    """Exact antipodal-pair matter identity used by all registered fixtures.

    The aggregate typed state intentionally does not invent one net velocity
    vector for two counter-streaming species.  ``Omega_tilt`` is instead
    recomputed from the exact species weights stored here.
    """

    model_id: str
    equation_of_state_w: Fraction
    omega_m_total: Fraction
    stream_density_fractions: tuple[Fraction, ...]
    stream_rapidity_signs: tuple[int, ...]
    sinh_squared_rapidity: Fraction
    frame: str

    def __post_init__(self) -> None:
        _text(self.model_id, "model_id")
        object.__setattr__(
            self,
            "equation_of_state_w",
            _fraction(self.equation_of_state_w, "equation_of_state_w"),
        )
        omega_m = _fraction(self.omega_m_total, "omega_m_total")
        if omega_m <= 0:
            raise ComparatorAttainabilityError("omega_m_total must be positive")
        object.__setattr__(self, "omega_m_total", omega_m)
        weights = tuple(
            _fraction(value, "stream_density_fractions")
            for value in self.stream_density_fractions
        )
        signs = tuple(self.stream_rapidity_signs)
        if (
            len(weights) != 2
            or weights != (Fraction(1, 2), Fraction(1, 2))
            or signs != (1, -1)
        ):
            raise ComparatorAttainabilityError(
                "PR-190 requires the registered equal-density antipodal pair"
            )
        object.__setattr__(self, "stream_density_fractions", weights)
        rapidity = _fraction(
            self.sinh_squared_rapidity,
            "sinh_squared_rapidity",
        )
        if rapidity < 0:
            raise ComparatorAttainabilityError(
                "sinh_squared_rapidity must be non-negative"
            )
        object.__setattr__(self, "sinh_squared_rapidity", rapidity)
        _text(self.frame, "matter frame")

    @property
    def omega_tilt(self) -> Fraction:
        return (
            (1 + self.equation_of_state_w)
            * self.omega_m_total
            * sum(self.stream_density_fractions, Fraction(0))
            * self.sinh_squared_rapidity
        )

    @property
    def net_flux_parity_sum(self) -> Fraction:
        return sum(
            sign * weight
            for sign, weight in zip(
                self.stream_rapidity_signs,
                self.stream_density_fractions,
                strict=True,
            )
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "equation_of_state_w": str(self.equation_of_state_w),
            "frame": self.frame,
            "model_id": self.model_id,
            "net_flux_parity_sum": str(self.net_flux_parity_sum),
            "omega_m_total": str(self.omega_m_total),
            "omega_tilt": str(self.omega_tilt),
            "sinh_squared_rapidity": str(self.sinh_squared_rapidity),
            "stream_density_fractions": [
                str(value) for value in self.stream_density_fractions
            ],
            "stream_rapidity_signs": list(self.stream_rapidity_signs),
        }


@dataclass(frozen=True)
class RegisteredTarget:
    endpoint_id: str
    kind: EndpointKind
    solution_class: SolutionClass
    congruence_class: CongruenceClass
    sigma2: Fraction
    w2: Fraction
    omega_tilt: Fraction
    delta_omega_k: Fraction
    x_c: Fraction

    def as_payload(self) -> dict[str, str]:
        return {
            "DeltaOmega_k": str(self.delta_omega_k),
            "Omega_tilt": str(self.omega_tilt),
            "Sigma2": str(self.sigma2),
            "W2": str(self.w2),
            "x_C": str(self.x_c),
        }


REGISTERED_TARGETS: Mapping[EndpointKind, RegisteredTarget] = MappingProxyType(
    {
        EndpointKind.LOWER: RegisteredTarget(
            endpoint_id="PR190-LOWER-XC-11-100",
            kind=EndpointKind.LOWER,
            solution_class=SolutionClass.BIANCHI_I_HOMOGENEOUS,
            congruence_class=CongruenceClass.HYPERSURFACE_NORMAL,
            sigma2=Fraction(3, 25),
            w2=Fraction(1, 25),
            omega_tilt=Fraction(3, 100),
            delta_omega_k=Fraction(0),
            x_c=Fraction(11, 100),
        ),
        EndpointKind.INTERIOR_CHALLENGE: RegisteredTarget(
            endpoint_id="PR190-INTERIOR-XC-12-100",
            kind=EndpointKind.INTERIOR_CHALLENGE,
            solution_class=SolutionClass.BIANCHI_I_HOMOGENEOUS,
            congruence_class=CongruenceClass.HYPERSURFACE_NORMAL,
            sigma2=Fraction(3, 25),
            w2=Fraction(3, 100),
            omega_tilt=Fraction(3, 100),
            delta_omega_k=Fraction(0),
            x_c=Fraction(3, 25),
        ),
        EndpointKind.UPPER: RegisteredTarget(
            endpoint_id="PR190-UPPER-XC-17-100",
            kind=EndpointKind.UPPER,
            solution_class=SolutionClass.BIANCHI_V_HOMOGENEOUS,
            congruence_class=CongruenceClass.HYPERSURFACE_NORMAL,
            sigma2=Fraction(3, 25),
            w2=Fraction(0),
            omega_tilt=Fraction(3, 100),
            delta_omega_k=Fraction(1, 50),
            x_c=Fraction(17, 100),
        ),
    }
)


def build_registered_matter_model(*, frame: str) -> MatterModelBinding:
    return MatterModelBinding(
        model_id="equal-density-antipodal-dust-pair-plus-Lambda",
        equation_of_state_w=Fraction(0),
        omega_m_total=Fraction(3, 10),
        stream_density_fractions=(Fraction(1, 2), Fraction(1, 2)),
        stream_rapidity_signs=(1, -1),
        sinh_squared_rapidity=Fraction(1, 10),
        frame=frame,
    )


def build_registered_typed_witnesses() -> tuple[EndpointWitnessBinding, ...]:
    """Build the three frozen typed fixtures used by the PR-190 programme.

    These are target states, not automatically admissible solutions.  The
    evaluator is responsible for detecting the lower/interior Frobenius
    contradiction.
    """

    frame = "homogeneous orthonormal frame"
    congruence = "hypersurface-normal n"
    epoch = "initial homogeneous slice t=t0"
    scale = "group-invariant homogeneous slice"
    perturbative_order = "exact homogeneous initial-data target"
    catalogue_spec = build_orbit_catalogue_v3_spec(
        catalogue_id="PR190-TYPED-ENDPOINT-ORBIT-V3"
    )
    sigma = (0.2, -0.2, 0.0, 0.0, 0.0)
    omega_by_kind = {
        EndpointKind.LOWER: (math.sqrt(1.0 / 75.0), 0.0, 0.0),
        EndpointKind.INTERIOR_CHALLENGE: (0.1, 0.0, 0.0),
        EndpointKind.UPPER: (0.0, 0.0, 0.0),
    }
    receipt_by_kind = {
        EndpointKind.LOWER: (
            "docs/research_program/THEOREM_REGISTRY.yaml#KE-DYN"
        ),
        EndpointKind.INTERIOR_CHALLENGE: (
            "docs/research_program/THEOREM_REGISTRY.yaml#T3-int"
        ),
        EndpointKind.UPPER: (
            "docs/research_program/THEOREM_REGISTRY.yaml#T3-full"
        ),
    }
    out: list[EndpointWitnessBinding] = []
    for kind in EndpointKind:
        target = REGISTERED_TARGETS[kind]
        acceleration = missing_component(
            "acceleration_polar3",
            "PR-190 target does not register an acceleration component",
            status=MissingComponentStatus.ABSTAIN,
            required_for=("non-geodesic dynamical development",),
        )
        kinematics = CongruenceKinematics(
            sigma_stf5=sigma,
            omega_axial3=omega_by_kind[kind],
            acceleration_polar3=acceleration,
            frame=frame,
            congruence_id=congruence,
            epoch_window=epoch,
            averaging_scale=scale,
            basis=STF5_CARTESIAN_BASIS,
            units_convention=(
                UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
            ),
            velocity_normalization=(
                VelocityNormalization.BETA_EQUALS_V_OVER_C
            ),
            perturbative_order=perturbative_order,
            acceleration_normalization=None,
        )
        velocity = build_velocity_frame_bundle(
            beta_RO=missing_component(
                "beta_RO",
                "no single aggregate observer velocity represents the antipodal pair",
                status=MissingComponentStatus.ABSTAIN,
            ),
            beta_RM=missing_component(
                "beta_RM",
                "two matter streams have opposite registered rapidities",
                status=MissingComponentStatus.ABSTAIN,
            ),
            beta_MO=missing_component(
                "beta_MO",
                "observer-to-matter component is not needed by the target",
                status=MissingComponentStatus.ABSTAIN,
            ),
            coordinate_frame=frame,
            radiation_frame_id="radiation-rest-frame",
            matter_frame_id="antipodal-dust-pair-frame-bundle",
            observer_frame_id="registered-observer-frame",
            basis=STF5_CARTESIAN_BASIS,
            epoch_window=epoch,
            averaging_scale=scale,
            first_order_beta_ceiling=0.1,
        )
        geometry = GeometryState(
            delta_omega_k=float(target.delta_omega_k),
            frame=frame,
            congruence_id=congruence,
            epoch_window=epoch,
            averaging_scale=scale,
            basis=STF5_CARTESIAN_BASIS,
            units_convention=(
                UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
            ),
            perturbative_order=perturbative_order,
        )
        state = JointAnisotropyState(
            congruence_kinematics=kinematics,
            velocity_frames=velocity,
            geometry_state=geometry,
            frame=frame,
            congruence=congruence,
            epoch_window=epoch,
            averaging_scale=scale,
            basis=STF5_CARTESIAN_BASIS,
            units_convention=(
                UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
            ),
            perturbative_order=perturbative_order,
            beta_semantic_role=BetaSemanticRole.DIRECT_STATE,
            transfer_source=TransferSource.NONE,
            transfer_spec=None,
            source_kind=JointStateSourceKind.DIRECT,
            source_identity=target.endpoint_id,
        )
        orbit = orbit_catalogue_v3(state, catalogue_spec)
        matter = build_registered_matter_model(frame=frame)
        out.append(
            bind_registered_witness(
                kind=kind,
                state=state,
                orbit_report=orbit,
                matter_model=matter,
                solution_receipt=receipt_by_kind[kind],
            )
        )
    return tuple(out)


def _computed_invariants(
    state: JointAnisotropyState,
    matter: MatterModelBinding,
) -> dict[str, float]:
    sigma = stf5_to_matrix(state.congruence_kinematics.sigma_stf5)
    omega = np.asarray(
        state.congruence_kinematics.omega_axial3,
        dtype=float,
    )
    sigma2 = 1.5 * float(np.sum(sigma * sigma))
    w2 = 3.0 * float(omega @ omega)
    omega_tilt = float(matter.omega_tilt)
    delta = float(state.geometry_state.delta_omega_k)
    return {
        "Sigma2": sigma2,
        "W2": w2,
        "Omega_tilt": omega_tilt,
        "DeltaOmega_k": delta,
        "x_C": sigma2 - w2 + omega_tilt + delta,
    }


@dataclass(frozen=True)
class EndpointWitnessBinding:
    """Factory-only state/orbit/matter binding for one registered target."""

    target: RegisteredTarget
    state: JointAnisotropyState
    orbit_report: OrbitCatalogueV3Report
    matter_model: MatterModelBinding
    epoch_window: str
    averaging_scale: str
    solution_receipt: str
    computed_invariants: Mapping[str, float]
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _WITNESS_TOKEN:
            raise ComparatorAttainabilityError(
                "EndpointWitnessBinding must be created by "
                "bind_registered_witness"
            )
        if type(self.target) is not RegisteredTarget:
            raise ComparatorAttainabilityError(
                "target must be an exact RegisteredTarget"
            )
        if type(self.state) is not JointAnisotropyState:
            raise ComparatorAttainabilityError(
                "state must be an exact JointAnisotropyState"
            )
        if type(self.orbit_report) is not OrbitCatalogueV3Report:
            raise ComparatorAttainabilityError(
                "orbit_report must be an exact OrbitCatalogueV3Report"
            )
        if type(self.matter_model) is not MatterModelBinding:
            raise ComparatorAttainabilityError(
                "matter_model must be an exact MatterModelBinding"
            )
        _text(self.epoch_window, "epoch_window")
        _text(self.averaging_scale, "averaging_scale")
        _text(self.solution_receipt, "solution_receipt")
        if self.orbit_report.source_state_id != self.state.content_id:
            raise ComparatorAttainabilityError(
                "orbit report does not bind the supplied state identity"
            )
        if self.state.transfer_source is not PR190_TRANSFER_SOURCE:
            raise ComparatorAttainabilityError(
                "PR-190 registered witnesses must be transfer-free"
            )
        if (
            self.state.epoch_window != self.epoch_window
            or self.state.averaging_scale != self.averaging_scale
        ):
            raise ComparatorAttainabilityError(
                "witness epoch/scale does not match the typed state"
            )
        if self.matter_model.frame != self.state.frame:
            raise ComparatorAttainabilityError(
                "matter model and typed state must use the same frame"
            )
        if (
            self.target.congruence_class
            is CongruenceClass.HYPERSURFACE_NORMAL
            and self.state.congruence != "hypersurface-normal n"
        ):
            raise ComparatorAttainabilityError(
                "registered normal-congruence witness has a congruence mismatch"
            )
        computed = dict(self.computed_invariants)
        if computed != _computed_invariants(self.state, self.matter_model):
            raise ComparatorAttainabilityError(
                "computed invariants must be factory-derived"
            )
        object.__setattr__(
            self,
            "computed_invariants",
            MappingProxyType(computed),
        )

    @property
    def witness_id(self) -> str:
        return _content_id(self.as_payload())

    @property
    def algebraically_matches_target(self) -> bool:
        expected = self.target.as_payload()
        return all(
            math.isclose(
                self.computed_invariants[name],
                float(Fraction(value)),
                rel_tol=0.0,
                abs_tol=_TOLERANCE,
            )
            for name, value in expected.items()
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "averaging_scale": self.averaging_scale,
            "computed_invariants": {
                name: self.computed_invariants[name]
                for name in sorted(self.computed_invariants)
            },
            "congruence": self.state.congruence,
            "congruence_class": self.target.congruence_class.value,
            "epoch_window": self.epoch_window,
            "frame": self.state.frame,
            "matter_model": self.matter_model.as_payload(),
            "orbit_report_id": self.orbit_report.report_id,
            "solution_class": self.target.solution_class.value,
            "solution_receipt": self.solution_receipt,
            "state_id": self.state.content_id,
            "target": self.target.as_payload(),
            "target_id": self.target.endpoint_id,
            "target_kind": self.target.kind.value,
            "transfer_source": self.state.transfer_source.value,
            "units_convention": self.state.units_convention.value,
        }


def bind_registered_witness(
    *,
    kind: EndpointKind,
    state: JointAnisotropyState,
    orbit_report: OrbitCatalogueV3Report,
    matter_model: MatterModelBinding,
    solution_receipt: str,
) -> EndpointWitnessBinding:
    if type(kind) is not EndpointKind:
        raise ComparatorAttainabilityError(
            "kind must be an exact EndpointKind"
        )
    checked = JointAnisotropyState.from_payload(state.to_payload())
    if checked.content_id != state.content_id:
        raise ComparatorAttainabilityError(
            "typed state failed canonical content replay"
        )
    return EndpointWitnessBinding(
        target=REGISTERED_TARGETS[kind],
        state=checked,
        orbit_report=orbit_report,
        matter_model=matter_model,
        epoch_window=checked.epoch_window,
        averaging_scale=checked.averaging_scale,
        solution_receipt=solution_receipt,
        computed_invariants=_computed_invariants(checked, matter_model),
        _construction_token=_WITNESS_TOKEN,
    )


@dataclass(frozen=True)
class SharpnessStageDecision:
    target_id: str
    level: SharpnessLevel
    status: SharpnessStatus
    premise_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    reason: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _STAGE_TOKEN:
            raise ComparatorAttainabilityError(
                "SharpnessStageDecision is evaluator-only"
            )
        _text(self.target_id, "target_id")
        if type(self.level) is not SharpnessLevel:
            raise ComparatorAttainabilityError(
                "level must be an exact SharpnessLevel"
            )
        if type(self.status) is not SharpnessStatus:
            raise ComparatorAttainabilityError(
                "status must be an exact SharpnessStatus"
            )
        if not self.premise_ids or not self.evidence_refs:
            raise ComparatorAttainabilityError(
                "stage decisions require premise and evidence identities"
            )
        _text(self.reason, "reason")

    def as_payload(self) -> dict[str, object]:
        return {
            "evidence_refs": list(self.evidence_refs),
            "level": self.level.value,
            "premise_ids": list(self.premise_ids),
            "reason": self.reason,
            "status": self.status.value,
            "target_id": self.target_id,
        }


def _decision(
    witness: EndpointWitnessBinding,
    level: SharpnessLevel,
    status: SharpnessStatus,
    *,
    premises: Sequence[str],
    evidence: Sequence[str],
    reason: str,
) -> SharpnessStageDecision:
    return SharpnessStageDecision(
        target_id=witness.target.endpoint_id,
        level=level,
        status=status,
        premise_ids=tuple(premises),
        evidence_refs=tuple(evidence),
        reason=reason,
        _construction_token=_STAGE_TOKEN,
    )


@dataclass(frozen=True)
class ComparatorAttainabilityReport:
    witnesses: tuple[EndpointWitnessBinding, ...]
    decisions: tuple[SharpnessStageDecision, ...]
    outcome: ProgrammeOutcome
    execution_resolution: str
    success_dependency_satisfied: bool
    decisive_falsifier: str | None
    theorem_capability: str = PR190_THEOREM_CAPABILITY
    claim_ceiling: str = PR190_CLAIM_CEILING
    public_use: bool = PR190_PUBLIC_USE
    _construction_token: InitVar[object] = None

    allowed_use: ClassVar[tuple[str, ...]] = PR190_ALLOWED_USE
    forbidden_use: ClassVar[tuple[str, ...]] = PR190_FORBIDDEN_USE

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise ComparatorAttainabilityError(
                "ComparatorAttainabilityReport is evaluator-only"
            )
        expected_targets = tuple(
            REGISTERED_TARGETS[kind].endpoint_id for kind in EndpointKind
        )
        if tuple(item.target.endpoint_id for item in self.witnesses) != expected_targets:
            raise ComparatorAttainabilityError(
                "report must contain the lower, interior, and upper witnesses in order"
            )
        expected_pairs = tuple(
            (target, level)
            for target in expected_targets
            for level in SharpnessLevel
        )
        actual_pairs = tuple(
            (item.target_id, item.level) for item in self.decisions
        )
        if actual_pairs != expected_pairs:
            raise ComparatorAttainabilityError(
                "report decisions must cover every target and sharpness level"
            )
        refuted = any(
            item.status is SharpnessStatus.REFUTED for item in self.decisions
        )
        if refuted:
            if (
                self.outcome
                is not ProgrammeOutcome.FULL_TYPED_DYNAMICAL_SHARPNESS_REFUTED
                or self.execution_resolution
                != "COMPLETED_FAILED_WITH_RECEIPT"
                or self.success_dependency_satisfied is not False
                or self.decisive_falsifier is None
            ):
                raise ComparatorAttainabilityError(
                    "refuted programme must preserve the failed receipt and close its success edge"
                )
        if self.theorem_capability != PR190_THEOREM_CAPABILITY:
            raise ComparatorAttainabilityError(
                "PR-190 cannot grant theorem capability before PR-285"
            )
        if self.claim_ceiling != PR190_CLAIM_CEILING or self.public_use is not False:
            raise ComparatorAttainabilityError(
                "PR-190 claim ceiling or public-use boundary drifted"
            )

    @property
    def report_id(self) -> str:
        return _content_id(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "claim_ceiling": self.claim_ceiling,
            "comparator": PR190_COMPARATOR,
            "decisive_falsifier": self.decisive_falsifier,
            "decisions": [item.as_payload() for item in self.decisions],
            "execution_resolution": self.execution_resolution,
            "forbidden_use": list(self.forbidden_use),
            "metric_signature": PR190_METRIC_SIGNATURE,
            "outcome": self.outcome.value,
            "public_use": self.public_use,
            "schema": "HTT_PR190_COMPARATOR_ATTAINABILITY_REPORT_V1",
            "success_dependency_satisfied": self.success_dependency_satisfied,
            "theorem_capability": self.theorem_capability,
            "transfer_source": PR190_TRANSFER_SOURCE.value,
            "witnesses": [item.as_payload() for item in self.witnesses],
        }


def evaluate_registered_attainability(
    witnesses: Sequence[EndpointWitnessBinding],
) -> ComparatorAttainabilityReport:
    """Evaluate the unweakened registered programme, fail-closed by level."""

    ordered = tuple(witnesses)
    if (
        len(ordered) != len(EndpointKind)
        or tuple(item.target.kind for item in ordered) != tuple(EndpointKind)
        or any(type(item) is not EndpointWitnessBinding for item in ordered)
    ):
        raise ComparatorAttainabilityError(
            "witnesses must exactly cover lower, interior challenge, and upper"
        )

    decisions: list[SharpnessStageDecision] = []
    for witness in ordered:
        algebraic = witness.algebraically_matches_target
        decisions.append(
            _decision(
                witness,
                SharpnessLevel.ALGEBRAIC,
                SharpnessStatus.ATTAINED if algebraic else SharpnessStatus.REFUTED,
                premises=("PR189-JOINT-SUPPORT", "PR190-TYPED-INVARIANTS"),
                evidence=(witness.witness_id,),
                reason=(
                    "typed state and matter binding reproduce the registered exact comparator target"
                    if algebraic
                    else "typed state does not reproduce the registered comparator target"
                ),
            )
        )

        normal_w2_conflict = (
            witness.target.solution_class
            is SolutionClass.BIANCHI_I_HOMOGENEOUS
            and witness.target.congruence_class
            is CongruenceClass.HYPERSURFACE_NORMAL
            and witness.target.w2 > 0
        )
        if not algebraic:
            constraint_status = SharpnessStatus.BLOCKED
            constraint_reason = "constraint evaluation blocked by algebraic target mismatch"
        elif normal_w2_conflict:
            constraint_status = SharpnessStatus.REFUTED
            constraint_reason = (
                "Bianchi-I hypersurface-normal Frobenius identity requires W2=0, "
                f"but the same-frame target requires W2={witness.target.w2}"
            )
        elif witness.target.kind is EndpointKind.UPPER:
            constraint_status = SharpnessStatus.ATTAINED
            constraint_reason = (
                "registered Bianchi-V transverse-shear receipt supplies exact Gauss and momentum closure; "
                "this does not establish endpoint dynamics"
            )
        else:
            constraint_status = SharpnessStatus.INCONCLUSIVE
            constraint_reason = "no registered same-frame constraint proof is available"
        decisions.append(
            _decision(
                witness,
                SharpnessLevel.CONSTRAINT,
                constraint_status,
                premises=(
                    "FROBENIUS-HYPERSURFACE-NORMAL",
                    "GAUSS-MOMENTUM-MATTER-COMPATIBILITY",
                ),
                evidence=(
                    witness.solution_receipt,
                    "docs/research_program/THEOREM_REGISTRY.yaml#T3-full",
                ),
                reason=constraint_reason,
            )
        )

        if constraint_status is SharpnessStatus.REFUTED:
            local_status = SharpnessStatus.BLOCKED
            local_reason = "local development cannot promote a refuted constraint witness"
        elif constraint_status is not SharpnessStatus.ATTAINED:
            local_status = SharpnessStatus.BLOCKED
            local_reason = "local development requires an attained constraint witness"
        else:
            local_status = SharpnessStatus.INCONCLUSIVE
            local_reason = (
                "KE-DYN proves a registered Omega_k>0 ansatz development, but no receipt binds "
                "that trajectory to this exact upper endpoint state identity"
            )
        decisions.append(
            _decision(
                witness,
                SharpnessLevel.LOCAL_DYNAMICAL,
                local_status,
                premises=("CONSTRAINT-ATTAINED", "ENDPOINT-BOUND-LOCAL-DEVELOPMENT"),
                evidence=(
                    "docs/research_program/THEOREM_REGISTRY.yaml#KE-DYN",
                    witness.witness_id,
                ),
                reason=local_reason,
            )
        )

        if local_status is SharpnessStatus.REFUTED:
            global_status = SharpnessStatus.BLOCKED
            global_reason = "global development cannot promote a refuted local witness"
        elif local_status is not SharpnessStatus.ATTAINED:
            global_status = SharpnessStatus.BLOCKED
            global_reason = "global sharpness requires an attained endpoint-bound local development"
        else:
            global_status = SharpnessStatus.INCONCLUSIVE
            global_reason = "no registered global endpoint-bound evolution receipt is available"
        decisions.append(
            _decision(
                witness,
                SharpnessLevel.GLOBAL_DYNAMICAL,
                global_status,
                premises=("LOCAL-DYNAMICAL-ATTAINED", "DECLARED-EVOLUTION-INTERVAL"),
                evidence=(
                    "docs/research_program/strengthening/pr190_spec.yaml#sharpness_levels",
                    witness.witness_id,
                ),
                reason=global_reason,
            )
        )

    refuted = tuple(
        item for item in decisions if item.status is SharpnessStatus.REFUTED
    )
    if refuted:
        outcome = ProgrammeOutcome.FULL_TYPED_DYNAMICAL_SHARPNESS_REFUTED
        resolution = "COMPLETED_FAILED_WITH_RECEIPT"
        success = False
        decisive = (
            "registered lower and interior Bianchi-I hypersurface-normal targets "
            "require nonzero W2 although Frobenius forces W2=0"
        )
    elif all(item.status is SharpnessStatus.ATTAINED for item in decisions):
        outcome = ProgrammeOutcome.FULL_TYPED_DYNAMICAL_SHARPNESS_CANDIDATE
        resolution = "COMPLETED_SUCCESS"
        success = True
        decisive = None
    else:
        outcome = (
            ProgrammeOutcome.FULL_TYPED_DYNAMICAL_SHARPNESS_BLOCKED_WITH_RECEIPT
        )
        resolution = "BLOCKED_WITH_RECEIPT"
        success = False
        decisive = None
    return ComparatorAttainabilityReport(
        witnesses=ordered,
        decisions=tuple(decisions),
        outcome=outcome,
        execution_resolution=resolution,
        success_dependency_satisfied=success,
        decisive_falsifier=decisive,
        _construction_token=_REPORT_TOKEN,
    )


__all__ = [
    "ComparatorAttainabilityError",
    "ComparatorAttainabilityReport",
    "CongruenceClass",
    "EndpointKind",
    "EndpointWitnessBinding",
    "MatterModelBinding",
    "ProgrammeOutcome",
    "REGISTERED_TARGETS",
    "SharpnessLevel",
    "SharpnessStageDecision",
    "SharpnessStatus",
    "SolutionClass",
    "bind_registered_witness",
    "build_registered_matter_model",
    "build_registered_typed_witnesses",
    "evaluate_registered_attainability",
]
