"""Versioned, externally authenticated authorization for observed lane execution.

PR-289's ``ExecutionAuthorizationReceipt`` remains an identity-admission
placeholder.  This module deliberately does not mint authorizations: callers
provide an externally signed receipt and a trusted key resolver, and only this
validator can construct the opaque validated capability consumed by a runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
from typing import Callable, Mapping, Sequence


AUTHORIZATION_DOMAIN = "lane_data_execution"
SCHEMA = "htt.human_execution_authorization.v1"
MAX_TTL_SECONDS = 1800
_VALIDATED_TOKEN = object()


class HumanExecutionAuthorizationError(ValueError):
    """An external receipt is malformed, unauthenticated, or not usable."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _utc(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise HumanExecutionAuthorizationError(f"{field_name} must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise HumanExecutionAuthorizationError(f"{field_name} must be UTC")
    return parsed


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HumanExecutionAuthorizationError(f"{field_name} must be non-empty")
    return value


def _ordered_ids(value: Sequence[object]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not value:
        raise HumanExecutionAuthorizationError("exact_admission_record_ids must be non-empty")
    parsed = tuple(_text(item, "exact_admission_record_id") for item in value)
    if len(parsed) != len(set(parsed)):
        raise HumanExecutionAuthorizationError("exact_admission_record_ids must be unique and ordered")
    return parsed


@dataclass(frozen=True)
class HumanExecutionAuthorizationReceiptV1:
    lane_id: str
    required_human_gate_id: str
    analysis_plan_id: str
    exact_admission_record_ids: tuple[str, ...]
    lane_admission_bundle_id: str
    authorized_scope: str
    authorization_domain: str
    key_id: str
    key_sha256: str
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    hmac_sha256: str

    def unsigned_payload(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "lane_id": self.lane_id,
            "required_human_gate_id": self.required_human_gate_id,
            "analysis_plan_id": self.analysis_plan_id,
            "exact_admission_record_ids": list(self.exact_admission_record_ids),
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
            "authorized_scope": self.authorized_scope,
            "authorization_domain": self.authorization_domain,
            "key_id": self.key_id,
            "key_sha256": self.key_sha256,
            "issued_at_utc": self.issued_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "nonce": self.nonce,
        }

    @property
    def authorization_id(self) -> str:
        return _sha256(self.unsigned_payload())

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "HumanExecutionAuthorizationReceiptV1":
        if not isinstance(payload, Mapping) or payload.get("schema") != SCHEMA:
            raise HumanExecutionAuthorizationError("authorization schema mismatch")
        return cls(
            lane_id=_text(payload.get("lane_id"), "lane_id"),
            required_human_gate_id=_text(payload.get("required_human_gate_id"), "required_human_gate_id"),
            analysis_plan_id=_text(payload.get("analysis_plan_id"), "analysis_plan_id"),
            exact_admission_record_ids=_ordered_ids(payload.get("exact_admission_record_ids", ())),
            lane_admission_bundle_id=_text(payload.get("lane_admission_bundle_id"), "lane_admission_bundle_id"),
            authorized_scope=_text(payload.get("authorized_scope"), "authorized_scope"),
            authorization_domain=_text(payload.get("authorization_domain"), "authorization_domain"),
            key_id=_text(payload.get("key_id"), "key_id"),
            key_sha256=_text(payload.get("key_sha256"), "key_sha256"),
            issued_at_utc=_text(payload.get("issued_at_utc"), "issued_at_utc"),
            expires_at_utc=_text(payload.get("expires_at_utc"), "expires_at_utc"),
            nonce=_text(payload.get("nonce"), "nonce"),
            hmac_sha256=_text(payload.get("hmac_sha256"), "hmac_sha256"),
        )


@dataclass(frozen=True)
class ValidatedHumanExecutionAuthorization:
    """Opaque runner capability; constructor use is restricted to the validator."""

    authorization_id: str
    lane_id: str
    authorization_hash: str
    _token: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._token is not _VALIDATED_TOKEN:
            raise HumanExecutionAuthorizationError("validated authorization is validator-issued only")


def _consume_nonce(nonce_ledger: Path, nonce: str) -> None:
    nonce_ledger.mkdir(mode=0o700, parents=True, exist_ok=True)
    ledger_status = nonce_ledger.lstat()
    if stat.S_ISLNK(ledger_status.st_mode) or not stat.S_ISDIR(ledger_status.st_mode):
        raise HumanExecutionAuthorizationError("nonce ledger must be a real directory")
    target = nonce_ledger / f"{hashlib.sha256(nonce.encode('utf-8')).hexdigest()}.nonce"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(target, flags, 0o600)
    except FileExistsError as exc:
        raise HumanExecutionAuthorizationError("authorization nonce was already consumed") from exc
    except OSError as exc:
        raise HumanExecutionAuthorizationError("nonce ledger cannot safely consume nonce") from exc
    try:
        os.write(descriptor, nonce.encode("utf-8"))
    finally:
        os.close(descriptor)
    created = target.lstat()
    if stat.S_ISLNK(created.st_mode) or created.st_nlink != 1 or not stat.S_ISREG(created.st_mode):
        raise HumanExecutionAuthorizationError("nonce ledger entry is not a private regular file")


def validate_and_consume(
    receipt: HumanExecutionAuthorizationReceiptV1,
    *,
    expected_lane_id: str,
    expected_human_gate_id: str,
    expected_analysis_plan_id: str,
    expected_record_ids: Sequence[str],
    expected_bundle_id: str,
    expected_scope: str,
    key_resolver: Callable[[str], bytes],
    nonce_ledger: Path,
    now_utc: datetime,
) -> ValidatedHumanExecutionAuthorization:
    """Authenticate a receipt and atomically consume its nonce for one lane start."""

    if type(receipt) is not HumanExecutionAuthorizationReceiptV1:
        raise HumanExecutionAuthorizationError("authorization receipt must be the exact V1 type")
    if receipt.authorization_domain != AUTHORIZATION_DOMAIN:
        raise HumanExecutionAuthorizationError("authorization domain mismatch")
    expected = {
        "lane_id": expected_lane_id,
        "required_human_gate_id": expected_human_gate_id,
        "analysis_plan_id": expected_analysis_plan_id,
        "lane_admission_bundle_id": expected_bundle_id,
        "authorized_scope": expected_scope,
    }
    for field_name, expected_value in expected.items():
        if getattr(receipt, field_name) != expected_value:
            raise HumanExecutionAuthorizationError(f"authorization {field_name} mismatch")
    if tuple(expected_record_ids) != receipt.exact_admission_record_ids:
        raise HumanExecutionAuthorizationError("authorization admission record identity/order mismatch")
    issued = _utc(receipt.issued_at_utc, "issued_at_utc")
    expires = _utc(receipt.expires_at_utc, "expires_at_utc")
    if now_utc.tzinfo is None or now_utc.utcoffset() != timezone.utc.utcoffset(now_utc):
        raise HumanExecutionAuthorizationError("validator time must be UTC")
    if issued > now_utc or expires <= now_utc or expires <= issued:
        raise HumanExecutionAuthorizationError("authorization is not active in its half-open interval")
    if (expires - issued).total_seconds() > MAX_TTL_SECONDS:
        raise HumanExecutionAuthorizationError("authorization TTL exceeds registered maximum")
    try:
        key = key_resolver(receipt.key_id)
    except Exception as exc:
        raise HumanExecutionAuthorizationError("authorization key is unavailable") from exc
    if not isinstance(key, bytes) or hashlib.sha256(key).hexdigest() != receipt.key_sha256:
        raise HumanExecutionAuthorizationError("authorization key identity mismatch")
    expected_hmac = hmac.new(key, _canonical_bytes(receipt.unsigned_payload()), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hmac, receipt.hmac_sha256):
        raise HumanExecutionAuthorizationError("authorization HMAC mismatch")
    _consume_nonce(nonce_ledger, receipt.nonce)
    return ValidatedHumanExecutionAuthorization(
        authorization_id=receipt.authorization_id,
        lane_id=receipt.lane_id,
        authorization_hash=_sha256({**receipt.unsigned_payload(), "hmac_sha256": receipt.hmac_sha256}),
        _token=_VALIDATED_TOKEN,
    )
