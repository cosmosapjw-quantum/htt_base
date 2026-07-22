"""Compatibility export for :class:`enum.StrEnum` across the Python floor."""

from __future__ import annotations

from enum import Enum

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # pragma: no cover - exercised by the Python 3.10 CI lane

    class StrEnum(str, Enum):
        """Minimal stdlib-compatible fallback for explicit string-valued enums."""

        def __str__(self) -> str:
            return str(self.value)


__all__ = ["StrEnum"]
