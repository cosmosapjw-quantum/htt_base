# R32-09-BANDPASS-PAPER affected-component closeout

Independent reviewer: `/root/rc_1862a4246299c380`. Requested runtime: gpt-6-astra/xhigh; observed runtime: UNKNOWN. Read-only review of the product; all new review evidence is confined to this external directory. No children, Git changes, controller-state changes, product edits, upstream integrations, or numerical-suite replay.

**Decision: scoped PASS**, qualifying only `bandpass_manuscript` for candidate `sha256:58bbadbdeb8577702b2c376b612bafe5f3c417bfbf1d1b76283763d57abfd3fc`. The source-definition finding `BANDPASS_MANUSCRIPT_RESPONSE_DEFINITION_AMBIGUOUS` is closed. No blocking or substantive new finding was found within this repair scope.

## Binding and evidence

Review packet `1862a4246299c380be0a475024d891fba39cdaeed822820a379b52e2cc23235f`, task `R32-09-BANDPASS-PAPER`, input `sha256:2cae6d43b4647b33db316df0ebd28efef8cc0e7882fe33bcfbbfff20719fe94c`; actual controller ACK binds this reviewer. The candidate identity is the independently recomputed SHA256 of `repair_01/ARTIFACT_MANIFEST.json`. Its 68 entries all match bytes and sizes. The original manifest remains `sha256:e550dd06518c162e4ee0dc8c8d08f37e1951058dbe8bc36076a8e8de0cb57020`, and its original 168 entries all remain intact.

Evidence read: exact packet/specification and repair plan; immutable `data/SPECTRAL_ONLY_CONTRACT.md:28-48`; base and repaired manuscript and their diff; candidate/base manifests; the 33 numerical/input/code assets; updated claim-source map and data-availability pointer; retained successful manuscript-build receipt and raw output; final log, PDF text, and rendered pages. Prior 14-test and 9-asset independent reproduction is reused only for the unchanged component, as assigned. This closeout does not claim a new execution of those tests or a new proof of upstream qualification.

## Equations, assumptions, and conventions

The controlling model is the stipulated finite trapezoidal response on released retained nodes. Its signed foreground moments are free coordinates of a finite linear relaxation; no observed sky, physical moment radius, noise law, or continuous-passband certificate is supplied.

| Repaired definition | Independent check | Result |
|---|---|---|
| Planck intensity and CMB derivative | `main.tex:31-40` states the exact Planck function and derivative at stipulated T_CMB. The written exp-minus-one is mathematically the source's expm1. | PASS |
| Synchrotron normalization | `main.tex:58-65` gives b_nus times (nu/nu_s)^(beta+2), with beta_s the RJ-temperature index. | PASS |
| Dust normalization | The denominator is B_nud(T) with the same variable T as the numerator before differentiation. It cannot be read as frozen B_nud(T_d). | PASS |
| Temperature derivatives | t=(T-T_d)/T_d and the second derivative T_d^2 partial_T^2 are explicit. A small independent symbolic check gives zero residuals for both chain rules. At nu=nu_d the normalized dust spectrum is b_nud for every T, so both temperature derivatives vanish there. The former frozen-denominator counterexample is excluded. | PASS |
| LFI effective response | Raw g times (nu_ref/nu)^2, 30/44/70 GHz references, finite positive-frequency retained nodes, finite nonnegative transmissions, no cutoff. | PASS |
| HFI selection and integration | Finite positive-frequency nodes, exact FLAG F, raw transmission above each declared B_T, adjacent retained-node trapezoids including removed intervals. The unchanged released input/node validation is reused; the manuscript supplies the source selection definition. | PASS |
| Branch B | Exact (nu_last-nu_first)/(2(N-1)) shift from branch A, before every frequency-dependent factor including nu^-2, described only as version sensitivity. | PASS |
| Column order | F1 and F2 derivative order, pivot values, and absorbed Taylor factorials agree with the immutable source. | PASS |
| Dimensions and scope | Spectra are per reference K_CMB amplitude; R and F are dimensionless; Y,s,U share harmonic-amplitude units. The full signed E2/E3/B2/B3 24-carrier, common harmonic frame, and separate temperature observable remain explicit. | PASS |

The inserted definitions uniquely identify the foreground columns underlying the unchanged coefficient metric. The diff is restricted to the intended section II definitions and data availability; it introduces no normalization change in the underlying data or generated numerical assets. The data paragraph identifies included finite response matrices, bounded sufficient statistics, the source contract, `consumer.py`, `publication.py`, `reproduce.py`, and `SOURCE_BINDINGS.json`; these paths exist. The full signed carrier and coefficient-fibre statements remain intact.

## Numerical asset and build audit

`check_closeout.py` independently enumerated the retained data, generated assets, figure files, code/tests, bindings, and bibliography: 33 files, all byte-identical to the original candidate. It verified all original168 and repaired68 manifest entries, recorded the source diff, and checked included assets and exact source/build bindings. `SOURCE_ALGEBRA.json` records the small SymPy 1.14.0 definition checks. Neither operation re-executed a passband integration or the unchanged 14-test suite.

The actual retained command `latexmk -pdf -interaction=nonstopmode -halt-on-error -cd report/main.tex` exited 0 in the repair, with a source hash matching the reviewed main.tex. Its raw output retains transient early-pass missing bibliography/citation warnings; the final main.log and final pdflatex output resolve them. The sole final warning is the pre-existing nameref label-definition package warning. There are no final undefined citations/references, missing assets, duplicate labels, overfull/underfull boxes, or build errors.

Independent PDF inspection confirms 11 pages, 356626 bytes, SHA256 `09d92308ba44db071b51fdabb4cdc634f6b99dfd640d94cc84a3f47f348fee9f`. All pages were rasterized and inspected in a contact sheet, with detailed inspection of the repaired definition pages 2 and 3 and final page11. The final text contains the new normalization and source pointer; no unresolved reference markers were found. No equation, figure, or table clipping or overlap was observed. A one-line continuation of data availability onto page11 is cosmetic and does not impede interpretation; no cosmetic repair is required for this scope.

## Claim ceiling, residual limits, and stopping rule

The safe product is a source-bound, conditional finite signed24 seven-passband bounded-moment methods manuscript. MIO/HTT ownership is unchanged. The paper retains the separate SMICA-derived-map qualification, absence of observed Y or target amplitude, undefined physical sectors, and absence of physical moment/noise calibration. No physical null, native Bianchi solver, native-family identification, ODE evolution, original42 acceptance, same-sky independence, or cosmic anomaly claim is admitted.

No manuscript repair is requested. No new numerical tests are required for this unchanged component. New physical conclusions would still require the branch-local physical inputs already identified by the paper. This verdict closes only the exact repaired manuscript node; it does not constitute submission, publication, or completion of the original 42-node scientific acceptances. The controller may consume the exact bound return and proceed to its next dependency-safe action.
