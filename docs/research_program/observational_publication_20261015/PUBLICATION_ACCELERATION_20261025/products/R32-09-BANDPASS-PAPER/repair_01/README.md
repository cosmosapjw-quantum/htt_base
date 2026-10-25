# Manuscript definition repair candidate

This successor addresses the independent review's single source-definition finding. The original sealed candidate remains unchanged in the parent directory, identity `sha256:e550dd06518c162e4ee0dc8c8d08f37e1951058dbe8bc36076a8e8de0cb57020`. Scientific acceptance remains pending exact-candidate independent closeout; original42 acceptances are unchanged.

The public manuscript is `report/main.tex` and its eleven-page `report/main.pdf`. Section II now states the frozen Planck intensity, normalized synchrotron/dust spectra, varying-temperature dust reference denominator, effective LFI transmission, HFI node selection and exact branch-B half-bin shift. A data-availability paragraph points to included finite matrices, source definitions and runnable consumers. These definitions come from the unchanged `data/SPECTRAL_ONLY_CONTRACT.md`, SHA256 `fb137b19b2ec901604691f5d4aa62f05a29e5cbe86404c3c748bf8c8c40386df`.

Only the manuscript was rebuilt. All included data, generated numerical tables/CSV/JSON/macros, vector figures, computational scripts, both existing test sources, source bindings and bibliography remain byte-identical to the original candidate. `NUMERICAL_ASSET_PARITY.json` records the comparison. No response integration, statistics consumer, plotting code, numerical test or upstream solver was rerun in this repair. The existing 14-test result and independent reproduction are reused. The original review and its definition counterexample are retained under `raw/first_review_*`; its alternative normalization is a diagnostic of the missing prose, not an adopted spectrum or result.

For this repair's manuscript-only rebuild, run:

```sh
/usr/bin/python /absolute/path/to/repair_01/rebuild_manuscript.py
```

The unchanged `reproduce.py` remains the full cached-statistics reproduction entrypoint if separately needed. Its constituent numerical work was already executed and checked for the base candidate. `SOURCE_BINDINGS.json` identifies the exact included sources. `CLAIM_SOURCE_MAP.md` and `report/generated/ASSET_PROVENANCE.json` retain the conditional finite signed24 scope and missing physical inputs. No metric, tolerance, covariance, prior, noise law, native-solver boundary or scientific claim ceiling changed.

The final build resolves all citations/references and has no missing figures, duplicate labels or overfull boxes. The existing nameref label-definition package warning remains. Author/affiliation metadata is unspecified, without an invented author. The bounded-moment input remains qualified by its exact external independent decision, while this manuscript successor is only a proposed `bandpass_manuscript` product pending review.
