"""Compatibility entrypoint for the canonical architecture-boundary tests.

The repository's established architecture contract lives at
``scripts/architecture/test_import_boundaries.py``.  The active Planck MES
formalism work units refer to this stable ``tests/architecture`` path, so this
module deliberately re-exports the canonical pytest tests instead of copying
or weakening them.

PMG-WU-002 may add formalism-specific tests here, but the generic import-graph
scanner remains owned by ``scripts/architecture``.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys


_CANONICAL_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "architecture"
    / "test_import_boundaries.py"
)

if not _CANONICAL_PATH.is_file():
    raise RuntimeError(
        "canonical architecture test is missing: " f"{_CANONICAL_PATH}"
    )

# The canonical module intentionally imports its sibling helper as a top-level
# module.  Mirror direct pytest execution by placing that directory first.
_CANONICAL_DIR = str(_CANONICAL_PATH.parent)
if _CANONICAL_DIR not in sys.path:
    sys.path.insert(0, _CANONICAL_DIR)

_SPEC = importlib.util.spec_from_file_location(
    "_canonical_repository_import_boundaries",
    _CANONICAL_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load canonical architecture test: {_CANONICAL_PATH}")

_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

_EXPORTED = 0
for _name, _value in vars(_MODULE).items():
    if _name.startswith("test_") and callable(_value):
        globals()[_name] = _value
        _EXPORTED += 1

if _EXPORTED == 0:
    raise RuntimeError(
        "canonical architecture test exported no pytest tests: "
        f"{_CANONICAL_PATH}"
    )


def _imports(relative_path: str) -> set[str]:
    tree = ast.parse(
        (_CANONICAL_PATH.parents[2] / relative_path).read_text(encoding="utf-8")
    )
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_pmg_wu002_formalism_dependencies_remain_observer_side() -> None:
    premise_imports = _imports("htt/src/common/mes_premise_normalization.py")
    response_imports = _imports(
        "htt/src/common/response_bound_observable_state.py"
    )
    forbidden_roots = {"bass_py", "htt", "mio", "obsstat", "tsc_legacy"}
    for module in premise_imports | response_imports:
        assert module.split(".", 1)[0] not in forbidden_roots

    orbit_imports = _imports("htt/src/common/orbit_catalogue_v3.py")
    assert "common.observable_irrep_state" not in orbit_imports
