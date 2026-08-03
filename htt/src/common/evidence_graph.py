"""Claim-addressed, content-addressed evidence graph contracts.

The graph in this module is release *mechanics* substrate.  A closed graph is
not evidence that an estimand is correct, that an oracle is independent, or
that a scientific claim is true.  In particular, process results, evidence
condition, and scientific status remain three orthogonal axes.

All node, edge, closure, and receipt identifiers are SHA-256 addresses of
canonical JSON.  Receipt attestations are verified through the existing
``AuthorityRegistry`` trust root; this module deliberately does not introduce
a second principal registry or accept caller-supplied readiness booleans.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
from importlib import metadata as importlib_metadata
import inspect
import json
import math
import platform
import re
import sys
import weakref
from dis import get_instructions
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from types import CodeType, MappingProxyType, ModuleType
from typing import Callable, Mapping, Sequence

from common.remediation_state import (
    AdjudicationReceipt,
    ArtifactReadinessAxis,
    AuthorityError,
    AuthorityRegistry,
    CapabilityAction,
    CapabilityBlocker,
    CapabilityBlockerKind,
    CapabilityEvidenceBranch,
    CapabilityIdentification,
    CapabilityOutcome,
    CapabilityProvenanceGrade,
    CapabilityScientificSemantics,
    ClaimCapability,
    IdentityDimension,
    NON_RELAXABLE_CAPABILITY_RULES,
    PrincipalRecord,
    RemediationContractError,
    ScientificStatus,
    VersionedClaimIdentity,
    _ALLOWED_OUTCOMES_BY_ACTION,
    require_independent_external_principal,
)


GRAPH_SCHEMA_VERSION = "claim_evidence_graph_v1"
RECEIPT_SCHEMA_VERSION = "claim_evidence_receipt_v2"
CANONICALIZATION = "sorted_compact_json_utf8_v1"
UTC = timezone.utc
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_PYTEST_EXCLUDED_IMPORT_ORIGINS: tuple[dict[str, object], ...] = ()


class EvidenceGraphError(ValueError):
    """Raised when evidence graph or receipt integrity fails closed."""


_RELEASE_PIN_FIELD_NAMES = frozenset(
    {
        "graph_path",
        "graph_file_sha256",
        "graph_ref",
        "receipt_path",
        "receipt_file_sha256",
        "receipt_id",
        "parent_receipt_path",
        "parent_receipt_file_sha256",
        "parent_receipt_id",
        "closure_path",
        "closure_file_sha256",
        "artifact_manifest_path",
        "artifact_manifest_file_sha256",
        "authority_registry_ref",
    }
)


def load_literal_release_pin_fields(path: Path | str) -> dict[str, str]:
    """Parse the fixed-point pin without executing its Python module body."""

    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise EvidenceGraphError("release pin source is missing or non-regular")
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise EvidenceGraphError(
            "release pin source is not valid literal Python"
        ) from exc
    if len(tree.body) != 3:
        raise EvidenceGraphError(
            "release pin source must contain exactly three literals"
        )
    docstring, fields_assignment, export_assignment = tree.body
    if not (
        isinstance(docstring, ast.Expr)
        and isinstance(docstring.value, ast.Constant)
        and isinstance(docstring.value.value, str)
    ):
        raise EvidenceGraphError("release pin source requires one literal docstring")
    if not (
        isinstance(fields_assignment, ast.Assign)
        and len(fields_assignment.targets) == 1
        and isinstance(fields_assignment.targets[0], ast.Name)
        and fields_assignment.targets[0].id == "DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS"
        and isinstance(fields_assignment.value, ast.Dict)
    ):
        raise EvidenceGraphError("release pin fields must be one exact literal mapping")
    if not (
        isinstance(export_assignment, ast.Assign)
        and len(export_assignment.targets) == 1
        and isinstance(export_assignment.targets[0], ast.Name)
        and export_assignment.targets[0].id == "__all__"
    ):
        raise EvidenceGraphError("release pin exports must be one exact literal list")
    try:
        raw_fields = ast.literal_eval(fields_assignment.value)
        raw_exports = ast.literal_eval(export_assignment.value)
    except (ValueError, TypeError, SyntaxError) as exc:
        raise EvidenceGraphError(
            "release pin source contains executable syntax"
        ) from exc
    if (
        not isinstance(raw_fields, dict)
        or set(raw_fields) != _RELEASE_PIN_FIELD_NAMES
        or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in raw_fields.items()
        )
    ):
        raise EvidenceGraphError("release pin literal fields are invalid")
    if raw_exports != ["DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS"]:
        raise EvidenceGraphError("release pin literal exports are invalid")
    return dict(raw_fields)


class ProcessResult(str, Enum):
    """Execution outcome only; it carries no scientific meaning."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"


class EvidenceStatus(str, Enum):
    """Condition of the evidence, kept distinct from process/science axes."""

    PRESENT = "PRESENT"
    BLOCKED = "BLOCKED"
    MISSING = "MISSING"
    STALE = "STALE"
    INVALID = "INVALID"
    SKIPPED = "SKIPPED"
    XFAIL = "XFAIL"


class EvidenceNodeKind(str, Enum):
    CLAIM = "claim"
    PRODUCER = "producer"
    INPUT = "input"
    CONFIG = "config"
    ENVIRONMENT = "environment"
    TEST = "test"
    ORACLE = "oracle"
    ARTIFACT = "artifact"
    CONSUMER = "consumer"


class EvidenceEdgeKind(str, Enum):
    PRODUCED_BY = "produced_by"
    USES_INPUT = "uses_input"
    USES_CONFIG = "uses_config"
    USES_ENVIRONMENT = "uses_environment"
    CHECKED_BY = "checked_by"
    GENERATES = "generates"
    CONSUMED_BY = "consumed_by"
    DEPENDS_ON = "depends_on"
    SUPERSEDED_BY = "superseded_by"
    INVALIDATES_THEOREM = "invalidates_theorem"
    INVALIDATES_DATA = "invalidates_data"
    INVALIDATES_MASK = "invalidates_mask"
    INVALIDATES_COVARIANCE = "invalidates_covariance"
    INVALIDATES_TRANSFER = "invalidates_transfer"
    INVALIDATES_ESTIMAND = "invalidates_estimand"
    REQUIRES_RECALIBRATION = "requires_recalibration"
    REQUIRES_REEXECUTION = "requires_reexecution"


class TestOutcome(str, Enum):
    __test__ = False

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    XFAIL = "XFAIL"
    XPASS = "XPASS"


class ReceiptDependencyKind(str, Enum):
    PARENT = "parent"
    INDEPENDENT = "independent"


_ALLOWED_EDGE_ENDPOINTS: Mapping[
    EvidenceEdgeKind, frozenset[tuple[EvidenceNodeKind, EvidenceNodeKind]]
] = {
    EvidenceEdgeKind.PRODUCED_BY: frozenset(
        {(EvidenceNodeKind.CLAIM, EvidenceNodeKind.PRODUCER)}
    ),
    EvidenceEdgeKind.USES_INPUT: frozenset(
        {(EvidenceNodeKind.PRODUCER, EvidenceNodeKind.INPUT)}
    ),
    EvidenceEdgeKind.USES_CONFIG: frozenset(
        {(EvidenceNodeKind.PRODUCER, EvidenceNodeKind.CONFIG)}
    ),
    EvidenceEdgeKind.USES_ENVIRONMENT: frozenset(
        {(EvidenceNodeKind.PRODUCER, EvidenceNodeKind.ENVIRONMENT)}
    ),
    EvidenceEdgeKind.CHECKED_BY: frozenset(
        {
            (EvidenceNodeKind.PRODUCER, EvidenceNodeKind.TEST),
            (EvidenceNodeKind.PRODUCER, EvidenceNodeKind.ORACLE),
        }
    ),
    EvidenceEdgeKind.GENERATES: frozenset(
        {
            (EvidenceNodeKind.PRODUCER, EvidenceNodeKind.ARTIFACT),
            (EvidenceNodeKind.TEST, EvidenceNodeKind.ARTIFACT),
            (EvidenceNodeKind.ORACLE, EvidenceNodeKind.ARTIFACT),
        }
    ),
    EvidenceEdgeKind.CONSUMED_BY: frozenset(
        {(EvidenceNodeKind.ARTIFACT, EvidenceNodeKind.CONSUMER)}
    ),
    EvidenceEdgeKind.DEPENDS_ON: frozenset(
        {
            (EvidenceNodeKind.PRODUCER, EvidenceNodeKind.PRODUCER),
            (EvidenceNodeKind.INPUT, EvidenceNodeKind.INPUT),
            (EvidenceNodeKind.CONFIG, EvidenceNodeKind.CONFIG),
            (EvidenceNodeKind.ENVIRONMENT, EvidenceNodeKind.ENVIRONMENT),
            (EvidenceNodeKind.TEST, EvidenceNodeKind.TEST),
            (EvidenceNodeKind.ORACLE, EvidenceNodeKind.ORACLE),
            (EvidenceNodeKind.ARTIFACT, EvidenceNodeKind.ARTIFACT),
            (EvidenceNodeKind.CONSUMER, EvidenceNodeKind.CONSUMER),
        }
    ),
    EvidenceEdgeKind.SUPERSEDED_BY: frozenset(
        (kind, kind) for kind in EvidenceNodeKind
    ),
    EvidenceEdgeKind.INVALIDATES_THEOREM: frozenset(
        (EvidenceNodeKind.CLAIM, target)
        for target in (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
    ),
    EvidenceEdgeKind.INVALIDATES_DATA: frozenset(
        (EvidenceNodeKind.INPUT, target)
        for target in (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
    ),
    EvidenceEdgeKind.INVALIDATES_MASK: frozenset(
        (source, target)
        for source in (EvidenceNodeKind.INPUT, EvidenceNodeKind.CONFIG)
        for target in (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
    ),
    EvidenceEdgeKind.INVALIDATES_COVARIANCE: frozenset(
        (source, target)
        for source in (EvidenceNodeKind.INPUT, EvidenceNodeKind.CONFIG)
        for target in (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
    ),
    EvidenceEdgeKind.INVALIDATES_TRANSFER: frozenset(
        (source, target)
        for source in (EvidenceNodeKind.INPUT, EvidenceNodeKind.CONFIG)
        for target in (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
    ),
    EvidenceEdgeKind.INVALIDATES_ESTIMAND: frozenset(
        (source, target)
        for source in (EvidenceNodeKind.CLAIM, EvidenceNodeKind.CONFIG)
        for target in (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
    ),
    EvidenceEdgeKind.REQUIRES_RECALIBRATION: frozenset(
        (source, target)
        for source in (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.INPUT,
            EvidenceNodeKind.CONFIG,
            EvidenceNodeKind.ARTIFACT,
        )
        for target in (
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
    ),
    EvidenceEdgeKind.REQUIRES_REEXECUTION: frozenset(
        (source, target)
        for source in (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.INPUT,
            EvidenceNodeKind.CONFIG,
            EvidenceNodeKind.ARTIFACT,
        )
        for target in (
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
    ),
}

_LIFECYCLE_EDGE_KINDS = frozenset(
    {
        EvidenceEdgeKind.SUPERSEDED_BY,
        EvidenceEdgeKind.INVALIDATES_THEOREM,
        EvidenceEdgeKind.INVALIDATES_DATA,
        EvidenceEdgeKind.INVALIDATES_MASK,
        EvidenceEdgeKind.INVALIDATES_COVARIANCE,
        EvidenceEdgeKind.INVALIDATES_TRANSFER,
        EvidenceEdgeKind.INVALIDATES_ESTIMAND,
        EvidenceEdgeKind.REQUIRES_RECALIBRATION,
        EvidenceEdgeKind.REQUIRES_REEXECUTION,
    }
)

_ACTIVE_CAPABILITY_BLOCKING_EDGE_KINDS = _LIFECYCLE_EDGE_KINDS - {
    EvidenceEdgeKind.SUPERSEDED_BY
}

_INVALIDATION_DIMENSION_BY_EDGE: Mapping[EvidenceEdgeKind, IdentityDimension] = {
    EvidenceEdgeKind.INVALIDATES_THEOREM: IdentityDimension.THEOREM,
    EvidenceEdgeKind.INVALIDATES_DATA: IdentityDimension.DATA,
    EvidenceEdgeKind.INVALIDATES_MASK: IdentityDimension.MASK,
    EvidenceEdgeKind.INVALIDATES_COVARIANCE: IdentityDimension.COVARIANCE,
    EvidenceEdgeKind.INVALIDATES_TRANSFER: IdentityDimension.TRANSFER,
    EvidenceEdgeKind.INVALIDATES_ESTIMAND: IdentityDimension.ESTIMAND,
}

_READINESS_KEYS = frozenset(
    {
        "readyforclaims",
        "claimready",
        "releaseready",
        "releaseeligible",
        "scientificallyvalid",
    }
)
_CALLER_STATISTICAL_GATE_KEYS = frozenset(
    {"ppcpassed", "bayesfactor", "pseudoppc", "posteriorprobability"}
)
_BLOCKING_SCIENTIFIC_STATUSES = frozenset(
    {
        ScientificStatus.BLOCKED,
        ScientificStatus.FALSIFIED,
        ScientificStatus.ABANDONED,
    }
)
_PACKAGE_CONSUMABLE_SCIENTIFIC_STATUSES = frozenset(
    {
        ScientificStatus.EVIDENCE_READY,
        ScientificStatus.ADJUDICATION_PENDING,
        ScientificStatus.RESCUED,
        ScientificStatus.CORRECTED_SUPERSEDED,
    }
)
_CLAIM_RELEASE_SCIENTIFIC_STATUSES = frozenset(
    {
        ScientificStatus.RESCUED,
        ScientificStatus.CORRECTED_SUPERSEDED,
    }
)
_AUTHORITY_GATED_SCIENTIFIC_STATUSES = frozenset(
    {
        ScientificStatus.RESCUED,
        ScientificStatus.CORRECTED_SUPERSEDED,
        ScientificStatus.FALSIFIED,
        ScientificStatus.BLOCKED,
        ScientificStatus.ABANDONED,
    }
)
_EVIDENCE_PRECEDENCE = (
    EvidenceStatus.INVALID,
    EvidenceStatus.STALE,
    EvidenceStatus.MISSING,
    EvidenceStatus.BLOCKED,
    EvidenceStatus.SKIPPED,
    EvidenceStatus.XFAIL,
    EvidenceStatus.PRESENT,
)


def _enum_value(value: object) -> str:
    return str(value.value) if isinstance(value, Enum) else str(value)


def _exact_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceGraphError(f"{field} must be a non-empty string")
    if value != value.strip():
        raise EvidenceGraphError(
            f"{field} must not contain leading or trailing whitespace"
        )
    return value


def _sha256(value: object, field: str) -> str:
    digest = _exact_text(value, field)
    if not _SHA256_RE.fullmatch(digest):
        raise EvidenceGraphError(f"{field} must be a lowercase SHA-256 digest")
    return digest


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            _jsonable(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EvidenceGraphError("value is not canonical JSON data") from exc


def _content_address(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _reject_readiness_fields(value: object, *, path: str = "metadata") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise EvidenceGraphError(f"{path} keys must be strings")
            if _normalized_key(key) in _READINESS_KEYS:
                raise EvidenceGraphError(
                    f"caller-supplied readiness field is forbidden: {path}.{key}"
                )
            if _normalized_key(key) in _CALLER_STATISTICAL_GATE_KEYS:
                raise EvidenceGraphError(
                    "caller-supplied statistical gate field is forbidden: "
                    f"{path}.{key}"
                )
            _reject_readiness_fields(nested, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _reject_readiness_fields(nested, path=f"{path}[{index}]")


def _freeze_json(value: object) -> object:
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise EvidenceGraphError("JSON object keys must be strings")
            frozen[key] = _freeze_json(value[key])
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, bool, int, float)):
        _canonical_bytes_scalar(value)
        return value
    raise EvidenceGraphError(
        f"metadata contains non-JSON value of type {type(value).__name__}"
    )


def _canonical_bytes_scalar(value: object) -> None:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EvidenceGraphError("metadata contains a non-canonical scalar") from exc


def _jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def _parse_datetime(value: datetime | date | str, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime(value.year, value.month, value.day, tzinfo=UTC)
    elif isinstance(value, str) and value:
        raw = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise EvidenceGraphError(f"{field} must be an ISO-8601 datetime") from exc
    else:
        raise EvidenceGraphError(f"{field} must be an ISO-8601 datetime")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _strict_keys(
    value: Mapping[str, object], *, required: set[str], field: str
) -> None:
    missing = required - set(value)
    unknown = set(value) - required
    if missing:
        raise EvidenceGraphError(f"{field} is missing fields: {sorted(missing)}")
    if unknown:
        raise EvidenceGraphError(f"{field} has unknown fields: {sorted(unknown)}")


def verify_pytest_selector_inputs(
    repo_root: Path | str, payload: Mapping[str, object]
) -> tuple[tuple[str, str], ...]:
    """Rehash every explicit pytest selector source under the repository root.

    Test-result JSON is not durable execution evidence if the selected source
    files can drift after collection.  This verifier is shared by graph
    generation and release consumption so both enforce the same path and hash
    contract.
    """

    if not isinstance(payload, Mapping):
        raise EvidenceGraphError("pytest evidence payload must be a mapping")
    root = Path(repo_root).resolve()
    rows = payload.get("selector_inputs")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise EvidenceGraphError("pytest evidence requires selector_inputs")
    verified: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise EvidenceGraphError("pytest selector input must be a mapping")
        _strict_keys(
            row,
            required={"scope", "path", "sha256"},
            field="pytest selector input",
        )
        if row["scope"] != "repo":
            raise EvidenceGraphError(
                "authoritative pytest selector inputs must be repository-local"
            )
        relative = _exact_text(row["path"], "pytest selector input path")
        if "\\" in relative:
            raise EvidenceGraphError("pytest selector input must use POSIX separators")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
            raise EvidenceGraphError(
                "pytest selector input must be repository-relative"
            )
        if relative in seen:
            raise EvidenceGraphError("pytest selector inputs contain a duplicate path")
        seen.add(relative)
        expected = _sha256(row["sha256"], "pytest selector input sha256")
        path = root.joinpath(*pure.parts)
        try:
            path.resolve(strict=False).relative_to(root)
        except ValueError as exc:
            raise EvidenceGraphError(
                f"pytest selector input escapes repository: {relative}"
            ) from exc
        if path.is_symlink() or not path.is_file():
            raise EvidenceGraphError(
                f"pytest selector input is missing or non-regular: {relative}"
            )
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise EvidenceGraphError(f"pytest selector input hash drift: {relative}")
        verified.append((relative, expected))
    verify_pytest_environment_inputs(root, payload)
    return tuple(sorted(verified))


_PYTEST_ENVIRONMENT_SCHEMA = "common.pytest_execution_environment.v1"
_ENVIRONMENT_PATH_SCOPES = frozenset(
    {
        "repo",
        "python_prefix",
        "python_base_prefix",
        "python_config",
        "external_untrusted",
    }
)


def _reject_host_paths_in_pytest_argv(payload: Mapping[str, object]) -> None:
    for field in ("selector_argv", "normalized_invocation_argv"):
        rows = payload.get(field)
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise EvidenceGraphError(f"pytest evidence {field} must be a sequence")
        for raw in rows:
            value = _exact_text(raw, f"pytest evidence {field}")
            if value == "--noconftest" or value.startswith("--confcutdir"):
                raise EvidenceGraphError(
                    "pytest conftest discovery controls are not authoritative"
                )
            for candidate in value.split("="):
                path_part = candidate.split("::", 1)[0]
                if PurePosixPath(path_part).is_absolute() or re.match(
                    r"[A-Za-z]:[\\/]", path_part
                ):
                    raise EvidenceGraphError(
                        f"pytest evidence {field} contains a host-absolute path"
                    )


def _environment_path_binding(
    value: object,
    *,
    field: str,
    require_hash: bool,
) -> tuple[str, str, str | None]:
    if not isinstance(value, Mapping):
        raise EvidenceGraphError(f"{field} must be a mapping")
    required = {"scope", "path", *(("sha256",) if require_hash else ())}
    _strict_keys(value, required=required, field=field)
    scope = _exact_text(value["scope"], f"{field}.scope")
    if scope not in _ENVIRONMENT_PATH_SCOPES:
        raise EvidenceGraphError(f"{field}.scope is unsupported")
    relative = _exact_text(value["path"], f"{field}.path")
    if "\\" in relative:
        raise EvidenceGraphError(f"{field}.path must use POSIX separators")
    pure = PurePosixPath(relative)
    if relative != "." and (
        pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise EvidenceGraphError(f"{field}.path must be a canonical relative path")
    digest = None
    if require_hash:
        digest = _sha256(value["sha256"], f"{field}.sha256")
    return scope, relative, digest


def _pytest_environment_contract(
    payload: Mapping[str, object],
) -> tuple[Mapping[str, object], str]:
    raw = payload.get("environment_contract")
    if not isinstance(raw, Mapping):
        raise EvidenceGraphError("pytest evidence requires environment_contract")
    required = {
        "schema_version",
        "interpreter",
        "sys_path",
        "pytest",
        "import_origins",
        "excluded_import_origins",
        "bytecode_policy",
        "startup_policy",
        "hidden_controls",
        "environment_ref",
    }
    _strict_keys(raw, required=required, field="pytest environment contract")
    if raw["schema_version"] != _PYTEST_ENVIRONMENT_SCHEMA:
        raise EvidenceGraphError("unsupported pytest environment contract schema")
    _reject_host_paths_in_pytest_argv(payload)
    unsigned = dict(raw)
    expected_ref = _sha256(unsigned.pop("environment_ref"), "environment_ref")
    if _content_address(unsigned) != expected_ref:
        raise EvidenceGraphError("pytest environment_ref does not match contract")

    interpreter = raw["interpreter"]
    if not isinstance(interpreter, Mapping):
        raise EvidenceGraphError("pytest interpreter contract must be a mapping")
    _strict_keys(
        interpreter,
        required={
            "implementation",
            "version",
            "cache_tag",
            "executable",
            "isolated",
            "safe_path",
            "user_site_enabled",
        },
        field="pytest interpreter contract",
    )
    for key in ("implementation", "version", "cache_tag"):
        _exact_text(interpreter[key], f"pytest interpreter {key}")
    _environment_path_binding(
        interpreter["executable"],
        field="pytest interpreter executable",
        require_hash=True,
    )
    for key in ("isolated", "safe_path", "user_site_enabled"):
        if type(interpreter[key]) is not bool:
            raise EvidenceGraphError(f"pytest interpreter {key} must be boolean")
    if not interpreter["isolated"] or not interpreter["safe_path"]:
        raise EvidenceGraphError(
            "authoritative pytest execution requires isolated safe-path mode"
        )
    if interpreter["user_site_enabled"]:
        raise EvidenceGraphError(
            "authoritative pytest execution requires user-site isolation"
        )

    sys_path_rows = raw["sys_path"]
    if (
        not isinstance(sys_path_rows, Sequence)
        or isinstance(sys_path_rows, (str, bytes))
        or not sys_path_rows
    ):
        raise EvidenceGraphError("pytest environment sys_path must be non-empty")
    path_identities: list[tuple[str, str]] = []
    for index, row in enumerate(sys_path_rows):
        scope, relative, _digest = _environment_path_binding(
            row,
            field=f"pytest environment sys_path[{index}]",
            require_hash=False,
        )
        path_identities.append((scope, relative))
    if len(path_identities) != len(set(path_identities)):
        raise EvidenceGraphError("pytest environment sys_path contains duplicates")

    pytest_contract = raw["pytest"]
    if not isinstance(pytest_contract, Mapping):
        raise EvidenceGraphError("pytest runner environment must be a mapping")
    _strict_keys(
        pytest_contract,
        required={
            "version",
            "rootdir",
            "import_mode",
            "config_file",
            "config_values",
            "config_values_sha256",
            "plugins",
            "conftests",
        },
        field="pytest runner environment",
    )
    if pytest_contract["rootdir"] != ".":
        raise EvidenceGraphError("pytest rootdir must be the repository root")
    if pytest_contract["import_mode"] != "importlib":
        raise EvidenceGraphError("authoritative pytest requires importlib mode")
    _exact_text(pytest_contract["version"], "pytest environment version")
    _environment_path_binding(
        pytest_contract["config_file"],
        field="pytest config file",
        require_hash=True,
    )
    config_values = pytest_contract["config_values"]
    if not isinstance(config_values, Mapping):
        raise EvidenceGraphError("pytest config_values must be a mapping")
    config_ref = _sha256(
        pytest_contract["config_values_sha256"], "pytest config_values_sha256"
    )
    if _content_address(config_values) != config_ref:
        raise EvidenceGraphError("pytest config_values_sha256 mismatch")

    plugins = pytest_contract["plugins"]
    if (
        not isinstance(plugins, Sequence)
        or isinstance(plugins, (str, bytes))
        or not plugins
    ):
        raise EvidenceGraphError("pytest environment plugin inventory is empty")
    plugin_ids: list[tuple[str, str]] = []
    for index, row in enumerate(plugins):
        if not isinstance(row, Mapping):
            raise EvidenceGraphError("pytest plugin inventory row must be a mapping")
        _strict_keys(
            row,
            required={"module", "qualname", "source"},
            field=f"pytest plugin[{index}]",
        )
        module = _exact_text(row["module"], f"pytest plugin[{index}].module")
        qualname = _exact_text(row["qualname"], f"pytest plugin[{index}].qualname")
        _environment_path_binding(
            row["source"],
            field=f"pytest plugin[{index}].source",
            require_hash=True,
        )
        plugin_ids.append((module, qualname))
    if len(plugin_ids) != len(set(plugin_ids)):
        raise EvidenceGraphError("pytest plugin inventory contains duplicates")
    if not any(
        module == "common.pytest_execution_evidence" for module, _ in plugin_ids
    ):
        raise EvidenceGraphError("pytest evidence plugin is absent from inventory")

    conftests = pytest_contract["conftests"]
    if not isinstance(conftests, Sequence) or isinstance(conftests, (str, bytes)):
        raise EvidenceGraphError("pytest conftest inventory must be a sequence")
    conftest_ids: list[tuple[str, str]] = []
    for index, row in enumerate(conftests):
        scope, relative, _digest = _environment_path_binding(
            row,
            field=f"pytest conftest[{index}]",
            require_hash=True,
        )
        conftest_ids.append((scope, relative))
    if len(conftest_ids) != len(set(conftest_ids)):
        raise EvidenceGraphError("pytest conftest inventory contains duplicates")

    origins = raw["import_origins"]
    if (
        not isinstance(origins, Sequence)
        or isinstance(origins, (str, bytes))
        or not origins
    ):
        raise EvidenceGraphError("pytest import-origin inventory is empty")
    origin_ids: list[str] = []
    for index, row in enumerate(origins):
        if not isinstance(row, Mapping):
            raise EvidenceGraphError("pytest import-origin row must be a mapping")
        _strict_keys(
            row,
            required={"module", "source"},
            field=f"pytest import origin[{index}]",
        )
        module = _exact_text(row["module"], f"pytest import origin[{index}].module")
        _environment_path_binding(
            row["source"],
            field=f"pytest import origin[{index}].source",
            require_hash=True,
        )
        origin_ids.append(module)
    if len(origin_ids) != len(set(origin_ids)):
        raise EvidenceGraphError("pytest import-origin inventory contains duplicates")
    if not {"pytest", "common.pytest_execution_evidence"} <= set(origin_ids):
        raise EvidenceGraphError("pytest runner import origins are incomplete")

    excluded_origins = raw["excluded_import_origins"]
    if not isinstance(excluded_origins, Sequence) or isinstance(
        excluded_origins, (str, bytes)
    ):
        raise EvidenceGraphError("pytest excluded import origins must be a sequence")
    normalized_exclusions: list[dict[str, object]] = []
    for index, row in enumerate(excluded_origins):
        if not isinstance(row, Mapping):
            raise EvidenceGraphError(
                "pytest excluded import-origin row must be a mapping"
            )
        _strict_keys(
            row,
            required={"module", "source", "reason"},
            field=f"pytest excluded import origin[{index}]",
        )
        scope, relative, _digest = _environment_path_binding(
            row["source"],
            field=f"pytest excluded import origin[{index}].source",
            require_hash=False,
        )
        normalized_exclusions.append(
            {
                "module": _exact_text(
                    row["module"], f"pytest excluded import origin[{index}].module"
                ),
                "source": {"scope": scope, "path": relative},
                "reason": _exact_text(
                    row["reason"], f"pytest excluded import origin[{index}].reason"
                ),
            }
        )
    if tuple(normalized_exclusions) != _PYTEST_EXCLUDED_IMPORT_ORIGINS:
        raise EvidenceGraphError(
            "pytest excluded import origins do not match the exact fixed-point policy"
        )
    excluded_modules = {str(row["module"]) for row in normalized_exclusions}
    excluded_sources = {
        (str(row["source"]["scope"]), str(row["source"]["path"]))
        for row in normalized_exclusions
        if isinstance(row["source"], Mapping)
    }
    if excluded_modules & set(origin_ids):
        raise EvidenceGraphError(
            "pytest excluded import origin is also present in the bound inventory"
        )
    for index, row in enumerate(origins):
        assert isinstance(row, Mapping)
        scope, relative, _digest = _environment_path_binding(
            row["source"],
            field=f"pytest import origin[{index}].source",
            require_hash=True,
        )
        if (scope, relative) in excluded_sources:
            raise EvidenceGraphError(
                "pytest excluded import source is present under a module alias"
            )

    bytecode = raw["bytecode_policy"]
    if not isinstance(bytecode, Mapping):
        raise EvidenceGraphError("pytest bytecode policy must be a mapping")
    _strict_keys(
        bytecode,
        required={
            "dont_write_bytecode",
            "pycache_prefix_status",
            "loaded_cache_files",
        },
        field="pytest bytecode policy",
    )
    if bytecode["dont_write_bytecode"] is not True:
        raise EvidenceGraphError("pytest bytecode policy requires -B")
    if bytecode["pycache_prefix_status"] != "isolated_empty_external":
        raise EvidenceGraphError("pytest bytecode cache prefix is not isolated")
    if bytecode["loaded_cache_files"] != []:
        raise EvidenceGraphError("pytest execution loaded bytecode cache files")

    startup = raw["startup_policy"]
    if not isinstance(startup, Mapping):
        raise EvidenceGraphError("pytest startup policy must be a mapping")
    _strict_keys(
        startup,
        required={
            "no_site",
            "automatic_pth_processing",
            "pyvenv_cfg_activation",
        },
        field="pytest startup policy",
    )
    if startup != {
        "no_site": True,
        "automatic_pth_processing": "disabled_by_no_site",
        "pyvenv_cfg_activation": "disabled_by_no_site",
    }:
        raise EvidenceGraphError(
            "pytest startup policy must disable site, .pth, and pyvenv activation"
        )

    hidden = raw["hidden_controls"]
    if not isinstance(hidden, Mapping):
        raise EvidenceGraphError("pytest hidden-controls contract must be a mapping")
    _strict_keys(
        hidden,
        required={
            "pytest_addopts",
            "pytest_plugins",
            "pytest_disable_plugin_autoload",
            "pythonpath_status",
        },
        field="pytest hidden controls",
    )
    if hidden["pytest_addopts"] not in {None, ""}:
        raise EvidenceGraphError(
            "PYTEST_ADDOPTS cannot influence authoritative evidence"
        )
    if hidden["pytest_plugins"] not in {None, ""}:
        raise EvidenceGraphError(
            "PYTEST_PLUGINS cannot influence authoritative evidence"
        )
    if hidden["pytest_disable_plugin_autoload"] != "1":
        raise EvidenceGraphError(
            "authoritative pytest requires disabled plugin autoload"
        )
    if hidden["pythonpath_status"] not in {"unset", "ignored_by_isolated_mode"}:
        raise EvidenceGraphError("effective PYTHONPATH is not authoritative")
    return raw, expected_ref


def _resolve_environment_path(
    root: Path,
    *,
    scope: str,
    relative: str,
) -> Path:
    if scope == "external_untrusted":
        raise EvidenceGraphError("external execution-environment path is untrusted")
    sitecustomize = importlib.util.find_spec("sitecustomize")
    python_config_root = (
        None
        if sitecustomize is None or sitecustomize.origin is None
        else Path(sitecustomize.origin).resolve().parent
    )
    anchors = {
        "repo": root,
        "python_prefix": Path(sys.prefix).resolve(),
        "python_base_prefix": Path(sys.base_prefix).resolve(),
        "python_config": python_config_root,
    }
    anchor = anchors[scope]
    if anchor is None:
        raise EvidenceGraphError("Python configuration root cannot be resolved")
    candidate = (
        anchor if relative == "." else anchor.joinpath(*PurePosixPath(relative).parts)
    )
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(anchor)
    except ValueError as exc:
        raise EvidenceGraphError(
            "pytest environment path escapes its bound root"
        ) from exc
    return candidate


def _canonical_environment_path_identity(
    root: Path,
    path: Path,
) -> tuple[str, str]:
    resolved = path.resolve(strict=False)
    if resolved.suffix == ".pyc":
        try:
            source = Path(importlib.util.source_from_cache(str(resolved)))
        except (NotImplementedError, ValueError):
            source = resolved
        if source.is_file():
            resolved = source.resolve()
    for scope, anchor in (
        ("repo", root),
        ("python_base_prefix", Path(sys.base_prefix).resolve()),
        ("python_prefix", Path(sys.prefix).resolve()),
        (
            "python_config",
            (
                Path(sitecustomize.origin).resolve().parent
                if (
                    (sitecustomize := importlib.util.find_spec("sitecustomize"))
                    is not None
                    and sitecustomize.origin is not None
                )
                else None
            ),
        ),
    ):
        if anchor is None:
            continue
        try:
            relative = resolved.relative_to(anchor)
        except ValueError:
            continue
        return scope, relative.as_posix() or "."
    raise EvidenceGraphError("canonical execution-environment path is untrusted")


def _canonical_module_path_identity(root: Path, module: str) -> tuple[str, str]:
    try:
        spec = importlib.util.find_spec(module)
    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        raise EvidenceGraphError(
            f"pytest plugin module cannot be resolved: {module}"
        ) from exc
    if spec is None or spec.origin in {None, "built-in", "frozen"}:
        raise EvidenceGraphError(f"pytest plugin module has no source: {module}")
    return _canonical_environment_path_identity(root, Path(spec.origin))


def _require_canonical_binding(
    value: object,
    *,
    expected: tuple[str, str],
    field: str,
) -> None:
    scope, relative, _digest = _environment_path_binding(
        value,
        field=field,
        require_hash=True,
    )
    if (scope, relative) != expected:
        raise EvidenceGraphError(f"{field} does not match its canonical source")


def _expected_pytest_conftests(
    root: Path,
    payload: Mapping[str, object],
) -> tuple[tuple[str, str], ...]:
    rows = payload.get("selector_inputs")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise EvidenceGraphError("pytest selector inputs must be a sequence")
    expected: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping) or row.get("scope") != "repo":
            raise EvidenceGraphError(
                "authoritative pytest selector inputs must be repository-local"
            )
        relative = PurePosixPath(str(row.get("path", "")))
        if relative.is_absolute() or any(
            part in {"", ".", ".."} for part in relative.parts
        ):
            raise EvidenceGraphError("pytest selector path is not canonical")
        directory = root.joinpath(*relative.parts).parent
        while True:
            candidate = directory / "conftest.py"
            if candidate.is_file() and not candidate.is_symlink():
                expected.add(_canonical_environment_path_identity(root, candidate))
            if directory == root:
                break
            try:
                directory.relative_to(root)
            except ValueError as exc:
                raise EvidenceGraphError(
                    "pytest selector escapes repository during conftest discovery"
                ) from exc
            directory = directory.parent
    return tuple(sorted(expected))


def verify_pytest_environment_inputs(
    repo_root: Path | str,
    payload: Mapping[str, object],
    *,
    parent_environment_lock: Mapping[str, object] | None = None,
) -> str:
    """Rehash the interpreter, config, plugins, conftests, and import origins."""

    if not isinstance(payload, Mapping):
        raise EvidenceGraphError("pytest evidence payload must be a mapping")
    root = Path(repo_root).resolve()
    contract, environment_ref = _pytest_environment_contract(payload)
    interpreter = contract["interpreter"]
    pytest_contract = contract["pytest"]
    assert isinstance(interpreter, Mapping)
    assert isinstance(pytest_contract, Mapping)

    current_interpreter = {
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
        "cache_tag": str(getattr(sys.implementation, "cache_tag", "")),
    }
    for field, current in current_interpreter.items():
        if interpreter[field] != current:
            raise EvidenceGraphError(
                f"pytest interpreter {field} mismatches verifier environment"
            )
    try:
        current_pytest_version = importlib_metadata.version("pytest")
    except importlib_metadata.PackageNotFoundError as exc:
        raise EvidenceGraphError("pytest distribution cannot be resolved") from exc
    if pytest_contract["version"] != current_pytest_version:
        raise EvidenceGraphError("pytest version mismatches verifier environment")
    _require_canonical_binding(
        interpreter["executable"],
        expected=_canonical_environment_path_identity(root, Path(sys.executable)),
        field="pytest interpreter executable",
    )
    _require_canonical_binding(
        pytest_contract["config_file"],
        expected=_canonical_environment_path_identity(root, root / "pytest.ini"),
        field="pytest config file",
    )
    for index, row in enumerate(pytest_contract["plugins"]):
        assert isinstance(row, Mapping)
        module = str(row["module"])
        _require_canonical_binding(
            row["source"],
            expected=_canonical_module_path_identity(root, module),
            field=f"pytest plugin[{index}].source",
        )
    mandatory_origins = {"pytest", "common.pytest_execution_evidence"}
    for index, row in enumerate(contract["import_origins"]):
        assert isinstance(row, Mapping)
        module = str(row["module"])
        if module not in mandatory_origins:
            continue
        _require_canonical_binding(
            row["source"],
            expected=_canonical_module_path_identity(root, module),
            field=f"pytest import origin[{index}].source",
        )

    declared_conftests: list[tuple[str, str]] = []
    for index, row in enumerate(pytest_contract["conftests"]):
        scope, relative, _digest = _environment_path_binding(
            row,
            field=f"pytest conftest[{index}]",
            require_hash=True,
        )
        declared_conftests.append((scope, relative))
    if tuple(sorted(declared_conftests)) != _expected_pytest_conftests(root, payload):
        raise EvidenceGraphError(
            "pytest conftest inventory does not match selector ancestry"
        )

    bindings: list[tuple[str, Mapping[str, object]]] = [
        ("pytest interpreter executable", interpreter["executable"]),
        ("pytest config file", pytest_contract["config_file"]),
    ]
    for index, row in enumerate(pytest_contract["plugins"]):
        assert isinstance(row, Mapping)
        bindings.append((f"pytest plugin[{index}]", row["source"]))
    for index, row in enumerate(pytest_contract["conftests"]):
        bindings.append((f"pytest conftest[{index}]", row))
    for index, row in enumerate(contract["import_origins"]):
        assert isinstance(row, Mapping)
        bindings.append((f"pytest import origin[{index}]", row["source"]))
    for label, raw_binding in bindings:
        scope, relative, expected = _environment_path_binding(
            raw_binding,
            field=label,
            require_hash=True,
        )
        assert expected is not None
        path = _resolve_environment_path(root, scope=scope, relative=relative)
        if path.is_symlink() or not path.is_file():
            raise EvidenceGraphError(f"{label} is missing or non-regular")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise EvidenceGraphError(f"{label} hash drift")

    for index, row in enumerate(contract["sys_path"]):
        scope, relative, _digest = _environment_path_binding(
            row,
            field=f"pytest environment sys_path[{index}]",
            require_hash=False,
        )
        _resolve_environment_path(root, scope=scope, relative=relative)

    if parent_environment_lock is not None:
        if not isinstance(parent_environment_lock, Mapping):
            raise EvidenceGraphError("parent environment lock must be a mapping")
        expected_python = parent_environment_lock.get("python")
        if interpreter["version"] != expected_python:
            raise EvidenceGraphError("pytest Python version mismatches PR-121 lock")
        if parent_environment_lock.get("isolated_mode") != "required_and_observed":
            raise EvidenceGraphError("PR-121 isolated-mode lock is not authoritative")
        if parent_environment_lock.get("user_site") != "disabled":
            raise EvidenceGraphError("PR-121 user-site lock is not authoritative")
        if pytest_contract["import_mode"] != parent_environment_lock.get(
            "pytest_import_mode"
        ):
            raise EvidenceGraphError("pytest import mode mismatches PR-121 lock")
        if parent_environment_lock.get("host_paths_in_receipt") != "forbidden":
            raise EvidenceGraphError("PR-121 host-path policy is not authoritative")
    return environment_ref


def authority_registry_content_ref(registry: AuthorityRegistry) -> str:
    """Hash the exact principal registry semantics consumed by a receipt.

    Verifier implementation trust remains with ``AuthorityRegistry``; the
    digest binds principal identities, aliases, roles, scopes, validity,
    independence class, revocation state, and the semantic state of every
    verifier callback so a receipt cannot silently validate against a
    different principal set or verifier policy.
    """

    if not isinstance(registry, AuthorityRegistry):
        raise TypeError("registry must be an AuthorityRegistry")
    principals = []
    callbacks = registry.verifier_bindings()
    verifier_names: set[str] = set()
    for principal in sorted(registry.all(), key=lambda row: row.principal_id):
        verifier_names.add(principal.verifier)
        principals.append(
            {
                "principal_id": principal.principal_id,
                "identity_fingerprint": principal.identity_fingerprint,
                "aliases": sorted(principal.aliases),
                "allowed_roles": sorted(principal.allowed_roles),
                "allowed_scopes": sorted(principal.allowed_scopes),
                "independence_class": principal.independence_class,
                "valid_from": principal.valid_from.isoformat(),
                "valid_until": principal.valid_until.isoformat(),
                "revoked": principal.revoked,
                "verifier": principal.verifier,
            }
        )
    if not principals:
        raise EvidenceGraphError("authority registry must contain principals")
    verifier_bindings = []
    for name in sorted(verifier_names):
        callback = callbacks.get(name)
        verifier_bindings.append(
            {
                "name": name,
                "implementation_ref": (
                    "UNBOUND"
                    if callback is None
                    else _verifier_implementation_ref(callback)
                ),
            }
        )
    return _content_address(
        {
            "schema_version": "authority_registry_content_v3",
            "canonicalization": CANONICALIZATION,
            "default_deny": registry.default_deny,
            "principals": principals,
            "verifier_bindings": verifier_bindings,
        }
    )


def _finite_float_identity(value: float, *, field: str) -> str:
    if not math.isfinite(value):
        raise EvidenceGraphError(f"{field} must be finite")
    return value.hex()


def _code_constant_identity(value: object) -> object:
    """Return a deterministic identity for the closed set of code constants."""

    if value is None:
        return {"kind": "none"}
    if value is Ellipsis:
        return {"kind": "ellipsis"}
    if type(value) is bool:
        return {"kind": "bool", "value": value}
    if type(value) is int:
        return {"kind": "int", "value": str(value)}
    if type(value) is float:
        return {
            "kind": "float",
            "hex": _finite_float_identity(value, field="verifier code float"),
        }
    if type(value) is complex:
        return {
            "kind": "complex",
            "real_hex": _finite_float_identity(
                value.real, field="verifier code complex real part"
            ),
            "imag_hex": _finite_float_identity(
                value.imag, field="verifier code complex imaginary part"
            ),
        }
    if type(value) is str:
        return {"kind": "str", "value": value}
    if type(value) is bytes:
        return {
            "kind": "bytes",
            "length": len(value),
            "sha256": hashlib.sha256(value).hexdigest(),
        }
    if type(value) is tuple:
        return {
            "kind": "tuple",
            "items": [_code_constant_identity(item) for item in value],
        }
    if type(value) is frozenset:
        items = [_code_constant_identity(item) for item in value]
        return {
            "kind": "frozenset",
            "items": sorted(items, key=_canonical_bytes),
        }
    if isinstance(value, CodeType):
        return {"kind": "nested_code", "code": _code_identity(value)}
    raise EvidenceGraphError(
        "trusted verifier contains an unsupported code constant of type "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _code_identity(value: CodeType) -> Mapping[str, object]:
    constants = [_code_constant_identity(constant) for constant in value.co_consts]
    line_table = getattr(value, "co_linetable", None)
    if not isinstance(line_table, bytes):
        line_table = value.co_lnotab
    return {
        "bytecode_sha256": hashlib.sha256(value.co_code).hexdigest(),
        "exception_table_sha256": hashlib.sha256(
            getattr(value, "co_exceptiontable", b"")
        ).hexdigest(),
        "line_table_sha256": hashlib.sha256(line_table).hexdigest(),
        "constants": constants,
        "name": value.co_name,
        "qualname": getattr(value, "co_qualname", value.co_name),
        "firstlineno": value.co_firstlineno,
        "names": list(value.co_names),
        "varnames": list(value.co_varnames),
        "freevars": list(value.co_freevars),
        "cellvars": list(value.co_cellvars),
        "argcount": value.co_argcount,
        "posonlyargcount": value.co_posonlyargcount,
        "kwonlyargcount": value.co_kwonlyargcount,
        "flags": value.co_flags,
        "nlocals": value.co_nlocals,
        "stacksize": value.co_stacksize,
    }


def _module_origin_identity(module: ModuleType) -> Mapping[str, object]:
    name = getattr(module, "__name__", None)
    if not isinstance(name, str) or not name:
        raise EvidenceGraphError("trusted verifier references an unnamed module")
    spec = getattr(module, "__spec__", None)
    origin = getattr(spec, "origin", None)
    if origin in {"built-in", "frozen"}:
        return {
            "kind": str(origin),
            "module": name,
            "python_implementation": sys.implementation.name,
            "python_version": list(sys.version_info[:3]),
        }
    if not isinstance(origin, str) or not origin:
        file_name = getattr(module, "__file__", None)
        origin = file_name if isinstance(file_name, str) and file_name else None
    if origin is None:
        raise EvidenceGraphError(
            f"trusted verifier module {name!r} has no verifiable origin"
        )
    path = Path(origin)
    if not path.is_file():
        raise EvidenceGraphError(
            f"trusted verifier module {name!r} origin is not a regular file"
        )
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise EvidenceGraphError(
            f"trusted verifier module {name!r} origin cannot be read"
        ) from exc
    return {
        "kind": "file",
        "module": name,
        "origin_suffix": path.suffix,
        "content_sha256": hashlib.sha256(payload).hexdigest(),
    }


def _type_identity(value: type[object]) -> Mapping[str, object]:
    module_name = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None)
    if not isinstance(module_name, str) or not module_name:
        raise EvidenceGraphError("trusted verifier references an unnamed type")
    if not isinstance(qualname, str) or not qualname:
        raise EvidenceGraphError("trusted verifier references an unqualified type")
    module = sys.modules.get(module_name)
    if not isinstance(module, ModuleType):
        raise EvidenceGraphError(
            f"trusted verifier type module {module_name!r} is not loaded"
        )
    try:
        source = inspect.getsource(value).encode("utf-8")
    except (OSError, TypeError):
        source = b""
    return {
        "kind": "type",
        "module": module_name,
        "qualname": qualname,
        "module_origin": _module_origin_identity(module),
        "source_sha256": hashlib.sha256(source).hexdigest(),
    }


def _referenced_global_accesses(
    code: CodeType,
) -> Mapping[str, tuple[tuple[str, ...], ...]]:
    accesses: dict[str, set[tuple[str, ...]]] = {}
    instructions = tuple(get_instructions(code))
    for index, instruction in enumerate(instructions):
        if instruction.opname not in {"LOAD_GLOBAL", "LOAD_NAME"}:
            continue
        name = instruction.argval
        if not isinstance(name, str) or not name:
            raise EvidenceGraphError("trusted verifier has an invalid global load")
        path: list[str] = []
        for following in instructions[index + 1 :]:
            if following.opname not in {"LOAD_ATTR", "LOAD_METHOD"}:
                break
            attribute = following.argval
            if not isinstance(attribute, str) or not attribute:
                raise EvidenceGraphError(
                    "trusted verifier has an invalid attribute load"
                )
            path.append(attribute)
        accesses.setdefault(name, set()).add(tuple(path))
    for constant in code.co_consts:
        if isinstance(constant, CodeType):
            for name, paths in _referenced_global_accesses(constant).items():
                accesses.setdefault(name, set()).update(paths)
    return {name: tuple(sorted(paths)) for name, paths in sorted(accesses.items())}


def _module_attribute_value(module: ModuleType, path: tuple[str, ...]) -> object:
    if not path:
        raise EvidenceGraphError(
            f"trusted verifier passes module {module.__name__!r} dynamically"
        )
    current: object = module
    for attribute in path:
        if not isinstance(current, ModuleType):
            raise EvidenceGraphError(
                "trusted verifier uses an unverifiable module attribute chain"
            )
        namespace = vars(current)
        if attribute not in namespace:
            raise EvidenceGraphError(
                f"trusted verifier module attribute is unresolved: "
                f"{current.__name__}.{attribute}"
            )
        current = namespace[attribute]
    return current


def _builtin_callable_identity(value: object) -> Mapping[str, object]:
    module_name = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None) or getattr(value, "__name__", None)
    if not isinstance(module_name, str) or not module_name:
        raise EvidenceGraphError("trusted verifier references an unnamed builtin")
    if not isinstance(qualname, str) or not qualname:
        raise EvidenceGraphError("trusted verifier references an unqualified builtin")
    module = sys.modules.get(module_name)
    if not isinstance(module, ModuleType):
        raise EvidenceGraphError(
            f"trusted verifier builtin module {module_name!r} is not loaded"
        )
    return {
        "kind": "builtin_callable",
        "module": module_name,
        "qualname": qualname,
        "module_origin": _module_origin_identity(module),
    }


class _SemanticReferenceTable:
    """Assign traversal-stable IDs while retaining exact Python alias topology."""

    def __init__(self) -> None:
        self._objects: dict[int, tuple[object, str]] = {}

    def bind(self, value: object) -> tuple[str, bool]:
        identity = id(value)
        prior = self._objects.get(identity)
        if prior is not None:
            prior_value, reference = prior
            if prior_value is not value:  # pragma: no cover - strong ref forbids reuse
                raise EvidenceGraphError(
                    "trusted verifier semantic reference identity was reused"
                )
            return reference, True
        reference = f"semantic-ref-{len(self._objects):08d}"
        self._objects[identity] = (value, reference)
        return reference, False


def _semantic_order_token(value: object, *, field: str) -> bytes:
    """Canonical pre-traversal key for unordered containers and mappings."""

    try:
        identity = _code_constant_identity(value)
    except EvidenceGraphError as exc:
        raise EvidenceGraphError(
            f"trusted verifier {field} is not deterministically orderable"
        ) from exc
    return _canonical_bytes(identity)


def _semantic_value_identity(
    value: object,
    *,
    references: _SemanticReferenceTable,
    active_values: set[int],
    active_callables: list[int],
    module_accesses: tuple[tuple[str, ...], ...] = (),
    depth: int = 0,
) -> object:
    reference, already_bound = references.bind(value)
    if already_bound:
        return {"kind": "semantic_backref", "ref": reference}
    payload = _semantic_value_payload(
        value,
        references=references,
        active_values=active_values,
        active_callables=active_callables,
        module_accesses=module_accesses,
        depth=depth,
    )
    return {
        "kind": "semantic_definition",
        "ref": reference,
        "payload": payload,
    }


def _semantic_value_payload(
    value: object,
    *,
    references: _SemanticReferenceTable,
    active_values: set[int],
    active_callables: list[int],
    module_accesses: tuple[tuple[str, ...], ...] = (),
    depth: int = 0,
) -> object:
    if depth > 32:
        raise EvidenceGraphError("trusted verifier state exceeds maximum depth")
    if isinstance(value, Enum):
        return {
            "kind": "enum",
            "enum_type": _type_identity(type(value)),
            "value": _semantic_value_identity(
                value.value,
                references=references,
                active_values=active_values,
                active_callables=active_callables,
                depth=depth + 1,
            ),
        }
    if (
        value is None
        or value is Ellipsis
        or type(value)
        in {
            str,
            bytes,
            bool,
            int,
            float,
            complex,
            CodeType,
        }
    ):
        return _code_constant_identity(value)
    if isinstance(value, ModuleType):
        attributes = []
        for path in sorted(set(module_accesses)):
            attributes.append(
                {
                    "path": list(path),
                    "value": _semantic_value_identity(
                        _module_attribute_value(value, path),
                        references=references,
                        active_values=active_values,
                        active_callables=active_callables,
                        depth=depth + 1,
                    ),
                }
            )
        return {
            "kind": "module",
            "origin": _module_origin_identity(value),
            "referenced_attributes": attributes,
        }
    if inspect.isfunction(value):
        return _python_function_identity(
            value,
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
    if inspect.ismethod(value):
        return {
            "kind": "bound_method",
            "function": _semantic_value_identity(
                value.__func__,
                references=references,
                active_values=active_values,
                active_callables=active_callables,
                depth=depth + 1,
            ),
            "bound_self": _semantic_value_identity(
                value.__self__,
                references=references,
                active_values=active_values,
                active_callables=active_callables,
                depth=depth + 1,
            ),
        }
    if inspect.isbuiltin(value) or inspect.ismethoddescriptor(value):
        return _builtin_callable_identity(value)
    if isinstance(value, type):
        return _type_identity(value)
    if type(value) is dict or isinstance(value, MappingProxyType):
        identity = id(value)
        if identity in active_values:
            raise EvidenceGraphError("trusted verifier state contains a cycle")
        active_values.add(identity)
        try:
            items = []
            ordered_items = sorted(
                value.items(),
                key=lambda row: _semantic_order_token(row[0], field="mapping key"),
            )
            for key, nested in ordered_items:
                key_identity = _semantic_value_identity(
                    key,
                    references=references,
                    active_values=active_values,
                    active_callables=active_callables,
                    depth=depth + 1,
                )
                items.append(
                    {
                        "key": key_identity,
                        "value": _semantic_value_identity(
                            nested,
                            references=references,
                            active_values=active_values,
                            active_callables=active_callables,
                            depth=depth + 1,
                        ),
                    }
                )
            return {"kind": "mapping", "items": sorted(items, key=_canonical_bytes)}
        finally:
            active_values.remove(identity)
    if type(value) in {list, tuple, set, frozenset}:
        identity = id(value)
        if identity in active_values:
            raise EvidenceGraphError("trusted verifier state contains a cycle")
        active_values.add(identity)
        try:
            raw_items = list(value)
            if type(value) in {set, frozenset}:
                raw_items.sort(
                    key=lambda item: _semantic_order_token(item, field="set member")
                )
            items = [
                _semantic_value_identity(
                    item,
                    references=references,
                    active_values=active_values,
                    active_callables=active_callables,
                    depth=depth + 1,
                )
                for item in raw_items
            ]
            return {
                "kind": type(value).__name__,
                "items": items,
            }
        finally:
            active_values.remove(identity)
    raise EvidenceGraphError(
        "trusted verifier contains unverifiable state of type "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _python_function_identity(
    callback: Callable[..., object],
    *,
    references: _SemanticReferenceTable,
    active_values: set[int],
    active_callables: list[int],
    depth: int,
) -> Mapping[str, object]:
    identity = id(callback)
    if identity in active_callables:
        return {"kind": "recursive_callable", "index": active_callables.index(identity)}
    code = getattr(callback, "__code__", None)
    if not isinstance(code, CodeType):
        raise EvidenceGraphError("trusted verifier must expose verifiable Python code")
    active_callables.append(identity)
    try:
        source = inspect.getsource(callback).encode("utf-8")
    except (OSError, TypeError):
        source = b""
    try:
        code_state = _semantic_value_identity(
            code,
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        module_state = _semantic_value_identity(
            getattr(callback, "__module__", None),
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        name_state = _semantic_value_identity(
            getattr(callback, "__name__", None),
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        qualname_state = _semantic_value_identity(
            getattr(callback, "__qualname__", None),
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        doc_state = _semantic_value_identity(
            getattr(callback, "__doc__", None),
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        closure = getattr(callback, "__closure__", None) or ()
        if len(closure) != len(code.co_freevars):
            raise EvidenceGraphError("trusted verifier closure layout is inconsistent")
        closure_values = []
        for name, cell in zip(code.co_freevars, closure, strict=True):
            try:
                cell_value = cell.cell_contents
            except ValueError:
                value_identity: object = {"kind": "empty_cell"}
            else:
                value_identity = _semantic_value_identity(
                    cell_value,
                    references=references,
                    active_values=active_values,
                    active_callables=active_callables,
                    depth=depth + 1,
                )
            closure_values.append({"name": name, "value": value_identity})

        accesses = _referenced_global_accesses(code)
        globals_mapping = getattr(callback, "__globals__", None)
        builtins_mapping = getattr(callback, "__builtins__", None)
        if not isinstance(globals_mapping, Mapping) or not isinstance(
            builtins_mapping, Mapping
        ):
            raise EvidenceGraphError(
                "trusted verifier global namespaces are not verifiable mappings"
            )
        global_values = []
        for name, attribute_paths in accesses.items():
            if name in globals_mapping:
                scope = "global"
                value = globals_mapping[name]
            elif name in builtins_mapping:
                scope = "builtin"
                value = builtins_mapping[name]
            else:
                raise EvidenceGraphError(
                    f"trusted verifier referenced global {name!r} is unresolved"
                )
            if scope == "builtin" and name in {
                "__import__",
                "compile",
                "eval",
                "exec",
                "globals",
                "locals",
                "vars",
            }:
                raise EvidenceGraphError(
                    f"trusted verifier uses unverifiable dynamic builtin {name!r}"
                )
            global_values.append(
                {
                    "name": name,
                    "scope": scope,
                    "value": _semantic_value_identity(
                        value,
                        references=references,
                        active_values=active_values,
                        active_callables=active_callables,
                        module_accesses=attribute_paths,
                        depth=depth + 1,
                    ),
                }
            )

        defaults = _semantic_value_identity(
            getattr(callback, "__defaults__", None),
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        kwdefaults = _semantic_value_identity(
            getattr(callback, "__kwdefaults__", None),
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        attributes = getattr(callback, "__dict__", None)
        if not isinstance(attributes, Mapping):
            raise EvidenceGraphError("trusted verifier attributes are not verifiable")
        if not all(isinstance(key, str) and key for key in attributes):
            raise EvidenceGraphError(
                "trusted verifier attribute names must be non-empty strings"
            )
        attribute_identity = _semantic_value_identity(
            attributes,
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        annotation_identity = _semantic_value_identity(
            getattr(callback, "__annotations__", None),
            references=references,
            active_values=active_values,
            active_callables=active_callables,
            depth=depth + 1,
        )
        return {
            "schema_version": "authority_verifier_python_semantics_v1",
            "module": module_state,
            "name": name_state,
            "qualname": qualname_state,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "code": code_state,
            "defaults": defaults,
            "kwdefaults": kwdefaults,
            "closure": closure_values,
            "referenced_globals": global_values,
            "attributes": attribute_identity,
            "annotations": annotation_identity,
            "doc": doc_state,
        }
    finally:
        active_callables.pop()


def _verifier_implementation_ref(callback: Callable[..., object]) -> str:
    if not (inspect.isfunction(callback) or inspect.ismethod(callback)):
        raise EvidenceGraphError(
            "trusted verifier must be a Python function or bound Python method"
        )
    explicit = getattr(callback, "__htt_verifier_ref__", None)
    declared_ref = (
        None
        if explicit is None
        else _sha256(explicit, "declared verifier implementation ref")
    )
    semantic_identity = _semantic_value_identity(
        callback,
        references=_SemanticReferenceTable(),
        active_values=set(),
        active_callables=[],
    )
    return _content_address(
        {
            "schema_version": "authority_verifier_implementation_v2",
            "declared_ref": declared_ref,
            "semantic_identity": semantic_identity,
        }
    )


@dataclass(frozen=True)
class EvidenceAxes:
    """The process, evidence, and science axes for one graph node."""

    process_result: ProcessResult | str
    evidence_status: EvidenceStatus | str
    scientific_status: ScientificStatus | str

    def __post_init__(self) -> None:
        try:
            process = ProcessResult(_enum_value(self.process_result))
        except ValueError as exc:
            raise EvidenceGraphError(
                f"unknown process_result {self.process_result!r}"
            ) from exc
        try:
            evidence = EvidenceStatus(_enum_value(self.evidence_status))
        except ValueError as exc:
            raise EvidenceGraphError(
                f"unknown evidence_status {self.evidence_status!r}"
            ) from exc
        try:
            science = ScientificStatus(_enum_value(self.scientific_status))
        except ValueError as exc:
            raise EvidenceGraphError(
                f"unknown scientific_status {self.scientific_status!r}"
            ) from exc

        object.__setattr__(self, "process_result", process)
        object.__setattr__(self, "evidence_status", evidence)
        object.__setattr__(self, "scientific_status", science)

    def to_record(self) -> dict[str, str]:
        return {
            "process_result": self.process_result.value,
            "evidence_status": self.evidence_status.value,
            "scientific_status": self.scientific_status.value,
        }

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "EvidenceAxes":
        _strict_keys(
            value,
            required={"process_result", "evidence_status", "scientific_status"},
            field="evidence axes",
        )
        return cls(
            process_result=value["process_result"],
            evidence_status=value["evidence_status"],
            scientific_status=value["scientific_status"],
        )


@dataclass(frozen=True)
class TestCaseResult:
    __test__ = False

    test_id: str
    outcome: TestOutcome | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "test_id", _exact_text(self.test_id, "test_id"))
        try:
            outcome = TestOutcome(_enum_value(self.outcome))
        except ValueError as exc:
            raise EvidenceGraphError(f"unknown test outcome {self.outcome!r}") from exc
        object.__setattr__(self, "outcome", outcome)

    def to_record(self) -> dict[str, str]:
        return {"test_id": self.test_id, "outcome": self.outcome.value}


@dataclass(frozen=True)
class TestExecution:
    """Identity-bearing test run with derived authority and reconciled counts."""

    __test__ = False

    framework: str
    selector: str
    command: Sequence[str]
    collected_test_ids: Sequence[str]
    executed_test_ids: Sequence[str]
    results: Sequence[TestCaseResult]
    reported_collected_count: int
    reported_executed_count: int
    source_receipt_sha256: str | None = None
    environment_ref: str | None = None

    def __post_init__(self) -> None:
        framework = _exact_text(self.framework, "framework")
        selector = _exact_text(self.selector, "selector")
        if isinstance(self.command, (str, bytes)) or not isinstance(
            self.command, Sequence
        ):
            raise EvidenceGraphError("command must be a sequence of exact arguments")
        command = tuple(_exact_text(item, "command argument") for item in self.command)
        if not command:
            raise EvidenceGraphError("command must not be empty")
        if isinstance(self.collected_test_ids, (str, bytes)) or not isinstance(
            self.collected_test_ids, Sequence
        ):
            raise EvidenceGraphError("collected_test_ids must be a sequence")
        collected = tuple(
            sorted(
                _exact_text(item, "collected test id")
                for item in self.collected_test_ids
            )
        )
        if len(collected) != len(set(collected)):
            raise EvidenceGraphError("collected_test_ids contains duplicates")
        if isinstance(self.executed_test_ids, (str, bytes)) or not isinstance(
            self.executed_test_ids, Sequence
        ):
            raise EvidenceGraphError("executed_test_ids must be a sequence")
        executed = tuple(
            sorted(
                _exact_text(item, "executed test id") for item in self.executed_test_ids
            )
        )
        if len(executed) != len(set(executed)):
            raise EvidenceGraphError("executed_test_ids contains duplicates")
        if not set(executed) <= set(collected):
            raise EvidenceGraphError(
                "executed_test_ids must be an exact subset of collected_test_ids"
            )
        if isinstance(self.results, (str, bytes)) or not isinstance(
            self.results, Sequence
        ):
            raise EvidenceGraphError("results must be a sequence")
        raw_results = tuple(self.results)
        if not all(isinstance(row, TestCaseResult) for row in raw_results):
            raise EvidenceGraphError("results must contain TestCaseResult values")
        results = tuple(sorted(raw_results, key=lambda row: row.test_id))
        result_ids = tuple(row.test_id for row in results)
        if len(result_ids) != len(set(result_ids)):
            raise EvidenceGraphError("test results contain duplicate test identities")
        if set(result_ids) != set(collected):
            missing = sorted(set(collected) - set(result_ids))
            extra = sorted(set(result_ids) - set(collected))
            raise EvidenceGraphError(
                "test results must reconcile exactly with collected identities; "
                f"missing={missing}, extra={extra}"
            )
        for row in results:
            if (
                row.test_id not in set(executed)
                and row.outcome is not TestOutcome.SKIPPED
            ):
                raise EvidenceGraphError(
                    "a collected but non-executed test must have SKIPPED outcome"
                )
        collected_count = len(collected)
        executed_count = len(executed)
        for field, reported, derived in (
            (
                "reported_collected_count",
                self.reported_collected_count,
                collected_count,
            ),
            ("reported_executed_count", self.reported_executed_count, executed_count),
        ):
            if not isinstance(reported, int) or isinstance(reported, bool):
                raise EvidenceGraphError(f"{field} must be an integer")
            if reported != derived:
                raise EvidenceGraphError(
                    f"{field}={reported} does not match identity-derived count {derived}"
                )
        source_receipt = (
            None
            if self.source_receipt_sha256 is None
            else _sha256(self.source_receipt_sha256, "source_receipt_sha256")
        )
        environment_ref = (
            None
            if self.environment_ref is None
            else _sha256(self.environment_ref, "environment_ref")
        )
        object.__setattr__(self, "framework", framework)
        object.__setattr__(self, "selector", selector)
        object.__setattr__(self, "command", command)
        object.__setattr__(self, "collected_test_ids", collected)
        object.__setattr__(self, "executed_test_ids", executed)
        object.__setattr__(self, "results", results)
        object.__setattr__(self, "source_receipt_sha256", source_receipt)
        object.__setattr__(self, "environment_ref", environment_ref)

    @property
    def collected_count(self) -> int:
        return len(self.collected_test_ids)

    @property
    def executed_count(self) -> int:
        return len(self.executed_test_ids)

    @property
    def axes(self) -> tuple[ProcessResult, EvidenceStatus]:
        outcomes = {row.outcome for row in self.results}
        if self.collected_count == 0:
            return ProcessResult.NOT_RUN, EvidenceStatus.MISSING
        if self.executed_count == 0:
            return ProcessResult.NOT_RUN, EvidenceStatus.SKIPPED
        if TestOutcome.FAILED in outcomes:
            return ProcessResult.FAIL, EvidenceStatus.INVALID
        if TestOutcome.XPASS in outcomes:
            return ProcessResult.FAIL, EvidenceStatus.INVALID
        if TestOutcome.XFAIL in outcomes:
            return ProcessResult.FAIL, EvidenceStatus.XFAIL
        if TestOutcome.SKIPPED in outcomes:
            return ProcessResult.NOT_RUN, EvidenceStatus.SKIPPED
        if set(self.executed_test_ids) != set(self.collected_test_ids):
            return ProcessResult.NOT_RUN, EvidenceStatus.SKIPPED
        return ProcessResult.PASS, EvidenceStatus.PRESENT

    @property
    def is_authoritative(self) -> bool:
        return self.axes == (ProcessResult.PASS, EvidenceStatus.PRESENT)

    def payload(self) -> dict[str, object]:
        return {
            "framework": self.framework,
            "selector": self.selector,
            "command": list(self.command),
            "collected_test_ids": list(self.collected_test_ids),
            "executed_test_ids": list(self.executed_test_ids),
            "results": [row.to_record() for row in self.results],
            "reported_collected_count": self.reported_collected_count,
            "reported_executed_count": self.reported_executed_count,
            "source_receipt_sha256": self.source_receipt_sha256,
            "environment_ref": self.environment_ref,
        }

    @property
    def execution_ref(self) -> str:
        return _content_address(
            {
                "schema_version": "test_execution_v1",
                "canonicalization": CANONICALIZATION,
                **self.payload(),
            }
        )

    def to_record(self) -> dict[str, object]:
        return {**self.payload(), "execution_ref": self.execution_ref}

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "TestExecution":
        required = {
            "framework",
            "selector",
            "command",
            "collected_test_ids",
            "executed_test_ids",
            "results",
            "reported_collected_count",
            "reported_executed_count",
            "source_receipt_sha256",
            "environment_ref",
            "execution_ref",
        }
        _strict_keys(value, required=required, field="test execution")
        raw_results = value["results"]
        if not isinstance(raw_results, Sequence) or isinstance(
            raw_results, (str, bytes)
        ):
            raise EvidenceGraphError("test execution results must be a sequence")
        results: list[TestCaseResult] = []
        for row in raw_results:
            if not isinstance(row, Mapping):
                raise EvidenceGraphError("test execution result must be a mapping")
            _strict_keys(row, required={"test_id", "outcome"}, field="test result")
            results.append(TestCaseResult(str(row["test_id"]), row["outcome"]))
        execution = cls(
            framework=str(value["framework"]),
            selector=str(value["selector"]),
            command=value["command"],  # type: ignore[arg-type]
            collected_test_ids=value["collected_test_ids"],  # type: ignore[arg-type]
            executed_test_ids=value["executed_test_ids"],  # type: ignore[arg-type]
            results=results,
            reported_collected_count=value["reported_collected_count"],  # type: ignore[arg-type]
            reported_executed_count=value["reported_executed_count"],  # type: ignore[arg-type]
            source_receipt_sha256=(
                None
                if value["source_receipt_sha256"] is None
                else str(value["source_receipt_sha256"])
            ),
            environment_ref=(
                None
                if value["environment_ref"] is None
                else str(value["environment_ref"])
            ),
        )
        expected = _sha256(value["execution_ref"], "execution_ref")
        if execution.execution_ref != expected:
            raise EvidenceGraphError("test execution_ref does not match its payload")
        return execution

    @classmethod
    def from_pytest_evidence(cls, value: Mapping[str, object]) -> "TestExecution":
        """Parse the repo pytest plugin receipt and recompute every identity/count.

        The plugin receipt is process evidence only.  This adapter deliberately
        ignores its caller-facing ``process_result`` when deriving authority.
        """

        required = {
            "schema_version",
            "runner",
            "runner_version",
            "python_version",
            "python_implementation",
            "platform",
            "rootdir",
            "selector_argv",
            "normalized_invocation_argv",
            "selector_hash",
            "selector_inputs",
            "environment_contract",
            "collected_node_ids",
            "collected_node_ids_hash",
            "executed_node_ids",
            "executed_node_ids_hash",
            "passed_node_ids",
            "failed_node_ids",
            "skipped_node_ids",
            "xfailed_node_ids",
            "xpassed_node_ids",
            "counts",
            "exit_status",
            "process_result",
            "caveats",
            "content_sha256",
        }
        _strict_keys(value, required=required, field="pytest execution evidence")
        if value["schema_version"] != "common.pytest_execution_evidence.v2":
            raise EvidenceGraphError("unsupported pytest execution evidence schema")
        if value["runner"] != "pytest":
            raise EvidenceGraphError("pytest execution evidence runner must be pytest")
        environment, environment_ref = _pytest_environment_contract(value)
        interpreter = environment["interpreter"]
        pytest_environment = environment["pytest"]
        assert isinstance(interpreter, Mapping)
        assert isinstance(pytest_environment, Mapping)
        if value["python_version"] != interpreter["version"]:
            raise EvidenceGraphError(
                "pytest python_version mismatches environment contract"
            )
        if value["python_implementation"] != interpreter["implementation"]:
            raise EvidenceGraphError(
                "pytest python_implementation mismatches environment contract"
            )
        if value["runner_version"] != pytest_environment["version"]:
            raise EvidenceGraphError(
                "pytest runner_version mismatches environment contract"
            )
        if value["rootdir"] != pytest_environment["rootdir"]:
            raise EvidenceGraphError("pytest rootdir mismatches environment contract")
        unsigned = dict(value)
        expected_content = _sha256(unsigned.pop("content_sha256"), "content_sha256")
        if _content_address(unsigned) != expected_content:
            raise EvidenceGraphError(
                "pytest execution evidence content_sha256 does not match payload"
            )

        def text_sequence(field: str) -> tuple[str, ...]:
            raw = value[field]
            if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
                raise EvidenceGraphError(f"pytest evidence {field} must be a sequence")
            return tuple(_exact_text(item, field) for item in raw)

        selectors = text_sequence("selector_argv")
        invocation = text_sequence("normalized_invocation_argv")
        collected = text_sequence("collected_node_ids")
        executed = text_sequence("executed_node_ids")
        if len(collected) != len(set(collected)):
            raise EvidenceGraphError("pytest collected_node_ids contains duplicates")
        if len(executed) != len(set(executed)):
            raise EvidenceGraphError("pytest executed_node_ids contains duplicates")
        if not set(executed) <= set(collected):
            raise EvidenceGraphError(
                "pytest executed_node_ids must be a subset of collected_node_ids"
            )
        if _content_address(list(selectors)) != _sha256(
            value["selector_hash"], "selector_hash"
        ):
            raise EvidenceGraphError(
                "pytest selector_hash does not match selector_argv"
            )
        if _content_address(list(collected)) != _sha256(
            value["collected_node_ids_hash"], "collected_node_ids_hash"
        ):
            raise EvidenceGraphError("pytest collected_node_ids_hash mismatch")
        if _content_address(list(executed)) != _sha256(
            value["executed_node_ids_hash"], "executed_node_ids_hash"
        ):
            raise EvidenceGraphError("pytest executed_node_ids_hash mismatch")

        outcome_fields = {
            "passed_node_ids": TestOutcome.PASSED,
            "failed_node_ids": TestOutcome.FAILED,
            "skipped_node_ids": TestOutcome.SKIPPED,
            "xfailed_node_ids": TestOutcome.XFAIL,
            "xpassed_node_ids": TestOutcome.XPASS,
        }
        outcomes: dict[str, TestOutcome] = {}
        outcome_rows: dict[str, tuple[str, ...]] = {}
        for field, outcome in outcome_fields.items():
            ids = text_sequence(field)
            outcome_rows[field] = ids
            for test_id in ids:
                if test_id in outcomes:
                    raise EvidenceGraphError(
                        "pytest outcome identity occurs in multiple buckets"
                    )
                outcomes[test_id] = outcome
        if set(outcomes) != set(collected):
            raise EvidenceGraphError(
                "pytest outcome buckets must cover collected identities exactly"
            )
        counts = value["counts"]
        if not isinstance(counts, Mapping):
            raise EvidenceGraphError("pytest evidence counts must be a mapping")
        _strict_keys(
            counts,
            required={
                "collected",
                "executed",
                "passed",
                "failed",
                "skipped",
                "xfailed",
                "xpassed",
            },
            field="pytest evidence counts",
        )
        derived_counts = {
            "collected": len(collected),
            "executed": len(executed),
            "passed": len(outcome_rows["passed_node_ids"]),
            "failed": len(outcome_rows["failed_node_ids"]),
            "skipped": len(outcome_rows["skipped_node_ids"]),
            "xfailed": len(outcome_rows["xfailed_node_ids"]),
            "xpassed": len(outcome_rows["xpassed_node_ids"]),
        }
        for field, derived in derived_counts.items():
            reported = counts[field]
            if not isinstance(reported, int) or isinstance(reported, bool):
                raise EvidenceGraphError(f"pytest count {field} must be an integer")
            if reported != derived:
                raise EvidenceGraphError(
                    f"pytest count {field}={reported} does not match {derived}"
                )
        exit_status = value["exit_status"]
        if not isinstance(exit_status, int) or isinstance(exit_status, bool):
            raise EvidenceGraphError("pytest exit_status must be an integer")
        expected_process = (
            "passed"
            if exit_status == 0 and bool(outcome_rows["passed_node_ids"])
            else "failed"
        )
        if value["process_result"] != expected_process:
            raise EvidenceGraphError(
                "pytest process_result does not match exit_status and outcomes"
            )
        if exit_status != 0:
            raise EvidenceGraphError(
                "nonzero pytest exit_status cannot authorize test evidence"
            )
        selector = json.dumps(
            list(selectors), separators=(",", ":"), ensure_ascii=False
        )
        return cls(
            framework=f"pytest:{_exact_text(value['runner_version'], 'runner_version')}",
            selector=selector,
            command=invocation,
            collected_test_ids=collected,
            executed_test_ids=executed,
            results=tuple(
                TestCaseResult(test_id, outcomes[test_id])
                for test_id in sorted(outcomes)
            ),
            reported_collected_count=derived_counts["collected"],
            reported_executed_count=derived_counts["executed"],
            source_receipt_sha256=expected_content,
            environment_ref=environment_ref,
        )


@dataclass(frozen=True)
class EvidenceNode:
    kind: EvidenceNodeKind | str
    label: str
    content_sha256: str
    axes: EvidenceAxes
    metadata: Mapping[str, object]
    test_execution: TestExecution | None = None

    def __post_init__(self) -> None:
        try:
            kind = EvidenceNodeKind(_enum_value(self.kind))
        except ValueError as exc:
            raise EvidenceGraphError(
                f"unknown evidence node kind {self.kind!r}"
            ) from exc
        label = _exact_text(self.label, "node label")
        digest = _sha256(self.content_sha256, "node content_sha256")
        if not isinstance(self.axes, EvidenceAxes):
            raise EvidenceGraphError("node axes must be EvidenceAxes")
        if not isinstance(self.metadata, Mapping):
            raise EvidenceGraphError("node metadata must be a mapping")
        _reject_readiness_fields(self.metadata)
        metadata = _freeze_json(self.metadata)
        if kind is EvidenceNodeKind.TEST:
            if not isinstance(self.test_execution, TestExecution):
                raise EvidenceGraphError("test nodes require a TestExecution record")
            if digest != self.test_execution.execution_ref:
                raise EvidenceGraphError(
                    "test node content_sha256 must equal TestExecution.execution_ref"
                )
            process, evidence = self.test_execution.axes
            if (
                self.axes.process_result is not process
                or self.axes.evidence_status is not evidence
            ):
                raise EvidenceGraphError(
                    "test node axes do not match identity-derived execution outcome"
                )
        elif self.test_execution is not None:
            raise EvidenceGraphError("only test nodes may carry TestExecution")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "content_sha256", digest)
        object.__setattr__(self, "metadata", metadata)

    def payload(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "label": self.label,
            "content_sha256": self.content_sha256,
            "axes": self.axes.to_record(),
            "metadata": _jsonable(self.metadata),
            "test_execution": (
                None if self.test_execution is None else self.test_execution.to_record()
            ),
        }

    @property
    def node_ref(self) -> str:
        return _content_address(
            {
                "schema_version": "evidence_node_v1",
                "canonicalization": CANONICALIZATION,
                **self.payload(),
            }
        )

    def to_record(self) -> dict[str, object]:
        return {**self.payload(), "node_ref": self.node_ref}

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "EvidenceNode":
        required = {
            "kind",
            "label",
            "content_sha256",
            "axes",
            "metadata",
            "test_execution",
            "node_ref",
        }
        _strict_keys(value, required=required, field="evidence node")
        axes = value["axes"]
        metadata = value["metadata"]
        if not isinstance(axes, Mapping) or not isinstance(metadata, Mapping):
            raise EvidenceGraphError("node axes and metadata must be mappings")
        raw_execution = value["test_execution"]
        if raw_execution is None:
            execution = None
        elif isinstance(raw_execution, Mapping):
            execution = TestExecution.from_record(raw_execution)
        else:
            raise EvidenceGraphError("test_execution must be a mapping or null")
        node = cls(
            kind=value["kind"],
            label=str(value["label"]),
            content_sha256=str(value["content_sha256"]),
            axes=EvidenceAxes.from_record(axes),
            metadata=metadata,
            test_execution=execution,
        )
        expected = _sha256(value["node_ref"], "node_ref")
        if node.node_ref != expected:
            raise EvidenceGraphError("node_ref does not match node payload")
        return node


def _lifecycle_edge_metadata(
    kind: EvidenceEdgeKind,
    metadata: Mapping[str, object],
) -> Mapping[str, object]:
    """Normalize the exact capability-scoped lifecycle-edge payload."""

    required = {"affected_capabilities", "reason_ref"}
    if kind is EvidenceEdgeKind.SUPERSEDED_BY:
        required.add("changed_dimensions")
    _strict_keys(metadata, required=required, field=f"{kind.value} metadata")
    raw_capabilities = metadata["affected_capabilities"]
    if isinstance(raw_capabilities, (str, bytes)) or not isinstance(
        raw_capabilities, Sequence
    ):
        raise EvidenceGraphError(
            "lifecycle affected_capabilities must be a sequence"
        )
    try:
        capabilities = tuple(
            sorted(
                {ClaimCapability(_enum_value(value)) for value in raw_capabilities},
                key=lambda item: item.value,
            )
        )
    except ValueError as exc:
        raise EvidenceGraphError(
            "lifecycle edge contains an unknown affected capability"
        ) from exc
    if not capabilities or len(capabilities) != len(raw_capabilities):
        raise EvidenceGraphError(
            "lifecycle affected_capabilities must be non-empty and unique"
        )
    normalized: dict[str, object] = {
        "affected_capabilities": [item.value for item in capabilities],
        "reason_ref": _sha256(metadata["reason_ref"], "lifecycle reason_ref"),
    }
    if kind is EvidenceEdgeKind.SUPERSEDED_BY:
        raw_dimensions = metadata["changed_dimensions"]
        if isinstance(raw_dimensions, (str, bytes)) or not isinstance(
            raw_dimensions, Sequence
        ):
            raise EvidenceGraphError("changed_dimensions must be a sequence")
        try:
            dimensions = tuple(
                sorted(
                    {IdentityDimension(_enum_value(value)) for value in raw_dimensions},
                    key=lambda item: item.value,
                )
            )
        except ValueError as exc:
            raise EvidenceGraphError(
                "SUPERSEDED_BY contains an unknown identity dimension"
            ) from exc
        if not dimensions or len(dimensions) != len(raw_dimensions):
            raise EvidenceGraphError(
                "SUPERSEDED_BY changed_dimensions must be non-empty and unique"
            )
        normalized["changed_dimensions"] = [item.value for item in dimensions]
    return MappingProxyType(normalized)


@dataclass(frozen=True)
class EvidenceEdge:
    kind: EvidenceEdgeKind | str
    source_ref: str
    target_ref: str
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        try:
            kind = EvidenceEdgeKind(_enum_value(self.kind))
        except ValueError as exc:
            raise EvidenceGraphError(
                f"unknown evidence edge kind {self.kind!r}"
            ) from exc
        source = _sha256(self.source_ref, "edge source_ref")
        target = _sha256(self.target_ref, "edge target_ref")
        if source == target:
            raise EvidenceGraphError("self-referential evidence edge is forbidden")
        if not isinstance(self.metadata, Mapping):
            raise EvidenceGraphError("edge metadata must be a mapping")
        _reject_readiness_fields(self.metadata)
        metadata = (
            _lifecycle_edge_metadata(kind, self.metadata)
            if kind in _LIFECYCLE_EDGE_KINDS
            else self.metadata
        )
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "source_ref", source)
        object.__setattr__(self, "target_ref", target)
        object.__setattr__(self, "metadata", _freeze_json(metadata))

    def payload(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "source_ref": self.source_ref,
            "target_ref": self.target_ref,
            "metadata": _jsonable(self.metadata),
        }

    @property
    def edge_ref(self) -> str:
        return _content_address(
            {
                "schema_version": "evidence_edge_v1",
                "canonicalization": CANONICALIZATION,
                **self.payload(),
            }
        )

    def to_record(self) -> dict[str, object]:
        return {**self.payload(), "edge_ref": self.edge_ref}

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "EvidenceEdge":
        required = {"kind", "source_ref", "target_ref", "metadata", "edge_ref"}
        _strict_keys(value, required=required, field="evidence edge")
        metadata = value["metadata"]
        if not isinstance(metadata, Mapping):
            raise EvidenceGraphError("edge metadata must be a mapping")
        edge = cls(
            kind=value["kind"],
            source_ref=str(value["source_ref"]),
            target_ref=str(value["target_ref"]),
            metadata=metadata,
        )
        expected = _sha256(value["edge_ref"], "edge_ref")
        if edge.edge_ref != expected:
            raise EvidenceGraphError("edge_ref does not match edge payload")
        return edge


@dataclass(frozen=True)
class ClaimClosure:
    claim_ref: str
    node_refs: tuple[str, ...]
    edge_refs: tuple[str, ...]
    missing_node_requirements: tuple[str, ...]
    missing_edge_kinds: tuple[str, ...]
    process_result: ProcessResult
    evidence_status: EvidenceStatus
    evidence_statuses: tuple[EvidenceStatus, ...]
    scientific_status: ScientificStatus
    scientific_statuses: tuple[ScientificStatus, ...]
    mechanics_closed: bool
    package_eligible: bool
    claim_release_eligible: bool

    def payload(self) -> dict[str, object]:
        return {
            "claim_ref": self.claim_ref,
            "node_refs": list(self.node_refs),
            "edge_refs": list(self.edge_refs),
            "missing_node_requirements": list(self.missing_node_requirements),
            "missing_edge_kinds": list(self.missing_edge_kinds),
            "process_result": self.process_result.value,
            "evidence_status": self.evidence_status.value,
            "evidence_statuses": [status.value for status in self.evidence_statuses],
            "scientific_status": self.scientific_status.value,
            "scientific_statuses": [
                status.value for status in self.scientific_statuses
            ],
            "mechanics_closed": self.mechanics_closed,
            "package_eligible": self.package_eligible,
            "claim_release_eligible": self.claim_release_eligible,
        }

    @property
    def closure_ref(self) -> str:
        return _content_address(
            {
                "schema_version": "claim_closure_v2",
                "canonicalization": CANONICALIZATION,
                **self.payload(),
            }
        )

    def to_record(self) -> dict[str, object]:
        return {**self.payload(), "closure_ref": self.closure_ref}

    def require_package_eligible(self) -> None:
        if set(self.scientific_statuses) & _BLOCKING_SCIENTIFIC_STATUSES:
            raise EvidenceGraphError(
                "blocked/falsified/abandoned science cannot enter a green package"
            )
        if not self.mechanics_closed:
            raise EvidenceGraphError("claim evidence mechanics are not closed")
        if not self.package_eligible:
            raise EvidenceGraphError(
                "scientific status is not consumable by a release package"
            )

    def require_claim_release_eligible(self) -> None:
        if not self.claim_release_eligible:
            raise EvidenceGraphError(
                "claim release requires closed mechanics and an independently "
                "adjudicated positive terminal scientific status"
            )


@dataclass(frozen=True)
class EvidenceGraph:
    nodes: Sequence[EvidenceNode]
    edges: Sequence[EvidenceEdge]

    def __post_init__(self) -> None:
        if isinstance(self.nodes, (str, bytes)) or not isinstance(self.nodes, Sequence):
            raise EvidenceGraphError("nodes must be a sequence")
        if isinstance(self.edges, (str, bytes)) or not isinstance(self.edges, Sequence):
            raise EvidenceGraphError("edges must be a sequence")
        raw_nodes = tuple(self.nodes)
        raw_edges = tuple(self.edges)
        if not raw_nodes or not all(
            isinstance(node, EvidenceNode) for node in raw_nodes
        ):
            raise EvidenceGraphError("graph requires EvidenceNode values")
        if not all(isinstance(edge, EvidenceEdge) for edge in raw_edges):
            raise EvidenceGraphError("graph edges must be EvidenceEdge values")
        nodes = tuple(sorted(raw_nodes, key=lambda node: node.node_ref))
        edges = tuple(sorted(raw_edges, key=lambda edge: edge.edge_ref))
        node_refs = tuple(node.node_ref for node in nodes)
        edge_refs = tuple(edge.edge_ref for edge in edges)
        if len(node_refs) != len(set(node_refs)):
            raise EvidenceGraphError("graph contains duplicate node refs")
        if len(edge_refs) != len(set(edge_refs)):
            raise EvidenceGraphError("graph contains duplicate edge refs")
        labels = tuple((node.kind, node.label) for node in nodes)
        if len(labels) != len(set(labels)):
            raise EvidenceGraphError("graph contains duplicate kind/label identities")
        by_ref = {node.node_ref: node for node in nodes}
        for edge in edges:
            if edge.source_ref not in by_ref or edge.target_ref not in by_ref:
                raise EvidenceGraphError("edge references a node outside the graph")
            endpoint = (by_ref[edge.source_ref].kind, by_ref[edge.target_ref].kind)
            if endpoint not in _ALLOWED_EDGE_ENDPOINTS[edge.kind]:
                raise EvidenceGraphError(
                    f"edge {edge.kind.value} has invalid endpoints "
                    f"{endpoint[0].value}->{endpoint[1].value}"
                )
        if not any(node.kind is EvidenceNodeKind.CLAIM for node in nodes):
            raise EvidenceGraphError("graph requires at least one claim node")
        _assert_acyclic(node_refs, edges)
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", edges)

    @property
    def graph_ref(self) -> str:
        return _content_address(
            {
                "schema_version": GRAPH_SCHEMA_VERSION,
                "canonicalization": CANONICALIZATION,
                "nodes": [node.to_record() for node in self.nodes],
                "edges": [edge.to_record() for edge in self.edges],
            }
        )

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": GRAPH_SCHEMA_VERSION,
            "canonicalization": CANONICALIZATION,
            "nodes": [node.to_record() for node in self.nodes],
            "edges": [edge.to_record() for edge in self.edges],
            "graph_ref": self.graph_ref,
        }

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "EvidenceGraph":
        required = {"schema_version", "canonicalization", "nodes", "edges", "graph_ref"}
        _strict_keys(value, required=required, field="evidence graph")
        if value["schema_version"] != GRAPH_SCHEMA_VERSION:
            raise EvidenceGraphError("unsupported evidence graph schema version")
        if value["canonicalization"] != CANONICALIZATION:
            raise EvidenceGraphError("unsupported evidence graph canonicalization")
        raw_nodes, raw_edges = value["nodes"], value["edges"]
        if (
            not isinstance(raw_nodes, Sequence)
            or isinstance(raw_nodes, (str, bytes))
            or not isinstance(raw_edges, Sequence)
            or isinstance(raw_edges, (str, bytes))
        ):
            raise EvidenceGraphError("graph nodes and edges must be sequences")
        nodes = [
            (
                EvidenceNode.from_record(row)
                if isinstance(row, Mapping)
                else _raise_mapping("node")
            )
            for row in raw_nodes
        ]
        edges = [
            (
                EvidenceEdge.from_record(row)
                if isinstance(row, Mapping)
                else _raise_mapping("edge")
            )
            for row in raw_edges
        ]
        graph = cls(nodes=nodes, edges=edges)
        expected = _sha256(value["graph_ref"], "graph_ref")
        if graph.graph_ref != expected:
            raise EvidenceGraphError("graph_ref does not match graph payload")
        return graph

    def closure(self, claim_ref: str) -> ClaimClosure:
        claim_ref = _sha256(claim_ref, "claim_ref")
        by_ref = {node.node_ref: node for node in self.nodes}
        claim = by_ref.get(claim_ref)
        if claim is None or claim.kind is not EvidenceNodeKind.CLAIM:
            raise EvidenceGraphError("claim_ref does not identify a graph claim node")
        outgoing: dict[str, list[EvidenceEdge]] = {ref: [] for ref in by_ref}
        for edge in self.edges:
            outgoing[edge.source_ref].append(edge)
        reachable = {claim_ref}
        frontier = [claim_ref]
        closure_edges: set[str] = set()
        while frontier:
            current = frontier.pop()
            for edge in outgoing[current]:
                # Supersession/invalidation lineage is governance metadata, not
                # evidence support for the claim closure being adjudicated.
                if edge.kind in _LIFECYCLE_EDGE_KINDS:
                    continue
                closure_edges.add(edge.edge_ref)
                if edge.target_ref not in reachable:
                    reachable.add(edge.target_ref)
                    frontier.append(edge.target_ref)
        selected = tuple(by_ref[ref] for ref in sorted(reachable))
        kinds = {node.kind for node in selected}
        required_singletons = (
            EvidenceNodeKind.CLAIM,
            EvidenceNodeKind.PRODUCER,
            EvidenceNodeKind.INPUT,
            EvidenceNodeKind.CONFIG,
            EvidenceNodeKind.ENVIRONMENT,
            EvidenceNodeKind.ARTIFACT,
            EvidenceNodeKind.CONSUMER,
        )
        missing_nodes = [
            kind.value for kind in required_singletons if kind not in kinds
        ]
        if not ({EvidenceNodeKind.TEST, EvidenceNodeKind.ORACLE} & kinds):
            missing_nodes.append("test_or_oracle")
        selected_edges = tuple(
            edge for edge in self.edges if edge.edge_ref in closure_edges
        )
        present_edge_kinds = {edge.kind for edge in selected_edges}
        required_edge_kinds = (
            EvidenceEdgeKind.PRODUCED_BY,
            EvidenceEdgeKind.USES_INPUT,
            EvidenceEdgeKind.USES_CONFIG,
            EvidenceEdgeKind.USES_ENVIRONMENT,
            EvidenceEdgeKind.CHECKED_BY,
            EvidenceEdgeKind.GENERATES,
            EvidenceEdgeKind.CONSUMED_BY,
        )
        missing_edges = [
            kind.value for kind in required_edge_kinds if kind not in present_edge_kinds
        ]
        # A bag of required edge kinds is not a claim evidence path.  Every
        # producer directly asserted by the claim must carry its own
        # input/config/environment/test-or-oracle chain, and that checked
        # evidence must generate an artifact consumed downstream.  Otherwise
        # an unrelated decoy branch could make the closure falsely green.
        direct_producers = tuple(
            edge.target_ref
            for edge in outgoing[claim_ref]
            if edge.kind is EvidenceEdgeKind.PRODUCED_BY
        )
        producer_requirements = (
            EvidenceEdgeKind.USES_INPUT,
            EvidenceEdgeKind.USES_CONFIG,
            EvidenceEdgeKind.USES_ENVIRONMENT,
            EvidenceEdgeKind.CHECKED_BY,
        )
        for producer_ref in direct_producers:
            producer = by_ref[producer_ref]
            producer_edges = outgoing[producer_ref]
            for required_kind in producer_requirements:
                if not any(edge.kind is required_kind for edge in producer_edges):
                    missing_edges.append(f"{producer.label}:{required_kind.value}")
            checked_refs = {
                edge.target_ref
                for edge in producer_edges
                if edge.kind is EvidenceEdgeKind.CHECKED_BY
            }
            checked_chain = False
            for checked_ref in checked_refs:
                for generated in outgoing[checked_ref]:
                    if generated.kind is not EvidenceEdgeKind.GENERATES:
                        continue
                    if any(
                        edge.kind is EvidenceEdgeKind.CONSUMED_BY
                        for edge in outgoing[generated.target_ref]
                    ):
                        checked_chain = True
                        break
                if checked_chain:
                    break
            if not checked_chain:
                missing_edges.append(
                    f"{producer.label}:checked_by->generates->consumed_by"
                )
        missing_edges_tuple = tuple(sorted(set(missing_edges)))
        statuses = {node.axes.evidence_status for node in selected}
        if missing_nodes or missing_edges_tuple:
            statuses.add(EvidenceStatus.MISSING)
        evidence_statuses = tuple(
            status for status in _EVIDENCE_PRECEDENCE if status in statuses
        )
        primary_evidence = evidence_statuses[0]
        process_values = {node.axes.process_result for node in selected}
        if ProcessResult.FAIL in process_values:
            process = ProcessResult.FAIL
        elif (
            ProcessResult.NOT_RUN in process_values
            or missing_nodes
            or missing_edges_tuple
        ):
            process = ProcessResult.NOT_RUN
        else:
            process = ProcessResult.PASS
        mechanics_closed = (
            process is ProcessResult.PASS
            and evidence_statuses == (EvidenceStatus.PRESENT,)
            and not missing_nodes
            and not missing_edges_tuple
        )
        science = claim.axes.scientific_status
        scientific_statuses = tuple(
            sorted(
                {node.axes.scientific_status for node in selected},
                key=lambda status: status.value,
            )
        )
        package_eligible = (
            mechanics_closed
            and science in _PACKAGE_CONSUMABLE_SCIENTIFIC_STATUSES
            and not (set(scientific_statuses) & _BLOCKING_SCIENTIFIC_STATUSES)
        )
        claim_release_eligible = (
            mechanics_closed
            and science in _CLAIM_RELEASE_SCIENTIFIC_STATUSES
            and not (set(scientific_statuses) & _BLOCKING_SCIENTIFIC_STATUSES)
        )
        return ClaimClosure(
            claim_ref=claim_ref,
            node_refs=tuple(sorted(reachable)),
            edge_refs=tuple(sorted(closure_edges)),
            missing_node_requirements=tuple(sorted(missing_nodes)),
            missing_edge_kinds=missing_edges_tuple,
            process_result=process,
            evidence_status=primary_evidence,
            evidence_statuses=evidence_statuses,
            scientific_status=science,
            scientific_statuses=scientific_statuses,
            mechanics_closed=mechanics_closed,
            package_eligible=package_eligible,
            claim_release_eligible=claim_release_eligible,
        )


def _raise_mapping(kind: str) -> None:
    raise EvidenceGraphError(f"graph {kind} must be a mapping")


def _assert_acyclic(node_refs: Sequence[str], edges: Sequence[EvidenceEdge]) -> None:
    outgoing: dict[str, list[str]] = {ref: [] for ref in node_refs}
    indegree = {ref: 0 for ref in node_refs}
    for edge in edges:
        outgoing[edge.source_ref].append(edge.target_ref)
        indegree[edge.target_ref] += 1
    ready = [ref for ref, count in indegree.items() if count == 0]
    visited = 0
    while ready:
        current = ready.pop()
        visited += 1
        for target in outgoing[current]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    if visited != len(node_refs):
        raise EvidenceGraphError("evidence graph contains a dependency cycle")


@dataclass(frozen=True)
class ReceiptDependency:
    kind: ReceiptDependencyKind | str
    receipt_ref: str

    def __post_init__(self) -> None:
        try:
            kind = ReceiptDependencyKind(_enum_value(self.kind))
        except ValueError as exc:
            raise EvidenceGraphError(
                f"unknown receipt dependency kind {self.kind!r}"
            ) from exc
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self, "receipt_ref", _sha256(self.receipt_ref, "receipt_ref")
        )

    @property
    def dependency_ref(self) -> str:
        return _content_address(
            {
                "schema_version": "receipt_dependency_v1",
                "kind": self.kind.value,
                "receipt_ref": self.receipt_ref,
            }
        )

    def to_record(self) -> dict[str, str]:
        return {
            "kind": self.kind.value,
            "receipt_ref": self.receipt_ref,
            "dependency_ref": self.dependency_ref,
        }

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "ReceiptDependency":
        _strict_keys(
            value,
            required={"kind", "receipt_ref", "dependency_ref"},
            field="receipt dependency",
        )
        dependency = cls(value["kind"], str(value["receipt_ref"]))
        expected = _sha256(value["dependency_ref"], "dependency_ref")
        if dependency.dependency_ref != expected:
            raise EvidenceGraphError("dependency_ref does not match dependency payload")
        return dependency


@dataclass(frozen=True)
class EvidenceReceiptBody:
    graph_ref: str
    claim_ref: str
    closure_ref: str
    node_refs: Sequence[str]
    edge_refs: Sequence[str]
    process_result: ProcessResult | str
    evidence_status: EvidenceStatus | str
    evidence_statuses: Sequence[EvidenceStatus | str]
    scientific_status: ScientificStatus | str
    authority_registry_ref: str
    author: str
    author_identity_fingerprint: str
    adjudicator: str
    adjudicator_identity_fingerprint: str
    scope: str
    issued_at: datetime | date | str
    dependencies: Sequence[ReceiptDependency] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_ref", _sha256(self.graph_ref, "graph_ref"))
        object.__setattr__(self, "claim_ref", _sha256(self.claim_ref, "claim_ref"))
        object.__setattr__(
            self, "closure_ref", _sha256(self.closure_ref, "closure_ref")
        )
        object.__setattr__(
            self,
            "authority_registry_ref",
            _sha256(self.authority_registry_ref, "authority_registry_ref"),
        )
        node_refs = tuple(sorted(_sha256(ref, "node_ref") for ref in self.node_refs))
        edge_refs = tuple(sorted(_sha256(ref, "edge_ref") for ref in self.edge_refs))
        if not node_refs or len(node_refs) != len(set(node_refs)):
            raise EvidenceGraphError("receipt node_refs must be non-empty and unique")
        if len(edge_refs) != len(set(edge_refs)):
            raise EvidenceGraphError("receipt edge_refs must be unique")
        try:
            process = ProcessResult(_enum_value(self.process_result))
            evidence = EvidenceStatus(_enum_value(self.evidence_status))
            science = ScientificStatus(_enum_value(self.scientific_status))
        except ValueError as exc:
            raise EvidenceGraphError("receipt contains an unknown state value") from exc
        EvidenceAxes(process, evidence, science)
        if isinstance(self.evidence_statuses, (str, bytes)) or not isinstance(
            self.evidence_statuses, Sequence
        ):
            raise EvidenceGraphError("receipt evidence_statuses must be a sequence")
        try:
            evidence_statuses = tuple(
                EvidenceStatus(_enum_value(value)) for value in self.evidence_statuses
            )
        except ValueError as exc:
            raise EvidenceGraphError(
                "receipt evidence_statuses contains an unknown state"
            ) from exc
        if (
            not evidence_statuses
            or len(evidence_statuses) != len(set(evidence_statuses))
            or tuple(
                status for status in _EVIDENCE_PRECEDENCE if status in evidence_statuses
            )
            != evidence_statuses
            or evidence_statuses[0] is not evidence
        ):
            raise EvidenceGraphError(
                "receipt evidence_statuses must be unique, precedence ordered, "
                "and start with evidence_status"
            )
        author = _exact_text(self.author, "receipt author")
        adjudicator = _exact_text(self.adjudicator, "receipt adjudicator")
        author_fp = _sha256(
            self.author_identity_fingerprint, "author_identity_fingerprint"
        )
        adjudicator_fp = _sha256(
            self.adjudicator_identity_fingerprint,
            "adjudicator_identity_fingerprint",
        )
        if author == adjudicator or author_fp == adjudicator_fp:
            raise EvidenceGraphError(
                "receipt author and adjudicator must have distinct identities"
            )
        scope = _exact_text(self.scope, "receipt scope")
        issued_at = _parse_datetime(self.issued_at, "issued_at")
        if isinstance(self.dependencies, (str, bytes)) or not isinstance(
            self.dependencies, Sequence
        ):
            raise EvidenceGraphError("receipt dependencies must be a sequence")
        raw_dependencies = tuple(self.dependencies)
        if not all(isinstance(row, ReceiptDependency) for row in raw_dependencies):
            raise EvidenceGraphError(
                "dependencies must contain ReceiptDependency values"
            )
        dependencies = tuple(
            sorted(raw_dependencies, key=lambda dependency: dependency.dependency_ref)
        )
        refs = tuple(row.receipt_ref for row in dependencies)
        if len(refs) != len(set(refs)):
            raise EvidenceGraphError("receipt dependencies contain duplicate refs")
        parent_refs = {
            row.receipt_ref
            for row in dependencies
            if row.kind is ReceiptDependencyKind.PARENT
        }
        independent_refs = {
            row.receipt_ref
            for row in dependencies
            if row.kind is ReceiptDependencyKind.INDEPENDENT
        }
        if parent_refs & independent_refs:
            raise EvidenceGraphError(
                "one receipt cannot be both parent and independent evidence"
            )
        object.__setattr__(self, "node_refs", node_refs)
        object.__setattr__(self, "edge_refs", edge_refs)
        object.__setattr__(self, "process_result", process)
        object.__setattr__(self, "evidence_status", evidence)
        object.__setattr__(self, "evidence_statuses", evidence_statuses)
        object.__setattr__(self, "scientific_status", science)
        object.__setattr__(self, "author", author)
        object.__setattr__(self, "author_identity_fingerprint", author_fp)
        object.__setattr__(self, "adjudicator", adjudicator)
        object.__setattr__(self, "adjudicator_identity_fingerprint", adjudicator_fp)
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "issued_at", issued_at)
        object.__setattr__(self, "dependencies", dependencies)
        if self.receipt_id in refs:
            raise EvidenceGraphError("receipt cannot depend on itself")

    @classmethod
    def from_graph(
        cls,
        graph: EvidenceGraph,
        *,
        claim_ref: str,
        author: str,
        author_identity_fingerprint: str,
        adjudicator: str,
        adjudicator_identity_fingerprint: str,
        authority_registry_ref: str,
        scope: str,
        issued_at: datetime | date | str,
        dependencies: Sequence[ReceiptDependency] = (),
    ) -> "EvidenceReceiptBody":
        if not isinstance(graph, EvidenceGraph):
            raise TypeError("graph must be an EvidenceGraph")
        closure = graph.closure(claim_ref)
        return cls(
            graph_ref=graph.graph_ref,
            claim_ref=closure.claim_ref,
            closure_ref=closure.closure_ref,
            node_refs=closure.node_refs,
            edge_refs=closure.edge_refs,
            process_result=closure.process_result,
            evidence_status=closure.evidence_status,
            evidence_statuses=closure.evidence_statuses,
            scientific_status=closure.scientific_status,
            authority_registry_ref=authority_registry_ref,
            author=author,
            author_identity_fingerprint=author_identity_fingerprint,
            adjudicator=adjudicator,
            adjudicator_identity_fingerprint=adjudicator_identity_fingerprint,
            scope=scope,
            issued_at=issued_at,
            dependencies=dependencies,
        )

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "canonicalization": CANONICALIZATION,
            "graph_ref": self.graph_ref,
            "claim_ref": self.claim_ref,
            "closure_ref": self.closure_ref,
            "node_refs": list(self.node_refs),
            "edge_refs": list(self.edge_refs),
            "process_result": self.process_result.value,
            "evidence_status": self.evidence_status.value,
            "evidence_statuses": [status.value for status in self.evidence_statuses],
            "scientific_status": self.scientific_status.value,
            "authority_registry_ref": self.authority_registry_ref,
            "author": self.author,
            "author_identity_fingerprint": self.author_identity_fingerprint,
            "adjudicator": self.adjudicator,
            "adjudicator_identity_fingerprint": self.adjudicator_identity_fingerprint,
            "scope": self.scope,
            "issued_at": self.issued_at.isoformat(),
            "dependencies": [
                dependency.to_record() for dependency in self.dependencies
            ],
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.payload())

    @property
    def receipt_id(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def to_record(self) -> dict[str, object]:
        return {**self.payload(), "receipt_id": self.receipt_id}

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "EvidenceReceiptBody":
        required = {
            "schema_version",
            "canonicalization",
            "graph_ref",
            "claim_ref",
            "closure_ref",
            "node_refs",
            "edge_refs",
            "process_result",
            "evidence_status",
            "evidence_statuses",
            "scientific_status",
            "authority_registry_ref",
            "author",
            "author_identity_fingerprint",
            "adjudicator",
            "adjudicator_identity_fingerprint",
            "scope",
            "issued_at",
            "dependencies",
            "receipt_id",
        }
        _strict_keys(value, required=required, field="evidence receipt body")
        if value["schema_version"] != RECEIPT_SCHEMA_VERSION:
            raise EvidenceGraphError("unsupported evidence receipt schema version")
        if value["canonicalization"] != CANONICALIZATION:
            raise EvidenceGraphError("unsupported receipt canonicalization")
        raw_dependencies = value["dependencies"]
        if not isinstance(raw_dependencies, Sequence) or isinstance(
            raw_dependencies, (str, bytes)
        ):
            raise EvidenceGraphError("receipt dependencies must be a sequence")
        dependencies = [
            (
                ReceiptDependency.from_record(row)
                if isinstance(row, Mapping)
                else _raise_mapping("receipt dependency")
            )
            for row in raw_dependencies
        ]
        body = cls(
            graph_ref=str(value["graph_ref"]),
            claim_ref=str(value["claim_ref"]),
            closure_ref=str(value["closure_ref"]),
            node_refs=value["node_refs"],  # type: ignore[arg-type]
            edge_refs=value["edge_refs"],  # type: ignore[arg-type]
            process_result=value["process_result"],
            evidence_status=value["evidence_status"],
            evidence_statuses=value["evidence_statuses"],  # type: ignore[arg-type]
            scientific_status=value["scientific_status"],
            authority_registry_ref=str(value["authority_registry_ref"]),
            author=str(value["author"]),
            author_identity_fingerprint=str(value["author_identity_fingerprint"]),
            adjudicator=str(value["adjudicator"]),
            adjudicator_identity_fingerprint=str(
                value["adjudicator_identity_fingerprint"]
            ),
            scope=str(value["scope"]),
            issued_at=value["issued_at"],  # type: ignore[arg-type]
            dependencies=dependencies,
        )
        expected = _sha256(value["receipt_id"], "receipt_id")
        if body.receipt_id != expected:
            raise EvidenceGraphError("receipt_id does not match receipt body")
        return body


@dataclass(frozen=True)
class EvidenceReceipt:
    body: EvidenceReceiptBody
    attestation: str

    def __post_init__(self) -> None:
        if not isinstance(self.body, EvidenceReceiptBody):
            raise EvidenceGraphError("receipt body must be EvidenceReceiptBody")
        object.__setattr__(
            self, "attestation", _exact_text(self.attestation, "attestation")
        )

    @property
    def receipt_id(self) -> str:
        return self.body.receipt_id

    def to_record(self) -> dict[str, object]:
        return {"body": self.body.to_record(), "attestation": self.attestation}

    def audit_disclosure(self) -> dict[str, object]:
        """Return a downclaimed disclosure, not an authority-verification result.

        This representation is safe for an internally produced, not-yet-trusted
        receipt: it never says that authority validation passed and never maps a
        process result to scientific readiness.
        """

        return {
            "receipt_id": self.receipt_id,
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "claim_ref": self.body.claim_ref,
            "graph_ref": self.body.graph_ref,
            "closure_ref": self.body.closure_ref,
            "authority_registry_ref": self.body.authority_registry_ref,
            "process_result": self.body.process_result.value,
            "evidence_status": self.body.evidence_status.value,
            "evidence_statuses": [
                status.value for status in self.body.evidence_statuses
            ],
            "scientific_status": self.body.scientific_status.value,
            "authority_status": "REQUIRES_TRUSTED_REGISTRY_VALIDATION",
            "claim_ceiling": "roadmap_rescue_v1:C1 mechanics only",
            "caveat": (
                "Receipt presence and process success are not scientific "
                "validation or independent adjudication."
            ),
        }

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "EvidenceReceipt":
        _strict_keys(value, required={"body", "attestation"}, field="evidence receipt")
        body = value["body"]
        if not isinstance(body, Mapping):
            raise EvidenceGraphError("receipt body must be a mapping")
        return cls(
            body=EvidenceReceiptBody.from_record(body),
            attestation=str(value["attestation"]),
        )

    def validate(
        self,
        graph: EvidenceGraph,
        registry: AuthorityRegistry,
        *,
        evaluated_at: datetime | date | str | None = None,
        receipt_index: Mapping[str, "EvidenceReceipt"] | None = None,
        graph_index: Mapping[str, EvidenceGraph] | None = None,
    ) -> ClaimClosure:
        """Validate exact graph binding, authority, attestation, and lineage."""

        closure = self._validate_binding_and_authority(
            graph, registry, evaluated_at=evaluated_at
        )
        if self.body.dependencies:
            if receipt_index is None or graph_index is None:
                raise EvidenceGraphError(
                    "receipt_index and graph_index are required for "
                    "parent/independence dependencies"
                )
            normalized_receipts = dict(receipt_index)
            normalized_receipts[self.receipt_id] = self
            lineage = validate_receipt_lineage(
                normalized_receipts,
                registry=registry,
                evaluated_at=evaluated_at,
            )
            normalized_graphs = dict(graph_index)
            normalized_graphs[graph.graph_ref] = graph
            for ref in lineage:
                receipt = normalized_receipts[ref]
                dependency_graph = normalized_graphs.get(receipt.body.graph_ref)
                if dependency_graph is None:
                    raise EvidenceGraphError(
                        "receipt dependency graph is missing: "
                        f"{receipt.body.graph_ref}"
                    )
                if dependency_graph.graph_ref != receipt.body.graph_ref:
                    raise EvidenceGraphError(
                        "graph index key/content mismatch for receipt dependency"
                    )
                receipt._validate_binding_and_authority(
                    dependency_graph,
                    registry,
                    evaluated_at=evaluated_at,
                )
        return closure

    def _validate_binding_and_authority(
        self,
        graph: EvidenceGraph,
        registry: AuthorityRegistry,
        *,
        evaluated_at: datetime | date | str | None,
    ) -> ClaimClosure:
        if not isinstance(graph, EvidenceGraph):
            raise TypeError("graph must be an EvidenceGraph")
        if not isinstance(registry, AuthorityRegistry):
            raise TypeError("registry must be an AuthorityRegistry")
        if self.body.authority_registry_ref != authority_registry_content_ref(registry):
            raise AuthorityError(
                "evidence receipt authority_registry_ref does not match trusted registry"
            )
        if self.body.graph_ref != graph.graph_ref:
            raise EvidenceGraphError("receipt graph_ref does not match exact graph")
        closure = graph.closure(self.body.claim_ref)
        expected = {
            "closure_ref": closure.closure_ref,
            "node_refs": closure.node_refs,
            "edge_refs": closure.edge_refs,
            "process_result": closure.process_result,
            "evidence_status": closure.evidence_status,
            "evidence_statuses": closure.evidence_statuses,
            "scientific_status": closure.scientific_status,
        }
        actual = {
            "closure_ref": self.body.closure_ref,
            "node_refs": self.body.node_refs,
            "edge_refs": self.body.edge_refs,
            "process_result": self.body.process_result,
            "evidence_status": self.body.evidence_status,
            "evidence_statuses": self.body.evidence_statuses,
            "scientific_status": self.body.scientific_status,
        }
        if actual != expected:
            raise EvidenceGraphError(
                "receipt does not match the exact recomputed claim closure"
            )
        when = (
            datetime.now(UTC)
            if evaluated_at is None
            else _parse_datetime(evaluated_at, "evaluated_at")
        )
        if self.body.issued_at > when:
            raise AuthorityError("evidence receipt issued_at cannot be in the future")
        author_record = registry.resolve(
            self.body.author,
            role="author",
            scope=self.body.scope,
            at=self.body.issued_at,
            identity_fingerprint=self.body.author_identity_fingerprint,
        )
        adjudicator_record = registry.resolve(
            self.body.adjudicator,
            role="adjudicator",
            scope=self.body.scope,
            at=self.body.issued_at,
            identity_fingerprint=self.body.adjudicator_identity_fingerprint,
        )
        if (
            author_record.principal_id == adjudicator_record.principal_id
            or author_record.identity_fingerprint
            == adjudicator_record.identity_fingerprint
        ):
            raise AuthorityError(
                "evidence receipt author and adjudicator must be distinct"
            )
        if set(closure.scientific_statuses) & _AUTHORITY_GATED_SCIENTIFIC_STATUSES:
            promotion_record = registry.resolve(
                self.body.adjudicator,
                role="scientific_status_promoter",
                scope=self.body.scope,
                at=self.body.issued_at,
                identity_fingerprint=self.body.adjudicator_identity_fingerprint,
            )
            require_independent_external_principal(
                promotion_record,
                use="evidence receipt terminal scientific-status promotion",
            )
        registry.verify_attestation(
            adjudicator_record,
            payload=self.body.canonical_bytes(),
            attestation=self.attestation,
        )
        return closure

    def validate_for_release(
        self,
        graph: EvidenceGraph,
        registry: AuthorityRegistry,
        *,
        evaluated_at: datetime | date | str | None = None,
        receipt_index: Mapping[str, "EvidenceReceipt"] | None = None,
        graph_index: Mapping[str, EvidenceGraph] | None = None,
    ) -> ClaimClosure:
        """Validate a receipt and reject any non-consumable science/mechanics."""

        closure = self.validate(
            graph,
            registry,
            evaluated_at=evaluated_at,
            receipt_index=receipt_index,
            graph_index=graph_index,
        )
        closure.require_claim_release_eligible()
        return closure

    def validate_for_package(
        self,
        graph: EvidenceGraph,
        registry: AuthorityRegistry,
        *,
        evaluated_at: datetime | date | str | None = None,
        receipt_index: Mapping[str, "EvidenceReceipt"] | None = None,
        graph_index: Mapping[str, EvidenceGraph] | None = None,
    ) -> ClaimClosure:
        """Validate trusted evidence for packaging without implying claim release."""

        closure = self.validate(
            graph,
            registry,
            evaluated_at=evaluated_at,
            receipt_index=receipt_index,
            graph_index=graph_index,
        )
        closure.require_package_eligible()
        return closure


def validate_receipt_lineage(
    receipts: Mapping[str, EvidenceReceipt],
    *,
    registry: AuthorityRegistry | None = None,
    evaluated_at: datetime | date | str | None = None,
) -> tuple[str, ...]:
    """Validate exact parent/independence refs, identity separation, and cycles."""

    if not isinstance(receipts, Mapping) or not receipts:
        raise EvidenceGraphError("receipt lineage requires a non-empty mapping")
    normalized: dict[str, EvidenceReceipt] = {}
    for key, receipt in receipts.items():
        ref = _sha256(key, "receipt index key")
        if not isinstance(receipt, EvidenceReceipt):
            raise EvidenceGraphError("receipt index values must be EvidenceReceipt")
        if receipt.receipt_id != ref:
            raise EvidenceGraphError("receipt index key does not match receipt_id")
        normalized[ref] = receipt
    outgoing: dict[str, list[str]] = {ref: [] for ref in normalized}
    for ref, receipt in normalized.items():
        for dependency in receipt.body.dependencies:
            if dependency.receipt_ref not in normalized:
                raise EvidenceGraphError(
                    f"receipt dependency {dependency.receipt_ref} is missing"
                )
            if dependency.receipt_ref == ref:
                raise EvidenceGraphError("receipt cannot depend on itself")
            upstream = normalized[dependency.receipt_ref]
            if dependency.kind is ReceiptDependencyKind.INDEPENDENT:
                if receipt.body.author_identity_fingerprint in {
                    upstream.body.author_identity_fingerprint,
                    upstream.body.adjudicator_identity_fingerprint,
                } or receipt.body.adjudicator_identity_fingerprint in {
                    upstream.body.author_identity_fingerprint,
                    upstream.body.adjudicator_identity_fingerprint,
                }:
                    raise EvidenceGraphError(
                        "independent receipt edge reuses an author/adjudicator identity"
                    )
                if registry is None:
                    raise EvidenceGraphError(
                        "independent receipt edges require a trusted authority registry"
                    )
                for role, identifier, fingerprint in (
                    (
                        "author",
                        upstream.body.author,
                        upstream.body.author_identity_fingerprint,
                    ),
                    (
                        "adjudicator",
                        upstream.body.adjudicator,
                        upstream.body.adjudicator_identity_fingerprint,
                    ),
                ):
                    principal = registry.resolve(
                        identifier,
                        role=role,
                        scope=upstream.body.scope,
                        at=upstream.body.issued_at,
                        identity_fingerprint=fingerprint,
                    )
                    require_independent_external_principal(
                        principal,
                        use=f"independent receipt {role}",
                    )
            outgoing[ref].append(dependency.receipt_ref)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(ref: str) -> None:
        if ref in visiting:
            raise EvidenceGraphError("receipt lineage contains a dependency cycle")
        if ref in visited:
            return
        visiting.add(ref)
        for upstream in outgoing[ref]:
            visit(upstream)
        visiting.remove(ref)
        visited.add(ref)

    for ref in sorted(normalized):
        visit(ref)
    return tuple(sorted(normalized))


def issue_evidence_receipt(
    body: EvidenceReceiptBody,
    *,
    attestation_factory: Callable[[bytes], str],
) -> EvidenceReceipt:
    """Create an envelope; trust is established only by ``validate`` later."""

    if not isinstance(body, EvidenceReceiptBody):
        raise TypeError("body must be EvidenceReceiptBody")
    if not callable(attestation_factory):
        raise TypeError("attestation_factory must be callable")
    attestation = attestation_factory(body.canonical_bytes())
    return EvidenceReceipt(body=body, attestation=attestation)


def _reject_duplicate_object_pairs(
    pairs: Sequence[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceGraphError(f"JSON object contains duplicate key {key!r}")
        result[key] = value
    return result


def _load_json_mapping(path: Path | str, *, artifact: str) -> Mapping[str, object]:
    source = Path(path)
    if not source.is_file():
        raise EvidenceGraphError(f"{artifact} is missing or non-regular: {source}")
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise EvidenceGraphError(f"cannot read {artifact}: {source}") from exc
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_object_pairs)
    except json.JSONDecodeError as exc:
        raise EvidenceGraphError(f"invalid {artifact} JSON: {source}") from exc
    if not isinstance(payload, Mapping):
        raise EvidenceGraphError(f"{artifact} JSON root must be an object")
    return payload


def load_exact_evidence_receipt(
    path: Path | str,
    *,
    expected_receipt_id: str,
) -> EvidenceReceipt:
    """Load a strict receipt and require the caller's exact content address."""

    expected = _sha256(expected_receipt_id, "expected_receipt_id")
    receipt = EvidenceReceipt.from_record(
        _load_json_mapping(path, artifact="evidence receipt")
    )
    if receipt.receipt_id != expected:
        raise EvidenceGraphError(
            "loaded evidence receipt does not match expected_receipt_id"
        )
    return receipt


def load_exact_evidence_graph(
    path: Path | str,
    *,
    expected_graph_ref: str,
) -> EvidenceGraph:
    """Load a strict graph and require the caller's exact content address."""

    expected = _sha256(expected_graph_ref, "expected_graph_ref")
    graph = EvidenceGraph.from_record(
        _load_json_mapping(path, artifact="evidence graph")
    )
    if graph.graph_ref != expected:
        raise EvidenceGraphError(
            "loaded evidence graph does not match expected_graph_ref"
        )
    return graph


def lifecycle_invalidation_dimension(
    kind: EvidenceEdgeKind | str,
) -> IdentityDimension | None:
    """Return the component invalidated by a typed edge, if component-specific."""

    try:
        parsed = EvidenceEdgeKind(_enum_value(kind))
    except ValueError as exc:
        raise EvidenceGraphError(f"unknown evidence edge kind {kind!r}") from exc
    return _INVALIDATION_DIMENSION_BY_EDGE.get(parsed)


def typed_invalidation_targets(
    graph: EvidenceGraph,
    *,
    source_ref: str,
    capability: ClaimCapability | str,
) -> tuple[str, ...]:
    """Return only downstream refs reached by edges affecting one capability."""

    if not isinstance(graph, EvidenceGraph):
        raise TypeError("graph must be an EvidenceGraph")
    source = _sha256(source_ref, "source_ref")
    if source not in {node.node_ref for node in graph.nodes}:
        raise EvidenceGraphError("source_ref is outside the evidence graph")
    try:
        parsed_capability = ClaimCapability(_enum_value(capability))
    except ValueError as exc:
        raise EvidenceGraphError(f"unknown claim capability {capability!r}") from exc
    outgoing: dict[str, list[EvidenceEdge]] = {}
    for edge in graph.edges:
        if edge.kind not in _LIFECYCLE_EDGE_KINDS:
            continue
        affected = tuple(edge.metadata.get("affected_capabilities", ()))
        if parsed_capability.value not in affected:
            continue
        outgoing.setdefault(edge.source_ref, []).append(edge)
    reached: set[str] = set()
    frontier = [source]
    while frontier:
        current = frontier.pop()
        for edge in outgoing.get(current, ()):
            if edge.target_ref in reached:
                continue
            reached.add(edge.target_ref)
            frontier.append(edge.target_ref)
    reached.discard(source)
    return tuple(sorted(reached))


_CAPABILITY_PROFILES: Mapping[
    ClaimCapability,
    tuple[
        CapabilityEvidenceBranch,
        CapabilityScientificSemantics,
        CapabilityIdentification,
        tuple[str, ...],
        str,
        frozenset[str],
    ],
] = {
    ClaimCapability.CONTRACT_VALIDATED: (
        CapabilityEvidenceBranch.CONTRACT,
        CapabilityScientificSemantics.CONTRACT_ONLY,
        CapabilityIdentification.NOT_APPLICABLE,
        ("validated_contract_consumption",),
        "contract_only",
        frozenset({"COMMON"}),
    ),
    ClaimCapability.THEOREM_PROVED_EXACT: (
        CapabilityEvidenceBranch.THEOREM,
        CapabilityScientificSemantics.EXACT_THEOREM,
        CapabilityIdentification.NOT_APPLICABLE,
        ("exact_theorem_reference",),
        "exact_theorem_only",
        frozenset({"COMMON", "BASS"}),
    ),
    ClaimCapability.THEOREM_PROVED_CONDITIONAL: (
        CapabilityEvidenceBranch.THEOREM,
        CapabilityScientificSemantics.CONDITIONAL_THEOREM,
        CapabilityIdentification.NOT_APPLICABLE,
        ("conditional_theorem_reference",),
        "conditional_theorem_only",
        frozenset({"COMMON", "BASS"}),
    ),
    ClaimCapability.METHOD_CALIBRATED: (
        CapabilityEvidenceBranch.METHOD,
        CapabilityScientificSemantics.CALIBRATED_METHOD,
        CapabilityIdentification.NOT_APPLICABLE,
        ("calibrated_method_use",),
        "method_only",
        frozenset({"COMMON", "HTT", "MIO", "BASS", "OBSSTAT"}),
    ),
    ClaimCapability.DATA_ADMITTED: (
        CapabilityEvidenceBranch.DATA,
        CapabilityScientificSemantics.DATA_ADMISSION_ONLY,
        CapabilityIdentification.NOT_APPLICABLE,
        ("admitted_data_input",),
        "data_admission_only",
        frozenset({"COMMON", "OBSSTAT"}),
    ),
    ClaimCapability.OBSERVED_DESCRIPTIVE: (
        CapabilityEvidenceBranch.OBSERVATION,
        CapabilityScientificSemantics.OBSERVED_DESCRIPTION,
        CapabilityIdentification.PARTIAL_IDENTIFICATION,
        ("observed_descriptive_reporting",),
        "observed_descriptive_only",
        frozenset({"HTT", "MIO", "OBSSTAT"}),
    ),
    ClaimCapability.OBSERVED_INFERENTIAL: (
        CapabilityEvidenceBranch.OBSERVATION,
        CapabilityScientificSemantics.OBSERVED_INFERENCE,
        CapabilityIdentification.PARTIAL_IDENTIFICATION,
        ("htt_observed_inference",),
        "htt_inference_only",
        frozenset({"HTT"}),
    ),
    ClaimCapability.SOURCE_SEPARATION_CANDIDATE: (
        CapabilityEvidenceBranch.SOURCE_SEPARATION,
        CapabilityScientificSemantics.SOURCE_SEPARATION_CANDIDATE,
        CapabilityIdentification.PARTIAL_IDENTIFICATION,
        ("source_separation_candidate_only",),
        "candidate_only",
        frozenset({"HTT"}),
    ),
    ClaimCapability.MORPHOLOGY_COMPATIBILITY: (
        CapabilityEvidenceBranch.MORPHOLOGY,
        CapabilityScientificSemantics.MORPHOLOGY_COMPATIBILITY,
        CapabilityIdentification.COMPATIBILITY_ONLY,
        ("morphology_compatibility_only",),
        "compatibility_only",
        frozenset({"HTT", "BASS", "OBSSTAT"}),
    ),
    ClaimCapability.FAMILY_IDENTIFICATION: (
        CapabilityEvidenceBranch.FAMILY,
        CapabilityScientificSemantics.FAMILY_IDENTIFICATION,
        CapabilityIdentification.NATIVE_ATLAS_REQUIRED,
        ("blocked_pre_native_atlas",),
        "blocked_pre_native_atlas",
        frozenset({"BASS"}),
    ),
    ClaimCapability.PUBLIC_RELEASE: (
        CapabilityEvidenceBranch.RELEASE,
        CapabilityScientificSemantics.PUBLICATION,
        CapabilityIdentification.NOT_APPLICABLE,
        ("receipt_scoped_public_release",),
        "receipt_scoped_public_release",
        frozenset({"COMMON"}),
    ),
}


def _claim_node_for_versioned_identity(
    graph: EvidenceGraph,
    versioned_identity: VersionedClaimIdentity,
    claim_ref: str,
) -> EvidenceNode:
    by_ref = {node.node_ref: node for node in graph.nodes}
    claim = by_ref.get(claim_ref)
    if claim is None or claim.kind is not EvidenceNodeKind.CLAIM:
        raise EvidenceGraphError("receipt claim_ref is not a graph claim node")
    if claim.content_sha256 != versioned_identity.identity_ref:
        raise EvidenceGraphError(
            "claim node content identity is not the exact VersionedClaimIdentity"
        )
    required_metadata = {
        "claim_id": versioned_identity.claim_identity.claim_id,
        "claim_identity_fingerprint": (
            versioned_identity.claim_identity.identity_fingerprint
        ),
        "versioned_identity_ref": versioned_identity.identity_ref,
    }
    for key, expected in required_metadata.items():
        if claim.metadata.get(key) != expected:
            raise EvidenceGraphError(
                f"claim node metadata {key} does not match versioned identity"
            )
    rules = tuple(claim.metadata.get("non_relaxable_rules", ()))
    if rules != NON_RELAXABLE_CAPABILITY_RULES:
        raise EvidenceGraphError(
            "claim node must bind every non-relaxable capability rule"
        )
    return claim


def _require_exact_capability_binding(
    claim: EvidenceNode,
    *,
    capability: ClaimCapability,
    action: CapabilityAction,
    outcome: CapabilityOutcome,
    claim_ceiling: str,
) -> None:
    """Require the adjudicated claim node to name the exact requested grant."""

    raw_binding = claim.metadata.get("capability_binding")
    if not isinstance(raw_binding, Mapping):
        raise EvidenceGraphError(
            "claim node is missing an exact capability_binding payload"
        )
    required = {
        "schema_version",
        "capability",
        "action",
        "outcome",
        "claim_ceiling",
    }
    _strict_keys(
        raw_binding,
        required=required,
        field="claim capability_binding",
    )
    expected = {
        "schema_version": "claim_capability_binding_v1",
        "capability": capability.value,
        "action": action.value,
        "outcome": outcome.value,
        "claim_ceiling": claim_ceiling,
    }
    if dict(raw_binding) != expected:
        raise EvidenceGraphError(
            "requested capability decision does not match the adjudicated "
            "claim capability_binding"
        )


def _graph_blockers_for_capability(
    graph: EvidenceGraph,
    capability: ClaimCapability,
) -> tuple[CapabilityBlocker, ...]:
    """Derive active blockers from the exact graph, never from caller omission."""

    blockers: list[CapabilityBlocker] = []
    for edge in sorted(graph.edges, key=lambda item: item.edge_ref):
        if edge.kind not in _ACTIVE_CAPABILITY_BLOCKING_EDGE_KINDS:
            continue
        affected = tuple(edge.metadata.get("affected_capabilities", ()))
        if capability.value not in affected:
            continue
        blockers.append(
            CapabilityBlocker(
                blocker_id=f"lifecycle:{edge.kind.value}:{edge.edge_ref}",
                kind=CapabilityBlockerKind.EVIDENCE_CONDITIONAL,
                affected_capabilities=(capability,),
                evidence_ref=edge.edge_ref,
            )
        )
    return tuple(blockers)


def _require_exact_supersession_edge(
    graph: EvidenceGraph,
    *,
    claim: EvidenceNode,
    versioned_identity: VersionedClaimIdentity,
    capability: ClaimCapability,
) -> None:
    if versioned_identity.predecessor_ref is None:
        return
    by_ref = {node.node_ref: node for node in graph.nodes}
    matches = []
    for edge in graph.edges:
        if (
            edge.kind is EvidenceEdgeKind.SUPERSEDED_BY
            and edge.target_ref == claim.node_ref
            and capability.value
            in tuple(edge.metadata.get("affected_capabilities", ()))
        ):
            source = by_ref[edge.source_ref]
            if source.content_sha256 != versioned_identity.predecessor_ref:
                continue
            if tuple(edge.metadata.get("changed_dimensions", ())) != tuple(
                item.value for item in versioned_identity.changed_dimensions
            ):
                continue
            matches.append(edge)
    if len(matches) != 1:
        raise EvidenceGraphError(
            "successor capability requires exactly one matching SUPERSEDED_BY edge"
        )


_CLAIM_CAPABILITY_DECISION_FIELDS = (
    "versioned_identity",
    "capability",
    "action",
    "outcome",
    "artifact_readiness",
    "evidence_branch",
    "scientific_semantics",
    "identification",
    "provenance_grade",
    "allowed_use",
    "claim_ceiling",
    "evidence_graph_ref",
    "evidence_closure_ref",
    "evidence_receipt_id",
    "adjudication_receipt_ref",
    "blockers",
    "non_relaxable_rules",
)
_CLAIM_CAPABILITY_TRUST_BEARING_NAMES = frozenset(
    {
        "__dict__",
        *_CLAIM_CAPABILITY_DECISION_FIELDS,
        "granted",
        "payload",
        "decision_ref",
        "to_record",
    }
)


def _make_claim_capability_registration_contract() -> tuple[
    Callable[[object], None],
    Callable[[Callable[..., object]], Callable[[object], None]],
]:
    """Return an identity guard and an issuer-frame-bound one-use registrar."""

    issued_instances: dict[int, weakref.ReferenceType[object]] = {}

    def require_registered(value: object) -> None:
        reference = issued_instances.get(id(value))
        if reference is None or reference() is not value:
            raise RemediationContractError(
                "ClaimCapabilityDecision was not issued by the validated "
                "evidence authority"
            )

    def bind_registration(
        issuer: Callable[..., object],
    ) -> Callable[[object], None]:
        issuer_code = issuer.__code__

        def mark_issued(value: object) -> None:
            if sys._getframe(1).f_code is not issuer_code:
                raise RemediationContractError(
                    "decision registration requires the validated issuer frame"
                )
            identity = id(value)

            def retire(reference: weakref.ReferenceType[object]) -> None:
                if issued_instances.get(identity) is reference:
                    issued_instances.pop(identity, None)

            issued_instances[identity] = weakref.ref(value, retire)

        return mark_issued

    return require_registered, bind_registration


(
    _require_claim_capability_decision_registered,
    _bind_claim_capability_decision_registration,
) = _make_claim_capability_registration_contract()
del _make_claim_capability_registration_contract


@dataclass(frozen=True)
class _ClaimCapabilityValidationContext:
    graph: EvidenceGraph
    versioned_identity: VersionedClaimIdentity
    evidence_receipt: EvidenceReceipt
    adjudication_receipt: AdjudicationReceipt
    registry: AuthorityRegistry
    capability: ClaimCapability
    action: CapabilityAction
    outcome: CapabilityOutcome
    blockers: tuple[CapabilityBlocker, ...]
    evaluated_at: datetime
    receipt_index: Mapping[str, EvidenceReceipt] | None
    graph_index: Mapping[str, EvidenceGraph] | None


@dataclass(frozen=True, init=False)
class ClaimCapabilityDecision:
    """Decision whose public use revalidates its exact evidence authority."""

    versioned_identity: VersionedClaimIdentity
    capability: ClaimCapability
    action: CapabilityAction
    outcome: CapabilityOutcome
    artifact_readiness: ArtifactReadinessAxis
    evidence_branch: CapabilityEvidenceBranch
    scientific_semantics: CapabilityScientificSemantics
    identification: CapabilityIdentification
    provenance_grade: CapabilityProvenanceGrade
    allowed_use: tuple[str, ...]
    claim_ceiling: str
    evidence_graph_ref: str
    evidence_closure_ref: str
    evidence_receipt_id: str
    adjudication_receipt_ref: str
    blockers: tuple[CapabilityBlocker, ...]
    non_relaxable_rules: tuple[str, ...]
    _validation_context: _ClaimCapabilityValidationContext = field(
        repr=False,
        compare=False,
        hash=False,
    )

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise RemediationContractError(
            "ClaimCapabilityDecision is factory-only; use "
            "common.evidence_graph.issue_claim_capability_decision"
        )

    def __getattribute__(self, name: str) -> object:
        if name == "_validation_context":
            raise AttributeError("validation context is private")
        if name in _CLAIM_CAPABILITY_TRUST_BEARING_NAMES:
            _require_claim_capability_decision_valid(self)
        return object.__getattribute__(self, name)

    @property
    def granted(self) -> bool:
        """Compatibility projection derived solely from action and outcome."""

        action = object.__getattribute__(self, "action")
        outcome = object.__getattribute__(self, "outcome")
        return action in {
            CapabilityAction.GRANT,
            CapabilityAction.SUPERSEDE,
        } and outcome in {
            CapabilityOutcome.PASS,
            CapabilityOutcome.PASS_WITH_CEILING,
        }

    def payload(self) -> dict[str, object]:
        raw = object.__getattribute__
        versioned_identity = raw(self, "versioned_identity")
        action = raw(self, "action")
        outcome = raw(self, "outcome")
        granted = action in {
            CapabilityAction.GRANT,
            CapabilityAction.SUPERSEDE,
        } and outcome in {
            CapabilityOutcome.PASS,
            CapabilityOutcome.PASS_WITH_CEILING,
        }
        return {
            "schema_version": "claim_capability_decision_v1",
            "versioned_identity_ref": versioned_identity.identity_ref,
            "claim_id": versioned_identity.claim_identity.claim_id,
            "claim_identity_fingerprint": (
                versioned_identity.claim_identity.identity_fingerprint
            ),
            "capability": raw(self, "capability").value,
            "action": action.value,
            "outcome": outcome.value,
            "granted": granted,
            "artifact_readiness": raw(self, "artifact_readiness").value,
            "evidence_branch": raw(self, "evidence_branch").value,
            "scientific_semantics": raw(self, "scientific_semantics").value,
            "identification": raw(self, "identification").value,
            "provenance_grade": raw(self, "provenance_grade").value,
            "allowed_use": list(raw(self, "allowed_use")),
            "claim_ceiling": raw(self, "claim_ceiling"),
            "evidence_graph_ref": raw(self, "evidence_graph_ref"),
            "evidence_closure_ref": raw(self, "evidence_closure_ref"),
            "evidence_receipt_id": raw(self, "evidence_receipt_id"),
            "adjudication_receipt_ref": raw(self, "adjudication_receipt_ref"),
            "blockers": [item.to_record() for item in raw(self, "blockers")],
            "non_relaxable_rules": list(raw(self, "non_relaxable_rules")),
        }

    @property
    def decision_ref(self) -> str:
        payload = object.__getattribute__(self, "payload")()
        return hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()

    def to_record(self) -> dict[str, object]:
        payload = object.__getattribute__(self, "payload")()
        decision_ref = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        return {**payload, "decision_ref": decision_ref}


def _issue_claim_capability_decision_unbound(
    graph: EvidenceGraph,
    *,
    versioned_identity: VersionedClaimIdentity,
    evidence_receipt: EvidenceReceipt,
    adjudication_receipt: AdjudicationReceipt,
    registry: AuthorityRegistry,
    capability: ClaimCapability | str,
    action: CapabilityAction | str,
    outcome: CapabilityOutcome | str,
    blockers: Sequence[CapabilityBlocker] = (),
    evaluated_at: datetime | date | str | None = None,
    receipt_index: Mapping[str, EvidenceReceipt] | None = None,
    graph_index: Mapping[str, EvidenceGraph] | None = None,
    _mark_issued: Callable[[object], None],
) -> ClaimCapabilityDecision:
    """Issue one decision after exact closure and existing-authority validation."""

    if not isinstance(graph, EvidenceGraph):
        raise TypeError("graph must be an EvidenceGraph")
    if not isinstance(versioned_identity, VersionedClaimIdentity):
        raise TypeError("versioned_identity must be a VersionedClaimIdentity")
    if not isinstance(evidence_receipt, EvidenceReceipt):
        raise TypeError("evidence_receipt must be an EvidenceReceipt")
    if not isinstance(adjudication_receipt, AdjudicationReceipt):
        raise TypeError("adjudication_receipt must be an AdjudicationReceipt")
    if not isinstance(registry, AuthorityRegistry):
        raise TypeError("registry must be an AuthorityRegistry")
    validation_time = (
        datetime.now(UTC)
        if evaluated_at is None
        else _parse_datetime(evaluated_at, "evaluated_at")
    )
    if receipt_index is not None and not isinstance(receipt_index, Mapping):
        raise TypeError("receipt_index must be a mapping")
    if graph_index is not None and not isinstance(graph_index, Mapping):
        raise TypeError("graph_index must be a mapping")
    receipt_index_snapshot = (
        None if receipt_index is None else MappingProxyType(dict(receipt_index))
    )
    graph_index_snapshot = (
        None if graph_index is None else MappingProxyType(dict(graph_index))
    )
    try:
        parsed_capability = ClaimCapability(_enum_value(capability))
        parsed_action = CapabilityAction(_enum_value(action))
        parsed_outcome = CapabilityOutcome(_enum_value(outcome))
    except ValueError as exc:
        raise EvidenceGraphError("unknown capability action or outcome") from exc
    if parsed_outcome not in _ALLOWED_OUTCOMES_BY_ACTION[parsed_action]:
        raise RemediationContractError(
            f"outcome {parsed_outcome.value} is invalid for action "
            f"{parsed_action.value}"
        )
    if (
        parsed_action is CapabilityAction.SUPERSEDE
        and versioned_identity.predecessor_ref is None
    ):
        raise RemediationContractError(
            "SUPERSEDE requires an exact predecessor identity"
        )
    closure = evidence_receipt.validate(
        graph,
        registry,
        evaluated_at=validation_time,
        receipt_index=receipt_index_snapshot,
        graph_index=graph_index_snapshot,
    )
    adjudication_receipt.validate(
        registry,
        expected_scope=evidence_receipt.body.scope,
        at=validation_time,
    )
    claim = _claim_node_for_versioned_identity(
        graph, versioned_identity, evidence_receipt.body.claim_ref
    )
    accepted = tuple(
        row
        for row in adjudication_receipt.accepted_claims
        if row.claim_id == versioned_identity.claim_identity.claim_id
        and row.identity_fingerprint
        == versioned_identity.claim_identity.identity_fingerprint
    )
    if len(accepted) != 1:
        raise EvidenceGraphError(
            "adjudication receipt is not bound to the exact claim identity"
        )
    if accepted[0].scientific_status is not closure.scientific_status:
        raise EvidenceGraphError(
            "adjudication status does not match the exact evidence closure"
        )
    profile = _CAPABILITY_PROFILES[parsed_capability]
    branch, semantics, identification, allowed_use, ceiling, allowed_owners = profile
    _require_exact_capability_binding(
        claim,
        capability=parsed_capability,
        action=parsed_action,
        outcome=parsed_outcome,
        claim_ceiling=ceiling,
    )
    _require_exact_supersession_edge(
        graph,
        claim=claim,
        versioned_identity=versioned_identity,
        capability=parsed_capability,
    )
    if versioned_identity.owner not in allowed_owners:
        raise EvidenceGraphError(
            f"owner {versioned_identity.owner} cannot receive "
            f"{parsed_capability.value} capability"
        )
    caller_blockers = tuple(blockers)
    if not all(isinstance(item, CapabilityBlocker) for item in caller_blockers):
        raise EvidenceGraphError("blockers must contain CapabilityBlocker values")
    graph_blockers = _graph_blockers_for_capability(graph, parsed_capability)
    blocker_tuple = (*caller_blockers, *graph_blockers)
    blocker_ids = tuple(item.blocker_id for item in blocker_tuple)
    if len(blocker_ids) != len(set(blocker_ids)):
        raise EvidenceGraphError(
            "caller blockers conflict with blockers derived from the exact graph"
        )
    blocked_here = any(
        parsed_capability in blocker.affected_capabilities
        for blocker in blocker_tuple
    )
    grant_like = parsed_action in {
        CapabilityAction.GRANT,
        CapabilityAction.SUPERSEDE,
    } and parsed_outcome in {
        CapabilityOutcome.PASS,
        CapabilityOutcome.PASS_WITH_CEILING,
    }
    if grant_like and blocked_here:
        raise EvidenceGraphError(
            "a blocker affecting this capability forbids a grant"
        )
    if grant_like and parsed_capability is ClaimCapability.FAMILY_IDENTIFICATION:
        raise EvidenceGraphError(
            "FAMILY_IDENTIFICATION is blocked before an admitted native atlas"
        )
    blocking_science = {
        ScientificStatus.BLOCKED,
        ScientificStatus.FALSIFIED,
        ScientificStatus.ABANDONED,
    }
    if grant_like:
        if not closure.mechanics_closed:
            raise EvidenceGraphError("capability grant requires closed evidence mechanics")
        if closure.scientific_status not in _CLAIM_RELEASE_SCIENTIFIC_STATUSES:
            raise EvidenceGraphError(
                "capability grant requires a positive terminal adjudication"
            )
        readiness = ArtifactReadinessAxis.EVIDENCE_CLOSED
    elif closure.scientific_status in blocking_science or blocked_here:
        readiness = ArtifactReadinessAxis.EVIDENCE_BLOCKED
    elif closure.mechanics_closed:
        readiness = ArtifactReadinessAxis.EVIDENCE_CLOSED
    else:
        readiness = ArtifactReadinessAxis.EVIDENCE_INCOMPLETE
    adjudication_ref = hashlib.sha256(
        adjudication_receipt.canonical_attestation_payload()
        + b"\x00"
        + adjudication_receipt.attestation.encode("utf-8")
    ).hexdigest()
    # ClaimCapabilityDecision deliberately has no callable constructor bridge.
    # Authority comes from exact evidence revalidation, not from Python object
    # identity, hidden tokens, or an allocation marker. Every public use checks
    # the immutable context captured below against this same validation kernel.
    decision = object.__new__(ClaimCapabilityDecision)
    values: Mapping[str, object] = {
        "versioned_identity": versioned_identity,
        "capability": parsed_capability,
        "action": parsed_action,
        "outcome": parsed_outcome,
        "artifact_readiness": readiness,
        "evidence_branch": branch,
        "scientific_semantics": semantics,
        "identification": identification,
        "provenance_grade": (
            CapabilityProvenanceGrade.CONTENT_ADDRESSED_ADJUDICATED
        ),
        "allowed_use": tuple(allowed_use),
        "claim_ceiling": ceiling,
        "evidence_graph_ref": graph.graph_ref,
        "evidence_closure_ref": closure.closure_ref,
        "evidence_receipt_id": evidence_receipt.receipt_id,
        "adjudication_receipt_ref": adjudication_ref,
        "blockers": tuple(
            sorted(blocker_tuple, key=lambda item: item.blocker_id)
        ),
        "non_relaxable_rules": NON_RELAXABLE_CAPABILITY_RULES,
    }
    for field, value in values.items():
        object.__setattr__(decision, field, value)
    object.__setattr__(
        decision,
        "_validation_context",
        _ClaimCapabilityValidationContext(
            graph=graph,
            versioned_identity=versioned_identity,
            evidence_receipt=evidence_receipt,
            adjudication_receipt=adjudication_receipt,
            registry=registry,
            capability=parsed_capability,
            action=parsed_action,
            outcome=parsed_outcome,
            blockers=caller_blockers,
            evaluated_at=validation_time,
            receipt_index=receipt_index_snapshot,
            graph_index=graph_index_snapshot,
        ),
    )
    _mark_issued(decision)
    return decision


def _bind_claim_capability_decision_issuer(
    unbound: Callable[..., ClaimCapabilityDecision],
    bind_registration: Callable[
        [Callable[..., object]], Callable[[object], None]
    ],
) -> Callable[..., ClaimCapabilityDecision]:
    """Bind registration to the validated implementation's exact frame."""

    mark_issued: Callable[[object], None]

    def issued_impl(
        graph: EvidenceGraph,
        *,
        versioned_identity: VersionedClaimIdentity,
        evidence_receipt: EvidenceReceipt,
        adjudication_receipt: AdjudicationReceipt,
        registry: AuthorityRegistry,
        capability: ClaimCapability | str,
        action: CapabilityAction | str,
        outcome: CapabilityOutcome | str,
        blockers: Sequence[CapabilityBlocker] = (),
        evaluated_at: datetime | date | str | None = None,
        receipt_index: Mapping[str, EvidenceReceipt] | None = None,
        graph_index: Mapping[str, EvidenceGraph] | None = None,
    ) -> ClaimCapabilityDecision:
        return unbound(
            graph,
            versioned_identity=versioned_identity,
            evidence_receipt=evidence_receipt,
            adjudication_receipt=adjudication_receipt,
            registry=registry,
            capability=capability,
            action=action,
            outcome=outcome,
            blockers=blockers,
            evaluated_at=evaluated_at,
            receipt_index=receipt_index,
            graph_index=graph_index,
            _mark_issued=mark_issued,
        )

    mark_issued = bind_registration(unbound)
    return issued_impl


_issue_claim_capability_decision_impl = _bind_claim_capability_decision_issuer(
    _issue_claim_capability_decision_unbound,
    _bind_claim_capability_decision_registration,
)
del _bind_claim_capability_decision_issuer
del _bind_claim_capability_decision_registration
del _issue_claim_capability_decision_unbound


def _require_claim_capability_decision_valid(
    decision: ClaimCapabilityDecision,
) -> None:
    """Revalidate all trust-bearing fields against exact authority inputs."""

    if type(decision) is not ClaimCapabilityDecision:
        raise RemediationContractError(
            "claim capability decision must use the exact public type"
        )
    _require_claim_capability_decision_registered(decision)
    try:
        context = object.__getattribute__(decision, "_validation_context")
    except AttributeError as exc:
        raise RemediationContractError(
            "ClaimCapabilityDecision lacks exact validation context"
        ) from exc
    if not isinstance(context, _ClaimCapabilityValidationContext):
        raise RemediationContractError(
            "ClaimCapabilityDecision validation context is invalid"
        )
    try:
        expected = _issue_claim_capability_decision_impl(
            context.graph,
            versioned_identity=context.versioned_identity,
            evidence_receipt=context.evidence_receipt,
            adjudication_receipt=context.adjudication_receipt,
            registry=context.registry,
            capability=context.capability,
            action=context.action,
            outcome=context.outcome,
            blockers=context.blockers,
            evaluated_at=context.evaluated_at,
            receipt_index=context.receipt_index,
            graph_index=context.graph_index,
        )
    except (
        AuthorityError,
        EvidenceGraphError,
        RemediationContractError,
        TypeError,
        ValueError,
    ) as exc:
        raise RemediationContractError(
            "ClaimCapabilityDecision exact authority revalidation failed"
        ) from exc
    for field in _CLAIM_CAPABILITY_DECISION_FIELDS:
        if object.__getattribute__(decision, field) != object.__getattribute__(
            expected, field
        ):
            raise RemediationContractError(
                "ClaimCapabilityDecision fields do not match exact authority "
                f"context: {field}"
            )


def issue_claim_capability_decision(
    graph: EvidenceGraph,
    *,
    versioned_identity: VersionedClaimIdentity,
    evidence_receipt: EvidenceReceipt,
    adjudication_receipt: AdjudicationReceipt,
    registry: AuthorityRegistry,
    capability: ClaimCapability | str,
    action: CapabilityAction | str,
    outcome: CapabilityOutcome | str,
    blockers: Sequence[CapabilityBlocker] = (),
    evaluated_at: datetime | date | str | None = None,
    receipt_index: Mapping[str, EvidenceReceipt] | None = None,
    graph_index: Mapping[str, EvidenceGraph] | None = None,
) -> ClaimCapabilityDecision:
    """Issue a decision that revalidates its exact authority on public use."""

    return _issue_claim_capability_decision_impl(
        graph,
        versioned_identity=versioned_identity,
        evidence_receipt=evidence_receipt,
        adjudication_receipt=adjudication_receipt,
        registry=registry,
        capability=capability,
        action=action,
        outcome=outcome,
        blockers=blockers,
        evaluated_at=evaluated_at,
        receipt_index=receipt_index,
        graph_index=graph_index,
    )


__all__ = [
    "CANONICALIZATION",
    "GRAPH_SCHEMA_VERSION",
    "RECEIPT_SCHEMA_VERSION",
    "ClaimClosure",
    "EvidenceAxes",
    "EvidenceEdge",
    "EvidenceEdgeKind",
    "EvidenceGraph",
    "EvidenceGraphError",
    "EvidenceNode",
    "EvidenceNodeKind",
    "EvidenceReceipt",
    "EvidenceReceiptBody",
    "EvidenceStatus",
    "ProcessResult",
    "ReceiptDependency",
    "ReceiptDependencyKind",
    "TestCaseResult",
    "TestExecution",
    "TestOutcome",
    "authority_registry_content_ref",
    "issue_evidence_receipt",
    "issue_claim_capability_decision",
    "lifecycle_invalidation_dimension",
    "load_literal_release_pin_fields",
    "load_exact_evidence_graph",
    "load_exact_evidence_receipt",
    "validate_receipt_lineage",
    "typed_invalidation_targets",
    "verify_pytest_environment_inputs",
    "verify_pytest_selector_inputs",
]
