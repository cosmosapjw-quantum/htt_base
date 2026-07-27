"""Legacy MIO channel-ratio reproduction.

The historical spelling is preserved for frozen callers.  Active analysis
uses ``AnchorStressReport``; this module does not establish physical occupancy.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
import warnings
from typing import Any

LEGACY_REPRODUCTION_ONLY = True

warnings.warn(
    "mio.formalism.channel_occupancy_vector is legacy reproduction only",
    DeprecationWarning,
    stacklevel=2,
)


def _finite(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _non_empty(value: object, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _config_hash(rows: Sequence[Mapping[str, object]]) -> str:
    encoded = json.dumps(
        [
            {
                "channel": str(row.get("channel", "")),
                "numerator": float(row.get("numerator", 0.0)),
                "denominator": float(row.get("denominator", 0.0)),
                "denominator_channel": str(
                    row.get("denominator_channel", row.get("channel", ""))
                ),
            }
            for row in rows
        ],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def channel_matched_occupancy(
    rows: Sequence[Mapping[str, object]],
    *,
    generating_command: str,
    worktree_state: str,
    input_hashes: Sequence[str],
) -> dict[str, Any]:
    """Return historical bounded channel ratios ``X_i/U_i``."""

    if isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("rows must be a non-empty sequence")
    hashes = tuple(_non_empty(value, "input_hashes") for value in input_hashes)
    if not hashes:
        raise ValueError("input_hashes must be non-empty")
    command = _non_empty(generating_command, "generating_command")
    state = _non_empty(worktree_state, "worktree_state")
    output_rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        channel = _non_empty(row.get("channel"), f"rows[{index}].channel")
        if channel in seen:
            raise ValueError(f"duplicate channel {channel!r}")
        seen.add(channel)
        denominator_channel = _non_empty(
            row.get("denominator_channel", channel),
            f"rows[{index}].denominator_channel",
        )
        if denominator_channel != channel:
            raise ValueError("cross-channel denominator use is forbidden")
        numerator = _finite(row.get("numerator"), f"rows[{index}].numerator")
        denominator = _finite(row.get("denominator"), f"rows[{index}].denominator")
        if numerator < 0.0:
            raise ValueError("numerator must be non-negative")
        if denominator <= 0.0:
            raise ValueError("denominator must be positive")
        ratio = numerator / denominator
        if not 0.0 <= ratio <= 1.0:
            raise ValueError("legacy ratio must be within [0, 1] without clipping")
        output_rows.append(
            {
                "channel": channel,
                "numerator": numerator,
                "denominator": denominator,
                "denominator_channel": denominator_channel,
                "ratio": ratio,
                "denominator_policy": "channel_matched",
                "legacy_compatibility": {"occupancy": ratio},
            }
        )
    return {
        "owner": "MIO",
        "implementation_scope": "mio",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "posterior_compatible": False,
        "evidence_compatible": False,
        "truth_certificate": False,
        "score_kind": "legacy_channel_matched_ratio_vector",
        "classification": "BC1_LEGACY_PROJECTION",
        "representation_policy": "BC2_NO_REPRESENTATION_PROMOTION",
        "physical_occupancy": False,
        "rows": output_rows,
        "config_hash": _config_hash(rows),
        "input_hashes": list(hashes),
        "generating_command": command,
        "worktree_state": state,
        "caveats": [
            "MIO diagnostic occupancy only",
            "not posterior odds",
            "not evidence",
            "not a truth certificate",
            "not family or geometry evidence",
        ],
    }


_OCCUPANCY_LANGUAGE_TOKENS = (
    "occupancy",
    "physical occupancy",
    "filling",
    "filled",
)


def classify_occupancy_language(
    *,
    numerator_channel: str,
    denominator_channel: str,
    requested_phrase: str,
    joint_admissible_ceiling_proof: str | None = None,
) -> dict[str, Any]:
    """Classify whether occupancy language is admissible for a scalar Q/F row.

    Occupancy language (e.g. "physical occupancy") is only admissible when the
    numerator and denominator live in the same channel (a channel-matched
    occupancy), or when a joint admissible-ceiling proof is attached. Otherwise
    a scalar Q/F row is a proxy score only and must not use occupancy language.
    """

    numerator = _non_empty(numerator_channel, "numerator_channel")
    denominator = _non_empty(denominator_channel, "denominator_channel")
    phrase = str(requested_phrase or "").strip().lower()
    channels_match = numerator == denominator
    has_ceiling_proof = bool(str(joint_admissible_ceiling_proof or "").strip())
    uses_occupancy_language = any(token in phrase for token in _OCCUPANCY_LANGUAGE_TOKENS)
    allowed = False

    blocked_reasons: list[str] = []
    if not channels_match:
        blocked_reasons.append("channel_mismatch")
    if uses_occupancy_language:
        blocked_reasons.append("occupancy_language_retired_for_legacy_ratio")
    if has_ceiling_proof:
        blocked_reasons.append(
            "joint_ceiling_proof_does_not_convert_ratio_to_occupancy"
        )
    status = "legacy_ratio_only"

    return {
        "owner": "MIO",
        "implementation_scope": "mio",
        "claim_tier": "diagnostic_only",
        "numerator_channel": numerator,
        "denominator_channel": denominator,
        "requested_phrase": requested_phrase,
        "uses_occupancy_language": uses_occupancy_language,
        "channels_match": channels_match,
        "joint_admissible_ceiling_proof": (
            str(joint_admissible_ceiling_proof) if has_ceiling_proof else None
        ),
        "allowed": allowed,
        "status": status,
        "blocked_reasons": blocked_reasons,
    }


__all__ = ["channel_matched_occupancy", "classify_occupancy_language"]
