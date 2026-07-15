from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_TEX = REPO_ROOT / "docs/manuscript/main.tex"


def test_manuscript_quarantine_gate_precedes_document_class():
    source = MAIN_TEX.read_text(encoding="utf-8")

    assert source.index(
        r"\ifcsname HTTCF4PZeroLegacyReproduction\endcsname"
    ) < source.index(
        "\n" + r"\documentclass"
    )
    assert "NO CURRENT MANUSCRIPT PDF IS AUTHORIZED" in source
    assert "PUBLIC_USE=FALSE" in source
    assert (
        r"\expandafter\def\csname HTTCF4PZeroLegacyReproduction\endcsname{1}"
        in source
    )


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex unavailable")
def test_normal_nonstopmode_build_fails_before_emitting_pdf_or_dvi(tmp_path: Path):
    completed = subprocess.run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={tmp_path}",
            MAIN_TEX.as_posix(),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "NO CURRENT MANUSCRIPT PDF IS AUTHORIZED" in completed.stdout
    assert not list(tmp_path.glob("*.pdf"))
    assert not list(tmp_path.glob("*.dvi"))
