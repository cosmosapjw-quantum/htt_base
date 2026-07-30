"""Exact, typed statistical foundations for the vector/tensor successor lane.

The objects here are method contracts.  They do not consume observed data and
do not create a likelihood, posterior, evidence value, native-solver result,
geometry verdict, or Bianchi-family label.

The implementation keeps five distinctions explicit:

* an estimand is not a sampling law;
* finite-sample and asymptotic statements are not interchangeable;
* an empirical pushforward is sample-wise, not a plug-in ratio of means;
* paired covariance includes both ordered cross-covariance blocks; and
* exact sign/tower statements require their exchangeability/filtration
  premises rather than inferring them from labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum
from fractions import Fraction
import hashlib
import json
import math
from numbers import Integral, Rational, Real
from pathlib import Path
from typing import Hashable, Mapping, Sequence

import numpy as np
import yaml

from common.conditional_exceedance import (
    ConditionalExceedanceProfile,
    ExceedanceStatus,
)
from common.tensor_departure_statistics import (
    CertifiedFunctionalPushforward,
    FunctionalCellStatus,
)


class VectorTensorStatisticalFoundationError(ValueError):
    """Raised when a statistical-foundation premise fails closed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class EvidenceGrade(_StringEnum):
    EXACT_ANALYTIC = "EXACT_ANALYTIC"
    FINITE_REGISTERED_EXACT = "FINITE_REGISTERED_EXACT"
    ASYMPTOTIC_ANALYTIC = "ASYMPTOTIC_ANALYTIC"
    SIMULATION_DIAGNOSTIC = "SIMULATION_DIAGNOSTIC"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    INCONCLUSIVE = "INCONCLUSIVE"


class FoundationVerdict(_StringEnum):
    PROVED_ANALYTIC_UNDER_TYPED_PREMISES = (
        "PROVED_ANALYTIC_UNDER_TYPED_PREMISES"
    )
    PROVED_FINITE_REGISTERED_PATH = "PROVED_FINITE_REGISTERED_PATH"
    REFERENCE_RESOLVED_WITH_SCALAR_REDUCTION = (
        "REFERENCE_RESOLVED_WITH_SCALAR_REDUCTION"
    )
    INCONCLUSIVE_MISSING_SIGNATURE = "INCONCLUSIVE_MISSING_SIGNATURE"


class AcceptanceBodyKind(_StringEnum):
    COORDINATE_THRESHOLDS = "COORDINATE_THRESHOLDS"
    WEIGHTED_MAX = "WEIGHTED_MAX"
    COVARIANCE_ELLIPSOID = "COVARIANCE_ELLIPSOID"
    ONE_DIMENSIONAL_INTERVAL = "ONE_DIMENSIONAL_INTERVAL"


class AcceptanceBoundaryRelation(_StringEnum):
    LT = "LT"
    EQ = "EQ"
    GT = "GT"


class PairingStatus(_StringEnum):
    PAIRED_JOINT_LAW = "PAIRED_JOINT_LAW"
    INDEPENDENT_MARGINALS_ONLY = "INDEPENDENT_MARGINALS_ONLY"


CLAIM_CEILING = "diagnostic_only"
ALLOWED_USE = (
    "exact or explicitly bounded statistical-method diagnostic",
    "finite registered scalar-reduction check",
    "input to a separately owned HTT inference adapter",
)
FORBIDDEN_USE = (
    "simulation-only evidence promoted to an exact statement",
    "model-dependent inference outside HTT ownership",
    "optimizer output relabelled as a probability law",
    "native solver validation or native morphology atlas",
    "geometry detection or Bianchi family identification",
)
REGISTRY_PATH = Path(
    "docs/research_program/vector_tensor/proofs/"
    "PILLAR_S_CORE_PROOFS_V1.yaml"
)
EXPECTED_REGISTRY_SHA256 = (
    "48262fce614cdcc3f78e43e85cc86e5b27d0e829e86dec5025512bf90441c9a6"
)
EXPECTED_LEGACY_REFERENCE_IDS = frozenset(
    {"SIG-P18", "SIG-T1p", "SIG-DL1", "SIG-L-T2-EXIST", "SIG-T2G"}
)
EXPECTED_VT_IDS = frozenset({"VT-S1", "VT-S2", "VT-S4", "VT-S7", "VT-S8"})
EXPECTED_TF_IDS = frozenset(
    {"TF-09-PARITY-SIGN-EXACTNESS", "TF-11-MASK-PATH-MARTINGALE"}
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be non-empty trimmed text"
        )
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a sequence of text"
        )
    result = tuple(_text(value, name) for value in values)
    if not result and not empty_ok:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must not be empty"
        )
    if len(result) != len(set(result)):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must not contain duplicates"
        )
    return result


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise VectorTensorStatisticalFoundationError(f"{name} must be real")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be finite"
        ) from exc
    if not math.isfinite(result):
        raise VectorTensorStatisticalFoundationError(f"{name} must be finite")
    return result


def _vector(values: Sequence[object], name: str) -> np.ndarray:
    if isinstance(values, (str, bytes)):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a numeric sequence"
        )
    try:
        result = np.asarray(tuple(values), dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a finite vector"
        ) from exc
    if result.ndim != 1 or not np.all(np.isfinite(result)):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a finite vector"
        )
    return result


def _matrix(
    values: Sequence[Sequence[object]],
    name: str,
    *,
    size: int | None = None,
) -> np.ndarray:
    if isinstance(values, (str, bytes)):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a numeric matrix"
        )
    try:
        result = np.asarray(
            tuple(tuple(row) for row in values), dtype=float
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a finite square matrix"
        ) from exc
    if (
        result.ndim != 2
        or result.shape[0] != result.shape[1]
        or (size is not None and result.shape != (size, size))
        or not np.all(np.isfinite(result))
    ):
        expected = "square" if size is None else f"shape ({size}, {size})"
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a finite matrix of {expected}"
        )
    return result


def _exact_float_matrix(values: np.ndarray) -> list[list[Fraction]]:
    return [
        [Fraction.from_float(float(value)) for value in row]
        for row in values
    ]


def _exact_float_psd(values: np.ndarray) -> bool:
    """Decide PSD for the exact binary-rational values carried by floats."""

    work = _exact_float_matrix(values)
    while work:
        size = len(work)
        diagonals = tuple(work[index][index] for index in range(size))
        if any(value < 0 for value in diagonals):
            return False
        pivot_index = next(
            (index for index, value in enumerate(diagonals) if value > 0),
            None,
        )
        if pivot_index is None:
            return all(value == 0 for row in work for value in row)
        if pivot_index != 0:
            work[0], work[pivot_index] = work[pivot_index], work[0]
            for row in work:
                row[0], row[pivot_index] = (
                    row[pivot_index],
                    row[0],
                )
        pivot = work[0][0]
        work = [
            [
                work[row][column]
                - work[row][0] * work[0][column] / pivot
                for column in range(1, size)
            ]
            for row in range(1, size)
        ]
    return True


def _exact_float_rank(values: np.ndarray) -> int:
    work = _exact_float_matrix(values)
    row_count = len(work)
    column_count = len(work[0]) if work else 0
    rank = 0
    for column in range(column_count):
        pivot = next(
            (
                row
                for row in range(rank, row_count)
                if work[row][column] != 0
            ),
            None,
        )
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        pivot_value = work[rank][column]
        for row in range(row_count):
            if row == rank or work[row][column] == 0:
                continue
            multiplier = work[row][column] / pivot_value
            work[row] = [
                left - multiplier * right
                for left, right in zip(
                    work[row], work[rank], strict=True
                )
            ]
        rank += 1
        if rank == row_count:
            break
    return rank


def _exact_float_quadratic_solve(
    matrix: np.ndarray,
    vector: np.ndarray,
) -> Fraction:
    coefficients = _exact_float_matrix(matrix)
    right = [Fraction.from_float(float(value)) for value in vector]
    size = len(coefficients)
    augmented = [
        [*row, right[index]]
        for index, row in enumerate(coefficients)
    ]
    for column in range(size):
        pivot = next(
            (
                row
                for row in range(column, size)
                if augmented[row][column] != 0
            ),
            None,
        )
        if pivot is None:
            raise VectorTensorStatisticalFoundationError(
                "active covariance body is rank deficient"
            )
        augmented[column], augmented[pivot] = (
            augmented[pivot],
            augmented[column],
        )
        pivot_value = augmented[column][column]
        augmented[column] = [
            value / pivot_value for value in augmented[column]
        ]
        for row in range(size):
            if row == column or augmented[row][column] == 0:
                continue
            multiplier = augmented[row][column]
            augmented[row] = [
                left - multiplier * right_value
                for left, right_value in zip(
                    augmented[row], augmented[column], strict=True
                )
            ]
    solution = tuple(row[-1] for row in augmented)
    quadratic = sum(
        (
            Fraction.from_float(float(value)) * solved
            for value, solved in zip(vector, solution, strict=True)
        ),
        Fraction(0, 1),
    )
    if quadratic < 0:
        raise VectorTensorStatisticalFoundationError(
            "ellipsoid quadratic form became negative"
        )
    return quadratic


def _sqrt_fraction_to_float(value: Fraction, name: str) -> float:
    if value == 0:
        return 0.0
    with localcontext() as context:
        context.prec = 80
        context.Emax = 999_999_999
        context.Emin = -999_999_999
        root = (
            Decimal(value.numerator) / Decimal(value.denominator)
        ).sqrt()
    try:
        result = float(root)
    except (TypeError, ValueError, OverflowError) as exc:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must remain finite and representable"
        ) from exc
    if not math.isfinite(result) or result == 0.0:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must remain finite and representable"
        )
    return result


def _fraction_to_float(value: Fraction, name: str) -> float:
    if value == 0:
        return 0.0
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must remain finite and representable"
        ) from exc
    if not math.isfinite(result) or result == 0.0:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must remain finite and representable"
        )
    return result


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_evidence(repo_root: Path, value: str) -> None:
    path_text = value.split("#", 1)[0]
    path = repo_root / path_text
    if path.is_symlink() or not path.is_file():
        raise VectorTensorStatisticalFoundationError(
            f"evidence reference is not resolvable: {value}"
        )


@dataclass(frozen=True)
class StatisticalProofRecord:
    obligation_id: str
    source_group: str
    source_status: str
    source_proof_adjudication_status: str
    source_statement_identity_sha256: str
    relation_to_source: str
    estimand: str
    sampling_law: str
    covariance_assumptions: tuple[str, ...]
    finite_or_asymptotic_status: str
    assumptions: tuple[str, ...]
    domains: tuple[str, ...]
    proof_method: str
    evidence_grade: EvidenceGrade
    verdict: FoundationVerdict
    evidence_refs: tuple[str, ...]
    counterexample_boundaries: tuple[str, ...]
    claim_ceiling: str = CLAIM_CEILING

    def __post_init__(self) -> None:
        for name in (
            "obligation_id",
            "source_group",
            "source_status",
            "source_proof_adjudication_status",
            "source_statement_identity_sha256",
            "relation_to_source",
            "estimand",
            "sampling_law",
            "finite_or_asymptotic_status",
            "proof_method",
        ):
            _text(getattr(self, name), name)
        if self.source_proof_adjudication_status != "NOT_ADJUDICATED":
            raise VectorTensorStatisticalFoundationError(
                "PR-268 source adjudication status must remain NOT_ADJUDICATED"
            )
        if type(self.evidence_grade) is not EvidenceGrade:
            raise VectorTensorStatisticalFoundationError(
                "evidence_grade must use the registered vocabulary"
            )
        if type(self.verdict) is not FoundationVerdict:
            raise VectorTensorStatisticalFoundationError(
                "verdict must use the registered vocabulary"
            )
        if (
            self.evidence_grade is EvidenceGrade.SIMULATION_DIAGNOSTIC
            and self.verdict
            in {
                FoundationVerdict.PROVED_ANALYTIC_UNDER_TYPED_PREMISES,
                FoundationVerdict.PROVED_FINITE_REGISTERED_PATH,
            }
        ):
            raise VectorTensorStatisticalFoundationError(
                "simulation-only evidence cannot promote an exact verdict"
            )
        if self.claim_ceiling != CLAIM_CEILING:
            raise VectorTensorStatisticalFoundationError(
                "claim ceiling drifted"
            )
        object.__setattr__(
            self,
            "covariance_assumptions",
            _texts(
                self.covariance_assumptions,
                "covariance_assumptions",
                empty_ok=True,
            ),
        )
        object.__setattr__(
            self,
            "assumptions",
            _texts(self.assumptions, "assumptions", empty_ok=True),
        )
        object.__setattr__(
            self,
            "domains",
            _texts(self.domains, "domains", empty_ok=True),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _texts(self.evidence_refs, "evidence_refs"),
        )
        object.__setattr__(
            self,
            "counterexample_boundaries",
            _texts(
                self.counterexample_boundaries,
                "counterexample_boundaries",
                empty_ok=True,
            ),
        )


@dataclass(frozen=True)
class PillarSCoreRegistry:
    records: tuple[StatisticalProofRecord, ...]
    registry_sha256: str
    source_hashes: tuple[tuple[str, str], ...]
    claim_ceiling: str = CLAIM_CEILING

    def __post_init__(self) -> None:
        identifiers = tuple(record.obligation_id for record in self.records)
        if len(identifiers) != len(set(identifiers)):
            raise VectorTensorStatisticalFoundationError(
                "proof registry contains duplicate obligation IDs"
            )
        if self.claim_ceiling != CLAIM_CEILING:
            raise VectorTensorStatisticalFoundationError(
                "registry claim ceiling drifted"
            )

    def record(self, obligation_id: str) -> StatisticalProofRecord:
        matches = tuple(
            record
            for record in self.records
            if record.obligation_id == obligation_id
        )
        if len(matches) != 1:
            raise VectorTensorStatisticalFoundationError(
                f"expected one record for {obligation_id}"
            )
        return matches[0]

    def reject_raw_proof_count(self, claimed_count: int) -> None:
        raise VectorTensorStatisticalFoundationError(
            f"raw PR-271 record count {claimed_count} is not an accepted "
            "proof count"
        )


def load_pillar_s_core_registry(
    repo_root: Path,
    registry_path: Path = REGISTRY_PATH,
) -> PillarSCoreRegistry:
    """Load and fail-closed validate the generated PR-271 proof-author rows."""

    repo_root = Path(repo_root)
    path = repo_root / registry_path
    if path.is_symlink() or not path.is_file():
        raise VectorTensorStatisticalFoundationError(
            "PR-271 proof registry is missing or not regular"
        )
    registry_sha = _file_sha256(path)
    if registry_sha != EXPECTED_REGISTRY_SHA256:
        raise VectorTensorStatisticalFoundationError(
            "PR-271 proof registry bytes drifted"
        )
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise VectorTensorStatisticalFoundationError(
            "PR-271 proof registry must be a mapping"
        )
    required = {
        "schema": "htt.pillar_s_core_proofs.v1",
        "authority": "PR-271",
        "claim_ceiling": CLAIM_CEILING,
        "scientific_status_effect": "statistical_method_status_only",
        "source_proof_adjudication_status": "NOT_ADJUDICATED",
        "raw_count_publication": "FORBIDDEN",
    }
    if any(payload.get(key) != value for key, value in required.items()):
        raise VectorTensorStatisticalFoundationError(
            "PR-271 registry authority or claim boundary drifted"
        )
    source_hashes_raw = payload.get("source_hashes")
    if not isinstance(source_hashes_raw, Mapping) or not source_hashes_raw:
        raise VectorTensorStatisticalFoundationError(
            "source_hashes must be a non-empty mapping"
        )
    source_hashes: list[tuple[str, str]] = []
    for relative, expected in source_hashes_raw.items():
        relative_text = _text(relative, "source path")
        expected_text = _text(expected, "source sha256")
        actual = _file_sha256(repo_root / relative_text)
        if actual != expected_text:
            raise VectorTensorStatisticalFoundationError(
                f"frozen PR-271 source drifted: {relative_text}"
            )
        source_hashes.append((relative_text, expected_text))
    rows = payload.get("records")
    if (
        isinstance(rows, (str, bytes))
        or not isinstance(rows, Sequence)
        or any(not isinstance(row, Mapping) for row in rows)
    ):
        raise VectorTensorStatisticalFoundationError(
            "records must be a list of mappings"
        )
    records: list[StatisticalProofRecord] = []
    for row in rows:
        try:
            grade = EvidenceGrade(str(row.get("evidence_grade")))
            verdict = FoundationVerdict(str(row.get("verdict")))
        except ValueError as exc:
            raise VectorTensorStatisticalFoundationError(
                "unregistered evidence grade or verdict"
            ) from exc
        record = StatisticalProofRecord(
            obligation_id=_text(row.get("obligation_id"), "obligation_id"),
            source_group=_text(row.get("source_group"), "source_group"),
            source_status=_text(row.get("source_status"), "source_status"),
            source_proof_adjudication_status=_text(
                row.get("source_proof_adjudication_status"),
                "source_proof_adjudication_status",
            ),
            source_statement_identity_sha256=_text(
                row.get("source_statement_identity_sha256"),
                "source_statement_identity_sha256",
            ),
            relation_to_source=_text(
                row.get("relation_to_source"), "relation_to_source"
            ),
            estimand=_text(row.get("estimand"), "estimand"),
            sampling_law=_text(row.get("sampling_law"), "sampling_law"),
            covariance_assumptions=tuple(
                row.get("covariance_assumptions") or ()
            ),
            finite_or_asymptotic_status=_text(
                row.get("finite_or_asymptotic_status"),
                "finite_or_asymptotic_status",
            ),
            assumptions=tuple(row.get("assumptions") or ()),
            domains=tuple(row.get("domains") or ()),
            proof_method=_text(row.get("proof_method"), "proof_method"),
            evidence_grade=grade,
            verdict=verdict,
            evidence_refs=tuple(row.get("evidence_refs") or ()),
            counterexample_boundaries=tuple(
                row.get("counterexample_boundaries") or ()
            ),
            claim_ceiling=_text(row.get("claim_ceiling"), "claim_ceiling"),
        )
        for evidence_ref in record.evidence_refs:
            _resolve_evidence(repo_root, evidence_ref)
        records.append(record)
    groups = {
        group: frozenset(
            record.obligation_id
            for record in records
            if record.source_group == group
        )
        for group in ("LEGACY_S", "VT_S", "TF_S")
    }
    if len(groups["LEGACY_S"]) != 34:
        raise VectorTensorStatisticalFoundationError(
            "PR-271 registry must contain exactly 34 legacy Pillar-S rows"
        )
    if groups["VT_S"] != EXPECTED_VT_IDS or groups["TF_S"] != EXPECTED_TF_IDS:
        raise VectorTensorStatisticalFoundationError(
            "PR-271 VT/TF selection drifted"
        )
    reference_ids = frozenset(
        record.obligation_id
        for record in records
        if record.verdict
        is FoundationVerdict.REFERENCE_RESOLVED_WITH_SCALAR_REDUCTION
    )
    if reference_ids != EXPECTED_LEGACY_REFERENCE_IDS:
        raise VectorTensorStatisticalFoundationError(
            "legacy typed-reference selection drifted"
        )
    declared_sha = payload.get("canonical_records_sha256")
    canonical_rows = json.loads(
        json.dumps(rows, sort_keys=True, ensure_ascii=True)
    )
    if declared_sha != _canonical_sha256(canonical_rows):
        raise VectorTensorStatisticalFoundationError(
            "canonical PR-271 record identity drifted"
        )
    return PillarSCoreRegistry(
        records=tuple(records),
        registry_sha256=registry_sha,
        source_hashes=tuple(sorted(source_hashes)),
    )


def _probability_mass(value: object, name: str) -> Fraction:
    if isinstance(value, (bool, np.bool_)):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must contain finite real probability masses"
        )
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise VectorTensorStatisticalFoundationError(
                f"{name} must contain finite real probability masses"
            )
        mass = Fraction(value)
    elif isinstance(value, Rational):
        mass = Fraction(value.numerator, value.denominator)
    elif isinstance(value, Real):
        try:
            encoded = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise VectorTensorStatisticalFoundationError(
                f"{name} must contain finite real probability masses"
            ) from exc
        if not math.isfinite(encoded):
            raise VectorTensorStatisticalFoundationError(
                f"{name} must contain finite real probability masses"
            )
        # A binary float enters this contract through its shortest
        # round-trip decimal spelling.  This makes ordinary declared decimal
        # laws such as (0.4, 0.1, 0.2, 0.3) exact while still refusing a
        # tolerance-only mass such as 1.0 + 5e-13.
        mass = Fraction(str(encoded))
    else:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must contain finite real probability masses"
        )
    if mass < 0:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must contain nonnegative probability masses"
        )
    return mass


def _probability_vector(
    values: Sequence[object],
    name: str,
) -> tuple[Fraction, ...]:
    if isinstance(values, (str, bytes)):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a probability vector summing to one"
        )
    result = tuple(
        _probability_mass(value, name) for value in values
    )
    if not result or sum(result, Fraction(0, 1)) != Fraction(1, 1):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be a probability vector summing to one"
        )
    return result


def _aggregate(
    probabilities: Sequence[Fraction],
    labels: Sequence[Hashable],
) -> tuple[tuple[Hashable, ...], tuple[Fraction, ...]]:
    order: list[Hashable] = []
    totals: dict[Hashable, Fraction] = {}
    for probability, label in zip(probabilities, labels, strict=True):
        try:
            hash(label)
        except TypeError as exc:
            raise VectorTensorStatisticalFoundationError(
                "partition labels must be hashable"
            ) from exc
        if label not in totals:
            order.append(label)
            totals[label] = Fraction(0, 1)
        totals[label] += probability
    return tuple(order), tuple(totals[label] for label in order)


def _require_hashable(value: object, name: str) -> Hashable:
    try:
        hash(value)
    except TypeError as exc:
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be hashable"
        ) from exc
    return value


def _total_variation(
    left: Sequence[Fraction],
    right: Sequence[Fraction],
) -> Fraction:
    return sum(
        (
            abs(p_value - q_value)
            for p_value, q_value in zip(left, right, strict=True)
        ),
        Fraction(0, 1),
    ) / 2


def _kl(
    left: Sequence[Fraction],
    right: Sequence[Fraction],
) -> float:
    if any(
        p_value > 0 and q_value == 0
        for p_value, q_value in zip(left, right, strict=True)
    ):
        return math.inf
    with localcontext() as context:
        context.prec = 120
        total = Decimal(0)
        for p_value, q_value in zip(left, right, strict=True):
            if p_value == 0:
                continue
            p_decimal = (
                Decimal(p_value.numerator) / Decimal(p_value.denominator)
            )
            q_decimal = (
                Decimal(q_value.numerator) / Decimal(q_value.denominator)
            )
            total += p_decimal * (p_decimal / q_decimal).ln()
    # Exact normalization makes KL nonnegative.  Decimal logarithms can leave
    # a negative final-place residue after cancellation; it has no semantic
    # standing and must never be exposed as a divergence.
    if total < 0:
        total = Decimal(0)
    result = float(total)
    if not math.isfinite(result):
        return math.inf
    return result


@dataclass(frozen=True)
class ScalarizationDominanceReport:
    profile_total_variation: float
    scalar_total_variation: float
    profile_kl: float
    scalar_kl: float
    decision_sufficient: bool | None
    exact_statement: str = (
        "deterministic scalarization cannot increase TV or KL divergence"
    )
    claim_ceiling: str = CLAIM_CEILING


def certify_deterministic_scalarization(
    *,
    profile_labels: Sequence[Hashable],
    scalar_labels: Sequence[Hashable],
    law_p: Sequence[object],
    law_q: Sequence[object],
    registered_decisions: Sequence[Hashable] | None = None,
) -> ScalarizationDominanceReport:
    """Verify one finite deterministic data-processing instance for VT-S1."""

    p_values = _probability_vector(law_p, "law_p")
    q_values = _probability_vector(law_q, "law_q")
    size = len(p_values)
    if (
        len(q_values) != size
        or len(profile_labels) != size
        or len(scalar_labels) != size
    ):
        raise VectorTensorStatisticalFoundationError(
            "laws and partition labels must have one common length"
        )
    scalar_by_profile: dict[Hashable, Hashable] = {}
    for profile, scalar in zip(profile_labels, scalar_labels, strict=True):
        _require_hashable(profile, "profile label")
        _require_hashable(scalar, "scalar label")
        if profile in scalar_by_profile and scalar_by_profile[profile] != scalar:
            raise VectorTensorStatisticalFoundationError(
                "scalarization is not a deterministic function of the profile"
            )
        scalar_by_profile[profile] = scalar
    profile_order, p_profile = _aggregate(p_values, profile_labels)
    q_order, q_profile = _aggregate(q_values, profile_labels)
    if profile_order != q_order:
        raise AssertionError("shared labels must produce shared order")
    scalar_order, p_scalar = _aggregate(p_values, scalar_labels)
    q_scalar_order, q_scalar = _aggregate(q_values, scalar_labels)
    if scalar_order != q_scalar_order:
        raise AssertionError("shared labels must produce shared order")
    profile_tv_exact = _total_variation(p_profile, q_profile)
    scalar_tv_exact = _total_variation(p_scalar, q_scalar)
    if scalar_tv_exact > profile_tv_exact:
        raise VectorTensorStatisticalFoundationError(
            "deterministic data-processing inequality failed exactly"
        )
    profile_tv = float(profile_tv_exact)
    scalar_tv = float(scalar_tv_exact)
    profile_kl = _kl(p_profile, q_profile)
    scalar_kl = _kl(p_scalar, q_scalar)
    tolerance = 128.0 * np.finfo(float).eps
    if scalar_tv > profile_tv + tolerance or (
        math.isfinite(profile_kl)
        and scalar_kl > profile_kl + tolerance
    ):
        raise VectorTensorStatisticalFoundationError(
            "deterministic data-processing inequality failed numerically"
        )
    decision_sufficient: bool | None = None
    if registered_decisions is not None:
        if len(registered_decisions) != size:
            raise VectorTensorStatisticalFoundationError(
                "registered_decisions must align with the support"
            )
        decision_by_scalar: dict[Hashable, Hashable] = {}
        decision_sufficient = True
        for scalar, decision in zip(
            scalar_labels, registered_decisions, strict=True
        ):
            _require_hashable(scalar, "scalar label")
            _require_hashable(decision, "registered decision")
            if (
                scalar in decision_by_scalar
                and decision_by_scalar[scalar] != decision
            ):
                decision_sufficient = False
            decision_by_scalar[scalar] = decision
    return ScalarizationDominanceReport(
        profile_total_variation=profile_tv,
        scalar_total_variation=scalar_tv,
        profile_kl=profile_kl,
        scalar_kl=scalar_kl,
        decision_sufficient=decision_sufficient,
    )


@dataclass(frozen=True)
class AcceptanceBodySpec:
    body_id: str
    kind: AcceptanceBodyKind
    coordinate_labels: tuple[str, ...]
    radii: tuple[float, ...] | None = None
    covariance: tuple[tuple[float, ...], ...] | None = None
    active_set: tuple[str, ...] = ()
    claim_ceiling: str = CLAIM_CEILING

    def __post_init__(self) -> None:
        _text(self.body_id, "body_id")
        if type(self.kind) is not AcceptanceBodyKind:
            raise VectorTensorStatisticalFoundationError(
                "kind must use AcceptanceBodyKind"
            )
        labels = _texts(self.coordinate_labels, "coordinate_labels")
        if self.claim_ceiling != CLAIM_CEILING:
            raise VectorTensorStatisticalFoundationError(
                "claim ceiling drifted"
            )
        if self.active_set:
            active = _texts(self.active_set, "active_set")
            if not set(active).issubset(labels):
                raise VectorTensorStatisticalFoundationError(
                    "active_set must be a subset of coordinate_labels"
                )
        else:
            active = labels
        object.__setattr__(self, "coordinate_labels", labels)
        object.__setattr__(self, "active_set", active)
        if self.kind is AcceptanceBodyKind.COVARIANCE_ELLIPSOID:
            if self.radii is not None or self.covariance is None:
                raise VectorTensorStatisticalFoundationError(
                    "ellipsoid requires covariance and no radii"
                )
            matrix = _matrix(
                self.covariance, "covariance", size=len(labels)
            )
            if not np.allclose(
                matrix, matrix.T, atol=0.0, rtol=0.0
            ):
                raise VectorTensorStatisticalFoundationError(
                    "covariance must be exactly symmetric"
                )
            if (
                not _exact_float_psd(matrix)
                or _exact_float_rank(matrix) != len(labels)
            ):
                raise VectorTensorStatisticalFoundationError(
                    "covariance ellipsoid requires positive-definite covariance"
                )
            object.__setattr__(
                self,
                "covariance",
                tuple(tuple(float(value) for value in row) for row in matrix),
            )
            return
        if self.covariance is not None or self.radii is None:
            raise VectorTensorStatisticalFoundationError(
                "non-ellipsoid bodies require radii and no covariance"
            )
        radii = tuple(_real(value, "radii") for value in self.radii)
        if len(radii) != len(labels) or any(value <= 0.0 for value in radii):
            raise VectorTensorStatisticalFoundationError(
                "radii must align with coordinates and be strictly positive"
            )
        if (
            self.kind is AcceptanceBodyKind.ONE_DIMENSIONAL_INTERVAL
            and len(radii) != 1
        ):
            raise VectorTensorStatisticalFoundationError(
                "one-dimensional interval requires exactly one coordinate"
            )
        object.__setattr__(self, "radii", radii)


@dataclass(frozen=True)
class AcceptanceGaugeResult:
    body_id: str
    q_value: float
    exact_acceptance_relation: AcceptanceBoundaryRelation
    accepted: bool
    active_set: tuple[str, ...]
    point: tuple[float, ...]
    claim_ceiling: str = CLAIM_CEILING


def evaluate_acceptance_gauge(
    spec: AcceptanceBodySpec,
    point: Sequence[object],
) -> AcceptanceGaugeResult:
    """Evaluate the unified VT-S2 gauge without rank-deficient fallback."""

    if type(spec) is not AcceptanceBodySpec:
        raise TypeError("spec must be an exact AcceptanceBodySpec")
    values = _vector(point, "point")
    if len(values) != len(spec.coordinate_labels):
        raise VectorTensorStatisticalFoundationError(
            "point dimension does not match the acceptance body"
        )
    active_indices = tuple(
        spec.coordinate_labels.index(label) for label in spec.active_set
    )
    active_values = values[np.asarray(active_indices)]
    if spec.kind is AcceptanceBodyKind.COVARIANCE_ELLIPSOID:
        covariance = np.asarray(spec.covariance, dtype=float)
        subcovariance = covariance[np.ix_(active_indices, active_indices)]
        quadratic = _exact_float_quadratic_solve(
            subcovariance, active_values
        )
        q_value = _sqrt_fraction_to_float(
            quadratic, "ellipsoid gauge"
        )
        exact_gauge_relation = (
            AcceptanceBoundaryRelation.LT
            if quadratic < 1
            else AcceptanceBoundaryRelation.EQ
            if quadratic == 1
            else AcceptanceBoundaryRelation.GT
        )
    else:
        radii = np.asarray(spec.radii, dtype=float)[np.asarray(active_indices)]
        exact_ratios = tuple(
            abs(Fraction.from_float(float(value)))
            / Fraction.from_float(float(radius))
            for value, radius in zip(active_values, radii, strict=True)
        )
        exact_gauge = max(exact_ratios)
        q_value = _fraction_to_float(exact_gauge, "max gauge")
        exact_gauge_relation = (
            AcceptanceBoundaryRelation.LT
            if exact_gauge < 1
            else AcceptanceBoundaryRelation.EQ
            if exact_gauge == 1
            else AcceptanceBoundaryRelation.GT
        )
    if not math.isfinite(q_value):
        raise VectorTensorStatisticalFoundationError(
            "acceptance gauge must be finite"
        )
    return AcceptanceGaugeResult(
        body_id=spec.body_id,
        q_value=q_value,
        exact_acceptance_relation=exact_gauge_relation,
        accepted=exact_gauge_relation is not AcceptanceBoundaryRelation.GT,
        active_set=spec.active_set,
        point=tuple(float(value) for value in values),
    )


@dataclass(frozen=True)
class SurvivalMonotonicityReport:
    profile_id: str
    sampling_law: str
    lane: str
    threshold_count: int
    exact_empirical_measure_statement: bool
    claim_ceiling: str = CLAIM_CEILING


def certify_survival_monotonicity(
    profile: ConditionalExceedanceProfile,
) -> SurvivalMonotonicityReport:
    """Revalidate the sealed VT-S4 survival profile and its law identity."""

    if type(profile) is not ConditionalExceedanceProfile:
        raise TypeError(
            "profile must be an exact ConditionalExceedanceProfile"
        )
    profile.as_payload()
    if profile.status not in {
        ExceedanceStatus.DEFINED_POINT,
        ExceedanceStatus.DEFINED_ENVELOPE,
    }:
        raise VectorTensorStatisticalFoundationError(
            "VT-S4 certification requires a defined probability-law profile"
        )
    if profile.sampling_law is None or profile.lane is None:
        raise VectorTensorStatisticalFoundationError(
            "defined survival profile lost its sampling law"
        )
    for values in (profile.lower, profile.upper, profile.point):
        if values is not None and any(
            left < right
            for left, right in zip(values, values[1:], strict=False)
        ):
            raise VectorTensorStatisticalFoundationError(
                "survival profile is not nonincreasing"
            )
    return SurvivalMonotonicityReport(
        profile_id=profile.profile_id,
        sampling_law=profile.sampling_law.value,
        lane=profile.lane.value,
        threshold_count=len(profile.thresholds),
        exact_empirical_measure_statement=True,
    )


@dataclass(frozen=True)
class SamplewisePushforwardReport:
    pushforward_id: str
    sample_count: int
    functional_count: int
    complete_cell_count: int
    missing_or_ineligible_cell_count: int
    summary_status: str
    claim_ceiling: str = CLAIM_CEILING


def certify_samplewise_pushforward(
    pushforward: CertifiedFunctionalPushforward,
) -> SamplewisePushforwardReport:
    """Revalidate one sealed VT-S7 sample-by-functional pushforward."""

    if type(pushforward) is not CertifiedFunctionalPushforward:
        raise TypeError(
            "pushforward must be an exact CertifiedFunctionalPushforward"
        )
    pushforward.as_payload()
    statuses = tuple(
        status for row in pushforward.cell_statuses for status in row
    )
    complete = sum(
        status
        in {
            FunctionalCellStatus.DEFINED,
            FunctionalCellStatus.CONDITIONAL_ANCHOR,
        }
        for status in statuses
    )
    return SamplewisePushforwardReport(
        pushforward_id=pushforward.pushforward_id,
        sample_count=len(pushforward.sample_state_ids),
        functional_count=len(pushforward.functional_ids),
        complete_cell_count=complete,
        missing_or_ineligible_cell_count=len(statuses) - complete,
        summary_status=pushforward.summary_status.value,
    )


@dataclass(frozen=True)
class RatioPushforwardComparison:
    samplewise_ratios: tuple[float, ...]
    mean_of_samplewise_ratios: float
    ratio_of_means: float
    interchangeable: bool
    claim_ceiling: str = CLAIM_CEILING


def compare_samplewise_ratio_to_ratio_of_means(
    numerators: Sequence[object],
    denominators: Sequence[object],
) -> RatioPushforwardComparison:
    """Expose, rather than erase, the VT-S7 plug-in discrepancy."""

    numerator = _vector(numerators, "numerators")
    denominator = _vector(denominators, "denominators")
    if len(numerator) != len(denominator) or len(numerator) == 0:
        raise VectorTensorStatisticalFoundationError(
            "numerators and denominators must have one non-empty common length"
        )
    if np.any(denominator == 0.0):
        raise VectorTensorStatisticalFoundationError(
            "sample-wise denominators must be nonzero"
        )
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        ratios = numerator / denominator
    denominator_mean = float(np.mean(denominator))
    if denominator_mean == 0.0:
        raise VectorTensorStatisticalFoundationError(
            "mean denominator must be nonzero"
        )
    samplewise_mean = float(np.mean(ratios))
    plug_in = float(np.mean(numerator)) / denominator_mean
    if not (
        np.all(np.isfinite(ratios))
        and math.isfinite(samplewise_mean)
        and math.isfinite(plug_in)
    ):
        raise VectorTensorStatisticalFoundationError(
            "ratio pushforward calculations must remain finite"
        )
    return RatioPushforwardComparison(
        samplewise_ratios=tuple(float(value) for value in ratios),
        mean_of_samplewise_ratios=samplewise_mean,
        ratio_of_means=plug_in,
        interchangeable=math.isclose(
            samplewise_mean, plug_in, rel_tol=0.0, abs_tol=1e-14
        ),
    )


@dataclass(frozen=True)
class PairedContrastCovarianceReport:
    contrast_covariance: tuple[tuple[float, ...], ...]
    omitted_cross_covariance: tuple[tuple[float, ...], ...]
    omitted_minus_actual: tuple[tuple[float, ...], ...]
    actual_minus_omitted: tuple[tuple[float, ...], ...]
    joint_rank: int
    claim_ceiling: str = CLAIM_CEILING


def paired_contrast_covariance(
    *,
    covariance_aa: Sequence[Sequence[object]],
    covariance_bb: Sequence[Sequence[object]],
    covariance_ab: Sequence[Sequence[object]],
    covariance_ba: Sequence[Sequence[object]],
    pairing_status: PairingStatus | str,
) -> PairedContrastCovarianceReport:
    """Evaluate VT-S8 with an explicit signed omission convention."""

    try:
        status = PairingStatus(pairing_status)
    except ValueError as exc:
        raise VectorTensorStatisticalFoundationError(
            "pairing_status is not registered"
        ) from exc
    if status is not PairingStatus.PAIRED_JOINT_LAW:
        raise VectorTensorStatisticalFoundationError(
            "independent marginals cannot be relabelled as paired covariance"
        )
    aa = _matrix(covariance_aa, "covariance_aa")
    size = aa.shape[0]
    bb = _matrix(covariance_bb, "covariance_bb", size=size)
    ab = _matrix(covariance_ab, "covariance_ab", size=size)
    ba = _matrix(covariance_ba, "covariance_ba", size=size)
    if not np.allclose(aa, aa.T, atol=0.0, rtol=0.0) or not np.allclose(
        bb, bb.T, atol=0.0, rtol=0.0
    ):
        raise VectorTensorStatisticalFoundationError(
            "marginal covariance blocks must be exactly symmetric"
        )
    if not np.allclose(ba, ab.T, atol=0.0, rtol=0.0):
        raise VectorTensorStatisticalFoundationError(
            "ordered cross-covariance blocks must satisfy C_ba=C_ab^T"
        )
    joint = np.block([[aa, ab], [ba, bb]])
    if not _exact_float_psd(joint):
        raise VectorTensorStatisticalFoundationError(
            "joint covariance block must be positive semidefinite"
        )
    with np.errstate(over="ignore", invalid="ignore"):
        contrast = aa + bb - ab - ba
        omitted = aa + bb
        omitted_minus_actual = ab + ba
        actual_minus_omitted = -omitted_minus_actual
    if any(
        not np.all(np.isfinite(matrix))
        for matrix in (
            contrast,
            omitted,
            omitted_minus_actual,
            actual_minus_omitted,
        )
    ):
        raise VectorTensorStatisticalFoundationError(
            "paired covariance calculation must remain finite"
        )
    joint_rank = _exact_float_rank(joint)

    def freeze(matrix: np.ndarray) -> tuple[tuple[float, ...], ...]:
        return tuple(tuple(float(value) for value in row) for row in matrix)

    return PairedContrastCovarianceReport(
        contrast_covariance=freeze(contrast),
        omitted_cross_covariance=freeze(omitted),
        omitted_minus_actual=freeze(omitted_minus_actual),
        actual_minus_omitted=freeze(actual_minus_omitted),
        joint_rank=joint_rank,
    )


@dataclass(frozen=True)
class ExactParitySignReport:
    positive_count: int
    negative_count: int
    tie_count: int
    conditioned_nonzero_count: int
    two_sided_p_numerator: int
    two_sided_p_denominator: int
    conditional_sign_law: str
    claim_ceiling: str = CLAIM_CEILING

    @property
    def two_sided_p_value(self) -> Fraction:
        return Fraction(
            self.two_sided_p_numerator, self.two_sided_p_denominator
        )


def exact_parity_sign_test(
    values: Sequence[object],
    *,
    parity_odd: bool,
    uniform_conditional_sign_vector: bool,
) -> ExactParitySignReport:
    """Compute TF-09 only under the full conditional sign-flip premise."""

    if parity_odd is not True:
        raise VectorTensorStatisticalFoundationError(
            "TF-09 requires a registered parity-odd statistic"
        )
    if uniform_conditional_sign_vector is not True:
        raise VectorTensorStatisticalFoundationError(
            "pooled exact sign testing requires a uniform conditional "
            "sign-vector law"
        )
    vector = _vector(values, "values")
    positive = int(np.count_nonzero(vector > 0.0))
    negative = int(np.count_nonzero(vector < 0.0))
    ties = int(np.count_nonzero(vector == 0.0))
    nonzero = positive + negative
    if nonzero == 0:
        p_value = Fraction(1, 1)
    else:
        tail = sum(
            math.comb(nonzero, index)
            for index in range(min(positive, negative) + 1)
        )
        p_value = min(Fraction(1, 1), Fraction(2 * tail, 2**nonzero))
    return ExactParitySignReport(
        positive_count=positive,
        negative_count=negative,
        tie_count=ties,
        conditioned_nonzero_count=nonzero,
        two_sided_p_numerator=p_value.numerator,
        two_sided_p_denominator=p_value.denominator,
        conditional_sign_law="UNIFORM_CONDITIONAL_SIGN_VECTOR",
    )


def _fraction(value: object, name: str) -> Fraction:
    if isinstance(value, bool):
        raise VectorTensorStatisticalFoundationError(
            f"{name} must be an exact rational"
        )
    if isinstance(value, Fraction):
        return value
    if isinstance(value, Integral):
        return Fraction(int(value), 1)
    if isinstance(value, Rational):
        return Fraction(value)
    raise VectorTensorStatisticalFoundationError(
        f"{name} must be an exact rational encoded as int or Fraction"
    )


def _conditional_expectations(
    weights: tuple[Fraction, ...],
    target: tuple[Fraction, ...],
    labels: tuple[Hashable, ...],
) -> dict[Hashable, Fraction]:
    mass: dict[Hashable, Fraction] = {}
    weighted: dict[Hashable, Fraction] = {}
    for probability, value, label in zip(
        weights, target, labels, strict=True
    ):
        mass[label] = mass.get(label, Fraction(0, 1)) + probability
        weighted[label] = (
            weighted.get(label, Fraction(0, 1)) + probability * value
        )
    if any(value <= 0 for value in mass.values()):
        raise VectorTensorStatisticalFoundationError(
            "every conditional cell must have positive mass"
        )
    return {label: weighted[label] / mass[label] for label in mass}


@dataclass(frozen=True)
class FiniteTowerIdentityReport:
    rung_count: int
    atom_count: int
    exact_equalities: tuple[bool, ...]
    conditional_expectations: tuple[
        tuple[tuple[str, str], ...], ...
    ]
    claim_ceiling: str = CLAIM_CEILING


def certify_finite_partition_tower(
    *,
    weights: Sequence[object],
    common_target: Sequence[object],
    partitions: Sequence[Sequence[Hashable]],
) -> FiniteTowerIdentityReport:
    """Verify TF-11 on one common target and explicit finite filtration."""

    probabilities = tuple(
        _fraction(value, "weights") for value in weights
    )
    target = tuple(
        _fraction(value, "common_target") for value in common_target
    )
    if (
        not probabilities
        or len(probabilities) != len(target)
        or sum(probabilities, Fraction(0, 1)) != 1
        or any(value <= 0 for value in probabilities)
    ):
        raise VectorTensorStatisticalFoundationError(
            "weights must be positive exact probabilities summing to one"
        )
    if isinstance(partitions, (str, bytes)) or not isinstance(
        partitions, Sequence
    ) or len(partitions) < 2:
        raise VectorTensorStatisticalFoundationError(
            "finite tower requires at least two partition rungs"
        )
    try:
        normalized = tuple(tuple(partition) for partition in partitions)
    except TypeError as exc:
        raise VectorTensorStatisticalFoundationError(
            "every partition rung must be a sequence of labels"
        ) from exc
    if any(len(partition) != len(target) for partition in normalized):
        raise VectorTensorStatisticalFoundationError(
            "every partition must label the common atomic space"
        )
    for partition in normalized:
        for label in partition:
            try:
                hash(label)
            except TypeError as exc:
                raise VectorTensorStatisticalFoundationError(
                    "partition labels must be hashable"
                ) from exc
    conditional = tuple(
        _conditional_expectations(probabilities, target, partition)
        for partition in normalized
    )
    equalities: list[bool] = []
    for coarse_index in range(len(normalized) - 1):
        coarse = normalized[coarse_index]
        fine = normalized[coarse_index + 1]
        coarse_by_fine: dict[Hashable, Hashable] = {}
        for coarse_label, fine_label in zip(coarse, fine, strict=True):
            if (
                fine_label in coarse_by_fine
                and coarse_by_fine[fine_label] != coarse_label
            ):
                raise VectorTensorStatisticalFoundationError(
                    "finer partition does not refine the preceding rung"
                )
            coarse_by_fine[fine_label] = coarse_label
        fine_values = tuple(conditional[coarse_index + 1][label] for label in fine)
        iterated = _conditional_expectations(
            probabilities, fine_values, coarse
        )
        equal = iterated == conditional[coarse_index]
        if not equal:
            raise VectorTensorStatisticalFoundationError(
                "finite conditional-expectation tower identity failed"
            )
        equalities.append(equal)
    serialized = tuple(
        tuple(
            sorted(
                (
                    str(label),
                    f"{value.numerator}/{value.denominator}",
                )
                for label, value in rung.items()
            )
        )
        for rung in conditional
    )
    return FiniteTowerIdentityReport(
        rung_count=len(normalized),
        atom_count=len(target),
        exact_equalities=tuple(equalities),
        conditional_expectations=serialized,
    )


__all__ = [
    "ALLOWED_USE",
    "AcceptanceBoundaryRelation",
    "AcceptanceBodyKind",
    "AcceptanceBodySpec",
    "AcceptanceGaugeResult",
    "CLAIM_CEILING",
    "EvidenceGrade",
    "EXPECTED_REGISTRY_SHA256",
    "EXPECTED_LEGACY_REFERENCE_IDS",
    "EXPECTED_TF_IDS",
    "EXPECTED_VT_IDS",
    "ExactParitySignReport",
    "FORBIDDEN_USE",
    "FiniteTowerIdentityReport",
    "FoundationVerdict",
    "PairingStatus",
    "PairedContrastCovarianceReport",
    "PillarSCoreRegistry",
    "RatioPushforwardComparison",
    "REGISTRY_PATH",
    "SamplewisePushforwardReport",
    "ScalarizationDominanceReport",
    "StatisticalProofRecord",
    "SurvivalMonotonicityReport",
    "VectorTensorStatisticalFoundationError",
    "certify_deterministic_scalarization",
    "certify_finite_partition_tower",
    "certify_samplewise_pushforward",
    "certify_survival_monotonicity",
    "compare_samplewise_ratio_to_ratio_of_means",
    "evaluate_acceptance_gauge",
    "exact_parity_sign_test",
    "load_pillar_s_core_registry",
    "paired_contrast_covariance",
]
