"""Preregistered synthetic inference validation for Pillar S.

This module implements the PR-272 method contracts.  It does not consume
observed data and it does not promote the source status of any VT theorem.
Every numeric result is conditional on a frozen synthetic design.  HTT owns
the model-dependent validation; MIO may consume only the diagnostic
cross-check returned by :func:`build_mio_depth_cross_check`.

The implementation deliberately keeps the following objects distinct:

* a calibration sample and an evaluation sample;
* simultaneous coverage and unadjusted pointwise coverage;
* a registered joint numerator-anchor law and two marginals;
* full rank and useful identification strength;
* a model-dependent GLS comparison and a MIO residual diagnostic; and
* a finite-library open-set benchmark and a family label.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from numbers import Integral, Real
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import yaml

from common.weak_id_coverage import clopper_pearson_lower


class PillarSInferenceError(ValueError):
    """Raised when a PR-272 statistical contract fails closed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ValidationStatus(_StringEnum):
    VALIDATED_REGISTERED_SYNTHETIC = "VALIDATED_REGISTERED_SYNTHETIC"
    VALIDATED_REGISTERED_LINEAR_CELL = "VALIDATED_REGISTERED_LINEAR_CELL"
    FAILED_REGISTERED_COVERAGE = "FAILED_REGISTERED_COVERAGE"
    FAILED_MISSPECIFIED_COVARIANCE = "FAILED_MISSPECIFIED_COVARIANCE"
    ABSTAIN_WEAK_IDENTIFICATION = "ABSTAIN_WEAK_IDENTIFICATION"
    ABSTAIN_NON_IDENTIFIED = "ABSTAIN_NON_IDENTIFIED"
    INCONCLUSIVE_UNBOUNDED = "INCONCLUSIVE_UNBOUNDED"
    INCONCLUSIVE_MISSING_CONTRACT = "INCONCLUSIVE_MISSING_CONTRACT"


class SourceDisposition(_StringEnum):
    CONDITIONAL_PROGRAM_RETAINED = "CONDITIONAL_PROGRAM_RETAINED"
    PROGRAM_OBLIGATION_RETAINED = "PROGRAM_OBLIGATION_RETAINED"


class ModelCandidate(_StringEnum):
    LOCAL = "LOCAL"
    GLOBAL = "GLOBAL"
    INDETERMINATE = "INDETERMINATE"


CLAIM_CEILING = "diagnostic_only"
SPEC_PATH = Path("docs/research_program/vector_tensor/pr272_spec.yaml")
EXPECTED_SPEC_SHA256 = (
    "4ab978cf971e565dd6a598bd795249555a717aefa8f6c89b26727fdf58f7f9a2"
)
_PR272_FROZEN_RELOCATION_RULES = {
    "pr271_statistical_foundations": {
        "manifest_path": (
            "docs/research_program/vector_tensor/integration/"
            "PR282_PR272_V1_RELOCATION.json"
        ),
        "schema": "htt.pr282.frozen_source_relocation.v1",
        "relocation_id": "PR282-PR272-STATISTICAL-FOUNDATIONS-V1",
        "successor_pr": "PR-282",
        "relocated_path": (
            "docs/research_program/vector_tensor/frozen_sources/"
            "pr272_vector_tensor_statistical_foundations.py"
        ),
        "caveat": (
            "PR-282 exact-sign hardening is the current implementation; "
            "this relocation cannot promote or reseal the PR-272 result"
        ),
    },
    "open_set_response": {
        "manifest_path": (
            "docs/research_program/vector_tensor/integration/"
            "PR283_PR272_OPEN_SET_V1_RELOCATION.json"
        ),
        "schema": "htt.pr283.frozen_source_relocation.v1",
        "relocation_id": "PR283-PR272-OPEN-SET-RESPONSE-V1",
        "successor_pr": "PR-283",
        "relocated_path": (
            "docs/research_program/vector_tensor/frozen_sources/"
            "pr272_open_set_response_classes.py"
        ),
        "caveat": (
            "PR-283 weak-identification precedence is the current implementation; "
            "this relocation cannot promote or reseal the PR-272 result"
        ),
    },
}
REGISTRY_PATH = Path(
    "docs/research_program/vector_tensor/proofs/"
    "PILLAR_S_INFERENCE_VALIDATION_V1.yaml"
)
EXPECTED_REGISTRY_SHA256 = (
    "71e609b1034b3d992c5697cdc714100f739efca8f6eb96fa2999beb438e975bf"
)
EXPECTED_VT_IDS = frozenset(
    {
        "VT-S3",
        "VT-S5",
        "VT-S6",
        "VT-S9",
        "VT-S10",
        "VT-S11",
        "VT-S12",
        "VT-S13",
        "VT-S14",
    }
)
ALLOWED_USE = (
    "registered synthetic coverage and calibration diagnostic",
    "weak-identification abstention diagnostic",
    "finite-library open-set sensitivity diagnostic",
    "HTT-owned synthetic GLS comparison",
    "MIO residual and coherence cross-check without inference ownership",
)
FORBIDDEN_USE = (
    "observed-data or PR-151 partial-data result",
    "post-hoc seed, DGP, tolerance, grid, or threshold adjustment",
    "optimizer output relabelled as a sample or posterior",
    "MIO likelihood, posterior, Bayes factor, or evidence",
    "native solver or native morphology-atlas validation",
    "geometry detection or Bianchi family identification",
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise PillarSInferenceError(f"{name} must be non-empty trimmed text")
    return value


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise PillarSInferenceError(f"{name} must be real")
    out = float(value)
    if not math.isfinite(out):
        raise PillarSInferenceError(f"{name} must be finite")
    return out


def _probability(value: object, name: str, *, open_zero: bool = False) -> float:
    out = _real(value, name)
    lower_ok = out > 0.0 if open_zero else out >= 0.0
    if not lower_ok or out > 1.0:
        bracket = "(0, 1]" if open_zero else "[0, 1]"
        raise PillarSInferenceError(f"{name} must be in {bracket}")
    return out


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise PillarSInferenceError(f"{name} must be an integer")
    out = int(value)
    if out < 1:
        raise PillarSInferenceError(f"{name} must be positive")
    return out


def _vector(values: Sequence[object], name: str) -> np.ndarray:
    if isinstance(values, (str, bytes)):
        raise PillarSInferenceError(f"{name} must be a numeric sequence")
    try:
        out = np.asarray(tuple(values), dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PillarSInferenceError(f"{name} must be a finite vector") from exc
    if out.ndim != 1 or not out.size or not np.all(np.isfinite(out)):
        raise PillarSInferenceError(f"{name} must be a non-empty finite vector")
    return out


def _matrix(values: Sequence[Sequence[object]], name: str) -> np.ndarray:
    if isinstance(values, (str, bytes)):
        raise PillarSInferenceError(f"{name} must be a numeric matrix")
    try:
        out = np.asarray(tuple(tuple(row) for row in values), dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PillarSInferenceError(f"{name} must be a finite matrix") from exc
    if (
        out.ndim != 2
        or not out.shape[0]
        or not out.shape[1]
        or not np.all(np.isfinite(out))
    ):
        raise PillarSInferenceError(f"{name} must be a non-empty finite matrix")
    return out


def _square_matrix(
    values: Sequence[Sequence[object]],
    name: str,
    *,
    size: int | None = None,
) -> np.ndarray:
    out = _matrix(values, name)
    if out.shape[0] != out.shape[1] or (
        size is not None and out.shape != (size, size)
    ):
        expected = "square" if size is None else f"shape ({size}, {size})"
        raise PillarSInferenceError(f"{name} must be {expected}")
    return out


def _positive_definite(
    values: Sequence[Sequence[object]],
    name: str,
    *,
    size: int | None = None,
) -> np.ndarray:
    out = _square_matrix(values, name, size=size)
    if not np.array_equal(out, out.T):
        raise PillarSInferenceError(f"{name} must be exactly symmetric")
    try:
        np.linalg.cholesky(out)
    except np.linalg.LinAlgError as exc:
        raise PillarSInferenceError(
            f"{name} must be numerically positive definite"
        ) from exc
    return out


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _payload_sha256(payload: object) -> str:
    return _sha256_bytes(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    )


def _readonly(values: np.ndarray) -> np.ndarray:
    out = np.asarray(values, dtype=float).copy()
    out.setflags(write=False)
    return out


def _cp_lower(covered: int, total: int, confidence: float) -> float:
    _positive_int(total, "total")
    if not isinstance(covered, Integral) or isinstance(covered, bool):
        raise PillarSInferenceError("covered must be an integer")
    if not 0 <= int(covered) <= total:
        raise PillarSInferenceError("covered must be in [0, total]")
    _probability(confidence, "confidence", open_zero=True)
    return float(clopper_pearson_lower(int(covered), total, confidence))


def resolve_preregistered_frozen_input(
    repo_root: Path,
    name: str,
    record: Mapping[str, object],
) -> Path:
    """Resolve one exact PR-272 input without rewriting its preregistration.

    Successors may change an active source only after preserving the exact
    preregistered bytes at a fixed repository-local path and binding that path
    through a successor-specific relocation manifest.
    """

    root = repo_root.resolve()
    relative = record.get("path")
    expected = record.get("sha256")
    if not isinstance(name, str) or not name:
        raise PillarSInferenceError("PR-272 frozen input name is malformed")
    if not isinstance(relative, str) or not isinstance(expected, str):
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} is malformed"
        )

    original_relative = Path(relative)
    if original_relative.is_absolute() or ".." in original_relative.parts:
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} path is not repository-relative"
        )
    original = root / original_relative
    if original.is_file() and not original.is_symlink():
        try:
            original.resolve(strict=True).relative_to(root)
        except (OSError, ValueError) as exc:
            raise PillarSInferenceError(
                f"PR-272 frozen input {name!r} escapes the repository"
            ) from exc
        if _sha256_bytes(original.read_bytes()) == expected:
            return original

    rule = _PR272_FROZEN_RELOCATION_RULES.get(name)
    if rule is None:
        raise PillarSInferenceError(f"PR-272 frozen input {name!r} drifted")
    manifest_relative = Path(rule["manifest_path"])
    manifest_path = root / manifest_relative
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} relocation manifest is missing"
        )
    try:
        manifest_path.resolve(strict=True).relative_to(root)
        relocation = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} relocation manifest is invalid"
        ) from exc

    expected_top = {
        "entries",
        "relocation_id",
        "schema",
        "source_pr",
        "successor_pr",
    }
    if (
        not isinstance(relocation, Mapping)
        or set(relocation) != expected_top
        or relocation.get("schema") != rule["schema"]
        or relocation.get("relocation_id") != rule["relocation_id"]
        or relocation.get("source_pr") != "PR-272"
        or relocation.get("successor_pr") != rule["successor_pr"]
        or not isinstance(relocation.get("entries"), list)
        or len(relocation["entries"]) != 1
    ):
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} relocation binding drifted"
        )
    entry = relocation["entries"][0]
    if (
        not isinstance(entry, Mapping)
        or set(entry)
        != {
            "allowed_use",
            "caveat",
            "frozen_input",
            "original_path",
            "relocated_path",
            "sha256",
        }
        or entry.get("frozen_input") != name
        or entry.get("original_path") != relative
        or entry.get("relocated_path") != rule["relocated_path"]
        or entry.get("sha256") != expected
        or entry.get("allowed_use") != "exact historical PR-272 replay only"
        or entry.get("caveat") != rule["caveat"]
    ):
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} relocation binding drifted"
        )
    relocated_relative = Path(str(entry["relocated_path"]))
    if relocated_relative.is_absolute() or ".." in relocated_relative.parts:
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} relocation path is invalid"
        )
    relocated = root / relocated_relative
    if relocated.is_symlink() or not relocated.is_file():
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} relocation is not a regular file"
        )
    try:
        relocated.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} relocation escapes the repository"
        ) from exc
    if _sha256_bytes(relocated.read_bytes()) != expected:
        raise PillarSInferenceError(
            f"PR-272 frozen input {name!r} relocated bytes drifted"
        )
    return relocated


def load_preregistered_design(repo_root: Path) -> Mapping[str, object]:
    """Load the byte-frozen PR-272 design and reject post-result drift."""

    path = repo_root / SPEC_PATH
    data = path.read_bytes()
    actual = _sha256_bytes(data)
    if actual != EXPECTED_SPEC_SHA256:
        raise PillarSInferenceError(
            f"PR-272 preregistration bytes drifted: {actual}"
        )
    payload = yaml.safe_load(data.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise PillarSInferenceError("PR-272 preregistration must be a mapping")
    if payload.get("frozen_before_result_inspection") is not True:
        raise PillarSInferenceError(
            "PR-272 design must be frozen before result inspection"
        )
    selected = payload.get("selection", {}).get("vt_inference_ids", ())
    if frozenset(selected) != EXPECTED_VT_IDS or len(selected) != 9:
        raise PillarSInferenceError("PR-272 VT obligation selection drifted")
    if payload.get("claim_ceiling") != CLAIM_CEILING:
        raise PillarSInferenceError("PR-272 claim ceiling drifted")
    frozen_inputs = payload.get("frozen_inputs")
    if not isinstance(frozen_inputs, Mapping) or not frozen_inputs:
        raise PillarSInferenceError("PR-272 frozen input registry is missing")
    for name, record in frozen_inputs.items():
        if not isinstance(record, Mapping):
            raise PillarSInferenceError(
                f"PR-272 frozen input {name!r} must be a mapping"
            )
        relative = record.get("path")
        expected = record.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise PillarSInferenceError(
                f"PR-272 frozen input {name!r} is malformed"
            )
        source_path = resolve_preregistered_frozen_input(
            repo_root,
            name,
            record,
        )
        if _sha256_bytes(source_path.read_bytes()) != expected:
            raise PillarSInferenceError(
                f"PR-272 frozen input {name!r} drifted"
            )
    return payload


def derive_seed(master_seed: int, cell_id: str, family: str) -> int:
    """Derive a stable PCG64 seed without relying on Python's hash salt."""

    if isinstance(master_seed, bool) or not isinstance(master_seed, Integral):
        raise PillarSInferenceError("master_seed must be an integer")
    cell = _text(cell_id, "cell_id")
    stream = _text(family, "family")
    digest = hashlib.sha256(
        f"{int(master_seed)}|{cell}|{stream}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


def derive_registered_seed(
    master_seed: int,
    seed_family: Sequence[int],
    cell_id: str,
    family: str,
) -> int:
    """Derive a stream seed bound to the complete registered seed family."""

    if isinstance(master_seed, bool) or not isinstance(master_seed, Integral):
        raise PillarSInferenceError("master_seed must be an integer")
    if isinstance(seed_family, (str, bytes)) or not isinstance(
        seed_family, Sequence
    ):
        raise PillarSInferenceError("seed_family must be an integer sequence")
    normalized: list[int] = []
    for value in seed_family:
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise PillarSInferenceError(
                "seed_family must contain only integers"
            )
        normalized.append(int(value))
    if not normalized or len(set(normalized)) != len(normalized):
        raise PillarSInferenceError(
            "seed_family must be nonempty and contain unique values"
        )
    cell = _text(cell_id, "cell_id")
    stream = _text(family, "family")
    registered = json.dumps(
        normalized,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(
        f"{int(master_seed)}|{registered}|{cell}|{stream}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


@dataclass(frozen=True)
class SimultaneousCalibrationReport:
    status: ValidationStatus
    critical_value: float
    critical_order: int
    alpha: float
    calibration_count: int
    evaluation_count: int
    accepted_count: int
    simultaneous_coverage: float
    family_confidence: float
    coverage_lower_bound: float
    retain_lower_bound: float
    calibration_covariance_id: str
    evaluation_covariance_id: str
    failure_visible: bool
    claim_ceiling: str = CLAIM_CEILING

    @property
    def report_id(self) -> str:
        return _payload_sha256(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "accepted_count": self.accepted_count,
            "alpha": self.alpha,
            "calibration_count": self.calibration_count,
            "calibration_covariance_id": self.calibration_covariance_id,
            "claim_ceiling": self.claim_ceiling,
            "coverage_lower_bound": self.coverage_lower_bound,
            "critical_order": self.critical_order,
            "critical_value": self.critical_value,
            "evaluation_count": self.evaluation_count,
            "evaluation_covariance_id": self.evaluation_covariance_id,
            "failure_visible": self.failure_visible,
            "family_confidence": self.family_confidence,
            "retain_lower_bound": self.retain_lower_bound,
            "simultaneous_coverage": self.simultaneous_coverage,
            "status": self.status.value,
        }


def calibrate_split_max_statistic(
    calibration_vectors: Sequence[Sequence[object]],
    evaluation_vectors: Sequence[Sequence[object]],
    *,
    alpha: float,
    family_confidence: float,
    retain_lower_bound: float,
    calibration_covariance_id: str,
    evaluation_covariance_id: str,
) -> SimultaneousCalibrationReport:
    """Calibrate a finite-family max statistic on an independent split."""

    calibration = _matrix(calibration_vectors, "calibration_vectors")
    evaluation = _matrix(evaluation_vectors, "evaluation_vectors")
    if calibration.shape[1] != evaluation.shape[1]:
        raise PillarSInferenceError(
            "calibration and evaluation dimensions must match"
        )
    alpha_value = _probability(alpha, "alpha", open_zero=True)
    if alpha_value >= 1.0:
        raise PillarSInferenceError("alpha must be less than one")
    confidence = _probability(
        family_confidence, "family_confidence", open_zero=True
    )
    threshold = _probability(retain_lower_bound, "retain_lower_bound")
    calibration_id = _text(
        calibration_covariance_id, "calibration_covariance_id"
    )
    evaluation_id = _text(
        evaluation_covariance_id, "evaluation_covariance_id"
    )
    scores = np.max(np.abs(calibration), axis=1)
    evaluation_scores = np.max(np.abs(evaluation), axis=1)
    order = int(math.ceil((len(scores) + 1) * (1.0 - alpha_value)))
    if order > len(scores):
        raise PillarSInferenceError(
            "calibration sample is too small for the registered alpha"
        )
    critical = float(np.partition(scores, order - 1)[order - 1])
    accepted = int(np.count_nonzero(evaluation_scores <= critical))
    coverage = accepted / len(evaluation_scores)
    lower = _cp_lower(accepted, len(evaluation_scores), confidence)
    covariance_match = calibration_id == evaluation_id
    if not covariance_match:
        status = ValidationStatus.FAILED_MISSPECIFIED_COVARIANCE
    elif lower >= threshold:
        status = ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    else:
        status = ValidationStatus.FAILED_REGISTERED_COVERAGE
    return SimultaneousCalibrationReport(
        status=status,
        critical_value=critical,
        critical_order=order,
        alpha=alpha_value,
        calibration_count=len(scores),
        evaluation_count=len(evaluation_scores),
        accepted_count=accepted,
        simultaneous_coverage=coverage,
        family_confidence=confidence,
        coverage_lower_bound=lower,
        retain_lower_bound=threshold,
        calibration_covariance_id=calibration_id,
        evaluation_covariance_id=evaluation_id,
        failure_visible=status
        in {
            ValidationStatus.FAILED_REGISTERED_COVERAGE,
            ValidationStatus.FAILED_MISSPECIFIED_COVARIANCE,
        },
    )


def require_simultaneous_control(
    report: SimultaneousCalibrationReport,
) -> None:
    if (
        report.status
        is not ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
        or report.calibration_covariance_id
        != report.evaluation_covariance_id
        or report.coverage_lower_bound < report.retain_lower_bound
        or report.failure_visible
    ):
        raise PillarSInferenceError(
            "simultaneous-control claim refused for failed or "
            "misspecified-covariance calibration"
        )


@dataclass(frozen=True)
class JointAnchorLaw:
    law_id: str
    mean: tuple[float, float]
    covariance: np.ndarray
    sample_size: int
    joint_cross_covariance_declared: bool
    content_id: str

    def __post_init__(self) -> None:
        _text(self.law_id, "law_id")
        if len(self.mean) != 2:
            raise PillarSInferenceError("joint anchor mean must have length two")
        _vector(self.mean, "mean")
        covariance = _positive_definite(self.covariance, "covariance", size=2)
        object.__setattr__(self, "covariance", _readonly(covariance))
        _positive_int(self.sample_size, "sample_size")
        if self.joint_cross_covariance_declared is not True:
            raise PillarSInferenceError(
                "joint numerator-anchor cross-covariance must be declared"
            )
        expected = _payload_sha256(
            {
                "covariance": covariance.tolist(),
                "joint_cross_covariance_declared": True,
                "law_id": self.law_id,
                "mean": list(self.mean),
                "sample_size": self.sample_size,
            }
        )
        if self.content_id != expected:
            raise PillarSInferenceError("joint anchor law content id drifted")


def build_joint_anchor_law(
    *,
    law_id: str,
    mean: Sequence[object],
    covariance: Sequence[Sequence[object]],
    sample_size: int,
    joint_cross_covariance_declared: bool,
) -> JointAnchorLaw:
    mean_array = _vector(mean, "mean")
    if mean_array.shape != (2,):
        raise PillarSInferenceError("joint anchor mean must have length two")
    covariance_array = _positive_definite(covariance, "covariance", size=2)
    if joint_cross_covariance_declared is not True:
        raise PillarSInferenceError(
            "marginal numerator and anchor laws cannot replace a joint law"
        )
    payload = {
        "covariance": covariance_array.tolist(),
        "joint_cross_covariance_declared": True,
        "law_id": _text(law_id, "law_id"),
        "mean": mean_array.tolist(),
        "sample_size": _positive_int(sample_size, "sample_size"),
    }
    return JointAnchorLaw(
        law_id=payload["law_id"],
        mean=(float(mean_array[0]), float(mean_array[1])),
        covariance=covariance_array,
        sample_size=payload["sample_size"],
        joint_cross_covariance_declared=True,
        content_id=_payload_sha256(payload),
    )


@dataclass(frozen=True)
class FiellerInterval:
    status: ValidationStatus
    lower: float | None
    upper: float | None
    ratio_point: float | None
    law_id: str


def joint_fieller_interval(
    numerator_hat: float,
    anchor_hat: float,
    *,
    law: JointAnchorLaw,
    normal_critical_value: float,
) -> FiellerInterval:
    """Push one joint Gaussian confidence body through numerator/anchor."""

    numerator = _real(numerator_hat, "numerator_hat")
    anchor = _real(anchor_hat, "anchor_hat")
    critical = _real(normal_critical_value, "normal_critical_value")
    if critical <= 0.0:
        raise PillarSInferenceError("normal_critical_value must be positive")
    covariance = law.covariance / law.sample_size
    var_n = float(covariance[0, 0])
    cov_na = float(covariance[0, 1])
    var_a = float(covariance[1, 1])
    z2 = critical * critical
    quadratic = anchor * anchor - z2 * var_a
    linear = -2.0 * numerator * anchor + 2.0 * z2 * cov_na
    constant = numerator * numerator - z2 * var_n
    discriminant = linear * linear - 4.0 * quadratic * constant
    point = None if anchor == 0.0 else numerator / anchor
    if quadratic <= 0.0 or discriminant < 0.0:
        return FiellerInterval(
            status=ValidationStatus.INCONCLUSIVE_UNBOUNDED,
            lower=None,
            upper=None,
            ratio_point=point,
            law_id=law.law_id,
        )
    root = math.sqrt(max(discriminant, 0.0))
    lower = (-linear - root) / (2.0 * quadratic)
    upper = (-linear + root) / (2.0 * quadratic)
    return FiellerInterval(
        status=ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC,
        lower=min(lower, upper),
        upper=max(lower, upper),
        ratio_point=point,
        law_id=law.law_id,
    )


@dataclass(frozen=True)
class JointAnchorCoverageReport:
    status: ValidationStatus
    law_id: str
    true_ratio: float
    evaluation_count: int
    bounded_count: int
    unbounded_count: int
    covered_count: int
    coverage: float
    coverage_lower_bound: float
    retain_lower_bound: float
    family_confidence: float

    @property
    def report_id(self) -> str:
        return _payload_sha256(self.__dict__)


def evaluate_joint_anchor_coverage(
    estimator_draws: Sequence[Sequence[object]],
    *,
    law: JointAnchorLaw,
    true_ratio: float,
    normal_critical_value: float,
    family_confidence: float,
    retain_lower_bound: float,
) -> JointAnchorCoverageReport:
    draws = _matrix(estimator_draws, "estimator_draws")
    if draws.shape[1] != 2:
        raise PillarSInferenceError(
            "estimator_draws must contain numerator and anchor columns"
        )
    ratio = _real(true_ratio, "true_ratio")
    confidence = _probability(
        family_confidence, "family_confidence", open_zero=True
    )
    retain = _probability(retain_lower_bound, "retain_lower_bound")
    covered = 0
    bounded = 0
    unbounded = 0
    for numerator, anchor in draws:
        interval = joint_fieller_interval(
            float(numerator),
            float(anchor),
            law=law,
            normal_critical_value=normal_critical_value,
        )
        if interval.status is ValidationStatus.INCONCLUSIVE_UNBOUNDED:
            unbounded += 1
            continue
        bounded += 1
        assert interval.lower is not None and interval.upper is not None
        covered += int(interval.lower <= ratio <= interval.upper)
    coverage = covered / len(draws)
    lower = _cp_lower(covered, len(draws), confidence)
    status = (
        ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
        if unbounded == 0 and lower >= retain
        else ValidationStatus.FAILED_REGISTERED_COVERAGE
    )
    return JointAnchorCoverageReport(
        status=status,
        law_id=law.law_id,
        true_ratio=ratio,
        evaluation_count=len(draws),
        bounded_count=bounded,
        unbounded_count=unbounded,
        covered_count=covered,
        coverage=coverage,
        coverage_lower_bound=lower,
        retain_lower_bound=retain,
        family_confidence=confidence,
    )


@dataclass(frozen=True)
class DepthMultiplicityReport:
    status: ValidationStatus
    corrected: SimultaneousCalibrationReport
    pointwise_critical_values: tuple[float, ...]
    unadjusted_familywise_error_rate: float
    adjusted_familywise_error_rate: float
    depth_count: int
    same_centered_target: bool
    nested_path: bool

    @property
    def report_id(self) -> str:
        return _payload_sha256(
            {
                "adjusted_familywise_error_rate": (
                    self.adjusted_familywise_error_rate
                ),
                "corrected": self.corrected.as_payload(),
                "depth_count": self.depth_count,
                "nested_path": self.nested_path,
                "pointwise_critical_values": list(
                    self.pointwise_critical_values
                ),
                "same_centered_target": self.same_centered_target,
                "status": self.status.value,
                "unadjusted_familywise_error_rate": (
                    self.unadjusted_familywise_error_rate
                ),
            }
        )


def evaluate_depth_multiplicity(
    calibration_paths: Sequence[Sequence[object]],
    evaluation_paths: Sequence[Sequence[object]],
    *,
    alpha: float,
    family_confidence: float,
    retain_lower_bound: float,
    covariance_id: str,
    same_centered_target: bool,
    nested_path: bool,
) -> DepthMultiplicityReport:
    if same_centered_target is not True:
        raise PillarSInferenceError(
            "depth path must report the same centered target at every rung"
        )
    if nested_path is not True:
        raise PillarSInferenceError(
            "multiple-depth calibration requires a registered nested path"
        )
    calibration = _matrix(calibration_paths, "calibration_paths")
    evaluation = _matrix(evaluation_paths, "evaluation_paths")
    corrected = calibrate_split_max_statistic(
        calibration,
        evaluation,
        alpha=alpha,
        family_confidence=family_confidence,
        retain_lower_bound=retain_lower_bound,
        calibration_covariance_id=covariance_id,
        evaluation_covariance_id=covariance_id,
    )
    alpha_value = _probability(alpha, "alpha", open_zero=True)
    pointwise_order = int(
        math.ceil((calibration.shape[0] + 1) * (1.0 - alpha_value))
    )
    if pointwise_order > calibration.shape[0]:
        raise PillarSInferenceError(
            "calibration sample is too small for pointwise alpha"
        )
    pointwise_critical = np.asarray(
        [
            float(
                np.partition(
                    np.abs(calibration[:, column]),
                    pointwise_order - 1,
                )[pointwise_order - 1]
            )
            for column in range(calibration.shape[1])
        ]
    )
    unadjusted_rejections = np.any(
        np.abs(evaluation) > pointwise_critical[None, :], axis=1
    )
    adjusted_rejections = np.max(np.abs(evaluation), axis=1) > (
        corrected.critical_value
    )
    status = corrected.status
    return DepthMultiplicityReport(
        status=status,
        corrected=corrected,
        pointwise_critical_values=tuple(
            float(value) for value in pointwise_critical
        ),
        unadjusted_familywise_error_rate=float(
            np.mean(unadjusted_rejections)
        ),
        adjusted_familywise_error_rate=float(np.mean(adjusted_rejections)),
        depth_count=calibration.shape[1],
        same_centered_target=True,
        nested_path=True,
    )


@dataclass(frozen=True)
class WeakIdentificationReport:
    status: ValidationStatus
    supported_rank: int
    parameter_dimension: int
    singular_values: tuple[float, ...]
    minimum_singular_value: float
    singular_value_floor: float
    principal_angle_radians: float
    principal_angle_floor_radians: float
    perturbation_radius: float
    worst_case_parameter_error_bound: float | None
    covariance_id: str
    claim_ceiling: str = CLAIM_CEILING

    @property
    def report_id(self) -> str:
        return _payload_sha256(self.__dict__)


def evaluate_weak_identification(
    response: Sequence[Sequence[object]],
    covariance: Sequence[Sequence[object]],
    *,
    covariance_id: str,
    expected_covariance_id: str,
    singular_value_floor: float,
    local_response_space: Sequence[Sequence[object]],
    global_response_space: Sequence[Sequence[object]],
    principal_angle_floor_radians: float,
    perturbation_radius: float,
    rank_tolerance: float = 1.0e-12,
) -> WeakIdentificationReport:
    matrix = _matrix(response, "response")
    covariance_matrix = _positive_definite(
        covariance, "covariance", size=matrix.shape[0]
    )
    actual_id = _text(covariance_id, "covariance_id")
    expected_id = _text(expected_covariance_id, "expected_covariance_id")
    if actual_id != expected_id:
        raise PillarSInferenceError("wrong covariance identity refused")
    singular_floor = _real(singular_value_floor, "singular_value_floor")
    angle_floor = _real(
        principal_angle_floor_radians, "principal_angle_floor_radians"
    )
    radius = _real(perturbation_radius, "perturbation_radius")
    tolerance = _real(rank_tolerance, "rank_tolerance")
    if min(singular_floor, angle_floor, radius, tolerance) <= 0.0:
        raise PillarSInferenceError(
            "identification floors, radius, and rank tolerance must be positive"
        )
    whitened = np.linalg.solve(np.linalg.cholesky(covariance_matrix), matrix)
    local_space = _matrix(local_response_space, "local_response_space")
    global_space = _matrix(global_response_space, "global_response_space")
    if (
        local_space.shape[0] != matrix.shape[0]
        or global_space.shape[0] != matrix.shape[0]
    ):
        raise PillarSInferenceError(
            "local/global response spaces must share the response codomain"
        )
    cholesky = np.linalg.cholesky(covariance_matrix)
    whitened_local = np.linalg.solve(cholesky, local_space)
    whitened_global = np.linalg.solve(cholesky, global_space)
    local_q, local_r = np.linalg.qr(whitened_local, mode="reduced")
    global_q, global_r = np.linalg.qr(whitened_global, mode="reduced")
    if (
        np.linalg.matrix_rank(local_r, tol=tolerance)
        != local_space.shape[1]
        or np.linalg.matrix_rank(global_r, tol=tolerance)
        != global_space.shape[1]
    ):
        raise PillarSInferenceError(
            "local/global response spaces must have full declared rank"
        )
    maximum_cosine = float(
        np.linalg.svd(local_q.T @ global_q, compute_uv=False)[0]
    )
    angle = math.acos(min(max(maximum_cosine, 0.0), 1.0))
    singular_values = np.linalg.svd(whitened, compute_uv=False)
    rank = int(np.count_nonzero(singular_values > tolerance))
    parameter_dimension = matrix.shape[1]
    minimum = (
        float(singular_values[-1])
        if len(singular_values) >= parameter_dimension
        else 0.0
    )
    if rank < parameter_dimension:
        status = ValidationStatus.ABSTAIN_NON_IDENTIFIED
        bound = None
    elif minimum < singular_floor or angle < angle_floor:
        status = ValidationStatus.ABSTAIN_WEAK_IDENTIFICATION
        bound = radius / minimum
    else:
        status = ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
        bound = radius / minimum
    return WeakIdentificationReport(
        status=status,
        supported_rank=rank,
        parameter_dimension=parameter_dimension,
        singular_values=tuple(float(value) for value in singular_values),
        minimum_singular_value=minimum,
        singular_value_floor=singular_floor,
        principal_angle_radians=angle,
        principal_angle_floor_radians=angle_floor,
        perturbation_radius=radius,
        worst_case_parameter_error_bound=bound,
        covariance_id=actual_id,
    )


@dataclass(frozen=True)
class CompositionIdentifiabilityReport:
    status: ValidationStatus
    orbit_rank: int
    response_rank: int
    composition_rank: int
    parameter_dimension: int
    registered_linear_cell_only: bool
    global_orbit_separation_claimed: bool = False
    claim_ceiling: str = CLAIM_CEILING

    @property
    def report_id(self) -> str:
        return _payload_sha256(self.__dict__)


def evaluate_registered_composition(
    orbit_jacobian: Sequence[Sequence[object]],
    supported_response: Sequence[Sequence[object]],
    *,
    rank_tolerance: float,
    registered_linear_cell_only: bool,
) -> CompositionIdentifiabilityReport:
    orbit = _matrix(orbit_jacobian, "orbit_jacobian")
    response = _matrix(supported_response, "supported_response")
    if response.shape[1] != orbit.shape[0]:
        raise PillarSInferenceError(
            "supported response domain must match orbit-chart codomain"
        )
    if registered_linear_cell_only is not True:
        raise PillarSInferenceError(
            "composition validation is restricted to a registered linear cell"
        )
    tolerance = _real(rank_tolerance, "rank_tolerance")
    if tolerance <= 0.0:
        raise PillarSInferenceError("rank_tolerance must be positive")
    dimension = orbit.shape[1]
    orbit_rank = int(np.linalg.matrix_rank(orbit, tol=tolerance))
    response_rank = int(np.linalg.matrix_rank(response, tol=tolerance))
    composition_rank = int(
        np.linalg.matrix_rank(response @ orbit, tol=tolerance)
    )
    status = (
        ValidationStatus.VALIDATED_REGISTERED_LINEAR_CELL
        if orbit_rank == dimension and composition_rank == dimension
        else ValidationStatus.ABSTAIN_NON_IDENTIFIED
    )
    return CompositionIdentifiabilityReport(
        status=status,
        orbit_rank=orbit_rank,
        response_rank=response_rank,
        composition_rank=composition_rank,
        parameter_dimension=dimension,
        registered_linear_cell_only=True,
    )


@dataclass(frozen=True)
class MatchedCounterpairReport:
    status: ValidationStatus
    critical_value: float
    null_rejection_rate: float
    alternative_power: float
    alternative_power_lower_bound: float
    minimum_power_lower_bound: float
    scalar_coordinates_matched: bool
    anchor_coordinates_matched: bool
    evaluation_count: int
    claim_ceiling: str = CLAIM_CEILING

    @property
    def report_id(self) -> str:
        return _payload_sha256(self.__dict__)


def evaluate_matched_counterpair_power(
    calibration_null_features: Sequence[Sequence[object]],
    evaluation_null_features: Sequence[Sequence[object]],
    alternative_features: Sequence[Sequence[object]],
    *,
    scalar_differences: Sequence[object],
    anchor_differences: Sequence[object],
    alpha: float,
    family_confidence: float,
    minimum_power_lower_bound: float,
) -> MatchedCounterpairReport:
    calibration = _matrix(
        calibration_null_features, "calibration_null_features"
    )
    evaluation = _matrix(evaluation_null_features, "evaluation_null_features")
    alternative = _matrix(alternative_features, "alternative_features")
    if (
        calibration.shape[1] != evaluation.shape[1]
        or alternative.shape != evaluation.shape
    ):
        raise PillarSInferenceError(
            "counterpair feature dimensions and evaluation counts must match"
        )
    scalar = _vector(scalar_differences, "scalar_differences")
    anchor = _vector(anchor_differences, "anchor_differences")
    if len(scalar) != len(alternative) or len(anchor) != len(alternative):
        raise PillarSInferenceError(
            "counterpair scalar/anchor rows must match feature rows"
        )
    scalar_matched = bool(np.array_equal(scalar, np.zeros_like(scalar)))
    anchor_matched = bool(np.array_equal(anchor, np.zeros_like(anchor)))
    if not scalar_matched or not anchor_matched:
        raise PillarSInferenceError(
            "matched counterpair requires exactly equal scalar and anchor cells"
        )
    alpha_value = _probability(alpha, "alpha", open_zero=True)
    confidence = _probability(
        family_confidence, "family_confidence", open_zero=True
    )
    minimum = _probability(
        minimum_power_lower_bound, "minimum_power_lower_bound"
    )
    calibration_scores = np.linalg.norm(calibration, axis=1)
    null_scores = np.linalg.norm(evaluation, axis=1)
    alternative_scores = np.linalg.norm(alternative, axis=1)
    order = int(
        math.ceil((len(calibration_scores) + 1) * (1.0 - alpha_value))
    )
    if order > len(calibration_scores):
        raise PillarSInferenceError(
            "counterpair calibration sample is too small"
        )
    critical = float(
        np.partition(calibration_scores, order - 1)[order - 1]
    )
    null_rejections = int(np.count_nonzero(null_scores > critical))
    alternative_rejections = int(
        np.count_nonzero(alternative_scores > critical)
    )
    power = alternative_rejections / len(alternative_scores)
    power_lower = _cp_lower(
        alternative_rejections, len(alternative_scores), confidence
    )
    status = (
        ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
        if power_lower >= minimum
        else ValidationStatus.FAILED_REGISTERED_COVERAGE
    )
    return MatchedCounterpairReport(
        status=status,
        critical_value=critical,
        null_rejection_rate=null_rejections / len(null_scores),
        alternative_power=power,
        alternative_power_lower_bound=power_lower,
        minimum_power_lower_bound=minimum,
        scalar_coordinates_matched=True,
        anchor_coordinates_matched=True,
        evaluation_count=len(alternative_scores),
    )


@dataclass(frozen=True)
class OpenSetValidationReport:
    status: ValidationStatus
    distance_threshold: float
    known_correct_count: int
    known_total: int
    known_coverage: float
    known_coverage_lower_bound: float
    unknown_abstained_count: int
    unknown_total: int
    unknown_abstention_rate: float
    unknown_abstention_lower_bound: float
    reduced_library_known_coverage: float
    finite_library_sensitivity: float
    thresholds_frozen_before_evaluation: bool
    claim_ceiling: str = CLAIM_CEILING

    @property
    def report_id(self) -> str:
        return _payload_sha256(self.__dict__)


def _nearest_centres(
    values: np.ndarray, centres: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    squared = np.sum((values[:, None, :] - centres[None, :, :]) ** 2, axis=2)
    labels = np.argmin(squared, axis=1)
    distances = np.sqrt(np.min(squared, axis=1))
    return labels, distances


def evaluate_open_set_validation(
    calibration_known: Sequence[Sequence[object]],
    calibration_truth: Sequence[int],
    evaluation_known: Sequence[Sequence[object]],
    evaluation_truth: Sequence[int],
    evaluation_unknown: Sequence[Sequence[object]],
    *,
    known_centres: Sequence[Sequence[object]],
    alpha: float,
    family_confidence: float,
    minimum_known_coverage_lower_bound: float,
    minimum_unknown_abstention_lower_bound: float,
    thresholds_frozen_before_evaluation: bool,
) -> OpenSetValidationReport:
    if thresholds_frozen_before_evaluation is not True:
        raise PillarSInferenceError(
            "open-set threshold must freeze before evaluation"
        )
    centres = _matrix(known_centres, "known_centres")
    calibration = _matrix(calibration_known, "calibration_known")
    known = _matrix(evaluation_known, "evaluation_known")
    unknown = _matrix(evaluation_unknown, "evaluation_unknown")
    if not (
        calibration.shape[1] == known.shape[1] == unknown.shape[1]
        == centres.shape[1]
    ):
        raise PillarSInferenceError("open-set feature dimensions must match")
    raw_calibration_labels = tuple(calibration_truth)
    raw_known_labels = tuple(evaluation_truth)
    if any(
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, Integral)
        for value in (*raw_calibration_labels, *raw_known_labels)
    ):
        raise PillarSInferenceError(
            "open-set truth labels must be exact integers"
        )
    calibration_labels = np.asarray(raw_calibration_labels, dtype=int)
    known_labels = np.asarray(raw_known_labels, dtype=int)
    if calibration_labels.shape != (len(calibration),) or known_labels.shape != (
        len(known),
    ):
        raise PillarSInferenceError("open-set truth labels must match rows")
    if (
        np.any(calibration_labels < 0)
        or np.any(calibration_labels >= len(centres))
        or np.any(known_labels < 0)
        or np.any(known_labels >= len(centres))
    ):
        raise PillarSInferenceError("open-set truth label is out of range")
    alpha_value = _probability(alpha, "alpha", open_zero=True)
    confidence = _probability(
        family_confidence, "family_confidence", open_zero=True
    )
    minimum_known = _probability(
        minimum_known_coverage_lower_bound,
        "minimum_known_coverage_lower_bound",
    )
    minimum_unknown = _probability(
        minimum_unknown_abstention_lower_bound,
        "minimum_unknown_abstention_lower_bound",
    )
    calibration_distances = np.linalg.norm(
        calibration - centres[calibration_labels], axis=1
    )
    order = int(
        math.ceil((len(calibration_distances) + 1) * (1.0 - alpha_value))
    )
    if order > len(calibration_distances):
        raise PillarSInferenceError("open-set calibration sample is too small")
    threshold = float(
        np.partition(calibration_distances, order - 1)[order - 1]
    )
    predicted, known_distances = _nearest_centres(known, centres)
    known_correct = int(
        np.count_nonzero(
            (predicted == known_labels) & (known_distances <= threshold)
        )
    )
    _, unknown_distances = _nearest_centres(unknown, centres)
    unknown_abstained = int(np.count_nonzero(unknown_distances > threshold))
    known_lower = _cp_lower(known_correct, len(known), confidence)
    unknown_lower = _cp_lower(
        unknown_abstained, len(unknown), confidence
    )
    if len(centres) < 2:
        raise PillarSInferenceError(
            "finite-library sensitivity requires at least two known classes"
        )
    reduced_centres = centres[:-1]
    reduced_predicted, reduced_distances = _nearest_centres(
        known, reduced_centres
    )
    reduced_correct = int(
        np.count_nonzero(
            (known_labels < len(reduced_centres))
            & (reduced_predicted == known_labels)
            & (reduced_distances <= threshold)
        )
    )
    known_coverage = known_correct / len(known)
    reduced_coverage = reduced_correct / len(known)
    status = (
        ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
        if known_lower >= minimum_known and unknown_lower >= minimum_unknown
        else ValidationStatus.FAILED_REGISTERED_COVERAGE
    )
    return OpenSetValidationReport(
        status=status,
        distance_threshold=threshold,
        known_correct_count=known_correct,
        known_total=len(known),
        known_coverage=known_coverage,
        known_coverage_lower_bound=known_lower,
        unknown_abstained_count=unknown_abstained,
        unknown_total=len(unknown),
        unknown_abstention_rate=unknown_abstained / len(unknown),
        unknown_abstention_lower_bound=unknown_lower,
        reduced_library_known_coverage=reduced_coverage,
        finite_library_sensitivity=known_coverage - reduced_coverage,
        thresholds_frozen_before_evaluation=True,
    )


@dataclass(frozen=True)
class HttDepthDiscriminationReport:
    status: ValidationStatus
    selected_candidate: ModelCandidate
    local_chi_square: float
    global_chi_square: float
    chi_square_difference_global_minus_local: float
    local_amplitude: float
    global_amplitude: float
    covariance_id: str
    covariance_sha256: str
    mask_path_id: str
    transfer_source: str
    likelihood_owner: str = "HTT"
    claim_ceiling: str = CLAIM_CEILING

    @property
    def report_id(self) -> str:
        return _payload_sha256(self.__dict__)


@dataclass(frozen=True)
class MioDepthDiagnosticCrossCheck:
    status: ValidationStatus
    local_residual_norm: float
    global_residual_norm: float
    residual_norm_difference_global_minus_local: float
    mask_path_id: str
    owner: str = "MIO"
    likelihood_present: bool = False
    posterior_present: bool = False
    evidence_present: bool = False
    claim_ceiling: str = CLAIM_CEILING

    @property
    def report_id(self) -> str:
        return _payload_sha256(self.__dict__)


def _gls_fit(
    data: np.ndarray, design: np.ndarray, covariance: np.ndarray
) -> tuple[float, float, np.ndarray]:
    inverse_data = np.linalg.solve(covariance, data)
    inverse_design = np.linalg.solve(covariance, design)
    information = float(design @ inverse_design)
    if information <= 0.0:
        raise PillarSInferenceError("GLS design information must be positive")
    amplitude = float(design @ inverse_data) / information
    residual = data - amplitude * design
    chi_square = float(residual @ np.linalg.solve(covariance, residual))
    return amplitude, chi_square, residual


def evaluate_depth_local_global(
    data: Sequence[object],
    *,
    covariance: Sequence[Sequence[object]],
    covariance_id: str,
    local_design: Sequence[object],
    global_design: Sequence[object],
    mask_path_id: str,
    transfer_source: str,
    indifference_tolerance: float = 1.0e-12,
    principal_angle_floor_radians: float = 1.0e-12,
) -> HttDepthDiscriminationReport:
    values = _vector(data, "data")
    covariance_matrix = _positive_definite(
        covariance, "covariance", size=len(values)
    )
    local = _vector(local_design, "local_design")
    global_ = _vector(global_design, "global_design")
    if local.shape != values.shape or global_.shape != values.shape:
        raise PillarSInferenceError(
            "local/global designs must match the depth path"
        )
    angle_floor = _real(
        principal_angle_floor_radians, "principal_angle_floor_radians"
    )
    if angle_floor < 0.0 or angle_floor >= math.pi / 2.0:
        raise PillarSInferenceError(
            "principal_angle_floor_radians must lie in [0, pi/2)"
        )
    whitening = np.linalg.inv(np.linalg.cholesky(covariance_matrix))
    whitened_local = whitening @ local
    whitened_global = whitening @ global_
    cosine = abs(float(whitened_local @ whitened_global)) / (
        float(np.linalg.norm(whitened_local))
        * float(np.linalg.norm(whitened_global))
    )
    principal_angle = math.acos(min(1.0, max(0.0, cosine)))
    design_rank = int(
        np.linalg.matrix_rank(np.column_stack((local, global_)))
    )
    local_amplitude, local_chi2, _ = _gls_fit(
        values, local, covariance_matrix
    )
    global_amplitude, global_chi2, _ = _gls_fit(
        values, global_, covariance_matrix
    )
    difference = global_chi2 - local_chi2
    tolerance = _real(indifference_tolerance, "indifference_tolerance")
    if tolerance < 0.0:
        raise PillarSInferenceError(
            "indifference_tolerance must be nonnegative"
        )
    if design_rank < 2 or principal_angle <= angle_floor:
        selected = ModelCandidate.INDETERMINATE
        status = ValidationStatus.ABSTAIN_NON_IDENTIFIED
    elif difference > tolerance:
        selected = ModelCandidate.LOCAL
        status = ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    elif difference < -tolerance:
        selected = ModelCandidate.GLOBAL
        status = ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    else:
        selected = ModelCandidate.INDETERMINATE
        status = ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    return HttDepthDiscriminationReport(
        status=status,
        selected_candidate=selected,
        local_chi_square=local_chi2,
        global_chi_square=global_chi2,
        chi_square_difference_global_minus_local=difference,
        local_amplitude=local_amplitude,
        global_amplitude=global_amplitude,
        covariance_id=_text(covariance_id, "covariance_id"),
        covariance_sha256=_payload_sha256(covariance_matrix.tolist()),
        mask_path_id=_text(mask_path_id, "mask_path_id"),
        transfer_source=_text(transfer_source, "transfer_source"),
    )


def build_mio_depth_cross_check(
    data: Sequence[object],
    *,
    local_design: Sequence[object],
    global_design: Sequence[object],
    mask_path_id: str,
) -> MioDepthDiagnosticCrossCheck:
    """Build a Euclidean residual diagnostic with no inference semantics."""

    values = _vector(data, "data")
    local = _vector(local_design, "local_design")
    global_ = _vector(global_design, "global_design")
    if local.shape != values.shape or global_.shape != values.shape:
        raise PillarSInferenceError(
            "MIO diagnostic designs must match the depth path"
        )
    local_scale = float(local @ local)
    global_scale = float(global_ @ global_)
    if min(local_scale, global_scale) <= 0.0:
        raise PillarSInferenceError("MIO diagnostic design must be nonzero")
    local_residual = values - (float(local @ values) / local_scale) * local
    global_residual = (
        values - (float(global_ @ values) / global_scale) * global_
    )
    local_norm = float(np.linalg.norm(local_residual))
    global_norm = float(np.linalg.norm(global_residual))
    return MioDepthDiagnosticCrossCheck(
        status=ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC,
        local_residual_norm=local_norm,
        global_residual_norm=global_norm,
        residual_norm_difference_global_minus_local=(
            global_norm - local_norm
        ),
        mask_path_id=_text(mask_path_id, "mask_path_id"),
    )


@dataclass(frozen=True)
class StatisticalValidationRecord:
    theorem_id: str
    source_disposition: SourceDisposition
    validation_status: ValidationStatus
    evidence_grade: str
    evidence_path: str
    assumptions: tuple[str, ...]
    counterexample_boundaries: tuple[str, ...]
    claim_ceiling: str


@dataclass(frozen=True)
class PillarSInferenceRegistry:
    schema: str
    preregistration_sha256: str
    records: tuple[StatisticalValidationRecord, ...]
    raw_count_publication: str
    observed_data_used: bool
    source_status_promoted: bool
    claim_ceiling: str

    def __post_init__(self) -> None:
        if {row.theorem_id for row in self.records} != EXPECTED_VT_IDS:
            raise PillarSInferenceError(
                "PR-272 registry must contain the exact nine VT-S rows"
            )
        if len(self.records) != len(EXPECTED_VT_IDS):
            raise PillarSInferenceError(
                "PR-272 registry theorem ids must be unique"
            )
        if self.preregistration_sha256 != EXPECTED_SPEC_SHA256:
            raise PillarSInferenceError(
                "PR-272 registry preregistration identity drifted"
            )
        if self.raw_count_publication != "FORBIDDEN":
            raise PillarSInferenceError(
                "raw validation rows are not a theorem proof count"
            )
        if self.observed_data_used or self.source_status_promoted:
            raise PillarSInferenceError(
                "synthetic validation cannot use data or promote source status"
            )
        if self.claim_ceiling != CLAIM_CEILING:
            raise PillarSInferenceError("registry claim ceiling drifted")
        for row in self.records:
            if row.evidence_grade != "SIMULATION_DIAGNOSTIC":
                raise PillarSInferenceError(
                    "PR-272 records must retain simulation-diagnostic grade"
                )
            if row.claim_ceiling != CLAIM_CEILING:
                raise PillarSInferenceError("record claim ceiling drifted")
            if not row.assumptions or not row.counterexample_boundaries:
                raise PillarSInferenceError(
                    "every PR-272 record needs assumptions and boundaries"
                )

    def record(self, theorem_id: str) -> StatisticalValidationRecord:
        target = _text(theorem_id, "theorem_id")
        for row in self.records:
            if row.theorem_id == target:
                return row
        raise KeyError(target)

    def reject_raw_proof_count(self, value: object) -> None:
        raise PillarSInferenceError(
            f"{value!r} is a validation-row count, not an accepted proof count"
        )


def load_pillar_s_inference_registry(
    repo_root: Path,
    path: Path | None = None,
) -> PillarSInferenceRegistry:
    registry_path = path or (repo_root / REGISTRY_PATH)
    raw = registry_path.read_bytes()
    actual_registry_sha256 = _sha256_bytes(raw)
    if actual_registry_sha256 != EXPECTED_REGISTRY_SHA256:
        raise PillarSInferenceError(
            "PR-272 validation registry bytes drifted: "
            f"{actual_registry_sha256}"
        )
    payload = yaml.safe_load(raw.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise PillarSInferenceError("PR-272 registry must be a mapping")
    design = load_preregistered_design(repo_root)
    stream_spec = design["preregistration"]["random_stream"]
    stream_receipt = payload.get("random_stream_receipt")
    if not isinstance(stream_receipt, Mapping):
        raise PillarSInferenceError(
            "PR-272 random-stream receipt must be a mapping"
        )
    derived_streams = stream_receipt.get("derived_streams")
    if not isinstance(derived_streams, Mapping) or not derived_streams:
        raise PillarSInferenceError(
            "PR-272 derived random streams must be recorded"
        )
    if (
        stream_receipt.get("engine") != stream_spec["engine"]
        or stream_receipt.get("derivation") != stream_spec["derivation"]
        or stream_receipt.get("master_seed") != stream_spec["master_seed"]
        or stream_receipt.get("registered_seed_family")
        != stream_spec["seed_family"]
        or stream_receipt.get("derived_streams_sha256")
        != _payload_sha256(derived_streams)
    ):
        raise PillarSInferenceError("PR-272 random-stream receipt drifted")
    records_payload = payload.get("records")
    if not isinstance(records_payload, list):
        raise PillarSInferenceError("PR-272 registry records must be a list")
    canonical = _payload_sha256(records_payload)
    if payload.get("canonical_records_sha256") != canonical:
        raise PillarSInferenceError("PR-272 registry record seal mismatch")
    validation_results = payload.get("validation_results")
    if not isinstance(validation_results, Mapping):
        raise PillarSInferenceError(
            "PR-272 validation results must be a mapping"
        )
    if payload.get("validation_results_sha256") != _payload_sha256(
        validation_results
    ):
        raise PillarSInferenceError("PR-272 validation-result seal mismatch")
    if type(payload.get("observed_data_used")) is not bool or type(
        payload.get("source_status_promoted")
    ) is not bool:
        raise PillarSInferenceError(
            "PR-272 data-use and source-promotion flags must be booleans"
        )
    expected_statuses = {
        "VT-S3": validation_results["VT-S3"]["correct"]["status"],
        "VT-S5": validation_results["VT-S5"]["status"],
        "VT-S6": validation_results["VT-S6"]["coverage"]["status"],
        "VT-S9": validation_results["VT-S9"]["report"]["status"],
        "VT-S10": ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC.value,
        "VT-S11": validation_results["VT-S11"]["registered_cell"]["status"],
        "VT-S12": validation_results["VT-S12"]["status"],
        "VT-S13": validation_results["VT-S13"]["status"],
        "VT-S14": validation_results["VT-S14"]["status"],
    }
    required_negative_controls = (
        validation_results["VT-S3"].get(
            "misspecified_failure_preserved"
        )
        is True
        and bool(
            validation_results["VT-S5"].get("adversarial_failure_map")
        )
        and validation_results["VT-S6"].get("marginal_only_mutation")
        == "REFUSED"
        and validation_results["VT-S9"].get(
            "unadjusted_failure_preserved"
        )
        is True
        and validation_results["VT-S10"]["weak"]["status"]
        == ValidationStatus.ABSTAIN_WEAK_IDENTIFICATION.value
        and validation_results["VT-S11"]["rank_loss"]["status"]
        == ValidationStatus.ABSTAIN_NON_IDENTIFIED.value
        and validation_results["SBC-HTT-COMPUTATION"].get(
            "all_misspecified_fail"
        )
        is True
    )
    if not required_negative_controls:
        raise PillarSInferenceError(
            "PR-272 required negative-control evidence is incomplete"
        )
    records = []
    for item in records_payload:
        if not isinstance(item, Mapping):
            raise PillarSInferenceError("PR-272 registry row must be a mapping")
        try:
            source_disposition = SourceDisposition(
                str(item["source_disposition"])
            )
            validation_status = ValidationStatus(
                str(item["validation_status"])
            )
        except (KeyError, ValueError) as exc:
            raise PillarSInferenceError(
                "PR-272 registry vocabulary is invalid"
            ) from exc
        records.append(
            StatisticalValidationRecord(
                theorem_id=_text(item.get("theorem_id"), "theorem_id"),
                source_disposition=source_disposition,
                validation_status=validation_status,
                evidence_grade=_text(
                    item.get("evidence_grade"), "evidence_grade"
                ),
                evidence_path=_text(item.get("evidence_path"), "evidence_path"),
                assumptions=tuple(
                    _text(value, "assumption")
                    for value in item.get("assumptions", ())
                ),
                counterexample_boundaries=tuple(
                    _text(value, "counterexample_boundary")
                    for value in item.get("counterexample_boundaries", ())
                ),
                claim_ceiling=_text(
                    item.get("claim_ceiling"), "claim_ceiling"
                ),
            )
        )
    for record in records:
        if record.validation_status.value != expected_statuses[record.theorem_id]:
            raise PillarSInferenceError(
                f"{record.theorem_id} record/result status mismatch"
            )
        expected_disposition = (
            SourceDisposition.PROGRAM_OBLIGATION_RETAINED
            if record.theorem_id == "VT-S14"
            else SourceDisposition.CONDITIONAL_PROGRAM_RETAINED
        )
        if record.source_disposition is not expected_disposition:
            raise PillarSInferenceError(
                f"{record.theorem_id} source disposition drifted"
            )
    return PillarSInferenceRegistry(
        schema=_text(payload.get("schema"), "schema"),
        preregistration_sha256=_text(
            payload.get("preregistration_sha256"),
            "preregistration_sha256",
        ),
        records=tuple(records),
        raw_count_publication=_text(
            payload.get("raw_count_publication"),
            "raw_count_publication",
        ),
        observed_data_used=bool(payload.get("observed_data_used")),
        source_status_promoted=bool(payload.get("source_status_promoted")),
        claim_ceiling=_text(payload.get("claim_ceiling"), "claim_ceiling"),
    )
