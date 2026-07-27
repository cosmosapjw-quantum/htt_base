"""Active MIO core namespace.

The historical scalar ceiling-family registry is available only through lazy
deprecated attribute access and is not listed as an active export.
"""
from __future__ import annotations

from importlib import import_module
import warnings

_LEGACY_CEILING_EXPORTS = {
    "CEILING_FAMILIES",
    "CeilingFamily",
    "CeilingStatus",
    "blocked_families",
    "certified_families",
    "get_ceiling_family",
}


def __getattr__(name: str):
    if name not in _LEGACY_CEILING_EXPORTS:
        raise AttributeError(name)
    warnings.warn(
        f"mio.core.{name} is a legacy scalar-ceiling export",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(import_module("mio.core.ceiling_families"), name)


__all__: list[str] = []
