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
from .redshift_selection import (
    RedshiftSelectionCorrectionSpec,
    apply_redshift_selection_correction,
)
from .spectroscopic_dipole import (
    SpectroscopicCatalog,
    SpectroscopicCatalogMetadata,
    SpectroscopicDipoleFeature,
    build_spectroscopic_catalog_from_mapping,
    estimate_data_random_dipole,
    first_moment,
)

for _submodule in ("cf4", "redshift_selection", "spectroscopic_dipole"):
    _loaded = _sys.modules.get(f"{__name__}.{_submodule}")
    if _loaded is not None:
        for _alias in _PACKAGE_ALIASES:
            _sys.modules.setdefault(f"{_alias}.{_submodule}", _loaded)

__all__ = [
    "Cf4Catalog",
    "Cf4CatalogMetadata",
    "RedshiftSelectionCorrectionSpec",
    "SpectroscopicCatalog",
    "SpectroscopicCatalogMetadata",
    "SpectroscopicDipoleFeature",
    "apply_redshift_selection_correction",
    "build_cf4_catalog_from_mapping",
    "build_spectroscopic_catalog_from_mapping",
    "estimate_data_random_dipole",
    "first_moment",
    "load_cf4_catalog_npz",
]
