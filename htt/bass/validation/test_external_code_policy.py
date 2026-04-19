"""External-code import policy guard (LB-0).

Enforces invariant #3 from `docs/lowell_bianchi/README.md §5` and the
hard rule of `docs/lowell_bianchi/00_conventions.md §11`:

    External cosmology codes (CAMB, CLASS, AniCLASS, HyRec, RECFAST, …)
    may appear in oracle scripts and test files only. They must NOT
    appear anywhere in production code under `bass_py/bass/` or
    `bass_py/tsc/`.

This test scans every `.py` file under the production trees and fails
if any forbidden import is found. Test files (``test_*.py``) and
pre-computed recombination fixtures (``bass/recombination/fixtures/``)
are exempt. Oracle scripts live under ``scripts/`` and are outside the
scanned trees.

Parametrised negative tests inject synthetic files with each forbidden
import into a temporary directory and verify that the scanner catches
them — proving the guard is actually functioning.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

import pytest


# Forbidden top-level module names. Matches any import form:
#   import camb
#   import camb as c
#   from camb import ...
#   from camb.submod import ...
FORBIDDEN_MODULES: Tuple[str, ...] = (
    "camb",
    "classy",
    "aniclass",
    "hyrec",
    "hyrec2",
    "recfast",
    "class_sz",
    "camb_ini_ext",
)

# Regex that matches both `import X[.sub]` and `from X[.sub] import …`
# anywhere in a logical code statement. A statement can be:
#   • at line start  (`import camb`)
#   • indented       (`    import camb`)
#   • semicolon-chained (`import os; import camb`)
#   • in a ``lambda:`` or one-liner (`def f(): import camb`)
# We therefore split the code portion of each line on ``;`` and match each
# segment. Post-audit LB-1 F5 repair — prior regex anchored at ``^`` only,
# missing ``import X; import Y`` bypasses.
_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(?P<mod>[A-Za-z_][\w\.]*)",
)

# Production trees to scan.
_PRODUCTION_ROOTS_REL: Tuple[str, ...] = ("bass", "tsc")


def _repo_bass_py_root() -> Path:
    """Absolute path to the `bass_py/` directory containing production code."""
    # This file lives at bass_py/bass/validation/test_external_code_policy.py
    return Path(__file__).resolve().parent.parent.parent


def _is_exempt(path: Path) -> bool:
    """Return True if `path` is exempt from the policy.

    Exemptions (per `00_conventions.md §11`):
      - Test files (``test_*.py``).
      - Files under ``bass/recombination/fixtures/`` (pre-computed
        HyRec data tables, read-only).
    """
    if path.name.startswith("test_"):
        return True
    parts = path.parts
    # Normalise: look for the exact fixtures directory inside recombination.
    for i in range(len(parts) - 1):
        if parts[i] == "recombination" and parts[i + 1] == "fixtures":
            return True
    return False


def _iter_production_files(root: Path) -> Iterable[Path]:
    for sub in _PRODUCTION_ROOTS_REL:
        tree = root / sub
        if not tree.is_dir():
            continue
        for path in tree.rglob("*.py"):
            if _is_exempt(path):
                continue
            yield path


def _scan_forbidden_imports(path: Path) -> List[Tuple[int, str, str]]:
    """Return a list of (line_number, forbidden_module, raw_line).

    An empty list means the file is clean. Handles ``import X; import Y``
    semicolon chains (LB-1 F5 post-audit repair) by splitting the code
    portion of each line on ``;`` before matching.
    """
    violations: List[Tuple[int, str, str]] = []
    text = path.read_text(encoding="utf-8", errors="strict")
    for lineno, raw in enumerate(text.splitlines(), start=1):
        # Strip trailing comments before matching so `# import camb` in
        # a trailing comment does not trigger. We only care about the
        # code portion.
        code = raw.split("#", 1)[0]
        # Split on ``;`` so each chained statement is scanned independently
        # (``import os; import camb`` must flag the ``camb`` segment).
        for segment in code.split(";"):
            match = _IMPORT_RE.match(segment)
            if not match:
                continue
            top = match.group("mod").split(".", 1)[0]
            if top in FORBIDDEN_MODULES:
                violations.append((lineno, top, raw.rstrip()))
    return violations


# ════════════════════════════════════════════════════════════════════
# Positive test: production tree is clean.
# ════════════════════════════════════════════════════════════════════


def test_no_external_code_imports_in_production() -> None:
    """No production file under bass/ or tsc/ imports an external cosmology code.

    If this fails, move the offending import into a ``scripts/`` oracle
    generator or a ``test_*.py`` file, and construct a static reference
    fixture if needed. See ``docs/lowell_bianchi/00_conventions.md §11``.
    """
    root = _repo_bass_py_root()
    offenders: List[Tuple[Path, List[Tuple[int, str, str]]]] = []
    for path in _iter_production_files(root):
        violations = _scan_forbidden_imports(path)
        if violations:
            offenders.append((path, violations))

    if offenders:
        msg_lines = [
            "External-code imports found in production tree "
            "(violates 00_conventions.md §11):",
        ]
        for path, violations in offenders:
            rel = path.relative_to(root)
            for lineno, mod, raw in violations:
                msg_lines.append(f"  {rel}:{lineno}: {mod!r} — {raw}")
        pytest.fail("\n".join(msg_lines))


# ════════════════════════════════════════════════════════════════════
# Negative (self-) tests: confirm the scanner actually detects things.
# ════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "snippet",
    [
        "import camb\n",
        "import camb as c\n",
        "from camb import model\n",
        "from camb.symbolic import foo\n",
        "import classy\n",
        "from classy import Class\n",
        "import aniclass as ac\n",
        "import hyrec\n",
        "from hyrec import solve\n",
        "import hyrec2\n",
        "import recfast\n",
        "import class_sz\n",
        "import camb_ini_ext\n",
        # Indented import (e.g. inside a function body) must still trip.
        "def f():\n    import camb\n",
        # Semicolon-chained imports (LB-1 F5 post-audit regression).
        "import os; import camb\n",
        "import numpy as np; from camb.symbolic import bar\n",
        "    import logging; import classy  # indented chain\n",
    ],
)
def test_scanner_detects_forbidden_import(
    tmp_path: Path, snippet: str,
) -> None:
    """Injecting a forbidden import must be caught by the scanner."""
    offender = tmp_path / "bogus_module.py"
    offender.write_text(snippet, encoding="utf-8")
    violations = _scan_forbidden_imports(offender)
    assert len(violations) >= 1, (
        f"Scanner failed to flag forbidden import in snippet: {snippet!r}"
    )


@pytest.mark.parametrize(
    "snippet",
    [
        "import numpy as np\n",
        "from scipy.integrate import solve_ivp\n",
        "# import camb  — forbidden; in a comment only\n",
        "s = 'import camb'  # string literal, not an import\n",
        "from bass.background import einstein_bianchi\n",
        "import bass.recombination.recombination_ingest as ri\n",
    ],
)
def test_scanner_allows_innocent_lines(
    tmp_path: Path, snippet: str,
) -> None:
    """Non-forbidden imports and comments must not trigger false positives."""
    path = tmp_path / "innocent.py"
    path.write_text(snippet, encoding="utf-8")
    assert _scan_forbidden_imports(path) == []


def test_exempt_paths_are_skipped(tmp_path: Path) -> None:
    """Test files and recombination fixtures are exempt from the scan."""
    # Test file by name.
    p1 = tmp_path / "test_something.py"
    p1.write_text("import camb\n", encoding="utf-8")
    assert _is_exempt(p1)

    # Recombination fixtures directory.
    fxdir = tmp_path / "recombination" / "fixtures"
    fxdir.mkdir(parents=True)
    p2 = fxdir / "data_loader.py"
    p2.write_text("import hyrec\n", encoding="utf-8")
    assert _is_exempt(p2)

    # A non-exempt file in a plain production-style path.
    p3 = tmp_path / "some_module.py"
    p3.write_text("import camb\n", encoding="utf-8")
    assert not _is_exempt(p3)
