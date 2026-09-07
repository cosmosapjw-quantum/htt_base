# Native build and inspection record

The six-part manuscript was frozen at `f666b244f7061451a6941f5a57aa2d721bbfa81d` before execution. The only source correction is the form-feed transcription at Appendix C Eq. C.14, restored to `\frac1{45}` in `297f7f97af6646f243344812a7e2db6827d942f7`. The eight full authored linking replacements were applied by the unchanged assembly program. Bibliography bytes remain the fixed source blob `331c557c0f6a7de84fdd97123d8bdb8fae0e0a53`.

The published TeX is standalone. Build it in a separate output directory with the existing XeLaTeX/latexmk environment:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.tex
```

To regenerate TeX from the single assembled Markdown, run in this artifact directory with Pandoc 3.1.3:

```bash
pandoc FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.md --from=markdown+tex_math_single_backslash+raw_tex+citations+fenced_code_blocks+pipe_tables --to=latex --standalone --number-sections --top-level-division=section --toc --toc-depth=2 --lua-filter=layout/structure.lua --citeproc --bibliography=references.bib --metadata-file=layout/metadata.yaml --include-in-header=layout/header.tex --wrap=preserve --output=FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.tex
```

Before compiling regenerated TeX, replace its single `\usepackage{amsmath,amssymb}` line with `\usepackage{amsmath,amssymb,mathtools}`. This loads mathtools before unicode-math; it changes no body mathematics. The exact executed commands, absolute paths, exit codes and timings are preserved under evidence, especially `pandoc-stf.command.json`, `tex-stf.command.json`, `raster-stf.command.json` and `final-render-check-heading-fixed.command.json`. The recipe above expresses those final commands with portable relative artifact paths. It has not been claimed to reproduce identical PDF packaging bytes in a different environment.

The actual tools were Python 3.12.3, Pandoc 3.1.3, XeTeX 0.999995 / TeX Live 2023 Debian, latexmk 4.83 and Poppler. Their raw version outputs are included. No fonts or installed packages are distributed. PDF fonts are embedded in the ordinary rendered document; no font binaries are separate artifacts.

## Corrections and preserved failures

1. First real assembly exited 1 on a form-feed in Appendix C.14. Restoring the intended backslash-f is the only manuscript source edit; its exact diff and original error are included. The intended Gram prefactor follows independently from the preceding moment formula.
2. The first run-local source checker exited 1 because its result-ID regex included a trailing full stop. The corrected selector passed; no theorem was changed.
3. Initial native TeX compilation exited 12 because the initial header invoked hypersetup before hyperref existed. Move colour-link settings to metadata. The actual initial compiler log and header remain available.
4. The 49-page layout exposed incorrect Part contents page positions. Place clearpage before part commands. The 53-page layout then showed inherited unnumbered hyperlink anchors; dedicated clearpage/phantomsection anchors fix them. The resulting 55-page layout has matching contents pages and dedicated destinations.
5. Actual page 50 inspection found Markdown interpreting `<a e_b>` and `<a q_b>` as HTML and omitting them. The final Lua filter preserves these as literal strings. The assembled Markdown is unchanged. Exact 120 dpi PNG comparison shows only page 50 changed, and it was re-viewed.
6. Final PDF-correspondence checker development exposed two checker selection defects: comparing unescaped text with escaped TeX, then selecting equation tag B.3 instead of the B.3 subsection. Exact selectors were corrected; both failed raw outputs are retained. No certificate value or PDF was changed to satisfy the checker. An attempted reuse of the already occupied command name `pandoc-final` was rejected by the run logger before executing a tool; execution proceeded under the distinct `pandoc-stf` name.

The final compiler exits 0. There are no overfull/underfull boxes, missing glyphs or undefined references/citations. Two unicode-math warnings remain about unused bracket/colon macro definitions; neither macro family appears in the body. The final 931 source Math nodes occur unchanged and in order in the TeX AST; its two extra Math nodes are in the fixed bibliography. All 147 explicit tags and all 12 exact rational fractions also survive into the actual PDF. Source identities and conditions are separate from scientific truth or novelty.

## Evidence and reproduction boundaries

The original six sources, unchanged assembly program and exact Fraction checker are tracked at the corrected source commit. `ASSEMBLY_RECORD.json` records all six inputs and eight replacements. `inspection_scripts` contains the actual run-local inspection programs, including their original absolute-path orchestration (`runner.py`); their paths must be rebound to a new isolated run to replay them. `prepare_render.py` is the preserved initial setup script, not the final layout recipe; use the final published layout files and commands above. The original checker failures have distinct copies and logs.

`evidence/axial-first.json` contains actual Fraction computations; `axial-sensitivity.json` records the in-memory expected-numerator mutation reporting NONPASS. `radiation-model-check.json` and PROOF_REVIEW describe the explicit first-order model checks. `final-render-check.json` reconstructs the large integer fractions from the PDF after removing only identified page footers and whitespace. No old research suites, four-axis CAS validation or external scientific promotion were rerun.

Intermediate PDFs, bulky ASTs and page images are retained in the isolated run and identified under `retained-local-intermediates.json` / PAGE_REVIEW.json. The decisive final PDF/TeX/Markdown, compact checks and raw command/build logs are included here. Original dirty-checkout inventories, private corpus/style files, credentials and installed environments are excluded.
