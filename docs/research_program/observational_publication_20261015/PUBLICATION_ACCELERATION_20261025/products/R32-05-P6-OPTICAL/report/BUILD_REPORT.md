# Build status

Candidate built successfully: 12-page English RevTeX PDF, title and abstract together, 35 tagged equations, 2 generated tables, 2 vector figures, 4 bibliography entries. All pages were rendered and inspected in a contact sheet; the title/abstract and figure pages were inspected at readable size. No clipping or blank pages was observed.

# Entrypoint and included files

`main.tex`, `references.tex`, `generated/tensor.tex`, `generated/frontier.tex`, and the two vector PDFs in `figures/`. Scientific author files in `../science/` are unchanged. Equation (26) has a layout-only line break; every equation matches the scientific source after ignoring spacing and the added gathered environment.

# Commands run

Exact commands, cwd and exits are in `raw/commands.json`. Retained consumer executed once, exit 0; initial and final source/LaTeX builds exit 0. PDF extraction/render and focused candidate audit exit 0. No broad scientific rerun or repository test suite was needed for this prescribed retained-input build.

# Errors and warnings

The first actual command failure was read-only inventory of the not-yet-created assigned report directory (exit 2), retained in `raw/intake_first_failure.txt`. No consumer/build failure occurred. A later packager invocation failed because three package files were written at the repository cwd; the misplaced files were moved into this report and the originally clean tracked root README restored exactly from HEAD. Original/accidental/restored hashes and an empty restoration diff are retained in raw/misplaced_file_recovery.json and raw/root_README_restoration.diff. No preexisting root BUILD_REPORT.md or finalize.py was present in the initial status. Initial successful TeX build had one overfull box in equation (26); line wrapping fixed it. Final log: zero overfull boxes, zero undefined citations/references; one `nameref` warning about RevTeX changing the definition of `label`.

# Missing figures and missing figure sources

None. `reproduce.py` generates both figures and their exact numerical data. `pdfimages -list` reports no embedded raster objects in either figure. Source identities are verified against the frozen evidence manifest for each consumed retained entry.

# Citation/reference status

All four bibliography entries are copied from the author's already verified references; no new acquisition or bibliographic audit was undertaken. The companion is described as a repository manuscript, and the CF4 sufficient statistics as retained numerical research products.

# Claim audit

| Claim group | Owner | Status | Evidence | Required limit |
|---|---|---|---|---|
| Optical inverse, finite response and support | common | DERIVED/CONDITIONAL | Author proofs; focused algebra fixtures | Full-field and finite-model domains remain distinct |
| Retained CF4 tensor | mio | DIAGNOSTIC_ONLY | Frozen retained statistics and unit correction | Apparent dimensionless statistic; no second kappa/H division |
| Tensor error image and shear frontier | mio | DERIVED/CONDITIONAL | Assumed deterministic error sets and generated formula checks | No calibrated radius, empirical covariance, coverage or physical detection |
| x/F/Pi/Q/G_F | mio | SPECIFIED/CONDITIONAL | Author definitions and explicit generated statuses | Missing physical sectors, measures, law and policy inputs remain unknown/undefined |

No scientific claims were upgraded. Full nine-row claim-to-source bindings are in `generated/claim_to_source.json`. The signed comparator W² vorticity contribution is explicitly distinguished from the whitening matrix W. Forbidden production language scan passed. The source-unit/basis mismatch, nonpositive shape matrix or any failed scientific formula check is a stopping condition; none occurred.

# Required manuscript fixes and remaining limits

No remaining build fix identified. Independent scientific review is pending. The complete candidate and exact manifest are delivered for the author/controller to consume; this build does not change original42 acceptance, counters or campaign state. No new permanent claim registry or acceptance threshold was added.
