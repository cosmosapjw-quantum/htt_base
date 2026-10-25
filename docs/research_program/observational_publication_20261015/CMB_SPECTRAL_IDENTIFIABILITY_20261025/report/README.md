# Spectral identifiability supplement

`main.pdf` is a seven-page REVTeX supplement prepared from an independently accepted finite spectral-table result. It is publication preparation, not submission or further scientific admission. No new numerical fit, map read, SVD, or response integration occurred during report assembly.

## Build

Required: a TeX Live installation with REVTeX 4.2, latexmk, BibTeX, amsmath, booktabs, graphicx, and hyperref. The included figures and generated table suffice:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Optional regeneration of figures and table requires Python 3 and matplotlib:

```sh
python code/assemble.py
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The script only reads stored `data/RESULT.json` fields. It does not redo the scientific computation. `generated/branch_summary.csv` retains all branches, both numerical ranks and condition numbers, both principal-angle sines, the quotient norm, the spectral witness residual, and maximum full24 witness residual. `generated/plot_data.json` gives exact plotted values; `generated/FIGURE_MANIFEST.json` records scope and provenance. Complete matrices, signed coordinates, controls and witnesses remain in the full RESULT and independent check. The 120 F1 nuisance basis columns are retained, alongside the 24 CMB basis controls.

The source archive is independently buildable without external files. It contains the accepted result, independent review and check, framing contract, theory note, source figures, renderer, and table. Original RIMO FITS inputs are identified by URL and SHA in the contract and RESULT; they are not needed to build this report. The archive does not claim to be a self-contained rerun of the original scientific integrations.

## Evidence and qualification

Accepted candidate SHA256: b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f.
Contract SHA256: fb137b19b2ec901604691f5d4aa62f05a29e5cbe86404c3c748bf8c8c40386df.
Final independent decision SHA256: ac948932ba9827ae9368ed05e8cbc1417d1fe8999cce10c0b51d9c4ec497537f.
The independent review decision qualifies only the new finite-table task; the candidate's older embedded pending-review field is historical. Requested and observed executor settings are distinct in the retained original evidence; unknown runtime remains unknown.

Owner: obsstat. Claim tier: C0 conditional model diagnostic. Transfer source: none. No sky used; no noise/null law. Physical x and observed quotient tensor are NOT_MEASURED; Q NOT_EVALUATED; F_physical NOT_EVALUABLE; Pi NOT_CALIBRATED; G_F NOT_APPLICABLE because frequency is not depth. The common response assumption, unconstrained signed moment family, and absent remainder bounds remain explicit.

Original L03 HOLD, original 22/42 baseline and 23/42 restricted alternative, historical 17/42 and 18/42, and R9 UNKNOWN remain unchanged. Accounting uses the final retained account head and corrected enclosing science bound 61.1 <= 270 seconds. Historical enforcement/source-scope limitations remain in original evidence. The prior mixed-clock number is not used.

No Git, live state, source candidate, source evidence, or repository file was changed. The source theory note is actually adjacent to the contract as `THEORY_AND_REOPENING.md`, not in a SOURCE subdirectory.

## Build notes

Initial LaTeX failures and build logs are retained locally under `evidence/` and omitted from the source ZIP. A table-closing booktabs noalign error was corrected in report formatting; a subsequent latexmk invocation initially reused the failed cache, so the candidate was explicitly rebuilt. The final PDF has seven pages and resolves all citations and references. No overfull/underfull boxes or missing figures occur. The remaining nameref warning about REVTeX's label definition is non-blocking. Matplotlib reports unavailable Axes3D because multiple installations are present; the report uses two-dimensional plots, which rendered successfully.

The PDF table and coefficient figure were visually inspected. The source ZIP includes `evidence/BUILD_AUDIT.json`; the detailed build logs that record the final checks are retained locally under `evidence/` and omitted from the ZIP. References are qualified from the supplied source/theory contract; no new literature/source acquisition occurred.
