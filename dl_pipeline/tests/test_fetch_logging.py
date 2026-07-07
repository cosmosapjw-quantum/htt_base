from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from fetch import _console_safe_text


def test_console_safe_text_preserves_utf8() -> None:
    text = "BASS data pipeline — root=workdir"

    assert _console_safe_text(text, encoding="utf-8") == text


def test_console_safe_text_replaces_unencodable_console_chars() -> None:
    text = "BASS data pipeline — root=workdir"

    safe = _console_safe_text(text, encoding="ascii")

    assert safe == "BASS data pipeline ? root=workdir"
