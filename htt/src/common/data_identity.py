"""PR-289 stable external-data identities and separate authorization receipts.

The module performs a read-only local preflight. It never downloads, copies,
links, analyzes, or authorizes data. Missing roots are typed refusal outcomes,
not skipped checks.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Mapping, Sequence


LANE_REGISTRY_SCHEMA = "common.data_identity_lane_registry.v2"
DATA_IDENTITY_RECORD_SCHEMA = "common.data_identity_record.v2"
DATA_IDENTITY_EVIDENCE_SCHEMA = "common.data_identity_evidence.v2"
AUTHORIZATION_RECEIPT_SCHEMA = "common.execution_authorization_receipt.v1"
PREFLIGHT_RECEIPT_SCHEMA = "common.data_identity_v2_preflight_receipt.v1"
REGISTRY_ID = "PR289-LANE-REGISTRY-V2"
PASS_TOKEN = "PASS_DATA_IDENTITY_V2_PREFLIGHT"
CLAIM_TIER = "diagnostic_only"
TRANSFER_SOURCE = "none"
FAMILY_GATE = "BLOCKED_PRE_NATIVE_ATLAS"
AUTHORIZATION_DOMAIN = "lane_data_execution"

_RECORD_TOKEN = object()
_REGISTRY_TOKEN = object()
_AUTH_TOKEN = object()
_PREFLIGHT_TOKEN = object()
_RAW_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LANE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_IDENTITY_PREFIXES = ("doi:", "url:", "urn:", "repo:", "docs:")
_LICENSE_PREFIXES = ("spdx:",) + _IDENTITY_PREFIXES
_EXPECTED_LANE_GATES = {
    "PLANCK": "H-PLANCK",
    "CF4": "H-CF4",
    "HSC_KIDS": "H-HSC-KiDS",
    "ACT": "H-ACT",
    "DESI": "H-DESI",
    "JWST_SN": "H-JWST",
}
_EXPECTED_NATIVE_SCHEMAS = {
    "PLANCK": "common.planck_native_identity.v1",
    "CF4": "common.cf4_native_identity.v1",
    "HSC_KIDS": "common.hsc_kids_native_identity.v1",
    "ACT": "common.registered_product_native_identity.v1",
    "DESI": "common.registered_product_native_identity.v1",
    "JWST_SN": "common.registered_product_native_identity.v1",
}
_EXPECTED_UNIVERSAL_SEMANTIC_FIELDS = (
    "units_contract_id",
    "coordinate_frame_id",
    "sign_orientation_convention_id",
    "directional_convention_id",
    "harmonic_convention_id",
    "mask_id",
    "selection_id",
    "sky_support_id",
    "covariance_id",
    "covariance_status",
    "null_ensemble_id",
    "null_ensemble_status",
    "transfer_source",
    "transfer_function_spec_id",
    "transfer_provenance_status",
    "sky_support_status",
    "license_status",
    "native_identity_profile",
)
_EXPECTED_NATIVE_COMPONENT_IDS = {
    "PLANCK": (
        "smica_map",
        "commander_map",
        "smica_mask",
        "commander_mask",
        "smica_beam",
        "commander_beam",
        "smica_window_operator",
        "commander_window_operator",
        "smica_covariance",
        "commander_covariance",
        "pixelization",
        "native_selection",
        "ffp10_null_inventory",
    ),
    "CF4": (
        "catalogue",
        "row_selection",
        "covariance",
        "frame_definition",
        "sign_convention",
        "units_contract",
        "grouping_definition",
        "depth_definition",
        "zoa_definition",
    ),
    "HSC_KIDS": (
        "hsc_product",
        "kids_product",
        "hsc_mask",
        "kids_mask",
        "hsc_randoms",
        "kids_randoms",
        "hsc_psf",
        "kids_psf",
        "hsc_n_z",
        "kids_n_z",
        "hsc_shear_calibration",
        "kids_shear_response",
        "hsc_covariance",
        "kids_covariance",
        "hsc_kids_cross_covariance",
    ),
}
_STATUS_PRECEDENCE = (
    "BLOCKED_PATH_ESCAPE_OR_MUTATION",
    "BLOCKED_PR151_INCOMPLETE",
    "REJECTED_NAME_ONLY",
    "REJECTED_NOT_PRESENT",
    "REJECTED_NOT_REGULAR_FILE",
    "REJECTED_SYMLINK_OR_ALIAS",
    "REJECTED_IDENTITY_MISMATCH",
    "REJECTED_MISSING_RELEASE_OR_LICENSE",
    "REJECTED_MISSING_SEMANTIC_CONTRACT",
    "REJECTED_INCOMPLETE_COMPONENT_SET",
    "ADMITTED_IDENTITY_ONLY",
)
_EVIDENCE_FIELDS = frozenset(
    {
        "schema",
        "lane_id",
        "product_id",
        "source_locator_identity",
        "release_name",
        "release_version",
        "release_identity",
        "license_identity",
        "license_status",
        "units_contract_id",
        "coordinate_frame_id",
        "sign_orientation_convention_id",
        "directional_convention_id",
        "harmonic_convention_id",
        "mask_id",
        "selection_id",
        "sky_support_id",
        "covariance_id",
        "covariance_status",
        "null_ensemble_id",
        "null_ensemble_status",
        "transfer_source",
        "transfer_function_spec_id",
        "transfer_provenance_status",
        "sky_support_status",
        "native_identity_profile",
    }
)
_DESCRIPTOR_FIELDS = frozenset(
    {
        "root",
        "evidence_relative_path",
        "evidence_sha256",
        "components",
        "acquisition_status",
        "name_only",
    }
)
_COMPONENT_FIELDS = frozenset(
    {"component_id", "relative_path", "byte_size", "content_sha256"}
)


class DataIdentityError(ValueError):
    """Raised when the PR-289 contract itself is malformed."""


class AdmissionStatus(str, Enum):
    BLOCKED_PATH_ESCAPE_OR_MUTATION = "BLOCKED_PATH_ESCAPE_OR_MUTATION"
    BLOCKED_PR151_INCOMPLETE = "BLOCKED_PR151_INCOMPLETE"
    REJECTED_NAME_ONLY = "REJECTED_NAME_ONLY"
    REJECTED_NOT_PRESENT = "REJECTED_NOT_PRESENT"
    REJECTED_NOT_REGULAR_FILE = "REJECTED_NOT_REGULAR_FILE"
    REJECTED_SYMLINK_OR_ALIAS = "REJECTED_SYMLINK_OR_ALIAS"
    REJECTED_IDENTITY_MISMATCH = "REJECTED_IDENTITY_MISMATCH"
    REJECTED_MISSING_RELEASE_OR_LICENSE = "REJECTED_MISSING_RELEASE_OR_LICENSE"
    REJECTED_MISSING_SEMANTIC_CONTRACT = "REJECTED_MISSING_SEMANTIC_CONTRACT"
    REJECTED_INCOMPLETE_COMPONENT_SET = "REJECTED_INCOMPLETE_COMPONENT_SET"
    ADMITTED_IDENTITY_ONLY = "ADMITTED_IDENTITY_ONLY"


class AggregateStatus(str, Enum):
    NO_ADMITTED_IDENTITIES = "NO_ADMITTED_IDENTITIES"
    PARTIAL_LANE_ADMISSION = "PARTIAL_LANE_ADMISSION"
    ADMITTED_IDENTITIES_AWAITING_SEPARATE_AUTHORIZATION = (
        "ADMITTED_IDENTITIES_AWAITING_SEPARATE_AUTHORIZATION"
    )


class AuthorizationStatus(str, Enum):
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    AUTHORIZED = "AUTHORIZED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise DataIdentityError("payload is not canonical finite JSON") from exc


def canonical_sha256(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _raw_sha(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise DataIdentityError(f"{field_name} must be a SHA-256 string")
    raw = value.removeprefix("sha256:")
    if _RAW_SHA256_RE.fullmatch(raw) is None:
        raise DataIdentityError(f"{field_name} must be a lowercase SHA-256")
    return raw


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DataIdentityError(f"{field_name} must be nonempty trimmed text")
    return value


def _exact_mapping(
    value: object, *, field_name: str, expected: frozenset[str]
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DataIdentityError(f"{field_name} must be a mapping")
    actual = set(value)
    if actual != expected:
        raise DataIdentityError(
            f"{field_name} fields drifted; "
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )
    return value


def _utc(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DataIdentityError(f"{field_name} must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise DataIdentityError(f"{field_name} must be timezone-aware UTC")
    return text


def _identity(value: object, field_name: str, prefixes: Sequence[str]) -> str:
    text = _text(value, field_name)
    folded = text.casefold()
    for prefix in prefixes:
        if folded.startswith(prefix.casefold()):
            suffix = text[len(prefix) :].strip()
            if len(suffix) >= 2 and any(char.isalnum() for char in suffix):
                return text
    raise DataIdentityError(f"{field_name} lacks a registered resolvable identity")


def _release_version(value: object) -> str:
    text = _text(value, "release_version")
    if (
        len(text) < 3
        or not any(char.isalpha() for char in text)
        or not any(char.isdigit() for char in text)
    ):
        raise DataIdentityError("release_version must contain version material")
    return text


def _strict_json_bytes(raw: bytes, *, field_name: str) -> Mapping[str, object]:
    def no_duplicate(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise DataIdentityError(f"{field_name} contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=no_duplicate,
            parse_constant=lambda token: (_ for _ in ()).throw(
                DataIdentityError(
                    f"{field_name} contains non-finite constant {token}"
                )
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DataIdentityError(f"{field_name} is not strict JSON") from exc
    if not isinstance(value, Mapping):
        raise DataIdentityError(f"{field_name} must contain a mapping")
    _canonical_bytes(value)
    return value


def _file_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _read_regular_bytes(
    path: Path,
    *,
    field_name: str,
    expected_info: os.stat_result | None = None,
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise DataIdentityError(f"{field_name} cannot be opened safely") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise DataIdentityError(f"{field_name} is not a unique regular file")
        if expected_info is not None and _file_identity(before) != _file_identity(
            expected_info
        ):
            raise DataIdentityError(f"{field_name} changed before inspection")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if _file_identity(before) != _file_identity(after):
            raise DataIdentityError(f"{field_name} changed during inspection")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _strict_json(
    path: Path,
    *,
    field_name: str,
    expected_info: os.stat_result | None = None,
) -> Mapping[str, object]:
    return _strict_json_bytes(
        _read_regular_bytes(
            path, field_name=field_name, expected_info=expected_info
        ),
        field_name=field_name,
    )


def _stream_sha256(
    path: Path,
    *,
    field_name: str = "file",
    expected_info: os.stat_result | None = None,
) -> str:
    return hashlib.sha256(
        _read_regular_bytes(
            path, field_name=field_name, expected_info=expected_info
        )
    ).hexdigest()


def _relative_path(value: object, field_name: str) -> Path:
    text = _text(value, field_name)
    candidate = Path(text)
    if (
        candidate.is_absolute()
        or ".." in candidate.parts
        or "\\" in text
        or candidate.as_posix() != text
        or text in {".", ""}
    ):
        raise DataIdentityError(f"{field_name} must be canonical and root-relative")
    return candidate


def _regular_beneath(
    root: Path, relative: Path, field_name: str
) -> tuple[Path, os.stat_result]:
    cursor = root
    for component in relative.parts:
        cursor = cursor / component
        try:
            info = cursor.lstat()
        except FileNotFoundError as exc:
            raise DataIdentityError(f"{field_name} is missing") from exc
        if stat.S_ISLNK(info.st_mode):
            raise DataIdentityError(f"{field_name} traverses a symlink")
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise DataIdentityError(f"{field_name} escapes its declared root") from exc
    info = candidate.lstat()
    if resolved != candidate or not stat.S_ISREG(info.st_mode):
        raise DataIdentityError(f"{field_name} is not an exact regular file")
    if info.st_nlink != 1:
        raise DataIdentityError(f"{field_name} is a hardlink alias")
    return candidate, info


@dataclass(frozen=True)
class LaneSpec:
    lane_id: str
    product_id: str
    required_component_ids: tuple[str, ...]
    component_cardinality: tuple[tuple[str, int], ...]
    native_identity_schema: str
    required_human_gate_id: str
    analysis_plan_id: str
    allowed_transfer_sources: tuple[str, ...]
    name_only_forbidden: bool

    @property
    def cardinality(self) -> Mapping[str, int]:
        return dict(self.component_cardinality)

    @property
    def expected_component_sequence(self) -> tuple[str, ...]:
        return tuple(
            component_id
            for component_id in self.required_component_ids
            for _ in range(self.cardinality[component_id])
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "lane_id": self.lane_id,
            "product_id": self.product_id,
            "required_component_ids": list(self.required_component_ids),
            "component_cardinality": dict(self.component_cardinality),
            "native_identity_schema": self.native_identity_schema,
            "required_human_gate_id": self.required_human_gate_id,
            "analysis_plan_id": self.analysis_plan_id,
            "allowed_transfer_sources": list(self.allowed_transfer_sources),
            "name_only_forbidden": self.name_only_forbidden,
        }


@dataclass(frozen=True)
class LaneRegistryV2:
    lanes: tuple[LaneSpec, ...]
    universal_semantic_fields: tuple[str, ...]
    _construction_token: InitVar[object] = None
    _seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REGISTRY_TOKEN:
            raise DataIdentityError("LaneRegistryV2 must be factory-built")
        if tuple(lane.lane_id for lane in self.lanes) != (
            "PLANCK",
            "CF4",
            "HSC_KIDS",
            "ACT",
            "DESI",
            "JWST_SN",
        ):
            raise DataIdentityError("lane registry order drifted")
        object.__setattr__(self, "_seal", canonical_sha256(self._payload()))

    def _payload(self) -> dict[str, object]:
        return {
            "schema": LANE_REGISTRY_SCHEMA,
            "registry_id": REGISTRY_ID,
            "lane_order": [lane.lane_id for lane in self.lanes],
            "universal_semantic_fields": list(self.universal_semantic_fields),
            "lanes": [lane.as_payload() for lane in self.lanes],
        }

    @property
    def content_id(self) -> str:
        if canonical_sha256(self._payload()) != self._seal:
            raise DataIdentityError("lane registry identity drifted")
        return self._seal

    def lane(self, lane_id: str) -> LaneSpec:
        matches = [lane for lane in self.lanes if lane.lane_id == lane_id]
        if len(matches) != 1:
            raise DataIdentityError(f"unregistered lane {lane_id!r}")
        return matches[0]

    def as_payload(self) -> dict[str, object]:
        return {**self._payload(), "content_id": self.content_id}


def lane_registry_from_mapping(payload: Mapping[str, object]) -> LaneRegistryV2:
    checked = _exact_mapping(
        payload,
        field_name="lane registry",
        expected=frozenset(
            {
                "schema",
                "registry_id",
                "lane_order",
                "universal_semantic_fields",
                "lanes",
            }
        ),
    )
    if checked["schema"] != LANE_REGISTRY_SCHEMA or checked["registry_id"] != REGISTRY_ID:
        raise DataIdentityError("lane registry authority drifted")
    order = checked["lane_order"]
    semantic = checked["universal_semantic_fields"]
    raw_lanes = checked["lanes"]
    if (
        isinstance(order, (str, bytes))
        or not isinstance(order, Sequence)
        or isinstance(semantic, (str, bytes))
        or not isinstance(semantic, Sequence)
        or isinstance(raw_lanes, (str, bytes))
        or not isinstance(raw_lanes, Sequence)
    ):
        raise DataIdentityError("lane registry sequences are malformed")
    semantic_tuple = tuple(
        _text(value, "universal semantic field") for value in semantic
    )
    order_tuple = tuple(_text(value, "lane_order entry") for value in order)
    if len(order_tuple) != len(set(order_tuple)) or len(semantic_tuple) != len(
        set(semantic_tuple)
    ):
        raise DataIdentityError("lane registry contains duplicate identities")
    if semantic_tuple != _EXPECTED_UNIVERSAL_SEMANTIC_FIELDS:
        raise DataIdentityError("lane registry semantic field inventory drifted")
    lanes: list[LaneSpec] = []
    expected_lane_fields = frozenset(
        {
            "lane_id",
            "product_id",
            "required_component_ids",
            "component_cardinality",
            "native_identity_schema",
            "required_human_gate_id",
            "analysis_plan_id",
            "allowed_transfer_sources",
            "name_only_forbidden",
        }
    )
    for index, raw_lane in enumerate(raw_lanes):
        row = _exact_mapping(
            raw_lane, field_name=f"lane {index}", expected=expected_lane_fields
        )
        lane_id = _text(row["lane_id"], "lane_id")
        if _LANE_ID_RE.fullmatch(lane_id) is None:
            raise DataIdentityError("lane_id is not canonical")
        component_ids = row["required_component_ids"]
        cardinality = row["component_cardinality"]
        sources = row["allowed_transfer_sources"]
        if (
            isinstance(component_ids, (str, bytes))
            or not isinstance(component_ids, Sequence)
            or not isinstance(cardinality, Mapping)
            or isinstance(sources, (str, bytes))
            or not isinstance(sources, Sequence)
        ):
            raise DataIdentityError(f"{lane_id} lane inventory is malformed")
        component_tuple = tuple(
            _text(value, f"{lane_id} component_id") for value in component_ids
        )
        if len(component_tuple) != len(set(component_tuple)):
            raise DataIdentityError(f"{lane_id} components are duplicated")
        expected_native_components = _EXPECTED_NATIVE_COMPONENT_IDS.get(lane_id)
        if (
            expected_native_components is not None
            and component_tuple != expected_native_components
        ):
            raise DataIdentityError(f"{lane_id} native component roles drifted")
        if set(cardinality) != set(component_tuple):
            raise DataIdentityError(f"{lane_id} component cardinality drifted")
        pairs: list[tuple[str, int]] = []
        for component_id in component_tuple:
            count = cardinality[component_id]
            if type(count) is not int or count < 1:
                raise DataIdentityError(f"{lane_id} component cardinality is invalid")
            pairs.append((component_id, count))
        human_gate = _text(
            row["required_human_gate_id"], "required_human_gate_id"
        )
        if human_gate != _EXPECTED_LANE_GATES.get(lane_id):
            raise DataIdentityError(f"{lane_id} human gate identity drifted")
        native_schema = _text(
            row["native_identity_schema"], "native_identity_schema"
        )
        if native_schema != _EXPECTED_NATIVE_SCHEMAS.get(lane_id):
            raise DataIdentityError(f"{lane_id} native identity schema drifted")
        if type(row["name_only_forbidden"]) is not bool:
            raise DataIdentityError(f"{lane_id} name_only_forbidden must be boolean")
        source_tuple = tuple(
            _text(value, "allowed_transfer_source") for value in sources
        )
        if not source_tuple or len(source_tuple) != len(set(source_tuple)):
            raise DataIdentityError(f"{lane_id} transfer sources are malformed")
        lanes.append(
            LaneSpec(
                lane_id=lane_id,
                product_id=_text(row["product_id"], "product_id"),
                required_component_ids=component_tuple,
                component_cardinality=tuple(pairs),
                native_identity_schema=native_schema,
                required_human_gate_id=human_gate,
                analysis_plan_id=_text(row["analysis_plan_id"], "analysis_plan_id"),
                allowed_transfer_sources=source_tuple,
                name_only_forbidden=row["name_only_forbidden"],
            )
        )
    if order_tuple != tuple(lane.lane_id for lane in lanes):
        raise DataIdentityError("lane_order and lane rows disagree")
    return LaneRegistryV2(
        lanes=tuple(lanes),
        universal_semantic_fields=semantic_tuple,
        _construction_token=_REGISTRY_TOKEN,
    )


def load_lane_registry(path: Path) -> LaneRegistryV2:
    if path.is_symlink() or not path.is_file():
        raise DataIdentityError("lane registry must be a regular file")
    info = path.lstat()
    return lane_registry_from_mapping(
        _strict_json(
            path, field_name="lane registry", expected_info=info
        )
    )


def component_inventory_id(components: Sequence[Mapping[str, object]]) -> str:
    rows = []
    for row in components:
        checked = _exact_mapping(
            row, field_name="component descriptor", expected=_COMPONENT_FIELDS
        )
        size = checked["byte_size"]
        if type(size) is not int or size <= 0:
            raise DataIdentityError("component byte_size must be a positive integer")
        rows.append(
            {
                "component_id": _text(checked["component_id"], "component_id"),
                "byte_size": size,
                "content_sha256": "sha256:"
                + _raw_sha(checked["content_sha256"], "component content_sha256"),
            }
        )
    return canonical_sha256(rows)


_NATIVE_BINDING_FIELDS = frozenset(
    {
        "component_id",
        "ordinal",
        "relative_path",
        "byte_size",
        "content_sha256",
    }
)


def _native_component_bindings(
    components: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    ordinals: dict[str, int] = {}
    rows: list[dict[str, object]] = []
    for component in components:
        checked = _exact_mapping(
            component,
            field_name="native component descriptor",
            expected=_COMPONENT_FIELDS,
        )
        component_id = _text(checked["component_id"], "component_id")
        ordinal = ordinals.get(component_id, 0)
        ordinals[component_id] = ordinal + 1
        byte_size = checked["byte_size"]
        if type(byte_size) is not int or byte_size <= 0:
            raise DataIdentityError("native component byte_size is invalid")
        rows.append(
            {
                "component_id": component_id,
                "ordinal": ordinal,
                "relative_path": _relative_path(
                    checked["relative_path"], "native component relative_path"
                ).as_posix(),
                "byte_size": byte_size,
                "content_sha256": "sha256:"
                + _raw_sha(
                    checked["content_sha256"], "native component content_sha256"
                ),
            }
        )
    return rows


def _validate_profile_id(profile: Mapping[str, object]) -> None:
    profile_id = profile.get("profile_id")
    unsigned = dict(profile)
    unsigned.pop("profile_id", None)
    if profile_id != canonical_sha256(unsigned):
        raise DataIdentityError("native identity profile_id drifted")


def _validate_nested_identity(
    value: object,
    *,
    field_name: str,
    expected_fields: frozenset[str],
    identity_field: str,
    component_bindings: Sequence[Mapping[str, object]] | None = None,
) -> Mapping[str, object]:
    row = _exact_mapping(
        value, field_name=field_name, expected=expected_fields | {identity_field}
    )
    unsigned = dict(row)
    observed = unsigned.pop(identity_field)
    expected_identity = _relationship_content_identity(
        unsigned, component_bindings=component_bindings
    )
    if observed != expected_identity:
        raise DataIdentityError(f"{field_name} {identity_field} drifted")
    return row


def _relationship_content_identity(
    payload: Mapping[str, object],
    *,
    component_bindings: Sequence[Mapping[str, object]] | None,
) -> str:
    if component_bindings is None:
        return canonical_sha256(payload)
    referenced = {
        value
        for key, value in payload.items()
        if (key == "component_id" or key.endswith("_component_id"))
        and isinstance(value, str)
    }
    selected = [
        dict(row)
        for row in component_bindings
        if row.get("component_id") in referenced
    ]
    if len({row.get("component_id") for row in selected}) != len(referenced):
        raise DataIdentityError("native relationship component binding is incomplete")
    return canonical_sha256(
        {"relationship": dict(payload), "component_bindings": selected}
    )


def _validate_component_reference(
    value: object,
    *,
    field_name: str,
    expected: str,
    available: frozenset[str],
) -> None:
    component_id = _text(value, field_name)
    if component_id != expected or component_id not in available:
        raise DataIdentityError(f"{field_name} does not bind the native role")


def _validate_planck_native_profile(
    profile: Mapping[str, object],
    *,
    evidence: Mapping[str, object],
    available: frozenset[str],
) -> None:
    bindings = profile["component_bindings"]
    if evidence["covariance_status"] != "REGISTERED":
        raise DataIdentityError(
            "Planck covariance roles require REGISTERED covariance status"
        )
    if evidence["sky_support_status"] != "REGISTERED":
        raise DataIdentityError(
            "Planck same-sky roles require REGISTERED sky support status"
        )
    pipelines = _exact_mapping(
        profile["pipelines"],
        field_name="Planck pipelines",
        expected=frozenset({"SMICA", "COMMANDER"}),
    )
    pipeline_fields = frozenset(
        {
            "pipeline",
            "map_component_id",
            "mask_component_id",
            "beam_component_id",
            "window_operator_component_id",
            "covariance_component_id",
            "pixelization_component_id",
            "native_selection_component_id",
            "sky_support_id",
            "harmonic_convention_id",
        }
    )
    for name, prefix in (("SMICA", "smica"), ("COMMANDER", "commander")):
        row = _validate_nested_identity(
            pipelines[name],
            field_name=f"Planck {name} pipeline",
            expected_fields=pipeline_fields,
            identity_field="pipeline_identity",
            component_bindings=bindings,
        )
        if row["pipeline"] != name:
            raise DataIdentityError(f"Planck {name} pipeline identity drifted")
        for field_name, expected in (
            ("map_component_id", f"{prefix}_map"),
            ("mask_component_id", f"{prefix}_mask"),
            ("beam_component_id", f"{prefix}_beam"),
            ("window_operator_component_id", f"{prefix}_window_operator"),
            ("covariance_component_id", f"{prefix}_covariance"),
            ("pixelization_component_id", "pixelization"),
            ("native_selection_component_id", "native_selection"),
        ):
            _validate_component_reference(
                row[field_name],
                field_name=f"Planck {name} {field_name}",
                expected=expected,
                available=available,
            )
        if (
            row["sky_support_id"] != evidence["sky_support_id"]
            or row["harmonic_convention_id"]
            != evidence["harmonic_convention_id"]
        ):
            raise DataIdentityError(
                f"Planck {name} sky or harmonic identity drifted"
            )
    pair = _validate_nested_identity(
        profile["same_sky_pair"],
        field_name="Planck same-sky pair",
        expected_fields=frozenset(
            {
                "smica_map_component_id",
                "commander_map_component_id",
                "sky_support_id",
                "pixelization_component_id",
            }
        ),
        identity_field="pair_id",
        component_bindings=bindings,
    )
    for field_name, expected in (
        ("smica_map_component_id", "smica_map"),
        ("commander_map_component_id", "commander_map"),
        ("pixelization_component_id", "pixelization"),
    ):
        _validate_component_reference(
            pair[field_name],
            field_name=f"Planck pair {field_name}",
            expected=expected,
            available=available,
        )
    if pair["sky_support_id"] != evidence["sky_support_id"]:
        raise DataIdentityError("Planck SMICA/Commander are not same-sky paired")
    null = _validate_nested_identity(
        profile["ffp10_null"],
        field_name="Planck FFP10 null",
        expected_fields=frozenset(
            {"ensemble_kind", "inventory_component_id", "null_ensemble_id"}
        ),
        identity_field="null_identity",
        component_bindings=bindings,
    )
    if null["ensemble_kind"] != "FFP10":
        raise DataIdentityError("Planck null ensemble must be FFP10")
    _validate_component_reference(
        null["inventory_component_id"],
        field_name="Planck FFP10 inventory_component_id",
        expected="ffp10_null_inventory",
        available=available,
    )
    if (
        null["null_ensemble_id"] != evidence["null_ensemble_id"]
        or evidence["null_ensemble_status"] != "REGISTERED"
    ):
        raise DataIdentityError("Planck FFP10 null identity drifted")


def _validate_cf4_native_profile(
    profile: Mapping[str, object],
    *,
    evidence: Mapping[str, object],
    available: frozenset[str],
) -> None:
    bindings = profile["component_bindings"]
    catalogue = _validate_nested_identity(
        profile["catalogue"],
        field_name="CF4 catalogue",
        expected_fields=frozenset(
            {
                "catalogue_component_id",
                "row_selection_component_id",
                "covariance_component_id",
                "row_selection_id",
                "covariance_id",
            }
        ),
        identity_field="catalogue_identity",
        component_bindings=bindings,
    )
    for field_name, expected in (
        ("catalogue_component_id", "catalogue"),
        ("row_selection_component_id", "row_selection"),
        ("covariance_component_id", "covariance"),
    ):
        _validate_component_reference(
            catalogue[field_name],
            field_name=f"CF4 {field_name}",
            expected=expected,
            available=available,
        )
    if (
        catalogue["row_selection_id"] != evidence["selection_id"]
        or catalogue["covariance_id"] != evidence["covariance_id"]
        or evidence["covariance_status"] != "REGISTERED"
    ):
        raise DataIdentityError("CF4 selection or covariance identity drifted")
    semantics = _validate_nested_identity(
        profile["semantics"],
        field_name="CF4 semantic roles",
        expected_fields=frozenset(
            {
                "frame_component_id",
                "sign_component_id",
                "units_component_id",
                "grouping_component_id",
                "depth_component_id",
                "zoa_component_id",
                "coordinate_frame_id",
                "sign_orientation_convention_id",
                "units_contract_id",
            }
        ),
        identity_field="semantics_identity",
        component_bindings=bindings,
    )
    for field_name, expected in (
        ("frame_component_id", "frame_definition"),
        ("sign_component_id", "sign_convention"),
        ("units_component_id", "units_contract"),
        ("grouping_component_id", "grouping_definition"),
        ("depth_component_id", "depth_definition"),
        ("zoa_component_id", "zoa_definition"),
    ):
        _validate_component_reference(
            semantics[field_name],
            field_name=f"CF4 {field_name}",
            expected=expected,
            available=available,
        )
    for field_name in (
        "coordinate_frame_id",
        "sign_orientation_convention_id",
        "units_contract_id",
    ):
        if semantics[field_name] != evidence[field_name]:
            raise DataIdentityError(f"CF4 {field_name} drifted")


def _validate_hsc_kids_native_profile(
    profile: Mapping[str, object],
    *,
    evidence: Mapping[str, object],
    available: frozenset[str],
) -> None:
    bindings = profile["component_bindings"]
    children = _exact_mapping(
        profile["children"],
        field_name="HSC/KiDS children",
        expected=frozenset({"HSC", "KIDS"}),
    )
    child_fields = frozenset(
        {
            "survey_id",
            "product_component_id",
            "mask_component_id",
            "randoms_component_id",
            "psf_component_id",
            "n_z_component_id",
            "calibration_or_response_component_id",
            "covariance_component_id",
        }
    )
    checked_children: dict[str, Mapping[str, object]] = {}
    for survey, prefix, calibration in (
        ("HSC", "hsc", "hsc_shear_calibration"),
        ("KIDS", "kids", "kids_shear_response"),
    ):
        row = _validate_nested_identity(
            children[survey],
            field_name=f"{survey} child identity",
            expected_fields=child_fields,
            identity_field="child_identity_id",
            component_bindings=bindings,
        )
        if row["survey_id"] != survey:
            raise DataIdentityError(f"{survey} child survey identity drifted")
        for field_name, expected in (
            ("product_component_id", f"{prefix}_product"),
            ("mask_component_id", f"{prefix}_mask"),
            ("randoms_component_id", f"{prefix}_randoms"),
            ("psf_component_id", f"{prefix}_psf"),
            ("n_z_component_id", f"{prefix}_n_z"),
            ("calibration_or_response_component_id", calibration),
            ("covariance_component_id", f"{prefix}_covariance"),
        ):
            _validate_component_reference(
                row[field_name],
                field_name=f"{survey} {field_name}",
                expected=expected,
                available=available,
            )
        checked_children[survey] = row
    for field_name in (
        "product_component_id",
        "mask_component_id",
        "randoms_component_id",
        "psf_component_id",
        "n_z_component_id",
        "calibration_or_response_component_id",
        "covariance_component_id",
    ):
        if checked_children["HSC"][field_name] == checked_children["KIDS"][field_name]:
            raise DataIdentityError(f"HSC and KiDS share forbidden {field_name}")
    cross = _validate_nested_identity(
        profile["cross_covariance"],
        field_name="HSC/KiDS cross covariance",
        expected_fields=frozenset(
            {
                "component_id",
                "hsc_child_identity_id",
                "kids_child_identity_id",
                "covariance_id",
            }
        ),
        identity_field="cross_covariance_identity",
        component_bindings=bindings,
    )
    _validate_component_reference(
        cross["component_id"],
        field_name="HSC/KiDS cross covariance component_id",
        expected="hsc_kids_cross_covariance",
        available=available,
    )
    if (
        cross["hsc_child_identity_id"]
        != checked_children["HSC"]["child_identity_id"]
        or cross["kids_child_identity_id"]
        != checked_children["KIDS"]["child_identity_id"]
        or cross["covariance_id"] != evidence["covariance_id"]
        or evidence["covariance_status"] != "REGISTERED"
    ):
        raise DataIdentityError("HSC/KiDS cross-covariance relationship drifted")


def validate_native_identity_profile(
    *,
    lane: LaneSpec,
    profile: Mapping[str, object],
    components: Sequence[Mapping[str, object]],
    evidence: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(profile, Mapping):
        raise DataIdentityError("native identity profile must be a mapping")
    common = {"schema", "lane_id", "product_id", "component_bindings", "profile_id"}
    lane_specific = {
        "PLANCK": {"pipelines", "same_sky_pair", "ffp10_null"},
        "CF4": {"catalogue", "semantics"},
        "HSC_KIDS": {"children", "cross_covariance"},
    }.get(lane.lane_id, set())
    checked = _exact_mapping(
        profile,
        field_name=f"{lane.lane_id} native identity profile",
        expected=frozenset(common | lane_specific),
    )
    if (
        checked["schema"] != lane.native_identity_schema
        or checked["lane_id"] != lane.lane_id
        or checked["product_id"] != lane.product_id
    ):
        raise DataIdentityError("native identity profile authority drifted")
    raw_bindings = checked["component_bindings"]
    if isinstance(raw_bindings, (str, bytes)) or not isinstance(
        raw_bindings, Sequence
    ):
        raise DataIdentityError("native component bindings must be a sequence")
    normalized_bindings: list[dict[str, object]] = []
    for index, value in enumerate(raw_bindings):
        row = _exact_mapping(
            value,
            field_name=f"native component binding {index}",
            expected=_NATIVE_BINDING_FIELDS,
        )
        ordinal = row["ordinal"]
        byte_size = row["byte_size"]
        if type(ordinal) is not int or ordinal < 0:
            raise DataIdentityError("native component ordinal is invalid")
        if type(byte_size) is not int or byte_size <= 0:
            raise DataIdentityError("native component byte_size is invalid")
        normalized_bindings.append(
            {
                "component_id": _text(row["component_id"], "component_id"),
                "ordinal": ordinal,
                "relative_path": _relative_path(
                    row["relative_path"], "native component relative_path"
                ).as_posix(),
                "byte_size": byte_size,
                "content_sha256": "sha256:"
                + _raw_sha(row["content_sha256"], "native content_sha256"),
            }
        )
    expected_bindings = _native_component_bindings(components)
    if normalized_bindings != expected_bindings:
        raise DataIdentityError("native component bindings drifted")
    expected_ids = tuple(row["component_id"] for row in expected_bindings)
    if expected_ids != lane.expected_component_sequence:
        raise DataIdentityError("native component role inventory drifted")
    available = frozenset(expected_ids)
    _validate_profile_id(checked)
    if lane.lane_id == "PLANCK":
        _validate_planck_native_profile(checked, evidence=evidence, available=available)
    elif lane.lane_id == "CF4":
        _validate_cf4_native_profile(checked, evidence=evidence, available=available)
    elif lane.lane_id == "HSC_KIDS":
        _validate_hsc_kids_native_profile(
            checked, evidence=evidence, available=available
        )
    return json.loads(_canonical_bytes(checked).decode("ascii"))


def _with_content_identity(
    payload: Mapping[str, object],
    identity_field: str,
    *,
    component_bindings: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    unsigned = dict(payload)
    return {
        **unsigned,
        identity_field: _relationship_content_identity(
            unsigned, component_bindings=component_bindings
        ),
    }


def _build_registered_native_profile(
    lane: LaneSpec,
    components: Sequence[Mapping[str, object]],
    evidence: Mapping[str, object],
) -> dict[str, object]:
    common: dict[str, object] = {
        "schema": lane.native_identity_schema,
        "lane_id": lane.lane_id,
        "product_id": lane.product_id,
        "component_bindings": _native_component_bindings(components),
    }
    bindings = common["component_bindings"]
    if lane.lane_id == "PLANCK":
        pipelines = {}
        for name, prefix in (("SMICA", "smica"), ("COMMANDER", "commander")):
            pipelines[name] = _with_content_identity(
                {
                    "pipeline": name,
                    "map_component_id": f"{prefix}_map",
                    "mask_component_id": f"{prefix}_mask",
                    "beam_component_id": f"{prefix}_beam",
                    "window_operator_component_id": f"{prefix}_window_operator",
                    "covariance_component_id": f"{prefix}_covariance",
                    "pixelization_component_id": "pixelization",
                    "native_selection_component_id": "native_selection",
                    "sky_support_id": evidence["sky_support_id"],
                    "harmonic_convention_id": evidence["harmonic_convention_id"],
                },
                "pipeline_identity",
                component_bindings=bindings,
            )
        pair = _with_content_identity(
            {
                "smica_map_component_id": "smica_map",
                "commander_map_component_id": "commander_map",
                "sky_support_id": evidence["sky_support_id"],
                "pixelization_component_id": "pixelization",
            },
            "pair_id",
            component_bindings=bindings,
        )
        ffp10 = _with_content_identity(
            {
                "ensemble_kind": "FFP10",
                "inventory_component_id": "ffp10_null_inventory",
                "null_ensemble_id": evidence["null_ensemble_id"],
            },
            "null_identity",
            component_bindings=bindings,
        )
        return _with_content_identity(
            {
                **common,
                "pipelines": pipelines,
                "same_sky_pair": pair,
                "ffp10_null": ffp10,
            },
            "profile_id",
        )
    if lane.lane_id == "CF4":
        catalogue = _with_content_identity(
            {
                "catalogue_component_id": "catalogue",
                "row_selection_component_id": "row_selection",
                "covariance_component_id": "covariance",
                "row_selection_id": evidence["selection_id"],
                "covariance_id": evidence["covariance_id"],
            },
            "catalogue_identity",
            component_bindings=bindings,
        )
        semantics = _with_content_identity(
            {
                "frame_component_id": "frame_definition",
                "sign_component_id": "sign_convention",
                "units_component_id": "units_contract",
                "grouping_component_id": "grouping_definition",
                "depth_component_id": "depth_definition",
                "zoa_component_id": "zoa_definition",
                "coordinate_frame_id": evidence["coordinate_frame_id"],
                "sign_orientation_convention_id": evidence[
                    "sign_orientation_convention_id"
                ],
                "units_contract_id": evidence["units_contract_id"],
            },
            "semantics_identity",
            component_bindings=bindings,
        )
        return _with_content_identity(
            {**common, "catalogue": catalogue, "semantics": semantics},
            "profile_id",
        )
    if lane.lane_id == "HSC_KIDS":
        children = {}
        for survey, prefix, calibration in (
            ("HSC", "hsc", "hsc_shear_calibration"),
            ("KIDS", "kids", "kids_shear_response"),
        ):
            children[survey] = _with_content_identity(
                {
                    "survey_id": survey,
                    "product_component_id": f"{prefix}_product",
                    "mask_component_id": f"{prefix}_mask",
                    "randoms_component_id": f"{prefix}_randoms",
                    "psf_component_id": f"{prefix}_psf",
                    "n_z_component_id": f"{prefix}_n_z",
                    "calibration_or_response_component_id": calibration,
                    "covariance_component_id": f"{prefix}_covariance",
                },
                "child_identity_id",
                component_bindings=bindings,
            )
        cross = _with_content_identity(
            {
                "component_id": "hsc_kids_cross_covariance",
                "hsc_child_identity_id": children["HSC"]["child_identity_id"],
                "kids_child_identity_id": children["KIDS"]["child_identity_id"],
                "covariance_id": evidence["covariance_id"],
            },
            "cross_covariance_identity",
            component_bindings=bindings,
        )
        return _with_content_identity(
            {**common, "children": children, "cross_covariance": cross},
            "profile_id",
        )
    return _with_content_identity(common, "profile_id")


def compute_source_locator_identity(
    *,
    lane_id: str,
    product_id: str,
    components: Sequence[Mapping[str, object]],
    evidence_bindings: Mapping[str, object],
) -> str:
    stable_evidence = {
        key: evidence_bindings[key]
        for key in (
            "release_name",
            "release_version",
            "release_identity",
            "license_identity",
            "license_status",
            "native_identity_profile",
        )
    }
    component_rows = []
    for row in components:
        checked = _exact_mapping(
            row, field_name="component descriptor", expected=_COMPONENT_FIELDS
        )
        size = checked["byte_size"]
        if type(size) is not int or size <= 0:
            raise DataIdentityError("component byte_size must be a positive integer")
        component_rows.append(
            {
                "component_id": _text(checked["component_id"], "component_id"),
                "relative_path": _relative_path(
                    checked["relative_path"], "component relative_path"
                ).as_posix(),
                "byte_size": size,
                "content_sha256": "sha256:"
                + _raw_sha(
                    checked["content_sha256"], "component content_sha256"
                ),
            }
        )
    return canonical_sha256(
        {
            "domain": "PR289_ROOT_DESCRIPTOR_V2",
            "lane_id": _text(lane_id, "lane_id"),
            "product_id": _text(product_id, "product_id"),
            "components": component_rows,
            "evidence": stable_evidence,
        }
    )


@dataclass(frozen=True)
class DataIdentityRecordV2:
    record_id: str
    inspection_receipt_id: str
    lane_id: str
    product_id: str
    component_id: str
    component_ordinal: int
    source_locator_kind: str
    source_locator_identity: str
    release_name: str
    release_version: str
    release_identity: str
    license_identity: str
    regular_file_status: str
    symlink_status: str
    byte_size: int
    content_sha256: str
    component_inventory_id: str
    completeness_status: str
    units_contract_id: str
    coordinate_frame_id: str
    sign_orientation_convention_id: str
    directional_convention_id: str
    harmonic_convention_id: str
    mask_id: str
    selection_id: str
    sky_support_id: str
    covariance_id: str
    covariance_status: str
    null_ensemble_id: str
    null_ensemble_status: str
    transfer_source: str
    transfer_function_spec_id: str
    transfer_provenance_status: str
    sky_support_status: str
    license_status: str
    native_identity_profile_id: str
    native_identity_profile: Mapping[str, object]
    acquisition_status: str
    inspected_at_utc: str
    _construction_token: InitVar[object] = None
    _seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RECORD_TOKEN:
            raise DataIdentityError("DataIdentityRecordV2 must be factory-built")
        if self.record_id != canonical_sha256(self._stable_payload()):
            raise DataIdentityError("record_id does not bind the stable identity")
        if self.inspection_receipt_id != canonical_sha256(
            self._inspection_payload()
        ):
            raise DataIdentityError(
                "inspection_receipt_id does not bind the inspection"
            )
        if (
            not isinstance(self.native_identity_profile, Mapping)
            or self.native_identity_profile_id
            != self.native_identity_profile.get("profile_id")
        ):
            raise DataIdentityError("record native identity profile drifted")
        _canonical_bytes(self.native_identity_profile)
        object.__setattr__(self, "_seal", canonical_sha256(self.as_payload()))

    def _stable_payload(self) -> dict[str, object]:
        payload = self.as_payload_unchecked()
        for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
            payload.pop(key)
        return payload

    def _inspection_payload(self) -> dict[str, object]:
        payload = self.as_payload_unchecked()
        payload.pop("inspection_receipt_id")
        return payload

    def as_payload_unchecked(self) -> dict[str, object]:
        return {
            "schema": DATA_IDENTITY_RECORD_SCHEMA,
            **{
                name: getattr(self, name)
                for name in self.__dataclass_fields__
                if not name.startswith("_")
            },
        }

    def as_payload(self) -> dict[str, object]:
        payload = self.as_payload_unchecked()
        if hasattr(self, "_seal") and canonical_sha256(payload) != self._seal:
            raise DataIdentityError("data identity record drifted")
        return payload


def _build_record(
    *,
    lane: LaneSpec,
    component: Mapping[str, object],
    component_ordinal: int,
    evidence: Mapping[str, object],
    inventory_id: str,
    native_profile: Mapping[str, object],
    inspected_at_utc: str,
) -> DataIdentityRecordV2:
    shared = {
        "lane_id": lane.lane_id,
        "product_id": lane.product_id,
        "component_id": _text(component["component_id"], "component_id"),
        "component_ordinal": component_ordinal,
        "source_locator_kind": "absolute_local_root",
        "source_locator_identity": _text(
            evidence["source_locator_identity"], "source_locator_identity"
        ),
        "release_name": _text(evidence["release_name"], "release_name"),
        "release_version": _release_version(evidence["release_version"]),
        "release_identity": _identity(
            evidence["release_identity"], "release_identity", _IDENTITY_PREFIXES
        ),
        "license_identity": _identity(
            evidence["license_identity"], "license_identity", _LICENSE_PREFIXES
        ),
        "regular_file_status": "REGULAR_FILE_VERIFIED",
        "symlink_status": "NO_SYMLINK_OR_ALIAS",
        "byte_size": component["byte_size"],
        "content_sha256": "sha256:"
        + _raw_sha(component["content_sha256"], "content_sha256"),
        "component_inventory_id": inventory_id,
        "completeness_status": "COMPLETE_LANE_COMPONENT",
        **{
            field_name: evidence[field_name]
            for field_name in (
                "units_contract_id",
                "coordinate_frame_id",
                "sign_orientation_convention_id",
                "directional_convention_id",
                "harmonic_convention_id",
                "mask_id",
                "selection_id",
                "sky_support_id",
                "covariance_id",
                "covariance_status",
                "null_ensemble_id",
                "null_ensemble_status",
                "transfer_source",
                "transfer_function_spec_id",
                "transfer_provenance_status",
                "sky_support_status",
                "license_status",
            )
        },
        "acquisition_status": "COMPLETE",
        "native_identity_profile_id": native_profile["profile_id"],
        "native_identity_profile": json.loads(
            _canonical_bytes(native_profile).decode("ascii")
        ),
        "inspected_at_utc": inspected_at_utc,
    }
    provisional = {
        "schema": DATA_IDENTITY_RECORD_SCHEMA,
        "record_id": "",
        "inspection_receipt_id": "",
        **shared,
    }
    stable = dict(provisional)
    for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
        stable.pop(key)
    record_id = canonical_sha256(stable)
    provisional["record_id"] = record_id
    inspection = dict(provisional)
    inspection.pop("inspection_receipt_id")
    inspection_id = canonical_sha256(inspection)
    return DataIdentityRecordV2(
        record_id=record_id,
        inspection_receipt_id=inspection_id,
        _construction_token=_RECORD_TOKEN,
        **shared,
    )


@dataclass(frozen=True)
class LaneAdmissionDecision:
    lane_id: str
    product_id: str
    status: AdmissionStatus
    reasons: tuple[str, ...]
    records: tuple[DataIdentityRecordV2, ...]
    lane_admission_bundle_id: str | None

    @property
    def complete(self) -> bool:
        return self.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY

    def as_payload(self) -> dict[str, object]:
        return {
            "lane_id": self.lane_id,
            "product_id": self.product_id,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "records": [record.as_payload() for record in self.records],
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
        }


def _decision(
    lane: LaneSpec,
    issues: Sequence[tuple[AdmissionStatus, str]],
    records: Sequence[DataIdentityRecordV2] = (),
    bundle_id: str | None = None,
) -> LaneAdmissionDecision:
    applicable = {status.value for status, _ in issues}
    selected = next(
        AdmissionStatus(value)
        for value in _STATUS_PRECEDENCE
        if value in applicable
        or (not applicable and value == "ADMITTED_IDENTITY_ONLY")
    )
    if selected is not AdmissionStatus.ADMITTED_IDENTITY_ONLY:
        records = ()
        bundle_id = None
    return LaneAdmissionDecision(
        lane_id=lane.lane_id,
        product_id=lane.product_id,
        status=selected,
        reasons=tuple(reason for _, reason in issues),
        records=tuple(records),
        lane_admission_bundle_id=bundle_id,
    )


def _validate_evidence(
    lane: LaneSpec,
    evidence: Mapping[str, object],
    *,
    components: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    _exact_mapping(
        evidence, field_name="identity evidence", expected=_EVIDENCE_FIELDS
    )
    if evidence["schema"] != DATA_IDENTITY_EVIDENCE_SCHEMA:
        raise DataIdentityError("identity evidence schema drifted")
    if (
        evidence["lane_id"] != lane.lane_id
        or evidence["product_id"] != lane.product_id
    ):
        raise DataIdentityError("identity evidence lane or product drifted")
    _text(evidence["release_name"], "release_name")
    _release_version(evidence["release_version"])
    _identity(
        evidence["release_identity"], "release_identity", _IDENTITY_PREFIXES
    )
    _identity(
        evidence["license_identity"], "license_identity", _LICENSE_PREFIXES
    )
    if evidence["license_status"] != "BOUND":
        raise DataIdentityError("license_status must be BOUND")
    for field_name in (
        "units_contract_id",
        "coordinate_frame_id",
        "sign_orientation_convention_id",
        "directional_convention_id",
        "harmonic_convention_id",
        "mask_id",
        "selection_id",
        "sky_support_id",
        "covariance_id",
        "null_ensemble_id",
    ):
        _text(evidence[field_name], field_name)
    if evidence["covariance_status"] not in {"REGISTERED", "NOT_APPLICABLE"}:
        raise DataIdentityError("covariance_status is unregistered")
    if evidence["null_ensemble_status"] not in {
        "REGISTERED",
        "NOT_APPLICABLE",
        "UNAVAILABLE_DECLARED",
    }:
        raise DataIdentityError("null_ensemble_status is unregistered")
    if evidence["sky_support_status"] not in {
        "REGISTERED",
        "NOT_APPLICABLE",
    }:
        raise DataIdentityError("sky_support_status is unregistered")
    transfer_source = _text(evidence["transfer_source"], "transfer_source")
    if transfer_source not in lane.allowed_transfer_sources:
        raise DataIdentityError("transfer_source is not allowed for the lane")
    if transfer_source == "none" and (
        evidence["transfer_function_spec_id"] != "none"
        or evidence["transfer_provenance_status"] != "NOT_APPLICABLE"
    ):
        raise DataIdentityError(
            "observer-side transfer status contradicts identity"
        )
    expected_locator = compute_source_locator_identity(
        lane_id=lane.lane_id,
        product_id=lane.product_id,
        components=components,
        evidence_bindings=evidence,
    )
    if evidence["source_locator_identity"] != expected_locator:
        raise DataIdentityError("source_locator_identity drifted")
    return validate_native_identity_profile(
        lane=lane,
        profile=evidence["native_identity_profile"],
        components=components,
        evidence=evidence,
    )


def evaluate_lane_identity(
    *,
    registry: LaneRegistryV2,
    lane_id: str,
    descriptor: Mapping[str, object] | None,
    inspected_at_utc: str,
) -> LaneAdmissionDecision:
    lane = registry.lane(lane_id)
    inspected = _utc(inspected_at_utc, "inspected_at_utc")
    if descriptor is None:
        return _decision(
            lane,
            (
                (
                    AdmissionStatus.REJECTED_NOT_PRESENT,
                    "candidate root not supplied",
                ),
            ),
        )
    try:
        checked = _exact_mapping(
            descriptor,
            field_name=f"{lane_id} root descriptor",
            expected=_DESCRIPTOR_FIELDS,
        )
    except DataIdentityError as exc:
        return _decision(
            lane, ((AdmissionStatus.REJECTED_IDENTITY_MISMATCH, str(exc)),)
        )
    issues: list[tuple[AdmissionStatus, str]] = []
    if lane.name_only_forbidden and checked["name_only"] is True:
        issues.append(
            (
                AdmissionStatus.REJECTED_NAME_ONLY,
                "name-only lane input is forbidden",
            )
        )
    if type(checked["name_only"]) is not bool:
        issues.append(
            (
                AdmissionStatus.REJECTED_IDENTITY_MISMATCH,
                "name_only must be boolean",
            )
        )
    acquisition = checked["acquisition_status"]
    if lane_id == "DESI" and acquisition != "COMPLETE":
        issues.append(
            (
                AdmissionStatus.BLOCKED_PR151_INCOMPLETE,
                "DESI/PR-151 acquisition is incomplete or mutable",
            )
        )
    elif acquisition != "COMPLETE":
        issues.append(
            (
                AdmissionStatus.REJECTED_IDENTITY_MISMATCH,
                "acquisition_status must equal COMPLETE",
            )
        )
    root_value = checked["root"]
    if not isinstance(root_value, str) or not root_value:
        issues.append(
            (AdmissionStatus.REJECTED_NOT_PRESENT, "candidate root is absent")
        )
        return _decision(lane, issues)
    root = Path(root_value)
    if not root.is_absolute():
        issues.append(
            (
                AdmissionStatus.BLOCKED_PATH_ESCAPE_OR_MUTATION,
                "candidate root must be absolute",
            )
        )
        return _decision(lane, issues)
    try:
        root_info = root.lstat()
    except FileNotFoundError:
        issues.append(
            (
                AdmissionStatus.REJECTED_NOT_PRESENT,
                "candidate root does not exist",
            )
        )
        return _decision(lane, issues)
    if stat.S_ISLNK(root_info.st_mode):
        issues.append(
            (
                AdmissionStatus.BLOCKED_PATH_ESCAPE_OR_MUTATION,
                "candidate root is a symlink alias",
            )
        )
        return _decision(lane, issues)
    if not stat.S_ISDIR(root_info.st_mode) or root.resolve() != root:
        issues.append(
            (
                AdmissionStatus.BLOCKED_PATH_ESCAPE_OR_MUTATION,
                "candidate root is not a canonical directory",
            )
        )
        return _decision(lane, issues)
    components = checked["components"]
    if isinstance(components, (str, bytes)) or not isinstance(
        components, Sequence
    ):
        issues.append(
            (
                AdmissionStatus.REJECTED_INCOMPLETE_COMPONENT_SET,
                "component inventory is not a sequence",
            )
        )
        return _decision(lane, issues)
    try:
        normalized_components = [
            dict(
                _exact_mapping(
                    row,
                    field_name=f"{lane_id} component {index}",
                    expected=_COMPONENT_FIELDS,
                )
            )
            for index, row in enumerate(components)
        ]
        observed_ids = tuple(row["component_id"] for row in normalized_components)
        if observed_ids != lane.expected_component_sequence:
            raise DataIdentityError("component inventory count or order drifted")
        inventory_id = component_inventory_id(normalized_components)
    except DataIdentityError as exc:
        issues.append(
            (AdmissionStatus.REJECTED_INCOMPLETE_COMPONENT_SET, str(exc))
        )
        return _decision(lane, issues)
    seen_inodes: set[tuple[int, int]] = set()
    for row in normalized_components:
        try:
            relative = _relative_path(
                row["relative_path"], "component relative_path"
            )
            if lane_id == "DESI" and (
                relative.name.endswith((".part", ".aria2"))
                or "unfinished" in relative.as_posix().casefold()
            ):
                issues.append(
                    (
                        AdmissionStatus.BLOCKED_PR151_INCOMPLETE,
                        f"partial DESI component is forbidden: {relative}",
                    )
                )
                continue
            path, info = _regular_beneath(root, relative, "component")
            inode = (info.st_dev, info.st_ino)
            if inode in seen_inodes:
                raise DataIdentityError("component inode is duplicated")
            seen_inodes.add(inode)
            if info.st_size <= 0 or info.st_size != row["byte_size"]:
                raise DataIdentityError("component byte_size drifted")
            if _stream_sha256(
                path, field_name="component", expected_info=info
            ) != _raw_sha(
                row["content_sha256"], "component content_sha256"
            ):
                raise DataIdentityError("component content_sha256 drifted")
        except DataIdentityError as exc:
            text = str(exc)
            if "symlink" in text or "hardlink" in text or "inode" in text:
                status_value = AdmissionStatus.REJECTED_SYMLINK_OR_ALIAS
            elif "is missing" in text:
                status_value = AdmissionStatus.REJECTED_INCOMPLETE_COMPONENT_SET
            elif "regular file" in text:
                status_value = AdmissionStatus.REJECTED_NOT_REGULAR_FILE
            elif "escapes" in text or "canonical" in text:
                status_value = AdmissionStatus.BLOCKED_PATH_ESCAPE_OR_MUTATION
            else:
                status_value = AdmissionStatus.REJECTED_IDENTITY_MISMATCH
            issues.append((status_value, text))
    if issues:
        return _decision(lane, issues)
    try:
        evidence_relative = _relative_path(
            checked["evidence_relative_path"], "evidence_relative_path"
        )
        evidence_path, evidence_info = _regular_beneath(
            root, evidence_relative, "identity evidence"
        )
        evidence_raw = _read_regular_bytes(
            evidence_path,
            field_name="identity evidence",
            expected_info=evidence_info,
        )
        if hashlib.sha256(evidence_raw).hexdigest() != _raw_sha(
            checked["evidence_sha256"], "evidence_sha256"
        ):
            raise DataIdentityError("identity evidence hash drifted")
        evidence = _strict_json_bytes(
            evidence_raw, field_name="identity evidence"
        )
        native_profile = _validate_evidence(
            lane, evidence, components=normalized_components
        )
    except DataIdentityError as exc:
        text = str(exc)
        if "symlink" in text or "hardlink" in text:
            status_value = AdmissionStatus.REJECTED_SYMLINK_OR_ALIAS
        elif "release" in text or "license" in text:
            status_value = AdmissionStatus.REJECTED_MISSING_RELEASE_OR_LICENSE
        else:
            status_value = AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT
        return _decision(lane, ((status_value, text),))
    role_ordinals: dict[str, int] = {}
    record_rows = []
    for row in normalized_components:
        component_id = _text(row["component_id"], "component_id")
        component_ordinal = role_ordinals.get(component_id, 0)
        role_ordinals[component_id] = component_ordinal + 1
        record_rows.append(
            _build_record(
                lane=lane,
                component=row,
                component_ordinal=component_ordinal,
                evidence=evidence,
                inventory_id=inventory_id,
                native_profile=native_profile,
                inspected_at_utc=inspected,
            )
        )
    records = tuple(record_rows)
    bundle_id = canonical_sha256(
        {
            "lane_id": lane.lane_id,
            "product_id": lane.product_id,
            "component_inventory_id": inventory_id,
            "record_ids": [record.record_id for record in records],
        }
    )
    return _decision(lane, (), records, bundle_id)


def validate_data_identity_record_payload(
    payload: Mapping[str, object], *, registry: LaneRegistryV2
) -> DataIdentityRecordV2:
    public_fields = frozenset(
        name
        for name in DataIdentityRecordV2.__dataclass_fields__
        if not name.startswith("_")
    )
    checked = _exact_mapping(
        payload,
        field_name="data identity record payload",
        expected=public_fields | {"schema"},
    )
    if checked["schema"] != DATA_IDENTITY_RECORD_SCHEMA:
        raise DataIdentityError("data identity record schema drifted")
    lane_id = _text(checked["lane_id"], "lane_id")
    lane = registry.lane(lane_id)
    if checked["product_id"] != lane.product_id:
        raise DataIdentityError("data identity record product drifted")
    profile = checked["native_identity_profile"]
    if not isinstance(profile, Mapping):
        raise DataIdentityError("record native identity profile is malformed")
    bindings = profile.get("component_bindings")
    if isinstance(bindings, (str, bytes)) or not isinstance(bindings, Sequence):
        raise DataIdentityError("record native component bindings are malformed")
    replay_components: list[dict[str, object]] = []
    for index, value in enumerate(bindings):
        row = _exact_mapping(
            value,
            field_name=f"record native binding {index}",
            expected=_NATIVE_BINDING_FIELDS,
        )
        replay_components.append(
            {
                "component_id": row["component_id"],
                "relative_path": row["relative_path"],
                "byte_size": row["byte_size"],
                "content_sha256": row["content_sha256"],
            }
        )
    if checked["source_locator_kind"] != "absolute_local_root":
        raise DataIdentityError("record source locator kind drifted")
    for field_name, expected in (
        ("regular_file_status", "REGULAR_FILE_VERIFIED"),
        ("symlink_status", "NO_SYMLINK_OR_ALIAS"),
        ("completeness_status", "COMPLETE_LANE_COMPONENT"),
        ("acquisition_status", "COMPLETE"),
    ):
        if checked[field_name] != expected:
            raise DataIdentityError(f"record {field_name} drifted")
    evidence = {
        "schema": DATA_IDENTITY_EVIDENCE_SCHEMA,
        "lane_id": lane.lane_id,
        "product_id": lane.product_id,
        **{
            field_name: checked[field_name]
            for field_name in _EVIDENCE_FIELDS
            if field_name not in {"schema", "lane_id", "product_id"}
        },
    }
    normalized_profile = _validate_evidence(
        lane, evidence, components=replay_components
    )
    if checked["native_identity_profile_id"] != normalized_profile["profile_id"]:
        raise DataIdentityError("record native identity profile_id drifted")
    expected_inventory_id = component_inventory_id(replay_components)
    if checked["component_inventory_id"] != expected_inventory_id:
        raise DataIdentityError("record component inventory identity drifted")
    component_ordinal = checked["component_ordinal"]
    if type(component_ordinal) is not int or component_ordinal < 0:
        raise DataIdentityError("record component ordinal is invalid")
    own_matches = [
        row
        for row in bindings
        if row["component_id"] == checked["component_id"]
        and row["ordinal"] == component_ordinal
        and row["byte_size"] == checked["byte_size"]
        and "sha256:"
        + _raw_sha(row["content_sha256"], "record binding content_sha256")
        == "sha256:"
        + _raw_sha(checked["content_sha256"], "record content_sha256")
    ]
    if len(own_matches) != 1:
        raise DataIdentityError("record does not bind one native component role")
    _utc(checked["inspected_at_utc"], "inspected_at_utc")
    kwargs = {
        name: checked[name]
        for name in public_fields
    }
    kwargs["native_identity_profile"] = normalized_profile
    return DataIdentityRecordV2(
        **kwargs,
        _construction_token=_RECORD_TOKEN,
    )


def replay_lane_admission_decision(
    payload: Mapping[str, object], *, registry: LaneRegistryV2
) -> LaneAdmissionDecision:
    checked = _exact_mapping(
        payload,
        field_name="lane admission decision payload",
        expected=frozenset(
            {
                "lane_id",
                "product_id",
                "status",
                "reasons",
                "records",
                "lane_admission_bundle_id",
            }
        ),
    )
    lane = registry.lane(_text(checked["lane_id"], "lane_id"))
    if checked["product_id"] != lane.product_id:
        raise DataIdentityError("lane admission product identity drifted")
    try:
        status_value = AdmissionStatus(_text(checked["status"], "status"))
    except ValueError as exc:
        raise DataIdentityError("lane admission status is unregistered") from exc
    reasons_value = checked["reasons"]
    records_value = checked["records"]
    if (
        isinstance(reasons_value, (str, bytes))
        or not isinstance(reasons_value, Sequence)
        or isinstance(records_value, (str, bytes))
        or not isinstance(records_value, Sequence)
    ):
        raise DataIdentityError("lane admission sequences are malformed")
    reasons = tuple(_text(value, "lane admission reason") for value in reasons_value)
    records = tuple(
        validate_data_identity_record_payload(value, registry=registry)
        for value in records_value
    )
    bundle_id = checked["lane_admission_bundle_id"]
    if status_value is AdmissionStatus.ADMITTED_IDENTITY_ONLY:
        if reasons or tuple(record.component_id for record in records) != (
            lane.expected_component_sequence
        ):
            raise DataIdentityError("admitted native record inventory drifted")
        if len({record.native_identity_profile_id for record in records}) != 1:
            raise DataIdentityError("admitted native profiles disagree")
        profile_bindings = records[0].native_identity_profile[
            "component_bindings"
        ]
        expected_role_ordinals = tuple(
            (row["component_id"], row["ordinal"])
            for row in profile_bindings
        )
        observed_role_ordinals = tuple(
            (record.component_id, record.component_ordinal)
            for record in records
        )
        if observed_role_ordinals != expected_role_ordinals:
            raise DataIdentityError(
                "admitted native record ordinal inventory drifted"
            )
        shared_fields = tuple(
            name
            for name in DataIdentityRecordV2.__dataclass_fields__
            if not name.startswith("_")
            and name
            not in {
                "record_id",
                "inspection_receipt_id",
                "component_id",
                "component_ordinal",
                "byte_size",
                "content_sha256",
            }
        )
        reference = tuple(getattr(records[0], name) for name in shared_fields)
        if any(
            tuple(getattr(record, name) for name in shared_fields) != reference
            for record in records[1:]
        ):
            raise DataIdentityError("admitted native record semantics disagree")
        inventory_ids = {record.component_inventory_id for record in records}
        if len(inventory_ids) != 1:
            raise DataIdentityError("admitted component inventories disagree")
        expected_bundle = canonical_sha256(
            {
                "lane_id": lane.lane_id,
                "product_id": lane.product_id,
                "component_inventory_id": next(iter(inventory_ids)),
                "record_ids": [record.record_id for record in records],
            }
        )
        if bundle_id != expected_bundle:
            raise DataIdentityError("lane admission bundle identity drifted")
    elif records or bundle_id is not None:
        raise DataIdentityError("refused lane retained admitted native records")
    return LaneAdmissionDecision(
        lane_id=lane.lane_id,
        product_id=lane.product_id,
        status=status_value,
        reasons=reasons,
        records=records,
        lane_admission_bundle_id=bundle_id,
    )


@dataclass(frozen=True)
class ExecutionAuthorizationReceipt:
    authorization_id: str
    lane_id: str
    exact_admission_record_ids: tuple[str, ...]
    lane_admission_bundle_id: str | None
    analysis_plan_id: str
    required_human_gate_id: str
    human_gate_receipt_id: None
    human_authority_identity: None
    authorized_scope: None
    issued_at_utc: None
    expires_at_utc: None
    status: AuthorizationStatus
    authorization_domain: str
    _construction_token: InitVar[object] = None
    _seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _AUTH_TOKEN:
            raise DataIdentityError(
                "ExecutionAuthorizationReceipt must be factory-built"
            )
        if (
            self.status is not AuthorizationStatus.NOT_AUTHORIZED
            or self.human_gate_receipt_id is not None
            or self.human_authority_identity is not None
            or self.authorized_scope is not None
            or self.issued_at_utc is not None
            or self.expires_at_utc is not None
            or self.authorization_domain != AUTHORIZATION_DOMAIN
        ):
            raise DataIdentityError("PR-289 cannot construct authorization")
        if self.authorization_id != canonical_sha256(self._unsigned_payload()):
            raise DataIdentityError("authorization_id drifted")
        object.__setattr__(self, "_seal", canonical_sha256(self.as_payload()))

    def _unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": AUTHORIZATION_RECEIPT_SCHEMA,
            "lane_id": self.lane_id,
            "exact_admission_record_ids": list(
                self.exact_admission_record_ids
            ),
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
            "analysis_plan_id": self.analysis_plan_id,
            "required_human_gate_id": self.required_human_gate_id,
            "human_gate_receipt_id": self.human_gate_receipt_id,
            "human_authority_identity": self.human_authority_identity,
            "authorized_scope": self.authorized_scope,
            "issued_at_utc": self.issued_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "status": self.status.value,
            "authorization_domain": self.authorization_domain,
        }

    def as_payload(self) -> dict[str, object]:
        payload = {
            "authorization_id": self.authorization_id,
            **self._unsigned_payload(),
        }
        if hasattr(self, "_seal") and canonical_sha256(payload) != self._seal:
            raise DataIdentityError("execution authorization receipt drifted")
        return payload


def build_not_authorized_receipt(
    lane: LaneSpec, decision: LaneAdmissionDecision
) -> ExecutionAuthorizationReceipt:
    if (
        decision.lane_id != lane.lane_id
        or decision.product_id != lane.product_id
    ):
        raise DataIdentityError("authorization lane decision identity drifted")
    if decision.complete:
        if decision.reasons:
            raise DataIdentityError(
                "admitted authorization decision retained refusal reasons"
            )
        expected_roles: list[tuple[str, int]] = []
        role_ordinals: dict[str, int] = {}
        for component_id in lane.expected_component_sequence:
            ordinal = role_ordinals.get(component_id, 0)
            role_ordinals[component_id] = ordinal + 1
            expected_roles.append((component_id, ordinal))
        observed_roles = tuple(
            (record.component_id, record.component_ordinal)
            for record in decision.records
        )
        if observed_roles != tuple(expected_roles) or any(
            record.lane_id != lane.lane_id
            or record.product_id != lane.product_id
            for record in decision.records
        ):
            raise DataIdentityError(
                "authorization admission record inventory drifted"
            )
        for record in decision.records:
            record.as_payload()
        inventory_ids = {
            record.component_inventory_id for record in decision.records
        }
        if len(inventory_ids) != 1:
            raise DataIdentityError(
                "authorization admission inventory identity drifted"
            )
        expected_bundle = canonical_sha256(
            {
                "lane_id": lane.lane_id,
                "product_id": lane.product_id,
                "component_inventory_id": next(iter(inventory_ids)),
                "record_ids": [
                    record.record_id for record in decision.records
                ],
            }
        )
        if decision.lane_admission_bundle_id != expected_bundle:
            raise DataIdentityError(
                "authorization admission bundle identity drifted"
            )
    elif decision.records or decision.lane_admission_bundle_id is not None:
        raise DataIdentityError(
            "refused authorization decision retained admitted identity"
        )
    record_ids = (
        tuple(record.record_id for record in decision.records)
        if decision.complete
        else ()
    )
    bundle_id = (
        decision.lane_admission_bundle_id if decision.complete else None
    )
    unsigned = {
        "schema": AUTHORIZATION_RECEIPT_SCHEMA,
        "lane_id": lane.lane_id,
        "exact_admission_record_ids": list(record_ids),
        "lane_admission_bundle_id": bundle_id,
        "analysis_plan_id": lane.analysis_plan_id,
        "required_human_gate_id": lane.required_human_gate_id,
        "human_gate_receipt_id": None,
        "human_authority_identity": None,
        "authorized_scope": None,
        "issued_at_utc": None,
        "expires_at_utc": None,
        "status": AuthorizationStatus.NOT_AUTHORIZED.value,
        "authorization_domain": AUTHORIZATION_DOMAIN,
    }
    return ExecutionAuthorizationReceipt(
        authorization_id=canonical_sha256(unsigned),
        lane_id=lane.lane_id,
        exact_admission_record_ids=record_ids,
        lane_admission_bundle_id=bundle_id,
        analysis_plan_id=lane.analysis_plan_id,
        required_human_gate_id=lane.required_human_gate_id,
        human_gate_receipt_id=None,
        human_authority_identity=None,
        authorized_scope=None,
        issued_at_utc=None,
        expires_at_utc=None,
        status=AuthorizationStatus.NOT_AUTHORIZED,
        authorization_domain=AUTHORIZATION_DOMAIN,
        _construction_token=_AUTH_TOKEN,
    )


@dataclass(frozen=True)
class MutationResult:
    mutation_id: str
    executed: bool
    activated: bool
    killed: bool
    observed_marker: str

    def as_payload(self) -> dict[str, object]:
        return {
            "mutation_id": self.mutation_id,
            "executed": self.executed,
            "activated": self.activated,
            "killed": self.killed,
            "observed_marker": self.observed_marker,
        }


def _mutation_descriptor(root: Path, lane: LaneSpec) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=False)
    components: list[dict[str, object]] = []
    for index, component_id in enumerate(lane.expected_component_sequence):
        relative = f"components/{index:04d}-{component_id}.bin"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = f"{lane.lane_id}:{component_id}:{index}\n".encode("ascii")
        path.write_bytes(raw)
        components.append(
            {
                "component_id": component_id,
                "relative_path": relative,
                "byte_size": len(raw),
                "content_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    evidence: dict[str, object] = {
        "schema": DATA_IDENTITY_EVIDENCE_SCHEMA,
        "lane_id": lane.lane_id,
        "product_id": lane.product_id,
        "source_locator_identity": "pending",
        "release_name": f"{lane.lane_id} registered release",
        "release_version": f"{lane.lane_id.lower()}-v1",
        "release_identity": f"docs:pr289/{lane.lane_id.lower()}-release-v1",
        "license_identity": "spdx:CC-BY-4.0",
        "license_status": "BOUND",
        "units_contract_id": f"units:{lane.lane_id}:v1",
        "coordinate_frame_id": f"frame:{lane.lane_id}:v1",
        "sign_orientation_convention_id": f"sign:{lane.lane_id}:v1",
        "directional_convention_id": f"direction:{lane.lane_id}:v1",
        "harmonic_convention_id": f"harmonic:{lane.lane_id}:v1",
        "mask_id": f"mask:{lane.lane_id}:v1",
        "selection_id": f"selection:{lane.lane_id}:v1",
        "sky_support_id": f"sky:{lane.lane_id}:v1",
        "covariance_id": f"covariance:{lane.lane_id}:v1",
        "covariance_status": "REGISTERED",
        "null_ensemble_id": f"null:{lane.lane_id}:v1",
        "null_ensemble_status": "REGISTERED",
        "transfer_source": "none",
        "transfer_function_spec_id": "none",
        "transfer_provenance_status": "NOT_APPLICABLE",
        "sky_support_status": "REGISTERED",
    }
    evidence["native_identity_profile"] = _build_registered_native_profile(
        lane, components, evidence
    )
    evidence["source_locator_identity"] = compute_source_locator_identity(
        lane_id=lane.lane_id,
        product_id=lane.product_id,
        components=components,
        evidence_bindings=evidence,
    )
    evidence_path = root / "identity/evidence.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_bytes(_canonical_bytes(evidence) + b"\n")
    return {
        "root": str(root),
        "evidence_relative_path": "identity/evidence.json",
        "evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        "components": components,
        "acquisition_status": "COMPLETE",
        "name_only": False,
    }


def _rewrite_mutation_evidence(
    descriptor: Mapping[str, object],
    update: Mapping[str, object],
    *,
    remove: Sequence[str] = (),
    raw: bytes | None = None,
) -> None:
    root = Path(str(descriptor["root"]))
    path = root / str(descriptor["evidence_relative_path"])
    if raw is None:
        evidence = dict(_strict_json(path, field_name="mutation evidence"))
        evidence.update(update)
        for field_name in remove:
            evidence.pop(field_name, None)
        raw = _canonical_bytes(evidence) + b"\n"
    path.write_bytes(raw)
    descriptor["evidence_sha256"] = hashlib.sha256(raw).hexdigest()  # type: ignore[index]


def _kill_when(condition: bool, marker: str) -> None:
    if condition:
        raise DataIdentityError(marker)


def _probe_mutation(
    mutation_id: str,
    *,
    registry: LaneRegistryV2,
    spec_path: Path,
    source_bindings: Mapping[str, str],
    scratch_root: Path,
) -> None:
    planck = registry.lane("PLANCK")

    def descriptor(name: str, lane: LaneSpec = planck) -> dict[str, object]:
        return _mutation_descriptor(scratch_root / name, lane)

    def evaluate(
        lane_id: str, value: Mapping[str, object] | None
    ) -> LaneAdmissionDecision:
        return evaluate_lane_identity(
            registry=registry,
            lane_id=lane_id,
            descriptor=value,
            inspected_at_utc="2026-08-09T00:00:00+00:00",
        )

    def resign_record(record: dict[str, object]) -> None:
        stable = dict(record)
        for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
            stable.pop(key)
        record["record_id"] = canonical_sha256(stable)
        inspection = dict(record)
        inspection.pop("inspection_receipt_id")
        record["inspection_receipt_id"] = canonical_sha256(inspection)

    def resign_bundle(payload: dict[str, object]) -> None:
        records = payload["records"]
        if not isinstance(records, list) or not records:
            raise DataIdentityError("mutation requires admitted record rows")
        first = records[0]
        if not isinstance(first, Mapping):
            raise DataIdentityError("mutation record row is malformed")
        payload["lane_admission_bundle_id"] = canonical_sha256(
            {
                "lane_id": payload["lane_id"],
                "product_id": payload["product_id"],
                "component_inventory_id": first["component_inventory_id"],
                "record_ids": [row["record_id"] for row in records],
            }
        )

    def rewrite_native_profile(
        value: dict[str, object], mutate
    ) -> None:
        root = Path(str(value["root"]))
        evidence_path = root / str(value["evidence_relative_path"])
        evidence = dict(
            _strict_json(evidence_path, field_name="native mutation evidence")
        )
        profile = json.loads(
            _canonical_bytes(evidence["native_identity_profile"]).decode("ascii")
        )
        mutate(profile)
        unsigned_profile = dict(profile)
        unsigned_profile.pop("profile_id", None)
        profile["profile_id"] = canonical_sha256(unsigned_profile)
        evidence["native_identity_profile"] = profile
        evidence["source_locator_identity"] = compute_source_locator_identity(
            lane_id=str(evidence["lane_id"]),
            product_id=str(evidence["product_id"]),
            components=value["components"],  # type: ignore[arg-type]
            evidence_bindings=evidence,
        )
        _rewrite_mutation_evidence(value, evidence)

    if mutation_id == "MU289-PR274-MUTATION":
        mutated = dict(source_bindings)
        target = next(
            key for key in mutated if key.endswith("PR274_ADMISSION_RESULT.json")
        )
        mutated[target] = "0" * 64
        _validated_source_bindings(spec_path, mutated)
        return
    if mutation_id == "MU289-AUTH-LANE-BINDING":
        cf4 = registry.lane("CF4")
        decision = evaluate(
            "CF4", descriptor(mutation_id, cf4)
        )
        build_not_authorized_receipt(planck, decision)
        return
    if mutation_id in {
        "MU289-ADMISSION-AUTH-COLLAPSE",
        "MU289-WORKFLOW-AUTH-LAUNDERING",
    }:
        decision = evaluate("PLANCK", descriptor(mutation_id))
        authorization = build_not_authorized_receipt(planck, decision)
        replace(
            authorization,
            status=AuthorizationStatus.AUTHORIZED,
            _construction_token=_AUTH_TOKEN,
        )
        return
    if mutation_id in {
        "MU289-SYMLINK",
        "MU289-PARENT-SYMLINK",
        "MU289-HARDLINK-ALIAS",
        "MU289-SIZE",
        "MU289-HASH",
        "MU289-INVENTORY",
    }:
        value = descriptor(mutation_id)
        components = value["components"]
        assert isinstance(components, list)
        first = components[0]
        path = Path(str(value["root"])) / str(first["relative_path"])
        if mutation_id == "MU289-SYMLINK":
            outside = scratch_root / "symlink-outside.bin"
            outside.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(outside)
        elif mutation_id == "MU289-PARENT-SYMLINK":
            outside = scratch_root / "parent-symlink-outside"
            outside.mkdir()
            moved = outside / "component.bin"
            path.replace(moved)
            linked = Path(str(value["root"])) / "linked-parent"
            linked.symlink_to(outside, target_is_directory=True)
            first["relative_path"] = "linked-parent/component.bin"
        elif mutation_id == "MU289-HARDLINK-ALIAS":
            (scratch_root / "outside-hardlink.bin").hardlink_to(path)
        elif mutation_id == "MU289-SIZE":
            first["byte_size"] = int(first["byte_size"]) + 1
        elif mutation_id == "MU289-HASH":
            first["content_sha256"] = "0" * 64
        else:
            components.pop()
        decision = evaluate("PLANCK", value)
        _kill_when(
            decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY,
            f"{mutation_id} rejected as {decision.status.value}",
        )
        return
    if mutation_id == "MU289-SEMANTIC-STATUS":
        statuses = []
        for field_name in ("covariance_status", "sky_support_status"):
            value = descriptor(f"{mutation_id}-{field_name}")
            _rewrite_mutation_evidence(
                value,
                {field_name: "NOT_APPLICABLE"},
            )
            statuses.append(evaluate("PLANCK", value).status)
        _kill_when(
            all(
                status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT
                for status in statuses
            ),
            "allowed status values cannot contradict bound Planck roles",
        )
        return
    if mutation_id in {
        "MU289-RELEASE-LICENSE",
        "MU289-PLACEHOLDER-PROVENANCE",
        "MU289-EVIDENCE-JSON",
        "MU289-SEMANTIC-FIELD",
    }:
        value = descriptor(mutation_id)
        if mutation_id == "MU289-RELEASE-LICENSE":
            _rewrite_mutation_evidence(value, {"license_identity": ""})
        elif mutation_id == "MU289-PLACEHOLDER-PROVENANCE":
            _rewrite_mutation_evidence(value, {"release_version": "v"})
        elif mutation_id == "MU289-EVIDENCE-JSON":
            _rewrite_mutation_evidence(
                value,
                {},
                raw=(
                    b'{"schema":"common.data_identity_evidence.v2",'
                    b'"schema":"common.data_identity_evidence.v2"}\n'
                ),
            )
        else:
            _rewrite_mutation_evidence(value, {}, remove=("units_contract_id",))
        decision = evaluate("PLANCK", value)
        _kill_when(
            decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY,
            f"{mutation_id} rejected as {decision.status.value}",
        )
        return
    if mutation_id == "MU289-RECORD-ID-STABILITY":
        first = evaluate("PLANCK", descriptor("stable-a"))
        second_value = descriptor("stable-b")
        second = evaluate_lane_identity(
            registry=registry,
            lane_id="PLANCK",
            descriptor=second_value,
            inspected_at_utc="2026-08-09T00:01:00+00:00",
        )
        stable = (
            first.complete
            and second.complete
            and tuple(row.record_id for row in first.records)
            == tuple(row.record_id for row in second.records)
            and tuple(row.inspection_receipt_id for row in first.records)
            != tuple(row.inspection_receipt_id for row in second.records)
        )
        _kill_when(stable, "stable record identity excludes root and inspection time")
        return
    if mutation_id == "MU289-INVENTORY-ID":
        value = descriptor(mutation_id)
        decision = evaluate("PLANCK", value)
        expected = component_inventory_id(value["components"])  # type: ignore[arg-type]
        _kill_when(
            decision.complete
            and all(row.component_inventory_id == expected for row in decision.records),
            "component inventory identity independently recomputed",
        )
        return
    if mutation_id == "MU289-NATIVE-PROFILE-OMISSION":
        value = descriptor(mutation_id)
        _rewrite_mutation_evidence(
            value, {}, remove=("native_identity_profile",)
        )
        decision = evaluate("PLANCK", value)
        _kill_when(
            decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT,
            "generic record IDs cannot replace a native identity profile",
        )
        return
    if mutation_id == "MU289-NATIVE-REGISTRY-ROLE":
        payload = json.loads(json.dumps(registry._payload()))
        planck_row = next(
            row for row in payload["lanes"] if row["lane_id"] == "PLANCK"
        )
        planck_row["required_component_ids"][0] = "generic_map"
        cardinality = planck_row["component_cardinality"]
        cardinality["generic_map"] = cardinality.pop("smica_map")
        lane_registry_from_mapping(payload)
        return
    if mutation_id == "MU289-PLANCK-NATIVE-RELATIONSHIP":
        value = descriptor(mutation_id)

        def collapse(profile: dict[str, object]) -> None:
            pipeline = profile["pipelines"]["COMMANDER"]  # type: ignore[index]
            pipeline["map_component_id"] = "smica_map"  # type: ignore[index]
            unsigned = dict(pipeline)  # type: ignore[arg-type]
            unsigned.pop("pipeline_identity")
            pipeline["pipeline_identity"] = _relationship_content_identity(  # type: ignore[index]
                unsigned,
                component_bindings=profile["component_bindings"],  # type: ignore[arg-type]
            )

        rewrite_native_profile(value, collapse)
        decision = evaluate("PLANCK", value)
        _kill_when(
            decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT,
            "SMICA and Commander native roles cannot collapse",
        )
        return
    if mutation_id == "MU289-CF4-NATIVE-RELATIONSHIP":
        cf4 = registry.lane("CF4")
        value = descriptor(mutation_id, cf4)

        def drift_cf4(profile: dict[str, object]) -> None:
            semantics = profile["semantics"]  # type: ignore[index]
            semantics["frame_component_id"] = "sign_convention"  # type: ignore[index]
            unsigned = dict(semantics)  # type: ignore[arg-type]
            unsigned.pop("semantics_identity")
            semantics["semantics_identity"] = _relationship_content_identity(  # type: ignore[index]
                unsigned,
                component_bindings=profile["component_bindings"],  # type: ignore[arg-type]
            )

        rewrite_native_profile(value, drift_cf4)
        decision = evaluate("CF4", value)
        _kill_when(
            decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT,
            "CF4 exact frame and sign roles cannot alias",
        )
        return
    if mutation_id == "MU289-HSC-KIDS-CHILD-IDENTITY":
        lane = registry.lane("HSC_KIDS")
        value = descriptor(mutation_id, lane)

        def share_psf(profile: dict[str, object]) -> None:
            kids = profile["children"]["KIDS"]  # type: ignore[index]
            kids["psf_component_id"] = "hsc_psf"  # type: ignore[index]
            unsigned = dict(kids)  # type: ignore[arg-type]
            unsigned.pop("child_identity_id")
            kids["child_identity_id"] = _relationship_content_identity(  # type: ignore[index]
                unsigned,
                component_bindings=profile["component_bindings"],  # type: ignore[arg-type]
            )
            cross = profile["cross_covariance"]  # type: ignore[index]
            cross["kids_child_identity_id"] = kids["child_identity_id"]  # type: ignore[index]
            unsigned_cross = dict(cross)  # type: ignore[arg-type]
            unsigned_cross.pop("cross_covariance_identity")
            cross["cross_covariance_identity"] = _relationship_content_identity(  # type: ignore[index]
                unsigned_cross,
                component_bindings=profile["component_bindings"],  # type: ignore[arg-type]
            )

        rewrite_native_profile(value, share_psf)
        decision = evaluate("HSC_KIDS", value)
        _kill_when(
            decision.status is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT,
            "HSC and KiDS require separate PSF child identities",
        )
        return
    if mutation_id == "MU289-NATIVE-REPLAY":
        decision = evaluate("PLANCK", descriptor(mutation_id))
        payload = decision.as_payload()
        record = payload["records"][0]
        record["native_identity_profile"]["pipelines"]["SMICA"][  # type: ignore[index]
            "map_component_id"
        ] = "commander_map"
        replay_lane_admission_decision(payload, registry=registry)
        return
    if mutation_id == "MU289-EXPORTED-SEMANTIC-REPLAY":
        decision = evaluate("PLANCK", descriptor(mutation_id))
        payload = decision.as_payload()
        record = payload["records"][0]
        record["license_status"] = "UNBOUND"
        resign_record(record)
        resign_bundle(payload)
        replay_lane_admission_decision(payload, registry=registry)
        return
    if mutation_id == "MU289-REPEATED-ROLE-ORDINAL":
        desi = registry.lane("DESI")
        bounded_cardinality = tuple(
            (
                component_id,
                2 if component_id == "ezmock_inventory" else 1,
            )
            for component_id, _ in desi.component_cardinality
        )
        bounded_desi = replace(
            desi,
            component_cardinality=bounded_cardinality,
        )
        bounded_registry = LaneRegistryV2(
            lanes=tuple(
                bounded_desi if lane.lane_id == "DESI" else lane
                for lane in registry.lanes
            ),
            universal_semantic_fields=registry.universal_semantic_fields,
            _construction_token=_REGISTRY_TOKEN,
        )
        decision = evaluate_lane_identity(
            registry=bounded_registry,
            lane_id="DESI",
            descriptor=descriptor(mutation_id, bounded_desi),
            inspected_at_utc="2026-08-09T00:00:00+00:00",
        )
        payload = decision.as_payload()
        records = payload["records"]
        positions = [
            index
            for index, record in enumerate(records)
            if record["component_id"] == "ezmock_inventory"
        ][:2]
        records[positions[0]] = json.loads(
            _canonical_bytes(records[positions[1]]).decode("ascii")
        )
        resign_bundle(payload)
        replay_lane_admission_decision(payload, registry=bounded_registry)
        return
    if mutation_id == "MU289-NAME-ONLY":
        hsc = registry.lane("HSC_KIDS")
        value = descriptor(mutation_id, hsc)
        value["name_only"] = True
        decision = evaluate("HSC_KIDS", value)
        _kill_when(
            decision.status is AdmissionStatus.REJECTED_NAME_ONLY,
            "name-only HSC/KiDS input rejected",
        )
        return
    if mutation_id in {"MU289-DESI-PARTIAL", "MU289-STATUS-PRECEDENCE"}:
        value = {
            "root": str(scratch_root / "missing-desi"),
            "evidence_relative_path": "identity/evidence.json",
            "evidence_sha256": "0" * 64,
            "components": [],
            "acquisition_status": "PARTIAL_BACKGROUND",
            "name_only": True,
        }
        decision = evaluate("DESI", value)
        _kill_when(
            decision.status is AdmissionStatus.BLOCKED_PR151_INCOMPLETE,
            "PR-151 partial refusal has canonical precedence",
        )
        return
    if mutation_id == "MU289-AUTODOWNLOAD":
        absent = scratch_root / "must-remain-absent"
        decision = evaluate(
            "PLANCK",
            {
                "root": str(absent),
                "evidence_relative_path": "identity/evidence.json",
                "evidence_sha256": "0" * 64,
                "components": [],
                "acquisition_status": "COMPLETE",
                "name_only": False,
            },
        )
        _kill_when(
            decision.status is AdmissionStatus.REJECTED_NOT_PRESENT
            and not absent.exists(),
            "missing input refused without acquisition side effect",
        )
        return
    if mutation_id == "MU289-MUTATION-OMISSION":
        validate_mutation_results(
            ("registered-a", "registered-b"),
            (
                MutationResult(
                    mutation_id="registered-a",
                    executed=True,
                    activated=True,
                    killed=True,
                    observed_marker="executed",
                ),
            ),
        )
        return
    if mutation_id == "MU289-GATE-ID-ALIAS":
        payload = json.loads(json.dumps(registry._payload()))
        hsc = next(row for row in payload["lanes"] if row["lane_id"] == "HSC_KIDS")
        hsc["required_human_gate_id"] = "H-HSC/KiDS"
        lane_registry_from_mapping(payload)
        return
    if mutation_id == "MU289-PARTIAL-LANE-AGGREGATE":
        partial = descriptor(mutation_id)
        partial["components"].pop()  # type: ignore[union-attr]
        decision = evaluate("PLANCK", partial)
        decisions = (decision,) + tuple(
            evaluate(lane.lane_id, None) for lane in registry.lanes[1:]
        )
        _kill_when(
            _aggregate_status(decisions) is AggregateStatus.NO_ADMITTED_IDENTITIES,
            "partial component set does not count as an admitted lane",
        )
        return
    if mutation_id == "MU289-CLAIM-PROMOTION":
        decisions = tuple(evaluate(lane.lane_id, None) for lane in registry.lanes)
        authorizations = tuple(
            build_not_authorized_receipt(lane, decision)
            for lane, decision in zip(registry.lanes, decisions, strict=True)
        )
        probe_bindings = {"probe": "sha256:" + "0" * 64}
        receipt = DataIdentityPreflightReceipt(
            registry_content_id=registry.content_id,
            aggregate_status=AggregateStatus.NO_ADMITTED_IDENTITIES,
            lane_decisions=decisions,
            authorization_receipts=authorizations,
            mutation_results=(),
            source_bindings=probe_bindings,
            generation_identity={
                "schema": "common.source_bound_generation_identity.v1",
                "git_commit_or_worktree_state": "BOUND_SOURCE_WORKTREE:"
                + canonical_sha256(probe_bindings),
                "generating_procedure": [
                    "python3",
                    "-B",
                    "scripts/codex_harness/run_pr289_data_identity_v2.py",
                    "build",
                ],
            },
            terminal=PASS_TOKEN,
            _construction_token=_PREFLIGHT_TOKEN,
        ).as_payload()
        _kill_when(
            receipt["claim_tier"] == CLAIM_TIER
            and receipt["observed_data_executed"] is False
            and receipt["public_use"] is False
            and receipt["transfer_source"] == TRANSFER_SOURCE
            and receipt["family_identification_gate"] == FAMILY_GATE,
            "process PASS cannot promote scientific claims",
        )
        return
    raise DataIdentityError(f"unregistered mutation {mutation_id}")


def _run_registered_mutations(
    mutation_ids: Sequence[str],
    *,
    registry: LaneRegistryV2,
    spec_path: Path,
    source_bindings: Mapping[str, str],
) -> tuple[MutationResult, ...]:
    results: list[MutationResult] = []
    with tempfile.TemporaryDirectory(prefix="pr289-mutations-") as temp:
        root = Path(temp)
        for index, mutation_id in enumerate(mutation_ids):
            try:
                _probe_mutation(
                    mutation_id,
                    registry=registry,
                    spec_path=spec_path,
                    source_bindings=source_bindings,
                    scratch_root=root / f"{index:02d}",
                )
            except DataIdentityError as exc:
                results.append(
                    MutationResult(
                        mutation_id=mutation_id,
                        executed=True,
                        activated=True,
                        killed=True,
                        observed_marker=str(exc),
                    )
                )
            else:
                results.append(
                    MutationResult(
                        mutation_id=mutation_id,
                        executed=True,
                        activated=True,
                        killed=False,
                        observed_marker="mutation survived",
                    )
                )
    return tuple(results)


def validate_mutation_results(
    expected_ids: Sequence[str], results: Sequence[MutationResult]
) -> tuple[MutationResult, ...]:
    values = tuple(results)
    if tuple(result.mutation_id for result in values) != tuple(expected_ids):
        raise DataIdentityError(
            "registered mutation results are omitted or reordered"
        )
    if any(
        type(result) is not MutationResult
        or result.executed is not True
        or result.activated is not True
        or result.killed is not True
        or not result.observed_marker
        for result in values
    ):
        raise DataIdentityError(
            "registered mutation execution did not fail closed"
        )
    return values


def registered_mutation_ids(spec_path: Path) -> tuple[str, ...]:
    if spec_path.is_symlink() or not spec_path.is_file():
        raise DataIdentityError("PR-289 spec must be a regular file")
    import yaml

    try:
        payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise DataIdentityError("PR-289 spec cannot be parsed") from exc
    rows = payload.get("mutation_registry") if isinstance(payload, Mapping) else None
    if (
        isinstance(rows, (str, bytes))
        or not isinstance(rows, Sequence)
        or not rows
    ):
        raise DataIdentityError("PR-289 mutation registry is absent")
    mutation_ids = tuple(
        _text(
            row.get("mutation_id") if isinstance(row, Mapping) else None,
            "mutation_id",
        )
        for row in rows
    )
    if len(mutation_ids) != len(set(mutation_ids)):
        raise DataIdentityError("PR-289 mutation IDs are duplicated")
    return mutation_ids


def _validated_source_bindings(
    spec_path: Path, source_bindings: Mapping[str, str]
) -> dict[str, str]:
    import yaml

    if spec_path.is_symlink() or not spec_path.is_file():
        raise DataIdentityError("PR-289 spec must be a regular file")
    repository_root = spec_path.resolve().parents[3]
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise DataIdentityError("PR-289 spec cannot be parsed") from exc
    if not isinstance(spec, Mapping):
        raise DataIdentityError("PR-289 spec must contain a mapping")
    checked: dict[str, str] = {}
    for relative, digest in source_bindings.items():
        relative_text = _relative_path(relative, "source binding path").as_posix()
        path = repository_root / relative_text
        cursor = repository_root
        for part in Path(relative_text).parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise DataIdentityError(
                    f"source binding traverses a symlink: {relative_text}"
                )
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(repository_root)
        except (OSError, ValueError) as exc:
            raise DataIdentityError(
                f"source binding escapes or is missing: {relative_text}"
            ) from exc
        if resolved != path or not path.is_file() or path.stat().st_nlink != 1:
            raise DataIdentityError(
                f"source binding is not an exact regular file: {relative_text}"
            )
        expected = _raw_sha(digest, f"source binding {relative_text}")
        if _stream_sha256(path) != expected:
            raise DataIdentityError(f"source binding hash drifted: {relative_text}")
        checked[relative_text] = "sha256:" + expected
    required_paths = {
        "docs/research_program/post_pr275/pr289_spec.yaml": _stream_sha256(
            spec_path
        ),
        "docs/research_program/post_pr275/pr289_publication_policy.json": _stream_sha256(
            repository_root
            / "docs/research_program/post_pr275/pr289_publication_policy.json"
        ),
        "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json": _stream_sha256(
            repository_root
            / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
        ),
        "docs/research_program/post_pr275/data_runbooks.yaml": _stream_sha256(
            repository_root
            / "docs/research_program/post_pr275/data_runbooks.yaml"
        ),
        "docs/harness/CLAIM_LEDGER.md": _stream_sha256(
            repository_root / "docs/harness/CLAIM_LEDGER.md"
        ),
        "htt/src/common/data_identity.py": _stream_sha256(
            repository_root / "htt/src/common/data_identity.py"
        ),
        "scripts/codex_harness/run_pr289_data_identity_v2.py": _stream_sha256(
            repository_root
            / "scripts/codex_harness/run_pr289_data_identity_v2.py"
        ),
        "tests/contracts/test_data_identity_registry_v2.py": _stream_sha256(
            repository_root
            / "tests/contracts/test_data_identity_registry_v2.py"
        ),
        "docs/research_program/vector_tensor/data_admission/"
        "PR274_DATA_IDENTITY_REGISTRY.yaml": str(
            spec.get("historical_boundary", {}).get("v1_registry_sha256", "")
        ),
        "docs/research_program/vector_tensor/data_admission/"
        "PR274_ADMISSION_RESULT.json": str(
            spec.get("historical_boundary", {}).get("v1_result_sha256", "")
        ),
    }
    for relative, expected in required_paths.items():
        if checked.get(relative) != "sha256:" + _raw_sha(
            expected, f"required source binding {relative}"
        ):
            raise DataIdentityError(
                f"required source binding missing or stale: {relative}"
            )
    return checked


def _validated_generation_identity(
    generation_identity: Mapping[str, object],
    *,
    source_bindings: Mapping[str, str],
) -> dict[str, object]:
    checked = _exact_mapping(
        generation_identity,
        field_name="generation identity",
        expected=frozenset(
            {
                "schema",
                "git_commit_or_worktree_state",
                "generating_procedure",
            }
        ),
    )
    if checked["schema"] != "common.source_bound_generation_identity.v1":
        raise DataIdentityError("generation identity schema drifted")
    expected_state = "BOUND_SOURCE_WORKTREE:" + canonical_sha256(
        dict(source_bindings)
    )
    if checked["git_commit_or_worktree_state"] != expected_state:
        raise DataIdentityError("generation identity source binding drifted")
    procedure = checked["generating_procedure"]
    if (
        isinstance(procedure, (str, bytes))
        or not isinstance(procedure, Sequence)
        or len(procedure) != 4
        or procedure[0] != "python3"
        or list(procedure[1:])
        != [
            "-B",
            "scripts/codex_harness/run_pr289_data_identity_v2.py",
            "build",
        ]
    ):
        raise DataIdentityError("generation procedure is not the exact build argv")
    return {
        "schema": checked["schema"],
        "git_commit_or_worktree_state": checked["git_commit_or_worktree_state"],
        "generating_procedure": list(procedure),
    }


@dataclass(frozen=True)
class DataIdentityPreflightReceipt:
    registry_content_id: str
    aggregate_status: AggregateStatus
    lane_decisions: tuple[LaneAdmissionDecision, ...]
    authorization_receipts: tuple[ExecutionAuthorizationReceipt, ...]
    mutation_results: tuple[MutationResult, ...]
    source_bindings: Mapping[str, str]
    generation_identity: Mapping[str, object]
    terminal: str
    _construction_token: InitVar[object] = None
    _seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PREFLIGHT_TOKEN:
            raise DataIdentityError(
                "DataIdentityPreflightReceipt must be factory-built"
            )
        if self.terminal != PASS_TOKEN:
            raise DataIdentityError("preflight receipt terminal drifted")
        if (
            len(self.lane_decisions) != 6
            or len(self.authorization_receipts) != 6
        ):
            raise DataIdentityError("preflight receipt must cover every lane")
        if any(
            receipt.status is not AuthorizationStatus.NOT_AUTHORIZED
            for receipt in self.authorization_receipts
        ):
            raise DataIdentityError(
                "preflight receipt cannot authorize execution"
            )
        _validated_generation_identity(
            self.generation_identity,
            source_bindings=self.source_bindings,
        )
        object.__setattr__(
            self, "_seal", canonical_sha256(self._unsigned_payload())
        )

    def _unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": PREFLIGHT_RECEIPT_SCHEMA,
            "terminal": self.terminal,
            "owner": "COMMON",
            "scope": (
                "external-data identity admission without acquisition or analysis"
            ),
            "claim_tier": CLAIM_TIER,
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
            "transfer_source": TRANSFER_SOURCE,
            "observed_data_executed": False,
            "public_use": False,
            "scientific_status_effect": "OPEN_UNCHANGED",
            "family_identification_gate": FAMILY_GATE,
            "registry_content_id": self.registry_content_id,
            "aggregate_status": self.aggregate_status.value,
            "lane_decisions": [
                value.as_payload() for value in self.lane_decisions
            ],
            "lane_and_product_identities": [
                {
                    "lane_id": value.lane_id,
                    "product_id": value.product_id,
                    "lane_admission_bundle_id": value.lane_admission_bundle_id,
                    "native_identity_profile_id": (
                        value.records[0].native_identity_profile_id
                        if value.complete
                        else None
                    ),
                    "status": value.status.value,
                }
                for value in self.lane_decisions
            ],
            "sky_mask_selection_covariance_null_status": [
                {
                    "lane_id": value.lane_id,
                    "status": (
                        "BOUND_BY_COMPONENT_RECORDS"
                        if value.complete
                        else "NOT_EVALUATED_NO_COMPLETE_LANE"
                    ),
                }
                for value in self.lane_decisions
            ],
            "authorization_receipts": [
                value.as_payload() for value in self.authorization_receipts
            ],
            "mutation_results": [
                value.as_payload() for value in self.mutation_results
            ],
            "source_bindings": dict(self.source_bindings),
            "generation_identity": dict(self.generation_identity),
            "git_commit_or_worktree_state": self.generation_identity[
                "git_commit_or_worktree_state"
            ],
            "assumptions": [
                "candidate roots, when supplied, are read-only local directories",
                "identity admission is separate from lane execution authorization",
            ],
            "caveats": [
                "process PASS does not admit, authorize, execute, or validate a lane",
                "PR-151 partial acquisition is forbidden input",
                "no native solver, observed-data statistic, or family claim is produced",
            ],
            "allowed_uses": [
                "read-only external product identity preflight",
                "explicit refusal and input-gap reporting",
            ],
            "forbidden_uses": [
                "automatic acquisition",
                "observed-data execution",
                "admission inferred as execution authorization",
                "native or family claim promotion",
            ],
            "generating_procedure": list(
                self.generation_identity["generating_procedure"]
            ),
        }

    @property
    def receipt_content_id(self) -> str:
        if canonical_sha256(self._unsigned_payload()) != self._seal:
            raise DataIdentityError("preflight receipt drifted")
        return self._seal

    def as_payload(self) -> dict[str, object]:
        return {
            **self._unsigned_payload(),
            "receipt_content_id": self.receipt_content_id,
        }


def _aggregate_status(
    decisions: Sequence[LaneAdmissionDecision],
) -> AggregateStatus:
    admitted = sum(decision.complete for decision in decisions)
    if admitted == 0:
        return AggregateStatus.NO_ADMITTED_IDENTITIES
    if admitted == len(decisions):
        return AggregateStatus.ADMITTED_IDENTITIES_AWAITING_SEPARATE_AUTHORIZATION
    return AggregateStatus.PARTIAL_LANE_ADMISSION


def build_data_identity_v2_receipt(
    *,
    registry: LaneRegistryV2,
    root_descriptors: Mapping[str, Mapping[str, object]],
    inspected_at_utc: str,
    spec_path: Path,
    source_bindings: Mapping[str, str],
    generation_identity: Mapping[str, object],
) -> DataIdentityPreflightReceipt:
    unknown = set(root_descriptors) - {
        lane.lane_id for lane in registry.lanes
    }
    if unknown:
        raise DataIdentityError(
            f"unregistered root descriptors: {sorted(unknown)}"
        )
    decisions = tuple(
        evaluate_lane_identity(
            registry=registry,
            lane_id=lane.lane_id,
            descriptor=root_descriptors.get(lane.lane_id),
            inspected_at_utc=inspected_at_utc,
        )
        for lane in registry.lanes
    )
    aggregate = _aggregate_status(decisions)
    authorizations = tuple(
        build_not_authorized_receipt(lane, decision)
        for lane, decision in zip(registry.lanes, decisions, strict=True)
    )
    mutation_ids = registered_mutation_ids(spec_path)
    mutations = validate_mutation_results(
        mutation_ids,
        _run_registered_mutations(
            mutation_ids,
            registry=registry,
            spec_path=spec_path,
            source_bindings=source_bindings,
        ),
    )
    checked_bindings = _validated_source_bindings(spec_path, source_bindings)
    if not checked_bindings:
        raise DataIdentityError("preflight receipt requires source bindings")
    if not isinstance(generation_identity, Mapping) or not generation_identity:
        raise DataIdentityError("generation identity is required")
    checked_generation_identity = _validated_generation_identity(
        generation_identity,
        source_bindings=checked_bindings,
    )
    return DataIdentityPreflightReceipt(
        registry_content_id=registry.content_id,
        aggregate_status=aggregate,
        lane_decisions=decisions,
        authorization_receipts=authorizations,
        mutation_results=mutations,
        source_bindings=checked_bindings,
        generation_identity=checked_generation_identity,
        terminal=PASS_TOKEN,
        _construction_token=_PREFLIGHT_TOKEN,
    )


__all__ = [
    "AdmissionStatus",
    "AggregateStatus",
    "AuthorizationStatus",
    "DataIdentityError",
    "DataIdentityPreflightReceipt",
    "DataIdentityRecordV2",
    "ExecutionAuthorizationReceipt",
    "LaneAdmissionDecision",
    "LaneRegistryV2",
    "LaneSpec",
    "MutationResult",
    "build_data_identity_v2_receipt",
    "build_not_authorized_receipt",
    "canonical_sha256",
    "component_inventory_id",
    "compute_source_locator_identity",
    "evaluate_lane_identity",
    "lane_registry_from_mapping",
    "load_lane_registry",
    "replay_lane_admission_decision",
    "registered_mutation_ids",
    "validate_data_identity_record_payload",
    "validate_native_identity_profile",
    "validate_mutation_results",
]
