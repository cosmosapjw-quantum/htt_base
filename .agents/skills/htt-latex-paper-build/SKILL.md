---
name: htt-latex-paper-build
summary: Build and audit LaTeX manuscripts, figures, BibTeX, appendices, and arXiv/source-package readiness for the HTT/Bianchi project.
description: Use when editing or auditing TeX files, references, figures, manuscript snapshots, appendix material, figure provenance, or external-audit manuscript bundles.
---

# HTT LaTeX / Paper Build Skill

## Purpose

Keep the manuscript source tree buildable, citation-complete, figure-provenance-complete, and claim-tier consistent.

## Required workflow

1. Locate the main TeX entrypoint: usually `main.tex`, `main(2).tex`, or repo-specific manuscript root.
2. Identify included chapter files and bibliography file.
3. Scan `\includegraphics` paths and check whether each figure exists.
4. Build with `latexmk` if available; otherwise use documented fallback.
5. Scan logs for undefined citations, undefined references, missing files, duplicate labels, and overfull boxes.
6. Check figure sources: every publication figure should have a script/artifact/manifest or be marked external.
7. Check claim language in captions: no scalar-only geometry/family claim.
8. Update build/figure inventory artifacts.

## HTT-specific manuscript caveats

- Do not let scalar `D_l`, `x,Q,Pi,F,G`, or direction coherence alone imply Bianchi family identification.
- If current result uses AniCLASS/external transfer, captions must say so.
- MIO diagnostics are not HTT posterior/evidence.
- Teff/TSC legacy text must not describe full spin-2/BB/family identification.

## Required output

```markdown
## Build status

## Entrypoint and included files

## Commands run

## Errors and warnings

## Missing figures and missing figure sources

## Citation/reference status

## Claim-language risks

## Required manuscript fixes
```

## Hard prohibitions

- Do not claim the PDF compiled unless build command succeeded.
- Do not hide missing citations or missing figures.
- Do not include hand-edited/generated figures without provenance.
- Do not use manual test/module/status counts in manuscript-facing text if generated snapshots exist.
