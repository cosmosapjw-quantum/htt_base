# Coding research handoff — independent review / thin integration only

This packet already contains executed prototype code and synthetic campaigns. Do not restart a planning-only cycle and do not label the unperformed independent review PASS.

## Read
1. SCIENTIFIC_CONTRACT.md
2. CODING_RESEARCH_REPORT_KO.md
3. results/FINAL_EXECUTION_RECEIPT.json
4. review/IMPLEMENTER_AUDIT.md
5. review/INDEPENDENT_REVIEW_BRIEF.md
6. provenance/SEED_COVERAGE.json

## First execution
In an isolated environment, without changing the user's HTT venv:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q -p no:cacheprovider tests seed/MES_TENSOR_TILT_RESEARCH_20260830/code/test_research_core.py
python tools/validate_harness.py
python tools/check_regression_sensitivity.py
```

Run a new campaign only into a new output directory. Compare its deterministic files with `results/final_execution/`; timing and PDF bytes are not scientific numeric identity. The tested stack is in requirements-tested.txt, not a demand to install into production.

## Do not
- query/run GitHub Actions;
- download data or read raw maps;
- resurrect withdrawn WU006–008 ranks;
- rename a Q/O response projection beta as an observed physical velocity;
- infer instantaneous shear from integrated B without dynamics;
- remove intrinsic nuisance to obtain point identification;
- treat unmatched query/null noise as exchangeable;
- change a frozen scientific convention in the production repository;
- push/merge any external repository without explicit approval;
- claim independent review from the implementer's audit or seed Wolfram receipt.

## Next objective
A separate read-only reviewer should inspect the exact source, tests, campaign registry, held negative results and input/output manifest. In particular inspect the STF basis sign/scale, Lorentz eigenproblem, near-isotropic cancellation, noise-model distinction, nuisance rank threshold and exact rank comparisons. Review must bind actual code hashes, not just generated outputs.

A thin production adapter is a later separately authorized change. It must preserve existing public APIs and scientific baselines, use explicit convention conversion at boundaries, and be tested against the real caller/exporter with corrected normalization. Do not integrate by copying generated physical labels or old observed ranks.
