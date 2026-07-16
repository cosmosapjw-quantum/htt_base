"""Repo-root compatibility shim for the nested HTT package.

The installable HTT package lives under ``htt/htt/`` while the active
``bass-py`` package root is ``htt/``. Importing from the repository root would
otherwise resolve this outer directory as a namespace package and shadow the
nested public ``htt`` package.
"""

from __future__ import annotations

import sys
import importlib as _importlib
from importlib import abc as _importlib_abc
from importlib import util as _importlib_util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_NESTED_HTT = _ROOT / "htt" / "htt"

if _NESTED_HTT.is_dir():
    _nested_str = str(_NESTED_HTT)
    if _nested_str not in __path__:
        __path__.append(_nested_str)

__version__ = "8.3.0"
_TOP_LEVEL_ALIASES = (
    "bass",
    "obsstat",
    "mio",
    "tsc_legacy",
    "tsc",
    "teff",
    "workspace",
)
_ALIAS_PREFIXES = {
    f"htt.{name}": name for name in _TOP_LEVEL_ALIASES
}
__all__ = [
    "core",
    "nulls",
    "infer",
    "departure",
    "bridge",
    "figures",
    "integration",
    "zoa",
    "direction",
    "statistics",
    "rest_frame",
    "tilt",
    "catalogs",
    *_TOP_LEVEL_ALIASES,
]


def _alias_top_level_package(name: str):
    """Bind a canonical bass-py package to the repo-root ``htt`` shim."""
    module = _importlib.import_module(name)
    sys.modules[f"htt.{name}"] = module
    globals()[name] = module
    prefix = f"{name}."
    for loaded_name, loaded_module in tuple(sys.modules.items()):
        if loaded_name.startswith(prefix):
            sys.modules.setdefault(f"htt.{loaded_name}", loaded_module)
    return module


class _CompatibilityAliasLoader(_importlib_abc.Loader):
    """Load one ``htt.<owner>.*`` name as its canonical module object.

    Returning the already-loaded canonical object from ``create_module`` keeps
    ``__name__``, ``__package__``, ``__spec__``, and ``__loader__`` canonical.
    The compatibility spelling is only an additional ``sys.modules`` key; the
    module is never executed a second time under the alias name.
    """

    def __init__(self, alias_name: str, canonical_name: str) -> None:
        self.alias_name = alias_name
        self.canonical_name = canonical_name
        self._canonical_metadata = None

    def create_module(self, spec):  # noqa: ANN001 - importlib protocol
        module = _importlib.import_module(self.canonical_name)
        self._canonical_metadata = (
            module.__name__,
            module.__package__,
            module.__spec__,
            module.__loader__,
        )
        return module

    def exec_module(self, module) -> None:  # noqa: ANN001 - importlib protocol
        canonical = sys.modules.get(self.canonical_name)
        if canonical is not module:
            raise ImportError(
                f"compatibility alias {self.alias_name!r} lost canonical identity"
            )
        if self._canonical_metadata is None:
            raise ImportError(
                f"compatibility alias {self.alias_name!r} lacks canonical metadata"
            )
        (
            module.__name__,
            module.__package__,
            module.__spec__,
            module.__loader__,
        ) = self._canonical_metadata
        sys.modules[self.alias_name] = canonical


class _CompatibilityAliasFinder(_importlib_abc.MetaPathFinder):
    """Resolve only declared deep ``htt`` compatibility prefixes.

    This deliberately does not intercept ordinary imports or active HTT
    subpackages such as ``htt.core``.  Canonical modules are imported lazily,
    one requested module at a time, so alias identity does not require walking
    or eagerly importing an owner package's module tree.
    """

    _htt_compat_alias_prefixes = tuple(_ALIAS_PREFIXES)

    def find_spec(self, fullname, path=None, target=None):  # noqa: ANN001
        for alias_prefix, canonical_prefix in _ALIAS_PREFIXES.items():
            nested_prefix = f"{alias_prefix}."
            if not fullname.startswith(nested_prefix):
                continue
            suffix = fullname[len(alias_prefix) :]
            canonical_name = f"{canonical_prefix}{suffix}"
            canonical_spec = _importlib_util.find_spec(canonical_name)
            if canonical_spec is None:
                return None
            return _importlib_util.spec_from_loader(
                fullname,
                _CompatibilityAliasLoader(fullname, canonical_name),
                origin=canonical_spec.origin,
                is_package=canonical_spec.submodule_search_locations is not None,
            )
        return None


def _install_compatibility_alias_finder() -> None:
    marker = tuple(_ALIAS_PREFIXES)
    if any(
        getattr(finder, "_htt_compat_alias_prefixes", None) == marker
        for finder in sys.meta_path
    ):
        return
    sys.meta_path.insert(0, _CompatibilityAliasFinder())


for _alias in _TOP_LEVEL_ALIASES:
    _alias_top_level_package(_alias)

_install_compatibility_alias_finder()


def __getattr__(name: str):
    """Lazy compatibility export for nested HTT subpackages."""
    if name in __all__:
        module = _importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
