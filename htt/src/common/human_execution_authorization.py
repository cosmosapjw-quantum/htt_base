"""Admission-bound, external-key validation for a future observed run.

This module validates a human-issued authorization without opening a data
payload or consuming its nonce.  PR-305 owns the transaction that consumes a
nonce immediately before opening any observed bytes.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import stat
from typing import Mapping

from common.data_identity import (
    AdmissionStatus,
    DataIdentityError,
    LaneAdmissionDecision,
    LaneSpec,
    build_not_authorized_receipt,
    canonical_sha256,
    load_lane_registry,
    replay_lane_admission_decision,
)


AUTHORIZATION_SCHEMA = "common.human_execution_authorization_receipt.v1"
VALIDATED_AUTHORIZATION_SCHEMA = "common.validated_human_execution_authorization.v1"
AUTHORIZATION_DOMAIN = "lane_data_execution"
MAX_AUTHORIZATION_TTL = timedelta(seconds=1800)

_RAW_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_OBJECT = re.compile(r"^[0-9a-f]{40}$")
_VALIDATION_TOKEN = object()
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = (
    _REPOSITORY_ROOT
    / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
_SCOPES_BY_LANE = {
    "PLANCK": "admitted_planck_observed_execution",
    "CF4": "admitted_cf4_observed_execution",
    "HSC_KIDS": "admitted_hsc_kids_observed_execution",
    "ACT": "admitted_act_observed_execution",
    "DESI": "admitted_desi_observed_execution",
    "JWST_SN": "admitted_jwst_sn_observed_execution",
}


class HumanExecutionAuthorizationError(ValueError):
    """Raised when a human-execution authorization cannot be validated."""


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise HumanExecutionAuthorizationError(f"{field} must be a non-empty canonical string")
    return value


def _sha256_identity(value: object, field: str) -> str:
    text = _text(value, field)
    if not text.startswith("sha256:") or _RAW_SHA256.fullmatch(text[7:]) is None:
        raise HumanExecutionAuthorizationError(f"{field} must be a lowercase sha256 identity")
    return text


def _git_object(value: object, field: str) -> str:
    text = _text(value, field)
    if _GIT_OBJECT.fullmatch(text) is None:
        raise HumanExecutionAuthorizationError(f"{field} must be a lowercase git object id")
    return text


def _utc(value: object, field: str) -> tuple[str, datetime]:
    text = _text(value, field)
    if not text.endswith("Z"):
        raise HumanExecutionAuthorizationError(f"{field} must use a UTC Z timestamp")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise HumanExecutionAuthorizationError(f"{field} is not a canonical UTC timestamp") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != text:
        raise HumanExecutionAuthorizationError(f"{field} is not a canonical UTC timestamp")
    return text, parsed


def _canonical_bytes(payload: Mapping[str, object]) -> bytes:
    try:
        return json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise HumanExecutionAuthorizationError("authorization payload is not canonical finite JSON") from exc


def _exact_mapping(
    payload: Mapping[str, object], *, expected: frozenset[str]
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise HumanExecutionAuthorizationError("authorization receipt fields drifted")
    return payload


def _record_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise HumanExecutionAuthorizationError("exact_admission_record_ids must be an ordered sequence")
    records = tuple(_sha256_identity(item, "exact_admission_record_ids") for item in value)
    if not records or len(records) != len(set(records)):
        raise HumanExecutionAuthorizationError("exact_admission_record_ids must be non-empty and unique")
    return records


def lane_spec_content_id(lane_spec: LaneSpec) -> str:
    """Content-bind the exact PR-289 LaneSpec used by this validation."""

    if type(lane_spec) is not LaneSpec:
        raise HumanExecutionAuthorizationError("lane_spec must be the exact PR-289 LaneSpec type")
    return canonical_sha256(
        {
            "schema": "common.human_execution_authorization_lane_spec_binding.v1",
            "lane_spec": lane_spec.as_payload(),
        }
    )


@dataclass(frozen=True)
class HumanExecutionAuthorizationReceiptV1:
    authorization_id: str
    lane_id: str
    exact_admission_record_ids: tuple[str, ...]
    lane_admission_bundle_id: str
    analysis_plan_id: str
    required_human_gate_id: str
    authorized_scope: str
    authorization_domain: str
    candidate_commit: str
    candidate_tree: str
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    authority_key_id: str
    authorization_hmac_sha256: str

    @classmethod
    def from_payload(
        cls, payload: Mapping[str, object]
    ) -> "HumanExecutionAuthorizationReceiptV1":
        expected = frozenset(
            {
                "schema",
                "authorization_id",
                "lane_id",
                "exact_admission_record_ids",
                "lane_admission_bundle_id",
                "analysis_plan_id",
                "required_human_gate_id",
                "authorized_scope",
                "authorization_domain",
                "candidate_commit",
                "candidate_tree",
                "issued_at_utc",
                "expires_at_utc",
                "nonce",
                "authority_key_id",
                "authorization_hmac_sha256",
            }
        )
        checked = _exact_mapping(payload, expected=expected)
        if checked["schema"] != AUTHORIZATION_SCHEMA:
            raise HumanExecutionAuthorizationError("authorization receipt schema drifted")
        receipt = cls(
            authorization_id=_sha256_identity(checked["authorization_id"], "authorization_id"),
            lane_id=_text(checked["lane_id"], "lane_id"),
            exact_admission_record_ids=_record_ids(checked["exact_admission_record_ids"]),
            lane_admission_bundle_id=_sha256_identity(
                checked["lane_admission_bundle_id"], "lane_admission_bundle_id"
            ),
            analysis_plan_id=_text(checked["analysis_plan_id"], "analysis_plan_id"),
            required_human_gate_id=_text(
                checked["required_human_gate_id"], "required_human_gate_id"
            ),
            authorized_scope=_text(checked["authorized_scope"], "authorized_scope"),
            authorization_domain=_text(
                checked["authorization_domain"], "authorization_domain"
            ),
            candidate_commit=_git_object(checked["candidate_commit"], "candidate_commit"),
            candidate_tree=_git_object(checked["candidate_tree"], "candidate_tree"),
            issued_at_utc=_utc(checked["issued_at_utc"], "issued_at_utc")[0],
            expires_at_utc=_utc(checked["expires_at_utc"], "expires_at_utc")[0],
            nonce=_text(checked["nonce"], "nonce"),
            authority_key_id=_sha256_identity(checked["authority_key_id"], "authority_key_id"),
            authorization_hmac_sha256=_sha256_identity(
                "sha256:" + _text(
                    checked["authorization_hmac_sha256"], "authorization_hmac_sha256"
                ),
                "authorization_hmac_sha256",
            )[7:],
        )
        if receipt.authorization_id != canonical_sha256(receipt.unsigned_payload()):
            raise HumanExecutionAuthorizationError("authorization_id does not bind the unsigned receipt")
        return receipt

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": AUTHORIZATION_SCHEMA,
            "lane_id": self.lane_id,
            "exact_admission_record_ids": list(self.exact_admission_record_ids),
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
            "analysis_plan_id": self.analysis_plan_id,
            "required_human_gate_id": self.required_human_gate_id,
            "authorized_scope": self.authorized_scope,
            "authorization_domain": self.authorization_domain,
            "candidate_commit": self.candidate_commit,
            "candidate_tree": self.candidate_tree,
            "issued_at_utc": self.issued_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "nonce": self.nonce,
            "authority_key_id": self.authority_key_id,
        }

    def hmac_payload(self) -> dict[str, object]:
        return {"authorization_id": self.authorization_id, **self.unsigned_payload()}

    def as_payload(self) -> dict[str, object]:
        return {
            **self.hmac_payload(),
            "authorization_hmac_sha256": self.authorization_hmac_sha256,
        }


@dataclass(frozen=True)
class ValidatedHumanExecutionAuthorization:
    receipt: HumanExecutionAuthorizationReceiptV1
    replayed_lane_spec_content_id: str
    replayed_admission_bundle_id: str
    validated_at_utc: str
    validation_content_id: str
    _construction_token: InitVar[object] = None
    _seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _VALIDATION_TOKEN:
            raise HumanExecutionAuthorizationError(
                "ValidatedHumanExecutionAuthorization must be validator-built"
            )
        if type(self.receipt) is not HumanExecutionAuthorizationReceiptV1:
            raise HumanExecutionAuthorizationError("validated authorization receipt type drifted")
        _sha256_identity(self.replayed_lane_spec_content_id, "replayed_lane_spec_content_id")
        _sha256_identity(self.replayed_admission_bundle_id, "replayed_admission_bundle_id")
        _utc(self.validated_at_utc, "validated_at_utc")
        expected = canonical_sha256(self._unsigned_payload())
        if self.validation_content_id != expected:
            raise HumanExecutionAuthorizationError("validated authorization content identity drifted")
        object.__setattr__(self, "_seal", canonical_sha256(self.as_payload()))

    def _unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": VALIDATED_AUTHORIZATION_SCHEMA,
            "receipt": self.receipt.as_payload(),
            "replayed_lane_spec_content_id": self.replayed_lane_spec_content_id,
            "replayed_admission_bundle_id": self.replayed_admission_bundle_id,
            "validated_at_utc": self.validated_at_utc,
        }

    def as_payload(self) -> dict[str, object]:
        payload = {**self._unsigned_payload(), "validation_content_id": self.validation_content_id}
        if hasattr(self, "_seal") and canonical_sha256(payload) != self._seal:
            raise HumanExecutionAuthorizationError("validated authorization object drifted")
        return payload


def _external_authority_key(path: Path) -> tuple[bytes, str]:
    if not isinstance(path, Path) or not path.is_absolute():
        raise HumanExecutionAuthorizationError("authority_key_path must be an absolute external path")
    try:
        path.relative_to(_REPOSITORY_ROOT)
    except ValueError:
        pass
    else:
        raise HumanExecutionAuthorizationError("authority_key_path must remain outside the repository")
    try:
        info = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise HumanExecutionAuthorizationError("authority key is unavailable") from exc
    if resolved != path or path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise HumanExecutionAuthorizationError("authority key must be one external regular file")
    try:
        resolved.relative_to(_REPOSITORY_ROOT)
    except ValueError:
        pass
    else:
        raise HumanExecutionAuthorizationError("authority_key_path must remain outside the repository")
    try:
        key = path.read_bytes()
    except OSError as exc:
        raise HumanExecutionAuthorizationError("authority key cannot be read") from exc
    if not key:
        raise HumanExecutionAuthorizationError("authority key is empty")
    return key, "sha256:" + hashlib.sha256(key).hexdigest()


def replay_complete_lane_admission(
    *, lane_spec: LaneSpec, admission_decision: LaneAdmissionDecision
) -> LaneAdmissionDecision:
    """Replay one complete PR-289 decision against the registered LaneSpec."""

    if type(lane_spec) is not LaneSpec:
        raise HumanExecutionAuthorizationError("lane_spec must be the exact PR-289 LaneSpec type")
    if type(admission_decision) is not LaneAdmissionDecision:
        raise HumanExecutionAuthorizationError(
            "admission_decision must be the exact PR-289 LaneAdmissionDecision type"
        )
    try:
        registry = load_lane_registry(_REGISTRY_PATH)
        registered_lane = registry.lane(lane_spec.lane_id)
    except DataIdentityError as exc:
        raise HumanExecutionAuthorizationError("registered PR-289 lane registry is unavailable") from exc
    if lane_spec.as_payload() != registered_lane.as_payload():
        raise HumanExecutionAuthorizationError("lane_spec is not the registered exact PR-289 lane")
    if (
        admission_decision.lane_id != lane_spec.lane_id
        or admission_decision.product_id != lane_spec.product_id
        or admission_decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
    ):
        raise HumanExecutionAuthorizationError("authorization requires a complete admitted PR-289 lane")
    try:
        replayed = replay_lane_admission_decision(
            admission_decision.as_payload(), registry=registry
        )
        pr289_receipt = build_not_authorized_receipt(lane_spec, replayed)
    except DataIdentityError as exc:
        raise HumanExecutionAuthorizationError("admission replay failed") from exc
    if pr289_receipt.status.value != "NOT_AUTHORIZED":
        raise HumanExecutionAuthorizationError("PR-289 receipt unexpectedly promoted authorization")
    return replayed


def validate_human_execution_authorization(
    *,
    receipt_payload: Mapping[str, object],
    lane_spec: LaneSpec,
    admission_decision: LaneAdmissionDecision,
    expected_candidate_commit: str,
    expected_candidate_tree: str,
    evaluated_at_utc: str,
    authority_key_path: Path,
) -> ValidatedHumanExecutionAuthorization:
    """Validate, but never consume, a future lane-scoped authorization."""

    replayed = replay_complete_lane_admission(
        lane_spec=lane_spec, admission_decision=admission_decision
    )
    receipt = HumanExecutionAuthorizationReceiptV1.from_payload(receipt_payload)
    expected_commit = _git_object(expected_candidate_commit, "expected_candidate_commit")
    expected_tree = _git_object(expected_candidate_tree, "expected_candidate_tree")
    evaluated_text, evaluated = _utc(evaluated_at_utc, "evaluated_at_utc")
    expected_record_ids = tuple(record.record_id for record in replayed.records)
    if receipt.lane_id != lane_spec.lane_id:
        raise HumanExecutionAuthorizationError("authorization lane does not match replayed admission")
    if receipt.exact_admission_record_ids != expected_record_ids:
        raise HumanExecutionAuthorizationError("authorization record ordering or membership drifted")
    if receipt.lane_admission_bundle_id != replayed.lane_admission_bundle_id:
        raise HumanExecutionAuthorizationError("authorization admission bundle drifted")
    if receipt.analysis_plan_id != lane_spec.analysis_plan_id:
        raise HumanExecutionAuthorizationError("authorization analysis plan drifted")
    if receipt.required_human_gate_id != lane_spec.required_human_gate_id:
        raise HumanExecutionAuthorizationError("authorization human gate drifted")
    if receipt.authorization_domain != AUTHORIZATION_DOMAIN:
        raise HumanExecutionAuthorizationError("authorization domain is not registered")
    if receipt.authorized_scope != _SCOPES_BY_LANE.get(lane_spec.lane_id):
        raise HumanExecutionAuthorizationError("authorization scope is not registered for the lane")
    if receipt.candidate_commit != expected_commit or receipt.candidate_tree != expected_tree:
        raise HumanExecutionAuthorizationError("authorization candidate commit or tree drifted")
    issued_text, issued = _utc(receipt.issued_at_utc, "issued_at_utc")
    _, expires = _utc(receipt.expires_at_utc, "expires_at_utc")
    if expires <= issued:
        raise HumanExecutionAuthorizationError("authorization interval is empty or reversed")
    if expires - issued > MAX_AUTHORIZATION_TTL:
        raise HumanExecutionAuthorizationError("authorization TTL exceeds 1800 seconds")
    if issued > evaluated:
        raise HumanExecutionAuthorizationError("authorization issue time is in the future")
    if not issued <= evaluated < expires:
        raise HumanExecutionAuthorizationError("authorization is expired at evaluation")
    key, expected_key_id = _external_authority_key(authority_key_path)
    if receipt.authority_key_id != expected_key_id:
        raise HumanExecutionAuthorizationError("authorization authority key id is unknown")
    expected_hmac = hmac.new(key, _canonical_bytes(receipt.hmac_payload()), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(receipt.authorization_hmac_sha256, expected_hmac):
        raise HumanExecutionAuthorizationError("authorization HMAC is forged or mismatched")
    lane_content_id = lane_spec_content_id(lane_spec)
    unsigned = {
        "schema": VALIDATED_AUTHORIZATION_SCHEMA,
        "receipt": receipt.as_payload(),
        "replayed_lane_spec_content_id": lane_content_id,
        "replayed_admission_bundle_id": replayed.lane_admission_bundle_id,
        "validated_at_utc": evaluated_text,
    }
    return ValidatedHumanExecutionAuthorization(
        receipt=receipt,
        replayed_lane_spec_content_id=lane_content_id,
        replayed_admission_bundle_id=replayed.lane_admission_bundle_id,
        validated_at_utc=evaluated_text,
        validation_content_id=canonical_sha256(unsigned),
        _construction_token=_VALIDATION_TOKEN,
    )


__all__ = [
    "AUTHORIZATION_DOMAIN",
    "AUTHORIZATION_SCHEMA",
    "HumanExecutionAuthorizationError",
    "HumanExecutionAuthorizationReceiptV1",
    "MAX_AUTHORIZATION_TTL",
    "ValidatedHumanExecutionAuthorization",
    "lane_spec_content_id",
    "replay_complete_lane_admission",
    "validate_human_execution_authorization",
]
