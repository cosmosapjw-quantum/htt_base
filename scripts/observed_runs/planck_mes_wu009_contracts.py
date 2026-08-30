#!/usr/bin/env python3
"""Pure standard-library contracts for PMG-WU-009 Gate A and bounded Gate B.

The numerical checks in this module are executable checks of deliberately
bounded identities, domains, and counterexamples.  They are not a replay of
the unavailable P01--P27 formal proof dossier.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
import itertools
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


AUTHORITY_SOURCE = "USER_SUPPLIED_SUMMARY"
FORMAL_PROOF_PROVENANCE = "FORMAL_DOSSIER_PENDING"
EVIDENCE_STATUS = "SUMMARY_ONLY_FORMAL_DOSSIER_PENDING"
RELEASE_STATUS = "NOT_RELEASED_FORMAL_DOSSIER_PENDING"
LEDGER_FORMAT = "PLANCK_MES_WU009_THEOREM_ADJUDICATION_V1"
ALLOWED_VERDICTS = frozenset(
    {"PROVED", "STRENGTHENED", "CORRECTED", "REFUTED", "UNDEFINED"}
)


def _ids(prefix: str, count: int) -> tuple[str, ...]:
    return tuple(f"{prefix}{number:02d}" for number in range(1, count + 1))


EXPECTED_ROW_IDS = frozenset(
    _ids("A", 14) + _ids("B", 22) + _ids("C", 18) + _ids("D", 8) + _ids("E", 16)
)


def _parse_authority_map(specification: str) -> dict[str, tuple[str, str]]:
    parsed: dict[str, tuple[str, str]] = {}
    for item in specification.split():
        row_id, verdict, proof = item.split(":")
        parsed[row_id] = (verdict, f"USER_SUMMARY:{proof}")
    return parsed


EXPECTED_AUTHORITY = _parse_authority_map(
    """
    A01:PROVED:P01 A02:PROVED:P01 A03:CORRECTED:P02 A04:PROVED:P03
    A05:PROVED:P04 A06:PROVED:P04 A07:PROVED:P05 A08:PROVED:P05
    A09:PROVED:P05 A10:REFUTED:P06 A11:REFUTED:P07 A12:PROVED:P08
    A13:PROVED:P08 A14:PROVED:P19
    B01:PROVED:P01 B02:PROVED:P09 B03:PROVED:P09 B04:PROVED:P09
    B05:PROVED:P09 B06:PROVED:P10 B07:PROVED:P10 B08:PROVED:P10
    B09:PROVED:P10 B10:PROVED:P11 B11:PROVED:P12 B12:PROVED:P12
    B13:PROVED:P13 B14:PROVED:P13 B15:PROVED:P13 B16:PROVED:P13
    B17:PROVED:P14 B18:STRENGTHENED:P14 B19:STRENGTHENED:P14
    B20:PROVED:P14 B21:CORRECTED:P15 B22:PROVED:P06
    C01:PROVED:P16 C02:PROVED:P16 C03:PROVED:P11 C04:STRENGTHENED:P11
    C05:PROVED:P11 C06:PROVED:P11 C07:REFUTED:P17 C08:PROVED:P18
    C09:PROVED:P18 C10:PROVED:P18 C11:STRENGTHENED:P18 C12:PROVED:P18
    C13:PROVED:P18 C14:CORRECTED:P18 C15:PROVED:P20 C16:PROVED:P20
    C17:PROVED:P20 C18:UNDEFINED:P21
    D01:PROVED:P22 D02:PROVED:P22 D03:PROVED:P22 D04:PROVED:P22
    D05:PROVED:P22 D06:PROVED:P23 D07:PROVED:P23 D08:REFUTED:P23
    E01:PROVED:P19 E02:CORRECTED:P19 E03:PROVED:P19 E04:PROVED:P19
    E05:UNDEFINED:P24 E06:CORRECTED:P24 E07:PROVED:P25 E08:PROVED:P19
    E09:STRENGTHENED:P25 E10:PROVED:P23 E11:PROVED:P23 E12:PROVED:P26
    E13:PROVED:P26 E14:PROVED:P26 E15:REFUTED:P27 E16:PROVED:P27
    """
)


class ContractState(str, Enum):
    PASS = "PASS"
    ABSTAIN = "ABSTAIN"
    REJECT = "REJECT"


@dataclass(frozen=True)
class ContractDiagnostic:
    state: ContractState
    code: str
    message: str
    metrics: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "code": self.code,
            "message": self.message,
            "metrics": _json_safe(self.metrics),
        }


@dataclass(frozen=True)
class EPath:
    probability: float
    increments: tuple[float, ...]


class TemperatureNoiseModel(str, Enum):
    UNTRUNCATED_GAUSSIAN_DIRECT_T = "UNTRUNCATED_GAUSSIAN_DIRECT_T"
    OTHER_DECLARED_MODEL = "OTHER_DECLARED_MODEL"


class FitObjective(str, Enum):
    GAUSSIAN_DIRECT_T_WEIGHTED_LEAST_SQUARES = (
        "GAUSSIAN_DIRECT_T_WEIGHTED_LEAST_SQUARES"
    )
    UNWEIGHTED_INVERSE_SQUARE = "UNWEIGHTED_INVERSE_SQUARE"


class ProjectionDomain(str, Enum):
    CLOSED_CONVEX_CONE = "CLOSED_CONVEX_CONE"
    BOUNDED_CONVEX_BODY = "BOUNDED_CONVEX_BODY"


def _json_safe(value: Any) -> Any:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    return value


def load_ledger(path: Path | str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("theorem adjudication ledger must be a JSON object")
    return payload


def validate_ledger(ledger: Mapping[str, Any]) -> ContractDiagnostic:
    """Validate exact row authority without upgrading summary evidence."""

    issues: list[str] = []
    schema_version = ledger.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        issues.append("schema_version must equal 1")
    if ledger.get("format") != LEDGER_FORMAT:
        issues.append(f"format must equal {LEDGER_FORMAT}")
    if ledger.get("authority_source") != AUTHORITY_SOURCE:
        issues.append("authority_source must be USER_SUPPLIED_SUMMARY")
    if ledger.get("formal_proof_provenance") != FORMAL_PROOF_PROVENANCE:
        issues.append("formal_proof_provenance must remain FORMAL_DOSSIER_PENDING")
    if ledger.get("formal_dossier_replayed") is not False:
        issues.append("formal_dossier_replayed must be exactly false")
    rows = ledger.get("rows")
    if not isinstance(rows, list):
        rows = []
        issues.append("rows must be a list")
    row_ids = [row.get("id") for row in rows if isinstance(row, Mapping)]
    if len(rows) != 78:
        issues.append(f"expected 78 rows, found {len(rows)}")
    declared_row_count = ledger.get("row_count")
    if type(declared_row_count) is not int or declared_row_count != len(rows):
        issues.append("declared row_count differs from materialized rows")
    if len(row_ids) != len(set(row_ids)):
        issues.append("row ids are not unique")
    if set(row_ids) != EXPECTED_ROW_IDS:
        missing = sorted(EXPECTED_ROW_IDS.difference(row_ids))
        extra = sorted(set(row_ids).difference(EXPECTED_ROW_IDS))
        issues.append(f"row id set mismatch; missing={missing}, extra={extra}")

    required = {
        "id",
        "verdict",
        "assumptions_and_domain",
        "withdrawn_or_narrowed_claim",
        "replacement_statement",
        "summary_proof_reference",
        "executable_test_ids",
        "affected_claims",
        "affected_files",
        "evidence_status",
        "release_status",
    }
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            issues.append(f"row {index} is not an object")
            continue
        row_id = row.get("id", f"row-{index}")
        missing_fields = sorted(required.difference(row))
        if missing_fields:
            issues.append(f"{row_id}: missing fields {missing_fields}")
            continue
        expected = EXPECTED_AUTHORITY.get(str(row_id))
        if expected is not None:
            if row.get("verdict") != expected[0]:
                issues.append(f"{row_id}: verdict differs from accepted authority")
            if row.get("summary_proof_reference") != expected[1]:
                issues.append(f"{row_id}: summary proof reference differs")
        if row.get("verdict") not in ALLOWED_VERDICTS:
            issues.append(f"{row_id}: invalid verdict")
        for name in ("assumptions_and_domain", "executable_test_ids", "affected_claims", "affected_files"):
            value = row.get(name)
            if not isinstance(value, list) or not value or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                issues.append(f"{row_id}: {name} must be a nonempty string list")
        for name in ("withdrawn_or_narrowed_claim", "replacement_statement"):
            value = row.get(name)
            if not isinstance(value, str) or not value.strip():
                issues.append(f"{row_id}: {name} must be nonempty text")
        if row.get("evidence_status") != EVIDENCE_STATUS:
            issues.append(f"{row_id}: evidence status promotes unavailable proof")
        if row.get("release_status") != RELEASE_STATUS:
            issues.append(f"{row_id}: release status promotes unavailable proof")
        serialized = json.dumps(row, sort_keys=True)
        if "LOCALLY_REPLAYED" in serialized or "FORMAL_DOSSIER_REPLAYED" in serialized:
            issues.append(f"{row_id}: falsely claims local formal replay")

    state = ContractState.PASS if not issues else ContractState.REJECT
    return ContractDiagnostic(
        state,
        "LEDGER_VALID" if not issues else "LEDGER_INVALID",
        "ledger matches the accepted summary authority and pending-proof boundary"
        if not issues
        else "; ".join(issues),
        {"row_count": len(rows), "issue_count": len(issues), "issues": tuple(issues)},
    )


def _finite_tuple(values: Sequence[float], *, size: int, name: str) -> tuple[float, ...]:
    converted = tuple(float(value) for value in values)
    if len(converted) != size or not all(math.isfinite(value) for value in converted):
        raise ValueError(f"{name} must contain {size} finite values")
    return converted


def _positive_finite_tolerance(value: float) -> float:
    if isinstance(value, bool):
        raise ValueError("tolerance must be a positive finite real number")
    tolerance = float(value)
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be a positive finite real number")
    return tolerance


def stf_cubic_contract(
    eigenvalues: Sequence[float], *, tolerance: float = 1.0e-12
) -> ContractDiagnostic:
    """Check |tr(Q^3)| <= tr(Q^2)^(3/2)/sqrt(6) on STF2 spectra."""

    tolerance = _positive_finite_tolerance(tolerance)
    spectrum = _finite_tuple(eigenvalues, size=3, name="eigenvalues")
    trace = sum(spectrum)
    scale = max(1.0, max(abs(value) for value in spectrum))
    if abs(trace) > tolerance * scale:
        return ContractDiagnostic(
            ContractState.REJECT,
            "OUTSIDE_STF2_TRACEFREE_DOMAIN",
            "the cubic STF bound requires a trace-free three-spectrum",
            {"trace": trace},
        )
    quadratic = sum(value * value for value in spectrum)
    cubic = sum(value**3 for value in spectrum)
    bound = quadratic**1.5 / math.sqrt(6.0)
    slack = bound - abs(cubic)
    passed = slack >= -tolerance * max(1.0, bound)
    saturated = passed and abs(slack) <= tolerance * max(1.0, bound)
    return ContractDiagnostic(
        ContractState.PASS if passed else ContractState.REJECT,
        "STF_CUBIC_BOUND_VERIFIED" if passed else "STF_CUBIC_BOUND_VIOLATION",
        "bounded numerical identity check; not a formal-dossier replay",
        {
            "quadratic": quadratic,
            "absolute_cubic": abs(cubic),
            "bound": bound,
            "slack": slack,
            "saturated": saturated,
        },
    )


def _determinant3(matrix: Sequence[Sequence[float]]) -> float:
    rows = tuple(_finite_tuple(row, size=3, name="matrix row") for row in matrix)
    if len(rows) != 3:
        raise ValueError("matrix must have three rows")
    a, b, c = rows
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def generic_stratum_contract(
    krylov_matrix: Sequence[Sequence[float]], *, tolerance: float = 1.0e-12
) -> ContractDiagnostic:
    """Pass only a scale-aware det(K) != 0 generic-stratum certificate."""

    tolerance = _positive_finite_tolerance(tolerance)
    rows = tuple(tuple(float(value) for value in row) for row in krylov_matrix)
    if len(rows) != 3:
        raise ValueError("krylov matrix must have three rows")
    row_norms = tuple(math.hypot(*row) for row in rows)
    if any(not math.isfinite(norm) or norm <= 0.0 for norm in row_norms):
        return ContractDiagnostic(
            ContractState.ABSTAIN,
            "BLOCKED_BY_DEGENERATE_STRATUM",
            "row normalization is zero or nonfinite; no generic reconstruction",
            {"row_norms": row_norms, "relative_margin": 0.0},
        )
    normalized = tuple(
        tuple(value / norm for value in row) for row, norm in zip(rows, row_norms)
    )
    determinant = _determinant3(normalized)
    margin = abs(determinant)
    if not math.isfinite(determinant) or not math.isfinite(margin):
        return ContractDiagnostic(
            ContractState.ABSTAIN,
            "BLOCKED_BY_NUMERICAL_STRATUM_CERTIFICATE",
            "normalized determinant is nonfinite; no generic reconstruction",
            {
                "normalized_determinant": determinant,
                "relative_margin": margin,
            },
        )
    if margin <= tolerance:
        return ContractDiagnostic(
            ContractState.ABSTAIN,
            "BLOCKED_BY_DEGENERATE_STRATUM",
            "det(K) is zero or numerically unstable; no generic reconstruction",
            {
                "normalized_determinant": determinant,
                "relative_margin": margin,
            },
        )
    return ContractDiagnostic(
        ContractState.PASS,
        "GENERIC_STRATUM_CERTIFIED",
        "det(K) has a resolved nonzero margin",
        {
            "normalized_determinant": determinant,
            "relative_margin": margin,
        },
    )


def mirror_chirality_control(
    left_o3_invariants: Sequence[float],
    right_o3_invariants: Sequence[float],
    left_chirality: float,
    right_chirality: float,
    *,
    tolerance: float = 1.0e-12,
) -> ContractDiagnostic:
    """Require the mirror control to collide in O(3) data and split in chirality."""

    tolerance = _positive_finite_tolerance(tolerance)
    left = tuple(float(value) for value in left_o3_invariants)
    right = tuple(float(value) for value in right_o3_invariants)
    collision = len(left) == len(right) and all(
        math.isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)
        for a, b in zip(left, right)
    )
    opposite = (
        abs(left_chirality) > tolerance
        and math.isclose(
            float(left_chirality),
            -float(right_chirality),
            rel_tol=tolerance,
            abs_tol=tolerance,
        )
    )
    passed = collision and opposite
    return ContractDiagnostic(
        ContractState.PASS if passed else ContractState.REJECT,
        "MIRROR_CHIRALITY_LOSS_DETECTED" if passed else "INVALID_MIRROR_CONTROL",
        "O(3)-only features lose mirror chirality" if passed else "control does not isolate chirality loss",
        {"o3_collision": collision, "opposite_nonzero_chirality": opposite},
    )


def weak_upper_rank_pvalues(scores: Sequence[float]) -> tuple[Fraction, ...]:
    values = tuple(float(score) for score in scores)
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("scores must be a nonempty finite sequence")
    count = len(values)
    return tuple(
        Fraction(sum(other >= value for other in values), count) for value in values
    )


def finite_rank_superuniformity_contract(scores: Sequence[float]) -> ContractDiagnostic:
    """Exhaustively check weak-rank superuniformity for a finite tied pool."""

    pvalues = weak_upper_rank_pvalues(scores)
    thresholds = sorted(set(pvalues) | {Fraction(0), Fraction(1)})
    violations: list[tuple[Fraction, Fraction]] = []
    for threshold in thresholds:
        probability = Fraction(sum(value <= threshold for value in pvalues), len(pvalues))
        if probability > threshold:
            violations.append((threshold, probability))
    passed = not violations
    return ContractDiagnostic(
        ContractState.PASS if passed else ContractState.REJECT,
        "FINITE_RANK_SUPERUNIFORM" if passed else "FINITE_RANK_INVALID",
        "weak finite ranks are superuniform over the exchangeable query label",
        {"pvalues": pvalues, "violations": tuple(violations)},
    )


def _loo_midrank(scores: Sequence[float], index: int) -> Fraction:
    query = scores[index]
    references = tuple(scores[:index]) + tuple(scores[index + 1 :])
    if not references:
        raise ValueError("LOO midrank requires at least two rows")
    less = sum(value < query for value in references)
    tied = sum(value == query for value in references)
    return (Fraction(less, 1) + Fraction(tied, 2)) / len(references)


def decreasing_tail_swap_contract(
    scores: Sequence[float], transformed_scores: Sequence[float]
) -> ContractDiagnostic:
    original = tuple(float(value) for value in scores)
    transformed = tuple(float(value) for value in transformed_scores)
    if len(original) != len(transformed) or len(original) < 2:
        raise ValueError("score sequences must have equal length of at least two")
    decreasing = True
    for i, j in itertools.combinations(range(len(original)), 2):
        if original[i] < original[j] and not transformed[i] > transformed[j]:
            decreasing = False
        elif original[i] > original[j] and not transformed[i] < transformed[j]:
            decreasing = False
        elif original[i] == original[j] and transformed[i] != transformed[j]:
            decreasing = False
    swaps = tuple(
        _loo_midrank(original, index) + _loo_midrank(transformed, index)
        for index in range(len(original))
    )
    passed = decreasing and all(value == 1 for value in swaps)
    return ContractDiagnostic(
        ContractState.PASS if passed else ContractState.REJECT,
        "DECREASING_TAIL_SWAP_VERIFIED" if passed else "TAIL_SWAP_REQUIRED",
        "a decreasing transform sends the LOO midrank to 1-u",
        {"tail_swap_verified": passed, "midrank_sums": swaps},
    )


def _outputs_equal(left: Sequence[Any], right: Sequence[Any]) -> bool:
    if len(left) != len(right):
        return False
    for first, second in zip(left, right):
        if isinstance(first, (int, float)) and isinstance(second, (int, float)):
            if not math.isclose(float(first), float(second), rel_tol=1.0e-12, abs_tol=1.0e-12):
                return False
        elif first != second:
            return False
    return True


def row_equivariance_contract(
    rows: Sequence[Any], pipeline: Callable[[tuple[Any, ...]], Sequence[Any]]
) -> ContractDiagnostic:
    values = tuple(rows)
    if not 2 <= len(values) <= 7:
        raise ValueError("exhaustive row-equivariance check requires 2--7 rows")
    baseline = tuple(pipeline(values))
    if len(baseline) != len(values):
        raise ValueError("pipeline must emit one score per row")
    for permutation in itertools.permutations(range(len(values))):
        permuted_rows = tuple(values[index] for index in permutation)
        actual = tuple(pipeline(permuted_rows))
        expected = tuple(baseline[index] for index in permutation)
        if not _outputs_equal(actual, expected):
            return ContractDiagnostic(
                ContractState.REJECT,
                "BLOCKED_BY_NON_EQUIVARIANT_ADAPTATION",
                "the complete pipeline privileges a row under permutation",
                {"failing_permutation": permutation, "expected": expected, "actual": actual},
            )
    return ContractDiagnostic(
        ContractState.PASS,
        "ROW_EQUIVARIANCE_VERIFIED",
        "the bounded complete pipeline commutes with every row permutation",
        {"permutations_checked": math.factorial(len(values))},
    )


def selection_symmetry_contract(
    values: Sequence[Any], selector: Callable[[tuple[Any, ...]], int]
) -> ContractDiagnostic:
    rows = tuple(values)
    if not 2 <= len(rows) <= 8 or len(set(rows)) != len(rows):
        raise ValueError("selection symmetry check requires 2--8 distinct rows")
    counts = [0] * len(rows)
    for permuted in itertools.permutations(rows):
        selected = selector(permuted)
        if not isinstance(selected, int) or not 0 <= selected < len(rows):
            raise ValueError("selector must return one valid positional label")
        counts[selected] += 1
    passed = len(set(counts)) == 1
    return ContractDiagnostic(
        ContractState.PASS if passed else ContractState.REJECT,
        "SELECTION_SYMMETRY_VERIFIED" if passed else "SELECTION_SYMMETRY_BROKEN",
        "data-dependent selection may be valid when query-label symmetry is exact",
        {"selected_label_counts": tuple(counts)},
    )


def conditional_e_composition_contract(
    paths: Sequence[EPath], *, tolerance: float = 1.0e-12
) -> ContractDiagnostic:
    """Check conditional means on a finite path tree before multiplying e-values."""

    tolerance = _positive_finite_tolerance(tolerance)
    branches = tuple(paths)
    if not branches:
        raise ValueError("at least one e-path is required")
    depth = len(branches[0].increments)
    if depth == 0 or any(len(path.increments) != depth for path in branches):
        raise ValueError("all e-paths must have the same positive depth")
    if any(
        not math.isfinite(path.probability)
        or path.probability < 0.0
        or any(not math.isfinite(value) or value < 0.0 for value in path.increments)
        for path in branches
    ):
        raise ValueError("probabilities and e-increments must be finite and nonnegative")
    total_probability = sum(path.probability for path in branches)
    if not math.isclose(total_probability, 1.0, rel_tol=tolerance, abs_tol=tolerance):
        raise ValueError("e-path probabilities must sum to one")

    conditional_means: dict[str, float] = {}
    violation: tuple[int, tuple[float, ...], float] | None = None
    for step in range(depth):
        histories = sorted({path.increments[:step] for path in branches})
        for history in histories:
            matching = [path for path in branches if path.increments[:step] == history]
            mass = sum(path.probability for path in matching)
            if mass <= 0.0:
                continue
            mean = sum(
                path.probability * path.increments[step] for path in matching
            ) / mass
            conditional_means[f"step={step + 1};history={history}"] = mean
            if mean > 1.0 + tolerance and violation is None:
                violation = (step + 1, history, mean)
    product_expectation = sum(
        path.probability * math.prod(path.increments) for path in branches
    )
    passed = violation is None and product_expectation <= 1.0 + tolerance
    return ContractDiagnostic(
        ContractState.PASS if passed else ContractState.REJECT,
        "CONDITIONAL_E_COMPOSITION_VERIFIED"
        if passed
        else "MARGINAL_ONLY_E_VALUE_MULTIPLICATION",
        "products require conditionally valid e-increments, not marginal means alone",
        {
            "conditional_means": conditional_means,
            "product_expectation": product_expectation,
            "first_violation": violation,
        },
    )


def boost_response_condition_contract(
    q_eigenvalues: Sequence[float], *, tolerance: float = 1.0e-12
) -> ContractDiagnostic:
    """Check the sharp 5/3 condition bound for q2 I + (6/5) Q^2."""

    tolerance = _positive_finite_tolerance(tolerance)
    spectrum = _finite_tuple(q_eigenvalues, size=3, name="Q eigenvalues")
    trace = sum(spectrum)
    scale = max(1.0, max(abs(value) for value in spectrum))
    if abs(trace) > tolerance * scale:
        return ContractDiagnostic(
            ContractState.REJECT,
            "OUTSIDE_STF2_TRACEFREE_DOMAIN",
            "boost response contract requires trace-free Q",
            {"trace": trace},
        )
    q2 = sum(value * value for value in spectrum)
    if q2 <= tolerance:
        return ContractDiagnostic(
            ContractState.ABSTAIN,
            "RANK_DEFICIENT_ZERO_QUADRUPOLE",
            "zero Q has no invertible boost response",
            {"q2": q2},
        )
    response_eigenvalues = tuple(q2 + 6.0 * value * value / 5.0 for value in spectrum)
    condition_number = max(response_eigenvalues) / min(response_eigenvalues)
    bound = 5.0 / 3.0
    passed = condition_number <= bound + tolerance
    saturated = passed and math.isclose(
        condition_number, bound, rel_tol=tolerance, abs_tol=tolerance
    )
    return ContractDiagnostic(
        ContractState.PASS if passed else ContractState.REJECT,
        "BOOST_RESPONSE_CONDITION_BOUND_VERIFIED"
        if passed
        else "BOOST_RESPONSE_CONDITION_BOUND_VIOLATION",
        "bounded spectral check for the declared Q-to-O response",
        {
            "q2": q2,
            "response_eigenvalues": response_eigenvalues,
            "condition_number": condition_number,
            "bound": bound,
            "saturated": saturated,
        },
    )


def positive_quadratic_domain_contract(
    *,
    certified_minimum: float | None,
    has_absolute_temperature: bool,
    includes_monopole: bool,
    includes_dipole: bool,
) -> ContractDiagnostic:
    """Fail closed unless the full quadratic sky has a strict positive certificate."""

    prerequisites = has_absolute_temperature and includes_monopole and includes_dipole
    if not prerequisites:
        return ContractDiagnostic(
            ContractState.ABSTAIN,
            "NOT_ADMISSIBLE_MISSING_ABSOLUTE_T_MONOPOLE_DIPOLE",
            "the representation inverse needs absolute T plus monopole and dipole",
            {
                "has_absolute_temperature": has_absolute_temperature,
                "includes_monopole": includes_monopole,
                "includes_dipole": includes_dipole,
            },
        )
    if certified_minimum is None or not math.isfinite(float(certified_minimum)):
        return ContractDiagnostic(
            ContractState.ABSTAIN,
            "STRICT_POSITIVITY_UNCERTIFIED",
            "no finite global lower-bound certificate was supplied",
        )
    if float(certified_minimum) <= 0.0:
        return ContractDiagnostic(
            ContractState.REJECT,
            "STRICT_POSITIVITY_REQUIRED",
            "nonnegative boundary cases with zeros are outside the theorem domain",
            {"certified_minimum": float(certified_minimum)},
        )
    return ContractDiagnostic(
        ContractState.PASS,
        "STRICT_POSITIVE_QUADRATIC_DOMAIN_CERTIFIED",
        "representation domain accepted; this does not identify a physical cause",
        {"certified_minimum": float(certified_minimum)},
    )


def temperature_likelihood_contract(
    noise_model: TemperatureNoiseModel, objective: FitObjective
) -> ContractDiagnostic:
    if (
        noise_model is TemperatureNoiseModel.UNTRUNCATED_GAUSSIAN_DIRECT_T
        and objective is FitObjective.UNWEIGHTED_INVERSE_SQUARE
    ):
        return ContractDiagnostic(
            ContractState.REJECT,
            "INVERSE_SQUARE_LIKELIHOOD_REFUSED",
            "under untruncated Gaussian direct-T noise E[Y^-2] diverges; fit direct T",
            {"noise_model": noise_model, "objective": objective},
        )
    if (
        noise_model is TemperatureNoiseModel.UNTRUNCATED_GAUSSIAN_DIRECT_T
        and objective is FitObjective.GAUSSIAN_DIRECT_T_WEIGHTED_LEAST_SQUARES
    ):
        return ContractDiagnostic(
            ContractState.PASS,
            "DIRECT_T_GAUSSIAN_LIKELIHOOD_ACCEPTED",
            "weighted least squares in direct temperature matches the declared likelihood",
            {"noise_model": noise_model, "objective": objective},
        )
    return ContractDiagnostic(
        ContractState.ABSTAIN,
        "LIKELIHOOD_CONTRACT_UNSPECIFIED",
        "the supplied noise/objective pair is outside this bounded contract",
        {"noise_model": noise_model, "objective": objective},
    )


def projection_glrt_domain_contract(domain: object) -> ContractDiagnostic:
    if domain is ProjectionDomain.BOUNDED_CONVEX_BODY:
        return ContractDiagnostic(
            ContractState.REJECT,
            "BOUNDED_BODY_IS_NOT_A_CONE",
            "the Gaussian cone projection formula cannot be copied to a bounded MES body",
            {
                "interval_counterexample": "C=[0,1], z=2",
                "interval_counterexample_lr": 3.0,
                "interval_counterexample_projection_sq": 1.0,
            },
        )
    if domain is ProjectionDomain.CLOSED_CONVEX_CONE:
        return ContractDiagnostic(
            ContractState.PASS,
            "CLOSED_CONVEX_CONE_DOMAIN_ACCEPTED",
            "the bounded domain guard accepts only the declared cone formula domain",
            {"domain": domain},
        )
    return ContractDiagnostic(
        ContractState.REJECT,
        "INVALID_PROJECTION_DOMAIN",
        "unknown or unconverted projection domains fail closed",
        {"domain": repr(domain)},
    )


def run_self_check(ledger_path: Path | str) -> dict[str, Any]:
    """Run all bounded positive and negative controls without writing artifacts."""

    ledger = load_ledger(ledger_path)
    rows = (1.0, 3.0, 8.0)

    def equivariant(values: tuple[float, ...]) -> tuple[float, ...]:
        return tuple(sum(abs(value - other) for other in values) for value in values)

    def broken(values: tuple[float, ...]) -> tuple[float, ...]:
        return (values[0],) * len(values)

    controls: list[tuple[str, ContractDiagnostic, ContractState]] = [
        ("ledger", validate_ledger(ledger), ContractState.PASS),
        ("stf_cubic_saturation", stf_cubic_contract((2, -1, -1)), ContractState.PASS),
        (
            "generic_stratum",
            generic_stratum_contract(((1, 0, 0), (0, 1, 0), (0, 0, 1))),
            ContractState.PASS,
        ),
        (
            "generic_stratum_abstention",
            generic_stratum_contract(((1, 1, 0), (0, 0, 1), (0, 0, 0))),
            ContractState.ABSTAIN,
        ),
        ("finite_rank_ties", finite_rank_superuniformity_contract((0, 0, 1)), ContractState.PASS),
        (
            "decreasing_tail_swap",
            decreasing_tail_swap_contract((0, 0, 2, 5), (0, 0, -2, -5)),
            ContractState.PASS,
        ),
        ("row_equivariance", row_equivariance_contract(rows, equivariant), ContractState.PASS),
        ("broken_row_equivariance", row_equivariance_contract(rows, broken), ContractState.REJECT),
        (
            "selection_symmetry",
            selection_symmetry_contract(rows, lambda values: values.index(max(values))),
            ContractState.PASS,
        ),
        (
            "conditional_e_composition",
            conditional_e_composition_contract(
                (
                    EPath(0.25, (0.5, 0.0)),
                    EPath(0.25, (0.5, 2.0)),
                    EPath(0.25, (1.5, 0.0)),
                    EPath(0.25, (1.5, 2.0)),
                )
            ),
            ContractState.PASS,
        ),
        (
            "marginal_e_product_refusal",
            conditional_e_composition_contract(
                (EPath(0.5, (0.0, 0.0)), EPath(0.5, (2.0, 2.0)))
            ),
            ContractState.REJECT,
        ),
        (
            "boost_response_condition",
            boost_response_condition_contract((5, -4, -1)),
            ContractState.PASS,
        ),
        (
            "positive_quadratic_domain",
            positive_quadratic_domain_contract(
                certified_minimum=0.25,
                has_absolute_temperature=True,
                includes_monopole=True,
                includes_dipole=True,
            ),
            ContractState.PASS,
        ),
        (
            "missing_absolute_temperature",
            positive_quadratic_domain_contract(
                certified_minimum=0.25,
                has_absolute_temperature=False,
                includes_monopole=False,
                includes_dipole=False,
            ),
            ContractState.ABSTAIN,
        ),
        (
            "inverse_square_refusal",
            temperature_likelihood_contract(
                TemperatureNoiseModel.UNTRUNCATED_GAUSSIAN_DIRECT_T,
                FitObjective.UNWEIGHTED_INVERSE_SQUARE,
            ),
            ContractState.REJECT,
        ),
        (
            "mirror_chirality_loss",
            mirror_chirality_control((1, 2, 3, 4), (1, 2, 3, 4), 5, -5),
            ContractState.PASS,
        ),
        (
            "bounded_body_cone_confusion",
            projection_glrt_domain_contract(ProjectionDomain.BOUNDED_CONVEX_BODY),
            ContractState.REJECT,
        ),
    ]
    checks = {
        name: {
            "expected_state": expected.value,
            "matched_expectation": diagnostic.state is expected,
            "diagnostic": diagnostic.as_dict(),
        }
        for name, diagnostic, expected in controls
    }
    passed = all(check["matched_expectation"] for check in checks.values())
    return {
        "format": "PLANCK_MES_WU009_BOUNDED_CONTRACT_SELF_CHECK_V1",
        "status": "SUCCEEDED_NO_CLAIM_PROMOTION" if passed else "FAILED_CONTRACT_CHECK",
        "authority_source": ledger.get("authority_source"),
        "formal_proof_provenance": ledger.get("formal_proof_provenance"),
        "formal_dossier_replayed": ledger.get("formal_dossier_replayed"),
        "bounded_contract_count": len(checks),
        "checks": checks,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if not args.self_check:
        parser.error("--self-check is required; this command performs no generation")
    payload = run_self_check(args.ledger)
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0 if payload["status"] == "SUCCEEDED_NO_CLAIM_PROMOTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
