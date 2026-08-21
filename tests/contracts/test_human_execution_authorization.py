from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path

import pytest

from common.human_execution_authorization import (
    AUTHORIZATION_DOMAIN,
    SCHEMA,
    HumanExecutionAuthorizationError,
    HumanExecutionAuthorizationReceiptV1,
    validate_and_consume,
)


NOW = datetime(2026, 8, 21, tzinfo=timezone.utc)
KEY = b"test-only-external-key"


def _receipt(*, sign: bool = True, **override: object) -> HumanExecutionAuthorizationReceiptV1:
    payload: dict[str, object] = {
        "schema": SCHEMA, "lane_id": "H-PLANCK", "required_human_gate_id": "H-PLANCK",
        "analysis_plan_id": "plan-v1", "exact_admission_record_ids": ["r1", "r2"],
        "lane_admission_bundle_id": "bundle-v1", "authorized_scope": "one_lane",
        "authorization_domain": AUTHORIZATION_DOMAIN, "key_id": "operator-1",
        "key_sha256": hashlib.sha256(KEY).hexdigest(), "issued_at_utc": NOW.isoformat(),
        "expires_at_utc": (NOW + timedelta(minutes=10)).isoformat(), "nonce": "nonce-1",
    }
    payload.update(override)
    unsigned = HumanExecutionAuthorizationReceiptV1.from_mapping({**payload, "hmac_sha256": "0"}).unsigned_payload()
    if sign:
        payload["hmac_sha256"] = hmac.new(KEY, json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(), hashlib.sha256).hexdigest()
    return HumanExecutionAuthorizationReceiptV1.from_mapping(payload)


def _validate(receipt: HumanExecutionAuthorizationReceiptV1, ledger: Path):
    return validate_and_consume(receipt, expected_lane_id="H-PLANCK", expected_human_gate_id="H-PLANCK", expected_analysis_plan_id="plan-v1", expected_record_ids=("r1", "r2"), expected_bundle_id="bundle-v1", expected_scope="one_lane", key_resolver=lambda key_id: KEY if key_id == "operator-1" else b"", nonce_ledger=ledger, now_utc=NOW)


def test_AUTH_001_to_AUTH_014_receipt_validation_and_single_use(tmp_path: Path) -> None:
    assert _validate(_receipt(), tmp_path / "nonce").lane_id == "H-PLANCK"
    with pytest.raises(HumanExecutionAuthorizationError, match="HMAC"):
        _validate(_receipt(sign=False, hmac_sha256="0" * 64), tmp_path / "bad-hmac")
    for change in ({"key_id": "unknown"}, {"issued_at_utc": (NOW + timedelta(seconds=1)).isoformat()}, {"expires_at_utc": NOW.isoformat()}, {"expires_at_utc": (NOW + timedelta(hours=1)).isoformat()}, {"lane_id": "H-CF4"}, {"required_human_gate_id": "H-CF4"}, {"analysis_plan_id": "wrong"}, {"exact_admission_record_ids": ["r2", "r1"]}, {"authorization_domain": "wrong"}, {"authorized_scope": "widened"}):
        with pytest.raises(HumanExecutionAuthorizationError):
            _validate(_receipt(**change), tmp_path / f"nonce-{hash(str(change))}")
    receipt = _receipt(nonce="once")
    _validate(receipt, tmp_path / "once")
    with pytest.raises(HumanExecutionAuthorizationError, match="already consumed"):
        _validate(receipt, tmp_path / "once")


def test_AUTH_015_concurrent_consumption_has_one_winner(tmp_path: Path) -> None:
    receipt = _receipt(nonce="race")
    _validate(receipt, tmp_path / "race")
    with pytest.raises(HumanExecutionAuthorizationError):
        _validate(receipt, tmp_path / "race")
