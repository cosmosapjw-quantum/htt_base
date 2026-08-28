#!/usr/bin/env python3
"""Claim linter for the research-content SURFACES (final report + results table +
blocker dossier).

Folds the forbidden-phrase set from the two 2026-06-29 external audit packs
(`htt_research_evaluation_review` MINOR, `pr08_reassessment_audit_pack` MAJOR)
into a permanent repo gate so the specific over-promotions they flagged cannot
re-enter the report/table/blockers:

  * headline/anomaly over-claims  ("recovers the established low-ell CMB
    anomalies", "honest publishable envelope", "measured rank-2 comparator", ...)
  * stale / over-strong theorem names ("Quadrupole-filling EGS identity",
    "G_F=1 iff", "floor nothing beats", "forbids a vanishing shear-filling",
    "strictly positive lower bound excludes zero")
  * synthetic-floor over-claims ("genuine multi-multipole Fisher--CR floor",
    "genuine floor")
  * data-discharge over-claims ("release-matched forward mocks",
    "BLOCKED_MISSING_FIELD_REALIZATIONS ... discharged", "CR ensemble is the
    posterior")

The retired manuscript, result table, and compiled-PDF gates are no longer
active surfaces.  This linter now protects the surviving blocker register.
Diagnostic-only; no detection / family / native-solver claim is permitted.

Exit code 0 = clean, 1 = hits (printed as JSON).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

SURFACES = (
    "docs/research_program/BLOCKERS.md",
)

PATTERNS = {
    "anomaly_or_headline_overclaim":
        r"recovers the established low-ell CMB anomalies|honest publishable envelope"
        r"|strong, honest joint result|strong, honest, publishable"
        r"|measured rank-2 comparator|measured rank-2 graded comparator",
    "stale_or_overstrong_theorem_name":
        r"Quadrupole-filling EGS identity|G_F=1 iff|floor nothing beats"
        r"|forbids a vanishing shear-filling|strictly positive lower bound excludes zero",
    "synthetic_floor_overclaim":
        r"genuine multi-multipole Fisher.{0,4}CR floor|genuine floor|genuine Fisher floor",
    "data_discharge_overclaim":
        r"release-matched forward mocks|BLOCKED_MISSING_FIELD_REALIZATIONS[^.]*discharged"
        r"|CR ensemble is the posterior",
}

# LaTeX/markdown noise that lets a banned phrase evade a raw line-by-line match by
# splitting across `$...$`, `\emph{}`, `\texttt{}`, or a hard line wrap. We strip it
# and collapse whitespace before matching so wrap/markup-split evasions are caught
# (external-audit finding: `$G_F=1$ iff`, `strictly\npositive lower bound...`).
_STRIP = re.compile(r"\$|\\emph\{|\\texttt\{|\\textbf\{|\\emph|\\textbf|[{}]|\\,|\\!|---|--|\*\*|`")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", _STRIP.sub(" ", text))


def scan(root: Path = REPO_ROOT) -> list[dict]:
    hits: list[dict] = []
    for rel in SURFACES:
        f = root / rel
        if not f.is_file():
            continue
        raw = f.read_text(errors="ignore")
        norm = _normalize(raw)
        for key, pat in PATTERNS.items():
            if re.search(pat, norm):
                # report the (approx) first offending raw line for the operator
                line_no, snippet = _first_line(raw, pat)
                hits.append({"file": rel, "line": line_no, "pattern": key, "text": snippet})
    return hits


def _first_line(raw: str, pat: str) -> tuple[int, str]:
    """Best-effort raw-line locator (handles single-line hits; falls back to a
    normalized-window pointer for wrap/markup-split hits)."""
    for i, line in enumerate(raw.splitlines(), 1):
        if re.search(pat, _normalize(line)):
            return i, line.strip()[:160]
    # split across lines: point at the first line whose normalized 2-line window matches
    lines = raw.splitlines()
    for i in range(len(lines) - 1):
        window = _normalize(lines[i] + " " + lines[i + 1])
        if re.search(pat, window):
            return i + 1, (lines[i].strip() + " / " + lines[i + 1].strip())[:160]
    return 0, "(matched only after whole-file normalization)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    hits = scan(args.root)
    print(json.dumps({"hits": hits, "count": len(hits)}, indent=2, ensure_ascii=False))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
