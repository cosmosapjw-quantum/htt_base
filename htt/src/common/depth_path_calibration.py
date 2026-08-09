"""Immutable PR-284 depth-path calibration contracts.

This module stores exact, content-addressed values only.  HTT evaluates the
finite-law premise and constructs reports through private token-gated builders;
callers cannot supply a proof status or probability bound directly.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
from fractions import Fraction
import hashlib
import json
from numbers import Integral, Rational
from typing import Sequence

from common.depth_path import DepthPath, DepthPathError, revalidate_depth_path
from common.vector_tensor_statistical_foundations import (
    VectorTensorStatisticalFoundationError,
    certify_finite_partition_tower,
)


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ReverseMartingalePremiseStatus(_StringEnum):
    PROVED_FINITE_REGISTERED_PATH = "PROVED_FINITE_REGISTERED_PATH"
    UNPROVED_REQUIRES_MATCHED_MOCKS = "UNPROVED_REQUIRES_MATCHED_MOCKS"


class DepthPathCalibrationStatus(_StringEnum):
    BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE = (
        "BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE"
    )
    MATCHED_MOCKS_REQUIRED = "MATCHED_MOCKS_REQUIRED"


PR284_OWNER = "HTT"
PR284_CLAIM_TIER = "diagnostic_only"
PR284_TRANSFER_SOURCE = "none"
PR284_FAMILY_GATE = "BLOCKED_PRE_NATIVE_ATLAS"
PR284_ALLOWED_USE = (
    "synthetic exact replay of one finite registered depth path",
    "conservative premise-bound path-maximum diagnostic",
    "routing to a content-addressed matched-mock plan when the premise is unproved",
)
PR284_FORBIDDEN_USE = (
    "free calibration from support nesting alone",
    "observed-data significance, posterior, evidence, or source attribution",
    "optional-stopping, convergence, or general reverse-martingale theorem claim",
    "native validation, geometry detection, or Bianchi family identification",
)
PR284_SOURCE_ORACLE_ID = "TF-11-MASK-PATH-MARTINGALE"
PR284_SOURCE_STATUS = "ORACLE_VERIFIED"
PR284_TYPED_PROOF_VERDICT = "PROVED_FINITE_REGISTERED_PATH"
PR284_SOURCE_ADJUDICATION = "NOT_ADJUDICATED"
PR284_RELATION_TO_SOURCE = "FINITE_REGISTERED_PATH_ONLY"
PR284_FAST_ORACLE_CAVEAT = (
    "known fast TF-11 simulation-oracle instability is excluded from acceptance evidence"
)
PR284_EVENT_COMPARISON = "GREATER_THAN_OR_EQUAL_EXACT_SQUARES"


_LAW_TOKEN = object()
_SELECTION_TOKEN = object()
_THRESHOLD_TOKEN = object()
_MOCK_PLAN_TOKEN = object()
_REPORT_TOKEN = object()
_CALIBRATION_TOKEN = object()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DepthPathError(f"{name} must be non-empty trimmed text")
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    minimum: int = 1,
    unique: bool = True,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise DepthPathError(f"{name} must be a sequence of text")
    result = tuple(_text(value, name) for value in values)
    if len(result) < minimum:
        raise DepthPathError(f"{name} must contain at least {minimum} value(s)")
    if unique and len(result) != len(set(result)):
        raise DepthPathError(f"{name} must not contain duplicates")
    return result


def _exact_fraction(value: object, name: str) -> Fraction:
    if isinstance(value, bool):
        raise DepthPathError(f"{name} must be an exact rational")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, Integral):
        return Fraction(int(value), 1)
    if isinstance(value, Rational):
        return Fraction(value)
    raise DepthPathError(
        f"{name} must be an exact rational encoded as int or Fraction"
    )


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _assert_sealed(payload: object, seal: str, *, name: str) -> None:
    if _sha256_payload(payload) != seal:
        raise DepthPathError(f"{name} identity drifted after construction")


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
        raise DepthPathError(f"{name} must be a non-negative integer")
    return int(value)


def _conditional_values(
    *,
    weights: tuple[Fraction, ...],
    target: tuple[Fraction, ...],
    labels: tuple[str, ...],
) -> tuple[Fraction, ...]:
    mass: dict[str, Fraction] = {}
    weighted: dict[str, Fraction] = {}
    for probability, value, label in zip(weights, target, labels, strict=True):
        mass[label] = mass.get(label, Fraction()) + probability
        weighted[label] = weighted.get(label, Fraction()) + probability * value
    if any(value <= 0 for value in mass.values()):
        raise DepthPathError("every conditional cell must have positive mass")
    conditional = {label: weighted[label] / mass[label] for label in mass}
    return tuple(conditional[label] for label in labels)


@dataclass(frozen=True)
class DepthPathFiniteTargetLaw:
    law_id: str
    common_target_id: str
    atom_ids: tuple[str, ...]
    weights: tuple[Fraction, ...]
    common_target: tuple[Fraction, ...]
    registration_id: str
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _LAW_TOKEN:
            raise DepthPathError("DepthPathFiniteTargetLaw must be factory-built")
        for name in ("law_id", "common_target_id", "registration_id"):
            _text(getattr(self, name), name)
        atoms = _texts(self.atom_ids, "atom_ids", minimum=2)
        weights = tuple(_exact_fraction(value, "weights") for value in self.weights)
        target = tuple(
            _exact_fraction(value, "common_target") for value in self.common_target
        )
        if len(weights) != len(atoms) or len(target) != len(atoms):
            raise DepthPathError("atom_ids, weights, and common_target must align")
        if any(value <= 0 for value in weights) or sum(weights, Fraction()) != 1:
            raise DepthPathError(
                "weights must be positive exact probabilities summing to one"
            )
        object.__setattr__(self, "atom_ids", atoms)
        object.__setattr__(self, "weights", weights)
        object.__setattr__(self, "common_target", target)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "atom_ids": list(self.atom_ids),
            "common_target": [_fraction_text(value) for value in self.common_target],
            "common_target_id": self.common_target_id,
            "law_id": self.law_id,
            "registration_id": self.registration_id,
            "schema": "HTT_DEPTH_PATH_FINITE_TARGET_LAW_V1",
            "weights": [_fraction_text(value) for value in self.weights],
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="finite target law",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_depth_path_finite_target_law(
    *,
    law_id: str,
    common_target_id: str,
    atom_ids: Sequence[str],
    weights: Sequence[object],
    common_target: Sequence[object],
    registration_id: str,
) -> DepthPathFiniteTargetLaw:
    return DepthPathFiniteTargetLaw(
        law_id=law_id,
        common_target_id=common_target_id,
        atom_ids=tuple(atom_ids),
        weights=tuple(weights),
        common_target=tuple(common_target),
        registration_id=registration_id,
        _construction_token=_LAW_TOKEN,
    )


def revalidate_depth_path_finite_target_law(
    value: DepthPathFiniteTargetLaw,
) -> DepthPathFiniteTargetLaw:
    if type(value) is not DepthPathFiniteTargetLaw:
        raise TypeError("value must be an exact DepthPathFiniteTargetLaw")
    value.as_payload()
    return value


@dataclass(frozen=True)
class DepthPathSelectionContract:
    selection_id: str
    finite_target_law: DepthPathFiniteTargetLaw
    selected_atom_id: str
    selected_atom_index: int
    selection_rule_id: str
    registration_id: str
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SELECTION_TOKEN:
            raise DepthPathError("DepthPathSelectionContract must be factory-built")
        for name in (
            "selection_id",
            "selected_atom_id",
            "selection_rule_id",
            "registration_id",
        ):
            _text(getattr(self, name), name)
        law = revalidate_depth_path_finite_target_law(self.finite_target_law)
        index = _nonnegative_int(self.selected_atom_index, "selected_atom_index")
        if index >= len(law.atom_ids):
            raise DepthPathError("selected_atom_index is outside the finite law")
        if law.atom_ids[index] != self.selected_atom_id:
            raise DepthPathError("selected_atom_id does not match selected_atom_index")
        object.__setattr__(self, "selected_atom_index", index)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "finite_target_law_content_id": self.finite_target_law.content_id,
            "registration_id": self.registration_id,
            "schema": "HTT_DEPTH_PATH_SELECTION_CONTRACT_V1",
            "selected_atom_id": self.selected_atom_id,
            "selected_atom_index": self.selected_atom_index,
            "selection_id": self.selection_id,
            "selection_rule_id": self.selection_rule_id,
        }

    def _assert_identity_sealed(self) -> None:
        revalidate_depth_path_finite_target_law(self.finite_target_law)
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="selection contract",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_depth_path_selection_contract(
    *,
    selection_id: str,
    finite_target_law: DepthPathFiniteTargetLaw,
    selected_atom_id: str,
    selected_atom_index: int,
    selection_rule_id: str,
    registration_id: str,
) -> DepthPathSelectionContract:
    return DepthPathSelectionContract(
        selection_id=selection_id,
        finite_target_law=finite_target_law,
        selected_atom_id=selected_atom_id,
        selected_atom_index=selected_atom_index,
        selection_rule_id=selection_rule_id,
        registration_id=registration_id,
        _construction_token=_SELECTION_TOKEN,
    )


def revalidate_depth_path_selection_contract(
    value: DepthPathSelectionContract,
) -> DepthPathSelectionContract:
    if type(value) is not DepthPathSelectionContract:
        raise TypeError("value must be an exact DepthPathSelectionContract")
    value.as_payload()
    return value


@dataclass(frozen=True)
class DepthPathThresholdContract:
    contract_id: str
    multiplier: Fraction
    registration_id: str
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _THRESHOLD_TOKEN:
            raise DepthPathError("DepthPathThresholdContract must be factory-built")
        _text(self.contract_id, "contract_id")
        _text(self.registration_id, "registration_id")
        multiplier = _exact_fraction(self.multiplier, "multiplier")
        if multiplier <= 0:
            raise DepthPathError("multiplier must be positive")
        object.__setattr__(self, "multiplier", multiplier)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "event_comparison": PR284_EVENT_COMPARISON,
            "multiplier": _fraction_text(self.multiplier),
            "registration_id": self.registration_id,
            "schema": "HTT_DEPTH_PATH_THRESHOLD_CONTRACT_V1",
            "threshold_representation": "EXACT_LAMBDA_SQUARED_TIMES_SECOND_MOMENT",
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="threshold contract",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_depth_path_threshold_contract(
    *,
    contract_id: str,
    multiplier: object,
    registration_id: str,
) -> DepthPathThresholdContract:
    return DepthPathThresholdContract(
        contract_id=contract_id,
        multiplier=multiplier,
        registration_id=registration_id,
        _construction_token=_THRESHOLD_TOKEN,
    )


def revalidate_depth_path_threshold_contract(
    value: DepthPathThresholdContract,
) -> DepthPathThresholdContract:
    if type(value) is not DepthPathThresholdContract:
        raise TypeError("value must be an exact DepthPathThresholdContract")
    value.as_payload()
    return value


@dataclass(frozen=True)
class DepthPathMatchedMockPlan:
    plan_id: str
    path_content_id: str
    threshold_contract_content_id: str
    preprocessing_id: str
    estimator_id: str
    registration_id: str
    null_law_id: str
    mock_generator_id: str
    ensemble_policy_id: str
    seed_policy_id: str
    matching_variable_ids: tuple[str, ...]
    acceptance_rule_id: str
    multiplicity_rule_id: str
    null_mock_status: str = "required_not_executed"
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _MOCK_PLAN_TOKEN:
            raise DepthPathError("DepthPathMatchedMockPlan must be factory-built")
        for name in (
            "plan_id",
            "path_content_id",
            "threshold_contract_content_id",
            "preprocessing_id",
            "estimator_id",
            "registration_id",
            "null_law_id",
            "mock_generator_id",
            "ensemble_policy_id",
            "seed_policy_id",
            "acceptance_rule_id",
            "multiplicity_rule_id",
        ):
            _text(getattr(self, name), name)
        variables = _texts(
            self.matching_variable_ids,
            "matching_variable_ids",
            minimum=1,
        )
        if self.null_mock_status != "required_not_executed":
            raise DepthPathError("matched-mock plan is not execution evidence")
        object.__setattr__(self, "matching_variable_ids", variables)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "acceptance_rule_id": self.acceptance_rule_id,
            "ensemble_policy_id": self.ensemble_policy_id,
            "estimator_id": self.estimator_id,
            "matching_variable_ids": list(self.matching_variable_ids),
            "mock_generator_id": self.mock_generator_id,
            "multiplicity_rule_id": self.multiplicity_rule_id,
            "null_law_id": self.null_law_id,
            "null_mock_status": self.null_mock_status,
            "path_content_id": self.path_content_id,
            "plan_id": self.plan_id,
            "preprocessing_id": self.preprocessing_id,
            "registration_id": self.registration_id,
            "schema": "HTT_DEPTH_PATH_MATCHED_MOCK_PLAN_V1",
            "seed_policy_id": self.seed_policy_id,
            "threshold_contract_content_id": self.threshold_contract_content_id,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="matched-mock plan",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def _build_depth_path_matched_mock_plan_contract(**kwargs: object) -> DepthPathMatchedMockPlan:
    return DepthPathMatchedMockPlan(
        **kwargs,
        _construction_token=_MOCK_PLAN_TOKEN,
    )


def revalidate_depth_path_matched_mock_plan(
    value: DepthPathMatchedMockPlan,
) -> DepthPathMatchedMockPlan:
    if type(value) is not DepthPathMatchedMockPlan:
        raise TypeError("value must be an exact DepthPathMatchedMockPlan")
    value.as_payload()
    return value


@dataclass(frozen=True)
class DepthPathReverseMartingaleReport:
    report_id: str
    path: DepthPath
    path_content_id: str
    stratum_content_ids: tuple[str, ...]
    threshold_contract: DepthPathThresholdContract
    filtration_id: str
    filtration_direction: str
    preprocessing_id: str
    estimator_id: str
    premise_evidence_id: str
    premise_status: ReverseMartingalePremiseStatus
    finite_target_law: DepthPathFiniteTargetLaw | None
    selection_contract: DepthPathSelectionContract | None
    path_partitions: tuple[tuple[str, ...], ...]
    sigma_field_ids: tuple[str, ...]
    path_values: tuple[Fraction, ...]
    path_maximum_abs: Fraction | None
    path_maximum_content_id: str | None
    target_second_moment: Fraction | None
    exact_tower_equalities: tuple[bool, ...]
    exact_tower_report_content_id: str | None
    unresolved_reasons: tuple[str, ...]
    matched_mock_plan: DepthPathMatchedMockPlan | None
    owner: str = PR284_OWNER
    claim_tier: str = PR284_CLAIM_TIER
    transfer_source: str = PR284_TRANSFER_SOURCE
    observed_data_executed: bool = False
    public_use: bool = False
    family_identification_gate: str = PR284_FAMILY_GATE
    allowed_use: tuple[str, ...] = PR284_ALLOWED_USE
    forbidden_use: tuple[str, ...] = PR284_FORBIDDEN_USE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise DepthPathError(
                "DepthPathReverseMartingaleReport must be factory-built"
            )
        for name in (
            "report_id",
            "path_content_id",
            "filtration_id",
            "preprocessing_id",
            "estimator_id",
            "premise_evidence_id",
        ):
            _text(getattr(self, name), name)
        strata = _texts(self.stratum_content_ids, "stratum_content_ids", minimum=2)
        threshold = revalidate_depth_path_threshold_contract(self.threshold_contract)
        if self.filtration_direction != "DECREASING":
            raise DepthPathError("filtration direction must remain DECREASING")
        if type(self.premise_status) is not ReverseMartingalePremiseStatus:
            raise DepthPathError("premise_status must use ReverseMartingalePremiseStatus")
        partitions = tuple(
            _texts(row, "path_partitions", minimum=1, unique=False)
            for row in self.path_partitions
        )
        sigma_fields = tuple(self.sigma_field_ids)
        path_values = tuple(
            _exact_fraction(value, "path_values") for value in self.path_values
        )
        reasons = tuple(self.unresolved_reasons)
        if self.premise_status is ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH:
            if type(self.finite_target_law) is not DepthPathFiniteTargetLaw:
                raise DepthPathError("proved report requires an exact finite target law")
            law = revalidate_depth_path_finite_target_law(self.finite_target_law)
            if type(self.selection_contract) is not DepthPathSelectionContract:
                raise DepthPathError("proved report requires an exact selection contract")
            selection = revalidate_depth_path_selection_contract(self.selection_contract)
            if selection.finite_target_law.content_id != law.content_id:
                raise DepthPathError("selection contract is not bound to the finite law")
            if len(partitions) != len(strata) or len(sigma_fields) != len(strata):
                raise DepthPathError("one partition and sigma field are required per stratum")
            _texts(sigma_fields, "sigma_field_ids", minimum=len(strata))
            if any(len(row) != len(law.atom_ids) for row in partitions):
                raise DepthPathError("every partition must label the finite atom space")
            if len(path_values) != len(strata):
                raise DepthPathError("one exact path value is required per stratum")
            maximum = _exact_fraction(self.path_maximum_abs, "path_maximum_abs")
            second = _exact_fraction(
                self.target_second_moment,
                "target_second_moment",
            )
            if maximum != max(abs(value) for value in path_values):
                raise DepthPathError("path maximum does not match exact path values")
            if second <= 0:
                raise DepthPathError("target requires a positive second moment")
            _text(self.path_maximum_content_id, "path_maximum_content_id")
            _text(
                self.exact_tower_report_content_id,
                "exact_tower_report_content_id",
            )
            equalities = tuple(self.exact_tower_equalities)
            if len(equalities) != len(strata) - 1 or not all(
                type(value) is bool and value for value in equalities
            ):
                raise DepthPathError("proved report requires every exact tower equality")
            if reasons or self.matched_mock_plan is not None:
                raise DepthPathError("proved report must not carry matched-mock fallback")
        else:
            if self.finite_target_law is not None or self.selection_contract is not None:
                raise DepthPathError("unproved report must not carry a finite-law proof")
            if partitions or sigma_fields or path_values:
                raise DepthPathError("unproved report must not carry proved path values")
            if any(
                value is not None
                for value in (
                    self.path_maximum_abs,
                    self.path_maximum_content_id,
                    self.target_second_moment,
                    self.exact_tower_report_content_id,
                )
            ) or self.exact_tower_equalities:
                raise DepthPathError("unproved report must not carry bound premises")
            reasons = _texts(reasons, "unresolved_reasons", minimum=1, unique=False)
            if type(self.matched_mock_plan) is not DepthPathMatchedMockPlan:
                raise DepthPathError("unproved report requires an exact matched_mock_plan")
            plan = revalidate_depth_path_matched_mock_plan(self.matched_mock_plan)
            if (
                plan.path_content_id != self.path_content_id
                or plan.threshold_contract_content_id != threshold.content_id
                or plan.preprocessing_id != self.preprocessing_id
                or plan.estimator_id != self.estimator_id
            ):
                raise DepthPathError("matched_mock_plan is not bound to this report")
        if (
            self.owner != PR284_OWNER
            or self.claim_tier != PR284_CLAIM_TIER
            or self.transfer_source != PR284_TRANSFER_SOURCE
            or self.observed_data_executed is not False
            or self.public_use is not False
            or self.family_identification_gate != PR284_FAMILY_GATE
            or tuple(self.allowed_use) != PR284_ALLOWED_USE
            or tuple(self.forbidden_use) != PR284_FORBIDDEN_USE
        ):
            raise DepthPathError("PR-284 claim boundary drifted")
        object.__setattr__(self, "stratum_content_ids", strata)
        object.__setattr__(self, "path_partitions", partitions)
        object.__setattr__(self, "sigma_field_ids", sigma_fields)
        object.__setattr__(self, "path_values", path_values)
        object.__setattr__(self, "unresolved_reasons", reasons)
        object.__setattr__(self, "path", self._replay_exact_path_binding())
        self._assert_proved_premise_replay()
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    @property
    def weights(self) -> tuple[Fraction, ...]:
        return () if self.finite_target_law is None else self.finite_target_law.weights

    @property
    def common_target(self) -> tuple[Fraction, ...]:
        return () if self.finite_target_law is None else self.finite_target_law.common_target

    @property
    def selected_atom_index(self) -> int | None:
        return None if self.selection_contract is None else self.selection_contract.selected_atom_index

    @property
    def selected_atom_id(self) -> str | None:
        return None if self.selection_contract is None else self.selection_contract.selected_atom_id

    @property
    def matched_mock_plan_id(self) -> str | None:
        return None if self.matched_mock_plan is None else self.matched_mock_plan.plan_id

    def _replay_exact_path_binding(self) -> DepthPath:
        if type(self.path) is not DepthPath:
            raise DepthPathError("report requires an exact DepthPath")
        resolved_path = revalidate_depth_path(self.path)
        if self.path_content_id != resolved_path.content_id:
            raise DepthPathError(
                "path content identity does not match exact DepthPath replay"
            )
        if self.stratum_content_ids != tuple(
            stratum.content_id for stratum in resolved_path.strata
        ):
            raise DepthPathError(
                "stratum identities do not match exact DepthPath replay"
            )
        return resolved_path

    def _assert_proved_premise_replay(self) -> None:
        if (
            self.premise_status
            is not ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH
        ):
            return
        if type(self.finite_target_law) is not DepthPathFiniteTargetLaw:
            raise DepthPathError(
                "proved report requires an exact finite target law"
            )
        if type(self.selection_contract) is not DepthPathSelectionContract:
            raise DepthPathError(
                "proved report requires an exact selection contract"
            )
        law = revalidate_depth_path_finite_target_law(self.finite_target_law)
        selection = revalidate_depth_path_selection_contract(
            self.selection_contract
        )
        mean = sum(
            probability * value
            for probability, value in zip(
                law.weights, law.common_target, strict=True
            )
        )
        if mean != 0:
            raise DepthPathError("common target must be exactly centered")
        second_moment = sum(
            probability * value * value
            for probability, value in zip(
                law.weights, law.common_target, strict=True
            )
        )
        if second_moment <= 0:
            raise DepthPathError("common target requires a positive second moment")
        if self.target_second_moment != second_moment:
            raise DepthPathError(
                "target second moment does not match exact finite-law replay"
            )
        try:
            tower = certify_finite_partition_tower(
                weights=law.weights,
                common_target=law.common_target,
                partitions=tuple(reversed(self.path_partitions)),
            )
        except VectorTensorStatisticalFoundationError as exc:
            raise DepthPathError(
                "path partitions do not form the required decreasing filtration: "
                f"{exc}"
            ) from exc
        conditionals = tuple(
            _conditional_values(
                weights=law.weights,
                target=law.common_target,
                labels=partition,
            )
            for partition in self.path_partitions
        )
        expected_path_values = tuple(
            row[selection.selected_atom_index] for row in conditionals
        )
        if self.path_values != expected_path_values:
            raise DepthPathError(
                "path values do not match exact conditional-expectation replay"
            )
        expected_maximum = max(abs(value) for value in expected_path_values)
        if self.path_maximum_abs != expected_maximum:
            raise DepthPathError(
                "path maximum does not match exact conditional-expectation replay"
            )
        expected_equalities = tuple(tower.exact_equalities)
        if self.exact_tower_equalities != expected_equalities:
            raise DepthPathError("tower equalities do not match exact replay")
        expected_tower_content_id = _sha256_payload(
            {
                "atom_count": tower.atom_count,
                "conditional_expectations": [
                    list(row) for row in tower.conditional_expectations
                ],
                "exact_equalities": list(tower.exact_equalities),
                "rung_count": tower.rung_count,
                "schema": "PR284_EXACT_FINITE_TOWER_REPLAY_V1",
            }
        )
        if self.exact_tower_report_content_id != expected_tower_content_id:
            raise DepthPathError("tower report identity does not match exact replay")
        expected_path_maximum_content_id = _sha256_payload(
            {
                "path_values": [
                    _fraction_text(value) for value in expected_path_values
                ],
                "selected_atom_id": selection.selected_atom_id,
                "selection_contract_content_id": selection.content_id,
                "value": _fraction_text(expected_maximum),
            }
        )
        if self.path_maximum_content_id != expected_path_maximum_content_id:
            raise DepthPathError(
                "path maximum identity does not match exact replay"
            )

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "claim_tier": self.claim_tier,
            "exact_tower_equalities": list(self.exact_tower_equalities),
            "exact_tower_report_content_id": self.exact_tower_report_content_id,
            "family_identification_gate": self.family_identification_gate,
            "fast_oracle_caveat": PR284_FAST_ORACLE_CAVEAT,
            "filtration_direction": self.filtration_direction,
            "filtration_id": self.filtration_id,
            "finite_target_law": (
                None if self.finite_target_law is None else self.finite_target_law.as_payload()
            ),
            "forbidden_use": list(self.forbidden_use),
            "matched_mock_plan": (
                None if self.matched_mock_plan is None else self.matched_mock_plan.as_payload()
            ),
            "observed_data_executed": self.observed_data_executed,
            "owner": self.owner,
            "path": self.path.as_payload(),
            "path_content_id": self.path_content_id,
            "path_maximum_abs": (
                None if self.path_maximum_abs is None else _fraction_text(self.path_maximum_abs)
            ),
            "path_maximum_content_id": self.path_maximum_content_id,
            "path_partitions": [list(row) for row in self.path_partitions],
            "path_values": [_fraction_text(value) for value in self.path_values],
            "premise_evidence_id": self.premise_evidence_id,
            "premise_status": self.premise_status.value,
            "preprocessing_id": self.preprocessing_id,
            "public_use": self.public_use,
            "relation_to_source": PR284_RELATION_TO_SOURCE,
            "report_id": self.report_id,
            "schema": "HTT_DEPTH_PATH_REVERSE_MARTINGALE_REPORT_V1",
            "selection_contract": (
                None if self.selection_contract is None else self.selection_contract.as_payload()
            ),
            "sigma_field_ids": list(self.sigma_field_ids),
            "source_oracle_id": PR284_SOURCE_ORACLE_ID,
            "source_proof_adjudication_status": PR284_SOURCE_ADJUDICATION,
            "source_registry_status": PR284_SOURCE_STATUS,
            "stratum_content_ids": list(self.stratum_content_ids),
            "target_second_moment": (
                None
                if self.target_second_moment is None
                else _fraction_text(self.target_second_moment)
            ),
            "threshold_contract": self.threshold_contract.as_payload(),
            "transfer_source": self.transfer_source,
            "typed_proof_verdict": PR284_TYPED_PROOF_VERDICT,
            "unresolved_reasons": list(self.unresolved_reasons),
        }

    def _assert_identity_sealed(self) -> None:
        self._replay_exact_path_binding()
        self.threshold_contract.as_payload()
        if self.finite_target_law is not None:
            self.finite_target_law.as_payload()
        if self.selection_contract is not None:
            self.selection_contract.as_payload()
        if self.matched_mock_plan is not None:
            self.matched_mock_plan.as_payload()
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="reverse-martingale report",
        )
        self._assert_proved_premise_replay()

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def _build_depth_path_reverse_martingale_report_contract(
    *,
    path: DepthPath | None = None,
    **kwargs: object,
) -> DepthPathReverseMartingaleReport:
    if type(path) is not DepthPath:
        raise DepthPathError(
            "report construction requires an exact DepthPath"
        )
    return DepthPathReverseMartingaleReport(
        path=revalidate_depth_path(path),
        **kwargs,
        _construction_token=_REPORT_TOKEN,
    )


def revalidate_depth_path_reverse_martingale_report(
    value: DepthPathReverseMartingaleReport,
) -> DepthPathReverseMartingaleReport:
    if type(value) is not DepthPathReverseMartingaleReport:
        raise TypeError(
            "value must be an exact DepthPathReverseMartingaleReport"
        )
    value.as_payload()
    return value


@dataclass(frozen=True)
class DepthPathDoobCalibration:
    calibration_id: str
    report: DepthPathReverseMartingaleReport
    threshold_contract: DepthPathThresholdContract
    preprocessing_id: str
    estimator_id: str
    status: DepthPathCalibrationStatus
    probability_upper_bound: Fraction | None
    target_second_moment: Fraction | None
    threshold_squared: Fraction | None
    path_maximum_squared: Fraction | None
    path_exceeds_threshold: bool | None
    event_comparison: str
    owner: str = PR284_OWNER
    claim_tier: str = PR284_CLAIM_TIER
    transfer_source: str = PR284_TRANSFER_SOURCE
    observed_data_executed: bool = False
    public_use: bool = False
    family_identification_gate: str = PR284_FAMILY_GATE
    allowed_use: tuple[str, ...] = PR284_ALLOWED_USE
    forbidden_use: tuple[str, ...] = PR284_FORBIDDEN_USE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CALIBRATION_TOKEN:
            raise DepthPathError("DepthPathDoobCalibration must be factory-built")
        _text(self.calibration_id, "calibration_id")
        _text(self.preprocessing_id, "preprocessing_id")
        _text(self.estimator_id, "estimator_id")
        report = revalidate_depth_path_reverse_martingale_report(self.report)
        threshold = revalidate_depth_path_threshold_contract(self.threshold_contract)
        if report.threshold_contract.content_id != threshold.content_id:
            raise DepthPathError("threshold contract does not match the report")
        if report.preprocessing_id != self.preprocessing_id:
            raise DepthPathError("preprocessing identity does not match the report")
        if report.estimator_id != self.estimator_id:
            raise DepthPathError("estimator identity does not match the report")
        if type(self.status) is not DepthPathCalibrationStatus:
            raise DepthPathError("status must use DepthPathCalibrationStatus")
        if self.event_comparison != PR284_EVENT_COMPARISON:
            raise DepthPathError("event comparison drifted")
        if self.status is DepthPathCalibrationStatus.BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE:
            if report.premise_status is not ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH:
                raise DepthPathError("a bound requires the proved finite premise")
            bound = _exact_fraction(
                self.probability_upper_bound,
                "probability_upper_bound",
            )
            second = _exact_fraction(self.target_second_moment, "target_second_moment")
            threshold_squared = _exact_fraction(
                self.threshold_squared,
                "threshold_squared",
            )
            maximum_squared = _exact_fraction(
                self.path_maximum_squared,
                "path_maximum_squared",
            )
            expected_bound = min(
                Fraction(1, 1),
                Fraction(1, 1) / (threshold.multiplier * threshold.multiplier),
            )
            if bound != expected_bound:
                raise DepthPathError("Doob probability bound is not exact")
            if second != report.target_second_moment:
                raise DepthPathError("second moment does not match the report")
            if threshold_squared != threshold.multiplier**2 * second:
                raise DepthPathError("exact squared threshold does not match")
            if maximum_squared != report.path_maximum_abs**2:
                raise DepthPathError("exact squared path maximum does not match")
            if type(self.path_exceeds_threshold) is not bool or self.path_exceeds_threshold != (
                maximum_squared >= threshold_squared
            ):
                raise DepthPathError("inclusive exact threshold event does not match")
        else:
            if report.premise_status is not ReverseMartingalePremiseStatus.UNPROVED_REQUIRES_MATCHED_MOCKS:
                raise DepthPathError("matched mocks require an unproved premise")
            if any(
                value is not None
                for value in (
                    self.probability_upper_bound,
                    self.target_second_moment,
                    self.threshold_squared,
                    self.path_maximum_squared,
                    self.path_exceeds_threshold,
                )
            ):
                raise DepthPathError("matched-mock fallback must not carry a free bound")
            if report.matched_mock_plan is None:
                raise DepthPathError("matched-mock fallback requires its exact plan")
        if (
            self.owner != PR284_OWNER
            or self.claim_tier != PR284_CLAIM_TIER
            or self.transfer_source != PR284_TRANSFER_SOURCE
            or self.observed_data_executed is not False
            or self.public_use is not False
            or self.family_identification_gate != PR284_FAMILY_GATE
            or tuple(self.allowed_use) != PR284_ALLOWED_USE
            or tuple(self.forbidden_use) != PR284_FORBIDDEN_USE
        ):
            raise DepthPathError("PR-284 claim boundary drifted")
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    @property
    def report_content_id(self) -> str:
        return self.report.content_id

    @property
    def matched_mock_plan_id(self) -> str | None:
        return self.report.matched_mock_plan_id

    @property
    def matched_mock_plan_content_id(self) -> str | None:
        return (
            None
            if self.report.matched_mock_plan is None
            else self.report.matched_mock_plan.content_id
        )

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "calibration_id": self.calibration_id,
            "claim_tier": self.claim_tier,
            "event_comparison": self.event_comparison,
            "family_identification_gate": self.family_identification_gate,
            "forbidden_use": list(self.forbidden_use),
            "matched_mock_plan_content_id": self.matched_mock_plan_content_id,
            "matched_mock_plan_id": self.matched_mock_plan_id,
            "observed_data_executed": self.observed_data_executed,
            "owner": self.owner,
            "path_exceeds_threshold": self.path_exceeds_threshold,
            "path_maximum_squared": (
                None
                if self.path_maximum_squared is None
                else _fraction_text(self.path_maximum_squared)
            ),
            "preprocessing_id": self.preprocessing_id,
            "probability_upper_bound": (
                None
                if self.probability_upper_bound is None
                else _fraction_text(self.probability_upper_bound)
            ),
            "public_use": self.public_use,
            "report_content_id": self.report.content_id,
            "schema": "HTT_DEPTH_PATH_DOOB_CALIBRATION_V1",
            "status": self.status.value,
            "target_second_moment": (
                None
                if self.target_second_moment is None
                else _fraction_text(self.target_second_moment)
            ),
            "threshold_contract_content_id": self.threshold_contract.content_id,
            "threshold_squared": (
                None
                if self.threshold_squared is None
                else _fraction_text(self.threshold_squared)
            ),
            "transfer_source": self.transfer_source,
        }

    def _assert_identity_sealed(self) -> None:
        self.report.as_payload()
        self.threshold_contract.as_payload()
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="Doob calibration",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def _build_depth_path_doob_calibration_contract(
    **kwargs: object,
) -> DepthPathDoobCalibration:
    return DepthPathDoobCalibration(
        **kwargs,
        _construction_token=_CALIBRATION_TOKEN,
    )


def revalidate_depth_path_doob_calibration(
    value: DepthPathDoobCalibration,
) -> DepthPathDoobCalibration:
    if type(value) is not DepthPathDoobCalibration:
        raise TypeError("value must be an exact DepthPathDoobCalibration")
    value.as_payload()
    return value


__all__ = [
    "DepthPathCalibrationStatus",
    "DepthPathDoobCalibration",
    "DepthPathFiniteTargetLaw",
    "DepthPathMatchedMockPlan",
    "DepthPathReverseMartingaleReport",
    "DepthPathSelectionContract",
    "DepthPathThresholdContract",
    "PR284_EVENT_COMPARISON",
    "ReverseMartingalePremiseStatus",
    "build_depth_path_finite_target_law",
    "build_depth_path_selection_contract",
    "build_depth_path_threshold_contract",
    "revalidate_depth_path_doob_calibration",
    "revalidate_depth_path_finite_target_law",
    "revalidate_depth_path_matched_mock_plan",
    "revalidate_depth_path_reverse_martingale_report",
    "revalidate_depth_path_selection_contract",
    "revalidate_depth_path_threshold_contract",
]
