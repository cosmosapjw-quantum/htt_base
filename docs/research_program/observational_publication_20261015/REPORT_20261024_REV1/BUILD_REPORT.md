# Build status

SUCCESS: English REVTeX 4.2 report, 140 pages and 93 displayed figures. All 104 surveyed figure families have an inclusion or historical-exclusion decision; all 185 original format files remain preserved.

## Entrypoint and included files

`main.tex`, eight section files, `figures/atlas.tex`, and `references.bib`. The atlas is mechanically assembled from the scientific author's `FIGURE_CAPTIONS.json`.

## Commands run

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=/mnt/extdrive/workdir/htt_open_data/r26_revtex_build/final_v5 main.tex
pdfinfo main.pdf
pdftotext main.pdf main.txt
```

Auxiliary files and complete build logs are outside the checkout at `/mnt/extdrive/workdir/htt_open_data/r26_revtex_build/final_v5`. Earlier failed-build and rendering logs remain in the external build root.

## Errors and warnings

No final build errors, missing files, missing characters, overfull boxes, duplicate labels, undefined citations or undefined references. One nonfatal nameref warning concerns REVTeX's label definition. Four bibliography paragraphs have underfull spacing notices; their badness and source lines are in `BUILD_REPORT.json`. Initial failures (a squared unit macro and an unsupported SVG import) and the earlier probability-interval overflow were corrected and preserved in the raw logs.

## Missing figures and missing figure sources

None among the 93 displayed figures. Related candidate scripts are distinguished from confirmed label-rendering procedures. Unknown original generating-script identities remain unavailable. Figure-source and copy hashes, scope decisions and traceable result links are in `FIGURE_INVENTORY.json`. No new fitting, random sampling or catalogue analysis was performed.

## Citation/reference status

All final citations and references resolve. The final PDF text scan contains no internal task/status labels. Mathematical covariance notation is retained.

## Figure fidelity and claim-language risks

Label-only rendering preserves all recorded nontext artist arrays and geometry. Safe title/footer viewports are rendered at 300 dpi, with their scientific qualifications restored in author captions; the asymmetric two-panel view preserves the projection figure's full axes and data. The SVG conversion preserves all nontext geometry. These are document-display operations and do not establish physical calibration, native-solver validation or broader scientific acceptance. Parent-managed independent review remains a separate decision.

## Required manuscript fixes

No unresolved build fix. Scientific review and publication decisions are outside this build report.

## Deliverables

- `main.pdf`: 7,312,347 bytes; SHA-256 `ea438df677a373d9320830deb848910c665789dc5adfc7fd4dbc320776f38183`.
- `source_bundle.zip`: 6,649,949 bytes, 108 members; SHA-256 `99acb88217194488ff70ca834417852714303d612373706cf8e1c98b525e56fa`.

The source archive contains TeX, BibTeX, all displayed figures, an external-readable figure provenance map and rebuild instructions. It excludes raw catalogues, internal execution receipts, duplicate formats and historical candidates. Archive integrity was checked.
