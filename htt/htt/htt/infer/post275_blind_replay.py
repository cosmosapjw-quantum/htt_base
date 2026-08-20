"""Truth-incapable analyst surface for the PR-287 fresh challenge."""

from __future__ import annotations

from typing import Mapping

from common.post275_blind_replay import (
    BlindReplayContractError,
    BlindReplayPackKind,
    DiagnosticPack,
    FreshChallenge,
    FrozenSubmission,
    _issue_diagnostic_pack,
    validate_fresh_challenge,
)


def analyze_fresh_challenge(
    challenge: FreshChallenge,
    *,
    analyzer: object = None,
) -> FrozenSubmission:
    """Refuse ambient in-process callbacks pending an isolated analyst executor."""

    validate_fresh_challenge(challenge)
    if analyzer is not None:
        raise BlindReplayContractError(
            "in-process analyzer callbacks are forbidden by the blind capability boundary"
        )
    raise BlindReplayContractError(
        "capability-isolated analyst executor is not installed; fresh analysis remains blocked"
    )


def build_htt_pack_b(
    *, metadata: Mapping[str, object], surfaces: Mapping[str, object]
) -> DiagnosticPack:
    """Build the HTT-owned diagnostic gate pack; no likelihood is authorized."""

    return _issue_diagnostic_pack(
        kind=BlindReplayPackKind.PACK_B,
        factory_module=__name__,
        metadata=metadata,
        surfaces=surfaces,
    )


__all__ = ["analyze_fresh_challenge", "build_htt_pack_b"]
