"""Non-authoritative wire contracts for an observed-execution transaction.

The privileged transaction is implemented by the separately built Rust
launcher.  This Python module only parses, validates, and content-addresses
receipts.  It cannot verify a human authorization, consume a nonce, spawn a
worker, or open observed data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Mapping, Sequence


class ObservedExecutionError(ValueError):
    """Raised when an execution wire object is noncanonical or inconsistent."""


class ArtifactMode(str, Enum):
    """Keep rehearsal evidence structurally separate from production evidence."""

    SYNTHETIC_FIXTURE = "synthetic_fixture"
    PRODUCTION = "production"


_RAW_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_OBJECT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ObservedExecutionError("payload is not canonical finite ASCII JSON") from exc


def parse_strict_json_bytes(raw: bytes) -> Mapping[str, object]:
    """Parse exact compact sorted ASCII JSON while rejecting duplicate keys."""

    if type(raw) is not bytes:
        raise ObservedExecutionError("strict JSON input must be exact bytes")

    def no_duplicate(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ObservedExecutionError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        decoded = raw.decode("ascii")
        value = json.loads(
            decoded,
            object_pairs_hook=no_duplicate,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ObservedExecutionError(
                    f"strict JSON contains non-finite constant {token}"
                )
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ObservedExecutionError("strict JSON is not canonical ASCII JSON") from exc
    if not isinstance(value, Mapping):
        raise ObservedExecutionError("strict JSON root must be an object")
    if raw != _canonical_json_bytes(value):
        raise ObservedExecutionError("strict JSON bytes are not canonical")
    return value


def _content_id(payload: Mapping[str, object]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _exact_mapping(
    value: object, *, expected: frozenset[str], field: str
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ObservedExecutionError(f"{field} fields drifted")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ObservedExecutionError(f"{field} must be a non-empty canonical string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ObservedExecutionError(f"{field} must contain ASCII only") from exc
    return value


def _sha256(value: object, field: str) -> str:
    text = _text(value, field)
    if not text.startswith("sha256:") or _RAW_SHA256.fullmatch(text[7:]) is None:
        raise ObservedExecutionError(f"{field} must be a lowercase sha256 identity")
    return text


def _git_object(value: object, field: str) -> str:
    text = _text(value, field)
    if _GIT_OBJECT.fullmatch(text) is None:
        raise ObservedExecutionError(f"{field} must be a lowercase Git object id")
    return text


def _timestamp(value: object, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ObservedExecutionError(f"{field} must be canonical UTC seconds") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != text:
        raise ObservedExecutionError(f"{field} must be canonical UTC seconds")
    return text


def _artifact_mode(value: object) -> ArtifactMode:
    try:
        return value if isinstance(value, ArtifactMode) else ArtifactMode(value)
    except (TypeError, ValueError) as exc:
        raise ObservedExecutionError("artifact_mode is invalid") from exc


def _record_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ObservedExecutionError(
            "exact_admission_record_ids must be an ordered sequence"
        )
    rows = tuple(_sha256(item, "exact_admission_record_ids") for item in value)
    if not rows or len(rows) != len(set(rows)):
        raise ObservedExecutionError(
            "exact_admission_record_ids must be non-empty and unique"
        )
    return rows


def _output_root(value: object) -> str:
    text = _text(value, "output_root")
    path = PurePosixPath(text)
    if not path.is_absolute() or ".." in path.parts or str(path) != text:
        raise ObservedExecutionError("output_root must be a canonical absolute path")
    return text


@dataclass(frozen=True)
class ObservedExecutionBindingV1:
    artifact_mode: ArtifactMode
    run_id: str
    lane_id: str
    candidate_commit: str
    candidate_tree: str
    exact_admission_record_ids: tuple[str, ...]
    lane_admission_bundle_id: str
    authorization_id: str
    model_contract_content_id: str
    runtime_environment_receipt_id: str
    computed_response_rank_receipt_id: str
    normalization_evidence_id: str
    execution_plan_content_id: str
    launcher_binary_sha256: str
    output_root: str
    binding_id: str

    SCHEMA = "common.observed_execution_binding.v1"

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "artifact_mode": self.artifact_mode.value,
            "run_id": self.run_id,
            "lane_id": self.lane_id,
            "candidate_commit": self.candidate_commit,
            "candidate_tree": self.candidate_tree,
            "exact_admission_record_ids": list(self.exact_admission_record_ids),
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
            "authorization_id": self.authorization_id,
            "model_contract_content_id": self.model_contract_content_id,
            "runtime_environment_receipt_id": self.runtime_environment_receipt_id,
            "computed_response_rank_receipt_id": self.computed_response_rank_receipt_id,
            "normalization_evidence_id": self.normalization_evidence_id,
            "execution_plan_content_id": self.execution_plan_content_id,
            "launcher_binary_sha256": self.launcher_binary_sha256,
            "output_root": self.output_root,
        }

    def as_payload(self) -> dict[str, object]:
        return {
            "schema": self.SCHEMA,
            **self.unsigned_payload(),
            "binding_id": self.binding_id,
        }

    @classmethod
    def build(
        cls,
        *,
        artifact_mode: ArtifactMode | str,
        run_id: object,
        lane_id: object,
        candidate_commit: object,
        candidate_tree: object,
        exact_admission_record_ids: object,
        lane_admission_bundle_id: object,
        authorization_id: object,
        model_contract_content_id: object,
        runtime_environment_receipt_id: object,
        computed_response_rank_receipt_id: object,
        normalization_evidence_id: object,
        execution_plan_content_id: object,
        launcher_binary_sha256: object,
        output_root: object,
    ) -> "ObservedExecutionBindingV1":
        normalized = cls(
            artifact_mode=_artifact_mode(artifact_mode),
            run_id=_text(run_id, "run_id"),
            lane_id=_text(lane_id, "lane_id"),
            candidate_commit=_git_object(candidate_commit, "candidate_commit"),
            candidate_tree=_git_object(candidate_tree, "candidate_tree"),
            exact_admission_record_ids=_record_ids(exact_admission_record_ids),
            lane_admission_bundle_id=_sha256(
                lane_admission_bundle_id, "lane_admission_bundle_id"
            ),
            authorization_id=_sha256(authorization_id, "authorization_id"),
            model_contract_content_id=_sha256(
                model_contract_content_id, "model_contract_content_id"
            ),
            runtime_environment_receipt_id=_sha256(
                runtime_environment_receipt_id, "runtime_environment_receipt_id"
            ),
            computed_response_rank_receipt_id=_sha256(
                computed_response_rank_receipt_id,
                "computed_response_rank_receipt_id",
            ),
            normalization_evidence_id=_sha256(
                normalization_evidence_id, "normalization_evidence_id"
            ),
            execution_plan_content_id=_sha256(
                execution_plan_content_id, "execution_plan_content_id"
            ),
            launcher_binary_sha256=_sha256(
                launcher_binary_sha256, "launcher_binary_sha256"
            ),
            output_root=_output_root(output_root),
            binding_id="",
        )
        return cls(**{**normalized.__dict__, "binding_id": _content_id(normalized.unsigned_payload())})

    @classmethod
    def from_mapping(cls, value: object) -> "ObservedExecutionBindingV1":
        expected = frozenset({"schema"} | set(cls.__dataclass_fields__))
        payload = _exact_mapping(value, expected=expected, field="execution binding")
        if payload["schema"] != cls.SCHEMA:
            raise ObservedExecutionError("execution binding schema drifted")
        unsigned = {key: payload[key] for key in payload if key not in {"schema", "binding_id"}}
        rebuilt = cls.build(**unsigned)
        if _sha256(payload["binding_id"], "binding_id") != rebuilt.binding_id:
            raise ObservedExecutionError("execution binding content identity drifted")
        return rebuilt


@dataclass(frozen=True)
class NonceConsumptionReceiptV1:
    artifact_mode: ArtifactMode
    authorization_id: str
    run_id: str
    nonce_sha256: str
    consumed_at_utc: str
    ledger_entry_identity: str
    receipt_id: str

    SCHEMA = "common.nonce_consumption_receipt.v1"

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "artifact_mode": self.artifact_mode.value,
            "authorization_id": self.authorization_id,
            "run_id": self.run_id,
            "nonce_sha256": self.nonce_sha256,
            "consumed_at_utc": self.consumed_at_utc,
            "ledger_entry_identity": self.ledger_entry_identity,
        }

    def as_payload(self) -> dict[str, object]:
        return {"schema": self.SCHEMA, **self.unsigned_payload(), "receipt_id": self.receipt_id}

    @classmethod
    def build(cls, **values: object) -> "NonceConsumptionReceiptV1":
        normalized = cls(
            artifact_mode=_artifact_mode(values["artifact_mode"]),
            authorization_id=_sha256(values["authorization_id"], "authorization_id"),
            run_id=_text(values["run_id"], "run_id"),
            nonce_sha256=_sha256(values["nonce_sha256"], "nonce_sha256"),
            consumed_at_utc=_timestamp(values["consumed_at_utc"], "consumed_at_utc"),
            ledger_entry_identity=_sha256(values["ledger_entry_identity"], "ledger_entry_identity"),
            receipt_id="",
        )
        return cls(**{**normalized.__dict__, "receipt_id": _content_id(normalized.unsigned_payload())})

    @classmethod
    def from_mapping(cls, value: object) -> "NonceConsumptionReceiptV1":
        payload = _exact_mapping(
            value,
            expected=frozenset(
                {
                    "schema",
                    "artifact_mode",
                    "authorization_id",
                    "run_id",
                    "nonce_sha256",
                    "consumed_at_utc",
                    "ledger_entry_identity",
                    "receipt_id",
                }
            ),
            field="nonce receipt",
        )
        if payload["schema"] != cls.SCHEMA:
            raise ObservedExecutionError("nonce receipt schema drifted")
        rebuilt = cls.build(
            artifact_mode=payload["artifact_mode"],
            authorization_id=payload["authorization_id"],
            run_id=payload["run_id"],
            nonce_sha256=payload["nonce_sha256"],
            consumed_at_utc=payload["consumed_at_utc"],
            ledger_entry_identity=payload["ledger_entry_identity"],
        )
        if _sha256(payload["receipt_id"], "receipt_id") != rebuilt.receipt_id:
            raise ObservedExecutionError("nonce receipt content identity drifted")
        return rebuilt


@dataclass(frozen=True)
class ObservedRunStartReceiptV1:
    artifact_mode: ArtifactMode
    binding_id: str
    started_at_utc: str
    observed_bytes_opened: bool
    receipt_id: str

    SCHEMA = "common.observed_run_start_receipt.v1"

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "artifact_mode": self.artifact_mode.value,
            "binding_id": self.binding_id,
            "started_at_utc": self.started_at_utc,
            "observed_bytes_opened": self.observed_bytes_opened,
        }

    def as_payload(self) -> dict[str, object]:
        return {"schema": self.SCHEMA, **self.unsigned_payload(), "receipt_id": self.receipt_id}

    @classmethod
    def build(cls, **values: object) -> "ObservedRunStartReceiptV1":
        if values.get("observed_bytes_opened") is not False:
            raise ObservedExecutionError(
                "start receipt observed_bytes_opened must be false"
            )
        normalized = cls(
            artifact_mode=_artifact_mode(values["artifact_mode"]),
            binding_id=_sha256(values["binding_id"], "binding_id"),
            started_at_utc=_timestamp(values["started_at_utc"], "started_at_utc"),
            observed_bytes_opened=False,
            receipt_id="",
        )
        return cls(**{**normalized.__dict__, "receipt_id": _content_id(normalized.unsigned_payload())})

    @classmethod
    def from_mapping(cls, value: object) -> "ObservedRunStartReceiptV1":
        payload = _exact_mapping(
            value,
            expected=frozenset(
                {"schema", "artifact_mode", "binding_id", "started_at_utc", "observed_bytes_opened", "receipt_id"}
            ),
            field="start receipt",
        )
        if payload["schema"] != cls.SCHEMA:
            raise ObservedExecutionError("start receipt schema drifted")
        rebuilt = cls.build(
            artifact_mode=payload["artifact_mode"],
            binding_id=payload["binding_id"],
            started_at_utc=payload["started_at_utc"],
            observed_bytes_opened=payload["observed_bytes_opened"],
        )
        if _sha256(payload["receipt_id"], "receipt_id") != rebuilt.receipt_id:
            raise ObservedExecutionError("start receipt content identity drifted")
        return rebuilt


@dataclass(frozen=True)
class ObservedRunTerminalReceiptV1:
    artifact_mode: ArtifactMode
    binding_id: str
    terminal: str
    exit_code: int | None
    observed_bytes_opened: bool
    output_artifact_hashes: dict[str, str]
    stdout_sha256: str
    stderr_sha256: str
    started_at_utc: str
    ended_at_utc: str
    signal: int | None
    timeout: bool
    receipt_id: str

    SCHEMA = "common.observed_run_terminal_receipt.v1"

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "artifact_mode": self.artifact_mode.value,
            "binding_id": self.binding_id,
            "terminal": self.terminal,
            "exit_code": self.exit_code,
            "observed_bytes_opened": self.observed_bytes_opened,
            "output_artifact_hashes": dict(sorted(self.output_artifact_hashes.items())),
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "started_at_utc": self.started_at_utc,
            "ended_at_utc": self.ended_at_utc,
            "signal": self.signal,
            "timeout": self.timeout,
        }

    def as_payload(self) -> dict[str, object]:
        return {"schema": self.SCHEMA, **self.unsigned_payload(), "receipt_id": self.receipt_id}

    @classmethod
    def build(cls, **values: object) -> "ObservedRunTerminalReceiptV1":
        terminal = _text(values["terminal"], "terminal")
        exit_code = values["exit_code"]
        signal = values["signal"]
        timeout = values["timeout"]
        opened = values["observed_bytes_opened"]
        if type(opened) is not bool or type(timeout) is not bool:
            raise ObservedExecutionError("terminal boolean fields are invalid")
        if exit_code is not None and (type(exit_code) is not int or exit_code < 0):
            raise ObservedExecutionError("exit_code is invalid")
        if signal is not None and (type(signal) is not int or signal <= 0):
            raise ObservedExecutionError("signal is invalid")
        expected = {
            "SUCCESS": exit_code == 0 and signal is None and timeout is False,
            "ERROR": type(exit_code) is int and exit_code != 0 and signal is None and timeout is False,
            "TIMEOUT": exit_code is None and signal is None and timeout is True,
            "SIGNAL": exit_code is None and type(signal) is int and signal > 0 and timeout is False,
        }
        if terminal not in expected or not expected[terminal]:
            raise ObservedExecutionError("terminal exit semantics are inconsistent")
        raw_hashes = values["output_artifact_hashes"]
        if not isinstance(raw_hashes, Mapping):
            raise ObservedExecutionError("output_artifact_hashes must be a mapping")
        hashes: dict[str, str] = {}
        for key, value in raw_hashes.items():
            canonical_key = _text(key, "output artifact path")
            if canonical_key in hashes:
                raise ObservedExecutionError("duplicate output artifact path")
            hashes[canonical_key] = _sha256(value, "output artifact hash")
        started = _timestamp(values["started_at_utc"], "started_at_utc")
        ended = _timestamp(values["ended_at_utc"], "ended_at_utc")
        if ended < started:
            raise ObservedExecutionError("terminal ended_at_utc precedes start")
        normalized = cls(
            artifact_mode=_artifact_mode(values["artifact_mode"]),
            binding_id=_sha256(values["binding_id"], "binding_id"),
            terminal=terminal,
            exit_code=exit_code,
            observed_bytes_opened=opened,
            output_artifact_hashes=hashes,
            stdout_sha256=_sha256(values["stdout_sha256"], "stdout_sha256"),
            stderr_sha256=_sha256(values["stderr_sha256"], "stderr_sha256"),
            started_at_utc=started,
            ended_at_utc=ended,
            signal=signal,
            timeout=timeout,
            receipt_id="",
        )
        return cls(**{**normalized.__dict__, "receipt_id": _content_id(normalized.unsigned_payload())})

    @classmethod
    def from_mapping(cls, value: object) -> "ObservedRunTerminalReceiptV1":
        expected = frozenset({"schema"} | set(cls.__dataclass_fields__))
        payload = _exact_mapping(value, expected=expected, field="terminal receipt")
        if payload["schema"] != cls.SCHEMA:
            raise ObservedExecutionError("terminal receipt schema drifted")
        rebuilt = cls.build(
            **{
                key: payload[key]
                for key in payload
                if key not in {"schema", "receipt_id"}
            }
        )
        if _sha256(payload["receipt_id"], "receipt_id") != rebuilt.receipt_id:
            raise ObservedExecutionError("terminal receipt content identity drifted")
        return rebuilt


def assert_resume_compatible(
    sealed: ObservedExecutionBindingV1, requested: ObservedExecutionBindingV1
) -> None:
    if sealed.binding_id != requested.binding_id:
        raise ObservedExecutionError("resume binding identity drifted")


def require_production_terminal(
    receipt: ObservedRunTerminalReceiptV1,
) -> ObservedRunTerminalReceiptV1:
    if receipt.artifact_mode is not ArtifactMode.PRODUCTION:
        raise ObservedExecutionError(
            "synthetic fixture terminal cannot satisfy a production consumer"
        )
    return receipt


__all__ = [
    "ArtifactMode",
    "NonceConsumptionReceiptV1",
    "ObservedExecutionBindingV1",
    "ObservedExecutionError",
    "ObservedRunStartReceiptV1",
    "ObservedRunTerminalReceiptV1",
    "assert_resume_compatible",
    "parse_strict_json_bytes",
    "require_production_terminal",
]
