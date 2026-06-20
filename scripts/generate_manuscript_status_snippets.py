#!/usr/bin/env python3
"""Regenerate the manuscript count snippets from generated source artifacts.

REV-R090 closes the strict-audit finding that manuscript count sentences were
hand-typed prose. The four count-bearing VER2 snippets

    docs/manuscript/generated/ver2_titlepage_status.tex
    docs/manuscript/generated/ver2_status_snapshot.tex
    docs/manuscript/generated/ver2_artifact_export_policy.tex
    docs/manuscript/generated/ver2_figure_manifest_status.tex

are derived here from the canonical generated sources

    docs/ver2_upgrade/generated/status_snapshot.json   (status counts)
    figures/paper/VER2_MANIFEST_INDEX.md               (figure-manifest counts)

and each emitted snippet carries a ``% generated from <source> (sha256:...)``
provenance comment so the figure/text auditor can distinguish a generated count
from a hand-typed manual status number.

This is the single render path: it reuses the exact renderers used by
``scripts/ver2_artifact_export.py`` (which also emits these four files during a
full export run), so a focused refresh here and a full export run produce
byte-identical snippets.

Usage:
    venv/bin/python scripts/generate_manuscript_status_snippets.py
    venv/bin/python scripts/generate_manuscript_status_snippets.py --check
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import ver2_artifact_export as ver2  # noqa: E402


def render_snippets() -> dict[Path, str]:
    """Render the four count snippets from the cached export bundle and figures."""

    records, packs = ver2.build_export_bundle()
    figures = ver2._scan_figures(ver2.FIGURE_ROOT)
    status_rows = ver2._status_rows(records)
    manifest_fields = ver2._field_names(ver2.ArtifactManifest)

    status_json_content = ver2._dump_json(ver2.STATUS_JSON, status_rows)
    manifest_index_content = ver2._render_manifest_index(figures, manifest_fields)
    status_provenance = ver2._provenance_comment(
        "docs/ver2_upgrade/generated/status_snapshot.json", status_json_content
    )
    figure_index_provenance = ver2._provenance_comment(
        "figures/paper/VER2_MANIFEST_INDEX.md", manifest_index_content
    )

    gen = ver2.MANUSCRIPT_GEN
    return {
        gen / "ver2_titlepage_status.tex": ver2._render_titlepage_status_tex(
            status_rows, status_provenance
        ),
        gen / "ver2_status_snapshot.tex": ver2._render_status_snapshot_tex(
            status_rows, status_provenance
        ),
        gen / "ver2_artifact_export_policy.tex": ver2._render_artifact_policy_tex(
            manifest_fields, figures, figure_index_provenance
        ),
        gen / "ver2_figure_manifest_status.tex": ver2._render_figure_manifest_status_tex(
            packs, figures, figure_index_provenance
        ),
    }


def _normalized(content: str) -> str:
    return content.rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if any generated count snippet is missing or stale",
    )
    args = parser.parse_args()

    snippets = render_snippets()

    if args.check:
        stale: list[str] = []
        for path, content in snippets.items():
            expected = _normalized(content)
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                stale.append(path.relative_to(ver2.REPO_ROOT).as_posix())
        if stale:
            print("Out-of-date manuscript count snippets:")
            for rel in sorted(stale):
                print(f"  - {rel}")
            return 1
        print("Manuscript count snippets are up to date.")
        return 0

    for path, content in snippets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_normalized(content), encoding="utf-8")
        print(f"wrote {path.relative_to(ver2.REPO_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
