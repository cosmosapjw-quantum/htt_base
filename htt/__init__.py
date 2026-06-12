"""Repo-root compatibility shim for the nested HTT package.

The installable HTT package lives under ``htt/htt/`` while the active
``bass-py`` package root is ``htt/``. Importing from the repository root would
otherwise resolve this outer directory as a namespace package and shadow the
nested public ``htt`` package.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
_NESTED_HTT = _ROOT / "htt" / "htt"

for _path in (_ROOT, _SRC):
    if _path.is_dir():
        _path_str = str(_path)
        if _path_str not in sys.path:
            sys.path.insert(0, _path_str)

if _NESTED_HTT.is_dir():
    _nested_str = str(_NESTED_HTT)
    if _nested_str not in __path__:
        __path__.append(_nested_str)

__version__ = "0.1.0"
__all__ = [
    "core",
    "nulls",
    "infer",
    "bridge",
    "figures",
    "integration",
    "zoa",
    "direction",
]
