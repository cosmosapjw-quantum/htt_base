"""HTT-owned posterior exceedance summaries.

This module intentionally does not export MIO ``Pi``.  It reports an HTT
model-conditional posterior exceedance probability named ``P_post`` so the
posterior lane cannot be confused with MIO empirical diagnostic exceedance
curves.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any


DEFAULT_CAVEATS = (
    "not a MIO diagnostic Pi",
    "not a truth probability",
    "not family or geometry evidence",
    "transfer-conditional unless transfer_source is none",
)
ALLOWED_CLAIM_TIERS = frozenset(
    {
        "transfer_conditional",
        "diagnostic_only",
        "blocked",
    }
)
ALLOWED_TRANSFER_SOURCES = frozenset(
    {
        "none",
        "legacy_external_proxy",
        "external_transfer",
        "AniCLASS_external",
        "empirical_proxy",
    }
)
_FORBIDDEN_SOURCE_QUANTITY_TERMS = (
    "mio",
    "mio_pi",
    "pi_mio",
    "diagnostic pi",
    "diagnostic exceedance",
    "truth",
    "evidence",
    "family identification",
    "geometry detection",
)
_FORBIDDEN_ARTIFACT_TEXT_TERMS = (
    "native solver result",
    "external transfer " + "validated as " + "native",
    "validated as native",
    "native_validated",
    "bianchi " + "geometry detected",
    "bianchi " + "family identified",
    "family identification",
    "family identified",
    "geometry detection",
    "truth certificate",
    "model-independent truth certificate",
    "mio posterior",
    "mio evidence",
    "combined mio" + "+htt score",
)


def _non_empty(value: object, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _tuple_of_str(
    values: Sequence[object],
    name: str,
    *,
    require_non_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    result = tuple(_non_empty(value, name) for value in values)
    if require_non_empty and not result:
        raise ValueError(f"{name} must contain at least one entry")
    return result


def _finite_float(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _samples(values: Sequence[object]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("samples must be a non-string sequence")
    result = tuple(_finite_float(value, "samples") for value in values)
    if not result:
        raise ValueError("samples must contain at least one value")
    return result


def _jsonable(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_jsonable(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("metadata floats must be finite")
        return value
    if isinstance(value, (int, bool)) or value is None:
        return value
    raise TypeError(f"value {value!r} is not JSON-compatible")


def _metadata(value: Mapping[str, object] | None) -> dict[str, Any]:
    if value is None:
        return {}
    payload = _jsonable(value)
    if not isinstance(payload, dict):
        raise ValueError("metadata must be a mapping")
    json.dumps(payload, sort_keys=True, allow_nan=False)
    return payload


def _config_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_source_quantity(value: str) -> None:
    lowered = value.lower().replace("_", " ")
    for term in _FORBIDDEN_SOURCE_QUANTITY_TERMS:
        if term.replace("_", " ") in lowered:
            raise ValueError(
                "source_quantity must be an HTT posterior quantity, not a "
                "MIO diagnostic"
            )


def _scan_reserved_language(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _scan_reserved_language(str(key), f"{name}.{key}")
            _scan_reserved_language(item, f"{name}.{key}")
        return
    if isinstance(value, (str, bytes)):
        lowered = str(value).lower().replace("_", " ")
        for term in _FORBIDDEN_ARTIFACT_TEXT_TERMS:
            if term.replace("_", " ") in lowered:
                raise ValueError(f"{name} contains reserved claim language")
        return
    if isinstance(value, Sequence):
        for index, item in enumerate(value):
            _scan_reserved_language(item, f"{name}[{index}]")


def _validate_claim_tier(value: str) -> None:
    if value not in ALLOWED_CLAIM_TIERS:
        allowed = ", ".join(sorted(ALLOWED_CLAIM_TIERS))
        raise ValueError(f"claim_tier must be one of: {allowed}")
    _scan_reserved_language(value, "claim_tier")


def _validate_transfer_source(value: str) -> None:
    if value not in ALLOWED_TRANSFER_SOURCES:
        allowed = ", ".join(sorted(ALLOWED_TRANSFER_SOURCES))
        raise ValueError(f"transfer_source must be one of: {allowed}")
    _scan_reserved_language(value, "transfer_source")


def posterior_exceedance_summary(
    *,
    samples: Sequence[object],
    threshold: object,
    model_label: object,
    source_quantity: object,
    input_hashes: Sequence[object],
    generating_command: object,
    transfer_source: object = "legacy_external_proxy",
    claim_tier: object = "transfer_conditional",
    git_commit: object | None = None,
    worktree_state: object | None = None,
    metadata: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable HTT posterior exceedance summary.

    The returned quantity is named ``P_post``.  It is deliberately marked
    incompatible with MIO ``Pi`` because MIO ``Pi`` is an empirical diagnostic
    exceedance curve with threshold-policy metadata, not an HTT posterior.
    """

    sample_values = _samples(samples)
    threshold_value = _finite_float(threshold, "threshold")
    model = _non_empty(model_label, "model_label")
    source = _non_empty(source_quantity, "source_quantity")
    _validate_source_quantity(source)
    hashes = _tuple_of_str(input_hashes, "input_hashes", require_non_empty=True)
    command = _non_empty(generating_command, "generating_command")
    transfer = _non_empty(transfer_source, "transfer_source")
    _validate_transfer_source(transfer)
    tier = _non_empty(claim_tier, "claim_tier")
    _validate_claim_tier(tier)
    commit = None if git_commit is None else _non_empty(git_commit, "git_commit")
    state = (
        None
        if worktree_state is None
        else _non_empty(worktree_state, "worktree_state")
    )
    if commit is None and state is None:
        raise ValueError("posterior exceedance summary requires git_commit or worktree_state")
    extra_metadata = _metadata(metadata)
    _scan_reserved_language(extra_metadata, "metadata")

    exceedance_count = sum(1 for value in sample_values if value > threshold_value)
    probability = exceedance_count / len(sample_values)
    config_hash = _config_hash(
        {
            "model_label": model,
            "quantity_name": "P_post",
            "samples_count": len(sample_values),
            "source_quantity": source,
            "threshold": threshold_value,
            "transfer_source": transfer,
        }
    )

    return {
        "owner": "HTT",
        "implementation_scope": "htt",
        "claim_tier": tier,
        "quantity_name": "P_post",
        "definition": "model-conditional posterior exceedance",
        "mio_pi_compatible": False,
        "model_label": model,
        "source_quantity": source,
        "threshold": threshold_value,
        "samples_count": len(sample_values),
        "exceedance_count": exceedance_count,
        "exceedance_probability": probability,
        "exceedance_rule": "posterior_sample_value > threshold",
        "transfer_source": transfer,
        "config_hash": config_hash,
        "input_hashes": list(hashes),
        "generating_command": command,
        "git_commit": commit,
        "worktree_state": state,
        "sky_support_status": "not_directional",
        "covariance_status": "inherited_from_htt_posterior",
        "null_mock_status": "inherited_from_htt_posterior",
        "metadata": extra_metadata,
        "caveats": list(DEFAULT_CAVEATS),
    }
