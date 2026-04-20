"""VER2-V0 status snapshot helpers.

This module is intentionally thin: the canonical dataclass lives in
``common.contracts.StatusSnapshotEntry`` and this file provides a dedicated
import surface for later snapshot/export tooling without duplicating schema.
"""
from __future__ import annotations

from dataclasses import asdict

from common.contracts import StatusSnapshotEntry


def snapshot_entry_to_dict(entry: StatusSnapshotEntry) -> dict[str, object]:
    """Return a JSON-ready dictionary for one status row."""
    return asdict(entry)
