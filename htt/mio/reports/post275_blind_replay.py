"""MIO-owned PR-287 family-independent diagnostic pack factory."""

from __future__ import annotations

from typing import Mapping

from common.post275_blind_replay import (
    BlindReplayPackKind,
    DiagnosticPack,
    _issue_diagnostic_pack,
)


def build_mio_pack_c(
    *, metadata: Mapping[str, object], surfaces: Mapping[str, object]
) -> DiagnosticPack:
    """Build Pack C without posterior, evidence, or truth-certificate surfaces."""

    return _issue_diagnostic_pack(
        kind=BlindReplayPackKind.PACK_C,
        factory_module=__name__,
        metadata=metadata,
        surfaces=surfaces,
    )


__all__ = ["build_mio_pack_c"]
