# HTT methodology foundations — internal, 28 October 2026

Start with `output/FOUNDATION_REPORT.md` or the separately supplied 18-page PDF. The report reconnects the MES/radiation equalities, optical inverse and current PM response to physical confidence images. It includes the newly executed Gaia-INFO-01 saved-law experiment and finite compression-error checks. `output/NOVELTY_AND_RESEARCH_DECISION.md` contains the separate prior-art assessment.

The active branch was inspected at `7f3f49a6b6d95b6ae0323d5bebd3afce0067b1a7`. All new work in this bundle is internal. No push, live harness/DAG state change, catalogue refit, native solver or ODE integration occurred. Original observational acceptance is unchanged.

## Reproduce the small calculations

Use Python 3.12 with NumPy 2.3.5, SciPy 1.17.0 and Matplotlib 3.10.8, the versions used here. The source input is included; no data download or account is required. Run these commands from this directory:

```bash
OPENBLAS_NUM_THREADS=1 python code/gaia_info.py --draws 100000
OPENBLAS_NUM_THREADS=1 python code/foundation_checks.py
python assemble_report.py
```

The Gaia code checks the exact Git blob of its saved 24D input. It regenerates `lanes/GAIA_INFO.json` and its two figures. The foundation code regenerates `lanes/FOUNDATION_CHECKS.json` and the finite-remainder figure. Monte Carlo seed is 20261028; each stated coverage experiment uses 100,000 draws. No command above accesses the raw 755,850-row catalogue. `sources/gaia/*compute.py` is the inherited producer, included for source interpretation; it need not be executed.

To render the report with Pandoc and XeLaTeX:

```bash
cd output
pandoc FOUNDATION_REPORT.md --from=markdown+tex_math_single_backslash+tex_math_dollars --pdf-engine=xelatex -V mainfont='DejaVu Serif' -V sansfont='DejaVu Sans' -V monofont='DejaVu Sans Mono' --toc --toc-depth=2 -o HTT_METHOD_FOUNDATIONS_20261028.pdf
```

## Evidence and interpretation

- `lanes/MES_FOUNDATION.md`: normalization, harmonic/STF relation, radiation operator, directional inverse and optical interpretation.
- `lanes/GAIA_INFO.md` and `.json`: exact retained carrier, distinct slope estimands, matched joint GLS comparison, scalar sign loss and common-family repair.
- `lanes/PRIOR_ART.md` and `.json`: primary literature and the boundary between established theory and proposed application contributions.
- `lanes/REVIEW.md` and `.json`: one independent scientific review, independent numerical reproduction and the bounded corrections that closed it.
- `sources/current`: read-only current R36 interpretations and formal qualification records. These conditional products are real recent progress, distinct from the original 42-node acceptance.
- `sources/mes`: reused project derivations and exact Wolfram/check receipts. The original unsuccessful Wolfram call and its corrected call are both retained.
- `sources/literature/retrieval_receipts.json`: primary-source metadata and read scope; the papers themselves remain at their original URLs.
- `RESULT_SUMMARY.json`: machine-readable scope, principal results and the next focused scientific unit.
- `ARTIFACT_MANIFEST.json`: hashes and byte counts of every bundled file.

The PDF provides a foundation and application assessment. Its Gaussian calculations validate the retained observation law; they are not a new empirical Gaia/Planck detection. The 24D source is E1/B1, while the latest R36 common E2/STF response is a separate product. The report makes that distinction explicitly. The raw console receipt retains its original `E2_coverage`/`E2_power` keys meaning experiment 2; the current script expands those labels to `experiment2_*` to avoid confusing them with harmonic E2, with numerical computation unchanged.

The scientific review bound its final pre-render draft. Subsequent rendering fixes inserted a missing heading break, abbreviated long displayed hashes while retaining full identities in manifests, and corrected the 2019 nuisance-hardening author list to Alsing and Wandelt against its primary abstract. The root artifact manifest records the final delivered bytes.

The next unit is a response-qualified kinematic confidence image with a finite compression-error certificate: use identical physical inputs for full-data/GLS and tensor-carrier inference, retain out-of-family diagnostics, and map a declared MES/optical residual allowance into physical and likelihood-error budgets. This is a suggested internal study, not a new controller task or a claim that source-limited original nodes are complete.
