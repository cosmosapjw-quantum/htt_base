"""Fail-closed access contract for the quarantined CF4 channel-c input.

PR-120 does not replace the affected observational numbers.  Active HTT
code may either omit channel ``c`` or stop with :class:`CF4InputQuarantined`.
Historical numerical reproduction belongs under ``legacy/cf4_p0`` and is
deliberately not exposed by this module.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, NoReturn

__all__ = [
    "ACTIVE_DEFAULT_CHANNELS",
    "CF4InputQuarantined",
    "CF4QuarantineStatus",
    "OPEN_FINDING_IDS",
    "cf4_quarantine_status",
    "normalize_active_channels",
    "require_cf4_observational_input",
]


OPEN_FINDING_IDS = (
    "C1-K5-MV-F1",
    "C3-K5-VCORR-ML-F1",
    "N-DATA-CF4-DOWNSTREAM",
)
ACTIVE_DEFAULT_CHANNELS = "abdefh"
_KNOWN_CHANNELS = "abcdefgh"


@dataclass(frozen=True)
class CF4QuarantineStatus:
    """Typed, non-numerical status for the unavailable active input."""

    status: str = "QUARANTINED_OPEN_FINDINGS"
    channel: str = "c"
    owner: str = "HTT"
    claim_tier: str = "blocked"
    finding_ids: tuple[str, ...] = OPEN_FINDING_IDS
    numerical_payload: None = None
    replacement_payload: None = None
    active_use_allowed: bool = False
    allowed_use: str = "legacy_reproduction_only_under_legacy/cf4_p0"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class CF4InputQuarantined(RuntimeError):
    """Raised before active code can consume the quarantined input."""

    def __init__(self, *, consumer: str):
        self.consumer = str(consumer).strip() or "unknown_consumer"
        self.status = cf4_quarantine_status()
        findings = ", ".join(self.status.finding_ids)
        super().__init__(
            f"CF4 observational channel c is quarantined for {self.consumer}; "
            f"OPEN findings: {findings}. No active numerical or replacement "
            "payload is available. Historical reproduction is confined to "
            "legacy/cf4_p0."
        )


def cf4_quarantine_status() -> CF4QuarantineStatus:
    """Return the canonical typed status without any numerical payload."""

    return CF4QuarantineStatus()


def require_cf4_observational_input(*, consumer: str) -> NoReturn:
    """Stop an active consumer before it can request channel-c numbers."""

    raise CF4InputQuarantined(consumer=consumer)


def normalize_active_channels(
    channels: str | Iterable[str] | None,
    *,
    consumer: str,
) -> str:
    """Validate an active HTT channel selection and reject channel ``c``.

    ``None`` represents the historical implicit/default likelihood request and
    therefore fails closed: that request included channel ``c`` before PR-120.
    Callers that intentionally exercise independent method substrate must pass
    :data:`ACTIVE_DEFAULT_CHANNELS` (or another explicit c-free set). Ordering
    is canonicalized so manifests and tests cannot hide channel ``c`` in a
    reordered iterable.
    """

    if channels is None:
        require_cf4_observational_input(
            consumer=f"{consumer} implicit/default likelihood",
        )
    requested = set(channels if not isinstance(channels, str) else channels)
    unknown = requested.difference(_KNOWN_CHANNELS)
    if unknown:
        raise ValueError(f"unknown HTT likelihood channels: {sorted(unknown)}")
    if "c" in requested:
        require_cf4_observational_input(consumer=consumer)
    return "".join(channel for channel in _KNOWN_CHANNELS if channel in requested)
