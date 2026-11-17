# R63 validation and claim boundaries

Baseline: `f29bbab420a33aecb1c398ddd961fd45097f536b`.
Branch: `research/r63-local-boost-global-tilt-20261117`.
Scope: one integrated ten-stage local-boost/global-tilt study; C0 conditional actual-data response experiment.

## Executed scientific verification

- Native runtime: Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1; single-thread BLAS.
- Primary affected suite: **54 passed, exit 0, 2.28 s**. This includes the 20 R63 construction tests; do not add them twice. Receipt: `RESULTS/AFFECTED_TEST_RECEIPT.json` and log.
- Actual observed experiment: **exit 0**, first execution, 2.283 s. Original R58 carrier, actual 35,970 CF4 rows, seven operators and full 32-dimensional covariance. Four overlapping Gaussian windows are correlated, as are the seven alternative nuisance prescriptions.
- 14 free-history fits, 42 baseline/physical fits and seven additional J2 calibration fits. Actual-source injection, R62 parity, rank, h-quotient, Wald/LR, Schur identity and path invariance checks are inside that run.
- Catalogue chart: 42 deterministic affine transports agree with direct GLS within scaled error 4.66e-12; **exit 0**. The same data selection, quoted-redshift operators, covariance and designs are retained.
- Interpretation summarizer: **exit 0**; no further fitting. The corrected physical-ball likelihood bound is computed from the corrected target score; original and corrected fields are distinguished. Maximum corrected bound 7.072507307971148e-6.
- Two PNG/PDF figures were inspected. Labels, legends, units and scope text are legible; the plots report a tangent-coefficient sensitivity and deterministic catalogue operation, not a physical superluminal velocity or a new observer measurement.
- Wolfram symbolic identities returned zero residuals. Intermediate Limit/infinity warnings and the initial tool error are retained in `REVIEW/WOLFRAM_CHECK.json`; this is not a replacement for the numerical native checks.

Primary test command:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/r63/test_frame_history.py tests/r58/test_mixed_tensor_likelihood.py tests/r58/test_five_views.py
```

Reproduction entry points, with a fresh output destination for the scripts that refuse overwrite:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -B scripts/r63/run_r63_frame_history.py --root . --output /tmp/htt-r63-observed-reproduction
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -B scripts/r63/transport_r63_catalogue_chart.py --root . --output /tmp/htt-r63-chart-reproduction.json
```

The chart script intentionally pins the archived observed carrier; a new reproduction is compared with that carrier rather than silently replacing it. NPZ file byte identity and numerical semantic equivalence are distinct.

## Evidence states

| Item | State | Boundary |
|---|---|---|
| Qualified local relative-frame invariant and standard distance response | established / literature-supported | A local invariant alone does not establish global homogeneity |
| Processed chart fibre, compensated history map and Gaussian oracle bound | derived / numerically checked | First-order source law and specified nuisance/working covariance |
| Actual CF4 rank, scores, chart transport and five-view invariance | implementation-verified | The retained 32D experiment; not all possible raw-data modes |
| Common-calibration full-tensor rank advantage | implementation-verified | Same finite source-STF nuisance must be used in both comparisons |
| Photon/electron remote-dipole map of the same source | derived | Source matching and reconstruction calibration required |
| A new adopted kSZ U limit or CMB 3D likelihood | unresolved | Exact convention, window/bias and joint likelihood unavailable |
| Physical global-tilt detection, universal no-go or measured superluminal W | not established | No such claim is made |
| Method-level photometry, group mixing, selection and nonlinear remainder | unresolved | Limits physical attribution, not the execution of the working experiment |

## Final independent review and release

`REVIEW_STATUS: PASS; zero open findings`

One fresh independent review completed with no findings. It verified all 22 frozen hashes and independently reconstructed the history/separation information for 14 saved carriers using QR, without repeating the fits or suite. The recomputed maximum power was 0.10000041873090332, agreeing at the displayed precision. No scientific correction episode was needed. Inputs are pinned in `REVIEW/FINAL_REVIEW_INPUT.json`; findings and actual reading/execution scope are in `REVIEW/final_review.json`. Post-review document changes only record this verdict. Stage10 DAG validation is recorded in `DAG_VALIDATION.json`; a review PASS does not imply journal readiness.

Original publication acceptance contracts and 42 science gates remain authoritative. P4 is `NOT_READY_TO_SUBMIT`. No automatic successor loop, main merge or local coding-agent prompt is part of this release.

## Completed DAG verification

The reviewed finalizer added exactly one card (286 to287) and one scoped completion (221 to222). Canonical PR DAG validation, mirror `--check`, publication DAG validation and `git diff --check` all exited0. Original42 node payload SHA256 remains `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d`. The first mirror invocation omitted its mandatory `--write` mode and exited2 before mutation; that CLI-usage failure is preserved in `DAG_VALIDATION_ATTEMPT01.json`. The corrected invocation and all required gates succeeded without scientific changes.

The staged-file check additionally found seven redundant final blank lines. Only those EOF bytes were normalized; both affected Python ASTs are identical. `REVIEW/POST_REVIEW_WHITESPACE.json` records every before/after hash, and original execution/review hashes remain unchanged as provenance. The final staged check is recorded separately.
