# Rebuilding the rendered review document

The supplied HTT_REPORT_A_R3.tex is standalone: header and bibliography output are inlined, with no external figures. In a directory containing it, run:

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error HTT_REPORT_A_R3.tex
```

For Markdown regeneration, use the exact companion Markdown and bibliography, metadata.yaml, structure-r3.lua and header-r3.tex with the argv in pandoc-render-final.command.json, replacing only local input/output directory prefixes. Apply the exact package-order replacement in tex-package-order.patch before latexmk: mathtools must load with amsmath/amssymb before unicode-math. The supplied TeX already contains that adjustment.

The archived runner/check_source/prepare_render/fix_literal/verify_final Python scripts are the actual run-local procedures, not an installed public validator. Their paths and command records bind to the external run directory named by RENDER_RECEIPT.json. They are retained for inspection; adjust locations deliberately for a new independent render. No scientific replay is needed to compile this TeX. Font/tool differences can affect PDF bytes and pagination; validate a new output independently rather than attributing this review to it.

The original PNG raster set and intermediate build products remain in the external run directory; their identities are recorded. Only the two page-10 images are included here to show the actual layout correction. The final PDF is the complete 29-page deliverable.
