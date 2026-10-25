# Build report

PDF build succeeded: 17 pages in REVTeX 4.2, within the requested 15–25 pages. This is a build and packaging result; scientific admission and publication remain separate decisions.

## Entrypoint and inputs

`main.tex`, seven `sections/*.tex`, `references.bib`, and four figure PDFs. All referenced figures exist. Full SHA-256 identities are in `BUILD_REPORT.json` and `FIGURE_PROVENANCE.json`.

## Command and logs

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=/mnt/extdrive/workdir/htt_open_data/r26_p1_paper_build/latex_20261024T025228Z main.tex
```

Exit status: 0. Raw final logs: `/mnt/extdrive/workdir/htt_open_data/r26_p1_paper_build/latex_20261024T025228Z`. First build and initial preparation failures remain retained externally.

## Warnings and checks

No undefined citations, undefined references, missing files, duplicate labels, overfull boxes, or pending cross-reference rerun. Three BibTeX warnings concern missing journal-number fields in Heinesen2021, Maartens2024, and Kalbouneh2026; the author retained those bibliographic records. REVTeX reports default 10pt, a nameref label-definition warning, and four float-placement warnings. All four figures and their captions are visible on pages 7, 9, 11, and 14. Repaired abstract/domain/support/caption/discussion pages 1, 10, 12, 14, and 15 were inspected without clipping or missing content.

## Figures and claim scope

The selected-cohort tensor plot and selection-bound plot use label-only saved-value rendering with unchanged numerical artists and axes geometry. The model-comparison asset is a byte-identical report copy. The coupled-functionals asset is a vector SVG-to-PDF conversion. No fit, draw, null, solver, or science-consumer execution occurred. Captions and scientific scope are author-owned; no native family-identification, physical shear, physical posterior, or calibrated physical coverage is admitted by this build.

## Source bundle

`source_bundle.zip` contains the TeX, bibliography, all four referenced figure PDFs, Korean rebuild instructions, scientific scope, claim/source map, and figure provenance/specification. It excludes raw catalogues and internal execution receipts. ZIP CRC and bundled-input SHA-256 comparisons passed. A fresh independent scientific/source/PDF review is still required before publication.
