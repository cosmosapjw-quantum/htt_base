"""Preferred-axis construction and validation helpers for HTT.

The canonical schema remains :class:`common.contracts.PreferredAxis`.  This
module only provides HTT-facing constructors and gate-oriented validation so
callers do not create another axis type while wiring downstream synthesis
locks.
"""
from __future__ import annotations

import math
import re

from common.contracts import PreferredAxis

__all__ = [
    "PreferredAxis",
    "axis_coordinate_blockers",
    "axis_provenance_is_stable",
    "build_preferred_axis",
]


_PLACEHOLDER_HASHES = {
    "",
    "abc",
    "abc123",
    "axis-1",
    "placeholder",
    "pending",
    "legacy_unspecified",
    "none",
    "unknown",
    "worktree",
}
_AXIS_PROVENANCE_RE = re.compile(r"^(?:[0-9a-fA-F]{16}|sha256:[0-9a-fA-F]{64})$")


def build_preferred_axis(
    *,
    l_deg: float,
    b_deg: float,
    label: str,
    source: str,
    weight_mode: str,
    selection_mode: str,
    production_allowed: bool = False,
    provenance_hash: str = "",
) -> PreferredAxis:
    """Build the canonical axis with a fail-closed production default."""

    return PreferredAxis(
        l_deg=l_deg,
        b_deg=b_deg,
        label=label,
        source=source,  # type: ignore[arg-type]
        weight_mode=weight_mode,  # type: ignore[arg-type]
        selection_mode=selection_mode,  # type: ignore[arg-type]
        production_allowed=bool(production_allowed),
        provenance_hash=str(provenance_hash),
    )


def axis_coordinate_blockers(axis: PreferredAxis) -> tuple[str, ...]:
    """Return gate blockers for non-finite or out-of-domain axis coordinates."""

    blocked: list[str] = []
    l_deg = float(axis.l_deg)
    b_deg = float(axis.b_deg)
    if not math.isfinite(l_deg):
        blocked.append("axis_l_deg_not_finite")
    elif not (0.0 <= l_deg < 360.0):
        blocked.append("axis_l_deg_out_of_range")
    if not math.isfinite(b_deg):
        blocked.append("axis_b_deg_not_finite")
    elif not (-90.0 <= b_deg <= 90.0):
        blocked.append("axis_b_deg_out_of_range")
    return tuple(blocked)


def axis_provenance_is_stable(value: str) -> bool:
    """Return whether a provenance token is non-placeholder gate metadata."""

    token = str(value).strip()
    lowered = token.lower()
    if lowered in _PLACEHOLDER_HASHES:
        return False
    if "placeholder" in lowered or "pending" in lowered:
        return False
    return _AXIS_PROVENANCE_RE.fullmatch(token) is not None
