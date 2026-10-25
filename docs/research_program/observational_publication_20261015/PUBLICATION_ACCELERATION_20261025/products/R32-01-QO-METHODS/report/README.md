# Sharp quadrupole–octupole chirality: manuscript source and reproduction

From this directory run:

```bash
python3 reproduce.py --build
```

Requirements: Python 3, NumPy, Matplotlib; latexmk, pdflatex, BibTeX, RevTeX 4.2 and standard AMS/graphics/hyperref packages. The repository's retained evidence and sibling science directory must remain at their recorded relative paths. The consumer verifies the frozen science hashes and relevant EVIDENCE_MANIFEST input hashes before reading the two retained JSON payloads. It never invokes historical producer scripts or repeats spherical integration.

The command constructs the explicit unit STF tensors from the manuscript lift, checks the fixed 1e-12 invariants and mirror parity, validates all 45 saved optical rows and their analytic bound, and creates three figures, the five-row table, the full RevTeX manuscript and PDF. It preserves all 41 numbered mathematical displays from the scientific source. `generated/optical_rows.csv` contains all saved rows; `generated/summary.json` identifies the exact five table rows and the retained quadrature comparison. Full ordered-index tensors are retained in the summary.

`main.tex`, `references.bib`, `generated/optical_table.tex` and the three `figures/*.pdf` are the complete LaTeX source package. `RESULT.json` records source and candidate hashes, package versions, checks and build commands. `raw/latexmk.stdout`, `main.log`, and `raw/commands.json` preserve build evidence. `raw/consumer.stdout` and `raw/consumer_command.json` preserve the outer consumer invocation.

The English scientific content follows the frozen MANUSCRIPT.md; the personal writing protocol is applied only to formatting and publication English. All substantive equations, assumptions, proof content and limitations are retained. Anonymous review authorship carries no inferred credentials or affiliation. Primary bibliography metadata is supplied in the scientific source; the full author lists of the Desmorat and Pisanty preprints were checked against their arXiv abstract pages on 2026-10-25 (https://arxiv.org/abs/2105.14930 and https://arxiv.org/abs/2603.26793v1). No journal publication is inferred for the latter.

Scope: C0 deterministic/conditional mathematics and synthetic local optical response; transfer source none. This build is a review candidate and makes no scientific-admission or original42-acceptance decision. The two-grid comparison is numerical consistency evidence, not a rigorous quadrature error bound. No empirical sampling law is supplied. The common angular frame, magnitude units and positivity/remainder restrictions are stated in the manuscript and figure captions.
