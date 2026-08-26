"""Observed MES execution must traverse only the active typed authority."""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
FORBIDDEN_MODULES = {
    "bass.observational.planck_mes_bounds",
    "htt.bass.observational.planck_mes_bounds",
}


def test_observed_mes_sources_have_no_lazy_legacy_import() -> None:
    """Catch a forbidden import hidden behind a runtime-only branch."""

    for relative in (
        "htt/obsstat/mes_row_anchor.py",
        "scripts/observed_runs/run_planck_mes_morphology.py",
    ):
        tree = ast.parse((REPO / relative).read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert imported.isdisjoint(FORBIDDEN_MODULES), (relative, imported)


def test_observed_runner_import_graph_excludes_legacy_mes_module() -> None:
    """Catch direct or import-time activation of the quarantined Planck code."""

    program = r"""
import json
import sys
import scripts.observed_runs.run_planck_mes_morphology as runner
import obsstat.mes_row_anchor as row_anchor

forbidden = sorted(
    name for name in sys.modules
    if name in """ + repr(FORBIDDEN_MODULES) + r"""
)
print(json.dumps({
    "forbidden_loaded": forbidden,
    "runner_module": runner.__name__,
    "row_operator_module": row_anchor.__name__,
}))
raise SystemExit(1 if forbidden else 0)
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        str(REPO / path) for path in ("htt", "htt/src", "htt/htt")
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", program],
        cwd=REPO,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload == {
        "forbidden_loaded": [],
        "runner_module": "scripts.observed_runs.run_planck_mes_morphology",
        "row_operator_module": "obsstat.mes_row_anchor",
    }
