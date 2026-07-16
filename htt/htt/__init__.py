"""HTT — Hubble Tilt Tracker.

Outer wrapper that re-exports htt.htt.* as htt.* via sys.modules aliasing.
Only commonly-imported subpackages are aliased eagerly; others are aliased
on first access to avoid triggering file I/O at import time.
"""
import sys as _sys
import importlib as _il
from importlib import abc as _il_abc
from importlib import util as _il_util
from pathlib import Path as _Path

__version__ = "8.3.0"

_INNER = _Path(__file__).resolve().parent / "htt"
if _INNER.is_dir():
    _inner_path = str(_INNER)
    if _inner_path not in __path__:
        __path__.append(_inner_path)

# Nested HTT packages stay lazy so ``import htt`` cannot trigger generators,
# mutate process state, or pull optional science dependencies into collection.
_EAGER = []
_LAZY = [
    'core', 'nulls', 'infer', 'departure', 'bridge', 'figures', 'integration',
    'zoa', 'direction', 'statistics', 'rest_frame', 'tilt', 'catalogs',
]
_TOP_LEVEL_ALIASES = ['bass', 'obsstat', 'mio', 'tsc_legacy', 'tsc', 'teff', 'workspace']
_ALIAS_PREFIXES = {f'htt.{name}': name for name in _TOP_LEVEL_ALIASES}
__all__ = [*_EAGER, *_LAZY, *_TOP_LEVEL_ALIASES]

for _s in _EAGER:
    _outer = f'htt.{_s}'
    if _outer not in _sys.modules:
        try:
            _mod = _il.import_module(_outer)
            _sys.modules[_outer] = _mod
            _sys.modules.setdefault(f'htt.htt.{_s}', _mod)
            globals()[_s] = _mod
        except ImportError:
            pass

def _alias_top_level_package(name):
    """Expose a bass-py-owned top-level package through ``htt.<name>``.

    The compatibility distribution owns no Python package.  These aliases live
    in the ``bass-py`` wheel and preserve object identity for modules imported
    while the canonical package is initialising.
    """
    module = _il.import_module(name)
    _sys.modules[f'htt.{name}'] = module
    globals()[name] = module
    prefix = f'{name}.'
    for loaded_name, loaded_module in tuple(_sys.modules.items()):
        if loaded_name.startswith(prefix):
            _sys.modules.setdefault(f'htt.{loaded_name}', loaded_module)


class _CompatibilityAliasLoader(_il_abc.Loader):
    """Load one deep compatibility name as its canonical module object."""

    def __init__(self, alias_name, canonical_name):
        self.alias_name = alias_name
        self.canonical_name = canonical_name
        self._canonical_metadata = None

    def create_module(self, spec):  # noqa: ANN001 - importlib protocol
        module = _il.import_module(self.canonical_name)
        self._canonical_metadata = (
            module.__name__,
            module.__package__,
            module.__spec__,
            module.__loader__,
        )
        return module

    def exec_module(self, module):  # noqa: ANN001 - importlib protocol
        canonical = _sys.modules.get(self.canonical_name)
        if canonical is not module:
            raise ImportError(
                f'compatibility alias {self.alias_name!r} lost canonical identity'
            )
        if self._canonical_metadata is None:
            raise ImportError(
                f'compatibility alias {self.alias_name!r} lacks canonical metadata'
            )
        (
            module.__name__,
            module.__package__,
            module.__spec__,
            module.__loader__,
        ) = self._canonical_metadata
        _sys.modules[self.alias_name] = canonical


class _CompatibilityAliasFinder(_il_abc.MetaPathFinder):
    """Resolve only declared deep ``htt`` compatibility prefixes lazily."""

    _htt_compat_alias_prefixes = tuple(_ALIAS_PREFIXES)

    def find_spec(self, fullname, path=None, target=None):  # noqa: ANN001
        for alias_prefix, canonical_prefix in _ALIAS_PREFIXES.items():
            nested_prefix = f'{alias_prefix}.'
            if not fullname.startswith(nested_prefix):
                continue
            suffix = fullname[len(alias_prefix):]
            canonical_name = f'{canonical_prefix}{suffix}'
            canonical_spec = _il_util.find_spec(canonical_name)
            if canonical_spec is None:
                return None
            return _il_util.spec_from_loader(
                fullname,
                _CompatibilityAliasLoader(fullname, canonical_name),
                origin=canonical_spec.origin,
                is_package=canonical_spec.submodule_search_locations is not None,
            )
        return None


def _install_compatibility_alias_finder():
    marker = tuple(_ALIAS_PREFIXES)
    if any(
        getattr(finder, '_htt_compat_alias_prefixes', None) == marker
        for finder in _sys.meta_path
    ):
        return
    _sys.meta_path.insert(0, _CompatibilityAliasFinder())


for _s in _TOP_LEVEL_ALIASES:
    _alias_top_level_package(_s)

_install_compatibility_alias_finder()

def __getattr__(name):
    """Lazy alias for optional subpackages."""
    if name in _LAZY:
        _outer = f'htt.{name}'
        try:
            _mod = _il.import_module(_outer)
            _sys.modules[_outer] = _mod
            _sys.modules.setdefault(f'htt.htt.{name}', _mod)
            globals()[name] = _mod
            return _mod
        except ImportError:
            pass
    raise AttributeError(f"module 'htt' has no attribute {name!r}")
