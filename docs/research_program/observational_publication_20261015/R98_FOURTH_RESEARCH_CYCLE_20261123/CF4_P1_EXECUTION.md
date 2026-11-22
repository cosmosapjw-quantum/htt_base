# CF4 and P1 execution result, R98

The full selected group list is exactly the 0.01 ≤ V3k/c ≤ 0.10 cut on the released group table. All 55,877 galaxy rows and 38,053 group rows were inventoried. 52,810 catalogue galaxies belong to the 35,970 primary groups. The 2,083 outside groups comprise 2,075 below and 8 above the redshift interval. The supplementary log regression uses all 38,004 groups with positive velocities. The remaining 49 have no positive log argument and still enter the catalogue-velocity comparison. No group was subsampled.

## Release column convention, numerically checked

The CDS ReadMe defines table4 V3k, fV3k, Vpds, Vpwf and Vpec in integer km/s. DMzp is the calibrated modulus to 0.001 mag, while the displayed Dist is rounded to 0.1 Mpc. We used d=10^((DMzp−25)/5) Mpc and the released fV3k (v), separately from V3k/c defining the redshift window. Direct distance estimates for a source with higher measured recession speed give positive velocities in the DS and log formulas below.

| Reconstructed rule | Release comparison | RMS (km/s) | Max absolute (km/s) |
|---|---:|---:|---:|
| (v−75d)/(1+75d/c) versus Vpds | all 38,053 | 0.39868 | 0.98611 |
| [v/(1+v/c)] log10[v/(75d)] versus Vpwf | positive 38,004 | 0.31333 | 0.95594 |
| same base-ten formula | selected 35,970 | 0.31318 | 0.77510 |
| [v/(1+v/c)] ln[v/(75d)] versus Vpwf | selected 35,970 | 2127.58 | 10992.89 |

75 denotes km/s/Mpc. A separate linear regression of Vpwf/[v/(1+v/c)] against ln[(v/d)/(1 km/s/Mpc)] on the selected groups gives slope 0.43429527 (1/ln 10 = 0.43429448), intercept −1.87506473 and inferred reference 75.0000094 km/s/Mpc. Table4 reproduces the base-ten scaling to approximately the integer release precision. Astropy's independent CDS named-column reader checks the units and formula for all 38,004 positive rows. Tully et al. (2023) Eq. 10 prints “log” and the local ReadMe identifies the column by equation number. The empirical result identifies this release convention. The Watkins–Feldman natural-log estimator, the base-ten catalogue column and our 74.6 km/s/Mpc regression reference have distinct normalizations.

The natural-log working velocity amplitude u=[v/(1+v/c)]y used to set the 250 km/s floor has units km/s. Matching a base-ten velocity noise column at the same reference would require adjusting its units/normalization by ln(10). The new likelihood specifies a dispersion **in u**, not Vpwf. It does not assign physical meaning to the catalogue's Vpwf=0 on the 49 nonpositive-velocity rows.

The published ramp Vpec can be compared to the mix of the displayed DS and WF columns with clipped Vls/3000 weight and DS-only for v<0. The full release RMS difference is 0.08694 km/s. 1PGC 51922 has the only residual above 1 km/s, 2.309 km/s. This is a finite-precision comparison using integer velocity input columns. We did not infer the unavailable unrounded values. The DS–WF RMS difference on the selected rows is 2287.44 km/s, and Vpec differs from Vpwf on 192 of those rows.

## Calibrator genealogy and source response

The full release contains 336 CAL-bearing groups, 228 direct-only and 108 mixed, with 1,134 overlaps among the six velocity-indicator columns. The main selection contains 11 CAL-bearing groups, 2 direct-only (20679, 59927), 9 mixed, and 944 velocity-method overlaps. The descriptive mixed-group CAL−DMzp median/RMS are 0.014/0.441 mag for all 108 and 0.049/0.343 mag for the selected nine. These differences reuse registered products. Numerical-method overlap has rank five in the seven-channel model: the overall zero point and DirectCal relative to the six velocity methods are separate unconstrained directions. DirectCal can move all four signed coefficient vectors; the largest per-magnitude coefficient response is 0.001842. Arbitrarily extending its domain removes finite linear component bounds whenever that component responds to DirectCal.

The geometric angular monopoles are 75.9833, 76.6305, 76.8754 and 75.8854 km/s/Mpc. Full-sample log-STF norms are 0.026860, 0.039792, 0.045817 and 0.024384 in the selected cut, versus 0.030363, 0.039926, 0.045819 and 0.024402 on the broad positive domain. Exponentiating the log monopole gives the geometric angular monopole of the fitted expansion function. The arithmetic sky mean also receives contributions from angular structure. All signed 4×9 coefficients, the direct 36×7 calibration map, overlapping 36×36 covariance and sharp component widths are in CF4_P1_RESULTS.json.

## Internally held-out prediction and finite-law coupling

Each J2000 Cartesian sky octant was held out once. Four Gaussian-window fits on the seven training octants were blended with normalized redshift kernels in log predicted expansion, followed by conversion to modulus. All four models are scored on the same 35,970 held-out μ values and fixed σμ=σlog/a. H03 fits use their archived distance-dependent training weights; log fits keep the same fV-based weights for cz/fV comparison. The full eight-octant score table is saved. Octants share upstream registration, so the small score differences give no independent evidence of cosmological preference.

| Working prediction | Cross-fitted modulus RMS (mag) | Mean squared standardized error | Mean Gaussian NLL (mag density) |
|---|---:|---:|---:|
| Velocity WLS, cz | 0.458295 | 0.886084 | 0.595182 |
| Velocity WLS, fV | 0.457806 | 0.883334 | 0.593807 |
| Log WLS, cz | 0.456969 | 0.877707 | 0.590993 |
| Log WLS, fV | 0.456858 | 0.876551 | 0.590415 |

For all 2,048 paired draws, the nominal log-STF threshold 0.05 yields 0, 57, 626 and 11 window exceedances, with ANY=640 and ALL=0. One common DirectCal perturbation within ±0.5 mag gives ANY=634–649, third window=622–630 and ALL=0. For comparison under the R97 source-Jacobian H03 norm ratio the same illustrative slice gives ANY=1229–1238 and third window=1224–1225. The first column of the five-dimensional relative-contrast Cholesky factor swept over |s|≤sqrt(χ²₅(0.95)) gives ANY=605–912 in the log model and 1065–1662 in the R97 linearized H03 model. These fractions use one offset for all four windows and all draw IDs. Bounds for each of the five one-coordinate slices are in JSON. Neither the 0.5-mag bound nor χ² radius supplies a calibrated posterior or a joint optimum over seven dimensions.

## Coding C1–C10

C1–C2 bound the immutable inputs, H03 producer, R27 row support and the R97 source-Jacobian versus new log-response conventions. C3–C4 used QR, 36×36 covariances and low-dimensional factors. No dense source-square allocation is needed. C5 is the runner below. C6–C8 and the targeted C9 repair passed nine tests, including independent CDS parsing, finite-shift/Cov invariance on independent mocks, attained component supports, zero/tangent/coincident root strictness and analytic sweeps compared to direct sampled ratios. All original 2,048 Sobol coordinates agreed with an independent seeded reconstruction within 1.44e−13. On catalogue data the arbitrary finite 7-mode perturbation matched a full source refit to 7.64e−16 in coefficients, the uniform .087-mag shift to 1.59e−15, and both full 36×36 covariance differences were zero. The stacked-design identity error was 1.12e−15. Minimum covariance eigenvalue 2.063e−7. R6 design and sign checks were lane checks. The fresh parent-assigned R6/C9 review separately reproduced the selected fit/covariance and found an adversarial cancellation in the strict tail calculation. With signed numerators (1,2⁻⁴⁰) and (1,2⁻⁴¹), subtracting unit threshold squared erased both nonzero constants even in extended precision. An exact fallback now uses the original binary-rational inputs, ordered real algebraic roots, and collective strict ties whenever coefficient, discriminant or root-order resolution is doubtful. The regression recovers two distinct tangent roots, nominal event mass 1, minimum 1/2, maximum 1. A second regression covers irrational roots. The independent reviewer owns the final targeted closure receipt. C10 preserves the artifacts, commands, evidence and remaining obligations below.

Run in /home/cosmosapjw/Dropbox/bianchi/htt_base on research/r69-observable-physics-bridges-20261118 at source baseline 52fee3f277d715cdb982dfbe751fefac10513060:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.
.venv/bin/python -B -m scripts.r98.cf4_p1
.venv/bin/python -B -m pytest -q tests/obsstat/test_r98_cf4_p1.py
```

Run status completed in 2.264 s in the repaired calculation, tests 9 passed in 1.65 s. Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1, Linux x86_64. Input path/SHA before and after are recorded in the JSON. The source, tests and exact emitted result SHA256 are 08dcb1231dec0f1aab1789cb8e597830cde54ebae1c48de5573fc42678606b92, 4bfc867baa027170695407aee0c2ad676c2bf68806fe11d1ddba60fa2efb18f6 and 0b9d49d55a1ce2471a5231dc5fda585873cd8a868489ac83092e6ab62d7aa4b6, respectively. Elapsed-time metadata changes on rerun. The downstream tests do not claim repo-wide validity.

| Affected gate | Remaining input/work |
|---|---|
| SQ-CF4 / DATA | Acquire pre-registration per-observation survey/method provenance, native modulus or method observable/error, shared calibration/anchor covariance or samples with gauge reference, CAL errors and cross-method ties including direct-only cases; join by PGC plus survey/object identifier and publish overlap accounting. EDD method landing pages (https://edd.ifa.hawaii.edu/catalogs/ and https://edd.ifa.hawaii.edu/catalog/kcf4snia) identify public adjusted inputs, not automatically independent raw calibration. |
| SQ-CF4 / DATA, MODEL | Obtain group-space, unit/frame-matched correlated PV responses or joint draws, survey selection/completeness versus sky/depth/magnitude/indicator and known MC or independent heldout partition. The R36 projected H03 prior is insufficient to project onto a different source operator. Published CF4 mock catalogues or reconstructed fields require a provenance/overlap audit before treating them as independent. |
| P3 / ADDITIONAL_ANALYSIS | Fit a joint latent-distance/velocity/measurement-selection likelihood including calibration and cosmographic transport. Compare out-of-training predictions on upstream-independent data. The current product score evaluates local apparent structure. |
| P1 / MODEL, ADDITIONAL_ANALYSIS | A physical congruence, optical map, declared physical body and source-qualified joint law/holdout are needed to identify physical Q/Pi/F/G_F. The exact scalar sweeps provide finite-conditional working diagnostics. |
| RUNTIME | No execution blocker for this bounded lane. No root changes, native solver or 60 independent admissions follow from these CF4 calculations. |

Skill context used: physmath-research-loop 1.3.0, THEORY_LOOP, CODING_LOOP, POLICY_INTEGRATION, SUBAGENT_MODE; computation-audit; repository htt-observable-statistics and htt-xqpi-fg-formalism. Sources: Tully et al. (2023), https://arxiv.org/abs/2209.11238; Watkins & Feldman (2015), https://doi.org/10.1093/mnras/stv651; archived original CDS ReadMe, tables and predecessor identities in the result.
