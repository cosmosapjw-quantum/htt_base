# Building the research report

This source archive contains the English REVTeX manuscript, bibliography and every displayed figure. Install REVTeX 4.2, pdfLaTeX, BibTeX and latexmk; from this directory run:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=/absolute/path/to/build main.tex
```

The packaged figures reproduce the document without catalogue access or new scientific computation. FIGURE_PROVENANCE.json records original source identities and display-only transformations. Original numerical analyses, raw catalogues, unselected historical variants and internal execution receipts are outside this document-build archive. Scientific assumptions and limitations are stated in the paper and captions.
