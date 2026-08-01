"""Sealed contracts for PR-273 blind synthetic integration.

The analyst receives only a :class:`BlindSyntheticChallenge`.  Scenario
labels and expected outcomes live in a separate truth-vault payload and enter
only after a sealed :class:`BlindSyntheticSubmission` exists.  These
contracts enforce process separation; they do not turn synthetic diagnostics
into observed-data, geometry, or family-identification claims.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
import hashlib
import json
import math
from numbers import Integral, Real
from typing import Mapping, Sequence


class BlindSyntheticContractError(ValueError):
    """Raised when a blind-integration envelope fails closed."""


BLIND_SYNTHETIC_CLAIM_CEILING = "diagnostic_only"
BLIND_SYNTHETIC_TRANSFER_SOURCE = "none"
BLIND_SYNTHETIC_ALLOWED_USE = (
    "synthetic state-to-report integration diagnostic",
    "held-out abstention and mutation testing",
)
BLIND_SYNTHETIC_FORBIDDEN_USE = (
    "observed-data inference",
    "native solver or native morphology-atlas validation",
    "geometry detection",
    "Bianchi family identification or ranking",
    "MIO likelihood, posterior, Bayes factor, or evidence",
)
CHALLENGE_SCHEMA = "htt.pr273.blind_synthetic_challenge.v1"
BLIND_SYNTHETIC_CHALLENGE_ID = "PR273-BLIND-SYNTHETIC-V1"
SUBMISSION_SCHEMA = "htt.pr273.blind_synthetic_submission.v1"
ADJUDICATION_SCHEMA = "htt.pr273.blind_synthetic_adjudication.v1"
TRUTH_VAULT_SCHEMA = "htt.pr273.blind_synthetic_truth_vault.v1"

_CHALLENGE_TOKEN = object()
_SUBMISSION_TOKEN = object()
_ADJUDICATION_TOKEN = object()
_TRUTH_FIELD_TOKENS = frozenset(
    {
        "label",
        "truth",
        "truth_parameters",
        "truth_label",
        "scenario",
        "expected",
        "expected_outcome",
        "expected_status",
        "reviewer_verdict",
    }
)
_CASE_KEYS = frozenset({"case_id", "state", "responses", "depth"})
_STATE_KEYS = frozenset(
    {
        "sigma_stf5",
        "omega_axial3",
        "acceleration_polar3",
        "beta_rm",
        "beta_mo",
        "geometry_stf5",
    }
)
_RESPONSE_KEYS = frozenset({"local", "global", "observation"})
_DEPTH_KEYS = frozenset({"support", "features", "covariance_scale"})
_REQUIRED_CASE_IDS = ("C01", "C02", "C03", "C04", "C05")
_REQUIRED_PARTITIONS = (
    ("development", ("C01", "C02", "C03")),
    ("held_out", ("C04", "C05")),
)
_PARTITION_BY_CASE = {
    case_id: partition
    for partition, case_ids in _REQUIRED_PARTITIONS
    for case_id in case_ids
}
_SUBMISSION_PAYLOAD_KEYS = frozenset(
    {
        "schema",
        "submission_id",
        "analyzer_id",
        "challenge_id",
        "challenge_content_id",
        "truth_accessed",
        "observed_data",
        "claim_ceiling",
        "case_results",
        "content_id",
    }
)
_TRUTH_VAULT_KEYS = frozenset(
    {
        "schema",
        "vault_id",
        "challenge_id",
        "unblind_stage",
        "observed_data",
        "expected_cases",
    }
)
_TRUTH_CASE_KEYS = frozenset(
    {
        "case_id",
        "scenario",
        "expected_geometry_status",
        "expected_local_global_status",
        "expected_depth_alert",
        "expected_missing_functional",
    }
)
_TRUTH_VAULT_ID = "PR273-TRUTH-VAULT-V1"
_TRUTH_UNBLIND_STAGE = "REGISTERED_POST_SUBMISSION_ADJUDICATION_ONLY"
_REQUIRED_MUTATIONS = (
    "TRUTH_FIELD_IN_CHALLENGE",
    "OBSERVED_DATA_FLAG",
    "CHALLENGE_AFTER_SUBMISSION",
    "SUBMISSION_AFTER_SEAL",
    "TRUTH_VAULT_COMMITMENT",
)
_REQUIRED_RESULT_KEYS = frozenset(
    {
        "case_id",
        "partition",
        "state_content_id",
        "functional_result_ids",
        "functional_statuses",
        "orbit_content_id",
        "orbit_stratum",
        "pushforward_content_id",
        "x_values",
        "q_values",
        "support_utilization_content_id",
        "support_utilization_status",
        "occupancy_content_id",
        "occupancy_status",
        "conditional_exceedance_content_id",
        "conditional_exceedance_status",
        "depth_path_content_id",
        "depth_coherence_content_id",
        "depth_coherence_status",
        "depth_mean_normalized_score",
        "depth_alert",
        "type_report_content_id",
        "geometry_status",
        "local_global_status",
        "compatibility_status",
        "missing_functional",
        "claim_ceiling",
        "transfer_source",
    }
)


def canonical_sha256(payload: object) -> str:
    """Return a stable content identity for one JSON-compatible value."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def file_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _parse_committed_json_mapping(raw: bytes, name: str) -> Mapping[str, object]:
    """Parse the exact committed bytes without a detached mapping authority."""

    if not isinstance(raw, bytes):
        raise BlindSyntheticContractError(f"{name} raw payload must be bytes")

    def reject_constant(value: str) -> object:
        raise BlindSyntheticContractError(
            f"{name} contains non-finite JSON constant {value}"
        )

    def reject_duplicate_keys(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise BlindSyntheticContractError(
                    f"{name} contains duplicate key {key!r}"
                )
            result[key] = value
        return result

    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BlindSyntheticContractError(
            f"{name} must be UTF-8 JSON bytes"
        ) from exc
    try:
        parsed = json.loads(
            decoded,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, TypeError) as exc:
        raise BlindSyntheticContractError(
            f"{name} must be valid JSON bytes"
        ) from exc
    if not isinstance(parsed, Mapping):
        raise BlindSyntheticContractError(f"{name} root must be a mapping")
    return parsed


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise BlindSyntheticContractError(
            f"{name} must be non-empty trimmed text"
        )
    return value


def _real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise BlindSyntheticContractError(f"{name} must be real")
    out = float(value)
    if not math.isfinite(out):
        raise BlindSyntheticContractError(f"{name} must be finite")
    return out


def _json_clone(value: object) -> object:
    try:
        return json.loads(
            json.dumps(
                value,
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise BlindSyntheticContractError(
            "payload must be finite JSON data"
        ) from exc


def _forbidden_truth_paths(
    value: object,
    *,
    path: str = "$",
) -> tuple[str, ...]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            token = str(key).lower()
            if (
                token in _TRUTH_FIELD_TOKENS
                or token.startswith("expected_")
                or any(
                    marker in token
                    for marker in (
                        "truth",
                        "scenario",
                        "label",
                        "verdict",
                    )
                )
            ):
                findings.append(f"{path}.{key}")
            findings.extend(
                _forbidden_truth_paths(child, path=f"{path}.{key}")
            )
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, child in enumerate(value):
            findings.extend(
                _forbidden_truth_paths(child, path=f"{path}[{index}]")
            )
    return tuple(findings)


def _sequence(value: object, name: str) -> tuple[object, ...]:
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, bytearray)
    ):
        raise BlindSyntheticContractError(f"{name} must be a sequence")
    return tuple(value)


def _case_ids(cases: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    ids = tuple(_text(case.get("case_id"), "case_id") for case in cases)
    if not ids or len(ids) != len(set(ids)):
        raise BlindSyntheticContractError(
            "challenge case IDs must be non-empty and unique"
        )
    return ids


def _exact_mapping(
    value: object,
    *,
    name: str,
    expected_keys: frozenset[str],
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise BlindSyntheticContractError(f"{name} must be a mapping")
    actual = set(value)
    if actual != expected_keys:
        raise BlindSyntheticContractError(
            f"{name} fields drifted; "
            f"missing={sorted(expected_keys - actual)}, "
            f"extra={sorted(actual - expected_keys)}"
        )
    return value


def _validate_case_payload(case: Mapping[str, object]) -> None:
    checked = _exact_mapping(
        case,
        name="case",
        expected_keys=_CASE_KEYS,
    )
    _text(checked["case_id"], "case_id")
    _exact_mapping(
        checked["state"],
        name="case.state",
        expected_keys=_STATE_KEYS,
    )
    _exact_mapping(
        checked["responses"],
        name="case.responses",
        expected_keys=_RESPONSE_KEYS,
    )
    _exact_mapping(
        checked["depth"],
        name="case.depth",
        expected_keys=_DEPTH_KEYS,
    )


@dataclass(frozen=True)
class BlindSyntheticChallenge:
    challenge_id: str
    seed: int
    partitions: tuple[tuple[str, tuple[str, ...]], ...]
    functional_scales: tuple[float, ...]
    null_draws: tuple[float, ...]
    declared_mutations: tuple[str, ...]
    cases: tuple[dict[str, object], ...]
    transfer_source: str = BLIND_SYNTHETIC_TRANSFER_SOURCE
    claim_ceiling: str = BLIND_SYNTHETIC_CLAIM_CEILING
    observed_data: bool = False
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CHALLENGE_TOKEN:
            raise BlindSyntheticContractError(
                "BlindSyntheticChallenge must be factory-built"
            )
        _text(self.challenge_id, "challenge_id")
        if self.challenge_id != BLIND_SYNTHETIC_CHALLENGE_ID:
            raise BlindSyntheticContractError(
                "challenge ID must remain the registered opaque identity"
            )
        if (
            isinstance(self.seed, bool)
            or not isinstance(self.seed, Integral)
            or self.seed < 0
        ):
            raise BlindSyntheticContractError(
                "seed must be a non-negative integer"
            )
        if self.transfer_source != BLIND_SYNTHETIC_TRANSFER_SOURCE:
            raise BlindSyntheticContractError(
                "blind synthetic transfer source must remain none"
            )
        if self.claim_ceiling != BLIND_SYNTHETIC_CLAIM_CEILING:
            raise BlindSyntheticContractError("claim ceiling drifted")
        if self.observed_data is not False:
            raise BlindSyntheticContractError(
                "blind synthetic challenge must not contain observed data"
            )
        cases = tuple(dict(case) for case in self.cases)
        for case in cases:
            _validate_case_payload(case)
        case_ids = _case_ids(cases)
        if case_ids != _REQUIRED_CASE_IDS:
            raise BlindSyntheticContractError(
                "challenge case IDs must match the exact registered opaque inventory"
            )
        partitions = tuple(
            (
                _text(name, "partition"),
                tuple(_text(value, "partition case ID") for value in values),
            )
            for name, values in self.partitions
        )
        if partitions != _REQUIRED_PARTITIONS:
            raise BlindSyntheticContractError(
                "partitions must match the exact registered opaque partition"
            )
        flat = tuple(
            case_id for _, values in partitions for case_id in values
        )
        if (
            set(flat) != set(case_ids)
            or len(flat) != len(set(flat))
            or not dict(partitions)["held_out"]
        ):
            raise BlindSyntheticContractError(
                "partitions must cover each case exactly once and include held-out cases"
            )
        scales = tuple(
            _real(value, "functional_scales") for value in self.functional_scales
        )
        if not scales or any(value <= 0.0 for value in scales):
            raise BlindSyntheticContractError(
                "functional scales must be positive"
            )
        null_draws = tuple(_real(value, "null_draws") for value in self.null_draws)
        if len(null_draws) < 2:
            raise BlindSyntheticContractError(
                "at least two matched-null draws are required"
            )
        if tuple(self.declared_mutations) != _REQUIRED_MUTATIONS:
            raise BlindSyntheticContractError(
                "declared mutation inventory drifted"
            )
        truth_paths = _forbidden_truth_paths(cases)
        if truth_paths:
            raise BlindSyntheticContractError(
                "challenge contains forbidden truth fields: "
                + ", ".join(truth_paths)
            )
        object.__setattr__(self, "cases", cases)
        object.__setattr__(self, "partitions", partitions)
        object.__setattr__(self, "functional_scales", scales)
        object.__setattr__(self, "null_draws", null_draws)
        object.__setattr__(
            self,
            "_identity_seal",
            canonical_sha256(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_sealed()
        return self._identity_seal

    @property
    def case_ids(self) -> tuple[str, ...]:
        self._assert_sealed()
        return tuple(str(case["case_id"]) for case in self.cases)

    def partition_for(self, case_id: str) -> str:
        self._assert_sealed()
        for name, values in self.partitions:
            if case_id in values:
                return name
        raise BlindSyntheticContractError("case is absent from partitions")

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "schema": CHALLENGE_SCHEMA,
            "challenge_id": self.challenge_id,
            "seed": int(self.seed),
            "transfer_source": self.transfer_source,
            "claim_ceiling": self.claim_ceiling,
            "observed_data": self.observed_data,
            "partitions": {
                name: list(values) for name, values in self.partitions
            },
            "functional_scales": list(self.functional_scales),
            "null_draws": list(self.null_draws),
            "declared_mutations": list(self.declared_mutations),
            "cases": _json_clone(self.cases),
        }

    def _assert_sealed(self) -> None:
        if canonical_sha256(self._payload_unchecked()) != self._identity_seal:
            raise BlindSyntheticContractError(
                "challenge identity drifted after construction"
            )

    def as_payload(self) -> dict[str, object]:
        self._assert_sealed()
        return {**self._payload_unchecked(), "content_id": self.content_id}


def build_blind_synthetic_challenge(
    payload: Mapping[str, object],
) -> BlindSyntheticChallenge:
    if not isinstance(payload, Mapping):
        raise BlindSyntheticContractError("challenge must be a mapping")
    if payload.get("schema") != CHALLENGE_SCHEMA:
        raise BlindSyntheticContractError("challenge schema drifted")
    allowed_keys = {
        "schema",
        "challenge_id",
        "seed",
        "transfer_source",
        "claim_ceiling",
        "observed_data",
        "partitions",
        "functional_scales",
        "null_draws",
        "declared_mutations",
        "cases",
        "content_id",
    }
    if set(payload) - allowed_keys:
        raise BlindSyntheticContractError(
            "challenge contains unregistered fields: "
            + ", ".join(sorted(set(payload) - allowed_keys))
        )
    truth_paths = _forbidden_truth_paths(payload)
    if truth_paths:
        raise BlindSyntheticContractError(
            "challenge contains forbidden truth fields: "
            + ", ".join(truth_paths)
        )
    cases = _sequence(payload.get("cases"), "cases")
    if any(not isinstance(case, Mapping) for case in cases):
        raise BlindSyntheticContractError("cases must contain mappings")
    partitions = payload.get("partitions")
    if not isinstance(partitions, Mapping):
        raise BlindSyntheticContractError("partitions must be a mapping")
    if set(partitions) != {"development", "held_out"}:
        raise BlindSyntheticContractError(
            "partition fields must match the exact registered schema"
        )
    rebuilt = BlindSyntheticChallenge(
        challenge_id=_text(payload.get("challenge_id"), "challenge_id"),
        seed=payload.get("seed"),
        partitions=tuple(
            (
                name,
                tuple(_sequence(partitions.get(name), f"partitions.{name}")),
            )
            for name in ("development", "held_out")
        ),
        functional_scales=tuple(
            _sequence(payload.get("functional_scales"), "functional_scales")
        ),
        null_draws=tuple(_sequence(payload.get("null_draws"), "null_draws")),
        declared_mutations=tuple(
            _sequence(payload.get("declared_mutations"), "declared_mutations")
        ),
        cases=tuple(dict(case) for case in cases),
        transfer_source=payload.get("transfer_source"),
        claim_ceiling=payload.get("claim_ceiling"),
        observed_data=payload.get("observed_data"),
        _construction_token=_CHALLENGE_TOKEN,
    )
    if "content_id" in payload and payload["content_id"] != rebuilt.content_id:
        raise BlindSyntheticContractError(
            "challenge content identity does not match payload"
        )
    return rebuilt


@dataclass(frozen=True)
class BlindSyntheticSubmission:
    submission_id: str
    analyzer_id: str
    challenge_id: str
    challenge_content_id: str
    case_results: tuple[dict[str, object], ...]
    truth_accessed: bool = False
    observed_data: bool = False
    claim_ceiling: str = BLIND_SYNTHETIC_CLAIM_CEILING
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SUBMISSION_TOKEN:
            raise BlindSyntheticContractError(
                "BlindSyntheticSubmission must be factory-built"
            )
        for name in (
            "submission_id",
            "analyzer_id",
            "challenge_id",
            "challenge_content_id",
        ):
            _text(getattr(self, name), name)
        if self.truth_accessed is not False:
            raise BlindSyntheticContractError(
                "blind analysis must attest that truth was not accessed"
            )
        if self.observed_data is not False:
            raise BlindSyntheticContractError(
                "blind synthetic submission must not contain observed data"
            )
        if self.claim_ceiling != BLIND_SYNTHETIC_CLAIM_CEILING:
            raise BlindSyntheticContractError("submission claim ceiling drifted")
        results = tuple(dict(value) for value in self.case_results)
        if not results:
            raise BlindSyntheticContractError(
                "submission must contain case results"
            )
        ids = _case_ids(results)
        if ids != _REQUIRED_CASE_IDS:
            raise BlindSyntheticContractError(
                "submission case IDs must match the exact challenge order"
            )
        for result in results:
            if set(result) != _REQUIRED_RESULT_KEYS:
                missing = sorted(_REQUIRED_RESULT_KEYS - set(result))
                extra = sorted(set(result) - _REQUIRED_RESULT_KEYS)
                raise BlindSyntheticContractError(
                    f"case result fields drifted; missing={missing}, extra={extra}"
                )
            if result["claim_ceiling"] != BLIND_SYNTHETIC_CLAIM_CEILING:
                raise BlindSyntheticContractError(
                    "case result claim ceiling drifted"
                )
            if result["transfer_source"] != BLIND_SYNTHETIC_TRANSFER_SOURCE:
                raise BlindSyntheticContractError(
                    "case result transfer source drifted"
                )
            if type(result["depth_alert"]) is not bool:
                raise BlindSyntheticContractError(
                    "depth_alert must be Boolean"
                )
            if type(result["missing_functional"]) is not bool:
                raise BlindSyntheticContractError(
                    "missing_functional must be Boolean"
                )
            if result["partition"] != _PARTITION_BY_CASE[result["case_id"]]:
                raise BlindSyntheticContractError(
                    "submission partition does not match the registered case"
                )
        truth_paths = _forbidden_truth_paths(results)
        if truth_paths:
            raise BlindSyntheticContractError(
                "submission contains forbidden truth fields: "
                + ", ".join(truth_paths)
            )
        object.__setattr__(self, "case_results", results)
        object.__setattr__(
            self,
            "_identity_seal",
            canonical_sha256(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "schema": SUBMISSION_SCHEMA,
            "submission_id": self.submission_id,
            "analyzer_id": self.analyzer_id,
            "challenge_id": self.challenge_id,
            "challenge_content_id": self.challenge_content_id,
            "truth_accessed": self.truth_accessed,
            "observed_data": self.observed_data,
            "claim_ceiling": self.claim_ceiling,
            "case_results": _json_clone(self.case_results),
        }

    def _assert_sealed(self) -> None:
        if canonical_sha256(self._payload_unchecked()) != self._identity_seal:
            raise BlindSyntheticContractError(
                "submission identity drifted after construction"
            )

    def as_payload(self) -> dict[str, object]:
        self._assert_sealed()
        return {**self._payload_unchecked(), "content_id": self.content_id}


def build_blind_synthetic_submission(
    *,
    submission_id: str,
    analyzer_id: str,
    challenge: BlindSyntheticChallenge,
    case_results: Sequence[Mapping[str, object]],
) -> BlindSyntheticSubmission:
    if type(challenge) is not BlindSyntheticChallenge:
        raise TypeError("challenge must be an exact BlindSyntheticChallenge")
    challenge.as_payload()
    results = tuple(dict(value) for value in case_results)
    if tuple(str(value.get("case_id")) for value in results) != challenge.case_ids:
        raise BlindSyntheticContractError(
            "submission must preserve exact challenge case order"
        )
    for result in results:
        if result.get("partition") != challenge.partition_for(
            str(result.get("case_id"))
        ):
            raise BlindSyntheticContractError(
                "submission partition does not match challenge"
            )
    return BlindSyntheticSubmission(
        submission_id=submission_id,
        analyzer_id=analyzer_id,
        challenge_id=challenge.challenge_id,
        challenge_content_id=challenge.content_id,
        case_results=results,
        _construction_token=_SUBMISSION_TOKEN,
    )


def replay_blind_synthetic_submission(
    payload: Mapping[str, object],
    *,
    expected_content_id: str,
) -> BlindSyntheticSubmission:
    _text(expected_content_id, "expected_content_id")
    if not isinstance(payload, Mapping):
        raise BlindSyntheticContractError("submission must be a mapping")
    if set(payload) != _SUBMISSION_PAYLOAD_KEYS:
        raise BlindSyntheticContractError(
            "submission envelope fields drifted; "
            f"missing={sorted(_SUBMISSION_PAYLOAD_KEYS - set(payload))}, "
            f"extra={sorted(set(payload) - _SUBMISSION_PAYLOAD_KEYS)}"
        )
    truth_paths = _forbidden_truth_paths(payload["case_results"])
    if truth_paths:
        raise BlindSyntheticContractError(
            "submission contains forbidden truth fields: "
            + ", ".join(truth_paths)
        )
    if payload.get("schema") != SUBMISSION_SCHEMA:
        raise BlindSyntheticContractError("submission schema drifted")
    results = _sequence(payload.get("case_results"), "case_results")
    if any(not isinstance(value, Mapping) for value in results):
        raise BlindSyntheticContractError(
            "case_results must contain mappings"
        )
    rebuilt = BlindSyntheticSubmission(
        submission_id=payload.get("submission_id"),
        analyzer_id=payload.get("analyzer_id"),
        challenge_id=payload.get("challenge_id"),
        challenge_content_id=payload.get("challenge_content_id"),
        case_results=tuple(dict(value) for value in results),
        truth_accessed=payload.get("truth_accessed"),
        observed_data=payload.get("observed_data"),
        claim_ceiling=payload.get("claim_ceiling"),
        _construction_token=_SUBMISSION_TOKEN,
    )
    if payload.get("content_id") != rebuilt.content_id:
        raise BlindSyntheticContractError(
            "submission content identity does not match payload"
        )
    if rebuilt.content_id != expected_content_id:
        raise BlindSyntheticContractError(
            "submission content identity does not match the frozen analysis-stage identity"
        )
    return rebuilt


@dataclass(frozen=True)
class BlindSyntheticAdjudication:
    adjudication_id: str
    challenge_content_id: str
    submission_content_id: str
    truth_vault_sha256: str
    case_verdicts: tuple[dict[str, object], ...]
    mutation_results: tuple[tuple[str, str], ...]
    status: str
    claim_ceiling: str = BLIND_SYNTHETIC_CLAIM_CEILING
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _ADJUDICATION_TOKEN:
            raise BlindSyntheticContractError(
                "BlindSyntheticAdjudication must be factory-built"
            )
        for name in (
            "adjudication_id",
            "challenge_content_id",
            "submission_content_id",
            "truth_vault_sha256",
        ):
            _text(getattr(self, name), name)
        verdicts = tuple(dict(value) for value in self.case_verdicts)
        if not verdicts:
            raise BlindSyntheticContractError(
                "adjudication requires case verdicts"
            )
        mutations = tuple(
            (_text(name, "mutation"), _text(status, "mutation status"))
            for name, status in self.mutation_results
        )
        if tuple(name for name, _ in mutations) != _REQUIRED_MUTATIONS:
            raise BlindSyntheticContractError(
                "adjudication mutation inventory drifted"
            )
        if any(status != "KILLED" for _, status in mutations):
            raise BlindSyntheticContractError(
                "every declared mutation must be killed"
            )
        expected_status = (
            "PASS"
            if all(value.get("status") == "MATCH" for value in verdicts)
            else "FAIL"
        )
        if self.status != expected_status:
            raise BlindSyntheticContractError(
                "adjudication status does not match case verdicts"
            )
        if self.claim_ceiling != BLIND_SYNTHETIC_CLAIM_CEILING:
            raise BlindSyntheticContractError(
                "adjudication claim ceiling drifted"
            )
        object.__setattr__(self, "case_verdicts", verdicts)
        object.__setattr__(self, "mutation_results", mutations)
        object.__setattr__(
            self,
            "_identity_seal",
            canonical_sha256(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "schema": ADJUDICATION_SCHEMA,
            "adjudication_id": self.adjudication_id,
            "challenge_content_id": self.challenge_content_id,
            "submission_content_id": self.submission_content_id,
            "truth_vault_sha256": self.truth_vault_sha256,
            "case_verdicts": _json_clone(self.case_verdicts),
            "mutation_results": {
                name: status for name, status in self.mutation_results
            },
            "status": self.status,
            "claim_ceiling": self.claim_ceiling,
        }

    def _assert_sealed(self) -> None:
        if canonical_sha256(self._payload_unchecked()) != self._identity_seal:
            raise BlindSyntheticContractError(
                "adjudication identity drifted after construction"
            )

    def as_payload(self) -> dict[str, object]:
        self._assert_sealed()
        return {**self._payload_unchecked(), "content_id": self.content_id}


def build_blind_synthetic_adjudication(
    *,
    adjudication_id: str,
    challenge: BlindSyntheticChallenge,
    submission: BlindSyntheticSubmission,
    truth_vault_raw: bytes,
    expected_truth_vault_sha256: str,
    expected_submission_content_id: str,
    mutation_results: Mapping[str, str],
) -> BlindSyntheticAdjudication:
    """Unblind only after replaying the frozen analyst submission."""

    if type(challenge) is not BlindSyntheticChallenge:
        raise TypeError("challenge must be exact BlindSyntheticChallenge")
    if type(submission) is not BlindSyntheticSubmission:
        raise TypeError("submission must be exact BlindSyntheticSubmission")
    challenge.as_payload()
    submission.as_payload()
    _text(expected_submission_content_id, "expected_submission_content_id")
    if submission.content_id != expected_submission_content_id:
        raise BlindSyntheticContractError(
            "submission does not match the frozen analysis-stage identity"
        )
    if submission.challenge_id != challenge.challenge_id:
        raise BlindSyntheticContractError(
            "submission challenge ID does not match"
        )
    if submission.challenge_content_id != challenge.content_id:
        raise BlindSyntheticContractError(
            "challenge changed after the analyst submission"
        )
    actual_sha = file_sha256(truth_vault_raw)
    if actual_sha != expected_truth_vault_sha256:
        raise BlindSyntheticContractError(
            "truth vault commitment does not match frozen bytes"
        )
    truth_vault = _parse_committed_json_mapping(
        truth_vault_raw,
        "truth_vault",
    )
    checked_truth = _exact_mapping(
        truth_vault,
        name="truth_vault",
        expected_keys=_TRUTH_VAULT_KEYS,
    )
    if checked_truth.get("schema") != TRUTH_VAULT_SCHEMA:
        raise BlindSyntheticContractError("truth vault schema drifted")
    if checked_truth.get("vault_id") != _TRUTH_VAULT_ID:
        raise BlindSyntheticContractError("truth vault ID drifted")
    if checked_truth.get("unblind_stage") != _TRUTH_UNBLIND_STAGE:
        raise BlindSyntheticContractError("truth vault unblind stage drifted")
    if checked_truth.get("challenge_id") != challenge.challenge_id:
        raise BlindSyntheticContractError(
            "truth vault challenge ID does not match"
        )
    if checked_truth.get("observed_data") is not False:
        raise BlindSyntheticContractError(
            "truth vault must remain synthetic"
        )
    expected_cases = _sequence(
        checked_truth.get("expected_cases"), "expected_cases"
    )
    if any(not isinstance(value, Mapping) for value in expected_cases):
        raise BlindSyntheticContractError(
            "expected_cases must contain mappings"
        )
    if tuple(value.get("case_id") for value in expected_cases) != challenge.case_ids:
        raise BlindSyntheticContractError(
            "truth vault must preserve exact challenge case order"
        )
    for expected in expected_cases:
        _exact_mapping(
            expected,
            name="truth_vault.expected_case",
            expected_keys=_TRUTH_CASE_KEYS,
        )
    actual_by_id = {
        str(value["case_id"]): value for value in submission.case_results
    }
    verdicts: list[dict[str, object]] = []
    for expected in expected_cases:
        case_id = str(expected["case_id"])
        actual = actual_by_id[case_id]
        comparisons = {
            "geometry_status": (
                actual["geometry_status"]
                == expected.get("expected_geometry_status")
            ),
            "local_global_status": (
                actual["local_global_status"]
                == expected.get("expected_local_global_status")
            ),
            "depth_alert": (
                actual["depth_alert"] == expected.get("expected_depth_alert")
            ),
            "missing_functional": (
                actual["missing_functional"]
                == expected.get("expected_missing_functional")
            ),
        }
        verdicts.append(
            {
                "case_id": case_id,
                "partition": actual["partition"],
                "scenario": _text(expected.get("scenario"), "scenario"),
                "comparisons": comparisons,
                "status": (
                    "MATCH" if all(comparisons.values()) else "MISMATCH"
                ),
            }
        )
    ordered_mutations = tuple(
        (name, mutation_results.get(name, "MISSING"))
        for name in _REQUIRED_MUTATIONS
    )
    return BlindSyntheticAdjudication(
        adjudication_id=adjudication_id,
        challenge_content_id=challenge.content_id,
        submission_content_id=submission.content_id,
        truth_vault_sha256=actual_sha,
        case_verdicts=tuple(verdicts),
        mutation_results=ordered_mutations,
        status=(
            "PASS"
            if all(value["status"] == "MATCH" for value in verdicts)
            else "FAIL"
        ),
        _construction_token=_ADJUDICATION_TOKEN,
    )


__all__ = [
    "ADJUDICATION_SCHEMA",
    "BLIND_SYNTHETIC_ALLOWED_USE",
    "BLIND_SYNTHETIC_CHALLENGE_ID",
    "BLIND_SYNTHETIC_CLAIM_CEILING",
    "BLIND_SYNTHETIC_FORBIDDEN_USE",
    "BlindSyntheticAdjudication",
    "BlindSyntheticChallenge",
    "BlindSyntheticContractError",
    "BlindSyntheticSubmission",
    "build_blind_synthetic_adjudication",
    "build_blind_synthetic_challenge",
    "build_blind_synthetic_submission",
    "canonical_sha256",
    "file_sha256",
    "replay_blind_synthetic_submission",
]
