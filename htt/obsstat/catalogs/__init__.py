"""OBSSTAT catalog adapters."""

from __future__ import annotations

import sys as _sys

_PACKAGE_ALIASES = ("obsstat.catalogs", "htt.obsstat.catalogs")
_THIS_PACKAGE = _sys.modules[__name__]
if __name__ in _PACKAGE_ALIASES:
    for _alias in _PACKAGE_ALIASES:
        _sys.modules.setdefault(_alias, _THIS_PACKAGE)

from .cf4 import (
    Cf4Catalog,
    Cf4CatalogMetadata,
    build_cf4_catalog_from_mapping,
    load_cf4_catalog_npz,
)

_loaded = _sys.modules.get(f"{__name__}.cf4")
if _loaded is not None:
    for _alias in _PACKAGE_ALIASES:
        _sys.modules.setdefault(f"{_alias}.cf4", _loaded)

__all__ = [
    "Cf4Catalog",
    "Cf4CatalogMetadata",
    "build_cf4_catalog_from_mapping",
    "load_cf4_catalog_npz",
]

