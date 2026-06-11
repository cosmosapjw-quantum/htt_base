"""HTT — Hubble Tilt Tracker.

Outer wrapper that re-exports htt.htt.* as htt.* via sys.modules aliasing.
Only commonly-imported subpackages are aliased eagerly; others are aliased
on first access to avoid triggering file I/O at import time.
"""
import sys as _sys
import importlib as _il
from pathlib import Path as _Path

_INNER = _Path(__file__).resolve().parent / "htt"
if _INNER.is_dir():
    _inner_path = str(_INNER)
    if _inner_path not in __path__:
        __path__.append(_inner_path)

# Core subpackages: alias eagerly (no side effects at import)
_EAGER = ['core', 'infer', 'bridge', 'figures', 'tilt', 'nulls']
# Optional subpackages: alias lazily to avoid file I/O on import
_LAZY = ['catalogs', 'integration']

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
